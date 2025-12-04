"""
API endpoints for viewing audit logs
"""
from fastapi import APIRouter, Query, Depends
from typing import Optional
from datetime import datetime, timedelta
from app.services.supabase_service import SupabaseService
from app.services.audit_logger import audit_logger
from app.api.auth import get_current_user
from app.core.error_utils import handle_api_errors
from app.db.models import AuditLogAction, AuditLog
from app.db.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_

router = APIRouter()


@router.get("/audit/logs")
@handle_api_errors(context="fetching audit logs")
async def get_audit_logs(
    action: Optional[str] = Query(None, description="Filter by action type"),
    user_email: Optional[str] = Query(None, description="Filter by user email"),
    status: Optional[str] = Query(None, description="Filter by status (success, error, partial)"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: Optional[int] = Query(100, description="Number of records to return"),
    offset: Optional[int] = Query(0, description="Offset for pagination"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get audit logs with optional filtering.
    Only accessible to authenticated users.
    """
    # Use raw SQL to avoid ORM enum conversion issues
    from sqlalchemy import text
    
    # Build WHERE clause conditions
    where_clauses = []
    params = {}
    
    if action:
        where_clauses.append("action = :action")
        params["action"] = action
    if user_email:
        where_clauses.append("user_email = :user_email")
        params["user_email"] = user_email
    if status:
        where_clauses.append("status = :status")
        params["status"] = status
    if start_date:
        start_datetime = datetime.fromisoformat(f"{start_date}T00:00:00+00:00")
        where_clauses.append("created_at >= :start_date")
        params["start_date"] = start_datetime
    if end_date:
        end_datetime = datetime.fromisoformat(f"{end_date}T23:59:59+00:00")
        where_clauses.append("created_at <= :end_date")
        params["end_date"] = end_datetime
    
    where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
    
    # Get total count
    count_query = text(f"SELECT COUNT(*) FROM audit_logs WHERE {where_clause}")
    total_count = db.execute(count_query, params).scalar() or 0
    
    # Build main query
    query_str = f"""
        SELECT id, action, user_id, user_email, ip_address, user_agent, 
               details, status, error_message, created_at
        FROM audit_logs
        WHERE {where_clause}
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :offset
    """
    
    params["limit"] = limit or 100
    params["offset"] = offset or 0
    
    # Execute query
    query = text(query_str)
    result = db.execute(query, params)
    rows = result.fetchall()
    
    # Convert to dict format
    logs_data = []
    for row in rows:
        log_dict = {
            "id": row[0],
            "action": row[1],  # Already a string from database
            "user_id": row[2],
            "user_email": row[3],
            "ip_address": row[4],
            "user_agent": row[5],
            "details": row[6],
            "status": row[7],
            "error_message": row[8],
            "created_at": row[9].isoformat() if row[9] else None
        }
        logs_data.append(log_dict)
    
    return {
        "items": logs_data,
        "count": len(logs_data),
        "total": total_count,
        "limit": limit,
        "offset": offset
    }


@router.get("/audit/stats")
@handle_api_errors(context="fetching audit statistics")
async def get_audit_stats(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get audit log statistics.
    Returns counts by action type, status, and user.
    """
    # Use raw SQL to avoid ORM enum conversion issues
    from sqlalchemy import text
    
    # Build WHERE clause conditions
    where_clauses = []
    params = {}
    
    if start_date:
        start_datetime = datetime.fromisoformat(f"{start_date}T00:00:00+00:00")
        where_clauses.append("created_at >= :start_date")
        params["start_date"] = start_datetime
    if end_date:
        end_datetime = datetime.fromisoformat(f"{end_date}T23:59:59+00:00")
        where_clauses.append("created_at <= :end_date")
        params["end_date"] = end_datetime
    
    where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
    
    # Get all logs in date range (for aggregation)
    query_str = f"""
        SELECT action, status, user_email
        FROM audit_logs
        WHERE {where_clause}
    """
    query = text(query_str)
    result = db.execute(query, params)
    rows = result.fetchall()
    
    # Convert rows to list of dicts for processing
    logs = [{"action": row[0], "status": row[1], "user_email": row[2]} for row in rows]
    
    # Aggregate statistics
    stats = {
        "total_logs": len(logs),
        "by_action": {},
        "by_status": {},
        "by_user": {},
        "recent_logins": 0,
        "recent_syncs": 0,
        "recent_user_creations": 0
    }
    
    # Calculate stats
    for log in logs:
        action = log["action"]  # Already a string from database
        status = log["status"]
        user_email = log["user_email"]
        
        # Count by action
        if action:
            stats["by_action"][action] = stats["by_action"].get(action, 0) + 1
        
        # Count by status
        if status:
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
        
        # Count by user
        if user_email:
            stats["by_user"][user_email] = stats["by_user"].get(user_email, 0) + 1
        
        # Count specific actions
        if action == "login":
            stats["recent_logins"] += 1
        elif action in ["sync_brands", "sync_prompts", "sync_responses", "sync_ga4", "sync_agency_analytics", "sync_all"]:
            stats["recent_syncs"] += 1
        elif action == "user_created":
            stats["recent_user_creations"] += 1
    
    return stats


@router.get("/audit/user-activity")
@handle_api_errors(context="fetching user activity")
async def get_user_activity(
    user_email: Optional[str] = Query(None, description="Filter by user email (defaults to current user)"),
    limit: Optional[int] = Query(50, description="Number of records to return"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get activity logs for a specific user.
    Defaults to current user if user_email not provided.
    """
    # Use current user if no email provided
    target_email = user_email or current_user["email"]
    
    # Use raw SQL to avoid ORM enum conversion issues
    from sqlalchemy import text
    
    # Build query
    query_str = """
        SELECT id, action, user_id, user_email, ip_address, user_agent, 
               details, status, error_message, created_at
        FROM audit_logs
        WHERE user_email = :user_email
        ORDER BY created_at DESC
        LIMIT :limit
    """
    
    query = text(query_str)
    result = db.execute(query, {
        "user_email": target_email,
        "limit": limit or 50
    })
    rows = result.fetchall()
    
    # Convert to dict format
    logs_data = []
    for row in rows:
        log_dict = {
            "id": row[0],
            "action": row[1],  # Already a string from database
            "user_id": row[2],
            "user_email": row[3],
            "ip_address": row[4],
            "user_agent": row[5],
            "details": row[6],
            "status": row[7],
            "error_message": row[8],
            "created_at": row[9].isoformat() if row[9] else None
        }
        logs_data.append(log_dict)
    
    return {
        "user_email": target_email,
        "items": logs_data,
        "count": len(logs_data)
    }


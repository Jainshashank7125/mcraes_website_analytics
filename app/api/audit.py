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
    # Build query using SQLAlchemy ORM
    query = select(AuditLog)
    count_query = select(func.count(AuditLog.id))
    
    # Apply filters
    conditions = []
    if action:
        conditions.append(AuditLog.action == action)
    if user_email:
        conditions.append(AuditLog.user_email == user_email)
    if status:
        conditions.append(AuditLog.status == status)
    if start_date:
        start_datetime = datetime.fromisoformat(f"{start_date}T00:00:00+00:00")
        conditions.append(AuditLog.created_at >= start_datetime)
    if end_date:
        end_datetime = datetime.fromisoformat(f"{end_date}T23:59:59+00:00")
        conditions.append(AuditLog.created_at <= end_datetime)
    
    if conditions:
        query = query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))
    
    # Get total count
    total_count = db.execute(count_query).scalar() or 0
    
    # Order by created_at descending (most recent first)
    query = query.order_by(AuditLog.created_at.desc())
    
    # Apply pagination
    if limit:
        query = query.limit(limit)
    if offset:
        query = query.offset(offset)
    
    # Execute query
    result = db.execute(query)
    logs = result.scalars().all()
    
    # Convert to dict format
    logs_data = []
    for log in logs:
        log_dict = {
            "id": log.id,
            "action": log.action.value if hasattr(log.action, 'value') else str(log.action),
            "user_id": log.user_id,
            "user_email": log.user_email,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "details": log.details,
            "status": log.status,
            "error_message": log.error_message,
            "created_at": log.created_at.isoformat() if log.created_at else None
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
    # Build query with date filters
    query = select(AuditLog)
    conditions = []
    
    if start_date:
        start_datetime = datetime.fromisoformat(f"{start_date}T00:00:00+00:00")
        conditions.append(AuditLog.created_at >= start_datetime)
    if end_date:
        end_datetime = datetime.fromisoformat(f"{end_date}T23:59:59+00:00")
        conditions.append(AuditLog.created_at <= end_datetime)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    # Get all logs in date range (for aggregation)
    result = db.execute(query)
    logs = result.scalars().all()
    
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
        action = log.action.value if hasattr(log.action, 'value') else str(log.action)
        status = log.status
        user_email = log.user_email
        
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
    
    # Build query using SQLAlchemy ORM
    query = select(AuditLog).where(AuditLog.user_email == target_email)
    query = query.order_by(AuditLog.created_at.desc()).limit(limit or 50)
    
    # Execute query
    result = db.execute(query)
    logs = result.scalars().all()
    
    # Convert to dict format
    logs_data = []
    for log in logs:
        log_dict = {
            "id": log.id,
            "action": log.action.value if hasattr(log.action, 'value') else str(log.action),
            "user_id": log.user_id,
            "user_email": log.user_email,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "details": log.details,
            "status": log.status,
            "error_message": log.error_message,
            "created_at": log.created_at.isoformat() if log.created_at else None
        }
        logs_data.append(log_dict)
    
    return {
        "user_email": target_email,
        "items": logs_data,
        "count": len(logs_data)
    }


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
from app.db.models import AuditLogAction

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
    current_user: dict = Depends(get_current_user)
):
    """
    Get audit logs with optional filtering.
    Only accessible to authenticated users.
    """
    supabase = SupabaseService()
    
    query = supabase.client.table("audit_logs").select("*")
    
    # Apply filters
    if action:
        query = query.eq("action", action)
    if user_email:
        query = query.eq("user_email", user_email)
    if status:
        query = query.eq("status", status)
    if start_date:
        query = query.gte("created_at", f"{start_date}T00:00:00Z")
    if end_date:
        query = query.lte("created_at", f"{end_date}T23:59:59Z")
    
    # Order by created_at descending (most recent first)
    query = query.order("created_at", desc=True)
    
    # Apply pagination
    if limit:
        query = query.limit(limit)
    if offset:
        query = query.offset(offset)
    
    result = query.execute()
    logs = result.data if hasattr(result, 'data') else []
    
    # Get total count for pagination
    count_query = supabase.client.table("audit_logs").select("id", count="exact")
    if action:
        count_query = count_query.eq("action", action)
    if user_email:
        count_query = count_query.eq("user_email", user_email)
    if status:
        count_query = count_query.eq("status", status)
    if start_date:
        count_query = count_query.gte("created_at", f"{start_date}T00:00:00Z")
    if end_date:
        count_query = count_query.lte("created_at", f"{end_date}T23:59:59Z")
    
    count_result = count_query.execute()
    total_count = count_result.count if hasattr(count_result, 'count') else len(logs)
    
    return {
        "items": logs,
        "count": len(logs),
        "total": total_count,
        "limit": limit,
        "offset": offset
    }


@router.get("/audit/stats")
@handle_api_errors(context="fetching audit statistics")
async def get_audit_stats(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get audit log statistics.
    Returns counts by action type, status, and user.
    """
    supabase = SupabaseService()
    
    # Build base query
    base_query = supabase.client.table("audit_logs").select("*")
    if start_date:
        base_query = base_query.gte("created_at", f"{start_date}T00:00:00Z")
    if end_date:
        base_query = base_query.lte("created_at", f"{end_date}T23:59:59Z")
    
    # Get all logs in date range (for aggregation)
    result = base_query.execute()
    logs = result.data if hasattr(result, 'data') else []
    
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
        action = log.get("action")
        status = log.get("status")
        user_email = log.get("user_email")
        
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
    current_user: dict = Depends(get_current_user)
):
    """
    Get activity logs for a specific user.
    Defaults to current user if user_email not provided.
    """
    supabase = SupabaseService()
    
    # Use current user if no email provided
    target_email = user_email or current_user["email"]
    
    query = supabase.client.table("audit_logs").select("*").eq("user_email", target_email)
    query = query.order("created_at", desc=True).limit(limit or 50)
    
    result = query.execute()
    logs = result.data if hasattr(result, 'data') else []
    
    return {
        "user_email": target_email,
        "items": logs,
        "count": len(logs)
    }


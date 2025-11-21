"""
Audit logging service for tracking user actions and data syncs
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from app.services.supabase_service import SupabaseService
from app.db.models import AuditLogAction
from app.core.config import settings

logger = logging.getLogger(__name__)


class AuditLogger:
    """Service for logging audit events"""
    
    def __init__(self):
        self.supabase = SupabaseService()
    
    def _get_client_ip(self, request) -> Optional[str]:
        """Extract client IP address from request"""
        if not request:
            return None
        
        # Check for forwarded IP (behind proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        # Check for real IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return None
    
    def _get_user_agent(self, request) -> Optional[str]:
        """Extract user agent from request"""
        if not request:
            return None
        return request.headers.get("User-Agent")
    
    async def log(
        self,
        action: AuditLogAction,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        status: str = "success",
        details: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        request = None
    ):
        """
        Log an audit event
        
        Args:
            action: Type of action (from AuditLogAction enum)
            user_id: Supabase user ID
            user_email: User email
            status: Status of action ('success', 'error', 'partial')
            details: Additional context (brand_id, sync counts, etc.)
            error_message: Error message if status is 'error'
            request: FastAPI request object (for IP and user agent)
        """
        try:
            ip_address = self._get_client_ip(request) if request else None
            user_agent = self._get_user_agent(request) if request else None
            
            log_entry = {
                "action": action.value,
                "user_id": user_id,
                "user_email": user_email,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "details": details or {},
                "status": status,
                "error_message": error_message,
                "created_at": datetime.utcnow().isoformat() + "Z"
            }
            
            # Insert into audit_logs table
            result = self.supabase.client.table("audit_logs").insert(log_entry).execute()
            
            logger.info(
                f"Audit log created: action={action.value}, user={user_email}, status={status}"
            )
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            # Don't fail the main operation if logging fails
            logger.error(f"Failed to create audit log: {str(e)}")
            return None
    
    async def log_login(
        self,
        user_id: str,
        user_email: str,
        status: str = "success",
        error_message: Optional[str] = None,
        request = None
    ):
        """Log user login"""
        return await self.log(
            action=AuditLogAction.LOGIN,
            user_id=user_id,
            user_email=user_email,
            status=status,
            error_message=error_message,
            request=request
        )
    
    async def log_logout(
        self,
        user_id: str,
        user_email: str,
        request = None
    ):
        """Log user logout"""
        return await self.log(
            action=AuditLogAction.LOGOUT,
            user_id=user_id,
            user_email=user_email,
            status="success",
            request=request
        )
    
    async def log_user_created(
        self,
        created_by_user_id: str,
        created_by_email: str,
        new_user_id: str,
        new_user_email: str,
        request = None
    ):
        """Log user creation"""
        return await self.log(
            action=AuditLogAction.USER_CREATED,
            user_id=created_by_user_id,
            user_email=created_by_email,
            status="success",
            details={
                "new_user_id": new_user_id,
                "new_user_email": new_user_email
            },
            request=request
        )
    
    async def log_sync(
        self,
        sync_type: AuditLogAction,
        user_id: Optional[str],
        user_email: Optional[str],
        status: str = "success",
        details: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        request = None
    ):
        """Log data sync operation"""
        return await self.log(
            action=sync_type,
            user_id=user_id,
            user_email=user_email,
            status=status,
            details=details,
            error_message=error_message,
            request=request
        )


# Global instance
audit_logger = AuditLogger()


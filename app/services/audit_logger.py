"""
Audit logging service for tracking user actions and data syncs
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.models import AuditLogAction, AuditLog
from app.core.config import settings

logger = logging.getLogger(__name__)


class AuditLogger:
    """Service for logging audit events"""
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db
    
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
        request = None,
        db: Optional[Session] = None
    ):
        """
        Log an audit event
        
        Args:
            action: Type of action (from AuditLogAction enum)
            user_id: User ID
            user_email: User email
            status: Status of action ('success', 'error', 'partial')
            details: Additional context (brand_id, sync counts, etc.)
            error_message: Error message if status is 'error'
            request: FastAPI request object (for IP and user agent)
            db: Database session (optional, will use self.db if not provided)
        """
        db_session = None
        should_close = False
        try:
            # Use provided db or instance db
            db_session = db or self.db
            if not db_session:
                # Fallback: create a new session if none provided
                from app.db.database import SessionLocal
                db_session = SessionLocal()
                should_close = True
            
            ip_address = self._get_client_ip(request) if request else None
            user_agent = self._get_user_agent(request) if request else None
            
            # Use SQLAlchemy Core with raw SQL to insert into audit_logs table
            # This bypasses the ORM's enum conversion which was using enum names instead of values
            from sqlalchemy import text
            
            action_value = action.value  # Get the string value (e.g., "login")
            details_dict = details or {}
            
            # Ensure action_value is a string, not an enum
            if hasattr(action_value, 'value'):
                action_value = action_value.value
            action_value = str(action_value)
            
            # Import json for details serialization
            import json
            
            # Serialize details to JSON string
            details_json_str = json.dumps(details_dict) if details_dict else '{}'
            
            # Use text() with proper parameter binding - use :name style for SQLAlchemy text()
            stmt = text("""
                INSERT INTO audit_logs (action, user_id, user_email, ip_address, user_agent, details, status, error_message)
                VALUES (CAST(:action AS auditlogaction), :user_id, :user_email, :ip_address, :user_agent, CAST(:details AS jsonb), :status, :error_message)
                RETURNING id
            """)
            
            result = db_session.execute(stmt, {
                "action": action_value,
                "user_id": user_id,
                "user_email": user_email,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "details": details_json_str,
                "status": status,
                "error_message": error_message,
            })
            db_session.commit()
            log_id = result.scalar()
            
            logger.info(
                f"Audit log created: action={action.value}, user={user_email}, status={status}, id={log_id}"
            )
            
            return {
                "id": log_id,
                "action": action.value,
                "user_id": user_id,
                "user_email": user_email,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "details": details or {},
                "status": status,
                "error_message": error_message,
            }
            
        except Exception as e:
            # Don't fail the main operation if logging fails
            logger.error(f"Failed to create audit log: {str(e)}")
            return None
        finally:
            if should_close and db_session:
                try:
                    db_session.close()
                except:
                    pass
    
    async def log_login(
        self,
        user_id: str,
        user_email: str,
        status: str = "success",
        error_message: Optional[str] = None,
        request = None,
        db: Optional[Session] = None
    ):
        """Log user login"""
        return await self.log(
            action=AuditLogAction.LOGIN,
            user_id=user_id,
            user_email=user_email,
            status=status,
            error_message=error_message,
            request=request,
            db=db
        )
    
    async def log_logout(
        self,
        user_id: str,
        user_email: str,
        request = None,
        db: Optional[Session] = None
    ):
        """Log user logout"""
        return await self.log(
            action=AuditLogAction.LOGOUT,
            user_id=user_id,
            user_email=user_email,
            status="success",
            request=request,
            db=db
        )
    
    async def log_user_created(
        self,
        created_by_user_id: str,
        created_by_email: str,
        new_user_id: str,
        new_user_email: str,
        request = None,
        db: Optional[Session] = None
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
            request=request,
            db=db
        )
    
    async def log_sync(
        self,
        sync_type: AuditLogAction,
        user_id: Optional[str],
        user_email: Optional[str],
        status: str = "success",
        details: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        request = None,
        db: Optional[Session] = None
    ):
        """Log data sync operation"""
        return await self.log(
            action=sync_type,
            user_id=user_id,
            user_email=user_email,
            status=status,
            details=details,
            error_message=error_message,
            request=request,
            db=db
        )


# Global instance
audit_logger = AuditLogger()


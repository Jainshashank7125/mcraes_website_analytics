"""
Service for managing async sync jobs
"""
import uuid
import asyncio
import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text, Table, MetaData, select, update, insert
from app.db.database import get_db, SessionLocal
from app.services.audit_logger import audit_logger
from app.db.models import AuditLogAction

logger = logging.getLogger(__name__)


class SyncJobService:
    """Service for managing async sync jobs"""
    
    def __init__(self, db: Optional[Session] = None):
        """
        Initialize service with optional database session.
        If db is None, will create a new session when needed.
        """
        self.db = db
        self.running_jobs: Dict[str, asyncio.Task] = {}
        self.cancelled_jobs: set = set()  # Track cancelled job IDs
    
    def _get_db(self) -> Session:
        """Get database session - creates new one if not provided"""
        if self.db:
            return self.db
        return SessionLocal()
    
    def _get_sync_jobs_table(self) -> Table:
        """Get sync_jobs table using reflection"""
        db = self._get_db()
        metadata = MetaData()
        metadata.reflect(bind=db.bind, only=["sync_jobs"])
        return metadata.tables["sync_jobs"]
    
    def _generate_job_id(self) -> str:
        """Generate unique job ID"""
        return str(uuid.uuid4())
    
    async def create_job(
        self,
        sync_type: str,
        user_id: Optional[str],
        user_email: Optional[str],
        parameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new sync job and return job ID"""
        job_id = self._generate_job_id()
        db = self._get_db()
        
        try:
            # Convert parameters dict to JSON string for JSONB column
            parameters_json = json.dumps(parameters or {})
            created_at = datetime.utcnow()
            
            # Use CAST instead of ::jsonb to avoid parameter binding issues
            query = text("""
                INSERT INTO sync_jobs (job_id, sync_type, user_id, user_email, status, progress, parameters, created_at)
                VALUES (:job_id, :sync_type, :user_id, :user_email, :status, :progress, CAST(:parameters AS jsonb), :created_at)
            """)
            
            db.execute(query, {
                "job_id": job_id,
                "sync_type": sync_type,
                "user_id": user_id,
                "user_email": user_email,
                "status": "pending",
                "progress": 0,
                "parameters": parameters_json,  # Pass as JSON string
                "created_at": created_at
            })
            db.commit()
            logger.info(f"Created sync job {job_id} for {sync_type}")
            return job_id
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create sync job: {str(e)}")
            raise
        finally:
            if not self.db:  # Only close if we created the session
                db.close()
    
    async def update_job_status(
        self,
        job_id: str,
        status: str,
        progress: Optional[int] = None,
        current_step: Optional[str] = None,
        total_steps: Optional[int] = None,
        completed_steps: Optional[int] = None,
        error_message: Optional[str] = None
    ):
        """Update job status"""
        db = self._get_db()
        
        try:
            # Build update query dynamically
            updates = ["status = :status", "updated_at = NOW()"]
            params = {"job_id": job_id, "status": status}
            
            if progress is not None:
                updates.append("progress = :progress")
                params["progress"] = progress
            if current_step is not None:
                updates.append("current_step = :current_step")
                params["current_step"] = current_step
            if total_steps is not None:
                updates.append("total_steps = :total_steps")
                params["total_steps"] = total_steps
            if completed_steps is not None:
                updates.append("completed_steps = :completed_steps")
                params["completed_steps"] = completed_steps
            if error_message is not None:
                updates.append("error_message = :error_message")
                params["error_message"] = error_message
            
            if status == "running":
                updates.append("started_at = COALESCE(started_at, NOW())")
            
            if status in ["completed", "failed", "cancelled"]:
                updates.append("completed_at = NOW()")
            
            query = text(f"""
                UPDATE sync_jobs
                SET {', '.join(updates)}
                WHERE job_id = :job_id
            """)
            
            db.execute(query, params)
            db.commit()
            
            # Send WebSocket notification for status changes
            try:
                from app.services.websocket_manager import websocket_manager
                job = await self.get_job(job_id)
                if job:
                    sync_type = job.get("sync_type", "unknown")
                    parameters = job.get("parameters", {})
                    brand_id = parameters.get("brand_id")
                    
                    if status == "running":
                        message = f"Sync started: {current_step or 'Processing...'}"
                    elif status in ["completed", "failed", "cancelled"]:
                        message = f"Sync {status}: {current_step or 'Finished'}"
                    else:
                        message = current_step or f"Sync {status}"
                    
                    await websocket_manager.notify_sync_status(
                        sync_type=sync_type,
                        brand_id=brand_id,
                        status=status,
                        message=message,
                        job_id=job_id
                    )
            except Exception as ws_error:
                logger.warning(f"Failed to send WebSocket notification for job {job_id}: {str(ws_error)}")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update job {job_id}: {str(e)}")
        finally:
            if not self.db:  # Only close if we created the session
                db.close()
    
    async def complete_job(
        self,
        job_id: str,
        result: Dict[str, Any],
        status: str = "completed"
    ):
        """Mark job as completed with result"""
        db = self._get_db()
        
        try:
            # Convert result dict to JSON string for JSONB column
            result_json = json.dumps(result)
            
            # Use CAST instead of ::jsonb to avoid parameter binding issues
            query = text("""
                UPDATE sync_jobs
                SET status = :status,
                    progress = 100,
                    result = CAST(:result AS jsonb),
                    completed_at = NOW(),
                    updated_at = NOW()
                WHERE job_id = :job_id
            """)
            
            db.execute(query, {
                "job_id": job_id,
                "status": status,
                "result": result_json  # Pass as JSON string
            })
            db.commit()
            logger.info(f"Completed sync job {job_id}")
            
            # Send WebSocket notification
            try:
                from app.services.websocket_manager import websocket_manager
                job = await self.get_job(job_id)
                if job:
                    sync_type = job.get("sync_type", "unknown")
                    parameters = job.get("parameters", {})
                    brand_id = parameters.get("brand_id")
                    message = result.get("message", f"Sync {status} successfully")
                    
                    await websocket_manager.notify_sync_status(
                        sync_type=sync_type,
                        brand_id=brand_id,
                        status=status,
                        message=message,
                        job_id=job_id
                    )
            except Exception as ws_error:
                logger.warning(f"Failed to send WebSocket notification for job {job_id}: {str(ws_error)}")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to complete job {job_id}: {str(e)}")
        finally:
            if not self.db:  # Only close if we created the session
                db.close()
    
    async def fail_job(
        self,
        job_id: str,
        error_message: str
    ):
        """Mark job as failed"""
        await self.update_job_status(
            job_id=job_id,
            status="failed",
            error_message=error_message
        )
        logger.error(f"Sync job {job_id} failed: {error_message}")
    
    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job by ID"""
        db = self._get_db()
        
        try:
            query = text("SELECT * FROM sync_jobs WHERE job_id = :job_id LIMIT 1")
            result = db.execute(query, {"job_id": job_id})
            row = result.first()
            if row:
                return dict(row._mapping)
            return None
        except Exception as e:
            logger.error(f"Failed to get job {job_id}: {str(e)}")
            return None
        finally:
            if not self.db:  # Only close if we created the session
                db.close()
    
    async def get_user_jobs(
        self,
        user_email: str,
        status: Optional[str] = None,
        limit: int = 50
    ) -> list:
        """Get jobs for a user"""
        db = self._get_db()
        
        try:
            query_str = "SELECT * FROM sync_jobs WHERE user_email = :user_email"
            params = {"user_email": user_email, "limit": limit}
            
            if status:
                query_str += " AND status = :status"
                params["status"] = status
            
            query_str += " ORDER BY created_at DESC LIMIT :limit"
            
            query = text(query_str)
            result = db.execute(query, params)
            return [dict(row._mapping) for row in result]
        except Exception as e:
            logger.error(f"Failed to get user jobs: {str(e)}")
            return []
        finally:
            if not self.db:  # Only close if we created the session
                db.close()
    
    async def get_active_jobs(self, user_email: Optional[str] = None) -> list:
        """Get active (pending or running) jobs only - excludes completed and failed"""
        db = self._get_db()
        
        try:
            query_str = "SELECT * FROM sync_jobs WHERE status IN ('pending', 'running')"
            params = {}
            
            if user_email:
                query_str += " AND user_email = :user_email"
                params["user_email"] = user_email
            
            query_str += " ORDER BY created_at DESC"
            
            query = text(query_str)
            result = db.execute(query, params)
            jobs = [dict(row._mapping) for row in result]
            
            # Double-check: filter out any completed/failed jobs that might have slipped through
            active_jobs = [j for j in jobs if j.get("status") in ["pending", "running"]]
            
            return active_jobs
        except Exception as e:
            logger.error(f"Failed to get active jobs: {str(e)}")
            return []
        finally:
            if not self.db:  # Only close if we created the session
                db.close()
    
    def is_cancelled(self, job_id: str) -> bool:
        """Check if a job has been cancelled"""
        return job_id in self.cancelled_jobs
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job"""
        try:
            # Mark as cancelled
            self.cancelled_jobs.add(job_id)
            
            # Update job status in database
            await self.update_job_status(
                job_id=job_id,
                status="cancelled",
                current_step="Cancelled by user"
            )
            
            # Cancel the running task if it exists
            if job_id in self.running_jobs:
                task = self.running_jobs[job_id]
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info(f"Job {job_id} task cancelled")
                finally:
                    if job_id in self.running_jobs:
                        del self.running_jobs[job_id]
            
            # Remove from cancelled set after cleanup
            self.cancelled_jobs.discard(job_id)
            
            logger.info(f"Cancelled sync job {job_id}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling job {job_id}: {str(e)}")
            return False
    
    def run_background_task(self, task_coro, job_id: str):
        """Run a task in the background and track it"""
        async def wrapped_task():
            try:
                await task_coro
            except asyncio.CancelledError:
                logger.info(f"Background task {job_id} was cancelled")
                await self.update_job_status(
                    job_id=job_id,
                    status="cancelled",
                    current_step="Cancelled by user"
                )
            except Exception as e:
                logger.error(f"Background task {job_id} failed: {str(e)}")
                await self.fail_job(job_id, str(e))
            finally:
                # Clean up running job reference
                if job_id in self.running_jobs:
                    del self.running_jobs[job_id]
                if job_id in self.cancelled_jobs:
                    self.cancelled_jobs.discard(job_id)
        
        task = asyncio.create_task(wrapped_task())
        self.running_jobs[job_id] = task
        return task


# Global instance
sync_job_service = SyncJobService()


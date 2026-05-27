from fastapi import APIRouter, Query, Request, Depends
from typing import Optional
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.services.sync_job_service import sync_job_service
from app.services.background_sync import sync_ga4_background
from app.core.error_utils import handle_api_errors
from app.db.database import get_db
from app.api.routes.sync_shared import get_user_for_sync

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/sync/ga4")
@handle_api_errors(context="syncing Google Analytics data")
async def sync_ga4(
    sync_mode: str = Query("complete", description="Sync mode: 'new' (only clients without GA4 data) or 'complete' (all clients with GA4)"),
    client_id: Optional[int] = Query(None, description="Sync GA4 data for specific client ID (if not provided, syncs all clients with GA4 configured)"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD), defaults to 30 days ago if not provided"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD), defaults to today if not provided"),
    sync_realtime: bool = Query(True, description="Whether to sync realtime data"),
    cron: bool = Query(False, description="Set to true for cron jobs to bypass authentication"),
    request: Request = None,
    current_user: dict = Depends(get_user_for_sync),
    db: Session = Depends(get_db)
):
    """
    Start async sync of GA4 data. Returns immediately with job ID. Uses client_id instead of brand_id.
    
    - **sync_mode**: 'new' (only clients without GA4 data) or 'complete' (all clients with GA4)
    - **client_id**: Optional specific client ID to sync. If not provided, syncs all clients with GA4 configured.
    - **start_date**: Optional start date (YYYY-MM-DD). If not provided, defaults to 30 days ago.
    - **end_date**: Optional end date (YYYY-MM-DD). If not provided, defaults to today.
    - **sync_realtime**: Whether to sync realtime data
    """
    if sync_mode not in ["new", "complete"]:
        raise ValueError("sync_mode must be 'new' or 'complete'")
    
    # Validate date format if provided
    if start_date:
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("start_date must be in YYYY-MM-DD format")
    
    if end_date:
        try:
            datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("end_date must be in YYYY-MM-DD format")
    
    # Validate date range
    if start_date and end_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        if start_dt > end_dt:
            raise ValueError("start_date must be before or equal to end_date")
    
    # Create job with database session
    from app.services.sync_job_service import SyncJobService
    sync_job_service_instance = SyncJobService(db=db)
    job_id = await sync_job_service_instance.create_job(
        sync_type="sync_ga4",
        user_id=current_user["id"],
        user_email=current_user["email"],
        parameters={
            "sync_mode": sync_mode,
            "client_id": client_id,
            "start_date": start_date,
            "end_date": end_date,
            "sync_realtime": sync_realtime
        }
    )
    
    # Start background task (will create its own database session)
    sync_job_service.run_background_task(
        sync_ga4_background(job_id, current_user["id"], current_user["email"], sync_mode, client_id, start_date, end_date, sync_realtime, request),
        job_id
    )
    
    return {
        "status": "started",
        "message": "GA4 sync job started. Use the job_id to check status.",
        "job_id": job_id
    }


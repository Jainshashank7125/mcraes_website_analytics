from fastapi import APIRouter, Query, Request, Depends
from typing import Optional
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.services.sync_job_service import sync_job_service
from app.services.background_sync import sync_agency_analytics_background
from app.core.error_utils import handle_api_errors
from app.db.database import get_db
from app.api.routes.sync_shared import get_user_for_sync

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/sync/agency-analytics")
@handle_api_errors(context="syncing Agency Analytics data")
async def sync_agency_analytics(
    sync_mode: str = Query("complete", description="Sync mode: 'new' (only missing campaigns) or 'complete' (all campaigns)"),
    campaign_id: Optional[int] = Query(None, description="Sync specific campaign (if not provided, syncs all campaigns)"),
    auto_match_brands: bool = Query(True, description="Automatically match campaigns to brands by URL"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD) for syncing keyword rankings. If not provided, syncs all historical data."),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD) for syncing keyword rankings. If not provided, syncs all historical data."),
    cron: bool = Query(False, description="Set to true for cron jobs to bypass authentication"),
    request: Request = None,
    current_user: dict = Depends(get_user_for_sync),
    db: Session = Depends(get_db)
):
    """
    Start async sync of Agency Analytics data (campaigns, campaign links, and keyword rankings). 
    Returns immediately with job ID.
    
    - **sync_mode**: 'new' (only missing campaigns) or 'complete' (all campaigns)
    - **campaign_id**: Optional specific campaign ID to sync. If not provided, syncs all campaigns.
    - **auto_match_brands**: Automatically match campaigns to brands by URL
    - **start_date**: Optional start date (YYYY-MM-DD) for filtering keyword rankings. If not provided, syncs all historical data.
    - **end_date**: Optional end date (YYYY-MM-DD) for filtering keyword rankings. If not provided, syncs all historical data.
    
    Note: Date parameters only apply to keyword rankings sync. Campaigns and campaign links are always synced completely.
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
        sync_type="sync_agency_analytics",
        user_id=current_user["id"],
        user_email=current_user["email"],
        parameters={
            "sync_mode": sync_mode,
            "campaign_id": campaign_id,
            "auto_match_brands": auto_match_brands,
            "start_date": start_date,
            "end_date": end_date
        }
    )
    
    # Start background task (will create its own database session)
    sync_job_service.run_background_task(
        sync_agency_analytics_background(job_id, current_user["id"], current_user["email"], sync_mode, campaign_id, auto_match_brands, start_date, end_date, request),
        job_id
    )
    
    return {
        "status": "started",
        "message": "Agency Analytics sync job started. Use the job_id to check status.",
        "job_id": job_id,
        "parameters": {
            "sync_mode": sync_mode,
            "campaign_id": campaign_id,
            "auto_match_brands": auto_match_brands,
            "start_date": start_date,
            "end_date": end_date
        }
    }


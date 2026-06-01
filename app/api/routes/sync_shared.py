from fastapi import APIRouter, Query, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.services.supabase_service import SupabaseService
from app.services.background_sync import (
    sync_all_background,
    sync_ga4_background,
    sync_agency_analytics_background,
)
from app.core.error_utils import handle_api_errors
from app.api.auth_v2 import get_current_user_v2
from app.db.database import get_db
from app.services.sync_job_service import sync_job_service

logger = logging.getLogger(__name__)
router = APIRouter()

# System user dict for cron jobs
SYSTEM_USER = {
    "id": "system",
    "email": "system@mcraes.internal",
    "full_name": "System (Cron Job)"
}

async def get_user_for_sync(
    request: Request,
    cron: bool = Query(False, description="Set to true for cron jobs to bypass authentication"),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> dict:
    """
    Dependency that returns system user if cron=true, otherwise requires authentication.
    This allows cron jobs to bypass authentication while regular API calls still require it.
    """
    if cron:
        logger.info("Cron job detected - using system user")
        return SYSTEM_USER
    
    # For non-cron requests, require authentication
    if not credentials:
        from app.core.exceptions import AuthenticationException
        raise AuthenticationException(
            user_message="Authentication required",
            technical_message="No authentication token provided"
        )
    
    # Use the regular authentication - need to call it properly with db session
    # get_current_user_v2 expects credentials and db as dependencies
    # Since we're calling it from within another dependency, we need to pass both
    return await get_current_user_v2(credentials, db)

@router.get("/sync/check")
async def sync_check():
    """No-auth check that this backend has sync routes (e.g. POST /api/v1/sync/client/:id). Returns 200 if deployed."""
    return {"ok": True, "sync_client_route": True}

@router.get("/sync/status")
@handle_api_errors(context="fetching sync status")
async def sync_status(db: Session = Depends(get_db)):
    """Get sync status from local PostgreSQL database"""
    supabase = SupabaseService(db=db)
    return supabase.get_sync_status_counts()

@router.post("/sync/client/{client_id}")
@handle_api_errors(context="syncing client data")
async def sync_client(
    client_id: int,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD), defaults to 30 days ago"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD), defaults to today"),
    request: Request = None,
    current_user: dict = Depends(get_current_user_v2),
    db: Session = Depends(get_db)
):
    """
    Start async syncs of all configured integrations for a specific client.

    Fires the exact same background jobs used by the individual sync endpoints:
    - GA4   → sync_ga4_background(client_id=<id>)          — same as POST /sync/ga4?client_id=<id>
    - Agency Analytics → sync_agency_analytics_background(campaign_id=<id>)
                         — one job per campaign linked to the client,
                           same as POST /sync/agency-analytics?campaign_id=<id>
    - Scrunch → sync_all_background(brand_id=<id>)          — same as POST /sync/all scoped to the client's brand

    Returns all started job IDs so the frontend can poll each one.
    """
    # Validate dates
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
    if start_date and end_date:
        if datetime.strptime(start_date, "%Y-%m-%d") > datetime.strptime(end_date, "%Y-%m-%d"):
            raise ValueError("start_date must be before or equal to end_date")

    from app.services.sync_job_service import SyncJobService
    from app.services.supabase_service import SupabaseService

    sjs = SyncJobService(db=db)
    supabase = SupabaseService(db=db)

    # Fetch client to determine which integrations are configured
    client = supabase.get_client_by_id(client_id)
    if not client:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")

    client_name = client.get("company_name", f"Client {client_id}")
    ga4_property_id = client.get("ga4_property_id")
    scrunch_brand_id = client.get("scrunch_brand_id")

    # Get campaigns linked to this client
    linked_campaigns = supabase.get_client_campaigns(client_id)
    campaign_ids = [c["id"] for c in linked_campaigns if c.get("id")]

    job_ids = {
        "ga4": None,
        "agency_analytics": [],  # one job per campaign
        "scrunch": None,
    }

    # ── GA4 — exact same as POST /sync/ga4?client_id=<id>&sync_mode=complete ──
    if ga4_property_id:
        ga4_job_id = await sjs.create_job(
            sync_type="sync_ga4",
            user_id=current_user["id"],
            user_email=current_user["email"],
            parameters={"sync_mode": "complete", "client_id": client_id,
                        "start_date": start_date, "end_date": end_date, "sync_realtime": True}
        )
        sync_job_service.run_background_task(
            sync_ga4_background(ga4_job_id, current_user["id"], current_user["email"],
                                "complete", client_id, start_date, end_date, True, request),
            ga4_job_id
        )
        job_ids["ga4"] = ga4_job_id

    # ── Agency Analytics — exact same as POST /sync/agency-analytics?campaign_id=<id> ──
    for cam_id in campaign_ids:
        aa_job_id = await sjs.create_job(
            sync_type="sync_agency_analytics",
            user_id=current_user["id"],
            user_email=current_user["email"],
            parameters={"sync_mode": "complete", "campaign_id": cam_id,
                        "start_date": start_date, "end_date": end_date, "auto_match_brands": True}
        )
        sync_job_service.run_background_task(
            sync_agency_analytics_background(aa_job_id, current_user["id"], current_user["email"],
                                             "complete", cam_id, True, start_date, end_date, request),
            aa_job_id
        )
        job_ids["agency_analytics"].append(aa_job_id)

    # ── Scrunch — exact same as POST /sync/all, scoped to this client's brand ──
    if scrunch_brand_id:
        scrunch_job_id = await sjs.create_job(
            sync_type="sync_all",
            user_id=current_user["id"],
            user_email=current_user["email"],
            parameters={"sync_mode": "complete", "brand_id": scrunch_brand_id,
                        "start_date": start_date, "end_date": end_date}
        )
        sync_job_service.run_background_task(
            sync_all_background(scrunch_job_id, current_user["id"], current_user["email"],
                                "complete", start_date, end_date, request, brand_id=scrunch_brand_id),
            scrunch_job_id
        )
        job_ids["scrunch"] = scrunch_job_id

    # Flatten all job IDs for easy frontend polling
    all_job_ids = [jid for jid in [job_ids["ga4"], job_ids["scrunch"]] if jid]
    all_job_ids += job_ids["agency_analytics"]

    return {
        "status": "started",
        "message": f"Sync started for {client_name} ({len(all_job_ids)} job(s)).",
        "client_id": client_id,
        "client_name": client_name,
        "job_ids": job_ids,           # structured: { ga4, agency_analytics: [], scrunch }
        "all_job_ids": all_job_ids,   # flat list for easy polling
    }


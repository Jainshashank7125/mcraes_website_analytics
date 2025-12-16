from fastapi import APIRouter, Query, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.services.scrunch_client import ScrunchAPIClient
from app.services.supabase_service import SupabaseService
from app.services.ga4_client import GA4APIClient
from app.services.agency_analytics_client import AgencyAnalyticsClient
from app.services.audit_logger import audit_logger
from app.services.sync_job_service import sync_job_service
from app.services.background_sync import (
    sync_all_background,
    sync_ga4_background,
    sync_agency_analytics_background
)
from app.core.config import settings
from app.core.error_utils import handle_api_errors
from app.api.auth_v2 import get_current_user_v2
from app.db.database import get_db
from app.db.models import Brand, Prompt, Response

logger = logging.getLogger(__name__)

router = APIRouter()
ga4_client = GA4APIClient()

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

@router.post("/sync/brands")
@handle_api_errors(context="syncing brands")
async def sync_brands(
    request: Request,
    current_user: dict = Depends(get_current_user_v2),
    db: Session = Depends(get_db)
):
    """Sync brands from Scrunch AI to local PostgreSQL database"""
    from app.db.models import AuditLogAction
    
    client = ScrunchAPIClient()
    supabase = SupabaseService(db=db)
    
    try:
        brands = await client.get_brands()
        count = supabase.upsert_brands(brands)
        
        # Log sync operation
        await audit_logger.log_sync(
            sync_type=AuditLogAction.SYNC_BRANDS,
            user_id=current_user["id"],
            user_email=current_user["email"],
            status="success",
            details={"count": count},
            request=request,
            db=db
        )
        
        return {
            "status": "success",
            "message": f"Synced {count} brands",
            "count": count
        }
    except Exception as e:
        # Log failed sync
        await audit_logger.log_sync(
            sync_type=AuditLogAction.SYNC_BRANDS,
            user_id=current_user["id"],
            user_email=current_user["email"],
            status="error",
            error_message=str(e),
            request=request,
            db=db
        )
        raise

@router.post("/sync/prompts")
@handle_api_errors(context="syncing prompts")
async def sync_prompts(
    brand_id: Optional[int] = Query(None, description="Sync prompts for specific brand ID (if not provided, syncs all brands)"),
    stage: Optional[str] = Query(None, description="Filter by funnel stage"),
    persona_id: Optional[int] = Query(None, description="Filter by persona ID"),
    request: Request = None,
    current_user: dict = Depends(get_current_user_v2),
    db: Session = Depends(get_db)
):
    """Sync prompts from Scrunch AI to local PostgreSQL database for all brands or a specific brand"""
    from app.db.models import AuditLogAction
    
    client = ScrunchAPIClient()
    supabase = SupabaseService(db=db)
    
    try:
        total_count = 0
        brand_results = []
        
        if brand_id:
            # Sync for specific brand
            logger.info(f"Syncing prompts for brand {brand_id}")
            prompts = await client.get_all_prompts_paginated(
                brand_id=brand_id,
                stage=stage,
                persona_id=persona_id
            )
            count = supabase.upsert_prompts(prompts, brand_id=brand_id)
            total_count = count
            brand_results.append({"brand_id": brand_id, "count": count})
        else:
            # Sync for all brands
            logger.info("Syncing prompts for all brands")
            brands = await client.get_brands()
            
            for brand in brands:
                brand_id_val = brand.get("id")
                if not brand_id_val:
                    continue
                
                try:
                    logger.info(f"Syncing prompts for brand {brand_id_val} ({brand.get('name', 'Unknown')})")
                    prompts = await client.get_all_prompts_paginated(
                        brand_id=brand_id_val,
                        stage=stage,
                        persona_id=persona_id
                    )
                    count = supabase.upsert_prompts(prompts, brand_id=brand_id_val)
                    total_count += count
                    brand_results.append({"brand_id": brand_id_val, "brand_name": brand.get("name"), "count": count})
                    logger.info(f"Synced {count} prompts for brand {brand_id_val}")
                except Exception as e:
                    logger.error(f"Error syncing prompts for brand {brand_id_val}: {str(e)}")
                    brand_results.append({"brand_id": brand_id_val, "brand_name": brand.get("name"), "count": 0, "error": str(e)})
        
        # Determine status
        status = "success" if all("error" not in r for r in brand_results) else "partial"
        
        # Log sync operation
        await audit_logger.log_sync(
            sync_type=AuditLogAction.SYNC_PROMPTS,
            user_id=current_user["id"],
            user_email=current_user["email"],
            status=status,
            details={
                "total_count": total_count,
                "brand_count": len(brand_results),
                "brand_id": brand_id,
                "brand_results": brand_results
            },
            request=request,
            db=db
        )
        
        return {
            "status": "success",
            "message": f"Synced {total_count} prompts across {len(brand_results)} brand(s)",
            "total_count": total_count,
            "brand_results": brand_results
        }
    except Exception as e:
        # Log failed sync
        await audit_logger.log_sync(
            sync_type=AuditLogAction.SYNC_PROMPTS,
            user_id=current_user["id"],
            user_email=current_user["email"],
            status="error",
            error_message=str(e),
            details={"brand_id": brand_id},
            request=request,
            db=db
        )
        raise

@router.post("/sync/responses")
@handle_api_errors(context="syncing responses")
async def sync_responses(
    brand_id: Optional[int] = Query(None, description="Sync responses for specific brand ID (if not provided, syncs all brands)"),
    platform: Optional[str] = Query(None, description="Filter by AI platform"),
    prompt_id: Optional[int] = Query(None, description="Filter by prompt ID"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD). If not provided, syncs all historical responses."),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD). If not provided, syncs all historical responses."),
    request: Request = None,
    current_user: dict = Depends(get_current_user_v2),
    db: Session = Depends(get_db)
):
    """
    Sync responses from Scrunch AI to local PostgreSQL database for all brands or a specific brand.
    
    - **brand_id**: Optional specific brand ID to sync. If not provided, syncs all brands.
    - **platform**: Optional filter by AI platform
    - **prompt_id**: Optional filter by prompt ID
    - **start_date**: Optional start date (YYYY-MM-DD). If not provided, syncs all historical responses.
    - **end_date**: Optional end date (YYYY-MM-DD). If not provided, syncs all historical responses.
    """
    from app.db.models import AuditLogAction
    
    client = ScrunchAPIClient()
    supabase = SupabaseService(db=db)
    
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
    
    try:
        total_count = 0
        brand_results = []
        
        if brand_id:
            # Sync for specific brand
            logger.info(f"Syncing responses for brand {brand_id}")
            responses = await client.get_all_responses_paginated(
                brand_id=brand_id,
                platform=platform,
                prompt_id=prompt_id,
                start_date=start_date,
                end_date=end_date
            )
            count = supabase.upsert_responses(responses, brand_id=brand_id)
            total_count = count
            brand_results.append({"brand_id": brand_id, "count": count})
        else:
            # Sync for all brands
            logger.info("Syncing responses for all brands")
            brands = await client.get_brands()
            
            for brand in brands:
                brand_id_val = brand.get("id")
                if not brand_id_val:
                    continue
                
                try:
                    logger.info(f"Syncing responses for brand {brand_id_val} ({brand.get('name', 'Unknown')})")
                    responses = await client.get_all_responses_paginated(
                        brand_id=brand_id_val,
                        platform=platform,
                        prompt_id=prompt_id,
                        start_date=start_date,
                        end_date=end_date
                    )
                    count = supabase.upsert_responses(responses, brand_id=brand_id_val)
                    total_count += count
                    brand_results.append({"brand_id": brand_id_val, "brand_name": brand.get("name"), "count": count})
                    logger.info(f"Synced {count} responses for brand {brand_id_val}")
                except Exception as e:
                    logger.error(f"Error syncing responses for brand {brand_id_val}: {str(e)}")
                    brand_results.append({"brand_id": brand_id_val, "brand_name": brand.get("name"), "count": 0, "error": str(e)})
        
        # Determine status
        status = "success" if all("error" not in r for r in brand_results) else "partial"
        
        # Log sync operation
        await audit_logger.log_sync(
            sync_type=AuditLogAction.SYNC_RESPONSES,
            user_id=current_user["id"],
            user_email=current_user["email"],
            status=status,
            details={
                "total_count": total_count,
                "brand_count": len(brand_results),
                "brand_id": brand_id,
                "platform": platform,
                "start_date": start_date,
                "end_date": end_date,
                "brand_results": brand_results
            },
            request=request,
            db=db
        )
        
        return {
            "status": "success",
            "message": f"Synced {total_count} responses across {len(brand_results)} brand(s)",
            "total_count": total_count,
            "brand_results": brand_results
        }
    except Exception as e:
        # Log failed sync
        await audit_logger.log_sync(
            sync_type=AuditLogAction.SYNC_RESPONSES,
            user_id=current_user["id"],
            user_email=current_user["email"],
            status="error",
            error_message=str(e),
            details={"brand_id": brand_id},
            request=request,
            db=db
        )
        raise

@router.post("/sync/all")
@handle_api_errors(context="syncing all data")
async def sync_all(
    sync_mode: str = Query("complete", description="Sync mode: 'new' (only missing items) or 'complete' (all items)"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD) for syncing responses. If not provided, syncs all historical responses."),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD) for syncing responses. If not provided, syncs all historical responses."),
    cron: bool = Query(False, description="Set to true for cron jobs to bypass authentication"),
    request: Request = None,
    current_user: dict = Depends(get_user_for_sync),
    db: Session = Depends(get_db)
):
    """
    Start async sync of all Scrunch AI data (brands, prompts, and responses). 
    Returns immediately with job ID.
    
    - **sync_mode**: 'new' (only missing items) or 'complete' (all items)
    - **start_date**: Optional start date (YYYY-MM-DD) for filtering responses. If not provided, syncs all historical responses.
    - **end_date**: Optional end date (YYYY-MM-DD) for filtering responses. If not provided, syncs all historical responses.
    
    Note: Date parameters only apply to responses sync. Brands and prompts are always synced completely.
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
        sync_type="sync_all",
        user_id=current_user["id"],
        user_email=current_user["email"],
        parameters={
            "sync_mode": sync_mode,
            "start_date": start_date,
            "end_date": end_date
        }
    )
    
    # Start background task (will create its own database session)
    sync_job_service.run_background_task(
        sync_all_background(job_id, current_user["id"], current_user["email"], sync_mode, start_date, end_date, request),
        job_id
    )
    
    return {
        "status": "started",
        "message": "Sync job started. Use the job_id to check status.",
        "job_id": job_id,
        "parameters": {
            "sync_mode": sync_mode,
            "start_date": start_date,
            "end_date": end_date
        }
    }
@router.get("/sync/status")
@handle_api_errors(context="fetching sync status")
async def sync_status(db: Session = Depends(get_db)):
    """Get sync status from local PostgreSQL database"""
    supabase = SupabaseService(db=db)
    return supabase.get_sync_status_counts()

# =====================================================
# Agency Analytics Sync Endpoints
# =====================================================

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

# =====================================================
# GA4 Sync Endpoints
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
# Note: Removed duplicate sync_status endpoint - using the one above that returns counts

from fastapi import APIRouter, Query, Request, Depends
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
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    request: Request = None,
    current_user: dict = Depends(get_current_user_v2),
    db: Session = Depends(get_db)
):
    """Sync responses from Scrunch AI to local PostgreSQL database for all brands or a specific brand"""
    from app.db.models import AuditLogAction
    
    client = ScrunchAPIClient()
    supabase = SupabaseService(db=db)
    
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
    request: Request = None,
    current_user: dict = Depends(get_current_user_v2),
    db: Session = Depends(get_db)
):
    """Start async sync of all Scrunch AI data. Returns immediately with job ID."""
    if sync_mode not in ["new", "complete"]:
        raise ValueError("sync_mode must be 'new' or 'complete'")
    
    # Create job with database session
    from app.services.sync_job_service import SyncJobService
    sync_job_service_instance = SyncJobService(db=db)
    job_id = await sync_job_service_instance.create_job(
        sync_type="sync_all",
        user_id=current_user["id"],
        user_email=current_user["email"],
        parameters={"sync_mode": sync_mode}
    )
    
    # Start background task (will create its own database session)
    sync_job_service.run_background_task(
        sync_all_background(job_id, current_user["id"], current_user["email"], sync_mode, request),
        job_id
    )
    
    return {
        "status": "started",
        "message": "Sync job started. Use the job_id to check status.",
        "job_id": job_id
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
    request: Request = None,
    current_user: dict = Depends(get_current_user_v2),
    db: Session = Depends(get_db)
):
    """Start async sync of Agency Analytics data. Returns immediately with job ID."""
    if sync_mode not in ["new", "complete"]:
        raise ValueError("sync_mode must be 'new' or 'complete'")
    
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
            "auto_match_brands": auto_match_brands
        }
    )
    
    # Start background task (will create its own database session)
    sync_job_service.run_background_task(
        sync_agency_analytics_background(job_id, current_user["id"], current_user["email"], sync_mode, campaign_id, auto_match_brands, request),
        job_id
    )
    
    return {
        "status": "started",
        "message": "Agency Analytics sync job started. Use the job_id to check status.",
        "job_id": job_id
    }

# =====================================================
# GA4 Sync Endpoints
@router.post("/sync/ga4")
@handle_api_errors(context="syncing Google Analytics data")
async def sync_ga4(
    sync_mode: str = Query("complete", description="Sync mode: 'new' (only clients without GA4 data) or 'complete' (all clients with GA4)"),
    client_id: Optional[int] = Query(None, description="Sync GA4 data for specific client ID (if not provided, syncs all clients with GA4 configured)"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD), defaults to 30 days ago"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD), defaults to today"),
    sync_realtime: bool = Query(True, description="Whether to sync realtime data"),
    request: Request = None,
    current_user: dict = Depends(get_current_user_v2),
    db: Session = Depends(get_db)
):
    """Start async sync of GA4 data. Returns immediately with job ID. Now uses client_id instead of brand_id."""
    if sync_mode not in ["new", "complete"]:
        raise ValueError("sync_mode must be 'new' or 'complete'")
    
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

from fastapi import APIRouter, Query, Request, Depends
from typing import Optional
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.services.scrunch_client import ScrunchAPIClient
from app.services.supabase_service import SupabaseService
from app.services.audit_logger import audit_logger
from app.services.sync_job_service import sync_job_service
from app.services.background_sync import sync_all_background
from app.core.error_utils import handle_api_errors
from app.api.auth_v2 import get_current_user_v2
from app.db.database import get_db
from app.api.routes.sync_shared import get_user_for_sync

logger = logging.getLogger(__name__)
router = APIRouter()

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


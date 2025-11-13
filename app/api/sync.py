from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging
from app.services.scrunch_client import ScrunchAPIClient
from app.services.supabase_service import SupabaseService
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/sync/brands")
async def sync_brands():
    """Sync brands from Scrunch AI to Supabase"""
    try:
        client = ScrunchAPIClient()
        supabase = SupabaseService()
        
        brands = await client.get_brands()
        count = supabase.upsert_brands(brands)
        
        return {
            "status": "success",
            "message": f"Synced {count} brands",
            "count": count
        }
    except Exception as e:
        logger.error(f"Error syncing brands: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync/prompts")
async def sync_prompts(
    stage: Optional[str] = Query(None, description="Filter by funnel stage"),
    persona_id: Optional[int] = Query(None, description="Filter by persona ID")
):
    """Sync prompts from Scrunch AI to Supabase"""
    try:
        client = ScrunchAPIClient()
        supabase = SupabaseService()
        
        prompts = await client.get_all_prompts_paginated(
            brand_id=settings.BRAND_ID,
            stage=stage,
            persona_id=persona_id
        )
        count = supabase.upsert_prompts(prompts)
        
        return {
            "status": "success",
            "message": f"Synced {count} prompts",
            "count": count
        }
    except Exception as e:
        logger.error(f"Error syncing prompts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync/responses")
async def sync_responses(
    platform: Optional[str] = Query(None, description="Filter by AI platform"),
    prompt_id: Optional[int] = Query(None, description="Filter by prompt ID"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Sync responses from Scrunch AI to Supabase"""
    try:
        client = ScrunchAPIClient()
        supabase = SupabaseService()
        
        responses = await client.get_all_responses_paginated(
            brand_id=settings.BRAND_ID,
            platform=platform,
            prompt_id=prompt_id,
            start_date=start_date,
            end_date=end_date
        )
        count = supabase.upsert_responses(responses)
        
        # Optionally sync citations separately
        # citations_count = supabase.upsert_citations(responses)
        
        return {
            "status": "success",
            "message": f"Synced {count} responses",
            "count": count
        }
    except Exception as e:
        logger.error(f"Error syncing responses: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync/all")
async def sync_all():
    """Sync all data (brands, prompts, responses) from Scrunch AI to Supabase"""
    try:
        client = ScrunchAPIClient()
        supabase = SupabaseService()
        
        # Sync brands
        brands = await client.get_brands()
        brands_count = supabase.upsert_brands(brands)
        
        # Sync prompts
        prompts = await client.get_all_prompts_paginated(brand_id=settings.BRAND_ID)
        prompts_count = supabase.upsert_prompts(prompts)
        
        # Sync responses
        responses = await client.get_all_responses_paginated(brand_id=settings.BRAND_ID)
        responses_count = supabase.upsert_responses(responses)
        
        return {
            "status": "success",
            "message": "Synced all data",
            "counts": {
                "brands": brands_count,
                "prompts": prompts_count,
                "responses": responses_count
            }
        }
    except Exception as e:
        logger.error(f"Error syncing all data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sync/status")
async def sync_status():
    """Get sync status from database"""
    try:
        supabase = SupabaseService()
        
        # Get counts from database
        brands_result = supabase.client.table("brands").select("id", count="exact").execute()
        prompts_result = supabase.client.table("prompts").select("id", count="exact").execute()
        responses_result = supabase.client.table("responses").select("id", count="exact").execute()
        
        return {
            "brands_count": brands_result.count if hasattr(brands_result, 'count') else 0,
            "prompts_count": prompts_result.count if hasattr(prompts_result, 'count') else 0,
            "responses_count": responses_result.count if hasattr(responses_result, 'count') else 0
        }
    except Exception as e:
        logger.error(f"Error getting sync status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


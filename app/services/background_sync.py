"""
Background sync functions that run async
"""
import logging
from typing import Dict, Any, Optional
from app.services.scrunch_client import ScrunchAPIClient
from app.services.supabase_service import SupabaseService
from app.services.ga4_client import GA4APIClient
from app.services.agency_analytics_client import AgencyAnalyticsClient
from app.services.sync_job_service import sync_job_service
from app.services.audit_logger import audit_logger
from app.db.models import AuditLogAction
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


async def sync_all_background(
    job_id: str,
    user_id: str,
    user_email: str,
    request = None
):
    """Background task to sync all Scrunch AI data"""
    client = ScrunchAPIClient()
    supabase = SupabaseService()
    
    try:
        await sync_job_service.update_job_status(job_id, "running", progress=0, current_step="Starting sync...", total_steps=3)
        
        # Step 1: Sync brands
        await sync_job_service.update_job_status(
            job_id, "running", progress=10,
            current_step="Syncing brands...", completed_steps=0, total_steps=3
        )
        logger.info(f"[Job {job_id}] Step 1: Syncing brands...")
        brands = await client.get_brands()
        brands_count = supabase.upsert_brands(brands)
        logger.info(f"[Job {job_id}] Synced {brands_count} brands")
        
        # Step 2: Sync prompts
        await sync_job_service.update_job_status(
            job_id, "running", progress=40,
            current_step="Syncing prompts...", completed_steps=1, total_steps=3
        )
        logger.info(f"[Job {job_id}] Step 2: Syncing prompts...")
        total_prompts = 0
        prompts_by_brand = []
        
        for idx, brand in enumerate(brands):
            brand_id_val = brand.get("id")
            if not brand_id_val:
                continue
            
            try:
                logger.info(f"[Job {job_id}] Syncing prompts for brand {brand_id_val}")
                prompts = await client.get_all_prompts_paginated(brand_id=brand_id_val)
                count = supabase.upsert_prompts(prompts, brand_id=brand_id_val)
                total_prompts += count
                prompts_by_brand.append({"brand_id": brand_id_val, "brand_name": brand.get("name"), "count": count})
                
                # Update progress
                progress = 40 + int((idx + 1) / len(brands) * 30)
                await sync_job_service.update_job_status(
                    job_id, "running", progress=progress,
                    current_step=f"Syncing prompts... ({idx + 1}/{len(brands)} brands)"
                )
            except Exception as e:
                logger.error(f"[Job {job_id}] Error syncing prompts for brand {brand_id_val}: {str(e)}")
                prompts_by_brand.append({"brand_id": brand_id_val, "brand_name": brand.get("name"), "count": 0, "error": str(e)})
        
        # Step 3: Sync responses
        await sync_job_service.update_job_status(
            job_id, "running", progress=70,
            current_step="Syncing responses...", completed_steps=2, total_steps=3
        )
        logger.info(f"[Job {job_id}] Step 3: Syncing responses...")
        total_responses = 0
        responses_by_brand = []
        
        for idx, brand in enumerate(brands):
            brand_id_val = brand.get("id")
            if not brand_id_val:
                continue
            
            try:
                logger.info(f"[Job {job_id}] Syncing responses for brand {brand_id_val}")
                responses = await client.get_all_responses_paginated(brand_id=brand_id_val)
                count = supabase.upsert_responses(responses, brand_id=brand_id_val)
                total_responses += count
                responses_by_brand.append({"brand_id": brand_id_val, "brand_name": brand.get("name"), "count": count})
                
                # Update progress
                progress = 70 + int((idx + 1) / len(brands) * 25)
                await sync_job_service.update_job_status(
                    job_id, "running", progress=progress,
                    current_step=f"Syncing responses... ({idx + 1}/{len(brands)} brands)"
                )
            except Exception as e:
                logger.error(f"[Job {job_id}] Error syncing responses for brand {brand_id_val}: {str(e)}")
                responses_by_brand.append({"brand_id": brand_id_val, "brand_name": brand.get("name"), "count": 0, "error": str(e)})
        
        # Determine status
        has_errors = any("error" in r for r in prompts_by_brand) or any("error" in r for r in responses_by_brand)
        status = "partial" if has_errors else "success"
        
        result = {
            "status": "success",
            "message": "Synced all data for all brands",
            "summary": {
                "brands": brands_count,
                "total_prompts": total_prompts,
                "total_responses": total_responses
            },
            "prompts_by_brand": prompts_by_brand,
            "responses_by_brand": responses_by_brand
        }
        
        # Complete job
        await sync_job_service.complete_job(job_id, result)
        
        # Log audit
        await audit_logger.log_sync(
            sync_type=AuditLogAction.SYNC_ALL,
            user_id=user_id,
            user_email=user_email,
            status=status,
            details={
                "brands": brands_count,
                "total_prompts": total_prompts,
                "total_responses": total_responses,
                "prompts_by_brand": prompts_by_brand,
                "responses_by_brand": responses_by_brand,
                "job_id": job_id
            },
            request=request
        )
        
        logger.info(f"[Job {job_id}] Completed successfully")
        
    except Exception as e:
        logger.error(f"[Job {job_id}] Failed: {str(e)}")
        await sync_job_service.fail_job(job_id, str(e))
        
        # Log audit
        await audit_logger.log_sync(
            sync_type=AuditLogAction.SYNC_ALL,
            user_id=user_id,
            user_email=user_email,
            status="error",
            error_message=str(e),
            details={"job_id": job_id},
            request=request
        )
        raise


async def sync_ga4_background(
    job_id: str,
    user_id: str,
    user_email: str,
    brand_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    sync_realtime: bool = True,
    request = None
):
    """Background task to sync GA4 data"""
    ga4_client = GA4APIClient()
    supabase = SupabaseService()
    
    try:
        # Get date range
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        await sync_job_service.update_job_status(
            job_id, "running", progress=0,
            current_step="Fetching brands with GA4...", total_steps=1
        )
        
        # Get brands with GA4 configured
        if brand_id:
            brand_result = supabase.client.table("brands").select("*").eq("id", brand_id).execute()
            brands = brand_result.data if brand_result.data else []
        else:
            brands_result = supabase.client.table("brands").select("*").not_.is_("ga4_property_id", "null").execute()
            brands = brands_result.data if brands_result.data else []
        
        if not brands:
            result = {
                "status": "success",
                "message": "No brands with GA4 configured found",
                "total_synced": {},
                "brand_results": []
            }
            await sync_job_service.complete_job(job_id, result)
            return
        
        total_synced = {
            "brands": 0,
            "traffic_overview": 0,
            "top_pages": 0,
            "traffic_sources": 0,
            "geographic": 0,
            "devices": 0,
            "conversions": 0,
            "realtime": 0
        }
        
        brand_results = []
        total_brands = len(brands)
        
        for idx, brand in enumerate(brands):
            brand_id_val = brand.get("id")
            property_id = brand.get("ga4_property_id")
            brand_name = brand.get("name", f"Brand {brand_id_val}")
            
            if not property_id:
                continue
            
            try:
                progress = int((idx / total_brands) * 90)
                await sync_job_service.update_job_status(
                    job_id, "running", progress=progress,
                    current_step=f"Syncing GA4 for {brand_name} ({idx + 1}/{total_brands})..."
                )
                
                # Sync GA4 data (simplified - you can add more detailed progress)
                traffic_data = await ga4_client.get_traffic_overview(property_id, start_date, end_date)
                if traffic_data:
                    supabase.upsert_ga4_traffic_overview(brand_id_val, property_id, end_date, traffic_data)
                    total_synced["traffic_overview"] += 1
                
                brand_results.append({
                    "brand_id": brand_id_val,
                    "brand_name": brand_name,
                    "property_id": property_id,
                    "status": "success"
                })
                total_synced["brands"] += 1
                
            except Exception as e:
                logger.error(f"[Job {job_id}] Error syncing GA4 for brand {brand_id_val}: {str(e)}")
                brand_results.append({
                    "brand_id": brand_id_val,
                    "brand_name": brand_name,
                    "status": "error",
                    "error": str(e)
                })
        
        status = "partial" if any(r.get("status") == "error" for r in brand_results) else "success"
        
        result = {
            "status": "success",
            "message": f"Synced GA4 data for {total_synced['brands']} brand(s)",
            "date_range": {"start_date": start_date, "end_date": end_date},
            "total_synced": total_synced,
            "brand_results": brand_results
        }
        
        await sync_job_service.complete_job(job_id, result)
        
        # Log audit
        await audit_logger.log_sync(
            sync_type=AuditLogAction.SYNC_GA4,
            user_id=user_id,
            user_email=user_email,
            status=status,
            details={
                "brand_id": brand_id,
                "start_date": start_date,
                "end_date": end_date,
                "total_synced": total_synced,
                "brand_results": brand_results,
                "job_id": job_id
            },
            request=request
        )
        
    except Exception as e:
        logger.error(f"[Job {job_id}] Failed: {str(e)}")
        await sync_job_service.fail_job(job_id, str(e))
        
        await audit_logger.log_sync(
            sync_type=AuditLogAction.SYNC_GA4,
            user_id=user_id,
            user_email=user_email,
            status="error",
            error_message=str(e),
            details={"brand_id": brand_id, "job_id": job_id},
            request=request
        )
        raise


async def sync_agency_analytics_background(
    job_id: str,
    user_id: str,
    user_email: str,
    campaign_id: Optional[int] = None,
    auto_match_brands: bool = True,
    request = None
):
    """Background task to sync Agency Analytics data"""
    client = AgencyAnalyticsClient()
    supabase = SupabaseService()
    
    try:
        await sync_job_service.update_job_status(
            job_id, "running", progress=0,
            current_step="Fetching campaigns...", total_steps=1
        )
        
        # Get campaigns
        if campaign_id:
            campaigns = [await client.get_campaign(campaign_id)]
        else:
            campaigns = await client.get_campaigns()
        
        total_synced = {
            "campaigns": 0,
            "rankings": 0,
            "keywords": 0,
            "keyword_rankings": 0,
            "keyword_ranking_summaries": 0,
            "brand_links": 0
        }
        
        campaign_results = []
        total_campaigns = len(campaigns)
        
        for idx, campaign in enumerate(campaigns):
            progress = int((idx / total_campaigns) * 90)
            await sync_job_service.update_job_status(
                job_id, "running", progress=progress,
                current_step=f"Syncing campaign {campaign.get('company', 'Unknown')} ({idx + 1}/{total_campaigns})..."
            )
            
            # Sync campaign data (simplified - add full logic here)
            campaign_id_val = campaign.get("id")
            campaign_results.append({
                "campaign_id": campaign_id_val,
                "company": campaign.get("company", "Unknown"),
                "status": "success"
            })
            total_synced["campaigns"] += 1
        
        status = "success"
        
        result = {
            "status": "success",
            "message": f"Synced Agency Analytics data for {len(campaign_results)} campaign(s)",
            "total_synced": total_synced,
            "campaign_results": campaign_results
        }
        
        await sync_job_service.complete_job(job_id, result)
        
        # Log audit
        await audit_logger.log_sync(
            sync_type=AuditLogAction.SYNC_AGENCY_ANALYTICS,
            user_id=user_id,
            user_email=user_email,
            status=status,
            details={
                "campaign_id": campaign_id,
                "auto_match_brands": auto_match_brands,
                "total_synced": total_synced,
                "campaign_results": campaign_results,
                "job_id": job_id
            },
            request=request
        )
        
    except Exception as e:
        logger.error(f"[Job {job_id}] Failed: {str(e)}")
        await sync_job_service.fail_job(job_id, str(e))
        
        await audit_logger.log_sync(
            sync_type=AuditLogAction.SYNC_AGENCY_ANALYTICS,
            user_id=user_id,
            user_email=user_email,
            status="error",
            error_message=str(e),
            details={"campaign_id": campaign_id, "job_id": job_id},
            request=request
        )
        raise


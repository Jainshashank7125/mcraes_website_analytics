"""
Background sync for Agency Analytics (campaigns, keywords, rankings)
"""
import logging
from typing import Optional
from app.services.agency_analytics_client import AgencyAnalyticsClient
from app.services.supabase_service import SupabaseService
from app.services.sync_job_service import SyncJobService
from app.services.audit_logger import audit_logger
from app.db.models import AuditLogAction
from app.db.database import SessionLocal

logger = logging.getLogger(__name__)


async def sync_agency_analytics_background(
    job_id: str,
    user_id: str,
    user_email: str,
    sync_mode: str = "complete",
    campaign_id: Optional[int] = None,
    auto_match_brands: bool = True,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    request = None
):
    """Background task to sync Agency Analytics data"""
    # Create database session for background task
    db = SessionLocal()
    sync_job_service = SyncJobService(db=db)
    client = AgencyAnalyticsClient()
    supabase = SupabaseService(db=db)

    try:
        # Check for cancellation before starting
        if sync_job_service.is_cancelled(job_id):
            logger.info(f"[Job {job_id}] Job was cancelled before starting")
            return

        await sync_job_service.update_job_status(
            job_id, "running", progress=0,
            current_step="Fetching all campaigns...", total_steps=1
        )

        # Step 1: Get all campaigns and update them in database first
        logger.info(f"[Job {job_id}] Starting campaign fetch (sync_mode={sync_mode}, campaign_id={campaign_id})")

        if campaign_id:
            logger.info(f"[Job {job_id}] Fetching specific campaign: {campaign_id}")
            campaign = await client.get_campaign(campaign_id)
            campaigns = [campaign] if campaign else []
            logger.info(f"[Job {job_id}] Fetched campaign: {campaign.get('id') if campaign else 'None'}")
        else:
            logger.info(f"[Job {job_id}] Fetching all campaigns from Agency Analytics API...")
            try:
                campaigns = await client.get_all_campaigns()
                logger.info(f"[Job {job_id}] API returned {len(campaigns)} campaigns")
                if len(campaigns) == 0:
                    logger.warning(f"[Job {job_id}] WARNING: API returned 0 campaigns. This may indicate an API issue or authentication problem.")
                    # Log API key status (first 10 chars only for security)
                    from app.core.config import settings
                    api_key_preview = settings.AGENCY_ANALYTICS_API_KEY[:10] + "..." if settings.AGENCY_ANALYTICS_API_KEY else "NOT SET"
                    logger.info(f"[Job {job_id}] API Key status: {api_key_preview} (length: {len(settings.AGENCY_ANALYTICS_API_KEY) if settings.AGENCY_ANALYTICS_API_KEY else 0})")
            except Exception as e:
                logger.error(f"[Job {job_id}] Error fetching campaigns from API: {str(e)}")
                import traceback
                logger.error(f"[Job {job_id}] Traceback: {traceback.format_exc()}")
                await sync_job_service.update_job_status(
                    job_id, "error", progress=0,
                    current_step=f"Error fetching campaigns: {str(e)}"
                )
                raise Exception(f"Failed to fetch campaigns from Agency Analytics API: {str(e)}")

        # Check for cancellation after fetching campaigns
        if sync_job_service.is_cancelled(job_id):
            logger.info(f"[Job {job_id}] Job cancelled after fetching campaigns")
            return

        # Filter out None campaigns
        original_count = len(campaigns)
        campaigns = [c for c in campaigns if c is not None]
        logger.info(f"[Job {job_id}] After filtering None values: {len(campaigns)} campaigns (from {original_count} total)")

        # For "new" mode, filter to only missing campaigns
        if sync_mode == "new" and not campaign_id:
            from app.db.models import AgencyAnalyticsCampaign
            logger.info(f"[Job {job_id}] New mode: Checking for existing campaigns in database...")
            existing_campaign_ids = set(
                db.query(AgencyAnalyticsCampaign.id).all()
            )
            existing_campaign_ids = {row[0] for row in existing_campaign_ids}
            logger.info(f"[Job {job_id}] Found {len(existing_campaign_ids)} existing campaigns in database")
            original_count = len(campaigns)
            campaigns = [c for c in campaigns if c.get("id") not in existing_campaign_ids]
            logger.info(f"[Job {job_id}] New mode: Filtered to {len(campaigns)} new campaigns (out of {original_count} total from API)")

        total_campaigns = len(campaigns)

        if total_campaigns == 0:
            error_msg = "No campaigns found to sync"
            if sync_mode == "new":
                error_msg += " (all campaigns from API already exist in database)"
            elif campaign_id:
                error_msg += f" (campaign {campaign_id} not found or could not be fetched)"
            else:
                error_msg += " (Agency Analytics API returned no campaigns)"

            logger.warning(f"[Job {job_id}] {error_msg}")
            await sync_job_service.update_job_status(
                job_id, "error", progress=0,
                current_step=error_msg
            )
            raise Exception(error_msg)

        # Step 1: Update all campaigns in database
        await sync_job_service.update_job_status(
            job_id, "running", progress=5,
            current_step=f"Updating {total_campaigns} campaigns in database...", total_steps=1
        )

        total_synced = {
            "campaigns": 0,
            "clients": 0,
            "rankings": 0,
            "keywords": 0,
            "keyword_rankings": 0,
            "keyword_ranking_summaries": 0,
            "brand_links": 0
        }

        # Batch upsert all campaigns
        for campaign in campaigns:
            # Check for cancellation before each campaign
            if sync_job_service.is_cancelled(job_id):
                logger.info(f"[Job {job_id}] Job cancelled during campaign upsert")
                return

            try:
                # Upsert campaign
                supabase.upsert_agency_analytics_campaign(campaign)
                total_synced["campaigns"] += 1
            except Exception as e:
                logger.warning(f"Error upserting campaign {campaign.get('id')}: {str(e)}")

        # Step 2: Filter to only active campaigns and batch create/update clients
        active_campaigns = [c for c in campaigns if c.get("status", "").lower() == "active"]
        active_count = len(active_campaigns)

        logger.info(f"Total campaigns: {total_campaigns}, Active campaigns: {active_count} (mode: {sync_mode})")

        # Batch create/update clients from active campaigns
        if active_campaigns:
            await sync_job_service.update_job_status(
                job_id, "running", progress=10,
                current_step=f"Creating/updating clients from {active_count} active campaigns...", total_steps=1
            )
            try:
                client_results = supabase.upsert_clients_from_campaigns_batch(active_campaigns, user_email)
                total_synced["clients"] = client_results.get("total", 0)
                logger.info(f"Batch processed clients: {client_results.get('created', 0)} created, {client_results.get('updated', 0)} updated, {client_results.get('linked', 0)} campaign links")
            except Exception as client_error:
                logger.error(f"Error batch creating/updating clients: {str(client_error)}")
                # Continue even if client creation fails

        if active_count == 0:
            # Check for cancellation before completing
            if sync_job_service.is_cancelled(job_id):
                logger.info(f"[Job {job_id}] Job was cancelled")
                return
            result = {
                "status": "success",
                "message": f"Updated {total_synced['campaigns']} campaigns. No active campaigns to sync data for.",
                "total_synced": total_synced,
                "campaign_results": []
            }
            await sync_job_service.complete_job(job_id, result)
            return

        campaign_results = []

        # Calculate steps: rankings + keywords + keyword rankings for active campaigns
        total_steps = active_count * 3  # Each active campaign: rankings, keywords, keyword_rankings
        current_step_num = 0

        # Step 3: Fetch data only for active campaigns (in "new" mode, only sync data for new campaigns)
        for idx, campaign in enumerate(active_campaigns):
            # Check for cancellation before each campaign
            if sync_job_service.is_cancelled(job_id):
                logger.info(f"[Job {job_id}] Job cancelled during Agency Analytics data fetch")
                return

            campaign_id_val = campaign.get("id")
            company_name = campaign.get("company", "Unknown")

            try:
                # Collect all data for this campaign before pushing
                campaign_data_batch = {
                    "rankings": [],
                    "keywords": [],
                    "keyword_rankings": [],
                    "keyword_summaries": []
                }

                # Step 3a: Fetch campaign rankings
                current_step_num += 1
                progress = 10 + int((current_step_num / total_steps) * 80)
                date_range_info = f" (date range: {start_date} to {end_date})" if start_date or end_date else ""
                await sync_job_service.update_job_status(
                    job_id, "running", progress=progress,
                    current_step=f"[{idx + 1}/{active_count}] Fetching rankings for: {company_name}{date_range_info}..."
                )

                if sync_job_service.is_cancelled(job_id):
                    logger.info(f"[Job {job_id}] Job cancelled before fetching rankings for {company_name}")
                    return

                rankings = await client.get_campaign_rankings(
                    campaign_id_val,
                    start_date=start_date,
                    end_date=end_date
                )

                if sync_job_service.is_cancelled(job_id):
                    logger.info(f"[Job {job_id}] Job cancelled after fetching rankings for {company_name}")
                    return
                if rankings:
                    try:
                        formatted_rankings = client.format_rankings_data(rankings, campaign)
                        campaign_data_batch["rankings"] = formatted_rankings
                    except Exception as rankings_format_error:
                        import traceback
                        error_trace = traceback.format_exc()
                        logger.error(f"[Job {job_id}] Error formatting rankings for campaign {campaign_id_val} ({company_name}): {str(rankings_format_error)}")
                        logger.error(f"[Job {job_id}] Stack trace:\n{error_trace}")
                        raise

                # Step 3b: Fetch keywords
                current_step_num += 1
                progress = 10 + int((current_step_num / total_steps) * 80)
                await sync_job_service.update_job_status(
                    job_id, "running", progress=progress,
                    current_step=f"[{idx + 1}/{active_count}] Fetching keywords for: {company_name}..."
                )

                if sync_job_service.is_cancelled(job_id):
                    logger.info(f"[Job {job_id}] Job cancelled before fetching keywords for {company_name}")
                    return

                keywords = await client.get_all_campaign_keywords(campaign_id_val)

                if sync_job_service.is_cancelled(job_id):
                    logger.info(f"[Job {job_id}] Job cancelled after fetching keywords for {company_name}")
                    return

                if keywords:
                    try:
                        formatted_keywords = client.format_keywords_data(keywords)
                        campaign_data_batch["keywords"] = formatted_keywords
                    except Exception as keywords_format_error:
                        import traceback
                        error_trace = traceback.format_exc()
                        logger.error(f"[Job {job_id}] Error formatting keywords for campaign {campaign_id_val} ({company_name}): {str(keywords_format_error)}")
                        logger.error(f"[Job {job_id}] Stack trace:\n{error_trace}")
                        logger.error(f"[Job {job_id}] Sample keyword data (first item): {keywords[0] if keywords else 'No keywords'}")
                        raise

                    # Step 3c: Fetch keyword rankings
                    current_step_num += 1
                    progress = 10 + int((current_step_num / total_steps) * 80)
                    await sync_job_service.update_job_status(
                        job_id, "running", progress=progress,
                        current_step=f"[{idx + 1}/{active_count}] Fetching keyword rankings for: {company_name}..."
                    )

                    for keyword in formatted_keywords:
                        # Check for cancellation before each keyword
                        if sync_job_service.is_cancelled(job_id):
                            logger.info(f"[Job {job_id}] Job cancelled during keyword rankings fetch for {company_name}")
                            return

                        keyword_id = keyword.get("id")
                        keyword_phrase = keyword.get("keyword_phrase", "")

                        try:
                            keyword_rankings = await client.get_keyword_rankings(
                                keyword_id,
                                start_date=start_date,
                                end_date=end_date
                            )

                            if sync_job_service.is_cancelled(job_id):
                                logger.info(f"[Job {job_id}] Job cancelled after fetching rankings for keyword {keyword_id}")
                                return

                            if keyword_rankings:
                                logger.debug(f"[Job {job_id}] Fetched {len(keyword_rankings)} ranking records for keyword {keyword_id} ({keyword_phrase})")
                                try:
                                    daily_records, summary = client.format_keyword_rankings_data(
                                        keyword_rankings, keyword_id, campaign_id_val, keyword_phrase
                                    )
                                except Exception as ranking_format_error:
                                    import traceback
                                    error_trace = traceback.format_exc()
                                    logger.error(f"[Job {job_id}] Error formatting keyword rankings for keyword {keyword_id} ({keyword_phrase}) in campaign {campaign_id_val}: {str(ranking_format_error)}")
                                    logger.error(f"[Job {job_id}] Stack trace:\n{error_trace}")
                                    logger.error(f"[Job {job_id}] Sample ranking data (first item): {keyword_rankings[0] if keyword_rankings else 'No rankings'}")
                                    raise

                                if daily_records:
                                    logger.debug(f"[Job {job_id}] Formatted {len(daily_records)} daily records for keyword {keyword_id}")
                                    campaign_data_batch["keyword_rankings"].extend(daily_records)
                                else:
                                    logger.warning(f"[Job {job_id}] No daily records formatted for keyword {keyword_id} despite {len(keyword_rankings)} API results")

                                if summary:
                                    logger.debug(f"[Job {job_id}] Created summary for keyword {keyword_id}")
                                    campaign_data_batch["keyword_summaries"].append(summary)
                                else:
                                    logger.warning(f"[Job {job_id}] No summary created for keyword {keyword_id} despite {len(keyword_rankings)} API results")
                            else:
                                logger.debug(f"[Job {job_id}] No ranking data returned from API for keyword {keyword_id} ({keyword_phrase})")
                        except Exception as keyword_error:
                            logger.warning(f"[Job {job_id}] Error syncing keyword rankings for keyword {keyword_id} ({keyword_phrase}): {str(keyword_error)}")
                            import traceback
                            logger.debug(f"[Job {job_id}] Traceback: {traceback.format_exc()}")
                            continue
                else:
                    # No keywords, but still count as a step
                    current_step_num += 1

                # Step 4: Push all data for this campaign at once
                await sync_job_service.update_job_status(
                    job_id, "running", progress=10 + int((current_step_num / total_steps) * 80),
                    current_step=f"[{idx + 1}/{active_count}] Saving data for: {company_name}..."
                )

                # Batch upsert all data for this campaign
                if campaign_data_batch["rankings"]:
                    count = supabase.upsert_agency_analytics_rankings(campaign_data_batch["rankings"])
                    total_synced["rankings"] += count

                if campaign_data_batch["keywords"]:
                    count = supabase.upsert_agency_analytics_keywords(campaign_data_batch["keywords"])
                    total_synced["keywords"] += count

                if campaign_data_batch["keyword_rankings"]:
                    logger.info(f"[Job {job_id}] Upserting {len(campaign_data_batch['keyword_rankings'])} keyword ranking records for campaign {campaign_id_val}")
                    count = supabase.upsert_agency_analytics_keyword_rankings(campaign_data_batch["keyword_rankings"])
                    total_synced["keyword_rankings"] += count
                    logger.info(f"[Job {job_id}] Successfully upserted {count} keyword ranking records")
                else:
                    logger.warning(f"[Job {job_id}] No keyword rankings to upsert for campaign {campaign_id_val}")

                if campaign_data_batch["keyword_summaries"]:
                    logger.info(f"[Job {job_id}] Upserting {len(campaign_data_batch['keyword_summaries'])} keyword ranking summaries for campaign {campaign_id_val}")
                    count = supabase.upsert_agency_analytics_keyword_ranking_summaries_batch(campaign_data_batch["keyword_summaries"])
                    total_synced["keyword_ranking_summaries"] += count
                    logger.info(f"[Job {job_id}] Successfully upserted {count} keyword ranking summaries")
                else:
                    logger.warning(f"[Job {job_id}] No keyword ranking summaries to upsert for campaign {campaign_id_val}")

                campaign_results.append({
                    "campaign_id": campaign_id_val,
                    "company": company_name,
                    "status": "success"
                })

            except Exception as campaign_error:
                import traceback
                error_trace = traceback.format_exc()
                logger.error(f"[Job {job_id}] Error syncing campaign {campaign_id_val} ({company_name}): {str(campaign_error)}")
                logger.error(f"[Job {job_id}] Full stack trace:\n{error_trace}")
                campaign_results.append({
                    "campaign_id": campaign_id_val,
                    "company": company_name,
                    "status": "error",
                    "error": str(campaign_error)
                })
                continue

        # Step 5: Auto-match campaigns to brands
        if auto_match_brands:
            await sync_job_service.update_job_status(
                job_id, "running", progress=90,
                current_step="Auto-matching campaigns to brands..."
            )

            try:
                # Check for cancellation before auto-matching
                if sync_job_service.is_cancelled(job_id):
                    logger.info(f"[Job {job_id}] Job cancelled before auto-matching")
                    return

                # Get all brands
                brands_result = supabase.client.table("brands").select("*").execute()
                brands = brands_result.data if hasattr(brands_result, 'data') else []

                # Get all campaigns
                campaigns_result = supabase.client.table("agency_analytics_campaigns").select("*").execute()
                all_campaigns = campaigns_result.data if hasattr(campaigns_result, 'data') else []

                # Match campaigns to brands
                for campaign in all_campaigns:
                    # Check for cancellation during matching
                    if sync_job_service.is_cancelled(job_id):
                        logger.info(f"[Job {job_id}] Job cancelled during auto-matching")
                        return
                    for brand in brands:
                        match_result = client.match_campaign_to_brand(campaign, brand)
                        if match_result:
                            try:
                                supabase.link_campaign_to_brand(
                                    match_result["campaign_id"],
                                    match_result["brand_id"],
                                    match_result["match_method"],
                                    match_result["match_confidence"]
                                )
                                total_synced["brand_links"] += 1
                            except Exception as link_error:
                                logger.warning(f"Error linking campaign {match_result['campaign_id']} to brand {match_result['brand_id']}: {str(link_error)}")
                                continue
            except Exception as match_error:
                logger.warning(f"Error during auto-matching: {str(match_error)}")

        # Check for cancellation before completing
        if sync_job_service.is_cancelled(job_id):
            logger.info(f"[Job {job_id}] Job was cancelled, not completing")
            return

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
                "job_id": job_id,
                "start_date": start_date,
                "end_date": end_date
            },
            request=request,
            db=db
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
            request=request,
            db=db
        )
        raise
    finally:
        db.close()

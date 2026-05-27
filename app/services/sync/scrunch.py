"""
Background sync for Scrunch AI (brands, prompts, responses)
"""
import logging
from typing import Optional
from app.services.scrunch_client import ScrunchAPIClient
from app.services.supabase_service import SupabaseService
from app.services.sync_job_service import SyncJobService
from app.services.audit_logger import audit_logger
from app.db.models import AuditLogAction
from app.db.database import SessionLocal

logger = logging.getLogger(__name__)


async def sync_all_background(
    job_id: str,
    user_id: str,
    user_email: str,
    sync_mode: str = "complete",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    request = None,
    brand_id: Optional[int] = None,  # When set, scope sync to this single brand only
):
    """Background task to sync all Scrunch AI data.

    When brand_id is provided the sync is scoped to that single brand:
    - Brands step is skipped (brand already exists in DB)
    - Prompts and responses are synced only for brand_id
    This is backward-compatible; existing callers that omit brand_id behave identically.
    """
    # Create database session for background task
    db = SessionLocal()
    sync_job_service = SyncJobService(db=db)
    client = ScrunchAPIClient()
    supabase = SupabaseService(db=db)

    try:
        # Check for cancellation before starting
        if sync_job_service.is_cancelled(job_id):
            logger.info(f"[Job {job_id}] Job was cancelled before starting")
            return

        await sync_job_service.update_job_status(job_id, "running", progress=0, current_step="Starting sync...", total_steps=3)

        # Step 1: Sync brands
        if sync_job_service.is_cancelled(job_id):
            logger.info(f"[Job {job_id}] Job cancelled during brand sync")
            return

        brands_count = 0
        if brand_id:
            # Scoped sync: brand already in DB, skip the brands API call entirely
            logger.info(f"[Job {job_id}] Scoped sync for brand_id={brand_id} — skipping brands step")
            brands = [{"id": brand_id}]
        else:
            await sync_job_service.update_job_status(
                job_id, "running", progress=10,
                current_step="Syncing brands...", completed_steps=0, total_steps=3
            )
            logger.info(f"[Job {job_id}] Step 1: Syncing brands... (mode: {sync_mode})")
            brands = await client.get_brands()

            if sync_job_service.is_cancelled(job_id):
                logger.info(f"[Job {job_id}] Job cancelled after fetching brands")
                return

            # For "new" mode, filter to only missing brands
            if sync_mode == "new":
                from app.db.models import Brand
                existing_brand_ids = set(db.query(Brand.id).all())
                existing_brand_ids = {row[0] for row in existing_brand_ids}
                brands = [b for b in brands if b.get("id") not in existing_brand_ids]
                logger.info(f"[Job {job_id}] New mode: Filtered to {len(brands)} new brands (out of {len(brands) + len(existing_brand_ids)} total)")

            brands_count = supabase.upsert_brands(brands) if brands else 0
            logger.info(f"[Job {job_id}] Synced {brands_count} brands")

        # Step 2: Sync prompts
        await sync_job_service.update_job_status(
            job_id, "running", progress=40,
            current_step="Syncing prompts...", completed_steps=1, total_steps=3
        )
        logger.info(f"[Job {job_id}] Step 2: Syncing prompts... (mode: {sync_mode})")
        total_prompts = 0
        prompts_by_brand = []

        # For "new" mode (full sync), get all brands from DB to sync prompts/responses for all
        brands_to_process = brands
        if sync_mode == "new" and not brand_id:
            from app.db.models import Brand
            all_brands = db.query(Brand).all()
            brands_to_process = [{"id": b.id, "name": b.name} for b in all_brands]
            logger.info(f"[Job {job_id}] New mode: Will sync prompts/responses for all {len(brands_to_process)} existing brands")

        for idx, brand in enumerate(brands_to_process):
            # Check for cancellation before each brand
            if sync_job_service.is_cancelled(job_id):
                logger.info(f"[Job {job_id}] Job cancelled during prompts sync")
                return

            brand_id_val = brand.get("id")
            if not brand_id_val:
                continue

            try:
                logger.info(f"[Job {job_id}] Syncing prompts for brand {brand_id_val}")
                prompts = await client.get_all_prompts_paginated(brand_id=brand_id_val)

                if sync_job_service.is_cancelled(job_id):
                    logger.info(f"[Job {job_id}] Job cancelled after fetching prompts for brand {brand_id_val}")
                    return

                count = supabase.upsert_prompts(prompts, brand_id=brand_id_val)
                total_prompts += count
                prompts_by_brand.append({"brand_id": brand_id_val, "brand_name": brand.get("name"), "count": count})

                # Update progress
                progress = 40 + int((idx + 1) / len(brands_to_process) * 30) if brands_to_process else 40
                await sync_job_service.update_job_status(
                    job_id, "running", progress=progress,
                    current_step=f"Syncing prompts... ({idx + 1}/{len(brands_to_process)} brands)"
                )
            except Exception as e:
                logger.error(f"[Job {job_id}] Error syncing prompts for brand {brand_id_val}: {str(e)}")
                prompts_by_brand.append({"brand_id": brand_id_val, "brand_name": brand.get("name"), "count": 0, "error": str(e)})

        # Step 3: Sync responses
        await sync_job_service.update_job_status(
            job_id, "running", progress=70,
            current_step="Syncing responses...", completed_steps=2, total_steps=3
        )
        logger.info(f"[Job {job_id}] Step 3: Syncing responses... (mode: {sync_mode})")
        total_responses = 0
        responses_by_brand = []

        for idx, brand in enumerate(brands_to_process):
            # Check for cancellation before each brand
            if sync_job_service.is_cancelled(job_id):
                logger.info(f"[Job {job_id}] Job cancelled during responses sync")
                return

            brand_id_val = brand.get("id")
            if not brand_id_val:
                continue

            try:
                logger.info(f"[Job {job_id}] Syncing responses for brand {brand_id_val}" + (f" (date range: {start_date} to {end_date})" if start_date or end_date else ""))
                responses = await client.get_all_responses_paginated(
                    brand_id=brand_id_val,
                    start_date=start_date,
                    end_date=end_date
                )

                if sync_job_service.is_cancelled(job_id):
                    logger.info(f"[Job {job_id}] Job cancelled after fetching responses for brand {brand_id_val}")
                    return

                count = supabase.upsert_responses(responses, brand_id=brand_id_val)
                total_responses += count
                responses_by_brand.append({"brand_id": brand_id_val, "brand_name": brand.get("name"), "count": count})

                # Update progress
                progress = 70 + int((idx + 1) / len(brands_to_process) * 25) if brands_to_process else 70
                await sync_job_service.update_job_status(
                    job_id, "running", progress=progress,
                    current_step=f"Syncing responses... ({idx + 1}/{len(brands_to_process)} brands)"
                )
            except Exception as e:
                logger.error(f"[Job {job_id}] Error syncing responses for brand {brand_id_val}: {str(e)}")
                responses_by_brand.append({"brand_id": brand_id_val, "brand_name": brand.get("name"), "count": 0, "error": str(e)})

        # Check for cancellation before completing
        if sync_job_service.is_cancelled(job_id):
            logger.info(f"[Job {job_id}] Job was cancelled, not completing")
            return

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
                "job_id": job_id,
                "start_date": start_date,
                "end_date": end_date
            },
            request=request,
            db=db
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
            request=request,
            db=db
        )
        raise
    finally:
        db.close()

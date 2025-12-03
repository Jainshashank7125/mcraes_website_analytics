from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import logging
from app.services.supabase_service import SupabaseService
from app.core.config import settings
from app.db.database import get_db
from app.db.models import Prompt, Response
from sqlalchemy.orm import Session
from sqlalchemy import select, update, text

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/database/migrate/add-brand-id")
async def add_brand_id_columns(db: Session = Depends(get_db)):
    """Add brand_id columns to prompts and responses tables via Supabase API"""
    try:
        supabase = SupabaseService(db=db)
        
        # Note: Supabase REST API doesn't support ALTER TABLE directly
        # This endpoint will update existing records with brand_id
        # The columns should be added manually via Supabase SQL Editor first
        # OR we can use RPC if available
        
        return {
            "status": "info",
            "message": "Please add brand_id columns manually via Supabase SQL Editor. Use /database/update-brand-ids to populate existing records.",
            "sql": """
                ALTER TABLE prompts ADD COLUMN IF NOT EXISTS brand_id INTEGER;
                ALTER TABLE responses ADD COLUMN IF NOT EXISTS brand_id INTEGER;
                CREATE INDEX IF NOT EXISTS idx_prompts_brand_id ON prompts(brand_id);
                CREATE INDEX IF NOT EXISTS idx_responses_brand_id ON responses(brand_id);
            """
        }
    except Exception as e:
        logger.error(f"Error in migration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/database/update-brand-ids")
async def update_brand_ids(
    brand_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Update existing prompts and responses with brand_id"""
    try:
        brand_id_to_use = brand_id or settings.BRAND_ID
        
        if not brand_id_to_use:
            raise HTTPException(status_code=400, detail="brand_id is required")
        
        # Update prompts using SQLAlchemy
        prompts_query = select(Prompt.id)
        prompts_result = db.execute(prompts_query)
        prompts = prompts_result.scalars().all()
        
        prompts_updated = 0
        if prompts:
            # Update prompts in batches using SQLAlchemy
            batch_size = 100
            for i in range(0, len(prompts), batch_size):
                batch = prompts[i:i + batch_size]
                try:
                    update_stmt = (
                        update(Prompt)
                        .where(Prompt.id.in_(batch))
                        .values(brand_id=brand_id_to_use)
                    )
                    result = db.execute(update_stmt)
                    prompts_updated += result.rowcount
                except Exception as e:
                    logger.warning(f"Failed to update prompts batch: {e}")
        
        db.commit()
        
        # Update responses using SQLAlchemy
        responses_query = select(Response.id)
        responses_result = db.execute(responses_query)
        responses = responses_result.scalars().all()
        
        responses_updated = 0
        if responses:
            # Update responses in batches using SQLAlchemy
            batch_size = 100
            for i in range(0, len(responses), batch_size):
                batch = responses[i:i + batch_size]
                try:
                    update_stmt = (
                        update(Response)
                        .where(Response.id.in_(batch))
                        .values(brand_id=brand_id_to_use)
                    )
                    result = db.execute(update_stmt)
                    responses_updated += result.rowcount
                except Exception as e:
                    logger.warning(f"Failed to update responses batch: {e}")
        
        db.commit()
        
        return {
            "status": "success",
            "message": f"Updated brand_id for existing records",
            "brand_id": brand_id_to_use,
            "prompts_updated": prompts_updated,
            "responses_updated": responses_updated
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating brand_ids: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/database/verify")
async def verify_database(db: Session = Depends(get_db)):
    """Verify database schema and brand_id columns"""
    try:
        prompts_has_brand_id = True
        responses_has_brand_id = True
        prompts_without_brand_id = 0
        responses_without_brand_id = 0
        
        try:
            # Check prompts - try to select brand_id column
            prompts_query = select(Prompt.id, Prompt.brand_id)
            prompts_result = db.execute(prompts_query)
            prompts_data = prompts_result.all()
            prompts_without_brand_id = sum(1 for p in prompts_data if not p.brand_id)
        except Exception as e:
            logger.warning(f"Error checking prompts: {e}")
            prompts_has_brand_id = False
        
        try:
            # Check responses - try to select brand_id column
            responses_query = select(Response.id, Response.brand_id)
            responses_result = db.execute(responses_query)
            responses_data = responses_result.all()
            responses_without_brand_id = sum(1 for r in responses_data if not r.brand_id)
        except Exception as e:
            logger.warning(f"Error checking responses: {e}")
            responses_has_brand_id = False
        
        return {
            "status": "success",
            "schema": {
                "prompts_has_brand_id": prompts_has_brand_id,
                "responses_has_brand_id": responses_has_brand_id,
                "prompts_without_brand_id": prompts_without_brand_id,
                "responses_without_brand_id": responses_without_brand_id
            },
            "message": "Database verification complete"
        }
    except Exception as e:
        logger.error(f"Error verifying database: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime
from app.services.supabase_service import SupabaseService
from app.api.auth_v2 import get_current_user_v2
from app.db.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/data/agency-analytics/campaigns")
async def get_agency_analytics_campaigns(
    page: Optional[int] = Query(1, description="Page number (1-indexed)"),
    page_size: Optional[int] = Query(50, description="Number of records per page"),
    search: Optional[str] = Query(None, description="Search by company name or URL"),
    current_user: dict = Depends(get_current_user_v2),
    db: Session = Depends(get_db)
):
    """Get Agency Analytics campaigns with pagination and search"""
    try:
        supabase = SupabaseService(db=db)
        
        # Build query using SQLAlchemy Core
        table = supabase._get_table("agency_analytics_campaigns")
        query = select(table)
        
        # Apply search filter if provided
        if search and search.strip():
            search_term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    table.c.company.ilike(search_term),
                    table.c.url.ilike(search_term)
                )
            )
        
        # Get total count
        count_query = select(func.count()).select_from(query.alias())
        total_count = supabase.db.execute(count_query).scalar()
        
        # Order by id descending
        query = query.order_by(table.c.id.desc())
            
            # Apply pagination
        offset = (page - 1) * page_size if page > 0 else 0
        query = query.offset(offset).limit(page_size)
        
        # Execute query
        result = supabase.db.execute(query)
        campaigns = [dict(row._mapping) for row in result]
        
        total_pages = (total_count + page_size - 1) // page_size if page_size > 0 else 0
        
        return {
            "items": campaigns,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    except Exception as e:
        logger.error(f"Error fetching campaigns: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/agency-analytics/campaign/{campaign_id}/rankings")
async def get_campaign_rankings(
    campaign_id: int,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    page: Optional[int] = Query(1, description="Page number (1-indexed)"),
    page_size: Optional[int] = Query(50, description="Number of records per page"),
    db: Session = Depends(get_db)
):
    """Get campaign rankings for a specific campaign with pagination"""
    try:
        supabase = SupabaseService(db=db)
        
        # Build query using SQLAlchemy Core
        rankings_table = supabase._get_table("agency_analytics_campaign_rankings")
        query = select(rankings_table).where(rankings_table.c.campaign_id == campaign_id)
        
        if start_date:
            query = query.where(rankings_table.c.date >= start_date)
        if end_date:
            query = query.where(rankings_table.c.date <= end_date)
        
        # Get total count
        count_query = select(func.count()).select_from(query.alias())
        total_count = supabase.db.execute(count_query).scalar()
        
        # Order by date ascending
        query = query.order_by(rankings_table.c.date.asc())
        
        # Apply pagination
        offset = (page - 1) * page_size if page > 0 else 0
        query = query.offset(offset).limit(page_size)
        
        # Execute query
        result = supabase.db.execute(query)
        rankings = [dict(row._mapping) for row in result]
        
        total_pages = (total_count + page_size - 1) // page_size if page_size > 0 else 0
        
        # Get campaign info using SQLAlchemy Core
        campaigns_table = supabase._get_table("agency_analytics_campaigns")
        campaign_query = select(campaigns_table).where(campaigns_table.c.id == campaign_id).limit(1)
        campaign_result = supabase.db.execute(campaign_query)
        campaign_row = campaign_result.first()
        campaign = dict(campaign_row._mapping) if campaign_row else None
        
        return {
            "campaign": campaign,
            "rankings": rankings,
            "count": len(rankings),
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    except Exception as e:
        logger.error(f"Error fetching campaign rankings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/agency-analytics/rankings")
async def get_all_rankings(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(1000, description="Number of records to return"),
    db: Session = Depends(get_db)
):
    """Get all campaign rankings"""
    try:
        supabase = SupabaseService(db=db)
        
        # Build query using SQLAlchemy Core
        table = supabase._get_table("agency_analytics_campaign_rankings")
        query = select(table)
        
        if start_date:
            query = query.where(table.c.date >= start_date)
        if end_date:
            query = query.where(table.c.date <= end_date)
        
        query = query.order_by(table.c.date.desc()).limit(limit)
        result = supabase.db.execute(query)
        rankings = [dict(row._mapping) for row in result]
        
        return {
            "rankings": rankings,
            "count": len(rankings)
        }
    except Exception as e:
        logger.error(f"Error fetching rankings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/agency-analytics/campaign/{campaign_id}/keywords")
async def get_campaign_keywords(
    campaign_id: int,
    limit: int = Query(1000, description="Number of keywords to return"),
    db: Session = Depends(get_db)
):
    """Get keywords for a specific campaign"""
    try:
        supabase = SupabaseService(db=db)
        
        # Build query using SQLAlchemy Core
        table = supabase._get_table("agency_analytics_keywords")
        query = select(table).where(table.c.campaign_id == campaign_id)
        query = query.order_by(table.c.id.desc()).limit(limit)
        
        result = supabase.db.execute(query)
        keywords = [dict(row._mapping) for row in result]
        
        return {
            "campaign_id": campaign_id,
            "keywords": keywords,
            "count": len(keywords)
        }
    except Exception as e:
        logger.error(f"Error fetching campaign keywords: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/agency-analytics/keywords")
async def get_all_keywords(
    campaign_id: Optional[int] = Query(None, description="Filter by campaign ID"),
    limit: int = Query(1000, description="Number of keywords to return"),
    db: Session = Depends(get_db)
):
    """Get all keywords"""
    try:
        supabase = SupabaseService(db=db)
        
        # Build query using SQLAlchemy Core
        table = supabase._get_table("agency_analytics_keywords")
        query = select(table)
        
        if campaign_id:
            query = query.where(table.c.campaign_id == campaign_id)
        
        query = query.order_by(table.c.id.desc()).limit(limit)
        result = supabase.db.execute(query)
        keywords = [dict(row._mapping) for row in result]
        
        return {
            "keywords": keywords,
            "count": len(keywords)
        }
    except Exception as e:
        logger.error(f"Error fetching keywords: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/agency-analytics/keyword/{keyword_id}/rankings")
async def get_keyword_rankings(
    keyword_id: int,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(1000, description="Number of records to return"),
    db: Session = Depends(get_db)
):
    """Get keyword rankings for a specific keyword"""
    try:
        supabase = SupabaseService(db=db)
        
        # Build query using SQLAlchemy Core
        table = supabase._get_table("agency_analytics_keyword_rankings")
        query = select(table).where(table.c.keyword_id == keyword_id)
        
        if start_date:
            query = query.where(table.c.date >= start_date)
        if end_date:
            query = query.where(table.c.date <= end_date)
        
        query = query.order_by(table.c.date.asc()).limit(limit)
        result = supabase.db.execute(query)
        rankings = [dict(row._mapping) for row in result]
        
        return {
            "keyword_id": keyword_id,
            "rankings": rankings,
            "count": len(rankings)
        }
    except Exception as e:
        logger.error(f"Error fetching keyword rankings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/agency-analytics/keyword/{keyword_id}/ranking-summary")
async def get_keyword_ranking_summary(keyword_id: int, db: Session = Depends(get_db)):
    """Get keyword ranking summary (latest + change)"""
    try:
        supabase = SupabaseService(db=db)
        
        # Build query using SQLAlchemy Core
        table = supabase._get_table("agency_analytics_keyword_ranking_summaries")
        query = select(table).where(table.c.keyword_id == keyword_id).limit(1)
        result = supabase.db.execute(query)
        row = result.first()
        summary = dict(row._mapping) if row else None
        
        return {
            "keyword_id": keyword_id,
            "summary": summary
        }
    except Exception as e:
        logger.error(f"Error fetching keyword ranking summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/agency-analytics/campaign/{campaign_id}/keyword-rankings")
async def get_campaign_keyword_rankings(
    campaign_id: int,
    limit: int = Query(1000, description="Number of records to return"),
    db: Session = Depends(get_db)
):
    """Get all keyword rankings for a campaign"""
    try:
        supabase = SupabaseService(db=db)
        
        # Build query using SQLAlchemy Core
        table = supabase._get_table("agency_analytics_keyword_rankings")
        query = select(table).where(table.c.campaign_id == campaign_id)
        query = query.order_by(table.c.date.desc()).limit(limit)
        result = supabase.db.execute(query)
        rankings = [dict(row._mapping) for row in result]
        
        return {
            "campaign_id": campaign_id,
            "rankings": rankings,
            "count": len(rankings)
        }
    except Exception as e:
        logger.error(f"Error fetching campaign keyword rankings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/agency-analytics/campaign/{campaign_id}/keyword-ranking-summaries")
async def get_campaign_keyword_ranking_summaries(
    campaign_id: int,
    page: Optional[int] = Query(1, description="Page number (1-indexed)"),
    page_size: Optional[int] = Query(50, description="Number of records per page"),
    search: Optional[str] = Query(None, description="Search by keyword phrase"),
    db: Session = Depends(get_db)
):
    """Get keyword ranking summaries for a campaign with pagination and search"""
    try:
        supabase = SupabaseService(db=db)
        
        # Build query using SQLAlchemy Core
        table = supabase._get_table("agency_analytics_keyword_ranking_summaries")
        query = select(table).where(table.c.campaign_id == campaign_id)
        
        # Apply search filter if provided
        if search and search.strip():
            search_term = f"%{search.strip()}%"
            query = query.where(table.c.keyword_phrase.ilike(search_term))
        
        # Get total count
        count_query = select(func.count()).select_from(query.alias())
        total_count = supabase.db.execute(count_query).scalar()
        
        # Apply ordering
        query = query.order_by(table.c.keyword_phrase.asc())
        
        # Apply pagination
        offset = (page - 1) * page_size if page > 0 else 0
        query = query.offset(offset).limit(page_size)
        
        # Execute query
        result = supabase.db.execute(query)
        summaries = [dict(row._mapping) for row in result]
        
        total_pages = (total_count + page_size - 1) // page_size if page_size > 0 else 0
        
        return {
            "campaign_id": campaign_id,
            "summaries": summaries,
            "count": len(summaries),
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    except Exception as e:
        logger.error(f"Error fetching keyword ranking summaries: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/agency-analytics/campaign-brands")
async def get_campaign_brand_links(
    campaign_id: Optional[int] = Query(None, description="Filter by campaign ID"),
    brand_id: Optional[int] = Query(None, description="Filter by brand ID"),
    db: Session = Depends(get_db)
):
    """Get campaign-brand links"""
    try:
        supabase = SupabaseService(db=db)
        links = supabase.get_campaign_brand_links(campaign_id, brand_id)
        
        return {
            "links": links,
            "count": len(links)
        }
    except Exception as e:
        logger.error(f"Error fetching campaign-brand links: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/data/agency-analytics/campaign-brands")
async def create_campaign_brand_link(
    campaign_id: int,
    brand_id: int,
    match_method: str = "manual",
    match_confidence: str = "manual",
    db: Session = Depends(get_db)
):
    """Manually link a campaign to a brand"""
    try:
        supabase = SupabaseService(db=db)
        supabase.link_campaign_to_brand(campaign_id, brand_id, match_method, match_confidence)
        
        return {
            "status": "success",
            "message": f"Linked campaign {campaign_id} to brand {brand_id}"
        }
    except Exception as e:
        logger.error(f"Error linking campaign to brand: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/agency-analytics/brand/{brand_id}/campaigns")
async def get_brand_campaigns(brand_id: int, db: Session = Depends(get_db)):
    """Get all campaigns linked to a brand"""
    try:
        supabase = SupabaseService(db=db)
        
        # Get links for this brand (returns empty list if table doesn't exist)
        links = supabase.get_campaign_brand_links(brand_id=brand_id)
        
        # Get campaign details using SQLAlchemy Core
        campaigns = []
        if links:
            campaign_ids = [link["campaign_id"] for link in links]
            campaigns_table = supabase._get_table("agency_analytics_campaigns")
            query = select(campaigns_table).where(campaigns_table.c.id.in_(campaign_ids))
            result = supabase.db.execute(query)
            
            for row in result:
                try:
                    campaign = dict(row._mapping)
                    # Find matching link info
                    link = next((l for l in links if l["campaign_id"] == campaign["id"]), {})
                    campaign["link_info"] = {
                        "match_method": link.get("match_method"),
                        "match_confidence": link.get("match_confidence")
                    }
                    campaigns.append(campaign)
                except Exception as e:
                    logger.warning(f"Error processing campaign: {str(e)}")
                    continue
        
        return {
            "brand_id": brand_id,
            "campaigns": campaigns,
            "count": len(campaigns)
        }
    except Exception as e:
        logger.error(f"Error fetching brand campaigns: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# =====================================================
# Reporting Dashboard Endpoint
# =====================================================


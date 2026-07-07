from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime, timedelta
from app.services.supabase_service import SupabaseService
from app.services.ga4_client import GA4APIClient
from app.api.auth_v2 import get_current_user_v2
from app.db.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter()
ga4_client = GA4APIClient()

@router.get("/data/ga4/properties")
async def get_ga4_properties():
    """Get all GA4 properties accessible via service account"""
    try:
        properties = await ga4_client.get_account_summaries()
        return {
            "items": properties,
            "count": len(properties)
        }
    except Exception as e:
        logger.error(f"Error fetching GA4 properties: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/ga4/brand/{brand_id}")
async def get_brand_ga4_analytics(
    brand_id: int,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get GA4 analytics for a specific brand (if property ID is configured)"""
    try:
        # Get brand from database using SQLAlchemy
        supabase = SupabaseService(db=db)
        brand = supabase.get_brand_by_id(brand_id)

        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        if not brand.get("ga4_property_id"):
            return {
                "brand_id": brand_id,
                "brand_name": brand.get("name"),
                "ga4_configured": False,
                "message": "No GA4 property ID configured for this brand"
            }
        
        property_id = brand["ga4_property_id"]
        
        # Get comprehensive GA4 analytics with error handling
        analytics = {}
        
        # Set default date range if not provided
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        date_range = {"startDate": start_date, "endDate": end_date}
        
        # Store data when fetched to ensure all data is persisted (use existing supabase instance with db)
        
        try:
            analytics["trafficOverview"] = await ga4_client.get_traffic_overview(property_id, start_date, end_date)
            # Store traffic overview
            if analytics["trafficOverview"]:
                try:
                    supabase.upsert_ga4_traffic_overview(property_id, end_date, analytics["trafficOverview"], brand_id=brand_id)
                except Exception as store_error:
                    logger.warning(f"Error storing traffic overview: {str(store_error)}")
        except Exception as e:
            logger.warning(f"Error fetching traffic overview: {str(e)}")
            analytics["trafficOverview"] = None
        
        try:
            analytics["topPages"] = await ga4_client.get_top_pages(property_id, start_date, end_date, limit=10)
            # Store top pages
            if analytics["topPages"]:
                try:
                    supabase.upsert_ga4_top_pages(property_id, end_date, analytics["topPages"], brand_id=brand_id)
                except Exception as store_error:
                    logger.warning(f"Error storing top pages: {str(store_error)}")
        except Exception as e:
            logger.warning(f"Error fetching top pages: {str(e)}")
            analytics["topPages"] = []
        
        try:
            analytics["trafficSources"] = await ga4_client.get_traffic_sources(property_id, start_date, end_date)
            # Store traffic sources
            if analytics["trafficSources"]:
                try:
                    supabase.upsert_ga4_traffic_sources(property_id, end_date, analytics["trafficSources"], brand_id=brand_id)
                except Exception as store_error:
                    logger.warning(f"Error storing traffic sources: {str(store_error)}")
        except Exception as e:
            logger.warning(f"Error fetching traffic sources: {str(e)}")
            analytics["trafficSources"] = []
        
        try:
            # For display purposes, use aggregated geographic breakdown (not daily)
            geographic_raw = await ga4_client.get_geographic_breakdown(property_id, start_date, end_date, limit=10, include_daily_breakdown=False)
            # Filter out blank or "(not set)" country names
            analytics["geographic"] = [g for g in (geographic_raw or []) if g.get("country") and g.get("country").strip() and g.get("country").strip().lower() not in ['(not set)', 'not set', '']]
            # Store geographic data (only if this is a single-day query)
            if analytics["geographic"] and start_date == end_date:
                try:
                    supabase.upsert_ga4_geographic(property_id, end_date, analytics["geographic"], brand_id=brand_id)
                except Exception as store_error:
                    logger.warning(f"Error storing geographic data: {str(store_error)}")
        except Exception as e:
            logger.warning(f"Error fetching geographic data: {str(e)}")
            analytics["geographic"] = []
        
        try:
            analytics["devices"] = await ga4_client.get_device_breakdown(property_id, start_date, end_date)
            # Store device data
            if analytics["devices"]:
                try:
                    supabase.upsert_ga4_devices(property_id, end_date, analytics["devices"], brand_id=brand_id)
                except Exception as store_error:
                    logger.warning(f"Error storing device data: {str(store_error)}")
        except Exception as e:
            logger.warning(f"Error fetching device data: {str(e)}")
            analytics["devices"] = []
        
        try:
            analytics["conversions"] = await ga4_client.get_conversions(property_id, start_date, end_date)
            # Store conversions
            if analytics["conversions"]:
                try:
                    supabase.upsert_ga4_conversions(property_id, end_date, analytics["conversions"], brand_id=brand_id)
                    # Also store daily conversions summary
                    total_conversions = sum(c.get("count", 0) for c in analytics["conversions"])
                    if total_conversions > 0:
                        supabase.upsert_ga4_daily_conversions(property_id, end_date, total_conversions, brand_id=brand_id)
                except Exception as store_error:
                    logger.warning(f"Error storing conversions: {str(store_error)}")
        except Exception as e:
            logger.warning(f"Error fetching conversions: {str(e)}")
            analytics["conversions"] = []
        
        try:
            analytics["realtime"] = await ga4_client.get_realtime_snapshot(property_id)
            # Store realtime data
            if analytics["realtime"]:
                try:
                    supabase.upsert_ga4_realtime(property_id, analytics["realtime"], brand_id=brand_id)
                except Exception as store_error:
                    logger.warning(f"Error storing realtime data: {str(store_error)}")
        except Exception as e:
            logger.warning(f"Error fetching realtime data: {str(e)}")
            analytics["realtime"] = None
        
        try:
            analytics["propertyDetails"] = await ga4_client.get_property_details(property_id)
            # Store property details
            if analytics["propertyDetails"]:
                try:
                    supabase.upsert_ga4_property_details(property_id, analytics["propertyDetails"], brand_id=brand_id)
                except Exception as store_error:
                    logger.warning(f"Error storing property details: {str(store_error)}")
        except Exception as e:
            logger.warning(f"Error fetching property details: {str(e)}")
            analytics["propertyDetails"] = None
        
        analytics["dateRange"] = date_range
        
        return {
            "brand_id": brand_id,
            "brand_name": brand.get("name"),
            "ga4_configured": True,
            "property_id": property_id,
            "analytics": analytics
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching GA4 analytics for brand {brand_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/ga4/client/{client_id}")
async def get_client_ga4_analytics(
    client_id: int,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get GA4 analytics for a specific client (if property ID is configured)"""
    try:
        # Get client from database using SQLAlchemy
        supabase = SupabaseService(db=db)
        client = supabase.get_client_by_id(client_id)
        
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        if not client.get("ga4_property_id"):
            return {
                "client_id": client_id,
                "client_name": client.get("company_name"),
                "ga4_configured": False,
                "message": "No GA4 property ID configured for this client"
            }
        
        property_id = client["ga4_property_id"]
        
        # Get comprehensive GA4 analytics with error handling
        analytics = {}
        
        # Set default date range if not provided
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        date_range = {"startDate": start_date, "endDate": end_date}
        
        # Store data when fetched to ensure all data is persisted
        scrunch_brand_id = client.get("scrunch_brand_id")  # For backward compatibility
        
        try:
            analytics["trafficOverview"] = await ga4_client.get_traffic_overview(property_id, start_date, end_date)
            # Store traffic overview
            if analytics["trafficOverview"]:
                try:
                    supabase.upsert_ga4_traffic_overview(property_id, end_date, analytics["trafficOverview"], client_id=client_id, brand_id=scrunch_brand_id)
                except Exception as store_error:
                    logger.warning(f"Error storing traffic overview: {str(store_error)}")
        except Exception as e:
            logger.warning(f"Error fetching traffic overview: {str(e)}")
            analytics["trafficOverview"] = None
        
        try:
            analytics["topPages"] = await ga4_client.get_top_pages(property_id, start_date, end_date, limit=10)
            # Store top pages
            if analytics["topPages"]:
                try:
                    supabase.upsert_ga4_top_pages(property_id, end_date, analytics["topPages"], client_id=client_id, brand_id=scrunch_brand_id)
                except Exception as store_error:
                    logger.warning(f"Error storing top pages: {str(store_error)}")
        except Exception as e:
            logger.warning(f"Error fetching top pages: {str(e)}")
            analytics["topPages"] = []
        
        try:
            analytics["trafficSources"] = await ga4_client.get_traffic_sources(property_id, start_date, end_date)
            # Store traffic sources
            if analytics["trafficSources"]:
                try:
                    supabase.upsert_ga4_traffic_sources(property_id, end_date, analytics["trafficSources"], client_id=client_id, brand_id=scrunch_brand_id)
                except Exception as store_error:
                    logger.warning(f"Error storing traffic sources: {str(store_error)}")
        except Exception as e:
            logger.warning(f"Error fetching traffic sources: {str(e)}")
            analytics["trafficSources"] = []
        
        try:
            # For display purposes, use aggregated geographic breakdown (not daily)
            analytics["geographic"] = await ga4_client.get_geographic_breakdown(property_id, start_date, end_date, limit=10, include_daily_breakdown=False)
            # Store geographic data (only if this is a single-day query)
            if analytics["geographic"] and start_date == end_date:
                try:
                    supabase.upsert_ga4_geographic(property_id, end_date, analytics["geographic"], client_id=client_id, brand_id=scrunch_brand_id)
                except Exception as store_error:
                    logger.warning(f"Error storing geographic data: {str(store_error)}")
        except Exception as e:
            logger.warning(f"Error fetching geographic data: {str(e)}")
            analytics["geographic"] = []
        
        try:
            analytics["devices"] = await ga4_client.get_device_breakdown(property_id, start_date, end_date)
            # Store device data
            if analytics["devices"]:
                try:
                    supabase.upsert_ga4_devices(property_id, end_date, analytics["devices"], client_id=client_id, brand_id=scrunch_brand_id)
                except Exception as store_error:
                    logger.warning(f"Error storing device data: {str(store_error)}")
        except Exception as e:
            logger.warning(f"Error fetching device data: {str(e)}")
            analytics["devices"] = []
        
        try:
            analytics["conversions"] = await ga4_client.get_conversions(property_id, start_date, end_date)
            # Store conversions
            if analytics["conversions"]:
                try:
                    supabase.upsert_ga4_conversions(property_id, end_date, analytics["conversions"], client_id=client_id, brand_id=scrunch_brand_id)
                    # Also store daily conversions summary
                    total_conversions = sum(c.get("count", 0) for c in analytics["conversions"])
                    if total_conversions > 0:
                        supabase.upsert_ga4_daily_conversions(property_id, end_date, total_conversions, client_id=client_id, brand_id=scrunch_brand_id)
                except Exception as store_error:
                    logger.warning(f"Error storing conversions: {str(store_error)}")
        except Exception as e:
            logger.warning(f"Error fetching conversions: {str(e)}")
            analytics["conversions"] = []
        
        try:
            analytics["realtime"] = await ga4_client.get_realtime_snapshot(property_id)
            # Store realtime data
            if analytics["realtime"]:
                try:
                    supabase.upsert_ga4_realtime(property_id, analytics["realtime"], client_id=client_id, brand_id=scrunch_brand_id)
                except Exception as store_error:
                    logger.warning(f"Error storing realtime data: {str(store_error)}")
        except Exception as e:
            logger.warning(f"Error fetching realtime data: {str(e)}")
            analytics["realtime"] = None
        
        try:
            analytics["propertyDetails"] = await ga4_client.get_property_details(property_id)
            # Store property details
            if analytics["propertyDetails"]:
                try:
                    supabase.upsert_ga4_property_details(property_id, analytics["propertyDetails"], client_id=client_id, brand_id=scrunch_brand_id)
                except Exception as store_error:
                    logger.warning(f"Error storing property details: {str(store_error)}")
        except Exception as e:
            logger.warning(f"Error fetching property details: {str(e)}")
            analytics["propertyDetails"] = None
        
        analytics["dateRange"] = date_range
        
        return {
            "client_id": client_id,
            "client_name": client.get("company_name"),
            "ga4_configured": True,
            "property_id": property_id,
            "analytics": analytics
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching GA4 analytics for client {client_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/ga4/traffic-overview/{property_id}")
async def get_ga4_traffic_overview(
    property_id: str,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Get traffic overview for a GA4 property"""
    try:
        data = await ga4_client.get_traffic_overview(property_id, start_date, end_date)
        return data
    except Exception as e:
        logger.error(f"Error fetching traffic overview: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/ga4/top-pages/{property_id}")
async def get_ga4_top_pages(
    property_id: str,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(10, description="Number of pages to return")
):
    """Get top performing pages for a GA4 property"""
    try:
        data = await ga4_client.get_top_pages(property_id, start_date, end_date, limit)
        return {"items": data, "count": len(data)}
    except Exception as e:
        logger.error(f"Error fetching top pages: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/ga4/traffic-sources/{property_id}")
async def get_ga4_traffic_sources(
    property_id: str,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Get traffic sources for a GA4 property"""
    try:
        data = await ga4_client.get_traffic_sources(property_id, start_date, end_date)
        return {"items": data, "count": len(data)}
    except Exception as e:
        logger.error(f"Error fetching traffic sources: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/ga4/geographic/{property_id}")
async def get_ga4_geographic(
    property_id: str,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(20, description="Number of countries to return")
):
    """Get geographic breakdown for a GA4 property (aggregated for display)"""
    try:
        # Use aggregated mode for display purposes
        data_raw = await ga4_client.get_geographic_breakdown(property_id, start_date, end_date, limit, include_daily_breakdown=False)
        # Filter out blank or "(not set)" country names
        data = [g for g in (data_raw or []) if g.get("country") and g.get("country").strip() and g.get("country").strip().lower() not in ['(not set)', 'not set', '']]
        return {"items": data, "count": len(data)}
    except Exception as e:
        logger.error(f"Error fetching geographic breakdown: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/ga4/devices/{property_id}")
async def get_ga4_devices(
    property_id: str,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Get device breakdown for a GA4 property"""
    try:
        data = await ga4_client.get_device_breakdown(property_id, start_date, end_date)
        return {"items": data, "count": len(data)}
    except Exception as e:
        logger.error(f"Error fetching device breakdown: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/ga4/realtime/{property_id}")
async def get_ga4_realtime(property_id: str):
    """Get realtime snapshot for a GA4 property"""
    try:
        data = await ga4_client.get_realtime_snapshot(property_id)
        return data
    except Exception as e:
        logger.error(f"Error fetching realtime data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/ga4/brands-with-ga4")
async def get_brands_with_ga4(db: Session = Depends(get_db)):
    """Get all brands that have GA4 property IDs configured"""
    try:
        supabase = SupabaseService(db=db)
        brands = supabase.get_brands_with_ga4()
        
        return {
            "items": brands,
            "count": len(brands)
        }
    except Exception as e:
        logger.error(f"Error fetching brands with GA4: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# =====================================================
# Agency Analytics Data Endpoints
# =====================================================


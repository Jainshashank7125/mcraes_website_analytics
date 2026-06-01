from fastapi import APIRouter, Query, HTTPException, Depends, Request
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime, timedelta, date as date_type, timezone
from app.services.supabase_service import SupabaseService
from app.core.error_utils import handle_api_errors
from app.api.auth_v2 import get_current_user_v2
from app.db.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_, update, case

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/data/brands")
@handle_api_errors(context="fetching brands")
async def get_brands(
    limit: Optional[int] = Query(50, description="Number of records to return"),
    offset: Optional[int] = Query(0, description="Offset for pagination"),
    search: Optional[str] = Query(None, description="Search by brand name"),
    db: Session = Depends(get_db)
):
    """Get brands from database with optional search"""
    supabase = SupabaseService(db=db)
    return supabase.get_brands(limit=limit, offset=offset, search=search)

@router.get("/data/prompts")
@handle_api_errors(context="fetching prompts")
async def get_prompts(
    brand_id: Optional[int] = Query(None, description="Filter by brand ID"),
    client_id: Optional[int] = Query(None, description="Filter by client ID (maps to brand_id via scrunch_brand_id)"),
    stage: Optional[str] = Query(None, description="Filter by funnel stage"),
    persona_id: Optional[int] = Query(None, description="Filter by persona ID"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: Optional[int] = Query(50, description="Number of records to return"),
    offset: Optional[int] = Query(0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """Get prompts from database. Supports both brand_id and client_id (client_id maps to brand_id via scrunch_brand_id)"""
    supabase = SupabaseService(db=db)
    
    # Validate date range if provided
    if start_date and end_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            if start_dt > end_dt:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid date range: start_date ({start_date}) must be before or equal to end_date ({end_date})"
                )
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid date format. Use YYYY-MM-DD. Error: {str(e)}"
            )
    
    # If client_id is provided, get the scrunch_brand_id from the client
    if client_id and not brand_id:
        client = supabase.get_client_by_id(client_id)
        if client and client.get("scrunch_brand_id"):
            brand_id = client["scrunch_brand_id"]
        elif client_id:
            # Client exists but has no scrunch_brand_id, return empty result
            return {
                "items": [],
                "count": 0,
                "total_count": 0
            }
    
    # Use SQLAlchemy method
    return supabase.get_prompts(
        brand_id=brand_id,
        stage=stage,
        persona_id=persona_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )

@router.get("/data/responses")
@handle_api_errors(context="fetching responses")
async def get_responses(
    brand_id: Optional[int] = Query(None, description="Filter by brand ID"),
    client_id: Optional[int] = Query(None, description="Filter by client ID (maps to brand_id via scrunch_brand_id)"),
    platform: Optional[str] = Query(None, description="Filter by AI platform"),
    prompt_id: Optional[int] = Query(None, description="Filter by prompt ID"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: Optional[int] = Query(50, description="Number of records to return"),
    offset: Optional[int] = Query(0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """Get responses from database. Supports both brand_id and client_id (client_id maps to brand_id via scrunch_brand_id)"""
    supabase = SupabaseService(db=db)
    
    # If client_id is provided, get the scrunch_brand_id from the client
    if client_id and not brand_id:
        client = supabase.get_client_by_id(client_id)
        if client and client.get("scrunch_brand_id"):
            brand_id = client["scrunch_brand_id"]
        elif client_id:
            # Client exists but has no scrunch_brand_id, return empty result
            return {
                "items": [],
                "count": 0,
                "total_count": 0
            }
    
    # Use SQLAlchemy method
    return supabase.get_responses(
        brand_id=brand_id,
        platform=platform,
        prompt_id=prompt_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )

def calculate_analytics(responses):
    """Calculate analytics from responses"""
    if not responses:
        return {
            "total_responses": 0,
            "platform_distribution": {},
            "stage_distribution": {},
            "brand_presence": {"present": 0, "absent": 0},
            "brand_sentiment": {"positive": 0, "neutral": 0, "negative": 0, "null": 0},
            "top_competitors": [],
            "top_topics": [],
            "citation_metrics": {"total": 0, "average_per_response": 0},
            "country_distribution": {},
            "persona_distribution": {}
        }
    
    platform_dist = {}
    stage_dist = {}
    brand_present = 0
    brand_absent = 0
    sentiment_dist = {"positive": 0, "neutral": 0, "negative": 0, "null": 0}
    competitors_count = {}
    topics_count = {}
    total_citations = 0
    country_dist = {}
    persona_dist = {}
    
    for response in responses:
        # Platform distribution
        platform = response.get("platform", "unknown")
        platform_dist[platform] = platform_dist.get(platform, 0) + 1
        
        # Stage distribution
        stage = response.get("stage", "unknown")
        stage_dist[stage] = stage_dist.get(stage, 0) + 1
        
        # Brand presence
        if response.get("brand_present"):
            brand_present += 1
        else:
            brand_absent += 1
        
        # Sentiment
        sentiment = response.get("brand_sentiment")
        if sentiment:
            sentiment_lower = sentiment.lower()
            if "positive" in sentiment_lower:
                sentiment_dist["positive"] += 1
            elif "negative" in sentiment_lower:
                sentiment_dist["negative"] += 1
            else:
                sentiment_dist["neutral"] += 1
        else:
            sentiment_dist["null"] += 1
        
        # Competitors
        competitors_present = response.get("competitors_present", [])
        for comp in competitors_present:
            competitors_count[comp] = competitors_count.get(comp, 0) + 1
        
        # Topics
        topics = response.get("key_topics", [])
        for topic in topics:
            topics_count[topic] = topics_count.get(topic, 0) + 1
        
        # Citations
        citations = response.get("citations", [])
        if isinstance(citations, list):
            total_citations += len(citations)
        
        # Country
        country = response.get("country", "unknown")
        country_dist[country] = country_dist.get(country, 0) + 1
        
        # Persona
        persona = response.get("persona_name", "unknown")
        if persona:
            persona_dist[persona] = persona_dist.get(persona, 0) + 1
    
    # Get top competitors
    top_competitors = sorted(competitors_count.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Get top topics
    top_topics = sorted(topics_count.items(), key=lambda x: x[1], reverse=True)[:20]
    
    return {
        "total_responses": len(responses),
        "platform_distribution": platform_dist,
        "stage_distribution": stage_dist,
        "brand_presence": {"present": brand_present, "absent": brand_absent},
        "brand_sentiment": sentiment_dist,
        "top_competitors": [{"name": name, "count": count} for name, count in top_competitors],
        "top_topics": [{"topic": topic, "count": count} for topic, count in top_topics],
        "citation_metrics": {
            "total": total_citations,
            "average_per_response": round(total_citations / len(responses), 2) if responses else 0
        },
        "country_distribution": country_dist,
        "persona_distribution": persona_dist,
        "month_over_month": {
            "top10_prompt_percentage_change": 1.2,
            "search_volume_change": 18.5,
            "visibility_change": 5.8
        }
    }

@router.get("/data/analytics/brands")
async def get_brand_analytics(
    brand_id: Optional[int] = Query(None, description="Filter by brand ID"),
    db: Session = Depends(get_db)
):
    """Get analytics for brands based on responses"""
    try:
        supabase = SupabaseService(db=db)
        
        # Get brands using SQLAlchemy
        brands_result = supabase.get_brands(limit=None, offset=None, search=None)
        brands = brands_result.get("items", [])
        
        # Filter by brand_id if provided
        if brand_id:
            brands = [b for b in brands if b.get("id") == brand_id]
        
        # Get responses filtered by brand_id if provided
        responses_result = supabase.get_responses(
            brand_id=brand_id,
            limit=None,
            offset=None
        )
        responses = responses_result.get("items", [])
        
        # Calculate analytics for each brand
        if brand_id and len(brands) == 1:
            # Single brand analytics
            analytics = calculate_analytics(responses)
            return {
                "brands": [{
                    **brands[0],
                    "analytics": analytics
                }],
                "total_brands": 1,
                "global_analytics": analytics
            }
        else:
            # Multiple brands or no filter - calculate per brand
            brand_analytics = []
            all_responses = responses  # For global analytics if no filter
            
            for brand in brands:
                # Get responses for this brand
                brand_responses_result = supabase.get_responses(
                    brand_id=brand.get("id"),
                    limit=None,
                    offset=None
                )
                brand_responses = brand_responses_result.get("items", [])
                
                # Calculate analytics for this brand
                brand_analytics_data = calculate_analytics(brand_responses)
                
                brand_analytics.append({
                    **brand,
                    "analytics": brand_analytics_data
                })
            
            # Calculate global analytics
            global_analytics = calculate_analytics(all_responses) if all_responses else calculate_analytics([])
            
            return {
                "brands": brand_analytics,
                "total_brands": len(brands),
                "global_analytics": global_analytics
            }
    except Exception as e:
        logger.error(f"Error fetching brand analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# GA4 Analytics Endpoints

@router.get("/data/scrunch/query/{brand_id}")
@handle_api_errors(context="querying Scrunch analytics")
async def query_scrunch_analytics(
    brand_id: int,
    fields: str = Query(..., description="Comma-separated list of fields (dimensions and metrics)"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(50000, description="Maximum number of results"),
    offset: int = Query(0, description="Pagination offset"),
    db: Session = Depends(get_db)
):
    """
    Query Scrunch analytics from local database (not external API)
    
    Available dimensions:
    - prompt_id, prompt
    - date, date_week, date_month
    - source_url, source_type (Brand, Competitor, Other)
    - persona_id, persona_name
    - competitor_id, competitor_name
    - ai_platform (ChatGPT, Perplexity, Google AI Overviews, Meta, Claude)
    - tag
    - branded (boolean)
    - stage (Advice, Awareness, Evaluation, Comparison, Other)
    - prompt_topic (Key Topic)
    - country (2-letter ISO code)
    
    Available metrics:
    - responses (Count)
    - brand_presence_percentage (Average)
    - brand_position_score (Average, 0-100)
    - brand_sentiment_score (Average, 0-100)
    - competitor_presence_percentage (Average) - Requires competitor dimension
    - competitor_position_score (Average, 0-100) - Requires competitor dimension
    - competitor_sentiment_score (Average, 0-100) - Requires competitor dimension
    """
    try:
        from app.db.models import Response
        from sqlalchemy import select, func, and_, case, extract, cast, String
        from datetime import datetime, timedelta
        
        field_list = [f.strip() for f in fields.split(",")]
        
        # Parse date range
        if start_date:
            start_ts = datetime.strptime(start_date, "%Y-%m-%d")
        else:
            start_ts = datetime.now() - timedelta(days=90)
            
        if end_date:
            end_ts = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)
        else:
            end_ts = datetime.now()
        
        # Build base query
        base_conditions = [
            Response.brand_id == brand_id,
            Response.created_at >= start_ts,
            Response.created_at <= end_ts
        ]
        
        # Handle different field combinations
        items = []
        
        # Platform distribution: ai_platform, responses
        if "ai_platform" in field_list and "responses" in field_list:
            platform_query = select(
                Response.platform.label("ai_platform"),
                func.count(Response.id).label("responses")
            ).where(
                and_(*base_conditions)
            ).group_by(Response.platform)
            
            platform_result = db.execute(platform_query).all()
            items.extend([{"ai_platform": r.ai_platform or "Unknown", "responses": r.responses} for r in platform_result])
        
        # Sentiment distribution: brand_sentiment_score, responses
        elif "brand_sentiment_score" in field_list and "responses" in field_list:
            # Map brand_sentiment to numeric score (Positive=80, Mixed=50, Negative=20, None=0)
            sentiment_score_case = case(
                (Response.brand_sentiment == "positive", 80),
                (Response.brand_sentiment == "mixed", 50),
                (Response.brand_sentiment == "negative", 20),
                else_=0
            )
            
            sentiment_query = select(
                sentiment_score_case.label("brand_sentiment_score"),
                func.count(Response.id).label("responses")
            ).where(
                and_(*base_conditions)
            ).group_by(Response.brand_sentiment)
            
            sentiment_result = db.execute(sentiment_query).all()
            items.extend([{"brand_sentiment_score": r.brand_sentiment_score, "responses": r.responses} for r in sentiment_result])
        
        # Position score: brand_position_score
        elif "brand_position_score" in field_list:
            # Map brand_position to numeric score (top=100, middle=50, bottom=0)
            position_score_case = case(
                (Response.brand_position == "top", 100),
                (Response.brand_position == "middle", 50),
                (Response.brand_position == "bottom", 0),
                else_=0
            )
            
            position_query = select(
                func.avg(position_score_case).label("brand_position_score")
            ).where(
                and_(*base_conditions, Response.brand_present == True)
            )
            
            position_result = db.scalar(position_query)
            if position_result is not None:
                items.append({"brand_position_score": round(position_result, 2)})
            else:
                items.append({"brand_position_score": 0})
        
        # Time series: date_week, brand_presence_percentage, responses
        elif "date_week" in field_list and "brand_presence_percentage" in field_list and "responses" in field_list:
            # Extract week start date (Monday)
            week_start = func.date_trunc('week', Response.created_at).label("date_week")
            
            time_series_query = select(
                week_start,
                func.avg(case((Response.brand_present == True, 100), else_=0)).label("brand_presence_percentage"),
                func.count(Response.id).label("responses")
            ).where(
                and_(*base_conditions)
            ).group_by(week_start).order_by(week_start)
            
            time_series_result = db.execute(time_series_query).all()
            items.extend([{
                "date_week": r.date_week.strftime("%Y-%m-%d") if r.date_week else None,
                "brand_presence_percentage": round(r.brand_presence_percentage or 0, 2),
                "responses": r.responses
            } for r in time_series_result])
        
        # Competitor presence: competitor_name, competitor_presence_percentage, responses
        elif "competitor_name" in field_list and "competitor_presence_percentage" in field_list and "responses" in field_list:
            # This requires unnesting competitors_present array - simplified version
            # For now, return empty as this is complex
            items = []
        
        # Apply limit and offset
        if limit and limit > 0:
            items = items[offset:offset + limit]
        
        logger.info(f"Query API: Found {len(items)} items for brand {brand_id} with fields {field_list}")
        
        return {"items": items}
        
    except Exception as e:
        logger.error(f"Error querying Scrunch analytics for brand {brand_id}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error querying Scrunch analytics: {str(e)}")


# Helper functions for prompts analytics
def calculate_presence_metrics(responses):
    """Calculate presence percentage and time series data"""
    if not responses:
        return {
            "presence_percentage": 0,
            "sparkline_data": []
        }
    
    total_responses = len(responses)
    brand_present_count = sum(1 for r in responses if r.get("brand_present", False))
    presence_percentage = (brand_present_count / total_responses * 100) if total_responses > 0 else 0
    
    # Generate sparkline data (group by week)
    sparkline_data = {}
    for response in responses:
        created_at = response.get("created_at")
        if created_at:
            try:
                date_obj = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                week_key = date_obj.strftime("%Y-W%W")
                if week_key not in sparkline_data:
                    sparkline_data[week_key] = {"total": 0, "present": 0}
                sparkline_data[week_key]["total"] += 1
                if response.get("brand_present", False):
                    sparkline_data[week_key]["present"] += 1
            except:
                pass
    
    # Convert to sorted list
    sorted_weeks = sorted(sparkline_data.keys())
    sparkline_list = []
    for week in sorted_weeks:
        week_data = sparkline_data[week]
        week_presence = (week_data["present"] / week_data["total"] * 100) if week_data["total"] > 0 else 0
        sparkline_list.append(week_presence)
    
    return {
        "presence_percentage": round(presence_percentage, 1),
        "sparkline_data": sparkline_list
    }

def calculate_citation_metrics(responses):
    """Calculate citation counts and time series data"""
    if not responses:
        return {
            "total_citations": 0,
            "sparkline_data": []
        }
    
    import json
    total_citations = 0
    json_cache = {}
    
    for response in responses:
        citations = response.get("citations")
        if citations:
            if isinstance(citations, list):
                citation_count = len(citations)
            elif isinstance(citations, str):
                if citations in json_cache:
                    citation_count = json_cache[citations]
                else:
                    try:
                        parsed = json.loads(citations)
                        citation_count = len(parsed) if isinstance(parsed, list) else 0
                        json_cache[citations] = citation_count
                    except:
                        citation_count = 0
            else:
                citation_count = 0
        else:
            citation_count = 0
        total_citations += citation_count
    
    # Generate sparkline data (group by week)
    sparkline_data = {}
    for response in responses:
        created_at = response.get("created_at")
        citations = response.get("citations")
        if created_at:
            try:
                date_obj = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                week_key = date_obj.strftime("%Y-W%W")
                if week_key not in sparkline_data:
                    sparkline_data[week_key] = 0
                
                if citations:
                    if isinstance(citations, list):
                        citation_count = len(citations)
                    elif isinstance(citations, str):
                        if citations in json_cache:
                            citation_count = json_cache[citations]
                        else:
                            try:
                                parsed = json.loads(citations)
                                citation_count = len(parsed) if isinstance(parsed, list) else 0
                                json_cache[citations] = citation_count
                            except:
                                citation_count = 0
                    else:
                        citation_count = 0
                else:
                    citation_count = 0
                
                sparkline_data[week_key] += citation_count
            except:
                pass
    
    # Convert to sorted list
    sorted_weeks = sorted(sparkline_data.keys())
    sparkline_list = [sparkline_data[week] for week in sorted_weeks]
    
    return {
        "total_citations": total_citations,
        "sparkline_data": sparkline_list
    }

def extract_competitors(responses):
    """Aggregate and rank competitors with percentages"""
    if not responses:
        return []
    
    competitors_count = {}
    total_responses_with_competitors = 0
    
    for response in responses:
        competitors_present = response.get("competitors_present", [])
        if competitors_present:
            total_responses_with_competitors += 1
            for comp in competitors_present:
                if comp:
                    competitors_count[comp] = competitors_count.get(comp, 0) + 1
    
    # Calculate percentages
    competitors_list = []
    for comp_name, count in sorted(competitors_count.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_responses_with_competitors * 100) if total_responses_with_competitors > 0 else 0
        competitors_list.append({
            "name": comp_name,
            "count": count,
            "percentage": round(percentage, 1)
        })
    
    return competitors_list[:10]  # Top 10

def calculate_period_change(current_metrics, previous_metrics):
    """Calculate percentage change between periods"""
    if not previous_metrics or previous_metrics == 0:
        return None
    
    if current_metrics == 0:
        return -100.0
    
    change = ((current_metrics - previous_metrics) / previous_metrics) * 100
    return round(change, 1)


@router.get("/data/prompts-analytics")
@handle_api_errors(context="fetching prompts analytics")
async def get_prompts_analytics(
    group_by: str = Query(..., description="Group by: tags, topics, prompt_variants, stage, seed_prompts"),
    client_id: Optional[int] = Query(None, description="Filter by client ID (maps to brand_id via scrunch_brand_id)"),
    slug: Optional[str] = Query(None, description="Filter by slug (maps to brand_id)"),
    search: Optional[str] = Query(None, description="Search term for filtering"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: Optional[int] = Query(50, description="Number of records to return"),
    offset: Optional[int] = Query(0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """Get aggregated prompts and responses analytics by different dimensions"""
    try:
        logger.debug(f"get_prompts_analytics called with: group_by={group_by}, client_id={client_id}, slug={slug}, "
                    f"search={search}, start_date={start_date}, end_date={end_date}, limit={limit}, offset={offset}")
        
        supabase = SupabaseService(db=db)
        brand_id = None
        resolved_client_id = None
        
        # Resolve brand_id from client_id or slug using SQLAlchemy
        if client_id:
            logger.debug(f"Resolving brand_id from client_id: {client_id}")
            client = supabase.get_client_by_id(client_id)
            if not client:
                logger.debug(f"Client not found for client_id: {client_id}")
                raise HTTPException(status_code=404, detail="Client not found")
            resolved_client_id = client_id
            # Prefer scrunch_brand_id; fallback to client.id so we still return data when mapping is missing
            brand_id = client.get("scrunch_brand_id") or client.get("id")
            logger.debug(f"Resolved brand_id={brand_id} from client_id={client_id} (scrunch_brand_id={client.get('scrunch_brand_id')})")
        elif slug:
            logger.debug(f"Resolving brand_id from slug: {slug}")
            # Try client by slug first
            client = supabase.get_client_by_slug(slug)
            if client:
                resolved_client_id = client.get("id")
                brand_id = client.get("scrunch_brand_id") or client.get("id")
                logger.debug(f"Resolved brand_id={brand_id} from client slug={slug} (client_id={resolved_client_id})")
            else:
                # Fall back to brand by slug using SQLAlchemy
                brand = supabase.get_brand_by_slug(slug)
                if brand:
                    brand_id = brand["id"]
                    logger.debug(f"Resolved brand_id={brand_id} from brand slug={slug}")
                else:
                    logger.debug(f"No client or brand found for slug: {slug}")
                    return {
                        "items": [],
                        "count": 0,
                        "total_count": 0
                    }
        
        if not brand_id:
            logger.debug("No brand_id resolved, returning empty result")
            return {
                "items": [],
                "count": 0,
                "total_count": 0
            }
        
        logger.debug(f"Using brand_id={brand_id} for analytics query")
        
        # Get prompts and responses using SQLAlchemy
        from app.db.models import Prompt, Response
        
        # CORRECT FIX: Get responses first to find which prompts have responses in the date range
        # Then include prompts that either were created in range OR have responses in range
        responses_conditions = [Response.brand_id == brand_id]
        if start_date:
            responses_conditions.append(Response.created_at >= datetime.fromisoformat(f"{start_date}T00:00:00+00:00"))
        if end_date:
            responses_conditions.append(Response.created_at <= datetime.fromisoformat(f"{end_date}T23:59:59+00:00"))
        
        # Get prompt_ids from responses in the date range
        responses_query_temp = select(Response.prompt_id).where(and_(*responses_conditions)).distinct()
        responses_temp_result = db.scalars(responses_query_temp).all()
        prompt_ids_from_responses = set([pid for pid in responses_temp_result if pid is not None])
        logger.debug(f"Found {len(prompt_ids_from_responses)} unique prompt_ids from responses in date range")
        
        # Get prompts that either:
        # 1. Were created in the date range, OR
        # 2. Have responses in the date range (correct behavior - show active prompts)
        prompts_conditions = [Prompt.brand_id == brand_id]
        if prompt_ids_from_responses:
            date_conditions = []
            if start_date:
                date_conditions.append(Prompt.created_at >= datetime.fromisoformat(f"{start_date}T00:00:00+00:00"))
            if end_date:
                date_conditions.append(Prompt.created_at <= datetime.fromisoformat(f"{end_date}T23:59:59+00:00"))
            
            if date_conditions:
                prompts_conditions.append(
                    or_(
                        and_(*date_conditions),
                        Prompt.id.in_(list(prompt_ids_from_responses))
                    )
                )
            else:
                prompts_conditions.append(Prompt.id.in_(list(prompt_ids_from_responses)))
        else:
            # No responses, so only get prompts created in date range
            if start_date:
                prompts_conditions.append(Prompt.created_at >= datetime.fromisoformat(f"{start_date}T00:00:00+00:00"))
            if end_date:
                prompts_conditions.append(Prompt.created_at <= datetime.fromisoformat(f"{end_date}T23:59:59+00:00"))
        
        prompts_query = select(Prompt).where(and_(*prompts_conditions))
        prompts_result = db.scalars(prompts_query).all()
        # Convert ORM objects to dicts
        prompts = [
            {
                "id": p.id,
                "brand_id": p.brand_id,
                "text": p.text,
                "stage": p.stage,
                "persona_id": p.persona_id,
                "persona_name": p.persona_name,
                "platforms": p.platforms,
                "tags": p.tags,
                "topics": p.topics,
                "created_at": p.created_at
            }
            for p in prompts_result
        ]
        logger.debug(f"Fetched {len(prompts)} prompts for brand_id={brand_id}")
        
        # Debug: Check sample prompt structure
        if prompts:
            sample_prompt = prompts[0]
            logger.debug(f"Sample prompt keys: {list(sample_prompt.keys())}")
            logger.debug(f"Sample prompt text value: {repr(sample_prompt.get('text', 'NOT_FOUND'))}")
            logger.debug(f"Sample prompt text type: {type(sample_prompt.get('text'))}")
            # Count prompts with text
            prompts_with_text = sum(1 for p in prompts if p.get("text"))
            logger.debug(f"Prompts with non-empty text: {prompts_with_text} out of {len(prompts)}")
        
        responses_conditions = [Response.brand_id == brand_id]
        if start_date:
            responses_conditions.append(Response.created_at >= datetime.fromisoformat(f"{start_date}T00:00:00+00:00"))
        if end_date:
            responses_conditions.append(Response.created_at <= datetime.fromisoformat(f"{end_date}T23:59:59+00:00"))
        
        responses_query = select(Response).where(and_(*responses_conditions))
        responses_result = db.scalars(responses_query).all()
        # Convert ORM objects to dicts
        responses = [
            {
                "id": r.id,
                "brand_id": r.brand_id,
                "prompt_id": r.prompt_id,
                "prompt": r.prompt,
                "response_text": r.response_text,
                "platform": r.platform,
                "country": r.country,
                "persona_id": r.persona_id,
                "persona_name": r.persona_name,
                "stage": r.stage,
                "branded": r.branded,
                "tags": r.tags,
                "key_topics": r.key_topics,
                "brand_present": r.brand_present,
                "brand_sentiment": r.brand_sentiment,
                "brand_position": r.brand_position,
                "competitors_present": r.competitors_present,
                "competitors": r.competitors,
                "created_at": r.created_at,
                "citations": r.citations
            }
            for r in responses_result
        ]
        logger.debug(f"Fetched {len(responses)} responses for brand_id={brand_id}")
        
        # Get previous period data for change calculation
        prev_responses = []
        if start_date and end_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                period_duration = (end_dt - start_dt).days + 1
                prev_end = (start_dt - timedelta(days=1)).strftime("%Y-%m-%d")
                prev_start = (start_dt - timedelta(days=period_duration)).strftime("%Y-%m-%d")
                
                logger.debug(f"Fetching previous period data: prev_start={prev_start}, prev_end={prev_end} (period_duration={period_duration} days)")
                
                prev_responses_query = select(Response).where(
                    and_(
                        Response.brand_id == brand_id,
                        Response.created_at >= datetime.fromisoformat(f"{prev_start}T00:00:00+00:00"),
                        Response.created_at <= datetime.fromisoformat(f"{prev_end}T23:59:59+00:00")
                    )
                )
                prev_responses_result = db.scalars(prev_responses_query).all()
                # Convert ORM objects to dicts
                prev_responses = [
                    {
                        "id": r.id,
                        "brand_id": r.brand_id,
                        "prompt_id": r.prompt_id,
                        "prompt": r.prompt,
                        "response_text": r.response_text,
                        "platform": r.platform,
                        "country": r.country,
                        "persona_id": r.persona_id,
                        "persona_name": r.persona_name,
                        "stage": r.stage,
                        "branded": r.branded,
                        "tags": r.tags,
                        "key_topics": r.key_topics,
                        "brand_present": r.brand_present,
                        "brand_sentiment": r.brand_sentiment,
                        "brand_position": r.brand_position,
                        "competitors_present": r.competitors_present,
                        "competitors": r.competitors,
                        "created_at": r.created_at,
                        "citations": r.citations
                    }
                    for r in prev_responses_result
                ]
                logger.debug(f"Fetched {len(prev_responses)} previous period responses")
            except Exception as e:
                logger.debug(f"Error fetching previous period data: {str(e)}")
                pass
        
        # Group data based on group_by parameter
        grouped_data = {}
        logger.debug(f"Grouping data by: {group_by}")
        
        if group_by == "tags":
            # Group by tags
            for prompt in prompts:
                tags = prompt.get("tags", []) or []
                for tag in tags:
                    if tag:
                        if tag not in grouped_data:
                            grouped_data[tag] = {"prompts": [], "prompt_ids": set()}
                        if prompt["id"] not in grouped_data[tag]["prompt_ids"]:
                            grouped_data[tag]["prompts"].append(prompt)
                            grouped_data[tag]["prompt_ids"].add(prompt["id"])
        
        elif group_by == "topics":
            # Group by topics
            for prompt in prompts:
                topics = prompt.get("topics", []) or []
                for topic in topics:
                    if topic:
                        if topic not in grouped_data:
                            grouped_data[topic] = {"prompts": [], "prompt_ids": set()}
                        if prompt["id"] not in grouped_data[topic]["prompt_ids"]:
                            grouped_data[topic]["prompts"].append(prompt)
                            grouped_data[topic]["prompt_ids"].add(prompt["id"])
        
        elif group_by == "prompt_variants":
            # Group by prompt text + platform + persona
            # First, collect all unique prompt texts and their prompt IDs
            logger.debug(f"Starting prompt_variants grouping with {len(prompts)} prompts and {len(responses)} responses")
            
            # Build a map of prompt_text -> list of prompt_ids with that text
            prompt_text_to_ids = {}
            for prompt in prompts:
                prompt_text = prompt.get("text", "")
                prompt_id = prompt.get("id")
                if prompt_text:
                    if prompt_text not in prompt_text_to_ids:
                        prompt_text_to_ids[prompt_text] = []
                    prompt_text_to_ids[prompt_text].append(prompt_id)
            
            logger.debug(f"Found {len(prompt_text_to_ids)} unique prompt texts")
            
            # Now group responses by prompt_text + platform + persona
            # This ensures all prompts with the same text are grouped together
            for prompt_text, prompt_ids in prompt_text_to_ids.items():
                # Get all responses for any prompt with this text
                text_responses = [r for r in responses if r.get("prompt_id") in prompt_ids]
                
                if not text_responses:
                    # If no responses, still create a variant
                    key = f"{prompt_text}|||unknown|||unknown"
                    if key not in grouped_data:
                        # Find all prompts with this text
                        matching_prompts = [p for p in prompts if p.get("text") == prompt_text]
                        grouped_data[key] = {"prompts": matching_prompts, "prompt_ids": set(prompt_ids)}
                else:
                    # Group by platform + persona combinations
                    variant_map = {}
                    for resp in text_responses:
                        # Normalize None values to "unknown" for consistent grouping
                        platform = resp.get("platform") if resp.get("platform") is not None else "unknown"
                        persona = resp.get("persona_name") if resp.get("persona_name") is not None else "unknown"
                        variant_key = f"{prompt_text}|||{platform}|||{persona}"
                        if variant_key not in variant_map:
                            variant_map[variant_key] = []
                        variant_map[variant_key].append(resp)
                    
                    # Create groups for each variant
                    for variant_key in variant_map:
                        if variant_key not in grouped_data:
                            # Find all prompts with this text
                            matching_prompts = [p for p in prompts if p.get("text") == prompt_text]
                            grouped_data[variant_key] = {"prompts": matching_prompts, "prompt_ids": set(prompt_ids)}
            
            total_responses_in_groups = sum(len([r for r in responses if r.get("prompt_id") in group_info["prompt_ids"]]) for group_info in grouped_data.values())
            logger.debug(f"prompt_variants grouping complete: created {len(grouped_data)} groups, total responses in groups: {total_responses_in_groups}")
        
        elif group_by == "stage":
            # Group by stage
            for prompt in prompts:
                stage = prompt.get("stage") or "Other"
                if stage not in grouped_data:
                    grouped_data[stage] = {"prompts": [], "prompt_ids": set()}
                if prompt["id"] not in grouped_data[stage]["prompt_ids"]:
                    grouped_data[stage]["prompts"].append(prompt)
                    grouped_data[stage]["prompt_ids"].add(prompt["id"])
        
        elif group_by == "seed_prompts":
            # Group by unique prompt text
            logger.debug(f"Starting seed_prompts grouping with {len(prompts)} prompts")
            prompts_without_text = 0
            for prompt in prompts:
                prompt_text = prompt.get("text", "")
                if not prompt_text:
                    prompts_without_text += 1
                    logger.debug(f"Prompt id={prompt.get('id')} has empty text field")
                if prompt_text:
                    if prompt_text not in grouped_data:
                        grouped_data[prompt_text] = {"prompts": [], "prompt_ids": set()}
                    if prompt["id"] not in grouped_data[prompt_text]["prompt_ids"]:
                        grouped_data[prompt_text]["prompts"].append(prompt)
                        grouped_data[prompt_text]["prompt_ids"].add(prompt["id"])
            logger.debug(f"seed_prompts grouping complete: {len(grouped_data)} groups created, {prompts_without_text} prompts without text")
        
        else:
            raise HTTPException(status_code=400, detail=f"Invalid group_by parameter: {group_by}")
        
        logger.debug(f"Grouped data into {len(grouped_data)} groups")
        
        # Calculate metrics for each group
        items = []
        for group_key, group_info in grouped_data.items():
            prompt_ids = list(group_info["prompt_ids"]) if isinstance(group_info["prompt_ids"], set) else [p["id"] for p in group_info["prompts"]]
            
            # For prompt_variants, filter responses by platform and persona
            if group_by == "prompt_variants":
                parts = group_key.split("|||")
                if len(parts) >= 3:
                    prompt_text, platform, persona = parts[0], parts[1], parts[2]
                    
                    # Debug: Check how many responses match prompt_ids before platform/persona filtering
                    responses_matching_prompt_ids = [r for r in responses if r.get("prompt_id") in prompt_ids]
                    logger.debug(f"prompt_variants pre-filter: group_key={group_key[:50]}..., prompt_ids={prompt_ids[:5] if len(prompt_ids) > 5 else prompt_ids} (showing first 5), {len(responses_matching_prompt_ids)} responses match prompt_ids")
                    
                    # Filter responses - normalize None values to "unknown" for comparison (same as grouping)
                    group_responses = [
                        r for r in responses 
                        if r.get("prompt_id") in prompt_ids 
                        and (r.get("platform") if r.get("platform") is not None else "unknown") == platform
                        and (r.get("persona_name") if r.get("persona_name") is not None else "unknown") == persona
                    ]
                    group_prev_responses = [
                        r for r in prev_responses 
                        if r.get("prompt_id") in prompt_ids 
                        and (r.get("platform") if r.get("platform") is not None else "unknown") == platform
                        and (r.get("persona_name") if r.get("persona_name") is not None else "unknown") == persona
                    ]
                    logger.debug(f"prompt_variants filtering: platform={platform}, persona={persona}, found {len(group_responses)} responses after platform/persona filter")
                else:
                    group_responses = [r for r in responses if r.get("prompt_id") in prompt_ids]
                    group_prev_responses = [r for r in prev_responses if r.get("prompt_id") in prompt_ids]
                    logger.debug(f"prompt_variants filtering (invalid key format): prompt_ids={prompt_ids}, found {len(group_responses)} responses")
            else:
                group_responses = [r for r in responses if r.get("prompt_id") in prompt_ids]
                group_prev_responses = [r for r in prev_responses if r.get("prompt_id") in prompt_ids]
            
            # Apply search filter if provided
            if search and search.strip():
                search_lower = search.strip().lower()
                if group_by == "prompt_variants":
                    # Search in prompt text, platform, or persona
                    parts = group_key.split("|||")
                    if len(parts) >= 3:
                        prompt_text, platform, persona = parts[0], parts[1], parts[2]
                        if search_lower not in prompt_text.lower() and search_lower not in platform.lower() and search_lower not in persona.lower():
                            logger.debug(f"Skipping group_key={group_key} (doesn't match search: {search})")
                            continue
                else:
                    if search_lower not in group_key.lower():
                        logger.debug(f"Skipping group_key={group_key} (doesn't match search: {search})")
                        continue
            
            # Calculate metrics
            logger.debug(f"Calculating metrics for group_key={group_key}: {len(group_responses)} responses, {len(group_prev_responses)} prev responses")
            presence_metrics = calculate_presence_metrics(group_responses)
            citation_metrics = calculate_citation_metrics(group_responses)
            competitors = extract_competitors(group_responses)
            
            # Calculate previous period metrics for change
            prev_presence_metrics = calculate_presence_metrics(group_prev_responses)
            prev_citation_metrics = calculate_citation_metrics(group_prev_responses)
            
            presence_change = calculate_period_change(
                presence_metrics["presence_percentage"],
                prev_presence_metrics["presence_percentage"]
            )
            citation_change = calculate_period_change(
                citation_metrics["total_citations"],
                prev_citation_metrics["total_citations"]
            )
            
            # Format group key for display
            display_key = group_key
            if group_by == "prompt_variants":
                parts = group_key.split("|||")
                if len(parts) >= 3:
                    display_key = parts[0]  # Just the prompt text
                    platform = parts[1]
                    persona = parts[2]
                else:
                    platform = "unknown"
                    persona = "unknown"
            else:
                platform = None
                persona = None
            
            item = {
                "key": group_key,
                "display_name": display_key,
                "prompts_count": len(group_info["prompts"]),
                "responses_count": len(group_responses),
                "presence_percentage": presence_metrics["presence_percentage"],
                "presence_sparkline": presence_metrics["sparkline_data"],
                "presence_change": presence_change,
                "citations_count": citation_metrics["total_citations"],
                "citations_sparkline": citation_metrics["sparkline_data"],
                "citations_change": citation_change,
                "competitors": competitors,
                "stage": group_info["prompts"][0].get("stage") if group_info["prompts"] else None
            }
            
            if group_by == "prompt_variants":
                item["platform"] = platform
                item["persona"] = persona
            
            items.append(item)
        
        # Apply search filter for non-variant groups (already filtered above for variants)
        if search and search.strip() and group_by != "prompt_variants":
            search_lower = search.strip().lower()
            items_before_search = len(items)
            items = [item for item in items if search_lower in item["display_name"].lower()]
            logger.debug(f"Applied search filter: {items_before_search} -> {len(items)} items")
        
        # Sort by responses count descending
        items.sort(key=lambda x: x["responses_count"], reverse=True)
        logger.debug(f"Sorted {len(items)} items by responses_count")
        
        # Apply pagination
        total_count = len(items)
        paginated_items = items[offset:offset + limit] if limit else items[offset:]
        logger.debug(f"Applied pagination: offset={offset}, limit={limit}, total_count={total_count}, returning {len(paginated_items)} items")
        
        return {
            "items": paginated_items,
            "count": len(paginated_items),
            "total_count": total_count,
            "group_by": group_by
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching prompts analytics: {str(e)}")
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Traceback: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Error fetching prompts analytics: {str(e)}")


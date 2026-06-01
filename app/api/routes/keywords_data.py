from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime, timedelta, date as date_type
from app.services.supabase_service import SupabaseService
from app.core.error_utils import handle_api_errors
from app.db.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/data/clients/{client_id}/keywords")
@handle_api_errors(context="fetching client keywords")
async def get_client_keywords(
    client_id: int,
    campaign_id: Optional[int] = Query(None, description="Filter by campaign ID"),
    location_country: Optional[str] = Query(None, description="Filter by country code"),
    location_region: Optional[str] = Query(None, description="Filter by region name"),
    location_city: Optional[str] = Query(None, description="Filter by city"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    from_date: Optional[str] = Query(None, alias="from", description="Start date alias (YYYY-MM-DD)"),
    to_date: Optional[str] = Query(None, alias="to", description="End date alias (YYYY-MM-DD)"),
    volume_min: Optional[int] = Query(None, description="Minimum search volume"),
    volume_max: Optional[int] = Query(None, description="Maximum search volume"),
    google_ranking_min: Optional[int] = Query(None, description="Minimum Google ranking"),
    google_ranking_max: Optional[int] = Query(None, description="Maximum Google ranking"),
    bing_ranking_min: Optional[int] = Query(None, description="Minimum Bing ranking"),
    bing_ranking_max: Optional[int] = Query(None, description="Maximum Bing ranking"),
    competition_min: Optional[float] = Query(None, description="Minimum competition score"),
    competition_max: Optional[float] = Query(None, description="Maximum competition score"),
    primary_only: Optional[bool] = Query(None, description="Filter primary keywords only"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    language: Optional[str] = Query(None, description="Filter by language code"),
    search: Optional[str] = Query(None, description="Search keyword phrase"),
    sort_by: Optional[str] = Query("volume", description="Sort field: volume, google_ranking, bing_ranking, keyword_phrase"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc or desc"),
    page: Optional[int] = Query(1, description="Page number (1-indexed)"),
    page_size: Optional[int] = Query(50, description="Items per page"),
    include_zero_volume: Optional[bool] = Query(False, description="Include keywords with zero search volume (e.g. for agency analytics report)"),
    db: Session = Depends(get_db)
):
    """Get keywords for a client with filtering, sorting, and pagination (public access)"""
    try:
        supabase = SupabaseService(db=db)
        
        # Check if client exists using SQLAlchemy
        client = supabase.get_client_by_id(client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Get campaign IDs for this client
        client_campaigns = supabase.get_client_campaigns(client_id)
        campaign_ids = [c.get("id") for c in client_campaigns if c.get("id")]
        
        if not campaign_ids:
            return {
                "keywords": [],
                "pagination": {
                    "total": 0,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": 0
                },
                "summary": {
                    "total_keywords": 0,
                    "google_rankings_count": 0,
                    "google_change_total": 0,
                    "bing_rankings_count": 0,
                    "bing_change_total": 0
                }
            }
        
        # Resolve and validate date range (accept aliases, default last 30 days)
        start_date = start_date or from_date
        end_date = end_date or to_date

        today = datetime.utcnow().date()
        if not end_date:
            end_date = today.isoformat()
        if not start_date:
            start_date = (today - timedelta(days=30)).isoformat()

        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format, expected YYYY-MM-DD")

        if start_dt > end_dt:
            raise HTTPException(status_code=400, detail="start_date cannot be after end_date")

        # Normalize to ISO strings for downstream queries
        start_date = start_dt.isoformat()
        end_date = end_dt.isoformat()
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            if start_dt > end_dt:
                raise HTTPException(status_code=400, detail=f"Invalid date range: start_date ({start_date}) must be before or equal to end_date ({end_date})")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid date format. Use YYYY-MM-DD. Error: {str(e)}")
        
        # Build base query for keywords with joins using SQLAlchemy Core
        keywords_table = supabase._get_table("agency_analytics_keywords")
        campaigns_table = supabase._get_table("agency_analytics_campaigns")
        rankings_table = supabase._get_table("agency_analytics_keyword_rankings")
        
        # Averages from rankings within the date range
        averages_subquery = (
            select(
                rankings_table.c.keyword_id.label("avg_keyword_id"),
                func.avg(rankings_table.c.google_ranking).label("avg_google_ranking"),
                func.avg(rankings_table.c.volume).label("avg_search_volume"),
            )
            .where(
                and_(
                    rankings_table.c.date >= start_date,
                    rankings_table.c.date <= end_date,
                )
            )
            .group_by(rankings_table.c.keyword_id)
            .subquery()
        )
        
        # Build conditions
        conditions = [keywords_table.c.campaign_id.in_(campaign_ids)]
        if campaign_id:
            conditions.append(keywords_table.c.campaign_id == campaign_id)
        if location_country:
            conditions.append(keywords_table.c.search_location_country_code == location_country)
        if location_region:
            conditions.append(keywords_table.c.search_location_region_name == location_region)
        if location_city:
            conditions.append(keywords_table.c.search_location_formatted_name == location_city)
        if primary_only:
            conditions.append(keywords_table.c.primary_keyword == True)
        if language:
            conditions.append(keywords_table.c.search_language == language)
        if search:
            conditions.append(keywords_table.c.keyword_phrase.ilike(f"%{search}%"))
        
        # Get keywords with joins
        query = select(
            keywords_table,
            campaigns_table.c.company,
            averages_subquery.c.avg_google_ranking,
            averages_subquery.c.avg_search_volume
        ).join(
            campaigns_table, keywords_table.c.campaign_id == campaigns_table.c.id, isouter=True
        ).join(
            averages_subquery, keywords_table.c.id == averages_subquery.c.avg_keyword_id, isouter=True
        ).where(and_(*conditions))
        
        # Execute query
        result = db.execute(query)
        keywords_data = []
        for row in result:
            kw_dict = dict(row._mapping)
            kw_dict["average_google_ranking"] = kw_dict.get("avg_google_ranking")
            kw_dict["average_search_volume"] = kw_dict.get("avg_search_volume")
            # Handle the joined data
            if 'company' in kw_dict:
                kw_dict['agency_analytics_campaigns'] = {'company': kw_dict.pop('company')}
            keywords_data.append(kw_dict)
        
        # Process and filter by summary fields (volume, rankings, competition) - using latest ranking per keyword within range
        filtered_keywords = []
        for kw in keywords_data:
            # Latest ranking in range
            ranking_row = supabase.db.execute(
                select(rankings_table)
                .where(
                    and_(
                        rankings_table.c.keyword_id == kw.get("id"),
                        rankings_table.c.date >= start_date,
                        rankings_table.c.date <= end_date,
                    )
                )
                .order_by(rankings_table.c.date.desc())
                .limit(1)
            ).fetchone()
            summary = dict(ranking_row._mapping) if ranking_row else {}
            
            # Apply summary-based filters
            volume = summary.get("volume", 0) or 0
            # Require volume > 0 and not null unless include_zero_volume (e.g. for report view)
            if not include_zero_volume and volume <= 0:
                continue
            google_ranking = summary.get("google_ranking")
            bing_ranking = summary.get("bing_ranking")
            competition = summary.get("competition", 0) or 0  # competition may be null in rankings
            
            if volume_min is not None and volume < volume_min:
                continue
            if volume_max is not None and volume > volume_max:
                continue
            if google_ranking_min is not None and (google_ranking is None or google_ranking < google_ranking_min):
                continue
            if google_ranking_max is not None and (google_ranking is None or google_ranking > google_ranking_max):
                continue
            if bing_ranking_min is not None and (bing_ranking is None or bing_ranking < bing_ranking_min):
                continue
            if bing_ranking_max is not None and (bing_ranking is None or bing_ranking > bing_ranking_max):
                continue
            if competition_min is not None and competition < competition_min:
                continue
            if competition_max is not None and competition > competition_max:
                continue
            
            # Filter by tags if provided
            if tags:
                kw_tags = kw.get("tags", "") or ""
                tag_list = [t.strip().lower() for t in tags.split(",")]
                kw_tag_list = [t.strip().lower() for t in kw_tags.split(",") if t.strip()]
                if not any(tag in kw_tag_list for tag in tag_list):
                    continue
            
            filtered_keywords.append(kw)
        
        # Sort keywords (use latest ranking fetched above)
        reverse_order = sort_order.lower() == "desc"
        if sort_by == "volume":
            filtered_keywords.sort(
                key=lambda x: supabase.db.execute(
                    select(rankings_table.c.volume)
                    .where(
                        and_(
                            rankings_table.c.keyword_id == x.get("id"),
                            rankings_table.c.date >= start_date,
                            rankings_table.c.date <= end_date,
                        )
                    )
                    .order_by(rankings_table.c.date.desc())
                    .limit(1)
                ).scalar() or 0,
                reverse=reverse_order
            )
        elif sort_by == "google_ranking":
            filtered_keywords.sort(
                key=lambda x: supabase.db.execute(
                    select(rankings_table.c.google_ranking)
                    .where(
                        and_(
                            rankings_table.c.keyword_id == x.get("id"),
                            rankings_table.c.date >= start_date,
                            rankings_table.c.date <= end_date,
                        )
                    )
                    .order_by(rankings_table.c.date.desc())
                    .limit(1)
                ).scalar() or 999,
                reverse=not reverse_order  # Lower ranking is better, so reverse logic
            )
        elif sort_by == "bing_ranking":
            filtered_keywords.sort(
                key=lambda x: supabase.db.execute(
                    select(rankings_table.c.bing_ranking)
                    .where(
                        and_(
                            rankings_table.c.keyword_id == x.get("id"),
                            rankings_table.c.date >= start_date,
                            rankings_table.c.date <= end_date,
                        )
                    )
                    .order_by(rankings_table.c.date.desc())
                    .limit(1)
                ).scalar() or 999,
                reverse=not reverse_order
            )
        elif sort_by == "keyword_phrase":
            filtered_keywords.sort(
                key=lambda x: (x.get("keyword_phrase", "") or "").lower(),
                reverse=reverse_order
            )
        
        # Calculate summary KPIs
        total_keywords = len(filtered_keywords)
        google_rankings_count = 0
        google_change_total = 0
        bing_rankings_count = 0
        bing_change_total = 0
        avg_google_list = []
        avg_volume_list = []
        available_locations_set = set()
        
        for kw in filtered_keywords:
            # Latest ranking in range
            ranking_row = supabase.db.execute(
                select(rankings_table)
                .where(
                    and_(
                        rankings_table.c.keyword_id == kw.get("id"),
                        rankings_table.c.date >= start_date,
                        rankings_table.c.date <= end_date,
                    )
                )
                .order_by(rankings_table.c.date.desc())
                .limit(1)
            ).fetchone()
            summary = dict(ranking_row._mapping) if ranking_row else {}
            volume = summary.get("volume", 0) or 0
            loc = kw.get("search_location_formatted_name") or kw.get("search_location") or kw.get("search_location_country_code")
            if loc:
                available_locations_set.add(loc)
            
            if summary.get("google_ranking") is not None:
                google_rankings_count += 1
                change = summary.get("ranking_change", 0) or 0
                if change > 0:  # Positive change means improvement (lower ranking number)
                    google_change_total += change
            if kw.get("average_google_ranking") is not None:
                avg_google_list.append(kw.get("average_google_ranking"))
            if kw.get("average_search_volume") is not None and kw.get("average_search_volume") > 0:
                avg_volume_list.append(kw.get("average_search_volume"))
            elif volume > 0:
                avg_volume_list.append(volume)
            
            if summary.get("bing_ranking") is not None:
                bing_rankings_count += 1
                # Bing change calculation - would need to be added to summaries or calculated
                # For now, we'll use 0 or calculate from historical if needed
        
        # Paginate
        total = len(filtered_keywords)
        offset = (page - 1) * page_size
        paginated_keywords = filtered_keywords[offset:offset + page_size]
        
        # Format response
        formatted_keywords = []
        for kw in paginated_keywords:
            # Get the LATEST ranking within the date range (not average)
            # This query orders by date DESC and limits to 1 to get the most recent ranking
            ranking_row = supabase.db.execute(
                select(rankings_table)
                .where(
                    and_(
                        rankings_table.c.keyword_id == kw.get("id"),
                        rankings_table.c.date >= start_date,
                        rankings_table.c.date <= end_date,
                    )
                )
                .order_by(rankings_table.c.date.desc())
                .limit(1)
            ).fetchone()
            summary = dict(ranking_row._mapping) if ranking_row else {}
            volume = summary.get("volume", 0) or 0
            
            campaign = kw.get("agency_analytics_campaigns")
            if campaign and isinstance(campaign, dict):
                campaign_name = campaign.get("company", "")
            else:
                campaign_name = ""
            
            formatted_keywords.append({
                "keyword_id": kw.get("id"),
                "keyword_phrase": kw.get("keyword_phrase", ""),
                "campaign_id": kw.get("campaign_id"),
                "campaign_name": campaign_name,
                # google_ranking uses the LATEST ranking from the date range, not the average
                "google_ranking": summary.get("google_ranking"),
                "google_ranking_url": summary.get("google_ranking_url"),
                "google_mobile_ranking": summary.get("google_mobile_ranking"),
                "google_local_ranking": summary.get("google_local_ranking"),
                "bing_ranking": summary.get("bing_ranking"),
                "bing_ranking_url": summary.get("bing_ranking_url"),
                "google_change": summary.get("ranking_change", 0) or 0,
                "bing_change": 0,  # Would need to calculate from historical data
                "search_volume": volume,
                "competition": summary.get("competition", 0) or 0,
                "average_google_ranking": kw.get("average_google_ranking"),
                "average_search_volume": kw.get("average_search_volume"),
                "search_location": kw.get("search_location", ""),
                "search_location_formatted_name": kw.get("search_location_formatted_name", ""),
                "search_location_country_code": kw.get("search_location_country_code", ""),
                "search_location_region_name": kw.get("search_location_region_name", ""),
                "search_language": kw.get("search_language", ""),
                "tags": kw.get("tags", ""),
                "primary_keyword": kw.get("primary_keyword", False),
                "last_updated": summary.get("date")
            })
        
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1
        
        return {
            "keywords": formatted_keywords,
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            },
            "summary": {
                "total_keywords": total_keywords,
                "google_rankings_count": google_rankings_count,
                "google_change_total": google_change_total,
                "bing_rankings_count": bing_rankings_count,
                "bing_change_total": bing_change_total,
                "average_google_ranking": round(sum(avg_google_list) / len(avg_google_list), 1) if avg_google_list else 0,
                "average_search_volume": round(sum(avg_volume_list) / len(avg_volume_list), 1) if avg_volume_list else 0,
                "available_locations": sorted(available_locations_set)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching client keywords: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/clients/{client_id}/keywords/rankings-over-time")
@handle_api_errors(context="fetching keyword rankings over time")
async def get_client_keyword_rankings_over_time(
    client_id: int,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    from_date: Optional[str] = Query(None, alias="from", description="Start date alias (YYYY-MM-DD)"),
    to_date: Optional[str] = Query(None, alias="to", description="End date alias (YYYY-MM-DD)"),
    campaign_id: Optional[int] = Query(None, description="Filter by campaign ID"),
    location_country: Optional[str] = Query(None, description="Filter by country code"),
    group_by: Optional[str] = Query("day", description="Group by: day, week, month"),
    engine: Optional[str] = Query("both", description="Engine: google, bing, both"),
    db: Session = Depends(get_db)
):
    """Get keyword rankings distribution over time by position buckets (public access)"""
    try:
        supabase = SupabaseService(db=db)
        
        # Check if client exists using SQLAlchemy
        client = supabase.get_client_by_id(client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Resolve and validate date range (accept aliases and default last 30 days)
        start_date = start_date or from_date
        end_date = end_date or to_date

        today = datetime.utcnow().date()
        if not end_date:
            end_date = today.isoformat()
        if not start_date:
            start_date = (today - timedelta(days=30)).isoformat()

        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format, expected YYYY-MM-DD")

        if start_dt > end_dt:
            raise HTTPException(status_code=400, detail="start_date cannot be after end_date")

        # Normalize to ISO strings for downstream queries
        start_date = start_dt.isoformat()
        end_date = end_dt.isoformat()
        
        # Get campaign IDs for this client using SQLAlchemy
        client_campaigns = supabase.get_client_campaigns(client_id)
        campaign_ids = [c.get("id") for c in client_campaigns if c.get("id")]
        
        if not campaign_ids:
            return {"data": []}
        
        # Get keyword IDs for filtering using SQLAlchemy Core
        keywords_table = supabase._get_table("agency_analytics_keywords")
        keyword_conditions = [keywords_table.c.campaign_id.in_(campaign_ids)]
        if campaign_id:
            keyword_conditions.append(keywords_table.c.campaign_id == campaign_id)
        if location_country:
            keyword_conditions.append(keywords_table.c.search_location_country_code == location_country)
        
        keyword_query = select(keywords_table.c.id).where(and_(*keyword_conditions))
        keywords_result = db.execute(keyword_query)
        keyword_ids = [row.id for row in keywords_result if row.id]
        
        if not keyword_ids:
            return {"data": []}
        
        # Get rankings data using SQLAlchemy Core
        # Use a subquery to get only the LATEST ranking per keyword per date
        # This prevents counting duplicate rankings if there are multiple entries for the same keyword/date
        rankings_table = supabase._get_table("agency_analytics_keyword_rankings")
        
        # Subquery to get the max id (latest entry) per keyword_id and date
        # This ensures we only count one ranking per keyword per date
        latest_ids_subquery = (
            select(
                rankings_table.c.keyword_id,
                rankings_table.c.date,
                func.max(rankings_table.c.id).label("max_id")
            )
            .where(
                and_(
                    rankings_table.c.keyword_id.in_(keyword_ids),
                    rankings_table.c.date >= start_date,
                    rankings_table.c.date <= end_date
                )
            )
            .group_by(rankings_table.c.keyword_id, rankings_table.c.date)
            .subquery()
        )
        
        # Main query to get the latest ranking per keyword per date
        # Filter by volume > 0 to match the keywords table logic
        # Also need keyword_id to ensure we're counting unique keywords per date
        rankings_query = select(
            rankings_table.c.keyword_id,
            rankings_table.c.date,
            rankings_table.c.google_ranking,
            rankings_table.c.bing_ranking,
            rankings_table.c.volume
        ).join(
            latest_ids_subquery,
            and_(
                rankings_table.c.keyword_id == latest_ids_subquery.c.keyword_id,
                rankings_table.c.date == latest_ids_subquery.c.date,
                rankings_table.c.id == latest_ids_subquery.c.max_id
            )
        ).where(
            and_(
                rankings_table.c.volume != None,
                rankings_table.c.volume > 0
            )
        ).order_by(rankings_table.c.date.asc(), rankings_table.c.keyword_id.asc())
        
        rankings_result = db.execute(rankings_query)
        rankings_data = [dict(row._mapping) for row in rankings_result]
        
        # Log raw rankings data for debugging
        logger.info(f"[Rankings Over Time API] Client {client_id} - Fetched {len(rankings_data)} ranking records from database")
        if rankings_data:
            # Log sample of raw rankings
            logger.info(f"[Rankings Over Time API] Sample raw rankings (first 10):")
            for idx, ranking in enumerate(rankings_data[:10]):
                logger.info(f"[Rankings Over Time API]   [{idx+1}] Date: {ranking.get('date')}, Google: {ranking.get('google_ranking')}, Bing: {ranking.get('bing_ranking')}")
            
            # Count by bucket from raw data (after volume filter)
            filtered_rankings = [r for r in rankings_data if (r.get("volume", 0) or 0) > 0]
            raw_not_found = sum(1 for r in filtered_rankings if r.get("google_ranking") is None or r.get("google_ranking") == 0)
            raw_1_3 = sum(1 for r in filtered_rankings if r.get("google_ranking") and 1 <= r.get("google_ranking") <= 3)
            raw_4_10 = sum(1 for r in filtered_rankings if r.get("google_ranking") and 4 <= r.get("google_ranking") <= 10)
            raw_11_20 = sum(1 for r in filtered_rankings if r.get("google_ranking") and 11 <= r.get("google_ranking") <= 20)
            raw_21_50 = sum(1 for r in filtered_rankings if r.get("google_ranking") and 21 <= r.get("google_ranking") <= 50)
            raw_51_plus = sum(1 for r in filtered_rankings if r.get("google_ranking") and r.get("google_ranking") > 50)
            logger.info(f"[Rankings Over Time API] Raw data bucket counts (after volume filter) - Not Found: {raw_not_found}, 1-3: {raw_1_3}, 4-10: {raw_4_10}, 11-20: {raw_11_20}, 21-50: {raw_21_50}, 51+: {raw_51_plus}")
            logger.info(f"[Rankings Over Time API] Total records: {len(rankings_data)}, After volume filter: {len(filtered_rankings)}")
        
        # Group by date and calculate position buckets
        # Track unique keywords per date to ensure we don't double-count
        # Each ranking in rankings_data represents one keyword's ranking on that date
        date_groups = {}
        date_keyword_tracker = {}  # Track which keywords we've counted per date to avoid duplicates
        
        for ranking in rankings_data:
            date_val = ranking.get("date")
            keyword_id = ranking.get("keyword_id")
            if not date_val or not keyword_id:
                continue
            
            # Convert date to string if it's a date object
            if isinstance(date_val, date_type):
                date_str = date_val.isoformat()
            else:
                date_str = str(date_val)
            
            # Handle group_by parameter
            if group_by == "week":
                # Get week start date (Monday)
                if isinstance(date_val, date_type):
                    date_obj = date_val
                else:
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
                days_since_monday = date_obj.weekday()
                week_start = date_obj - timedelta(days=days_since_monday)
                date_key = week_start.strftime("%Y-%m-%d")
            elif group_by == "month":
                if isinstance(date_val, date_type):
                    date_obj = date_val
                else:
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
                date_key = date_obj.strftime("%Y-%m")
            else:  # day
                date_key = date_str
            
            # Initialize date group if needed
            if date_key not in date_groups:
                date_groups[date_key] = {
                    "google": {"position_1_3": 0, "position_4_10": 0, "position_11_20": 0, "position_21_50": 0, "position_51_plus": 0, "not_found": 0},
                    "bing": {"position_1_3": 0, "position_4_10": 0, "position_11_20": 0, "position_21_50": 0, "position_51_plus": 0, "not_found": 0}
                }
                date_keyword_tracker[date_key] = set()  # Track unique keywords per date
            
            # Skip if we've already counted this keyword for this date (avoid duplicates)
            if keyword_id in date_keyword_tracker[date_key]:
                continue
            
            # Check volume filter (matches table filter: volume > 0)
            volume = ranking.get("volume", 0) or 0
            if volume <= 0:
                continue  # Skip this ranking record if volume is 0 or null
            
            # Mark this keyword as counted for this date
            date_keyword_tracker[date_key].add(keyword_id)
            
            # Process Google ranking
            # Treat ranking 0 or None as not found
            if engine in ["google", "both"]:
                google_rank = ranking.get("google_ranking")
                if google_rank is None or google_rank == 0:
                    date_groups[date_key]["google"]["not_found"] += 1
                elif 1 <= google_rank <= 3:
                    date_groups[date_key]["google"]["position_1_3"] += 1
                elif 4 <= google_rank <= 10:
                    date_groups[date_key]["google"]["position_4_10"] += 1
                elif 11 <= google_rank <= 20:
                    date_groups[date_key]["google"]["position_11_20"] += 1
                elif 21 <= google_rank <= 50:
                    date_groups[date_key]["google"]["position_21_50"] += 1
                elif google_rank > 50:
                    date_groups[date_key]["google"]["position_51_plus"] += 1
                # else: skip invalid rankings
            
            # Process Bing ranking
            # Treat ranking 0 or None as not found
            if engine in ["bing", "both"]:
                bing_rank = ranking.get("bing_ranking")
                if bing_rank is None or bing_rank == 0:
                    date_groups[date_key]["bing"]["not_found"] += 1
                elif 1 <= bing_rank <= 3:
                    date_groups[date_key]["bing"]["position_1_3"] += 1
                elif 4 <= bing_rank <= 10:
                    date_groups[date_key]["bing"]["position_4_10"] += 1
                elif 11 <= bing_rank <= 20:
                    date_groups[date_key]["bing"]["position_11_20"] += 1
                elif 21 <= bing_rank <= 50:
                    date_groups[date_key]["bing"]["position_21_50"] += 1
                elif bing_rank > 50:
                    date_groups[date_key]["bing"]["position_51_plus"] += 1
                # else: skip invalid rankings
        
        # Convert to list and calculate totals
        result_data = []
        for date_key in sorted(date_groups.keys()):
            google_data = date_groups[date_key]["google"]
            bing_data = date_groups[date_key]["bing"]
            
            google_total = sum(google_data.values())
            bing_total = sum(bing_data.values())
            
            result_data.append({
                "date": date_key,
                "google": {
                    **google_data,
                    "total": google_total
                },
                "bing": {
                    **bing_data,
                    "total": bing_total
                }
            })
        
        # Log the result data for debugging
        logger.info(f"[Rankings Over Time API] Client {client_id} - Returning {len(result_data)} date groups")
        if result_data:
            # Log summary statistics
            total_not_found = sum(item["google"]["not_found"] for item in result_data)
            total_1_3 = sum(item["google"]["position_1_3"] for item in result_data)
            total_4_10 = sum(item["google"]["position_4_10"] for item in result_data)
            total_11_20 = sum(item["google"]["position_11_20"] for item in result_data)
            total_21_50 = sum(item["google"]["position_21_50"] for item in result_data)
            total_51_plus = sum(item["google"]["position_51_plus"] for item in result_data)
            logger.info(f"[Rankings Over Time API] Totals across all dates - Not Found: {total_not_found}, 1-3: {total_1_3}, 4-10: {total_4_10}, 11-20: {total_11_20}, 21-50: {total_21_50}, 51+: {total_51_plus}")
            
            # Log first 3 entries as sample
            logger.info(f"[Rankings Over Time API] Sample data (first 3 entries):")
            for item in result_data[:3]:
                logger.info(f"[Rankings Over Time API]   Date: {item['date']}, Google buckets: {item['google']}")
        
        return {"data": result_data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching keyword rankings over time: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/clients/{client_id}/keywords/summary")
@handle_api_errors(context="fetching keyword summary")
async def get_client_keyword_summary(
    client_id: int,
    campaign_id: Optional[int] = Query(None, description="Filter by campaign ID"),
    location_country: Optional[str] = Query(None, description="Filter by country code"),
    date_range: Optional[str] = Query("last_30_days", description="Date range: last_7_days, last_30_days, last_90_days, custom"),
    start_date: Optional[str] = Query(None, description="Custom start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Custom end date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get keyword summary KPIs for a client (public access)"""
    try:
        supabase = SupabaseService(db=db)
        
        # Check if client exists using SQLAlchemy
        client = supabase.get_client_by_id(client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Get campaign IDs for this client
        client_campaigns = supabase.get_client_campaigns(client_id)
        campaign_ids = [c.get("id") for c in client_campaigns if c.get("id")]
        
        if not campaign_ids:
            return {
                "google_rankings": 0,
                "google_change": 0,
                "bing_rankings": 0,
                "bing_change": 0,
                "total_keywords": 0,
                "average_google_ranking": 0,
                "average_bing_ranking": 0,
                "total_search_volume": 0,
                "top_10_visibility_percentage": 0,
                "improving_keywords_count": 0,
                "declining_keywords_count": 0,
                "stable_keywords_count": 0
            }
        
        # Resolve date range
        today_str = datetime.now().strftime("%Y-%m-%d")
        if not end_date:
            end_date = today_str
        if not start_date:
            if date_range == "last_7_days":
                start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            elif date_range == "last_90_days":
                start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
            else:  # default last 30 days
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            if start_dt > end_dt:
                raise HTTPException(status_code=400, detail=f"Invalid date range: start_date ({start_date}) must be before or equal to end_date ({end_date})")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid date format. Use YYYY-MM-DD. Error: {str(e)}")
        
        # Build query for keywords using SQLAlchemy Core
        keywords_table = supabase._get_table("agency_analytics_keywords")
        rankings_table = supabase._get_table("agency_analytics_keyword_rankings")
        
        conditions = [keywords_table.c.campaign_id.in_(campaign_ids)]
        if campaign_id:
            conditions.append(keywords_table.c.campaign_id == campaign_id)
        if location_country:
            conditions.append(keywords_table.c.search_location_country_code == location_country)
        
        # Get keyword ids
        keyword_query = select(keywords_table.c.id).where(and_(*conditions))
        keyword_rows = db.execute(keyword_query)
        keyword_ids = [row.id for row in keyword_rows if row.id]
        total_keywords = len(keyword_ids)
        
        if not keyword_ids:
            return {
                "google_rankings": 0,
                "google_change": 0,
                "bing_rankings": 0,
                "bing_change": 0,
                "total_keywords": 0,
                "average_google_ranking": 0,
                "average_bing_ranking": 0,
                "total_search_volume": 0,
                "top_10_visibility_percentage": 0,
                "improving_keywords_count": 0,
                "declining_keywords_count": 0,
                "stable_keywords_count": 0
            }
        
        # Pull rankings in date range
        rankings_query = select(
            rankings_table.c.keyword_id,
            rankings_table.c.date,
            rankings_table.c.google_ranking,
            rankings_table.c.bing_ranking,
            rankings_table.c.volume
        ).where(
            and_(
                rankings_table.c.keyword_id.in_(keyword_ids),
                rankings_table.c.date >= start_date,
                rankings_table.c.date <= end_date
            )
        )
        rankings_rows = db.execute(rankings_query)
        
        # Bucket by keyword
        rankings_by_keyword = {kw_id: [] for kw_id in keyword_ids}
        for row in rankings_rows:
            rd = dict(row._mapping)
            rankings_by_keyword.setdefault(rd["keyword_id"], []).append(rd)
        
        # Calculate KPIs
        google_rankings = 0
        bing_rankings = 0
        google_change_total = 0
        google_rankings_list = []
        bing_rankings_list = []
        total_search_volume = 0
        volume_entries = 0
        top_10_count = 0
        improving_count = 0
        declining_count = 0
        stable_count = 0
        
        for kw_id, rows in rankings_by_keyword.items():
            if not rows:
                continue
            rows_sorted = sorted(rows, key=lambda r: r.get("date"))
            google_vals = [r.get("google_ranking") for r in rows_sorted if r.get("google_ranking") is not None]
            bing_vals = [r.get("bing_ranking") for r in rows_sorted if r.get("bing_ranking") is not None]
            volume_vals = [r.get("volume") or 0 for r in rows_sorted if r.get("volume") is not None]
            
            if google_vals:
                google_rankings += len(google_vals)
                google_rankings_list.extend(google_vals)
                if min(google_vals) <= 10:
                    top_10_count += 1
                # Trend: compare earliest vs latest non-null google ranking
                first_g = google_vals[0]
                last_g = google_vals[-1]
                if last_g < first_g:
                    improving_count += 1
                    google_change_total += (first_g - last_g)
                elif last_g > first_g:
                    declining_count += 1
                else:
                    stable_count += 1
            # If no google values but there are bing values, count stable for completeness
            elif bing_vals:
                stable_count += 1
            
            if bing_vals:
                bing_rankings += len(bing_vals)
                bing_rankings_list.extend(bing_vals)
            
            total_search_volume += sum(volume_vals)
            volume_entries += len(volume_vals)
        
        # Calculate averages
        average_google_ranking = sum(google_rankings_list) / len(google_rankings_list) if google_rankings_list else 0
        average_bing_ranking = sum(bing_rankings_list) / len(bing_rankings_list) if bing_rankings_list else 0
        average_search_volume = total_search_volume / volume_entries if volume_entries > 0 else 0
        top_10_visibility_percentage = (top_10_count / total_keywords * 100) if total_keywords > 0 else 0
        
        return {
            "google_rankings": google_rankings,
            "google_change": google_change_total,
            "bing_rankings": bing_rankings,
            "bing_change": 0,  # Would need to calculate from historical data
            "total_keywords": total_keywords,
            "average_google_ranking": round(average_google_ranking, 1),
            "average_bing_ranking": round(average_bing_ranking, 1),
            "average_search_volume": round(average_search_volume, 1),
            "total_search_volume": total_search_volume,
            "top_10_visibility_percentage": round(top_10_visibility_percentage, 1),
            "improving_keywords_count": improving_count,
            "declining_keywords_count": declining_count,
            "stable_keywords_count": stable_count
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching keyword summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



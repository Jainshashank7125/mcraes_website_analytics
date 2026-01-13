"""
Agency Analytics API Client
Fetches campaigns and campaign rankings data
"""
import httpx
import logging
import json
import base64
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from urllib.parse import urlparse
from app.core.config import settings

logger = logging.getLogger(__name__)

class AgencyAnalyticsClient:
    """Client for interacting with Agency Analytics API"""
    
    def __init__(self):
        self.base_url = "https://apirequest.app/query"
        
        # Get API key from config (can be overridden via .env)
        api_key = settings.AGENCY_ANALYTICS_API_KEY
        if not api_key:
            raise ValueError(
                "AGENCY_ANALYTICS_API_KEY is not set. "
                "Please set it in config.py or .env file."
            )
        
        # Format: BASE64_ENCODE(:API_KEY) as per API documentation
        # Basic auth requires base64 encoding of ":API_KEY"
        auth_string = f":{api_key}"
        auth_bytes = auth_string.encode('utf-8')
        auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
        
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {auth_b64}"
        }
    
    async def _request(self, body: Dict) -> Dict:
        """Make HTTP request to Agency Analytics API"""
        try:
            logger.debug(f"[Agency Analytics] Making API request to {self.base_url}")
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.base_url,
                    headers=self.headers,
                    json=body
                )
                
                logger.debug(f"[Agency Analytics] API response status: {response.status_code}")
                
                # API always returns 200, but check response status field
                try:
                    response_data = response.json()
                except Exception as json_error:
                    logger.error(f"[Agency Analytics] Failed to parse JSON response: {str(json_error)}")
                    logger.error(f"[Agency Analytics] Response text: {response.text[:500]}")
                    raise Exception(f"Invalid JSON response from Agency Analytics API: {str(json_error)}")
                
                # Check for errors in response
                if response_data.get("status") == "error":
                    error_code = response_data.get("code", 0)
                    error_messages = response_data.get("results", {}).get("messages", {})
                    
                    error_msg = f"Agency Analytics API error (code {error_code})"
                    if error_messages:
                        error_msg += f": {json.dumps(error_messages)}"
                    
                    logger.error(f"[Agency Analytics] {error_msg}")
                    raise Exception(error_msg)
                
                # Check HTTP status code (should be 200, but handle other codes)
                if response.status_code != 200:
                    logger.error(f"[Agency Analytics] HTTP error: {response.status_code} - {response.text[:500]}")
                    response.raise_for_status()
                
                # Log successful response structure
                results = response_data.get("results", {})
                rows = results.get("rows", [])
                logger.debug(f"[Agency Analytics] Response contains {len(rows)} rows")
                
                return response_data
        except httpx.HTTPStatusError as e:
            logger.error(f"[Agency Analytics] HTTP error: {e.response.status_code} - {e.response.text[:500]}")
            raise
        except Exception as e:
            logger.error(f"[Agency Analytics] Error making request: {str(e)}")
            import traceback
            logger.error(f"[Agency Analytics] Traceback: {traceback.format_exc()}")
            raise
    
    async def get_campaigns(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get campaigns with pagination"""
        try:
            body = {
                "provider": "agency-analytics-v2",
                "asset": "campaign",
                "operation": "read",
                "fields": [
                    "id",
                    "date_created",
                    "date_modified",
                    "url",
                    "company",
                    "scope",
                    "status",
                    "group_title",
                    "email_addresses",
                    "phone_numbers",
                    "address",
                    "city",
                    "state",
                    "zip",
                    "country",
                    "revenue",
                    "headcount",
                    "google_ignore_places",
                    "enforce_google_cid",
                    "timezone",
                    "type",
                    "campaign_group_id",
                    "company_id",
                    "account_id"
                ],
                "sort": {"id": "desc"},
                "offset": offset,
                "limit": limit
            }
            
            response = await self._request(body)
            return response.get("results", {}).get("rows", [])
        except Exception as e:
            logger.error(f"Error fetching campaigns: {str(e)}")
            raise
    
    async def get_all_campaigns(self) -> List[Dict]:
        """Get all campaigns with automatic pagination"""
        all_campaigns = []
        offset = 0
        batch_size = 100  # Reasonable batch size
        
        logger.info(f"[Agency Analytics] Starting to fetch all campaigns (batch_size={batch_size})")
        
        while True:
            try:
                logger.debug(f"[Agency Analytics] Fetching campaigns batch: offset={offset}, limit={batch_size}")
                campaigns = await self.get_campaigns(limit=batch_size, offset=offset)
                logger.info(f"[Agency Analytics] Batch at offset {offset}: received {len(campaigns)} campaigns")
                
                if not campaigns:
                    logger.info(f"[Agency Analytics] No more campaigns at offset {offset}, stopping pagination")
                    break
                
                all_campaigns.extend(campaigns)
                logger.info(f"[Agency Analytics] Total campaigns so far: {len(all_campaigns)}")
                
                # If we got fewer than batch_size, we've reached the end
                if len(campaigns) < batch_size:
                    logger.info(f"[Agency Analytics] Received fewer than batch_size ({len(campaigns)} < {batch_size}), reached end")
                    break
                
                offset += batch_size
            except Exception as e:
                logger.error(f"[Agency Analytics] Error fetching campaigns batch at offset {offset}: {str(e)}")
                import traceback
                logger.error(f"[Agency Analytics] Traceback: {traceback.format_exc()}")
                # Don't break on first error - try to continue, but log the error
                # Only break if we have no campaigns at all
                if len(all_campaigns) == 0:
                    logger.error(f"[Agency Analytics] No campaigns fetched yet, stopping due to error")
                    break
                # Otherwise, continue to next batch
                offset += batch_size
        
        logger.info(f"[Agency Analytics] Finished fetching all campaigns. Total: {len(all_campaigns)}")
        return all_campaigns
    
    async def get_campaign(self, campaign_id: int) -> Optional[Dict]:
        """Get a specific campaign by ID"""
        try:
            body = {
                "provider": "agency-analytics-v2",
                "asset": "campaign",
                "operation": "read",
                "fields": [
                    "id",
                    "date_created",
                    "date_modified",
                    "url",
                    "company",
                    "scope",
                    "status",
                    "group_title",
                    "email_addresses",
                    "phone_numbers",
                    "address",
                    "city",
                    "state",
                    "zip",
                    "country",
                    "revenue",
                    "headcount",
                    "google_ignore_places",
                    "enforce_google_cid",
                    "timezone",
                    "type",
                    "campaign_group_id",
                    "company_id",
                    "account_id"
                ],
                "filters": [
                    {
                        "id": {"$equals_comparison": campaign_id}
                    }
                ],
                "sort": {"id": "desc"},
                "offset": 0,
                "limit": 50
            }
            
            response = await self._request(body)
            rows = response.get("results", {}).get("rows", [])
            return rows[0] if rows else None
        except Exception as e:
            logger.error(f"Error fetching campaign {campaign_id}: {str(e)}")
            raise
    
    async def get_campaign_rankings(
        self,
        campaign_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """
        Get campaign rankings data.
        
        Args:
            campaign_id: Campaign ID
            start_date: Optional start date (YYYY-MM-DD). If not provided, defaults to first day of current month.
            end_date: Optional end date (YYYY-MM-DD). If not provided, defaults to today.
        
        Returns:
            List of campaign ranking records
        """
        try:
            # Default to current month if dates not provided
            if not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")
            if not start_date:
                # First day of current month
                start_date = datetime.now().replace(day=1).strftime("%Y-%m-%d")
            
            filters = [
                {"campaign_id": {"$equals_comparison": campaign_id}},
                {"end_date": {"$lessthanorequal_comparison": end_date}},
                {"start_date": {"$greaterthanorequal_comparison": start_date}}
            ]
            
            body = {
                "provider": "agency-analytics-v2",
                "asset": "campaign-rankings",
                "operation": "read",
                "fields": [
                    "date",
                    "google_ranking_change",
                    "google_ranking_count",
                    "google_local_ranking_change",
                    "google_local_ranking_count",
                    "google_mobile_ranking_change",
                    "google_mobile_ranking_count",
                    "bing_ranking_change",
                    "bing_ranking_count",
                    "ranking_average",
                    "results",
                    "volume",
                    "competition",
                    "field_status"
                ],
                "filters": filters,
                "group_by": ["date"],
                "sort": {"date": "asc"},
                "offset": 0,
                "limit": 9999
            }
            
            response = await self._request(body)
            return response.get("results", {}).get("rows", [])
        except Exception as e:
            logger.error(f"Error fetching campaign rankings for {campaign_id}: {str(e)}")
            raise
    
    async def get_campaign_keywords(self, campaign_id: int, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get keywords for a specific campaign (max limit is 500 per API)"""
        try:
            # API has max limit of 500, so cap it
            limit = min(limit, 500)
            
            body = {
                "provider": "agency-analytics-v2",
                "asset": "keyword",
                "operation": "read",
                "fields": [
                    "id",
                    "date_created",
                    "date_modified",
                    "keyword_phrase",
                    "primary_keyword",
                    "campaign_id",
                    "search_location",
                    "search_language",
                    "tags"
                ],
                "filters": [
                    {"campaign_id": {"$equals_comparison": campaign_id}}
                ],
                "sort": [{"id": "desc"}],  # Use array format to match API playground
                "offset": offset,
                "limit": limit
            }
            
            response = await self._request(body)
            return response.get("results", {}).get("rows", [])
        except Exception as e:
            logger.error(f"Error fetching keywords for campaign {campaign_id}: {str(e)}")
            raise
    
    async def get_all_campaign_keywords(self, campaign_id: int) -> List[Dict]:
        """Get all keywords for a campaign with automatic pagination (handles limit of 500)"""
        all_keywords = []
        offset = 0
        batch_size = 500  # Max allowed by API
        
        while True:
            try:
                keywords = await self.get_campaign_keywords(campaign_id, limit=batch_size, offset=offset)
                if not keywords:
                    break
                
                all_keywords.extend(keywords)
                
                # If we got fewer than batch_size, we've reached the end
                if len(keywords) < batch_size:
                    break
                
                offset += batch_size
            except Exception as e:
                logger.error(f"Error fetching keywords batch at offset {offset}: {str(e)}")
                break
        
        return all_keywords
    
    def format_keywords_data(self, keywords: List[Dict]) -> List[Dict]:
        """Format keywords data for database storage"""
        formatted_rows = []
        
        for row in keywords:
            # Format search_location
            location_text = "N/A"
            location_obj = row.get("search_location")
            
            if location_obj and isinstance(location_obj, dict):
                parts = []
                try:
                    formatted_name = location_obj.get("formatted_name")
                    if formatted_name:
                        parts.append(str(formatted_name))
                    
                    region_name = location_obj.get("region_name")
                    if region_name and str(region_name) != str(formatted_name):
                        parts.append(str(region_name))
                    
                    country_code = location_obj.get("country_code")
                    if country_code:
                        parts.append(f"({str(country_code)})")
                    
                    latitude = location_obj.get("latitude")
                    longitude = location_obj.get("longitude")
                    if latitude and longitude:
                        parts.append(f"lat: {str(latitude)}, long: {str(longitude)}")
                    
                    location_text = " ".join(parts) if parts else "N/A"
                except Exception as location_error:
                    logger.error(f"Error formatting location for keyword {row.get('id')}: {str(location_error)}. Location value: {location_obj}")
                    location_text = str(location_obj) if location_obj else "N/A"
            
            # Create unique identifier
            campaign_id = row.get("campaign_id", "N/A")
            keyword_id = row.get("id", "N/A")
            campaign_keyword_id = f"{campaign_id} - {keyword_id}"
            
            # Format tags
            tags = row.get("tags", [])
            try:
                if isinstance(tags, list):
                    # Handle case where tags might be a list of dicts or strings
                    tag_strings = []
                    for tag in tags:
                        if isinstance(tag, str):
                            tag_strings.append(tag)
                        elif isinstance(tag, dict):
                            # If tag is a dict, try to extract a meaningful string
                            # Common fields might be "name", "value", "tag", etc.
                            tag_str = tag.get("name") or tag.get("value") or tag.get("tag") or str(tag)
                            tag_strings.append(str(tag_str))
                        else:
                            tag_strings.append(str(tag))
                    tags_str = ", ".join(tag_strings) if tag_strings else "N/A"
                else:
                    tags_str = str(tags) if tags else "N/A"
            except Exception as tag_error:
                logger.error(f"Error formatting tags for keyword {row.get('id')}: {str(tag_error)}. Tags value: {tags}")
                tags_str = str(tags) if tags else "N/A"
            
            formatted_rows.append({
                "id": keyword_id,
                "campaign_id": campaign_id,
                "campaign_keyword_id": campaign_keyword_id,
                "keyword_phrase": row.get("keyword_phrase", ""),
                "primary_keyword": bool(row.get("primary_keyword", False)),
                "search_location": location_text,
                "search_location_formatted_name": location_obj.get("formatted_name") if isinstance(location_obj, dict) else None,
                "search_location_region_name": location_obj.get("region_name") if isinstance(location_obj, dict) else None,
                "search_location_country_code": location_obj.get("country_code") if isinstance(location_obj, dict) else None,
                "search_location_latitude": float(location_obj.get("latitude")) if isinstance(location_obj, dict) and location_obj.get("latitude") else None,
                "search_location_longitude": float(location_obj.get("longitude")) if isinstance(location_obj, dict) and location_obj.get("longitude") else None,
                "search_language": self._format_search_language(row.get("search_language")),
                "tags": tags_str,
                "date_created": row.get("date_created"),
                "date_modified": row.get("date_modified")
            })
        
        return formatted_rows
    
    def _format_search_language(self, search_language) -> str:
        """Format search_language to a string (handles list, dict, or string)"""
        if not search_language:
            return "N/A"
        
        if isinstance(search_language, str):
            return search_language
        elif isinstance(search_language, list):
            if not search_language:
                return "N/A"
            # If list contains dicts, extract meaningful values
            lang_strings = []
            for lang in search_language:
                if isinstance(lang, dict):
                    # Extract name or code from dict
                    lang_str = lang.get("name") or lang.get("google_code") or lang.get("bing_code") or str(lang)
                    lang_strings.append(str(lang_str))
                elif isinstance(lang, str):
                    lang_strings.append(lang)
                else:
                    lang_strings.append(str(lang))
            return ", ".join(lang_strings) if lang_strings else "N/A"
        elif isinstance(search_language, dict):
            # Extract meaningful value from dict
            lang_str = search_language.get("name") or search_language.get("google_code") or search_language.get("bing_code") or str(search_language)
            return str(lang_str)
        else:
            return str(search_language)
    
    def format_rankings_data(self, rankings: List[Dict], campaign_data: Dict) -> List[Dict]:
        """Format rankings data for database storage"""
        client_name = campaign_data.get("company", "Unknown Client")
        campaign_id = campaign_data.get("id", "N/A")
        
        formatted_rows = []
        for row in rankings:
            date = row.get("date", "N/A")
            
            # Convert date from "YYYY-MM" to "YYYY-MM-01" (first day of month)
            # PostgreSQL DATE type requires full date format
            if date and date != "N/A" and len(date) == 7 and date.count("-") == 1:
                # Format is "YYYY-MM", append "-01" to make it a valid date
                date = f"{date}-01"
            elif date and date != "N/A":
                # Try to parse and format if it's already a date string
                try:
                    # If it's already in YYYY-MM-DD format, keep it
                    if len(date) == 10 and date.count("-") == 2:
                        # Validate it's a proper date
                        datetime.strptime(date, "%Y-%m-%d")
                    else:
                        # Try to parse various formats
                        parsed_date = datetime.strptime(date, "%Y-%m-%d")
                        date = parsed_date.strftime("%Y-%m-%d")
                except ValueError:
                    # If parsing fails, default to first day of current month
                    logger.warning(f"Invalid date format: {date}, using first day of month")
                    date = datetime.now().strftime("%Y-%m-01")
            
            formatted_rows.append({
                "campaign_id": campaign_id,
                "client_name": client_name,
                "date": date,
                "campaign_id_date": f"{campaign_id}-{date}",
                "google_ranking_count": row.get("google_ranking_count", 0) or 0,
                "google_ranking_change": row.get("google_ranking_change", 0) or 0,
                "google_local_count": row.get("google_local_ranking_count", 0) or 0,
                "google_mobile_count": row.get("google_mobile_ranking_count", 0) or 0,
                "bing_ranking_count": row.get("bing_ranking_count", 0) or 0,
                "ranking_average": float(row.get("ranking_average", 0) or 0),
                "search_volume": row.get("volume", 0) or 0,
                "competition": float(row.get("competition", 0) or 0)
            })
        
        return formatted_rows
    
    async def get_keyword_rankings(
        self,
        keyword_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """
        Get keyword rankings data.
        
        Args:
            keyword_id: Keyword ID
            start_date: Optional start date (YYYY-MM-DD). If not provided, defaults to first day of current month.
            end_date: Optional end date (YYYY-MM-DD). If not provided, defaults to today.
        
        Returns:
            List of keyword ranking records
        """
        try:
            # Default to current month if dates not provided
            if not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")
            if not start_date:
                # First day of current month
                start_date = datetime.now().replace(day=1).strftime("%Y-%m-%d")
            
            filters = [
                {"keyword_id": {"$equals_comparison": keyword_id}},
                {"end_date": {"$lessthanorequal_comparison": end_date}},
                {"start_date": {"$greaterthanorequal_comparison": start_date}}
            ]
            
            body = {
                "provider": "agency-analytics-v2",
                "asset": "keyword-rankings",
                "operation": "read",
                "fields": [
                    "date",
                    "google_ranking",
                    "google_ranking_url",
                    "google_mobile_ranking",
                    "google_mobile_ranking_url",
                    "google_local_ranking",
                    "bing_ranking",
                    "bing_ranking_url",
                    "results",
                    "volume",
                    "competition",
                    "field_status"
                ],
                "filters": filters,
                "group_by": ["date"],
                "sort": [{"date": "asc"}],  # Use array format to match API playground
                "offset": 0,
                "limit": 9999
            }
            
            response = await self._request(body)
            rows = response.get("results", {}).get("rows", [])
            if not rows:
                logger.debug(f"No ranking data returned from API for keyword {keyword_id} (response keys: {list(response.keys())})")
            else:
                logger.debug(f"API returned {len(rows)} ranking records for keyword {keyword_id}")
            return rows
        except Exception as e:
            logger.error(f"Error fetching keyword rankings for {keyword_id}: {str(e)}")
            raise
    
    def format_keyword_rankings_data(
        self,
        rankings: List[Dict],
        keyword_id: int,
        campaign_id: int,
        keyword_phrase: str = ""
    ) -> Tuple[List[Dict], Optional[Dict]]:
        """
        Format keyword rankings data for database storage
        Returns: (daily_records, summary_record)
        """
        if not rankings:
            logger.debug(f"No rankings to format for keyword {keyword_id} ({keyword_phrase})")
            return [], None
        
        # Sort by date
        sorted_rankings = sorted(rankings, key=lambda x: x.get("date", ""))
        
        daily_records = []
        for row in sorted_rankings:
            date = row.get("date", "N/A")
            
            # Convert date from "YYYY-MM" to "YYYY-MM-01" if needed
            if date and date != "N/A" and len(date) == 7 and date.count("-") == 1:
                date = f"{date}-01"
            elif date and date != "N/A":
                try:
                    # If already in YYYY-MM-DD format, validate it
                    if len(date) == 10 and date.count("-") == 2:
                        datetime.strptime(date, "%Y-%m-%d")
                        # Date is already in correct format, use as-is
                    else:
                        # Try to parse other formats
                        parsed_date = datetime.strptime(date, "%Y-%m-%d")
                        date = parsed_date.strftime("%Y-%m-%d")
                except ValueError:
                    logger.warning(f"Invalid date format for keyword {keyword_id}: {date}, using current date")
                    date = datetime.now().strftime("%Y-%m-%d")
            
            keyword_id_date = f"{keyword_id}-{date}"
            
            # Handle field_status (store as JSON)
            field_status = row.get("field_status")
            if field_status and not isinstance(field_status, dict):
                try:
                    if isinstance(field_status, str):
                        field_status = json.loads(field_status)
                except:
                    field_status = {}
            
            daily_records.append({
                "keyword_id": keyword_id,
                "campaign_id": campaign_id,
                "keyword_id_date": keyword_id_date,
                "date": date,
                "google_ranking": row.get("google_ranking"),
                "google_ranking_url": row.get("google_ranking_url"),
                "google_mobile_ranking": row.get("google_mobile_ranking"),
                "google_mobile_ranking_url": row.get("google_mobile_ranking_url"),
                "google_local_ranking": row.get("google_local_ranking"),
                "bing_ranking": row.get("bing_ranking"),
                "bing_ranking_url": row.get("bing_ranking_url"),
                "results": row.get("results"),
                "volume": row.get("volume"),
                "competition": float(row.get("competition", 0) or 0) if row.get("competition") else None,
                "field_status": field_status
            })
        
        # Calculate summary (latest data + ranking change)
        first_row = sorted_rankings[0]
        last_row = sorted_rankings[-1]
        
        first_rank = first_row.get("google_ranking")
        last_rank = last_row.get("google_ranking")
        ranking_change = None
        if first_rank is not None and last_rank is not None:
            ranking_change = first_rank - last_rank
        
        # Format latest date
        latest_date = last_row.get("date", "")
        if latest_date and len(latest_date) == 7 and latest_date.count("-") == 1:
            latest_date = f"{latest_date}-01"
        
        start_date = first_row.get("date", "")
        if start_date and len(start_date) == 7 and start_date.count("-") == 1:
            start_date = f"{start_date}-01"
        
        # Handle field_status for summary
        summary_field_status = last_row.get("field_status")
        if summary_field_status and not isinstance(summary_field_status, dict):
            try:
                if isinstance(summary_field_status, str):
                    summary_field_status = json.loads(summary_field_status)
            except:
                summary_field_status = {}
        
        summary_record = {
            "keyword_id": keyword_id,
            "campaign_id": campaign_id,
            "keyword_phrase": keyword_phrase,
            "keyword_id_date": f"{keyword_id}-{latest_date}",
            "date": latest_date,
            "google_ranking": last_rank,
            "google_ranking_url": last_row.get("google_ranking_url"),
            "google_mobile_ranking": last_row.get("google_mobile_ranking"),
            "google_mobile_ranking_url": last_row.get("google_mobile_ranking_url"),
            "google_local_ranking": last_row.get("google_local_ranking"),
            "bing_ranking": last_row.get("bing_ranking"),
            "bing_ranking_url": last_row.get("bing_ranking_url"),
            "search_volume": last_row.get("volume"),
            "competition": float(last_row.get("competition", 0) or 0) if last_row.get("competition") else None,
            "results": last_row.get("results"),
            "field_status": summary_field_status,
            "start_date": start_date,
            "end_date": latest_date,
            "start_ranking": first_rank,
            "end_ranking": last_rank,
            "ranking_change": ranking_change
        }
        
        return daily_records, summary_record
    
    @staticmethod
    def extract_domain(url: str) -> Optional[str]:
        """Extract domain from URL"""
        if not url:
            return None
        try:
            # Remove protocol if present
            url = url.strip()
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except Exception:
            return None
    
    @staticmethod
    def normalize_domain(domain: str) -> str:
        """Normalize domain for comparison"""
        if not domain:
            return ""
        domain = domain.lower().strip()
        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        # Remove trailing slash
        domain = domain.rstrip('/')
        return domain
    
    @staticmethod
    def match_campaign_to_brand(campaign: Dict, brand: Dict) -> Optional[Dict]:
        """Match campaign to brand based on URL"""
        campaign_url = campaign.get("url", "")
        brand_website = brand.get("website", "")
        
        if not campaign_url or not brand_website:
            return None
        
        campaign_domain = AgencyAnalyticsClient.extract_domain(campaign_url)
        brand_domain = AgencyAnalyticsClient.extract_domain(brand_website)
        
        if not campaign_domain or not brand_domain:
            return None
        
        # Normalize domains
        campaign_domain = AgencyAnalyticsClient.normalize_domain(campaign_domain)
        brand_domain = AgencyAnalyticsClient.normalize_domain(brand_domain)
        
        # Exact match
        if campaign_domain == brand_domain:
            return {
                "campaign_id": campaign.get("id"),
                "brand_id": brand.get("id"),
                "match_method": "url_match",
                "match_confidence": "exact"
            }
        
        # Check if brand domain is in campaign URL or vice versa
        if brand_domain in campaign_url.lower() or campaign_domain in brand_website.lower():
            return {
                "campaign_id": campaign.get("id"),
                "brand_id": brand.get("id"),
                "match_method": "url_match",
                "match_confidence": "partial"
            }
        
        return None


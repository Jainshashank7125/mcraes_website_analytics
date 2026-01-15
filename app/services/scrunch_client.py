import httpx
import logging
from typing import Dict, List, Optional, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

class ScrunchAPIClient:
    """Client for interacting with Scrunch AI API"""
    
    def __init__(self):
        self.base_url = settings.SCRUNCH_API_BASE_URL
        self.token = settings.SCRUNCH_API_TOKEN
        if not self.token:
            raise ValueError(
                "SCRUNCH_API_TOKEN is not set. "
                "Please set it in your .env file."
            )
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    async def _request(self, method: str, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make HTTP request to Scrunch API"""
        url = f"{self.base_url}{endpoint}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                # Enhanced error logging with detailed response information
                status_code = e.response.status_code
                response_text = e.response.text
                response_headers = dict(e.response.headers)
                
                # Try to parse JSON error response if available
                error_details = {}
                try:
                    if response_text:
                        error_details = e.response.json()
                except:
                    # If not JSON, use text as-is
                    error_details = {"raw_response": response_text}
                
                # Build comprehensive error log
                error_log = {
                    "url": url,
                    "method": method,
                    "status_code": status_code,
                    "params": params,
                    "response_body": error_details,
                    "response_text": response_text[:1000] if response_text else None,  # Limit to 1000 chars
                    "response_headers": {k: v for k, v in response_headers.items() if k.lower() not in ['authorization', 'cookie']}  # Exclude sensitive headers
                }
                
                logger.error(
                    f"Scrunch API HTTP error for {method} {url}: "
                    f"Status {status_code} - {response_text[:200] if response_text else 'No response body'}"
                )
                logger.error(f"Scrunch API error details: {error_log}")
                
                # Create a more descriptive exception
                error_message = f"Server error '{status_code} {e.response.reason_phrase}' for url '{url}'"
                if error_details and isinstance(error_details, dict):
                    if "error" in error_details:
                        error_message += f" - Error: {error_details['error']}"
                    if "message" in error_details:
                        error_message += f" - Message: {error_details['message']}"
                    if "detail" in error_details:
                        error_message += f" - Detail: {error_details['detail']}"
                
                # Raise with more context
                raise Exception(error_message) from e
            except httpx.TimeoutException as e:
                logger.error(f"Scrunch API timeout for {method} {url} (params: {params})")
                raise Exception(f"Request to Scrunch API timed out: {url}") from e
            except httpx.RequestError as e:
                logger.error(f"Scrunch API request error for {method} {url}: {str(e)} (params: {params})")
                raise Exception(f"Request error to Scrunch API: {str(e)}") from e
            except Exception as e:
                logger.error(f"Scrunch API unexpected error for {method} {url}: {str(e)} (params: {params})")
                logger.exception("Full traceback for Scrunch API error:")
                raise
    
    async def get_brands(self) -> List[Dict]:
        """Retrieve all brands"""
        logger.info("Fetching brands from Scrunch API")
        data = await self._request("GET", "/brands")
        return data if isinstance(data, list) else data.get("items", [])
    
    async def get_prompts(
        self, 
        brand_id: int,
        stage: Optional[str] = None,
        persona_id: Optional[int] = None,
        limit: int = 1000,
        offset: int = 0
    ) -> Dict:
        """Retrieve prompts for a brand"""
        logger.info(f"Fetching prompts for brand {brand_id}")
        params = {
            "limit": limit,
            "offset": offset
        }
        if stage:
            params["stage"] = stage
        if persona_id:
            params["persona_id"] = persona_id
        
        return await self._request("GET", f"/{brand_id}/prompts", params=params)
    
    async def get_responses(
        self,
        brand_id: int,
        platform: Optional[str] = None,
        prompt_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 1000,
        offset: int = 0
    ) -> Dict:
        """Retrieve responses for a brand"""
        logger.info(f"Fetching responses for brand {brand_id}")
        params = {
            "limit": limit,
            "offset": offset
        }
        if platform:
            params["platform"] = platform
        if prompt_id:
            params["prompt_id"] = prompt_id
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        return await self._request("GET", f"/{brand_id}/responses", params=params)
    
    async def get_all_prompts_paginated(
        self, 
        brand_id: int,
        stage: Optional[str] = None,
        persona_id: Optional[int] = None
    ) -> List[Dict]:
        """Get all prompts with pagination"""
        all_prompts = []
        offset = 0
        limit = 1000
        
        while True:
            data = await self.get_prompts(
                brand_id, 
                stage=stage,
                persona_id=persona_id,
                limit=limit, 
                offset=offset
            )
            prompts = data if isinstance(data, list) else data.get("items", [])
            
            if not prompts:
                break
            
            all_prompts.extend(prompts)
            
            if len(prompts) < limit:
                break
            
            offset += limit
        
        logger.info(f"Fetched {len(all_prompts)} total prompts")
        return all_prompts
    
    async def get_all_responses_paginated(
        self, 
        brand_id: int,
        platform: Optional[str] = None,
        prompt_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """Get all responses with pagination"""
        all_responses = []
        offset = 0
        limit = 1000
        
        while True:
            data = await self.get_responses(
                brand_id=brand_id,
                platform=platform,
                prompt_id=prompt_id,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
                offset=offset
            )
            
            responses = data if isinstance(data, list) else data.get("items", [])
            
            if not responses:
                break
            
            all_responses.extend(responses)
            
            if len(responses) < limit:
                break
            
            offset += limit
        
        logger.info(f"Fetched {len(all_responses)} total responses")
        return all_responses
    
    async def query_analytics(
        self,
        brand_id: int,
        fields: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 50000,
        offset: int = 0
    ) -> Dict:
        """
        Query analytics data using the Query API
        
        Args:
            brand_id: Brand ID
            fields: List of dimension and metric fields to retrieve
            start_date: Start date (YYYY-MM-DD), last 90 days only
            end_date: End date (YYYY-MM-DD)
            limit: Max results (default 50,000)
            offset: Pagination offset
        
        Returns:
            Dict with query results
        """
        logger.info(f"Querying analytics for brand {brand_id} with fields: {fields}, start_date: {start_date}, end_date: {end_date}")
        params = {
            "fields": ",".join(fields),
            "limit": limit,
            "offset": offset
        }
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        logger.debug(f"Scrunch Query API request params: {params}")
        result = await self._request("GET", f"/{brand_id}/query", params=params)
        
        if result:
            items_count = len(result.get("items", [])) if isinstance(result, dict) else 0
            logger.info(f"Scrunch Query API returned {items_count} items for brand {brand_id}")
        
        return result


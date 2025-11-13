from typing import List, Dict, Optional, Any
from app.core.database import get_supabase_client
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SupabaseService:
    """Service for interacting with Supabase database"""
    
    def __init__(self):
        self.client = get_supabase_client()
    
    def upsert_brands(self, brands: List[Dict]) -> int:
        """Upsert brands data"""
        if not brands:
            return 0
        
        # Transform data to match database schema
        records = []
        for brand in brands:
            records.append({
                "id": brand.get("id"),
                "name": brand.get("name"),
                "created_at": brand.get("created_at")
            })
        
        try:
            result = self.client.table("brands").upsert(records).execute()
            logger.info(f"Upserted {len(records)} brands")
            return len(records)
        except Exception as e:
            logger.error(f"Error upserting brands: {str(e)}")
            raise
    
    def upsert_prompts(self, prompts: List[Dict]) -> int:
        """Upsert prompts data"""
        if not prompts:
            return 0
        
        records = []
        for prompt in prompts:
            records.append({
                "id": prompt.get("id"),
                "prompt_text": prompt.get("prompt_text"),
                "stage": prompt.get("stage"),
                "persona_id": prompt.get("persona_id"),
                "persona_name": prompt.get("persona_name"),
                "tags": prompt.get("tags"),
                "key_topics": prompt.get("key_topics"),
                "created_at": prompt.get("created_at") or datetime.utcnow().isoformat()
            })
        
        try:
            result = self.client.table("prompts").upsert(records).execute()
            logger.info(f"Upserted {len(records)} prompts")
            return len(records)
        except Exception as e:
            logger.error(f"Error upserting prompts: {str(e)}")
            raise
    
    def upsert_responses(self, responses: List[Dict]) -> int:
        """Upsert responses data"""
        if not responses:
            return 0
        
        records = []
        for response in responses:
            # Extract citations
            citations = response.get("citations", [])
            
            record = {
                "id": response.get("id"),
                "prompt_id": response.get("prompt_id"),
                "prompt": response.get("prompt"),
                "response_text": response.get("response_text"),
                "platform": response.get("platform"),
                "country": response.get("country"),
                "persona_name": response.get("persona_name"),
                "stage": response.get("stage"),
                "branded": response.get("branded"),
                "key_topics": response.get("key_topics"),
                "brand_present": response.get("brand_present"),
                "brand_sentiment": response.get("brand_sentiment"),
                "brand_position": response.get("brand_position"),
                "competitors_present": response.get("competitors_present"),
                "competitors": response.get("competitors"),
                "created_at": response.get("created_at"),
                "citations": citations  # Store as JSON array
            }
            records.append(record)
        
        try:
            result = self.client.table("responses").upsert(records).execute()
            logger.info(f"Upserted {len(records)} responses")
            return len(records)
        except Exception as e:
            logger.error(f"Error upserting responses: {str(e)}")
            raise
    
    def upsert_citations(self, responses: List[Dict]) -> int:
        """Upsert citations separately (if you want a separate citations table)"""
        if not responses:
            return 0
        
        citations_records = []
        for response in responses:
            response_id = response.get("id")
            citations = response.get("citations", [])
            
            for citation in citations:
                citations_records.append({
                    "response_id": response_id,
                    "url": citation.get("url"),
                    "domain": citation.get("domain"),
                    "source_type": citation.get("source_type"),
                    "title": citation.get("title"),
                    "snippet": citation.get("snippet")
                })
        
        if not citations_records:
            return 0
        
        try:
            result = self.client.table("citations").upsert(citations_records).execute()
            logger.info(f"Upserted {len(citations_records)} citations")
            return len(citations_records)
        except Exception as e:
            logger.error(f"Error upserting citations: {str(e)}")
            raise


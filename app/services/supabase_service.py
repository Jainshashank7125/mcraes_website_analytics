from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import text, Table, MetaData, select, update, insert, delete, and_, or_, func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.db.database import get_db
from app.db.models import Brand, Prompt, Response, Citation, AuditLog, Client, DashboardLink
from app.core.database import get_supabase_client
import logging
import re
import unicodedata
import uuid
from urllib.parse import urlparse
from datetime import datetime, timedelta, date

logger = logging.getLogger(__name__)

class SupabaseService:
    """Service for interacting with database using SQLAlchemy"""
    
    def __init__(self, db: Optional[Session] = None):
        """
        Initialize service with database session.
        If db is None, will get a new session (for backward compatibility).
        """
        if db is None:
            # Get a new session for backward compatibility
            self.db = next(get_db())
            self._close_db = True
        else:
            self.db = db
            self._close_db = False
        self._supabase_client = None  # Lazy-loaded for backward compatibility
        self._table_cache = {}  # Cache table metadata to avoid repeated reflection
    
    @property
    def client(self):
        """
        DEPRECATED: Supabase REST API client for backward compatibility.
        This property is kept for methods that haven't been migrated to SQLAlchemy yet.
        New code should use SQLAlchemy methods directly.
        """
        if self._supabase_client is None:
            logger.warning(
                "Using deprecated Supabase REST API client. "
                "This method should be migrated to use SQLAlchemy. "
                "The Supabase client is only kept for backward compatibility during migration."
            )
            try:
                self._supabase_client = get_supabase_client()
            except Exception as e:
                logger.error(f"Failed to create Supabase client for backward compatibility: {e}")
                raise
        return self._supabase_client
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._close_db:
            self.db.close()
    
    def _execute_text(self, query: str, params: Optional[Dict] = None) -> Any:
        """Execute raw SQL query"""
        return self.db.execute(text(query), params or {})
    
    def _get_table(self, table_name: str) -> Table:
        """Get table object using reflection (with caching for performance)"""
        # Use cache to avoid repeated reflection
        if table_name not in self._table_cache:
            metadata = MetaData()
            metadata.reflect(bind=self.db.bind, only=[table_name])
            self._table_cache[table_name] = metadata.tables[table_name]
        return self._table_cache[table_name]
    
    def _table_select(self, table_name: str, filters: Optional[Dict] = None, limit: Optional[int] = None, offset: Optional[int] = None, order_by: Optional[str] = None, desc: bool = False) -> List[Dict]:
        """Helper method to select from any table using SQLAlchemy Core"""
        try:
            table = self._get_table(table_name)
            query = select(table)
            
            # Apply filters
            if filters:
                conditions = []
                for key, value in filters.items():
                    if value is not None:
                        conditions.append(table.c[key] == value)
                if conditions:
                    query = query.where(and_(*conditions))
            
            # Apply ordering
            if order_by:
                col = table.c[order_by]
                query = query.order_by(col.desc() if desc else col.asc())
            
            # Apply pagination
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            
            result = self.db.execute(query)
            return [dict(row._mapping) for row in result]
        except Exception as e:
            logger.error(f"Error selecting from {table_name}: {str(e)}")
            raise
    
    def _table_insert(self, table_name: str, records: List[Dict], on_conflict: Optional[str] = None) -> int:
        """Helper method to insert into any table using SQLAlchemy Core"""
        try:
            if not records:
                return 0
            
            table = self._get_table(table_name)
            
            # Use PostgreSQL INSERT ... ON CONFLICT if specified
            if on_conflict:
                # This is a simplified version - for complex cases, use raw SQL
                stmt = pg_insert(table).values(records)
                stmt = stmt.on_conflict_do_update(set_=records[0])
                result = self.db.execute(stmt)
            else:
                stmt = insert(table).values(records)
                result = self.db.execute(stmt)
            
            self.db.commit()
            return len(records)
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error inserting into {table_name}: {str(e)}")
            raise
    
    def _table_update(self, table_name: str, data: Dict, filters: Dict) -> int:
        """Helper method to update any table using SQLAlchemy Core"""
        try:
            table = self._get_table(table_name)
            conditions = [table.c[key] == value for key, value in filters.items()]
            stmt = update(table).where(and_(*conditions)).values(**data)
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating {table_name}: {str(e)}")
            raise
    
    def _table_delete(self, table_name: str, filters: Dict) -> int:
        """Helper method to delete from any table using SQLAlchemy Core"""
        try:
            table = self._get_table(table_name)
            conditions = [table.c[key] == value for key, value in filters.items()]
            stmt = delete(table).where(and_(*conditions))
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting from {table_name}: {str(e)}")
            raise
    
    def upsert_brands(self, brands: List[Dict]) -> int:
        """Upsert brands data - Optimized with bulk operations"""
        if not brands:
            return 0
        
        try:
            # Extract all brand IDs for bulk lookup
            brand_ids = [b.get("id") for b in brands if b.get("id")]
            if not brand_ids:
                return 0
            
            # Bulk fetch existing brands in one query
            existing_brands = {
                b.id: b for b in self.db.query(Brand).filter(Brand.id.in_(brand_ids)).all()
            }
            
            # Separate into updates and inserts
            to_update = []
            to_insert = []
            
            for brand_data in brands:
                brand_id = brand_data.get("id")
                if not brand_id:
                    continue
                
                if brand_id in existing_brands:
                    # Update existing
                    existing = existing_brands[brand_id]
                    existing.name = brand_data.get("name")
                    existing.website = brand_data.get("website")
                    if "ga4_property_id" in brand_data:
                        existing.ga4_property_id = brand_data.get("ga4_property_id")
                    to_update.append(existing)
                else:
                    # Insert new
                    to_insert.append(Brand(
                        id=brand_id,
                        name=brand_data.get("name"),
                        website=brand_data.get("website"),
                        ga4_property_id=brand_data.get("ga4_property_id")
                    ))
            
            # Bulk add new brands
            if to_insert:
                self.db.bulk_save_objects(to_insert)
            
            # Commit once for all changes
            self.db.commit()
            
            count = len(to_update) + len(to_insert)
            logger.info(f"Upserted {count} brands ({len(to_update)} updated, {len(to_insert)} inserted)")
            return count
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error upserting brands: {str(e)}")
            raise
    
    def upsert_prompts(self, prompts: List[Dict], brand_id: int = None) -> int:
        """Upsert prompts data - Optimized with bulk operations"""
        if not prompts:
            return 0
        
        try:
            # Extract all prompt IDs for bulk lookup
            prompt_ids = [p.get("id") for p in prompts if p.get("id")]
            if not prompt_ids:
                return 0
            
            # Bulk fetch existing prompts in one query
            existing_prompts = {
                p.id: p for p in self.db.query(Prompt).filter(Prompt.id.in_(prompt_ids)).all()
            }
            
            # Separate into updates and inserts
            to_update = []
            to_insert = []
            
            for prompt_data in prompts:
                prompt_id = prompt_data.get("id")
                if not prompt_id:
                    continue
                
                final_brand_id = brand_id or prompt_data.get("brand_id")
                
                if prompt_id in existing_prompts:
                    # Update existing
                    existing = existing_prompts[prompt_id]
                    existing.brand_id = final_brand_id
                    existing.text = prompt_data.get("text")
                    existing.stage = prompt_data.get("stage")
                    existing.persona_id = prompt_data.get("persona_id")
                    existing.persona_name = prompt_data.get("persona_name")
                    existing.platforms = prompt_data.get("platforms", [])
                    existing.tags = prompt_data.get("tags", [])
                    existing.topics = prompt_data.get("topics", [])
                    if prompt_data.get("created_at"):
                        existing.created_at = prompt_data.get("created_at")
                    to_update.append(existing)
                else:
                    # Insert new
                    to_insert.append(Prompt(
                        id=prompt_id,
                        brand_id=final_brand_id,
                        text=prompt_data.get("text"),
                        stage=prompt_data.get("stage"),
                        persona_id=prompt_data.get("persona_id"),
                        persona_name=prompt_data.get("persona_name"),
                        platforms=prompt_data.get("platforms", []),
                        tags=prompt_data.get("tags", []),
                        topics=prompt_data.get("topics", []),
                        created_at=prompt_data.get("created_at")
                    ))
            
            # Bulk add new prompts
            if to_insert:
                self.db.bulk_save_objects(to_insert)
            
            # Commit once for all changes
            self.db.commit()
            
            count = len(to_update) + len(to_insert)
            logger.info(f"Upserted {count} prompts ({len(to_update)} updated, {len(to_insert)} inserted)")
            return count
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error upserting prompts: {str(e)}")
            raise
    
    def upsert_responses(self, responses: List[Dict], brand_id: int = None) -> int:
        """Upsert responses data - Optimized with bulk operations"""
        if not responses:
            return 0
        
        try:
            batch_size = 500  # Increased batch size for better performance
            total_upserted = 0
            
            for i in range(0, len(responses), batch_size):
                batch = responses[i:i + batch_size]
                
                # Extract all response IDs for bulk lookup
                response_ids = [r.get("id") for r in batch if r.get("id")]
                if not response_ids:
                    continue
                
                # Bulk fetch existing responses in one query
                existing_responses = {
                    r.id: r for r in self.db.query(Response).filter(Response.id.in_(response_ids)).all()
                }
                
                # Separate into updates and inserts
                to_update = []
                to_insert = []
                
                for response_data in batch:
                    response_id = response_data.get("id")
                    if not response_id:
                        continue
                    
                    final_brand_id = brand_id or response_data.get("brand_id")
                    
                    # Extract data
                    citations = response_data.get("citations", [])
                    competitors_present = response_data.get("competitors_present", [])
                    if not isinstance(competitors_present, list):
                        competitors_present = []
                    competitors = response_data.get("competitors", [])
        
                    if response_id in existing_responses:
                        # Update existing
                        existing = existing_responses[response_id]
                        existing.brand_id = final_brand_id
                        existing.prompt_id = response_data.get("prompt_id")
                        existing.prompt = response_data.get("prompt")
                        existing.response_text = response_data.get("response_text")
                        existing.platform = response_data.get("platform")
                        existing.country = response_data.get("country")
                        existing.persona_id = response_data.get("persona_id")
                        existing.persona_name = response_data.get("persona_name")
                        existing.stage = response_data.get("stage")
                        existing.branded = response_data.get("branded")
                        existing.tags = response_data.get("tags", [])
                        existing.key_topics = response_data.get("key_topics", [])
                        existing.brand_present = response_data.get("brand_present")
                        existing.brand_sentiment = response_data.get("brand_sentiment")
                        existing.brand_position = response_data.get("brand_position")
                        existing.competitors_present = competitors_present
                        existing.competitors = competitors
                        existing.citations = citations
                        if response_data.get("created_at"):
                            existing.created_at = response_data.get("created_at")
                        to_update.append(existing)
                    else:
                        # Insert new
                        to_insert.append(Response(
                            id=response_id,
                            brand_id=final_brand_id,
                            prompt_id=response_data.get("prompt_id"),
                            prompt=response_data.get("prompt"),
                            response_text=response_data.get("response_text"),
                            platform=response_data.get("platform"),
                            country=response_data.get("country"),
                            persona_id=response_data.get("persona_id"),
                            persona_name=response_data.get("persona_name"),
                            stage=response_data.get("stage"),
                            branded=response_data.get("branded"),
                            tags=response_data.get("tags", []),
                            key_topics=response_data.get("key_topics", []),
                            brand_present=response_data.get("brand_present"),
                            brand_sentiment=response_data.get("brand_sentiment"),
                            brand_position=response_data.get("brand_position"),
                            competitors_present=competitors_present,
                            competitors=competitors,
                            citations=citations,
                            created_at=response_data.get("created_at")
                        ))
                
                # Bulk add new responses
                if to_insert:
                    self.db.bulk_save_objects(to_insert)
                
                # Commit batch once
                self.db.commit()
                total_upserted += len(batch)
                logger.info(f"Upserted batch {i//batch_size + 1}: {len(batch)} responses ({len(to_update)} updated, {len(to_insert)} inserted)")
            
            logger.info(f"Total upserted {total_upserted} responses")
            return total_upserted
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error upserting responses: {str(e)}")
            raise
    
    def upsert_citations(self, responses: List[Dict]) -> int:
        """Upsert citations separately - Optimized with bulk operations"""
        if not responses:
            return 0
        
        try:
            # Collect all citations with their response_ids
            all_citations = []
            for response_data in responses:
                response_id = response_data.get("id")
                if not response_id:
                    continue
                citations = response_data.get("citations", [])
                for citation_data in citations:
                    all_citations.append({
                        "response_id": response_id,
                        "url": citation_data.get("url"),
                        "domain": citation_data.get("domain"),
                        "source_type": citation_data.get("source_type"),
                        "title": citation_data.get("title"),
                        "snippet": citation_data.get("snippet")
                    })
            
            if not all_citations:
                return 0
            
            # Build lookup keys for bulk fetch
            citation_keys = [(c["response_id"], c["url"]) for c in all_citations if c.get("url")]
            
            # Bulk fetch existing citations
            existing_citations = {}
            if citation_keys:
                # Fetch in batches to avoid IN clause limits
                batch_size = 1000
                for i in range(0, len(citation_keys), batch_size):
                    batch_keys = citation_keys[i:i + batch_size]
                    # Build OR conditions for batch
                    conditions = []
                    for response_id, url in batch_keys:
                        conditions.append(
                            and_(Citation.response_id == response_id, Citation.url == url)
                        )
                    if conditions:
                        batch_existing = self.db.query(Citation).filter(or_(*conditions)).all()
                        for cit in batch_existing:
                            existing_citations[(cit.response_id, cit.url)] = cit
            
            # Separate into updates and inserts
            to_update = []
            to_insert = []
            
            for citation_data in all_citations:
                key = (citation_data["response_id"], citation_data["url"])
                if key in existing_citations:
                    # Update existing
                    existing = existing_citations[key]
                    existing.domain = citation_data.get("domain")
                    existing.source_type = citation_data.get("source_type")
                    existing.title = citation_data.get("title")
                    existing.snippet = citation_data.get("snippet")
                    to_update.append(existing)
                else:
                    # Insert new
                    to_insert.append(Citation(
                        response_id=citation_data["response_id"],
                        url=citation_data["url"],
                        domain=citation_data.get("domain"),
                        source_type=citation_data.get("source_type"),
                        title=citation_data.get("title"),
                        snippet=citation_data.get("snippet")
                    ))
            
            # Bulk add new citations
            if to_insert:
                self.db.bulk_save_objects(to_insert)
            
            # Commit once for all changes
            self.db.commit()
            
            count = len(to_update) + len(to_insert)
            logger.info(f"Upserted {count} citations ({len(to_update)} updated, {len(to_insert)} inserted)")
            return count
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error upserting citations: {str(e)}")
            raise
    
    # =====================================================
    # Query Methods (for API endpoints)
    # =====================================================
    
    def get_brands(self, limit: Optional[int] = None, offset: Optional[int] = None, search: Optional[str] = None) -> Dict:
        """Get brands with optional search and pagination"""
        try:
            query = self.db.query(Brand)
            
            # Apply search filter
            if search and search.strip():
                search_term = f"%{search.strip()}%"
                query = query.filter(Brand.name.ilike(search_term))
            
            # Get total count
            total_count = query.count()
            
            # Apply ordering
            query = query.order_by(Brand.name.asc())
            
            # Apply pagination
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            
            items = query.all()
            items_dict = [
                {
                    "id": item.id,
                    "name": item.name,
                    "website": item.website,
                    "ga4_property_id": item.ga4_property_id,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                    "version": item.version,
                    "last_modified_by": item.last_modified_by,
                    "slug": getattr(item, 'slug', None),
                    "logo_url": getattr(item, 'logo_url', None),
                    "theme": getattr(item, 'theme', None)
                }
                for item in items
            ]
            
            return {
                "items": items_dict,
                "count": len(items_dict),
                "total_count": total_count
            }
        except Exception as e:
            logger.error(f"Error getting brands: {str(e)}")
            raise
    
    def get_brand_by_id(self, brand_id: int) -> Optional[Dict]:
        """Get a single brand by ID"""
        try:
            brand = self.db.query(Brand).filter(Brand.id == brand_id).first()
            if not brand:
                return None
            
            return {
                "id": brand.id,
                "name": brand.name,
                "website": brand.website,
                "ga4_property_id": brand.ga4_property_id,
                "created_at": brand.created_at.isoformat() if brand.created_at else None,
                "version": brand.version,
                "last_modified_by": brand.last_modified_by,
                "slug": getattr(brand, 'slug', None),
                "logo_url": getattr(brand, 'logo_url', None),
                "theme": getattr(brand, 'theme', None)
            }
        except Exception as e:
            logger.error(f"Error getting brand by ID: {str(e)}")
            raise
    
    def get_brand_by_slug(self, slug: str) -> Optional[Dict]:
        """Get a single brand by slug"""
        try:
            brand = self.db.query(Brand).filter(Brand.slug == slug).first()
            if not brand:
                return None
            
            return {
                "id": brand.id,
                "name": brand.name,
                "website": brand.website,
                "ga4_property_id": brand.ga4_property_id,
                "created_at": brand.created_at.isoformat() if brand.created_at else None,
                "version": brand.version,
                "last_modified_by": brand.last_modified_by,
                "slug": getattr(brand, 'slug', None),
                "logo_url": getattr(brand, 'logo_url', None),
                "theme": getattr(brand, 'theme', None)
            }
        except Exception as e:
            logger.error(f"Error getting brand by slug: {str(e)}")
            raise
    
    def get_brands_with_ga4(self) -> List[Dict]:
        """Get all brands that have GA4 property IDs configured"""
        try:
            brands = self.db.query(Brand).filter(Brand.ga4_property_id.isnot(None)).all()
            return [
                {
                    "id": brand.id,
                    "name": brand.name,
                    "website": brand.website,
                    "ga4_property_id": brand.ga4_property_id,
                    "created_at": brand.created_at.isoformat() if brand.created_at else None,
                    "version": brand.version,
                    "last_modified_by": brand.last_modified_by,
                    "slug": getattr(brand, 'slug', None),
                    "logo_url": getattr(brand, 'logo_url', None),
                    "theme": getattr(brand, 'theme', None)
                }
                for brand in brands
            ]
        except Exception as e:
            logger.error(f"Error getting brands with GA4: {str(e)}")
            raise
    
    def get_sync_status_counts(self) -> Dict:
        """Get counts of synced data for status endpoint - Optimized with single query"""
        try:
            # Use a single query with UNION ALL for better performance
            # This reduces database round trips from 4 to 1
            query = text("""
                SELECT 
                    (SELECT COUNT(*) FROM brands) as brands_count,
                    (SELECT COUNT(*) FROM prompts) as prompts_count,
                    (SELECT COUNT(*) FROM responses) as responses_count,
                    (SELECT COUNT(*) FROM clients) as clients_count
            """)
            result = self.db.execute(query).first()
            
            return {
                "brands_count": result.brands_count or 0,
                "prompts_count": result.prompts_count or 0,
                "responses_count": result.responses_count or 0,
                "clients_count": result.clients_count or 0
            }
        except Exception as e:
            logger.error(f"Error getting sync status counts: {str(e)}")
            raise
    
    def get_prompts(
        self,
        brand_id: Optional[int] = None,
        stage: Optional[str] = None,
        persona_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> Dict:
        """Get prompts with optional filters and pagination"""
        try:
            from datetime import datetime as dt

            def _parse_date(value: str, is_end: bool = False):
                """Normalize date strings to timezone-aware boundaries."""
                if "T" in value:
                    return dt.fromisoformat(value.replace("Z", "+00:00"))
                suffix = "23:59:59+00:00" if is_end else "00:00:00+00:00"
                return dt.fromisoformat(f"{value}T{suffix}")

            query = self.db.query(Prompt)
            
            # Apply filters
            if brand_id:
                query = query.filter(Prompt.brand_id == brand_id)
            if stage:
                query = query.filter(Prompt.stage == stage)
            if persona_id:
                query = query.filter(Prompt.persona_id == persona_id)
            if start_date:
                start_dt = _parse_date(start_date, is_end=False)
                query = query.filter(Prompt.created_at >= start_dt)
            if end_date:
                end_dt = _parse_date(end_date, is_end=True)
                query = query.filter(Prompt.created_at <= end_dt)
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            
            items = query.all()
            items_dict = [
                {
                    "id": item.id,
                    "brand_id": item.brand_id,
                    "text": item.text,
                    "stage": item.stage,
                    "persona_id": item.persona_id,
                    "persona_name": item.persona_name,
                    "platforms": item.platforms,
                    "tags": item.tags,
                    "topics": item.topics,
                    "created_at": item.created_at.isoformat() if item.created_at else None
                }
                for item in items
            ]
            
            return {
                "items": items_dict,
                "count": len(items_dict),
                "total_count": total_count
            }
        except Exception as e:
            logger.error(f"Error getting prompts: {str(e)}")
            raise
    
    def get_responses(
        self,
        brand_id: Optional[int] = None,
        platform: Optional[str] = None,
        prompt_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> Dict:
        """Get responses with optional filters and pagination"""
        try:
            from datetime import datetime as dt

            def _parse_date(value: str, is_end: bool = False):
                """Normalize date strings to timezone-aware boundaries."""
                if "T" in value:
                    return dt.fromisoformat(value.replace("Z", "+00:00"))
                suffix = "23:59:59+00:00" if is_end else "00:00:00+00:00"
                return dt.fromisoformat(f"{value}T{suffix}")

            # Query responses (citations is a JSON column, not a relationship)
            query = self.db.query(Response)
            
            # Apply filters
            if brand_id:
                query = query.filter(Response.brand_id == brand_id)
            if platform:
                query = query.filter(Response.platform == platform)
            if prompt_id:
                query = query.filter(Response.prompt_id == prompt_id)
            if start_date:
                start_dt = _parse_date(start_date, is_end=False)
                query = query.filter(Response.created_at >= start_dt)
            if end_date:
                end_dt = _parse_date(end_date, is_end=True)
                query = query.filter(Response.created_at <= end_dt)
            
            # Get total count (before pagination for accuracy)
            total_count = query.count()
            
            # Apply pagination
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            
            # Execute query
            items = query.all()
            
            # Convert to dict format (citations is a JSON column)
            items_dict = [
                {
                    "id": item.id,
                    "brand_id": item.brand_id,
                    "prompt_id": item.prompt_id,
                    "prompt": item.prompt,
                    "response_text": item.response_text,
                    "platform": item.platform,
                    "country": item.country,
                    "persona_id": item.persona_id,
                    "persona_name": item.persona_name,
                    "stage": item.stage,
                    "branded": item.branded,
                    "tags": item.tags,
                    "key_topics": item.key_topics,
                    "brand_present": item.brand_present,
                    "brand_sentiment": item.brand_sentiment,
                    "brand_position": item.brand_position,
                    "competitors_present": item.competitors_present,
                    "competitors": item.competitors,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                    "citations": item.citations if item.citations else []  # citations is a JSON column
                }
                for item in items
            ]
            
            return {
                "items": items_dict,
                "count": len(items_dict),
                "total_count": total_count
            }
        except Exception as e:
            logger.error(f"Error getting responses: {str(e)}")
            raise
    
    def get_clients(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        search: Optional[str] = None
    ) -> Dict:
        """Get clients with optional search and pagination"""
        try:
            # Build query using SQLAlchemy Core
            table = self._get_table("clients")
            query = select(table)
            
            # Apply search filter
            if search and search.strip():
                search_term = f"%{search.strip()}%"
                query = query.where(
                    or_(
                        table.c.company_name.ilike(search_term),
                        table.c.company_domain.ilike(search_term),
                        table.c.url.ilike(search_term)
                    )
                )
            
            # Get total count
            count_query = select(func.count()).select_from(query.alias())
            total_count = self.db.execute(count_query).scalar()
            
            # Apply ordering
            query = query.order_by(table.c.company_name.asc())
            
            # Apply pagination
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            
            result = self.db.execute(query)
            items = [dict(row._mapping) for row in result]
            
            return {
                "items": items,
                "count": len(items),
                "total_count": total_count
            }
        except Exception as e:
            logger.error(f"Error getting clients: {str(e)}")
            raise
    
    # =====================================================
    # GA4 Data Sync Methods
    # =====================================================
    
    def get_ga4_traffic_overview_by_date_range(self, brand_id: int, property_id: str, start_date: str, end_date: str, client_id: Optional[int] = None) -> Optional[Dict]:
        """Get aggregated GA4 traffic overview data from stored daily records for a date range
        
        Supports querying by brand_id or client_id. If client_id is provided, it will be used as the primary filter.
        If no data is found for the specific client_id, falls back to querying by property_id only
        (since multiple clients can share the same GA4 property).
        """
        try:
            records = []
            # Get all daily records for the date range
            # If client_id is provided, query by client_id first; otherwise use brand_id
            if client_id is not None:
                # First, check how many records are available by property_id vs client_id
                count_query = text("""
                    SELECT 
                        COUNT(*) as total_count,
                        COUNT(CASE WHEN client_id = :client_id THEN 1 END) as matching_client_count
                    FROM ga4_traffic_overview
                    WHERE property_id = :property_id
                      AND date >= CAST(:start_date AS DATE)
                      AND date <= CAST(:end_date AS DATE)
                """)
                count_result = self.db.execute(count_query, {
                    "client_id": client_id,
                    "property_id": property_id,
                    "start_date": start_date,
                    "end_date": end_date
                })
                count_row = count_result.fetchone()
                total_available_by_property = count_row[0] if count_row else 0
                matching_client_count = count_row[1] if count_row else 0
                
                # Decide whether to query by client_id or use property_id directly
                # If there are significantly more records by property_id than by client_id, use property_id query
                use_property_id_query = False
                if total_available_by_property > 0:
                    if total_available_by_property > matching_client_count * 2:  # Threshold: if property has >2x records
                        logger.info(f"Using property_id query for traffic overview: {total_available_by_property} records available by property_id vs {matching_client_count} by client_id")
                        use_property_id_query = True
                
                if use_property_id_query:
                    # Query by property_id only, but deduplicate by date (prefer records matching client_id if available)
                    # Use DISTINCT ON to get one record per date, prioritizing client_id matches
                    query = text("""
                        SELECT DISTINCT ON (date) *
                        FROM ga4_traffic_overview
                        WHERE property_id = :property_id
                          AND date >= CAST(:start_date AS DATE)
                          AND date <= CAST(:end_date AS DATE)
                        ORDER BY date ASC, 
                                 CASE WHEN client_id = :client_id THEN 0 ELSE 1 END ASC
                    """)
                    result = self.db.execute(query, {
                        "property_id": property_id,
                        "client_id": client_id,
                        "start_date": start_date,
                        "end_date": end_date
                    })
                    records = [dict(row._mapping) for row in result]
                else:
                    # Query by client_id first - use DISTINCT ON to handle duplicate records with same client_id but different brand_id
                    query = text("""
                        SELECT DISTINCT ON (date) *
                        FROM ga4_traffic_overview
                        WHERE client_id = :client_id
                          AND property_id = :property_id
                          AND date >= CAST(:start_date AS DATE)
                          AND date <= CAST(:end_date AS DATE)
                        ORDER BY date ASC,
                                 CASE WHEN brand_id IS NOT NULL THEN 0 ELSE 1 END ASC
                    """)
                    result = self.db.execute(query, {
                        "client_id": client_id,
                        "property_id": property_id,
                        "start_date": start_date,
                        "end_date": end_date
                    })
                    records = [dict(row._mapping) for row in result]
                    
                    # If no records found for this specific client_id, fall back to property_id only
                    # (data is shared across clients with the same property)
                    # Deduplicate by date to prevent double-counting when multiple clients share the same property
                    if not records:
                        logger.info(f"No GA4 traffic overview data found for client_id={client_id}, falling back to property_id={property_id} query (with deduplication)")
                        query = text("""
                            SELECT DISTINCT ON (date) *
                            FROM ga4_traffic_overview
                            WHERE property_id = :property_id
                              AND date >= CAST(:start_date AS DATE)
                              AND date <= CAST(:end_date AS DATE)
                            ORDER BY date ASC,
                                     CASE WHEN client_id = :client_id THEN 0 ELSE 1 END ASC
                        """)
                        result = self.db.execute(query, {
                            "property_id": property_id,
                            "client_id": client_id,
                            "start_date": start_date,
                            "end_date": end_date
                        })
                        records = [dict(row._mapping) for row in result]
            else:
                query = text("""
                    SELECT * FROM ga4_traffic_overview
                    WHERE brand_id = :brand_id
                      AND property_id = :property_id
                      AND date >= CAST(:start_date AS DATE)
                      AND date <= CAST(:end_date AS DATE)
                    ORDER BY date ASC
                """)
                result = self.db.execute(query, {
                    "brand_id": brand_id,
                    "property_id": property_id,
                    "start_date": start_date,
                    "end_date": end_date
                })
                records = [dict(row._mapping) for row in result]
            
            if not records:
                return None
            
            # Aggregate the daily data
            total_users = sum(int(r.get("users", 0) or 0) for r in records)
            total_sessions = sum(int(r.get("sessions", 0) or 0) for r in records)
            total_new_users = sum(int(r.get("new_users", 0) or 0) for r in records)
            total_engaged_sessions = sum(int(r.get("engaged_sessions", 0) or 0) for r in records)
            total_conversions = sum(float(r.get("conversions", 0) or 0) for r in records)
            total_revenue = sum(float(r.get("revenue", 0) or 0) for r in records)
            
            # Calculate weighted averages for rates
            total_session_duration = sum(float(r.get("average_session_duration", 0) or 0) * int(r.get("sessions", 0) or 0) for r in records)
            avg_session_duration = total_session_duration / total_sessions if total_sessions > 0 else 0
            
            # Calculate bounce rate (weighted average)
            total_bounce_sessions = sum((1 - float(r.get("engagement_rate", 0) or 0)) * int(r.get("sessions", 0) or 0) for r in records)
            bounce_rate = total_bounce_sessions / total_sessions if total_sessions > 0 else 0
            
            # Calculate engagement rate (weighted average)
            total_engagement_weight = sum(float(r.get("engagement_rate", 0) or 0) * int(r.get("sessions", 0) or 0) for r in records)
            engagement_rate = total_engagement_weight / total_sessions if total_sessions > 0 else 0
            
            return {
                "users": total_users,
                "sessions": total_sessions,
                "newUsers": total_new_users,
                "engagedSessions": total_engaged_sessions,
                "averageSessionDuration": avg_session_duration,
                "bounceRate": bounce_rate,
                "engagementRate": engagement_rate,
                "conversions": total_conversions,
                "revenue": total_revenue
            }
        except Exception as e:
            logger.error(f"Error getting GA4 traffic overview from stored data: {str(e)}")
            return None
    
    def upsert_ga4_traffic_overview(self, property_id: str, date: str, data: Dict, client_id: Optional[int] = None, brand_id: Optional[int] = None) -> int:
        """Upsert GA4 traffic overview data - now uses client_id (with brand_id for backward compatibility)"""
        if client_id is None and brand_id is None:
            raise ValueError("Either client_id or brand_id must be provided")
        
        try:
            # If client_id is provided but brand_id is not, get brand_id from client
            if client_id is not None and brand_id is None:
                client_query = text("SELECT scrunch_brand_id FROM clients WHERE id = :client_id")
                result = self.db.execute(client_query, {"client_id": client_id})
                row = result.first()
                if row:
                    brand_id = row[0]
            
            entity_id = client_id if client_id is not None else brand_id
            entity_type = "client" if client_id is not None else "brand"
            
            # Use PostgreSQL INSERT ... ON CONFLICT for upsert
            # Unique constraint is on (brand_id, property_id, date)
            query = text("""
                INSERT INTO ga4_traffic_overview (
                    brand_id, client_id, property_id, date,
                    users, sessions, new_users, bounce_rate,
                    average_session_duration, engaged_sessions, engagement_rate,
                    sessions_change, engaged_sessions_change, avg_session_duration_change,
                    engagement_rate_change, conversions, revenue, updated_at
                ) VALUES (
                    :brand_id, :client_id, :property_id, :date,
                    :users, :sessions, :new_users, :bounce_rate,
                    :average_session_duration, :engaged_sessions, :engagement_rate,
                    :sessions_change, :engaged_sessions_change, :avg_session_duration_change,
                    :engagement_rate_change, :conversions, :revenue, NOW()
                )
                ON CONFLICT (brand_id, property_id, date)
                DO UPDATE SET
                    client_id = EXCLUDED.client_id,
                    users = EXCLUDED.users,
                    sessions = EXCLUDED.sessions,
                    new_users = EXCLUDED.new_users,
                    bounce_rate = EXCLUDED.bounce_rate,
                    average_session_duration = EXCLUDED.average_session_duration,
                    engaged_sessions = EXCLUDED.engaged_sessions,
                    engagement_rate = EXCLUDED.engagement_rate,
                    sessions_change = EXCLUDED.sessions_change,
                    engaged_sessions_change = EXCLUDED.engaged_sessions_change,
                    avg_session_duration_change = EXCLUDED.avg_session_duration_change,
                    engagement_rate_change = EXCLUDED.engagement_rate_change,
                    conversions = EXCLUDED.conversions,
                    revenue = EXCLUDED.revenue,
                    updated_at = NOW()
            """)
            
            self.db.execute(query, {
                "brand_id": brand_id,
                "client_id": client_id,
                "property_id": property_id,
                "date": date,
                "users": data.get("users", 0),
                "sessions": data.get("sessions", 0),
                "new_users": data.get("newUsers", 0),
                "bounce_rate": data.get("bounceRate", 0),
                "average_session_duration": data.get("averageSessionDuration", 0),
                "engaged_sessions": data.get("engagedSessions", 0),
                "engagement_rate": data.get("engagementRate", 0),
                "sessions_change": data.get("sessionsChange", 0),
                "engaged_sessions_change": data.get("engagedSessionsChange", 0),
                "avg_session_duration_change": data.get("avgSessionDurationChange", 0),
                "engagement_rate_change": data.get("engagementRateChange", 0),
                "conversions": data.get("conversions", 0),
                "revenue": data.get("revenue", 0)
            })
            self.db.commit()
            logger.info(f"Upserted GA4 traffic overview for {entity_type} {entity_id}, property {property_id}, date {date}")
            return 1
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error upserting GA4 traffic overview: {str(e)}")
            raise
    
    def upsert_ga4_top_pages(self, property_id: str, date: str, pages: List[Dict], client_id: Optional[int] = None, brand_id: Optional[int] = None) -> int:
        """Upsert GA4 top pages data using SQLAlchemy Core (local PostgreSQL)"""
        if client_id is None and brand_id is None:
            raise ValueError("Either client_id or brand_id must be provided")
        if not pages:
            return 0
        
        entity_id = client_id if client_id is not None else brand_id
        entity_type = "client" if client_id is not None else "brand"
        
        try:
            table = self._get_table("ga4_top_pages")
            
            # Delete existing records for this date first, then insert new ones
            # This ensures we don't have stale data from previous syncs
            delete_conditions = [
                table.c.property_id == property_id,
                table.c.date == date
            ]
            if client_id is not None:
                delete_conditions.append(table.c.client_id == client_id)
            if brand_id is not None:
                delete_conditions.append(table.c.brand_id == brand_id)
            
            delete_stmt = delete(table).where(and_(*delete_conditions))
            self.db.execute(delete_stmt)
            self.db.commit()
        except Exception as delete_error:
            self.db.rollback()
            logger.warning(f"Error deleting existing top pages (may not exist): {str(delete_error)}")
        
        # Prepare records
        records = []
        for idx, page in enumerate(pages):
            record = {
                "property_id": property_id,
                "date": date,
                "page_path": page.get("pagePath", ""),
                "views": page.get("views", 0),
                "users": page.get("users", 0),
                "avg_session_duration": page.get("avgSessionDuration", 0),
                "rank": idx + 1,
                "updated_at": datetime.now()
            }
            if client_id is not None:
                record["client_id"] = client_id
            if brand_id is not None:
                record["brand_id"] = brand_id
            records.append(record)
        
        try:
            # Bulk insert using ON CONFLICT - process in larger batches
            batch_size = 500  # Increased from 50 for better performance
            total_inserted = 0
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                # Bulk insert all records at once
                insert_stmt = pg_insert(table).values(batch)
                insert_stmt = insert_stmt.on_conflict_do_update(
                    index_elements=['brand_id', 'property_id', 'date', 'page_path'],
                    set_={
                        'views': insert_stmt.excluded.views,
                        'users': insert_stmt.excluded.users,
                        'avg_session_duration': insert_stmt.excluded.avg_session_duration,
                        'rank': insert_stmt.excluded.rank,
                        'updated_at': insert_stmt.excluded.updated_at
                    }
                )
                self.db.execute(insert_stmt)
                self.db.commit()
                total_inserted += len(batch)
            
            logger.info(f"Upserted {total_inserted} GA4 top pages for {entity_type} {entity_id}, property {property_id}, date {date}")
            return total_inserted
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error upserting GA4 top pages: {str(e)}")
            raise
    
    def upsert_ga4_traffic_sources(self, property_id: str, date: str, sources: List[Dict], client_id: Optional[int] = None, brand_id: Optional[int] = None) -> int:
        """Upsert GA4 traffic sources data using SQLAlchemy Core (local PostgreSQL)"""
        if client_id is None and brand_id is None:
            raise ValueError("Either client_id or brand_id must be provided")
        if not sources:
            return 0
        
        entity_id = client_id if client_id is not None else brand_id
        entity_type = "client" if client_id is not None else "brand"
        
        try:
            table = self._get_table("ga4_traffic_sources")
            
            # Delete existing records for this date first
            delete_conditions = [
                table.c.property_id == property_id,
                table.c.date == date
            ]
            if client_id is not None:
                delete_conditions.append(table.c.client_id == client_id)
            if brand_id is not None:
                delete_conditions.append(table.c.brand_id == brand_id)
            
            delete_stmt = delete(table).where(and_(*delete_conditions))
            self.db.execute(delete_stmt)
            self.db.commit()
        except Exception as delete_error:
            self.db.rollback()
            logger.warning(f"Error deleting existing traffic sources (may not exist): {str(delete_error)}")
        
        records = []
        for source in sources:
            record = {
                "property_id": property_id,
                "date": date,
                "source": source.get("source", ""),
                "sessions": source.get("sessions", 0),
                "users": source.get("users", 0),
                "bounce_rate": source.get("bounceRate", 0),
                "updated_at": datetime.now()
            }
            if client_id is not None:
                record["client_id"] = client_id
            if brand_id is not None:
                record["brand_id"] = brand_id
            records.append(record)
        
        try:
            # Bulk insert using ON CONFLICT - process in batches
            batch_size = 500
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                insert_stmt = pg_insert(table).values(batch)
                insert_stmt = insert_stmt.on_conflict_do_update(
                    index_elements=['brand_id', 'property_id', 'date', 'source'],
                    set_={
                        'sessions': insert_stmt.excluded.sessions,
                        'users': insert_stmt.excluded.users,
                        'bounce_rate': insert_stmt.excluded.bounce_rate,
                        'updated_at': insert_stmt.excluded.updated_at
                    }
                )
                self.db.execute(insert_stmt)
            self.db.commit()
            
            logger.info(f"Upserted {len(records)} GA4 traffic sources for {entity_type} {entity_id}, property {property_id}, date {date}")
            return len(records)
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error upserting GA4 traffic sources: {str(e)}")
            raise
    
    def upsert_ga4_geographic(self, property_id: str, date: str, geographic: List[Dict], client_id: Optional[int] = None, brand_id: Optional[int] = None) -> int:
        """Upsert GA4 geographic data using SQLAlchemy Core (local PostgreSQL)"""
        if client_id is None and brand_id is None:
            raise ValueError("Either client_id or brand_id must be provided")
        if not geographic:
            return 0
        
        entity_id = client_id if client_id is not None else brand_id
        entity_type = "client" if client_id is not None else "brand"
        
        try:
            table = self._get_table("ga4_geographic")
            
            # Delete existing records for this date first
            delete_conditions = [
                table.c.property_id == property_id,
                table.c.date == date
            ]
            if client_id is not None:
                delete_conditions.append(table.c.client_id == client_id)
            if brand_id is not None:
                delete_conditions.append(table.c.brand_id == brand_id)
            
            delete_stmt = delete(table).where(and_(*delete_conditions))
            self.db.execute(delete_stmt)
            self.db.commit()
        except Exception as delete_error:
            self.db.rollback()
            logger.warning(f"Error deleting existing geographic data (may not exist): {str(delete_error)}")
        
        records = []
        for geo in geographic:
            record = {
                "property_id": property_id,
                "date": date,
                "country": geo.get("country", ""),
                "users": geo.get("users", 0),
                "sessions": geo.get("sessions", 0),
                "updated_at": datetime.now()
            }
            if client_id is not None:
                record["client_id"] = client_id
            if brand_id is not None:
                record["brand_id"] = brand_id
            records.append(record)
        
        try:
            # Bulk insert using ON CONFLICT - process in batches
            batch_size = 500
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                insert_stmt = pg_insert(table).values(batch)
                insert_stmt = insert_stmt.on_conflict_do_update(
                    index_elements=['brand_id', 'property_id', 'date', 'country'],
                    set_={
                        'users': insert_stmt.excluded.users,
                        'sessions': insert_stmt.excluded.sessions,
                        'updated_at': insert_stmt.excluded.updated_at
                    }
                )
                self.db.execute(insert_stmt)
            self.db.commit()
            
            logger.info(f"Upserted {len(records)} GA4 geographic records for {entity_type} {entity_id}, property {property_id}, date {date}")
            return len(records)
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error upserting GA4 geographic: {str(e)}")
            raise
    
    def upsert_ga4_devices(self, property_id: str, date: str, devices: List[Dict], client_id: Optional[int] = None, brand_id: Optional[int] = None) -> int:
        """Upsert GA4 devices data using SQLAlchemy Core (local PostgreSQL)"""
        if client_id is None and brand_id is None:
            raise ValueError("Either client_id or brand_id must be provided")
        if not devices:
            return 0
        
        entity_id = client_id if client_id is not None else brand_id
        entity_type = "client" if client_id is not None else "brand"
        
        try:
            table = self._get_table("ga4_devices")
            
            # Delete existing records for this date first
            delete_conditions = [
                table.c.property_id == property_id,
                table.c.date == date
            ]
            if client_id is not None:
                delete_conditions.append(table.c.client_id == client_id)
            if brand_id is not None:
                delete_conditions.append(table.c.brand_id == brand_id)
            
            delete_stmt = delete(table).where(and_(*delete_conditions))
            self.db.execute(delete_stmt)
            self.db.commit()
        except Exception as delete_error:
            self.db.rollback()
            logger.warning(f"Error deleting existing devices data (may not exist): {str(delete_error)}")
        
        records = []
        for device in devices:
            record = {
                "property_id": property_id,
                "date": date,
                "device_category": device.get("deviceCategory", ""),
                "operating_system": device.get("operatingSystem", ""),
                "users": device.get("users", 0),
                "sessions": device.get("sessions", 0),
                "bounce_rate": device.get("bounceRate", 0),
                "updated_at": datetime.now()
            }
            if client_id is not None:
                record["client_id"] = client_id
            if brand_id is not None:
                record["brand_id"] = brand_id
            records.append(record)
        
        try:
            # Bulk insert using ON CONFLICT - process in batches
            batch_size = 500
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                insert_stmt = pg_insert(table).values(batch)
                insert_stmt = insert_stmt.on_conflict_do_update(
                    index_elements=['brand_id', 'property_id', 'date', 'device_category', 'operating_system'],
                    set_={
                        'users': insert_stmt.excluded.users,
                        'sessions': insert_stmt.excluded.sessions,
                        'bounce_rate': insert_stmt.excluded.bounce_rate,
                        'updated_at': insert_stmt.excluded.updated_at
                    }
                )
                self.db.execute(insert_stmt)
            self.db.commit()
            
            logger.info(f"Upserted {len(records)} GA4 devices for {entity_type} {entity_id}, property {property_id}, date {date}")
            return len(records)
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error upserting GA4 devices: {str(e)}")
            raise
    
    def upsert_ga4_conversions(self, property_id: str, date: str, conversions: List[Dict], client_id: Optional[int] = None, brand_id: Optional[int] = None) -> int:
        """Upsert GA4 conversions data using SQLAlchemy Core (local PostgreSQL)"""
        if client_id is None and brand_id is None:
            raise ValueError("Either client_id or brand_id must be provided")
        if not conversions:
            return 0
        
        entity_id = client_id if client_id is not None else brand_id
        entity_type = "client" if client_id is not None else "brand"
        
        try:
            table = self._get_table("ga4_conversions")
            
            # Delete existing records for this date first
            delete_conditions = [
                table.c.property_id == property_id,
                table.c.date == date
            ]
            if client_id is not None:
                delete_conditions.append(table.c.client_id == client_id)
            if brand_id is not None:
                delete_conditions.append(table.c.brand_id == brand_id)
            
            delete_stmt = delete(table).where(and_(*delete_conditions))
            self.db.execute(delete_stmt)
            self.db.commit()
        except Exception as delete_error:
            self.db.rollback()
            logger.warning(f"Error deleting existing conversions data (may not exist): {str(delete_error)}")
        
        records = []
        for conversion in conversions:
            record = {
                "property_id": property_id,
                "date": date,
                "event_name": conversion.get("eventName", ""),
                "event_count": conversion.get("count", 0),
                "users": conversion.get("users", 0),
                "updated_at": datetime.now()
            }
            if client_id is not None:
                record["client_id"] = client_id
            if brand_id is not None:
                record["brand_id"] = brand_id
            records.append(record)
        
        try:
            # Bulk insert using ON CONFLICT - process in batches
            batch_size = 500
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                insert_stmt = pg_insert(table).values(batch)
                insert_stmt = insert_stmt.on_conflict_do_update(
                    index_elements=['brand_id', 'property_id', 'date', 'event_name'],
                    set_={
                        'event_count': insert_stmt.excluded.event_count,
                        'users': insert_stmt.excluded.users,
                        'updated_at': insert_stmt.excluded.updated_at
                    }
                )
                self.db.execute(insert_stmt)
            self.db.commit()
            
            logger.info(f"Upserted {len(records)} GA4 conversions for {entity_type} {entity_id}, property {property_id}, date {date}")
            return len(records)
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error upserting GA4 conversions: {str(e)}")
            raise
    
    def upsert_ga4_realtime(self, property_id: str, realtime_data: Dict, client_id: Optional[int] = None, brand_id: Optional[int] = None) -> int:
        """Upsert GA4 realtime data using SQLAlchemy Core (local PostgreSQL)"""
        if client_id is None and brand_id is None:
            raise ValueError("Either client_id or brand_id must be provided")
        
        try:
            table = self._get_table("ga4_realtime")
            snapshot_time = datetime.now()
            
            entity_id = client_id if client_id is not None else brand_id
            entity_type = "client" if client_id is not None else "brand"
            
            record = {
                "property_id": property_id,
                "snapshot_time": snapshot_time,
                "total_active_users": realtime_data.get("totalActiveUsers", 0),
                "active_pages": realtime_data.get("activePages", []),
            }
            
            if client_id is not None:
                record["client_id"] = client_id
            if brand_id is not None:
                record["brand_id"] = brand_id
            
            # Use PostgreSQL INSERT ... ON CONFLICT for upsert
            insert_stmt = pg_insert(table).values(**record)
            insert_stmt = insert_stmt.on_conflict_do_update(
                index_elements=['brand_id', 'property_id', 'snapshot_time'],
                set_={
                    'client_id': insert_stmt.excluded.client_id,
                    'total_active_users': insert_stmt.excluded.total_active_users,
                    'active_pages': insert_stmt.excluded.active_pages
                }
            )
            
            self.db.execute(insert_stmt)
            self.db.commit()
            logger.info(f"Upserted GA4 realtime data for {entity_type} {entity_id}, property {property_id}")
            return 1
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error upserting GA4 realtime: {str(e)}")
            raise
    
    def upsert_ga4_property_details(self, property_id: str, property_details: Dict, client_id: Optional[int] = None, brand_id: Optional[int] = None) -> int:
        """Upsert GA4 property details using SQLAlchemy Core (local PostgreSQL)"""
        if client_id is None and brand_id is None:
            raise ValueError("Either client_id or brand_id must be provided")
        
        try:
            table = self._get_table("ga4_property_details")
            
            entity_id = client_id if client_id is not None else brand_id
            entity_type = "client" if client_id is not None else "brand"
            
            record = {
                "property_id": property_id,
                "display_name": property_details.get("displayName"),
                "time_zone": property_details.get("timeZone"),
                "currency_code": property_details.get("currencyCode"),
                "create_time": self._parse_datetime(property_details.get("createTime")),
                "updated_at": datetime.now()
            }
            
            if client_id is not None:
                record["client_id"] = client_id
            if brand_id is not None:
                record["brand_id"] = brand_id
            
            # Remove None values
            clean_record = {k: v for k, v in record.items() if v is not None}
            
            # Use PostgreSQL INSERT ... ON CONFLICT for upsert
            # The unique constraint is on (brand_id, property_id)
            # If brand_id is provided, use the unique constraint
            # If only client_id is provided, check for existing record by property_id and update/insert accordingly
            if brand_id is not None:
                # Use the unique constraint on (brand_id, property_id)
                insert_stmt = pg_insert(table).values(**clean_record)
                insert_stmt = insert_stmt.on_conflict_do_update(
                    index_elements=['brand_id', 'property_id'],
                    set_={
                        'client_id': insert_stmt.excluded.client_id,
                        'display_name': insert_stmt.excluded.display_name,
                        'time_zone': insert_stmt.excluded.time_zone,
                        'currency_code': insert_stmt.excluded.currency_code,
                        'create_time': insert_stmt.excluded.create_time,
                        'updated_at': insert_stmt.excluded.updated_at
                    }
                )
                self.db.execute(insert_stmt)
                self.db.commit()
                logger.info(f"Upserted GA4 property details for {entity_type} {entity_id}, property {property_id}")
                return 1
            else:
                # Only client_id provided, check for existing record by property_id
                existing = self.db.execute(
                    select(table).where(table.c.property_id == property_id)
                ).first()
                if existing:
                    # Update existing record
                    update_stmt = update(table).where(
                        table.c.property_id == property_id
                    ).values(**clean_record)
                    self.db.execute(update_stmt)
                    self.db.commit()
                    logger.info(f"Updated GA4 property details for {entity_type} {entity_id}, property {property_id}")
                    return 1
                else:
                    # Insert new record
                    insert_stmt = insert(table).values(**clean_record)
                    self.db.execute(insert_stmt)
                    self.db.commit()
                    logger.info(f"Inserted GA4 property details for {entity_type} {entity_id}, property {property_id}")
                    return 1
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error upserting GA4 property details: {str(e)}")
            raise
    
    def upsert_ga4_revenue(self, property_id: str, date: str, revenue: float, client_id: Optional[int] = None, brand_id: Optional[int] = None) -> int:
        """Upsert GA4 revenue data using SQLAlchemy Core (local PostgreSQL)"""
        if client_id is None and brand_id is None:
            raise ValueError("Either client_id or brand_id must be provided")
        
        try:
            table = self._get_table("ga4_revenue")
            
            entity_id = client_id if client_id is not None else brand_id
            entity_type = "client" if client_id is not None else "brand"
            
            record = {
                "property_id": property_id,
                "date": date,
                "total_revenue": revenue,
                "updated_at": datetime.now()
            }
            
            if client_id is not None:
                record["client_id"] = client_id
            if brand_id is not None:
                record["brand_id"] = brand_id
            
            # Use PostgreSQL INSERT ... ON CONFLICT for upsert
            insert_stmt = pg_insert(table).values(**record)
            insert_stmt = insert_stmt.on_conflict_do_update(
                index_elements=['brand_id', 'property_id', 'date'],
                set_={
                    'client_id': insert_stmt.excluded.client_id,
                    'total_revenue': insert_stmt.excluded.total_revenue,
                    'updated_at': insert_stmt.excluded.updated_at
                }
            )
            
            self.db.execute(insert_stmt)
            self.db.commit()
            logger.info(f"Upserted GA4 revenue for {entity_type} {entity_id}, property {property_id}, date {date}: {revenue}")
            return 1
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error upserting GA4 revenue: {str(e)}")
            raise
    
    def upsert_ga4_daily_conversions(self, property_id: str, date: str, total_conversions: float, client_id: Optional[int] = None, brand_id: Optional[int] = None) -> int:
        """Upsert GA4 daily conversions summary using SQLAlchemy Core (local PostgreSQL)"""
        if client_id is None and brand_id is None:
            raise ValueError("Either client_id or brand_id must be provided")
        
        try:
            table = self._get_table("ga4_daily_conversions")
            
            entity_id = client_id if client_id is not None else brand_id
            entity_type = "client" if client_id is not None else "brand"
            
            record = {
                "property_id": property_id,
                "date": date,
                "total_conversions": total_conversions,
                "updated_at": datetime.now()
            }
            
            if client_id is not None:
                record["client_id"] = client_id
            if brand_id is not None:
                record["brand_id"] = brand_id
            
            # Use PostgreSQL INSERT ... ON CONFLICT for upsert
            insert_stmt = pg_insert(table).values(**record)
            insert_stmt = insert_stmt.on_conflict_do_update(
                index_elements=['brand_id', 'property_id', 'date'],
                set_={
                    'client_id': insert_stmt.excluded.client_id,
                    'total_conversions': insert_stmt.excluded.total_conversions,
                    'updated_at': insert_stmt.excluded.updated_at
                }
            )
            
            self.db.execute(insert_stmt)
            self.db.commit()
            logger.info(f"Upserted GA4 daily conversions for {entity_type} {entity_id}, property {property_id}, date {date}: {total_conversions}")
            return 1
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error upserting GA4 daily conversions: {str(e)}")
            raise
    
    def upsert_ga4_kpi_snapshot(
        self,
        property_id: str,
        period_end_date: str,
        period_start_date: str,
        prev_period_start_date: str,
        prev_period_end_date: str,
        current_values: Dict,
        previous_values: Dict,
        changes: Dict,
        client_id: Optional[int] = None,
        brand_id: Optional[int] = None
    ) -> int:
        """Upsert GA4 KPI snapshot for a 30-day period - now uses client_id (with brand_id for backward compatibility)"""
        if client_id is None and brand_id is None:
            raise ValueError("Either client_id or brand_id must be provided")
        
        try:
            # If client_id is provided but brand_id is not, get brand_id from client
            if client_id is not None and brand_id is None:
                client_query = text("SELECT scrunch_brand_id FROM clients WHERE id = :client_id")
                result = self.db.execute(client_query, {"client_id": client_id})
                row = result.first()
                if row:
                    brand_id = row[0]
            
            entity_id = client_id if client_id is not None else brand_id
            entity_type = "client" if client_id is not None else "brand"
            
            # Use PostgreSQL INSERT ... ON CONFLICT for upsert
            # Unique constraint is on (brand_id, property_id, period_end_date)
            query = text("""
                INSERT INTO ga4_kpi_snapshots (
                    brand_id, client_id, property_id, period_end_date, period_start_date,
                    prev_period_start_date, prev_period_end_date,
                    users, sessions, new_users, bounce_rate, avg_session_duration,
                    engagement_rate, engaged_sessions, conversions, revenue,
                    prev_users, prev_sessions, prev_new_users, prev_bounce_rate,
                    prev_avg_session_duration, prev_engagement_rate, prev_engaged_sessions,
                    prev_conversions, prev_revenue,
                    users_change, sessions_change, new_users_change, bounce_rate_change,
                    avg_session_duration_change, engagement_rate_change, engaged_sessions_change,
                    conversions_change, revenue_change, updated_at
                ) VALUES (
                    :brand_id, :client_id, :property_id, :period_end_date, :period_start_date,
                    :prev_period_start_date, :prev_period_end_date,
                    :users, :sessions, :new_users, :bounce_rate, :avg_session_duration,
                    :engagement_rate, :engaged_sessions, :conversions, :revenue,
                    :prev_users, :prev_sessions, :prev_new_users, :prev_bounce_rate,
                    :prev_avg_session_duration, :prev_engagement_rate, :prev_engaged_sessions,
                    :prev_conversions, :prev_revenue,
                    :users_change, :sessions_change, :new_users_change, :bounce_rate_change,
                    :avg_session_duration_change, :engagement_rate_change, :engaged_sessions_change,
                    :conversions_change, :revenue_change, NOW()
                )
                ON CONFLICT (brand_id, property_id, period_end_date)
                DO UPDATE SET
                    client_id = EXCLUDED.client_id,
                    period_start_date = EXCLUDED.period_start_date,
                    prev_period_start_date = EXCLUDED.prev_period_start_date,
                    prev_period_end_date = EXCLUDED.prev_period_end_date,
                    users = EXCLUDED.users,
                    sessions = EXCLUDED.sessions,
                    new_users = EXCLUDED.new_users,
                    bounce_rate = EXCLUDED.bounce_rate,
                    avg_session_duration = EXCLUDED.avg_session_duration,
                    engagement_rate = EXCLUDED.engagement_rate,
                    engaged_sessions = EXCLUDED.engaged_sessions,
                    conversions = EXCLUDED.conversions,
                    revenue = EXCLUDED.revenue,
                    prev_users = EXCLUDED.prev_users,
                    prev_sessions = EXCLUDED.prev_sessions,
                    prev_new_users = EXCLUDED.prev_new_users,
                    prev_bounce_rate = EXCLUDED.prev_bounce_rate,
                    prev_avg_session_duration = EXCLUDED.prev_avg_session_duration,
                    prev_engagement_rate = EXCLUDED.prev_engagement_rate,
                    prev_engaged_sessions = EXCLUDED.prev_engaged_sessions,
                    prev_conversions = EXCLUDED.prev_conversions,
                    prev_revenue = EXCLUDED.prev_revenue,
                    users_change = EXCLUDED.users_change,
                    sessions_change = EXCLUDED.sessions_change,
                    new_users_change = EXCLUDED.new_users_change,
                    bounce_rate_change = EXCLUDED.bounce_rate_change,
                    avg_session_duration_change = EXCLUDED.avg_session_duration_change,
                    engagement_rate_change = EXCLUDED.engagement_rate_change,
                    engaged_sessions_change = EXCLUDED.engaged_sessions_change,
                    conversions_change = EXCLUDED.conversions_change,
                    revenue_change = EXCLUDED.revenue_change,
                    updated_at = NOW()
            """)
            
            params = {
                "brand_id": brand_id,
                "client_id": client_id,
                "property_id": property_id,
                "period_end_date": period_end_date,
                "period_start_date": period_start_date,
                "prev_period_start_date": prev_period_start_date,
                "prev_period_end_date": prev_period_end_date,
                # Current period values
                "users": current_values.get("users", 0),
                "sessions": current_values.get("sessions", 0),
                "new_users": current_values.get("new_users", 0),
                "bounce_rate": current_values.get("bounce_rate", 0),
                "avg_session_duration": current_values.get("avg_session_duration", 0),
                "engagement_rate": current_values.get("engagement_rate", 0),
                "engaged_sessions": current_values.get("engaged_sessions", 0),
                "conversions": current_values.get("conversions", 0),
                "revenue": current_values.get("revenue", 0),
                # Previous period values
                "prev_users": previous_values.get("users", 0),
                "prev_sessions": previous_values.get("sessions", 0),
                "prev_new_users": previous_values.get("new_users", 0),
                "prev_bounce_rate": previous_values.get("bounce_rate", 0),
                "prev_avg_session_duration": previous_values.get("avg_session_duration", 0),
                "prev_engagement_rate": previous_values.get("engagement_rate", 0),
                "prev_engaged_sessions": previous_values.get("engaged_sessions", 0),
                "prev_conversions": previous_values.get("conversions", 0),
                "prev_revenue": previous_values.get("revenue", 0),
                # Percentage changes
                "users_change": changes.get("users_change", 0),
                "sessions_change": changes.get("sessions_change", 0),
                "new_users_change": changes.get("new_users_change", 0),
                "bounce_rate_change": changes.get("bounce_rate_change", 0),
                "avg_session_duration_change": changes.get("avg_session_duration_change", 0),
                "engagement_rate_change": changes.get("engagement_rate_change", 0),
                "engaged_sessions_change": changes.get("engaged_sessions_change", 0),
                "conversions_change": changes.get("conversions_change", 0),
                "revenue_change": changes.get("revenue_change", 0),
            }
            
            self.db.execute(query, params)
            self.db.commit()
            
            logger.info(f"Upserted GA4 KPI snapshot for {entity_type} {entity_id}, property {property_id}, period_end_date {period_end_date}")
            return 1
        except Exception as e:
            self.db.rollback()
            error_str = str(e)
            logger.error(f"Error upserting GA4 KPI snapshot: {error_str}")
            raise
    
    def get_latest_ga4_kpi_snapshot(self, brand_id: int, client_id: Optional[int] = None) -> Optional[Dict]:
        """Get the latest GA4 KPI snapshot for a brand or client
        
        If client_id is provided but no data is found, falls back to querying by brand_id only
        (since multiple clients can share the same GA4 property and brand).
        """
        try:
            query = text("""
                SELECT * FROM ga4_kpi_snapshots
                WHERE (:client_id IS NULL AND brand_id = :brand_id) OR (client_id = :client_id)
                ORDER BY period_end_date DESC
                LIMIT 1
            """)
            result = self.db.execute(query, {"brand_id": brand_id, "client_id": client_id})
            row = result.first()
            
            # If no data found for specific client_id, fall back to brand_id only
            if not row and client_id is not None:
                logger.info(f"No GA4 KPI snapshot found for client_id={client_id}, falling back to brand_id={brand_id} query")
                query = text("""
                    SELECT * FROM ga4_kpi_snapshots
                    WHERE brand_id = :brand_id
                    ORDER BY period_end_date DESC
                    LIMIT 1
                """)
                result = self.db.execute(query, {"brand_id": brand_id})
                row = result.first()
            
            if row:
                snapshot = dict(row._mapping)
                # Convert date objects to strings if needed (PostgreSQL DATE columns return date objects)
                if isinstance(snapshot.get("period_start_date"), date):
                    snapshot["period_start_date"] = snapshot["period_start_date"].strftime("%Y-%m-%d")
                if isinstance(snapshot.get("period_end_date"), date):
                    snapshot["period_end_date"] = snapshot["period_end_date"].strftime("%Y-%m-%d")
                if isinstance(snapshot.get("prev_period_start_date"), date):
                    snapshot["prev_period_start_date"] = snapshot["prev_period_start_date"].strftime("%Y-%m-%d")
                if isinstance(snapshot.get("prev_period_end_date"), date):
                    snapshot["prev_period_end_date"] = snapshot["prev_period_end_date"].strftime("%Y-%m-%d")
                return snapshot
            return None
        except Exception as e:
            logger.error(f"Error getting latest GA4 KPI snapshot for brand {brand_id}, client {client_id}: {str(e)}")
            return None
    
    def get_ga4_kpi_snapshot_by_period(self, brand_id: int, period_end_date: str, client_id: Optional[int] = None) -> Optional[Dict]:
        """Get GA4 KPI snapshot for a specific period end date
        
        If client_id is provided but no data is found, falls back to querying by brand_id only
        (since multiple clients can share the same GA4 property and brand).
        """
        try:
            query = text("""
                SELECT * FROM ga4_kpi_snapshots
                WHERE period_end_date = :period_end_date
                AND ((:client_id IS NULL AND brand_id = :brand_id) OR (client_id = :client_id))
                LIMIT 1
            """)
            result = self.db.execute(query, {
                "brand_id": brand_id,
                "client_id": client_id,
                "period_end_date": period_end_date
            })
            row = result.first()
            
            # If no data found for specific client_id, fall back to brand_id only
            if not row and client_id is not None:
                logger.info(f"No GA4 KPI snapshot found for client_id={client_id}, falling back to brand_id={brand_id} query")
                query = text("""
                    SELECT * FROM ga4_kpi_snapshots
                    WHERE period_end_date = :period_end_date
                    AND brand_id = :brand_id
                    LIMIT 1
                """)
                result = self.db.execute(query, {
                    "brand_id": brand_id,
                    "period_end_date": period_end_date
                })
                row = result.first()
            
            if row:
                return dict(row._mapping)
            return None
        except Exception as e:
            logger.error(f"Error getting GA4 KPI snapshot for brand {brand_id}, client {client_id}, period_end_date {period_end_date}: {str(e)}")
            return None
    
    def get_ga4_kpi_snapshot_by_date_range(self, brand_id: int, start_date: str, end_date: str, client_id: Optional[int] = None) -> Optional[Dict]:
        """Get GA4 KPI snapshot that matches the requested date range (within 1 day tolerance)
        
        If client_id is provided but no data is found, falls back to querying by brand_id only
        (since multiple clients can share the same GA4 property and brand).
        """
        try:
            # Convert dates to datetime for comparison
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            
            # Look for snapshots where period_end_date is within 1 day of the requested end_date
            query = text("""
                SELECT * FROM ga4_kpi_snapshots
                WHERE period_end_date >= :min_date AND period_end_date <= :max_date
                AND ((:client_id IS NULL AND brand_id = :brand_id) OR (client_id = :client_id))
                ORDER BY period_end_date DESC
                LIMIT 1
            """)
            result = self.db.execute(query, {
                "brand_id": brand_id,
                "client_id": client_id,
                "min_date": (end_dt - timedelta(days=1)).strftime("%Y-%m-%d"),
                "max_date": (end_dt + timedelta(days=1)).strftime("%Y-%m-%d")
            })
            row = result.first()
            
            # If no data found for specific client_id, fall back to brand_id only
            if not row and client_id is not None:
                logger.info(f"No GA4 KPI snapshot found for client_id={client_id}, falling back to brand_id={brand_id} query")
                query = text("""
                    SELECT * FROM ga4_kpi_snapshots
                    WHERE period_end_date >= :min_date AND period_end_date <= :max_date
                    AND brand_id = :brand_id
                    ORDER BY period_end_date DESC
                    LIMIT 1
                """)
                result = self.db.execute(query, {
                    "brand_id": brand_id,
                    "min_date": (end_dt - timedelta(days=1)).strftime("%Y-%m-%d"),
                    "max_date": (end_dt + timedelta(days=1)).strftime("%Y-%m-%d")
                })
                row = result.first()
            
            if row:
                snapshot = dict(row._mapping)
                # Convert date objects to strings if needed (PostgreSQL DATE columns return date objects)
                if isinstance(snapshot.get("period_start_date"), date):
                    snapshot["period_start_date"] = snapshot["period_start_date"].strftime("%Y-%m-%d")
                if isinstance(snapshot.get("period_end_date"), date):
                    snapshot["period_end_date"] = snapshot["period_end_date"].strftime("%Y-%m-%d")
                # Verify the snapshot's date range matches what we need (approximately 30 days)
                snapshot_start = datetime.strptime(str(snapshot["period_start_date"]), "%Y-%m-%d")
                snapshot_end = datetime.strptime(str(snapshot["period_end_date"]), "%Y-%m-%d")
                requested_start = start_dt
                requested_end = end_dt
                
                # Check if the snapshot's period matches the requested period (within tolerance)
                start_diff = abs((snapshot_start - requested_start).days)
                end_diff = abs((snapshot_end - requested_end).days)
                
                # Allow using snapshot if end date matches (within 2 days) and start date is reasonable
                # This allows using snapshots for longer periods (e.g., 45 days) when available
                if end_diff <= 2 and start_diff <= 15:
                    return snapshot
            
            return None
        except Exception as e:
            logger.error(f"Error getting GA4 KPI snapshot for brand {brand_id}, client {client_id}, date range {start_date} to {end_date}: {str(e)}")
            return None
    
    def get_ga4_top_pages_by_date_range(self, brand_id: int, property_id: str, start_date: str, end_date: str, limit: int = 10, client_id: Optional[int] = None) -> List[Dict]:
        """Get aggregated GA4 top pages data from stored daily records for a date range using SQLAlchemy Core
        
        Supports querying by brand_id or client_id. If client_id is provided, it will be used as the primary filter.
        If no data is found for the specific client_id, falls back to querying by property_id only
        (since multiple clients can share the same GA4 property).
        """
        try:
            table = self._get_table("ga4_top_pages")
            records = []
            if client_id is not None:
                # Use DISTINCT ON to handle duplicate records with same client_id/date/page_path but different brand_id
                query = text("""
                    SELECT DISTINCT ON (date, page_path) *
                    FROM ga4_top_pages
                    WHERE client_id = :client_id
                      AND property_id = :property_id
                      AND date >= CAST(:start_date AS DATE)
                      AND date <= CAST(:end_date AS DATE)
                    ORDER BY date ASC, page_path ASC,
                             CASE WHEN brand_id IS NOT NULL THEN 0 ELSE 1 END ASC
                """)
                result = self.db.execute(query, {
                    "client_id": client_id,
                    "property_id": property_id,
                    "start_date": start_date,
                    "end_date": end_date
                })
                records = [dict(row._mapping) for row in result]
                
                # If no records found for this specific client_id, fall back to property_id only
                # Use DISTINCT ON to deduplicate by date and page_path to prevent double-counting
                if not records:
                    logger.info(f"No GA4 top pages data found for client_id={client_id}, falling back to property_id={property_id} query (with deduplication)")
                    # Use raw SQL for DISTINCT ON since SQLAlchemy Core doesn't support it directly
                    query = text("""
                        SELECT DISTINCT ON (date, page_path) *
                        FROM ga4_top_pages
                        WHERE property_id = :property_id
                          AND date >= CAST(:start_date AS DATE)
                          AND date <= CAST(:end_date AS DATE)
                        ORDER BY date ASC, page_path ASC,
                                 CASE WHEN client_id = :client_id THEN 0 ELSE 1 END ASC
                    """)
                    result = self.db.execute(query, {
                        "property_id": property_id,
                        "client_id": client_id,
                        "start_date": start_date,
                        "end_date": end_date
                    })
                    records = [dict(row._mapping) for row in result]
            else:
                query = select(table).where(
                    and_(
                        table.c.brand_id == brand_id,
                        table.c.property_id == property_id,
                        table.c.date >= start_date,
                        table.c.date <= end_date
                    )
                )
                result = self.db.execute(query)
                records = [dict(row._mapping) for row in result]
            
            if not records:
                return []
            
            # Aggregate by page_path
            page_aggregates = {}
            for record in records:
                page_path = record.get("page_path")
                if not page_path:
                    continue
                
                if page_path not in page_aggregates:
                    page_aggregates[page_path] = {
                        "pagePath": page_path,
                        "views": 0,
                        "users": 0,
                        "avgSessionDuration": 0.0,
                        "count": 0
                    }
                
                # Convert Decimal to float for aggregation
                page_aggregates[page_path]["views"] += float(record.get("views", 0) or 0)
                page_aggregates[page_path]["users"] += float(record.get("users", 0) or 0)
                page_aggregates[page_path]["avgSessionDuration"] += float(record.get("avg_session_duration", 0) or 0)
                page_aggregates[page_path]["count"] += 1
            
            # Calculate averages and sort
            pages = []
            for page_path, data in page_aggregates.items():
                if data["count"] > 0:
                    data["avgSessionDuration"] = data["avgSessionDuration"] / data["count"]
                pages.append(data)
            
            # Sort by views descending and limit
            pages.sort(key=lambda x: x["views"], reverse=True)
            return pages[:limit]
        except Exception as e:
            logger.error(f"Error getting GA4 top pages for date range: {str(e)}")
            return []
    
    def get_ga4_traffic_sources_by_date_range(self, brand_id: int, property_id: str, start_date: str, end_date: str, client_id: Optional[int] = None) -> List[Dict]:
        """Get aggregated GA4 traffic sources data from stored daily records for a date range using SQLAlchemy Core
        
        Aggregates data by taking the maximum values for each month, then aggregates those monthly maxes by source.
        This prevents double-counting when the same data appears across multiple days in a month.
        
        Supports querying by brand_id or client_id. If client_id is provided, it will be used as the primary filter.
        If no data is found for the specific client_id, falls back to querying by property_id only
        (since multiple clients can share the same GA4 property).
        """
        try:
            from datetime import datetime
            from collections import defaultdict
            
            table = self._get_table("ga4_traffic_sources")
            records = []
            if client_id is not None:
                # Use DISTINCT ON to handle duplicate records with same client_id/date/source but different brand_id
                query = text("""
                    SELECT DISTINCT ON (date, source) *
                    FROM ga4_traffic_sources
                    WHERE client_id = :client_id
                      AND property_id = :property_id
                      AND date >= CAST(:start_date AS DATE)
                      AND date <= CAST(:end_date AS DATE)
                    ORDER BY date ASC, source ASC,
                             CASE WHEN brand_id IS NOT NULL THEN 0 ELSE 1 END ASC
                """)
                result = self.db.execute(query, {
                    "client_id": client_id,
                    "property_id": property_id,
                    "start_date": start_date,
                    "end_date": end_date
                })
                records = [dict(row._mapping) for row in result]
                
                # If no records found for this specific client_id, fall back to property_id only
                # Use DISTINCT ON to deduplicate by date and source to prevent double-counting
                if not records:
                    logger.info(f"No GA4 traffic sources data found for client_id={client_id}, falling back to property_id={property_id} query (with deduplication)")
                    query = text("""
                        SELECT DISTINCT ON (date, source) *
                        FROM ga4_traffic_sources
                        WHERE property_id = :property_id
                          AND date >= CAST(:start_date AS DATE)
                          AND date <= CAST(:end_date AS DATE)
                        ORDER BY date ASC, source ASC,
                                 CASE WHEN client_id = :client_id THEN 0 ELSE 1 END ASC
                    """)
                    result = self.db.execute(query, {
                        "property_id": property_id,
                        "client_id": client_id,
                        "start_date": start_date,
                        "end_date": end_date
                    })
                    records = [dict(row._mapping) for row in result]
            else:
                query = select(table).where(
                    and_(
                        table.c.brand_id == brand_id,
                        table.c.property_id == property_id,
                        table.c.date >= start_date,
                        table.c.date <= end_date
                    )
                )
                result = self.db.execute(query)
                records = [dict(row._mapping) for row in result]
            
            if not records:
                return []
            
            # Group records by (source, year-month) and find max values for each month
            monthly_maxes = defaultdict(lambda: {
                "sessions": 0,
                "users": 0,
                "bounce_rate": 0.0,
                "conversions": 0.0,
                "conversion_rate": 0.0,
                "date": None
            })
            
            for record in records:
                source = record.get("source")
                if not source:
                    continue
                
                # Extract year-month from date
                date_str = record.get("date")
                if isinstance(date_str, str):
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                else:
                    date_obj = date_str
                
                month_key = (source, date_obj.year, date_obj.month)
                
                # Convert Decimal to float
                sessions_val = float(record.get("sessions", 0) or 0)
                users_val = float(record.get("users", 0) or 0)
                bounce_rate_val = float(record.get("bounce_rate", 0) or 0)
                conversions_val = float(record.get("conversions", 0) or 0)
                conversion_rate_val = float(record.get("conversion_rate", 0) or 0)
                
                # Keep maximum values for each month
                if sessions_val > monthly_maxes[month_key]["sessions"]:
                    monthly_maxes[month_key]["sessions"] = sessions_val
                    monthly_maxes[month_key]["users"] = users_val
                    monthly_maxes[month_key]["bounce_rate"] = bounce_rate_val
                    monthly_maxes[month_key]["conversions"] = conversions_val
                    monthly_maxes[month_key]["conversion_rate"] = conversion_rate_val
                    monthly_maxes[month_key]["date"] = date_str
                elif sessions_val == monthly_maxes[month_key]["sessions"]:
                    # If sessions are equal, prefer the one with higher users
                    if users_val > monthly_maxes[month_key]["users"]:
                        monthly_maxes[month_key]["users"] = users_val
                        monthly_maxes[month_key]["bounce_rate"] = bounce_rate_val
                        monthly_maxes[month_key]["conversions"] = conversions_val
                        monthly_maxes[month_key]["conversion_rate"] = conversion_rate_val
                        monthly_maxes[month_key]["date"] = date_str
            
            # Now aggregate the monthly maxes by source
            source_aggregates = {}
            for (source, year, month), monthly_data in monthly_maxes.items():
                if source not in source_aggregates:
                    source_aggregates[source] = {
                        "source": source,
                        "sessions": 0,
                        "users": 0,
                        "bounceRate": 0.0,
                        "conversions": 0.0,
                        "conversionRate": 0.0,
                        "totalBounce": 0.0,
                        "totalSessions": 0,
                        "monthCount": 0  # Track number of months for averaging
                    }
                
                # Sum the monthly max values
                source_aggregates[source]["sessions"] += monthly_data["sessions"]
                source_aggregates[source]["users"] += monthly_data["users"]
                source_aggregates[source]["conversions"] += monthly_data["conversions"]
                source_aggregates[source]["totalBounce"] += monthly_data["bounce_rate"] * monthly_data["sessions"]
                source_aggregates[source]["totalSessions"] += monthly_data["sessions"]
                source_aggregates[source]["monthCount"] += 1
            
            # Calculate weighted average bounce rate and conversion rate
            sources = []
            for source, data in source_aggregates.items():
                if data["totalSessions"] > 0:
                    data["bounceRate"] = data["totalBounce"] / data["totalSessions"]
                    # Calculate conversion rate based on total conversions and sessions
                    data["conversionRate"] = data["conversions"] / data["totalSessions"] if data["totalSessions"] > 0 else 0.0
                # Remove monthCount from final output
                del data["monthCount"]
                # Add channel field (maps to source for backward compatibility)
                data["channel"] = data["source"]
                sources.append(data)
            
            # Sort by sessions descending
            sources.sort(key=lambda x: x["sessions"], reverse=True)
            return sources
        except Exception as e:
            logger.error(f"Error getting GA4 traffic sources for date range: {str(e)}")
            return []
    
    def get_ga4_geographic_by_date_range(self, brand_id: int, property_id: str, start_date: str, end_date: str, limit: int = 10, client_id: Optional[int] = None) -> List[Dict]:
        """Get aggregated GA4 geographic data from stored daily records for a date range using SQLAlchemy Core
        
        Supports querying by brand_id or client_id. If client_id is provided, it will be used as the primary filter.
        If no data is found for the specific client_id, falls back to querying by property_id only
        (since multiple clients can share the same GA4 property).
        """
        try:
            table = self._get_table("ga4_geographic")
            records = []
            if client_id is not None:
                # Use DISTINCT ON to handle duplicate records with same client_id/date/country but different brand_id
                query = text("""
                    SELECT DISTINCT ON (date, country) *
                    FROM ga4_geographic
                    WHERE client_id = :client_id
                      AND property_id = :property_id
                      AND date >= CAST(:start_date AS DATE)
                      AND date <= CAST(:end_date AS DATE)
                    ORDER BY date ASC, country ASC,
                             CASE WHEN brand_id IS NOT NULL THEN 0 ELSE 1 END ASC
                """)
                result = self.db.execute(query, {
                    "client_id": client_id,
                    "property_id": property_id,
                    "start_date": start_date,
                    "end_date": end_date
                })
                records = [dict(row._mapping) for row in result]
                
                # If no records found for this specific client_id, fall back to property_id only
                # Use DISTINCT ON to deduplicate by date and country to prevent double-counting
                if not records:
                    logger.info(f"No GA4 geographic data found for client_id={client_id}, falling back to property_id={property_id} query (with deduplication)")
                    query = text("""
                        SELECT DISTINCT ON (date, country) *
                        FROM ga4_geographic
                        WHERE property_id = :property_id
                          AND date >= CAST(:start_date AS DATE)
                          AND date <= CAST(:end_date AS DATE)
                        ORDER BY date ASC, country ASC,
                                 CASE WHEN client_id = :client_id THEN 0 ELSE 1 END ASC
                    """)
                    result = self.db.execute(query, {
                        "property_id": property_id,
                        "client_id": client_id,
                        "start_date": start_date,
                        "end_date": end_date
                    })
                    records = [dict(row._mapping) for row in result]
            else:
                query = select(table).where(
                    and_(
                        table.c.brand_id == brand_id,
                        table.c.property_id == property_id,
                        table.c.date >= start_date,
                        table.c.date <= end_date
                    )
                )
                result = self.db.execute(query)
                records = [dict(row._mapping) for row in result]
            
            if not records:
                return []
            
            # Aggregate by country
            country_aggregates = {}
            for record in records:
                country = record.get("country")
                if not country:
                    continue
                
                if country not in country_aggregates:
                    country_aggregates[country] = {
                        "country": country,
                        "users": 0,
                        "sessions": 0,
                        "engagementRate": 0.0
                    }
                
                country_aggregates[country]["users"] += record.get("users", 0)
                country_aggregates[country]["sessions"] += record.get("sessions", 0)
            
            # Calculate engagement rate (simplified - would need engaged_sessions in table for accurate calculation)
            countries = []
            for country, data in country_aggregates.items():
                countries.append(data)
            
            # Sort by sessions descending and limit
            countries.sort(key=lambda x: x["sessions"], reverse=True)
            return countries[:limit]
        except Exception as e:
            logger.error(f"Error getting GA4 geographic data for date range: {str(e)}")
            return []
    
    def get_ga4_devices_by_date_range(self, brand_id: int, property_id: str, start_date: str, end_date: str, client_id: Optional[int] = None) -> List[Dict]:
        """Get aggregated GA4 devices data from stored daily records for a date range using SQLAlchemy Core
        
        Supports querying by brand_id or client_id. If client_id is provided, it will be used as the primary filter.
        If no data is found for the specific client_id, falls back to querying by property_id only
        (since multiple clients can share the same GA4 property).
        """
        try:
            table = self._get_table("ga4_devices")
            records = []
            if client_id is not None:
                # Use DISTINCT ON to handle duplicate records with same client_id/date/device but different brand_id
                query = text("""
                    SELECT DISTINCT ON (date, device_category) *
                    FROM ga4_devices
                    WHERE client_id = :client_id
                      AND property_id = :property_id
                      AND date >= CAST(:start_date AS DATE)
                      AND date <= CAST(:end_date AS DATE)
                    ORDER BY date ASC, device_category ASC,
                             CASE WHEN brand_id IS NOT NULL THEN 0 ELSE 1 END ASC
                """)
                result = self.db.execute(query, {
                    "client_id": client_id,
                    "property_id": property_id,
                    "start_date": start_date,
                    "end_date": end_date
                })
                records = [dict(row._mapping) for row in result]
                
                # If no records found for this specific client_id, fall back to property_id only
                # Use DISTINCT ON to deduplicate by date and device_category to prevent double-counting
                if not records:
                    logger.info(f"No GA4 devices data found for client_id={client_id}, falling back to property_id={property_id} query (with deduplication)")
                    query = text("""
                        SELECT DISTINCT ON (date, device_category) *
                        FROM ga4_devices
                        WHERE property_id = :property_id
                          AND date >= CAST(:start_date AS DATE)
                          AND date <= CAST(:end_date AS DATE)
                        ORDER BY date ASC, device_category ASC,
                                 CASE WHEN client_id = :client_id THEN 0 ELSE 1 END ASC
                    """)
                    result = self.db.execute(query, {
                        "property_id": property_id,
                        "client_id": client_id,
                        "start_date": start_date,
                        "end_date": end_date
                    })
                    records = [dict(row._mapping) for row in result]
            else:
                query = select(table).where(
                    and_(
                        table.c.brand_id == brand_id,
                        table.c.property_id == property_id,
                        table.c.date >= start_date,
                        table.c.date <= end_date
                    )
                )
                result = self.db.execute(query)
                records = [dict(row._mapping) for row in result]
            
            if not records:
                return []
            
            # Aggregate by device_category and operating_system
            device_aggregates = {}
            for record in records:
                device_key = f"{record.get('device_category', 'unknown')}|{record.get('operating_system', 'unknown')}"
                
                if device_key not in device_aggregates:
                    device_aggregates[device_key] = {
                        "deviceCategory": record.get("device_category", "unknown"),
                        "operatingSystem": record.get("operating_system", "unknown"),
                        "users": 0,
                        "sessions": 0,
                        "bounceRate": 0.0,
                        "totalBounce": 0.0,
                        "totalSessions": 0
                    }
                
                # Convert Decimal to float for aggregation
                sessions_val = float(record.get("sessions", 0) or 0)
                users_val = float(record.get("users", 0) or 0)
                bounce_rate_val = float(record.get("bounce_rate", 0) or 0)
                device_aggregates[device_key]["users"] += users_val
                device_aggregates[device_key]["sessions"] += sessions_val
                device_aggregates[device_key]["totalBounce"] += bounce_rate_val * sessions_val
                device_aggregates[device_key]["totalSessions"] += sessions_val
            
            # Calculate weighted average bounce rate
            devices = []
            for device_key, data in device_aggregates.items():
                if data["totalSessions"] > 0:
                    data["bounceRate"] = data["totalBounce"] / data["totalSessions"]
                devices.append(data)
            
            # Sort by users descending
            devices.sort(key=lambda x: x["users"], reverse=True)
            return devices
        except Exception as e:
            logger.error(f"Error getting GA4 devices data for date range: {str(e)}")
            return []
    
    # =====================================================
    # Brand Methods
    # =====================================================
    
    def update_brand_logo_url(self, brand_id: int, logo_url: str, user_email: Optional[str] = None) -> bool:
        """Update brand logo URL using SQLAlchemy ORM (local PostgreSQL)"""
        try:
            brand = self.db.query(Brand).filter(Brand.id == brand_id).first()
            if not brand:
                logger.warning(f"No brand found with ID {brand_id} to update logo URL")
                return False
            
            brand.logo_url = logo_url
            brand.last_modified_by = user_email
            brand.version = brand.version + 1  # Increment version for optimistic locking
            
            self.db.commit()
            logger.info(f"Updated brand {brand_id} logo URL")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating brand logo URL for brand {brand_id}: {str(e)}")
            return False
    
    def update_brand_theme(self, brand_id: int, theme_data: Dict, user_email: Optional[str] = None) -> bool:
        """Update brand theme using SQLAlchemy ORM (local PostgreSQL)"""
        try:
            brand = self.db.query(Brand).filter(Brand.id == brand_id).first()
            if not brand:
                logger.warning(f"No brand found with ID {brand_id} to update theme")
                return False
            
            if "theme" in theme_data:
                brand.theme = theme_data["theme"]
            if "logo_url" in theme_data:
                brand.logo_url = theme_data["logo_url"]
            
            brand.last_modified_by = user_email
            brand.version = brand.version + 1  # Increment version for optimistic locking
            
            self.db.commit()
            logger.info(f"Updated brand {brand_id} theme")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating brand theme for brand {brand_id}: {str(e)}")
            return False
    
    # =====================================================
    # Client Methods
    # =====================================================
    
    def generate_client_slug(self, company_name: str = None) -> str:
        """Generate a URL-friendly slug using UUID for better security using SQLAlchemy Core"""
        # Generate UUID-based slug (32 hex characters, no hyphens)
        # This matches the database trigger logic for consistency
        slug = uuid.uuid4().hex.lower()
        
        # Check if slug exists (extremely unlikely with UUID, but safety check)
        while True:
            try:
                table = self._get_table("clients")
                query = select(table.c.id).where(table.c.url_slug == slug).limit(1)
                result = self.db.execute(query)
                if not result.first():
                    break
                # If collision occurs (should never happen), generate new UUID
                slug = uuid.uuid4().hex.lower()
            except Exception:
                break
        
        return slug
    
    def upsert_clients_from_campaigns_batch(self, campaigns: List[Dict], user_email: Optional[str] = None) -> Dict[str, int]:
        """Batch create/update clients from active campaigns
        
        Args:
            campaigns: List of campaign dictionaries (should be filtered to active only)
            user_email: Email of user performing the sync
            
        Returns:
            Dict with 'created', 'updated', 'total' counts
        """
        if not campaigns:
            return {"created": 0, "updated": 0, "total": 0}
        
        # Filter to only active campaigns
        active_campaigns = [c for c in campaigns if c.get("status", "").lower() == "active"]
        
        if not active_campaigns:
            logger.info("No active campaigns to create clients from")
            return {"created": 0, "updated": 0, "total": 0}
        
        # Step 1: Get all existing clients to check for updates
        try:
            from sqlalchemy import text, select
            from sqlalchemy.sql import or_
            
            # Get all company_ids and company_names from active campaigns
            # Ensure we extract simple values, not dicts
            company_ids = []
            for c in active_campaigns:
                company_id = c.get("company_id")
                if company_id is not None:
                    # Ensure it's a simple value, not a dict
                    if isinstance(company_id, (int, str)):
                        try:
                            company_ids.append(int(company_id))
                        except (ValueError, TypeError):
                            pass
            
            company_names = []
            for c in active_campaigns:
                company = c.get("company")
                if company:
                    # Ensure it's a string, not a dict
                    if isinstance(company, str):
                        company_names.append(company.strip())
                    elif isinstance(company, dict):
                        # If it's a dict, try to get a name field
                        company_name = company.get("name") or company.get("company")
                        if isinstance(company_name, str):
                            company_names.append(company_name.strip())
            
            # Remove duplicates
            company_ids = list(set(company_ids))
            company_names = list(set([n for n in company_names if n]))
            
            # Fetch existing clients by company_id or company_name using self.db session
            existing_clients = []
            if company_ids or company_names:
                # Build query using SQLAlchemy Core
                from sqlalchemy import Table, MetaData
                metadata = MetaData()
                clients_table = Table('clients', metadata, autoload_with=self.db.bind)
                
                conditions = []
                if company_ids:
                    conditions.append(clients_table.c.company_id.in_(company_ids))
                if company_names:
                    conditions.append(clients_table.c.company_name.in_(company_names))
                
                if conditions:
                    query = select(clients_table).where(or_(*conditions))
                    result = self.db.execute(query)
                    existing_clients = [dict(row._mapping) for row in result]
            
            # Create lookup maps
            existing_by_company_id = {c["company_id"]: c for c in existing_clients if c.get("company_id")}
            existing_by_company_name = {c["company_name"]: c for c in existing_clients if c.get("company_name")}
            
        except Exception as e:
            logger.warning(f"Error fetching existing clients: {str(e)}")
            existing_by_company_id = {}
            existing_by_company_name = {}
        
        # Step 2: Build all client records locally
        clients_to_insert = []
        clients_to_update = []
        campaign_client_links = []  # Store (campaign_id, client_id, company_name, is_primary) tuples
        
        for campaign in active_campaigns:
            try:
                company_name = campaign.get("company", "").strip()
                if not company_name:
                    logger.warning(f"Skipping campaign {campaign.get('id')}: no company name")
                    continue
                
                company_id = campaign.get("company_id")
                campaign_id = campaign.get("id")
                
                # Check if client exists
                existing_client = None
                if company_id and company_id in existing_by_company_id:
                    existing_client = existing_by_company_id[company_id]
                elif company_name in existing_by_company_name:
                    existing_client = existing_by_company_name[company_name]
                
                # Prepare client data
                client_data = {
                    "company_name": company_name,
                    "company_id": company_id,
                    "url": campaign.get("url"),
                    "email_addresses": campaign.get("email_addresses", []),
                    "phone_numbers": campaign.get("phone_numbers", []),
                    "address": campaign.get("address"),
                    "city": campaign.get("city"),
                    "state": campaign.get("state"),
                    "zip": campaign.get("zip"),
                    "country": campaign.get("country"),
                    "timezone": campaign.get("timezone"),
                    "company_domain": self._extract_domain(campaign.get("url", "")),
                    "updated_by": user_email,
                }
                
                if existing_client:
                    # Update existing client
                    client_data["id"] = existing_client["id"]
                    # Don't overwrite slug, theme, or mappings if they exist
                    if existing_client.get("url_slug"):
                        client_data["url_slug"] = existing_client["url_slug"]
                    clients_to_update.append(client_data)
                    client_id = existing_client["id"]
                else:
                    # New client - generate slug
                    client_data["url_slug"] = self.generate_client_slug()
                    client_data["created_by"] = user_email
                    clients_to_insert.append(client_data)
                    # We'll get the client_id after insert
                    client_id = None
                
                # Store campaign-client link info (include company_name for matching after insert)
                if campaign_id:
                    campaign_client_links.append((campaign_id, client_id, company_name, existing_client is None))
                    
            except Exception as e:
                logger.warning(f"Error preparing client data from campaign {campaign.get('id')}: {str(e)}")
                continue
        
        # Step 3: Batch insert new clients
        created_count = 0
        inserted_client_map = {}
        if clients_to_insert:
            try:
                table = self._get_table("clients")
                # Insert clients one by one to get the generated IDs
                for client_data in clients_to_insert:
                    try:
                        # Remove None values to avoid issues
                        clean_data = {k: v for k, v in client_data.items() if v is not None}
                        insert_stmt = insert(table).values(**clean_data).returning(table.c.id, table.c.company_name)
                        result = self.db.execute(insert_stmt)
                        row = result.first()
                        if row:
                            created_count += 1
                            inserted_client_map[row.company_name] = row.id
                    except Exception as insert_error:
                        logger.warning(f"Error inserting client {client_data.get('company_name')}: {str(insert_error)}")
                
                self.db.commit()
                
                # Update campaign_client_links with new client IDs
                updated_links = []
                for campaign_id, old_client_id, company_name, is_primary in campaign_client_links:
                    if old_client_id is None and company_name in inserted_client_map:
                        updated_links.append((campaign_id, inserted_client_map[company_name], company_name, is_primary))
                    else:
                        updated_links.append((campaign_id, old_client_id, company_name, is_primary))
                campaign_client_links = updated_links
                
                logger.info(f"Batch inserted {created_count} new clients")
            except Exception as e:
                self.db.rollback()
                logger.error(f"Error batch inserting clients: {str(e)}")
                raise
        
        # Step 4: Batch update existing clients
        updated_count = 0
        if clients_to_update:
            try:
                table = self._get_table("clients")
                # Update clients individually
                for client_data in clients_to_update:
                    try:
                        client_id = client_data.pop("id")
                        # Remove None values and id
                        clean_data = {k: v for k, v in client_data.items() if v is not None and k != "id"}
                        if clean_data:
                            # Add updated_at
                            clean_data["updated_at"] = datetime.now()
                            update_stmt = update(table).where(table.c.id == client_id).values(**clean_data)
                            result = self.db.execute(update_stmt)
                            if result.rowcount > 0:
                                updated_count += 1
                    except Exception as update_error:
                        logger.warning(f"Error updating client {client_data.get('company_name')}: {str(update_error)}")
                
                self.db.commit()
                logger.info(f"Batch updated {updated_count} existing clients")
            except Exception as e:
                self.db.rollback()
                logger.error(f"Error batch updating clients: {str(e)}")
        
        # Step 5: Link campaigns to clients
        linked_count = 0
        for campaign_id, client_id, company_name, is_primary in campaign_client_links:
            if client_id:
                try:
                    self._link_campaign_to_client(campaign_id, client_id, is_primary)
                    linked_count += 1
                except Exception as link_error:
                    logger.warning(f"Error linking campaign {campaign_id} to client {client_id} ({company_name}): {str(link_error)}")
        
        total_count = created_count + updated_count
        logger.info(f"Batch upserted clients: {created_count} created, {updated_count} updated, {linked_count} campaign links")
        
        return {
            "created": created_count,
            "updated": updated_count,
            "total": total_count,
            "linked": linked_count
        }
    
    def upsert_client_from_campaign(self, campaign: Dict, user_email: Optional[str] = None) -> Dict:
        """Create or update a client from an Agency Analytics campaign using SQLAlchemy"""
        try:
            company_name = campaign.get("company", "").strip()
            if not company_name:
                raise ValueError("Campaign must have a company name")
            
            company_id = campaign.get("company_id")
            
            # Check if client already exists by company_id or company_name using SQLAlchemy
            table = self._get_table("clients")
            existing_client = None
            
            if company_id:
                query = select(table).where(table.c.company_id == company_id).limit(1)
                result = self.db.execute(query)
                row = result.first()
                if row:
                    existing_client = dict(row._mapping)
            
            if not existing_client:
                query = select(table).where(table.c.company_name == company_name).limit(1)
                result = self.db.execute(query)
                row = result.first()
                if row:
                    existing_client = dict(row._mapping)
            
            # Prepare client data
            client_data = {
                "company_name": company_name,
                "company_id": company_id,
                "url": campaign.get("url"),
                "email_addresses": campaign.get("email_addresses", []),
                "phone_numbers": campaign.get("phone_numbers", []),
                "address": campaign.get("address"),
                "city": campaign.get("city"),
                "state": campaign.get("state"),
                "zip": campaign.get("zip"),
                "country": campaign.get("country"),
                "timezone": campaign.get("timezone"),
                "company_domain": self._extract_domain(campaign.get("url", "")),
                "updated_by": user_email,
                "updated_at": datetime.now()
            }
            
            # Generate slug if client doesn't exist (UUID-based for security)
            if not existing_client:
                client_data["url_slug"] = self.generate_client_slug()
                client_data["created_by"] = user_email
                # Insert new client
                clean_data = {k: v for k, v in client_data.items() if v is not None}
                insert_stmt = insert(table).values(**clean_data).returning(table)
                result = self.db.execute(insert_stmt)
                row = result.first()
                client = dict(row._mapping)
                self.db.commit()
            else:
                # Update existing client with campaign data (don't overwrite theme/branding)
                client_id = existing_client["id"]
                # Remove None values and preserve existing slug, theme, etc.
                clean_data = {k: v for k, v in client_data.items() if v is not None and k not in ["url_slug", "theme_color", "logo_url", "secondary_color", "font_family", "favicon_url", "report_title", "custom_css", "footer_text", "header_text"]}
                if clean_data:
                    update_stmt = update(table).where(table.c.id == client_id).values(**clean_data)
                    self.db.execute(update_stmt)
                    self.db.commit()
                # Fetch updated client
                query = select(table).where(table.c.id == client_id)
                result = self.db.execute(query)
                row = result.first()
                client = dict(row._mapping)
            
            # Link campaign to client
            campaign_id = campaign.get("id")
            if campaign_id:
                self._link_campaign_to_client(campaign_id, client["id"], existing_client is None)
            
            logger.info(f"Upserted client '{company_name}' (ID: {client.get('id')}) from campaign {campaign_id}")
            return client
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error upserting client from campaign: {str(e)}")
            raise
    
    def _extract_domain(self, url: str) -> Optional[str]:
        """Extract domain from URL"""
        if not url:
            return None
        try:
            parsed = urlparse(url)
            domain = parsed.netloc or parsed.path
            # Remove www. prefix
            if domain.startswith("www."):
                domain = domain[4:]
            return domain.lower() if domain else None
        except Exception:
            return None
    
    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        """Parse datetime from various formats (string, datetime, None)"""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                # Try ISO format first
                if 'T' in value or ' ' in value:
                    # Remove timezone info if present (e.g., '+00:00')
                    value_clean = value.split('+')[0].rstrip()
                    # Try common formats
                    for fmt in ['%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
                        try:
                            return datetime.strptime(value_clean, fmt)
                        except ValueError:
                            continue
                    # Fallback to dateutil parser if available
                    try:
                        from dateutil import parser
                        return parser.parse(value)
                    except (ImportError, ValueError):
                        pass
                return None
            except Exception:
                return None
        return None
    
    def _link_campaign_to_client(self, campaign_id: int, client_id: int, is_primary: bool = False):
        """Link a campaign to a client using SQLAlchemy"""
        try:
            table = self._get_table("client_campaigns")
            
            # Check if link already exists
            query = select(table).where(
                and_(
                    table.c.campaign_id == campaign_id,
                    table.c.client_id == client_id
                )
            ).limit(1)
            result = self.db.execute(query)
            existing_link = result.first()
            
            if existing_link:
                # Update existing link
                existing_link_dict = dict(existing_link._mapping)
                link_data = {
                    "is_primary": is_primary,
                    "updated_at": datetime.now()
                }
                update_stmt = update(table).where(table.c.id == existing_link_dict["id"]).values(**link_data)
                self.db.execute(update_stmt)
            else:
                # Create new link using ON CONFLICT
                link_data = {
                    "client_id": client_id,
                    "campaign_id": campaign_id,
                    "is_primary": is_primary,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
                # Use PostgreSQL INSERT ... ON CONFLICT
                insert_stmt = pg_insert(table).values(**link_data)
                insert_stmt = insert_stmt.on_conflict_do_update(
                    index_elements=['client_id', 'campaign_id'],
                    set_={
                        'is_primary': insert_stmt.excluded.is_primary,
                        'updated_at': insert_stmt.excluded.updated_at
                    }
                )
                self.db.execute(insert_stmt)
            
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.warning(f"Error linking campaign {campaign_id} to client {client_id}: {str(e)}")
    
    def get_client_by_slug(self, url_slug: str) -> Optional[Dict]:
        """Get client by URL slug using SQLAlchemy Core"""
        try:
            table = self._get_table("clients")
            query = select(table).where(table.c.url_slug == url_slug).limit(1)
            result = self.db.execute(query)
            row = result.first()
            if row:
                return dict(row._mapping)
            return None
        except Exception as e:
            logger.error(f"Error getting client by slug {url_slug}: {str(e)}")
            return None
    
    def get_client_by_id(self, client_id: int) -> Optional[Dict]:
        """Get client by ID using SQLAlchemy Core"""
        try:
            table = self._get_table("clients")
            query = select(table).where(table.c.id == client_id).limit(1)
            result = self.db.execute(query)
            row = result.first()
            if row:
                return dict(row._mapping)
            return None
        except Exception as e:
            logger.error(f"Error getting client by ID {client_id}: {str(e)}")
            return None
    
    def update_client_mapping(self, client_id: int, ga4_property_id: Optional[str] = None, scrunch_brand_id: Optional[int] = None, user_email: Optional[str] = None) -> bool:
        """Update client mappings (GA4 property ID or Scrunch brand ID) using SQLAlchemy Core"""
        try:
            table = self._get_table("clients")
            
            # Build update data
            update_data = {
                "updated_by": user_email,
                "last_modified_by": user_email,
                "updated_at": datetime.now()
            }
            
            if ga4_property_id is not None:
                update_data["ga4_property_id"] = ga4_property_id
            
            if scrunch_brand_id is not None:
                update_data["scrunch_brand_id"] = scrunch_brand_id
            
            # Execute update with version increment using SQL expression
            # Add version increment to update_data
            update_data["version"] = table.c.version + 1  # Increment version for optimistic locking
            
            update_stmt = (
                update(table)
                .where(table.c.id == client_id)
                .values(**update_data)
            )
            result = self.db.execute(update_stmt)
            self.db.commit()
            
            if result.rowcount == 0:
                logger.warning(f"No client found with ID {client_id} to update mappings")
                return False
            
            logger.info(f"Updated client {client_id} mappings (GA4: {ga4_property_id}, Scrunch: {scrunch_brand_id})")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating client mappings for client {client_id}: {str(e)}")
            return False
    
    def update_client_theme(self, client_id: int, theme_data: Dict, user_email: Optional[str] = None) -> bool:
        """Update client theme and branding using SQLAlchemy Core (local PostgreSQL)"""
        try:
            table = self._get_table("clients")
            
            update_data = {
                "updated_by": user_email,
                "last_modified_by": user_email,
                "updated_at": datetime.now()
            }
            
            if "theme_color" in theme_data:
                update_data["theme_color"] = theme_data["theme_color"]
            if "logo_url" in theme_data:
                update_data["logo_url"] = theme_data["logo_url"]
            if "secondary_color" in theme_data:
                update_data["secondary_color"] = theme_data["secondary_color"]
            if "font_family" in theme_data:
                update_data["font_family"] = theme_data["font_family"]
            if "favicon_url" in theme_data:
                update_data["favicon_url"] = theme_data["favicon_url"]
            if "report_title" in theme_data:
                update_data["report_title"] = theme_data["report_title"]
            if "custom_css" in theme_data:
                update_data["custom_css"] = theme_data["custom_css"]
            if "footer_text" in theme_data:
                update_data["footer_text"] = theme_data["footer_text"]
            if "header_text" in theme_data:
                update_data["header_text"] = theme_data["header_text"]
            
            # Increment version for optimistic locking
            update_data["version"] = table.c.version + 1
            
            # Remove None values
            clean_data = {k: v for k, v in update_data.items() if v is not None}
            
            update_stmt = update(table).where(table.c.id == client_id).values(**clean_data)
            result = self.db.execute(update_stmt)
            self.db.commit()
            
            if result.rowcount == 0:
                logger.warning(f"No client found with ID {client_id} to update theme")
                return False
            
            logger.info(f"Updated client {client_id} theme")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating client theme: {str(e)}")
            return False
    
    def update_client_report_dates(self, client_id: int, report_start_date: Optional[date] = None, report_end_date: Optional[date] = None, user_email: Optional[str] = None) -> bool:
        """Update client report date range using SQLAlchemy Core (local PostgreSQL)"""
        try:
            table = self._get_table("clients")
            
            update_data = {
                "updated_by": user_email,
                "last_modified_by": user_email,
                "updated_at": datetime.now()
            }
            
            if report_start_date is not None:
                update_data["report_start_date"] = report_start_date
            if report_end_date is not None:
                update_data["report_end_date"] = report_end_date
            
            # Increment version for optimistic locking
            update_data["version"] = table.c.version + 1
            
            # Remove None values
            clean_data = {k: v for k, v in update_data.items() if v is not None}
            
            update_stmt = update(table).where(table.c.id == client_id).values(**clean_data)
            result = self.db.execute(update_stmt)
            self.db.commit()
            
            if result.rowcount == 0:
                logger.warning(f"No client found with ID {client_id} to update report dates")
                return False
            
            logger.info(f"Updated client {client_id} report dates: start={report_start_date}, end={report_end_date}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating client report dates: {str(e)}")
            return False
    
    def get_client_campaigns(self, client_id: int) -> List[Dict]:
        """Get all campaigns linked to a client using SQLAlchemy Core (local PostgreSQL)"""
        try:
            # Get client_campaigns links
            client_campaigns_table = self._get_table("client_campaigns")
            campaigns_table = self._get_table("agency_analytics_campaigns")
            
            # First get the campaign IDs linked to this client
            links_query = select(client_campaigns_table).where(
                client_campaigns_table.c.client_id == client_id
            )
            links_result = self.db.execute(links_query)
            links = [dict(row._mapping) for row in links_result]
            
            if not links:
                return []
            
            # Get campaign IDs
            campaign_ids = [link["campaign_id"] for link in links]
            link_map = {link["campaign_id"]: link for link in links}
            
            # Get campaigns
            campaigns_query = select(campaigns_table).where(
                campaigns_table.c.id.in_(campaign_ids)
            )
            campaigns_result = self.db.execute(campaigns_query)
            campaigns = [dict(row._mapping) for row in campaigns_result]
            
            # Combine with link data
            for campaign in campaigns:
                campaign_id = campaign["id"]
                if campaign_id in link_map:
                    link = link_map[campaign_id]
                    campaign["is_primary"] = link.get("is_primary", False)
                    campaign["link_created_at"] = link.get("created_at")
                    campaign["link_updated_at"] = link.get("updated_at")
            
            return campaigns
        except Exception as e:
            logger.error(f"Error getting client campaigns: {str(e)}")
            return []
    
    def list_dashboard_links_for_client(self, client_id: int) -> List[Dict]:
        """List all dashboard links for a client ordered by creation time, including KPI selections"""
        try:
            table = self._get_table("dashboard_links")
            query = (
                select(table)
                .where(table.c.client_id == client_id)
                .order_by(table.c.created_at.desc())
            )
            result = self.db.execute(query)
            links = []
            for row in result:
                link_dict = dict(row._mapping)
                link_id = link_dict.get("id")
                
                # Fetch KPI selections for this link
                if link_id:
                    kpi_selection = self.get_dashboard_link_kpi_selection(link_id)
                    if kpi_selection:
                        link_dict["kpi_selection"] = kpi_selection
                
                links.append(link_dict)
            return links
        except Exception as e:
            logger.error(f"Error listing dashboard links for client {client_id}: {str(e)}")
            return []

    def get_dashboard_link_by_slug(self, slug: str) -> Optional[Dict]:
        """Get a dashboard link by slug, including KPI selections and executive summary"""
        try:
            table = self._get_table("dashboard_links")
            query = select(table).where(table.c.slug == slug).limit(1)
            result = self.db.execute(query).first()
            if result:
                link_dict = dict(result._mapping)
                link_id = link_dict.get("id")
                
                # Log executive summary for debugging
                logger.info(f"Dashboard link {link_id} (slug: {slug}) - executive_summary present: {bool(link_dict.get('executive_summary'))}")
                if link_dict.get('executive_summary'):
                    logger.debug(f"Executive summary keys: {list(link_dict.get('executive_summary', {}).keys()) if isinstance(link_dict.get('executive_summary'), dict) else 'not a dict'}")
                
                # Fetch KPI selections for this link
                if link_id:
                    kpi_selection = self.get_dashboard_link_kpi_selection(link_id)
                    if kpi_selection:
                        link_dict["kpi_selection"] = kpi_selection
                    # Executive summary is already included in link_dict from the query
                
                return link_dict
            return None
        except Exception as e:
            logger.error(f"Error getting dashboard link by slug {slug}: {str(e)}")
            return None

    def list_all_dashboard_links(self) -> List[Dict]:
        """List all dashboard links across all clients, including KPI selections and executive summaries - optimized batch query"""
        try:
            table = self._get_table("dashboard_links")
            # Get all links with a single query
            query = (
                select(table)
                .order_by(table.c.created_at.desc())
            )
            result = self.db.execute(query)
            links = []
            
            # Get all client IDs and link IDs to batch fetch related data
            client_ids = set()
            link_ids = []
            link_rows = []
            for row in result:
                link_dict = dict(row._mapping)
                link_id = link_dict.get("id")
                client_id = link_dict.get("client_id")
                if client_id:
                    client_ids.add(client_id)
                if link_id:
                    link_ids.append(link_id)
                link_rows.append((link_id, client_id, link_dict))
            
            # Batch fetch all clients in one query
            clients_map = {}
            if client_ids:
                clients_table = self._get_table("clients")
                clients_query = select(clients_table).where(clients_table.c.id.in_(list(client_ids)))
                clients_result = self.db.execute(clients_query)
                for client_row in clients_result:
                    client_dict = dict(client_row._mapping)
                    clients_map[client_dict["id"]] = client_dict
            
            # Batch fetch all KPI selections in one query
            kpi_selections_map = {}
            if link_ids:
                kpi_selection_table = self._get_table("dashboard_link_kpi_selections")
                kpi_query = select(kpi_selection_table).where(kpi_selection_table.c.dashboard_link_id.in_(link_ids))
                kpi_result = self.db.execute(kpi_query)
                for kpi_row in kpi_result:
                    kpi_dict = dict(kpi_row._mapping)
                    link_id = kpi_dict.get("dashboard_link_id")
                    if link_id:
                        # Format KPI selection to match get_dashboard_link_kpi_selection structure
                        kpi_selection_data = {
                            "dashboard_link_id": link_id,
                            "selected_kpis": kpi_dict.get("selected_kpis") or [],
                            "visible_sections": kpi_dict.get("visible_sections") or [],
                            "selected_charts": kpi_dict.get("selected_charts") or [],
                            "selected_performance_metrics_kpis": kpi_dict.get("selected_performance_metrics_kpis") or [],
                            "created_at": kpi_dict.get("created_at").isoformat() if kpi_dict.get("created_at") else None,
                            "updated_at": kpi_dict.get("updated_at").isoformat() if kpi_dict.get("updated_at") else None
                        }
                        # Include show_change_period if it exists
                        if kpi_dict.get("show_change_period"):
                            kpi_selection_data["show_change_period"] = kpi_dict.get("show_change_period")
                        kpi_selections_map[link_id] = kpi_selection_data
            
            # Process links and attach related data
            for link_id, client_id, link_dict in link_rows:
                # Attach KPI selection if available
                if link_id and link_id in kpi_selections_map:
                    link_dict["kpi_selection"] = kpi_selections_map[link_id]
                
                # Add client information
                if client_id and client_id in clients_map:
                    link_dict["client_id"] = client_id
                    link_dict["client_name"] = clients_map[client_id].get("company_name", "Unknown")
                
                links.append(link_dict)
            
            logger.info(f"Loaded {len(links)} dashboard links across all clients (batch optimized)")
            return links
        except Exception as e:
            logger.error(f"Error listing all dashboard links: {str(e)}")
            return []

    def disable_dashboard_link(self, link_id: int, user_email: Optional[str] = None) -> bool:
        """Disable a dashboard link"""
        try:
            table = self._get_table("dashboard_links")
            update_stmt = (
                update(table)
                .where(table.c.id == link_id)
                .values(enabled=False, updated_at=datetime.now())
            )
            result = self.db.execute(update_stmt)
            self.db.commit()
            return result.rowcount > 0
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error disabling dashboard link {link_id}: {str(e)}")
            return False

    def upsert_dashboard_link(
        self,
        client_id: int,
        start_date: date,
        end_date: date,
        slug: Optional[str] = None,
        enabled: bool = True,
        expires_at: Optional[datetime] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        user_email: Optional[str] = None,
        selected_kpis: Optional[List[str]] = None,
        visible_sections: Optional[List[str]] = None,
        selected_charts: Optional[List[str]] = None,
        selected_performance_metrics_kpis: Optional[List[str]] = None,
        show_change_period: Optional[Dict[str, bool]] = None,
        executive_summary: Optional[Dict] = None
    ) -> Optional[Dict]:
        """Create or update a dashboard link for a client based on date range"""
        try:
            table = self._get_table("dashboard_links")
            link_slug = slug or self.generate_client_slug()
            now = datetime.now()

            # Check if name, description, and executive_summary columns exist
            table_columns = [col.name for col in table.c]
            has_name_column = 'name' in table_columns
            has_description_column = 'description' in table_columns
            has_executive_summary_column = 'executive_summary' in table_columns

            link_data = {
                "client_id": client_id,
                "slug": link_slug,
                "start_date": start_date,
                "end_date": end_date,
                "enabled": enabled,
                "expires_at": expires_at,
                "updated_at": now,
            }

            # Only include name/description/executive_summary if columns exist
            if has_name_column and name is not None:
                link_data["name"] = name
            if has_description_column and description is not None:
                link_data["description"] = description
            if has_executive_summary_column and executive_summary is not None:
                link_data["executive_summary"] = executive_summary

            insert_stmt = pg_insert(table).values(
                **link_data,
                created_at=now
            ).returning(table)

            # Build update set conditionally
            update_set = {
                "slug": insert_stmt.excluded.slug,
                "enabled": insert_stmt.excluded.enabled,
                "expires_at": insert_stmt.excluded.expires_at,
                "updated_at": insert_stmt.excluded.updated_at,
            }
            
            # Only update name/description/executive_summary if columns exist
            if has_name_column:
                update_set["name"] = insert_stmt.excluded.name
            if has_description_column:
                update_set["description"] = insert_stmt.excluded.description
            if has_executive_summary_column:
                update_set["executive_summary"] = insert_stmt.excluded.executive_summary

            insert_stmt = insert_stmt.on_conflict_do_update(
                index_elements=['client_id', 'start_date', 'end_date'],
                set_=update_set
            )

            result = self.db.execute(insert_stmt)
            self.db.commit()

            row = result.fetchone()
            if row:
                link_dict = dict(row._mapping)
                link_id = link_dict.get("id")
                
                # Save KPI selections if provided
                if link_id and (selected_kpis is not None or visible_sections is not None or selected_charts is not None or selected_performance_metrics_kpis is not None or show_change_period is not None):
                    kpi_selection = self.upsert_dashboard_link_kpi_selection(
                        link_id=link_id,
                        selected_kpis=selected_kpis or [],
                        visible_sections=visible_sections,
                        selected_charts=selected_charts or [],
                        selected_performance_metrics_kpis=selected_performance_metrics_kpis or [],
                        show_change_period=show_change_period
                    )
                    if kpi_selection:
                        link_dict["kpi_selection"] = kpi_selection
                
                # Include executive_summary in response if it exists
                if link_dict.get("executive_summary"):
                    link_dict["executive_summary"] = link_dict["executive_summary"]
                
                return link_dict
            return None
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error upserting dashboard link for client {client_id}: {str(e)}")
            return None

    def track_dashboard_link_open(
        self,
        link_id: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        referer: Optional[str] = None
    ) -> bool:
        """Record a tracking entry when a dashboard link is opened"""
        try:
            table = self._get_table("dashboard_link_tracking")
            insert_stmt = table.insert().values(
                dashboard_link_id=link_id,
                ip_address=ip_address,
                user_agent=user_agent,
                referer=referer,
                opened_at=datetime.now()
            )
            self.db.execute(insert_stmt)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error tracking dashboard link open for link {link_id}: {str(e)}")
            return False

    def get_dashboard_link_metrics(
        self,
        link_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict:
        """Get metrics for a specific dashboard link"""
        try:
            tracking_table = self._get_table("dashboard_link_tracking")
            
            # Base query
            query = select(
                func.count(tracking_table.c.id).label("total_opens")
            ).where(tracking_table.c.dashboard_link_id == link_id)
            
            # Apply date filters if provided
            if start_date:
                query = query.where(tracking_table.c.opened_at >= start_date)
            if end_date:
                # Add one day to include the end date
                from datetime import timedelta
                end_datetime = datetime.combine(end_date, datetime.max.time())
                query = query.where(tracking_table.c.opened_at <= end_datetime)
            
            result = self.db.execute(query)
            total_opens = result.scalar() or 0
            
            # Get opens over time (daily aggregation)
            daily_query = select(
                func.date(tracking_table.c.opened_at).label("date"),
                func.count(tracking_table.c.id).label("opens")
            ).where(tracking_table.c.dashboard_link_id == link_id)
            
            if start_date:
                daily_query = daily_query.where(tracking_table.c.opened_at >= start_date)
            if end_date:
                from datetime import timedelta
                end_datetime = datetime.combine(end_date, datetime.max.time())
                daily_query = daily_query.where(tracking_table.c.opened_at <= end_datetime)
            
            daily_query = daily_query.group_by(func.date(tracking_table.c.opened_at)).order_by(func.date(tracking_table.c.opened_at))
            daily_result = self.db.execute(daily_query)
            opens_over_time = [{"date": str(row.date), "opens": row.opens} for row in daily_result]
            
            # Get recent opens (last 50)
            recent_query = select(tracking_table).where(
                tracking_table.c.dashboard_link_id == link_id
            ).order_by(tracking_table.c.opened_at.desc()).limit(50)
            
            recent_result = self.db.execute(recent_query)
            recent_opens = [dict(row._mapping) for row in recent_result]
            
            return {
                "total_opens": total_opens,
                "opens_over_time": opens_over_time,
                "recent_opens": recent_opens
            }
        except Exception as e:
            logger.error(f"Error getting dashboard link metrics for link {link_id}: {str(e)}")
            return {
                "total_opens": 0,
                "opens_over_time": [],
                "recent_opens": []
            }

    def get_client_dashboard_links_metrics(
        self,
        client_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict:
        """Get aggregated metrics for all dashboard links of a client"""
        try:
            links_table = self._get_table("dashboard_links")
            tracking_table = self._get_table("dashboard_link_tracking")
            
            # Get all links for the client
            links_query = select(links_table).where(links_table.c.client_id == client_id)
            links_result = self.db.execute(links_query)
            links = [dict(row._mapping) for row in links_result]
            
            total_opens = 0
            opens_per_link = []
            opens_over_time = []
            
            # Aggregate tracking data
            for link in links:
                link_id = link["id"]
                
                # Get opens for this link
                tracking_query = select(
                    func.count(tracking_table.c.id).label("opens")
                ).where(tracking_table.c.dashboard_link_id == link_id)
                
                if start_date:
                    tracking_query = tracking_query.where(tracking_table.c.opened_at >= start_date)
                if end_date:
                    from datetime import timedelta
                    end_datetime = datetime.combine(end_date, datetime.max.time())
                    tracking_query = tracking_query.where(tracking_table.c.opened_at <= end_datetime)
                
                result = self.db.execute(tracking_query)
                link_opens = result.scalar() or 0
                total_opens += link_opens
                
                opens_per_link.append({
                    "link_id": link_id,
                    "slug": link["slug"],
                    "name": link.get("name"),
                    "opens": link_opens
                })
            
            # Get opens over time (aggregated across all links)
            daily_query = select(
                func.date(tracking_table.c.opened_at).label("date"),
                func.count(tracking_table.c.id).label("opens")
            ).join(
                links_table, tracking_table.c.dashboard_link_id == links_table.c.id
            ).where(links_table.c.client_id == client_id)
            
            if start_date:
                daily_query = daily_query.where(tracking_table.c.opened_at >= start_date)
            if end_date:
                from datetime import timedelta
                end_datetime = datetime.combine(end_date, datetime.max.time())
                daily_query = daily_query.where(tracking_table.c.opened_at <= end_datetime)
            
            daily_query = daily_query.group_by(func.date(tracking_table.c.opened_at)).order_by(func.date(tracking_table.c.opened_at))
            daily_result = self.db.execute(daily_query)
            opens_over_time = [{"date": str(row.date), "opens": row.opens} for row in daily_result]
            
            return {
                "total_opens": total_opens,
                "opens_per_link": opens_per_link,
                "opens_over_time": opens_over_time,
                "total_links": len(links)
            }
        except Exception as e:
            logger.error(f"Error getting client dashboard links metrics for client {client_id}: {str(e)}")
            return {
                "total_opens": 0,
                "opens_per_link": [],
                "opens_over_time": [],
                "total_links": 0
            }

    def update_dashboard_link(
        self,
        link_id: int,
        updates: Dict,
        user_email: Optional[str] = None
    ) -> Optional[Dict]:
        """Update a dashboard link"""
        try:
            table = self._get_table("dashboard_links")
            
            # Check if name, description, and executive_summary columns exist
            table_columns = [col.name for col in table.c]
            has_name_column = 'name' in table_columns
            has_description_column = 'description' in table_columns
            has_executive_summary_column = 'executive_summary' in table_columns
            
            # Extract KPI selection fields if present (these are handled separately)
            selected_kpis = updates.pop("selected_kpis", None)
            visible_sections = updates.pop("visible_sections", None)
            selected_charts = updates.pop("selected_charts", None)
            selected_performance_metrics_kpis = updates.pop("selected_performance_metrics_kpis", None)
            show_change_period = updates.pop("show_change_period", None)
            # Extract executive_summary but we'll add it back to update_data if column exists
            executive_summary = updates.pop("executive_summary", None)
            
            # Only allow updating specific fields
            allowed_fields = ["start_date", "end_date", "enabled", "expires_at", "slug"]
            if has_name_column:
                allowed_fields.append("name")
            if has_description_column:
                allowed_fields.append("description")
            if has_executive_summary_column:
                allowed_fields.append("executive_summary")
            
            update_data = {k: v for k, v in updates.items() if k in allowed_fields}
            
            # Add executive_summary back to update_data if it was provided and column exists
            if has_executive_summary_column and executive_summary is not None:
                update_data["executive_summary"] = executive_summary
                logger.info(f"Adding executive_summary to update_data for link {link_id}, type: {type(executive_summary)}")
            
            # Update link fields if any
            if update_data:
                update_data["updated_at"] = datetime.now()
                
                update_stmt = (
                    update(table)
                    .where(table.c.id == link_id)
                    .values(**update_data)
                    .returning(table)
                )
                
                result = self.db.execute(update_stmt)
                self.db.commit()
                
                row = result.fetchone()
                if not row:
                    return None
            else:
                # If no link fields to update, just fetch the link
                query = select(table).where(table.c.id == link_id).limit(1)
                result = self.db.execute(query)
                row = result.first()
                if not row:
                    return None
            
            link_dict = dict(row._mapping)
            
            # Update KPI selections if provided
            if selected_kpis is not None or visible_sections is not None or selected_charts is not None or selected_performance_metrics_kpis is not None or show_change_period is not None:
                kpi_selection = self.upsert_dashboard_link_kpi_selection(
                    link_id=link_id,
                    selected_kpis=selected_kpis if selected_kpis is not None else [],
                    visible_sections=visible_sections,
                    selected_charts=selected_charts if selected_charts is not None else [],
                    selected_performance_metrics_kpis=selected_performance_metrics_kpis if selected_performance_metrics_kpis is not None else [],
                    show_change_period=show_change_period
                )
                if kpi_selection:
                    link_dict["kpi_selection"] = kpi_selection
            
            # Executive summary is already included in link_dict from the update query
            return link_dict
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating dashboard link {link_id}: {str(e)}")
            return None

    def delete_dashboard_link(self, link_id: int) -> bool:
        """Delete a dashboard link (cascades to tracking records and KPI selections)"""
        try:
            table = self._get_table("dashboard_links")
            delete_stmt = table.delete().where(table.c.id == link_id)
            result = self.db.execute(delete_stmt)
            self.db.commit()
            return result.rowcount > 0
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting dashboard link {link_id}: {str(e)}")
            return False

    def get_dashboard_link_kpi_selection(self, link_id: int) -> Optional[Dict]:
        """Get KPI selections for a dashboard link"""
        try:
            table = self._get_table("dashboard_link_kpi_selections")
            query = select(table).where(table.c.dashboard_link_id == link_id).limit(1)
            result = self.db.execute(query)
            row = result.first()
            
            if row:
                result_dict = {
                    "dashboard_link_id": link_id,
                    "selected_kpis": row.selected_kpis or [],
                    "visible_sections": row.visible_sections or [],
                    "selected_charts": row.selected_charts or [],
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None
                }
                # Include selected_performance_metrics_kpis if the column exists
                if hasattr(row, 'selected_performance_metrics_kpis'):
                    result_dict["selected_performance_metrics_kpis"] = row.selected_performance_metrics_kpis or []
                # Include show_change_period if the column exists
                if hasattr(row, 'show_change_period') and row.show_change_period:
                    result_dict["show_change_period"] = row.show_change_period
                return result_dict
            return None
        except Exception as e:
            logger.error(f"Error getting KPI selection for dashboard link {link_id}: {str(e)}")
            return None

    def upsert_dashboard_link_kpi_selection(
        self,
        link_id: int,
        selected_kpis: List[str],
        visible_sections: Optional[List[str]] = None,
        selected_charts: Optional[List[str]] = None,
        selected_performance_metrics_kpis: Optional[List[str]] = None,
        show_change_period: Optional[Dict[str, bool]] = None
    ) -> Optional[Dict]:
        """Create or update KPI selections for a dashboard link"""
        try:
            table = self._get_table("dashboard_link_kpi_selections")
            now = datetime.now()
            
            # Default visible sections if not provided
            if visible_sections is None:
                visible_sections = ['ga4', 'scrunch_ai', 'brand_analytics', 'advanced_analytics', 'keywords']
            
            # Default selected_charts if not provided
            if selected_charts is None:
                selected_charts = []
            
            # Default selected_performance_metrics_kpis if not provided
            if selected_performance_metrics_kpis is None:
                selected_performance_metrics_kpis = []
            
            # Default show_change_period if not provided
            if show_change_period is None:
                show_change_period = {
                    "ga4": True,
                    "agency_analytics": True,
                    "scrunch_ai": True,
                    "all_performance_metrics": True
                }
            
            kpi_data = {
                "dashboard_link_id": link_id,
                "selected_kpis": selected_kpis,
                "visible_sections": visible_sections,
                "selected_charts": selected_charts,
                "selected_performance_metrics_kpis": selected_performance_metrics_kpis,
                "updated_at": now,
            }
            
            # Only add show_change_period if column exists
            table_columns = [col.name for col in table.c]
            if 'show_change_period' in table_columns:
                kpi_data["show_change_period"] = show_change_period
            
            insert_stmt = pg_insert(table).values(
                **kpi_data,
                created_at=now
            ).returning(table)
            
            update_set = {
                "selected_kpis": insert_stmt.excluded.selected_kpis,
                "visible_sections": insert_stmt.excluded.visible_sections,
                "selected_charts": insert_stmt.excluded.selected_charts,
                "selected_performance_metrics_kpis": insert_stmt.excluded.selected_performance_metrics_kpis,
                "updated_at": insert_stmt.excluded.updated_at,
            }
            
            # Only update show_change_period if column exists
            if 'show_change_period' in table_columns:
                update_set["show_change_period"] = insert_stmt.excluded.show_change_period
            
            insert_stmt = insert_stmt.on_conflict_do_update(
                index_elements=['dashboard_link_id'],
                set_=update_set
            )
            
            result = self.db.execute(insert_stmt)
            self.db.commit()
            
            row = result.fetchone()
            if row:
                result_dict = {
                    "dashboard_link_id": link_id,
                    "selected_kpis": row.selected_kpis or [],
                    "visible_sections": row.visible_sections or [],
                    "selected_charts": row.selected_charts or [],
                    "selected_performance_metrics_kpis": getattr(row, 'selected_performance_metrics_kpis', None) or [],
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None
                }
                # Include show_change_period if the column exists
                if hasattr(row, 'show_change_period') and row.show_change_period:
                    result_dict["show_change_period"] = row.show_change_period
                return result_dict
            return None
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error upserting KPI selection for dashboard link {link_id}: {str(e)}")
            return None

    def get_dashboard_link_executive_summary(self, link_id: int) -> Optional[Dict]:
        """Get executive summary for a dashboard link"""
        try:
            table = self._get_table("dashboard_links")
            query = select(table.c.executive_summary).where(table.c.id == link_id).limit(1)
            result = self.db.execute(query)
            row = result.first()
            
            if row and row.executive_summary:
                return row.executive_summary
            return None
        except Exception as e:
            logger.error(f"Error getting executive summary for dashboard link {link_id}: {str(e)}")
            return None

    def upsert_dashboard_link_executive_summary(
        self,
        link_id: int,
        executive_summary: Dict
    ) -> Optional[Dict]:
        """Create or update executive summary for a dashboard link"""
        try:
            table = self._get_table("dashboard_links")
            now = datetime.now()
            
            update_stmt = (
                table.update()
                .where(table.c.id == link_id)
                .values(
                    executive_summary=executive_summary,
                    updated_at=now
                )
                .returning(table.c.executive_summary)
            )
            
            result = self.db.execute(update_stmt)
            self.db.commit()
            
            row = result.first()
            if row:
                return row.executive_summary
            return None
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error upserting executive summary for dashboard link {link_id}: {str(e)}")
            return None

    def delete_dashboard_link_kpi_selection(self, link_id: int) -> bool:
        """Delete KPI selections for a dashboard link (usually handled by CASCADE, but available for explicit deletion)"""
        try:
            table = self._get_table("dashboard_link_kpi_selections")
            delete_stmt = table.delete().where(table.c.dashboard_link_id == link_id)
            result = self.db.execute(delete_stmt)
            self.db.commit()
            return result.rowcount > 0
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting KPI selection for dashboard link {link_id}: {str(e)}")
            return False

    # =====================================================
    # Agency Analytics Methods
    # =====================================================
    
    def upsert_agency_analytics_campaign(self, campaign: Dict) -> int:
        """Upsert Agency Analytics campaign metadata using SQLAlchemy Core (local PostgreSQL)"""
        try:
            table = self._get_table("agency_analytics_campaigns")
            campaign_id = campaign.get("id")
            
            if not campaign_id:
                logger.warning("Campaign missing ID, skipping upsert")
                return 0
            
            # Prepare record data - handle date strings and None values
            record = {
                "id": campaign_id,
                "date_created": self._parse_datetime(campaign.get("date_created")),
                "date_modified": self._parse_datetime(campaign.get("date_modified")),
                "url": campaign.get("url"),
                "company": campaign.get("company"),
                "scope": campaign.get("scope"),
                "status": campaign.get("status"),
                "group_title": campaign.get("group_title"),
                "email_addresses": campaign.get("email_addresses"),
                "phone_numbers": campaign.get("phone_numbers"),
                "address": campaign.get("address"),
                "city": campaign.get("city"),
                "state": campaign.get("state"),
                "zip": campaign.get("zip"),
                "country": campaign.get("country"),
                "revenue": campaign.get("revenue"),
                "headcount": campaign.get("headcount"),
                "google_ignore_places": campaign.get("google_ignore_places"),
                "enforce_google_cid": campaign.get("enforce_google_cid"),
                "timezone": campaign.get("timezone"),
                "type": campaign.get("type"),
                "campaign_group_id": campaign.get("campaign_group_id"),
                "company_id": campaign.get("company_id"),
                "account_id": campaign.get("account_id"),
                "updated_at": datetime.now()
            }
            
            # Remove None values to avoid issues with NOT NULL constraints
            clean_record = {k: v for k, v in record.items() if v is not None}
            
            # Use PostgreSQL INSERT ... ON CONFLICT for upsert
            insert_stmt = pg_insert(table).values(**clean_record)
            insert_stmt = insert_stmt.on_conflict_do_update(
                index_elements=['id'],
                set_={
                    'date_created': insert_stmt.excluded.date_created,
                    'date_modified': insert_stmt.excluded.date_modified,
                    'url': insert_stmt.excluded.url,
                    'company': insert_stmt.excluded.company,
                    'scope': insert_stmt.excluded.scope,
                    'status': insert_stmt.excluded.status,
                    'group_title': insert_stmt.excluded.group_title,
                    'email_addresses': insert_stmt.excluded.email_addresses,
                    'phone_numbers': insert_stmt.excluded.phone_numbers,
                    'address': insert_stmt.excluded.address,
                    'city': insert_stmt.excluded.city,
                    'state': insert_stmt.excluded.state,
                    'zip': insert_stmt.excluded.zip,
                    'country': insert_stmt.excluded.country,
                    'revenue': insert_stmt.excluded.revenue,
                    'headcount': insert_stmt.excluded.headcount,
                    'google_ignore_places': insert_stmt.excluded.google_ignore_places,
                    'enforce_google_cid': insert_stmt.excluded.enforce_google_cid,
                    'timezone': insert_stmt.excluded.timezone,
                    'type': insert_stmt.excluded.type,
                    'campaign_group_id': insert_stmt.excluded.campaign_group_id,
                    'company_id': insert_stmt.excluded.company_id,
                    'account_id': insert_stmt.excluded.account_id,
                    'updated_at': insert_stmt.excluded.updated_at
                }
            )
            
            self.db.execute(insert_stmt)
            self.db.commit()
            logger.debug(f"Upserted campaign {campaign_id}")
            return 1
            
        except Exception as e:
            self.db.rollback()
            error_str = str(e)
            logger.error(f"Error upserting campaign {campaign.get('id')}: {error_str}")
            # Don't raise - return 0 to allow sync to continue
            return 0
    
    def upsert_agency_analytics_rankings(self, rankings: List[Dict]) -> int:
        """Upsert Agency Analytics campaign rankings - Optimized with bulk operations"""
        if not rankings:
            return 0
        
        try:
            table = self._get_table("agency_analytics_campaign_rankings")
            
            # Filter out records without required field
            valid_rankings = [r for r in rankings if r.get("campaign_id_date")]
            
            if not valid_rankings:
                return 0
            
            # Process in larger batches for better performance
            batch_size = 1000  # Increased from 500
            total_upserted = 0
            now = datetime.now()
            
            for i in range(0, len(valid_rankings), batch_size):
                batch = valid_rankings[i:i + batch_size]
                
                # Prepare all records in batch
                records = []
                for record in batch:
                    clean_record = {
                        "campaign_id": record.get("campaign_id"),
                        "client_name": record.get("client_name"),
                        "date": record.get("date"),
                        "campaign_id_date": record.get("campaign_id_date"),
                        "google_ranking_count": record.get("google_ranking_count", 0),
                        "google_ranking_change": record.get("google_ranking_change", 0),
                        "google_local_count": record.get("google_local_count", 0),
                        "google_mobile_count": record.get("google_mobile_count", 0),
                        "bing_ranking_count": record.get("bing_ranking_count", 0),
                        "ranking_average": record.get("ranking_average", 0),
                        "search_volume": record.get("search_volume", 0),
                        "competition": record.get("competition", 0),
                        "updated_at": now
                    }
                    # Remove None values
                    clean_record = {k: v for k, v in clean_record.items() if v is not None}
                    records.append(clean_record)
                
                # Bulk insert with ON CONFLICT - execute all at once
                if records:
                    insert_stmt = pg_insert(table).values(records)
                    insert_stmt = insert_stmt.on_conflict_do_update(
                        index_elements=['campaign_id_date'],
                        set_={
                            'campaign_id': insert_stmt.excluded.campaign_id,
                            'client_name': insert_stmt.excluded.client_name,
                            'date': insert_stmt.excluded.date,
                            'google_ranking_count': insert_stmt.excluded.google_ranking_count,
                            'google_ranking_change': insert_stmt.excluded.google_ranking_change,
                            'google_local_count': insert_stmt.excluded.google_local_count,
                            'google_mobile_count': insert_stmt.excluded.google_mobile_count,
                            'bing_ranking_count': insert_stmt.excluded.bing_ranking_count,
                            'ranking_average': insert_stmt.excluded.ranking_average,
                            'search_volume': insert_stmt.excluded.search_volume,
                            'competition': insert_stmt.excluded.competition,
                            'updated_at': insert_stmt.excluded.updated_at
                        }
                    )
                    self.db.execute(insert_stmt)
                    self.db.commit()
                
                total_upserted += len(batch)
                logger.debug(f"Upserted batch {i//batch_size + 1}: {len(batch)} records")
            
            logger.info(f"Total upserted {total_upserted} rankings")
            return total_upserted
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error upserting rankings: {str(e)}")
            raise
    
    def link_campaign_to_brand(self, campaign_id: int, brand_id: int, match_method: str = "url_match", match_confidence: str = "exact") -> int:
        """Link an Agency Analytics campaign to a brand using SQLAlchemy Core (local PostgreSQL)"""
        try:
            table = self._get_table("agency_analytics_campaign_brands")
            
            record = {
                "campaign_id": campaign_id,
                "brand_id": brand_id,
                "match_method": match_method,
                "match_confidence": match_confidence,
                "updated_at": datetime.now()
            }
            
            # Use PostgreSQL INSERT ... ON CONFLICT for upsert
            insert_stmt = pg_insert(table).values(**record)
            insert_stmt = insert_stmt.on_conflict_do_update(
                index_elements=['campaign_id', 'brand_id'],
                set_={
                    'match_method': insert_stmt.excluded.match_method,
                    'match_confidence': insert_stmt.excluded.match_confidence,
                    'updated_at': insert_stmt.excluded.updated_at
                }
            )
            
            self.db.execute(insert_stmt)
            self.db.commit()
            logger.info(f"Linked campaign {campaign_id} to brand {brand_id} ({match_method}, {match_confidence})")
            return 1
        except Exception as e:
            self.db.rollback()
            error_str = str(e)
            # Check if table doesn't exist
            if "does not exist" in error_str.lower() or "Could not find" in error_str:
                logger.warning(f"Table 'agency_analytics_campaign_brands' does not exist yet. Please run the SQL script to create it. Skipping link for campaign {campaign_id} to brand {brand_id}.")
                return 0  # Return 0 instead of raising error
            logger.error(f"Error linking campaign to brand: {error_str}")
            raise
    
    def upsert_brand_kpi_selection(
        self,
        brand_id: int,
        selected_kpis: List[str],
        visible_sections: Optional[List[str]] = None,
        selected_charts: Optional[List[str]] = None,
        version: Optional[int] = None,
        last_modified_by: Optional[str] = None
    ) -> Dict:
        """Upsert KPI selection for a brand using SQLAlchemy Core with ON CONFLICT"""
        try:
            import json
            table = self._get_table("brand_kpi_selections")
            
            # Prepare data
            selection_data = {
                "brand_id": brand_id,
                "selected_kpis": selected_kpis,
                "visible_sections": visible_sections or ["ga4", "scrunch_ai", "brand_analytics", "advanced_analytics", "performance_metrics"],
                "selected_charts": selected_charts or [],
                "last_modified_by": last_modified_by,
                "updated_at": datetime.utcnow()
            }
            
            # If version is provided, increment it; otherwise set to 1
            if version is not None:
                selection_data["version"] = version + 1
            else:
                # Check existing version
                existing_query = select(table.c.version).where(table.c.brand_id == brand_id).limit(1)
                existing_result = self.db.execute(existing_query)
                existing_row = existing_result.first()
                if existing_row:
                    selection_data["version"] = existing_row.version + 1
                else:
                    selection_data["version"] = 1
            
            # Use PostgreSQL INSERT ... ON CONFLICT for upsert
            stmt = pg_insert(table).values(**selection_data)
            stmt = stmt.on_conflict_do_update(
                index_elements=['brand_id'],
                set_={
                    "selected_kpis": stmt.excluded.selected_kpis,
                    "visible_sections": stmt.excluded.visible_sections,
                    "selected_charts": stmt.excluded.selected_charts,
                    "version": stmt.excluded.version,
                    "last_modified_by": stmt.excluded.last_modified_by,
                    "updated_at": stmt.excluded.updated_at
                }
            )
            
            self.db.execute(stmt)
            self.db.commit()
            
            # Get updated record
            query = select(table).where(table.c.brand_id == brand_id).limit(1)
            result = self.db.execute(query)
            row = result.first()
            
            if row:
                return {
                    "brand_id": brand_id,
                    "selected_kpis": row.selected_kpis or [],
                    "visible_sections": row.visible_sections or [],
                    "selected_charts": row.selected_charts or [],
                    "version": row.version,
                    "last_modified_by": row.last_modified_by,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None
                }
            return selection_data
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error upserting KPI selection: {str(e)}")
            raise
    
    def get_brand_kpi_selection(self, brand_id: int) -> Optional[Dict]:
        """Get KPI selection for a brand (backward compatibility)"""
        try:
            table = self._get_table("brand_kpi_selections")
            query = select(table).where(table.c.brand_id == brand_id).limit(1)
            result = self.db.execute(query)
            row = result.first()
            
            if row:
                return {
                    "brand_id": brand_id,
                    "client_id": row.client_id,
                    "selected_kpis": row.selected_kpis or [],
                    "visible_sections": row.visible_sections or [],
                    "selected_charts": row.selected_charts or [],
                    "version": row.version or 1,
                    "last_modified_by": row.last_modified_by,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None
                }
            return None
        except Exception as e:
            logger.error(f"Error getting KPI selection: {str(e)}")
            return None
    
    def get_client_kpi_selection(self, client_id: int) -> Optional[Dict]:
        """Get KPI selection for a client (client-centric)"""
        try:
            table = self._get_table("brand_kpi_selections")
            query = select(table).where(table.c.client_id == client_id).limit(1)
            result = self.db.execute(query)
            row = result.first()
            
            if row:
                return {
                    "client_id": client_id,
                    "brand_id": row.brand_id,
                    "selected_kpis": row.selected_kpis or [],
                    "visible_sections": row.visible_sections or [],
                    "selected_charts": row.selected_charts or [],
                    "selected_performance_metrics_kpis": getattr(row, 'selected_performance_metrics_kpis', None) or [],
                    "version": row.version or 1,
                    "last_modified_by": row.last_modified_by,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None
                }
            return None
        except Exception as e:
            logger.error(f"Error getting KPI selection for client {client_id}: {str(e)}")
            return None
    
    def upsert_client_kpi_selection(
        self,
        client_id: int,
        selected_kpis: List[str],
        visible_sections: Optional[List[str]] = None,
        selected_charts: Optional[List[str]] = None,
        selected_performance_metrics_kpis: Optional[List[str]] = None,
        version: Optional[int] = None,
        last_modified_by: Optional[str] = None
    ) -> Dict:
        """Upsert KPI selection for a client using SQLAlchemy Core with ON CONFLICT (client-centric)"""
        try:
            import json
            from datetime import datetime
            table = self._get_table("brand_kpi_selections")
            
            # Get client to derive brand_id (for backward compatibility)
            client = self.get_client_by_id(client_id)
            if not client:
                raise ValueError(f"Client {client_id} not found")
            brand_id = client.get("scrunch_brand_id")
            
            # Prepare data
            selection_data = {
                "client_id": client_id,
                "brand_id": brand_id,  # For backward compatibility
                "selected_kpis": selected_kpis,
                "visible_sections": visible_sections or ["ga4", "scrunch_ai", "brand_analytics", "advanced_analytics", "performance_metrics"],
                "selected_charts": selected_charts or [],
                "selected_performance_metrics_kpis": selected_performance_metrics_kpis or [],
                "last_modified_by": last_modified_by,
                "updated_at": datetime.utcnow()
            }
            
            # If version is provided, increment it; otherwise set to 1
            if version is not None:
                selection_data["version"] = version + 1
            else:
                # Check existing version
                existing_query = select(table.c.version).where(table.c.client_id == client_id).limit(1)
                existing_result = self.db.execute(existing_query)
                existing_row = existing_result.first()
                if existing_row:
                    selection_data["version"] = existing_row.version + 1
                else:
                    selection_data["version"] = 1
            
            # Use PostgreSQL INSERT ... ON CONFLICT for upsert (using client_id as unique key)
            stmt = pg_insert(table).values(**selection_data)
            stmt = stmt.on_conflict_do_update(
                index_elements=['client_id'],
                set_={
                    "brand_id": stmt.excluded.brand_id,  # Update brand_id in case it changed
                    "selected_kpis": stmt.excluded.selected_kpis,
                    "visible_sections": stmt.excluded.visible_sections,
                    "selected_charts": stmt.excluded.selected_charts,
                    "selected_performance_metrics_kpis": stmt.excluded.selected_performance_metrics_kpis,
                    "version": stmt.excluded.version,
                    "last_modified_by": stmt.excluded.last_modified_by,
                    "updated_at": stmt.excluded.updated_at
                }
            )
            
            self.db.execute(stmt)
            self.db.commit()
            
            # Get updated record
            query = select(table).where(table.c.client_id == client_id).limit(1)
            result = self.db.execute(query)
            row = result.first()
            
            if row:
                return {
                    "client_id": client_id,
                    "brand_id": row.brand_id,
                    "selected_kpis": row.selected_kpis or [],
                    "visible_sections": row.visible_sections or [],
                    "selected_charts": row.selected_charts or [],
                    "version": row.version,
                    "last_modified_by": row.last_modified_by,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None
                }
            return selection_data
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error upserting KPI selection for client {client_id}: {str(e)}")
            raise
    
    def get_campaign_brand_links(self, campaign_id: Optional[int] = None, brand_id: Optional[int] = None) -> List[Dict]:
        """Get campaign-brand links using SQLAlchemy Core"""
        try:
            table = self._get_table("agency_analytics_campaign_brands")
            query = select(table)
            
            if campaign_id:
                query = query.where(table.c.campaign_id == campaign_id)
            if brand_id:
                query = query.where(table.c.brand_id == brand_id)
            
            result = self.db.execute(query)
            return [dict(row._mapping) for row in result]
        except Exception as e:
            # Table might not exist, return empty list
            if "does not exist" in str(e).lower() or "Could not find" in str(e):
                logger.warning(f"Table 'agency_analytics_campaign_brands' does not exist: {str(e)}")
                return []
            logger.error(f"Error getting campaign-brand links: {str(e)}")
            raise
    
    def upsert_agency_analytics_keywords(self, keywords: List[Dict]) -> int:
        """Upsert Agency Analytics keywords - Optimized with bulk operations"""
        if not keywords:
            return 0
        
        try:
            table = self._get_table("agency_analytics_keywords")
            
            # Filter out records without required field
            valid_keywords = [r for r in keywords if r.get("campaign_keyword_id")]
            
            if not valid_keywords:
                return 0
            
            # Process in larger batches for better performance
            batch_size = 1000  # Increased from 500
            total_upserted = 0
            now = datetime.now()
            
            for i in range(0, len(valid_keywords), batch_size):
                batch = valid_keywords[i:i + batch_size]
                
                # Prepare all records in batch
                records = []
                for record in batch:
                    clean_record = {
                        "id": record.get("id"),
                        "campaign_id": record.get("campaign_id"),
                        "campaign_keyword_id": record.get("campaign_keyword_id"),
                        "keyword_phrase": record.get("keyword_phrase"),
                        "primary_keyword": record.get("primary_keyword", False),
                        "search_location": record.get("search_location"),
                        "search_location_formatted_name": record.get("search_location_formatted_name"),
                        "search_location_region_name": record.get("search_location_region_name"),
                        "search_location_country_code": record.get("search_location_country_code"),
                        "search_location_latitude": record.get("search_location_latitude"),
                        "search_location_longitude": record.get("search_location_longitude"),
                        "search_language": record.get("search_language"),
                        "tags": record.get("tags"),
                        "date_created": self._parse_datetime(record.get("date_created")),
                        "date_modified": self._parse_datetime(record.get("date_modified")),
                        "updated_at": now
                    }
                    # Remove None values
                    clean_record = {k: v for k, v in clean_record.items() if v is not None}
                    records.append(clean_record)
                
                # Bulk insert with ON CONFLICT - execute all at once
                if records:
                    insert_stmt = pg_insert(table).values(records)
                    insert_stmt = insert_stmt.on_conflict_do_update(
                        index_elements=['campaign_keyword_id'],
                        set_={
                            'campaign_id': insert_stmt.excluded.campaign_id,
                            'keyword_phrase': insert_stmt.excluded.keyword_phrase,
                            'primary_keyword': insert_stmt.excluded.primary_keyword,
                            'search_location': insert_stmt.excluded.search_location,
                            'search_location_formatted_name': insert_stmt.excluded.search_location_formatted_name,
                            'search_location_region_name': insert_stmt.excluded.search_location_region_name,
                            'search_location_country_code': insert_stmt.excluded.search_location_country_code,
                            'search_location_latitude': insert_stmt.excluded.search_location_latitude,
                            'search_location_longitude': insert_stmt.excluded.search_location_longitude,
                            'search_language': insert_stmt.excluded.search_language,
                            'tags': insert_stmt.excluded.tags,
                            'date_created': insert_stmt.excluded.date_created,
                            'date_modified': insert_stmt.excluded.date_modified,
                            'updated_at': insert_stmt.excluded.updated_at
                        }
                    )
                    self.db.execute(insert_stmt)
                    self.db.commit()
                
                total_upserted += len(batch)
                logger.debug(f"Upserted batch {i//batch_size + 1}: {len(batch)} keywords")
            
            logger.info(f"Total upserted {total_upserted} keywords")
            return total_upserted
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error upserting keywords: {str(e)}")
            raise
    
    def upsert_agency_analytics_keyword_rankings(self, rankings: List[Dict]) -> int:
        """Upsert Agency Analytics keyword rankings - Optimized with bulk operations"""
        if not rankings:
            return 0
        
        try:
            table = self._get_table("agency_analytics_keyword_rankings")
            
            # Filter out records without required field
            valid_rankings = [r for r in rankings if r.get("keyword_id_date")]
            
            if not valid_rankings:
                return 0
            
            # Process in larger batches for better performance
            batch_size = 1000  # Increased from 500
            total_upserted = 0
            now = datetime.now()
            
            for i in range(0, len(valid_rankings), batch_size):
                batch = valid_rankings[i:i + batch_size]
                
                # Prepare all records in batch
                # IMPORTANT: All records must have the same keys for SQLAlchemy bulk insert
                records = []
                for record in batch:
                    # Handle results separately - ensure it's an integer or None
                    results_val = record.get("results")
                    results_int = None
                    if results_val is not None and results_val != "":
                        try:
                            results_int = int(results_val)
                        except (ValueError, TypeError):
                            # If conversion fails, set to None
                            results_int = None
                    
                    # Build record with all fields - SQLAlchemy needs consistent structure
                    clean_record = {
                        "keyword_id": record.get("keyword_id"),
                        "campaign_id": record.get("campaign_id"),
                        "keyword_id_date": record.get("keyword_id_date"),
                        "date": record.get("date"),
                        "google_ranking": record.get("google_ranking"),
                        "google_ranking_url": record.get("google_ranking_url"),
                        "google_mobile_ranking": record.get("google_mobile_ranking"),
                        "google_mobile_ranking_url": record.get("google_mobile_ranking_url"),
                        "google_local_ranking": record.get("google_local_ranking"),
                        "bing_ranking": record.get("bing_ranking"),
                        "bing_ranking_url": record.get("bing_ranking_url"),
                        "results": results_int,  # Always include, even if None (column is nullable)
                        "volume": record.get("volume"),
                        "competition": record.get("competition"),
                        "field_status": record.get("field_status"),  # JSONB
                        "updated_at": now
                    }
                    
                    # For SQLAlchemy bulk insert, we need all records to have the same keys
                    # Only remove None values for optional fields (but keep results since column is nullable)
                    # Actually, it's safer to include all fields and let SQLAlchemy handle None values
                    records.append(clean_record)
                
                # Bulk insert all records at once (no unique constraint, so just insert)
                if records:
                    try:
                        # Ensure all records have the same keys by explicitly setting None for missing keys
                        # This is critical for SQLAlchemy bulk inserts
                        all_keys = set()
                        for rec in records:
                            all_keys.update(rec.keys())
                        
                        # Make sure all records have all keys
                        normalized_records = []
                        for rec in records:
                            normalized_rec = {}
                            for key in all_keys:
                                normalized_rec[key] = rec.get(key)  # Will be None if key doesn't exist
                            normalized_records.append(normalized_rec)
                        
                        insert_stmt = insert(table).values(normalized_records)
                        result = self.db.execute(insert_stmt)
                        self.db.commit()
                        logger.debug(f"Upserted batch {i//batch_size + 1}: {len(batch)} keyword ranking records")
                    except Exception as batch_error:
                        self.db.rollback()
                        logger.error(f"Error inserting batch {i//batch_size + 1} of keyword rankings: {str(batch_error)}")
                        # Log first record for debugging
                        if records:
                            logger.debug(f"First record in failed batch: {records[0]}")
                            logger.debug(f"First record keys: {list(records[0].keys())}")
                        raise
                else:
                    logger.warning(f"Batch {i//batch_size + 1} has no valid records to insert")
                
                total_upserted += len(batch)
            
            logger.info(f"Total upserted {total_upserted} keyword rankings")
            return total_upserted
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error upserting keyword rankings: {str(e)}")
            raise
    
    def upsert_agency_analytics_keyword_ranking_summary(self, summary: Dict) -> int:
        """Upsert Agency Analytics keyword ranking summary using SQLAlchemy Core (local PostgreSQL)"""
        if not summary:
            return 0
        
        try:
            table = self._get_table("agency_analytics_keyword_ranking_summaries")
            
            # Prepare record
            clean_record = {
                "keyword_id": summary.get("keyword_id"),
                "campaign_id": summary.get("campaign_id"),
                "keyword_phrase": summary.get("keyword_phrase"),
                "keyword_id_date": summary.get("keyword_id_date"),
                "date": summary.get("date"),
                "google_ranking": summary.get("google_ranking"),
                "google_ranking_url": summary.get("google_ranking_url"),
                "google_mobile_ranking": summary.get("google_mobile_ranking"),
                "google_mobile_ranking_url": summary.get("google_mobile_ranking_url"),
                "google_local_ranking": summary.get("google_local_ranking"),
                "bing_ranking": summary.get("bing_ranking"),
                "bing_ranking_url": summary.get("bing_ranking_url"),
                "search_volume": summary.get("search_volume"),
                "competition": summary.get("competition"),
                "results": summary.get("results"),
                "field_status": summary.get("field_status"),  # JSONB
                "start_date": summary.get("start_date"),
                "end_date": summary.get("end_date"),
                "start_ranking": summary.get("start_ranking"),
                "end_ranking": summary.get("end_ranking"),
                "ranking_change": summary.get("ranking_change"),
                "updated_at": datetime.now()
            }
            
            # Remove None values
            clean_record = {k: v for k, v in clean_record.items() if v is not None}
            
            # Use PostgreSQL INSERT ... ON CONFLICT for upsert (primary key is keyword_id)
            insert_stmt = pg_insert(table).values(**clean_record)
            insert_stmt = insert_stmt.on_conflict_do_update(
                index_elements=['keyword_id'],
                set_={
                    'campaign_id': insert_stmt.excluded.campaign_id,
                    'keyword_phrase': insert_stmt.excluded.keyword_phrase,
                    'keyword_id_date': insert_stmt.excluded.keyword_id_date,
                    'date': insert_stmt.excluded.date,
                    'google_ranking': insert_stmt.excluded.google_ranking,
                    'google_ranking_url': insert_stmt.excluded.google_ranking_url,
                    'google_mobile_ranking': insert_stmt.excluded.google_mobile_ranking,
                    'google_mobile_ranking_url': insert_stmt.excluded.google_mobile_ranking_url,
                    'google_local_ranking': insert_stmt.excluded.google_local_ranking,
                    'bing_ranking': insert_stmt.excluded.bing_ranking,
                    'bing_ranking_url': insert_stmt.excluded.bing_ranking_url,
                    'search_volume': insert_stmt.excluded.search_volume,
                    'competition': insert_stmt.excluded.competition,
                    'results': insert_stmt.excluded.results,
                    'field_status': insert_stmt.excluded.field_status,
                    'start_date': insert_stmt.excluded.start_date,
                    'end_date': insert_stmt.excluded.end_date,
                    'start_ranking': insert_stmt.excluded.start_ranking,
                    'end_ranking': insert_stmt.excluded.end_ranking,
                    'ranking_change': insert_stmt.excluded.ranking_change,
                    'updated_at': insert_stmt.excluded.updated_at
                }
            )
            
            self.db.execute(insert_stmt)
            self.db.commit()
            logger.debug(f"Upserted keyword ranking summary for keyword {summary.get('keyword_id')}")
            return 1
        except Exception as e:
            self.db.rollback()
            error_str = str(e)
            # Check if table doesn't exist
            if "does not exist" in error_str.lower() or "Could not find" in error_str:
                logger.warning(f"Table 'agency_analytics_keyword_ranking_summaries' does not exist yet. Please run the SQL script to create it.")
                return 0
            logger.error(f"Error upserting keyword ranking summary: {error_str}")
            # Don't raise - return 0 to allow sync to continue
            return 0
    
    def upsert_agency_analytics_keyword_ranking_summaries_batch(self, summaries: List[Dict]) -> int:
        """Batch upsert Agency Analytics keyword ranking summaries - Optimized with bulk operations"""
        if not summaries:
            return 0
        
        try:
            table = self._get_table("agency_analytics_keyword_ranking_summaries")
            
            # Process in larger batches for better performance
            batch_size = 500  # Increased from 100
            total_upserted = 0
            now = datetime.now()
            
            for i in range(0, len(summaries), batch_size):
                batch = summaries[i:i + batch_size]
                
                # Prepare all records in batch
                # IMPORTANT: All records must have the same keys for SQLAlchemy bulk insert
                records = []
                for summary in batch:
                    clean_record = {
                        "keyword_id": summary.get("keyword_id"),
                        "campaign_id": summary.get("campaign_id"),
                        "keyword_phrase": summary.get("keyword_phrase"),
                        "keyword_id_date": summary.get("keyword_id_date"),
                        "date": summary.get("date"),
                        "google_ranking": summary.get("google_ranking"),
                        "google_ranking_url": summary.get("google_ranking_url"),
                        "google_mobile_ranking": summary.get("google_mobile_ranking"),
                        "google_mobile_ranking_url": summary.get("google_mobile_ranking_url"),
                        "google_local_ranking": summary.get("google_local_ranking"),
                        "bing_ranking": summary.get("bing_ranking"),
                        "bing_ranking_url": summary.get("bing_ranking_url"),
                        "search_volume": summary.get("search_volume"),
                        "competition": summary.get("competition"),
                        "results": summary.get("results"),  # Always include, even if None (column is nullable)
                        "field_status": summary.get("field_status"),  # JSONB
                        "start_date": summary.get("start_date"),
                        "end_date": summary.get("end_date"),
                        "start_ranking": summary.get("start_ranking"),
                        "end_ranking": summary.get("end_ranking"),
                        "ranking_change": summary.get("ranking_change"),
                        "updated_at": now
                    }
                    # For SQLAlchemy bulk insert, we need all records to have the same keys
                    # Include all fields and let SQLAlchemy handle None values
                    records.append(clean_record)
                
                # Bulk insert with ON CONFLICT - execute all at once
                if records:
                    # Ensure all records have the same keys by explicitly setting None for missing keys
                    # This is critical for SQLAlchemy bulk inserts
                    all_keys = set()
                    for rec in records:
                        all_keys.update(rec.keys())
                    
                    # Make sure all records have all keys
                    normalized_records = []
                    for rec in records:
                        normalized_rec = {}
                        for key in all_keys:
                            normalized_rec[key] = rec.get(key)  # Will be None if key doesn't exist
                        normalized_records.append(normalized_rec)
                    
                    insert_stmt = pg_insert(table).values(normalized_records)
                    insert_stmt = insert_stmt.on_conflict_do_update(
                        index_elements=['keyword_id'],
                        set_={
                            'campaign_id': insert_stmt.excluded.campaign_id,
                            'keyword_phrase': insert_stmt.excluded.keyword_phrase,
                            'keyword_id_date': insert_stmt.excluded.keyword_id_date,
                            'date': insert_stmt.excluded.date,
                            'google_ranking': insert_stmt.excluded.google_ranking,
                            'google_ranking_url': insert_stmt.excluded.google_ranking_url,
                            'google_mobile_ranking': insert_stmt.excluded.google_mobile_ranking,
                            'google_mobile_ranking_url': insert_stmt.excluded.google_mobile_ranking_url,
                            'google_local_ranking': insert_stmt.excluded.google_local_ranking,
                            'bing_ranking': insert_stmt.excluded.bing_ranking,
                            'bing_ranking_url': insert_stmt.excluded.bing_ranking_url,
                            'search_volume': insert_stmt.excluded.search_volume,
                            'competition': insert_stmt.excluded.competition,
                            'results': insert_stmt.excluded.results,
                            'field_status': insert_stmt.excluded.field_status,
                            'start_date': insert_stmt.excluded.start_date,
                            'end_date': insert_stmt.excluded.end_date,
                            'start_ranking': insert_stmt.excluded.start_ranking,
                            'end_ranking': insert_stmt.excluded.end_ranking,
                            'ranking_change': insert_stmt.excluded.ranking_change,
                            'updated_at': insert_stmt.excluded.updated_at
                        }
                    )
                    self.db.execute(insert_stmt)
                    self.db.commit()
                
                total_upserted += len(batch)
                logger.debug(f"Upserted summary batch {i//batch_size + 1}: {len(batch)} summaries")
            
            logger.info(f"Total upserted {total_upserted} keyword ranking summaries")
            return total_upserted
        except Exception as e:
            self.db.rollback()
            error_str = str(e)
            if "does not exist" in error_str.lower() or "Could not find" in error_str:
                logger.warning(f"Table 'agency_analytics_keyword_ranking_summaries' does not exist yet. Please run the SQL script to create it.")
                return 0
            logger.error(f"Error upserting keyword ranking summaries: {error_str}")
            raise


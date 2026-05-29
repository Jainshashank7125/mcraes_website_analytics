from typing import List, Dict, Optional, Any
from sqlalchemy import text, Table, MetaData, select, update, insert, delete, and_, or_, func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.db.models import Brand, Prompt, Response
from app.services.db.base import BaseDB
import logging
import uuid
from urllib.parse import urlparse
from datetime import datetime, timedelta, date

logger = logging.getLogger(__name__)


class ClientDBMixin(BaseDB):
    """Client, shared query, brand utils, and dashboard link database methods"""

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

                # Resolve attached_link_ids to basic link info for public view toggling
                attached_ids = link_dict.get("attached_link_ids") or []
                attached_links = []
                for aid in attached_ids[:2]:
                    aq = select(table).where(table.c.id == aid).limit(1)
                    arow = self.db.execute(aq).first()
                    if arow:
                        arow_dict = dict(arow._mapping)
                        attached_links.append({
                            "id": arow_dict["id"],
                            "slug": arow_dict["slug"],
                            "name": arow_dict.get("name"),
                            "start_date": arow_dict["start_date"],
                            "end_date": arow_dict["end_date"],
                            "enabled": arow_dict["enabled"],
                            "expires_at": arow_dict.get("expires_at"),
                        })
                link_dict["attached_links"] = attached_links

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
        visible_highlights: Optional[List[str]] = None,
        selected_charts: Optional[List[str]] = None,
        selected_performance_metrics_kpis: Optional[List[str]] = None,
        show_change_period: Optional[Dict[str, bool]] = None,
        executive_summary: Optional[Dict] = None,
        global_filters: Optional[Dict[str, List[str]]] = None,
        attached_link_ids: Optional[List[int]] = None,
    ) -> Optional[Dict]:
        """Create a new dashboard link for a client (always creates new, allows multiple links for same date range)"""
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
            # Audit: created_by if column exists
            if "created_by" in table_columns and user_email:
                link_data["created_by"] = user_email
            # Attached links (up to 2 sibling link IDs for public view toggling)
            if "attached_link_ids" in table_columns and attached_link_ids is not None:
                link_data["attached_link_ids"] = attached_link_ids[:2]

            insert_stmt = pg_insert(table).values(
                **link_data,
                created_at=now
            ).returning(table)

            # Always create new link - don't update existing ones
            # This allows multiple links for the same date range with different configs
            # No on_conflict_do_update - always insert new record

            result = self.db.execute(insert_stmt)
            self.db.commit()

            row = result.fetchone()
            if row:
                link_dict = dict(row._mapping)
                link_id = link_dict.get("id")
                # Activity log: link created
                self._insert_dashboard_link_log(link_id, "created", user_email, None)
                # Save KPI selections if provided
                if link_id and (
                    selected_kpis is not None
                    or visible_sections is not None
                    or visible_highlights is not None
                    or selected_charts is not None
                    or selected_performance_metrics_kpis is not None
                    or show_change_period is not None
                    or global_filters is not None
                ):
                    kpi_selection = self.upsert_dashboard_link_kpi_selection(
                        link_id=link_id,
                        selected_kpis=selected_kpis or [],
                        visible_sections=visible_sections,
                        visible_highlights=visible_highlights,
                        selected_charts=selected_charts or [],
                        selected_performance_metrics_kpis=selected_performance_metrics_kpis
                        or [],
                        show_change_period=show_change_period,
                        global_filters=global_filters,
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
            visible_highlights = updates.pop("visible_highlights", None)
            selected_charts = updates.pop("selected_charts", None)
            selected_performance_metrics_kpis = updates.pop(
                "selected_performance_metrics_kpis", None
            )
            show_change_period = updates.pop("show_change_period", None)
            # Extract global_filters for KPI selections (stored on dashboard_link_kpi_selections)
            global_filters = updates.pop("global_filters", None)
            # Extract executive_summary but we'll add it back to update_data if column exists
            executive_summary = updates.pop("executive_summary", None)
            # Extract attached_link_ids (stored directly on dashboard_links)
            raw_attached_ids = updates.pop("attached_link_ids", None)
            attached_link_ids = raw_attached_ids[:2] if raw_attached_ids is not None else None

            # Only allow updating specific fields
            allowed_fields = ["start_date", "end_date", "enabled", "expires_at", "slug"]
            if has_name_column:
                allowed_fields.append("name")
            if has_description_column:
                allowed_fields.append("description")
            if has_executive_summary_column:
                allowed_fields.append("executive_summary")
            if "attached_link_ids" in table_columns:
                allowed_fields.append("attached_link_ids")

            update_data = {k: v for k, v in updates.items() if k in allowed_fields}

            # Add executive_summary back to update_data if it was provided and column exists
            if has_executive_summary_column and executive_summary is not None:
                update_data["executive_summary"] = executive_summary
                logger.info(f"Adding executive_summary to update_data for link {link_id}, type: {type(executive_summary)}")
            # Add attached_link_ids if provided and column exists
            if "attached_link_ids" in table_columns and attached_link_ids is not None:
                update_data["attached_link_ids"] = attached_link_ids

            # Audit: updated_by if column exists
            has_updated_by = "updated_by" in table_columns
            if has_updated_by and user_email:
                update_data["updated_by"] = user_email

            # Fetch current row before update for activity log (what changed)
            old_row = None
            if update_data:
                query_old = select(table).where(table.c.id == link_id).limit(1)
                old_result = self.db.execute(query_old)
                old_row = old_result.first()

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
                # Activity log: link updated (what changed)
                changes = self._build_link_changes(old_row, update_data) if old_row else None
                self._insert_dashboard_link_log(link_id, "updated", user_email, changes)
            else:
                # If no link fields to update, just fetch the link
                query = select(table).where(table.c.id == link_id).limit(1)
                result = self.db.execute(query)
                row = result.first()
                if not row:
                    return None

            link_dict = dict(row._mapping)

            # Update KPI selections if provided
            if (
                selected_kpis is not None
                or visible_sections is not None
                or visible_highlights is not None
                or selected_charts is not None
                or selected_performance_metrics_kpis is not None
                or show_change_period is not None
                or global_filters is not None
            ):
                kpi_selection = self.upsert_dashboard_link_kpi_selection(
                    link_id=link_id,
                    selected_kpis=selected_kpis if selected_kpis is not None else [],
                    visible_sections=visible_sections,
                    visible_highlights=visible_highlights,
                    selected_charts=selected_charts
                    if selected_charts is not None
                    else [],
                    selected_performance_metrics_kpis=selected_performance_metrics_kpis
                    if selected_performance_metrics_kpis is not None
                    else [],
                    show_change_period=show_change_period,
                    global_filters=global_filters,
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

    def _build_link_changes(self, old_row: Any, update_data: Dict) -> Optional[List[Dict]]:
        """Build human-readable list of {field, old_value, new_value} for activity log."""
        if not old_row or not update_data:
            return None
        changes = []
        skip_keys = {"updated_at", "updated_by"}
        old = dict(old_row._mapping) if hasattr(old_row, "_mapping") else {}
        for field, new_val in update_data.items():
            if field in skip_keys:
                continue
            old_val = old.get(field)
            if old_val == new_val:
                continue
            # Serialize for display (dates, bools, etc.)
            def _fmt(v):
                if v is None:
                    return None
                if hasattr(v, "isoformat"):
                    return v.isoformat()
                if isinstance(v, (dict, list)):
                    return str(v)[:200]
                return str(v)
            changes.append({
                "field": field,
                "old_value": _fmt(old_val),
                "new_value": _fmt(new_val),
            })
        return changes if changes else None

    def _insert_dashboard_link_log(
        self,
        link_id: int,
        action: str,
        created_by: Optional[str],
        changes: Optional[List[Dict]],
    ) -> None:
        """Insert one row into dashboard_link_logs (created or updated)."""
        try:
            log_table = self._get_table("dashboard_link_logs")
            self.db.execute(
                log_table.insert().values(
                    dashboard_link_id=link_id,
                    action=action,
                    created_by=created_by,
                    changes=changes,
                )
            )
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(
                f"Could not insert dashboard link log for link_id={link_id}: {e}. "
                "Ensure migration 002_dashboard_link_logs is applied (dashboard_link_logs table exists)."
            )

    def list_dashboard_link_logs(self, link_id: int) -> List[Dict]:
        """List activity logs for a dashboard link (created_at, created_by, action, changes)."""
        try:
            log_table = self._get_table("dashboard_link_logs")
            query = (
                select(log_table)
                .where(log_table.c.dashboard_link_id == link_id)
                .order_by(log_table.c.created_at.desc())
            )
            result = self.db.execute(query)
            rows = result.fetchall()
            out = []
            for r in rows:
                d = dict(r._mapping)
                if d.get("created_at") and hasattr(d["created_at"], "isoformat"):
                    d["created_at"] = d["created_at"].isoformat()
                out.append(d)
            return out
        except Exception as e:
            logger.error(f"Error listing dashboard link logs for link_id={link_id}: {e}")
            return []

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
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                }
                # Include selected_performance_metrics_kpis if the column exists
                if hasattr(row, "selected_performance_metrics_kpis"):
                    result_dict["selected_performance_metrics_kpis"] = (
                        row.selected_performance_metrics_kpis or []
                    )
                # Include visible_highlights if the column exists
                # CRITICAL: Use getattr with default None, then check if it's in the row mapping
                try:
                    # Try to get from row attribute first
                    visible_highlights_value = getattr(row, "visible_highlights", None)
                    # If that doesn't work, try from mapping
                    if visible_highlights_value is None and hasattr(row, "_mapping"):
                        visible_highlights_value = row._mapping.get("visible_highlights")

                    if visible_highlights_value is not None:
                        # Convert to list if it's a tuple or other iterable
                        if isinstance(visible_highlights_value, (list, tuple)):
                            result_dict["visible_highlights"] = list(
                                visible_highlights_value
                            )
                        else:
                            result_dict["visible_highlights"] = (
                                [visible_highlights_value]
                                if visible_highlights_value
                                else []
                            )
                        logger.info(
                            f"✅ Loaded visible_highlights for link {link_id}: {result_dict.get('visible_highlights')} (type: {type(result_dict.get('visible_highlights'))})"
                        )
                    else:
                        result_dict["visible_highlights"] = []
                        logger.warning(
                            f"⚠️ visible_highlights is None for link {link_id}, setting to empty array"
                        )
                except AttributeError:
                    # Column doesn't exist or can't be accessed
                    logger.warning(
                        f"Could not access visible_highlights column for link {link_id}"
                    )
                    result_dict["visible_highlights"] = []

                # Include global_filters if the column exists
                try:
                    global_filters_value = getattr(row, "global_filters", None)
                    if global_filters_value is None and hasattr(row, "_mapping"):
                        global_filters_value = row._mapping.get("global_filters")

                    # Store as dict; backend expects JSONB → Python dict
                    if isinstance(global_filters_value, dict):
                        result_dict["global_filters"] = global_filters_value
                    elif global_filters_value is not None:
                        # Fallback: log and still attach whatever structure we got
                        result_dict["global_filters"] = global_filters_value
                        logger.info(
                            f"Loaded global_filters for link {link_id}: type={type(global_filters_value)}"
                        )
                    else:
                        result_dict["global_filters"] = {}
                except AttributeError:
                    logger.warning(
                        f"Could not access global_filters column for link {link_id}"
                    )
                    result_dict["global_filters"] = {}

                # Include show_change_period if the column exists
                if hasattr(row, "show_change_period") and row.show_change_period:
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
        visible_highlights: Optional[List[str]] = None,
        selected_charts: Optional[List[str]] = None,
        selected_performance_metrics_kpis: Optional[List[str]] = None,
        show_change_period: Optional[Dict[str, bool]] = None,
        global_filters: Optional[Dict[str, List[str]]] = None,
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

            # Check which columns exist in the table
            table_columns = [col.name for col in table.c]

            # Only add visible_highlights if column exists
            # CRITICAL: Empty array [] is valid and should be saved (means no highlights selected)
            # Only skip if it's explicitly None (not provided in update)
            if "visible_highlights" in table_columns:
                if visible_highlights is not None:
                    # Ensure it's a list (not tuple or other iterable)
                    if not isinstance(visible_highlights, list):
                        visible_highlights = (
                            list(visible_highlights) if visible_highlights else []
                        )
                    kpi_data["visible_highlights"] = visible_highlights
                    logger.info(
                        f"✅ Saving visible_highlights for link {link_id}: {visible_highlights} (type: {type(visible_highlights)}, len: {len(visible_highlights)})"
                    )
                else:
                    # If None, don't include it (will keep existing value on update, or be NULL on insert)
                    logger.warning(
                        f"⚠️ visible_highlights is None for link {link_id}, skipping (will keep existing value or be NULL)"
                    )

            # Only add show_change_period if column exists
            if "show_change_period" in table_columns:
                kpi_data["show_change_period"] = show_change_period

            # Only add global_filters if column exists
            if "global_filters" in table_columns and global_filters is not None:
                kpi_data["global_filters"] = global_filters

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

            # Only update visible_highlights if column exists AND it was provided (not None)
            # CRITICAL: Empty array [] is valid (means no highlights), None means don't update
            if "visible_highlights" in table_columns and visible_highlights is not None:
                update_set["visible_highlights"] = insert_stmt.excluded.visible_highlights

            # Only update show_change_period if column exists
            if "show_change_period" in table_columns:
                update_set["show_change_period"] = insert_stmt.excluded.show_change_period

            # Only update global_filters if column exists AND it was provided
            if "global_filters" in table_columns and global_filters is not None:
                update_set["global_filters"] = insert_stmt.excluded.global_filters

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
                # Include global_filters if the column exists
                if hasattr(row, 'global_filters') and row.global_filters:
                    result_dict["global_filters"] = row.global_filters
                elif hasattr(row, '_mapping') and row._mapping.get('global_filters'):
                    result_dict["global_filters"] = row._mapping.get('global_filters')
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

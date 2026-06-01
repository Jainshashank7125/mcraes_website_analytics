from typing import List, Dict, Optional, Any
from sqlalchemy import select, update, insert, delete, and_
from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.services.db.base import BaseDB
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AgencyAnalyticsDBMixin(BaseDB):
    """Agency Analytics database methods"""

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

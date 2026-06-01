from typing import List, Dict, Optional, Any
from sqlalchemy import text, select, update, insert, delete, and_, func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.services.db.base import BaseDB
from datetime import datetime, timedelta, date
import logging

logger = logging.getLogger(__name__)


class GA4DBMixin(BaseDB):
    """GA4 database methods"""

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
                    # Query by property_id only (no client_id filter)
                    query = text("""
                        SELECT * FROM ga4_traffic_overview
                        WHERE property_id = :property_id
                          AND date >= CAST(:start_date AS DATE)
                          AND date <= CAST(:end_date AS DATE)
                        ORDER BY date ASC
                    """)
                    result = self.db.execute(query, {
                        "property_id": property_id,
                        "start_date": start_date,
                        "end_date": end_date
                    })
                    records = [dict(row._mapping) for row in result]
                else:
                    # Query by client_id first
                    query = text("""
                        SELECT * FROM ga4_traffic_overview
                        WHERE client_id = :client_id
                          AND property_id = :property_id
                          AND date >= CAST(:start_date AS DATE)
                          AND date <= CAST(:end_date AS DATE)
                        ORDER BY date ASC
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
                    if not records:
                        logger.info(f"No GA4 traffic overview data found for client_id={client_id}, falling back to property_id={property_id} query")
                        query = text("""
                            SELECT * FROM ga4_traffic_overview
                            WHERE property_id = :property_id
                              AND date >= CAST(:start_date AS DATE)
                              AND date <= CAST(:end_date AS DATE)
                            ORDER BY date ASC
                        """)
                        result = self.db.execute(query, {
                            "property_id": property_id,
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
        """Upsert GA4 traffic overview data - now uses client_id (with brand_id for backward compatibility)

        Uses delete-then-insert approach to handle the case where client_id is the primary identifier
        but the unique constraint is on (brand_id, property_id, date). This prevents duplicate records
        when brand_id is NULL.
        """
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

            # Delete existing record first to prevent duplicates
            # This handles the case where brand_id might be NULL (NULL != NULL in SQL)
            if client_id is not None:
                delete_query = text("""
                    DELETE FROM ga4_traffic_overview
                    WHERE client_id = :client_id AND property_id = :property_id AND date = :date
                """)
                self.db.execute(delete_query, {
                    "client_id": client_id,
                    "property_id": property_id,
                    "date": date
                })
            elif brand_id is not None:
                delete_query = text("""
                    DELETE FROM ga4_traffic_overview
                    WHERE brand_id = :brand_id AND property_id = :property_id AND date = :date
                """)
                self.db.execute(delete_query, {
                    "brand_id": brand_id,
                    "property_id": property_id,
                    "date": date
                })

            # Insert the new record
            insert_query = text("""
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
            """)

            self.db.execute(insert_query, {
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
            # Log new_users value being stored for debugging
            new_users_stored = data.get("newUsers", 0)
            if new_users_stored > 0:
                logger.debug(f"Upserted GA4 traffic overview with new_users={new_users_stored} for {entity_type} {entity_id}, property {property_id}, date {date}")
            else:
                logger.info(f"Upserted GA4 traffic overview for {entity_type} {entity_id}, property {property_id}, date {date} (new_users={new_users_stored})")
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
                "property_id":   property_id,
                "date":          date,
                "source":        source.get("source", ""),
                "sessions":      source.get("sessions", 0),
                "users":         source.get("users", 0),
                "bounce_rate":   source.get("bounceRate", 0),
                # conversions & conversion_rate were fetched but previously discarded
                "conversions":   source.get("conversions", 0),
                "conversion_rate": source.get("conversionRate", 0),
                "updated_at":    datetime.now()
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
                        'sessions':        insert_stmt.excluded.sessions,
                        'users':           insert_stmt.excluded.users,
                        'bounce_rate':     insert_stmt.excluded.bounce_rate,
                        'conversions':     insert_stmt.excluded.conversions,
                        'conversion_rate': insert_stmt.excluded.conversion_rate,
                        'updated_at':      insert_stmt.excluded.updated_at
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
        """Upsert GA4 geographic data using SQLAlchemy Core (local PostgreSQL)

        Supports both:
        1. Single date: geographic data all has same date (legacy mode)
        2. Multi-date: geographic data includes 'date' field in each record (new mode)
        """
        if client_id is None and brand_id is None:
            raise ValueError("Either client_id or brand_id must be provided")
        if not geographic:
            return 0

        entity_id = client_id if client_id is not None else brand_id
        entity_type = "client" if client_id is not None else "brand"

        # Check if data includes date field (multi-date mode)
        has_date_field = any(geo.get("date") for geo in geographic)

        if has_date_field:
            # Multi-date mode: Extract unique dates and delete all of them
            unique_dates = set(geo.get("date") for geo in geographic if geo.get("date"))
            try:
                table = self._get_table("ga4_geographic")

                # Delete existing records for ALL dates in this batch
                for date_to_delete in unique_dates:
                    delete_conditions = [
                        table.c.property_id == property_id,
                        table.c.date == date_to_delete
                    ]
                    if client_id is not None:
                        delete_conditions.append(table.c.client_id == client_id)
                    if brand_id is not None:
                        delete_conditions.append(table.c.brand_id == brand_id)

                    delete_stmt = delete(table).where(and_(*delete_conditions))
                    self.db.execute(delete_stmt)
                self.db.commit()
                logger.info(f"Deleted existing geographic data for {len(unique_dates)} dates")
            except Exception as delete_error:
                self.db.rollback()
                logger.warning(f"Error deleting existing geographic data (may not exist): {str(delete_error)}")
        else:
            # Single date mode (legacy): Use provided date parameter
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
            # Use date from record if available, otherwise use parameter
            record_date = geo.get("date", date)
            record = {
                "property_id":    property_id,
                "date":           record_date,
                "country":        geo.get("country", ""),
                "users":          geo.get("users", 0),
                "sessions":       geo.get("sessions", 0),
                # engagementRate was fetched but previously discarded
                "engagement_rate": geo.get("engagementRate", 0),
                "updated_at":     datetime.now()
            }
            if client_id is not None:
                record["client_id"] = client_id
            if brand_id is not None:
                record["brand_id"] = brand_id
            records.append(record)

        try:
            # Bulk insert using ON CONFLICT - process in batches
            # Use appropriate unique constraint based on entity type
            if client_id is not None:
                # For clients, use client_id in the unique constraint
                conflict_columns = ['client_id', 'property_id', 'date', 'country']
            else:
                # For brands, use brand_id in the unique constraint
                conflict_columns = ['brand_id', 'property_id', 'date', 'country']

            batch_size = 500
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                insert_stmt = pg_insert(table).values(batch)
                insert_stmt = insert_stmt.on_conflict_do_update(
                    index_elements=conflict_columns,
                    set_={
                        'users':           insert_stmt.excluded.users,
                        'sessions':        insert_stmt.excluded.sessions,
                        'engagement_rate': insert_stmt.excluded.engagement_rate,
                        'updated_at':      insert_stmt.excluded.updated_at
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

                # Check if the snapshot's period matches the requested period (within 2 days tolerance)
                start_diff = abs((snapshot_start - requested_start).days)
                end_diff = abs((snapshot_end - requested_end).days)

                if start_diff <= 2 and end_diff <= 2:
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
                query = select(table).where(
                    and_(
                        table.c.client_id == client_id,
                        table.c.property_id == property_id,
                        table.c.date >= start_date,
                        table.c.date <= end_date
                    )
                )
                result = self.db.execute(query)
                records = [dict(row._mapping) for row in result]

                # If no records found for this specific client_id, fall back to property_id only
                if not records:
                    logger.info(f"No GA4 top pages data found for client_id={client_id}, falling back to property_id={property_id} query")
                    query = select(table).where(
                        and_(
                            table.c.property_id == property_id,
                            table.c.date >= start_date,
                            table.c.date <= end_date
                        )
                    )
                    result = self.db.execute(query)
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
                query = select(table).where(
                    and_(
                        table.c.client_id == client_id,
                        table.c.property_id == property_id,
                        table.c.date >= start_date,
                        table.c.date <= end_date
                    )
                )
                result = self.db.execute(query)
                records = [dict(row._mapping) for row in result]

                # If no records found for this specific client_id, fall back to property_id only
                if not records:
                    logger.info(f"No GA4 traffic sources data found for client_id={client_id}, falling back to property_id={property_id} query")
                    query = select(table).where(
                        and_(
                            table.c.property_id == property_id,
                            table.c.date >= start_date,
                            table.c.date <= end_date
                        )
                    )
                    result = self.db.execute(query)
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
                query = select(table).where(
                    and_(
                        table.c.client_id == client_id,
                        table.c.property_id == property_id,
                        table.c.date >= start_date,
                        table.c.date <= end_date
                    )
                )
                result = self.db.execute(query)
                records = [dict(row._mapping) for row in result]

                # If no records found for this specific client_id, fall back to property_id only
                if not records:
                    logger.info(f"No GA4 geographic data found for client_id={client_id}, falling back to property_id={property_id} query")
                    query = select(table).where(
                        and_(
                            table.c.property_id == property_id,
                            table.c.date >= start_date,
                            table.c.date <= end_date
                        )
                    )
                    result = self.db.execute(query)
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

            # Aggregate by country; compute weighted-average engagementRate
            country_aggregates = {}
            for record in records:
                country = record.get("country")
                if not country:
                    continue

                if country not in country_aggregates:
                    country_aggregates[country] = {
                        "country":                country,
                        "users":                  0,
                        "sessions":               0,
                        "engagementRate":         0.0,
                        # internal accumulators (removed from output below)
                        "_total_engagement_weight": 0.0,
                        "_total_sessions":          0,
                    }

                sessions_val       = int(record.get("sessions", 0) or 0)
                engagement_rate_val = float(record.get("engagement_rate", 0) or 0)

                country_aggregates[country]["users"]    += int(record.get("users", 0) or 0)
                country_aggregates[country]["sessions"] += sessions_val
                country_aggregates[country]["_total_engagement_weight"] += engagement_rate_val * sessions_val
                country_aggregates[country]["_total_sessions"]          += sessions_val

            # Finalise: compute weighted engagementRate, strip internal keys
            countries = []
            for country, data in country_aggregates.items():
                total_sessions = data.pop("_total_sessions", 0)
                total_weight   = data.pop("_total_engagement_weight", 0.0)
                data["engagementRate"] = (total_weight / total_sessions) if total_sessions > 0 else 0.0
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
                query = select(table).where(
                    and_(
                        table.c.client_id == client_id,
                        table.c.property_id == property_id,
                        table.c.date >= start_date,
                        table.c.date <= end_date
                    )
                )
                result = self.db.execute(query)
                records = [dict(row._mapping) for row in result]

                # If no records found for this specific client_id, fall back to property_id only
                if not records:
                    logger.info(f"No GA4 devices data found for client_id={client_id}, falling back to property_id={property_id} query")
                    query = select(table).where(
                        and_(
                            table.c.property_id == property_id,
                            table.c.date >= start_date,
                            table.c.date <= end_date
                        )
                    )
                    result = self.db.execute(query)
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

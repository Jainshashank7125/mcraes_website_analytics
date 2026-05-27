"""
Background sync for Google Analytics 4 (GA4)
"""
import logging
from typing import Optional
from datetime import datetime, timedelta
from app.services.ga4_client import GA4APIClient
from app.services.supabase_service import SupabaseService
from app.services.sync_job_service import SyncJobService
from app.services.audit_logger import audit_logger
from app.db.models import AuditLogAction
from app.db.database import SessionLocal

logger = logging.getLogger(__name__)


async def sync_ga4_background(
    job_id: str,
    user_id: str,
    user_email: str,
    sync_mode: str = "complete",
    client_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    sync_realtime: bool = True,
    request = None
):
    """Background task to sync GA4 data - now iterates over Clients instead of Brands"""
    # Create database session for background task
    db = SessionLocal()
    sync_job_service = SyncJobService(db=db)
    ga4_client = GA4APIClient()
    supabase = SupabaseService(db=db)

    try:
        # Get date range
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        await sync_job_service.update_job_status(
            job_id, "running", progress=0,
            current_step="Fetching clients with GA4...", total_steps=1
        )

        # Get clients with GA4 configured from local PostgreSQL database
        from app.db.models import Client, GA4TrafficOverview
        from sqlalchemy import and_, distinct

        if client_id:
            # Get specific client
            client_obj = db.query(Client).filter(Client.id == client_id).first()
            clients = [client_obj] if client_obj else []
        else:
            # Get all clients with GA4 property ID configured (not null and not empty)
            all_clients = db.query(Client).filter(
                and_(
                    Client.ga4_property_id.isnot(None),
                    Client.ga4_property_id != ''
                )
            ).all()

            # For "new" mode, filter to only clients without existing GA4 data
            if sync_mode == "new":
                # Get client IDs that already have GA4 data
                existing_client_ids = set(
                    db.query(distinct(GA4TrafficOverview.client_id))
                    .filter(GA4TrafficOverview.client_id.isnot(None))
                    .all()
                )
                existing_client_ids = {row[0] for row in existing_client_ids}
                clients = [c for c in all_clients if c.id not in existing_client_ids]
                logger.info(f"[Job {job_id}] New mode: Filtered to {len(clients)} clients without GA4 data (out of {len(all_clients)} total)")
            else:
                clients = all_clients

        # Convert ORM objects to dicts for compatibility
        clients = [
            {
                "id": c.id,
                "company_name": c.company_name,
                "ga4_property_id": c.ga4_property_id,
                "scrunch_brand_id": c.scrunch_brand_id
            }
            for c in clients if c
        ]

        if not clients:
            # Check for cancellation before completing
            if sync_job_service.is_cancelled(job_id):
                logger.info(f"[Job {job_id}] Job was cancelled")
                return
            result = {
                "status": "success",
                "message": "No clients with GA4 configured found",
                "total_synced": {},
                "client_results": []
            }
            await sync_job_service.complete_job(job_id, result)
            return

        total_synced = {
            "clients": 0,
            "traffic_overview": 0,
            "top_pages": 0,
            "traffic_sources": 0,
            "geographic": 0,
            "devices": 0,
            "conversions": 0,
            "realtime": 0
        }

        client_results = []
        total_clients = len(clients)

        # Group clients by property_id to avoid duplicate API calls
        # and ensure data is stored for all clients sharing the same property
        property_to_clients = {}
        for client in clients:
            property_id = client.get("ga4_property_id")
            if property_id:
                if property_id not in property_to_clients:
                    property_to_clients[property_id] = []
                property_to_clients[property_id].append(client)

        # Process each unique property_id
        processed_properties = set()
        property_index = 0
        total_properties = len(property_to_clients)

        for property_id, clients_with_property in property_to_clients.items():
            # Check for cancellation before each property
            if sync_job_service.is_cancelled(job_id):
                logger.info(f"[Job {job_id}] Job cancelled during GA4 sync")
                return

            # Skip if we've already processed this property (avoid duplicate API calls)
            if property_id in processed_properties:
                continue
            processed_properties.add(property_id)

            # Use the first client as the primary one for API calls and logging
            primary_client = clients_with_property[0]
            client_id_val = primary_client.get("id")
            client_name = primary_client.get("company_name", f"Client {client_id_val}")
            scrunch_brand_id = primary_client.get("scrunch_brand_id")

            property_index += 1
            logger.info(f"[Job {job_id}] Processing property {property_id} for {len(clients_with_property)} client(s): {[c.get('company_name') for c in clients_with_property]}")

            try:
                progress = int((property_index / total_properties) * 80)
                await sync_job_service.update_job_status(
                    job_id, "running", progress=progress,
                    current_step=f"Syncing GA4 property {property_id} for {len(clients_with_property)} client(s) ({property_index}/{total_properties})..."
                )

                # Check for cancellation after status update
                if sync_job_service.is_cancelled(job_id):
                    logger.info(f"[Job {job_id}] Job cancelled before syncing client {client_name}")
                    return

                # Calculate date ranges using actual start_date and end_date
                # Current period: use the provided start_date and end_date
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                period_start_date = start_date
                period_end_date = end_date

                # Calculate period duration
                period_duration = (end_dt - start_dt).days + 1

                # Previous period: same duration, ending the day before current period starts
                prev_period_end_dt = start_dt - timedelta(days=1)
                prev_period_start_dt = start_dt - timedelta(days=period_duration)
                prev_period_start_date = prev_period_start_dt.strftime("%Y-%m-%d")
                prev_period_end_date = prev_period_end_dt.strftime("%Y-%m-%d")

                logger.info(f"[Job {job_id}] Calculating KPIs for client {client_id_val} ({client_name})")
                logger.info(f"[Job {job_id}] Current period: {period_start_date} to {period_end_date}")
                logger.info(f"[Job {job_id}] Previous period: {prev_period_start_date} to {prev_period_end_date}")

                # Fetch current period data
                await sync_job_service.update_job_status(
                    job_id, "running", progress=progress + 5,
                    current_step=f"Fetching current period data for {client_name}..."
                )

                current_traffic_overview = await ga4_client.get_traffic_overview(property_id, period_start_date, period_end_date)

                # Check for cancellation after API call
                if sync_job_service.is_cancelled(job_id):
                    logger.info(f"[Job {job_id}] Job cancelled after fetching traffic overview for {client_name}")
                    return

                # Get conversions and revenue for current period
                current_conversions = 0
                current_revenue = 0
                try:
                    from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Metric
                    client = ga4_client._get_data_client()

                    # Get conversions
                    conversions_request = RunReportRequest(
                        property=f"properties/{property_id}",
                        date_ranges=[DateRange(start_date=period_start_date, end_date=period_end_date)],
                        metrics=[Metric(name="conversions")],
                    )
                    conversions_response = client.run_report(conversions_request)
                    if conversions_response.rows:
                        current_conversions = float(conversions_response.rows[0].metric_values[0].value)

                    # Get revenue
                    revenue_request = RunReportRequest(
                        property=f"properties/{property_id}",
                        date_ranges=[DateRange(start_date=period_start_date, end_date=period_end_date)],
                        metrics=[Metric(name="totalRevenue")],
                    )
                    revenue_response = client.run_report(revenue_request)
                    if revenue_response.rows:
                        current_revenue = float(revenue_response.rows[0].metric_values[0].value)
                except Exception as e:
                    logger.warning(f"Could not fetch conversions/revenue for current period: {str(e)}")

                # Check for cancellation before fetching previous period
                if sync_job_service.is_cancelled(job_id):
                    logger.info(f"[Job {job_id}] Job cancelled after fetching current period data for {client_name}")
                    return

                # Fetch previous period data
                await sync_job_service.update_job_status(
                    job_id, "running", progress=progress + 10,
                    current_step=f"Fetching previous period data for {client_name}..."
                )

                prev_traffic_overview = await ga4_client.get_traffic_overview(property_id, prev_period_start_date, prev_period_end_date)

                # Check for cancellation after API call
                if sync_job_service.is_cancelled(job_id):
                    logger.info(f"[Job {job_id}] Job cancelled after fetching previous period traffic overview for {client_name}")
                    return

                # Get conversions and revenue for previous period
                prev_conversions = 0
                prev_revenue = 0
                try:
                    from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Metric
                    client = ga4_client._get_data_client()

                    # Get previous period conversions
                    prev_conversions_request = RunReportRequest(
                        property=f"properties/{property_id}",
                        date_ranges=[DateRange(start_date=prev_period_start_date, end_date=prev_period_end_date)],
                        metrics=[Metric(name="conversions")],
                    )
                    prev_conversions_response = client.run_report(prev_conversions_request)
                    if prev_conversions_response.rows:
                        prev_conversions = float(prev_conversions_response.rows[0].metric_values[0].value)

                    # Get previous period revenue
                    prev_revenue_request = RunReportRequest(
                        property=f"properties/{property_id}",
                        date_ranges=[DateRange(start_date=prev_period_start_date, end_date=prev_period_end_date)],
                        metrics=[Metric(name="totalRevenue")],
                    )
                    prev_revenue_response = client.run_report(prev_revenue_request)
                    if prev_revenue_response.rows:
                        prev_revenue = float(prev_revenue_response.rows[0].metric_values[0].value)
                except Exception as e:
                    logger.warning(f"Could not fetch conversions/revenue for previous period: {str(e)}")

                # Prepare current period values
                current_values = {
                    "users": current_traffic_overview.get("users", 0) if current_traffic_overview else 0,
                    "sessions": current_traffic_overview.get("sessions", 0) if current_traffic_overview else 0,
                    "new_users": current_traffic_overview.get("newUsers", 0) if current_traffic_overview else 0,
                    "bounce_rate": current_traffic_overview.get("bounceRate", 0) if current_traffic_overview else 0,
                    "avg_session_duration": current_traffic_overview.get("averageSessionDuration", 0) if current_traffic_overview else 0,
                    "engagement_rate": current_traffic_overview.get("engagementRate", 0) if current_traffic_overview else 0,
                    "engaged_sessions": current_traffic_overview.get("engagedSessions", 0) if current_traffic_overview else 0,
                    "conversions": current_conversions,
                    "revenue": current_revenue,
                }

                # Prepare previous period values
                previous_values = {
                    "users": prev_traffic_overview.get("users", 0) if prev_traffic_overview else 0,
                    "sessions": prev_traffic_overview.get("sessions", 0) if prev_traffic_overview else 0,
                    "new_users": prev_traffic_overview.get("newUsers", 0) if prev_traffic_overview else 0,
                    "bounce_rate": prev_traffic_overview.get("bounceRate", 0) if prev_traffic_overview else 0,
                    "avg_session_duration": prev_traffic_overview.get("averageSessionDuration", 0) if prev_traffic_overview else 0,
                    "engagement_rate": prev_traffic_overview.get("engagementRate", 0) if prev_traffic_overview else 0,
                    "engaged_sessions": prev_traffic_overview.get("engagedSessions", 0) if prev_traffic_overview else 0,
                    "conversions": prev_conversions,
                    "revenue": prev_revenue,
                }

                # Calculate percentage changes
                def calculate_change(current, previous):
                    if previous > 0:
                        return ((current - previous) / previous) * 100
                    return 0

                changes = {
                    "users_change": calculate_change(current_values["users"], previous_values["users"]),
                    "sessions_change": calculate_change(current_values["sessions"], previous_values["sessions"]),
                    "new_users_change": calculate_change(current_values["new_users"], previous_values["new_users"]),
                    "bounce_rate_change": calculate_change(current_values["bounce_rate"], previous_values["bounce_rate"]) if previous_values["bounce_rate"] > 0 else 0,
                    "avg_session_duration_change": calculate_change(current_values["avg_session_duration"], previous_values["avg_session_duration"]) if previous_values["avg_session_duration"] > 0 else 0,
                    "engagement_rate_change": calculate_change(current_values["engagement_rate"], previous_values["engagement_rate"]) if previous_values["engagement_rate"] > 0 else 0,
                    "engaged_sessions_change": calculate_change(current_values["engaged_sessions"], previous_values["engaged_sessions"]),
                    "conversions_change": calculate_change(current_values["conversions"], previous_values["conversions"]) if previous_values["conversions"] > 0 else 0,
                    "revenue_change": calculate_change(current_values["revenue"], previous_values["revenue"]) if previous_values["revenue"] > 0 else 0,
                }

                # Store KPI snapshot
                await sync_job_service.update_job_status(
                    job_id, "running", progress=progress + 15,
                    current_step=f"Storing KPI snapshot for {client_name}..."
                )

                # Store KPI snapshot for all clients sharing this property_id
                for client in clients_with_property:
                    client_id_for_storage = client.get("id")
                    brand_id_for_storage = client.get("scrunch_brand_id")
                    supabase.upsert_ga4_kpi_snapshot(
                        property_id=property_id,
                        period_end_date=period_end_date,
                        period_start_date=period_start_date,
                        prev_period_start_date=prev_period_start_date,
                        prev_period_end_date=prev_period_end_date,
                        current_values=current_values,
                        previous_values=previous_values,
                        changes=changes,
                        client_id=client_id_for_storage,
                        brand_id=brand_id_for_storage  # For backward compatibility
                    )

                # Store all GA4 data types for the current period
                await sync_job_service.update_job_status(
                    job_id, "running", progress=progress + 20,
                    current_step=f"Storing all GA4 data for {client_name}..."
                )

                # Store daily traffic overview records (one per day for the entire 30-day period)
                if current_traffic_overview and current_traffic_overview.get("daily_data"):
                    daily_records = current_traffic_overview.get("daily_data", [])
                    logger.info(f"[Job {job_id}] Storing {len(daily_records)} daily traffic overview records for {client_name}")

                    # Get daily conversions and revenue if available
                    daily_conversions_data = {}
                    daily_revenue_data = {}

                    # Try to get daily breakdown of conversions and revenue
                    try:
                        from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Metric, Dimension
                        client = ga4_client._get_data_client()

                        # Get daily conversions
                        daily_conversions_request = RunReportRequest(
                            property=f"properties/{property_id}",
                            date_ranges=[DateRange(start_date=period_start_date, end_date=period_end_date)],
                            dimensions=[Dimension(name="date")],
                            metrics=[Metric(name="conversions")],
                        )
                        daily_conversions_response = client.run_report(daily_conversions_request)
                        if daily_conversions_response.rows:
                            for row in daily_conversions_response.rows:
                                date_str = row.dimension_values[0].value
                                conversions_value = float(row.metric_values[0].value)
                                daily_conversions_data[date_str] = conversions_value

                        # Get daily revenue
                        daily_revenue_request = RunReportRequest(
                            property=f"properties/{property_id}",
                            date_ranges=[DateRange(start_date=period_start_date, end_date=period_end_date)],
                            dimensions=[Dimension(name="date")],
                            metrics=[Metric(name="totalRevenue")],
                        )
                        daily_revenue_response = client.run_report(daily_revenue_request)
                        if daily_revenue_response.rows:
                            for row in daily_revenue_response.rows:
                                date_str = row.dimension_values[0].value
                                revenue_value = float(row.metric_values[0].value)
                                daily_revenue_data[date_str] = revenue_value
                    except Exception as e:
                        logger.warning(f"Could not fetch daily conversions/revenue breakdown: {str(e)}")

                    # Store each daily record for ALL clients sharing this property_id
                    first_record_logged = False
                    for daily_record in daily_records:
                        date_str = daily_record.get("date")
                        if date_str:
                            # Add conversions and revenue for this day
                            daily_record_with_extras = daily_record.copy()
                            daily_record_with_extras["conversions"] = daily_conversions_data.get(date_str, 0)
                            daily_record_with_extras["revenue"] = daily_revenue_data.get(date_str, 0)

                            # Log first record to verify newUsers is present
                            if not first_record_logged:
                                logger.info(f"[Job {job_id}] Sample daily record: date={date_str}, users={daily_record_with_extras.get('users')}, sessions={daily_record_with_extras.get('sessions')}, newUsers={daily_record_with_extras.get('newUsers')}")
                                first_record_logged = True

                            # Store for all clients sharing this property_id
                            for client in clients_with_property:
                                client_id_for_storage = client.get("id")
                                brand_id_for_storage = client.get("scrunch_brand_id")
                                supabase.upsert_ga4_traffic_overview(property_id, date_str, daily_record_with_extras, client_id=client_id_for_storage, brand_id=brand_id_for_storage)
                                total_synced["traffic_overview"] += 1

                    logger.info(f"[Job {job_id}] Stored {len(daily_records)} daily traffic overview records for {len(clients_with_property)} client(s) with property {property_id}")
                elif current_traffic_overview:
                    # Fallback: Store aggregated record if daily data not available
                    traffic_overview_with_extras = current_traffic_overview.copy()
                    traffic_overview_with_extras["conversions"] = current_conversions
                    traffic_overview_with_extras["revenue"] = current_revenue

                    # Store for all clients sharing this property_id
                    for client in clients_with_property:
                        client_id_for_storage = client.get("id")
                        brand_id_for_storage = client.get("scrunch_brand_id")
                        supabase.upsert_ga4_traffic_overview(property_id, period_end_date, traffic_overview_with_extras, client_id=client_id_for_storage, brand_id=brand_id_for_storage)
                        total_synced["traffic_overview"] += 1

                # Store revenue separately for historical tracking (for all clients)
                if current_revenue > 0:
                    for client in clients_with_property:
                        client_id_for_storage = client.get("id")
                        brand_id_for_storage = client.get("scrunch_brand_id")
                        supabase.upsert_ga4_revenue(property_id, period_end_date, current_revenue, client_id=client_id_for_storage, brand_id=brand_id_for_storage)

                # Store daily conversions summary (for all clients)
                if current_conversions > 0:
                    for client in clients_with_property:
                        client_id_for_storage = client.get("id")
                        brand_id_for_storage = client.get("scrunch_brand_id")
                        supabase.upsert_ga4_daily_conversions(property_id, period_end_date, current_conversions, client_id=client_id_for_storage, brand_id=brand_id_for_storage)

                # Fetch and store additional GA4 data
                try:
                    # Top pages
                    if sync_job_service.is_cancelled(job_id):
                        logger.info(f"[Job {job_id}] Job cancelled before fetching top pages for {client_name}")
                        return
                    top_pages = await ga4_client.get_top_pages(property_id, period_start_date, period_end_date, limit=50)
                    if sync_job_service.is_cancelled(job_id):
                        logger.info(f"[Job {job_id}] Job cancelled after fetching top pages for {client_name}")
                        return
                    if top_pages:
                        # Store for all clients sharing this property_id
                        total_count = 0
                        for client in clients_with_property:
                            client_id_for_storage = client.get("id")
                            brand_id_for_storage = client.get("scrunch_brand_id")
                            count = supabase.upsert_ga4_top_pages(property_id, period_end_date, top_pages, client_id=client_id_for_storage, brand_id=brand_id_for_storage)
                            total_count += count
                        total_synced["top_pages"] += total_count

                    # Traffic sources
                    if sync_job_service.is_cancelled(job_id):
                        logger.info(f"[Job {job_id}] Job cancelled before fetching traffic sources for property {property_id}")
                        return
                    traffic_sources = await ga4_client.get_traffic_sources(property_id, period_start_date, period_end_date)
                    if sync_job_service.is_cancelled(job_id):
                        logger.info(f"[Job {job_id}] Job cancelled after fetching traffic sources for property {property_id}")
                        return
                    if traffic_sources:
                        # Store for all clients sharing this property_id
                        total_count = 0
                        for client in clients_with_property:
                            client_id_for_storage = client.get("id")
                            brand_id_for_storage = client.get("scrunch_brand_id")
                            count = supabase.upsert_ga4_traffic_sources(property_id, period_end_date, traffic_sources, client_id=client_id_for_storage, brand_id=brand_id_for_storage)
                            total_count += count
                        total_synced["traffic_sources"] += total_count

                    # Geographic breakdown
                    if sync_job_service.is_cancelled(job_id):
                        logger.info(f"[Job {job_id}] Job cancelled before fetching geographic data for {client_name}")
                        return
                    # Fetch daily geographic breakdown (includes date dimension)
                    # Use limit=None to get all records (need daily data for all countries)
                    geographic_daily = await ga4_client.get_geographic_breakdown(property_id, period_start_date, period_end_date, limit=None, include_daily_breakdown=True)
                    if sync_job_service.is_cancelled(job_id):
                        logger.info(f"[Job {job_id}] Job cancelled after fetching geographic data for {client_name}")
                        return
                    if geographic_daily:
                        # Store for all clients sharing this property_id
                        # The geographic data now includes 'date' field, so upsert will handle multiple dates
                        total_count = 0
                        for client in clients_with_property:
                            client_id_for_storage = client.get("id")
                            brand_id_for_storage = client.get("scrunch_brand_id")
                            # Pass empty string for date since data includes date field
                            count = supabase.upsert_ga4_geographic(property_id, "", geographic_daily, client_id=client_id_for_storage, brand_id=brand_id_for_storage)
                            total_count += count
                        total_synced["geographic"] += total_count
                        logger.info(f"[Job {job_id}] Stored {total_count} daily geographic records for property {property_id}")

                    # Device breakdown
                    if sync_job_service.is_cancelled(job_id):
                        logger.info(f"[Job {job_id}] Job cancelled before fetching device data for {client_name}")
                        return
                    devices = await ga4_client.get_device_breakdown(property_id, period_start_date, period_end_date)
                    if sync_job_service.is_cancelled(job_id):
                        logger.info(f"[Job {job_id}] Job cancelled after fetching device data for {client_name}")
                        return
                    if devices:
                        # Store for all clients sharing this property_id
                        total_count = 0
                        for client in clients_with_property:
                            client_id_for_storage = client.get("id")
                            brand_id_for_storage = client.get("scrunch_brand_id")
                            count = supabase.upsert_ga4_devices(property_id, period_end_date, devices, client_id=client_id_for_storage, brand_id=brand_id_for_storage)
                            total_count += count
                        total_synced["devices"] += total_count

                    # Conversions (individual events)
                    if sync_job_service.is_cancelled(job_id):
                        logger.info(f"[Job {job_id}] Job cancelled before fetching conversions for property {property_id}")
                        return
                    conversions = await ga4_client.get_conversions(property_id, period_start_date, period_end_date)
                    if sync_job_service.is_cancelled(job_id):
                        logger.info(f"[Job {job_id}] Job cancelled after fetching conversions for property {property_id}")
                        return
                    if conversions:
                        # Store for all clients sharing this property_id
                        total_count = 0
                        for client in clients_with_property:
                            client_id_for_storage = client.get("id")
                            brand_id_for_storage = client.get("scrunch_brand_id")
                            count = supabase.upsert_ga4_conversions(property_id, period_end_date, conversions, client_id=client_id_for_storage, brand_id=brand_id_for_storage)
                            total_count += count
                        total_synced["conversions"] += total_count

                    # Realtime snapshot (if enabled)
                    if sync_realtime:
                        if sync_job_service.is_cancelled(job_id):
                            logger.info(f"[Job {job_id}] Job cancelled before fetching realtime data for property {property_id}")
                            return
                        realtime = await ga4_client.get_realtime_snapshot(property_id)
                        if sync_job_service.is_cancelled(job_id):
                            logger.info(f"[Job {job_id}] Job cancelled after fetching realtime data for property {property_id}")
                            return
                        if realtime:
                            # Store for all clients sharing this property_id
                            for client in clients_with_property:
                                client_id_for_storage = client.get("id")
                                brand_id_for_storage = client.get("scrunch_brand_id")
                                supabase.upsert_ga4_realtime(property_id, realtime, client_id=client_id_for_storage, brand_id=brand_id_for_storage)
                            total_synced["realtime"] += len(clients_with_property)

                    # Property details (static, only fetch once or periodically)
                    if sync_job_service.is_cancelled(job_id):
                        logger.info(f"[Job {job_id}] Job cancelled before fetching property details for property {property_id}")
                        return
                    property_details = await ga4_client.get_property_details(property_id)
                    if sync_job_service.is_cancelled(job_id):
                        logger.info(f"[Job {job_id}] Job cancelled after fetching property details for property {property_id}")
                        return
                    if property_details:
                        # Store for all clients sharing this property_id
                        for client in clients_with_property:
                            client_id_for_storage = client.get("id")
                            brand_id_for_storage = client.get("scrunch_brand_id")
                            supabase.upsert_ga4_property_details(property_id, property_details, client_id=client_id_for_storage, brand_id=brand_id_for_storage)

                except Exception as e:
                    logger.warning(f"[Job {job_id}] Error storing additional GA4 data for property {property_id}: {str(e)}")
                    # Continue even if some data fails to store

                # Add result entry for each client that was processed together
                for client in clients_with_property:
                    client_id_for_result = client.get("id")
                    client_name_for_result = client.get("company_name", f"Client {client_id_for_result}")
                    client_results.append({
                        "client_id": client_id_for_result,
                        "client_name": client_name_for_result,
                        "property_id": property_id,
                        "status": "success",
                        "kpi_snapshot_stored": True,
                        "data_stored": {
                            "traffic_overview": total_synced.get("traffic_overview", 0),
                            "top_pages": total_synced.get("top_pages", 0),
                            "traffic_sources": total_synced.get("traffic_sources", 0),
                            "geographic": total_synced.get("geographic", 0),
                            "devices": total_synced.get("devices", 0),
                            "conversions": total_synced.get("conversions", 0),
                            "realtime": total_synced.get("realtime", 0)
                        }
                    })
                    total_synced["clients"] += 1

            except Exception as e:
                logger.error(f"[Job {job_id}] Error syncing GA4 for property {property_id}: {str(e)}")
                # Add error result for all clients that were supposed to be processed
                for client in clients_with_property:
                    client_id_for_result = client.get("id")
                    client_name_for_result = client.get("company_name", f"Client {client_id_for_result}")
                    client_results.append({
                        "client_id": client_id_for_result,
                        "client_name": client_name_for_result,
                        "property_id": property_id,
                        "status": "error",
                        "error": str(e)
                    })

        # Check for cancellation before completing
        if sync_job_service.is_cancelled(job_id):
            logger.info(f"[Job {job_id}] Job was cancelled, not completing")
            return

        status = "partial" if any(r.get("status") == "error" for r in client_results) else "success"

        result = {
            "status": "success",
            "message": f"Synced GA4 data for {total_synced['clients']} client(s)",
            "date_range": {"start_date": start_date, "end_date": end_date},
            "total_synced": total_synced,
            "client_results": client_results
        }

        await sync_job_service.complete_job(job_id, result)

        # Log audit
        await audit_logger.log_sync(
            sync_type=AuditLogAction.SYNC_GA4,
            user_id=user_id,
            user_email=user_email,
            status=status,
            details={
                "client_id": client_id,
                "start_date": start_date,
                "end_date": end_date,
                "total_synced": total_synced,
                "client_results": client_results,
                "job_id": job_id
            },
            request=request,
            db=db
        )

    except Exception as e:
        logger.error(f"[Job {job_id}] Failed: {str(e)}")
        await sync_job_service.fail_job(job_id, str(e))

        await audit_logger.log_sync(
            sync_type=AuditLogAction.SYNC_GA4,
            user_id=user_id,
            user_email=user_email,
            status="error",
            error_message=str(e),
            details={"client_id": client_id, "job_id": job_id},
            request=request,
            db=db
        )
        raise
    finally:
        db.close()

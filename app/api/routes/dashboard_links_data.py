from fastapi import APIRouter, Query, HTTPException, Depends, Request
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime, date as date_type, timezone
from app.services.supabase_service import SupabaseService
from app.core.error_utils import handle_api_errors
from app.api.auth_v2 import get_current_user_v2
from app.db.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from app.api.routes.models import DashboardLinkRequest, DashboardLinkUpdateRequest

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/data/dashboard-links/{slug}")
@handle_api_errors(context="fetching dashboard link by slug")
async def get_dashboard_link_by_slug(
    slug: str,
    db: Session = Depends(get_db)
):
    """Fetch a dashboard link by slug with expiry/enablement checks (public)"""
    supabase = SupabaseService(db=db)
    link = supabase.get_dashboard_link_by_slug(slug)
    if not link:
        raise HTTPException(status_code=404, detail="Dashboard link not found")
    if not link.get("enabled", False):
        raise HTTPException(status_code=403, detail="Dashboard link is disabled")

    expires_at = link.get("expires_at")
    if expires_at:
        # Handle timezone-aware comparison
        now = datetime.now(timezone.utc)
        # If expires_at is a string, parse it; if it's datetime, ensure it's timezone-aware
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
        elif isinstance(expires_at, datetime) and expires_at.tzinfo is None:
            # If naive, assume UTC
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        # Now both are timezone-aware, compare
        if now > expires_at:
            supabase.disable_dashboard_link(link["id"])
            raise HTTPException(status_code=410, detail="Dashboard link has expired")

    return link

@router.post("/data/dashboard-links/{slug}/track")
@handle_api_errors(context="tracking dashboard link open")
async def track_dashboard_link_open(
    slug: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Track when a dashboard link is opened (public access)"""
    
    supabase = SupabaseService(db=db)
    
    # Get the link first to verify it exists and is enabled
    link = supabase.get_dashboard_link_by_slug(slug)
    if not link:
        raise HTTPException(status_code=404, detail="Dashboard link not found")
    
    if not link.get("enabled", False):
        raise HTTPException(status_code=403, detail="Dashboard link is disabled")
    
    expires_at = link.get("expires_at")
    if expires_at:
        # Handle timezone-aware comparison
        now = datetime.now(timezone.utc)
        # If expires_at is a string, parse it; if it's datetime, ensure it's timezone-aware
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
        elif isinstance(expires_at, datetime) and expires_at.tzinfo is None:
            # If naive, assume UTC
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        # Now both are timezone-aware, compare
        if now > expires_at:
            supabase.disable_dashboard_link(link["id"])
            raise HTTPException(status_code=410, detail="Dashboard link has expired")
    
    # Get client IP address
    client_host = request.client.host if request.client else None
    # Try to get real IP from headers (for proxies)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        ip_address = forwarded_for.split(",")[0].strip()
    else:
        ip_address = client_host
    
    # Get user agent and referer from request body or headers
    try:
        body = await request.json()
        user_agent = body.get("user_agent") or request.headers.get("User-Agent")
        referer = body.get("referer") or request.headers.get("Referer")
    except:
        user_agent = request.headers.get("User-Agent")
        referer = request.headers.get("Referer")
    
    # Track the link open
    success = supabase.track_dashboard_link_open(
        link_id=link["id"],
        ip_address=ip_address,
        user_agent=user_agent,
        referer=referer
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to track link open")
    
    return {"status": "success", "message": "Link open tracked"}



@router.get("/data/dashboard-links")
@handle_api_errors(context="listing all dashboard links")
async def list_all_dashboard_links(
    current_user: dict = Depends(get_current_user_v2),
    db: Session = Depends(get_db)
):
    """List all dashboard links across all clients (admin view) - optimized for bulk loading"""
    supabase = SupabaseService(db=db)
    links = supabase.list_all_dashboard_links()
    return {"items": links}

@router.get("/data/clients/{client_id}/dashboard-links")
@handle_api_errors(context="listing dashboard links for client")
async def list_dashboard_links_for_client(
    client_id: int,
    current_user: dict = Depends(get_current_user_v2),
    db: Session = Depends(get_db)
):
    """List all dashboard links for a client (admin view)"""
    supabase = SupabaseService(db=db)
    client = supabase.get_client_by_id(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    links = supabase.list_dashboard_links_for_client(client_id)
    return {"items": links}

@router.post("/data/clients/{client_id}/dashboard-links")
@handle_api_errors(context="upserting dashboard link for client")
async def upsert_dashboard_link_for_client(
    client_id: int,
    request: DashboardLinkRequest,
    current_user: dict = Depends(get_current_user_v2),
    db: Session = Depends(get_db)
):
    """Create a new dashboard link for a client (always creates new, even for same date range)"""
    supabase = SupabaseService(db=db)
    client = supabase.get_client_by_id(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Validate attached_link_ids — must belong to the same client
    if request.attached_link_ids:
        client_links = supabase.list_dashboard_links_for_client(client_id)
        client_link_ids = {l["id"] for l in client_links}
        max_attachable = max(0, len(client_link_ids) - 1)  # can't attach self
        if len(request.attached_link_ids) > max_attachable:
            raise HTTPException(status_code=400, detail=f"Cannot attach more than {max_attachable} links for this client")
        invalid = [i for i in request.attached_link_ids if i not in client_link_ids]
        if invalid:
            raise HTTPException(status_code=400, detail=f"Attached link IDs not found for this client: {invalid}")

    link = supabase.upsert_dashboard_link(
        client_id=client_id,
        slug=request.slug,
        start_date=request.start_date,
        end_date=request.end_date,
        enabled=request.enabled,
        expires_at=request.expires_at,
        name=request.name,
        description=request.description,
        user_email=current_user.get("email"),
        selected_kpis=request.selected_kpis,
        visible_sections=request.visible_sections,
        visible_highlights=request.visible_highlights,  # Can be [] (empty array) or ['what_worked'] etc.
        selected_charts=request.selected_charts,
        selected_performance_metrics_kpis=request.selected_performance_metrics_kpis,
        show_change_period=request.show_change_period,
        executive_summary=request.executive_summary,
        global_filters=request.global_filters,
        attached_link_ids=request.attached_link_ids,
    )

    if not link:
        raise HTTPException(status_code=500, detail="Unable to save dashboard link")

    # Only generate AI Overview when client did NOT send executive_summary.
    # When client sends it (from reporting dashboard), use that as the link's overview so edits are preserved.
    if request.executive_summary is None or (isinstance(request.executive_summary, dict) and not request.executive_summary):
        try:
            from app.api.openai import generate_overall_overview, OverallOverviewRequest

            final_start_date = link.get("start_date")
            final_end_date = link.get("end_date")
            if final_start_date and final_end_date:
                start_date_str = final_start_date.isoformat() if hasattr(final_start_date, "isoformat") else str(final_start_date)
                end_date_str = final_end_date.isoformat() if hasattr(final_end_date, "isoformat") else str(final_end_date)
                logger.info(f"Generating AI Overview for new dashboard link {link.get('id')} - client_id={client_id}, dates={start_date_str} to {end_date_str}")
                link_slug = link.get("slug")
                overview_request = OverallOverviewRequest(
                    client_id=client_id,
                    brand_id=None,
                    start_date=start_date_str,
                    end_date=end_date_str,
                    dashboard_link_slug=link_slug,
                )
                overview_response = await generate_overall_overview(overview_request, db=db)
                if overview_response and overview_response.get("executive_summary"):
                    updated_link = supabase.update_dashboard_link(
                        link_id=link.get("id"),
                        updates={"executive_summary": overview_response["executive_summary"]},
                        user_email=current_user.get("email")
                    )
                    if updated_link:
                        link = updated_link
                else:
                    logger.warning(f"No executive summary in AI Overview response for dashboard link {link.get('id')}")
        except Exception as e:
            logger.error(f"Error generating AI Overview for dashboard link {link.get('id')}: {str(e)}", exc_info=True)
    else:
        logger.info(f"Using client-provided executive summary for new dashboard link {link.get('id')} (no regeneration)")

    return {
        "status": "success",
        "link": link,
        "shareable_url": f"/reporting/client/{link['slug']}"
    }

@router.put("/data/clients/{client_id}/dashboard-links/{link_id}")
@handle_api_errors(context="updating dashboard link")
async def update_dashboard_link(
    client_id: int,
    link_id: int,
    request: DashboardLinkUpdateRequest,
    current_user: dict = Depends(get_current_user_v2),
    db: Session = Depends(get_db)
):
    """Update a dashboard link"""
    supabase = SupabaseService(db=db)
    client = supabase.get_client_by_id(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Verify the link belongs to this client
    links = supabase.list_dashboard_links_for_client(client_id)
    link = next((l for l in links if l.get("id") == link_id), None)
    if not link:
        raise HTTPException(status_code=404, detail="Dashboard link not found")
    
    # Prepare update data
    update_data = {}
    if request.name is not None:
        update_data["name"] = request.name
    if request.description is not None:
        update_data["description"] = request.description
    if request.start_date is not None:
        update_data["start_date"] = request.start_date
    if request.end_date is not None:
        update_data["end_date"] = request.end_date
    if request.enabled is not None:
        update_data["enabled"] = request.enabled
    if request.expires_at is not None:
        update_data["expires_at"] = request.expires_at
    if request.slug is not None:
        update_data["slug"] = request.slug
    # Include KPI selections if provided
    if request.selected_kpis is not None:
        update_data["selected_kpis"] = request.selected_kpis
    if request.visible_sections is not None:
        update_data["visible_sections"] = request.visible_sections
    if request.visible_highlights is not None:
        update_data["visible_highlights"] = request.visible_highlights
    if request.selected_charts is not None:
        update_data["selected_charts"] = request.selected_charts
    if request.selected_performance_metrics_kpis is not None:
        update_data["selected_performance_metrics_kpis"] = request.selected_performance_metrics_kpis
    if request.show_change_period is not None:
        update_data["show_change_period"] = request.show_change_period
    if request.executive_summary is not None:
        update_data["executive_summary"] = request.executive_summary
    if request.attached_link_ids is not None:
        # Validate all IDs belong to this client and are not self-referential
        client_link_ids = {l["id"] for l in links}
        max_attachable = max(0, len(client_link_ids) - 1)
        if len(request.attached_link_ids) > max_attachable:
            raise HTTPException(status_code=400, detail=f"Cannot attach more than {max_attachable} links for this client")
        invalid = [i for i in request.attached_link_ids if i not in client_link_ids or i == link_id]
        if invalid:
            raise HTTPException(status_code=400, detail=f"Invalid attached link IDs: {invalid}")
        update_data["attached_link_ids"] = request.attached_link_ids

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    updated_link = supabase.update_dashboard_link(
        link_id=link_id,
        updates=update_data,
        user_email=current_user.get("email")
    )
    
    if not updated_link:
        raise HTTPException(status_code=500, detail="Failed to update dashboard link")

    # Only generate AI Overview when client did NOT send executive_summary.
    # When client sends it (from reporting dashboard), the update_data already has it; do not overwrite.
    if request.executive_summary is None:
        try:
            from app.api.openai import generate_overall_overview, OverallOverviewRequest

            final_start_date = updated_link.get("start_date") or link.get("start_date")
            final_end_date = updated_link.get("end_date") or link.get("end_date")
            if final_start_date and final_end_date:
                start_date_str = final_start_date.isoformat() if hasattr(final_start_date, "isoformat") else str(final_start_date)
                end_date_str = final_end_date.isoformat() if hasattr(final_end_date, "isoformat") else str(final_end_date)
                logger.info(f"Generating AI Overview for dashboard link {link_id} - client_id={client_id}, dates={start_date_str} to {end_date_str}")
                link_slug = updated_link.get("slug")
                overview_request = OverallOverviewRequest(
                    client_id=client_id,
                    brand_id=None,
                    start_date=start_date_str,
                    end_date=end_date_str,
                    dashboard_link_slug=link_slug,
                )
                overview_response = await generate_overall_overview(overview_request, db=db)
                if overview_response and overview_response.get("executive_summary"):
                    final_updated_link = supabase.update_dashboard_link(
                        link_id=link_id,
                        updates={"executive_summary": overview_response["executive_summary"]},
                        user_email=current_user.get("email")
                    )
                    if final_updated_link:
                        updated_link = final_updated_link
                else:
                    logger.warning(f"No executive summary in AI Overview response for dashboard link {link_id}")
        except Exception as e:
            logger.error(f"Error generating AI Overview for dashboard link {link_id}: {str(e)}", exc_info=True)
    else:
        logger.info(f"Using client-provided executive summary for dashboard link {link_id} (no regeneration)")

    return {
        "status": "success",
        "link": updated_link
    }

@router.delete("/data/clients/{client_id}/dashboard-links/{link_id}")
@handle_api_errors(context="deleting dashboard link")
async def delete_dashboard_link(
    client_id: int,
    link_id: int,
    current_user: dict = Depends(get_current_user_v2),
    db: Session = Depends(get_db)
):
    """Delete a dashboard link"""
    supabase = SupabaseService(db=db)
    client = supabase.get_client_by_id(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Verify the link belongs to this client
    links = supabase.list_dashboard_links_for_client(client_id)
    link = next((l for l in links if l.get("id") == link_id), None)
    if not link:
        raise HTTPException(status_code=404, detail="Dashboard link not found")
    
    success = supabase.delete_dashboard_link(link_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete dashboard link")
    
    return {
        "status": "success",
        "message": "Dashboard link deleted successfully"
    }

@router.post("/data/clients/{client_id}/regenerate-shareable-link")
@handle_api_errors(context="regenerating shareable link")
async def regenerate_shareable_link(
    client_id: int,
    current_user: dict = Depends(get_current_user_v2),
    db: Session = Depends(get_db)
):
    """Regenerate shareable link for a client (creates new slug and resets 48-hour window)"""
    from app.services.websocket_manager import websocket_manager
    from datetime import datetime
    from sqlalchemy import select, update
    import uuid
    
    try:
        supabase = SupabaseService(db=db)
        
        # Get current client
        table = supabase._get_table("clients")
        query = select(table.c.id, table.c.company_name).where(table.c.id == client_id).limit(1)
        result = db.execute(query)
        current_client_row = result.first()
        
        if not current_client_row:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Generate new UUID-based slug (non-guessable)
        new_slug = supabase.generate_client_slug()
        
        # Update client's url_slug (updated_at will be automatically updated by database trigger)
        update_stmt = update(table).where(table.c.id == client_id).values(
            url_slug=new_slug,
            updated_by=current_user.get("email"),
            last_modified_by=current_user.get("email")
        )
        db.execute(update_stmt)
        db.commit()
        
        # Get updated client to return new slug
        updated_query = select(table.c.url_slug, table.c.updated_at).where(table.c.id == client_id).limit(1)
        updated_result = db.execute(updated_query)
        updated_row = updated_result.first()
        
        if not updated_row:
            raise HTTPException(status_code=500, detail="Failed to retrieve updated client")
        
        new_url = f"/reporting/client/{new_slug}"
        
        # Broadcast WebSocket notification
        try:
            await websocket_manager.notify_resource_updated(
                resource_type="client",
                resource_id=client_id,
                updated_by=current_user.get("email"),
                updated_at=datetime.utcnow().isoformat() + "Z",
                exclude_user_id=current_user.get("id")
            )
        except Exception as ws_error:
            logger.warning(f"Failed to send WebSocket notification: {str(ws_error)}")
        
        return {
            "status": "success",
            "message": "Shareable link regenerated successfully",
            "slug": new_slug,
            "shareable_url": new_url,
            "expires_at": updated_row.updated_at  # Link expires 48 hours from updated_at
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error regenerating shareable link: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/clients/{client_id}/dashboard-links/{link_id}/kpi-selections")
@handle_api_errors(context="getting dashboard link KPI selections")
async def get_dashboard_link_kpi_selections(
    client_id: int,
    link_id: int,
    current_user: dict = Depends(get_current_user_v2),
    db: Session = Depends(get_db)
):
    """Get KPI selections for a specific dashboard link"""
    supabase = SupabaseService(db=db)
    client = supabase.get_client_by_id(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Verify the link belongs to this client
    links = supabase.list_dashboard_links_for_client(client_id)
    link = next((l for l in links if l.get("id") == link_id), None)
    if not link:
        raise HTTPException(status_code=404, detail="Dashboard link not found")
    
    kpi_selection = supabase.get_dashboard_link_kpi_selection(link_id)
    
    if not kpi_selection:
        # Return default selections if none exist
        return {
            "dashboard_link_id": link_id,
            "selected_kpis": [],
            "visible_sections": ['ga4', 'scrunch_ai', 'brand_analytics', 'advanced_analytics', 'keywords'],
            "selected_charts": [],
            "selected_performance_metrics_kpis": [],
            "created_at": None,
            "updated_at": None
        }
    
    return kpi_selection


@router.get("/data/clients/{client_id}/dashboard-links/{link_id}/logs")
@handle_api_errors(context="listing dashboard link activity logs")
async def list_dashboard_link_logs(
    client_id: int,
    link_id: int,
    current_user: dict = Depends(get_current_user_v2),
    db: Session = Depends(get_db)
):
    """List activity logs for a dashboard link (created/updated, created_at, created_by, changes)."""
    supabase = SupabaseService(db=db)
    client = supabase.get_client_by_id(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    links = supabase.list_dashboard_links_for_client(client_id)
    link = next((l for l in links if l.get("id") == link_id), None)
    if not link:
        raise HTTPException(status_code=404, detail="Dashboard link not found")
    logs = supabase.list_dashboard_link_logs(link_id)
    return {"items": logs}


@router.get("/data/clients/{client_id}/dashboard-links/{link_id}/metrics")
@handle_api_errors(context="getting dashboard link metrics")
async def get_dashboard_link_metrics(
    client_id: int,
    link_id: int,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: dict = Depends(get_current_user_v2),
    db: Session = Depends(get_db)
):
    """Get metrics for a specific dashboard link"""
    supabase = SupabaseService(db=db)
    client = supabase.get_client_by_id(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Verify the link belongs to this client
    links = supabase.list_dashboard_links_for_client(client_id)
    link = next((l for l in links if l.get("id") == link_id), None)
    if not link:
        raise HTTPException(status_code=404, detail="Dashboard link not found")
    
    # Parse dates if provided
    start_dt = None
    end_dt = None
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")
    
    metrics = supabase.get_dashboard_link_metrics(
        link_id=link_id,
        start_date=start_dt,
        end_date=end_dt
    )
    
    return metrics

@router.get("/data/clients/{client_id}/dashboard-links/metrics")
@handle_api_errors(context="getting dashboard links metrics")
async def get_dashboard_links_metrics(
    client_id: int,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: dict = Depends(get_current_user_v2),
    db: Session = Depends(get_db)
):
    """Get aggregated metrics for all dashboard links of a client"""
    supabase = SupabaseService(db=db)
    client = supabase.get_client_by_id(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Parse dates if provided
    start_dt = None
    end_dt = None
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")
    
    metrics = supabase.get_client_dashboard_links_metrics(
        client_id=client_id,
        start_date=start_dt,
        end_date=end_dt
    )
    
    return metrics



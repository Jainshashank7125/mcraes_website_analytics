from fastapi import APIRouter, Query, HTTPException, Depends, UploadFile, File
from typing import Optional, List, Dict, Any
import logging
import uuid
from datetime import datetime, date as date_type, timezone
from app.services.supabase_service import SupabaseService
from app.core.config import settings
from app.core.error_utils import handle_api_errors
from app.api.auth_v2 import get_current_user_v2
from app.db.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_, update, insert, delete
from pydantic import BaseModel
from app.api.routes.models import DashboardLinkRequest, DashboardLinkUpdateRequest

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/data/brands/slug/{slug}")
async def get_brand_by_slug(slug: str, db: Session = Depends(get_db)):
    """Get brand by slug for public access
    
    Supports both client url_slug and brand slug:
    - First tries to find a client by url_slug, then returns the associated brand
    - Falls back to finding a brand by slug if no client found
    """
    try:
        supabase = SupabaseService(db=db)
        dashboard_link = supabase.get_dashboard_link_by_slug(slug)
        client = None

        if dashboard_link:
            if not dashboard_link.get("enabled", False):
                raise HTTPException(status_code=403, detail="Dashboard link is disabled")
            expires_at = dashboard_link.get("expires_at")
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
                    supabase.disable_dashboard_link(dashboard_link["id"])
                    raise HTTPException(status_code=410, detail="Dashboard link has expired")
            client = supabase.get_client_by_id(dashboard_link["client_id"])
            if client:
                client["dashboard_link"] = dashboard_link
            else:
                raise HTTPException(status_code=404, detail="Client not found for dashboard link")
        
        # First, try to find a client by url_slug (for /reporting/client/:slug routes)
        if client is None:
            client = supabase.get_client_by_slug(slug)
        if client:
            # If client found, get the associated brand via scrunch_brand_id
            if client.get("scrunch_brand_id"):
                brand_id = client["scrunch_brand_id"]
                brand = supabase.get_brand_by_id(brand_id)
                if brand:
                    logger.info(f"Found client by url_slug '{slug}', returning associated brand")
                    brand_with_link = dict(brand)
                    if client.get("dashboard_link"):
                        brand_with_link["dashboard_link"] = client["dashboard_link"]
                    return brand_with_link
                else:
                    # Return client info as brand info for public view
                    # Don't set no_data: true here - let the dashboard endpoint check for Agency Analytics/GA4 data
                    logger.info(f"Client found but associated brand (id: {brand_id}) not found, returning client info - dashboard will check for Agency Analytics/GA4 data")
                    return {
                        "id": client.get("id"),
                        "name": client.get("company_name", "Unknown"),
                        "slug": slug,
                        "theme_color": client.get("theme_color"),
                        "logo_url": client.get("logo_url"),
                        "client_id": client.get("id"),  # Include client_id so dashboard can use it
                        "dashboard_link": client.get("dashboard_link")
                    }
            else:
                # Return client info as brand info for public view
                # Don't set no_data: true here - let the dashboard endpoint check for Agency Analytics/GA4 data
                logger.info(f"Client found but no brand mapping configured (scrunch_brand_id is null), returning client info - dashboard will check for Agency Analytics/GA4 data")
                return {
                    "id": client.get("id"),
                    "name": client.get("company_name", "Unknown"),
                    "slug": slug,
                    "theme_color": client.get("theme_color"),
                    "logo_url": client.get("logo_url"),
                    "client_id": client.get("id"),  # Include client_id so dashboard can use it
                    "dashboard_link": client.get("dashboard_link")
                }
        
        # Fall back to finding a brand by slug (for backward compatibility)
        brand = supabase.get_brand_by_slug(slug)
        
        if not brand:
            # Return empty brand info instead of 404 for public view (graceful degradation)
            logger.warning(f"Neither client nor brand found for slug '{slug}', returning empty brand info")
            return {
                "id": None,
                "name": "Unknown",
                "slug": slug,
                "theme_color": None,
                "logo_url": None,
                "no_data": True,
                "message": "No data available for this slug."
            }
        
        return brand
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching brand by slug: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class GA4PropertyUpdateRequest(BaseModel):
    ga4_property_id: Optional[str] = None
    version: Optional[int] = None  # Version for optimistic locking

@router.put("/data/brands/{brand_id}/ga4-property-id")
@handle_api_errors(context="updating GA4 property ID")
async def update_brand_ga4_property_id(
    brand_id: int,
    request: GA4PropertyUpdateRequest,
    current_user: dict = Depends(get_current_user_v2),
    db: Session = Depends(get_db)
):
    """Update GA4 Property ID for a brand"""
    from app.services.websocket_manager import websocket_manager
    from datetime import datetime
    
    try:
        supabase = SupabaseService(db=db)
        
        # Get current brand to check version using SQLAlchemy
        brand = supabase.get_brand_by_id(brand_id)
        
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        current_version = brand.get("version", 1)
        
        # Version conflict check
        if request.version is not None and request.version != current_version:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "conflict",
                    "message": "Resource was modified by another user. Please refresh and try again.",
                    "current_version": current_version,
                    "current_data": {
                        "ga4_property_id": brand.get("ga4_property_id"),
                        "last_modified_by": brand.get("last_modified_by")
                    }
                }
            )
        
        # Update GA4 property ID using SQLAlchemy method
        ga4_property_id = request.ga4_property_id
        success = supabase.update_brand_ga4_property_id(
            brand_id=brand_id,
            ga4_property_id=ga4_property_id if ga4_property_id else None,
            user_email=current_user.get("email")
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update GA4 property ID")
        
        # Get updated version using SQLAlchemy
        updated_brand = supabase.get_brand_by_id(brand_id)
        updated_version = updated_brand.get("version", 1) if updated_brand else 1
        
        logger.info(f"Updated GA4 property ID for brand {brand_id} by user {current_user.get('email')}, version={updated_version}")
        
        # Broadcast WebSocket notification
        try:
            await websocket_manager.notify_resource_updated(
                resource_type="brand",
                resource_id=brand_id,
                updated_by=current_user.get("email"),
                updated_at=datetime.utcnow().isoformat() + "Z",
                version=updated_version,
                exclude_user_id=current_user.get("id")
            )
        except Exception as ws_error:
            logger.warning(f"Failed to send WebSocket notification: {str(ws_error)}")
        
        return {
            "brand_id": brand_id,
            "ga4_property_id": update_data["ga4_property_id"],
            "version": updated_version,
            "message": "GA4 Property ID updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating GA4 property ID for brand {brand_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating GA4 property ID: {str(e)}")


@router.post("/data/brands/{brand_id}/agency-analytics-campaigns/{campaign_id}/link")
@handle_api_errors(context="linking Agency Analytics campaign")
async def link_agency_analytics_campaign(
    brand_id: int,
    campaign_id: int,
    current_user: dict = Depends(get_current_user_v2),
    db: Session = Depends(get_db)
):
    """Link an Agency Analytics campaign to a brand"""
    try:
        supabase = SupabaseService(db=db)
        
        # Check if brand exists using SQLAlchemy
        brand = supabase.get_brand_by_id(brand_id)
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        # Check if campaign exists using SQLAlchemy Core
        campaigns_table = supabase._get_table("agency_analytics_campaigns")
        campaign_query = select(campaigns_table).where(campaigns_table.c.id == campaign_id).limit(1)
        campaign_result = supabase.db.execute(campaign_query)
        campaign_row = campaign_result.first()
        
        if not campaign_row:
            raise HTTPException(status_code=404, detail="Agency Analytics campaign not found")
        
        # Check if link already exists using SQLAlchemy Core
        links_table = supabase._get_table("agency_analytics_campaign_brands")
        existing_query = select(links_table).where(
            and_(links_table.c.brand_id == brand_id, links_table.c.campaign_id == campaign_id)
        ).limit(1)
        existing_result = supabase.db.execute(existing_query)
        existing_row = existing_result.first()
        
        if existing_row:
            return {
                "brand_id": brand_id,
                "campaign_id": campaign_id,
                "message": "Campaign is already linked to this brand"
            }
        
        # Create link using SQLAlchemy Core
        link_data = {
            "brand_id": brand_id,
            "campaign_id": campaign_id,
            "match_method": "manual",
            "match_confidence": "manual",
            "updated_at": datetime.utcnow()
        }
        
        stmt = insert(links_table).values(**link_data)
        supabase.db.execute(stmt)
        supabase.db.commit()
        
        logger.info(f"Linked campaign {campaign_id} to brand {brand_id} by user {current_user.get('email')}")
        
        return {
            "brand_id": brand_id,
            "campaign_id": campaign_id,
            "message": "Campaign linked successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error linking campaign {campaign_id} to brand {brand_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error linking campaign: {str(e)}")

@router.delete("/data/brands/{brand_id}/agency-analytics-campaigns/{campaign_id}/link")
@handle_api_errors(context="unlinking Agency Analytics campaign")
async def unlink_agency_analytics_campaign(
    brand_id: int,
    campaign_id: int,
    current_user: dict = Depends(get_current_user_v2),
    db: Session = Depends(get_db)
):
    """Unlink an Agency Analytics campaign from a brand"""
    try:
        supabase = SupabaseService(db=db)
        
        # Check if brand exists using SQLAlchemy
        brand = supabase.get_brand_by_id(brand_id)
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        # Check if link exists using SQLAlchemy Core
        links_table = supabase._get_table("agency_analytics_campaign_brands")
        existing_query = select(links_table).where(
            and_(links_table.c.brand_id == brand_id, links_table.c.campaign_id == campaign_id)
        ).limit(1)
        existing_result = supabase.db.execute(existing_query)
        existing_row = existing_result.first()
        
        if not existing_row:
            raise HTTPException(status_code=404, detail="Campaign is not linked to this brand")
        
        # Delete link using SQLAlchemy Core
        delete_stmt = delete(links_table).where(
            and_(links_table.c.brand_id == brand_id, links_table.c.campaign_id == campaign_id)
        )
        supabase.db.execute(delete_stmt)
        supabase.db.commit()
        
        logger.info(f"Unlinked campaign {campaign_id} from brand {brand_id} by user {current_user.get('email')}")
        
        return {
            "brand_id": brand_id,
            "campaign_id": campaign_id,
            "message": "Campaign unlinked successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unlinking campaign {campaign_id} from brand {brand_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error unlinking campaign: {str(e)}")

@router.get("/data/brands/{brand_id}/agency-analytics-campaigns")
@handle_api_errors(context="fetching linked campaigns")
async def get_brand_linked_campaigns(
    brand_id: int,
    current_user: dict = Depends(get_current_user_v2),
    db: Session = Depends(get_db)
):
    """Get all Agency Analytics campaigns linked to a brand"""
    try:
        supabase = SupabaseService(db=db)
        
        # Get linked campaigns using SQLAlchemy
        links = supabase.get_campaign_brand_links(brand_id=brand_id)
        
        if not links:
            return {
                "brand_id": brand_id,
                "linked_campaigns": [],
                "available_campaigns": []
            }
        
        # Get campaign details using SQLAlchemy Core
        campaign_ids = [link["campaign_id"] for link in links]
        campaigns_table = supabase._get_table("agency_analytics_campaigns")
        query = select(campaigns_table).where(campaigns_table.c.id.in_(campaign_ids))
        result = supabase.db.execute(query)
        linked_campaigns = [dict(row._mapping) for row in result]
        
        # Get all available campaigns for selection using SQLAlchemy Core
        all_campaigns_query = select(campaigns_table).order_by(campaigns_table.c.id.desc())
        all_campaigns_result = supabase.db.execute(all_campaigns_query)
        all_campaigns = [dict(row._mapping) for row in all_campaigns_result]
        
        return {
            "brand_id": brand_id,
            "linked_campaigns": linked_campaigns,
            "available_campaigns": all_campaigns
        }
    except Exception as e:
        logger.error(f"Error fetching linked campaigns for brand {brand_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching linked campaigns: {str(e)}")


class ThemeUpdateRequest(BaseModel):
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    font_family: Optional[str] = None
    custom: Optional[Dict] = None
    version: Optional[int] = None  # Version for optimistic locking

@router.post("/data/brands/{brand_id}/logo")
@handle_api_errors(context="uploading brand logo")
async def upload_brand_logo(
    brand_id: int,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user_v2),
    db: Session = Depends(get_db)
):
    """Upload brand logo to Supabase Storage"""
    try:
        # Check if brand exists using SQLAlchemy
        supabase = SupabaseService(db=db)
        brand = supabase.get_brand_by_id(brand_id)
        
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        # Create Supabase client with service role key for storage operations
        # Service role key is required to bypass RLS for storage uploads
        from app.core.database import get_supabase_service_role_client
        storage_client = get_supabase_service_role_client()
        
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read file content
        file_content = await file.read()
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'png'
        
        # Generate unique filename (just the filename, not including bucket name in path)
        filename = f"brand-{brand_id}-{uuid.uuid4().hex[:8]}.{file_extension}"
        file_path = filename  # Path is relative to bucket root
        
        # Upload to Supabase Storage using Supabase client
        # The bucket name is 'brand-logos', file path is just the filename
        try:
            logger.info(f"Uploading file to storage: bucket=brand-logos, path={file_path}, size={len(file_content)} bytes, content-type={file.content_type}")
            
            responseBuckets = storage_client.storage.list_buckets()
            logger.info(f"Buckets: {responseBuckets}")
            # Upload using Supabase storage client
            storage_response = storage_client.storage.from_("brand-logos").upload(
                file=file_content,
                path=file_path,
                file_options={
                    "content-type": file.content_type,
                    "cache-control": "3600",
                    "upsert": "true"
                }
            )
            
            logger.info(f"Storage upload successful: {storage_response}")
            
            # Get public URL using Supabase client
            try:
                public_url_response = storage_client.storage.from_("brand-logos").get_public_url(file_path)
                if isinstance(public_url_response, str):
                    logo_url = public_url_response
                elif hasattr(public_url_response, 'get'):
                    logo_url = public_url_response.get('publicUrl', '')
                else:
                    logo_url = str(public_url_response)
            except Exception as url_error:
                logger.warning(f"Could not get public URL from response: {url_error}")
                logo_url = None
            
            # Construct public URL manually if Supabase client method fails
            if not logo_url:
                # Extract project ref from SUPABASE_URL
                # URL format: https://{project_ref}.supabase.co
                project_ref = settings.SUPABASE_URL.replace('https://', '').replace('.supabase.co', '')
                logo_url = f"https://{project_ref}.supabase.co/storage/v1/object/public/brand-logos/{file_path}"
            
            logger.info(f"Final logo URL: {logo_url}")
            
        except Exception as storage_error:
            logger.error(f"Storage error: {str(storage_error)}")
            # Fallback: Store as base64 data URL (not recommended for production)
            # For now, we'll raise an error and ask user to configure storage
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload to storage. Error: {str(storage_error)}"
            )
        
        # Update brand with logo URL using SQLAlchemy
        supabase = SupabaseService(db=db)
        success = supabase.update_brand_logo_url(
            brand_id=brand_id,
            logo_url=logo_url,
            user_email=current_user.get("email")
        )
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update brand logo URL")
        
        logger.info(f"Uploaded logo for brand {brand_id} by user {current_user.get('email')}")
        
        return {
            "brand_id": brand_id,
            "logo_url": logo_url,
            "message": "Logo uploaded successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading logo for brand {brand_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading logo: {str(e)}")

@router.delete("/data/brands/{brand_id}/logo")
@handle_api_errors(context="deleting brand logo")
async def delete_brand_logo(
    brand_id: int,
    current_user: dict = Depends(get_current_user_v2),
    db: Session = Depends(get_db)
):
    """Delete brand logo"""
    try:
        supabase = SupabaseService(db=db)
        
        # Check if brand exists and get current logo using SQLAlchemy
        brand = supabase.get_brand_by_id(brand_id)
        
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        logo_url = brand.get("logo_url")
        
        # Delete from storage if URL exists (storage still uses Supabase)
        if logo_url:
            try:
                from app.core.database import get_supabase_client
                # Use service role client for storage operations (bypasses RLS)
                from app.core.database import get_supabase_service_role_client
                storage_client = get_supabase_service_role_client()
                
                # Extract file path from URL
                # URL format: .../storage/v1/object/public/brand-logos/{filename}
                if "brand-logos/" in logo_url:
                    file_path = logo_url.split("brand-logos/")[-1].split("?")[0]  # Remove query params if any
                elif "/object/public/brand-logos/" in logo_url:
                    file_path = logo_url.split("/object/public/brand-logos/")[-1].split("?")[0]
                else:
                    # Try to extract just the filename
                    file_path = logo_url.split("/")[-1].split("?")[0]
                
                if file_path:
                    logger.info(f"Deleting file from storage: {file_path}")
                    storage_client.storage.from_("brand-logos").remove([file_path])
            except Exception as storage_error:
                logger.warning(f"Failed to delete logo from storage: {str(storage_error)}")
        
        # Update brand to remove logo URL using SQLAlchemy
        success = supabase.update_brand_logo_url(
            brand_id=brand_id,
            logo_url=None,
            user_email=current_user.get("email")
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update brand logo URL")
        
        logger.info(f"Deleted logo for brand {brand_id} by user {current_user.get('email')}")
        
        return {
            "brand_id": brand_id,
            "message": "Logo deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting logo for brand {brand_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting logo: {str(e)}")

@router.put("/data/brands/{brand_id}/theme")
@handle_api_errors(context="updating brand theme")
async def update_brand_theme(
    brand_id: int,
    request: ThemeUpdateRequest,
    current_user: dict = Depends(get_current_user_v2),
    db: Session = Depends(get_db)
):
    """Update brand theme configuration"""
    from app.services.websocket_manager import websocket_manager
    from datetime import datetime
    
    try:
        supabase = SupabaseService(db=db)
        
        # Get current brand to check version using SQLAlchemy
        brand = supabase.get_brand_by_id(brand_id)
        
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        current_version = brand.get("version", 1)
        
        # Version conflict check
        if request.version is not None and request.version != current_version:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "conflict",
                    "message": "Resource was modified by another user. Please refresh and try again.",
                    "current_version": current_version,
                    "current_data": {
                        "theme": brand.get("theme"),
                        "last_modified_by": brand.get("last_modified_by")
                    }
                }
            )
        
        # Get existing theme or initialize empty dict
        existing_theme = brand.get("theme") or {}
        if not isinstance(existing_theme, dict):
            existing_theme = {}
        
        # Build updated theme
        updated_theme = existing_theme.copy()
        if request.primary_color is not None:
            updated_theme["primary_color"] = request.primary_color
        if request.secondary_color is not None:
            updated_theme["secondary_color"] = request.secondary_color
        if request.accent_color is not None:
            updated_theme["accent_color"] = request.accent_color
        if request.font_family is not None:
            updated_theme["font_family"] = request.font_family
        if request.custom is not None:
            updated_theme["custom"] = request.custom
        
        # Update brand theme using SQLAlchemy method
        success = supabase.update_brand_theme(
            brand_id=brand_id,
            theme=updated_theme,
            user_email=current_user.get("email")
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update brand theme")
        
        # Get updated version using SQLAlchemy
        updated_brand = supabase.get_brand_by_id(brand_id)
        updated_version = updated_brand.get("version", 1) if updated_brand else 1
        
        logger.info(f"Updated theme for brand {brand_id} by user {current_user.get('email')}, version={updated_version}")
        
        # Broadcast WebSocket notification
        try:
            await websocket_manager.notify_resource_updated(
                resource_type="brand",
                resource_id=brand_id,
                updated_by=current_user.get("email"),
                updated_at=datetime.utcnow().isoformat() + "Z",
                version=updated_version,
                exclude_user_id=current_user.get("id")
            )
        except Exception as ws_error:
            logger.warning(f"Failed to send WebSocket notification: {str(ws_error)}")
        
        return {
            "brand_id": brand_id,
            "theme": updated_theme,
            "version": updated_version,
            "message": "Theme updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating theme for brand {brand_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating theme: {str(e)}")

# =====================================================
# Client Management Endpoints
# =====================================================


@router.get("/data/clients")
@handle_api_errors(context="fetching clients")
async def get_clients(
    page: Optional[int] = Query(1, description="Page number (1-indexed)"),
    page_size: Optional[int] = Query(25, description="Number of records per page"),
    search: Optional[str] = Query(None, description="Search by company name"),
    ga4_assigned: Optional[bool] = Query(None, description="Filter by GA4 assignment (true=assigned, false=not assigned)"),
    scrunch_assigned: Optional[bool] = Query(None, description="Filter by Scrunch assignment (true=assigned, false=not assigned)"),
    active: Optional[str] = Query("active", description="Filter by active status: 'active' (default), 'inactive', or 'all'"),
    current_user: dict = Depends(get_current_user_v2),
    db: Session = Depends(get_db)
):
    """Get all clients from database with pagination, search, and filters"""
    try:
        supabase = SupabaseService(db=db)
        
        # Calculate offset from page
        offset = (page - 1) * page_size if page > 0 else 0
        
        # Build query using SQLAlchemy Core
        clients_table = supabase._get_table("clients")
        query = select(clients_table)
        
        # Apply search filter if provided
        if search and search.strip():
            search_term = f"%{search.strip()}%"
            query = query.where(clients_table.c.company_name.ilike(search_term))
        
        # Apply GA4 filter
        if ga4_assigned is not None:
            if ga4_assigned:
                query = query.where(clients_table.c.ga4_property_id.isnot(None))
                query = query.where(clients_table.c.ga4_property_id != '')
            else:
                query = query.where(
                    or_(
                        clients_table.c.ga4_property_id.is_(None),
                        clients_table.c.ga4_property_id == ''
                    )
                )
        
        # Apply Scrunch filter
        if scrunch_assigned is not None:
            if scrunch_assigned:
                query = query.where(clients_table.c.scrunch_brand_id.isnot(None))
            else:
                query = query.where(clients_table.c.scrunch_brand_id.is_(None))
        
        # Apply is_active filter
        # active can be: "active" (default), "inactive", or "all"
        if active == "inactive":
            query = query.where(clients_table.c.is_active == False)
        elif active == "all":
            # Don't filter by is_active - show all clients
            pass
        else:
            # Default to "active" - show only active clients
            query = query.where(clients_table.c.is_active == True)
        
        # Get total count
        count_query = select(func.count()).select_from(query.alias())
        total_count = supabase.db.execute(count_query).scalar()
        
        # Order by company name for consistent results
        query = query.order_by(clients_table.c.company_name.asc())
        
        # Apply pagination
        query = query.offset(offset).limit(page_size)
        
        # Execute query
        result = supabase.db.execute(query)
        items = [dict(row._mapping) for row in result]
        
        # For each client, get campaigns and keyword count
        for item in items:
            client_id = item.get("id")
            
            # Get campaigns for this client
            campaigns = supabase.get_client_campaigns(client_id)
            item["client_campaigns"] = campaigns
            
            # Get keyword count from campaigns
            keywords_count = 0
            # get_client_campaigns returns campaigns with "id" key, not "campaign_id"
            campaign_ids = [c.get("id") for c in campaigns if c.get("id")]
            
            if campaign_ids:
                keywords_table = supabase._get_table("agency_analytics_keywords")
                keywords_query = select(func.count()).select_from(
                    keywords_table
                ).where(keywords_table.c.campaign_id.in_(campaign_ids))
                keywords_result = supabase.db.execute(keywords_query)
                keywords_count = keywords_result.scalar() or 0
            
            item["keywords_count"] = keywords_count
        
        # Calculate pagination metadata
        total_pages = (total_count + page_size - 1) // page_size if page_size > 0 else 1
        
        return {
            "items": items if isinstance(items, list) else [],
            "count": len(items) if isinstance(items, list) else 0,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_previous": page > 1
        }
    except Exception as e:
        logger.error(f"Error fetching clients: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/data/clients/{client_id}")
@handle_api_errors(context="soft deleting client")
async def delete_client(
    client_id: int,
    current_user: dict = Depends(get_current_user_v2),
    db: Session = Depends(get_db)
):
    """Soft delete a client by setting is_active to false"""
    try:
        supabase = SupabaseService(db=db)
        
        # Get client to verify it exists
        client = supabase.get_client_by_id(client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Check if already deleted
        if not client.get("is_active", True):
            raise HTTPException(status_code=400, detail="Client is already deleted")
        
        # Soft delete by setting is_active to false
        clients_table = supabase._get_table("clients")
        update_stmt = update(clients_table).where(
            clients_table.c.id == client_id
        ).values(
            is_active=False,
            updated_at=datetime.now(),
            updated_by=current_user.get("email")
        )
        supabase.db.execute(update_stmt)
        supabase.db.commit()
        
        logger.info(f"Soft deleted client {client_id} by user {current_user.get('email')}")
        
        return {
            "client_id": client_id,
            "message": "Client deleted successfully",
            "is_active": False
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error soft deleting client {client_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/clients/{client_id}")
@handle_api_errors(context="fetching client")
async def get_client(
    client_id: int,
    current_user: dict = Depends(get_current_user_v2),
    db: Session = Depends(get_db)
):
    """Get a specific client by ID"""
    try:
        supabase = SupabaseService(db=db)
        client = supabase.get_client_by_id(client_id)
        
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Get campaigns for this client
        campaigns = supabase.get_client_campaigns(client_id)
        client["client_campaigns"] = campaigns
        
        return client
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching client: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/clients/slug/{url_slug}")
@handle_api_errors(context="fetching client by slug")
async def get_client_by_slug(
    url_slug: str,
    db: Session = Depends(get_db)
):
    """Get client by URL slug (public access for whitelabeled reports)"""
    try:
        supabase = SupabaseService(db=db)
        link = supabase.get_dashboard_link_by_slug(url_slug)
        if link:
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
            client = supabase.get_client_by_id(link["client_id"])
            if not client:
                raise HTTPException(status_code=404, detail="Client not found for dashboard link")
            client["dashboard_link"] = link
            return client

        client = supabase.get_client_by_slug(url_slug)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        return client
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching client by slug: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class ClientMappingUpdateRequest(BaseModel):
    ga4_property_id: Optional[str] = None
    scrunch_brand_id: Optional[int] = None
    version: Optional[int] = None  # Version for optimistic locking

@router.put("/data/clients/{client_id}/mappings")
@handle_api_errors(context="updating client mappings")
async def update_client_mappings(
    client_id: int,
    request: ClientMappingUpdateRequest,
    current_user: dict = Depends(get_current_user_v2),
    db: Session = Depends(get_db)
):
    """Update client mappings (GA4 property ID and/or Scrunch brand ID)"""
    from app.services.websocket_manager import websocket_manager
    from datetime import datetime
    from sqlalchemy import select, update, text
    
    try:
        supabase = SupabaseService(db=db)
        
        # Get current client to check version using SQLAlchemy Core
        table = supabase._get_table("clients")
        query = select(
            table.c.id,
            table.c.version,
            table.c.ga4_property_id,
            table.c.scrunch_brand_id,
            table.c.last_modified_by
        ).where(table.c.id == client_id).limit(1)
        
        result = db.execute(query)
        current_client_row = result.first()
        
        if not current_client_row:
            raise HTTPException(status_code=404, detail="Client not found")
        
        current_client = dict(current_client_row._mapping)
        current_version = current_client.get("version", 1)
        
        # Version conflict check
        if request.version is not None and request.version != current_version:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "conflict",
                    "message": "Resource was modified by another user. Please refresh and try again.",
                    "current_version": current_version,
                    "current_data": {
                        "ga4_property_id": current_client.get("ga4_property_id"),
                        "scrunch_brand_id": current_client.get("scrunch_brand_id"),
                        "last_modified_by": current_client.get("last_modified_by")
                    }
                }
            )
        
        # Update client mappings
        success = supabase.update_client_mapping(
            client_id=client_id,
            ga4_property_id=request.ga4_property_id,
            scrunch_brand_id=request.scrunch_brand_id,
            user_email=current_user.get("email")
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update client mappings")
        
        # Get updated version using SQLAlchemy Core
        updated_query = select(table.c.version).where(table.c.id == client_id).limit(1)
        updated_result = db.execute(updated_query)
        updated_row = updated_result.first()
        updated_version = updated_row.version if updated_row else 1
        
        # Broadcast WebSocket notification
        try:
            await websocket_manager.notify_resource_updated(
                resource_type="client",
                resource_id=client_id,
                updated_by=current_user.get("email"),
                updated_at=datetime.utcnow().isoformat() + "Z",
                version=updated_version,
                exclude_user_id=current_user.get("id")
            )
        except Exception as ws_error:
            logger.warning(f"Failed to send WebSocket notification: {str(ws_error)}")
        
        return {
            "status": "success",
            "message": "Client mappings updated successfully",
            "version": updated_version
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating client mappings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class ClientThemeUpdateRequest(BaseModel):
    theme_color: Optional[str] = None
    logo_url: Optional[str] = None
    secondary_color: Optional[str] = None
    font_family: Optional[str] = None
    favicon_url: Optional[str] = None
    report_title: Optional[str] = None
    custom_css: Optional[str] = None
    footer_text: Optional[str] = None
    header_text: Optional[str] = None
    version: Optional[int] = None  # Version for optimistic locking

@router.put("/data/clients/{client_id}/theme")
@handle_api_errors(context="updating client theme")
async def update_client_theme(
    client_id: int,
    request: ClientThemeUpdateRequest,
    current_user: dict = Depends(get_current_user_v2),
    db: Session = Depends(get_db)
):
    """Update client theme and branding"""
    from app.services.websocket_manager import websocket_manager
    from datetime import datetime
    
    try:
        supabase = SupabaseService(db=db)
        
        # Get current client to check version using SQLAlchemy
        client = supabase.get_client_by_id(client_id)
        
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        current_version = client.get("version", 1)
        
        # Version conflict check
        if request.version is not None and request.version != current_version:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "conflict",
                    "message": "Resource was modified by another user. Please refresh and try again.",
                    "current_version": current_version,
                    "current_data": {
                        "theme_color": client.get("theme_color"),
                        "logo_url": client.get("logo_url"),
                        "secondary_color": client.get("secondary_color"),
                        "font_family": client.get("font_family"),
                        "favicon_url": client.get("favicon_url"),
                        "report_title": client.get("report_title"),
                        "custom_css": client.get("custom_css"),
                        "footer_text": client.get("footer_text"),
                        "header_text": client.get("header_text"),
                        "last_modified_by": client.get("last_modified_by")
                    }
                }
            )
        
        theme_data = {
            "theme_color": request.theme_color,
            "logo_url": request.logo_url,
            "secondary_color": request.secondary_color,
            "font_family": request.font_family,
            "favicon_url": request.favicon_url,
            "report_title": request.report_title,
            "custom_css": request.custom_css,
            "footer_text": request.footer_text,
            "header_text": request.header_text,
        }
        
        success = supabase.update_client_theme(
            client_id=client_id,
            theme_data=theme_data,
            user_email=current_user.get("email")
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update client theme")
        
        # Get updated version using SQLAlchemy
        updated_client = supabase.get_client_by_id(client_id)
        updated_version = updated_client.get("version", 1) if updated_client else 1
        
        # Broadcast WebSocket notification
        try:
            await websocket_manager.notify_resource_updated(
                resource_type="client",
                resource_id=client_id,
                updated_by=current_user.get("email"),
                updated_at=datetime.utcnow().isoformat() + "Z",
                version=updated_version,
                exclude_user_id=current_user.get("id")
            )
        except Exception as ws_error:
            logger.warning(f"Failed to send WebSocket notification: {str(ws_error)}")
        
        return {
            "status": "success",
            "message": "Client theme updated successfully",
            "version": updated_version
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating client theme: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class ClientReportDatesUpdateRequest(BaseModel):
    report_start_date: Optional[str] = None  # YYYY-MM-DD format
    report_end_date: Optional[str] = None  # YYYY-MM-DD format
    version: Optional[int] = None  # Version for optimistic locking

@router.put("/data/clients/{client_id}/report-dates")
@handle_api_errors(context="updating client report dates")
async def update_client_report_dates(
    client_id: int,
    request: ClientReportDatesUpdateRequest,
    current_user: dict = Depends(get_current_user_v2),
    db: Session = Depends(get_db)
):
    """Update client report date range for public dashboard"""
    from app.services.websocket_manager import websocket_manager
    from datetime import datetime, date
    
    try:
        supabase = SupabaseService(db=db)
        
        # Get current client to check version using SQLAlchemy
        client = supabase.get_client_by_id(client_id)
        
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        current_version = client.get("version", 1)
        
        # Version conflict check
        if request.version is not None and request.version != current_version:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "conflict",
                    "message": "Resource was modified by another user. Please refresh and try again.",
                    "current_version": current_version,
                    "current_data": {
                        "report_start_date": client.get("report_start_date"),
                        "report_end_date": client.get("report_end_date"),
                        "last_modified_by": client.get("last_modified_by")
                    }
                }
            )
        
        # Validate date format if provided
        report_start_date = None
        report_end_date = None
        
        if request.report_start_date:
            try:
                report_start_date = datetime.strptime(request.report_start_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid report_start_date format. Use YYYY-MM-DD.")
        
        if request.report_end_date:
            try:
                report_end_date = datetime.strptime(request.report_end_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid report_end_date format. Use YYYY-MM-DD.")
        
        # Validate date range
        if report_start_date and report_end_date and report_start_date > report_end_date:
            raise HTTPException(
                status_code=400,
                detail="report_start_date must be before or equal to report_end_date"
            )
        
        success = supabase.update_client_report_dates(
            client_id=client_id,
            report_start_date=report_start_date,
            report_end_date=report_end_date,
            user_email=current_user.get("email")
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update client report dates")
        
        # Get updated version using SQLAlchemy
        updated_client = supabase.get_client_by_id(client_id)
        updated_version = updated_client.get("version", 1) if updated_client else 1
        
        # Broadcast WebSocket notification
        try:
            await websocket_manager.notify_resource_updated(
                resource_type="client",
                resource_id=client_id,
                updated_by=current_user.get("email"),
                updated_at=datetime.utcnow().isoformat() + "Z",
                version=updated_version,
                exclude_user_id=current_user.get("id")
            )
        except Exception as ws_error:
            logger.warning(f"Failed to send WebSocket notification: {str(ws_error)}")
        
        return {
            "status": "success",
            "message": "Client report dates updated successfully",
            "version": updated_version
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating client report dates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/data/clients/{client_id}/logo")
@handle_api_errors(context="uploading client logo")
async def upload_client_logo(
    client_id: int,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user_v2),
    db: Session = Depends(get_db)
):
    """Upload client logo to Supabase Storage"""
    try:
        # Check if client exists using SQLAlchemy
        supabase = SupabaseService(db=db)
        client = supabase.get_client_by_id(client_id)
        
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Create Supabase client with service role key for storage operations
        # Service role key is required to bypass RLS for storage uploads
        from app.core.database import get_supabase_service_role_client
        storage_client = get_supabase_service_role_client()
        
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read file content
        file_content = await file.read()
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'png'
        
        # Generate unique filename
        filename = f"client-{client_id}-{uuid.uuid4().hex[:8]}.{file_extension}"
        file_path = filename
        
        # Upload to Supabase Storage using Supabase client
        # The bucket name is 'brand-logos', file path is just the filename
        try:
            logger.info(f"Uploading client logo to storage: bucket=brand-logos, path={file_path}, size={len(file_content)} bytes, content-type={file.content_type}")
            
            responseBuckets = storage_client.storage.list_buckets()
            logger.info(f"Buckets: {responseBuckets}")
            # Upload using Supabase storage client
            storage_response = storage_client.storage.from_("brand-logos").upload(
                file=file_content,
                path=file_path,
                file_options={
                    "content-type": file.content_type,
                    "cache-control": "3600",
                    "upsert": "true"
                }
            )
            
            logger.info(f"Storage upload successful: {storage_response}")
            
            # Get public URL using Supabase client
            try:
                public_url_response = storage_client.storage.from_("brand-logos").get_public_url(file_path)
                if isinstance(public_url_response, str):
                    logo_url = public_url_response
                elif hasattr(public_url_response, 'get'):
                    logo_url = public_url_response.get('publicUrl', '')
                else:
                    logo_url = str(public_url_response)
            except Exception as url_error:
                logger.warning(f"Could not get public URL from response: {url_error}")
                logo_url = None
            
            # Construct public URL manually if Supabase client method fails
            if not logo_url:
                project_ref = settings.SUPABASE_URL.replace('https://', '').replace('.supabase.co', '')
                logo_url = f"https://{project_ref}.supabase.co/storage/v1/object/public/brand-logos/{file_path}"
            
            logger.info(f"Final logo URL: {logo_url}")
            
        except Exception as storage_error:
            logger.error(f"Storage error: {str(storage_error)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload to storage. Error: {str(storage_error)}"
            )
        
        # Update client with logo URL using SQLAlchemy
        theme_data = {"logo_url": logo_url}
        success = supabase.update_client_theme(
            client_id=client_id,
            theme_data=theme_data,
            user_email=current_user.get("email")
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update client logo URL")
        
        logger.info(f"Uploaded logo for client {client_id} by user {current_user.get('email')}")
        
        return {
            "client_id": client_id,
            "logo_url": logo_url,
            "message": "Logo uploaded successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading logo for client {client_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading logo: {str(e)}")

@router.delete("/data/clients/{client_id}/logo")
@handle_api_errors(context="deleting client logo")
async def delete_client_logo(
    client_id: int,
    current_user: dict = Depends(get_current_user_v2),
    db: Session = Depends(get_db)
):
    """Delete client logo"""
    try:
        supabase = SupabaseService(db=db)
        
        # Check if client exists and get current logo using SQLAlchemy
        client = supabase.get_client_by_id(client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        logo_url = client.get("logo_url")
        
        # Delete from storage if URL exists (storage still uses Supabase)
        if logo_url:
            try:
                from app.core.database import get_supabase_client
                # Use service role client for storage operations (bypasses RLS)
                from app.core.database import get_supabase_service_role_client
                storage_client = get_supabase_service_role_client()
                
                # Extract file path from URL
                if "brand-logos/" in logo_url:
                    file_path = logo_url.split("brand-logos/")[-1].split("?")[0]
                elif "/object/public/brand-logos/" in logo_url:
                    file_path = logo_url.split("/object/public/brand-logos/")[-1].split("?")[0]
                else:
                    file_path = logo_url.split("/")[-1].split("?")[0]
                
                if file_path:
                    logger.info(f"Deleting file from storage: {file_path}")
                    storage_client.storage.from_("brand-logos").remove([file_path])
            except Exception as storage_error:
                logger.warning(f"Failed to delete logo from storage: {str(storage_error)}")
        
        # Update client to remove logo URL using SQLAlchemy
        theme_data = {"logo_url": None}
        success = supabase.update_client_theme(
            client_id=client_id,
            theme_data=theme_data,
            user_email=current_user.get("email")
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update client logo URL")
        
        logger.info(f"Deleted logo for client {client_id} by user {current_user.get('email')}")
        
        return {
            "client_id": client_id,
            "message": "Logo deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting logo for client {client_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting logo: {str(e)}")


@router.get("/data/clients/{client_id}/campaigns")
@handle_api_errors(context="fetching client campaigns")
async def get_client_campaigns(
    client_id: int,
    current_user: dict = Depends(get_current_user_v2),
    db: Session = Depends(get_db)
):
    """Get all campaigns linked to a client"""
    try:
        supabase = SupabaseService(db=db)
        
        # Check if client exists using SQLAlchemy
        client = supabase.get_client_by_id(client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        campaigns = supabase.get_client_campaigns(client_id)
        
        return {
            "client_id": client_id,
            "campaigns": campaigns,
            "count": len(campaigns)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching client campaigns: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/data/clients/{client_id}/campaigns/{campaign_id}/link")
@handle_api_errors(context="linking campaign to client")
async def link_client_campaign(
    client_id: int,
    campaign_id: int,
    is_primary: Optional[bool] = Query(False, description="Mark as primary campaign"),
    current_user: dict = Depends(get_current_user_v2),
    db: Session = Depends(get_db)
):
    """Link a campaign to a client"""
    try:
        supabase = SupabaseService(db=db)
        
        # Check if client exists using SQLAlchemy
        client = supabase.get_client_by_id(client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Check if campaign exists using SQLAlchemy Core
        campaigns_table = supabase._get_table("agency_analytics_campaigns")
        campaign_query = select(campaigns_table.c.id).where(campaigns_table.c.id == campaign_id).limit(1)
        campaign_result = db.execute(campaign_query)
        campaign_row = campaign_result.first()
        
        if not campaign_row:
            raise HTTPException(status_code=404, detail="Agency Analytics campaign not found")
        
        # Use the existing SQLAlchemy method to link campaign
        supabase._link_campaign_to_client(campaign_id, client_id, is_primary)
        
        logger.info(f"Linked campaign {campaign_id} to client {client_id} by user {current_user.get('email')}")
        
        return {
            "client_id": client_id,
            "campaign_id": campaign_id,
            "is_primary": is_primary,
            "message": "Campaign linked successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error linking campaign to client: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/data/clients/{client_id}/campaigns/{campaign_id}/link")
@handle_api_errors(context="unlinking campaign from client")
async def unlink_client_campaign(
    client_id: int,
    campaign_id: int,
    current_user: dict = Depends(get_current_user_v2),
    db: Session = Depends(get_db)
):
    """Unlink a campaign from a client"""
    try:
        supabase = SupabaseService(db=db)
        
        # Check if client exists using SQLAlchemy
        client = supabase.get_client_by_id(client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Check if link exists using SQLAlchemy Core
        client_campaigns_table = supabase._get_table("client_campaigns")
        link_query = select(client_campaigns_table).where(
            and_(
                client_campaigns_table.c.client_id == client_id,
                client_campaigns_table.c.campaign_id == campaign_id
            )
        ).limit(1)
        link_result = db.execute(link_query)
        existing_link = link_result.first()
        
        if not existing_link:
            raise HTTPException(status_code=404, detail="Campaign is not linked to this client")
        
        # Delete the link using SQLAlchemy Core
        delete_stmt = delete(client_campaigns_table).where(
            and_(
                client_campaigns_table.c.client_id == client_id,
                client_campaigns_table.c.campaign_id == campaign_id
            )
        )
        db.execute(delete_stmt)
        db.commit()
        
        logger.info(f"Unlinked campaign {campaign_id} from client {client_id} by user {current_user.get('email')}")
        
        return {
            "client_id": client_id,
            "campaign_id": campaign_id,
            "message": "Campaign unlinked successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unlinking campaign from client: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



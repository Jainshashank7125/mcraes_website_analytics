from fastapi import APIRouter, HTTPException, Depends, Body, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import logging
import json
from datetime import datetime
from sqlalchemy.orm import Session
from app.services.openai_client import OpenAIClient
from app.core.error_utils import handle_api_errors
from app.api.auth_v2 import get_current_user_v2
from app.db.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()
openai_client = OpenAIClient()

# Request/Response Models
class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role: 'system', 'user', or 'assistant'")
    content: str = Field(..., description="Message content")

class ChatCompletionRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., description="List of messages in the conversation")
    model: str = Field(default="gpt-4o-mini", description="Model to use (e.g., gpt-4o-mini, gpt-4, gpt-3.5-turbo)")
    temperature: float = Field(default=0.7, ge=0, le=2, description="Sampling temperature (0-2)")
    max_tokens: Optional[int] = Field(default=None, description="Maximum tokens to generate")
    stream: bool = Field(default=False, description="Whether to stream the response")

class TextCompletionRequest(BaseModel):
    prompt: str = Field(..., description="The prompt text")
    model: str = Field(default="gpt-3.5-turbo-instruct", description="Model to use")
    temperature: float = Field(default=0.7, ge=0, le=2, description="Sampling temperature (0-2)")
    max_tokens: Optional[int] = Field(default=None, description="Maximum tokens to generate")

class EmbeddingRequest(BaseModel):
    input: str | List[str] = Field(..., description="Text or list of texts to embed")
    model: str = Field(default="text-embedding-3-small", description="Embedding model to use")

@router.post("/openai/chat/completions")
@handle_api_errors(context="creating chat completion")
async def create_chat_completion(
    request: ChatCompletionRequest,
    current_user: dict = Depends(get_current_user_v2)
):
    """
    Create a chat completion using OpenAI API
    
    This endpoint allows you to have a conversation with OpenAI's chat models.
    """
    try:
        # Convert Pydantic models to dict format expected by OpenAI API
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        result = await openai_client.create_chat_completion(
            messages=messages,
            model=request.model,
            # temperature=request.temperature,
            # max_tokens=request.max_tokens,
            stream=request.stream
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating chat completion: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating chat completion: {str(e)}")

@router.post("/openai/completions")
@handle_api_errors(context="creating text completion")
async def create_completion(
    request: TextCompletionRequest,
    current_user: dict = Depends(get_current_user_v2)
):
    """
    Create a text completion using OpenAI API (legacy endpoint)
    
    This endpoint uses the older completion API for text generation.
    """
    try:
        result = await openai_client.create_completion(
            prompt=request.prompt,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating text completion: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating text completion: {str(e)}")

@router.post("/openai/embeddings")
@handle_api_errors(context="creating embeddings")
async def create_embedding(
    request: EmbeddingRequest,
    current_user: dict = Depends(get_current_user_v2)
):
    """
    Create embeddings using OpenAI API
    
    This endpoint generates vector embeddings for text, useful for semantic search,
    clustering, and other ML applications.
    """
    try:
        result = await openai_client.create_embedding(
            input_text=request.input,
            model=request.model
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating embeddings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating embeddings: {str(e)}")

@router.get("/openai/models")
@handle_api_errors(context="listing OpenAI models")
async def list_models(
    current_user: dict = Depends(get_current_user_v2)
):
    """
    List all available OpenAI models
    
    Returns a list of models available through the OpenAI API.
    """
    try:
        result = await openai_client.list_models()
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing models: {str(e)}")

@router.get("/openai/models/{model_id}")
@handle_api_errors(context="getting model information")
async def get_model(
    model_id: str,
    current_user: dict = Depends(get_current_user_v2)
):
    """
    Get information about a specific OpenAI model
    
    Returns detailed information about the specified model.
    """
    try:
        result = await openai_client.get_model(model_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting model information: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting model information: {str(e)}")

class MetricReviewRequest(BaseModel):
    brand_id: int = Field(..., description="Brand ID to analyze")
    data_source: str = Field(..., description="Data source to review: 'ga4', 'agency_analytics', or 'scrunch'")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")

class OverallOverviewRequest(BaseModel):
    client_id: Optional[int] = Field(None, description="Client ID to analyze (client-centric)")
    brand_id: Optional[int] = Field(None, description="Brand ID to analyze (fallback if client_id not provided)")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")

@router.post("/openai/metrics/review")
@handle_api_errors(context="generating metric review")
async def generate_metric_review(
    request: MetricReviewRequest,
    current_user: dict = Depends(get_current_user_v2)
):
    """
    Generate an AI-powered review of metrics for a specific data source
    
    Analyzes KPIs from the specified data source (GA4, Agency Analytics, or Scrunch)
    and generates insights about what's performing well, trends, and recommendations.
    """
    try:
        # Validate data source
        valid_sources = ["ga4", "agency_analytics", "scrunch"]
        if request.data_source.lower() not in valid_sources:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid data source. Must be one of: {', '.join(valid_sources)}"
            )
        
        # Import the dashboard function to fetch KPIs
        from app.api.data import get_reporting_dashboard
        
        # Fetch dashboard data to get KPIs
        dashboard_data = await get_reporting_dashboard(
            request.brand_id,
            request.start_date,
            request.end_date
        )
        
        # Filter KPIs by data source
        source_kpis = {}
        source_mapping = {
            "ga4": "GA4",
            "agency_analytics": "AgencyAnalytics",
            "scrunch": "Scrunch"
        }
        target_source = source_mapping[request.data_source.lower()]
        
        if not dashboard_data.get("kpis"):
            raise HTTPException(
                status_code=404,
                detail=f"No KPIs found for brand {request.brand_id}"
            )
        
        # Filter KPIs by source
        for kpi_key, kpi_data in dashboard_data["kpis"].items():
            if kpi_data.get("source") == target_source:
                source_kpis[kpi_key] = kpi_data
        
        if not source_kpis:
            raise HTTPException(
                status_code=404,
                detail=f"No {request.data_source} KPIs found for this brand. Make sure the data source is configured."
            )
        
        # Prepare metrics summary for OpenAI
        metrics_summary = []
        for kpi_key, kpi_data in source_kpis.items():
            metric_info = {
                "metric": kpi_data.get("label", kpi_key),
                "value": kpi_data.get("value"),
                "change": kpi_data.get("change"),
                "format": kpi_data.get("format", "number")
            }
            metrics_summary.append(metric_info)
        
        # Create prompt for OpenAI
        data_source_names = {
            "ga4": "Google Analytics 4",
            "agency_analytics": "Agency Analytics (SEO)",
            "scrunch": "Scrunch AI"
        }
        source_name = data_source_names[request.data_source.lower()]
        
        prompt = f"""You are an expert analytics consultant reviewing {source_name} metrics for a client.
 
Analyze the following metrics and provide a brief summary in pointers focusing on:
1. What's performing well (highlight strong metrics and positive trends)
2. Key insights and patterns
3. Notable changes from the previous period

 
Metrics Data:
{format_metrics_for_prompt(metrics_summary)}
 
Date Range: {dashboard_data.get('date_range', {}).get('start_date', 'N/A')} to {dashboard_data.get('date_range', {}).get('end_date', 'N/A')}
 
Provide a clear, professional review (4-5 bullet points) that highlights what's good and performing well. Be specific about the metrics and their significance. Use a positive, analytical tone."""

        
        # Generate review using OpenAI
        messages = [
            {
                "role": "system",
                "content": "You are an expert analytics consultant who provides clear, insightful reviews of marketing and analytics metrics. Focus on positive performance indicators and actionable insights."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        result = await openai_client.create_chat_completion(
            messages=messages,
            model="gpt-5-mini",
        )
        
        # Extract the review text
        review_text = ""
        if result.get("choices") and len(result["choices"]) > 0:
            review_text = result["choices"][0].get("message", {}).get("content", "")
        
        return {
            "brand_id": request.brand_id,
            "brand_name": dashboard_data.get("brand_name"),
            "data_source": request.data_source,
            "date_range": dashboard_data.get("date_range"),
            "metrics_analyzed": len(source_kpis),
            "review": review_text,
            "metrics": metrics_summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating metric review: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating metric review: {str(e)}")

@router.post("/openai/metrics/overview")
@handle_api_errors(context="generating overall metrics overview")
async def generate_overall_overview(
    request: OverallOverviewRequest,
    db: Session = Depends(get_db)
):
    """
    Generate an AI-powered overall overview of all metrics from all data sources
    
    Analyzes all KPIs from GA4, Agency Analytics, and Scrunch together
    to provide a comprehensive overview of overall performance.
    
    This endpoint is accessible without authentication to support public reporting views.
    """
    try:
        logger.info(f"[Executive Summary] Request received - client_id={request.client_id}, brand_id={request.brand_id}, start_date={request.start_date}, end_date={request.end_date}")
        
        # Validate that at least one identifier is provided
        client_id = request.client_id if request.client_id is not None else None
        brand_id = request.brand_id if request.brand_id is not None else None
        
        # Try to derive missing identifier if possible
        if client_id and not brand_id:
            # Try to get brand_id from client
            from app.services.supabase_service import SupabaseService
            supabase = SupabaseService(db=db)
            client = supabase.get_client_by_id(client_id)
            if client and client.get("scrunch_brand_id"):
                brand_id = client.get("scrunch_brand_id")
                logger.info(f"[Executive Summary] Derived brand_id={brand_id} from client_id={client_id}")
        
        if not client_id and not brand_id:
            logger.error("[Executive Summary] Validation failed: Neither client_id nor brand_id provided")
            raise HTTPException(
                status_code=400,
                detail="Either client_id or brand_id must be provided. Received: client_id=None, brand_id=None"
            )
        
        # Import the dashboard function to fetch KPIs
        from app.api.data import (
            get_reporting_dashboard, 
            get_reporting_dashboard_by_client,
            get_scrunch_dashboard_data
        )
        
        # Fetch dashboard data to get all KPIs (GA4 and Agency Analytics)
        # NOTE: Main dashboard endpoint skips Scrunch data for performance, so we fetch it separately
        logger.info(f"[Executive Summary] Fetching dashboard data for {'client' if client_id else 'brand'} {client_id or brand_id}")
        if client_id:
            # Use client-based endpoint
            dashboard_data = await get_reporting_dashboard_by_client(
                client_id,
                request.start_date,
                request.end_date,
                db=db
            )
        else:
            # Use brand-based endpoint
            dashboard_data = await get_reporting_dashboard(
                brand_id,
                request.start_date,
                request.end_date,
                client_id=None,
                db=db
            )
        
        # Handle case where dashboard_data might be None or empty
        if not dashboard_data:
            logger.warning(f"[Executive Summary] No dashboard data returned for {'client' if client_id else 'brand'} {client_id or brand_id}")
            raise HTTPException(
                status_code=404,
                detail=f"No data found for {'client' if client_id else 'brand'} {client_id or brand_id}"
            )
        
        # Fetch Scrunch data separately (main endpoint skips it for performance)
        scrunch_data = None
        try:
            logger.info(f"[Executive Summary] Fetching Scrunch data separately for {'client' if client_id else 'brand'} {client_id or brand_id}")
            if client_id:
                # Get client to find scrunch_brand_id
                from app.services.supabase_service import SupabaseService
                supabase = SupabaseService(db=db)
                client = supabase.get_client_by_id(client_id)
                if client and client.get("scrunch_brand_id"):
                    scrunch_brand_id = client.get("scrunch_brand_id")
                    scrunch_data = await get_scrunch_dashboard_data(
                        scrunch_brand_id,
                        request.start_date,
                        request.end_date,
                        client_id=client_id,
                        db=db
                    )
                    logger.info(f"[Executive Summary] Scrunch data fetched - {len(scrunch_data.get('kpis', {}))} KPIs found")
                else:
                    logger.warning(f"[Executive Summary] Client {client_id} has no scrunch_brand_id - skipping Scrunch data")
            else:
                # Use brand_id directly
                scrunch_data = await get_scrunch_dashboard_data(
                    brand_id,
                    request.start_date,
                    request.end_date,
                    client_id=None,
                    db=db
                )
                logger.info(f"[Executive Summary] Scrunch data fetched - {len(scrunch_data.get('kpis', {}))} KPIs found")
        except Exception as e:
            logger.warning(f"[Executive Summary] Error fetching Scrunch data (non-fatal): {str(e)}")
            # Don't fail if Scrunch data can't be fetched - continue with other data sources
            scrunch_data = None
        
        # Merge Scrunch KPIs with main dashboard KPIs
        all_kpis = dashboard_data.get("kpis", {}).copy()  # Start with main dashboard KPIs
        if scrunch_data and scrunch_data.get("kpis"):
            # Merge Scrunch KPIs into all_kpis
            scrunch_kpis = scrunch_data.get("kpis", {})
            all_kpis.update(scrunch_kpis)
            logger.info(f"[Executive Summary] Merged Scrunch KPIs - Added {len(scrunch_kpis)} Scrunch KPIs to dashboard data")
        
        if not all_kpis:
            logger.warning(f"[Executive Summary] No KPIs found in dashboard data for {'client' if client_id else 'brand'} {client_id or brand_id}")
            raise HTTPException(
                status_code=404,
                detail=f"No KPIs found for {'client' if client_id else 'brand'} {client_id or brand_id}"
            )
        
        logger.info(f"[Executive Summary] Dashboard data fetched successfully - Total KPIs: {len(all_kpis)} (Main: {len(dashboard_data.get('kpis', {}))}, Scrunch: {len(scrunch_data.get('kpis', {})) if scrunch_data else 0})")
        
        # ========== STRUCTURE DATA BY SECTIONS WITH KPIs AND CHARTS ==========
        # Organize data in a structured format with sections, KPIs, and chart data
        structured_data = {
            "GA4": {
                "section_name": "Google Analytics 4 (Web Analytics)",
                "kpis": [],
                "charts": {}
            },
            "AgencyAnalytics": {
                "section_name": "Agency Analytics (SEO Rankings)",
                "kpis": [],
                "charts": {}
            },
            "Scrunch": {
                "section_name": "Scrunch AI (Brand Mentions & Sentiment)",
                "kpis": [],
                "charts": {}
            }
        }
        
        # Group KPIs by source
        for kpi_key, kpi_data in all_kpis.items():
            source = kpi_data.get("source", "Unknown")
            if source in structured_data:
                metric_info = {
                    "key": kpi_key,
                    "label": kpi_data.get("label", kpi_key),
                    "value": kpi_data.get("value"),
                    "change": kpi_data.get("change"),
                    "format": kpi_data.get("format", "number"),
                    "icon": kpi_data.get("icon"),
                    "display": kpi_data.get("display")
                }
                structured_data[source]["kpis"].append(metric_info)
        
        # Add chart data from main dashboard
        main_chart_data = dashboard_data.get("chart_data", {})
        if main_chart_data:
            # GA4 Charts
            if main_chart_data.get("users_over_time"):
                structured_data["GA4"]["charts"]["users_over_time"] = {
                    "type": "line",
                    "description": "Daily users over the reporting period",
                    "data_points": len(main_chart_data["users_over_time"]),
                    "sample": main_chart_data["users_over_time"][:5] if isinstance(main_chart_data["users_over_time"], list) else None
                }
            if main_chart_data.get("traffic_sources"):
                structured_data["GA4"]["charts"]["traffic_sources"] = {
                    "type": "bar",
                    "description": "Traffic sources breakdown",
                    "data_points": len(main_chart_data["traffic_sources"]),
                    "top_sources": main_chart_data["traffic_sources"][:5] if isinstance(main_chart_data["traffic_sources"], list) else None
                }
            if main_chart_data.get("top_pages"):
                structured_data["GA4"]["charts"]["top_pages"] = {
                    "type": "table",
                    "description": "Top performing pages",
                    "data_points": len(main_chart_data["top_pages"]),
                    "top_pages": main_chart_data["top_pages"][:5] if isinstance(main_chart_data["top_pages"], list) else None
                }
            if main_chart_data.get("geographic_breakdown"):
                structured_data["GA4"]["charts"]["geographic_breakdown"] = {
                    "type": "map",
                    "description": "Geographic distribution of users",
                    "data_points": len(main_chart_data["geographic_breakdown"]),
                    "top_countries": main_chart_data["geographic_breakdown"][:5] if isinstance(main_chart_data["geographic_breakdown"], list) else None
                }
            
            # Agency Analytics Charts
            if main_chart_data.get("top_campaigns"):
                structured_data["AgencyAnalytics"]["charts"]["top_campaigns"] = {
                    "type": "bar",
                    "description": "Top performing SEO campaigns",
                    "data_points": len(main_chart_data["top_campaigns"]),
                    "top_campaigns": main_chart_data["top_campaigns"][:5] if isinstance(main_chart_data["top_campaigns"], list) else None
                }
        
        # Add Scrunch chart data
        if scrunch_data and scrunch_data.get("chart_data"):
            scrunch_chart_data = scrunch_data.get("chart_data", {})
            if scrunch_chart_data.get("top_performing_prompts"):
                structured_data["Scrunch"]["charts"]["top_performing_prompts"] = {
                    "type": "table",
                    "description": "Top performing AI prompts/mentions",
                    "data_points": len(scrunch_chart_data["top_performing_prompts"]),
                    "top_prompts": scrunch_chart_data["top_performing_prompts"][:5] if isinstance(scrunch_chart_data["top_performing_prompts"], list) else None
                }
            if scrunch_chart_data.get("scrunch_ai_insights"):
                structured_data["Scrunch"]["charts"]["scrunch_ai_insights"] = {
                    "type": "insights",
                    "description": "AI-generated insights from brand mentions",
                    "data_points": len(scrunch_chart_data["scrunch_ai_insights"]),
                    "sample_insights": scrunch_chart_data["scrunch_ai_insights"][:3] if isinstance(scrunch_chart_data["scrunch_ai_insights"], list) else None
                }
        
        # Prepare overall metrics summary (for backward compatibility)
        kpis_by_source = {
            "GA4": structured_data["GA4"]["kpis"],
            "AgencyAnalytics": structured_data["AgencyAnalytics"]["kpis"],
            "Scrunch": structured_data["Scrunch"]["kpis"]
        }
        
        all_metrics = []
        for source, metrics in kpis_by_source.items():
            all_metrics.extend(metrics)
        
        logger.info(f"[Executive Summary] Structured data - GA4: {len(structured_data['GA4']['kpis'])} KPIs, {len(structured_data['GA4']['charts'])} charts | AgencyAnalytics: {len(structured_data['AgencyAnalytics']['kpis'])} KPIs, {len(structured_data['AgencyAnalytics']['charts'])} charts | Scrunch: {len(structured_data['Scrunch']['kpis'])} KPIs, {len(structured_data['Scrunch']['charts'])} charts")
        
        if not all_metrics:
            logger.error("[Executive Summary] No metrics found to analyze after grouping")
            raise HTTPException(
                status_code=404,
                detail="No metrics found to analyze"
            )
        
        # Get client and brand information for header
        client_name = "Client"
        program_name = "Digital Marketing Program"
        if client_id:
            from app.services.supabase_service import SupabaseService
            supabase = SupabaseService(db=db)
            client = supabase.get_client_by_id(client_id)
            if client:
                client_name = client.get("company_name", "Client")
                program_name = client.get("report_title") or "Digital Marketing Program"
                logger.info(f"[Executive Summary] Client info loaded - name: {client_name}, program: {program_name}")
        elif brand_id:
            from app.services.supabase_service import SupabaseService
            supabase = SupabaseService(db=db)
            brand = supabase.get_brand_by_id(brand_id)
            if brand:
                client_name = brand.get("name", "Client")
                logger.info(f"[Executive Summary] Brand info loaded - name: {client_name}")
        
        # Create comprehensive prompt for OpenAI
        date_range = dashboard_data.get('date_range', {})
        start_date_str = date_range.get('start_date', 'N/A')
        end_date_str = date_range.get('end_date', 'N/A')
        
        # Format reporting period
        reporting_period = f"{start_date_str} to {end_date_str}"
        logger.info(f"[Executive Summary] Reporting period: {reporting_period}")
        
        # Format structured data with sections, KPIs, and charts
        structured_data_text = ""
        for section_key, section_data in structured_data.items():
            if section_data["kpis"] or section_data["charts"]:
                structured_data_text += f"\n\n{'='*60}\n"
                structured_data_text += f"{section_data['section_name']}\n"
                structured_data_text += f"{'='*60}\n"
                
                # Add KPIs
                if section_data["kpis"]:
                    structured_data_text += f"\n📊 Key Performance Indicators ({len(section_data['kpis'])} metrics):\n"
                    for kpi in section_data["kpis"]:
                        value_str = f"{kpi['value']}"
                        if kpi.get("change") is not None:
                            change_str = f"{kpi['change']:+.1f}%" if isinstance(kpi['change'], (int, float)) else str(kpi['change'])
                            value_str += f" ({change_str})"
                        if kpi.get("display"):
                            structured_data_text += f"  • {kpi['label']}: {kpi['display']}\n"
                        else:
                            structured_data_text += f"  • {kpi['label']}: {value_str}\n"
                
                # Add Charts
                if section_data["charts"]:
                    structured_data_text += f"\n📈 Charts & Visualizations ({len(section_data['charts'])} charts):\n"
                    for chart_key, chart_info in section_data["charts"].items():
                        structured_data_text += f"  • {chart_info['description']} ({chart_info['type']} chart, {chart_info['data_points']} data points)\n"
                        # Add sample data if available
                        if chart_info.get("sample") or chart_info.get("top_sources") or chart_info.get("top_pages") or chart_info.get("top_countries") or chart_info.get("top_campaigns") or chart_info.get("top_prompts") or chart_info.get("sample_insights"):
                            sample_data = (chart_info.get("sample") or chart_info.get("top_sources") or 
                                         chart_info.get("top_pages") or chart_info.get("top_countries") or 
                                         chart_info.get("top_campaigns") or chart_info.get("top_prompts") or 
                                         chart_info.get("sample_insights"))
                            if sample_data and len(sample_data) > 0:
                                structured_data_text += f"    Sample data: {json.dumps(sample_data[:3], indent=6, default=str)}\n"
        
        logger.debug(f"[Executive Summary] Structured data text length: {len(structured_data_text)} characters")
        
        # Also keep backward-compatible format for metrics
        metrics_by_source_text = ""
        for source, metrics in kpis_by_source.items():
            if metrics:
                source_name = {
                    "GA4": "Google Analytics 4 (Web Analytics)",
                    "AgencyAnalytics": "Agency Analytics (SEO Rankings)",
                    "Scrunch": "Scrunch AI (Brand Mentions & Sentiment)"
                }.get(source, source)
                metrics_by_source_text += f"\n\n{source_name} Metrics:\n"
                metrics_by_source_text += format_metrics_for_prompt(metrics)
        
        # New system prompt for Executive Brief
        system_prompt = """You are an AI reporting assistant for a B2B digital marketing agency.
Your job is to explain performance, not list metrics.
Prioritize clarity, honesty, and interpretation over completeness.

Hard constraints:
- Do NOT list raw metrics unless they support a clear insight
- Do NOT mention internal tools or data sources by name
- Do NOT speculate or invent explanations
- Do NOT hide negative performance; contextualize it calmly
- Do NOT exceed the defined section structure
- Assume performance may be strong, mixed, or poor
- If data is missing, acknowledge briefly and move on
- Maximum length: ~450-600 words total
- No emojis except for status indicators (✅ ⚠️ 🔴)
- No buzzwords or marketing hype
- No paragraphs longer than 3 lines
- Calm, confident, executive tone"""

        # User prompt requesting structured JSON output
        user_prompt = f"""Generate an Executive / Monthly Performance Brief for the following client and metrics.

Client Name: {client_name}
Program Name: {program_name}
Reporting Period: {reporting_period}

{structured_data_text}

NOTE: The data above is organized by sections (GA4, Agency Analytics, Scrunch) with both KPIs and chart visualizations. 
Use the chart data to provide context about trends, patterns, and visual insights that complement the KPI metrics.

You MUST return a valid JSON object with the following exact structure:
{{
  "header": {{
    "client_name": "{client_name}",
    "program_name": "{program_name}",
    "reporting_period": "{reporting_period}",
    "overall_status": "✅ Positive momentum" | "⚠️ Mixed / transitional" | "🔴 Underperforming"
  }},
  "executive_summary": "2-3 sentences describing overall performance, primary risk or limitation, and optional content/off-page progress reference",
  "what_worked": ["bullet 1 - clear win with WHY it matters", "bullet 2", "bullet 3", "bullet 4", "bullet 5"],
  "what_to_watch": ["bullet 1 - decline, risk, or flat area", "bullet 2", "bullet 3"],
  "ai_visibility_snapshot": ["bullet 1 - current presence level", "bullet 2 - direction if available", "bullet 3 - competitive signals"],
  "content_authority_snapshot": ["bullet 1 - on-site content summary", "bullet 2 - off-site/editorial or listings activity", "bullet 3 - pending items if relevant", "bullet 4 - one line tying content to SEO/AI goals"],
  "focus_next_30_days": ["1. Specific action tied to issues above", "2. Mix of optimization, expansion, validation", "3. Action 3", "4. Action 4", "5. Action 5"],
  "client_action_needed": "1-2 explicit actions OR 'No action needed this month.'"
}}

Requirements:
- what_worked: 3-5 bullets, each explaining WHY it matters to the business
- what_to_watch: 2-3 bullets covering declines, risks, flat areas, or tracking gaps
- ai_visibility_snapshot: 2-3 bullets
- content_authority_snapshot: 2-4 bullets (if unavailable, explicitly say so)
- focus_next_30_days: 3-5 numbered actions, specific and tied to issues above
- Total word count: ~450-600 words
- Return ONLY valid JSON, no markdown, no code blocks"""
        
        # Generate overview using OpenAI
        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]
        
        logger.info(f"[Executive Summary] Sending request to OpenAI - model: gpt-5.1-2025-11-13, max_tokens: 1000")
        logger.debug(f"[Executive Summary] System prompt length: {len(system_prompt)} characters")
        logger.debug(f"[Executive Summary] User prompt length: {len(user_prompt)} characters")
        
        result = await openai_client.create_chat_completion(
            messages=messages,
            model="gpt-5.1-2025-11-13",
            # max_tokens=1000
        )
        
        logger.info(f"[Executive Summary] OpenAI API response received - choices: {len(result.get('choices', []))}")
        
        # Extract and parse the response
        response_text = ""
        if result.get("choices") and len(result["choices"]) > 0:
            response_text = result["choices"][0].get("message", {}).get("content", "")
            logger.debug(f"[Executive Summary] Response text length: {len(response_text)} characters")
            logger.debug(f"[Executive Summary] Response text preview (first 200 chars): {response_text[:200]}")
        else:
            logger.warning("[Executive Summary] No choices in OpenAI response")
        
        # Parse JSON response
        executive_summary_data = None
        try:
            logger.info("[Executive Summary] Parsing OpenAI response as JSON")
            original_response_text = response_text
            
            # Try to extract JSON from markdown code blocks if present
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
                logger.debug("[Executive Summary] Extracted JSON from markdown code block (```json)")
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
                logger.debug("[Executive Summary] Extracted JSON from markdown code block (```)")
            
            executive_summary_data = json.loads(response_text)
            logger.info("[Executive Summary] JSON parsed successfully")
            
            # Validate structure
            validation_error = validate_executive_summary(executive_summary_data)
            if validation_error:
                logger.warning(f"[Executive Summary] Validation warning: {validation_error}")
                # Continue anyway, but log the issue
            else:
                logger.info("[Executive Summary] Validation passed - all required sections present")
            
            # Add metadata
            executive_summary_data["generated_at"] = datetime.now().isoformat()
            logger.info(f"[Executive Summary] Executive summary generated successfully at {executive_summary_data['generated_at']}")
            
        except json.JSONDecodeError as e:
            logger.error(f"[Executive Summary] Failed to parse OpenAI response as JSON: {str(e)}")
            logger.error(f"[Executive Summary] Response text (first 500 chars): {response_text[:500]}")
            logger.error(f"[Executive Summary] Full response text length: {len(response_text)} characters")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to parse AI response as structured JSON. Please try again."
            )
        
        response_data = {
            "client_id": client_id,
            "brand_id": brand_id,
            "brand_name": dashboard_data.get("brand_name"),
            "date_range": date_range,
            "total_metrics_analyzed": len(all_metrics),
            "metrics_by_source": {
                source: len(metrics) for source, metrics in kpis_by_source.items()
            },
            "executive_summary": executive_summary_data,
            "metrics": all_metrics
        }
        
        logger.info(f"[Executive Summary] Successfully generated executive summary for {'client' if client_id else 'brand'} {client_id or brand_id}")
        logger.debug(f"[Executive Summary] Response includes {len(executive_summary_data.get('what_worked', []))} 'what_worked' items, {len(executive_summary_data.get('what_to_watch', []))} 'what_to_watch' items")
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Executive Summary] Error generating overall overview: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating overall overview: {str(e)}")

def validate_executive_summary(summary: Dict) -> Optional[str]:
    """Validate executive summary structure and content"""
    required_sections = [
        "header", "executive_summary", "what_worked", "what_to_watch",
        "ai_visibility_snapshot", "content_authority_snapshot",
        "focus_next_30_days", "client_action_needed"
    ]
    
    # Check all required sections exist
    for section in required_sections:
        if section not in summary:
            return f"Missing required section: {section}"
    
    # Validate header structure
    header = summary.get("header", {})
    required_header_fields = ["client_name", "program_name", "reporting_period", "overall_status"]
    for field in required_header_fields:
        if field not in header:
            return f"Missing required header field: {field}"
    
    # Validate status value
    valid_statuses = ["✅ Positive momentum", "⚠️ Mixed / transitional", "🔴 Underperforming"]
    if header.get("overall_status") not in valid_statuses:
        return f"Invalid overall_status. Must be one of: {', '.join(valid_statuses)}"
    
    # Validate array lengths
    if not isinstance(summary.get("what_worked"), list) or len(summary.get("what_worked", [])) < 3:
        return "what_worked must be an array with at least 3 items"
    
    if not isinstance(summary.get("what_to_watch"), list) or len(summary.get("what_to_watch", [])) < 2:
        return "what_to_watch must be an array with at least 2 items"
    
    if not isinstance(summary.get("ai_visibility_snapshot"), list) or len(summary.get("ai_visibility_snapshot", [])) < 2:
        return "ai_visibility_snapshot must be an array with at least 2 items"
    
    if not isinstance(summary.get("content_authority_snapshot"), list) or len(summary.get("content_authority_snapshot", [])) < 2:
        return "content_authority_snapshot must be an array with at least 2 items"
    
    if not isinstance(summary.get("focus_next_30_days"), list) or len(summary.get("focus_next_30_days", [])) < 3:
        return "focus_next_30_days must be an array with at least 3 items"
    
    # Validate executive_summary is a string
    if not isinstance(summary.get("executive_summary"), str):
        return "executive_summary must be a string"
    
    # Validate client_action_needed is a string
    if not isinstance(summary.get("client_action_needed"), str):
        return "client_action_needed must be a string"
    
    return None  # No validation errors

def format_metrics_for_prompt(metrics: List[Dict]) -> str:
    """Format metrics data for OpenAI prompt"""
    formatted = []
    for metric in metrics:
        value_str = str(metric["value"])
        if metric.get("format") == "percentage":
            value_str = f"{metric['value']}%"
        elif metric.get("format") == "currency":
            value_str = f"${metric['value']:,.2f}"
        else:
            value_str = f"{metric['value']:,}" if isinstance(metric['value'], (int, float)) else str(metric['value'])
        
        change_str = ""
        change_value = metric.get("change")
        if change_value is not None:
            # Handle case where change might be a dict or a number
            if isinstance(change_value, dict):
                # If it's a dict, try to extract a numeric value
                # Common patterns: {"value": X}, {"percent": X}, or just use the first numeric value
                numeric_change = None
                for key in ["value", "percent", "percentage", "change"]:
                    if key in change_value and isinstance(change_value[key], (int, float)):
                        numeric_change = change_value[key]
                        break
                # If no numeric value found in dict, try to find any numeric value
                if numeric_change is None:
                    for val in change_value.values():
                        if isinstance(val, (int, float)):
                            numeric_change = val
                            break
                change_value = numeric_change
            
            # Only format if we have a valid numeric value
            if isinstance(change_value, (int, float)):
                change_direction = "↑" if change_value > 0 else "↓" if change_value < 0 else "→"
                change_str = f" ({change_direction} {abs(change_value):.1f}% vs previous period)"
        
        # Support both old format ('metric' key) and new format ('label' key)
        metric_name = metric.get("metric") or metric.get("label", "Unknown Metric")
        formatted.append(f"- {metric_name}: {value_str}{change_str}")
    
    return "\n".join(formatted)


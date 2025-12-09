from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, ARRAY, JSON, Enum, BigInteger, Numeric, Date, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, date
from typing import Optional
import enum

Base = declarative_base()


class AuditLogAction(str, enum.Enum):
    """Enum for audit log action types"""
    LOGIN = "login"
    LOGOUT = "logout"
    USER_CREATED = "user_created"
    SYNC_BRANDS = "sync_brands"
    SYNC_PROMPTS = "sync_prompts"
    SYNC_RESPONSES = "sync_responses"
    SYNC_GA4 = "sync_ga4"
    SYNC_AGENCY_ANALYTICS = "sync_agency_analytics"
    SYNC_ALL = "sync_all"


class Brand(Base):
    __tablename__ = "brands"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    website = Column(String, nullable=True)
    ga4_property_id = Column(String, nullable=True)  # Google Analytics 4 Property ID
    slug = Column(String, unique=True, nullable=True, index=True)  # URL-friendly identifier
    logo_url = Column(String, nullable=True)  # URL to brand logo image
    theme = Column(JSON, nullable=True, default={})  # Brand theme configuration (JSONB in DB)
    created_at = Column(DateTime(timezone=True), nullable=True)
    version = Column(Integer, nullable=False, default=1)  # Version for optimistic locking
    last_modified_by = Column(String, nullable=True)  # Email of user who last modified
    
    def __repr__(self):
        return f"<Brand(id={self.id}, name='{self.name}', version={self.version})>"


class Prompt(Base):
    __tablename__ = "prompts"
    
    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, nullable=True, index=True)  # References brands.id
    text = Column(Text, nullable=True)
    stage = Column(String, nullable=True, index=True)
    persona_id = Column(Integer, nullable=True, index=True)
    persona_name = Column(String, nullable=True)
    platforms = Column(ARRAY(String), nullable=True)
    tags = Column(ARRAY(String), nullable=True)
    topics = Column(ARRAY(String), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<Prompt(id={self.id}, stage='{self.stage}')>"


class Response(Base):
    __tablename__ = "responses"
    
    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, nullable=True, index=True)  # References brands.id
    prompt_id = Column(Integer, nullable=True, index=True)
    prompt = Column(Text, nullable=True)
    response_text = Column(Text, nullable=True)
    platform = Column(String, nullable=True, index=True)
    country = Column(String, nullable=True)
    persona_id = Column(Integer, nullable=True, index=True)
    persona_name = Column(String, nullable=True)
    stage = Column(String, nullable=True, index=True)
    branded = Column(Boolean, nullable=True)
    tags = Column(ARRAY(String), nullable=True)
    key_topics = Column(ARRAY(String), nullable=True)
    brand_present = Column(Boolean, nullable=True)
    brand_sentiment = Column(String, nullable=True)
    brand_position = Column(String, nullable=True)
    competitors_present = Column(ARRAY(String), nullable=True)
    competitors = Column(JSON, nullable=True)  # Array of competitor objects
    created_at = Column(DateTime(timezone=True), nullable=True, index=True)
    citations = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<Response(id={self.id}, platform='{self.platform}')>"


class Citation(Base):
    __tablename__ = "citations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    response_id = Column(Integer, ForeignKey("responses.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(Text, nullable=True)
    domain = Column(String, nullable=True, index=True)
    source_type = Column(String, nullable=True)
    title = Column(String, nullable=True)
    snippet = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Citation(id={self.id}, response_id={self.response_id}, domain='{self.domain}')>"


class AuditLog(Base):
    """Audit log table for tracking user actions and data syncs"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    action = Column(Enum(AuditLogAction), nullable=False, index=True)
    user_id = Column(String, nullable=True, index=True)  # Supabase user ID
    user_email = Column(String, nullable=True, index=True)  # User email for easier querying
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    
    # Action-specific details
    details = Column(JSON, nullable=True)  # Store additional context (brand_id, sync counts, etc.)
    
    # Status
    status = Column(String, nullable=True, index=True)  # 'success', 'error', 'partial'
    error_message = Column(Text, nullable=True)  # Error message if status is 'error'
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', user_email='{self.user_email}', created_at='{self.created_at}')>"


class User(Base):
    """User model for v2 local PostgreSQL authentication"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship to refresh tokens
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', full_name='{self.full_name}')>"


class RefreshToken(Base):
    """Refresh token model for v2 authentication"""
    __tablename__ = "refresh_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)  # Hashed token
    usage_count = Column(Integer, default=0, nullable=False)
    max_usage = Column(Integer, default=4, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationship to user
    user = relationship("User", back_populates="refresh_tokens")
    
    def __repr__(self):
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, usage_count={self.usage_count}/{self.max_usage}, expires_at='{self.expires_at}')>"


class Client(Base):
    """Client model for Agency Analytics campaigns"""
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_name = Column(Text, nullable=False)
    company_id = Column(Integer, nullable=True)
    url = Column(Text, nullable=True)
    email_addresses = Column(ARRAY(String), nullable=True)
    phone_numbers = Column(ARRAY(String), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    zip = Column(String, nullable=True)
    country = Column(String, nullable=True)
    timezone = Column(String, nullable=True)
    url_slug = Column(String, unique=True, nullable=True, index=True)
    ga4_property_id = Column(String, nullable=True, index=True)
    scrunch_brand_id = Column(Integer, ForeignKey("brands.id", ondelete="SET NULL"), nullable=True)
    theme_color = Column(String, nullable=True)
    logo_url = Column(String, nullable=True)
    secondary_color = Column(String, nullable=True)
    font_family = Column(String, nullable=True)
    favicon_url = Column(String, nullable=True)
    report_title = Column(String, nullable=True)
    company_domain = Column(String, nullable=True, index=True)
    custom_css = Column(Text, nullable=True)
    footer_text = Column(Text, nullable=True)
    header_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)
    version = Column(Integer, nullable=False, default=1, index=True)
    last_modified_by = Column(String, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    report_start_date = Column(Date, nullable=True)
    report_end_date = Column(Date, nullable=True)
    
    def __repr__(self):
        return f"<Client(id={self.id}, company_name='{self.company_name}', version={self.version}, is_active={self.is_active})>"


class DashboardLink(Base):
    """Shareable dashboard links per client"""
    __tablename__ = "dashboard_links"
    __table_args__ = (
        UniqueConstraint('client_id', 'start_date', 'end_date', name='uq_dashboard_links_client_dates'),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    slug = Column(String, unique=True, nullable=False, index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    enabled = Column(Boolean, nullable=False, default=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<DashboardLink(id={self.id}, client_id={self.client_id}, slug='{self.slug}', enabled={self.enabled})>"


class ClientCampaign(Base):
    """Client-Campaign link model"""
    __tablename__ = "client_campaigns"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    campaign_id = Column(BigInteger, nullable=False, index=True)  # References agency_analytics_campaigns.id (BIGINT after migration)
    is_primary = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<ClientCampaign(id={self.id}, client_id={self.client_id}, campaign_id={self.campaign_id}, is_primary={self.is_primary})>"


class GA4TrafficOverview(Base):
    """GA4 Traffic Overview model"""
    __tablename__ = "ga4_traffic_overview"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=True, index=True)
    property_id = Column(String, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    users = Column(Integer, default=0, nullable=False)
    sessions = Column(Integer, default=0, nullable=False)
    new_users = Column(Integer, default=0, nullable=False)
    bounce_rate = Column(Numeric(5, 2), default=0, nullable=False)
    average_session_duration = Column(Numeric(10, 2), default=0, nullable=False)
    engaged_sessions = Column(Integer, default=0, nullable=False)
    engagement_rate = Column(Numeric(5, 4), default=0, nullable=False)
    sessions_change = Column(Numeric(6, 2), default=0, nullable=False)
    engaged_sessions_change = Column(Numeric(6, 2), default=0, nullable=False)
    avg_session_duration_change = Column(Numeric(6, 2), default=0, nullable=False)
    engagement_rate_change = Column(Numeric(6, 2), default=0, nullable=False)
    revenue = Column(Numeric(15, 2), default=0, nullable=False)
    conversions = Column(Numeric(10, 2), default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<GA4TrafficOverview(id={self.id}, property_id='{self.property_id}', date='{self.date}')>"


class GA4TopPages(Base):
    """GA4 Top Pages model"""
    __tablename__ = "ga4_top_pages"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=True, index=True)
    property_id = Column(String, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    page_path = Column(Text, nullable=False)
    views = Column(Integer, default=0, nullable=False)
    users = Column(Integer, default=0, nullable=False)
    avg_session_duration = Column(Numeric(10, 2), default=0, nullable=False)
    rank = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<GA4TopPages(id={self.id}, page_path='{self.page_path}', rank={self.rank})>"


class GA4TrafficSources(Base):
    """GA4 Traffic Sources model"""
    __tablename__ = "ga4_traffic_sources"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=True, index=True)
    property_id = Column(String, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    source = Column(Text, nullable=False)
    sessions = Column(Integer, default=0, nullable=False)
    users = Column(Integer, default=0, nullable=False)
    bounce_rate = Column(Numeric(5, 2), default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<GA4TrafficSources(id={self.id}, source='{self.source}')>"


class GA4Geographic(Base):
    """GA4 Geographic model"""
    __tablename__ = "ga4_geographic"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=True, index=True)
    property_id = Column(String, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    country = Column(Text, nullable=False, index=True)
    users = Column(Integer, default=0, nullable=False)
    sessions = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<GA4Geographic(id={self.id}, country='{self.country}')>"


class GA4Devices(Base):
    """GA4 Devices model"""
    __tablename__ = "ga4_devices"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=True, index=True)
    property_id = Column(String, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    device_category = Column(Text, nullable=False)
    operating_system = Column(Text, nullable=False)
    users = Column(Integer, default=0, nullable=False)
    sessions = Column(Integer, default=0, nullable=False)
    bounce_rate = Column(Numeric(5, 2), default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<GA4Devices(id={self.id}, device_category='{self.device_category}')>"


class GA4Conversions(Base):
    """GA4 Conversions model"""
    __tablename__ = "ga4_conversions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=True, index=True)
    property_id = Column(String, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    event_name = Column(Text, nullable=False)
    event_count = Column(Integer, default=0, nullable=False)
    users = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<GA4Conversions(id={self.id}, event_name='{self.event_name}')>"


class GA4Realtime(Base):
    """GA4 Realtime model"""
    __tablename__ = "ga4_realtime"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=True, index=True)
    property_id = Column(String, nullable=False, index=True)
    snapshot_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    total_active_users = Column(Integer, default=0, nullable=False)
    active_pages = Column(JSON, nullable=True)  # JSONB in DB
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<GA4Realtime(id={self.id}, snapshot_time='{self.snapshot_time}')>"


class GA4PropertyDetails(Base):
    """GA4 Property Details model"""
    __tablename__ = "ga4_property_details"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=True, index=True)
    property_id = Column(String, nullable=False, unique=True, index=True)
    display_name = Column(Text, nullable=True)
    time_zone = Column(String, nullable=True)
    currency_code = Column(String, nullable=True)
    create_time = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<GA4PropertyDetails(id={self.id}, property_id='{self.property_id}')>"


class GA4Revenue(Base):
    """GA4 Revenue model"""
    __tablename__ = "ga4_revenue"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=True, index=True)
    property_id = Column(String, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    total_revenue = Column(Numeric(15, 2), default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<GA4Revenue(id={self.id}, date='{self.date}')>"


class GA4DailyConversions(Base):
    """GA4 Daily Conversions model"""
    __tablename__ = "ga4_daily_conversions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=True, index=True)
    property_id = Column(String, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    total_conversions = Column(Numeric(10, 2), default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<GA4DailyConversions(id={self.id}, date='{self.date}')>"


class GA4KPISnapshots(Base):
    """GA4 KPI Snapshots model"""
    __tablename__ = "ga4_kpi_snapshots"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=True, index=True)
    property_id = Column(String, nullable=False, index=True)
    period_end_date = Column(Date, nullable=False, index=True)
    period_start_date = Column(Date, nullable=False)
    prev_period_start_date = Column(Date, nullable=False)
    prev_period_end_date = Column(Date, nullable=False)
    # Current period values
    users = Column(Integer, default=0, nullable=False)
    sessions = Column(Integer, default=0, nullable=False)
    new_users = Column(Integer, default=0, nullable=False)
    bounce_rate = Column(Numeric(10, 4), default=0, nullable=False)
    avg_session_duration = Column(Numeric(10, 2), default=0, nullable=False)
    engagement_rate = Column(Numeric(10, 4), default=0, nullable=False)
    engaged_sessions = Column(Integer, default=0, nullable=False)
    conversions = Column(Numeric(10, 2), default=0, nullable=False)
    revenue = Column(Numeric(15, 2), default=0, nullable=False)
    # Previous period values
    prev_users = Column(Integer, default=0, nullable=False)
    prev_sessions = Column(Integer, default=0, nullable=False)
    prev_new_users = Column(Integer, default=0, nullable=False)
    prev_bounce_rate = Column(Numeric(10, 4), default=0, nullable=False)
    prev_avg_session_duration = Column(Numeric(10, 2), default=0, nullable=False)
    prev_engagement_rate = Column(Numeric(10, 4), default=0, nullable=False)
    prev_engaged_sessions = Column(Integer, default=0, nullable=False)
    prev_conversions = Column(Numeric(10, 2), default=0, nullable=False)
    prev_revenue = Column(Numeric(15, 2), default=0, nullable=False)
    # Percentage changes
    users_change = Column(Numeric(8, 2), default=0, nullable=False)
    sessions_change = Column(Numeric(8, 2), default=0, nullable=False)
    new_users_change = Column(Numeric(8, 2), default=0, nullable=False)
    bounce_rate_change = Column(Numeric(8, 2), default=0, nullable=False)
    avg_session_duration_change = Column(Numeric(8, 2), default=0, nullable=False)
    engagement_rate_change = Column(Numeric(8, 2), default=0, nullable=False)
    engaged_sessions_change = Column(Numeric(8, 2), default=0, nullable=False)
    conversions_change = Column(Numeric(8, 2), default=0, nullable=False)
    revenue_change = Column(Numeric(8, 2), default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<GA4KPISnapshots(id={self.id}, period_end_date='{self.period_end_date}')>"


class GA4Tokens(Base):
    """GA4 Tokens model"""
    __tablename__ = "ga4_tokens"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    access_token = Column(Text, nullable=False)
    expires_at = Column(BigInteger, nullable=False)
    generated_at = Column(BigInteger, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True, nullable=False)
    
    def __repr__(self):
        return f"<GA4Tokens(id={self.id}, is_active={self.is_active})>"


class AgencyAnalyticsCampaign(Base):
    """Agency Analytics Campaigns model"""
    __tablename__ = "agency_analytics_campaigns"
    
    id = Column(BigInteger, primary_key=True, index=True)  # Changed to BIGINT after migration
    date_created = Column(DateTime(timezone=True), nullable=True)
    date_modified = Column(DateTime(timezone=True), nullable=True)
    url = Column(Text, nullable=True)
    company = Column(Text, nullable=True, index=True)
    scope = Column(String, nullable=True)
    status = Column(String, nullable=True, index=True)
    group_title = Column(Text, nullable=True)
    email_addresses = Column(ARRAY(String), nullable=True)
    phone_numbers = Column(ARRAY(String), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    zip = Column(String, nullable=True)
    country = Column(String, nullable=True)
    revenue = Column(Numeric(15, 2), nullable=True)
    headcount = Column(Integer, nullable=True)
    google_ignore_places = Column(Boolean, nullable=True)
    enforce_google_cid = Column(Boolean, nullable=True)
    timezone = Column(String, nullable=True)
    type = Column(String, nullable=True)
    campaign_group_id = Column(BigInteger, nullable=True)  # Changed to BIGINT after migration
    company_id = Column(BigInteger, nullable=True)  # Changed to BIGINT after migration
    account_id = Column(BigInteger, nullable=True)  # Changed to BIGINT after migration
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<AgencyAnalyticsCampaign(id={self.id}, company='{self.company}')>"


class AgencyAnalyticsCampaignRanking(Base):
    """Agency Analytics Campaign Rankings model"""
    __tablename__ = "agency_analytics_campaign_rankings"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    campaign_id = Column(BigInteger, nullable=False, index=True)  # Changed to BIGINT after migration
    client_name = Column(Text, nullable=True, index=True)
    date = Column(Date, nullable=False, index=True)
    campaign_id_date = Column(String, unique=True, nullable=False, index=True)
    google_ranking_count = Column(Integer, default=0, nullable=False)
    google_ranking_change = Column(Integer, default=0, nullable=False)
    google_local_count = Column(Integer, default=0, nullable=False)
    google_mobile_count = Column(Integer, default=0, nullable=False)
    bing_ranking_count = Column(Integer, default=0, nullable=False)
    ranking_average = Column(Numeric(10, 2), default=0, nullable=False)
    search_volume = Column(BigInteger, default=0, nullable=False)  # Changed to BIGINT after migration
    competition = Column(Numeric(10, 2), default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<AgencyAnalyticsCampaignRanking(id={self.id}, campaign_id={self.campaign_id}, date='{self.date}')>"


class AgencyAnalyticsCampaignBrand(Base):
    """Agency Analytics Campaign-Brand Links model"""
    __tablename__ = "agency_analytics_campaign_brands"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    campaign_id = Column(BigInteger, ForeignKey("agency_analytics_campaigns.id", ondelete="CASCADE"), nullable=False, index=True)  # Changed to BIGINT
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True)
    match_method = Column(Text, nullable=False, index=True)
    match_confidence = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<AgencyAnalyticsCampaignBrand(id={self.id}, campaign_id={self.campaign_id}, brand_id={self.brand_id})>"


class AgencyAnalyticsKeyword(Base):
    """Agency Analytics Keywords model"""
    __tablename__ = "agency_analytics_keywords"
    
    id = Column(BigInteger, primary_key=True, index=True)  # Changed to BIGINT after migration
    campaign_id = Column(BigInteger, ForeignKey("agency_analytics_campaigns.id", ondelete="CASCADE"), nullable=False, index=True)  # Changed to BIGINT
    campaign_keyword_id = Column(String, unique=True, nullable=False, index=True)
    keyword_phrase = Column(Text, nullable=True, index=True)
    primary_keyword = Column(Boolean, default=False, nullable=False, index=True)
    search_location = Column(Text, nullable=True)
    search_location_formatted_name = Column(Text, nullable=True)
    search_location_region_name = Column(Text, nullable=True)
    search_location_country_code = Column(String, nullable=True)
    search_location_latitude = Column(Numeric(10, 8), nullable=True)
    search_location_longitude = Column(Numeric(11, 8), nullable=True)
    search_language = Column(String, nullable=True)
    tags = Column(Text, nullable=True)
    date_created = Column(DateTime(timezone=True), nullable=True)
    date_modified = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<AgencyAnalyticsKeyword(id={self.id}, keyword_phrase='{self.keyword_phrase}')>"


class AgencyAnalyticsKeywordRanking(Base):
    """Agency Analytics Keyword Rankings model"""
    __tablename__ = "agency_analytics_keyword_rankings"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    keyword_id = Column(BigInteger, ForeignKey("agency_analytics_keywords.id", ondelete="CASCADE"), nullable=False, index=True)  # Changed to BIGINT
    campaign_id = Column(BigInteger, ForeignKey("agency_analytics_campaigns.id", ondelete="CASCADE"), nullable=False, index=True)  # Changed to BIGINT
    keyword_id_date = Column(String, nullable=False, index=True)  # Unique constraint removed - allows multiple entries per keyword per date
    date = Column(Date, nullable=False, index=True)
    google_ranking = Column(Integer, nullable=True)
    google_ranking_url = Column(Text, nullable=True)
    google_mobile_ranking = Column(Integer, nullable=True)
    google_mobile_ranking_url = Column(Text, nullable=True)
    google_local_ranking = Column(Integer, nullable=True)
    bing_ranking = Column(Integer, nullable=True)
    bing_ranking_url = Column(Text, nullable=True)
    results = Column(BigInteger, nullable=True)  # Changed to BIGINT after migration
    volume = Column(BigInteger, nullable=True)  # Changed to BIGINT after migration
    competition = Column(Numeric(10, 2), nullable=True)
    field_status = Column(JSON, nullable=True)  # JSONB in DB
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<AgencyAnalyticsKeywordRanking(id={self.id}, keyword_id={self.keyword_id}, date='{self.date}')>"


class AgencyAnalyticsKeywordRankingSummary(Base):
    """Agency Analytics Keyword Ranking Summaries model"""
    __tablename__ = "agency_analytics_keyword_ranking_summaries"
    
    keyword_id = Column(BigInteger, ForeignKey("agency_analytics_keywords.id", ondelete="CASCADE"), primary_key=True, index=True)  # Changed to BIGINT
    campaign_id = Column(BigInteger, ForeignKey("agency_analytics_campaigns.id", ondelete="CASCADE"), nullable=False, index=True)  # Changed to BIGINT
    keyword_phrase = Column(Text, nullable=True)
    keyword_id_date = Column(String, nullable=False, index=True)  # Unique constraint removed - allows multiple entries per keyword per date
    date = Column(Date, nullable=True)
    google_ranking = Column(Integer, nullable=True)
    google_ranking_url = Column(Text, nullable=True)
    google_mobile_ranking = Column(Integer, nullable=True)
    google_mobile_ranking_url = Column(Text, nullable=True)
    google_local_ranking = Column(Integer, nullable=True)
    bing_ranking = Column(Integer, nullable=True)
    bing_ranking_url = Column(Text, nullable=True)
    search_volume = Column(BigInteger, nullable=True)  # Changed to BIGINT after migration
    competition = Column(Numeric(10, 2), nullable=True)
    results = Column(BigInteger, nullable=True)  # Changed to BIGINT after migration
    field_status = Column(JSON, nullable=True)  # JSONB in DB
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    start_ranking = Column(Integer, nullable=True)
    end_ranking = Column(Integer, nullable=True)
    ranking_change = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<AgencyAnalyticsKeywordRankingSummary(keyword_id={self.keyword_id}, date='{self.date}')>"


class BrandKPISelection(Base):
    """Brand KPI Selections model"""
    __tablename__ = "brand_kpi_selections"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=True, unique=True, index=True)  # Primary identifier (client-centric)
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=True, index=True)  # For backward compatibility
    selected_kpis = Column(ARRAY(String), nullable=False, default=[])
    visible_sections = Column(ARRAY(String), nullable=False, default=['ga4', 'scrunch_ai', 'brand_analytics', 'advanced_analytics', 'performance_metrics'])
    selected_charts = Column(ARRAY(String), nullable=False, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    version = Column(Integer, nullable=False, default=1)
    last_modified_by = Column(String, nullable=True)
    
    def __repr__(self):
        return f"<BrandKPISelection(id={self.id}, brand_id={self.brand_id}, version={self.version})>"


class SyncJob(Base):
    """Sync Jobs model"""
    __tablename__ = "sync_jobs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_id = Column(String(255), unique=True, nullable=False, index=True)
    sync_type = Column(String(50), nullable=False, index=True)
    user_id = Column(String(255), nullable=True, index=True)
    user_email = Column(String(255), nullable=True, index=True)
    status = Column(String(50), nullable=False, default='pending', index=True)
    progress = Column(Integer, default=0, nullable=False)
    current_step = Column(String(255), nullable=True)
    total_steps = Column(Integer, default=0, nullable=False)
    completed_steps = Column(Integer, default=0, nullable=False)
    result = Column(JSON, nullable=True)  # JSONB in DB
    error_message = Column(Text, nullable=True)
    parameters = Column(JSON, nullable=True)  # JSONB in DB
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<SyncJob(id={self.id}, job_id='{self.job_id}', status='{self.status}')>"

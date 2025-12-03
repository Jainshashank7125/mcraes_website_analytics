-- =====================================================
-- Complete Database Schema - Consolidated Migration v1
-- This migration includes all tables, columns, indexes, triggers, and functions
-- from all previous migrations (v1 through v19)
-- =====================================================
-- Run this in your PostgreSQL database to set up the complete schema
-- =====================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- 1. ENUMS
-- =====================================================

-- Audit log action enum
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'auditlogaction') THEN
        CREATE TYPE auditlogaction AS ENUM (
            'login',
            'logout',
            'user_created',
            'sync_brands',
            'sync_prompts',
            'sync_responses',
            'sync_ga4',
            'sync_agency_analytics',
            'sync_all'
        );
    END IF;
END $$;

-- =====================================================
-- 2. CORE TABLES (Scrunch AI Data)
-- =====================================================

-- Brands Table
CREATE TABLE IF NOT EXISTS brands (
    id INTEGER PRIMARY KEY,
    name TEXT,
    website TEXT,
    ga4_property_id TEXT,  -- Google Analytics 4 Property ID
    slug TEXT UNIQUE,  -- URL-friendly identifier (UUID-based)
    logo_url TEXT,  -- URL to brand logo image
    theme JSONB DEFAULT '{}'::jsonb,  -- Brand theme configuration
    version INTEGER NOT NULL DEFAULT 1,  -- Version for optimistic locking
    last_modified_by TEXT,  -- Email of user who last modified
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Prompts Table
CREATE TABLE IF NOT EXISTS prompts (
    id INTEGER PRIMARY KEY,
    brand_id INTEGER,  -- References brands.id
    text TEXT,  -- API returns "text" not "prompt_text"
    stage TEXT,
    persona_id INTEGER,
    persona_name TEXT,
    platforms TEXT[],  -- API returns "platforms" array
    tags TEXT[],
    topics TEXT[],  -- API returns "topics" not "key_topics"
    created_at TIMESTAMPTZ
);

-- Responses Table
CREATE TABLE IF NOT EXISTS responses (
    id INTEGER PRIMARY KEY,
    brand_id INTEGER,  -- References brands.id
    prompt_id INTEGER,
    prompt TEXT,
    response_text TEXT,
    platform TEXT,
    country TEXT,
    persona_id INTEGER,
    persona_name TEXT,
    stage TEXT,
    branded BOOLEAN,
    tags TEXT[],  -- API returns tags
    key_topics TEXT[],
    brand_present BOOLEAN,
    brand_sentiment TEXT,
    brand_position TEXT,
    competitors_present TEXT[],  -- Array of competitor names
    competitors JSONB,  -- Array of competitor objects
    created_at TIMESTAMPTZ,
    citations JSONB  -- Array of citation objects
);

-- Citations Table
CREATE TABLE IF NOT EXISTS citations (
    id SERIAL PRIMARY KEY,
    response_id INTEGER REFERENCES responses(id) ON DELETE CASCADE,
    url TEXT,
    domain TEXT,
    source_type TEXT,
    title TEXT,
    snippet TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- 3. CLIENTS TABLE (created before GA4 tables that reference it)
-- =====================================================

CREATE TABLE IF NOT EXISTS clients (
    id SERIAL PRIMARY KEY,
    company_name TEXT NOT NULL,
    company_id INTEGER,
    url TEXT,
    email_addresses TEXT[],
    phone_numbers TEXT[],
    address TEXT,
    city TEXT,
    state TEXT,
    zip TEXT,
    country TEXT,
    timezone TEXT,
    url_slug TEXT UNIQUE,
    ga4_property_id TEXT,
    scrunch_brand_id INTEGER REFERENCES brands(id) ON DELETE SET NULL,
    theme_color TEXT,
    logo_url TEXT,
    secondary_color TEXT,
    font_family TEXT,
    favicon_url TEXT,
    report_title TEXT,
    company_domain TEXT,
    custom_css TEXT,
    footer_text TEXT,
    header_text TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by TEXT,
    updated_by TEXT,
    version INTEGER NOT NULL DEFAULT 1,
    last_modified_by TEXT,
    CONSTRAINT clients_url_slug_check CHECK (url_slug IS NULL OR (url_slug ~ '^[a-z0-9-]+$' AND length(url_slug) >= 32))
);

-- Client-Campaign Links Table
CREATE TABLE IF NOT EXISTS client_campaigns (
    id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    campaign_id INTEGER NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(client_id, campaign_id)
);

-- =====================================================
-- 4. GA4 TABLES
-- =====================================================

-- GA4 Traffic Overview Table
CREATE TABLE IF NOT EXISTS ga4_traffic_overview (
    id SERIAL PRIMARY KEY,
    brand_id INTEGER REFERENCES brands(id) ON DELETE CASCADE,
    client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
    property_id TEXT NOT NULL,
    date DATE NOT NULL,
    users INTEGER DEFAULT 0,
    sessions INTEGER DEFAULT 0,
    new_users INTEGER DEFAULT 0,
    bounce_rate DECIMAL(5,2) DEFAULT 0,
    average_session_duration DECIMAL(10,2) DEFAULT 0,
    engaged_sessions INTEGER DEFAULT 0,
    engagement_rate DECIMAL(5,4) DEFAULT 0,
    sessions_change DECIMAL(6,2) DEFAULT 0,
    engaged_sessions_change DECIMAL(6,2) DEFAULT 0,
    avg_session_duration_change DECIMAL(6,2) DEFAULT 0,
    engagement_rate_change DECIMAL(6,2) DEFAULT 0,
    revenue DECIMAL(15,2) DEFAULT 0,
    conversions DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(brand_id, property_id, date)
);

-- GA4 Top Pages Table
CREATE TABLE IF NOT EXISTS ga4_top_pages (
    id SERIAL PRIMARY KEY,
    brand_id INTEGER REFERENCES brands(id) ON DELETE CASCADE,
    client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
    property_id TEXT NOT NULL,
    date DATE NOT NULL,
    page_path TEXT NOT NULL,
    views INTEGER DEFAULT 0,
    users INTEGER DEFAULT 0,
    avg_session_duration DECIMAL(10,2) DEFAULT 0,
    rank INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(brand_id, property_id, date, page_path)
);

-- GA4 Traffic Sources Table
CREATE TABLE IF NOT EXISTS ga4_traffic_sources (
    id SERIAL PRIMARY KEY,
    brand_id INTEGER REFERENCES brands(id) ON DELETE CASCADE,
    client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
    property_id TEXT NOT NULL,
    date DATE NOT NULL,
    source TEXT NOT NULL,
    sessions INTEGER DEFAULT 0,
    users INTEGER DEFAULT 0,
    bounce_rate DECIMAL(5,2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(brand_id, property_id, date, source)
);

-- GA4 Geographic Table
CREATE TABLE IF NOT EXISTS ga4_geographic (
    id SERIAL PRIMARY KEY,
    brand_id INTEGER REFERENCES brands(id) ON DELETE CASCADE,
    client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
    property_id TEXT NOT NULL,
    date DATE NOT NULL,
    country TEXT NOT NULL,
    users INTEGER DEFAULT 0,
    sessions INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(brand_id, property_id, date, country)
);

-- GA4 Devices Table
CREATE TABLE IF NOT EXISTS ga4_devices (
    id SERIAL PRIMARY KEY,
    brand_id INTEGER REFERENCES brands(id) ON DELETE CASCADE,
    client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
    property_id TEXT NOT NULL,
    date DATE NOT NULL,
    device_category TEXT NOT NULL,
    operating_system TEXT NOT NULL,
    users INTEGER DEFAULT 0,
    sessions INTEGER DEFAULT 0,
    bounce_rate DECIMAL(5,2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(brand_id, property_id, date, device_category, operating_system)
);

-- GA4 Conversions Table
CREATE TABLE IF NOT EXISTS ga4_conversions (
    id SERIAL PRIMARY KEY,
    brand_id INTEGER REFERENCES brands(id) ON DELETE CASCADE,
    client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
    property_id TEXT NOT NULL,
    date DATE NOT NULL,
    event_name TEXT NOT NULL,
    event_count INTEGER DEFAULT 0,
    users INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(brand_id, property_id, date, event_name)
);

-- GA4 Realtime Table
CREATE TABLE IF NOT EXISTS ga4_realtime (
    id SERIAL PRIMARY KEY,
    brand_id INTEGER REFERENCES brands(id) ON DELETE CASCADE,
    client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
    property_id TEXT NOT NULL,
    snapshot_time TIMESTAMPTZ DEFAULT NOW(),
    total_active_users INTEGER DEFAULT 0,
    active_pages JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(brand_id, property_id, snapshot_time)
);

-- GA4 Property Details Table
CREATE TABLE IF NOT EXISTS ga4_property_details (
    id SERIAL PRIMARY KEY,
    brand_id INTEGER REFERENCES brands(id) ON DELETE CASCADE,
    client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
    property_id TEXT NOT NULL,
    display_name TEXT,
    time_zone TEXT,
    currency_code TEXT,
    create_time TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(brand_id, property_id)
);

-- GA4 Revenue Table
CREATE TABLE IF NOT EXISTS ga4_revenue (
    id SERIAL PRIMARY KEY,
    brand_id INTEGER REFERENCES brands(id) ON DELETE CASCADE,
    client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
    property_id TEXT NOT NULL,
    date DATE NOT NULL,
    total_revenue DECIMAL(15,2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(brand_id, property_id, date)
);

-- GA4 Daily Conversions Table
CREATE TABLE IF NOT EXISTS ga4_daily_conversions (
    id SERIAL PRIMARY KEY,
    brand_id INTEGER REFERENCES brands(id) ON DELETE CASCADE,
    client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
    property_id TEXT NOT NULL,
    date DATE NOT NULL,
    total_conversions DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(brand_id, property_id, date)
);

-- GA4 KPI Snapshots Table (with client_id support)
CREATE TABLE IF NOT EXISTS ga4_kpi_snapshots (
    id SERIAL PRIMARY KEY,
    brand_id INTEGER REFERENCES brands(id) ON DELETE CASCADE,
    client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
    property_id TEXT NOT NULL,
    period_end_date DATE NOT NULL,
    period_start_date DATE NOT NULL,
    prev_period_start_date DATE NOT NULL,
    prev_period_end_date DATE NOT NULL,
    -- Current period values
    users INTEGER DEFAULT 0,
    sessions INTEGER DEFAULT 0,
    new_users INTEGER DEFAULT 0,
    bounce_rate DECIMAL(10,4) DEFAULT 0,
    avg_session_duration DECIMAL(10,2) DEFAULT 0,
    engagement_rate DECIMAL(10,4) DEFAULT 0,
    engaged_sessions INTEGER DEFAULT 0,
    conversions DECIMAL(10,2) DEFAULT 0,
    revenue DECIMAL(15,2) DEFAULT 0,
    -- Previous period values
    prev_users INTEGER DEFAULT 0,
    prev_sessions INTEGER DEFAULT 0,
    prev_new_users INTEGER DEFAULT 0,
    prev_bounce_rate DECIMAL(10,4) DEFAULT 0,
    prev_avg_session_duration DECIMAL(10,2) DEFAULT 0,
    prev_engagement_rate DECIMAL(10,4) DEFAULT 0,
    prev_engaged_sessions INTEGER DEFAULT 0,
    prev_conversions DECIMAL(10,2) DEFAULT 0,
    prev_revenue DECIMAL(15,2) DEFAULT 0,
    -- Percentage changes
    users_change DECIMAL(8,2) DEFAULT 0,
    sessions_change DECIMAL(8,2) DEFAULT 0,
    new_users_change DECIMAL(8,2) DEFAULT 0,
    bounce_rate_change DECIMAL(8,2) DEFAULT 0,
    avg_session_duration_change DECIMAL(8,2) DEFAULT 0,
    engagement_rate_change DECIMAL(8,2) DEFAULT 0,
    engaged_sessions_change DECIMAL(8,2) DEFAULT 0,
    conversions_change DECIMAL(8,2) DEFAULT 0,
    revenue_change DECIMAL(8,2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(brand_id, property_id, period_end_date)
);

-- GA4 Tokens Table
CREATE TABLE IF NOT EXISTS ga4_tokens (
    id SERIAL PRIMARY KEY,
    access_token TEXT NOT NULL,
    expires_at BIGINT NOT NULL,
    generated_at BIGINT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- =====================================================
-- 5. AGENCY ANALYTICS TABLES
-- =====================================================

-- Agency Analytics Campaigns Table
CREATE TABLE IF NOT EXISTS agency_analytics_campaigns (
    id INTEGER PRIMARY KEY,
    date_created TIMESTAMPTZ,
    date_modified TIMESTAMPTZ,
    url TEXT,
    company TEXT,
    scope TEXT,
    status TEXT,
    group_title TEXT,
    email_addresses TEXT[],
    phone_numbers TEXT[],
    address TEXT,
    city TEXT,
    state TEXT,
    zip TEXT,
    country TEXT,
    revenue DECIMAL(15, 2),
    headcount INTEGER,
    google_ignore_places BOOLEAN,
    enforce_google_cid BOOLEAN,
    timezone TEXT,
    type TEXT,
    campaign_group_id INTEGER,
    company_id INTEGER,
    account_id INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Agency Analytics Campaign Rankings Table
CREATE TABLE IF NOT EXISTS agency_analytics_campaign_rankings (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER NOT NULL,
    client_name TEXT,
    date DATE NOT NULL,
    campaign_id_date TEXT NOT NULL UNIQUE,
    google_ranking_count INTEGER DEFAULT 0,
    google_ranking_change INTEGER DEFAULT 0,
    google_local_count INTEGER DEFAULT 0,
    google_mobile_count INTEGER DEFAULT 0,
    bing_ranking_count INTEGER DEFAULT 0,
    ranking_average DECIMAL(10, 2) DEFAULT 0,
    search_volume INTEGER DEFAULT 0,
    competition DECIMAL(10, 2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Agency Analytics Campaign-Brand Links Table
CREATE TABLE IF NOT EXISTS agency_analytics_campaign_brands (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER NOT NULL REFERENCES agency_analytics_campaigns(id) ON DELETE CASCADE,
    brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    match_method TEXT NOT NULL,
    match_confidence TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(campaign_id, brand_id)
);

-- Agency Analytics Keywords Table
CREATE TABLE IF NOT EXISTS agency_analytics_keywords (
    id INTEGER PRIMARY KEY,
    campaign_id INTEGER NOT NULL REFERENCES agency_analytics_campaigns(id) ON DELETE CASCADE,
    campaign_keyword_id TEXT NOT NULL UNIQUE,
    keyword_phrase TEXT,
    primary_keyword BOOLEAN DEFAULT FALSE,
    search_location TEXT,
    search_location_formatted_name TEXT,
    search_location_region_name TEXT,
    search_location_country_code TEXT,
    search_location_latitude DECIMAL(10, 8),
    search_location_longitude DECIMAL(11, 8),
    search_language TEXT,
    tags TEXT,
    date_created TIMESTAMPTZ,
    date_modified TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Agency Analytics Keyword Rankings Table
CREATE TABLE IF NOT EXISTS agency_analytics_keyword_rankings (
    id SERIAL PRIMARY KEY,
    keyword_id INTEGER NOT NULL REFERENCES agency_analytics_keywords(id) ON DELETE CASCADE,
    campaign_id INTEGER NOT NULL REFERENCES agency_analytics_campaigns(id) ON DELETE CASCADE,
    keyword_id_date TEXT NOT NULL,
    date DATE NOT NULL,
    google_ranking INTEGER,
    google_ranking_url TEXT,
    google_mobile_ranking INTEGER,
    google_mobile_ranking_url TEXT,
    google_local_ranking INTEGER,
    bing_ranking INTEGER,
    bing_ranking_url TEXT,
    results INTEGER,
    volume INTEGER,
    competition DECIMAL(10, 2),
    field_status JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Agency Analytics Keyword Ranking Summaries Table
CREATE TABLE IF NOT EXISTS agency_analytics_keyword_ranking_summaries (
    keyword_id INTEGER PRIMARY KEY REFERENCES agency_analytics_keywords(id) ON DELETE CASCADE,
    campaign_id INTEGER NOT NULL REFERENCES agency_analytics_campaigns(id) ON DELETE CASCADE,
    keyword_phrase TEXT,
    keyword_id_date TEXT NOT NULL,
    date DATE,
    google_ranking INTEGER,
    google_ranking_url TEXT,
    google_mobile_ranking INTEGER,
    google_mobile_ranking_url TEXT,
    google_local_ranking INTEGER,
    bing_ranking INTEGER,
    bing_ranking_url TEXT,
    search_volume INTEGER,
    competition DECIMAL(10, 2),
    results INTEGER,
    field_status JSONB,
    start_date DATE,
    end_date DATE,
    start_ranking INTEGER,
    end_ranking INTEGER,
    ranking_change INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- 6. SYSTEM TABLES
-- =====================================================

-- Audit Logs Table
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    action auditlogaction NOT NULL,
    user_id VARCHAR(255),
    user_email VARCHAR(255),
    ip_address VARCHAR(45),
    user_agent TEXT,
    details JSONB,
    status VARCHAR(50),
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Sync Jobs Table
CREATE TABLE IF NOT EXISTS sync_jobs (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(255) UNIQUE NOT NULL,
    sync_type VARCHAR(50) NOT NULL,
    user_id VARCHAR(255),
    user_email VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    current_step VARCHAR(255),
    total_steps INTEGER DEFAULT 0,
    completed_steps INTEGER DEFAULT 0,
    result JSONB,
    error_message TEXT,
    parameters JSONB,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Brand KPI Selections Table
CREATE TABLE IF NOT EXISTS brand_kpi_selections (
    id SERIAL PRIMARY KEY,
    brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    selected_kpis TEXT[] NOT NULL DEFAULT '{}',
    visible_sections TEXT[] NOT NULL DEFAULT ARRAY['ga4', 'scrunch_ai', 'brand_analytics', 'advanced_analytics', 'performance_metrics'],
    selected_charts TEXT[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    version INTEGER NOT NULL DEFAULT 1,
    last_modified_by TEXT,
    UNIQUE(brand_id)
);

-- Note: client_campaigns.campaign_id references agency_analytics_campaigns which is created later
-- This is handled by PostgreSQL's deferred constraint checking or we can add the FK constraint after both tables exist
-- For now, we'll add it after agency_analytics_campaigns is created

-- =====================================================
-- 7. INDEXES
-- =====================================================

-- Brands indexes
CREATE INDEX IF NOT EXISTS idx_brands_slug ON brands(slug);
CREATE INDEX IF NOT EXISTS idx_brands_version ON brands(version);
CREATE INDEX IF NOT EXISTS idx_brands_logo_url ON brands(logo_url) WHERE logo_url IS NOT NULL;

-- Prompts indexes
CREATE INDEX IF NOT EXISTS idx_prompts_brand_id ON prompts(brand_id);
CREATE INDEX IF NOT EXISTS idx_prompts_stage ON prompts(stage);
CREATE INDEX IF NOT EXISTS idx_prompts_persona_id ON prompts(persona_id);

-- Responses indexes
CREATE INDEX IF NOT EXISTS idx_responses_brand_id ON responses(brand_id);
CREATE INDEX IF NOT EXISTS idx_responses_prompt_id ON responses(prompt_id);
CREATE INDEX IF NOT EXISTS idx_responses_platform ON responses(platform);
CREATE INDEX IF NOT EXISTS idx_responses_created_at ON responses(created_at);
CREATE INDEX IF NOT EXISTS idx_responses_stage ON responses(stage);
CREATE INDEX IF NOT EXISTS idx_responses_brand_id_created_at ON responses(brand_id, created_at);
CREATE INDEX IF NOT EXISTS idx_responses_brand_id_prompt_id ON responses(brand_id, prompt_id);

-- Citations indexes
CREATE INDEX IF NOT EXISTS idx_citations_response_id ON citations(response_id);
CREATE INDEX IF NOT EXISTS idx_citations_domain ON citations(domain);

-- GA4 Traffic Overview indexes
CREATE INDEX IF NOT EXISTS idx_ga4_traffic_brand_date ON ga4_traffic_overview(brand_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_ga4_traffic_property_date ON ga4_traffic_overview(property_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_ga4_traffic_client_date ON ga4_traffic_overview(client_id, date DESC) WHERE client_id IS NOT NULL;

-- GA4 Top Pages indexes
CREATE INDEX IF NOT EXISTS idx_ga4_pages_brand_date ON ga4_top_pages(brand_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_ga4_pages_property_date ON ga4_top_pages(property_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_ga4_pages_rank ON ga4_top_pages(brand_id, date DESC, rank);
CREATE INDEX IF NOT EXISTS idx_ga4_pages_client_date ON ga4_top_pages(client_id, date DESC) WHERE client_id IS NOT NULL;

-- GA4 Traffic Sources indexes
CREATE INDEX IF NOT EXISTS idx_ga4_sources_brand_date ON ga4_traffic_sources(brand_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_ga4_sources_property_date ON ga4_traffic_sources(property_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_ga4_sources_client_date ON ga4_traffic_sources(client_id, date DESC) WHERE client_id IS NOT NULL;

-- GA4 Geographic indexes
CREATE INDEX IF NOT EXISTS idx_ga4_geo_brand_date ON ga4_geographic(brand_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_ga4_geo_property_date ON ga4_geographic(property_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_ga4_geo_country ON ga4_geographic(country);
CREATE INDEX IF NOT EXISTS idx_ga4_geo_client_date ON ga4_geographic(client_id, date DESC) WHERE client_id IS NOT NULL;

-- GA4 Devices indexes
CREATE INDEX IF NOT EXISTS idx_ga4_devices_brand_date ON ga4_devices(brand_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_ga4_devices_property_date ON ga4_devices(property_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_ga4_devices_category ON ga4_devices(device_category);
CREATE INDEX IF NOT EXISTS idx_ga4_devices_client_date ON ga4_devices(client_id, date DESC) WHERE client_id IS NOT NULL;

-- GA4 Conversions indexes
CREATE INDEX IF NOT EXISTS idx_ga4_conversions_brand_date ON ga4_conversions(brand_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_ga4_conversions_property_date ON ga4_conversions(property_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_ga4_conversions_event ON ga4_conversions(event_name);
CREATE INDEX IF NOT EXISTS idx_ga4_conversions_client_date ON ga4_conversions(client_id, date DESC) WHERE client_id IS NOT NULL;

-- GA4 Realtime indexes
CREATE INDEX IF NOT EXISTS idx_ga4_realtime_brand ON ga4_realtime(brand_id, snapshot_time DESC);
CREATE INDEX IF NOT EXISTS idx_ga4_realtime_property ON ga4_realtime(property_id, snapshot_time DESC);
CREATE INDEX IF NOT EXISTS idx_ga4_realtime_client ON ga4_realtime(client_id, snapshot_time DESC) WHERE client_id IS NOT NULL;

-- GA4 Property Details indexes
CREATE INDEX IF NOT EXISTS idx_ga4_property_details_brand ON ga4_property_details(brand_id);
CREATE INDEX IF NOT EXISTS idx_ga4_property_details_property ON ga4_property_details(property_id);
CREATE INDEX IF NOT EXISTS idx_ga4_property_details_client ON ga4_property_details(client_id) WHERE client_id IS NOT NULL;

-- GA4 Revenue indexes
CREATE INDEX IF NOT EXISTS idx_ga4_revenue_brand_date ON ga4_revenue(brand_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_ga4_revenue_property_date ON ga4_revenue(property_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_ga4_revenue_client_date ON ga4_revenue(client_id, date DESC) WHERE client_id IS NOT NULL;

-- GA4 Daily Conversions indexes
CREATE INDEX IF NOT EXISTS idx_ga4_daily_conversions_brand_date ON ga4_daily_conversions(brand_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_ga4_daily_conversions_property_date ON ga4_daily_conversions(property_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_ga4_daily_conversions_client_date ON ga4_daily_conversions(client_id, date DESC) WHERE client_id IS NOT NULL;

-- GA4 KPI Snapshots indexes
CREATE INDEX IF NOT EXISTS idx_ga4_kpi_snapshots_brand_date ON ga4_kpi_snapshots(brand_id, period_end_date DESC);
CREATE INDEX IF NOT EXISTS idx_ga4_kpi_snapshots_property_date ON ga4_kpi_snapshots(property_id, period_end_date DESC);
CREATE INDEX IF NOT EXISTS idx_ga4_kpi_snapshots_client_date ON ga4_kpi_snapshots(client_id, period_end_date DESC) WHERE client_id IS NOT NULL;

-- GA4 Tokens indexes
CREATE INDEX IF NOT EXISTS idx_ga4_tokens_expires_at ON ga4_tokens(expires_at DESC);
CREATE INDEX IF NOT EXISTS idx_ga4_tokens_active ON ga4_tokens(is_active) WHERE is_active = TRUE;

-- Agency Analytics Campaigns indexes
CREATE INDEX IF NOT EXISTS idx_aa_campaigns_company ON agency_analytics_campaigns(company);
CREATE INDEX IF NOT EXISTS idx_aa_campaigns_status ON agency_analytics_campaigns(status);

-- Agency Analytics Campaign Rankings indexes
CREATE INDEX IF NOT EXISTS idx_aa_campaign_rankings_campaign_id ON agency_analytics_campaign_rankings(campaign_id);
CREATE INDEX IF NOT EXISTS idx_aa_campaign_rankings_date ON agency_analytics_campaign_rankings(date);
CREATE INDEX IF NOT EXISTS idx_aa_campaign_rankings_campaign_id_date ON agency_analytics_campaign_rankings(campaign_id_date);
CREATE INDEX IF NOT EXISTS idx_aa_campaign_rankings_client_name ON agency_analytics_campaign_rankings(client_name);

-- Agency Analytics Campaign-Brand Links indexes
CREATE INDEX IF NOT EXISTS idx_aa_campaign_brands_campaign_id ON agency_analytics_campaign_brands(campaign_id);
CREATE INDEX IF NOT EXISTS idx_aa_campaign_brands_brand_id ON agency_analytics_campaign_brands(brand_id);
CREATE INDEX IF NOT EXISTS idx_aa_campaign_brands_match_method ON agency_analytics_campaign_brands(match_method);

-- Agency Analytics Keywords indexes
CREATE INDEX IF NOT EXISTS idx_aa_keywords_campaign_id ON agency_analytics_keywords(campaign_id);
CREATE INDEX IF NOT EXISTS idx_aa_keywords_campaign_keyword_id ON agency_analytics_keywords(campaign_keyword_id);
CREATE INDEX IF NOT EXISTS idx_aa_keywords_keyword_phrase ON agency_analytics_keywords(keyword_phrase);
CREATE INDEX IF NOT EXISTS idx_aa_keywords_primary_keyword ON agency_analytics_keywords(primary_keyword);

-- Agency Analytics Keyword Rankings indexes
CREATE INDEX IF NOT EXISTS idx_aa_keyword_rankings_keyword_id ON agency_analytics_keyword_rankings(keyword_id);
CREATE INDEX IF NOT EXISTS idx_aa_keyword_rankings_campaign_id ON agency_analytics_keyword_rankings(campaign_id);
CREATE INDEX IF NOT EXISTS idx_aa_keyword_rankings_date ON agency_analytics_keyword_rankings(date);
CREATE INDEX IF NOT EXISTS idx_aa_keyword_rankings_keyword_id_date ON agency_analytics_keyword_rankings(keyword_id_date);

-- Agency Analytics Keyword Ranking Summaries indexes
CREATE INDEX IF NOT EXISTS idx_aa_keyword_summaries_campaign_id ON agency_analytics_keyword_ranking_summaries(campaign_id);
CREATE INDEX IF NOT EXISTS idx_aa_keyword_summaries_keyword_id_date ON agency_analytics_keyword_ranking_summaries(keyword_id_date);

-- Clients indexes
CREATE INDEX IF NOT EXISTS idx_clients_company_name ON clients(company_name);
CREATE INDEX IF NOT EXISTS idx_clients_company_id ON clients(company_id);
CREATE INDEX IF NOT EXISTS idx_clients_url_slug ON clients(url_slug);
CREATE INDEX IF NOT EXISTS idx_clients_ga4_property_id ON clients(ga4_property_id);
CREATE INDEX IF NOT EXISTS idx_clients_scrunch_brand_id ON clients(scrunch_brand_id);
CREATE INDEX IF NOT EXISTS idx_clients_company_domain ON clients(company_domain);
CREATE INDEX IF NOT EXISTS idx_clients_version ON clients(version);

-- Client-Campaign Links indexes
CREATE INDEX IF NOT EXISTS idx_client_campaigns_client_id ON client_campaigns(client_id);
CREATE INDEX IF NOT EXISTS idx_client_campaigns_campaign_id ON client_campaigns(campaign_id);
CREATE INDEX IF NOT EXISTS idx_client_campaigns_primary ON client_campaigns(client_id, is_primary) WHERE is_primary = TRUE;

-- Audit Logs indexes
CREATE INDEX IF NOT EXISTS ix_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS ix_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS ix_audit_logs_user_email ON audit_logs(user_email);
CREATE INDEX IF NOT EXISTS ix_audit_logs_status ON audit_logs(status);
CREATE INDEX IF NOT EXISTS ix_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS ix_audit_logs_user_action_date ON audit_logs(user_email, action, created_at DESC);

-- Sync Jobs indexes
CREATE INDEX IF NOT EXISTS ix_sync_jobs_job_id ON sync_jobs(job_id);
CREATE INDEX IF NOT EXISTS ix_sync_jobs_user_email ON sync_jobs(user_email);
CREATE INDEX IF NOT EXISTS ix_sync_jobs_status ON sync_jobs(status);
CREATE INDEX IF NOT EXISTS ix_sync_jobs_sync_type ON sync_jobs(sync_type);
CREATE INDEX IF NOT EXISTS ix_sync_jobs_created_at ON sync_jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS ix_sync_jobs_user_status ON sync_jobs(user_email, status, created_at DESC);

-- Brand KPI Selections indexes
CREATE INDEX IF NOT EXISTS idx_brand_kpi_selections_brand_id ON brand_kpi_selections(brand_id);
CREATE INDEX IF NOT EXISTS idx_brand_kpi_selections_version ON brand_kpi_selections(version);

-- Add foreign key constraint for client_campaigns.campaign_id after agency_analytics_campaigns is created
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'agency_analytics_campaigns') THEN
        -- Add FK constraint if it doesn't exist
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.table_constraints 
            WHERE constraint_name = 'client_campaigns_campaign_id_fkey'
        ) THEN
            ALTER TABLE client_campaigns 
            ADD CONSTRAINT client_campaigns_campaign_id_fkey 
            FOREIGN KEY (campaign_id) REFERENCES agency_analytics_campaigns(id) ON DELETE CASCADE;
        END IF;
    END IF;
END $$;

-- =====================================================
-- 8. FUNCTIONS
-- =====================================================

-- Generate slug function
CREATE OR REPLACE FUNCTION generate_slug(input_text TEXT)
RETURNS TEXT AS $$
BEGIN
  RETURN lower(regexp_replace(regexp_replace(input_text, '[^a-zA-Z0-9\s-]', '', 'g'), '\s+', '-', 'g'));
END;
$$ LANGUAGE plpgsql;

-- Generate brand slug function (UUID-based)
CREATE OR REPLACE FUNCTION generate_brand_slug()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.slug IS NULL OR NEW.slug = '' THEN
    NEW.slug := gen_random_uuid()::TEXT;
    WHILE EXISTS (
      SELECT 1 FROM brands 
      WHERE slug = NEW.slug 
      AND (TG_OP = 'INSERT' OR id != NEW.id)
    ) LOOP
      NEW.slug := gen_random_uuid()::TEXT;
    END LOOP;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Generate client slug function
CREATE OR REPLACE FUNCTION generate_client_slug()
RETURNS TEXT AS $$
DECLARE
    slug TEXT;
    uuid_part TEXT;
BEGIN
    uuid_part := replace(lower(gen_random_uuid()::TEXT), '-', '');
    slug := uuid_part;
    WHILE EXISTS (SELECT 1 FROM clients WHERE url_slug = slug) LOOP
        uuid_part := replace(lower(gen_random_uuid()::TEXT), '-', '');
        slug := uuid_part;
    END LOOP;
    RETURN slug;
END;
$$ LANGUAGE plpgsql;

-- Auto-generate client slug function
CREATE OR REPLACE FUNCTION auto_generate_client_slug()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.url_slug IS NULL OR NEW.url_slug = '' THEN
        NEW.url_slug := generate_client_slug();
    END IF;
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Increment brand version function
CREATE OR REPLACE FUNCTION increment_brand_version()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.version IS NULL THEN
        NEW.version := 1;
    ELSIF (OLD.ga4_property_id IS DISTINCT FROM NEW.ga4_property_id OR
           OLD.theme IS DISTINCT FROM NEW.theme OR
           OLD.logo_url IS DISTINCT FROM NEW.logo_url) THEN
        NEW.version := OLD.version + 1;
    ELSE
        NEW.version := OLD.version;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Increment client version function
CREATE OR REPLACE FUNCTION increment_client_version()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.version IS NULL THEN
        NEW.version := 1;
    ELSIF (OLD.ga4_property_id IS DISTINCT FROM NEW.ga4_property_id OR
           OLD.scrunch_brand_id IS DISTINCT FROM NEW.scrunch_brand_id OR
           OLD.theme_color IS DISTINCT FROM NEW.theme_color OR
           OLD.logo_url IS DISTINCT FROM NEW.logo_url OR
           OLD.secondary_color IS DISTINCT FROM NEW.secondary_color OR
           OLD.font_family IS DISTINCT FROM NEW.font_family OR
           OLD.favicon_url IS DISTINCT FROM NEW.favicon_url OR
           OLD.report_title IS DISTINCT FROM NEW.report_title OR
           OLD.company_domain IS DISTINCT FROM NEW.company_domain OR
           OLD.custom_css IS DISTINCT FROM NEW.custom_css OR
           OLD.footer_text IS DISTINCT FROM NEW.footer_text OR
           OLD.header_text IS DISTINCT FROM NEW.header_text) THEN
        NEW.version := OLD.version + 1;
    ELSE
        NEW.version := OLD.version;
    END IF;
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Increment brand KPI selections version function
CREATE OR REPLACE FUNCTION increment_brand_kpi_selections_version()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.version IS NULL THEN
        NEW.version := 1;
    ELSIF (OLD.selected_kpis IS DISTINCT FROM NEW.selected_kpis OR
           OLD.visible_sections IS DISTINCT FROM NEW.visible_sections OR
           OLD.selected_charts IS DISTINCT FROM NEW.selected_charts) THEN
        NEW.version := OLD.version + 1;
    ELSE
        NEW.version := OLD.version;
    END IF;
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Update sync jobs updated_at function
CREATE OR REPLACE FUNCTION update_sync_jobs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Update brand KPI selections updated_at function
CREATE OR REPLACE FUNCTION update_brand_kpi_selections_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 9. TRIGGERS
-- =====================================================

-- Brand slug generation trigger
DROP TRIGGER IF EXISTS trigger_generate_brand_slug ON brands;
CREATE TRIGGER trigger_generate_brand_slug
  BEFORE INSERT OR UPDATE ON brands
  FOR EACH ROW
  EXECUTE FUNCTION generate_brand_slug();

-- Brand version increment trigger
DROP TRIGGER IF EXISTS trigger_increment_brand_version ON brands;
CREATE TRIGGER trigger_increment_brand_version
    BEFORE UPDATE ON brands
    FOR EACH ROW
    EXECUTE FUNCTION increment_brand_version();

-- Client slug generation trigger
DROP TRIGGER IF EXISTS trigger_auto_generate_client_slug ON clients;
CREATE TRIGGER trigger_auto_generate_client_slug
    BEFORE INSERT OR UPDATE ON clients
    FOR EACH ROW
    EXECUTE FUNCTION auto_generate_client_slug();

-- Client version increment trigger
DROP TRIGGER IF EXISTS trigger_increment_client_version ON clients;
CREATE TRIGGER trigger_increment_client_version
    BEFORE UPDATE ON clients
    FOR EACH ROW
    EXECUTE FUNCTION increment_client_version();

-- Sync jobs updated_at trigger
DROP TRIGGER IF EXISTS sync_jobs_updated_at ON sync_jobs;
CREATE TRIGGER sync_jobs_updated_at
    BEFORE UPDATE ON sync_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_sync_jobs_updated_at();

-- Brand KPI selections updated_at trigger
DROP TRIGGER IF EXISTS trigger_update_brand_kpi_selections_updated_at ON brand_kpi_selections;
CREATE TRIGGER trigger_update_brand_kpi_selections_updated_at
    BEFORE UPDATE ON brand_kpi_selections
    FOR EACH ROW
    EXECUTE FUNCTION update_brand_kpi_selections_updated_at();

-- Brand KPI selections version increment trigger
DROP TRIGGER IF EXISTS trigger_increment_brand_kpi_selections_version ON brand_kpi_selections;
CREATE TRIGGER trigger_increment_brand_kpi_selections_version
    BEFORE UPDATE ON brand_kpi_selections
    FOR EACH ROW
    EXECUTE FUNCTION increment_brand_kpi_selections_version();

-- =====================================================
-- 10. COMMENTS FOR DOCUMENTATION
-- =====================================================

COMMENT ON TABLE brands IS 'Brands from Scrunch AI';
COMMENT ON COLUMN brands.slug IS 'URL-friendly identifier for public brand reporting dashboard access (UUID-based)';
COMMENT ON COLUMN brands.logo_url IS 'URL to the brand logo image';
COMMENT ON COLUMN brands.theme IS 'Brand theme configuration (colors, fonts, etc.) stored as JSON';
COMMENT ON COLUMN brands.version IS 'Version number for optimistic locking. Increments on each update to ga4_property_id, theme, or logo_url.';
COMMENT ON COLUMN brands.last_modified_by IS 'Email of user who last modified this brand record.';

COMMENT ON TABLE prompts IS 'Prompts from Scrunch AI';
COMMENT ON TABLE responses IS 'Responses from Scrunch AI';
COMMENT ON TABLE citations IS 'Citations from responses';

COMMENT ON TABLE ga4_traffic_overview IS 'Daily GA4 traffic overview metrics';
COMMENT ON TABLE ga4_top_pages IS 'Top performing pages from GA4';
COMMENT ON TABLE ga4_traffic_sources IS 'Traffic acquisition sources from GA4';
COMMENT ON TABLE ga4_geographic IS 'Geographic breakdown by country from GA4';
COMMENT ON TABLE ga4_devices IS 'Device and platform breakdown from GA4';
COMMENT ON TABLE ga4_conversions IS 'Conversion events from GA4';
COMMENT ON TABLE ga4_realtime IS 'Realtime snapshot data from GA4';
COMMENT ON TABLE ga4_property_details IS 'Static GA4 property configuration details';
COMMENT ON TABLE ga4_revenue IS 'Daily revenue data from GA4';
COMMENT ON TABLE ga4_daily_conversions IS 'Daily aggregated conversions from GA4';
COMMENT ON TABLE ga4_kpi_snapshots IS 'Pre-calculated GA4 KPIs for 30-day periods to speed up dashboard API calls';
COMMENT ON TABLE ga4_tokens IS 'Stores GA4 access tokens for daily authentication';

COMMENT ON TABLE agency_analytics_campaign_rankings IS 'Stores monthly campaign ranking data from Agency Analytics API';
COMMENT ON TABLE agency_analytics_campaigns IS 'Stores campaign metadata from Agency Analytics API';
COMMENT ON TABLE agency_analytics_campaign_brands IS 'Links Agency Analytics campaigns to brands based on URL matching';
COMMENT ON TABLE agency_analytics_keywords IS 'Stores keywords for Agency Analytics campaigns';
COMMENT ON TABLE agency_analytics_keyword_rankings IS 'Stores daily keyword ranking data from Agency Analytics API';
COMMENT ON TABLE agency_analytics_keyword_ranking_summaries IS 'Stores latest keyword ranking data with change calculations';

COMMENT ON TABLE clients IS 'Client entities created from Agency Analytics campaigns, used for whitelabeling reports';
COMMENT ON TABLE client_campaigns IS 'Links clients to their Agency Analytics campaigns (many-to-many relationship)';
COMMENT ON COLUMN clients.url_slug IS 'URL-friendly identifier for whitelabeled reports (UUID-based for security)';
COMMENT ON COLUMN clients.version IS 'Version number for optimistic locking. Increments on each update to editable fields.';
COMMENT ON COLUMN clients.last_modified_by IS 'Email of user who last modified this client record.';

COMMENT ON TABLE audit_logs IS 'Audit log table for tracking user actions, logins, and data sync operations';
COMMENT ON TABLE sync_jobs IS 'Tracks async sync job status and progress';
COMMENT ON TABLE brand_kpi_selections IS 'Stores KPI and section visibility preferences for each brand';
COMMENT ON COLUMN brand_kpi_selections.selected_kpis IS 'Array of KPI keys that should be visible in public view. If empty or NULL, all available KPIs are shown.';
COMMENT ON COLUMN brand_kpi_selections.visible_sections IS 'Array of section keys that should be visible in public view. Default: all sections visible.';
COMMENT ON COLUMN brand_kpi_selections.selected_charts IS 'Array of chart keys that should be visible in public view. If empty, no charts are shown.';
COMMENT ON COLUMN brand_kpi_selections.version IS 'Version number for optimistic locking. Increments on each update to selected_kpis, visible_sections, or selected_charts.';
COMMENT ON COLUMN brand_kpi_selections.last_modified_by IS 'Email of user who last modified this KPI selection record.';

-- =====================================================
-- SETUP COMPLETE!
-- =====================================================
-- This consolidated migration includes all schema changes from v1 through v19
-- All tables, columns, indexes, triggers, and functions are included
-- =====================================================


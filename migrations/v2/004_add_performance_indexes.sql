-- =====================================================
-- V2 Migration: Add Performance Indexes for Common Queries
-- =====================================================
-- This migration adds composite indexes for frequently used query patterns
-- to optimize read performance and reduce query latency.
-- =====================================================

-- Composite index for responses queries with brand_id and date range
-- Used in: get_responses with brand_id and date filters
CREATE INDEX IF NOT EXISTS idx_responses_brand_id_platform_created_at 
ON responses(brand_id, platform, created_at DESC) 
WHERE brand_id IS NOT NULL;

-- Composite index for prompts queries with brand_id and stage
-- Used in: get_prompts with brand_id and stage filters
CREATE INDEX IF NOT EXISTS idx_prompts_brand_id_stage 
ON prompts(brand_id, stage) 
WHERE brand_id IS NOT NULL;

-- Composite index for clients search queries
-- Used in: get_clients with search filter (company_name, company_domain, url)
CREATE INDEX IF NOT EXISTS idx_clients_search 
ON clients(company_name, company_domain, url) 
WHERE company_name IS NOT NULL;

-- Composite index for GA4 traffic overview queries with date range
-- Used in: get_ga4_traffic_overview_by_date_range
CREATE INDEX IF NOT EXISTS idx_ga4_traffic_brand_property_date_range 
ON ga4_traffic_overview(brand_id, property_id, date DESC) 
WHERE brand_id IS NOT NULL AND property_id IS NOT NULL;

-- Composite index for GA4 top pages queries with date range and rank
-- Used in: get_ga4_top_pages_by_date_range
CREATE INDEX IF NOT EXISTS idx_ga4_pages_brand_property_date_rank 
ON ga4_top_pages(brand_id, property_id, date DESC, rank) 
WHERE brand_id IS NOT NULL AND property_id IS NOT NULL;

-- Composite index for Agency Analytics keyword rankings queries
-- Used in: queries filtering by keyword_id and date
CREATE INDEX IF NOT EXISTS idx_aa_keyword_rankings_keyword_date 
ON agency_analytics_keyword_rankings(keyword_id, date DESC) 
WHERE keyword_id IS NOT NULL;

-- Composite index for Agency Analytics campaign rankings queries
-- Used in: queries filtering by campaign_id and date
CREATE INDEX IF NOT EXISTS idx_aa_campaign_rankings_campaign_date 
ON agency_analytics_campaign_rankings(campaign_id, date DESC) 
WHERE campaign_id IS NOT NULL;

-- Composite index for sync_jobs queries with user_email and status
-- Used in: get_user_jobs with status filter
CREATE INDEX IF NOT EXISTS idx_sync_jobs_user_status_created 
ON sync_jobs(user_email, status, created_at DESC) 
WHERE user_email IS NOT NULL;

-- Composite index for audit_logs queries with user_email and action
-- Used in: audit log queries filtering by user and action
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_action_created 
ON audit_logs(user_email, action, created_at DESC) 
WHERE user_email IS NOT NULL;

-- Index for brands queries with ga4_property_id filter
-- Used in: get_brands_with_ga4
CREATE INDEX IF NOT EXISTS idx_brands_ga4_property_id 
ON brands(ga4_property_id) 
WHERE ga4_property_id IS NOT NULL;

-- Comments for documentation
COMMENT ON INDEX idx_responses_brand_id_platform_created_at IS 'Composite index for responses queries with brand_id, platform, and date range filters';
COMMENT ON INDEX idx_prompts_brand_id_stage IS 'Composite index for prompts queries with brand_id and stage filters';
COMMENT ON INDEX idx_clients_search IS 'Composite index for clients search queries on company_name, company_domain, and url';
COMMENT ON INDEX idx_ga4_traffic_brand_property_date_range IS 'Composite index for GA4 traffic overview queries with brand_id, property_id, and date range';
COMMENT ON INDEX idx_ga4_pages_brand_property_date_rank IS 'Composite index for GA4 top pages queries with brand_id, property_id, date, and rank';
COMMENT ON INDEX idx_aa_keyword_rankings_keyword_date IS 'Composite index for Agency Analytics keyword rankings queries with keyword_id and date';
COMMENT ON INDEX idx_aa_campaign_rankings_campaign_date IS 'Composite index for Agency Analytics campaign rankings queries with campaign_id and date';
COMMENT ON INDEX idx_sync_jobs_user_status_created IS 'Composite index for sync_jobs queries with user_email, status, and created_at';
COMMENT ON INDEX idx_audit_logs_user_action_created IS 'Composite index for audit_logs queries with user_email, action, and created_at';
COMMENT ON INDEX idx_brands_ga4_property_id IS 'Index for brands queries filtering by ga4_property_id';


-- =====================================================
-- V2 Migration: Update Agency Analytics INTEGER columns to BIGINT
-- =====================================================
-- This migration fixes integer overflow errors by changing
-- INTEGER columns to BIGINT for columns that can exceed
-- the INTEGER limit (2,147,483,647)
-- =====================================================

-- Agency Analytics Campaigns Table
-- Change id from INTEGER to BIGINT (campaign IDs can be very large)
ALTER TABLE IF EXISTS agency_analytics_campaigns 
    ALTER COLUMN id TYPE BIGINT;

-- Change foreign key columns that reference campaign_id
ALTER TABLE IF EXISTS agency_analytics_campaign_rankings 
    ALTER COLUMN campaign_id TYPE BIGINT;

ALTER TABLE IF EXISTS agency_analytics_campaign_brands 
    ALTER COLUMN campaign_id TYPE BIGINT;

ALTER TABLE IF EXISTS agency_analytics_keywords 
    ALTER COLUMN campaign_id TYPE BIGINT;

ALTER TABLE IF EXISTS agency_analytics_keyword_rankings 
    ALTER COLUMN campaign_id TYPE BIGINT;

ALTER TABLE IF EXISTS agency_analytics_keyword_ranking_summaries 
    ALTER COLUMN campaign_id TYPE BIGINT;

-- Change other INTEGER columns that might exceed limits
ALTER TABLE IF EXISTS agency_analytics_campaigns 
    ALTER COLUMN campaign_group_id TYPE BIGINT,
    ALTER COLUMN company_id TYPE BIGINT,
    ALTER COLUMN account_id TYPE BIGINT;

-- Agency Analytics Keywords Table
-- Change id from INTEGER to BIGINT (keyword IDs can be very large)
ALTER TABLE IF EXISTS agency_analytics_keywords 
    ALTER COLUMN id TYPE BIGINT;

-- Change foreign key columns that reference keyword_id
ALTER TABLE IF EXISTS agency_analytics_keyword_rankings 
    ALTER COLUMN keyword_id TYPE BIGINT;

ALTER TABLE IF EXISTS agency_analytics_keyword_ranking_summaries 
    ALTER COLUMN keyword_id TYPE BIGINT;

-- Change volume/search_volume columns to BIGINT (can exceed INTEGER limit)
ALTER TABLE IF EXISTS agency_analytics_campaign_rankings 
    ALTER COLUMN search_volume TYPE BIGINT;

ALTER TABLE IF EXISTS agency_analytics_keyword_rankings 
    ALTER COLUMN volume TYPE BIGINT;

ALTER TABLE IF EXISTS agency_analytics_keyword_ranking_summaries 
    ALTER COLUMN search_volume TYPE BIGINT;

-- Change results column to BIGINT (can exceed INTEGER limit)
ALTER TABLE IF EXISTS agency_analytics_keyword_rankings 
    ALTER COLUMN results TYPE BIGINT;

ALTER TABLE IF EXISTS agency_analytics_keyword_ranking_summaries 
    ALTER COLUMN results TYPE BIGINT;

-- Comments
COMMENT ON COLUMN agency_analytics_campaigns.id IS 'Campaign ID from API (BIGINT to support large values)';
COMMENT ON COLUMN agency_analytics_keywords.id IS 'Keyword ID from API (BIGINT to support large values)';
COMMENT ON COLUMN agency_analytics_campaign_rankings.search_volume IS 'Search volume (BIGINT to support large values)';
COMMENT ON COLUMN agency_analytics_keyword_rankings.volume IS 'Search volume (BIGINT to support large values)';
COMMENT ON COLUMN agency_analytics_keyword_ranking_summaries.search_volume IS 'Search volume (BIGINT to support large values)';


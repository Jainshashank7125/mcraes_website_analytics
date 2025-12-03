-- =====================================================
-- V2 Migration: Drop Unique Constraint on keyword_id_date
-- =====================================================
-- This migration drops the unique constraint on keyword_id_date
-- in the agency_analytics_keyword_rankings table.
-- =====================================================

-- Drop the unique constraint on keyword_id_date
ALTER TABLE agency_analytics_keyword_rankings
DROP CONSTRAINT IF EXISTS agency_analytics_keyword_rankings_keyword_id_date_key;

-- Note: The index idx_aa_keyword_rankings_keyword_id_date will remain
-- as a non-unique index for query performance

-- Comments for documentation
COMMENT ON COLUMN agency_analytics_keyword_rankings.keyword_id_date IS 'Composite identifier: keyword_id-date (no longer unique, allows multiple entries per keyword per date)';


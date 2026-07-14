-- =====================================================
-- Add is_active / deactivated_at columns to agency_analytics_keywords
-- For soft-delete of keywords removed on the Agency Analytics platform.
--
-- Agency Analytics purges deleted keywords from all history, so its dashboards
-- stay flat. We previously kept the historical ranking rows for deleted keywords
-- forever, which produced phantom "cliffs" in our Google Rankings charts. Sync
-- reconciliation now marks keywords no longer returned by the API as inactive,
-- and all keyword charts/counts filter to is_active = TRUE.
-- =====================================================

-- Add is_active column with default true (existing keywords stay active until
-- the next sync reconciliation determines otherwise)
ALTER TABLE agency_analytics_keywords
ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;

-- Timestamp of when a keyword was last marked inactive (NULL while active)
ALTER TABLE agency_analytics_keywords
ADD COLUMN IF NOT EXISTS deactivated_at TIMESTAMPTZ;

-- Ensure any pre-existing rows are active
UPDATE agency_analytics_keywords
SET is_active = TRUE
WHERE is_active IS NULL;

-- Partial index for the common "active keywords" filter used by charts/counts
CREATE INDEX IF NOT EXISTS idx_aa_keywords_is_active
ON agency_analytics_keywords(is_active) WHERE is_active = TRUE;

-- Composite index for the frequent (campaign_id, is_active) filter
CREATE INDEX IF NOT EXISTS idx_aa_keywords_campaign_active
ON agency_analytics_keywords(campaign_id, is_active);

COMMENT ON COLUMN agency_analytics_keywords.is_active IS 'Soft-delete flag. FALSE = keyword no longer exists on the Agency Analytics platform; hidden from charts/counts but rows preserved. Defaults TRUE.';
COMMENT ON COLUMN agency_analytics_keywords.deactivated_at IS 'When the keyword was last marked inactive by sync reconciliation. NULL while active.';

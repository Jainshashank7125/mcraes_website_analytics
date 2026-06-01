-- =====================================================
-- Migration v31: Store conversions/conversion_rate in ga4_traffic_sources
--                and engagement_rate in ga4_geographic
--
-- Motivation:
--   1. GA4 API already returns conversions + conversionRate per channel; the
--      DB layer was silently discarding them. This adds the columns so the
--      data can be persisted (no UI change required).
--   2. GA4 API already returns engagementRate per country/date; the DB layer
--      was discarding it and always returning 0.0.  This adds the column.
--
-- Safe to re-run: all statements are idempotent (ADD COLUMN IF NOT EXISTS).
-- =====================================================

-- 1. ga4_traffic_sources: conversions + conversion_rate
ALTER TABLE ga4_traffic_sources
    ADD COLUMN IF NOT EXISTS conversions     DECIMAL(10,2) DEFAULT 0,
    ADD COLUMN IF NOT EXISTS conversion_rate DECIMAL(8,6)  DEFAULT 0;

-- 2. ga4_geographic: engagement_rate
ALTER TABLE ga4_geographic
    ADD COLUMN IF NOT EXISTS engagement_rate DECIMAL(5,4) DEFAULT 0;

-- 3. Indexes (cover the most common aggregation queries)
CREATE INDEX IF NOT EXISTS idx_ga4_sources_conversions
    ON ga4_traffic_sources(property_id, date DESC, conversions DESC);

CREATE INDEX IF NOT EXISTS idx_ga4_geo_engagement
    ON ga4_geographic(property_id, date DESC, engagement_rate);

-- =====================================================
-- Migration v31 complete
-- =====================================================

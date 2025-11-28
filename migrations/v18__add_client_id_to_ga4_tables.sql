-- =====================================================
-- Migration: Add client_id to GA4 tables
-- Migrates GA4 data from brand-centric to client-centric
-- =====================================================
-- Run this in your Supabase SQL Editor
-- =====================================================

-- Step 1: Add client_id column to all GA4 tables
ALTER TABLE ga4_traffic_overview ADD COLUMN IF NOT EXISTS client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE;
ALTER TABLE ga4_top_pages ADD COLUMN IF NOT EXISTS client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE;
ALTER TABLE ga4_traffic_sources ADD COLUMN IF NOT EXISTS client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE;
ALTER TABLE ga4_geographic ADD COLUMN IF NOT EXISTS client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE;
ALTER TABLE ga4_devices ADD COLUMN IF NOT EXISTS client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE;
ALTER TABLE ga4_conversions ADD COLUMN IF NOT EXISTS client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE;
ALTER TABLE ga4_realtime ADD COLUMN IF NOT EXISTS client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE;
ALTER TABLE ga4_property_details ADD COLUMN IF NOT EXISTS client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE;
ALTER TABLE ga4_revenue ADD COLUMN IF NOT EXISTS client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE;
ALTER TABLE ga4_daily_conversions ADD COLUMN IF NOT EXISTS client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE;

-- Step 2: Migrate existing data
-- Link GA4 records to clients via brand_id -> scrunch_brand_id
UPDATE ga4_traffic_overview 
SET client_id = (
    SELECT id FROM clients 
    WHERE clients.scrunch_brand_id = ga4_traffic_overview.brand_id 
    LIMIT 1
)
WHERE client_id IS NULL;

UPDATE ga4_top_pages 
SET client_id = (
    SELECT id FROM clients 
    WHERE clients.scrunch_brand_id = ga4_top_pages.brand_id 
    LIMIT 1
)
WHERE client_id IS NULL;

UPDATE ga4_traffic_sources 
SET client_id = (
    SELECT id FROM clients 
    WHERE clients.scrunch_brand_id = ga4_traffic_sources.brand_id 
    LIMIT 1
)
WHERE client_id IS NULL;

UPDATE ga4_geographic 
SET client_id = (
    SELECT id FROM clients 
    WHERE clients.scrunch_brand_id = ga4_geographic.brand_id 
    LIMIT 1
)
WHERE client_id IS NULL;

UPDATE ga4_devices 
SET client_id = (
    SELECT id FROM clients 
    WHERE clients.scrunch_brand_id = ga4_devices.brand_id 
    LIMIT 1
)
WHERE client_id IS NULL;

UPDATE ga4_conversions 
SET client_id = (
    SELECT id FROM clients 
    WHERE clients.scrunch_brand_id = ga4_conversions.brand_id 
    LIMIT 1
)
WHERE client_id IS NULL;

UPDATE ga4_realtime 
SET client_id = (
    SELECT id FROM clients 
    WHERE clients.scrunch_brand_id = ga4_realtime.brand_id 
    LIMIT 1
)
WHERE client_id IS NULL;

UPDATE ga4_property_details 
SET client_id = (
    SELECT id FROM clients 
    WHERE clients.scrunch_brand_id = ga4_property_details.brand_id 
    LIMIT 1
)
WHERE client_id IS NULL;

UPDATE ga4_revenue 
SET client_id = (
    SELECT id FROM clients 
    WHERE clients.scrunch_brand_id = ga4_revenue.brand_id 
    LIMIT 1
)
WHERE client_id IS NULL;

UPDATE ga4_daily_conversions 
SET client_id = (
    SELECT id FROM clients 
    WHERE clients.scrunch_brand_id = ga4_daily_conversions.brand_id 
    LIMIT 1
)
WHERE client_id IS NULL;

-- Step 3: Update unique constraints to include client_id
-- Note: We keep brand_id in constraints for backward compatibility during transition

-- Step 4: Add indexes for client_id
CREATE INDEX IF NOT EXISTS idx_ga4_traffic_client_date ON ga4_traffic_overview(client_id, date DESC) WHERE client_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_ga4_pages_client_date ON ga4_top_pages(client_id, date DESC) WHERE client_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_ga4_sources_client_date ON ga4_traffic_sources(client_id, date DESC) WHERE client_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_ga4_geo_client_date ON ga4_geographic(client_id, date DESC) WHERE client_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_ga4_devices_client_date ON ga4_devices(client_id, date DESC) WHERE client_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_ga4_conversions_client_date ON ga4_conversions(client_id, date DESC) WHERE client_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_ga4_realtime_client ON ga4_realtime(client_id, snapshot_time DESC) WHERE client_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_ga4_property_details_client ON ga4_property_details(client_id) WHERE client_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_ga4_revenue_client_date ON ga4_revenue(client_id, date DESC) WHERE client_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_ga4_daily_conversions_client_date ON ga4_daily_conversions(client_id, date DESC) WHERE client_id IS NOT NULL;

-- =====================================================
-- Migration Complete!
-- =====================================================
-- Note: brand_id columns are kept for backward compatibility
-- New syncs should use client_id
-- =====================================================


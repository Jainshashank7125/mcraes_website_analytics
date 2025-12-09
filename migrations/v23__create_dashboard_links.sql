-- =====================================================
-- Create dashboard_links table for shareable reporting links
-- Each client can have multiple links with unique date ranges
-- =====================================================
-- Run this in your Supabase/PostgreSQL SQL editor
-- =====================================================

CREATE TABLE IF NOT EXISTS dashboard_links (
    id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    slug TEXT NOT NULL UNIQUE,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Prevent duplicate date ranges per client
CREATE UNIQUE INDEX IF NOT EXISTS uq_dashboard_links_client_dates
    ON dashboard_links (client_id, start_date, end_date);

-- Helpful indexes for lookups
CREATE INDEX IF NOT EXISTS idx_dashboard_links_client_enabled
    ON dashboard_links (client_id, enabled);

CREATE INDEX IF NOT EXISTS idx_dashboard_links_expires_at
    ON dashboard_links (expires_at);

COMMENT ON TABLE dashboard_links IS 'Shareable dashboard links per client, keyed by slug and date range';
COMMENT ON COLUMN dashboard_links.slug IS 'Public slug used for the shareable dashboard URL';
COMMENT ON COLUMN dashboard_links.enabled IS 'Whether the link is currently active';
COMMENT ON COLUMN dashboard_links.expires_at IS 'When set, the link is automatically treated as disabled after this timestamp';

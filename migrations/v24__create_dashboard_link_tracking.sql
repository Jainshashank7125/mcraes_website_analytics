-- =====================================================
-- Create dashboard_link_tracking table for tracking link opens
-- Add optional name and description fields to dashboard_links
-- =====================================================
-- Run this in your Supabase/PostgreSQL SQL editor
-- =====================================================

-- Add optional name and description fields to dashboard_links
ALTER TABLE dashboard_links 
ADD COLUMN IF NOT EXISTS name TEXT,
ADD COLUMN IF NOT EXISTS description TEXT;

-- Create tracking table for dashboard link opens
CREATE TABLE IF NOT EXISTS dashboard_link_tracking (
    id SERIAL PRIMARY KEY,
    dashboard_link_id INTEGER NOT NULL REFERENCES dashboard_links(id) ON DELETE CASCADE,
    opened_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ip_address TEXT,
    user_agent TEXT,
    referer TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_dashboard_link_tracking_link_id 
    ON dashboard_link_tracking(dashboard_link_id, opened_at DESC);

CREATE INDEX IF NOT EXISTS idx_dashboard_link_tracking_opened_at 
    ON dashboard_link_tracking(opened_at DESC);

-- Comments for documentation
COMMENT ON TABLE dashboard_link_tracking IS 'Tracks when dashboard links are opened by public users';
COMMENT ON COLUMN dashboard_link_tracking.dashboard_link_id IS 'Foreign key to dashboard_links table';
COMMENT ON COLUMN dashboard_link_tracking.opened_at IS 'Timestamp when the link was opened';
COMMENT ON COLUMN dashboard_link_tracking.ip_address IS 'IP address of the user who opened the link';
COMMENT ON COLUMN dashboard_link_tracking.user_agent IS 'User agent string from the browser';
COMMENT ON COLUMN dashboard_link_tracking.referer IS 'Referer URL if available';
COMMENT ON COLUMN dashboard_links.name IS 'Optional friendly name for the link';
COMMENT ON COLUMN dashboard_links.description IS 'Optional description for the link';


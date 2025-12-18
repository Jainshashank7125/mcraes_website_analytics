-- =====================================================
-- Add executive_summary column to dashboard_links table
-- Stores structured JSONB data for Executive/Monthly Performance Brief
-- =====================================================
-- Run this in your Supabase/PostgreSQL SQL editor
-- =====================================================

ALTER TABLE dashboard_links 
ADD COLUMN IF NOT EXISTS executive_summary JSONB;

COMMENT ON COLUMN dashboard_links.executive_summary IS 'Structured Executive Brief data stored as JSONB with sections: header, executive_summary, what_worked, what_to_watch, ai_visibility_snapshot, content_authority_snapshot, focus_next_30_days, client_action_needed';

-- Create index for JSONB queries (optional but recommended)
CREATE INDEX IF NOT EXISTS idx_dashboard_links_executive_summary 
ON dashboard_links USING GIN (executive_summary);


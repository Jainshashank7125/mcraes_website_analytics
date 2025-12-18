-- =====================================================
-- Add show_change_period column to dashboard_link_kpi_selections table
-- This stores per-section flags for showing/hiding change period indicators
-- =====================================================

-- Add show_change_period column as JSONB to store section-specific flags
ALTER TABLE dashboard_link_kpi_selections
ADD COLUMN IF NOT EXISTS show_change_period JSONB DEFAULT '{"ga4": true, "agency_analytics": true, "scrunch_ai": true, "all_performance_metrics": true}'::jsonb;

-- Add comment for documentation
COMMENT ON COLUMN dashboard_link_kpi_selections.show_change_period IS 'JSON object storing per-section flags for showing change period indicators. Keys: ga4, agency_analytics, scrunch_ai, all_performance_metrics. Default: all true.';


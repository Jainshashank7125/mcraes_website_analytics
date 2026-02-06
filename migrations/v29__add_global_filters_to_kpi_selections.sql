-- Migration: Add global_filters column to dashboard_link_kpi_selections table
-- Version: v29
-- Description: Adds JSONB column to store global filter configurations for dashboard links
-- Global filters allow users to apply dimension-based filters (user type, traffic source, location, etc.)
-- across all KPIs and charts in the reporting dashboard

ALTER TABLE dashboard_link_kpi_selections 
ADD COLUMN IF NOT EXISTS global_filters JSONB DEFAULT '{}'::jsonb;

-- Add comment for documentation
COMMENT ON COLUMN dashboard_link_kpi_selections.global_filters IS 'Global filters configuration for dashboard links. Supported filter dimensions: user_type, traffic_channels, traffic_sources, countries, regions, cities, page_urls, conversion_types, conversion_by';

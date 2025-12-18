-- =====================================================
-- Create dashboard_link_kpi_selections table for storing KPI selections per dashboard link
-- This allows each shareable link to have its own KPI, section, and chart visibility settings
-- =====================================================
-- Run this in your Supabase/PostgreSQL SQL editor
-- =====================================================

-- Create dashboard_link_kpi_selections table
CREATE TABLE IF NOT EXISTS dashboard_link_kpi_selections (
    id SERIAL PRIMARY KEY,
    dashboard_link_id INTEGER NOT NULL UNIQUE REFERENCES dashboard_links(id) ON DELETE CASCADE,
    selected_kpis TEXT[] NOT NULL DEFAULT '{}',
    visible_sections TEXT[] NOT NULL DEFAULT ARRAY['ga4', 'scrunch_ai', 'brand_analytics', 'advanced_analytics', 'keywords'],
    selected_charts TEXT[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create index on dashboard_link_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_dashboard_link_kpi_selections_link_id 
    ON dashboard_link_kpi_selections(dashboard_link_id);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_dashboard_link_kpi_selections_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update updated_at
CREATE TRIGGER trigger_update_dashboard_link_kpi_selections_updated_at
    BEFORE UPDATE ON dashboard_link_kpi_selections
    FOR EACH ROW
    EXECUTE FUNCTION update_dashboard_link_kpi_selections_updated_at();

-- Comments for documentation
COMMENT ON TABLE dashboard_link_kpi_selections IS 'Stores KPI, section, and chart visibility preferences for each dashboard link. Each shareable link can have its own custom visibility settings.';
COMMENT ON COLUMN dashboard_link_kpi_selections.dashboard_link_id IS 'Reference to the dashboard link this selection applies to (one-to-one relationship)';
COMMENT ON COLUMN dashboard_link_kpi_selections.selected_kpis IS 'Array of KPI keys that should be visible for this link. If empty, all available KPIs are shown.';
COMMENT ON COLUMN dashboard_link_kpi_selections.visible_sections IS 'Array of section keys that should be visible for this link. Default: all sections visible. Valid sections: ga4, agency_analytics, scrunch_ai, brand_analytics, advanced_analytics, keywords';
COMMENT ON COLUMN dashboard_link_kpi_selections.selected_charts IS 'Array of chart keys that should be visible for this link. If empty, all available charts are shown.';


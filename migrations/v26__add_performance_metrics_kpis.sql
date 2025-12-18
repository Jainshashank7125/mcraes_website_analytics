-- =====================================================
-- Add selected_performance_metrics_kpis column to brand_kpi_selections and dashboard_link_kpi_selections tables
-- This allows independent selection of KPIs for the "All Performance Metrics" summary section
-- =====================================================
-- Run this in your Supabase/PostgreSQL SQL editor
-- =====================================================

-- Add selected_performance_metrics_kpis to brand_kpi_selections table
ALTER TABLE brand_kpi_selections 
ADD COLUMN IF NOT EXISTS selected_performance_metrics_kpis TEXT[] NOT NULL DEFAULT '{}';

-- Add selected_performance_metrics_kpis to dashboard_link_kpi_selections table
ALTER TABLE dashboard_link_kpi_selections 
ADD COLUMN IF NOT EXISTS selected_performance_metrics_kpis TEXT[] NOT NULL DEFAULT '{}';

-- Comments for documentation
COMMENT ON COLUMN brand_kpi_selections.selected_performance_metrics_kpis IS 'Array of KPI keys that should be visible in the "All Performance Metrics" summary section. Independent from selected_kpis. Empty array means show all KPIs (default behavior).';
COMMENT ON COLUMN dashboard_link_kpi_selections.selected_performance_metrics_kpis IS 'Array of KPI keys that should be visible in the "All Performance Metrics" summary section for this dashboard link. Independent from selected_kpis. Empty array means show all KPIs (default behavior).';


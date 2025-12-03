-- Migration: Add selected_charts column to brand_kpi_selections table
-- Run this in your Supabase SQL Editor

-- Add selected_charts column if it doesn't exist
ALTER TABLE brand_kpi_selections 
ADD COLUMN IF NOT EXISTS selected_charts TEXT[] NOT NULL DEFAULT '{}';

-- Update comment
COMMENT ON COLUMN brand_kpi_selections.selected_charts IS 'Array of chart keys that should be visible in public view. If empty, no charts are shown. Charts can be shown independently of KPIs.';


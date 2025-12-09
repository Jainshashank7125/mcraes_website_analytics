-- =====================================================
-- Add report_start_date and report_end_date to clients table
-- These fields store the date range that should be used
-- for displaying data on the public dashboard
-- =====================================================
-- Run this in your Supabase SQL Editor
-- =====================================================

ALTER TABLE clients
ADD COLUMN IF NOT EXISTS report_start_date DATE,
ADD COLUMN IF NOT EXISTS report_end_date DATE;

-- Add comments
COMMENT ON COLUMN clients.report_start_date IS 'Start date for the date range to display on public dashboard (YYYY-MM-DD format)';
COMMENT ON COLUMN clients.report_end_date IS 'End date for the date range to display on public dashboard (YYYY-MM-DD format)';

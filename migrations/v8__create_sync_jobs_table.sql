-- Migration: Create sync_jobs table for tracking async sync operations
-- Run this in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS sync_jobs (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(255) UNIQUE NOT NULL,
    sync_type VARCHAR(50) NOT NULL,  -- 'sync_brands', 'sync_prompts', 'sync_responses', 'sync_all', 'sync_ga4', 'sync_agency_analytics'
    user_id VARCHAR(255),
    user_email VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- 'pending', 'running', 'completed', 'failed', 'cancelled'
    progress INTEGER DEFAULT 0,  -- 0-100 percentage
    current_step VARCHAR(255),  -- Current step description
    total_steps INTEGER DEFAULT 0,
    completed_steps INTEGER DEFAULT 0,
    
    -- Results
    result JSONB,  -- Final result data
    error_message TEXT,  -- Error message if failed
    
    -- Metadata
    parameters JSONB,  -- Input parameters (brand_id, date ranges, etc.)
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS ix_sync_jobs_job_id ON sync_jobs(job_id);
CREATE INDEX IF NOT EXISTS ix_sync_jobs_user_email ON sync_jobs(user_email);
CREATE INDEX IF NOT EXISTS ix_sync_jobs_status ON sync_jobs(status);
CREATE INDEX IF NOT EXISTS ix_sync_jobs_sync_type ON sync_jobs(sync_type);
CREATE INDEX IF NOT EXISTS ix_sync_jobs_created_at ON sync_jobs(created_at DESC);

-- Create composite index for common queries
CREATE INDEX IF NOT EXISTS ix_sync_jobs_user_status ON sync_jobs(user_email, status, created_at DESC);

-- Add comments
COMMENT ON TABLE sync_jobs IS 'Tracks async sync job status and progress';
COMMENT ON COLUMN sync_jobs.job_id IS 'Unique job identifier (UUID)';
COMMENT ON COLUMN sync_jobs.status IS 'Job status: pending, running, completed, failed, cancelled';
COMMENT ON COLUMN sync_jobs.progress IS 'Progress percentage (0-100)';
COMMENT ON COLUMN sync_jobs.result IS 'Final result data when completed';
COMMENT ON COLUMN sync_jobs.parameters IS 'Input parameters for the sync job';

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_sync_jobs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at
DROP TRIGGER IF EXISTS sync_jobs_updated_at ON sync_jobs;
CREATE TRIGGER sync_jobs_updated_at
    BEFORE UPDATE ON sync_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_sync_jobs_updated_at();


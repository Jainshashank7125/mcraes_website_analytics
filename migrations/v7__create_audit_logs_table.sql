-- Migration: Create audit_logs table for tracking user actions and data syncs
-- Run this in Supabase SQL Editor or via Alembic

-- Create enum type for audit log actions (only if it doesn't exist)
DO $$ BEGIN
    CREATE TYPE auditlogaction AS ENUM (
        'login',
        'logout',
        'user_created',
        'sync_brands',
        'sync_prompts',
        'sync_responses',
        'sync_ga4',
        'sync_agency_analytics',
        'sync_all'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create audit_logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    action auditlogaction NOT NULL,
    user_id VARCHAR(255),
    user_email VARCHAR(255),
    ip_address VARCHAR(45),  -- IPv6 max length
    user_agent TEXT,
    details JSONB,  -- Store additional context (brand_id, sync counts, etc.)
    status VARCHAR(50),  -- 'success', 'error', 'partial'
    error_message TEXT,  -- Error message if status is 'error'
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS ix_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS ix_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS ix_audit_logs_user_email ON audit_logs(user_email);
CREATE INDEX IF NOT EXISTS ix_audit_logs_status ON audit_logs(status);
CREATE INDEX IF NOT EXISTS ix_audit_logs_created_at ON audit_logs(created_at);

-- Create composite index for common queries (user + action + date)
CREATE INDEX IF NOT EXISTS ix_audit_logs_user_action_date ON audit_logs(user_email, action, created_at DESC);

-- Add comment to table
COMMENT ON TABLE audit_logs IS 'Audit log table for tracking user actions, logins, and data sync operations';
COMMENT ON COLUMN audit_logs.action IS 'Type of action performed';
COMMENT ON COLUMN audit_logs.user_id IS 'Supabase user ID';
COMMENT ON COLUMN audit_logs.user_email IS 'User email for easier querying';
COMMENT ON COLUMN audit_logs.details IS 'JSON object with action-specific details (brand_id, sync counts, etc.)';
COMMENT ON COLUMN audit_logs.status IS 'Status of the action: success, error, or partial';


-- =====================================================
-- V2 Authentication: Users and Refresh Tokens Tables
-- =====================================================
-- This migration creates tables for local PostgreSQL-based authentication
-- Separate from Supabase auth system (v1)
-- =====================================================

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for users table
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Refresh Tokens Table
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,  -- Hashed refresh token
    usage_count INTEGER DEFAULT 0,
    max_usage INTEGER DEFAULT 4,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ
);

-- Indexes for refresh_tokens table
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token ON refresh_tokens(token);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires_at ON refresh_tokens(expires_at);

-- Trigger function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_users_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update updated_at on users table
DROP TRIGGER IF EXISTS trigger_update_users_updated_at ON users;
CREATE TRIGGER trigger_update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_users_updated_at();

-- Comments for documentation
COMMENT ON TABLE users IS 'Local PostgreSQL users table for v2 authentication system';
COMMENT ON TABLE refresh_tokens IS 'Refresh tokens for v2 authentication with usage limits';
COMMENT ON COLUMN refresh_tokens.token IS 'SHA-256 hashed refresh token (never store plain tokens)';
COMMENT ON COLUMN refresh_tokens.max_usage IS 'Maximum number of times this refresh token can be used (default: 4)';
COMMENT ON COLUMN refresh_tokens.usage_count IS 'Current number of times this refresh token has been used';


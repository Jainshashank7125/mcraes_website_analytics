-- =====================================================
-- Add role and is_active columns to users table
-- For admin panel: role-based access control and soft delete
-- =====================================================

-- Add role column with default 'user'
ALTER TABLE users
ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL DEFAULT 'user';

-- Add is_active column with default true (soft delete flag)
ALTER TABLE users
ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;

-- Backfill existing rows explicitly (defaults already cover new rows)
UPDATE users
SET role = 'user'
WHERE role IS NULL;

UPDATE users
SET is_active = TRUE
WHERE is_active IS NULL;

-- Indexes for filtering
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Comments
COMMENT ON COLUMN users.role IS 'User role: "admin" or "user". Controls access to the admin panel.';
COMMENT ON COLUMN users.is_active IS 'Soft delete flag. When false, user is deactivated and cannot log in. Defaults to true.';

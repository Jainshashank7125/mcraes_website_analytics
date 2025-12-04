-- =====================================================
-- Add is_active column to clients table
-- For soft delete functionality
-- =====================================================

-- Add is_active column with default true
ALTER TABLE clients 
ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;

-- Update existing records to have is_active = true
UPDATE clients 
SET is_active = TRUE 
WHERE is_active IS NULL;

-- Create index for filtering active clients
CREATE INDEX IF NOT EXISTS idx_clients_is_active ON clients(is_active) WHERE is_active = TRUE;

-- Add comment
COMMENT ON COLUMN clients.is_active IS 'Soft delete flag. When false, client is considered deleted but data is preserved. Defaults to true.';


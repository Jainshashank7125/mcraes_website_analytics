-- Migration: Add client_id column to brand_kpi_selections table and make it client-centric
-- This allows KPI selections to be stored per client instead of per brand

-- Add client_id column (nullable initially to allow migration of existing data)
ALTER TABLE brand_kpi_selections 
ADD COLUMN IF NOT EXISTS client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE;

-- Create index on client_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_brand_kpi_selections_client_id ON brand_kpi_selections(client_id);

-- Make brand_id nullable (since clients may not have scrunch_brand_id)
ALTER TABLE brand_kpi_selections 
ALTER COLUMN brand_id DROP NOT NULL;

-- Drop the unique constraint on brand_id (we'll add a new one on client_id)
ALTER TABLE brand_kpi_selections 
DROP CONSTRAINT IF EXISTS brand_kpi_selections_brand_id_key;

-- Add unique constraint on client_id (one selection per client)
ALTER TABLE brand_kpi_selections 
DROP CONSTRAINT IF EXISTS brand_kpi_selections_client_id_key;
ALTER TABLE brand_kpi_selections 
ADD CONSTRAINT brand_kpi_selections_client_id_key UNIQUE (client_id);

-- Update existing records: set client_id based on brand_id
-- This assumes each brand has a corresponding client with scrunch_brand_id matching the brand_id
UPDATE brand_kpi_selections bks
SET client_id = (
    SELECT c.id 
    FROM clients c 
    WHERE c.scrunch_brand_id = bks.brand_id 
    LIMIT 1
)
WHERE client_id IS NULL;

-- Comments
COMMENT ON COLUMN brand_kpi_selections.client_id IS 'Reference to the client this selection applies to. This is the primary identifier for KPI selections.';
COMMENT ON COLUMN brand_kpi_selections.brand_id IS 'Reference to the brand (for backward compatibility). Derived from client.scrunch_brand_id.';


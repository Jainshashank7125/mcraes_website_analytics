-- =====================================================
-- Add Logo and Theme Configuration to Brands Table
-- =====================================================
-- Run this in your Supabase SQL Editor
-- =====================================================

-- Add logo_url column to store logo image URL
ALTER TABLE brands 
ADD COLUMN IF NOT EXISTS logo_url TEXT;

-- Add theme column to store brand theme configuration (JSONB)
-- Theme structure: { primaryColor, secondaryColor, accentColor, fontFamily, etc. }
ALTER TABLE brands 
ADD COLUMN IF NOT EXISTS theme JSONB DEFAULT '{}'::jsonb;

-- Add index for logo_url (optional, for faster queries)
CREATE INDEX IF NOT EXISTS idx_brands_logo_url ON brands(logo_url) WHERE logo_url IS NOT NULL;

-- Comments
COMMENT ON COLUMN brands.logo_url IS 'URL to the brand logo image (stored in Supabase Storage)';
COMMENT ON COLUMN brands.theme IS 'Brand theme configuration (colors, fonts, etc.) stored as JSON';


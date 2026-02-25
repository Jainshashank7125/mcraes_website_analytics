-- =====================================================
-- Add created_by and updated_by to dashboard_links
-- Add dashboard_link_created and dashboard_link_updated to audit log enum
-- =====================================================

-- Add created_by and updated_by to dashboard_links
ALTER TABLE dashboard_links
ADD COLUMN IF NOT EXISTS created_by TEXT,
ADD COLUMN IF NOT EXISTS updated_by TEXT;

COMMENT ON COLUMN dashboard_links.created_by IS 'Email of user who created the link';
COMMENT ON COLUMN dashboard_links.updated_by IS 'Email of user who last updated the link';

-- Add new values to auditlogaction enum
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'dashboard_link_created' AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'auditlogaction')) THEN
        ALTER TYPE auditlogaction ADD VALUE 'dashboard_link_created';
    END IF;
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'dashboard_link_updated' AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'auditlogaction')) THEN
        ALTER TYPE auditlogaction ADD VALUE 'dashboard_link_updated';
    END IF;
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

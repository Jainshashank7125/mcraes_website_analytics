-- =====================================================
-- V34 Migration: One ranking row per keyword per day
-- =====================================================
-- Background: v2/003 dropped the unique constraint on keyword_id_date, and the sync
-- then INSERTed a fresh copy of every keyword/day on every run. The table grew to
-- ~29M rows for ~2.6M distinct keyword/days. Copies disagree when Agency Analytics
-- revises a day after the fact (e.g. first copy "not found", later copies ranked),
-- and readers that picked an arbitrary copy hid keywords / inflated counts.
--
-- This migration keeps the NEWEST copy (highest id) of each keyword/day, which is
-- the value Agency Analytics returned last, and restores the unique constraint so
-- the sync can upsert in place. It runs as ONE transaction (manage_migrations.py
-- executes the whole file at once), so any failure rolls back and leaves the table
-- exactly as it was.
-- =====================================================

SET LOCAL maintenance_work_mem = '512MB';
SET LOCAL work_mem = '128MB';

LOCK TABLE agency_analytics_keyword_rankings IN ACCESS EXCLUSIVE MODE;

-- 1. Ids of the newest copy per keyword/day (narrow columns only, cheap to aggregate)
CREATE TEMP TABLE aakr_keep_ids ON COMMIT DROP AS
SELECT max(id) AS id
FROM agency_analytics_keyword_rankings
GROUP BY keyword_id, date;

-- 2. Materialise the rows to keep
CREATE TEMP TABLE aakr_keep ON COMMIT DROP AS
SELECT r.*
FROM agency_analytics_keyword_rankings r
JOIN aakr_keep_ids k ON k.id = r.id;

-- Safety net: abort (and roll everything back) unless the kept set is exactly one row
-- per keyword/day. Fails the whole migration instead of silently losing data.
DO $$
DECLARE
    kept bigint;
    expected bigint;
BEGIN
    SELECT count(*) INTO kept FROM aakr_keep;
    SELECT count(*) INTO expected FROM (
        SELECT 1 FROM agency_analytics_keyword_rankings GROUP BY keyword_id, date
    ) s;
    IF kept <> expected THEN
        RAISE EXCEPTION USING MESSAGE = 'dedupe sanity check failed: kept ' || kept || ' rows, expected ' || expected || ' distinct keyword/days';
    END IF;
END
$$;

-- 3. Replace the table contents (keeps ids, sequence, FKs and indexes; frees the
--    dead space immediately, unlike DELETE which would need a VACUUM FULL)
TRUNCATE agency_analytics_keyword_rankings;
INSERT INTO agency_analytics_keyword_rankings SELECT * FROM aakr_keep;

-- 4. Restore uniqueness. The unique constraint creates its own unique index, so the
--    old plain index on the same column is redundant.
DROP INDEX IF EXISTS idx_aa_keyword_rankings_keyword_id_date;
ALTER TABLE agency_analytics_keyword_rankings
    ADD CONSTRAINT agency_analytics_keyword_rankings_keyword_id_date_key UNIQUE (keyword_id_date);

COMMENT ON COLUMN agency_analytics_keyword_rankings.keyword_id_date IS
    'Composite identifier keyword_id-date. Unique: one row per keyword per day, updated in place by the sync (restored by v34).';

ANALYZE agency_analytics_keyword_rankings;

# Recover This Week's Data (Feb 2-6, 2026)

## Issue
- Database was restored from Feb 1 backup
- This week's data (Feb 2-6) is missing
- No backup file exists for this week's data

## Solution: Re-sync from Source APIs

The data can be recovered by re-syncing from the source APIs:
1. **Agency Analytics** - Keyword rankings and volume data
2. **GA4** - Google Analytics data
3. **Scrunch** - Brand mentions and sentiment

## Recovery Steps

### 1. Trigger Full Sync for All Clients

```bash
# Agency Analytics sync (includes volume data)
curl -X POST "http://localhost:8000/api/v1/sync/agency-analytics?sync_mode=complete&cron=true"

# GA4 sync
curl -X POST "http://localhost:8000/api/v1/sync/ga4?sync_mode=complete&sync_realtime=false&cron=true"

# Scrunch sync
curl -X POST "http://localhost:8000/api/v1/sync/all?sync_mode=complete&cron=true"
```

### 2. Monitor Sync Jobs

Check sync job status:
```bash
curl -X GET "http://localhost:8000/api/v1/sync/jobs?status=running"
```

### 3. Verify Data Recovery

After syncs complete, verify data:
```sql
-- Check volume data for this week
SELECT COUNT(*) as total_rows, 
       COUNT(CASE WHEN volume IS NOT NULL AND volume > 0 THEN 1 END) as rows_with_volume,
       MIN(date) as min_date, 
       MAX(date) as max_date 
FROM agency_analytics_keyword_rankings 
WHERE date >= '2026-02-01';

-- Check daily data counts
SELECT date, COUNT(*) as row_count 
FROM agency_analytics_keyword_rankings 
WHERE date >= '2026-02-01' 
GROUP BY date 
ORDER BY date;
```

## Notes

- Sync jobs run in background and may take time depending on number of clients
- Volume data will be restored from Agency Analytics API
- All data from Feb 2-6 will be re-synced and stored in database
- After recovery, create a new backup to prevent future data loss

## Create Backup After Recovery

```bash
# After data is recovered, create a new backup
./scripts/weekly_backup.sh
```

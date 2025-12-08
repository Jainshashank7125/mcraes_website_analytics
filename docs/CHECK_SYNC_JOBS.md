# How to Check Sync Jobs and Cron Schedules

This guide explains how to check which sync jobs and cron schedules are configured in the McRAE Analytics application.

## 1. Check System Cron Jobs (Linux/Mac)

### View Current User's Cron Jobs
```bash
crontab -l
```

### Expected Output
If the daily sync is set up, you should see:
```
30 18 * * * cd /path/to/project && python3 daily_sync_job.py >> /path/to/project/logs/daily_sync.log 2>&1
```

This means:
- **Schedule**: Daily at 18:30 UTC (12:00 AM IST)
- **Script**: `daily_sync_job.py`
- **Logs**: `logs/daily_sync.log`

### Check System-Wide Cron Jobs
```bash
# System crontab
cat /etc/crontab

# Cron jobs in /etc/cron.d/
ls -la /etc/cron.d/

# Daily cron jobs
ls -la /etc/cron.daily/
```

## 2. Check Windows Task Scheduler (Windows)

### View Scheduled Task
```powershell
# View the McRAE sync task
Get-ScheduledTask -TaskName "McRAE_Daily_Sync_Job"

# View detailed task information
Get-ScheduledTask -TaskName "McRAE_Daily_Sync_Job" | Get-ScheduledTaskInfo

# View all scheduled tasks
Get-ScheduledTask
```

### Expected Output
- **Task Name**: `McRAE_Daily_Sync_Job`
- **Schedule**: Daily at 12:00 AM (local time)
- **Script**: `daily_sync_job.py`

## 3. Check Sync Jobs via API

### Get All Sync Jobs
```bash
# Get all sync jobs for current user
curl -X GET "http://localhost:8000/api/v1/sync/jobs" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Filter by status
curl -X GET "http://localhost:8000/api/v1/sync/jobs?status=running" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Filter by sync type
curl -X GET "http://localhost:8000/api/v1/sync/jobs?sync_type=agency_analytics" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Specific Sync Job Status
```bash
curl -X GET "http://localhost:8000/api/v1/sync/jobs/{job_id}" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Sync Status Summary
```bash
curl -X GET "http://localhost:8000/api/v1/sync/status" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 4. Check Sync Jobs in Database

### Using pgAdmin or psql
```sql
-- View all sync jobs
SELECT 
    id,
    job_id,
    sync_type,
    status,
    progress,
    current_step,
    user_email,
    created_at,
    updated_at,
    completed_at
FROM sync_jobs
ORDER BY created_at DESC
LIMIT 50;

-- View running jobs
SELECT * FROM sync_jobs 
WHERE status = 'running'
ORDER BY created_at DESC;

-- View recent completed jobs
SELECT * FROM sync_jobs 
WHERE status = 'completed'
ORDER BY completed_at DESC
LIMIT 10;

-- View failed jobs
SELECT * FROM sync_jobs 
WHERE status = 'failed'
ORDER BY updated_at DESC
LIMIT 10;
```

## 5. Check Sync Logs

### Daily Sync Logs (Linux/Mac)
```bash
# View recent log entries
tail -f logs/daily_sync.log

# View last 100 lines
tail -n 100 logs/daily_sync.log

# Search for errors
grep -i error logs/daily_sync.log
```

### Application Logs (Docker)
```bash
# View backend logs
docker logs mcraes-backend --tail 100

# Follow logs in real-time
docker logs mcraes-backend -f

# Filter sync-related logs
docker logs mcraes-backend | grep -i sync
```

## 6. Verify Daily Sync Job Setup

### Test the Daily Sync Script Manually
```bash
# Run the sync script manually to test
python3 daily_sync_job.py

# Or with Docker
docker exec mcraes-backend python3 daily_sync_job.py
```

### Check if Setup Scripts Exist
```bash
# Linux/Mac setup script
ls -la setup_daily_sync_linux.sh

# Windows setup script
ls -la setup_daily_sync_windows.ps1
```

## 7. What Sync Jobs Are Configured?

Based on the codebase, the following sync jobs are available:

### Daily Auto Sync (Scheduled via Cron)
- **Schedule**: Daily at 11:30 PM IST (18:30 UTC)
- **Script**: `daily_sync_job.py`
- **Syncs**:
  1. **AgencyAnalytics**: All active clients (Complete mode)
  2. **GA4**: All clients with GA4 property ID mapped (Complete mode)
  3. **Scrunch AI**: All clients linked to Scrunch (Complete mode)

### Manual Sync Jobs (Triggered via API/UI)
- **Scrunch AI Sync**: `/api/v1/sync/all?sync_mode=complete|new`
- **AgencyAnalytics Sync**: `/api/v1/sync/agency-analytics?sync_mode=complete|new`
- **GA4 Sync**: `/api/v1/sync/ga4?sync_mode=complete|new`

## 8. Quick Check Commands Summary

```bash
# 1. Check cron jobs
crontab -l

# 2. Check if daily sync script exists
ls -la daily_sync_job.py

# 3. Check sync logs
tail -n 50 logs/daily_sync.log

# 4. Check running sync jobs via API
curl -X GET "http://localhost:8000/api/v1/sync/jobs?status=running" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 5. Check database for sync jobs
docker exec mcraes-postgres psql -U postgres -d postgres -c \
  "SELECT job_id, sync_type, status, created_at FROM sync_jobs ORDER BY created_at DESC LIMIT 10;"
```

## Troubleshooting

### If cron job is not running:
1. Check if cron service is running: `systemctl status cron` (Linux) or `service cron status`
2. Verify cron job syntax: `crontab -l`
3. Check cron logs: `/var/log/cron` or `/var/log/syslog`
4. Test script manually: `python3 daily_sync_job.py`

### If sync jobs are not appearing in database:
1. Check if backend is running: `docker ps | grep mcraes-backend`
2. Check backend logs: `docker logs mcraes-backend`
3. Verify database connection
4. Check API endpoints are accessible


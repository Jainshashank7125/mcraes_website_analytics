# Docker Cron Job Setup and Validation Guide

This guide explains how to check, set up, and validate cron jobs when running the application in Docker containers.

## Quick Validation

Run the validation script to check cron status:
```bash
./validate_cron_docker.sh
```

## Setup and Check Script

Run the comprehensive setup/check script:
```bash
./check_and_setup_cron_docker.sh
```

This script will:
- ✅ Check if container is running
- ✅ Install cron if missing
- ✅ Start cron service if not running
- ✅ Check if daily sync job is configured
- ✅ Set up the cron job if needed
- ✅ Validate the configuration

## Manual Validation Commands

### 1. Check Container Status
```bash
docker ps | grep mcraes-backend
```

### 2. Check if Cron is Running in Container
```bash
docker exec mcraes-backend pgrep -x cron
```
If this returns a PID, cron is running. If empty, cron is not running.

### 3. Check Cron Jobs Configuration
```bash
docker exec mcraes-backend crontab -l
```

Expected output if configured:
```
0 * * * * cd /app && python3 generate_ga4_token.py >> /app/logs/ga4_token.log 2>&1
30 18 * * * cd /app && python3 daily_sync_job.py >> /app/logs/daily_sync.log 2>&1
```

### 4. Check if Cron Service is Running
```bash
docker exec mcraes-backend service cron status
```

### 5. Start Cron Service (if not running)
```bash
docker exec mcraes-backend service cron start
```

### 6. View Sync Logs
```bash
# View recent sync logs
docker exec mcraes-backend tail -n 50 /app/logs/daily_sync.log

# Follow sync logs in real-time
docker exec mcraes-backend tail -f /app/logs/daily_sync.log

# View GA4 token generation logs
docker exec mcraes-backend tail -n 50 /app/logs/ga4_token.log

# Follow token logs in real-time
docker exec mcraes-backend tail -f /app/logs/ga4_token.log
```

### 7. Test Scripts Manually
```bash
# Test GA4 token generation
docker exec mcraes-backend python3 /app/generate_ga4_token.py

# Test daily sync script
docker exec mcraes-backend python3 /app/daily_sync_job.py
```

### 8. Check Recent Sync Jobs in Database
```bash
docker exec mcraes-postgres psql -U postgres -d postgres -c \
  "SELECT job_id, sync_type, status, created_at FROM sync_jobs ORDER BY created_at DESC LIMIT 10;"
```

## Setting Up Cron in Docker

### Option 1: Automatic Setup (Recommended)

The `docker-entrypoint.sh` script automatically sets up cron when the container starts. Just rebuild the container:

```bash
docker-compose build backend
docker-compose up -d backend
```

### Option 2: Manual Setup

If cron is not automatically configured, run:

```bash
# Install cron (if not already installed)
docker exec mcraes-backend apt-get update && \
  docker exec mcraes-backend apt-get install -y cron && \
  docker exec mcraes-backend rm -rf /var/lib/apt/lists/*

# Start cron service
docker exec mcraes-backend service cron start

# Create logs directory
docker exec mcraes-backend mkdir -p /app/logs

# Add hourly GA4 token generation cron job
docker exec mcraes-backend bash -c \
  'echo "0 * * * * cd /app && python3 generate_ga4_token.py >> /app/logs/ga4_token.log 2>&1" | crontab -'

# Add daily sync cron job
docker exec mcraes-backend bash -c \
  'echo "30 18 * * * cd /app && python3 daily_sync_job.py >> /app/logs/daily_sync.log 2>&1" | crontab -'
```

### Option 3: Use Host Cron (Alternative)

Instead of running cron inside the container, you can use the host's cron to execute docker commands:

```bash
# Add to host crontab (crontab -e)
# Hourly GA4 token generation
0 * * * * docker exec mcraes-backend python3 /app/generate_ga4_token.py >> /path/to/logs/ga4_token.log 2>&1

# Daily sync job
30 18 * * * docker exec mcraes-backend python3 /app/daily_sync_job.py >> /path/to/logs/daily_sync.log 2>&1
```

## Verifying Cron is Working

### 1. Check Cron Process
```bash
docker exec mcraes-backend ps aux | grep cron
```

### 2. Check Cron Logs (if available)
```bash
docker exec mcraes-backend tail -f /var/log/cron.log
# Note: Some containers may not have cron logging enabled
```

### 3. Test by Running Scripts Manually
```bash
# Test GA4 token generation
docker exec mcraes-backend python3 /app/generate_ga4_token.py

# Test daily sync script
docker exec mcraes-backend python3 /app/daily_sync_job.py
```

### 4. Check for Recent Sync Jobs
```bash
# Via API (requires authentication token)
curl -X GET "http://localhost:8000/api/v1/sync/jobs?limit=5" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Via Database
docker exec mcraes-postgres psql -U postgres -d postgres -c \
  "SELECT COUNT(*) FROM sync_jobs WHERE created_at > NOW() - INTERVAL '1 hour';"
```

## Troubleshooting

### Cron Not Running

1. **Check if cron is installed:**
   ```bash
   docker exec mcraes-backend which cron
   ```

2. **Install cron if missing:**
   ```bash
   docker exec mcraes-backend apt-get update && \
     docker exec mcraes-backend apt-get install -y cron
   ```

3. **Start cron service:**
   ```bash
   docker exec mcraes-backend service cron start
   ```

4. **Make cron persist across container restarts:**
   - Update `docker-entrypoint.sh` to start cron (already done)
   - Or use `restart: unless-stopped` in docker-compose (already configured)

### Cron Job Not Executing

1. **Verify cron job is configured:**
   ```bash
   docker exec mcraes-backend crontab -l
   ```

2. **Check script permissions:**
   ```bash
   docker exec mcraes-backend ls -la /app/daily_sync_job.py
   ```

3. **Check logs for errors:**
   ```bash
   # Check sync logs
   docker exec mcraes-backend tail -n 100 /app/logs/daily_sync.log
   
   # Check token generation logs
   docker exec mcraes-backend tail -n 100 /app/logs/ga4_token.log
   ```

4. **Test scripts manually:**
   ```bash
   # Test token generation
   docker exec mcraes-backend python3 /app/generate_ga4_token.py
   
   # Test sync script
   docker exec mcraes-backend python3 /app/daily_sync_job.py
   ```

### Container Restart Loses Cron Configuration

If cron jobs are lost after container restart, ensure:
1. The `docker-entrypoint.sh` script sets up cron on startup (already configured)
2. Or use a volume to persist crontab:
   ```yaml
   volumes:
     - ./crontab:/etc/cron.d/daily-sync:ro
   ```

## Schedule Details

### GA4 Token Generation (Hourly)
- **Cron Schedule**: `0 * * * *` (Every hour at minute 0)
- **Script**: `generate_ga4_token.py`
- **Logs**: `/app/logs/ga4_token.log` (inside container)
- **Purpose**: Ensures GA4 access token is always fresh (tokens expire after 1 hour)

### Daily Sync Job
- **Cron Schedule**: `30 18 * * *` (Daily at 18:30 UTC)
- **IST Time**: 11:30 PM IST (IST = UTC + 5:30)
- **Script**: `daily_sync_job.py`
- **Logs**: `/app/logs/daily_sync.log` (inside container)
- **Note**: Token generation also runs as part of the daily sync script, but the hourly job ensures tokens are always fresh

## What Gets Synced

The daily sync job runs:
1. **AgencyAnalytics Sync**: All active clients (Complete mode)
2. **GA4 Sync**: All clients with GA4 property ID mapped (Complete mode)
3. **Scrunch AI Sync**: All clients linked to Scrunch (Complete mode)

All syncs use "complete" mode to sync all data, not just new items.

## Quick Reference

```bash
# Validate cron setup
./validate_cron_docker.sh

# Setup/check cron
./check_and_setup_cron_docker.sh

# View cron jobs
docker exec mcraes-backend crontab -l

# Check cron is running
docker exec mcraes-backend pgrep -x cron

# Start cron
docker exec mcraes-backend service cron start

# View sync logs
docker exec mcraes-backend tail -f /app/logs/daily_sync.log

# View token generation logs
docker exec mcraes-backend tail -f /app/logs/ga4_token.log

# Test token generation manually
docker exec mcraes-backend python3 /app/generate_ga4_token.py

# Test sync manually
docker exec mcraes-backend python3 /app/daily_sync_job.py
```


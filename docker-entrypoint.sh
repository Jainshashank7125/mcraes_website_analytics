#!/bin/bash
# Docker entrypoint script to run both cron and uvicorn

set -e

# Create logs directory
mkdir -p /app/logs

# Start cron service
echo "Starting cron service..."
service cron start

# Check if cron is running
if ! pgrep -x cron > /dev/null; then
    echo "Warning: Cron service failed to start"
fi

# Setup cron jobs if scripts exist
PYTHON_PATH=$(which python3 || which python)

# Setup hourly GA4 token generation cron job
if [ -f "/app/generate_ga4_token.py" ]; then
    if ! crontab -l 2>/dev/null | grep -q "generate_ga4_token.py"; then
        echo "Setting up hourly GA4 token generation cron job..."
        TOKEN_CRON_JOB="0 * * * * cd /app && ${PYTHON_PATH} generate_ga4_token.py >> /app/logs/ga4_token.log 2>&1"
        (crontab -l 2>/dev/null | grep -v "generate_ga4_token.py"; echo "$TOKEN_CRON_JOB") | crontab -
        echo "GA4 token generation cron job configured (runs every hour)"
    fi
fi

# Setup daily sync cron job (runs after token generation)
if [ -f "/app/daily_sync_job.py" ]; then
    if ! crontab -l 2>/dev/null | grep -q "daily_sync_job.py"; then
        echo "Setting up daily sync cron job..."
        # Run at 18:30 UTC (11:30 PM IST) - token will be generated hourly before this
        SYNC_CRON_JOB="30 18 * * * cd /app && ${PYTHON_PATH} daily_sync_job.py >> /app/logs/daily_sync.log 2>&1"
        (crontab -l 2>/dev/null | grep -v "daily_sync_job.py"; echo "$SYNC_CRON_JOB") | crontab -
        echo "Daily sync cron job configured (runs at 18:30 UTC / 11:30 PM IST)"
    fi
fi

# Print cron status
echo "Cron jobs configured:"
crontab -l 2>/dev/null || echo "  (none)"
echo ""

# Start the main application
exec "$@"


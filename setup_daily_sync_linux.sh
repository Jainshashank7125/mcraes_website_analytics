#!/bin/bash
# Linux/Mac cron job setup script
# Sets up:
# 1. Hourly GA4 token generation (runs every hour)
# 2. Daily sync at 12:00 AM IST (6:30 PM UTC / 18:30 UTC)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH=$(which python3 || which python)

echo "Setting up cron jobs..."
echo "Script directory: $SCRIPT_DIR"
echo "Python path: $PYTHON_PATH"
echo ""

# Create logs directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/logs"

# Get existing crontab
EXISTING_CRON=$(crontab -l 2>/dev/null || echo "")

# Setup hourly GA4 token generation cron job
if [ -f "$SCRIPT_DIR/generate_ga4_token.py" ]; then
    TOKEN_CRON_JOB="0 * * * * cd $SCRIPT_DIR && $PYTHON_PATH generate_ga4_token.py >> $SCRIPT_DIR/logs/ga4_token.log 2>&1"
    # Remove existing token cron job and add new one
    EXISTING_CRON=$(echo "$EXISTING_CRON" | grep -v "generate_ga4_token.py")
    EXISTING_CRON=$(echo "$EXISTING_CRON"; echo "$TOKEN_CRON_JOB")
    echo "[OK] GA4 token generation cron job configured (hourly)"
else
    echo "[WARNING] generate_ga4_token.py not found - skipping token generation cron job"
fi

# Setup daily sync cron job (runs at 18:30 UTC = 12:00 AM IST)
SYNC_CRON_JOB="30 18 * * * cd $SCRIPT_DIR && $PYTHON_PATH daily_sync_job.py >> $SCRIPT_DIR/logs/daily_sync.log 2>&1"
# Remove existing sync cron job and add new one
EXISTING_CRON=$(echo "$EXISTING_CRON" | grep -v "daily_sync_job.py")
EXISTING_CRON=$(echo "$EXISTING_CRON"; echo "$SYNC_CRON_JOB")

# Update crontab
echo "$EXISTING_CRON" | crontab -

echo "[SUCCESS] Cron jobs scheduled!"
echo ""
echo "Cron job details:"
if [ -f "$SCRIPT_DIR/generate_ga4_token.py" ]; then
    echo "  GA4 Token Generation: Every hour (0 * * * *)"
    echo "    Script: generate_ga4_token.py"
    echo "    Logs: $SCRIPT_DIR/logs/ga4_token.log"
fi
echo "  Daily Sync: Daily at 18:30 UTC (12:00 AM IST)"
echo "    Script: daily_sync_job.py"
echo "    Logs: $SCRIPT_DIR/logs/daily_sync.log"
echo ""
echo "To view cron jobs: crontab -l"
echo "To test token generation: python3 generate_ga4_token.py"
echo "To test daily sync: python3 daily_sync_job.py"


#!/bin/bash
# Setup daily backup cron job
# This script adds/updates the daily backup cron job

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUP_SCRIPT="$SCRIPT_DIR/daily_backup.sh"

# Cron schedule: Daily at 5 AM IST
# IST is UTC+5:30, so 5 AM IST = 23:30 UTC (previous day)
# Cron format: minute hour day month weekday
CRON_SCHEDULE="30 23 * * *"  # 23:30 UTC daily = 5:00 AM IST daily

echo "Setting up daily backup cron job..."
echo "Schedule: Every day at 5:00 AM IST (23:30 UTC)"
echo "Script: $BACKUP_SCRIPT"
echo ""

# Check if script exists
if [ ! -f "$BACKUP_SCRIPT" ]; then
    echo "ERROR: Backup script not found: $BACKUP_SCRIPT"
    exit 1
fi

# Make sure script is executable
chmod +x "$BACKUP_SCRIPT"

# Get current crontab
TEMP_CRON=$(mktemp)
crontab -l 2>/dev/null > "$TEMP_CRON" || touch "$TEMP_CRON"

# Remove existing daily backup entry if it exists
grep -v "daily_backup.sh" "$TEMP_CRON" > "${TEMP_CRON}.new" || true
mv "${TEMP_CRON}.new" "$TEMP_CRON"

# Add new cron job with proper environment
# Set PATH, TZ, and working directory
cat >> "$TEMP_CRON" << EOF

# Daily database backup - Every day at 5:00 AM IST
# IST is UTC+5:30, so this runs at 23:30 UTC
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
TZ=Asia/Kolkata
${CRON_SCHEDULE} cd $PROJECT_DIR && $BACKUP_SCRIPT >> $PROJECT_DIR/logs/cron_daily_backup.log 2>&1
EOF

# Install new crontab
crontab "$TEMP_CRON"
rm "$TEMP_CRON"

echo "✓ Daily backup cron job installed successfully!"
echo ""
echo "Current crontab:"
crontab -l | grep -E "(daily_backup|weekly_backup)"
echo ""
echo "To view all cron jobs: crontab -l"
echo "To remove this cron job: crontab -e (then delete the line)"


#!/bin/bash
# Setup weekly backup cron job
# This script adds/updates the weekly backup cron job

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUP_SCRIPT="$SCRIPT_DIR/weekly_backup.sh"

# Cron schedule: Every Sunday at 5 AM IST
# IST is UTC+5:30, so 5 AM IST = 23:30 UTC (Saturday)
# Cron format: minute hour day month weekday
# For Sunday at 23:30 UTC (which is 5:00 AM IST on Sunday):
CRON_SCHEDULE="30 23 * * 6"  # 23:30 UTC on Saturday = 5:00 AM IST on Sunday

echo "Setting up weekly backup cron job..."
echo "Schedule: Every Sunday at 5:00 AM IST (23:30 UTC Saturday)"
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

# Remove existing weekly backup entry if it exists
grep -v "weekly_backup.sh" "$TEMP_CRON" > "${TEMP_CRON}.new" || true
mv "${TEMP_CRON}.new" "$TEMP_CRON"

# Add new cron job with proper environment
# Set PATH, TZ, and working directory
cat >> "$TEMP_CRON" << EOF

# Weekly database backup - Every Sunday at 5:00 AM IST
# IST is UTC+5:30, so this runs at 23:30 UTC on Saturday
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
TZ=Asia/Kolkata
${CRON_SCHEDULE} cd $PROJECT_DIR && $BACKUP_SCRIPT >> $PROJECT_DIR/logs/cron_backup.log 2>&1
EOF

# Install new crontab
crontab "$TEMP_CRON"
rm "$TEMP_CRON"

echo "✓ Weekly backup cron job installed successfully!"
echo ""
echo "Current crontab:"
crontab -l | grep -A 2 "weekly_backup"
echo ""
echo "To view all cron jobs: crontab -l"
echo "To remove this cron job: crontab -e (then delete the line)"


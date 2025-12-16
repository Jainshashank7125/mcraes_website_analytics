# Database Backup Configuration

## Weekly Automated Backups

The system is configured to automatically create database backups every **Sunday at 5:00 AM IST**.

### Backup Details

- **Schedule**: Every Sunday at 5:00 AM IST (23:30 UTC Saturday)
- **Location**: `/root/mcraes_website_analytics/dumps/`
- **Format**: Compressed PostgreSQL custom format (`.dump.gz`)
- **Retention**: 30 days (older backups are automatically deleted)
- **Logs**: `/root/mcraes_website_analytics/logs/weekly_backup_*.log`

### Backup Files

Backup files are named: `weekly_backup_YYYYMMDD_HHMMSS.dump.gz`

Example: `weekly_backup_20251207_050000.dump.gz`

### Manual Backup

To create a manual backup:

```bash
cd /root/mcraes_website_analytics
./scripts/weekly_backup.sh
```

Or use the existing dump script:

```bash
./scripts/create_database_dump.sh
```

### Restore from Backup

To restore a backup:

```bash
cd /root/mcraes_website_analytics

# If backup is compressed, unzip it first
gunzip dumps/weekly_backup_YYYYMMDD_HHMMSS.dump.gz

# Restore
./scripts/restore_database_dump.sh dumps/weekly_backup_YYYYMMDD_HHMMSS.dump
```

### Cron Job Management

**View cron jobs:**
```bash
crontab -l
```

**Edit cron jobs:**
```bash
crontab -e
```

**Remove weekly backup cron:**
```bash
crontab -e
# Delete the line with weekly_backup.sh
```

**Reinstall weekly backup cron:**
```bash
cd /root/mcraes_website_analytics
./scripts/setup_weekly_backup_cron.sh
```

### Backup Verification

Check backup logs:
```bash
tail -f /root/mcraes_website_analytics/logs/weekly_backup_*.log
```

List recent backups:
```bash
ls -lh /root/mcraes_website_analytics/dumps/weekly_backup_*.dump.gz | tail -5
```

### Timezone Note

The cron job runs at **23:30 UTC on Saturday**, which equals **5:00 AM IST on Sunday** (IST = UTC+5:30).

### Backup Storage

- Backups are stored in: `/root/mcraes_website_analytics/dumps/`
- Logs are stored in: `/root/mcraes_website_analytics/logs/`
- Old backups (>30 days) are automatically cleaned up
- Old logs (>90 days) are automatically cleaned up

### Monitoring

Check if the cron job is running:
```bash
# View cron logs
tail -f /var/log/syslog | grep CRON

# Or check application logs
tail -f /root/mcraes_website_analytics/logs/cron_backup.log
```

### Troubleshooting

**Backup not running?**
1. Check cron service: `systemctl status cron`
2. Check cron logs: `grep CRON /var/log/syslog`
3. Verify script permissions: `ls -l scripts/weekly_backup.sh`
4. Test script manually: `./scripts/weekly_backup.sh`

**Backup file not created?**
1. Check PostgreSQL container is running: `docker compose ps postgres`
2. Check disk space: `df -h`
3. Check logs: `tail -f logs/weekly_backup_*.log`

**Timezone issues?**
- Cron uses system timezone (UTC by default)
- The script sets TZ=Asia/Kolkata for logging
- Backup runs at 23:30 UTC = 5:00 AM IST


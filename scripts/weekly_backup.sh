#!/bin/bash
# Weekly database backup script
# Runs every Sunday at 5 AM IST

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

DB_NAME="${DB_NAME:-postgres}"
DB_USER="${DB_USER:-postgres}"
DUMP_DIR="${DUMP_DIR:-$PROJECT_DIR/dumps}"
LOG_DIR="${LOG_DIR:-$PROJECT_DIR/logs}"
RETENTION_DAYS=30  # Keep backups for 30 days

# Create directories if they don't exist
mkdir -p "$DUMP_DIR"
mkdir -p "$LOG_DIR"

# Set timezone to IST for logging
export TZ="Asia/Kolkata"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DUMP_FILE="${DUMP_DIR}/weekly_backup_${TIMESTAMP}.dump"
LOG_FILE="${LOG_DIR}/weekly_backup_${TIMESTAMP}.log"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S %Z')] $1" | tee -a "$LOG_FILE"
}

log "=========================================="
log "Weekly Database Backup Started"
log "=========================================="
log "Database: $DB_NAME"
log "User: $DB_USER"
log "Output: $DUMP_FILE"
log ""

# Check if PostgreSQL container is running
if ! docker compose ps postgres | grep -q "Up"; then
    log "ERROR: PostgreSQL container is not running!"
    exit 1
fi

# Create dump using pg_dump
log "Creating database dump..."
if docker compose exec -T postgres pg_dump \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --verbose \
    --clean \
    --if-exists \
    --create \
    --format=custom \
    --no-owner \
    --no-acl \
    --blobs \
    --encoding=UTF8 \
    > "$DUMP_FILE" 2>>"$LOG_FILE"; then
    
    # Check if dump was created successfully
    if [ -f "$DUMP_FILE" ] && [ -s "$DUMP_FILE" ]; then
        DUMP_SIZE=$(du -h "$DUMP_FILE" | cut -f1)
        log ""
        log "✓ Dump created successfully!"
        log "File: $DUMP_FILE"
        log "Size: $DUMP_SIZE"
        
        # Compress the dump file to save space
        log "Compressing backup..."
        gzip "$DUMP_FILE"
        COMPRESSED_FILE="${DUMP_FILE}.gz"
        COMPRESSED_SIZE=$(du -h "$COMPRESSED_FILE" | cut -f1)
        log "Compressed file: $COMPRESSED_FILE"
        log "Compressed size: $COMPRESSED_SIZE"
        
        # Clean up old backups (older than RETENTION_DAYS)
        log ""
        log "Cleaning up old backups (older than $RETENTION_DAYS days)..."
        find "$DUMP_DIR" -name "weekly_backup_*.dump.gz" -type f -mtime +$RETENTION_DAYS -delete
        DELETED_COUNT=$(find "$DUMP_DIR" -name "weekly_backup_*.dump.gz" -type f -mtime +$RETENTION_DAYS 2>/dev/null | wc -l)
        if [ "$DELETED_COUNT" -gt 0 ]; then
            log "Deleted $DELETED_COUNT old backup(s)"
        else
            log "No old backups to delete"
        fi
        
        # Clean up old logs (older than 90 days)
        log "Cleaning up old logs (older than 90 days)..."
        find "$LOG_DIR" -name "weekly_backup_*.log" -type f -mtime +90 -delete
        
        log ""
        log "=========================================="
        log "✓ Weekly backup completed successfully!"
        log "=========================================="
        exit 0
    else
        log "ERROR: Dump file was not created or is empty"
        exit 1
    fi
else
    log "ERROR: Failed to create database dump"
    exit 1
fi


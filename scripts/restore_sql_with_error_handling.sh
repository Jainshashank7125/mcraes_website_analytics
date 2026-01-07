#!/bin/bash
# Script to restore SQL backup with error handling for malformed JSON/data
# This script continues past errors and logs them for review

set -e

# Check if SQL file is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <sql_file> [database_name] [database_user]"
    echo ""
    echo "Example:"
    echo "  $0 backup.sql"
    echo "  $0 backup.sql postgres postgres"
    echo ""
    exit 1
fi

SQL_FILE="$1"
DB_NAME="${2:-postgres}"
DB_USER="${3:-postgres}"
ERROR_LOG="${SQL_FILE}.errors.log"

# Check if SQL file exists
if [ ! -f "$SQL_FILE" ]; then
    echo "Error: SQL file not found: $SQL_FILE"
    exit 1
fi

echo "=========================================="
echo "Restoring SQL Backup with Error Handling"
echo "=========================================="
echo "SQL file: $SQL_FILE"
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo "Error log: $ERROR_LOG"
echo ""
echo "WARNING: This will attempt to restore the database."
echo "Errors will be logged but restoration will continue."
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

# Check if we're using Docker Compose
USE_DOCKER=false
if command -v docker &> /dev/null && docker compose ps postgres &> /dev/null 2>&1; then
    USE_DOCKER=true
    echo ""
    echo "Detected Docker Compose PostgreSQL container."
    echo ""
fi

echo "Starting restore (errors will be logged to $ERROR_LOG)..."
echo ""

if [ "$USE_DOCKER" = true ]; then
    # Restore with error handling - continue past errors
    docker compose exec -T postgres psql \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        -v ON_ERROR_STOP=0 \
        < "$SQL_FILE" 2>&1 | tee "$ERROR_LOG"
else
    # Use local psql
    if ! command -v psql &> /dev/null; then
        echo "Error: psql command not found."
        echo "Please install PostgreSQL client tools or use Docker Compose."
        exit 1
    fi
    
    psql \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        -v ON_ERROR_STOP=0 \
        < "$SQL_FILE" 2>&1 | tee "$ERROR_LOG"
fi

# Check for critical errors
if grep -qi "ERROR" "$ERROR_LOG" 2>/dev/null; then
    ERROR_COUNT=$(grep -ci "ERROR" "$ERROR_LOG" 2>/dev/null || echo "0")
    echo ""
    echo "=========================================="
    echo "Restore completed with $ERROR_COUNT error(s)"
    echo "=========================================="
    echo ""
    echo "Review errors in: $ERROR_LOG"
    echo ""
    echo "Common issues:"
    echo "  - Malformed JSON in JSONB columns"
    echo "  - Missing foreign key references"
    echo "  - Duplicate key violations"
    echo ""
    echo "To fix JSON errors, you may need to:"
    echo "  1. Use custom format (.dump) instead of plain SQL"
    echo "  2. Fix the source database before creating backup"
    echo "  3. Manually fix the problematic rows"
    echo ""
else
    echo ""
    echo "=========================================="
    echo "✓ Restore completed successfully!"
    echo "=========================================="
fi


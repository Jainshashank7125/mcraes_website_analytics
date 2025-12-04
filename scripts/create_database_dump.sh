#!/bin/bash
# Script to create a complete database dump (schema + data) for production restore

set -e

# Configuration
DB_NAME="${DB_NAME:-postgres}"
DB_USER="${DB_USER:-postgres}"
DUMP_DIR="${DUMP_DIR:-./dumps}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DUMP_FILE="${DUMP_DIR}/mcraes_full_dump_${TIMESTAMP}.dump"

# Create dump directory if it doesn't exist
mkdir -p "$DUMP_DIR"

echo "=========================================="
echo "Creating Database Dump"
echo "=========================================="
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo "Output: $DUMP_FILE"
echo ""

# Create dump using pg_dump with custom format (compressed, includes schema + data)
# Flags:
#   --verbose: Verbose output
#   --clean: Include DROP statements
#   --if-exists: Use IF EXISTS for DROP statements
#   --create: Include CREATE DATABASE statement
#   --format=custom: Custom format (compressed, can be restored with pg_restore)
#   --no-owner: Don't output commands to set ownership of objects
#   --no-acl: Don't output access privileges (grants)
#   --schema-only: NOT USED - we want data too
#   --data-only: NOT USED - we want schema too
#   --blobs: Include large objects (BLOBs)
#   --encoding=UTF8: Set encoding

if [ -n "$DOCKER_COMPOSE" ] || [ -f "docker-compose.yml" ]; then
    # Running in Docker environment
    echo "Creating dump from Docker container..."
    docker compose exec -T postgres pg_dump \
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
        > "$DUMP_FILE"
else
    # Running directly (not in Docker)
    echo "Creating dump directly from PostgreSQL..."
    pg_dump \
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
        -f "$DUMP_FILE"
fi

# Check if dump was created successfully
if [ -f "$DUMP_FILE" ] && [ -s "$DUMP_FILE" ]; then
    DUMP_SIZE=$(du -h "$DUMP_FILE" | cut -f1)
    echo ""
    echo "=========================================="
    echo "✓ Dump created successfully!"
    echo "=========================================="
    echo "File: $DUMP_FILE"
    echo "Size: $DUMP_SIZE"
    echo ""
    echo "To restore this dump, use:"
    echo "  ./scripts/restore_database_dump.sh $DUMP_FILE"
    echo ""
else
    echo ""
    echo "✗ Error: Dump file was not created or is empty"
    exit 1
fi


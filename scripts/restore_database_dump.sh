#!/bin/bash
# Script to restore a database dump to production

set -e

# Check if dump file is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <dump_file> [target_db_name] [target_db_user] [target_host] [target_port]"
    echo ""
    echo "Example:"
    echo "  $0 ./dumps/mcraes_full_dump_20251204_120000.dump"
    echo "  $0 ./dumps/mcraes_full_dump_20251204_120000.dump my_production_db postgres localhost 5432"
    echo ""
    exit 1
fi

DUMP_FILE="$1"
TARGET_DB_NAME="${2:-postgres}"
TARGET_DB_USER="${3:-postgres}"
TARGET_HOST="${4:-localhost}"
TARGET_PORT="${5:-5432}"

# Check if dump file exists
if [ ! -f "$DUMP_FILE" ]; then
    echo "Error: Dump file not found: $DUMP_FILE"
    exit 1
fi

echo "=========================================="
echo "Restoring Database Dump"
echo "=========================================="
echo "Dump file: $DUMP_FILE"
echo "Target database: $TARGET_DB_NAME"
echo "Target user: $TARGET_DB_USER"
echo "Target host: $TARGET_HOST"
echo "Target port: $TARGET_PORT"
echo ""
echo "WARNING: This will DROP and recreate the database!"
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

# Check if we're using Docker Compose
USE_DOCKER=false
if [ "$TARGET_HOST" == "localhost" ] || [ "$TARGET_HOST" == "127.0.0.1" ]; then
    # Check if docker compose is available and postgres container exists
    if command -v docker &> /dev/null && docker compose ps postgres &> /dev/null; then
        USE_DOCKER=true
        echo ""
        echo "Detected Docker Compose PostgreSQL container. Using container for restore."
        echo ""
    fi
fi

# Check if we're restoring to a remote server
if [ "$TARGET_HOST" != "localhost" ] && [ "$TARGET_HOST" != "127.0.0.1" ]; then
    echo ""
    echo "Restoring to remote server: $TARGET_HOST"
    echo "Make sure you have:"
    echo "  1. Network access to the server"
    echo "  2. PostgreSQL client tools installed"
    echo "  3. Proper credentials"
    echo ""
fi

# Restore using pg_restore
# Flags:
#   --verbose: Verbose output
#   --clean: Clean (drop) database objects before recreating
#   --if-exists: Use IF EXISTS for DROP statements
#   --create: Create the database before restoring
#   --no-owner: Don't restore ownership (use current user)
#   --no-acl: Don't restore access privileges
#   --dbname: Target database name
#   --host: Target host
#   --port: Target port
#   --username: Target user

echo "Starting restore..."

if [ "$USE_DOCKER" = true ]; then
    # Copy dump file to container and restore
    CONTAINER_NAME="mcraes-postgres"
    DUMP_BASENAME=$(basename "$DUMP_FILE")
    
    echo "Copying dump file to container..."
    docker cp "$DUMP_FILE" "$CONTAINER_NAME:/tmp/$DUMP_BASENAME"
    
    echo "Restoring database..."
    docker compose exec -T postgres pg_restore \
        --verbose \
        --clean \
        --if-exists \
        --create \
        --no-owner \
        --no-acl \
        --dbname="$TARGET_DB_NAME" \
        --host="localhost" \
        --port="5432" \
        --username="$TARGET_DB_USER" \
        "/tmp/$DUMP_BASENAME"
    
    # Clean up
    docker compose exec -T postgres rm -f "/tmp/$DUMP_BASENAME"
else
    # Use local pg_restore
    if ! command -v pg_restore &> /dev/null; then
        echo "Error: pg_restore command not found."
        echo "Please install PostgreSQL client tools or use Docker Compose."
        exit 1
    fi
    
    pg_restore \
        --verbose \
        --clean \
        --if-exists \
        --create \
        --no-owner \
        --no-acl \
        --dbname="$TARGET_DB_NAME" \
        --host="$TARGET_HOST" \
        --port="$TARGET_PORT" \
        --username="$TARGET_DB_USER" \
        "$DUMP_FILE"
fi

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✓ Database restored successfully!"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo "  1. Verify the database connection"
    echo "  2. Check that all tables exist: \\dt"
    echo "  3. Verify data: SELECT COUNT(*) FROM <table_name>;"
    echo "  4. Update application configuration if needed"
    echo ""
else
    echo ""
    echo "✗ Error: Restore failed"
    exit 1
fi


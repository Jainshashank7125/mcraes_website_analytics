#!/bin/bash
# Create password-protected database dump for remote push
# Usage: ./scripts/create_password_protected_dump.sh [password]

set -e

cd "$(dirname "$0")/.."

DUMP_FILE="dumps/mcraes_full_dump_$(date +%Y%m%d_%H%M%S).dump"
ZIP_FILE="dumps/mcraes_full_dump_$(date +%Y%m%d_%H%M%S).zip"

mkdir -p dumps

echo "Creating database dump..."
docker compose exec -T postgres pg_dump \
    -U postgres \
    -d postgres \
    --clean \
    --if-exists \
    --create \
    --format=custom \
    --no-owner \
    --no-acl \
    --blobs \
    --encoding=UTF8 \
    > "$DUMP_FILE" 2>/dev/null

if [ ! -s "$DUMP_FILE" ]; then
    echo "Error: Dump file is empty"
    exit 1
fi

echo "Creating password-protected ZIP..."

if [ -n "$1" ]; then
    PASSWORD="$1"
else
    echo "Enter password for ZIP file:"
    read -s PASSWORD
    echo ""
fi

if [ -z "$PASSWORD" ]; then
    echo "Error: Password cannot be empty"
    exit 1
fi

zip -P "$PASSWORD" -9 "$ZIP_FILE" "$DUMP_FILE" > /dev/null 2>&1

if [ -f "$ZIP_FILE" ] && [ -s "$ZIP_FILE" ]; then
    DUMP_SIZE=$(du -h "$DUMP_FILE" | cut -f1)
    ZIP_SIZE=$(du -h "$ZIP_FILE" | cut -f1)
    echo ""
    echo "✓ Success!"
    echo "  Dump: $DUMP_FILE ($DUMP_SIZE)"
    echo "  ZIP:  $ZIP_FILE ($ZIP_SIZE)"
    echo ""
    echo "Password-protected ZIP ready for push to remote server."
    echo ""
    echo "To extract: unzip -P '$PASSWORD' $ZIP_FILE"
    echo "To restore: ./scripts/restore_database_dump.sh $DUMP_FILE"
    
    # Remove original dump to save space
    rm -f "$DUMP_FILE"
    echo ""
    echo "✓ Original dump removed. Password-protected ZIP ready."
else
    echo "Error: Failed to create ZIP file"
    exit 1
fi

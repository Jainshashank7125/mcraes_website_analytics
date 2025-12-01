#!/bin/bash
# Migration script to move from Supabase to local PostgreSQL

set -e

echo "=========================================="
echo "Migration to Local PostgreSQL Database"
echo "=========================================="
echo ""

# Check if postgres container is running
if ! docker compose ps postgres | grep -q "Up"; then
    echo "Starting PostgreSQL container..."
    docker compose up -d postgres
    echo "Waiting for PostgreSQL to be ready..."
    sleep 10
fi

echo "Step 1: Exporting data from Supabase..."
echo "Please run this command to export your data:"
echo ""
echo "  docker compose exec backend python -c \""
echo "from app.services.supabase_service import SupabaseService"
echo "import json"
echo "supabase = SupabaseService()"
echo "# Export brands"
echo "brands = supabase.client.table('brands').select('*').execute().data"
echo "with open('brands_export.json', 'w') as f:"
echo "    json.dump(brands, f)"
echo "print('Brands exported')"
echo "  \""
echo ""
echo "Or use pg_dump if you have direct access:"
echo "  pg_dump -h <supabase-host> -U postgres -d postgres > backup.sql"
echo ""
read -p "Have you exported your data? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Please export your data first, then run this script again."
    exit 1
fi

echo ""
echo "Step 2: Running database migrations..."
echo "This will create all tables in local PostgreSQL..."

# Run migrations
for migration in migrations/v*.sql; do
    if [ -f "$migration" ]; then
        echo "Running $migration..."
        docker compose exec -T postgres psql -U postgres -d postgres < "$migration"
    fi
done

echo ""
echo "Step 3: Importing data (if you have backup.sql)..."
if [ -f "backup.sql" ]; then
    echo "Importing backup.sql..."
    docker compose exec -T postgres psql -U postgres -d postgres < backup.sql
else
    echo "No backup.sql found. Please import your data manually."
fi

echo ""
echo "Step 4: Updating environment variables..."
echo ""
echo "Your .env file should have:"
echo "  # Keep Supabase for Auth only"
echo "  SUPABASE_URL=your_supabase_url  # Keep for auth"
echo "  SUPABASE_KEY=your_supabase_key   # Keep for auth"
echo ""
echo "  # Local PostgreSQL (database operations)"
echo "  SUPABASE_DB_HOST=postgres"
echo "  SUPABASE_DB_PORT=5432"
echo "  SUPABASE_DB_NAME=postgres"
echo "  SUPABASE_DB_USER=postgres"
echo "  SUPABASE_DB_PASSWORD=changeme  # Change this!"
echo ""
echo "Step 5: Restarting backend..."
docker compose restart backend

echo ""
echo "✅ Migration complete!"
echo ""
echo "Next steps:"
echo "1. Update your .env file with local PostgreSQL settings"
echo "2. Restart containers: docker compose restart"
echo "3. Test the application"
echo ""
echo "To backup local database:"
echo "  docker compose exec postgres pg_dump -U postgres postgres > backup.sql"


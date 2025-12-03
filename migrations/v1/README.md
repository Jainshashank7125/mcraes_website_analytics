# Consolidated Database Schema Migration v1

This folder contains a consolidated database schema migration that includes all changes from migrations v1 through v19.

## Overview

The `complete_schema.sql` file contains:
- All table definitions with all columns
- All indexes for performance optimization
- All triggers for automatic updates
- All functions for business logic
- All comments for documentation

## What's Included

### Core Tables
- `brands` - Brands from Scrunch AI (with slug, logo_url, theme, version tracking)
- `prompts` - Prompts from Scrunch AI
- `responses` - Responses from Scrunch AI
- `citations` - Citations from responses

### GA4 Tables (with client_id support)
- `ga4_traffic_overview` - Daily traffic metrics
- `ga4_top_pages` - Top performing pages
- `ga4_traffic_sources` - Traffic acquisition sources
- `ga4_geographic` - Geographic breakdown
- `ga4_devices` - Device and platform breakdown
- `ga4_conversions` - Conversion events
- `ga4_realtime` - Realtime snapshot data
- `ga4_property_details` - Property configuration
- `ga4_revenue` - Daily revenue data
- `ga4_daily_conversions` - Daily aggregated conversions
- `ga4_kpi_snapshots` - Pre-calculated KPIs for 30-day periods (with client_id)
- `ga4_tokens` - Access tokens for authentication

### Agency Analytics Tables
- `agency_analytics_campaigns` - Campaign metadata
- `agency_analytics_campaign_rankings` - Campaign ranking data
- `agency_analytics_campaign_brands` - Links campaigns to brands
- `agency_analytics_keywords` - Keywords for campaigns
- `agency_analytics_keyword_rankings` - Daily keyword ranking data
- `agency_analytics_keyword_ranking_summaries` - Latest keyword rankings with changes

### Client Management Tables
- `clients` - Client entities (with version tracking, theme, branding)
- `client_campaigns` - Links clients to campaigns

### System Tables
- `audit_logs` - User actions and sync operations tracking
- `sync_jobs` - Async sync job status and progress
- `brand_kpi_selections` - KPI visibility preferences (with selected_charts)

## Key Features

1. **Client-Centric Support**: All GA4 tables now support both `brand_id` and `client_id` for flexible data organization
2. **Version Tracking**: Optimistic locking support for `brands`, `clients`, and `brand_kpi_selections`
3. **Automatic Slug Generation**: UUID-based slugs for brands and clients
4. **Comprehensive Indexing**: All tables have appropriate indexes for fast queries
5. **Trigger-Based Updates**: Automatic version increments and timestamp updates

## Usage

### For Fresh Database Setup

Run the complete schema migration:

```bash
docker compose exec postgres psql -U postgres -d postgres -f /path/to/migrations/v1/complete_schema.sql
```

Or from your local machine:

```bash
cat migrations/v1/complete_schema.sql | docker compose exec -T postgres psql -U postgres -d postgres
```

### For Existing Database

If you have an existing database, you can:

1. **Option A**: Run individual migrations (v1-v19) in order
2. **Option B**: Use this consolidated migration to verify your schema matches the expected state
3. **Option C**: Add missing columns/tables manually based on what's in this consolidated schema

## Important Notes

1. **Table Creation Order**: The migration creates tables in the correct order to handle foreign key dependencies:
   - Core tables (brands, prompts, responses) first
   - Clients table before GA4 tables
   - Agency Analytics tables
   - System tables

2. **Foreign Key Constraints**: Some constraints are added after table creation to handle circular dependencies (e.g., `client_campaigns.campaign_id`)

3. **client_id Column**: All GA4 tables support both `brand_id` and `client_id`. The `client_id` column is nullable to support backward compatibility during migration.

4. **Indexes**: Partial indexes are used for `client_id` columns (WHERE client_id IS NOT NULL) to optimize space and performance.

## Verification

After running the migration, verify the schema:

```sql
-- Check if ga4_kpi_snapshots has client_id
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'ga4_kpi_snapshots' 
AND column_name = 'client_id';

-- Check all tables
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
```

## Migration History

This consolidated migration includes changes from:
- v1: Core schema (brands, prompts, responses, citations)
- v2: GA4 tables setup
- v3: GA4 tokens table
- v4: Agency Analytics tables
- v5-v6: Brand slug support
- v7: Audit logs
- v8: Sync jobs
- v9-v10: Brand KPI selections
- v11: Brand logo and theme
- v12: UUID-based brand slugs
- v13: GA4 KPI snapshots
- v14: Additional GA4 tables
- v15: Clients table
- v16: Response composite indexes
- v17: Version tracking
- v18: Client ID support in GA4 tables (including ga4_kpi_snapshots)
- v19: Selected charts in KPI selections


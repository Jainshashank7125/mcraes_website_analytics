# API Documentation

## Project Overview

**McRAE's Website Analytics** is a comprehensive full-stack analytics platform that aggregates and visualizes data from multiple sources:

- **Scrunch AI**: AI platform visibility data including brands, prompts, and AI-generated responses
- **Google Analytics 4 (GA4)**: Website traffic, user behavior, and conversion metrics
- **Agency Analytics**: SEO campaign rankings, keyword performance, and search visibility data

The platform provides a unified dashboard to monitor brand performance across AI platforms and web analytics, enabling data-driven insights for marketing and SEO strategies.

---

## API Endpoints

### Base URL
- **Development**: `http://localhost:8000`
- **API Prefix**: `/api/v1`

### Health & Status

#### `GET /health`
**Description**: Health check endpoint to verify server status and configuration

**Response**: 
```json
{
  "status": "healthy",
  "config": {
    "supabase_url": "SET",
    "supabase_key": "SET",
    "scrunch_token": "SET"
  },
  "database": {
    "rest_api": "connected",
    "direct_postgres": "connected"
  }
}
```

**Associated View**: None (used internally for monitoring)

---

## Sync Endpoints

These endpoints synchronize data from external APIs (Scrunch AI, GA4, Agency Analytics) into the Supabase database.

### `GET /api/v1/sync/status`
**Description**: Get current sync status showing counts of brands, prompts, and responses in the database

**Response**:
```json
{
  "brands_count": 10,
  "prompts_count": 150,
  "responses_count": 5000
}
```

**Associated View**: 
- **Dashboard** (`/components/Dashboard.jsx`) - Displays counts in overview cards

---

### `POST /api/v1/sync/brands`
**Description**: Sync all brands from Scrunch AI API to Supabase

**Response**:
```json
{
  "status": "success",
  "message": "Synced 10 brands",
  "count": 10
}
```

**Associated View**: 
- **SyncPanel** (`/components/SyncPanel.jsx`) - Triggered via "Sync Scrunch API Data" button

---

### `POST /api/v1/sync/prompts`
**Description**: Sync prompts from Scrunch AI for all brands or a specific brand

**Query Parameters**:
- `brand_id` (optional): Filter by specific brand ID
- `stage` (optional): Filter by funnel stage (e.g., "Awareness", "Evaluation")
- `persona_id` (optional): Filter by persona ID

**Response**:
```json
{
  "status": "success",
  "message": "Synced 150 prompts across 10 brand(s)",
  "total_count": 150,
  "brand_results": [
    {"brand_id": 1, "brand_name": "Brand A", "count": 15}
  ]
}
```

**Associated View**: 
- **SyncPanel** (`/components/SyncPanel.jsx`) - Part of "Sync Scrunch API Data" operation

---

### `POST /api/v1/sync/responses`
**Description**: Sync AI responses from Scrunch AI for all brands or a specific brand

**Query Parameters**:
- `brand_id` (optional): Filter by specific brand ID
- `platform` (optional): Filter by AI platform (e.g., "ChatGPT", "Claude")
- `prompt_id` (optional): Filter by prompt ID
- `start_date` (optional): Start date filter (YYYY-MM-DD)
- `end_date` (optional): End date filter (YYYY-MM-DD)

**Response**:
```json
{
  "status": "success",
  "message": "Synced 5000 responses across 10 brand(s)",
  "total_count": 5000,
  "brand_results": [...]
}
```

**Associated View**: 
- **SyncPanel** (`/components/SyncPanel.jsx`) - Part of "Sync Scrunch API Data" operation

---

### `POST /api/v1/sync/all`
**Description**: Sync all Scrunch AI data (brands, prompts, responses) in one operation

**Response**:
```json
{
  "status": "success",
  "message": "Synced all data for all brands",
  "summary": {
    "brands": 10,
    "total_prompts": 150,
    "total_responses": 5000
  },
  "prompts_by_brand": [...],
  "responses_by_brand": [...]
}
```

**Associated View**: 
- **SyncPanel** (`/components/SyncPanel.jsx`) - Main "Sync Scrunch API Data" button triggers this endpoint

---

### `POST /api/v1/sync/ga4`
**Description**: Sync Google Analytics 4 data for all brands with GA4 configured or a specific brand

**Query Parameters**:
- `brand_id` (optional): Sync for specific brand ID
- `start_date` (optional): Start date (YYYY-MM-DD), defaults to 30 days ago
- `end_date` (optional): End date (YYYY-MM-DD), defaults to today
- `sync_realtime` (optional): Whether to sync realtime data (default: true)

**Response**:
```json
{
  "status": "success",
  "message": "Synced GA4 data for 5 brand(s)",
  "date_range": {
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  },
  "total_synced": {
    "brands": 5,
    "traffic_overview": 5,
    "top_pages": 250,
    "traffic_sources": 150,
    "geographic": 250,
    "devices": 15,
    "conversions": 30,
    "realtime": 5
  },
  "brand_results": [...]
}
```

**Associated View**: 
- **SyncPanel** (`/components/SyncPanel.jsx`) - "Sync GA4 Data" button

---

### `POST /api/v1/sync/agency-analytics`
**Description**: Sync Agency Analytics campaigns, rankings, keywords, and keyword rankings data

**Query Parameters**:
- `campaign_id` (optional): Sync specific campaign (if not provided, syncs all campaigns)
- `auto_match_brands` (optional): Automatically match campaigns to brands by URL (default: true)

**Response**:
```json
{
  "status": "success",
  "message": "Synced 20 campaigns, 200 ranking records, 500 keywords...",
  "total_synced": {
    "campaigns": 20,
    "rankings": 200,
    "keywords": 500,
    "keyword_rankings": 5000,
    "keyword_ranking_summaries": 500,
    "brand_links": 15
  },
  "campaign_results": [...]
}
```

**Associated View**: 
- **SyncPanel** (`/components/SyncPanel.jsx`) - "Sync Agency Analytics Data" button

---

## Data Retrieval Endpoints

These endpoints retrieve and query data from the Supabase database.

### Scrunch AI Data

#### `GET /api/v1/data/brands`
**Description**: Get all brands from database

**Query Parameters**:
- `limit` (optional): Number of records to return (default: 50)
- `offset` (optional): Offset for pagination (default: 0)

**Response**:
```json
{
  "items": [
    {
      "id": 1,
      "name": "Brand A",
      "website": "https://branda.com",
      "ga4_property_id": "123456789"
    }
  ],
  "count": 10
}
```

**Associated Views**: 
- **BrandAnalytics** (`/components/BrandAnalytics.jsx`) - Loads brands for filter dropdown
- **BrandAnalyticsDetail** (`/components/BrandAnalyticsDetail.jsx`) - Used when viewing brand details
- **BrandsList** (`/components/BrandsList.jsx`) - Displays list of all brands

---

#### `GET /api/v1/data/prompts`
**Description**: Get prompts from database with optional filters

**Query Parameters**:
- `brand_id` (optional): Filter by brand ID
- `stage` (optional): Filter by funnel stage
- `persona_id` (optional): Filter by persona ID
- `limit` (optional): Number of records (default: 50)
- `offset` (optional): Pagination offset (default: 0)

**Response**:
```json
{
  "items": [
    {
      "id": 1,
      "brand_id": 1,
      "text": "What is Brand A?",
      "stage": "Awareness",
      "persona_id": 1
    }
  ],
  "count": 150
}
```

**Associated Views**: 
- **BrandAnalyticsDetail** (`/components/BrandAnalyticsDetail.jsx`) - Loads prompts for brand insights table
- **DataView** (`/components/DataView.jsx`) - Displays prompts in data browser

---

#### `GET /api/v1/data/responses`
**Description**: Get AI responses from database with optional filters

**Query Parameters**:
- `brand_id` (optional): Filter by brand ID
- `platform` (optional): Filter by AI platform
- `prompt_id` (optional): Filter by prompt ID
- `start_date` (optional): Start date (YYYY-MM-DD)
- `end_date` (optional): End date (YYYY-MM-DD)
- `limit` (optional): Number of records (default: 50)
- `offset` (optional): Pagination offset (default: 0)

**Response**:
```json
{
  "items": [
    {
      "id": 1,
      "brand_id": 1,
      "prompt_id": 1,
      "platform": "ChatGPT",
      "brand_present": true,
      "brand_sentiment": "positive",
      "citations": ["url1", "url2"],
      "competitors_present": ["Competitor A"]
    }
  ],
  "count": 5000
}
```

**Associated Views**: 
- **BrandAnalyticsDetail** (`/components/BrandAnalyticsDetail.jsx`) - Loads responses for analytics calculations
- **DataView** (`/components/DataView.jsx`) - Displays responses in data browser

---

#### `GET /api/v1/data/analytics/brands`
**Description**: Get comprehensive analytics for brands based on responses data

**Query Parameters**:
- `brand_id` (optional): Get analytics for specific brand (if not provided, returns all brands)

**Response**:
```json
{
  "brands": [
    {
      "id": 1,
      "name": "Brand A",
      "analytics": {
        "total_responses": 500,
        "platform_distribution": {"ChatGPT": 300, "Claude": 200},
        "stage_distribution": {"Awareness": 200, "Evaluation": 300},
        "brand_presence": {"present": 400, "absent": 100},
        "brand_sentiment": {"positive": 250, "neutral": 100, "negative": 50},
        "top_competitors": [{"name": "Competitor A", "count": 50}],
        "top_topics": [{"topic": "features", "count": 100}],
        "citation_metrics": {"total": 1000, "average_per_response": 2.0},
        "country_distribution": {"US": 300, "UK": 200},
        "persona_distribution": {"Developer": 200, "Manager": 300}
      }
    }
  ],
  "total_brands": 10,
  "global_analytics": {...}
}
```

**Associated Views**: 
- **BrandAnalytics** (`/components/BrandAnalytics.jsx`) - Main analytics dashboard showing charts and metrics
- **BrandAnalyticsDetail** (`/components/BrandAnalyticsDetail.jsx`) - Shows brand-specific analytics

---

### Google Analytics 4 Data

#### `GET /api/v1/data/ga4/properties`
**Description**: Get all GA4 properties accessible via service account

**Response**:
```json
{
  "items": [
    {
      "propertyId": "123456789",
      "displayName": "Brand A Website",
      "account": "Account Name"
    }
  ],
  "count": 5
}
```

**Associated View**: None (used for configuration/admin purposes)

---

#### `GET /api/v1/data/ga4/brand/{brand_id}`
**Description**: Get comprehensive GA4 analytics for a specific brand

**Path Parameters**:
- `brand_id` (required): Brand ID

**Query Parameters**:
- `start_date` (optional): Start date (YYYY-MM-DD), defaults to 30 days ago
- `end_date` (optional): End date (YYYY-MM-DD), defaults to today

**Response**:
```json
{
  "brand_id": 1,
  "brand_name": "Brand A",
  "ga4_configured": true,
  "property_id": "123456789",
  "analytics": {
    "trafficOverview": {
      "sessions": 10000,
      "engagedSessions": 8000,
      "averageSessionDuration": 180,
      "engagementRate": 0.8,
      "sessionsChange": 5.2,
      "engagedSessionsChange": 3.1
    },
    "topPages": [
      {
        "pagePath": "/home",
        "views": 5000,
        "users": 3000,
        "avgSessionDuration": 200
      }
    ],
    "trafficSources": [
      {
        "source": "google",
        "sessions": 6000,
        "users": 4000,
        "bounceRate": 0.3
      }
    ],
    "geographic": [
      {
        "country": "United States",
        "users": 5000,
        "sessions": 7000
      }
    ],
    "devices": [
      {
        "deviceCategory": "desktop",
        "operatingSystem": "Windows",
        "users": 4000,
        "sessions": 6000,
        "bounceRate": 0.25
      }
    ],
    "conversions": [
      {
        "eventName": "purchase",
        "count": 100,
        "users": 80
      }
    ],
    "realtime": {
      "totalActiveUsers": 50,
      "activePages": [
        {
          "pagePath": "/home",
          "activeUsers": 30
        }
      ]
    },
    "propertyDetails": {
      "propertyId": "123456789",
      "displayName": "Brand A Website",
      "timeZone": "America/New_York",
      "currencyCode": "USD"
    },
    "dateRange": {
      "startDate": "2024-01-01",
      "endDate": "2024-01-31"
    }
  }
}
```

**Associated View**: 
- **BrandAnalyticsDetail** (`/components/BrandAnalyticsDetail.jsx`) - Displays GA4 metrics, top pages, traffic sources, geographic breakdown, devices, conversions, and realtime data

---

#### `GET /api/v1/data/ga4/traffic-overview/{property_id}`
**Description**: Get traffic overview for a GA4 property

**Path Parameters**:
- `property_id` (required): GA4 Property ID

**Query Parameters**:
- `start_date` (optional): Start date (YYYY-MM-DD)
- `end_date` (optional): End date (YYYY-MM-DD)

**Associated View**: None (used internally by brand analytics endpoint)

---

#### `GET /api/v1/data/ga4/top-pages/{property_id}`
**Description**: Get top performing pages for a GA4 property

**Path Parameters**:
- `property_id` (required): GA4 Property ID

**Query Parameters**:
- `start_date` (optional): Start date (YYYY-MM-DD)
- `end_date` (optional): End date (YYYY-MM-DD)
- `limit` (optional): Number of pages (default: 10)

**Associated View**: None (used internally by brand analytics endpoint)

---

#### `GET /api/v1/data/ga4/traffic-sources/{property_id}`
**Description**: Get traffic sources for a GA4 property

**Path Parameters**:
- `property_id` (required): GA4 Property ID

**Query Parameters**:
- `start_date` (optional): Start date (YYYY-MM-DD)
- `end_date` (optional): End date (YYYY-MM-DD)

**Associated View**: None (used internally by brand analytics endpoint)

---

#### `GET /api/v1/data/ga4/geographic/{property_id}`
**Description**: Get geographic breakdown for a GA4 property

**Path Parameters**:
- `property_id` (required): GA4 Property ID

**Query Parameters**:
- `start_date` (optional): Start date (YYYY-MM-DD)
- `end_date` (optional): End date (YYYY-MM-DD)
- `limit` (optional): Number of countries (default: 20)

**Associated View**: None (used internally by brand analytics endpoint)

---

#### `GET /api/v1/data/ga4/devices/{property_id}`
**Description**: Get device breakdown for a GA4 property

**Path Parameters**:
- `property_id` (required): GA4 Property ID

**Query Parameters**:
- `start_date` (optional): Start date (YYYY-MM-DD)
- `end_date` (optional): End date (YYYY-MM-DD)

**Associated View**: None (used internally by brand analytics endpoint)

---

#### `GET /api/v1/data/ga4/realtime/{property_id}`
**Description**: Get realtime snapshot for a GA4 property

**Path Parameters**:
- `property_id` (required): GA4 Property ID

**Associated View**: None (used internally by brand analytics endpoint)

---

#### `GET /api/v1/data/ga4/brands-with-ga4`
**Description**: Get all brands that have GA4 property IDs configured

**Response**:
```json
{
  "items": [
    {
      "id": 1,
      "name": "Brand A",
      "ga4_property_id": "123456789"
    }
  ],
  "count": 5
}
```

**Associated View**: None (used for configuration/admin purposes)

---

### Agency Analytics Data

#### `GET /api/v1/data/agency-analytics/campaigns`
**Description**: Get all Agency Analytics campaigns from database

**Response**:
```json
{
  "campaigns": [
    {
      "id": 1,
      "company": "Brand A",
      "url": "https://branda.com",
      "status": "active"
    }
  ],
  "count": 20
}
```

**Associated View**: 
- **AgencyAnalytics** (`/components/AgencyAnalytics.jsx`) - Loads campaigns for dropdown selection

---

#### `GET /api/v1/data/agency-analytics/campaign/{campaign_id}/rankings`
**Description**: Get campaign rankings for a specific campaign

**Path Parameters**:
- `campaign_id` (required): Campaign ID

**Query Parameters**:
- `start_date` (optional): Start date (YYYY-MM-DD)
- `end_date` (optional): End date (YYYY-MM-DD)

**Response**:
```json
{
  "campaign": {
    "id": 1,
    "company": "Brand A",
    "url": "https://branda.com"
  },
  "rankings": [
    {
      "id": 1,
      "campaign_id": 1,
      "date": "2024-01-01",
      "google_ranking_count": 150,
      "google_ranking_change": 10,
      "google_local_count": 50,
      "google_mobile_count": 100,
      "bing_ranking_count": 80,
      "ranking_average": 45.5,
      "search_volume": 100000,
      "competition": 0.65
    }
  ],
  "count": 12
}
```

**Associated View**: 
- **AgencyAnalytics** (`/components/AgencyAnalytics.jsx`) - Displays quarterly campaign rankings table

---

#### `GET /api/v1/data/agency-analytics/rankings`
**Description**: Get all campaign rankings

**Query Parameters**:
- `start_date` (optional): Start date (YYYY-MM-DD)
- `end_date` (optional): End date (YYYY-MM-DD)
- `limit` (optional): Number of records (default: 1000)

**Associated View**: None (used for data export/admin purposes)

---

#### `GET /api/v1/data/agency-analytics/campaign/{campaign_id}/keywords`
**Description**: Get keywords for a specific campaign

**Path Parameters**:
- `campaign_id` (required): Campaign ID

**Query Parameters**:
- `limit` (optional): Number of keywords (default: 1000)

**Associated View**: None (used internally)

---

#### `GET /api/v1/data/agency-analytics/keywords`
**Description**: Get all keywords

**Query Parameters**:
- `campaign_id` (optional): Filter by campaign ID
- `limit` (optional): Number of keywords (default: 1000)

**Associated View**: None (used for data export/admin purposes)

---

#### `GET /api/v1/data/agency-analytics/keyword/{keyword_id}/rankings`
**Description**: Get keyword rankings for a specific keyword

**Path Parameters**:
- `keyword_id` (required): Keyword ID

**Query Parameters**:
- `start_date` (optional): Start date (YYYY-MM-DD)
- `end_date` (optional): End date (YYYY-MM-DD)
- `limit` (optional): Number of records (default: 1000)

**Associated View**: None (used internally)

---

#### `GET /api/v1/data/agency-analytics/keyword/{keyword_id}/ranking-summary`
**Description**: Get keyword ranking summary (latest + change)

**Path Parameters**:
- `keyword_id` (required): Keyword ID

**Response**:
```json
{
  "keyword_id": 1,
  "summary": {
    "keyword_id": 1,
    "campaign_id": 1,
    "keyword_phrase": "brand analytics",
    "google_ranking": 5,
    "google_mobile_ranking": 6,
    "google_local_ranking": 4,
    "bing_ranking": 7,
    "ranking_change": 2,
    "search_volume": 50000,
    "competition": 0.7,
    "date": "2024-01-31"
  }
}
```

**Associated View**: None (used internally)

---

#### `GET /api/v1/data/agency-analytics/campaign/{campaign_id}/keyword-rankings`
**Description**: Get all keyword rankings for a campaign

**Path Parameters**:
- `campaign_id` (required): Campaign ID

**Query Parameters**:
- `limit` (optional): Number of records (default: 1000)

**Associated View**: None (used internally)

---

#### `GET /api/v1/data/agency-analytics/campaign/{campaign_id}/keyword-ranking-summaries`
**Description**: Get all keyword ranking summaries for a campaign

**Path Parameters**:
- `campaign_id` (required): Campaign ID

**Response**:
```json
{
  "campaign_id": 1,
  "summaries": [
    {
      "keyword_id": 1,
      "keyword_phrase": "brand analytics",
      "google_ranking": 5,
      "google_mobile_ranking": 6,
      "google_local_ranking": 4,
      "bing_ranking": 7,
      "ranking_change": 2,
      "search_volume": 50000,
      "competition": 0.7,
      "date": "2024-01-31"
    }
  ],
  "count": 100
}
```

**Associated View**: 
- **AgencyAnalytics** (`/components/AgencyAnalytics.jsx`) - Displays keyword rankings table with latest positions and changes

---

#### `GET /api/v1/data/agency-analytics/campaign-brands`
**Description**: Get campaign-brand links (which campaigns are linked to which brands)

**Query Parameters**:
- `campaign_id` (optional): Filter by campaign ID
- `brand_id` (optional): Filter by brand ID

**Response**:
```json
{
  "links": [
    {
      "campaign_id": 1,
      "brand_id": 1,
      "match_method": "url",
      "match_confidence": "exact"
    }
  ],
  "count": 15
}
```

**Associated View**: 
- **AgencyAnalytics** (`/components/AgencyAnalytics.jsx`) - Used to determine which campaigns are linked to brands
- **BrandAnalyticsDetail** (`/components/BrandAnalyticsDetail.jsx`) - Loads campaigns linked to a brand

---

#### `POST /api/v1/data/agency-analytics/campaign-brands`
**Description**: Manually link a campaign to a brand

**Request Body**:
```json
{
  "campaign_id": 1,
  "brand_id": 1,
  "match_method": "manual",
  "match_confidence": "manual"
}
```

**Associated View**: None (used for admin/manual linking)

---

#### `GET /api/v1/data/agency-analytics/brand/{brand_id}/campaigns`
**Description**: Get all campaigns linked to a brand

**Path Parameters**:
- `brand_id` (required): Brand ID

**Response**:
```json
{
  "brand_id": 1,
  "campaigns": [
    {
      "id": 1,
      "company": "Brand A",
      "url": "https://branda.com",
      "status": "active",
      "link_info": {
        "match_method": "url",
        "match_confidence": "exact"
      }
    }
  ],
  "count": 2
}
```

**Associated View**: 
- **BrandAnalyticsDetail** (`/components/BrandAnalyticsDetail.jsx`) - Displays linked Agency Analytics campaigns in a table

---

## Database Management Endpoints

### `POST /api/v1/database/migrate/add-brand-id`
**Description**: Provides SQL instructions for adding brand_id columns to prompts and responses tables

**Response**:
```json
{
  "status": "info",
  "message": "Please add brand_id columns manually via Supabase SQL Editor...",
  "sql": "ALTER TABLE prompts ADD COLUMN IF NOT EXISTS brand_id INTEGER;..."
}
```

**Associated View**: None (used for database migration)

---

### `POST /api/v1/database/update-brand-ids`
**Description**: Update existing prompts and responses with brand_id values

**Query Parameters**:
- `brand_id` (optional): Brand ID to use (defaults to config value)

**Response**:
```json
{
  "status": "success",
  "message": "Updated brand_id for existing records",
  "brand_id": 3230,
  "prompts_updated": 150,
  "responses_updated": 5000
}
```

**Associated View**: None (used for database migration)

---

### `POST /api/v1/database/verify`
**Description**: Verify database schema and check for records without brand_id

**Response**:
```json
{
  "status": "success",
  "schema": {
    "prompts_has_brand_id": true,
    "responses_has_brand_id": true,
    "prompts_without_brand_id": 0,
    "responses_without_brand_id": 0
  },
  "message": "Database verification complete"
}
```

**Associated View**: None (used for database verification)

---

## Frontend Views Summary

### Dashboard (`/`)
- **APIs Used**: `GET /api/v1/sync/status`
- **Purpose**: Overview of total brands, prompts, and responses counts

### Brands List (`/brands`)
- **APIs Used**: `GET /api/v1/data/brands`
- **Purpose**: Display all brands with navigation to brand detail pages

### Brand Analytics (`/analytics`)
- **APIs Used**: 
  - `GET /api/v1/data/brands` (for filter dropdown)
  - `GET /api/v1/data/analytics/brands` (for analytics charts and metrics)
- **Purpose**: Comprehensive analytics dashboard with charts showing platform distribution, stage distribution, sentiment, competitors, topics, etc.

### Brand Analytics Detail (`/brands/:id`)
- **APIs Used**:
  - `GET /api/v1/data/analytics/brands?brand_id={id}` (Scrunch AI analytics)
  - `GET /api/v1/data/prompts?brand_id={id}` (prompts list)
  - `GET /api/v1/data/responses?brand_id={id}` (responses list)
  - `GET /api/v1/data/ga4/brand/{id}` (GA4 analytics)
  - `GET /api/v1/data/agency-analytics/brand/{id}/campaigns` (linked campaigns)
- **Purpose**: Detailed brand performance view combining Scrunch AI insights, GA4 web analytics, and Agency Analytics SEO data

### Agency Analytics (`/agency-analytics`)
- **APIs Used**:
  - `GET /api/v1/data/agency-analytics/campaigns` (campaign list)
  - `GET /api/v1/data/agency-analytics/campaign/{id}/rankings` (quarterly rankings)
  - `GET /api/v1/data/agency-analytics/campaign/{id}/keyword-ranking-summaries` (keyword rankings)
  - `GET /api/v1/data/agency-analytics/campaign-brands` (campaign-brand links)
- **Purpose**: View SEO campaign performance, rankings, and keyword positions

### Sync Panel (`/sync`)
- **APIs Used**:
  - `POST /api/v1/sync/all` (sync Scrunch AI data)
  - `POST /api/v1/sync/ga4` (sync GA4 data)
  - `POST /api/v1/sync/agency-analytics` (sync Agency Analytics data)
- **Purpose**: Manual trigger for syncing data from external APIs

### Data View (`/data`)
- **APIs Used**:
  - `GET /api/v1/data/brands`
  - `GET /api/v1/data/prompts`
  - `GET /api/v1/data/responses`
- **Purpose**: Browse raw data from the database

---

## Error Handling

All endpoints return standard HTTP status codes:
- `200`: Success
- `400`: Bad Request (invalid parameters)
- `404`: Not Found (resource doesn't exist)
- `500`: Internal Server Error

Error responses follow this format:
```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## Authentication

Currently, the API does not require authentication. In production, consider implementing:
- API key authentication
- JWT tokens
- OAuth2

---

## Rate Limiting

No rate limiting is currently implemented. Consider adding rate limits for production use.

---

## Notes

- All date parameters should be in `YYYY-MM-DD` format
- Pagination uses `limit` and `offset` parameters
- The sync endpoints may take several minutes for large datasets
- GA4 endpoints require brands to have `ga4_property_id` configured in the database
- Agency Analytics campaigns are automatically matched to brands by URL during sync (if `auto_match_brands=true`)


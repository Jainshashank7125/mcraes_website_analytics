# McRAE's Website Analytics – Complete Project Features Documentation

**Document generated:** January 2026  
**Purpose:** Comprehensive, detailed overview of all features, implementations, workflows, and technical details.

**Table of Contents:**
1. [Project Overview](#1-project-overview)
2. [Data Sources & Integrations](#2-data-sources--integrations)
3. [Backend Features](#3-backend-features)
4. [Frontend Features](#4-frontend-features)
5. [KPI & Chart Configuration](#5-kpi--chart-configuration)
6. [Database Schema](#6-database-schema)
7. [Automation & DevOps](#7-automation--devops)
8. [User Workflows](#8-user-workflows)
9. [API Examples](#9-api-examples)
10. [Security & Performance](#10-security--performance)
11. [Summary](#11-summary)

---

## 1. Project Overview

**McRAE's Website Analytics** is a full-stack analytics platform that:

- **Aggregates data** from Scrunch AI, Google Analytics 4 (GA4), and Agency Analytics
- **Stores** it in a Supabase/PostgreSQL database
- **Exposes** it via a FastAPI backend and React frontend
- **Delivers** branded, shareable reporting dashboards for clients

Tech stack:

- **Backend:** FastAPI, Python 3.8+, SQLAlchemy, Supabase client
- **Frontend:** React, Vite, Material-UI, TanStack Query, Recharts, Framer Motion
- **Database:** PostgreSQL (Supabase)
- **Deployment:** Docker, Nginx, cron for daily sync

---

## 2. Data Sources & Integrations

### 2.1 Scrunch AI

**What:** AI visibility data (brands, prompts, AI-generated responses)

**API Details:**
- **Base URL:** `https://api.scrunchai.com/v1`
- **Authentication:** Bearer token (stored in environment: `SCRUNCH_API_TOKEN`)
- **Rate Limits:** Handled via pagination (max 1000 items per request)
- **Client Implementation:** `app/services/scrunch_client.py`

**Data Structure:**
- **Brands:** ID, name, website, created_at
- **Prompts:** ID, brand_id, text, stage (funnel stage), persona_id, persona_name, platforms (array), tags, topics, created_at
- **Responses:** ID, brand_id, prompt_id, prompt text, response_text, platform (ChatGPT, Claude, etc.), country, persona_id, stage, branded (boolean), brand_present (boolean), brand_sentiment (positive/neutral/negative), brand_position (top/middle/bottom), competitors_present (array), citations (JSON), created_at

**Sync Features:**
- **Pagination:** Automatic handling of large datasets (loops until all pages fetched)
- **Filters Available:**
  - `brand_id` - Filter by specific brand
  - `stage` - Filter by funnel stage (Awareness, Evaluation, etc.)
  - `persona_id` - Filter by persona ID
  - `platform` - Filter by AI platform (ChatGPT, Claude, etc.)
  - `start_date` / `end_date` - Date range filter (YYYY-MM-DD format)
- **Upsert Logic:** Uses ID-based upsert (insert or update based on ID)
- **Error Handling:** Retries on transient failures, logs errors, continues on partial failures

**Storage Tables:**
- `brands` - Brand metadata
- `prompts` - AI prompts linked to brands
- `responses` - AI-generated responses with analytics
- `citations` - Extracted citations from responses (normalized into separate table)

**Use Cases:**
- Track brand presence in AI-generated answers
- Monitor brand sentiment (positive/neutral/negative)
- Identify competitors mentioned alongside brand
- Analyze platform distribution (which AI platforms mention the brand)
- Track citations and sources
- Measure brand position (top/middle/bottom of AI responses)

### 2.2 Google Analytics 4 (GA4)

**What:** Website traffic and behavior analytics

**Authentication:**
- **Method:** OAuth2 Service Account (JSON key file)
- **Key File:** `service-key.json` (stored securely, never committed)
- **Token Generation:** Daily via `generate_ga4_token.py` script
- **Token Storage:** `ga4_tokens` table (stores access token, expiry, refresh token)
- **Token Refresh:** Automatic refresh before expiry (handled by `ga4_token_service.py`)
- **Service Account Setup:** Requires GA4 property access granted in Google Cloud Console

**API Details:**
- **API Used:** Google Analytics Data API (GA4)
- **Client Implementation:** `app/services/ga4_client.py`
- **Rate Limits:** Handled with exponential backoff retries
- **Date Range:** Supports custom date ranges (default: last 30 days)

**Data Types Synced:**
1. **Traffic Overview** (`ga4_traffic_overview`):
   - Daily aggregated metrics: users, sessions, new_users, engaged_sessions
   - Engagement: bounce_rate, avg_session_duration, engagement_rate
   - Conversions: conversions count, revenue
   - Period-over-period change calculations (sessions_change, engaged_sessions_change, etc.)

2. **Top Pages** (`ga4_top_pages`):
   - Page path, views, users, avg_session_duration
   - Ranked by views (top N pages per day)

3. **Traffic Sources** (`ga4_traffic_sources`):
   - Source/medium breakdown
   - Sessions, users, bounce_rate per source
   - Channel grouping (Organic, Paid, Direct, Referral, Social, Email)

4. **Geographic** (`ga4_geographic`):
   - Country-level breakdown
   - Users, sessions per country
   - Supports both aggregated (all dates) and daily breakdown modes

5. **Devices** (`ga4_devices`):
   - Device category (desktop, mobile, tablet)
   - Operating system
   - Users, sessions, bounce_rate per device

6. **Conversions** (`ga4_conversions`):
   - Conversion events (custom events configured in GA4)
   - Event count, users per conversion event
   - Daily breakdown

7. **Realtime** (`ga4_realtime`):
   - Current active users
   - Active pages (JSON array)
   - Snapshot timestamp

8. **Property Details** (`ga4_property_details`):
   - Property metadata: display_name, time_zone, currency_code
   - Cached to avoid repeated API calls

**Storage Tables:**
- `ga4_traffic_overview` - Daily traffic metrics
- `ga4_top_pages` - Top performing pages
- `ga4_traffic_sources` - Traffic acquisition channels
- `ga4_geographic` - Geographic breakdown (country-level)
- `ga4_devices` - Device/platform breakdown
- `ga4_conversions` - Conversion events
- `ga4_realtime` - Realtime user snapshots
- `ga4_tokens` - Access token storage
- `ga4_property_details` - Property metadata cache

**Mapping:**
- **Brand-level:** Brands can have `ga4_property_id` directly
- **Client-level:** Clients can have `ga4_property_id` (preferred approach)
- **Dual Support:** System supports both approaches for backward compatibility

**Use Cases:**
- Track website traffic (users, sessions)
- Measure engagement (bounce rate, session duration, engagement rate)
- Analyze traffic sources (organic, paid, direct, etc.)
- Geographic analysis (where users are located)
- Device analysis (desktop vs mobile)
- Conversion tracking (goals, revenue)
- Realtime monitoring (current active users)

### 2.3 Agency Analytics

**What:** SEO campaigns, keywords, rankings data

**API Details:**
- **API Used:** Agency Analytics API
- **Client Implementation:** `app/services/agency_analytics_client.py`
- **Authentication:** API key/token (stored in environment)
- **Rate Limits:** Handled with pagination and rate limiting

**Data Types Synced:**
1. **Campaigns** (`agency_analytics_campaigns`):
   - Campaign ID, name, URL, client information
   - Status, created date, updated date
   - Links to clients/brands

2. **Rankings** (`agency_analytics_rankings`):
   - Keyword ID, date, Google ranking, Bing ranking
   - Search volume, URL ranking for
   - Historical ranking data

3. **Keywords** (`agency_analytics_keywords`):
   - Keyword ID, keyword text, search volume
   - Campaign ID, URL tracking
   - Keyword metadata

4. **Keyword Rankings** (`agency_analytics_keyword_rankings`):
   - Daily ranking snapshots per keyword
   - Google and Bing rankings over time
   - Ranking changes tracked

5. **Keyword Ranking Summaries** (`agency_analytics_keyword_ranking_summaries`):
   - Aggregated summaries (average rankings, trends)
   - Visibility percentages (top 10, top 3, etc.)
   - Improving/declining/stable keyword counts

**Auto-Matching:**
- **Feature:** Automatic brand–campaign linking by URL matching
- **Logic:** Compares campaign URL with brand website URL
- **Configurable:** Can be enabled/disabled via `auto_match_brands` parameter
- **Manual Override:** Can manually link/unlink campaigns via API

**Storage Tables:**
- `agency_analytics_campaigns` - Campaign metadata
- `agency_analytics_rankings` - Ranking records
- `agency_analytics_keywords` - Keyword definitions
- `agency_analytics_keyword_rankings` - Historical keyword rankings
- `agency_analytics_keyword_ranking_summaries` - Aggregated keyword summaries
- `campaign_brands` / `client_campaigns` - Campaign–brand/client linking tables

**Use Cases:**
- Track keyword rankings over time (Google, Bing)
- Monitor search visibility (top 10, top 3 percentages)
- Analyze keyword performance (search volume, ranking trends)
- Identify improving/declining keywords
- Campaign performance tracking
- SEO reporting and insights

---

## 3. Backend Features

### 3.0 Architecture Overview

**Framework:** FastAPI (Python 3.8+)
**Database:** PostgreSQL via Supabase (direct connection + REST API)
**ORM:** SQLAlchemy for models, direct SQL for complex queries
**API Structure:** RESTful API with `/api/v1` prefix
**Documentation:** Auto-generated Swagger UI (`/docs`) and ReDoc (`/redoc`)

**Key Files:**
- `main.py` - FastAPI app initialization, middleware, route registration
- `app/api/` - API route handlers (data.py, sync.py, auth.py, etc.)
- `app/services/` - Business logic and external API clients
- `app/db/models.py` - SQLAlchemy models
- `app/core/` - Core utilities (config, database, error handlers, JWT utils)

---

### 3.1 API Structure

- **Base:** `/api/v1`
- **Docs:** Swagger at `/docs`, ReDoc at `/redoc`
- **Health:** `GET /health` (config and DB status)

### 3.2 Authentication

- **Supabase Auth (v1):** `auth.py` – signup, signin, signout, refresh, `/auth/me`
- **Local Auth (v2):** `auth_v2.py` – JWT + refresh tokens, `users` and `refresh_tokens` tables
  - Endpoints: signup, signin, signout, refresh, `/auth/v2/me`, cleanup of expired tokens

### 3.3 Sync Endpoints

**Base Path:** `/api/v1/sync`

**Authentication:** Most endpoints require authentication (JWT token). Exception: cron jobs can use `cron=true` query parameter with credentials.

#### `POST /api/v1/sync/brands`
**Description:** Sync all brands from Scrunch AI API to database

**Request:**
```bash
POST /api/v1/sync/brands
Headers: Authorization: Bearer <token>
```

**Response:**
```json
{
  "status": "success",
  "message": "Synced 10 brands",
  "count": 10,
  "brands": [
    {"id": 1, "name": "Brand A", "website": "https://branda.com"},
    ...
  ]
}
```

**Implementation Details:**
- Fetches all brands from Scrunch API
- Uses pagination to handle large datasets
- Upserts based on brand ID (insert or update)
- Logs audit event: `SYNC_BRANDS`
- Returns count of synced brands

#### `POST /api/v1/sync/prompts`
**Description:** Sync prompts from Scrunch AI

**Query Parameters:**
- `brand_id` (optional): Sync prompts for specific brand only
- `stage` (optional): Filter by funnel stage (e.g., "Awareness", "Evaluation")
- `persona_id` (optional): Filter by persona ID

**Request Example:**
```bash
POST /api/v1/sync/prompts?brand_id=123&stage=Awareness
```

**Response:**
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

**Implementation Details:**
- If `brand_id` provided: syncs only for that brand
- If no `brand_id`: syncs prompts for all brands in database
- Applies filters (stage, persona_id) if provided
- Handles pagination automatically
- Upserts based on prompt ID

#### `POST /api/v1/sync/responses`
**Description:** Sync AI responses from Scrunch AI

**Query Parameters:**
- `brand_id` (optional): Sync responses for specific brand
- `platform` (optional): Filter by AI platform (e.g., "ChatGPT", "Claude")
- `prompt_id` (optional): Filter by prompt ID
- `start_date` (optional): Start date (YYYY-MM-DD)
- `end_date` (optional): End date (YYYY-MM-DD)

**Request Example:**
```bash
POST /api/v1/sync/responses?brand_id=123&start_date=2025-01-01&end_date=2025-01-31
```

**Response:**
```json
{
  "status": "success",
  "message": "Synced 5000 responses across 10 brand(s)",
  "total_count": 5000,
  "brand_results": [
    {"brand_id": 1, "brand_name": "Brand A", "count": 500}
  ]
}
```

**Implementation Details:**
- Supports date range filtering
- Can filter by platform, prompt_id, brand_id
- Handles large datasets with pagination
- Upserts based on response ID
- Also syncs citations (normalized into `citations` table)

#### `POST /api/v1/sync/all`
**Description:** Sync all Scrunch AI data in one operation (brands, prompts, responses)

**Query Parameters:**
- `sync_mode` (default: "complete"): "new" (only missing) or "complete" (all)
- `start_date` (optional): Start date for responses sync
- `end_date` (optional): End date for responses sync
- `cron` (optional): Set to true for cron jobs

**Request Example:**
```bash
POST /api/v1/sync/all?sync_mode=complete&start_date=2025-01-01&end_date=2025-01-31
```

**Response:**
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

**Implementation Details:**
- Executes in sequence: brands → prompts → responses
- Can take 30+ minutes for large datasets
- Runs in background (async)
- Creates sync job record for tracking

#### `POST /api/v1/sync/ga4`
**Description:** Sync Google Analytics 4 data

**Query Parameters:**
- `sync_mode` (default: "complete"): "new" or "complete"
- `client_id` (optional): Sync for specific client
- `start_date` (optional): Start date (defaults to 30 days ago)
- `end_date` (optional): End date (defaults to today)
- `sync_realtime` (default: true): Whether to sync realtime data

**Request Example:**
```bash
POST /api/v1/sync/ga4?client_id=123&start_date=2025-01-01&end_date=2025-01-31
```

**Response:**
```json
{
  "status": "success",
  "message": "Synced GA4 data for 5 brand(s)",
  "date_range": {
    "start_date": "2025-01-01",
    "end_date": "2025-01-31"
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

**Implementation Details:**
- First refreshes GA4 access token (if expired)
- Syncs all GA4 data types (traffic, pages, sources, geographic, devices, conversions, realtime)
- Supports daily breakdown mode (one row per day) or aggregated mode
- Handles rate limits with exponential backoff
- Stores data with both `brand_id` and `client_id` for dual support

#### `POST /api/v1/sync/agency-analytics`
**Description:** Sync Agency Analytics campaigns, rankings, keywords

**Query Parameters:**
- `sync_mode` (default: "complete"): "new" or "complete"
- `campaign_id` (optional): Sync specific campaign only
- `auto_match_brands` (default: true): Automatically match campaigns to brands by URL
- `start_date` (optional): Start date for keyword rankings
- `end_date` (optional): End date for keyword rankings

**Request Example:**
```bash
POST /api/v1/sync/agency-analytics?sync_mode=complete&auto_match_brands=true
```

**Response:**
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

**Implementation Details:**
- Can take 2+ hours for complete sync (very large dataset)
- Syncs in sequence: campaigns → rankings → keywords → keyword_rankings → summaries
- Auto-matches campaigns to brands/clients by URL comparison
- Creates linking records in `client_campaigns` table
- Handles pagination for large keyword/ranking datasets

#### `GET /api/v1/sync/status`
**Description:** Get current sync status (counts from database)

**Request:**
```bash
GET /api/v1/sync/status
```

**Response:**
```json
{
  "brands_count": 10,
  "prompts_count": 150,
  "responses_count": 5000,
  "ga4_traffic_overview_count": 1500,
  "agency_analytics_campaigns_count": 20
}
```

**Implementation Details:**
- Fast query (counts from database, no API calls)
- Used by dashboard to show current data status
- No authentication required (public status endpoint)

### 3.4 Sync Jobs

- **Tables:** `sync_jobs` (and related)
- **Endpoints:** `GET /sync/jobs`, `GET /sync/jobs/{job_id}`, `POST /sync/jobs/{job_id}/cancel`
- **Behavior:** Background sync with job tracking and cancellation

### 3.5 Data Endpoints

**Scrunch / core:**

- `GET /data/brands` – List brands (pagination)
- `GET /data/brands/slug/{slug}` – Brand by slug
- `GET /data/prompts` – Prompts (brand_id, stage, persona_id, pagination)
- `GET /data/responses` – Responses (brand_id, platform, prompt_id, dates, pagination)
- `GET /data/analytics/brands` – Brand analytics from responses
- `GET /data/prompts-analytics` – Prompts analytics

**GA4:**

- `GET /data/ga4/properties` – List GA4 properties
- `GET /data/ga4/brand/{brand_id}` – GA4 for brand
- `GET /data/ga4/client/{client_id}` – GA4 for client
- `GET /data/ga4/traffic-overview/{property_id}`, `top-pages`, `traffic-sources`, `geographic`, `devices`, `realtime`
- `GET /data/ga4/brands-with-ga4` – Brands with GA4 configured

**Agency Analytics:**

- `GET /data/agency-analytics/campaigns` – Campaigns
- `GET /data/agency-analytics/campaign/{id}/rankings` – Campaign rankings
- `GET /data/agency-analytics/rankings` – All rankings
- `GET /data/agency-analytics/campaign/{id}/keywords` – Campaign keywords
- `GET /data/agency-analytics/keywords` – All keywords
- `GET /data/agency-analytics/keyword/{id}/rankings` – Keyword rankings
- `GET /data/agency-analytics/keyword/{id}/ranking-summary` – Keyword summary
- `GET/POST /data/agency-analytics/campaign-brands` – Campaign–brand links
- `GET /data/agency-analytics/brand/{brand_id}/campaigns` – Campaigns for brand

**Reporting dashboard (aggregated):**

- `GET /data/reporting-dashboard/{brand_id}` – Full dashboard for brand
- `GET /data/reporting-dashboard/client/{client_id}` – Full dashboard for client
- `GET /data/reporting-dashboard/slug/{slug}` – Dashboard by public slug
- `GET /data/reporting-dashboard/{brand_id}/scrunch` – Scrunch data for dashboard
- `GET /data/reporting-dashboard/slug/{slug}/scrunch` – Scrunch by slug
- `GET /data/reporting-dashboard/{brand_id}/diagnostics` – Diagnostics
- `GET /data/scrunch/query/{brand_id}` – Scrunch Query API for advanced visualizations

**KPI and chart configuration:**

- `GET/PUT /data/reporting-dashboard/{brand_id}/kpi-selections` – Brand KPI/chart choices
- `GET/PUT /data/reporting-dashboard/client/{client_id}/kpi-selections` – Client KPI/chart choices
- `GET /data/reporting-dashboard/client/{client_id}/dashboard-links/{link_id}/kpi-selections` – Per-link KPI/chart choices

**Brand management:**

- `PUT /data/brands/{brand_id}/ga4-property-id` – Set GA4 property for brand
- `POST/DELETE /data/brands/{brand_id}/agency-analytics-campaigns/{campaign_id}/link` – Link/unlink campaign
- `GET /data/brands/{brand_id}/agency-analytics-campaigns` – Linked campaigns
- `POST/DELETE /data/brands/{brand_id}/logo` – Upload/delete brand logo
- `PUT /data/brands/{brand_id}/theme` – Update brand theme (JSON)

**Clients:**

- `GET /data/clients` – List clients (filters, pagination)
- `GET /data/clients/{client_id}` – Single client
- `GET /data/clients/slug/{url_slug}` – Client by slug
- `DELETE /data/clients/{client_id}` – Delete client
- `PUT /data/clients/{client_id}/mappings` – GA4/Scrunch/campaign mappings
- `PUT /data/clients/{client_id}/theme` – Theme
- `PUT /data/clients/{client_id}/report-dates` – Report date range
- `POST/DELETE /data/clients/{client_id}/logo` – Logo upload/delete
- `GET/POST/DELETE /data/clients/{client_id}/campaigns` – Campaign links
- `GET /data/clients/{client_id}/keywords` – Keywords
- `GET /data/clients/{client_id}/keywords/rankings-over-time` – Keyword rankings over time
- `GET /data/clients/{client_id}/keywords/summary` – Keyword summary

**Dashboard links (shareable reports):**

- `GET /data/dashboard-links` – List links
- `GET /data/dashboard-links/{slug}` – Resolve by slug
- `GET /data/clients/{client_id}/dashboard-links` – Links for client
- `POST /data/clients/{client_id}/dashboard-links` – Create link
- `PUT /data/clients/{client_id}/dashboard-links/{link_id}` – Update link (incl. KPI/chart selections, executive summary)
- `DELETE /data/clients/{client_id}/dashboard-links/{link_id}` – Delete link
- `POST /data/clients/{client_id}/regenerate-shareable-link` – New link / extend validity
- `POST /data/dashboard-links/{slug}/track` – Track link open (IP, user agent, referer)
- `GET /data/clients/{client_id}/dashboard-links/{link_id}/kpi-selections` – KPI/chart for link
- `GET /data/clients/{client_id}/dashboard-links/{link_id}/metrics` – Metrics for link
- `GET /data/clients/{client_id}/dashboard-links/metrics` – Metrics for all client links

### 3.6 Database & Admin

- **Migrations:** `manage_migrations.py`; SQL migrations in `/migrations` (v1–v28+ and v2 subfolder)
- **Database API:** `POST /database/migrate/add-brand-id`, `POST /database/update-brand-ids`, `POST /database/verify`

### 3.7 Audit & Logging

- **Audit log:** Actions (login, logout, user_created, sync_*) with user, IP, user_agent, details, status
- **Endpoints:** `GET /audit/logs`, `GET /audit/stats`, `GET /audit/user-activity`

### 3.8 OpenAI Proxy (Optional)

- **Endpoints:** Chat completions, completions, embeddings, models, metrics/review, metrics/overview
- **Use:** Optional AI-driven insights or review features in the product

### 3.9 WebSocket

- **Service:** `websocket_manager.py` + `api/websocket.py`
- **Use:** Real-time updates (e.g. sync status) to the frontend

---

## 4. Frontend Features

### 4.1 Routing & Layout

- **Public:** `/login`, `/reporting/client/:slug` (public report by slug)
- **Protected (auth required):**
  - `/` – Dashboard (overview)
  - `/brands` – Brands list
  - `/brands/:id` – Brand analytics detail
  - `/clients` – Clients list
  - `/clients/:clientId/keywords` – Keywords dashboard for client
  - `/agency-analytics` – Agency Analytics view
  - `/sync` – Sync panel
  - `/data` – Data browser
  - `/reporting` – Internal reporting dashboard (brand/client selector)
  - `/dashboard-links` – Manage shareable dashboard links
  - `/audit-logs` – Audit log viewer
  - `/create-user` – User creation (admin)

Layout: sidebar navigation, auth-aware menu, theme (MUI).

### 4.2 Authentication & Context

- **AuthContext:** Login state, user, signin/signout, token refresh
- **ProtectedRoute:** Redirects unauthenticated users to `/login`
- **Token refresh:** Automatic refresh (e.g. `tokenRefresh.js`)

### 4.3 Dashboard (Overview)

- **Component:** `Dashboard.jsx`
- **Features:** Sync status, counts (brands, prompts, responses), high-level cards and links to Sync, Data, Reporting, etc.

### 4.4 Brands

- **BrandsList:** List brands, link to detail
- **BrandAnalyticsDetailWrapper / BrandAnalyticsDetail:** Brand-level analytics, GA4, Scrunch, prompts/responses
- **BrandManagement:** Create/edit brands (if exposed in routes)

### 4.5 Clients

- **ClientsList:** List clients, filters, link to client config and keywords
- **ClientManagement:** Client CRUD, mappings (GA4, Scrunch, campaigns), theme, report dates, logo
- **KeywordsDashboard:** Per-client keyword rankings, search volume, ranking over time, tables/charts

### 4.6 Sync Panel

- **Component:** `SyncPanel.jsx`
- **Features:** Buttons to trigger sync (Scrunch all, GA4, Agency Analytics), sync status, optional WebSocket updates

### 4.7 Data View

- **Component:** `DataView.jsx`
- **Features:** Browse brands, prompts, responses (filters, pagination)

### 4.8 Agency Analytics

- **Component:** `AgencyAnalytics.jsx`
- **Features:** Campaigns, rankings, keywords, brand–campaign linking

### 4.9 Reporting Dashboard (Internal)

- **Component:** `ReportingDashboard.jsx`
- **Features:**
  - Brand or client selector
  - Date range
  - KPI selector (which KPIs and sections to show)
  - Chart selector (which charts to show)
  - Sections: GA4, Scrunch AI, Brand Analytics, Advanced Query Visualizations, Performance/Keywords
  - Manual “Load data” for current selection
  - Uses: `ExecutiveSummary`, `GA4Section`, `BrandAnalyticsSection`, `ScrunchAISection`, `ScrunchVisualizations`, `ChartCard`, `KPIGrid`, `KPISelectorDialog`, etc.

### 4.10 Public Reporting Dashboard

- **Component:** `PublicReportingDashboard.jsx`
- **Route:** `/reporting/client/:slug`
- **Features:** Same reporting experience as internal dashboard but by shareable slug; no login; respects link’s KPI/chart/section and date range; optional tracking on open

### 4.11 Executive Summary

- **Component:** `ExecutiveSummary.jsx`
- **Features:** Narrative highlights, tags, expandable cards, date range, optional “performance metrics” summary; can be stored per dashboard link (`executive_summary` JSON).

### 4.12 GA4 Section

- **Component:** `GA4Section.jsx` (and optional `GA4SectionEnhanced.jsx`)
- **Features:** KPIs (users, sessions, new users, engaged sessions, bounce rate, avg session duration, engagement rate, conversions, revenue); traffic over time; top pages; traffic sources; geographic; devices; optional period-over-period change

### 4.13 Scrunch AI Section & Charts

- **Components:** `ScrunchAISection.jsx`, `PromptsAnalyticsTable.jsx`, `ScrunchVisualizations.jsx`
- **Features:**
  - Top prompts, Scrunch insights, brand analytics charts
  - Advanced Query Visualizations (from Scrunch Query API):
    - AI Platform Distribution
    - Competitive Presence Analysis
    - Brand Presence Trend Over Time
    - Position (% of total)
    - Brand Sentiment Analysis
  - Toggle visibility per chart (e.g. Position, Platform, Competitive, Trend, Sentiment)

### 4.14 Charts (Reusable)

- **PieChart, BarChart, LineChart, StackedBarChart** – Recharts-based; used in GA4 and Scrunch sections
- **ScrunchVisualizations** – Fetches Query API and renders Position, Platform, Sentiment, Citation source, Competitive presence, Time series
- **ChartCard** – Wrapper with title, loading, empty state

### 4.15 Dashboard Links Management

- **Component:** `DashboardLinksManagement.jsx`
- **Features:** List links per client, create/edit/delete links, set date range and KPI/chart/section per link, regenerate shareable URL, optional executive summary; view tracking (opens) if implemented

### 4.16 Audit Logs

- **Component:** `AuditLogs.jsx`
- **Features:** Table of audit events (user, action, time, status, details), filters

### 4.17 Create User

- **Component:** `CreateUser.jsx`
- **Features:** Admin form to create users (Supabase or local, depending on auth in use)

### 4.18 Theme & UI

- **Theme:** MUI theme (`theme.js`), optional client/brand theming for public report
- **Country names:** `countryNameMapper.js` for consistent geographic labels
- **Error handling:** `errorHandler.js`; toasts via `ToastContext`
- **Sync status:** `SyncStatusContext` (and optional `SyncStatusIndicator`)

---

## 5. KPI & Chart Configuration

### 5.1 KPI Selector Config (kpi_selector_config)

- **Google Analytics 4 / Website Analytics:**  
  KPIs: users, sessions, new_users, engaged_sessions, bounce_rate, avg_session_duration, engagement_rate, conversions, revenue.  
  Charts: users, sessions, new_users, top_performing_pages, traffic_sources_distribution, sessions_by_channel, geographic_distribution, sessions_vs_users_by_channel, top_countries, bounce_rate.

- **Agency Analytics / Keywords:**  
  KPIs: avg_google_ranking, avg_bing_ranking, avg_search_volume, top_10_visibility_percentage, improving/declining/stable keyword counts.  
  Charts: top_keywords_ranking, google_ranking, keyword_ranking_change_and_volume_table.

- **Scrunch AI / AI Visibility:**  
  Sections: top_performing_prompts, Scrunch AI insights, brand_analytics_charts.  
  Charts: Brand Analytics Charts, Advanced Query Visualization.  
  KPIs: total_citations, brand_presence_rate, brand_sentiment_score, top10_prompt_percentage, prompt_search_volume.

- **Summary / All performance metrics:** Combined list of GA4, Scrunch, and Agency KPIs for “all metrics” view.

### 5.2 Stored Selections

- **Brand KPI selections:** `brand_kpi_selections` – `selected_kpis`, `visible_sections`, `selected_charts`, `selected_performance_metrics_kpis`, `show_change_period`
- **Client KPI selections:** Same structure for client-level default
- **Dashboard link KPI selections:** `dashboard_link_kpi_selections` – per-link KPI/chart/section and executive summary visibility

---

## 6. Database Schema (Detailed)

### 6.1 Core Tables

#### `brands`
**Purpose:** Stores brand information from Scrunch AI

**Columns:**
- `id` (Integer, PK) - Brand ID from Scrunch API
- `name` (String) - Brand name
- `website` (String) - Brand website URL
- `ga4_property_id` (String, nullable) - Google Analytics 4 property ID
- `slug` (String, unique, indexed) - URL-friendly identifier (auto-generated UUID)
- `logo_url` (String, nullable) - URL to brand logo image
- `theme` (JSONB, nullable) - Brand theme configuration (colors, fonts, etc.)
- `created_at` (Timestamp) - Creation timestamp
- `version` (Integer, default: 1) - Optimistic locking version
- `last_modified_by` (String) - Email of user who last modified

**Indexes:** `id`, `slug`, `ga4_property_id`

**Relationships:**
- One-to-many: `prompts`, `responses`
- One-to-many: `brand_kpi_selections`
- Many-to-many: `agency_analytics_campaigns` (via `campaign_brands`)

#### `prompts`
**Purpose:** Stores AI prompts from Scrunch AI

**Columns:**
- `id` (Integer, PK) - Prompt ID from Scrunch API
- `brand_id` (Integer, FK → brands.id, indexed) - Brand this prompt belongs to
- `text` (Text) - Prompt text
- `stage` (String, indexed) - Funnel stage (Awareness, Evaluation, etc.)
- `persona_id` (Integer, indexed) - Persona ID
- `persona_name` (String) - Persona name
- `platforms` (Array[String]) - AI platforms this prompt is used on
- `tags` (Array[String]) - Tags
- `topics` (Array[String]) - Topics
- `created_at` (Timestamp) - Creation timestamp

**Indexes:** `id`, `brand_id`, `stage`, `persona_id`

**Relationships:**
- Many-to-one: `brands`
- One-to-many: `responses`

#### `responses`
**Purpose:** Stores AI-generated responses from Scrunch AI

**Columns:**
- `id` (Integer, PK) - Response ID from Scrunch API
- `brand_id` (Integer, FK → brands.id, indexed) - Brand this response is about
- `prompt_id` (Integer, FK → prompts.id, indexed) - Prompt that generated this response
- `prompt` (Text) - Prompt text (denormalized)
- `response_text` (Text) - AI-generated response text
- `platform` (String, indexed) - AI platform (ChatGPT, Claude, etc.)
- `country` (String) - Country code
- `persona_id` (Integer, indexed) - Persona ID
- `persona_name` (String) - Persona name
- `stage` (String, indexed) - Funnel stage
- `branded` (Boolean) - Whether response mentions brand
- `tags` (Array[String]) - Tags
- `key_topics` (Array[String]) - Key topics
- `brand_present` (Boolean) - Whether brand is present in response
- `brand_sentiment` (String) - Sentiment (positive, neutral, negative)
- `brand_position` (String) - Position (top, middle, bottom)
- `competitors_present` (Array[String]) - Competitor names mentioned
- `competitors` (JSONB) - Competitor objects with details
- `created_at` (Timestamp, indexed) - Creation timestamp
- `citations` (JSONB) - Citations array

**Indexes:** `id`, `brand_id`, `prompt_id`, `platform`, `persona_id`, `stage`, `created_at`
**Composite Index:** `(brand_id, created_at)` for date range queries

**Relationships:**
- Many-to-one: `brands`, `prompts`
- One-to-many: `citations`

#### `citations`
**Purpose:** Normalized citations from responses

**Columns:**
- `id` (Integer, PK, auto-increment)
- `response_id` (Integer, FK → responses.id, indexed, CASCADE delete)
- `url` (Text) - Citation URL
- `domain` (String, indexed) - Domain name
- `source_type` (String) - Source type
- `title` (String) - Citation title
- `snippet` (Text) - Citation snippet
- `created_at` (Timestamp) - Creation timestamp

**Indexes:** `id`, `response_id`, `domain`

**Relationships:**
- Many-to-one: `responses`

### 6.2 Authentication Tables

#### `users` (v2 Local Auth)
**Purpose:** User accounts for local authentication

**Columns:**
- `id` (Integer, PK, auto-increment)
- `email` (String(255), unique, indexed) - User email
- `password_hash` (String(255)) - Bcrypt hashed password
- `full_name` (String(255)) - User full name
- `created_at` (Timestamp) - Account creation timestamp
- `updated_at` (Timestamp) - Last update timestamp

**Indexes:** `id`, `email`

**Relationships:**
- One-to-many: `refresh_tokens`

#### `refresh_tokens`
**Purpose:** Refresh tokens for JWT authentication

**Columns:**
- `id` (Integer, PK, auto-increment)
- `user_id` (Integer, FK → users.id, indexed, CASCADE delete)
- `token` (String(255), unique, indexed) - Hashed refresh token
- `usage_count` (Integer, default: 0) - Number of times token used
- `max_usage` (Integer, default: 4) - Maximum allowed uses
- `expires_at` (Timestamp, indexed) - Token expiration
- `created_at` (Timestamp) - Token creation timestamp
- `last_used_at` (Timestamp) - Last usage timestamp

**Indexes:** `id`, `user_id`, `token`, `expires_at`

**Relationships:**
- Many-to-one: `users`

### 6.3 Client Management Tables

#### `clients`
**Purpose:** Client/company records (primary entity for reporting)

**Columns:**
- `id` (Integer, PK, auto-increment)
- `company_name` (Text) - Company name
- `company_id` (Integer) - External company ID
- `url` (Text) - Company website URL
- `email_addresses` (Array[String]) - Contact emails
- `phone_numbers` (Array[String]) - Contact phones
- `address`, `city`, `state`, `zip`, `country` - Address fields
- `timezone` (String) - Timezone
- `url_slug` (String, unique, indexed) - URL-friendly slug
- `ga4_property_id` (String, indexed) - GA4 property ID
- `scrunch_brand_id` (Integer, FK → brands.id, SET NULL) - Linked Scrunch brand
- `theme_color`, `secondary_color`, `font_family` - Theme colors
- `logo_url`, `favicon_url` - Branding assets
- `report_title` (String) - Custom report title
- `company_domain` (String, indexed) - Company domain
- `custom_css` (Text) - Custom CSS for public reports
- `footer_text`, `header_text` - Custom text
- `report_start_date`, `report_end_date` (Date) - Default report date range
- `is_active` (Boolean, default: true, indexed) - Active status
- `version` (Integer, default: 1) - Optimistic locking
- `created_at`, `updated_at` (Timestamp) - Timestamps
- `created_by`, `updated_by` (String) - User emails

**Indexes:** `id`, `url_slug`, `ga4_property_id`, `scrunch_brand_id`, `company_domain`, `is_active`

**Relationships:**
- Many-to-one: `brands` (via scrunch_brand_id)
- One-to-many: `client_campaigns`, `dashboard_links`, `client_kpi_selections`
- One-to-many: GA4 tables (via client_id)

#### `client_campaigns`
**Purpose:** Links clients to Agency Analytics campaigns

**Columns:**
- `id` (Integer, PK, auto-increment)
- `client_id` (Integer, FK → clients.id, indexed, CASCADE delete)
- `campaign_id` (BigInteger, indexed) - Agency Analytics campaign ID
- `is_primary` (Boolean, default: false) - Primary campaign flag
- `created_at`, `updated_at` (Timestamp)

**Indexes:** `id`, `client_id`, `campaign_id`

**Relationships:**
- Many-to-one: `clients`

### 6.4 GA4 Tables

All GA4 tables support both `brand_id` and `client_id` (for backward compatibility and flexibility).

#### `ga4_traffic_overview`
**Purpose:** Daily aggregated GA4 traffic metrics

**Columns:**
- `id` (Integer, PK, auto-increment)
- `brand_id` (Integer, FK → brands.id, nullable, indexed)
- `client_id` (Integer, FK → clients.id, nullable, indexed)
- `property_id` (String, indexed) - GA4 property ID
- `date` (Date, indexed) - Date of metrics
- `users`, `sessions`, `new_users`, `engaged_sessions` (Integer)
- `bounce_rate`, `average_session_duration`, `engagement_rate` (Numeric)
- `sessions_change`, `engaged_sessions_change`, `avg_session_duration_change`, `engagement_rate_change` (Numeric) - Period-over-period changes
- `revenue` (Numeric(15,2)) - Revenue
- `conversions` (Numeric(10,2)) - Conversion count
- `created_at`, `updated_at` (Timestamp)

**Indexes:** `id`, `brand_id`, `client_id`, `property_id`, `date`
**Unique Constraint:** `(property_id, date)` or `(client_id, property_id, date)`

#### `ga4_top_pages`
**Purpose:** Top performing pages per day

**Columns:**
- `id` (Integer, PK, auto-increment)
- `brand_id`, `client_id` (Integer, FK, nullable, indexed)
- `property_id` (String, indexed)
- `date` (Date, indexed)
- `page_path` (Text) - Page path
- `views`, `users` (Integer)
- `avg_session_duration` (Numeric)
- `rank` (Integer) - Ranking position

**Indexes:** `id`, `brand_id`, `client_id`, `property_id`, `date`

#### `ga4_traffic_sources`
**Purpose:** Traffic sources breakdown

**Columns:**
- `id` (Integer, PK, auto-increment)
- `brand_id`, `client_id` (Integer, FK, nullable, indexed)
- `property_id` (String, indexed)
- `date` (Date, indexed)
- `source` (Text) - Traffic source
- `sessions`, `users` (Integer)
- `bounce_rate` (Numeric)

**Indexes:** `id`, `brand_id`, `client_id`, `property_id`, `date`

#### `ga4_geographic`
**Purpose:** Geographic breakdown (country-level)

**Columns:**
- `id` (Integer, PK, auto-increment)
- `brand_id`, `client_id` (Integer, FK, nullable, indexed)
- `property_id` (String, indexed)
- `date` (Date, indexed)
- `country` (Text, indexed) - Country name
- `users`, `sessions` (Integer)

**Indexes:** `id`, `brand_id`, `client_id`, `property_id`, `date`, `country`

#### `ga4_devices`
**Purpose:** Device/platform breakdown

**Columns:**
- `id` (Integer, PK, auto-increment)
- `brand_id`, `client_id` (Integer, FK, nullable, indexed)
- `property_id` (String, indexed)
- `date` (Date, indexed)
- `device_category` (Text) - Desktop, Mobile, Tablet
- `operating_system` (Text) - OS name
- `users`, `sessions` (Integer)
- `bounce_rate` (Numeric)

**Indexes:** `id`, `brand_id`, `client_id`, `property_id`, `date`

#### `ga4_conversions`
**Purpose:** Conversion events

**Columns:**
- `id` (Integer, PK, auto-increment)
- `brand_id`, `client_id` (Integer, FK, nullable, indexed)
- `property_id` (String, indexed)
- `date` (Date, indexed)
- `event_name` (Text) - Conversion event name
- `event_count`, `users` (Integer)

**Indexes:** `id`, `brand_id`, `client_id`, `property_id`, `date`

#### `ga4_realtime`
**Purpose:** Realtime user snapshots

**Columns:**
- `id` (Integer, PK, auto-increment)
- `brand_id`, `client_id` (Integer, FK, nullable, indexed)
- `property_id` (String, indexed)
- `snapshot_time` (Timestamp, indexed) - Snapshot timestamp
- `total_active_users` (Integer)
- `active_pages` (JSONB) - Array of active pages
- `created_at` (Timestamp)

**Indexes:** `id`, `brand_id`, `client_id`, `property_id`, `snapshot_time`

#### `ga4_tokens`
**Purpose:** GA4 access token storage

**Columns:**
- `id` (Integer, PK, auto-increment)
- `access_token` (Text) - OAuth2 access token
- `refresh_token` (Text) - Refresh token
- `expires_at` (Timestamp, indexed) - Token expiration
- `created_at`, `updated_at` (Timestamp)

**Indexes:** `id`, `expires_at`

#### `ga4_property_details`
**Purpose:** Cached GA4 property metadata

**Columns:**
- `id` (Integer, PK, auto-increment)
- `brand_id`, `client_id` (Integer, FK, nullable, indexed)
- `property_id` (String, unique, indexed)
- `display_name` (Text) - Property display name
- `time_zone` (String) - Timezone
- `currency_code` (String) - Currency
- `created_at`, `updated_at` (Timestamp)

**Indexes:** `id`, `brand_id`, `client_id`, `property_id`

#### `ga4_kpi_snapshots`
**Purpose:** Pre-calculated KPI snapshots for performance

**Columns:**
- `id` (Integer, PK, auto-increment)
- `brand_id`, `client_id` (Integer, FK, nullable, indexed)
- `property_id` (String, indexed)
- `start_date`, `end_date` (Date, indexed) - Date range
- `kpis` (JSONB) - KPI values (users, sessions, etc.)
- `created_at`, `updated_at` (Timestamp)

**Indexes:** `id`, `brand_id`, `client_id`, `property_id`, `start_date`, `end_date`

### 6.5 Agency Analytics Tables

#### `agency_analytics_campaigns`
**Purpose:** SEO campaigns from Agency Analytics

**Columns:**
- `id` (BigInteger, PK) - Campaign ID from Agency Analytics
- `name` (Text) - Campaign name
- `url` (Text) - Campaign URL
- `client_id` (Integer) - Client ID
- `status` (String) - Campaign status
- `created_at`, `updated_at` (Timestamp)

**Indexes:** `id`, `client_id`

#### `agency_analytics_keywords`
**Purpose:** Keywords tracked in campaigns

**Columns:**
- `id` (BigInteger, PK) - Keyword ID
- `campaign_id` (BigInteger, FK → campaigns.id, indexed)
- `keyword` (Text, indexed) - Keyword text
- `search_volume` (Integer) - Monthly search volume
- `url` (Text) - URL being tracked
- `created_at`, `updated_at` (Timestamp)

**Indexes:** `id`, `campaign_id`, `keyword`

#### `agency_analytics_rankings`
**Purpose:** Ranking records

**Columns:**
- `id` (BigInteger, PK)
- `keyword_id` (BigInteger, FK → keywords.id, indexed)
- `date` (Date, indexed) - Ranking date
- `google_ranking` (Integer) - Google ranking position
- `bing_ranking` (Integer) - Bing ranking position
- `url` (Text) - URL ranking for
- `created_at`, `updated_at` (Timestamp)

**Indexes:** `id`, `keyword_id`, `date`

#### `agency_analytics_keyword_rankings`
**Purpose:** Historical keyword rankings (daily snapshots)

**Columns:**
- `id` (BigInteger, PK)
- `keyword_id` (BigInteger, FK → keywords.id, indexed)
- `date` (Date, indexed)
- `google_ranking`, `bing_ranking` (Integer)
- `search_volume` (Integer)
- `created_at`, `updated_at` (Timestamp)

**Indexes:** `id`, `keyword_id`, `date`

#### `agency_analytics_keyword_ranking_summaries`
**Purpose:** Aggregated keyword summaries

**Columns:**
- `id` (BigInteger, PK)
- `keyword_id` (BigInteger, FK → keywords.id, unique, indexed)
- `avg_google_ranking`, `avg_bing_ranking` (Numeric)
- `avg_search_volume` (Numeric)
- `top_10_visibility_percentage`, `top_3_visibility_percentage` (Numeric)
- `improving_count`, `declining_count`, `stable_count` (Integer)
- `created_at`, `updated_at` (Timestamp)

**Indexes:** `id`, `keyword_id`

### 6.6 Reporting Tables

#### `brand_kpi_selections`
**Purpose:** KPI/chart/section selections per brand

**Columns:**
- `id` (Integer, PK, auto-increment)
- `brand_id` (Integer, FK → brands.id, unique, indexed)
- `selected_kpis` (Array[String]) - Selected KPI IDs
- `visible_sections` (Array[String]) - Visible section IDs
- `selected_charts` (Array[String]) - Selected chart IDs
- `selected_performance_metrics_kpis` (Array[String]) - Performance metrics KPIs
- `show_change_period` (JSONB) - Period-over-period visibility per section
- `created_at`, `updated_at` (Timestamp)

**Indexes:** `id`, `brand_id`

**Relationships:**
- One-to-one: `brands`

#### `client_kpi_selections`
**Purpose:** KPI/chart/section selections per client (same structure as brand_kpi_selections)

**Columns:** Same as `brand_kpi_selections` but with `client_id` instead of `brand_id`

#### `dashboard_links`
**Purpose:** Shareable dashboard links

**Columns:**
- `id` (Integer, PK, auto-increment)
- `client_id` (Integer, FK → clients.id, indexed, CASCADE delete)
- `slug` (String, unique, indexed) - Unique slug (UUID)
- `start_date`, `end_date` (Date) - Report date range
- `enabled` (Boolean, default: true, indexed) - Link enabled status
- `expires_at` (Timestamp, indexed) - Link expiration
- `name` (String) - Link name/description
- `description` (Text) - Link description
- `executive_summary` (JSONB) - Executive summary highlights
- `created_at`, `updated_at` (Timestamp)

**Indexes:** `id`, `client_id`, `slug`, `enabled`, `expires_at`

**Relationships:**
- Many-to-one: `clients`
- One-to-one: `dashboard_link_kpi_selections`
- One-to-many: `dashboard_link_tracking`

#### `dashboard_link_kpi_selections`
**Purpose:** KPI/chart/section selections per dashboard link

**Columns:**
- `id` (Integer, PK, auto-increment)
- `dashboard_link_id` (Integer, FK → dashboard_links.id, unique, indexed, CASCADE delete)
- `selected_kpis` (Array[String])
- `visible_sections` (Array[String])
- `selected_charts` (Array[String])
- `selected_performance_metrics_kpis` (Array[String])
- `show_change_period` (JSONB)
- `created_at`, `updated_at` (Timestamp)

**Indexes:** `id`, `dashboard_link_id`

**Relationships:**
- One-to-one: `dashboard_links`

#### `dashboard_link_tracking`
**Purpose:** Track dashboard link opens

**Columns:**
- `id` (Integer, PK, auto-increment)
- `dashboard_link_id` (Integer, FK → dashboard_links.id, indexed, CASCADE delete)
- `opened_at` (Timestamp, indexed) - Open timestamp
- `ip_address` (String) - IP address (stored as string for INET compatibility)
- `user_agent` (Text) - User agent string
- `referer` (Text) - Referer URL
- `created_at` (Timestamp)

**Indexes:** `id`, `dashboard_link_id`, `opened_at`

**Relationships:**
- Many-to-one: `dashboard_links`

### 6.7 Audit & Sync Tables

#### `audit_logs`
**Purpose:** Audit trail for user actions and syncs

**Columns:**
- `id` (Integer, PK, auto-increment)
- `action` (Enum, indexed) - Action type (LOGIN, LOGOUT, SYNC_BRANDS, etc.)
- `user_id` (String, indexed) - Supabase user ID (if using Supabase auth)
- `user_email` (String, indexed) - User email
- `ip_address` (String) - IP address
- `user_agent` (String) - User agent
- `details` (JSONB) - Additional context (brand_id, sync counts, etc.)
- `status` (String, indexed) - Status (success, error, partial)
- `error_message` (Text) - Error message if failed
- `created_at` (Timestamp, indexed) - Timestamp

**Indexes:** `id`, `action`, `user_id`, `user_email`, `status`, `created_at`

**Action Types:**
- LOGIN, LOGOUT
- USER_CREATED
- SYNC_BRANDS, SYNC_PROMPTS, SYNC_RESPONSES, SYNC_GA4, SYNC_AGENCY_ANALYTICS, SYNC_ALL

#### `sync_jobs`
**Purpose:** Background sync job tracking

**Columns:**
- `id` (Integer, PK, auto-increment)
- `job_type` (String) - Sync type (brands, prompts, responses, ga4, agency_analytics, all)
- `status` (String, indexed) - Status (running, completed, failed, cancelled)
- `started_at` (Timestamp, indexed) - Start time
- `completed_at` (Timestamp) - Completion time
- `error_message` (Text) - Error if failed
- `details` (JSONB) - Job details (counts, results, etc.)
- `created_at`, `updated_at` (Timestamp)

**Indexes:** `id`, `status`, `started_at`

### 6.8 Migration History

**Migration Files (in `/migrations`):**
- `v1__database_schema.sql` - Initial schema
- `v2__ga4_tables_setup.sql` - GA4 tables
- `v3__ga4_token_table.sql` - GA4 token storage
- `v4__agency_analytics_tables_setup.sql` - Agency Analytics tables
- `v5__add_brand_slug_migration.sql` - Brand slugs
- `v6__add_brand_slug_trigger.sql` - Auto-generate slugs
- `v7__create_audit_logs_table.sql` - Audit logging
- `v8__create_sync_jobs_table.sql` - Sync jobs
- `v9__create_brand_kpi_selections_table.sql` - KPI selections
- `v10__add_visible_sections_to_brand_kpi_selections.sql` - Section visibility
- `v11__add_brand_logo_and_theme.sql` - Branding
- `v12__update_brand_slug_trigger_to_uuid.sql` - UUID slugs
- `v13__ga4_kpi_snapshots.sql` - KPI snapshots
- `v14__ga4_additional_tables.sql` - Additional GA4 tables
- `v15__create_clients_table.sql` - Clients table
- `v16__add_responses_composite_index.sql` - Performance index
- `v17__add_version_tracking.sql` - Optimistic locking
- `v18__add_client_id_to_ga4_tables.sql` - Client support in GA4
- `v19__add_selected_charts_to_brand_kpi_selections.sql` - Chart selections
- `v20__add_is_active_to_clients.sql` - Client active status
- `v21__add_client_id_to_brand_kpi_selections.sql` - Client KPI selections
- `v22__add_report_dates_to_clients.sql` - Report date ranges
- `v23__create_dashboard_links.sql` - Dashboard links
- `v24__create_dashboard_link_tracking.sql` - Link tracking
- `v25__create_dashboard_link_kpi_selections.sql` - Link KPI selections
- `v26__add_performance_metrics_kpis.sql` - Performance metrics
- `v27__add_executive_summary_to_dashboard_links.sql` - Executive summary
- `v28__add_show_change_period_to_kpi_selections.sql` - Period-over-period visibility

**v2 Subfolder (Additional Migrations):**
- `001_users_and_refresh_tokens.sql` - Local auth tables
- `002_update_agency_analytics_integer_to_bigint.sql` - BigInt support
- `003_drop_keyword_id_date_unique_constraint.sql` - Constraint removal
- `004_add_performance_indexes.sql` - Performance indexes
- `005_add_is_active_to_clients.sql` - Client active flag

---

## 7. Automation & DevOps

### 7.1 Daily Sync

- **Script:** `daily_sync_job.py`
- **Cron:** e.g. 11:30 PM IST (configurable via `setup_daily_sync_linux.sh`, `setup_daily_sync_windows.ps1`, `setup_cron_auto.sh`)
- **Typical flow:** GA4 token refresh, Scrunch sync (brands, prompts, responses), GA4 sync, Agency Analytics sync (all or per campaign)

### 7.2 Docker

- **Compose:** `docker-compose.yml` – backend, frontend, DB (if local), nginx
- **Images:** `Dockerfile.backend`, `Dockerfile.frontend`
- **Cron in container:** `check_and_setup_cron_docker.sh`, `validate_cron_docker.sh`
- **Entrypoint:** `docker-entrypoint.sh`

### 7.3 Backups

- **Scripts:** `scripts/weekly_backup.sh`, `scripts/create_database_dump.sh`, `scripts/restore_database_dump.sh`, etc.
- **Location:** e.g. `dumps/` (weekly backup files)

### 7.4 SSL / DNS

- **Scripts:** `setup_ssl.sh`, `check_dns_and_setup_ssl.sh`, `wait_for_dns_and_setup_ssl.sh`
- **Nginx:** `nginx.conf` for reverse proxy and TLS

---

## 8. User Workflows

### 8.1 Initial Setup Workflow

**Step 1: Configure Environment**
```bash
# Set environment variables
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_KEY="your-anon-key"
export SCRUNCH_API_TOKEN="your-scrunch-token"
export GA4_CREDENTIALS_PATH="service-key.json"
```

**Step 2: Run Database Migrations**
```bash
# Apply all migrations
python manage_migrations.py
# Or manually run SQL files from migrations/ folder
```

**Step 3: Initial Data Sync**
```bash
# Sync all Scrunch data (brands, prompts, responses)
POST /api/v1/sync/all?sync_mode=complete

# Sync GA4 data for configured brands/clients
POST /api/v1/sync/ga4?sync_mode=complete

# Sync Agency Analytics data
POST /api/v1/sync/agency-analytics?sync_mode=complete&auto_match_brands=true
```

**Step 4: Configure Client Mappings**
- Set GA4 property IDs for clients: `PUT /api/v1/data/clients/{client_id}/mappings`
- Link Scrunch brand IDs: `PUT /api/v1/data/clients/{client_id}/mappings`
- Link Agency Analytics campaigns: `POST /api/v1/data/clients/{client_id}/campaigns/{campaign_id}/link`

**Step 5: Set Up Daily Sync**
```bash
# Linux/Mac
./setup_daily_sync_linux.sh

# Windows
.\setup_daily_sync_windows.ps1

# Docker
./check_and_setup_cron_docker.sh
```

### 8.2 Creating a Shareable Dashboard Link Workflow

**Step 1: Navigate to Dashboard Links Management**
- Go to `/dashboard-links` in the frontend
- Select a client from the dropdown

**Step 2: Create New Link**
- Click "Create New Link"
- Set date range (start_date, end_date)
- Configure KPI selections (which KPIs to show)
- Configure chart selections (which charts to show)
- Configure visible sections (GA4, Scrunch AI, etc.)
- Optionally add executive summary (JSON)

**Step 3: Generate Shareable URL**
- System generates unique slug (UUID-based)
- Link format: `https://yourdomain.com/reporting/client/{slug}`
- Link expires after 48 hours (configurable)

**Step 4: Share Link**
- Copy the generated URL
- Share with client (no login required)
- Client opens link and sees branded dashboard

**Step 5: Track Usage (Optional)**
- System tracks link opens: `POST /api/v1/data/dashboard-links/{slug}/track`
- Records: IP address, user agent, referer, timestamp
- View metrics: `GET /api/v1/data/clients/{client_id}/dashboard-links/{link_id}/metrics`

### 8.3 Daily Sync Workflow (Automated)

**Cron Schedule:** Daily at 11:30 PM IST (configurable)

**Execution Flow:**
1. **GA4 Token Refresh**
   - Check if token expired
   - Generate new access token if needed
   - Store in `ga4_tokens` table

2. **Scrunch AI Sync**
   - Sync all brands (upsert)
   - Sync prompts for all brands
   - Sync responses for date range (last 30 days by default)

3. **GA4 Sync**
   - For each client with GA4 property ID:
     - Sync traffic overview (last 30 days)
     - Sync top pages
     - Sync traffic sources
     - Sync geographic data
     - Sync devices
     - Sync conversions
     - Sync realtime snapshot

4. **Agency Analytics Sync**
   - Sync all active campaigns
   - Sync rankings
   - Sync keywords
   - Sync keyword rankings (last 30 days)
   - Generate keyword ranking summaries

5. **Create Sync Job Record**
   - Record sync job in `sync_jobs` table
   - Status: "running" → "completed" or "failed"
   - Store error messages if any

**Monitoring:**
- Check sync status: `GET /api/v1/sync/status`
- View sync jobs: `GET /api/v1/sync/jobs`
- Check audit logs: `GET /api/v1/audit/logs?action=sync_*`

### 8.4 Reporting Dashboard Workflow (Internal)

**Step 1: Navigate to Reporting Dashboard**
- Go to `/reporting` in frontend
- Select brand or client from dropdown

**Step 2: Configure Date Range**
- Select preset (Last 7/30/90 days, etc.) or custom range
- Date format: YYYY-MM-DD

**Step 3: Configure KPI Selections**
- Click "Settings" or "KPI Selector" button
- Select which KPIs to display:
  - GA4 KPIs (users, sessions, conversions, etc.)
  - Scrunch AI KPIs (brand presence rate, sentiment, citations, etc.)
  - Agency Analytics KPIs (avg ranking, visibility, etc.)
- Save selections (stored per brand/client)

**Step 4: Configure Chart Selections**
- Select which charts to display:
  - GA4 charts (traffic over time, top pages, sources, geographic, devices)
  - Scrunch charts (platform distribution, competitive presence, sentiment, etc.)
  - Agency Analytics charts (keyword rankings, ranking trends)
- Save selections

**Step 5: Configure Visible Sections**
- Toggle sections on/off:
  - GA4 Section
  - Scrunch AI Section
  - Brand Analytics Section
  - Advanced Query Visualizations
  - Performance Metrics / Keywords Section

**Step 6: Load Data**
- Click "Load Data" button
- System fetches from `/api/v1/data/reporting-dashboard/{brand_id}` or `/api/v1/data/reporting-dashboard/client/{client_id}`
- Displays KPIs, charts, executive summary

**Step 7: View Dashboard**
- Executive Summary (if configured)
- GA4 Section with KPIs and charts
- Scrunch AI Section with insights and charts
- Brand Analytics charts
- Keywords section (if Agency Analytics linked)

### 8.5 Public Dashboard Workflow (Client View)

**Step 1: Client Receives Link**
- Client receives shareable URL: `https://yourdomain.com/reporting/client/{slug}`
- Link is valid for 48 hours (configurable)

**Step 2: Client Opens Link**
- No login required (public route)
- System resolves slug: `GET /api/v1/data/dashboard-links/{slug}`
- Gets link configuration (date range, KPI selections, chart selections, visible sections)

**Step 3: Track Link Open (Optional)**
- System records: `POST /api/v1/data/dashboard-links/{slug}/track`
- Records: IP address, user agent, referer, timestamp

**Step 4: Load Dashboard Data**
- System fetches: `GET /api/v1/data/reporting-dashboard/slug/{slug}`
- Uses link's configured date range and KPI/chart selections
- Applies client branding (logo, theme colors, custom CSS if configured)

**Step 5: Display Dashboard**
- Shows executive summary (if configured for this link)
- Shows selected KPIs and charts
- Shows only visible sections
- Branded with client logo and theme

**Step 6: Link Expiration**
- After 48 hours, link expires
- Internal user can regenerate link to extend validity
- New link gets new slug (old link no longer works)

---

## 9. API Examples

### 9.1 Authentication Examples

#### Sign Up (v2 Local Auth)
```bash
POST /api/v1/auth/v2/signup
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123",
  "full_name": "John Doe"
}

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "refresh_token_hash_here",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe"
  }
}
```

#### Sign In
```bash
POST /api/v1/auth/v2/signin
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}

Response: (same as signup)
```

#### Refresh Token
```bash
POST /api/v1/auth/v2/refresh
Content-Type: application/json

{
  "refresh_token": "refresh_token_hash_here"
}

Response: (new access_token and refresh_token)
```

### 9.2 Reporting Dashboard API Example

#### Get Dashboard Data for Brand
```bash
GET /api/v1/data/reporting-dashboard/123?start_date=2025-01-01&end_date=2025-01-31
Headers: Authorization: Bearer <token>

Response:
{
  "brand_id": 123,
  "brand_name": "Brand A",
  "date_range": {
    "start_date": "2025-01-01",
    "end_date": "2025-01-31"
  },
  "kpis": {
    "users": 15000,
    "sessions": 20000,
    "new_users": 5000,
    "engaged_sessions": 12000,
    "bounce_rate": 45.5,
    "avg_session_duration": 180,
    "engagement_rate": 60.0,
    "conversions": 150,
    "revenue": 50000.00,
    "total_citations": 5000,
    "brand_presence_rate": 75.5,
    "brand_sentiment_score": 0.65,
    "top10_prompt_percentage": 30.0,
    "prompt_search_volume": 10000,
    "avg_google_ranking": 15.5,
    "avg_search_volume": 5000,
    "top_10_visibility_percentage": 40.0
  },
  "chart_data": {
    "ga4_traffic_overview": [...],
    "ga4_top_pages": [...],
    "ga4_traffic_sources": [...],
    "ga4_geographic": [...],
    "ga4_devices": [...],
    "scrunch_platform_distribution": [...],
    "scrunch_competitive_presence": [...],
    "scrunch_brand_presence_trend": [...],
    "scrunch_sentiment_distribution": [...],
    "keyword_rankings_over_time": [...]
  },
  "executive_summary": {
    "highlights": [
      {
        "title": "Traffic Growth",
        "content": "Website traffic increased by 25% compared to last month...",
        "tag": "Success",
        "tagColor": "#4caf50"
      }
    ]
  }
}
```

### 9.3 KPI Selections API Example

#### Get KPI Selections for Brand
```bash
GET /api/v1/data/reporting-dashboard/123/kpi-selections
Headers: Authorization: Bearer <token>

Response:
{
  "brand_id": 123,
  "selected_kpis": [
    "users",
    "sessions",
    "conversions",
    "brand_presence_rate",
    "brand_sentiment_score",
    "avg_google_ranking"
  ],
  "visible_sections": [
    "ga4",
    "scrunch_ai",
    "brand_analytics",
    "advanced_analytics",
    "keywords"
  ],
  "selected_charts": [
    "ga4_traffic_overview",
    "ga4_top_pages",
    "ga4_traffic_sources",
    "scrunch_platform_distribution",
    "scrunch_competitive_presence",
    "keyword_rankings_over_time"
  ],
  "selected_performance_metrics_kpis": [
    "users",
    "sessions",
    "conversions",
    "brand_presence_rate"
  ],
  "show_change_period": {
    "ga4": true,
    "agency_analytics": true,
    "scrunch_ai": false
  }
}
```

#### Update KPI Selections
```bash
PUT /api/v1/data/reporting-dashboard/123/kpi-selections
Headers: Authorization: Bearer <token>
Content-Type: application/json

{
  "selected_kpis": ["users", "sessions", "conversions"],
  "visible_sections": ["ga4", "scrunch_ai"],
  "selected_charts": ["ga4_traffic_overview", "scrunch_platform_distribution"],
  "show_change_period": {
    "ga4": true,
    "scrunch_ai": false
  }
}

Response:
{
  "status": "success",
  "message": "KPI selections updated",
  "kpi_selections": {...}
}
```

### 9.4 Dashboard Links API Example

#### Create Dashboard Link
```bash
POST /api/v1/data/clients/123/dashboard-links
Headers: Authorization: Bearer <token>
Content-Type: application/json

{
  "start_date": "2025-01-01",
  "end_date": "2025-01-31",
  "name": "January 2025 Report",
  "description": "Monthly report for January",
  "enabled": true,
  "expires_at": "2025-02-02T23:59:59Z",
  "kpi_selections": {
    "selected_kpis": ["users", "sessions", "conversions"],
    "visible_sections": ["ga4", "scrunch_ai"],
    "selected_charts": ["ga4_traffic_overview"]
  },
  "executive_summary": {
    "highlights": [
      {
        "title": "Traffic Growth",
        "content": "Traffic increased by 25%...",
        "tag": "Success",
        "tagColor": "#4caf50"
      }
    ]
  }
}

Response:
{
  "id": 456,
  "client_id": 123,
  "slug": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "start_date": "2025-01-01",
  "end_date": "2025-01-31",
  "enabled": true,
  "expires_at": "2025-02-02T23:59:59Z",
  "url": "https://yourdomain.com/reporting/client/a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "created_at": "2025-01-28T10:00:00Z"
}
```

#### Track Link Open
```bash
POST /api/v1/data/dashboard-links/{slug}/track
Content-Type: application/json

{
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "referer": "https://example.com"
}

Response:
{
  "status": "success",
  "tracking_id": 789
}
```

---

## 10. Security & Performance

### 10.1 Security Features

**Authentication:**
- JWT tokens with expiration (access tokens: 1 hour, refresh tokens: 30 days)
- Refresh token rotation (new token on each refresh)
- Refresh token usage limits (max 4 uses per token)
- Password hashing using bcrypt (work factor: 12)
- HTTPS enforced in production (Nginx SSL termination)

**Authorization:**
- Protected routes require valid JWT token
- Token validation on every request
- User context available in all protected endpoints
- Audit logging for all sensitive operations

**API Security:**
- CORS configured (allowed origins in config)
- Rate limiting (handled by Nginx/reverse proxy)
- Input validation (Pydantic models for request validation)
- SQL injection prevention (parameterized queries, SQLAlchemy ORM)
- XSS prevention (React escapes by default, no innerHTML)

**Data Security:**
- Environment variables for secrets (never committed)
- Service account keys stored securely (not in Git)
- Database credentials in environment variables
- Audit logging for data access

**Public Links:**
- Unique slugs (UUID-based, unguessable)
- Expiration dates (48 hours default)
- Optional tracking (IP, user agent logged)
- No authentication required (by design for client sharing)

### 10.2 Performance Optimizations

**Database:**
- Indexes on frequently queried columns (brand_id, client_id, date, created_at)
- Composite indexes for common query patterns
- Connection pooling (SQLAlchemy pool)
- Query optimization (select only needed columns, avoid N+1 queries)

**API:**
- Parallel API calls where possible (Promise.all in frontend, asyncio.gather in backend)
- Caching for GA4 property details (stored in database)
- KPI snapshots for 30-day periods (pre-calculated, stored in `ga4_kpi_snapshots`)
- Pagination for large datasets (limit/offset)

**Frontend:**
- React Query for caching and automatic refetching
- Code splitting (Vite automatic code splitting)
- Lazy loading of components where appropriate
- Memoization (useMemo, useCallback) for expensive calculations
- Virtual scrolling for large lists (if implemented)

**Sync Performance:**
- Background jobs (don't block API requests)
- Batch operations (bulk upserts)
- Incremental syncs ("new" mode for faster updates)
- Rate limiting handling (exponential backoff)

**Caching:**
- GA4 property details cached in database
- KPI snapshots for common date ranges
- Frontend query caching (React Query)

---

## 8. Documentation (in repo)

- **API_DOCUMENTATION.md** – Full API reference and associated views
- **KPI_DOCUMENTATION.md** – KPI definitions, source, and accuracy
- **KPI_TECHNICAL_CALCULATIONS.md** – How KPIs are computed
- **USER_GUIDE.md** – Sync modes, reporting, shareable links, best practices
- **DATA_FLOW_EXPLANATION.md** – Scrunch, GA4, Agency Analytics flow
- **AUDIT_LOGGING.md** – Audit events and usage
- **CHECK_SYNC_JOBS.md** – Sync job monitoring
- **DOCKER_CRON_SETUP.md** – Cron in Docker
- **ERROR_HANDLING.md** – Error handling approach
- **SLUG_GENERATION_EXPLANATION.md** – Brand/client/dashboard link slugs

---

## 9. Summary: What We Have Built

| Area | What’s included |
|------|------------------|
| **Data ingestion** | Scrunch AI, GA4, Agency Analytics sync with filters and job tracking |
| **Storage** | PostgreSQL/Supabase with brands, prompts, responses, GA4, Agency Analytics, clients, links, KPI selections |
| **Auth** | Supabase auth + local JWT auth, refresh tokens, audit log |
| **APIs** | REST for sync, data, reporting, clients, dashboard links, KPIs, charts, tracking |
| **Reporting** | Single aggregated reporting endpoint for brand or client; KPI/chart/section selection per brand, client, and link |
| **Public reports** | Shareable links by slug, 48h (or configurable) validity, optional tracking, client theming |
| **Executive summary** | Configurable narrative highlights stored per dashboard link |
| **GA4** | Full GA4 metrics and charts; daily token; geographic/daily breakdown |
| **Scrunch** | Prompts, responses, Query API visualizations (position, platform, sentiment, competitive, trend) |
| **Keywords** | Agency Analytics keywords, rankings over time, summaries |
| **Frontend** | Dashboard, brands, clients, sync, data browser, agency analytics, internal + public reporting, dashboard link management, audit log |
| **Automation** | Daily cron sync, Docker, backups, SSL/DNS scripts |

This file is the single place that describes **what the project does** and **what has been implemented** end to end.

---

## 12. Document Summary

This comprehensive documentation covers:

✅ **Complete API Reference** - All endpoints with request/response examples  
✅ **Detailed Data Sources** - Scrunch AI, GA4, Agency Analytics integration details  
✅ **Frontend Components** - All React components with features and usage  
✅ **Database Schema** - Complete table structures with relationships and indexes  
✅ **User Workflows** - Step-by-step guides for common operations  
✅ **Security & Performance** - Security features and optimization strategies  
✅ **Automation** - Daily sync, Docker, backups, SSL setup  
✅ **KPI Configuration** - All available KPIs and charts  
✅ **API Examples** - Real request/response examples  

**Total Documentation:** ~1,900 lines covering all aspects of the project.

**Related Documentation Files:**
- `COMMIT_ANALYSIS_NOV_2025_TO_JAN_2026.md` - Git commit history analysis
- `docs/API_DOCUMENTATION.md` - Detailed API reference
- `docs/KPI_DOCUMENTATION.md` - KPI definitions and calculations
- `docs/USER_GUIDE.md` - User guide for sync and reporting
- `docs/DATA_FLOW_EXPLANATION.md` - Data flow architecture
- `README.md` - Quick start guide

This document serves as the **master reference** for understanding the entire project architecture, features, and implementation details.

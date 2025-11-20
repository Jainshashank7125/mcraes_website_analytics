# Data Flow Architecture: Scrunch, Google Analytics & Agency Analytics

## Overview
This document explains how data from **Scrunch AI**, **Google Analytics 4 (GA4)**, and **Agency Analytics** is fetched, stored, and displayed in the reporting dashboard.

---

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Scrunch AI API │     │   GA4 API       │     │ Agency Analytics│
│                 │     │                 │     │      API        │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         │  Sync Endpoints       │  Sync Endpoints       │  Sync Endpoints
         │  (POST /sync/*)       │  (POST /sync/ga4)     │  (POST /sync/agency-analytics)
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Supabase Database                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │   brands     │  │ ga4_traffic  │  │ agency_analytics_*   │  │
│  │   prompts    │  │ ga4_top_pages│  │ campaigns            │  │
│  │   responses  │  │ ga4_sources  │  │ keywords             │  │
│  └──────────────┘  └──────────────┘  │ rankings             │  │
│                                      └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
         │                       │                       │
         │  Data Endpoints       │  Data Endpoints       │  Data Endpoints
         │  (GET /data/*)        │  (GET /data/ga4/*)   │  (GET /data/agency-analytics/*)
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│         Reporting Dashboard Endpoint                            │
│         (GET /data/reporting-dashboard/{brand_id})              │
│                                                                 │
│  Aggregates KPIs from all three sources                         │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend Dashboard                            │
│  Displays KPIs, Charts, and Visualizations                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. SCRUNCH AI Data Flow

### 1.1 Data Sync (Fetching from Scrunch API)

**Location**: `app/api/sync.py` & `app/services/scrunch_client.py`

#### Step 1: Sync Brands
```python
# Endpoint: POST /api/v1/sync/brands
# File: app/api/sync.py:16-33

client = ScrunchAPIClient()
brands = await client.get_brands()  # Fetches from Scrunch API
supabase.upsert_brands(brands)     # Stores in Supabase
```

**What happens**:
- Makes GET request to `https://api.scrunchai.com/v1/brands`
- Uses Bearer token authentication
- Stores brand metadata (id, name, website, etc.) in `brands` table

#### Step 2: Sync Prompts
```python
# Endpoint: POST /api/v1/sync/prompts
# File: app/api/sync.py:35-93

prompts = await client.get_all_prompts_paginated(brand_id)
supabase.upsert_prompts(prompts, brand_id)
```

**What happens**:
- Fetches prompts for each brand from `/v1/{brand_id}/prompts`
- Handles pagination (1000 records per page)
- Stores prompts with metadata: `id`, `text`, `stage`, `persona_id`, `brand_id`

#### Step 3: Sync Responses
```python
# Endpoint: POST /api/v1/sync/responses
# File: app/api/sync.py:95-159

responses = await client.get_all_responses_paginated(brand_id)
supabase.upsert_responses(responses, brand_id)
```

**What happens**:
- Fetches AI responses from `/v1/{brand_id}/responses`
- Includes filters: `platform`, `prompt_id`, `start_date`, `end_date`
- Stores response data: `brand_present`, `citations`, `competitors_present`, `platform`, etc.

### 1.2 Data Retrieval (For Reports)

**Location**: `app/api/data.py`

```python
# Endpoint: GET /api/v1/data/prompts?brand_id={id}
# Endpoint: GET /api/v1/data/responses?brand_id={id}

# Queries Supabase directly
prompts = supabase.client.table("prompts").select("*").eq("brand_id", brand_id)
responses = supabase.client.table("responses").select("*").eq("brand_id", brand_id)
```

### 1.3 KPI Calculation (In Reporting Dashboard)

**Location**: `app/api/data.py:956-1032`

```python
# Get prompts and responses from database
prompts = supabase.client.table("prompts").select("*").eq("brand_id", brand_id)
responses = supabase.client.table("responses").select("*").eq("brand_id", brand_id)

# Calculate Visibility on AI Platform
presence_count = sum(1 for r in responses if r.get("brand_present") == True)
visibility = (presence_count / len(responses) * 100)

# Calculate Top 10 Prompt Percentage
prompt_counts = {}  # Count responses per prompt
sorted_prompts = sorted(prompt_counts.items(), reverse=True)[:10]
top10_percentage = (top10_count / len(responses) * 100)

# Calculate Total Citations
total_citations = sum(len(r.get("citations", [])) for r in responses)
```

**KPIs Generated**:
- `visibility_ai_platform`: % of responses where brand is mentioned
- `prompt_search_volume`: Total number of responses
- `top10_prompt_percentage`: % of responses from top 10 prompts
- `total_citations`: Total citation count across all responses

---

## 2. GOOGLE ANALYTICS 4 (GA4) Data Flow

### 2.1 Data Sync (Fetching from GA4 API)

**Location**: `app/api/sync.py:457-655` & `app/services/ga4_client.py`

#### Authentication
```python
# Uses Google Service Account or Access Token
credentials = service_account.Credentials.from_service_account_file(
    settings.GA4_CREDENTIALS_PATH,
    scopes=["https://www.googleapis.com/auth/analytics.readonly"]
)
client = BetaAnalyticsDataClient(credentials=credentials)
```

#### Step 1: Sync GA4 Data
```python
# Endpoint: POST /api/v1/sync/ga4?brand_id={id}&start_date=...&end_date=...
# File: app/api/sync.py:457-655

# For each brand with ga4_property_id configured:
property_id = brand["ga4_property_id"]

# Fetch various GA4 metrics
traffic_overview = await ga4_client.get_traffic_overview(property_id, start_date, end_date)
top_pages = await ga4_client.get_top_pages(property_id, start_date, end_date)
traffic_sources = await ga4_client.get_traffic_sources(property_id, start_date, end_date)
geographic = await ga4_client.get_geographic_breakdown(property_id, start_date, end_date)
devices = await ga4_client.get_device_breakdown(property_id, start_date, end_date)
conversions = await ga4_client.get_conversions(property_id, start_date, end_date)
realtime = await ga4_client.get_realtime_snapshot(property_id)

# Store in Supabase
supabase.upsert_ga4_traffic_overview(brand_id, property_id, end_date, traffic_overview)
supabase.upsert_ga4_top_pages(brand_id, property_id, end_date, top_pages)
# ... etc
```

**What happens**:
- Uses GA4 Data API (`BetaAnalyticsDataClient`)
- Makes `run_report` requests with dimensions and metrics
- Calculates month-over-month changes by comparing with previous period
- Stores aggregated data in Supabase tables:
  - `ga4_traffic_overview`
  - `ga4_top_pages`
  - `ga4_traffic_sources`
  - `ga4_geographic`
  - `ga4_devices`
  - `ga4_conversions`
  - `ga4_realtime`

#### Example: Traffic Overview Request
```python
# File: app/services/ga4_client.py:150-240

request = RunReportRequest(
    property=f"properties/{property_id}",
    date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
    metrics=[
        Metric(name="sessions"),
        Metric(name="engagedSessions"),
        Metric(name="averageSessionDuration"),
        Metric(name="engagementRate"),
    ],
)

response = client.run_report(request)
# Processes response and calculates changes vs previous period
```

### 2.2 Data Retrieval (For Reports)

**Location**: `app/api/data.py:307-407`

```python
# Endpoint: GET /api/v1/data/ga4/brand/{brand_id}
# Can fetch from database OR directly from GA4 API

# Option 1: From Database (if synced)
traffic_overview = supabase.client.table("ga4_traffic_overview")...

# Option 2: Direct from GA4 API (real-time)
traffic_overview = await ga4_client.get_traffic_overview(property_id, start_date, end_date)
```

### 2.3 KPI Calculation (In Reporting Dashboard)

**Location**: `app/api/data.py:829-870`

```python
# Get brand's GA4 property ID
property_id = brand["ga4_property_id"]

# Fetch traffic overview (from database or API)
traffic_overview = await ga4_client.get_traffic_overview(property_id, start_date, end_date)

# Extract KPIs
ga4_kpis = {
    "total_sessions": {
        "value": traffic_overview.get("sessions", 0),
        "change": traffic_overview.get("sessionsChange", 0),  # % change vs last month
        "source": "GA4",
        "label": "Total Sessions"
    },
    "engaged_sessions": {
        "value": traffic_overview.get("engagedSessions", 0),
        "change": traffic_overview.get("engagedSessionsChange", 0),
        ...
    },
    "avg_session_duration": {
        "value": traffic_overview.get("averageSessionDuration", 0),  # in seconds
        "change": traffic_overview.get("avgSessionDurationChange", 0),
        "format": "duration"  # Will be formatted as MM:SS
    },
    "engagement_rate": {
        "value": traffic_overview.get("engagementRate", 0) * 100,  # Convert to percentage
        "change": traffic_overview.get("engagementRateChange", 0),
        "format": "percentage"
    }
}
```

**KPIs Generated**:
- `total_sessions`: Total website sessions
- `engaged_sessions`: Sessions with engagement
- `avg_session_duration`: Average session length (formatted as MM:SS)
- `engagement_rate`: % of engaged sessions (formatted as percentage)

---

## 3. AGENCY ANALYTICS Data Flow

### 3.1 Data Sync (Fetching from Agency Analytics API)

**Location**: `app/api/sync.py:255-451` & `app/services/agency_analytics_client.py`

#### Authentication
```python
# Uses API key authentication
headers = {
    "Authorization": f"Bearer {settings.AGENCY_ANALYTICS_API_KEY}",
    "Content-Type": "application/json"
}
```

#### Step 1: Sync Campaigns
```python
# Endpoint: POST /api/v1/sync/agency-analytics
# File: app/api/sync.py:255-451

campaigns = await client.get_campaigns(limit=1000, offset=0)
supabase.upsert_agency_analytics_campaign(campaign)
```

**What happens**:
- Makes POST request to Agency Analytics API with GraphQL-like query
- Fetches campaign metadata: `id`, `company`, `url`, `status`, etc.
- Stores in `agency_analytics_campaigns` table

#### Step 2: Sync Rankings
```python
rankings = await client.get_campaign_rankings(campaign_id)
formatted_rankings = client.format_rankings_data(rankings, campaign)
supabase.upsert_agency_analytics_rankings(formatted_rankings)
```

**What happens**:
- Fetches quarterly ranking data (last 3 months)
- Includes: `google_ranking_count`, `google_local_ranking_count`, `google_mobile_ranking_count`, `bing_ranking_count`
- Stores in `agency_analytics_campaign_rankings` table

#### Step 3: Sync Keywords
```python
keywords = await client.get_all_campaign_keywords(campaign_id)
formatted_keywords = client.format_keywords_data(keywords)
supabase.upsert_agency_analytics_keywords(formatted_keywords)
```

**What happens**:
- Fetches all keywords for a campaign (with pagination)
- Includes: `keyword_phrase`, `search_volume`, `competition`, etc.
- Stores in `agency_analytics_keywords` table

#### Step 4: Sync Keyword Rankings
```python
for keyword in formatted_keywords:
    rankings = await client.get_keyword_rankings(keyword_id)
    daily_records, summary = client.format_keyword_rankings_data(rankings, keyword_id, campaign_id)
    supabase.upsert_agency_analytics_keyword_rankings(daily_records)
    supabase.upsert_agency_analytics_keyword_ranking_summary(summary)
```

**What happens**:
- Fetches daily ranking data for each keyword
- Creates summary with latest ranking and change
- Stores in `agency_analytics_keyword_rankings` and `agency_analytics_keyword_ranking_summaries` tables

#### Step 5: Link Campaigns to Brands
```python
# Auto-match campaigns to brands by URL
for brand in brands:
    match = client.match_campaign_to_brand(campaign, brand)
    if match:
        supabase.link_campaign_to_brand(
            campaign_id, brand_id, match_method, match_confidence
        )
```

**What happens**:
- Compares campaign URL with brand website URL
- Creates link in `agency_analytics_campaign_brands` table
- Enables brand-based reporting

### 3.2 Data Retrieval (For Reports)

**Location**: `app/api/data.py:511-796`

```python
# Get campaigns linked to brand
campaign_links = supabase.client.table("agency_analytics_campaign_brands")
    .select("*").eq("brand_id", brand_id)

campaign_ids = [link["campaign_id"] for link in campaign_links]

# Get keyword ranking summaries
summaries = supabase.client.table("agency_analytics_keyword_ranking_summaries")
    .select("*").eq("campaign_id", campaign_id)
```

### 3.3 KPI Calculation (In Reporting Dashboard)

**Location**: `app/api/data.py:872-954`

```python
# Get campaigns linked to this brand
campaign_links = supabase.client.table("agency_analytics_campaign_brands")
    .select("*").eq("brand_id", brand_id).execute()
campaign_ids = [link["campaign_id"] for link in campaign_links]

# Aggregate keyword data across all campaigns
for campaign_id in campaign_ids:
    summaries = supabase.client.table("agency_analytics_keyword_ranking_summaries")
        .select("*").eq("campaign_id", campaign_id).execute()
    
    for summary in summaries:
        total_search_volume += summary.get("search_volume", 0)
        ranking = summary.get("google_ranking") or summary.get("google_mobile_ranking") or 999
        
        # Categorize by ranking position
        if ranking <= 3:
            keywords_top3 += 1
        elif ranking <= 10:
            keywords_4_10 += 1
        # ... etc

# Get latest rankings for change calculation
rankings = supabase.client.table("agency_analytics_campaign_rankings")
    .select("*").eq("campaign_id", campaign_id)
    .order("date", desc=True).limit(2).execute()

# Calculate change
ranking_change = latest.get("google_ranking_count", 0) - previous.get("google_ranking_count", 0)

agency_kpis = {
    "google_rankings": {
        "value": latest.get("google_ranking_count", 0),
        "change": ranking_change,
        "source": "Agency Analytics"
    },
    "search_volume": {
        "value": total_search_volume,
        "source": "Agency Analytics"
    },
    "keywords_top3": {
        "value": keywords_top3,
        "source": "Agency Analytics"
    },
    "keywords_4_10": {
        "value": keywords_4_10,
        "source": "Agency Analytics"
    }
}
```

**KPIs Generated**:
- `google_rankings`: Total keywords ranking in Google
- `search_volume`: Combined search volume across all keywords
- `keywords_top3`: Count of keywords ranking in top 3 positions
- `keywords_4_10`: Count of keywords ranking in positions 4-10

---

## 4. REPORTING DASHBOARD AGGREGATION

### 4.1 Endpoint Flow

**Location**: `app/api/data.py:802-1054`

```python
# Endpoint: GET /api/v1/data/reporting-dashboard/{brand_id}?start_date=...&end_date=...

@router.get("/data/reporting-dashboard/{brand_id}")
async def get_reporting_dashboard(brand_id: int, start_date: str, end_date: str):
    # 1. Get brand info
    brand = supabase.client.table("brands").select("*").eq("id", brand_id)
    
    # 2. Fetch GA4 KPIs (if configured)
    if brand.get("ga4_property_id"):
        ga4_kpis = await fetch_ga4_kpis(brand, start_date, end_date)
    
    # 3. Fetch Agency Analytics KPIs (if linked campaigns exist)
    agency_kpis = await fetch_agency_analytics_kpis(brand_id)
    
    # 4. Fetch Scrunch AI KPIs (if prompts/responses exist)
    scrunch_kpis = await fetch_scrunch_kpis(brand_id)
    
    # 5. Combine all KPIs
    kpis = {**ga4_kpis, **agency_kpis, **scrunch_kpis}
    
    return {
        "brand_id": brand_id,
        "brand_name": brand.get("name"),
        "date_range": {"start_date": start_date, "end_date": end_date},
        "kpis": kpis,
        "available_sources": {
            "ga4": bool(ga4_kpis),
            "agency_analytics": bool(agency_kpis),
            "scrunch": bool(scrunch_kpis)
        }
    }
```

### 4.2 Response Structure

```json
{
  "brand_id": 1,
  "brand_name": "Example Brand",
  "date_range": {
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  },
  "kpis": {
    "total_sessions": {
      "value": 47832,
      "change": 12.4,
      "source": "GA4",
      "label": "Total Sessions",
      "icon": "BarChart"
    },
    "visibility_ai_platform": {
      "value": 73.2,
      "change": 5.8,
      "source": "Scrunch AI",
      "label": "Visibility On AI Platform",
      "icon": "Visibility",
      "format": "percentage"
    },
    "google_rankings": {
      "value": 163,
      "change": 15,
      "source": "Agency Analytics",
      "label": "Google Rankings",
      "icon": "Search"
    }
    // ... more KPIs
  },
  "available_sources": {
    "ga4": true,
    "agency_analytics": true,
    "scrunch": true
  }
}
```

---

## 5. FRONTEND DISPLAY FLOW

### 5.1 Component Flow

**Location**: `frontend/src/components/ReportingDashboard.jsx`

```javascript
// 1. Load brands list
const brands = await syncAPI.getBrands()

// 2. Load dashboard data for selected brand
const dashboardData = await reportingAPI.getReportingDashboard(
  selectedBrandId,
  startDate,
  endDate
)

// 3. Extract KPIs
const kpis = dashboardData.kpis  // Object with all KPIs

// 4. Display KPIs in cards
Object.entries(kpis).forEach(([key, kpi]) => {
  // Render KPI card with:
  // - Icon (based on kpi.icon)
  // - Label (kpi.label)
  // - Value (formatted based on kpi.format)
  // - Change indicator (kpi.change)
  // - Source badge (kpi.source)
})

// 5. Load additional chart data (if GA4 available)
if (dashboardData.available_sources.ga4) {
  const [sources, pages] = await Promise.all([
    ga4API.getTrafficSources(propertyId, startDate, endDate),
    ga4API.getTopPages(propertyId, startDate, endDate, 5)
  ])
  
  // Display charts using Recharts
  // - Pie chart for traffic sources
  // - Bar chart for top pages
}
```

### 5.2 Value Formatting

```javascript
const formatValue = (kpi) => {
  const { value, format } = kpi
  
  if (format === 'duration') {
    // Convert seconds to MM:SS
    const minutes = Math.floor(value / 60)
    const seconds = Math.floor(value % 60)
    return `${minutes}:${seconds.toString().padStart(2, '0')}`
  }
  
  if (format === 'percentage') {
    return `${value.toFixed(1)}%`
  }
  
  if (format === 'number') {
    return value.toLocaleString()  // Add commas
  }
  
  return value.toLocaleString()
}
```

---

## 6. DATA FLOW SUMMARY

### Sync Flow (External APIs → Database)
1. **Scrunch**: API → `brands`, `prompts`, `responses` tables
2. **GA4**: API → `ga4_traffic_overview`, `ga4_top_pages`, etc. tables
3. **Agency Analytics**: API → `agency_analytics_campaigns`, `agency_analytics_keywords`, etc. tables

### Report Flow (Database → Frontend)
1. **Reporting Dashboard Endpoint** aggregates KPIs from all three sources
2. **Frontend** fetches consolidated data via `/api/v1/data/reporting-dashboard/{brand_id}`
3. **KPIs** are displayed in cards with source badges
4. **Charts** are rendered using Recharts for visual data representation

### Key Points
- **Sync happens separately** for each data source (can be scheduled via cron jobs)
- **Reports fetch from database** (fast, no external API calls needed)
- **Real-time option**: GA4 can fetch directly from API if needed
- **Brand linking**: Agency Analytics campaigns are matched to brands by URL
- **Error handling**: Each source is independent - if one fails, others still work

---

## 7. EXAMPLE: Complete Flow for One Brand

### Step 1: Initial Sync (One-time setup)
```bash
# Sync Scrunch data
POST /api/v1/sync/all
→ Fetches brands, prompts, responses from Scrunch API
→ Stores in Supabase

# Sync GA4 data (if brand has ga4_property_id configured)
POST /api/v1/sync/ga4?brand_id=1
→ Fetches traffic data from GA4 API
→ Stores in Supabase

# Sync Agency Analytics data
POST /api/v1/sync/agency-analytics
→ Fetches campaigns, keywords, rankings
→ Auto-links campaigns to brands by URL
→ Stores in Supabase
```

### Step 2: View Report
```bash
# Frontend requests dashboard
GET /api/v1/data/reporting-dashboard/1?start_date=2024-01-01&end_date=2024-01-31

# Backend:
1. Gets brand info from brands table
2. Checks if GA4 configured → fetches GA4 KPIs
3. Checks for linked campaigns → fetches Agency Analytics KPIs
4. Checks for prompts/responses → calculates Scrunch KPIs
5. Combines all KPIs into single response

# Frontend:
1. Receives consolidated KPIs
2. Displays in animated cards
3. Fetches additional chart data if GA4 available
4. Renders pie chart (traffic sources) and bar chart (top pages)
```

### Step 3: Daily Sync (Automated)
```python
# daily_sync_job.py runs periodically
# Syncs latest data from all sources
# Keeps database up-to-date for reporting
```

---

## 8. Database Schema Overview

### Scrunch Tables
- `brands`: Brand metadata
- `prompts`: AI prompts tracked
- `responses`: AI responses with brand presence, citations, competitors

### GA4 Tables
- `ga4_traffic_overview`: Sessions, engagement metrics
- `ga4_top_pages`: Page performance data
- `ga4_traffic_sources`: Traffic source breakdown
- `ga4_geographic`: Geographic data
- `ga4_devices`: Device breakdown
- `ga4_conversions`: Conversion events
- `ga4_realtime`: Real-time snapshot

### Agency Analytics Tables
- `agency_analytics_campaigns`: Campaign metadata
- `agency_analytics_campaign_rankings`: Quarterly ranking data
- `agency_analytics_keywords`: Keyword metadata
- `agency_analytics_keyword_rankings`: Daily keyword rankings
- `agency_analytics_keyword_ranking_summaries`: Latest ranking summaries
- `agency_analytics_campaign_brands`: Links campaigns to brands

---

## 9. BRAND SEGREGATION & DATA ISOLATION

### 9.1 Brand as the Primary Entity

**Brands** are the central organizing entity in the system. All data from the three sources is linked to brands, enabling:
- Multi-brand support (each brand has isolated data)
- Brand-specific reporting
- Cross-brand analytics (when needed)
- Account manager access control (future)

### 9.2 Brand Table Structure

```sql
-- Brands table (primary entity)
CREATE TABLE brands (
    id INTEGER PRIMARY KEY,           -- Brand ID from Scrunch API
    name TEXT NOT NULL,               -- Brand name
    website TEXT,                      -- Brand website URL
    ga4_property_id TEXT,             -- GA4 Property ID (optional)
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
);
```

**Key Fields**:
- `id`: Primary identifier (from Scrunch API)
- `name`: Brand name for display
- `website`: Used for URL matching with Agency Analytics campaigns
- `ga4_property_id`: Links brand to GA4 property (optional, one-to-one)

### 9.3 Scrunch AI Data Segregation

#### How Brands Link to Scrunch Data

**Direct Foreign Key Relationship**:
```python
# Prompts table
CREATE TABLE prompts (
    id INTEGER PRIMARY KEY,
    brand_id INTEGER NOT NULL REFERENCES brands(id),  -- Direct link
    text TEXT,
    stage TEXT,
    ...
);

# Responses table
CREATE TABLE responses (
    id INTEGER PRIMARY KEY,
    brand_id INTEGER NOT NULL REFERENCES brands(id),  -- Direct link
    prompt_id INTEGER REFERENCES prompts(id),
    platform TEXT,
    brand_present BOOLEAN,
    ...
);
```

#### Sync Process
```python
# File: app/api/sync.py:35-93

# Step 1: Get all brands from Scrunch API
brands = await client.get_brands()

# Step 2: For each brand, sync prompts
for brand in brands:
    brand_id = brand.get("id")
    prompts = await client.get_all_prompts_paginated(brand_id=brand_id)
    supabase.upsert_prompts(prompts, brand_id=brand_id)  # Explicitly set brand_id

# Step 3: For each brand, sync responses
for brand in brands:
    brand_id = brand.get("id")
    responses = await client.get_all_responses_paginated(brand_id=brand_id)
    supabase.upsert_responses(responses, brand_id=brand_id)  # Explicitly set brand_id
```

**Key Points**:
- ✅ Each prompt and response has a `brand_id` foreign key
- ✅ Data is synced per brand (brand_id passed explicitly)
- ✅ Scrunch API provides brand-scoped endpoints (`/{brand_id}/prompts`, `/{brand_id}/responses`)
- ✅ Queries filter by `brand_id` for brand-specific data

#### Query Examples
```python
# Get prompts for a specific brand
prompts = supabase.client.table("prompts")
    .select("*")
    .eq("brand_id", brand_id)
    .execute()

# Get responses for a specific brand
responses = supabase.client.table("responses")
    .select("*")
    .eq("brand_id", brand_id)
    .execute()

# Get analytics for a specific brand
brand_responses = supabase.client.table("responses")
    .select("*")
    .eq("brand_id", brand_id)
    .execute()
analytics = calculate_analytics(brand_responses)
```

### 9.4 Google Analytics 4 Data Segregation

#### How Brands Link to GA4 Data

**Property ID Relationship**:
```python
# Brands table stores GA4 property ID
brand = {
    "id": 1,
    "name": "Example Brand",
    "ga4_property_id": "123456789"  # Links to GA4 property
}

# GA4 tables store brand_id
CREATE TABLE ga4_traffic_overview (
    brand_id INTEGER NOT NULL REFERENCES brands(id),  -- Links to brand
    property_id TEXT NOT NULL,                         -- GA4 Property ID
    date DATE NOT NULL,
    sessions INTEGER,
    ...
);
```

#### Sync Process
```python
# File: app/api/sync.py:507-655

# Step 1: Get all brands with GA4 configured
brands = supabase.client.table("brands")
    .select("*")
    .not_.is_("ga4_property_id", "null")
    .execute()

# Step 2: For each brand, sync GA4 data
for brand in brands:
    brand_id = brand.get("id")
    property_id = brand.get("ga4_property_id")
    
    # Fetch GA4 data using property_id
    traffic_data = await ga4_client.get_traffic_overview(property_id, start_date, end_date)
    
    # Store with brand_id
    supabase.upsert_ga4_traffic_overview(
        brand_id,           # Links data to brand
        property_id,        # GA4 property identifier
        end_date,
        traffic_data
    )
```

**Key Points**:
- ✅ One-to-one relationship: Each brand can have one GA4 property
- ✅ `ga4_property_id` stored in `brands` table
- ✅ All GA4 tables include `brand_id` column
- ✅ Data is synced per brand (only brands with `ga4_property_id` configured)
- ✅ If brand doesn't have GA4 configured, no GA4 data is synced/displayed

#### Query Examples
```python
# Get GA4 analytics for a specific brand
brand = supabase.client.table("brands")
    .select("*")
    .eq("id", brand_id)
    .execute()

if brand.get("ga4_property_id"):
    property_id = brand["ga4_property_id"]
    
    # Option 1: From database (if synced)
    traffic_overview = supabase.client.table("ga4_traffic_overview")
        .select("*")
        .eq("brand_id", brand_id)
        .eq("date", end_date)
        .execute()
    
    # Option 2: Direct from GA4 API (real-time)
    traffic_overview = await ga4_client.get_traffic_overview(property_id, start_date, end_date)
```

### 9.5 Agency Analytics Data Segregation

#### How Brands Link to Agency Analytics Data

**Campaign-Brand Linking Table**:
```sql
-- Campaign-Brand Linking Table (many-to-many relationship)
CREATE TABLE agency_analytics_campaign_brands (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER NOT NULL REFERENCES agency_analytics_campaigns(id),
    brand_id INTEGER NOT NULL REFERENCES brands(id),
    match_method TEXT NOT NULL,        -- 'url_match', 'manual'
    match_confidence TEXT,            -- 'exact', 'partial'
    created_at TIMESTAMPTZ,
    UNIQUE(campaign_id, brand_id)     -- One campaign can link to one brand
);
```

**Why Linking Table?**
- One campaign can belong to one brand (but system supports many-to-many if needed)
- Campaigns don't have direct brand relationship in Agency Analytics API
- URL matching creates the link automatically

#### Auto-Matching Process

**Location**: `app/services/agency_analytics_client.py:552-588`

```python
@staticmethod
def match_campaign_to_brand(campaign: Dict, brand: Dict) -> Optional[Dict]:
    """Match campaign to brand based on URL"""
    campaign_url = campaign.get("url", "")      # e.g., "https://example.com"
    brand_website = brand.get("website", "")    # e.g., "https://example.com"
    
    # Extract and normalize domains
    campaign_domain = extract_domain(campaign_url)    # "example.com"
    brand_domain = extract_domain(brand_website)      # "example.com"
    
    # Normalize (lowercase, remove www, etc.)
    campaign_domain = normalize_domain(campaign_domain)
    brand_domain = normalize_domain(brand_domain)
    
    # Exact match
    if campaign_domain == brand_domain:
        return {
            "campaign_id": campaign.get("id"),
            "brand_id": brand.get("id"),
            "match_method": "url_match",
            "match_confidence": "exact"
        }
    
    # Partial match (domain appears in URL)
    if brand_domain in campaign_url.lower():
        return {
            "campaign_id": campaign.get("id"),
            "brand_id": brand.get("id"),
            "match_method": "url_match",
            "match_confidence": "partial"
        }
    
    return None  # No match
```

#### Sync Process
```python
# File: app/api/sync.py:255-451

# Step 1: Get all brands for matching
brands = supabase.client.table("brands").select("*").execute()

# Step 2: Sync campaigns (no brand link yet)
campaigns = await client.get_campaigns()
for campaign in campaigns:
    supabase.upsert_agency_analytics_campaign(campaign)

# Step 3: Auto-match campaigns to brands
for campaign in campaigns:
    for brand in brands:
        match = client.match_campaign_to_brand(campaign, brand)
        if match:
            supabase.link_campaign_to_brand(
                match["campaign_id"],
                match["brand_id"],
                match["match_method"],
                match["match_confidence"]
            )
            break  # Only link to first matching brand

# Step 4: Sync keywords and rankings (campaign-scoped, not brand-scoped)
for campaign in campaigns:
    keywords = await client.get_all_campaign_keywords(campaign_id)
    supabase.upsert_agency_analytics_keywords(keywords)
    
    # Rankings are linked to campaign, not directly to brand
    rankings = await client.get_campaign_rankings(campaign_id)
    supabase.upsert_agency_analytics_rankings(rankings)
```

**Key Points**:
- ✅ Campaigns are matched to brands via URL comparison
- ✅ Linking happens automatically during sync (`auto_match_brands=True`)
- ✅ Manual linking also supported via API
- ✅ Keywords and rankings are linked to campaigns, not directly to brands
- ✅ To get brand data, query: Campaign → Campaign-Brand Link → Brand

#### Query Examples
```python
# Get campaigns linked to a brand
campaign_links = supabase.client.table("agency_analytics_campaign_brands")
    .select("*")
    .eq("brand_id", brand_id)
    .execute()

campaign_ids = [link["campaign_id"] for link in campaign_links]

# Get keywords for all campaigns linked to brand
for campaign_id in campaign_ids:
    keywords = supabase.client.table("agency_analytics_keywords")
        .select("*")
        .eq("campaign_id", campaign_id)
        .execute()

# Get keyword ranking summaries for all campaigns linked to brand
for campaign_id in campaign_ids:
    summaries = supabase.client.table("agency_analytics_keyword_ranking_summaries")
        .select("*")
        .eq("campaign_id", campaign_id)
        .execute()
```

### 9.6 Brand Segregation in Reporting Dashboard

**Location**: `app/api/data.py:802-1054`

```python
@router.get("/data/reporting-dashboard/{brand_id}")
async def get_reporting_dashboard(brand_id: int, ...):
    # 1. Get brand info
    brand = supabase.client.table("brands")
        .select("*")
        .eq("id", brand_id)
        .execute()
    
    # 2. SCRUNCH KPIs - Direct brand_id filter
    prompts = supabase.client.table("prompts")
        .select("*")
        .eq("brand_id", brand_id)  # Direct filter
        .execute()
    
    responses = supabase.client.table("responses")
        .select("*")
        .eq("brand_id", brand_id)  # Direct filter
        .execute()
    
    # Calculate Scrunch KPIs from brand-specific data
    scrunch_kpis = calculate_scrunch_kpis(prompts, responses)
    
    # 3. GA4 KPIs - Check if brand has GA4 configured
    if brand.get("ga4_property_id"):
        property_id = brand["ga4_property_id"]
        
        # Option A: From database (brand_id filter)
        traffic_overview = supabase.client.table("ga4_traffic_overview")
            .select("*")
            .eq("brand_id", brand_id)  # Direct filter
            .eq("date", end_date)
            .execute()
        
        # Option B: Direct from GA4 API (using property_id)
        traffic_overview = await ga4_client.get_traffic_overview(property_id, ...)
        
        ga4_kpis = calculate_ga4_kpis(traffic_overview)
    
    # 4. AGENCY ANALYTICS KPIs - Via campaign-brand links
    # Step 1: Get campaigns linked to this brand
    campaign_links = supabase.client.table("agency_analytics_campaign_brands")
        .select("*")
        .eq("brand_id", brand_id)  # Filter by brand
        .execute()
    
    campaign_ids = [link["campaign_id"] for link in campaign_links]
    
    # Step 2: Get data for all linked campaigns
    for campaign_id in campaign_ids:
        summaries = supabase.client.table("agency_analytics_keyword_ranking_summaries")
            .select("*")
            .eq("campaign_id", campaign_id)  # Filter by campaign
            .execute()
        
        # Aggregate across all campaigns for this brand
        # ...
    
    agency_kpis = calculate_agency_kpis(campaign_ids)
    
    # 5. Combine all KPIs
    return {
        "brand_id": brand_id,
        "kpis": {**ga4_kpis, **agency_kpis, **scrunch_kpis}
    }
```

### 9.7 Multi-Brand vs Single-Brand Queries

#### Single Brand Query (Reporting Dashboard)
```python
# All data filtered by brand_id
GET /api/v1/data/reporting-dashboard/{brand_id}

# Returns KPIs for ONE brand only
{
    "brand_id": 1,
    "brand_name": "Brand A",
    "kpis": {
        "total_sessions": {...},      # GA4 data for Brand A
        "visibility_ai_platform": {...},  # Scrunch data for Brand A
        "google_rankings": {...}     # Agency Analytics data for Brand A's campaigns
    }
}
```

#### Multi-Brand Query (Analytics Overview)
```python
# Get analytics for all brands or filtered brands
GET /api/v1/data/analytics/brands?brand_id={optional}

# If brand_id provided: Single brand analytics
if brand_id:
    responses = supabase.client.table("responses")
        .select("*")
        .eq("brand_id", brand_id)
        .execute()
    analytics = calculate_analytics(responses)

# If no brand_id: Multi-brand analytics
else:
    brands = supabase.client.table("brands").select("*").execute()
    brand_analytics = []
    
    for brand in brands:
        # Get responses for THIS brand only
        brand_responses = supabase.client.table("responses")
            .select("*")
            .eq("brand_id", brand["id"])  # Filter per brand
            .execute()
        
        brand_analytics.append({
            **brand,
            "analytics": calculate_analytics(brand_responses)
        })
    
    return {"brands": brand_analytics}
```

### 9.8 Brand Segregation Summary

| Data Source | Link Method | Relationship Type | Filter Method |
|------------|-------------|-------------------|---------------|
| **Scrunch AI** | Direct `brand_id` FK | One-to-Many (Brand → Prompts/Responses) | `.eq("brand_id", brand_id)` |
| **GA4** | `ga4_property_id` in brands + `brand_id` in GA4 tables | One-to-One (Brand ↔ GA4 Property) | `.eq("brand_id", brand_id)` |
| **Agency Analytics** | Campaign-Brand linking table | Many-to-Many (Brand ↔ Campaigns) | Join via `agency_analytics_campaign_brands` |

### 9.9 Data Isolation Guarantees

**Scrunch Data**:
- ✅ Each prompt/response has explicit `brand_id`
- ✅ Queries always filter by `brand_id`
- ✅ No cross-brand data leakage

**GA4 Data**:
- ✅ Each GA4 record has `brand_id` column
- ✅ Only brands with `ga4_property_id` have GA4 data
- ✅ Queries filter by `brand_id` when reading from database

**Agency Analytics Data**:
- ✅ Campaigns linked to brands via `agency_analytics_campaign_brands` table
- ✅ Keywords/rankings linked to campaigns (not directly to brands)
- ✅ To get brand data: Query campaigns → filter by brand_id in linking table → get campaign data

### 9.10 Example: Complete Brand Segregation Flow

```python
# Scenario: Get all data for Brand ID = 1

# 1. SCRUNCH DATA (Direct)
prompts_brand1 = supabase.client.table("prompts")
    .select("*")
    .eq("brand_id", 1)  # Direct filter
    .execute()

responses_brand1 = supabase.client.table("responses")
    .select("*")
    .eq("brand_id", 1)  # Direct filter
    .execute()

# 2. GA4 DATA (Property ID check)
brand1 = supabase.client.table("brands")
    .select("*")
    .eq("id", 1)
    .execute()

if brand1[0].get("ga4_property_id"):
    ga4_data_brand1 = supabase.client.table("ga4_traffic_overview")
        .select("*")
        .eq("brand_id", 1)  # Direct filter
        .execute()

# 3. AGENCY ANALYTICS DATA (Via linking table)
# Step 1: Get campaigns linked to Brand 1
campaign_links_brand1 = supabase.client.table("agency_analytics_campaign_brands")
    .select("*")
    .eq("brand_id", 1)  # Filter by brand
    .execute()

campaign_ids_brand1 = [link["campaign_id"] for link in campaign_links_brand1]

# Step 2: Get keywords for Brand 1's campaigns
keywords_brand1 = []
for campaign_id in campaign_ids_brand1:
    keywords = supabase.client.table("agency_analytics_keywords")
        .select("*")
        .eq("campaign_id", campaign_id)  # Filter by campaign
        .execute()
    keywords_brand1.extend(keywords)

# Result: All data is isolated to Brand 1
# - Scrunch: Direct brand_id filter
# - GA4: Direct brand_id filter (if configured)
# - Agency Analytics: Via campaign-brand links
```

### 9.11 Brand Configuration Requirements

For a brand to have complete reporting:

1. **Scrunch AI** (Required):
   - Brand must exist in `brands` table
   - Brand ID comes from Scrunch API
   - Prompts and responses automatically linked via `brand_id`

2. **GA4** (Optional):
   - Brand must have `ga4_property_id` configured in `brands` table
   - Property ID must be accessible via service account
   - If not configured, GA4 KPIs won't appear in dashboard

3. **Agency Analytics** (Optional):
   - Campaigns must be synced from Agency Analytics API
   - Campaigns must be matched to brand (auto or manual)
   - Link created in `agency_analytics_campaign_brands` table
   - If no campaigns linked, Agency Analytics KPIs won't appear

### 9.12 Frontend Brand Selection

**Location**: `frontend/src/components/ReportingDashboard.jsx`

```javascript
// 1. Load all brands
const brands = await syncAPI.getBrands()

// 2. User selects a brand
const selectedBrandId = 1

// 3. Fetch dashboard data for selected brand
const dashboardData = await reportingAPI.getReportingDashboard(
    selectedBrandId,  // Only data for this brand
    startDate,
    endDate
)

// 4. Display brand-specific KPIs
// All KPIs shown are for the selected brand only
```

---

## Conclusion

The system uses a **two-phase approach**:
1. **Sync Phase**: Fetch data from external APIs and store in Supabase (can be scheduled)
2. **Report Phase**: Aggregate data from Supabase and display in unified dashboard

**Brand Segregation** ensures:
- ✅ **Data Isolation**: Each brand's data is completely separate
- ✅ **Multi-Brand Support**: System handles multiple brands simultaneously
- ✅ **Flexible Linking**: Different linking methods for each data source
- ✅ **Selective Reporting**: Brands can have partial data (e.g., only Scrunch, or Scrunch + GA4)

This architecture provides:
- ✅ **Fast reporting** (no external API calls during report generation)
- ✅ **Reliability** (cached data available even if APIs are down)
- ✅ **Unified view** (all sources combined in one dashboard)
- ✅ **Flexibility** (each source can be enabled/disabled per brand)
- ✅ **Data isolation** (complete brand segregation for multi-tenant support)


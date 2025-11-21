# KPI Technical Calculations & Validation Guide

This document provides **exact technical details** for all KPIs displayed in the McRAE's Website Analytics dashboard. It includes precise formulas, data sources, API endpoints, database queries, and calculation steps needed to validate each metric when presenting to stakeholders.

**Document Purpose:** Use this document to verify and validate KPI calculations during stakeholder presentations and audits.

---

## Table of Contents

1. [Google Analytics 4 (GA4) KPIs - Technical Details](#google-analytics-4-ga4-kpis---technical-details)
2. [Agency Analytics KPIs - Technical Details](#agency-analytics-kpis---technical-details)
3. [Scrunch AI KPIs - Technical Details](#scrunch-ai-kpis---technical-details)
4. [Change Calculation Methodology](#change-calculation-methodology)
5. [Data Source References](#data-source-references)

---

## Google Analytics 4 (GA4) KPIs - Technical Details

**API Client:** `app/services/ga4_client.py`  
**Endpoint:** `app/api/data.py:927-1076`  
**API Used:** Google Analytics Data API v1beta  
**Authentication:** Service Account or OAuth Access Token

### Data Fetching Process

**Step 1:** Fetch Traffic Overview
- **Method:** `ga4_client.get_traffic_overview(property_id, start_date, end_date)`
- **API Call:** `RunReportRequest` to GA4 Data API
- **Metrics Requested:**
  - `activeUsers`
  - `sessions`
  - `newUsers`
  - `bounceRate`
  - `averageSessionDuration`
  - `engagedSessions`
  - `engagementRate`
- **Dimensions:** `date` (for daily breakdown)
- **Aggregation:** Sum across all dates in range (for count metrics), Average (for rate metrics)

**Step 2:** Fetch Conversions
- **Method:** `ga4_client.get_conversions(property_id, start_date, end_date)`
- **API Call:** `RunReportRequest` with filter for events containing "conversion"
- **Metrics:** `eventCount`, `totalUsers`
- **Aggregation:** Sum of all conversion event counts

**Step 3:** Fetch Revenue
- **Method:** Direct `RunReportRequest` for `totalRevenue` metric
- **API Call:** Single metric request (no dimensions)
- **Value:** Direct from GA4 API response

---

### 1. Users

**Formula:**
```
Users = SUM(activeUsers) for all dates in range
```

**Calculation Steps:**
1. Request GA4 API with metric `activeUsers` and dimension `date`
2. Iterate through all response rows
3. Sum all `activeUsers` values: `totals["users"] += int(metric_value.value)`
4. Return aggregated total

**Code Reference:** `app/services/ga4_client.py:145-146`

**Data Source:** Google Analytics 4 API - `activeUsers` metric

**Previous Period Comparison:**
- Previous period: `start_date - 60 days` to `start_date - 1 day`
- Change formula: `((current_users - prev_users) / prev_users) * 100`
- Display: Percentage change

**Validation:** Can be verified directly in GA4 dashboard under "Users" metric for the same date range.

---

### 2. Sessions

**Formula:**
```
Sessions = SUM(sessions) for all dates in range
```

**Calculation Steps:**
1. Request GA4 API with metric `sessions` and dimension `date`
2. Sum all session values across dates
3. GA4 defines a session as: starts when user opens website, ends after 30 minutes of inactivity or at midnight

**Code Reference:** `app/services/ga4_client.py:147-148`

**Data Source:** Google Analytics 4 API - `sessions` metric

**Previous Period Comparison:**
- Change comes from GA4 API response: `traffic_overview.get("sessionsChange", 0)`
- GA4 calculates this internally based on previous period comparison

**Validation:** Match against GA4 dashboard "Sessions" metric.

---

### 3. New Users

**Formula:**
```
New Users = SUM(newUsers) for all dates in range
```

**Calculation Steps:**
1. Request GA4 API with metric `newUsers`
2. Sum all `newUsers` values
3. GA4 identifies new users based on first-time visit detection (client ID)

**Code Reference:** `app/services/ga4_client.py:149-150` and `app/api/data.py:985`

**Data Source:** Google Analytics 4 API - `newUsers` metric

**Previous Period Comparison:**
```
new_users_change = ((new_users - prev_new_users) / prev_new_users) * 100
if prev_new_users > 0 else 0
```

**Code Reference:** `app/api/data.py:999`

**Validation:** Match against GA4 dashboard "New Users" metric.

---

### 4. Engaged Sessions

**Formula:**
```
Engaged Sessions = SUM(engagedSessions) for all dates in range
```

**GA4 Definition:** A session is considered "engaged" if it:
- Lasted longer than 10 seconds, OR
- Had a conversion event, OR
- Had 2 or more page views

**Calculation Steps:**
1. Request GA4 API with metric `engagedSessions`
2. Sum all values across dates

**Code Reference:** `app/services/ga4_client.py:155-156` and `app/api/data.py:986`

**Data Source:** Google Analytics 4 API - `engagedSessions` metric

**Previous Period Comparison:**
```
engaged_sessions_change = ((engaged_sessions - prev_engaged_sessions) / prev_engaged_sessions) * 100
if prev_engaged_sessions > 0 else 0
```

**Code Reference:** `app/api/data.py:1000`

**Validation:** Match against GA4 dashboard "Engaged Sessions" metric.

---

### 5. Bounce Rate

**Formula:**
```
Bounce Rate = AVERAGE(bounceRate) for all dates in range
```

**GA4 Definition:** Percentage of single-page sessions where users left without interacting.

**Calculation Steps:**
1. Request GA4 API with metric `bounceRate` and dimension `date`
2. Sum all bounce rate values: `totals["bounceRate"] += value`
3. Count number of dates: `count += 1`
4. Calculate average: `totals["bounceRate"] = totals["bounceRate"] / count`
5. Convert to percentage for display: `round(bounce_rate * 100, 2)`

**Code Reference:** 
- Aggregation: `app/services/ga4_client.py:151-152, 162`
- Display conversion: `app/api/data.py:1025`

**Data Source:** Google Analytics 4 API - `bounceRate` metric

**Previous Period Comparison:**
```
bounce_rate_change = ((bounce_rate - prev_bounce_rate) / prev_bounce_rate * 100)
if prev_bounce_rate > 0 else 0
```

**Code Reference:** `app/api/data.py:996`

**Validation:** Match against GA4 dashboard "Bounce Rate" metric (note: displayed as percentage 0-100%).

---

### 6. Average Session Duration

**Formula:**
```
Average Session Duration = AVERAGE(averageSessionDuration) for all dates in range
```

**Calculation Steps:**
1. Request GA4 API with metric `averageSessionDuration` and dimension `date`
2. Sum all duration values: `totals["averageSessionDuration"] += value`
3. Count dates: `count += 1`
4. Calculate average: `totals["averageSessionDuration"] = totals["averageSessionDuration"] / count`
5. Round to 1 decimal: `round(avg_session_duration, 1)`

**Code Reference:**
- Aggregation: `app/services/ga4_client.py:153-154, 163`
- Display: `app/api/data.py:1033`

**Data Source:** Google Analytics 4 API - `averageSessionDuration` metric (in seconds)

**Previous Period Comparison:**
```
avg_session_duration_change = ((avg_session_duration - prev_avg_session_duration) / prev_avg_session_duration * 100)
if prev_avg_session_duration > 0 else 0
```

**Code Reference:** `app/api/data.py:997`

**Validation:** Match against GA4 dashboard "Average Session Duration" (displayed as MM:SS format).

---

### 7. Engagement Rate

**Formula:**
```
Engagement Rate = AVERAGE(engagementRate) for all dates in range
```

**GA4 Definition:** Percentage of sessions that were engaged sessions.

**Calculation Steps:**
1. Request GA4 API with metric `engagementRate` and dimension `date`
2. Sum all engagement rate values
3. Calculate average: `totals["engagementRate"] = totals["engagementRate"] / count`
4. Convert to percentage: `round(engagement_rate * 100, 2)`

**Code Reference:**
- Aggregation: `app/services/ga4_client.py:157-158, 164`
- Display: `app/api/data.py:1041`

**Data Source:** Google Analytics 4 API - `engagementRate` metric

**Previous Period Comparison:**
```
engagement_rate_change = ((engagement_rate - prev_engagement_rate) / prev_engagement_rate * 100)
if prev_engagement_rate > 0 else 0
```

**Code Reference:** `app/api/data.py:998`

**Validation:** Match against GA4 dashboard "Engagement Rate" metric.

---

### 8. Conversions

**Formula:**
```
Conversions = SUM(eventCount) for all conversion events
```

**Calculation Steps:**
1. Request GA4 API with filter: `eventName CONTAINS "conversion"`
2. Get all conversion events with their `eventCount`
3. Sum all counts: `total_conversions = sum(c.get("count", 0) for c in conversions_data)`

**Code Reference:** `app/api/data.py:937-938`

**Data Source:** Google Analytics 4 API - Conversion events (custom events configured in GA4)

**Previous Period Comparison:**
```
conversions_change = ((total_conversions - prev_total_conversions) / prev_total_conversions) * 100
if prev_total_conversions > 0 else 0
```

**Code Reference:** `app/api/data.py:977-978`

**Validation:** Match against GA4 dashboard "Conversions" metric (sum of all conversion events).

**Note:** Only includes events that contain "conversion" in the event name. Custom conversion events must be properly configured in GA4.

---

### 9. Revenue

**Formula:**
```
Revenue = totalRevenue metric value from GA4 API
```

**Calculation Steps:**
1. Direct API request for `totalRevenue` metric (no dimensions)
2. Extract value: `revenue = float(revenue_response.rows[0].metric_values[0].value)`

**Code Reference:** `app/api/data.py:943-954`

**Data Source:** Google Analytics 4 API - `totalRevenue` metric

**Previous Period Comparison:**
- Currently set to 0 (not calculated)
- Can be added by fetching previous period revenue and calculating change

**Validation:** Match against GA4 dashboard "Revenue" metric (requires e-commerce tracking setup).

**Requirements:** E-commerce tracking must be properly configured in GA4 with purchase events tracking revenue.

---

## Agency Analytics KPIs - Technical Details

**Data Source:** Supabase Database Table `agency_analytics_keyword_ranking_summaries`  
**Endpoint:** `app/api/data.py:1078-1245`  
**API:** Agency Analytics API (synced to database)

### Data Fetching Process

**Step 1:** Get Linked Campaigns
```sql
SELECT * FROM agency_analytics_campaign_brands 
WHERE brand_id = {brand_id}
```

**Step 2:** Query Keyword Ranking Summaries
```sql
SELECT * FROM agency_analytics_keyword_ranking_summaries
WHERE campaign_id IN ({campaign_ids})
  AND date >= {start_date}
  AND date <= {end_date}
```

**Step 3:** Aggregate and Calculate KPIs

---

### 1. Impressions

**Formula:**
```
For each keyword summary:
  IF ranking <= 3:
    impression_rate = 0.95
  ELIF ranking <= 10:
    impression_rate = 0.75
  ELIF ranking <= 20:
    impression_rate = 0.50
  ELSE:
    impression_rate = 0.25

  estimated_impressions = search_volume × impression_rate

Total Impressions = SUM(estimated_impressions) for all keywords
```

**Calculation Steps:**
1. Query `agency_analytics_keyword_ranking_summaries` table
2. For each keyword summary:
   - Get `search_volume` and `google_ranking` (or `google_mobile_ranking`)
   - Determine impression rate based on ranking position
   - Calculate: `estimated_impressions = search_volume × impression_rate`
   - Add to total: `total_impressions += estimated_impressions`
3. Only count keywords with `ranking <= 100`

**Code Reference:** `app/api/data.py:1118-1134`

**Data Source:**
- `search_volume`: From Agency Analytics API (stored in database)
- `google_ranking` or `google_mobile_ranking`: From Agency Analytics API

**Impression Rate Assumptions:**
- Positions 1-3: 95% (industry standard - most users see top 3)
- Positions 4-10: 75% (most users see first page)
- Positions 11-20: 50% (half see second page)
- Positions 21+: 25% (fewer see beyond page 2)

**Validation:** This is an **ESTIMATE**. Actual impressions can only be verified in Google Search Console. The estimate is based on industry-standard visibility rates by position.

**Previous Period Comparison:**
- Currently set to 0 (not implemented)
- Would require historical data storage or recalculation

---

### 2. Clicks

**Formula:**
```
For each keyword summary:
  Calculate estimated_impressions (as above)
  
  IF ranking <= 3:
    ctr = 0.30  (30%)
  ELIF ranking <= 10:
    ctr = 0.10  (10%)
  ELIF ranking <= 20:
    ctr = 0.05  (5%)
  ELSE:
    ctr = 0.01  (1%)

  estimated_clicks = estimated_impressions × ctr

Total Clicks = SUM(estimated_clicks) for all keywords
```

**Calculation Steps:**
1. For each keyword, calculate estimated impressions (see Impressions above)
2. Determine CTR based on ranking position
3. Calculate: `estimated_clicks = estimated_impressions × ctr`
4. Sum all clicks: `total_clicks += estimated_clicks`

**Code Reference:** `app/api/data.py:1136-1147`

**Data Source:** Derived from estimated impressions and position-based CTR rates

**CTR Assumptions (Industry Standards):**
- Positions 1-3: ~30% CTR (position 1 gets ~31.7%, position 2 gets ~24.7%, position 3 gets ~18.6%)
- Positions 4-10: ~10% CTR (average across positions 4-10)
- Positions 11-20: ~5% CTR
- Positions 21+: ~1% CTR

**Validation:** This is an **ESTIMATE**. Actual clicks can only be verified in Google Search Console. CTR rates are industry averages and may vary by industry, keyword competitiveness, and listing quality.

**Previous Period Comparison:**
- Currently set to 0 (not implemented)

---

### 3. CTR (Click-Through Rate)

**Formula:**
```
CTR = (Total Clicks / Total Impressions) × 100
```

**Calculation Steps:**
1. Calculate total clicks (see Clicks above)
2. Calculate total impressions (see Impressions above)
3. Calculate percentage: `ctr_percentage = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0`

**Code Reference:** `app/api/data.py:1163`

**Data Source:** Derived from estimated clicks and impressions

**Validation:** This is calculated from estimated values, so it reflects the estimated CTR based on position-based assumptions.

---

### 4. Search Volume

**Formula:**
```
Search Volume = SUM(search_volume) for all keywords in date range
```

**Calculation Steps:**
1. Query keyword ranking summaries
2. Sum all `search_volume` values: `total_search_volume += search_volume`

**Code Reference:** `app/api/data.py:1154`

**Data Source:** `agency_analytics_keyword_ranking_summaries.search_volume` field (from Agency Analytics API)

**Validation:** This is **100% ACCURATE** - direct aggregation from Agency Analytics data. Can be verified by summing search volumes in Agency Analytics dashboard.

**Previous Period Comparison:**
- Currently set to 0 (not implemented)

---

### 5. Average Keyword Rank

**Formula:**
```
Average Keyword Rank = SUM(ranking) / COUNT(keywords)
```

**Calculation Steps:**
1. For each keyword summary:
   - Get ranking: `ranking = summary.get("google_ranking") or summary.get("google_mobile_ranking") or 999`
   - Only count if `ranking <= 100`
   - Add to sum: `ranking_sum += ranking`
   - Increment count: `total_rankings += 1`
2. Calculate average: `avg_keyword_rank = (ranking_sum / total_rankings) if total_rankings > 0 else 0`

**Code Reference:** `app/api/data.py:1120, 1149-1151, 1166`

**Data Source:** `agency_analytics_keyword_ranking_summaries.google_ranking` or `google_mobile_ranking`

**Ranking Priority:** Uses `google_ranking` if available, otherwise falls back to `google_mobile_ranking`. If neither exists, uses 999 (not ranking).

**Validation:** This is **100% ACCURATE** - direct calculation from Agency Analytics ranking data. Can be verified by calculating average rank in Agency Analytics dashboard.

**Previous Period Comparison:**
- Currently set to 0 (not implemented)

---

### 6. Average Ranking Change

**Formula:**
```
Average Ranking Change = SUM(ranking_change) / COUNT(keywords_with_change)
```

**Calculation Steps:**
1. For each keyword summary:
   - Get `ranking_change` field (calculated by Agency Analytics)
   - If `ranking_change` is not None:
     - Add to sum: `total_ranking_change += ranking_change`
     - Increment count: `ranking_change_count += 1`
2. Calculate average: `avg_ranking_change = (total_ranking_change / ranking_change_count) if ranking_change_count > 0 else 0`

**Code Reference:** `app/api/data.py:1157-1160, 1169`

**Data Source:** `agency_analytics_keyword_ranking_summaries.ranking_change` field

**Note:** The `ranking_change` field is calculated by Agency Analytics by comparing current ranking vs previous ranking. Positive values indicate improvement (moving up), negative values indicate decline (moving down).

**Validation:** This is **100% ACCURATE** - direct aggregation from Agency Analytics calculated field.

---

## Scrunch AI KPIs - Technical Details

**Data Source:** Supabase Database Tables `responses` and `prompts`  
**Endpoint:** `app/api/data.py:1261-1532`  
**API:** Scrunch AI API (synced to database)

### Data Fetching Process

**Step 1:** Query Responses
```sql
SELECT * FROM responses
WHERE brand_id = {brand_id}
  AND created_at >= '{start_date}T00:00:00Z'
  AND created_at <= '{end_date}T23:59:59Z'
```

**Step 2:** Query Prompts
```sql
SELECT * FROM prompts
WHERE brand_id = {brand_id}
```

**Step 3:** Calculate Metrics Using Helper Function

---

### 1. Influencer Reach

**Formula:**
```
Influencer Reach = Total Citations × 10,000
```

**Calculation Steps:**
1. Count total citations from all responses (see Total Citations below)
2. Apply multiplier: `influencer_reach = total_citations × 10000`

**Code Reference:** `app/api/data.py:1373-1374`

**Data Source:** Derived from Total Citations

**Assumption:** Each citation represents an average reach of 10,000 users. This is a **fixed multiplier assumption**.

**Validation:** This is an **ESTIMATE**. The 10,000 multiplier is an assumption and may not reflect actual reach. Actual reach would require data from AI platforms (ChatGPT, Claude, etc.) which is not available.

**Previous Period Comparison:**
```
influencer_reach_change = ((current_reach - prev_reach) / prev_reach) * 100
if prev_reach > 0 else (100.0 if current_reach > 0 else 0.0)
```

**Code Reference:** `app/api/data.py:1440`

---

### 2. Total Citations

**Formula:**
```
Total Citations = SUM(citation_count) for all responses
```

**Calculation Steps:**
1. For each response:
   - Get `citations` field (can be array or JSON string)
   - If array: `citation_count = len(citations)`
   - If JSON string: Parse and get length
   - Add to total: `total_citations += citation_count`

**Code Reference:** `app/api/data.py:1337-1351`

**Data Source:** `responses.citations` field (from Scrunch AI API)

**Citation Extraction Logic:**
```python
citations = r.get("citations")
citation_count = 0
if citations:
    if isinstance(citations, list):
        citation_count = len(citations)
    elif isinstance(citations, str):
        try:
            parsed = json.loads(citations)
            if isinstance(parsed, list):
                citation_count = len(parsed)
        except:
            pass
total_citations += citation_count
```

**Validation:** This is **100% ACCURATE** - direct count from Scrunch AI response data. Can be verified by counting citations in the database.

**Previous Period Comparison:**
```
total_citations_change = ((current_citations - prev_citations) / prev_citations) * 100
if prev_citations > 0 else (100.0 if current_citations > 0 else 0.0)
```

**Code Reference:** `app/api/data.py:1441`

---

### 3. Brand Presence Rate

**Formula:**
```
Brand Presence Rate = (Responses with brand_present = true / Total Responses) × 100
```

**Calculation Steps:**
1. Count responses where brand is present:
   ```python
   if r.get("brand_present"):
       brand_present_count += 1
   ```
2. Calculate percentage:
   ```python
   brand_presence_rate = (brand_present_count / len(responses_list) * 100)
   if responses_list else 0
   ```

**Code Reference:** `app/api/data.py:1354-1355, 1376`

**Data Source:** `responses.brand_present` field (boolean, from Scrunch AI API)

**Validation:** This is **100% ACCURATE** - direct calculation from Scrunch AI data. Can be verified by:
```sql
SELECT 
  COUNT(*) FILTER (WHERE brand_present = true) * 100.0 / COUNT(*) as presence_rate
FROM responses
WHERE brand_id = {brand_id}
  AND created_at >= '{start_date}'
  AND created_at <= '{end_date}'
```

**Previous Period Comparison:**
```
brand_presence_rate_change = ((current_rate - prev_rate) / prev_rate) * 100
if prev_rate > 0 else (100.0 if current_rate > 0 else 0.0)
```

**Code Reference:** `app/api/data.py:1442`

---

### 4. Brand Sentiment Score

**Formula:**
```
Sentiment Score = ((Positive × 1.0) + (Neutral × 0.0) + (Negative × -1.0)) / Total × 100
```

**Calculation Steps:**
1. Count sentiment distribution:
   ```python
   sentiment = r.get("brand_sentiment")
   if "positive" in sentiment.lower():
       sentiment_scores["positive"] += 1
   elif "negative" in sentiment.lower():
       sentiment_scores["negative"] += 1
   else:
       sentiment_scores["neutral"] += 1
   ```
2. Calculate weighted score:
   ```python
   total_sentiment_responses = sum(sentiment_scores.values())
   if total_sentiment_responses > 0:
       sentiment_score = (
           (sentiment_scores["positive"] * 1.0 + 
            sentiment_scores["neutral"] * 0.0 + 
            sentiment_scores["negative"] * -1.0) / total_sentiment_responses * 100
       )
   ```

**Code Reference:** `app/api/data.py:1358-1387`

**Data Source:** `responses.brand_sentiment` field (string: "positive", "neutral", "negative")

**Score Range:** -100 (all negative) to +100 (all positive), 0 (neutral or mixed)

**Validation:** This is **100% ACCURATE** - direct calculation from Scrunch AI sentiment data. Can be verified by:
```sql
SELECT 
  COUNT(*) FILTER (WHERE brand_sentiment ILIKE '%positive%') as positive,
  COUNT(*) FILTER (WHERE brand_sentiment ILIKE '%negative%') as negative,
  COUNT(*) FILTER (WHERE brand_sentiment NOT ILIKE '%positive%' AND brand_sentiment NOT ILIKE '%negative%') as neutral
FROM responses
WHERE brand_id = {brand_id}
  AND created_at >= '{start_date}'
  AND created_at <= '{end_date}'
```

Then calculate: `((positive × 1.0) + (neutral × 0.0) + (negative × -1.0)) / total × 100`

**Previous Period Comparison:**
```
sentiment_score_change = ((current_score - prev_score) / prev_score) * 100
if prev_score != 0 else (100.0 if current_score != 0 else 0.0)
```

**Code Reference:** `app/api/data.py:1444`

---

### 5. Engagement Rate (Scrunch)

**Formula:**
```
Engagement Rate = (Total Interactions / Influencer Reach) × 100
```

**Calculation Steps:**
1. Calculate Total Interactions (see below)
2. Calculate Influencer Reach (see above)
3. Calculate rate: `engagement_rate = (total_interactions / influencer_reach * 100) if influencer_reach > 0 else 0`

**Code Reference:** `app/api/data.py:1375`

**Data Source:** Derived from estimated interactions and reach

**Validation:** This is **ESTIMATED** - depends on estimated influencer reach and interactions.

**Previous Period Comparison:**
```
engagement_rate_change = ((current_rate - prev_rate) / prev_rate) * 100
if prev_rate > 0 else (100.0 if current_rate > 0 else 0.0)
```

**Code Reference:** `app/api/data.py:1445`

---

### 6. Total Interactions

**Formula:**
```
Total Interactions = Total Citations × 100
```

**Calculation Steps:**
1. For each response:
   - Get citation count
   - Calculate interactions: `interactions_per_citation = 100`
   - Add to total: `total_interactions += citation_count * interactions_per_citation`

**Code Reference:** `app/api/data.py:1369-1370`

**Data Source:** Derived from Total Citations

**Assumption:** Each citation generates an average of 100 interactions. This is a **fixed multiplier assumption**.

**Validation:** This is an **ESTIMATE**. The 100 interactions per citation is an assumption. Actual interactions would require data from AI platforms.

**Previous Period Comparison:**
```
total_interactions_change = ((current_interactions - prev_interactions) / prev_interactions) * 100
if prev_interactions > 0 else (100.0 if current_interactions > 0 else 0.0)
```

**Code Reference:** `app/api/data.py:1446`

---

### 7. Cost per Engagement

**Formula:**
```
Cost per Engagement = Total Cost / Total Interactions

Where:
  Total Cost = Number of Responses × $0.50
  Total Interactions = Total Citations × 100
```

**Calculation Steps:**
1. Count total responses: `len(responses_list)`
2. Calculate total cost: `total_cost = len(responses_list) × 0.50`
3. Calculate total interactions: `total_interactions = citations × 100` (see above)
4. Calculate CPE: `cost_per_engagement = (total_cost / total_interactions) if total_interactions > 0 else 0`

**Code Reference:** `app/api/data.py:1389-1391`

**Data Source:** 
- Response count: From database
- Cost assumption: Fixed at $0.50 per response
- Interactions: Estimated (see above)

**Assumptions:**
- Estimated cost per response: $0.50 USD
- Interactions per citation: 100 (see above)

**Validation:** This is **ESTIMATED** - based on assumed cost and estimated interactions. Actual cost would come from Scrunch AI billing data.

**Previous Period Comparison:**
```
cost_per_engagement_change = ((current_cpe - prev_cpe) / prev_cpe) * 100
if prev_cpe > 0 else (100.0 if current_cpe > 0 else 0.0)
```

**Code Reference:** `app/api/data.py:1447`

---

### 8. Top 10 Prompt Percentage

**Formula:**
```
Top 10 Prompt Percentage = (Responses from top 10 prompts / Total Responses) × 100
```

**Calculation Steps:**
1. Group responses by prompt:
   ```python
   prompt_counts = {}
   for r in responses_list:
       prompt_id = r.get("prompt_id")
       if prompt_id:
           prompt_counts[prompt_id] = prompt_counts.get(prompt_id, 0) + 1
   ```
2. Sort and get top 10:
   ```python
   sorted_prompts = sorted(prompt_counts.items(), key=lambda x: x[1], reverse=True)[:10]
   top10_count = sum(count for _, count in sorted_prompts)
   ```
3. Calculate percentage:
   ```python
   top10_prompt_percentage = (top10_count / len(responses_list) * 100)
   if responses_list else 0
   ```

**Code Reference:** `app/api/data.py:1324-1333`

**Data Source:** `responses.prompt_id` field

**Validation:** This is **100% ACCURATE** - direct calculation from response data. Can be verified by:
```sql
WITH prompt_counts AS (
  SELECT prompt_id, COUNT(*) as response_count
  FROM responses
  WHERE brand_id = {brand_id}
    AND created_at >= '{start_date}'
    AND created_at <= '{end_date}'
  GROUP BY prompt_id
),
top10 AS (
  SELECT SUM(response_count) as top10_count
  FROM (
    SELECT response_count
    FROM prompt_counts
    ORDER BY response_count DESC
    LIMIT 10
  ) t
)
SELECT 
  top10_count * 100.0 / (SELECT COUNT(*) FROM responses WHERE brand_id = {brand_id} AND created_at >= '{start_date}' AND created_at <= '{end_date}') as top10_percentage
FROM top10
```

**Previous Period Comparison:**
```
top10_prompt_change = ((current_percentage - prev_percentage) / prev_percentage) * 100
if prev_percentage > 0 else (100.0 if current_percentage > 0 else 0.0)
```

**Code Reference:** `app/api/data.py:1448`

---

### 9. Prompt Search Volume

**Formula:**
```
Prompt Search Volume = COUNT(responses) in date range
```

**Calculation Steps:**
1. Count all responses in the selected date range: `prompt_search_volume = len(responses_list)`

**Code Reference:** `app/api/data.py:1402`

**Data Source:** `responses` table count

**Validation:** This is **100% ACCURATE** - direct count from database. Can be verified by:
```sql
SELECT COUNT(*) 
FROM responses
WHERE brand_id = {brand_id}
  AND created_at >= '{start_date}T00:00:00Z'
  AND created_at <= '{end_date}T23:59:59Z'
```

**Previous Period Comparison:**
```
prompt_search_volume_change = ((current_volume - prev_volume) / prev_volume) * 100
if prev_volume > 0 else (100.0 if current_volume > 0 else 0.0)
```

**Code Reference:** `app/api/data.py:1449`

---

### 10. Visibility on AI Platform

**Formula:**
```
Visibility on AI Platform = Brand Presence Rate = (Responses with brand_present = true / Total Responses) × 100
```

**Calculation Steps:**
- Same as Brand Presence Rate (see above)
- `visibility_on_ai_platform = brand_presence_rate`

**Code Reference:** `app/api/data.py:1377`

**Data Source:** Same as Brand Presence Rate

**Validation:** Same as Brand Presence Rate - **100% ACCURATE**.

**Previous Period Comparison:**
```
visibility_change = ((current_visibility - prev_visibility) / prev_visibility) * 100
if prev_visibility > 0 else (100.0 if current_visibility > 0 else 0.0)
```

**Code Reference:** `app/api/data.py:1443`

---

## Change Calculation Methodology

### Previous Period Definition

**GA4 KPIs:**
- Previous period: `start_date - 60 days` to `start_date - 1 day`
- Duration: 60 days (fixed)
- Code: `app/api/data.py:959-960`

**Agency Analytics KPIs:**
- Previous period: Currently not calculated (set to 0)
- Would use same 60-day lookback if implemented

**Scrunch AI KPIs:**
- Previous period: Same duration as current period, ending the day before start_date
- Calculation:
  ```python
  period_duration = (end_date - start_date).days + 1
  prev_end = start_date - 1 day
  prev_start = start_date - period_duration days
  ```
- Code: `app/api/data.py:1267-1277`

### Change Formula

**Standard Percentage Change:**
```
change_percentage = ((current_value - previous_value) / previous_value) × 100
```

**Edge Cases:**
1. Both zero: `change = 0.0`
2. Previous zero, current > 0: `change = 100.0` (indicates new metric appeared)
3. Current zero, previous > 0: `change = -100.0` (indicates metric disappeared)
4. Previous > 0: Standard calculation

**Code Reference:** `app/api/data.py:1416-1438`

---

## Data Source References

### Database Tables

**Supabase Tables Used:**
1. `brands` - Brand configuration (includes `ga4_property_id`)
2. `responses` - Scrunch AI response data
   - Fields: `brand_id`, `created_at`, `citations`, `brand_present`, `brand_sentiment`, `prompt_id`
3. `prompts` - Scrunch AI prompt data
   - Fields: `id`, `brand_id`, `text`, `prompt_text`
4. `agency_analytics_campaign_brands` - Links campaigns to brands
   - Fields: `brand_id`, `campaign_id`
5. `agency_analytics_keyword_ranking_summaries` - Keyword ranking data
   - Fields: `campaign_id`, `date`, `search_volume`, `google_ranking`, `google_mobile_ranking`, `ranking_change`

### API Endpoints

**Google Analytics 4:**
- API: Google Analytics Data API v1beta
- Base URL: `https://analyticsdata.googleapis.com/v1beta`
- Endpoint: `properties/{property_id}:runReport`
- Authentication: Service Account or OAuth Access Token

**Agency Analytics:**
- API: Agency Analytics REST API
- Data synced to Supabase database
- Queries run against database tables

**Scrunch AI:**
- API: Scrunch AI REST API
- Data synced to Supabase database
- Queries run against database tables

---

## Validation Queries

### GA4 Validation

**Verify Users:**
```python
# In GA4 Dashboard:
# Navigate to Reports > Engagement > Overview
# Select date range
# Compare "Users" metric
```

**Verify Sessions:**
```python
# In GA4 Dashboard:
# Compare "Sessions" metric
```

**Verify Conversions:**
```python
# In GA4 Dashboard:
# Navigate to Reports > Engagement > Conversions
# Sum all conversion event counts
```

### Agency Analytics Validation

**Verify Search Volume:**
```sql
SELECT SUM(search_volume) as total_search_volume
FROM agency_analytics_keyword_ranking_summaries
WHERE campaign_id IN (
  SELECT campaign_id 
  FROM agency_analytics_campaign_brands 
  WHERE brand_id = {brand_id}
)
AND date >= '{start_date}'
AND date <= '{end_date}'
AND (google_ranking <= 100 OR google_mobile_ranking <= 100)
```

**Verify Average Keyword Rank:**
```sql
SELECT AVG(COALESCE(google_ranking, google_mobile_ranking, 999)) as avg_rank
FROM agency_analytics_keyword_ranking_summaries
WHERE campaign_id IN (
  SELECT campaign_id 
  FROM agency_analytics_campaign_brands 
  WHERE brand_id = {brand_id}
)
AND date >= '{start_date}'
AND date <= '{end_date}'
AND (COALESCE(google_ranking, google_mobile_ranking, 999) <= 100)
```

### Scrunch AI Validation

**Verify Total Citations:**
```sql
SELECT 
  SUM(
    CASE 
      WHEN citations IS NULL THEN 0
      WHEN jsonb_typeof(citations::jsonb) = 'array' THEN jsonb_array_length(citations::jsonb)
      ELSE 0
    END
  ) as total_citations
FROM responses
WHERE brand_id = {brand_id}
  AND created_at >= '{start_date}T00:00:00Z'
  AND created_at <= '{end_date}T23:59:59Z'
```

**Verify Brand Presence Rate:**
```sql
SELECT 
  COUNT(*) FILTER (WHERE brand_present = true) * 100.0 / COUNT(*) as presence_rate
FROM responses
WHERE brand_id = {brand_id}
  AND created_at >= '{start_date}T00:00:00Z'
  AND created_at <= '{end_date}T23:59:59Z'
```

**Verify Brand Sentiment Score:**
```sql
SELECT 
  (
    (COUNT(*) FILTER (WHERE brand_sentiment ILIKE '%positive%') * 1.0 +
     COUNT(*) FILTER (WHERE brand_sentiment NOT ILIKE '%positive%' AND brand_sentiment NOT ILIKE '%negative%') * 0.0 +
     COUNT(*) FILTER (WHERE brand_sentiment ILIKE '%negative%') * -1.0) / 
    COUNT(*) * 100
  ) as sentiment_score
FROM responses
WHERE brand_id = {brand_id}
  AND created_at >= '{start_date}T00:00:00Z'
  AND created_at <= '{end_date}T23:59:59Z'
  AND brand_sentiment IS NOT NULL
```

---

## Summary of Assumptions & Estimates

### Fixed Multipliers Used

1. **Agency Analytics - Impression Rates:**
   - Positions 1-3: 95%
   - Positions 4-10: 75%
   - Positions 11-20: 50%
   - Positions 21+: 25%

2. **Agency Analytics - CTR Rates:**
   - Positions 1-3: 30%
   - Positions 4-10: 10%
   - Positions 11-20: 5%
   - Positions 21+: 1%

3. **Scrunch AI - Influencer Reach:**
   - 10,000 reach per citation

4. **Scrunch AI - Interactions:**
   - 100 interactions per citation

5. **Scrunch AI - Cost per Response:**
   - $0.50 USD per response

### Industry Standards Reference

The CTR and impression rate assumptions are based on industry-standard research:
- **Moz CTR Study:** Average CTR by position (2014, updated periodically)
- **Advanced Web Ranking:** CTR distribution across search positions
- **SEMrush Studies:** Position-based visibility and click-through rates

**Note:** Actual CTR and impressions vary significantly by:
- Industry
- Keyword competitiveness
- Listing quality (title, description, rich snippets)
- Brand recognition
- Search intent

---

## Code File References

- **GA4 Client:** `app/services/ga4_client.py`
- **Reporting Dashboard Endpoint:** `app/api/data.py:882-1867`
- **Database Models:** `app/db/models.py`
- **Configuration:** `app/core/config.py`
- **Supabase Service:** `app/services/supabase_service.py`

---

## Conclusion

This document provides complete technical details for validating all KPIs. When presenting to stakeholders:

1. **For 100% Accurate KPIs:** Reference the exact API/database queries and show direct source verification
2. **For Estimated KPIs:** Clearly communicate the estimation methodology and industry-standard assumptions used
3. **For Change Calculations:** Explain the previous period comparison logic and edge case handling

All calculations can be independently verified using the provided SQL queries and API references.


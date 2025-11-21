# KPI Documentation

This document provides comprehensive information about all Key Performance Indicators (KPIs) displayed in the McRAE's Website Analytics system. KPIs are organized by data source and include details about their purpose, calculation methodology, and data accuracy.

---

## Table of Contents

1. [Google Analytics 4 (GA4) KPIs](#google-analytics-4-ga4-kpis)
2. [Agency Analytics KPIs](#agency-analytics-kpis)
3. [Scrunch AI KPIs](#scrunch-ai-kpis)
4. [Data Accuracy Summary](#data-accuracy-summary)

---

## Google Analytics 4 (GA4) KPIs

**Data Source**: Google Analytics 4 API  
**Total KPIs**: 9  
**Data Accuracy**: **100% Direct from Source** ✅

All GA4 KPIs are fetched directly from Google Analytics 4 API using the official GA4 Data API. No calculations or estimations are performed - values are exactly as reported by Google Analytics.

### 1. Users
- **Label**: Users
- **Description**: Total number of unique users who visited your website during the selected date range.
- **Why It's Used**: Measures the overall reach and audience size of your website. Essential for understanding brand awareness and traffic volume.
- **Calculation**: Direct metric from GA4 API (`activeUsers`). Counts unique users based on Google Analytics user identification.
- **Data Accuracy**: ✅ **100% Accurate** - Directly from GA4 API
- **Format**: Integer (whole number)

### 2. Sessions
- **Label**: Sessions
- **Description**: Total number of user sessions on your website. A session is a group of user interactions with your website within a given time frame.
- **Why It's Used**: Indicates overall website activity and engagement. Helps track traffic patterns and user behavior.
- **Calculation**: Direct metric from GA4 API (`sessions`). A session starts when a user opens your website and ends after 30 minutes of inactivity or at midnight.
- **Data Accuracy**: ✅ **100% Accurate** - Directly from GA4 API
- **Format**: Integer (whole number)

### 3. New Users
- **Label**: New Users
- **Description**: Number of users who visited your website for the first time during the selected period.
- **Why It's Used**: Measures acquisition effectiveness and brand growth. Helps evaluate marketing campaigns and new customer acquisition.
- **Calculation**: Direct metric from GA4 API (`newUsers`). Identified by Google Analytics based on first-time visit detection.
- **Data Accuracy**: ✅ **100% Accurate** - Directly from GA4 API
- **Format**: Integer (whole number)

### 4. Engaged Sessions
- **Label**: Engaged Sessions
- **Description**: Sessions that lasted longer than 10 seconds, had a conversion event, or had 2 or more page views.
- **Why It's Used**: Identifies sessions with meaningful user engagement, filtering out accidental or low-quality visits.
- **Calculation**: Direct metric from GA4 API (`engagedSessions`). GA4 automatically calculates this based on session duration and interaction criteria.
- **Data Accuracy**: ✅ **100% Accurate** - Directly from GA4 API
- **Format**: Integer (whole number)

### 5. Bounce Rate
- **Label**: Bounce Rate
- **Description**: Percentage of single-page sessions where users left without interacting with the page.
- **Why It's Used**: Indicates content relevance and user experience quality. Lower bounce rates typically suggest better engagement.
- **Calculation**: Direct metric from GA4 API (`bounceRate`). Calculated as: (Bounces / Sessions) × 100. Displayed as percentage (0-100%).
- **Data Accuracy**: ✅ **100% Accurate** - Directly from GA4 API
- **Format**: Percentage (0-100%)

### 6. Average Session Duration
- **Label**: Avg Session Duration
- **Description**: Average length of time users spend on your website per session.
- **Why It's Used**: Measures content engagement and user interest. Longer durations typically indicate better content quality and user satisfaction.
- **Calculation**: Direct metric from GA4 API (`averageSessionDuration`). Calculated by GA4 as total session duration divided by number of sessions. Displayed in seconds.
- **Data Accuracy**: ✅ **100% Accurate** - Directly from GA4 API
- **Format**: Duration (seconds, displayed as MM:SS)

### 7. Engagement Rate
- **Label**: Engagement Rate
- **Description**: Percentage of sessions that were engaged sessions (lasting >10 seconds, had conversions, or 2+ page views).
- **Why It's Used**: Overall indicator of website quality and user engagement. Higher rates suggest better user experience.
- **Calculation**: Direct metric from GA4 API (`engagementRate`). Calculated as: (Engaged Sessions / Total Sessions) × 100. Displayed as percentage (0-100%).
- **Data Accuracy**: ✅ **100% Accurate** - Directly from GA4 API
- **Format**: Percentage (0-100%)

### 8. Conversions
- **Label**: Conversions
- **Description**: Total number of conversion events that occurred during the selected period. Conversions are custom events you define in GA4 (e.g., purchases, form submissions, downloads).
- **Why It's Used**: Measures goal completion and business outcomes. Critical for evaluating ROI of marketing efforts.
- **Calculation**: Aggregated from GA4 Conversions API. Sums all conversion event counts across all conversion events configured in GA4.
- **Data Accuracy**: ✅ **100% Accurate** - Directly from GA4 API (based on your conversion event configuration)
- **Format**: Integer (whole number)

### 9. Revenue
- **Label**: Revenue
- **Description**: Total revenue generated from e-commerce transactions during the selected period.
- **Why It's Used**: Direct measure of business performance and financial impact. Essential for ROI calculations.
- **Calculation**: Direct metric from GA4 API (`totalRevenue`). Fetched from GA4 e-commerce data. Only available if e-commerce tracking is properly configured.
- **Data Accuracy**: ✅ **100% Accurate** - Directly from GA4 API (requires proper e-commerce setup)
- **Format**: Currency (USD)

---

## Agency Analytics KPIs

**Data Source**: Agency Analytics API → Supabase Database  
**Total KPIs**: 6  
**Data Accuracy**: **Mixed - Some Direct, Some Estimated** ⚠️

Agency Analytics KPIs are calculated from keyword ranking data stored in Supabase. Some metrics are direct aggregations, while others involve estimations based on industry-standard CTR and impression rates.

### 1. Impressions
- **Label**: Impressions
- **Description**: Estimated number of times your website appeared in Google search results for tracked keywords.
- **Why It's Used**: Measures brand visibility in search results. Higher impressions indicate better SEO performance and brand awareness.
- **Calculation**: **ESTIMATED** - Calculated from keyword search volume and ranking position:
  - Search Volume × Impression Rate (based on ranking position)
  - Top 3 positions: 95% impression rate
  - Positions 4-10: 75% impression rate
  - Positions 11-20: 50% impression rate
  - Positions 21+: 25% impression rate
- **Data Accuracy**: ⚠️ **Estimated** - Based on industry-standard impression rates, not actual Google Search Console data
- **Format**: Integer (whole number)

### 2. Clicks
- **Label**: Clicks
- **Description**: Estimated number of clicks your website received from Google search results.
- **Why It's Used**: Measures actual traffic generated from SEO efforts. Indicates how well your search listings convert impressions into visits.
- **Calculation**: **ESTIMATED** - Calculated from estimated impressions and position-based CTR:
  - Impressions × CTR (Click-Through Rate by position)
  - Top 3 positions: ~30% CTR
  - Positions 4-10: ~10% CTR
  - Positions 11-20: ~5% CTR
  - Positions 21+: ~1% CTR
- **Data Accuracy**: ⚠️ **Estimated** - Based on industry-standard CTR rates, not actual Google Search Console click data
- **Format**: Integer (whole number)

### 3. CTR (Click-Through Rate)
- **Label**: CTR
- **Description**: Percentage of impressions that resulted in clicks.
- **Why It's Used**: Measures the effectiveness of your search listings. Higher CTR indicates more compelling titles and descriptions.
- **Calculation**: **CALCULATED** - (Estimated Clicks / Estimated Impressions) × 100
- **Data Accuracy**: ⚠️ **Estimated** - Derived from estimated clicks and impressions
- **Format**: Percentage (0-100%)

### 4. Search Volume
- **Label**: Search Volume
- **Description**: Total combined monthly search volume for all tracked keywords.
- **Why It's Used**: Indicates the potential reach of your SEO efforts. Higher search volume suggests more opportunity for organic traffic.
- **Calculation**: **DIRECT AGGREGATION** - Sum of `search_volume` field from all keyword ranking summaries in the date range. This data comes from Agency Analytics API (which sources from keyword research tools).
- **Data Accuracy**: ✅ **100% Accurate** - Direct aggregation from Agency Analytics data
- **Format**: Integer (whole number)

### 5. Average Keyword Rank
- **Label**: Avg Keyword Rank
- **Description**: Average ranking position across all tracked keywords in Google search results.
- **Why It's Used**: Overall indicator of SEO performance. Lower numbers (closer to 1) indicate better rankings.
- **Calculation**: **CALCULATED** - Average of `google_ranking` or `google_mobile_ranking` values from keyword ranking summaries. Only includes keywords ranking in top 100.
- **Data Accuracy**: ✅ **100% Accurate** - Direct calculation from Agency Analytics ranking data
- **Format**: Number (decimal, typically 1-100)

### 6. Average Ranking Change
- **Label**: Avg Ranking Change
- **Description**: Average change in ranking position across all keywords (positive = improved, negative = declined).
- **Why It's Used**: Tracks SEO progress over time. Positive changes indicate improving rankings.
- **Calculation**: **DIRECT AGGREGATION** - Average of `ranking_change` field from keyword ranking summaries. This field is calculated by Agency Analytics comparing current vs previous rankings.
- **Data Accuracy**: ✅ **100% Accurate** - Direct aggregation from Agency Analytics calculated field
- **Format**: Number (decimal, can be positive or negative)

---

## Scrunch AI KPIs

**Data Source**: Scrunch AI API → Supabase Database  
**Total KPIs**: 10  
**Data Accuracy**: **Mixed - Some Direct, Some Estimated** ⚠️

Scrunch AI KPIs are calculated from AI platform response data stored in Supabase. Some metrics are direct counts from the data, while others involve estimations and calculations.

### 1. Influencer Reach
- **Label**: Influencer Reach
- **Description**: Estimated total reach of AI platforms/influencers that mentioned or cited your brand.
- **Why It's Used**: Measures brand visibility and potential audience exposure across AI platforms (ChatGPT, Claude, etc.).
- **Calculation**: **ESTIMATED** - `Total Citations × 10,000` (estimated average reach per citation)
- **Data Accuracy**: ⚠️ **Estimated** - Uses a fixed multiplier assumption (10,000 per citation)
- **Format**: Integer (whole number)

### 2. Total Citations
- **Label**: Total Citations
- **Description**: Total number of times your brand was cited or mentioned in AI platform responses.
- **Why It's Used**: Direct measure of brand presence in AI-generated content. Indicates how often your brand appears in AI responses.
- **Calculation**: **DIRECT COUNT** - Sum of citation counts from all responses. Citations are extracted from the `citations` field in response data (can be array or JSON string).
- **Data Accuracy**: ✅ **100% Accurate** - Direct count from Scrunch AI response data
- **Format**: Integer (whole number)

### 3. Brand Presence Rate
- **Label**: Brand Presence Rate
- **Description**: Percentage of AI responses that mentioned your brand.
- **Why It's Used**: Measures brand visibility in AI platforms. Higher rates indicate better brand recognition in AI-generated content.
- **Calculation**: **CALCULATED** - (Responses with `brand_present = true` / Total Responses) × 100
- **Data Accuracy**: ✅ **100% Accurate** - Direct calculation from Scrunch AI `brand_present` field
- **Format**: Percentage (0-100%)

### 4. Brand Sentiment Score
- **Label**: Brand Sentiment Score
- **Description**: Overall sentiment score indicating how positively your brand is mentioned in AI responses. Range: -100 (very negative) to +100 (very positive).
- **Why It's Used**: Measures brand perception in AI-generated content. Helps identify reputation issues or positive brand associations.
- **Calculation**: **CALCULATED** - Weighted average based on sentiment distribution:
  - Positive responses: +1.0 point
  - Neutral responses: 0.0 points
  - Negative responses: -1.0 point
  - Score = ((Positive × 1.0) + (Neutral × 0.0) + (Negative × -1.0)) / Total × 100
- **Data Accuracy**: ✅ **100% Accurate** - Direct calculation from Scrunch AI `brand_sentiment` field
- **Format**: Number (-100 to +100)

### 5. Engagement Rate
- **Label**: Engagement Rate (Scrunch)
- **Description**: Estimated percentage of influencer reach that resulted in interactions.
- **Why It's Used**: Measures audience engagement with AI-generated content mentioning your brand.
- **Calculation**: **CALCULATED** - (Total Interactions / Influencer Reach) × 100
- **Data Accuracy**: ⚠️ **Estimated** - Depends on estimated influencer reach and interactions
- **Format**: Percentage (0-100%)

### 6. Total Interactions
- **Label**: Total Interactions
- **Description**: Estimated total number of user interactions with AI responses that mentioned your brand.
- **Why It's Used**: Measures actual engagement with brand mentions in AI platforms.
- **Calculation**: **ESTIMATED** - `Total Citations × 100` (estimated interactions per citation)
- **Data Accuracy**: ⚠️ **Estimated** - Uses a fixed multiplier assumption (100 interactions per citation)
- **Format**: Integer (whole number)

### 7. Cost per Engagement
- **Label**: Cost per Engagement
- **Description**: Estimated cost per interaction with AI-generated content mentioning your brand.
- **Why It's Used**: Measures efficiency of AI brand presence efforts. Helps evaluate ROI of Scrunch AI campaigns.
- **Calculation**: **ESTIMATED** - (Total Cost / Total Interactions)
  - Total Cost = Number of Responses × $0.50 (estimated cost per response)
  - Total Interactions = Citations × 100
- **Data Accuracy**: ⚠️ **Estimated** - Based on assumed cost per response and estimated interactions
- **Format**: Currency (USD)

### 8. Top 10 Prompt Percentage
- **Label**: Top 10 Prompt
- **Description**: Percentage of responses that came from the top 10 most frequently used prompts.
- **Why It's Used**: Indicates prompt effectiveness and concentration of brand mentions. Higher percentages suggest successful prompt strategies.
- **Calculation**: **CALCULATED** - (Responses from top 10 prompts / Total Responses) × 100
  - Groups responses by `prompt_id`
  - Identifies top 10 prompts by response count
  - Calculates percentage
- **Data Accuracy**: ✅ **100% Accurate** - Direct calculation from response data grouped by prompt
- **Format**: Percentage (0-100%)

### 9. Prompt Search Volume
- **Label**: Prompt Search Volume
- **Description**: Total number of AI responses generated for your brand's prompts during the selected period.
- **Why It's Used**: Measures activity level and testing volume. Indicates how extensively your brand is being tested in AI platforms.
- **Calculation**: **DIRECT COUNT** - Count of responses in the selected date range
- **Data Accuracy**: ✅ **100% Accurate** - Direct count from database
- **Format**: Integer (whole number)

### 10. Visibility on AI Platform
- **Label**: Visibility On AI Platform
- **Description**: Percentage of AI responses where your brand was present/mentioned.
- **Why It's Used**: Overall indicator of brand visibility across AI platforms. Same as Brand Presence Rate but presented as a separate metric.
- **Calculation**: **CALCULATED** - Same as Brand Presence Rate: (Responses with `brand_present = true` / Total Responses) × 100
- **Data Accuracy**: ✅ **100% Accurate** - Direct calculation from Scrunch AI `brand_present` field
- **Format**: Percentage (0-100%)

---

## Data Accuracy Summary

### ✅ 100% Accurate - Direct from Source (18 KPIs)

These KPIs are fetched directly from their respective APIs or are direct aggregations/calculations from source data with no estimations:

**GA4 (9 KPIs)**:
- Users
- Sessions
- New Users
- Engaged Sessions
- Bounce Rate
- Average Session Duration
- Engagement Rate
- Conversions
- Revenue

**Agency Analytics (3 KPIs)**:
- Search Volume
- Average Keyword Rank
- Average Ranking Change

**Scrunch AI (6 KPIs)**:
- Total Citations
- Brand Presence Rate
- Brand Sentiment Score
- Top 10 Prompt Percentage
- Prompt Search Volume
- Visibility on AI Platform

### ⚠️ Estimated/Calculated (7 KPIs)

These KPIs involve estimations, assumptions, or industry-standard multipliers:

**Agency Analytics (3 KPIs)**:
- Impressions (estimated from search volume × position-based impression rates)
- Clicks (estimated from impressions × position-based CTR rates)
- CTR (calculated from estimated clicks/impressions)

**Scrunch AI (4 KPIs)**:
- Influencer Reach (estimated: citations × 10,000)
- Engagement Rate (calculated from estimated interactions/reach)
- Total Interactions (estimated: citations × 100)
- Cost per Engagement (estimated: cost/interactions using assumed $0.50 per response)

---

## Important Notes

### Data Freshness
- **GA4**: Data is fetched in real-time from GA4 API. May have up to 24-48 hour delay for final data.
- **Agency Analytics**: Data is synced periodically from Agency Analytics API. Freshness depends on sync frequency.
- **Scrunch AI**: Data is synced from Scrunch AI API. Freshness depends on sync frequency.

### Data Availability
- KPIs are only displayed if the corresponding data source is configured for the brand:
  - GA4 KPIs require `ga4_property_id` to be set in brand configuration
  - Agency Analytics KPIs require campaigns to be linked to the brand
  - Scrunch AI KPIs require prompts and responses to exist for the brand

### Change Calculations
- All KPIs include percentage change compared to the previous period (same duration, ending the day before the start date)
- Change calculations are performed automatically by comparing current period values with previous period values

### Limitations
1. **Estimated Metrics**: Impressions, Clicks, CTR, Influencer Reach, and Interactions are estimates based on industry standards and assumptions. Actual values may vary.
2. **Data Delays**: Some data sources may have processing delays (especially GA4, which can take 24-48 hours for final data).
3. **Configuration Required**: Each data source must be properly configured and synced for KPIs to appear.

---

## Conclusion

The system provides a comprehensive view of brand performance across three key areas:
- **Website Performance** (GA4) - 100% accurate, real-time data
- **SEO Performance** (Agency Analytics) - Mix of accurate rankings and estimated traffic metrics
- **AI Platform Presence** (Scrunch AI) - Mix of accurate presence metrics and estimated engagement metrics

Users should be aware that while most KPIs are directly sourced from their respective APIs, some metrics (particularly traffic estimates and engagement metrics) are calculated using industry-standard assumptions and should be used as directional indicators rather than exact values.


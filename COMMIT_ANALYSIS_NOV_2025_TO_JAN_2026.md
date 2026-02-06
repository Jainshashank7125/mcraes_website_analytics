# Git Commit Analysis: November 2025 to January 2026

**Generated:** 2026-01-28 08:25:18

**Total Commits:** 130

---

## 2026-01-15

### Commit: 1c7b4d79

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-15 20:47:45 +0000
- **Message:** Enhance GA4 data handling and reporting: - Modify geographic breakdown retrieval to support aggregated and daily data modes. - Update GA4APIClient to include daily breakdown option and improve logging. - Refactor SupabaseService to handle multi-date geographic data upserts. - Add manual data load trigger in ReportingDashboard for improved user control. - Adjust data formatting in GA4Section for consistency in user metrics display. - Update cron job setup script to export necessary environment variables for daily sync.

**Files Changed:** 7 files
**Total Additions:** +255 lines
**Total Deletions:** -134 lines

**Files Modified:**
- `app/api/data.py` (+17/-12)
- `app/services/background_sync.py` (+14/-3)
- `app/services/ga4_client.py` (+78/-33)
- `app/services/supabase_service.py` (+98/-44)
- `frontend/src/components/ReportingDashboard.jsx` (+44/-39)
- `frontend/src/components/reporting/GA4Section.jsx` (+2/-2)
- `setup_cron_auto.sh` (+2/-1)

---

### Commit: de0e14e3

- **Author:** satvik2131 (satvik213161@gmail.com)
- **Date:** 2026-01-15 17:25:15 +0530
- **Message:** fixes

**Files Changed:** 1 files
**Total Additions:** +1 lines
**Total Deletions:** -1 lines

**Files Modified:**
- `frontend/src/components/ReportingDashboard.jsx` (+1/-1)

---

### Commit: 569eec32

- **Author:** satvik2131 (satvik213161@gmail.com)
- **Date:** 2026-01-15 17:18:09 +0530
- **Message:** Decoupled Checboxes in settings + charts & visualization

**Files Changed:** 2 files
**Total Additions:** +204 lines
**Total Deletions:** -97 lines

**Files Modified:**
- `frontend/src/components/ReportingDashboard.jsx` (+185/-85)
- `frontend/src/components/reporting/ChartCard.jsx` (+19/-12)

---

### Commit: 2f21f84b

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-15 14:07:04 +0000
- **Message:** fixed ga4 client

**Files Changed:** 1 files
**Total Additions:** +120 lines
**Total Deletions:** -50 lines

**Files Modified:**
- `app/services/ga4_client.py` (+120/-50)

---

### Commit: f468c66e

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-15 11:26:37 +0000
- **Message:** On main: Temporary stash before revert

**Files Changed:** 2 files
**Total Additions:** +6 lines
**Total Deletions:** -2 lines

**Files Modified:**
- `app/services/supabase_service.py` (+6/-1)
- `frontend/src/components/ReportingDashboard.jsx` (+0/-1)

---

### Commit: 0f5c4857

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-15 11:26:37 +0000
- **Message:** Revert "Refactor GA4 reporting logic to improve snapshot handling and data accuracy. Enhance user metrics section in ReportingDashboard with new users trend and adjust chart visibility conditions. Implement weighted averages for engagement metrics in GA4APIClient. Add detailed logging for Scrunch API queries and responses to aid debugging."

**Description:**
```
This reverts commit 99983758a352e14f8a559aab0e62362e8808d5ed.
```

**Files Changed:** 7 files
**Total Additions:** +370 lines
**Total Deletions:** -554 lines

**Files Modified:**
- `app/api/data.py` (+37/-73)
- `app/services/ga4_client.py` (+17/-47)
- `app/services/scrunch_client.py` (+2/-9)
- `app/services/supabase_service.py` (+83/-160)
- `frontend/src/components/ReportingDashboard.jsx` (+212/-78)
- `frontend/src/components/reporting/charts/BarChart.jsx` (+0/-1)
- `frontend/src/components/reporting/charts/ScrunchVisualizations.jsx` (+19/-186)

---

### Commit: 541d3aeb

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-15 11:26:37 +0000
- **Message:** index on main: 9998375 Refactor GA4 reporting logic to improve snapshot handling and data accuracy. Enhance user metrics section in ReportingDashboard with new users trend and adjust chart visibility conditions. Implement weighted averages for engagement metrics in GA4APIClient. Add detailed logging for Scrunch API queries and responses to aid debugging.

---

### Commit: 99983758

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-15 10:25:43 +0000
- **Message:** Refactor GA4 reporting logic to improve snapshot handling and data accuracy. Enhance user metrics section in ReportingDashboard with new users trend and adjust chart visibility conditions. Implement weighted averages for engagement metrics in GA4APIClient. Add detailed logging for Scrunch API queries and responses to aid debugging.

**Files Changed:** 7 files
**Total Additions:** +554 lines
**Total Deletions:** -370 lines

**Files Modified:**
- `app/api/data.py` (+73/-37)
- `app/services/ga4_client.py` (+47/-17)
- `app/services/scrunch_client.py` (+9/-2)
- `app/services/supabase_service.py` (+160/-83)
- `frontend/src/components/ReportingDashboard.jsx` (+78/-212)
- `frontend/src/components/reporting/charts/BarChart.jsx` (+1/-0)
- `frontend/src/components/reporting/charts/ScrunchVisualizations.jsx` (+186/-19)

---

## 2026-01-14

### Commit: c32b07b3

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-14 07:44:31 +0000
- **Message:** Fix Position (% of total) visibility - add showPositionDistribution check to prevent chart from showing when unchecked

**Files Changed:** 1 files
**Total Additions:** +1 lines
**Total Deletions:** -1 lines

**Files Modified:**
- `frontend/src/components/reporting/charts/ScrunchVisualizations.jsx` (+1/-1)

---

### Commit: 3e5962b6

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-14 07:38:33 +0000
- **Message:** Split Advanced Query Visualizations into 5 separate chart options: AI Platform Distribution, Competitive Presence Analysis, Brand Presence Trend Over Time, Position (% of total), and Brand Sentiment Analysis

**Files Changed:** 2 files
**Total Additions:** +49 lines
**Total Deletions:** -10 lines

**Files Modified:**
- `frontend/src/components/ReportingDashboard.jsx` (+36/-6)
- `frontend/src/components/reporting/charts/ScrunchVisualizations.jsx` (+13/-4)

---

### Commit: 22b8dd3a

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-14 06:57:59 +0000
- **Message:** Add troubleshooting guide for Brand Presence Rate visibility

**Files Changed:** 1 files
**Total Additions:** +60 lines
**Total Deletions:** -0 lines

**Files Modified:**
- `BRAND_PRESENCE_RATE_VISIBILITY.md` (+60/-0)

---

### Commit: 299262f4

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-14 06:51:13 +0000
- **Message:** Fix Brand Presence Rate heading in ReportingDashboard - change from 'Brand Presence Metrics' to 'Brand Presence Rate'

**Files Changed:** 1 files
**Total Additions:** +1 lines
**Total Deletions:** -1 lines

**Files Modified:**
- `frontend/src/components/ReportingDashboard.jsx` (+1/-1)

---

### Commit: d750c07e

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-14 06:50:46 +0000
- **Message:** Fix Brand Presence Rate section heading - change from 'Brand Presence Metrics' to 'Brand Presence Rate' to match config box

**Files Changed:** 1 files
**Total Additions:** +1 lines
**Total Deletions:** -1 lines

**Files Modified:**
- `frontend/src/components/reporting/ScrunchAISection.jsx` (+1/-1)

---

### Commit: c6597c42

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-14 06:45:11 +0000
- **Message:** Add revenue KPI to KPI_ORDER - ensure it appears in config box

**Files Changed:** 1 files
**Total Additions:** +1 lines
**Total Deletions:** -0 lines

**Files Modified:**
- `frontend/src/components/reporting/constants.js` (+1/-0)

---

### Commit: b61e0fda

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-14 06:43:16 +0000
- **Message:** Complete channel deduplication in GA4Section - fix all remaining chart instances

**Files Changed:** 1 files
**Total Additions:** +9 lines
**Total Deletions:** -5 lines

**Files Modified:**
- `frontend/src/components/reporting/GA4Section.jsx` (+9/-5)

---

### Commit: 510f1deb

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-14 06:42:27 +0000
- **Message:** Apply channel deduplication to GA4Section component - fix duplicate channels in all charts

**Files Changed:** 1 files
**Total Additions:** +55 lines
**Total Deletions:** -9 lines

**Files Modified:**
- `frontend/src/components/reporting/GA4Section.jsx` (+55/-9)

---

### Commit: c745fe98

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-14 06:41:17 +0000
- **Message:** Fix duplicate channels in charts - add deduplication to aggregate same channels (e.g. Organic Search) by summing users and sessions

**Files Changed:** 1 files
**Total Additions:** +53 lines
**Total Deletions:** -21 lines

**Files Modified:**
- `frontend/src/components/ReportingDashboard.jsx` (+53/-21)

---

## 2026-01-13

### Commit: e74e36d2

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-13 15:12:16 +0000
- **Message:** Replace Traffic Sources Distribution by Channel with Total Users by Channel - update chart to show users instead of sessions

**Files Changed:** 2 files
**Total Additions:** +11 lines
**Total Deletions:** -11 lines

**Files Modified:**
- `frontend/src/components/ReportingDashboard.jsx` (+5/-5)
- `frontend/src/components/reporting/GA4Section.jsx` (+6/-6)

---

### Commit: f11e6539

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-13 15:07:28 +0000
- **Message:** Update Advanced Query Visualizations label and description to include all charts: AI Platform Distribution, Competitive Presence Analysis, Brand Presence Trend Over Time, Position (% of total), and Brand Sentiment Analysis

**Files Changed:** 1 files
**Total Additions:** +2 lines
**Total Deletions:** -2 lines

**Files Modified:**
- `frontend/src/components/ReportingDashboard.jsx` (+2/-2)

---

### Commit: 1531800e

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-13 15:00:09 +0000
- **Message:** Add complete audit documentation for all config box fixes

**Files Changed:** 1 files
**Total Additions:** +186 lines
**Total Deletions:** -0 lines

**Files Modified:**
- `COMPLETE_CONFIG_BOX_AUDIT.md` (+186/-0)

---

### Commit: 3dd5c165

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-13 14:59:27 +0000
- **Message:** Ensure BrandAnalyticsSection uses KPI_METADATA for consistent labels

**Files Changed:** 1 files
**Total Additions:** +2 lines
**Total Deletions:** -1 lines

**Files Modified:**
- `frontend/src/components/reporting/BrandAnalyticsSection.jsx` (+2/-1)

---

### Commit: e1b2a17e

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-13 14:58:52 +0000
- **Message:** Add comprehensive summary of config box label fixes

**Files Changed:** 1 files
**Total Additions:** +69 lines
**Total Deletions:** -0 lines

**Files Modified:**
- `CONFIG_BOX_FIXES_SUMMARY.md` (+69/-0)

---

### Commit: 4aab2171

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-13 14:58:36 +0000
- **Message:** Fix chart label mismatches - ensure config box matches dashboard display names

**Files Changed:** 1 files
**Total Additions:** +3 lines
**Total Deletions:** -3 lines

**Files Modified:**
- `frontend/src/components/ReportingDashboard.jsx` (+3/-3)

---

### Commit: 08843b46

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-13 14:56:58 +0000
- **Message:** Add documentation mapping config box labels to dashboard displays

**Files Changed:** 1 files
**Total Additions:** +34 lines
**Total Deletions:** -0 lines

**Files Modified:**
- `CONFIG_BOX_MAPPING.md` (+34/-0)

---

### Commit: 709a36cc

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-13 14:56:34 +0000
- **Message:** Update chart labels in config box - match dashboard names for Position and Brand Sentiment Analysis

**Files Changed:** 1 files
**Total Additions:** +2 lines
**Total Deletions:** -2 lines

**Files Modified:**
- `frontend/src/components/ReportingDashboard.jsx` (+2/-2)

---

### Commit: 694266ea

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-13 14:43:02 +0000
- **Message:** Ensure same KPI keys use same label in config box - use KPI_METADATA consistently

**Files Changed:** 1 files
**Total Additions:** +4 lines
**Total Deletions:** -4 lines

**Files Modified:**
- `frontend/src/components/ReportingDashboard.jsx` (+4/-4)

---

### Commit: e98d2772

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-13 14:42:01 +0000
- **Message:** Deduplicate KPIs in config box - ensure each KPI appears only once per section

**Files Changed:** 1 files
**Total Additions:** +4 lines
**Total Deletions:** -3 lines

**Files Modified:**
- `frontend/src/components/ReportingDashboard.jsx` (+4/-3)

---

### Commit: 108365be

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-13 14:41:02 +0000
- **Message:** Consolidate KPI_METADATA - use shared constants from constants.js to ensure config box and cards always match

**Files Changed:** 1 files
**Total Additions:** +4 lines
**Total Deletions:** -182 lines

**Files Modified:**
- `frontend/src/components/ReportingDashboard.jsx` (+4/-182)

---

### Commit: 0625148e

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-13 14:40:06 +0000
- **Message:** Fix KPI label mismatch - ensure config box and KPI cards use same labels from KPI_METADATA

**Files Changed:** 2 files
**Total Additions:** +12 lines
**Total Deletions:** -9 lines

**Files Modified:**
- `frontend/src/components/reporting/KPICard.jsx` (+4/-1)
- `frontend/src/components/reporting/constants.js` (+8/-8)

---

### Commit: c486a2db

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-13 14:25:52 +0000
- **Message:** Fix: Remove visibility checks for Sessions by Channel and Sessions vs Users by Channel charts - always show when data is available

**Files Changed:** 1 files
**Total Additions:** +10 lines
**Total Deletions:** -8 lines

**Files Modified:**
- `frontend/src/components/ReportingDashboard.jsx` (+10/-8)

---

### Commit: bf096566

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-13 14:16:47 +0000
- **Message:** Update getChannelLabel in ReportingDashboard to match enhanced channel name formatting

**Files Changed:** 1 files
**Total Additions:** +45 lines
**Total Deletions:** -20 lines

**Files Modified:**
- `frontend/src/components/ReportingDashboard.jsx` (+45/-20)

---

### Commit: 81a68be1

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-13 14:16:30 +0000
- **Message:** Enhance getChannelLabel to properly format GA4 channel names (Organic Search, Direct, Paid Search, etc.)

**Files Changed:** 2 files
**Total Additions:** +48 lines
**Total Deletions:** -12 lines

**Files Modified:**
- `frontend/src/components/ReportingDashboard.jsx` (+7/-4)
- `frontend/src/components/reporting/utils.js` (+41/-8)

---

### Commit: 381ee768

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-13 14:15:58 +0000
- **Message:** Fix channel display - use getChannelLabel to format channel names properly in Sessions by Channel and Sessions vs Users by Channel charts

**Files Changed:** 1 files
**Total Additions:** +10 lines
**Total Deletions:** -7 lines

**Files Modified:**
- `frontend/src/components/reporting/GA4Section.jsx` (+10/-7)

---

### Commit: 3e0fe6f6

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-13 13:51:10 +0000
- **Message:** Fix Bounce Rate alignment - appears beside Geographic/Top Countries charts when space is available

**Files Changed:** 1 files
**Total Additions:** +87 lines
**Total Deletions:** -10 lines

**Files Modified:**
- `frontend/src/components/reporting/GA4Section.jsx` (+87/-10)

---

### Commit: d7c026d8

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-13 13:46:09 +0000
- **Message:** Fix grid alignment - charts now align to top when others are removed, preventing bottom alignment issue

**Files Changed:** 1 files
**Total Additions:** +10 lines
**Total Deletions:** -10 lines

**Files Modified:**
- `frontend/src/components/reporting/GA4Section.jsx` (+10/-10)

---

### Commit: 7d705311

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-13 13:42:22 +0000
- **Message:** Fix alignment issue when Revenue chart is removed - Conversions chart now takes full width

**Files Changed:** 1 files
**Total Additions:** +2 lines
**Total Deletions:** -2 lines

**Files Modified:**
- `frontend/src/components/reporting/GA4Section.jsx` (+2/-2)

---

### Commit: 5dc3a58b

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-13 13:24:19 +0000
- **Message:** Add enhanced logging for Agency Analytics sync debugging

**Files Changed:** 2 files
**Total Additions:** +47 lines
**Total Deletions:** -7 lines

**Files Modified:**
- `app/services/agency_analytics_client.py` (+39/-7)
- `app/services/background_sync.py` (+8/-0)

---

### Commit: 2ba5a093

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-13 12:48:28 +0000
- **Message:** Add date range display to client report view (public view)

**Files Changed:** 1 files
**Total Additions:** +73 lines
**Total Deletions:** -0 lines

**Files Modified:**
- `frontend/src/components/ReportingDashboard.jsx` (+73/-0)

---

### Commit: 8b11e885

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-13 12:42:39 +0000
- **Message:** Update Traffic Sources Distribution to show channels instead of sources

**Files Changed:** 2 files
**Total Additions:** +7 lines
**Total Deletions:** -7 lines

**Files Modified:**
- `frontend/src/components/ReportingDashboard.jsx` (+3/-3)
- `frontend/src/components/reporting/GA4Section.jsx` (+4/-4)

---

### Commit: c5aa958e

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-13 12:37:06 +0000
- **Message:** Change Sessions by Channel charts to show channel names (Organic, Direct, etc.) instead of source/medium

**Files Changed:** 4 files
**Total Additions:** +32 lines
**Total Deletions:** -15 lines

**Files Modified:**
- `app/services/ga4_client.py` (+5/-2)
- `app/services/supabase_service.py` (+2/-0)
- `frontend/src/components/ReportingDashboard.jsx` (+13/-7)
- `frontend/src/components/reporting/GA4Section.jsx` (+12/-6)

---

### Commit: d9b37143

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-13 12:14:49 +0000
- **Message:** Change Top Countries and Geo Distribution to show sessions instead of users

**Files Changed:** 4 files
**Total Additions:** +17 lines
**Total Deletions:** -17 lines

**Files Modified:**
- `app/services/ga4_client.py` (+1/-1)
- `app/services/supabase_service.py` (+2/-2)
- `frontend/src/components/ReportingDashboard.jsx` (+5/-5)
- `frontend/src/components/reporting/GA4Section.jsx` (+9/-9)

---

### Commit: d498f7b8

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-13 12:07:51 +0000
- **Message:** Replace Active Users with Total Users across dashboard and config

**Files Changed:** 6 files
**Total Additions:** +174 lines
**Total Deletions:** -15 lines

**Files Modified:**
- `app/api/data.py` (+2/-2)
- `app/services/ga4_client.py` (+2/-2)
- `frontend/src/components/ReportingDashboard.jsx` (+4/-4)
- `frontend/src/components/reporting/BrandAnalyticsSection.jsx` (+2/-2)
- `frontend/src/components/reporting/GA4Section.jsx` (+5/-5)
- `frontend/src/components/reporting/constants.js` (+159/-0)

---

## 2026-01-12

### Commit: 1f1588a7

- **Author:** satvik2131 (satvik213161@gmail.com)
- **Date:** 2026-01-12 19:26:36 +0530
- **Message:** fix

**Files Changed:** 3 files
**Total Additions:** +5 lines
**Total Deletions:** -5 lines

**Files Modified:**
- `frontend/src/components/ReportingDashboard.jsx` (+3/-3)
- `frontend/src/components/reporting/BrandAnalyticsSection.jsx` (+1/-1)
- `frontend/src/components/reporting/GA4Section.jsx` (+1/-1)

---

### Commit: c89cf584

- **Author:** satvik2131 (satvik213161@gmail.com)
- **Date:** 2026-01-12 18:56:08 +0530
- **Message:** updated namings

**Files Changed:** 4 files
**Total Additions:** +21 lines
**Total Deletions:** -21 lines

**Files Modified:**
- `frontend/src/components/BrandAnalyticsDetail.jsx` (+2/-2)
- `frontend/src/components/ReportingDashboard.jsx` (+9/-9)
- `frontend/src/components/reporting/BrandAnalyticsSection.jsx` (+1/-1)
- `frontend/src/components/reporting/GA4Section.jsx` (+9/-9)

---

### Commit: 44b9dc0c

- **Author:** satvik2131 (satvik213161@gmail.com)
- **Date:** 2026-01-12 11:01:09 +0530
- **Message:** added config for individual graphs

**Files Changed:** 2 files
**Total Additions:** +53 lines
**Total Deletions:** -11 lines

**Files Modified:**
- `frontend/src/components/KeywordsDashboard.jsx` (+12/-1)
- `frontend/src/components/ReportingDashboard.jsx` (+41/-10)

---

## 2026-01-09

### Commit: 89fcafaf

- **Author:** satvik2131 (satvik213161@gmail.com)
- **Date:** 2026-01-09 20:22:04 +0530
- **Message:** fixed scrunch + ga4 badges in clients

**Files Changed:** 1 files
**Total Additions:** +68 lines
**Total Deletions:** -9 lines

**Files Modified:**
- `frontend/src/components/ClientsList.jsx` (+68/-9)

---

### Commit: aa968f69

- **Author:** satvik2131 (satvik213161@gmail.com)
- **Date:** 2026-01-09 18:17:14 +0530
- **Message:**  ga4 property id dropdown fix

**Files Changed:** 1 files
**Total Additions:** +17 lines
**Total Deletions:** -13 lines

**Files Modified:**
- `frontend/src/components/ClientManagement.jsx` (+17/-13)

---

### Commit: ae57de27

- **Author:** satvik2131 (satvik213161@gmail.com)
- **Date:** 2026-01-09 18:01:54 +0530
- **Message:** fixed the sync with g4a + previous period lines removal option working

**Files Changed:** 4 files
**Total Additions:** +138 lines
**Total Deletions:** -138 lines

**Files Modified:**
- `app/services/background_sync.py` (+9/-6)
- `frontend/src/components/ReportingDashboard.jsx` (+8/-8)
- `frontend/src/components/reporting/DashboardContent.jsx` (+2/-0)
- `frontend/src/components/reporting/GA4Section.jsx` (+119/-124)

---

### Commit: bdebca5a

- **Author:** satvik2131 (satvik213161@gmail.com)
- **Date:** 2026-01-09 15:43:42 +0530
- **Message:** fixed previous period sync

**Files Changed:** 1 files
**Total Additions:** +46 lines
**Total Deletions:** -16 lines

**Files Modified:**
- `app/api/data.py` (+46/-16)

---

### Commit: 3d78bd7a

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-09 09:08:35 +0000
- **Message:** Enhance keyword ranking retrieval in `get_client_keyword_rankings_over_time`

**Description:**
```
- Added filtering for rankings with volume greater than 0 to align with keywords table logic.
- Included keyword_id in the rankings query to ensure unique keyword counting per date.
- Implemented detailed logging for fetched ranking records and bucket counts for better debugging and analysis.
- Improved handling of duplicate keyword counts and invalid rankings for both Google and Bing results.
```

**Files Changed:** 1 files
**Total Additions:** +75 lines
**Total Deletions:** -8 lines

**Files Modified:**
- `app/api/data.py` (+75/-8)

---

### Commit: 384f8f33

- **Author:** satvik2131 (satvik213161@gmail.com)
- **Date:** 2026-01-09 09:31:45 +0530
- **Message:** fixed empty arrays reduce issue

**Files Changed:** 1 files
**Total Additions:** +1 lines
**Total Deletions:** -1 lines

**Files Modified:**
- `frontend/src/components/reporting/charts/ScrunchVisualizations.jsx` (+1/-1)

---

## 2026-01-08

### Commit: eacf59ea

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-08 11:12:43 +0530
- **Message:** Update ReportingDashboard to conditionally render traffic source chart based on visibility setting

**Files Changed:** 1 files
**Total Additions:** +1 lines
**Total Deletions:** -1 lines

**Files Modified:**
- `frontend/src/components/ReportingDashboard.jsx` (+1/-1)

---

### Commit: 872bc277

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-08 11:04:11 +0530
- **Message:** Enhance keyword ranking retrieval and campaign synchronization

**Description:**
```
- Updated `get_client_keywords` to clarify that the latest ranking is fetched within the specified date range, not an average.
- Improved `sync_agency_analytics_background` to include detailed logging for campaign fetching, error handling, and filtering of campaigns.
- Refined GA4 traffic source aggregation in `get_ga4_traffic_sources_by_date_range` to prevent double-counting by using monthly maximum values.
- Adjusted `KeywordsDashboard` and `ReportingDashboard` components to reflect changes in ranking data and KPI selections, ensuring a more intuitive user experience.
```

**Files Changed:** 5 files
**Total Additions:** +250 lines
**Total Deletions:** -37 lines

**Files Modified:**
- `app/api/data.py` (+48/-9)
- `app/services/background_sync.py` (+34/-3)
- `app/services/supabase_service.py` (+67/-13)
- `frontend/src/components/KeywordsDashboard.jsx` (+1/-0)
- `frontend/src/components/ReportingDashboard.jsx` (+100/-12)

---

## 2026-01-07

### Commit: 9a3024c8

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-07 17:50:39 +0000
- **Message:** Update database backup and restore documentation; add quick dump guide and error handling scripts

**Description:**
```
- Revised backup methods in `docker-help.md` to emphasize custom format and provide clearer instructions.
- Introduced `QUICK_DUMP_GUIDE.md` for streamlined database dump and restore processes.
- Added `restore_sql_with_error_handling.sh` script to manage SQL restoration with error logging and handling for malformed data.
```

**Files Changed:** 4 files
**Total Additions:** +378 lines
**Total Deletions:** -41 lines

**Files Modified:**
- `QUICK_DUMP_GUIDE.md` (+115/-0)
- `docker-help.md` (+149/-29)
- `scripts/restore_database_dump.sh` (+12/-12)
- `scripts/restore_sql_with_error_handling.sh` (+102/-0)

---

### Commit: b66da914

- **Author:** satvik2131 (satvik213161@gmail.com)
- **Date:** 2026-01-07 08:06:05 +0530
- **Message:** decimal issue fixed

**Files Changed:** 1 files
**Total Additions:** +76 lines
**Total Deletions:** -72 lines

**Files Modified:**
- `frontend/src/components/ReportingDashboard.jsx` (+76/-72)

---

## 2026-01-06

### Commit: 8f92f439

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-06 15:33:38 +0530
- **Message:** Enhance error handling and improve user experience in ReportingDashboard

**Files Changed:** 4 files
**Total Additions:** +22 lines
**Total Deletions:** -3 lines

**Files Modified:**
- `app/core/error_utils.py` (+7/-0)
- `app/core/exceptions.py` (+11/-1)
- `frontend/src/components/Layout.jsx` (+2/-1)
- `frontend/src/components/ReportingDashboard.jsx` (+2/-1)

---

### Commit: ceaf68a5

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2026-01-06 14:52:53 +0530
- **Message:** Implement automatic cron job setup and update entrypoint script & Changed image source paths in frontend components to use local assets.

**Files Changed:** 5 files
**Total Additions:** +76 lines
**Total Deletions:** -29 lines

**Files Modified:**
- `Dockerfile.backend` (+4/-0)
- `docker-entrypoint.sh` (+9/-27)
- `frontend/src/components/Layout.jsx` (+1/-1)
- `frontend/src/components/ReportingDashboard.jsx` (+1/-1)
- `setup_cron_auto.sh` (+61/-0)

---

## 2026-01-02

### Commit: dc9f2c81

- **Author:** Satvik Kushwaha (59243339+satvik2131@users.noreply.github.com)
- **Date:** 2026-01-02 14:42:03 +0530
- **Message:** Merge pull request #3 from Jainshashank7125/feat-added-geolocation-in-dashboard-links

**Description:**
```
added geolocation in dashboard links
```

**Files Changed:** 2 files
**Total Additions:** +467 lines
**Total Deletions:** -44 lines

**Files Modified:**
- `frontend/src/components/DashboardLinksManagement.jsx` (+133/-44)
- `frontend/src/services/geolocation.js` (+334/-0)

---

### Commit: 98d48d6b

- **Author:** satvik2131 (satvik213161@gmail.com)
- **Date:** 2026-01-02 14:41:03 +0530
- **Message:** added geolocation in dashboard links

**Files Changed:** 2 files
**Total Additions:** +467 lines
**Total Deletions:** -44 lines

**Files Modified:**
- `frontend/src/components/DashboardLinksManagement.jsx` (+133/-44)
- `frontend/src/services/geolocation.js` (+334/-0)

---

## 2025-12-24

### Commit: fbe8e970

- **Author:** Satvik Kushwaha (59243339+satvik2131@users.noreply.github.com)
- **Date:** 2025-12-24 16:30:51 +0530
- **Message:** Merge pull request #2 from Jainshashank7125/feat(ui)-responsivenes-for-exec-summary

**Description:**
```
Feat(UI) responsivenes for exec summary
```

**Files Changed:** 3 files
**Total Additions:** +703 lines
**Total Deletions:** -371 lines

**Files Modified:**
- `frontend/src/components/KeywordsDashboard.jsx` (+89/-29)
- `frontend/src/components/ReportingDashboard.jsx` (+99/-102)
- `frontend/src/components/reporting/ExecutiveSummary.jsx` (+515/-240)

---

### Commit: 2dd88d19

- **Author:** satvik2131 (satvik213161@gmail.com)
- **Date:** 2025-12-24 16:18:57 +0530
- **Message:** managed layout + spacing fixed

**Files Changed:** 2 files
**Total Additions:** +182 lines
**Total Deletions:** -117 lines

**Files Modified:**
- `frontend/src/components/KeywordsDashboard.jsx` (+89/-29)
- `frontend/src/components/ReportingDashboard.jsx` (+93/-88)

---

### Commit: 86f2f5bd

- **Author:** satvik2131 (satvik213161@gmail.com)
- **Date:** 2025-12-24 14:10:18 +0530
- **Message:** fixed responsiveness to the top bar

**Files Changed:** 2 files
**Total Additions:** +189 lines
**Total Deletions:** -196 lines

**Files Modified:**
- `frontend/src/components/ReportingDashboard.jsx` (+7/-16)
- `frontend/src/components/reporting/ExecutiveSummary.jsx` (+182/-180)

---

### Commit: 358c6729

- **Author:** satvik2131 (satvik213161@gmail.com)
- **Date:** 2025-12-24 11:37:11 +0530
- **Message:** carousel in exec summary

**Files Changed:** 2 files
**Total Additions:** +469 lines
**Total Deletions:** -195 lines

**Files Modified:**
- `frontend/src/components/ReportingDashboard.jsx` (+2/-1)
- `frontend/src/components/reporting/ExecutiveSummary.jsx` (+467/-194)

---

## 2025-12-22

### Commit: be329cd2

- **Author:** Shashank Jain (77048679+Jainshashank7125@users.noreply.github.com)
- **Date:** 2025-12-22 16:24:31 +0530
- **Message:** [fix]- Update Executive Summary Page to have a disclaimer and positive outcomes only

**Description:**
```
Fix(UI) summary page
```

**Files Changed:** 1 files
**Total Additions:** +34 lines
**Total Deletions:** -7 lines

**Files Modified:**
- `frontend/src/components/reporting/ExecutiveSummary.jsx` (+34/-7)

---

### Commit: d8ae99e2

- **Author:** Satvik Kushwaha (satvik@Satviks-Mac-mini.local)
- **Date:** 2025-12-22 16:08:54 +0530
- **Message:** removed unnecessary logs

**Files Changed:** 1 files
**Total Additions:** +0 lines
**Total Deletions:** -1 lines

**Files Modified:**
- `frontend/src/components/reporting/ExecutiveSummary.jsx` (+0/-1)

---

### Commit: 00c1cb52

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-12-22 14:51:10 +0530
- **Message:** Enhance AI Overview generation and executive summary updates in dashboard link operations

**Description:**
```
- Implemented automatic generation of AI Overview and executive summaries during dashboard link creation and updates, ensuring the latest metrics are reflected.
- Added error handling to log issues without failing the request, maintaining user experience.
- Introduced auto-generated link names and descriptions based on date ranges and creator information in the ReportingDashboard component, improving usability.
- Updated the UI to support new features, including a loading state during AI overview generation and improved form handling for link creation and editing.
```

**Files Changed:** 2 files
**Total Additions:** +331 lines
**Total Deletions:** -95 lines

**Files Modified:**
- `app/api/data.py` (+90/-0)
- `frontend/src/components/ReportingDashboard.jsx` (+241/-95)

---

### Commit: fa801c8f

- **Author:** Satvik Kushwaha (satvik@Satviks-Mac-mini.local)
- **Date:** 2025-12-22 16:00:10 +0530
- **Message:** badge display on success only + disclaimer added

**Files Changed:** 1 files
**Total Additions:** +35 lines
**Total Deletions:** -7 lines

**Files Modified:**
- `frontend/src/components/reporting/ExecutiveSummary.jsx` (+35/-7)

---

### Commit: f7fab847

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-12-22 14:51:10 +0530
- **Message:** Enhance AI Overview generation and executive summary updates in dashboard link operations

**Description:**
```
- Implemented automatic generation of AI Overview and executive summaries during dashboard link creation and updates, ensuring the latest metrics are reflected.
- Added error handling to log issues without failing the request, maintaining user experience.
- Introduced auto-generated link names and descriptions based on date ranges and creator information in the ReportingDashboard component, improving usability.
- Updated the UI to support new features, including a loading state during AI overview generation and improved form handling for link creation and editing.
```

**Files Changed:** 2 files
**Total Additions:** +331 lines
**Total Deletions:** -95 lines

**Files Modified:**
- `app/api/data.py` (+90/-0)
- `frontend/src/components/ReportingDashboard.jsx` (+241/-95)

---

### Commit: 1c88d857

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-12-22 12:42:39 +0530
- **Message:** Refactor query client import path in App component

**Description:**
```
- Updated the import statement for the query client in `App.jsx` to reflect its new location in the `hooks` directory, improving project structure and maintainability.
```

**Files Changed:** 1 files
**Total Additions:** +1 lines
**Total Deletions:** -1 lines

**Files Modified:**
- `frontend/src/App.jsx` (+1/-1)

---

### Commit: 41361938

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-12-22 12:41:08 +0530
- **Message:** Add query client configuration for React Query

**Description:**
```
- Introduced a new `queryClient.js` file to create and configure a React Query client with default options.
- Set default query options including stale time, garbage collection time, retry settings, and refetch behaviors to enhance data management and user experience.
- Established a structured approach for handling queries and mutations, improving the overall data fetching strategy in the frontend.
```

**Files Changed:** 1 files
**Total Additions:** +33 lines
**Total Deletions:** -0 lines

**Files Modified:**
- `frontend/src/hooks/queryClient.js` (+33/-0)

---

## 2025-12-19

### Commit: 1252142f

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-12-19 04:40:11 +0000
- **Message:** Refactor triggers in migration files for sync jobs, brand KPI selections, and clients

**Description:**
```
- Removed existing triggers before creating new ones for `sync_jobs`, `brand_kpi_selections`, and `clients` to ensure proper functionality.
- Updated migration scripts to maintain database integrity and prevent conflicts with existing triggers.
```

**Files Changed:** 4 files
**Total Additions:** +5 lines
**Total Deletions:** -0 lines

**Files Modified:**
- `migrations/v15__create_clients_table.sql` (+1/-0)
- `migrations/v21__add_client_id_to_brand_kpi_selections.sql` (+2/-0)
- `migrations/v8__create_sync_jobs_table.sql` (+1/-0)
- `migrations/v9__create_brand_kpi_selections_table.sql` (+1/-0)

---

## 2025-12-18

### Commit: 94e93218

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-12-18 21:47:40 +0530
- **Message:** Enhance overall overview generation in ReportingDashboard

**Description:**
```
- Updated the `generate_overall_overview` function to include fetching Scrunch data separately, improving KPI completeness.
- Introduced structured data organization for KPIs and charts, enhancing clarity in the generated overview.
- Implemented a refresh button in the ReportingDashboard to reload data and regenerate the overview, ensuring up-to-date information.
- Enhanced client and brand ID tracking to prevent stale data when switching between clients or brands.
- Improved handling of executive summaries, ensuring they are updated correctly based on the current client context.
```

**Files Changed:** 2 files
**Total Additions:** +467 lines
**Total Deletions:** -84 lines

**Files Modified:**
- `app/api/openai.py` (+191/-21)
- `frontend/src/components/ReportingDashboard.jsx` (+276/-63)

---

### Commit: e09d727d

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-12-18 20:19:57 +0530
- **Message:** Add show_change_period feature to dashboard links

**Description:**
```
- Introduced a new `show_change_period` field in the `DashboardLinkRequest` and `DashboardLinkUpdateRequest` models to manage per-section flags for displaying change period indicators.
- Updated the `DashboardLinkKPISelection` model to include the `show_change_period` column, allowing storage of these flags in the database.
- Enhanced the Supabase service methods to handle the new `show_change_period` data during dashboard link operations.
- Modified the ReportingDashboard component to support user interaction with the change period flags, including state management and UI updates.
- Added a migration script to update the database schema for the new `show_change_period` feature, ensuring backward compatibility and data integrity.
```

**Files Changed:** 5 files
**Total Additions:** +1625 lines
**Total Deletions:** -486 lines

**Files Modified:**
- `app/api/data.py` (+5/-0)
- `app/db/models.py` (+1/-0)
- `app/services/supabase_service.py` (+50/-14)
- `frontend/src/components/ReportingDashboard.jsx` (+1557/-472)
- `migrations/v28__add_show_change_period_to_kpi_selections.sql` (+12/-0)

---

### Commit: d0980092

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-12-18 16:39:21 +0530
- **Message:** Add endpoint to list all dashboard links and enhance Supabase service for optimized data retrieval

**Description:**
```
- Introduced a new API endpoint `/data/dashboard-links` to list all dashboard links across clients, optimized for bulk loading.
- Enhanced the `SupabaseService` with a method to retrieve all dashboard links in a single optimized query, including related client and KPI selection data.
- Updated the frontend to load all dashboard links in parallel with client data, improving performance and user experience.
- Added tracking metrics dialog in the `DashboardLinksManagement` component for better insights into link performance.
```

**Files Changed:** 4 files
**Total Additions:** +381 lines
**Total Deletions:** -88 lines

**Files Modified:**
- `app/api/data.py` (+11/-0)
- `app/services/supabase_service.py` (+81/-1)
- `frontend/src/components/DashboardLinksManagement.jsx` (+283/-87)
- `frontend/src/services/api.js` (+6/-0)

---

### Commit: 500e9bff

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-12-18 16:12:25 +0530
- **Message:** Enhance executive summary feature in dashboard links

**Description:**
```
- Added `executive_summary` field to the `DashboardLink` model, allowing storage of structured JSON data for performance briefs.
- Updated API endpoints and services to support retrieval and upsertion of executive summaries for dashboard links.
- Introduced a new `ExecutiveSummary` component in the frontend for displaying executive summaries, enhancing user experience with structured insights.
- Improved data handling in the ReportingDashboard to load and generate executive summaries based on available dashboard data.
- Implemented validation for executive summary structure to ensure data integrity and consistency.
- Added migration script to update the database schema for executive summary support.
```

**Files Changed:** 9 files
**Total Additions:** +1358 lines
**Total Deletions:** -612 lines

**Files Modified:**
- `app/api/data.py` (+8/-3)
- `app/api/openai.py` (+206/-22)
- `app/db/models.py` (+1/-0)
- `app/services/openai_client.py` (+7/-2)
- `app/services/supabase_service.py` (+81/-7)
- `frontend/src/components/ReportingDashboard.jsx` (+747/-578)
- `frontend/src/components/reporting/ExecutiveSummary.jsx` (+290/-0)
- `frontend/src/services/api.js` (+2/-0)
- `migrations/v27__add_executive_summary_to_dashboard_links.sql` (+16/-0)

---

### Commit: cb839b1a

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-12-18 12:51:20 +0530
- **Message:** Add performance metrics KPI selection feature and update related components

**Description:**
```
- Introduced a new configuration file for KPI selections, allowing independent selection of performance metrics KPIs for the "All Performance Metrics" summary section.
- Updated the database schema to include `selected_performance_metrics_kpis` in relevant tables, enabling storage of these selections.
- Enhanced API endpoints and data models to support the new performance metrics KPI feature, ensuring proper handling in both client and server interactions.
- Modified frontend components to accommodate the new KPI selections, including updates to the DashboardLinksManagement and ReportingDashboard components for better user experience and data display.
- Improved error handling and loading states in the login process to enhance user feedback during authentication.
- Refactored various service functions to streamline the management of KPI selections and improve overall code maintainability.
```

**Files Changed:** 10 files
**Total Additions:** +612 lines
**Total Deletions:** -237 lines

**Files Modified:**
- `app/api/data.py` (+21/-1)
- `app/db/models.py` (+2/-0)
- `app/services/supabase_service.py` (+22/-6)
- `frontend/src/components/DashboardLinksManagement.jsx` (+45/-69)
- `frontend/src/components/Login.jsx` (+14/-7)
- `frontend/src/components/ReportingDashboard.jsx` (+236/-63)
- `frontend/src/contexts/AuthContext.jsx` (+69/-70)
- `frontend/src/services/api.js` (+92/-21)
- `kpi_selector_config` (+92/-0)
- `migrations/v26__add_performance_metrics_kpis.sql` (+19/-0)

---

### Commit: 64c52dc2

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-12-18 11:20:48 +0530
- **Message:** Implement dashboard link management features and enhance tracking capabilities

**Description:**
```
- Added new API endpoints for creating, updating, deleting, and tracking dashboard links, including support for KPI selections and metrics.
- Introduced a new DashboardLinksManagement component in the frontend for managing dashboard links, including filtering and editing functionalities.
- Enhanced the SupabaseService to handle dashboard link operations and track link opens with user metadata.
- Updated database schema to include new tables for tracking link opens and storing KPI selections, improving data organization and retrieval.
- Improved date handling and validation for dashboard links, ensuring accurate management of expiration dates and visibility settings.
```

**Files Changed:** 15 files
**Total Additions:** +2239 lines
**Total Deletions:** -439 lines

**Files Modified:**
- `app/api/data.py` (+363/-18)
- `app/api/openai.py` (+7/-6)
- `app/db/models.py` (+43/-0)
- `app/services/supabase_service.py` (+426/-12)
- `frontend/src/App.jsx` (+2/-0)
- `frontend/src/components/ClientManagement.jsx` (+2/-0)
- `frontend/src/components/DashboardLinksManagement.jsx` (+798/-0)
- `frontend/src/components/Layout.jsx` (+3/-0)
- `frontend/src/components/PublicReportingDashboard.jsx` (+9/-0)
- `frontend/src/components/ReportingDashboard.jsx` (+438/-391)
- `frontend/src/services/api.js` (+46/-0)
- `migrations/v24__create_dashboard_link_tracking.sql` (+40/-0)
- `migrations/v25__create_dashboard_link_kpi_selections.sql` (+44/-0)
- `migrations/v6__add_brand_slug_trigger.sql` (+2/-0)
- `migrations/v7__create_audit_logs_table.sql` (+16/-12)

---

## 2025-12-16

### Commit: 134eae18

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-12-16 12:12:03 +0000
- **Message:** Update SQLAlchemy imports in data.py to include update function

**Description:**
```
- Added the update function to the SQLAlchemy imports in data.py, enabling support for update operations in future database interactions.
```

**Files Changed:** 1 files
**Total Additions:** +1 lines
**Total Deletions:** -1 lines

**Files Modified:**
- `app/api/data.py` (+1/-1)

---

### Commit: 5f3af500

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-12-16 15:51:54 +0530
- **Message:** Refactor soft delete client API endpoint for consistency

**Description:**
```
- Updated the softDeleteClient method to remove the '/soft-delete' suffix from the API endpoint, aligning it with the deleteClient method for a more consistent API design.
- Ensured that the response handling remains intact, returning the expected data format.
```

**Files Changed:** 1 files
**Total Additions:** +1 lines
**Total Deletions:** -1 lines

**Files Modified:**
- `frontend/src/services/api.js` (+1/-1)

---

### Commit: 8bef1eda

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-12-16 09:53:11 +0000
- **Message:** Add database backup configuration and scripts for automated weekly backups

**Description:**
```
- Introduced a new BACKUP_README.md file detailing the automated weekly backup process, including scheduling, retention, and restoration instructions.
- Added scripts for setting up a cron job to automate weekly backups and for executing the backup process, ensuring backups are created every Sunday at 5:00 AM IST.
- Enhanced the restore script to support Docker Compose, allowing for easier database restoration from backups.
- Implemented logging and cleanup mechanisms in the backup script to manage old backups and logs effectively.
- Created a sample backup file to demonstrate the backup process functionality.
```

**Files Changed:** 6 files
**Total Additions:** +399 lines
**Total Deletions:** -18 lines

**Files Modified:**
- `BACKUP_README.md` (+125/-0)
- `app/api/sync.py` (+41/-3)
- `daily_sync_job.py` (+7/-3)
- `scripts/restore_database_dump.sh` (+58/-12)
- `scripts/setup_weekly_backup_cron.sh` (+61/-0)
- `scripts/weekly_backup.sh` (+107/-0)

---

### Commit: 6699d2a4

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-12-16 14:52:59 +0530
- **Message:** Refactor StackedBarChart component for improved bar ordering and corner rounding

**Description:**
```
- Updated the bar configuration in the StackedBarChart to reverse the order of bars, ensuring that good rankings (green) appear on top and bad rankings (red) at the bottom.
- Enhanced the rendering logic to apply rounded corners to the top and bottom bars, improving the visual presentation of the chart.
- Commented out unused Box component in ReportingDashboard for cleaner code.
```

**Files Changed:** 2 files
**Total Additions:** +34 lines
**Total Deletions:** -22 lines

**Files Modified:**
- `frontend/src/components/ReportingDashboard.jsx` (+2/-2)
- `frontend/src/components/reporting/charts/StackedBarChart.jsx` (+32/-20)

---

## 2025-12-12

### Commit: 61f8760d

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-12-12 13:08:41 +0530
- **Message:** Refactor Supabase client initialization for storage operations to use service role key

**Description:**
```
- Updated the upload and delete functions for brand and client logos to utilize a Supabase client with a service role key, allowing for bypassing Row Level Security (RLS) during storage operations.
- Introduced a new method to create the Supabase service role client, ensuring secure access for storage tasks.
- Enhanced configuration to include a service role key in the environment settings for improved security and functionality.
- Updated frontend components to reflect changes in logo URLs and improved layout styling for better user experience.
```

**Files Changed:** 10 files
**Total Additions:** +327 lines
**Total Deletions:** -133 lines

**Files Modified:**
- `app/api/data.py` (+14/-8)
- `app/core/config.py` (+1/-0)
- `app/core/database.py` (+34/-0)
- `frontend/src/components/Layout.jsx` (+4/-3)
- `frontend/src/components/Login.jsx` (+17/-2)
- `frontend/src/components/ReportingDashboard.jsx` (+104/-70)
- `frontend/src/components/reporting/ReportingDashboardHeader.jsx` (+2/-2)
- `frontend/src/components/reporting/SectionContainer.jsx` (+1/-1)
- `frontend/src/contexts/AuthContext.jsx` (+117/-30)
- `frontend/src/services/tokenRefresh.js` (+33/-17)

---

## 2025-12-10

### Commit: 848009c2

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-12-10 19:52:15 +0530
- **Message:** Enhance reporting dashboard data retrieval with improved query logic and date handling

**Description:**
```
- Implemented a debug query to assess available records by client_id and property_id, enhancing data accuracy.
- Refactored date handling to ensure proper date comparisons using SQLAlchemy's cast function for date objects.
- Improved fallback logic for querying daily traffic records, allowing for more robust data retrieval when client_id data is insufficient.
- Updated SupabaseService to prioritize property_id queries when significantly more records are available, optimizing performance.
- Enhanced logging throughout the data retrieval process to provide clearer insights into query results and fallback actions.
```

**Files Changed:** 4 files
**Total Additions:** +308 lines
**Total Deletions:** -79 lines

**Files Modified:**
- `app/api/data.py` (+243/-59)
- `app/services/supabase_service.py` (+62/-17)
- `frontend/src/components/KeywordsDashboard.jsx` (+1/-1)
- `frontend/src/components/ReportingDashboard.jsx` (+2/-2)

---

### Commit: de7c4860

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-12-10 18:51:23 +0530
- **Message:** Enhance data synchronization and reporting features with date range validation

**Description:**
```
- Updated sync endpoints to include optional start_date and end_date parameters, allowing for more flexible data synchronization.
- Implemented date format validation and range checks to ensure correct input for date parameters.
- Enhanced logging throughout the sync processes to provide clearer insights into operations, including date ranges being processed.
- Refactored the AgencyAnalyticsClient to default to the first day of the current month for date ranges if not specified, improving data retrieval accuracy.
- Updated background sync tasks to handle date parameters, ensuring consistency across all data sync operations.
```

**Files Changed:** 4 files
**Total Additions:** +488 lines
**Total Deletions:** -72 lines

**Files Modified:**
- `app/api/data.py` (+266/-33)
- `app/api/sync.py` (+152/-14)
- `app/services/agency_analytics_client.py` (+42/-18)
- `app/services/background_sync.py` (+28/-7)

---

### Commit: c404dcba

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-12-10 14:55:23 +0530
- **Message:** Fix title typo in API and update frontend dashboard title for consistency; add Sync Date Parameters Analysis documentation

**Description:**
```
- Corrected the title from "McRAE's" to "MacRAE's" in main.py and index.html for brand consistency.
- Introduced a new documentation file, SYNC_DATE_PARAMETERS_ANALYSIS.md, detailing the behavior of sync endpoints regarding date parameters and their default values, enhancing clarity for future development and deployment.
```

**Files Changed:** 5 files
**Total Additions:** +307 lines
**Total Deletions:** -90 lines

**Files Modified:**
- `SYNC_DATE_PARAMETERS_ANALYSIS.md` (+154/-0)
- `app/api/data.py` (+145/-82)
- `frontend/index.html` (+1/-1)
- `frontend/src/components/ReportingDashboard.jsx` (+6/-6)
- `main.py` (+1/-1)

---

### Commit: f0421688

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-12-10 14:34:20 +0530
- **Message:** Enhance reporting dashboard with date range filtering and keyword ranking calculations

**Description:**
```
- Updated the get_reporting_dashboard function to include date range parameters for improved keyword ranking analysis.
- Implemented aggregation of keyword rankings and search volumes for both current and previous periods, allowing for better performance comparisons.
- Enhanced logging to provide detailed insights into the processing of campaigns and keyword metrics.
- Refactored date handling in the API to ensure proper validation and normalization of date inputs.
- Updated the KeywordsDashboard component to accept start and end date props, improving flexibility in date range selection for users.
```

**Files Changed:** 6 files
**Total Additions:** +4004 lines
**Total Deletions:** -2939 lines

**Files Modified:**
- `app/api/data.py` (+203/-25)
- `app/core/logging_config.py` (+8/-1)
- `frontend/src/components/KeywordsDashboard.jsx` (+31/-25)
- `frontend/src/components/ReportingDashboard.jsx` (+3654/-2872)
- `frontend/src/components/reporting/PromptsAnalyticsTable.jsx` (+105/-15)
- `frontend/src/services/api.js` (+3/-1)

---

### Commit: 0cfc7893

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-12-10 11:54:35 +0530
- **Message:** Implement debug logging enhancements across frontend components

**Description:**
```
- Introduced a centralized debug logging utility to replace console.error and console.log statements, improving consistency in error handling and logging.
- Updated various components to utilize debugLog, debugWarn, and debugError functions for better control over logging output based on the VITE_DEBUG_LOG environment variable.
- Added a new environment variable in docker-compose.yml to enable debug logging during development.
- Enhanced error handling in API calls and component lifecycle methods to provide clearer feedback on issues encountered during data fetching and processing.
```

**Files Changed:** 22 files
**Total Additions:** +120 lines
**Total Deletions:** -87 lines

**Files Modified:**
- `docker-compose.yml` (+1/-1)
- `frontend/src/components/AgencyAnalytics.jsx` (+5/-4)
- `frontend/src/components/AuditLogs.jsx` (+2/-1)
- `frontend/src/components/BrandAnalytics.jsx` (+2/-1)
- `frontend/src/components/BrandAnalyticsDetail.jsx` (+8/-7)
- `frontend/src/components/BrandDetail.jsx` (+3/-2)
- `frontend/src/components/BrandsList.jsx` (+2/-1)
- `frontend/src/components/ClientManagement.jsx` (+8/-7)
- `frontend/src/components/ClientsList.jsx` (+2/-1)
- `frontend/src/components/PublicReportingDashboard.jsx` (+3/-2)
- `frontend/src/components/ReportingDashboard.jsx` (+37/-36)
- `frontend/src/components/SyncPanel.jsx` (+2/-1)
- `frontend/src/components/SyncStatusIndicator.jsx` (+3/-2)
- `frontend/src/components/reporting/PromptsAnalyticsTable.jsx` (+2/-1)
- `frontend/src/components/reporting/charts/ScrunchVisualizations.jsx` (+2/-1)
- `frontend/src/contexts/AuthContext.jsx` (+2/-1)
- `frontend/src/contexts/SyncStatusContext.jsx` (+2/-1)
- `frontend/src/contexts/WebSocketContext.jsx` (+9/-8)
- `frontend/src/hooks/useResourceSubscription.js` (+3/-2)
- `frontend/src/services/api.js` (+2/-1)
- `frontend/src/services/tokenRefresh.js` (+7/-6)
- `frontend/src/utils/debug.js` (+13/-0)

---

### Commit: 07cb9ade

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-12-10 11:21:35 +0530
- **Message:** Enhance date filtering and keyword management in dashboards

**Description:**
```
- Added start_date and end_date parameters to the get_prompts and SupabaseService methods, allowing for flexible date range filtering.
- Implemented date validation logic to ensure correct date formats and ranges in the API.
- Updated KeywordsDashboard to support location filtering and sorting based on user-selected criteria, improving user experience.
- Refactored reporting components to utilize aggregated keyword data, enhancing the presentation of keyword performance metrics.
- Moved the Top Keywords Ranking chart into the Keywords section for better organization and visibility.
```

**Files Changed:** 4 files
**Total Additions:** +303 lines
**Total Deletions:** -139 lines

**Files Modified:**
- `app/api/data.py` (+161/-77)
- `app/services/supabase_service.py` (+27/-2)
- `frontend/src/components/KeywordsDashboard.jsx` (+68/-15)
- `frontend/src/components/ReportingDashboard.jsx` (+47/-45)

---

## 2025-12-09

### Commit: b6d8d0cc

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-12-09 17:28:11 +0530
- **Message:** Enhance reporting dashboard with date range flexibility and KPI management

**Description:**
```
- Added support for alias parameters `from` and `to` in the reporting dashboard API, allowing users to specify date ranges more intuitively.
- Implemented logic to map alias parameters to canonical start and end dates, improving user experience.
- Enhanced the response payload to gracefully handle cases with no data available for the selected date range, providing clear messaging.
- Updated frontend components to utilize new KPI selections, allowing for customizable visibility of key performance indicators in the KeywordsDashboard.
- Improved sorting and pagination logic in the KeywordsDashboard for better data presentation and user interaction.
- Refactored date handling in various components to ensure consistency across the application.
```

**Files Changed:** 5 files
**Total Additions:** +464 lines
**Total Deletions:** -177 lines

**Files Modified:**
- `app/api/data.py` (+252/-90)
- `frontend/src/components/KeywordsDashboard.jsx` (+131/-70)
- `frontend/src/components/PublicReportingDashboard.jsx` (+3/-2)
- `frontend/src/components/ReportingDashboard.jsx` (+76/-15)
- `frontend/src/services/api.js` (+2/-0)

---

### Commit: 5db241ff

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-12-09 14:32:24 +0530
- **Message:** Implement dashboard link management and reporting date updates

**Description:**
```
- Added new API endpoints for creating, updating, and listing dashboard links associated with clients, allowing for shareable reporting links with specific date ranges.
- Introduced a new DashboardLink model in the database to store link details, including start and end dates, enablement status, and expiration.
- Enhanced client report date management by adding fields for report_start_date and report_end_date in the clients table, enabling better control over public dashboard data display.
- Updated frontend components to handle dashboard link retrieval and date range selection, improving user experience for public reporting dashboards.
- Implemented error handling for expired or disabled links, ensuring users receive appropriate feedback when accessing dashboard links.
- Added migration scripts to create the necessary database structure for dashboard links and report dates.
```

**Files Changed:** 10 files
**Total Additions:** +835 lines
**Total Deletions:** -63 lines

**Files Modified:**
- `app/api/data.py` (+361/-38)
- `app/db/models.py` (+24/-1)
- `app/services/supabase_service.py` (+153/-3)
- `frontend/src/components/PublicReportingDashboard.jsx` (+92/-8)
- `frontend/src/components/ReportingDashboard.jsx` (+128/-9)
- `frontend/src/services/api.js` (+24/-0)
- `ga4_token.json` (+3/-3)
- `manage_migrations.py` (+1/-1)
- `migrations/v22__add_report_dates_to_clients.sql` (+15/-0)
- `migrations/v23__create_dashboard_links.sql` (+34/-0)

---

## 2025-12-08

### Commit: f12fd8c0

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-12-08 19:02:36 +0530
- **Message:** Update daily sync job to run at 11:30 PM IST and enhance sync functionality

**Description:**
```
- Changed the daily sync job schedule from 12:00 AM IST to 11:30 PM IST, aligning with cron configuration.
- Updated sync processes to include AgencyAnalytics, GA4, and Scrunch AI data, all operating in "complete" mode to ensure comprehensive data synchronization.
- Enhanced error handling for sync operations, including timeout and connection errors, to improve reliability.
- Added detailed logging for async job initiation and completion status, providing better visibility into sync operations.
- Updated documentation to reflect changes in sync job scheduling and functionality.
```

**Files Changed:** 25 files
**Total Additions:** +2283 lines
**Total Deletions:** -254 lines

**Files Modified:**
- `Dockerfile.backend` (+7/-1)
- `QUICK_CRON_CHECK.md` (+45/-0)
- `app/api/data.py` (+74/-1)
- `app/api/sync.py` (+19/-5)
- `app/services/background_sync.py` (+60/-15)
- `check_and_setup_cron_docker.sh` (+219/-0)
- `daily_sync_job.py` (+136/-36)
- `docker-compose.yml` (+20/-1)
- `docker-entrypoint.sh` (+49/-0)
- `docker-help.md` (+200/-0)
- `docs/CHECK_SYNC_JOBS.md` (+218/-0)
- `docs/DOCKER_CRON_SETUP.md` (+291/-0)
- `docs/USER_GUIDE.md` (+116/-0)
- `frontend/src/components/ClientsList.jsx` (+7/-3)
- `frontend/src/components/Dashboard.jsx` (+78/-0)
- `frontend/src/components/PublicReportingDashboard.jsx` (+56/-2)
- `frontend/src/components/ReportingDashboard.jsx` (+197/-35)
- `frontend/src/components/SyncPanel.jsx` (+209/-103)
- `frontend/src/contexts/AuthContext.jsx` (+6/-0)
- `frontend/src/services/api.js` (+25/-5)
- `frontend/src/services/tokenRefresh.js` (+12/-0)
- `ga4_token.json` (+3/-3)
- `setup_daily_sync_linux.sh` (+37/-10)
- `setup_daily_sync_windows.ps1` (+87/-34)
- `validate_cron_docker.sh` (+112/-0)

---

## 2025-12-04

### Commit: d4b10824

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-12-04 19:59:19 +0530
- **Message:** Refactor signup process to return simplified response without tokens

**Description:**
```
- Introduced SignUpResponseV2 model to standardize signup responses, providing success status, message, user ID, and email.
- Updated signup_v2 endpoint to return a success message instead of access and refresh tokens, requiring users to sign in separately after account creation.
- Modified frontend components to handle new response structure, displaying appropriate success messages and redirecting users accordingly.
- Removed token storage logic from the signup process to streamline user account creation.
```

**Files Changed:** 4 files
**Total Additions:** +43 lines
**Total Deletions:** -60 lines

**Files Modified:**
- `app/api/auth_v2.py` (+15/-18)
- `frontend/src/components/CreateUser.jsx` (+10/-13)
- `frontend/src/components/Signup.jsx` (+7/-5)
- `frontend/src/contexts/AuthContext.jsx` (+11/-24)

---

### Commit: 8497d260

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-12-04 19:35:16 +0530
- **Message:** Add database dump and restore scripts, along with comprehensive documentation

**Description:**
```
- Introduced scripts for creating and restoring database dumps, enhancing backup and recovery processes.
- Added a new guide for database dump creation and restoration, detailing methods and best practices.
- Updated .gitignore to exclude unencrypted dump files and added notes for handling password-protected ZIP files.
- Created README_DUMP.md for quick reference on creating password-protected dumps for remote servers.
- Included a sample password-protected dump file for demonstration purposes.
```

**Files Changed:** 7 files
**Total Additions:** +633 lines
**Total Deletions:** -0 lines

**Files Modified:**
- `.gitignore` (+8/-0)
- `DATABASE_DUMP_GUIDE.md` (+257/-0)
- `README_DUMP.md` (+45/-0)
- `scripts/create_database_dump.sh` (+90/-0)
- `scripts/create_dump_for_remote.sh` (+66/-0)
- `scripts/create_password_protected_dump.sh` (+70/-0)
- `scripts/restore_database_dump.sh` (+97/-0)

---

### Commit: 57e67aa4

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-12-04 19:24:58 +0530
- **Message:** Enhance client-centric KPI selection management and reporting features

**Description:**
```
- Introduced client_id to the brand_kpi_selections table, allowing KPI selections to be stored per client instead of per brand, improving data management.
- Updated SupabaseService methods to support client-centric queries for KPI selections, ensuring compatibility with the new schema.
- Implemented new API endpoints for fetching and saving KPI selections based on client_id, enhancing user experience for client management.
- Refactored frontend components to utilize client-centric API methods, ensuring seamless integration with the updated backend.
- Improved error handling and loading states in ReportingDashboard and KeywordsDashboard for better user feedback during data operations.
- Added migration script to update existing records and ensure backward compatibility with brand_id.
```

**Files Changed:** 9 files
**Total Additions:** +838 lines
**Total Deletions:** -126 lines

**Files Modified:**
- `app/api/data.py` (+359/-26)
- `app/db/models.py` (+2/-1)
- `app/services/supabase_service.py` (+276/-14)
- `frontend/src/components/KeywordsDashboard.jsx` (+9/-8)
- `frontend/src/components/PublicReportingDashboard.jsx` (+3/-23)
- `frontend/src/components/ReportingDashboard.jsx` (+71/-19)
- `frontend/src/components/reporting/KPICard.jsx` (+56/-33)
- `frontend/src/services/api.js` (+25/-2)
- `migrations/v21__add_client_id_to_brand_kpi_selections.sql` (+37/-0)

---

### Commit: 9ce42b30

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-12-04 17:28:25 +0530
- **Message:** Refactor authentication and API integration for improved user management

**Description:**
```
- Updated authentication system to utilize a new `auth_v2` module, enhancing user and refresh token management.
- Replaced `get_current_user` with `get_current_user_v2` across multiple API endpoints for consistent user session handling.
- Improved error handling and graceful degradation in frontend components, particularly in the ReportingDashboard and PublicReportingDashboard, to manage scenarios with no data available.
- Adjusted pagination settings in the KeywordsDashboard for better user experience.
- Enhanced GA4 data sync processes to support client-centric data management, ensuring compatibility with the updated authentication system.
```

**Files Changed:** 14 files
**Total Additions:** +904 lines
**Total Deletions:** -217 lines

**Files Modified:**
- `app/api/audit.py` (+4/-4)
- `app/api/data.py` (+135/-50)
- `app/api/openai.py` (+14/-7)
- `app/api/sync.py` (+7/-7)
- `app/api/sync_jobs.py` (+4/-4)
- `app/api/websocket.py` (+33/-16)
- `app/services/background_sync.py` (+166/-78)
- `frontend/src/components/KeywordsDashboard.jsx` (+1/-1)
- `frontend/src/components/PublicReportingDashboard.jsx` (+39/-2)
- `frontend/src/components/ReportingDashboard.jsx` (+102/-15)
- `frontend/src/contexts/AuthContext.jsx` (+107/-7)
- `frontend/src/services/api.js` (+115/-23)
- `frontend/src/services/tokenRefresh.js` (+174/-0)
- `ga4_token.json` (+3/-3)

---

### Commit: e271e9d3

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-12-04 15:56:40 +0530
- **Message:** Add comprehensive Docker Compose commands reference and migration manager script

**Description:**
```
- Introduced a new `docker-help.md` file containing detailed Docker Compose commands for managing the MacRAE's Website Analytics application, covering service management, database operations, and troubleshooting.
- Added `manage_migrations.py` script to facilitate a Django-like migration system for PostgreSQL, allowing for easy execution and tracking of database migrations.
- Updated `ga4_token.json` with a new access token and expiration details.
- Enhanced various API endpoints to include database session management and improved error handling.
- Implemented soft delete functionality for clients, including a new `is_active` column in the clients table, with corresponding migrations.
- Added frontend components for client management, including a delete confirmation dialog and improved search functionality.
- Updated API services to support new client soft delete operations and adjusted filters for active clients in API requests.
```

**Files Changed:** 19 files
**Total Additions:** +1759 lines
**Total Deletions:** -446 lines

**Files Modified:**
- `app/api/audit.py` (+99/-64)
- `app/api/auth.py` (+18/-8)
- `app/api/auth_v2.py` (+10/-5)
- `app/api/data.py` (+157/-258)
- `app/api/openai.py` (+31/-11)
- `app/api/sync.py` (+12/-6)
- `app/db/models.py` (+2/-1)
- `app/services/agency_analytics_client.py` (+84/-17)
- `app/services/audit_logger.py` (+83/-24)
- `app/services/background_sync.py` (+67/-15)
- `app/services/supabase_service.py` (+72/-28)
- `docker-help.md` (+682/-0)
- `frontend/src/components/AgencyAnalytics.jsx` (+22/-3)
- `frontend/src/components/ClientsList.jsx` (+85/-1)
- `frontend/src/services/api.js` (+20/-2)
- `ga4_token.json` (+3/-3)
- `manage_migrations.py` (+272/-0)
- `migrations/v2/005_add_is_active_to_clients.sql` (+20/-0)
- `migrations/v20__add_is_active_to_clients.sql` (+20/-0)

---

## 2025-12-03

### Commit: e74bc3f6

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-12-03 16:20:13 +0530
- **Message:** Enhance v2 authentication system: Introduce new user and refresh token management features, including user creation, password hashing, and token cleanup. Update database schema with users and refresh tokens tables, and implement JWT utilities for secure token handling. Refactor Supabase service to utilize SQLAlchemy for database operations, ensuring compatibility with local PostgreSQL. Add migration scripts for database setup and management.

**Files Changed:** 38 files
**Total Additions:** +8426 lines
**Total Deletions:** -2394 lines

**Files Modified:**
- `OPTIMIZATION_SUMMARY.md` (+192/-0)
- `app/api/audit.py` (+90/-50)
- `app/api/auth_v2.py` (+436/-0)
- `app/api/data.py` (+1809/-1205)
- `app/api/database.py` (+55/-45)
- `app/api/sync.py` (+41/-49)
- `app/core/config.py` (+65/-6)
- `app/core/database.py` (+20/-9)
- `app/core/jwt_utils.py` (+116/-0)
- `app/core/password_utils.py` (+59/-0)
- `app/db/database.py` (+53/-6)
- `app/db/models.py` (+569/-2)
- `app/services/background_sync.py` (+45/-9)
- `app/services/scrunch_client.py` (+51/-3)
- `app/services/supabase_service.py` (+2218/-898)
- `app/services/sync_job_service.py` (+153/-58)
- `app/services/user_service.py` (+264/-0)
- `docker-compose.yml` (+8/-6)
- `frontend/assets/site.webmanifest` (+1/-0)
- `frontend/index.html` (+4/-1)
- `frontend/src/components/ClientManagement.jsx` (+48/-18)
- `frontend/src/components/ClientsList.jsx` (+147/-10)
- `frontend/src/components/ReportingDashboard.jsx` (+1/-1)
- `frontend/src/components/SyncPanel.jsx` (+2/-2)
- `frontend/src/services/api.js` (+11/-2)
- `ga4_token.json` (+3/-3)
- `main.py` (+32/-11)
- `migrations/v1/README.md` (+137/-0)
- `migrations/v1/complete_schema.sql` (+982/-0)
- `migrations/{v18__add_selected_charts_to_brand_kpi_selections.sql => v19__add_selected_charts_to_brand_kpi_selections.sql}` (+0/-0)
- `migrations/v2/001_users_and_refresh_tokens.sql` (+60/-0)
- `migrations/v2/002_update_agency_analytics_integer_to_bigint.sql` (+71/-0)
- `migrations/v2/003_drop_keyword_id_date_unique_constraint.sql` (+17/-0)
- `migrations/v2/004_add_performance_indexes.sql` (+79/-0)
- `requirements.txt` (+1/-0)
- `scripts/README.md` (+175/-0)
- `scripts/create_user.py` (+58/-0)
- `scripts/db_helper.sh` (+353/-0)

---

## 2025-12-02

### Commit: 18787d07

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-12-02 15:35:59 +0000
- **Message:** Enhance authentication error handling: Add specific checks for email confirmation errors in the signin process, providing detailed user messages and technical information. Update exception handling to include new error mappings for unconfirmed emails. Improve frontend alert components for better error message display and word wrapping in Signup and Toast contexts.

**Files Changed:** 4 files
**Total Additions:** +50 lines
**Total Deletions:** -4 lines

**Files Modified:**
- `app/api/auth.py` (+15/-2)
- `app/core/exceptions.py` (+13/-1)
- `frontend/src/components/Signup.jsx` (+14/-1)
- `frontend/src/contexts/ToastContext.jsx` (+8/-0)

---

## 2025-12-01

### Commit: 02a9fc51

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-12-01 19:12:58 +0530
- **Message:** Enhance campaign analytics and reporting features: Implement pagination and search functionality for campaign rankings and keyword ranking summaries in the API. Update frontend components to support new pagination and search capabilities, improving user experience in the AgencyAnalytics and ReportingDashboard. Introduce AuditLogs component for tracking user actions and data sync operations, with filtering and pagination options. Update API services to handle audit log retrieval and statistics. Add migration for new selected_charts field in brand_kpi_selections table.

**Files Changed:** 13 files
**Total Additions:** +1680 lines
**Total Deletions:** -732 lines

**Files Modified:**
- `app/api/data.py` (+85/-25)
- `app/api/openai.py` (+3/-2)
- `app/api/sync.py` (+2/-2)
- `frontend/src/App.jsx` (+2/-0)
- `frontend/src/components/AgencyAnalytics.jsx` (+361/-186)
- `frontend/src/components/AuditLogs.jsx` (+423/-0)
- `frontend/src/components/ClientsList.jsx` (+75/-25)
- `frontend/src/components/Dashboard.jsx` (+7/-7)
- `frontend/src/components/DataView.jsx` (+16/-9)
- `frontend/src/components/Layout.jsx` (+17/-12)
- `frontend/src/components/ReportingDashboard.jsx` (+620/-459)
- `frontend/src/services/api.js` (+59/-5)
- `migrations/v18__add_selected_charts_to_brand_kpi_selections.sql` (+10/-0)

---

### Commit: 04e1ebe1

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-12-01 09:12:16 +0000
- **Message:** Add scripts for DNS propagation check and SSL setup, and create migration guide for transitioning from Supabase to local PostgreSQL. Update docker-compose to include PostgreSQL service and adjust environment variables for local database operations.

**Files Changed:** 5 files
**Total Additions:** +507 lines
**Total Deletions:** -9 lines

**Files Modified:**
- `DATABASE_MIGRATION_GUIDE.md` (+257/-0)
- `check_dns_and_setup_ssl.sh` (+67/-0)
- `docker-compose.yml` (+33/-9)
- `migrate_to_local_db.sh` (+92/-0)
- `wait_for_dns_and_setup_ssl.sh` (+58/-0)

---

## 2025-11-28

### Commit: fea6b564

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-11-28 13:39:56 +0000
- **Message:** Update docker-compose configuration: Disable DEBUG mode for production and modify healthcheck command to ensure proper exit status handling.

**Files Changed:** 5 files
**Total Additions:** +1019 lines
**Total Deletions:** -2 lines

**Files Modified:**
- `DEPLOYMENT.md` (+205/-0)
- `QUICK_REFERENCE.md` (+61/-0)
- `docker-compose.yml` (+2/-2)
- `get-docker.sh` (+720/-0)
- `setup_ssl.sh` (+31/-0)

---

### Commit: edd4d8c2

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-11-28 19:04:33 +0530
- **Message:** Implement campaign linking and unlinking features in client management: Add API endpoints for linking and unlinking Agency Analytics campaigns to clients, including pagination and search functionality for campaigns. Enhance the ClientManagement component to support campaign selection, linking, and un-linking, improving user experience with loading states and search capabilities. Update API service methods to accommodate new campaign management features.

**Files Changed:** 3 files
**Total Additions:** +396 lines
**Total Deletions:** -52 lines

**Files Modified:**
- `app/api/data.py` (+182/-38)
- `frontend/src/components/ClientManagement.jsx` (+183/-12)
- `frontend/src/services/api.js` (+31/-2)

---

### Commit: 3bd30cb3

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-11-28 18:02:56 +0530
- **Message:** Add KeywordsDashboard component and API integration for client keywords: Implement a new KeywordsDashboard to display and filter keywords for clients, including advanced filtering options and pagination. Enhance API endpoints for fetching client keywords, keyword rankings over time, and summary KPIs. Update routing in App.jsx to include the new dashboard and integrate it into the ReportingDashboard for comprehensive keyword analytics.

**Files Changed:** 10 files
**Total Additions:** +2208 lines
**Total Deletions:** -43 lines

**Files Modified:**
- `app/api/data.py` (+955/-0)
- `frontend/src/App.jsx` (+9/-0)
- `frontend/src/components/KeywordsDashboard.jsx` (+830/-0)
- `frontend/src/components/ReportingDashboard.jsx` (+118/-40)
- `frontend/src/components/SyncPanel.jsx` (+1/-1)
- `frontend/src/components/SyncStatusIndicator.jsx` (+1/-1)
- `frontend/src/components/reporting/charts/StackedBarChart.jsx` (+207/-0)
- `frontend/src/contexts/SyncStatusContext.jsx` (+1/-1)
- `frontend/src/hooks/queryKeys.js` (+8/-0)
- `frontend/src/services/api.js` (+78/-0)

---

### Commit: 455ad4ac

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-11-28 15:55:38 +0530
- **Message:** Enhance ReportingDashboard with loading states and PromptsAnalyticsTable: Introduce loading indicators for public reporting, including random captions during data fetch. Add PromptsAnalyticsTable component for detailed analytics, and refactor KPIGrid and KPICard to support dynamic source labels. Improve user experience with loading animations and better data presentation.

**Files Changed:** 5 files
**Total Additions:** +758 lines
**Total Deletions:** -42 lines

**Files Modified:**
- `frontend/src/components/ReportingDashboard.jsx` (+147/-38)
- `frontend/src/components/reporting/KPICard.jsx` (+4/-4)
- `frontend/src/components/reporting/KPIGrid.jsx` (+1/-0)
- `frontend/src/components/reporting/PromptsAnalyticsTable.jsx` (+531/-0)
- `frontend/src/components/reporting/Sparkline.jsx` (+75/-0)

---

### Commit: fc6658a5

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-11-28 12:24:09 +0530
- **Message:** Refactor GA4 data sync and API integration to support client-centric model: Update sync processes to utilize client_id instead of brand_id, enhancing data handling for GA4 metrics. Modify API endpoints and database structures to accommodate client-centric data management, ensuring backward compatibility with existing brand_id references. Introduce new migrations for updating GA4 tables and improve frontend components for client management and reporting dashboards, including pagination and keyword display enhancements.

**Files Changed:** 14 files
**Total Additions:** +2009 lines
**Total Deletions:** -589 lines

**Files Modified:**
- `app/api/data.py` (+327/-31)
- `app/api/openai.py` (+183/-9)
- `app/api/sync.py` (+4/-4)
- `app/services/background_sync.py` (+76/-74)
- `app/services/openai_client.py` (+1/-1)
- `app/services/supabase_service.py` (+383/-106)
- `daily_sync_job.py` (+3/-2)
- `frontend/src/components/BrandsList.jsx` (+68/-173)
- `frontend/src/components/ClientManagement.jsx` (+373/-125)
- `frontend/src/components/ClientsList.jsx` (+25/-0)
- `frontend/src/components/ReportingDashboard.jsx` (+354/-51)
- `frontend/src/components/reporting/ReportingDashboardHeader.jsx` (+18/-0)
- `frontend/src/services/api.js` (+71/-13)
- `migrations/v18__add_client_id_to_ga4_tables.sql` (+123/-0)

---

## 2025-11-27

### Commit: 71c4c672

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-11-27 14:47:46 +0530
- **Message:** Implement WebSocket support and version tracking for optimistic locking: Introduce a WebSocket API for real-time notifications, allowing clients to subscribe to updates on resources such as clients and brands. Enhance API endpoints to include versioning and last modified tracking for optimistic locking, ensuring data integrity during concurrent updates. Update frontend components to handle WebSocket connections and display notifications for resource changes, improving user experience and responsiveness.

**Files Changed:** 13 files
**Total Additions:** +1433 lines
**Total Deletions:** -46 lines

**Files Modified:**
- `app/api/data.py` (+259/-26)
- `app/api/openai.py` (+159/-1)
- `app/api/websocket.py` (+147/-0)
- `app/db/models.py` (+3/-1)
- `app/services/supabase_service.py` (+2/-0)
- `app/services/sync_job_service.py` (+46/-0)
- `app/services/websocket_manager.py` (+213/-0)
- `frontend/src/App.jsx` (+6/-3)
- `frontend/src/components/ClientManagement.jsx` (+129/-14)
- `frontend/src/contexts/WebSocketContext.jsx` (+163/-0)
- `frontend/src/hooks/useResourceSubscription.js` (+142/-0)
- `main.py` (+2/-1)
- `migrations/v17__add_version_tracking.sql` (+162/-0)

---

### Commit: 89d88e09

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-11-27 13:48:57 +0530
- **Message:** Add NotFound component and update routing in App.jsx: Introduce a new NotFound page for handling 404 errors and refactor routing structure to include Layout for each route. This enhances user experience by providing a clear navigation path when a page is not found.

**Files Changed:** 2 files
**Total Additions:** +90 lines
**Total Deletions:** -14 lines

**Files Modified:**
- `frontend/src/App.jsx` (+14/-14)
- `frontend/src/components/NotFound.jsx` (+76/-0)

---

### Commit: 5d669fe8

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-11-27 13:33:33 +0530
- **Message:** Enhance API and frontend integration for OpenAI: Introduce new OpenAI API client with endpoints for chat completions, text completions, and embeddings. Update FastAPI routes to include OpenAI functionalities and improve error handling. Refactor data fetching in ReportingDashboard to support public and admin views, ensuring compatibility with new client structures. Update environment configuration to require OpenAI API key and enhance Docker setup for seamless deployment.

**Files Changed:** 13 files
**Total Additions:** +622 lines
**Total Deletions:** -90 lines

**Files Modified:**
- `app/api/data.py` (+96/-22)
- `app/api/openai.py` (+155/-0)
- `app/core/config.py` (+14/-7)
- `app/services/openai_client.py` (+164/-0)
- `app/services/scrunch_client.py` (+5/-0)
- `docker-compose.yml` (+27/-2)
- `frontend/src/App.jsx` (+2/-2)
- `frontend/src/components/ClientsList.jsx` (+3/-2)
- `frontend/src/components/Layout.jsx` (+1/-1)
- `frontend/src/components/ReportingDashboard.jsx` (+64/-31)
- `frontend/src/components/SyncStatusIndicator.jsx` (+43/-12)
- `frontend/src/contexts/SyncStatusContext.jsx` (+46/-10)
- `main.py` (+2/-1)

---

### Commit: d5d3f878

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-11-27 11:21:45 +0530
- **Message:** Implement client management features: Add endpoints for uploading, deleting client logos, and managing client settings. Introduce new API methods for fetching client campaigns and updating client mappings. Enhance frontend components for client management, including a dedicated ClientsList and ClientManagement dialog for better user experience. Update database migrations to support client data storage and relationships.

**Files Changed:** 18 files
**Total Additions:** +4658 lines
**Total Deletions:** -629 lines

**Files Modified:**
- `app/api/data.py` (+1175/-512)
- `app/api/sync_jobs.py` (+49/-0)
- `app/services/background_sync.py` (+487/-9)
- `app/services/ga4_client.py` (+47/-8)
- `app/services/supabase_service.py` (+1033/-23)
- `app/services/sync_job_service.py` (+48/-0)
- `frontend/src/App.jsx` (+2/-0)
- `frontend/src/components/ClientManagement.jsx` (+734/-0)
- `frontend/src/components/ClientsList.jsx` (+499/-0)
- `frontend/src/components/Layout.jsx` (+3/-0)
- `frontend/src/components/ReportingDashboard.jsx` (+81/-69)
- `frontend/src/components/SyncStatusIndicator.jsx` (+54/-8)
- `frontend/src/hooks/queryKeys.js` (+11/-0)
- `frontend/src/services/api.js` (+85/-0)
- `migrations/v13__ga4_kpi_snapshots.sql` (+69/-0)
- `migrations/v14__ga4_additional_tables.sql` (+111/-0)
- `migrations/v15__create_clients_table.sql` (+156/-0)
- `migrations/v16__add_responses_composite_index.sql` (+14/-0)

---

## 2025-11-26

### Commit: 7c96a29f

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-11-26 19:21:21 +0530
- **Message:** Enhance reporting dashboard and API integration: Add detailed logging for campaign processing and KPI calculations in the reporting dashboard. Refactor data fetching to utilize automatic pagination for campaigns and improve error handling in the Agency Analytics client. Update Supabase service methods for optimized batch upserts and implement a new SQL migration for UUID-based brand slugs. Enhance frontend components with improved theme consistency and visualizations for better user experience.

**Files Changed:** 12 files
**Total Additions:** +1385 lines
**Total Deletions:** -400 lines

**Files Modified:**
- `app/api/data.py` (+29/-10)
- `app/core/config.py` (+7/-1)
- `app/services/agency_analytics_client.py` (+78/-18)
- `app/services/background_sync.py` (+187/-17)
- `app/services/supabase_service.py` (+129/-115)
- `frontend/src/components/Layout.jsx` (+19/-11)
- `frontend/src/components/PublicReportingDashboard.jsx` (+5/-0)
- `frontend/src/components/ReportingDashboard.jsx` (+648/-189)
- `frontend/src/components/reporting/constants.js` (+8/-6)
- `frontend/src/index.css` (+18/-6)
- `frontend/src/theme.js` (+175/-27)
- `migrations/v12__update_brand_slug_trigger_to_uuid.sql` (+82/-0)

---

### Commit: f80617d4

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-11-26 10:07:04 +0530
- **Message:** Integrate React Query for data management: Add hooks for fetching brands, prompts, responses, and sync status using React Query. Refactor components to utilize these hooks for improved data handling and performance. Introduce centralized query keys for consistent cache management across the application. Enhance BrandsList and Dashboard components to streamline data fetching and state management.

**Files Changed:** 11 files
**Total Additions:** +603 lines
**Total Deletions:** -182 lines

**Files Modified:**
- `frontend/package-lock.json` (+55/-0)
- `frontend/package.json` (+8/-7)
- `frontend/src/App.jsx` (+44/-38)
- `frontend/src/components/BrandsList.jsx` (+19/-56)
- `frontend/src/components/Dashboard.jsx` (+7/-24)
- `frontend/src/components/DataView.jsx` (+56/-57)
- `frontend/src/hooks/queryKeys.js` (+49/-0)
- `frontend/src/hooks/useBrands.js` (+191/-0)
- `frontend/src/hooks/useDashboard.js` (+97/-0)
- `frontend/src/hooks/useData.js` (+58/-0)
- `frontend/src/hooks/useSync.js` (+19/-0)

---

## 2025-11-25

### Commit: 3257e55d

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-11-25 18:33:43 +0530
- **Message:** Implement brand management features: Add endpoints for updating GA4 Property ID, linking and unlinking Agency Analytics campaigns, uploading and deleting brand logos, and updating brand themes. Enhance frontend components for managing brand settings, including logo uploads, theme customization, and campaign linking. Introduce database migrations for logo and theme storage in the brands table.

**Files Changed:** 12 files
**Total Additions:** +1533 lines
**Total Deletions:** -60 lines

**Files Modified:**
- `app/api/data.py` (+462/-1)
- `app/core/database.py` (+11/-3)
- `app/services/ga4_client.py` (+10/-1)
- `frontend/src/components/BrandManagement.jsx` (+721/-0)
- `frontend/src/components/BrandsList.jsx` (+96/-27)
- `frontend/src/components/PublicReportingDashboard.jsx` (+56/-10)
- `frontend/src/components/reporting/ReportingDashboardHeader.jsx` (+26/-11)
- `frontend/src/components/reporting/utils.js` (+4/-0)
- `frontend/src/contexts/SyncStatusContext.jsx` (+25/-7)
- `frontend/src/services/api.js` (+54/-0)
- `frontend/src/utils/roleUtils.js` (+46/-0)
- `migrations/v11__add_brand_logo_and_theme.sql` (+22/-0)

---

## 2025-11-24

### Commit: 934d94d7

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-11-24 19:25:03 +0530
- **Message:** Add KPI selection management for public reporting dashboard: Implement endpoints for fetching and saving KPI selections, allowing managers to control visibility of KPIs and sections in the public view. Update frontend components to load and display these selections, enhancing user experience and configurability. Introduce database migrations for storing KPI preferences and ensure backward compatibility with existing functionality.

**Files Changed:** 6 files
**Total Additions:** +620 lines
**Total Deletions:** -75 lines

**Files Modified:**
- `app/api/data.py` (+233/-6)
- `frontend/src/components/ReportingDashboard.jsx` (+318/-66)
- `frontend/src/components/reporting/charts/ScrunchVisualizations.jsx` (+3/-3)
- `frontend/src/services/api.js` (+18/-0)
- `migrations/v10__add_visible_sections_to_brand_kpi_selections.sql` (+10/-0)
- `migrations/v9__create_brand_kpi_selections_table.sql` (+38/-0)

---

### Commit: 95c48cb6

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-11-24 17:14:06 +0530
- **Message:** Enhance GA4 data logging and reporting calculations: Improve logging for GA4 API calls and responses in the reporting dashboard, including detailed change calculations for user metrics. Refactor data handling in Scrunch metrics to ensure brand ID filtering and accurate KPI calculations. Update frontend components for better display of KPI changes and integrate pagination for insights table.

**Files Changed:** 10 files
**Total Additions:** +1328 lines
**Total Deletions:** -1170 lines

**Files Modified:**
- `app/api/data.py` (+151/-29)
- `app/services/ga4_client.py` (+17/-0)
- `frontend/src/components/ReportingDashboard.jsx` (+718/-900)
- `frontend/src/components/reporting/ChartCard.jsx` (+5/-3)
- `frontend/src/components/reporting/KPICard.jsx` (+44/-55)
- `frontend/src/components/reporting/SectionContainer.jsx` (+1/-1)
- `frontend/src/components/reporting/charts/BarChart.jsx` (+12/-10)
- `frontend/src/components/reporting/charts/LineChart.jsx` (+12/-10)
- `frontend/src/components/reporting/charts/PieChart.jsx` (+102/-63)
- `frontend/src/components/reporting/charts/ScrunchVisualizations.jsx` (+266/-99)

---

### Commit: 820e0c42

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-11-24 11:47:33 +0530
- **Message:** Refactor ReportingDashboard and related components for improved structure and performance: Remove deprecated error handling in BrandsList, enhance the layout and responsiveness of SyncPanel, and introduce reusable ChartCard and SectionContainer components for better organization. Update constants for chart configurations and implement responsive design across various chart components. Streamline data handling in GA4SectionEnhanced for better clarity and maintainability.

**Files Changed:** 16 files
**Total Additions:** +2013 lines
**Total Deletions:** -8411 lines

**Files Modified:**
- `frontend/src/components/BrandsList.jsx` (+0/-16)
- `frontend/src/components/ReportingDashboard.backup.jsx` (+0/-366)
- `frontend/src/components/ReportingDashboard.jsx` (+556/-1864)
- `frontend/src/components/ReportingDashboard.old.jsx` (+0/-5401)
- `frontend/src/components/ReportingDashboard.refactored.jsx` (+0/-366)
- `frontend/src/components/SyncPanel.jsx` (+103/-19)
- `frontend/src/components/reporting/ChartCard.jsx` (+103/-0)
- `frontend/src/components/reporting/SectionContainer.jsx` (+92/-0)
- `frontend/src/components/reporting/charts/BarChart.jsx` (+159/-74)
- `frontend/src/components/reporting/charts/LineChart.jsx` (+128/-56)
- `frontend/src/components/reporting/charts/PieChart.jsx` (+86/-67)
- `frontend/src/components/reporting/charts/ScrunchVisualizations.jsx` (+213/-128)
- `frontend/src/components/reporting/constants.js` (+83/-51)
- `frontend/src/components/reporting/hooks/useChartData.js` (+161/-0)
- `frontend/src/components/reporting/sections/GA4SectionEnhanced.jsx` (+318/-0)
- `frontend/src/services/api.js` (+11/-3)

---

## 2025-11-23

### Commit: ff2dd5fc

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-11-23 12:33:31 +0530
- **Message:** Implement Scrunch analytics endpoints and visualizations: Add new API endpoints for querying Scrunch analytics and fetching dashboard data. Introduce reusable chart components (BarChart, LineChart, PieChart) for displaying Scrunch data in the ReportingDashboard. Enhance the frontend with ScrunchVisualizations component to present various metrics, including position distribution and sentiment analysis. Improve error handling and loading states for better user experience.

**Files Changed:** 10 files
**Total Additions:** +5991 lines
**Total Deletions:** -2971 lines

**Files Modified:**
- `app/api/data.py` (+388/-2)
- `app/services/scrunch_client.py` (+36/-0)
- `frontend/src/components/ReportingDashboard.jsx` (+4662/-2969)
- `frontend/src/components/reporting/charts/BarChart.jsx` (+115/-0)
- `frontend/src/components/reporting/charts/LineChart.jsx` (+90/-0)
- `frontend/src/components/reporting/charts/PieChart.jsx` (+110/-0)
- `frontend/src/components/reporting/charts/README.md` (+138/-0)
- `frontend/src/components/reporting/charts/ScrunchVisualizations.jsx` (+423/-0)
- `frontend/src/components/reporting/charts/index.js` (+6/-0)
- `frontend/src/services/api.js` (+23/-0)

---

## 2025-11-21

### Commit: 9cde2bca

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-11-21 19:58:19 +0530
- **Message:** Add package-lock.json and refactor reporting dashboard components: Introduce package-lock.json for dependency management. Refactor data fetching in ReportingDashboard to improve KPI consistency and enhance error handling. Update BrandAnalyticsDetail to remove simulated change calculations and ensure accurate data representation. Implement new reporting components for better organization and maintainability.

**Files Changed:** 19 files
**Total Additions:** +14064 lines
**Total Deletions:** -1230 lines

**Files Modified:**
- `app/api/data.py` (+437/-237)
- `frontend/src/components/BrandAnalyticsDetail.jsx` (+40/-26)
- `frontend/src/components/ReportingDashboard.backup.jsx` (+366/-0)
- `frontend/src/components/ReportingDashboard.jsx` (+2105/-967)
- `frontend/src/components/ReportingDashboard.old.jsx` (+5401/-0)
- `frontend/src/components/ReportingDashboard.refactored.jsx` (+366/-0)
- `frontend/src/components/reporting/BrandAnalyticsSection.jsx` (+1121/-0)
- `frontend/src/components/reporting/DashboardContent.jsx` (+85/-0)
- `frontend/src/components/reporting/GA4Section.content.jsx` (+3/-0)
- `frontend/src/components/reporting/GA4Section.jsx` (+2723/-0)
- `frontend/src/components/reporting/KPICard.jsx` (+168/-0)
- `frontend/src/components/reporting/KPIGrid.jsx` (+38/-0)
- `frontend/src/components/reporting/KPISelectorDialog.jsx` (+168/-0)
- `frontend/src/components/reporting/ReportingDashboardHeader.jsx` (+181/-0)
- `frontend/src/components/reporting/ScrunchAISection.jsx` (+567/-0)
- `frontend/src/components/reporting/ShareDialog.jsx` (+104/-0)
- `frontend/src/components/reporting/constants.js` (+53/-0)
- `frontend/src/components/reporting/utils.js` (+132/-0)
- `package-lock.json` (+6/-0)

---

### Commit: 2be582dc

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-11-21 09:49:11 +0530
- **Message:** Add Docker support with configuration files: Introduce Dockerfile for backend and frontend services, along with a docker-compose.yml for orchestrating containers. Create .dockerignore to exclude unnecessary files and add a comprehensive Docker setup guide in DOCKER.md for easy deployment and troubleshooting.

**Files Changed:** 5 files
**Total Additions:** +261 lines
**Total Deletions:** -0 lines

**Files Modified:**
- `.dockerignore` (+45/-0)
- `DOCKER.md` (+104/-0)
- `Dockerfile.backend` (+26/-0)
- `Dockerfile.frontend` (+31/-0)
- `docker-compose.yml` (+55/-0)

---

### Commit: c983e012

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-11-21 09:48:59 +0530
- **Message:** Implement audit logging and error handling enhancements: Introduce audit logging service and database model for tracking user actions and sync operations. Add centralized error handling with user-friendly messages and custom exception classes. Update FastAPI application to register exception handlers and improve API error responses. Enhance frontend components with toast notifications for error handling and sync status indicators.

**Files Changed:** 42 files
**Total Additions:** +5685 lines
**Total Deletions:** -935 lines

**Files Modified:**
- `app/api/audit.py` (+176/-0)
- `app/api/auth.py` (+118/-22)
- `app/api/data.py` (+110/-79)
- `app/api/sync.py` (+224/-548)
- `app/api/sync_jobs.py` (+65/-0)
- `app/core/error_handlers.py` (+110/-0)
- `app/core/error_utils.py` (+51/-0)
- `app/core/exceptions.py` (+332/-0)
- `app/db/alembic/versions/001_create_audit_logs_table.py` (+72/-0)
- `app/db/models.py` (+39/-1)
- `app/services/audit_logger.py` (+177/-0)
- `app/services/background_sync.py` (+392/-0)
- `app/services/sync_job_service.py` (+197/-0)
- `docs/AUDIT_LOGGING.md` (+378/-0)
- `docs/ERROR_HANDLING.md` (+277/-0)
- `docs/KPI_DOCUMENTATION.md` (+344/-0)
- `docs/KPI_TECHNICAL_CALCULATIONS.md` (+1196/-0)
- `frontend/package-lock.json` (+351/-1)
- `frontend/package.json` (+3/-1)
- `frontend/src/App.jsx` (+36/-30)
- `frontend/src/components/AgencyAnalytics.jsx` (+3/-3)
- `frontend/src/components/BrandAnalytics.jsx` (+1/-1)
- `frontend/src/components/BrandAnalyticsDetail.jsx` (+3/-3)
- `frontend/src/components/BrandAnalyticsDetailWrapper.jsx` (+10/-25)
- `frontend/src/components/BrandsList.jsx` (+4/-4)
- `frontend/src/components/CreateUser.jsx` (+197/-0)
- `frontend/src/components/Dashboard.jsx` (+5/-18)
- `frontend/src/components/DataView.jsx` (+97/-37)
- `frontend/src/components/Layout.jsx` (+18/-1)
- `frontend/src/components/Login.jsx` (+13/-31)
- `frontend/src/components/ProtectedRoute.jsx` (+1/-1)
- `frontend/src/components/PublicReportingDashboard.jsx` (+1/-1)
- `frontend/src/components/ReportingDashboard.jsx` (+2/-2)
- `frontend/src/components/SyncPanel.jsx` (+141/-117)
- `frontend/src/components/SyncStatusIndicator.jsx` (+215/-0)
- `frontend/src/contexts/AuthContext.jsx` (+3/-2)
- `frontend/src/contexts/SyncStatusContext.jsx` (+95/-0)
- `frontend/src/contexts/ToastContext.jsx` (+78/-0)
- `frontend/src/services/api.js` (+40/-5)
- `frontend/src/utils/errorHandler.js` (+48/-0)
- `main.py` (+18/-2)
- `nginx.conf` (+44/-0)

---

### Commit: 567fca8b

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-11-21 09:47:08 +0530
- **Message:** Add database migrations for brand slug functionality and audit logging: Introduce slug field in brands table with automatic generation via triggers, and create audit_logs and sync_jobs tables for tracking user actions and sync operations.

**Files Changed:** 8 files
**Total Additions:** +108 lines
**Total Deletions:** -0 lines

**Files Modified:**
- `database_schema.sql => migrations/v1__database_schema.sql` (+0/-0)
- `ga4_tables_setup.sql => migrations/v2__ga4_tables_setup.sql` (+0/-0)
- `ga4_token_table.sql => migrations/v3__ga4_token_table.sql` (+0/-0)
- `agency_analytics_tables_setup.sql => migrations/v4__agency_analytics_tables_setup.sql` (+0/-0)
- `add_brand_slug_migration.sql => migrations/v5__add_brand_slug_migration.sql` (+0/-0)
- `add_brand_slug_trigger.sql => migrations/v6__add_brand_slug_trigger.sql` (+0/-0)
- `migrations/v7__create_audit_logs_table.sql` (+48/-0)
- `migrations/v8__create_sync_jobs_table.sql` (+60/-0)

---

## 2025-11-20

### Commit: 3905cc0f

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-11-20 15:41:06 +0530
- **Message:** Enhance project dependencies and configuration: Update requirements.txt to include email-validator and psycopg2-binary for SQLAlchemy compatibility. Modify Settings class in config.py to use standard PostgreSQL URL format and ignore extra environment variables. Add comprehensive API documentation and data flow explanation for better understanding of system architecture. Implement slug generation for brands with database trigger setup.

**Files Changed:** 5 files
**Total Additions:** +2385 lines
**Total Deletions:** -2 lines

**Files Modified:**
- `app/core/config.py` (+4/-2)
- `docs/API_DOCUMENTATION.md` (+1002/-0)
- `docs/DATA_FLOW_EXPLANATION.md` (+1262/-0)
- `docs/SLUG_GENERATION_EXPLANATION.md` (+115/-0)
- `requirements.txt` (+2/-0)

---

### Commit: 9e8039d0

- **Author:** Shashank Jain (sjainsahajpur7125@gmail.com)
- **Date:** 2025-11-20 14:41:07 +0530
- **Message:** Add authentication and public reporting features: Implement user authentication with signup and login components, create protected routes for secure access, and develop public reporting dashboard for brand insights using slugs. Enhance UI with improved styling and animations.

**Files Changed:** 25 files
**Total Additions:** +6516 lines
**Total Deletions:** -1046 lines

**Files Modified:**
- `add_brand_slug_migration.sql` (+21/-0)
- `add_brand_slug_trigger.sql` (+89/-0)
- `app/api/auth.py` (+186/-0)
- `app/api/data.py` (+1124/-0)
- `app/api/sync.py` (+94/-36)
- `app/core/config.py` (+8/-0)
- `app/services/supabase_service.py` (+88/-49)
- `frontend/src/App.jsx` (+35/-11)
- `frontend/src/components/AgencyAnalytics.jsx` (+46/-18)
- `frontend/src/components/BrandAnalytics.jsx` (+15/-8)
- `frontend/src/components/BrandsList.jsx` (+126/-121)
- `frontend/src/components/Dashboard.jsx` (+307/-347)
- `frontend/src/components/DataView.jsx` (+50/-28)
- `frontend/src/components/Layout.jsx` (+151/-34)
- `frontend/src/components/Login.jsx` (+195/-0)
- `frontend/src/components/ProtectedRoute.jsx` (+31/-0)
- `frontend/src/components/PublicReportingDashboard.jsx` (+109/-0)
- `frontend/src/components/ReportingDashboard.jsx` (+2814/-0)
- `frontend/src/components/Signup.jsx` (+223/-0)
- `frontend/src/components/SyncPanel.jsx` (+317/-229)
- `frontend/src/contexts/AuthContext.jsx` (+118/-0)
- `frontend/src/index.css` (+98/-9)
- `frontend/src/services/api.js` (+123/-0)
- `frontend/src/theme.js` (+146/-155)
- `main.py` (+2/-1)

---

## 2025-11-14

### Commit: 184f8afd

- **Author:** RohitSingh555 (forrohitsingh99@gmail.com)
- **Date:** 2025-11-14 18:40:56 +0530
- **Message:** Add keyword rankings feature to AgencyAnalytics component: Introduce state management for keyword rankings, implement API call to fetch keyword data, and display rankings in a new card section with loading and error handling.

**Files Changed:** 1 files
**Total Additions:** +121 lines
**Total Deletions:** -0 lines

**Files Modified:**
- `frontend/src/components/AgencyAnalytics.jsx` (+121/-0)

---

### Commit: 01bbedd5

- **Author:** RohitSingh555 (forrohitsingh99@gmail.com)
- **Date:** 2025-11-14 18:38:14 +0530
- **Message:** Add Agency Analytics integration: Create SQL tables for campaign data, implement API endpoints for fetching campaigns and rankings, and develop frontend components for displaying analytics. Enhance SyncPanel for syncing Agency Analytics data.

**Files Changed:** 11 files
**Total Additions:** +2180 lines
**Total Deletions:** -10 lines

**Files Modified:**
- `agency_analytics_tables_setup.sql` (+177/-0)
- `app/api/data.py` (+292/-0)
- `app/api/sync.py` (+203/-0)
- `app/services/agency_analytics_client.py` (+589/-0)
- `app/services/supabase_service.py` (+309/-0)
- `frontend/src/App.jsx` (+2/-0)
- `frontend/src/components/AgencyAnalytics.jsx` (+275/-0)
- `frontend/src/components/BrandAnalyticsDetail.jsx` (+121/-6)
- `frontend/src/components/Layout.jsx` (+3/-1)
- `frontend/src/components/SyncPanel.jsx` (+98/-3)
- `frontend/src/services/api.js` (+111/-0)

---

### Commit: 1aa80fab

- **Author:** RohitSingh555 (forrohitsingh99@gmail.com)
- **Date:** 2025-11-14 17:31:44 +0530
- **Message:** Refactor BrandsList and SyncPanel components to enhance data syncing and analytics integration. Update BrandsList to manage brands with individual analytics, and modify SyncPanel to support syncing Scrunch AI and GA4 data with improved UI and messaging. Add new API method for GA4 data synchronization.

**Files Changed:** 3 files
**Total Additions:** +154 lines
**Total Deletions:** -229 lines

**Files Modified:**
- `frontend/src/components/BrandsList.jsx` (+28/-5)
- `frontend/src/components/SyncPanel.jsx` (+113/-223)
- `frontend/src/services/api.js` (+13/-1)

---

### Commit: 4ecda2a7

- **Author:** RohitSingh555 (forrohitsingh99@gmail.com)
- **Date:** 2025-11-14 17:05:58 +0530
- **Message:** Update README with security warning for service-key.json

**Files Changed:** 1 files
**Total Additions:** +2 lines
**Total Deletions:** -0 lines

**Files Modified:**
- `README.md` (+2/-0)

---

### Commit: 1ea30fd2

- **Author:** RohitSingh555 (forrohitsingh99@gmail.com)
- **Date:** 2025-11-14 17:05:03 +0530
- **Message:** Remove service-key.json from tracking and update .gitignore

**Files Changed:** 1 files
**Total Additions:** +11 lines
**Total Deletions:** -0 lines

**Files Modified:**
- `.gitignore` (+11/-0)

---

### Commit: f1872c97

- **Author:** RohitSingh555 (forrohitsingh99@gmail.com)
- **Date:** 2025-11-14 17:00:11 +0530
- **Message:** Add GA4 integration: Create SQL scripts for GA4 property IDs, implement Python scripts for syncing and verifying data, and set up frontend components for brand analytics dashboard.

**Files Changed:** 54 files
**Total Additions:** +13214 lines
**Total Deletions:** -174 lines

**Files Modified:**
- `README.md` (+151/-98)
- `app/api/data.py` (+505/-0)
- `app/api/database.py` (+144/-0)
- `app/api/sync.py` (+347/-35)
- `app/core/config.py` (+29/-4)
- `app/core/database.py` (+14/-3)
- `app/db/__init__.py` (+5/-0)
- `app/db/alembic.ini` (+116/-0)
- `app/db/alembic/env.py` (+85/-0)
- `app/db/alembic/script.py.mako` (+27/-0)
- `app/db/alembic/versions/.gitkeep` (+3/-0)
- `app/db/database.py` (+73/-0)
- `app/db/models.py` (+80/-0)
- `app/services/ga4_client.py` (+775/-0)
- `app/services/ga4_token_service.py` (+72/-0)
- `app/services/supabase_service.py` (+241/-17)
- `check_ga4_brands.py` (+58/-0)
- `clear_and_rematch_ga4.py` (+175/-0)
- `daily_sync_job.py` (+170/-0)
- `database_schema.sql` (+16/-8)
- `frontend/.gitignore` (+30/-0)
- `frontend/README.md` (+127/-0)
- `frontend/index.html` (+14/-0)
- `frontend/package-lock.json` (+2498/-0)
- `frontend/package.json` (+28/-0)
- `frontend/src/App.css` (+36/-0)
- `frontend/src/App.jsx` (+34/-0)
- `frontend/src/components/BrandAnalytics.css` (+295/-0)
- `frontend/src/components/BrandAnalytics.jsx` (+565/-0)
- `frontend/src/components/BrandAnalyticsDetail.jsx` (+1833/-0)
- `frontend/src/components/BrandAnalyticsDetailWrapper.jsx` (+89/-0)
- `frontend/src/components/BrandDetail.css` (+2/-0)
- `frontend/src/components/BrandDetail.jsx` (+861/-0)
- `frontend/src/components/BrandsList.jsx` (+398/-0)
- `frontend/src/components/Dashboard.jsx` (+431/-0)
- `frontend/src/components/DataView.jsx` (+601/-0)
- `frontend/src/components/Layout.jsx` (+252/-0)
- `frontend/src/components/SyncPanel.jsx` (+417/-0)
- `frontend/src/index.css` (+43/-0)
- `frontend/src/main.jsx` (+11/-0)
- `frontend/src/services/api.js` (+201/-0)
- `frontend/src/theme.js` (+278/-0)
- `frontend/vite.config.js` (+16/-0)
- `ga4_tables_setup.sql` (+191/-0)
- `ga4_token.json` (+5/-0)
- `ga4_token_table.sql` (+41/-0)
- `generate_ga4_token.py` (+233/-0)
- `list_all_brands.py` (+101/-0)
- `main.py` (+64/-5)
- `match_ga4_properties_to_brands.py` (+237/-0)
- `requirements.txt` (+15/-4)
- `setup_daily_sync_linux.sh` (+29/-0)
- `setup_daily_sync_windows.ps1` (+63/-0)
- `verify_synced_data.py` (+89/-0)

---

## 2025-11-13

### Commit: 26857aa1

- **Author:** RohitSingh555 (forrohitsingh99@gmail.com)
- **Date:** 2025-11-13 15:48:00 +0530
- **Message:** Improve .gitignore with additional patterns

**Files Changed:** 1 files
**Total Additions:** +33 lines
**Total Deletions:** -3 lines

**Files Modified:**
- `.gitignore` (+33/-3)

---

### Commit: 301d7bac

- **Author:** RohitSingh555 (forrohitsingh99@gmail.com)
- **Date:** 2025-11-13 15:33:30 +0530
- **Message:** first commit

**Files Changed:** 15 files
**Total Additions:** +885 lines
**Total Deletions:** -0 lines

**Files Modified:**
- `.gitignore` (+43/-0)
- `README.md` (+192/-0)
- `app/__init__.py` (+0/-0)
- `app/api/__init__.py` (+0/-0)
- `app/api/sync.py` (+141/-0)
- `app/core/__init__.py` (+0/-0)
- `app/core/config.py` (+24/-0)
- `app/core/database.py` (+29/-0)
- `app/core/logging_config.py` (+17/-0)
- `app/services/__init__.py` (+0/-0)
- `app/services/scrunch_client.py` (+167/-0)
- `app/services/supabase_service.py` (+131/-0)
- `database_schema.sql` (+74/-0)
- `main.py` (+58/-0)
- `requirements.txt` (+9/-0)

---


## Summary Statistics

- **Total Unique Files Changed:** 234
- **Total Lines Added:** +110790
- **Total Lines Deleted:** -31595
- **Net Change:** +79195 lines

### Files Changed by Type:
- `*.jsx`: 315 changes
- `*.py`: 222 changes
- `*.js`: 62 changes
- `*.sql`: 47 changes
- `*.md`: 35 changes
- `*.sh`: 23 changes
- `*.json`: 13 changes
- `*.yml`: 7 changes
- `*.css`: 6 changes
- `*.gitignore`: 5 changes
- `*.txt`: 4 changes
- `*.backend`: 3 changes
- `*.html`: 3 changes
- `*.ps1`: 2 changes
- `*.no-ext`: 1 changes
- `*.webmanifest`: 1 changes
- `*.sql}`: 1 changes
- `*.dockerignore`: 1 changes
- `*.frontend`: 1 changes
- `*.conf`: 1 changes
- `*.ini`: 1 changes
- `*.mako`: 1 changes
- `*.gitkeep`: 1 changes

### Files Changed by Directory:
- `frontend/src/components/`: 206 changes
- `root/`: 92 changes
- `app/api/`: 86 changes
- `app/services/`: 74 changes
- `frontend/src/components/reporting/`: 65 changes
- `frontend/src/services/`: 34 changes
- `migrations/`: 29 changes
- `frontend/src/components/reporting/charts/`: 25 changes
- `app/core/`: 24 changes
- `frontend/src/`: 21 changes
- `frontend/src/contexts/`: 17 changes
- `app/db/`: 15 changes
- `scripts/`: 12 changes
- `frontend/`: 12 changes
- `frontend/src/hooks/`: 10 changes
- `docs/`: 10 changes
- `migrations/v2/`: 5 changes
- `frontend/src/utils/`: 3 changes
- `migrations/v1/`: 2 changes
- `app/db/alembic/versions/`: 2 changes

### New Files Added:
- `.dockerignore`
- `.gitignore`
- `BACKUP_README.md`
- `BRAND_PRESENCE_RATE_VISIBILITY.md`
- `COMPLETE_CONFIG_BOX_AUDIT.md`
- `CONFIG_BOX_FIXES_SUMMARY.md`
- `CONFIG_BOX_MAPPING.md`
- `DATABASE_DUMP_GUIDE.md`
- `DATABASE_MIGRATION_GUIDE.md`
- `DEPLOYMENT.md`
- `DOCKER.md`
- `Dockerfile.backend`
- `Dockerfile.frontend`
- `OPTIMIZATION_SUMMARY.md`
- `QUICK_CRON_CHECK.md`
- `QUICK_DUMP_GUIDE.md`
- `QUICK_REFERENCE.md`
- `README.md`
- `README_DUMP.md`
- `SYNC_DATE_PARAMETERS_ANALYSIS.md`
- `add_brand_slug_migration.sql`
- `add_brand_slug_trigger.sql`
- `agency_analytics_tables_setup.sql`
- `app/api/audit.py`
- `app/api/auth.py`
- `app/api/auth_v2.py`
- `app/api/data.py`
- `app/api/database.py`
- `app/api/openai.py`
- `app/api/sync.py`
- `app/api/sync_jobs.py`
- `app/api/websocket.py`
- `app/core/config.py`
- `app/core/database.py`
- `app/core/error_handlers.py`
- `app/core/error_utils.py`
- `app/core/exceptions.py`
- `app/core/jwt_utils.py`
- `app/core/logging_config.py`
- `app/core/password_utils.py`
- `app/db/__init__.py`
- `app/db/alembic.ini`
- `app/db/alembic/env.py`
- `app/db/alembic/script.py.mako`
- `app/db/alembic/versions/.gitkeep`
- `app/db/alembic/versions/001_create_audit_logs_table.py`
- `app/db/database.py`
- `app/db/models.py`
- `app/services/agency_analytics_client.py`
- `app/services/audit_logger.py`
- `app/services/background_sync.py`
- `app/services/ga4_client.py`
- `app/services/ga4_token_service.py`
- `app/services/openai_client.py`
- `app/services/scrunch_client.py`
- `app/services/supabase_service.py`
- `app/services/sync_job_service.py`
- `app/services/user_service.py`
- `app/services/websocket_manager.py`
- `check_and_setup_cron_docker.sh`
- `check_dns_and_setup_ssl.sh`
- `check_ga4_brands.py`
- `clear_and_rematch_ga4.py`
- `daily_sync_job.py`
- `database_schema.sql`
- `docker-compose.yml`
- `docker-entrypoint.sh`
- `docker-help.md`
- `docs/API_DOCUMENTATION.md`
- `docs/AUDIT_LOGGING.md`
- `docs/CHECK_SYNC_JOBS.md`
- `docs/DATA_FLOW_EXPLANATION.md`
- `docs/DOCKER_CRON_SETUP.md`
- `docs/ERROR_HANDLING.md`
- `docs/KPI_DOCUMENTATION.md`
- `docs/KPI_TECHNICAL_CALCULATIONS.md`
- `docs/SLUG_GENERATION_EXPLANATION.md`
- `docs/USER_GUIDE.md`
- `frontend/.gitignore`
- `frontend/README.md`
- `frontend/assets/site.webmanifest`
- `frontend/index.html`
- `frontend/package-lock.json`
- `frontend/package.json`
- `frontend/src/App.css`
- `frontend/src/App.jsx`
- `frontend/src/components/AgencyAnalytics.jsx`
- `frontend/src/components/AuditLogs.jsx`
- `frontend/src/components/BrandAnalytics.css`
- `frontend/src/components/BrandAnalytics.jsx`
- `frontend/src/components/BrandAnalyticsDetail.jsx`
- `frontend/src/components/BrandAnalyticsDetailWrapper.jsx`
- `frontend/src/components/BrandDetail.css`
- `frontend/src/components/BrandDetail.jsx`
- `frontend/src/components/BrandManagement.jsx`
- `frontend/src/components/BrandsList.jsx`
- `frontend/src/components/ClientManagement.jsx`
- `frontend/src/components/ClientsList.jsx`
- `frontend/src/components/CreateUser.jsx`
- `frontend/src/components/Dashboard.jsx`
- `frontend/src/components/DashboardLinksManagement.jsx`
- `frontend/src/components/DataView.jsx`
- `frontend/src/components/KeywordsDashboard.jsx`
- `frontend/src/components/Layout.jsx`
- `frontend/src/components/Login.jsx`
- `frontend/src/components/NotFound.jsx`
- `frontend/src/components/ProtectedRoute.jsx`
- `frontend/src/components/PublicReportingDashboard.jsx`
- `frontend/src/components/ReportingDashboard.backup.jsx`
- `frontend/src/components/ReportingDashboard.jsx`
- `frontend/src/components/ReportingDashboard.old.jsx`
- `frontend/src/components/ReportingDashboard.refactored.jsx`
- `frontend/src/components/Signup.jsx`
- `frontend/src/components/SyncPanel.jsx`
- `frontend/src/components/SyncStatusIndicator.jsx`
- `frontend/src/components/reporting/BrandAnalyticsSection.jsx`
- `frontend/src/components/reporting/ChartCard.jsx`
- `frontend/src/components/reporting/DashboardContent.jsx`
- `frontend/src/components/reporting/ExecutiveSummary.jsx`
- `frontend/src/components/reporting/GA4Section.content.jsx`
- `frontend/src/components/reporting/GA4Section.jsx`
- `frontend/src/components/reporting/KPICard.jsx`
- `frontend/src/components/reporting/KPIGrid.jsx`
- `frontend/src/components/reporting/KPISelectorDialog.jsx`
- `frontend/src/components/reporting/PromptsAnalyticsTable.jsx`
- `frontend/src/components/reporting/ReportingDashboardHeader.jsx`
- `frontend/src/components/reporting/ScrunchAISection.jsx`
- `frontend/src/components/reporting/SectionContainer.jsx`
- `frontend/src/components/reporting/ShareDialog.jsx`
- `frontend/src/components/reporting/Sparkline.jsx`
- `frontend/src/components/reporting/charts/BarChart.jsx`
- `frontend/src/components/reporting/charts/LineChart.jsx`
- `frontend/src/components/reporting/charts/PieChart.jsx`
- `frontend/src/components/reporting/charts/README.md`
- `frontend/src/components/reporting/charts/ScrunchVisualizations.jsx`
- `frontend/src/components/reporting/charts/StackedBarChart.jsx`
- `frontend/src/components/reporting/charts/index.js`
- `frontend/src/components/reporting/constants.js`
- `frontend/src/components/reporting/hooks/useChartData.js`
- `frontend/src/components/reporting/sections/GA4SectionEnhanced.jsx`
- `frontend/src/components/reporting/utils.js`
- `frontend/src/contexts/AuthContext.jsx`
- `frontend/src/contexts/SyncStatusContext.jsx`
- `frontend/src/contexts/ToastContext.jsx`
- `frontend/src/contexts/WebSocketContext.jsx`
- `frontend/src/hooks/queryClient.js`
- `frontend/src/hooks/queryKeys.js`
- `frontend/src/hooks/useBrands.js`
- `frontend/src/hooks/useDashboard.js`
- `frontend/src/hooks/useData.js`
- `frontend/src/hooks/useResourceSubscription.js`
- `frontend/src/hooks/useSync.js`
- `frontend/src/index.css`
- `frontend/src/main.jsx`
- `frontend/src/services/api.js`
- `frontend/src/services/geolocation.js`
- `frontend/src/services/tokenRefresh.js`
- `frontend/src/theme.js`
- `frontend/src/utils/debug.js`
- `frontend/src/utils/errorHandler.js`
- `frontend/src/utils/roleUtils.js`
- `frontend/vite.config.js`
- `ga4_tables_setup.sql`
- `ga4_token.json`
- `ga4_token_table.sql`
- `generate_ga4_token.py`
- `get-docker.sh`
- `kpi_selector_config`
- `list_all_brands.py`
- `main.py`
- `manage_migrations.py`
- `match_ga4_properties_to_brands.py`
- `migrate_to_local_db.sh`
- `migrations/v1/README.md`
- `migrations/v1/complete_schema.sql`
- `migrations/v10__add_visible_sections_to_brand_kpi_selections.sql`
- `migrations/v11__add_brand_logo_and_theme.sql`
- `migrations/v12__update_brand_slug_trigger_to_uuid.sql`
- `migrations/v13__ga4_kpi_snapshots.sql`
- `migrations/v14__ga4_additional_tables.sql`
- `migrations/v15__create_clients_table.sql`
- `migrations/v16__add_responses_composite_index.sql`
- `migrations/v17__add_version_tracking.sql`
- `migrations/v18__add_client_id_to_ga4_tables.sql`
- `migrations/v18__add_selected_charts_to_brand_kpi_selections.sql`
- `migrations/v2/001_users_and_refresh_tokens.sql`
- `migrations/v2/002_update_agency_analytics_integer_to_bigint.sql`
- `migrations/v2/003_drop_keyword_id_date_unique_constraint.sql`
- `migrations/v2/004_add_performance_indexes.sql`
- `migrations/v2/005_add_is_active_to_clients.sql`
- `migrations/v20__add_is_active_to_clients.sql`
- `migrations/v21__add_client_id_to_brand_kpi_selections.sql`
- `migrations/v22__add_report_dates_to_clients.sql`
- `migrations/v23__create_dashboard_links.sql`
- `migrations/v24__create_dashboard_link_tracking.sql`
- `migrations/v25__create_dashboard_link_kpi_selections.sql`
- `migrations/v26__add_performance_metrics_kpis.sql`
- `migrations/v27__add_executive_summary_to_dashboard_links.sql`
- `migrations/v28__add_show_change_period_to_kpi_selections.sql`
- `migrations/v6__add_brand_slug_trigger.sql`
- `migrations/v7__create_audit_logs_table.sql`
- `migrations/v8__create_sync_jobs_table.sql`
- `migrations/v9__create_brand_kpi_selections_table.sql`
- `nginx.conf`
- `package-lock.json`
- `requirements.txt`
- `scripts/README.md`
- `scripts/create_database_dump.sh`
- `scripts/create_dump_for_remote.sh`
- `scripts/create_password_protected_dump.sh`
- `scripts/create_user.py`
- `scripts/db_helper.sh`
- `scripts/restore_database_dump.sh`
- `scripts/restore_sql_with_error_handling.sh`
- `scripts/setup_weekly_backup_cron.sh`
- `scripts/weekly_backup.sh`
- `setup_cron_auto.sh`
- `setup_daily_sync_linux.sh`
- `setup_daily_sync_windows.ps1`
- `setup_ssl.sh`
- `validate_cron_docker.sh`
- `verify_synced_data.py`
- `wait_for_dns_and_setup_ssl.sh`

### Files Removed:
- `frontend/src/components/BrandsList.jsx`
- `frontend/src/components/ReportingDashboard.backup.jsx`
- `frontend/src/components/ReportingDashboard.jsx`
- `frontend/src/components/ReportingDashboard.old.jsx`
- `frontend/src/components/ReportingDashboard.refactored.jsx`
- `frontend/src/components/reporting/ExecutiveSummary.jsx`
- `frontend/src/components/reporting/charts/BarChart.jsx`

### Most Modified Files:
- `frontend/src/components/ReportingDashboard.jsx`: 71 commits
- `app/api/data.py`: 45 commits
- `frontend/src/services/api.js`: 28 commits
- `app/services/supabase_service.py`: 26 commits
- `frontend/src/components/reporting/GA4Section.jsx`: 16 commits
- `app/services/background_sync.py`: 13 commits
- `frontend/src/App.jsx`: 13 commits
- `app/api/sync.py`: 13 commits
- `frontend/src/components/Layout.jsx`: 12 commits
- `app/services/ga4_client.py`: 11 commits
- `frontend/src/components/KeywordsDashboard.jsx`: 11 commits
- `app/db/models.py`: 11 commits
- `frontend/src/components/PublicReportingDashboard.jsx`: 11 commits
- `frontend/src/components/reporting/charts/ScrunchVisualizations.jsx`: 10 commits
- `frontend/src/components/SyncPanel.jsx`: 10 commits
- `frontend/src/components/ClientsList.jsx`: 9 commits
- `app/api/openai.py`: 9 commits
- `frontend/src/components/BrandsList.jsx`: 9 commits
- `frontend/src/components/ClientManagement.jsx`: 8 commits
- `frontend/src/contexts/AuthContext.jsx`: 8 commits

# Brand Presence Rate Visibility - Troubleshooting Guide

## Why "Brand Presence Rate" Might Not Be Visible on Dashboard

### Requirements for Visibility

"Brand Presence Rate" requires **TWO things** to be selected in the config box:

1. **KPI Selection**: `brand_presence_rate` must be checked in the config box
2. **Chart Selection**: `brand_presence_rate_donut` chart must be checked in the config box

### Code Location

The visibility is controlled at line 6086-6087 in `ReportingDashboard.jsx`:

```javascript
{shouldShowKPI("brand_presence_rate") &&
  isChartVisible("brand_presence_rate_donut") && (
  // Brand Presence Rate chart displays here
)}
```

### Why It Might Not Show

#### 1. KPI Not Selected
- **Check**: Open config box → "Scrunch AI" section → Ensure "Brand Presence Rate" KPI checkbox is checked
- **Fix**: Check the "Brand Presence Rate" checkbox in the KPIs list

#### 2. Chart Not Selected  
- **Check**: Open config box → "Scrunch AI" section → Ensure "Brand Presence Rate" chart checkbox is checked
- **Fix**: Check the "Brand Presence Rate" checkbox in the Charts list

#### 3. No Data Available
- **Check**: Verify that `dashboardData.kpis.brand_presence_rate` or `scrunchKPIs.brand_presence_rate` exists
- **Fix**: Ensure Scrunch data is synced for the selected brand/client

#### 4. Section Not Visible
- **Check**: Ensure "Scrunch AI" section is visible (section checkbox checked)
- **Fix**: Check the "Scrunch AI" section checkbox in config box

### How to Make It Visible

1. **Open Config Box** (gear icon)
2. **Expand "Scrunch AI" section**
3. **Under "KPIs displayed in this section"**:
   - ✅ Check "Brand Presence Rate"
4. **Under "Charts displayed in this section"**:
   - ✅ Check "Brand Presence Rate"
5. **Click "Save"** (if in admin mode) or ensure both are selected

### Current Implementation

- **KPI Key**: `brand_presence_rate`
- **Chart Key**: `brand_presence_rate_donut`
- **Display Type**: Donut chart (not a KPI card in "All Performance Metrics")
- **Location**: Scrunch AI section

### Note

The "Brand Presence Rate" appears as a **chart** (donut visualization), not as a KPI card in the "All Performance Metrics" section. This is why it requires both the KPI and chart to be selected.

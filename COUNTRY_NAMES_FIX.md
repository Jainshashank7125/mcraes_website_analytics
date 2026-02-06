# Country Names Display Fix

## Issue
Countries with long names (like "United States", "United Kingdom", etc.) were not showing up properly in the geographic distribution charts. Long country names were being cut off or hidden in the bar chart x-axis labels.

## Solution
Created a country name mapping utility that:
1. Maps long country names to shorter versions for display
2. Preserves the full country name in tooltips
3. Applies truncation for very long names (>15 characters)

## Changes Made

### 1. Created Country Name Mapper Utility
**File:** `frontend/src/utils/countryNameMapper.js`
- Maps common long country names to shorter versions:
  - "United States" → "USA"
  - "United Kingdom" → "UK"
  - "United Arab Emirates" → "UAE"
  - "Russian Federation" → "Russia"
  - And many more...
- Provides `getShortCountryName()` function
- Provides `mapGeographicData()` function to process geographic data arrays

### 2. Updated GA4Section Component
**File:** `frontend/src/components/reporting/GA4Section.jsx`
- Added import for country name mapper
- Applied mapping to both bar chart and pie chart data
- Updated tooltips to show full country names
- Set `interval={0}` on XAxis to show all labels

### 3. Updated ReportingDashboard Component
**File:** `frontend/src/components/ReportingDashboard.jsx`
- Added import for country name mapper
- Applied mapping to geographic charts
- Updated tooltips to show full country names

### 4. Updated BarChart Component
**File:** `frontend/src/components/reporting/charts/BarChart.jsx`
- Changed XAxis `interval` from `"preserveStartEnd"` to `0` to show all labels

## Features

1. **Short Names in Charts:** Long country names are automatically shortened for better display
2. **Full Names in Tooltips:** Hovering over chart elements shows the full country name
3. **Automatic Truncation:** Names longer than 15 characters are truncated with "..."
4. **All Labels Visible:** XAxis shows all country labels (no skipping)

## Example Mappings

- United States → USA
- United Kingdom → UK
- United Arab Emirates → UAE
- Russian Federation → Russia
- South Korea → S. Korea
- Democratic Republic of the Congo → DR Congo
- And 30+ more mappings

## Impact

✅ **All clients** will now see:
- All countries displayed in geographic charts
- Long country names properly shortened
- Full country names available in tooltips
- Better chart readability

## Testing

Test with dashboards that have:
- Countries with long names (United States, United Kingdom, etc.)
- Multiple countries in geographic breakdown
- Various date ranges

The fix ensures all countries are visible regardless of name length.

# Geographic Blank Country Names Fix

## Issue
For "Aeroport Taxi" client (and potentially others), blank country names were appearing in the Geographic Distribution charts. The GA4 API was returning "(not set)" as a country value, which was being displayed as blank in the charts.

## Root Cause
GA4 API sometimes returns "(not set)" or empty values for the country dimension when:
- Traffic source doesn't provide country information
- Bot traffic
- Invalid or missing geographic data

These values were being stored and displayed in the charts, causing blank entries.

## Solution
Added filtering at multiple levels to exclude blank, null, or "(not set)" country values:

### 1. GA4 Client Level (`app/services/ga4_client.py`)
- **Daily Breakdown Mode:** Filters out blank countries before returning data
- **Aggregated Mode:** Filters out blank countries before returning data
- Both modes now check for:
  - Empty strings
  - Whitespace-only strings
  - "(not set)" (case-insensitive)
  - "not set" (case-insensitive)

### 2. API Endpoint Level (`app/api/data.py`)
- Added safety filtering in all endpoints that return geographic data:
  - `/data/ga4/brand/{brand_id}`
  - `/data/ga4/client/{client_id}`
  - `/data/ga4/geographic/{property_id}`
  - `/data/reporting-dashboard/{brand_id}` (both occurrences)
- Ensures blank countries are filtered even if they somehow get through

## Changes Made

### Files Modified:
1. `app/services/ga4_client.py`
   - Lines ~527-536: Filter in daily breakdown mode
   - Lines ~560-568: Filter in aggregated mode

2. `app/api/data.py`
   - Multiple locations: Added filtering before assigning to `chart_data["geographic_breakdown"]`
   - Multiple locations: Added filtering in `analytics["geographic"]` assignments
   - Line ~725: Added filtering in `/data/ga4/geographic/{property_id}` endpoint

## Filtering Logic

```python
# Filter out blank or "(not set)" country names
geographic_filtered = [
    g for g in (geographic or []) 
    if g.get("country") 
    and g.get("country").strip() 
    and g.get("country").strip().lower() not in ['(not set)', 'not set', '']
]
```

## Impact

✅ **All clients** will now see:
- No blank country names in geographic charts
- Cleaner, more accurate geographic distribution data
- Only valid countries displayed

## Testing

Tested with:
- Aeroport Taxi client (ID: 54)
- Found 1 record with "(not set)" country
- After fix, this record will be filtered out

## Status

✅ **Backend restarted with fixes applied**
✅ **Filtering active at both GA4 client and API levels**
✅ **Blank countries will no longer appear in charts**

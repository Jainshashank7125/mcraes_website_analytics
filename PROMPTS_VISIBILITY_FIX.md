# Prompts Visibility Fix

## Issue
For several clients (Canadian Shade, City Duct Cleaning, MGA International, PolyPak Packaging), Scrunch graphs were visible but the list of prompts and prompts-related data was not visible.

## Root Cause
The backend API was filtering prompts by their `created_at` date when fetching data for the reporting dashboard. This meant:
- Prompts created outside the selected date range were excluded
- Even if those prompts had responses within the date range, they wouldn't appear
- Prompts are typically created once and then have responses over time, so filtering by prompt creation date is incorrect

## Solution
Changed the prompts query in `/data/reporting-dashboard/{brand_id}/scrunch` endpoint to:
1. Fetch ALL prompts for the brand (not filtered by date)
2. Filter to only include prompts that have responses within the selected date range

This ensures that:
- Prompts with responses in the date range are always included
- The prompts list shows all relevant prompts regardless of when they were created
- The "Top Performing Prompts" and "Scrunch AI Insights" sections will display correctly

## Files Modified
- `app/api/data.py` - Line ~4423-4440: Updated prompts query logic

## Affected Clients
- Canadian Shade (ID: 29, Brand ID: 5553)
- City Duct Cleaning (ID: 67, Brand ID: 5726)
- MGA International (ID: 69, Brand ID: 5908)
- PolyPak Packaging (ID: 70, Brand ID: 5915)

## Testing
After the fix, these clients should now show:
- Top Performing Prompts section
- Scrunch AI Insights table with prompts list
- All prompts-related data in the dashboard

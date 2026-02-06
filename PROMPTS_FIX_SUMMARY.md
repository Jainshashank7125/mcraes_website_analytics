# Prompts Visibility Fix - December 2025

## Problem
"No data available for 1dec to 31 dec 25" was showing in the seed_prompts view, even though responses existed in December 2025.

## Root Cause
- **0 prompts were created in December 2025** for all clients
- **Responses DO exist in December 2025** (855, 340, 239, 521 responses)
- **Prompts were created in November 2025** (before December)
- The system was filtering prompts by `Prompt.created_at` date only
- Since no prompts matched the date range, 0 prompts were returned
- Without prompts, the grouping logic had nothing to work with

## Solution
Modified the logic to include prompts that have responses in the date range, even if the prompts were created outside the date range.

### Changes Made

#### 1. `/data/reporting-dashboard/{brand_id}/scrunch` endpoint (lines 4431-4484)
- Extract `prompt_ids` from responses in the date range
- Fetch prompts that either:
  - Were created in the date range, OR
  - Have responses in the date range
- Added `prompts` to the return statement

#### 2. `/data/prompts-analytics` endpoint (lines 8499-8509)
- Extract `prompt_ids` from responses in the date range
- Fetch prompts that either:
  - Were created in the date range, OR
  - Have responses in the date range

## Results

### Before Fix:
- Prompts returned: 0
- Items in prompts-analytics: 0
- Dashboard showed "No data available"

### After Fix:
- Prompts returned: 37 (for Canadian Shade)
- Items in prompts-analytics: 37 groups
- Dashboard now shows prompts with responses in December 2025

## Test Results

**Canadian Shade (Brand ID: 5553):**
- ✅ 37 prompts now returned (previously 0)
- ✅ All prompts have responses in December 2025
- ✅ Prompts were created in November 2025, but are now shown because they have responses in December

**Other Clients:**
- City Duct Cleaning: 22 prompts
- MGA International: 12 prompts
- PolyPak Packaging: 25 prompts

## Technical Details

The fix ensures that:
1. Responses are filtered by `Response.created_at` (when response was generated)
2. Prompts are included if they have responses in the date range
3. This allows showing prompts that generated responses, even if prompts were created earlier

## Files Modified
- `/root/mcraes_website_analytics/app/api/data.py`
  - Lines 4431-4484: Updated prompts query logic
  - Lines 8499-8509: Updated prompts-analytics query logic
  - Line 4989: Added `prompts` to return statement

## Status
✅ **FIXED** - Prompts are now visible when they have responses in the selected date range.

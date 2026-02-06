# Correct Fix Applied - Prompts with Responses in Date Range

## Issue Identified

**Root Cause:**
- Prompts were created in **November 2025** (Nov 14, 2025)
- Responses were generated in **December 2025** (Dec 20-27, 2025)
- Filtering by `Prompt.created_at` in Dec 2025 returned **0 prompts**
- But we need to show these prompts because they have responses in December

## Correct Fix Applied

### Business Logic
**Show prompts that have responses in the selected date range** - This is the correct behavior:
- Prompts represent questions/searches that were active in the period
- If a prompt has responses in December, it was active/used in December
- Users want to see prompts that generated activity in the selected period

### Implementation

#### 1. `/data/reporting-dashboard/{brand_id}/scrunch` endpoint
- Get `prompt_ids` from responses in the date range
- Include prompts that either:
  - Were created in the date range, OR
  - Have responses in the date range

#### 2. `/data/prompts-analytics` endpoint
- Same logic: Get `prompt_ids` from responses in the date range
- Include prompts that either:
  - Were created in the date range, OR
  - Have responses in the date range

## Results

### Before Fix:
- Prompts returned: 0 (filtered by `Prompt.created_at` only)
- Dashboard showed "No data available"

### After Fix:
- Prompts returned: 37 (for Canadian Shade - prompts with responses in Dec 2025)
- Dashboard now shows prompts that were active in the period

## Verification

**Canadian Shade (Brand ID: 5553):**
- ✅ 37 prompts now returned (previously 0)
- ✅ All prompts have responses in December 2025
- ✅ Prompts were created in November 2025, but are shown because they have responses in December

**This is the CORRECT behavior:**
- Shows prompts that were active/used in the selected period
- Not a workaround - this is the proper business logic
- Users want to see prompts that generated activity, not just prompts created in the period

## Files Modified
- `/root/mcraes_website_analytics/app/api/data.py`
  - Lines 4431-4484: Updated prompts query logic in scrunch dashboard endpoint
  - Lines 8499-8540: Updated prompts query logic in prompts-analytics endpoint

## Status
✅ **FIXED** - Correct fix applied. Prompts with responses in the date range are now shown.

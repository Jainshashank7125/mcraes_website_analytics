# December 2025 "No Data Available" Issue

## Problem
The dashboard shows "No data available for 1dec to 31 dec 25" in the seed_prompts view.

## Root Cause

### Data Situation:
- **0 prompts created in December 2025** for all clients
- **Responses DO exist in December 2025:**
  - Canadian Shade: 855 responses
  - City Duct Cleaning: 340 responses
  - MGA International: 239 responses
  - PolyPak Packaging: 521 responses

### Why This Happens:
- Prompts were created in **November 2025** (before December)
- Responses were generated in **December 2025** (after prompts were created)
- The system filters prompts by `Prompt.created_at` date
- Since no prompts were created in December, 0 prompts are returned
- The `get_prompts_analytics` endpoint groups by prompts, so with 0 prompts, there's no data to display

## Current Behavior

The `/data/prompts-analytics` endpoint:
1. Filters prompts by `Prompt.created_at >= start_date` and `Prompt.created_at <= end_date`
2. Filters responses by `Response.created_at >= start_date` and `Response.created_at <= end_date`
3. Groups responses by prompts (seed_prompts groups by prompt text)
4. If no prompts match the date range, returns empty result

## Technical Details

**Endpoint:** `/api/v1/data/prompts-analytics`
**Filter Logic (lines 8474-8478):**
```python
prompts_conditions = [Prompt.brand_id == brand_id]
if start_date:
    prompts_conditions.append(Prompt.created_at >= datetime.fromisoformat(f"{start_date}T00:00:00+00:00"))
if end_date:
    prompts_conditions.append(Prompt.created_at <= datetime.fromisoformat(f"{end_date}T23:59:59+00:00"))
```

**Result:** Only prompts created in the date range are included.

## Options

### Option 1: Keep Current Behavior (Filter by Prompt.created_at)
- **Pros:** Consistent with user's previous request ("we want by created at only")
- **Cons:** Shows "No data available" when prompts were created before the date range but responses exist in the range

### Option 2: Show Prompts That Have Responses in Date Range
- **Pros:** Shows data when responses exist, even if prompts were created earlier
- **Cons:** Different from the explicit "created_at only" requirement

### Option 3: Show Both Prompts Created in Range AND Prompts with Responses in Range
- **Pros:** Most comprehensive view
- **Cons:** May be confusing, mixes two different date filters

## Recommendation

Since the user previously explicitly requested filtering by `Prompt.created_at` only, the current behavior is **correct as designed**. However, the "No data available" message might be confusing when responses exist.

**Suggested Solution:**
1. Keep the current filtering logic (by `Prompt.created_at`)
2. Improve the "No data available" message to explain why:
   - "No prompts were created in this date range. Prompts were created on [earliest date] to [latest date]."
   - "Responses exist for this period, but prompts were created outside the selected date range."

## Verification

Run this to verify:
```bash
docker exec mcraes-backend python3 /app/check_dec_2025_prompts.py
```

This confirms:
- 0 prompts created in Dec 2025
- Responses exist in Dec 2025
- Prompts were created in Nov 2025

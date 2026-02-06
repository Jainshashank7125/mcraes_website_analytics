# Changes Summary: Prompts Visibility Fix

## What Was Changed

### 1. Fixed `/data/reporting-dashboard/{brand_id}/scrunch` Endpoint
**Location:** `app/api/data.py` lines ~4423-4443

**Before:**
- Prompts were filtered by `Prompt.created_at >= start_date` and `Prompt.created_at <= end_date`
- This meant prompts created outside the date range were excluded, even if they had responses in that range

**After:**
- Fetch ALL prompts for the brand (no date filter on prompt creation)
- Filter to only include prompts that have responses within the selected date range
- This is the correct behavior: prompts are created once but have responses over time

**Code Change:**
```python
# OLD (incorrect):
prompts_query = select(...).where(
    and_(
        Prompt.brand_id == actual_brand_id,
        Prompt.created_at >= start_ts,  # ❌ Wrong filter
        Prompt.created_at <= end_ts
    )
)

# NEW (correct):
prompts_query = select(...).where(
    Prompt.brand_id == actual_brand_id  # ✅ No date filter
)
all_prompts = [dict(row._mapping) for row in prompts_result]
# Filter by which prompts have responses in date range
prompt_ids_with_responses = set(r.get("prompt_id") for r in responses if r.get("prompt_id"))
prompts = [p for p in all_prompts if p.get("id") in prompt_ids_with_responses]
```

### 2. Fixed Data Check Logic
**Location:** `app/api/data.py` lines ~4457-4465

**Before:**
- Checked if prompts were created in date range to determine if Scrunch data exists

**After:**
- Only checks if responses exist in date range (prompts are just metadata)

## Impact on Other Clients

### ✅ Positive Impact (No Breaking Changes)

**For ALL clients with Scrunch data:**
- **Before:** Prompts created outside the selected date range were hidden, even if they had responses in that range
- **After:** All prompts with responses in the selected date range will show, regardless of when the prompt was created
- **Result:** More accurate and complete data display

**Example:**
- Prompt created: January 1, 2025
- Responses in date range: January 15-30, 2026
- **Before:** Prompt wouldn't show (created outside range)
- **After:** Prompt WILL show (has responses in range) ✅

### 🔍 Other Endpoints (Not Changed)

These endpoints still filter by `Prompt.created_at` - this is **intentional** for different use cases:

1. **`/data/prompts`** - General prompts listing endpoint
   - Users may want to see prompts created in a specific date range
   - This is a different use case than the dashboard

2. **`/data/prompts-analytics`** - Analytics endpoint
   - May need date filtering for prompt creation analysis
   - Could be updated later if needed

3. **`supabase_service.get_prompts()`** - General-purpose method
   - Supports optional date filtering as a feature
   - Used by multiple endpoints with different requirements

## Why This Fix is Safe

1. **More Accurate:** Shows prompts that are actually relevant to the selected date range
2. **Backward Compatible:** Doesn't break existing functionality
3. **Logical:** Prompts are metadata - what matters is when responses occurred
4. **Targeted:** Only affects the dashboard Scrunch data endpoint, not other endpoints

## Testing Recommendations

Test with clients that:
- Have prompts created months ago but recent responses
- Have prompts created recently with responses
- Have no responses in the selected date range (should show no prompts)

## Files Modified

1. `app/api/data.py` - Lines ~4423-4443 (main fix)
2. `app/api/data.py` - Lines ~4457-4465 (data check fix)

## Status

✅ **Backend restarted with changes applied**
✅ **No breaking changes expected**
✅ **All clients should see improved prompts visibility**

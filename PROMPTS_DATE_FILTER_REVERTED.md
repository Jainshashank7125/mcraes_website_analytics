# Prompts Date Filter - Reverted to created_at

## Change Applied

Reverted the prompts filtering logic to use `Prompt.created_at` (when prompt was created) instead of filtering by response dates.

## How It Works Now

### Current Behavior (After Revert)
1. User selects a date range (e.g., December 1-31, 2025)
2. System finds all **PROMPTS created** in that date range
3. Only prompts created between start_date and end_date are shown

### Code Logic
```python
# Filter prompts by created_at date
prompts_query = select(...).where(
    and_(
        Prompt.brand_id == actual_brand_id,
        Prompt.created_at >= start_ts,  # Prompt created AFTER start
        Prompt.created_at <= end_ts      # Prompt created BEFORE end
    )
)
```

## Impact

- ✅ Prompts are filtered by when they were **created**
- ✅ Only prompts created in the selected date range will appear
- ✅ This matches the original behavior before the fix

## Note

If prompts were created outside the selected date range, they won't appear even if they have responses in that range. This is the expected behavior when filtering by `Prompt.created_at`.

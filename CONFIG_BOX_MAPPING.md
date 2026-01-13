# Config Box to Dashboard Mapping

This document shows how items in the config box map to what's displayed on the dashboard.

## Scrunch AI Section

### KPIs (shown in "All Performance Metrics" and "Scrunch AI" sections)
| Config Box Label | Dashboard Display | Key |
|-----------------|------------------|-----|
| Total Citations | Total Citations | `total_citations` |
| Brand Presence Rate | Brand Presence Rate | `brand_presence_rate` |
| **Brand Sentiment Score** | **Brand Sentiment Score** | `brand_sentiment_score` |
| Top 10 Prompt | Top 10 Prompt | `top10_prompt_percentage` |
| Prompt Search Volume | Prompt Search Volume | `prompt_search_volume` |

### Charts (shown under "Scrunch AI" section)
| Config Box Label | Dashboard Display | Key |
|-----------------|------------------|-----|
| Top Performing Prompts | Top Performing Prompts | `top_performing_prompts` |
| Scrunch AI Insights | Scrunch AI Insights | `scrunch_ai_insights` |
| Brand Analytics Charts | Brand Sentiment (donut), Platform Distribution, Funnel Stages | `brand_analytics_charts` |
| **Position (% of total) & Brand Sentiment Analysis** | **Position (% of total)** chart + **Brand Sentiment Analysis** chart | `scrunch_visualizations` |
| Brand Presence Rate Donut | Brand Presence Rate Donut | `brand_presence_rate_donut` |

## Key Points

1. **Brand Sentiment Score** - This is a KPI that shows as a card with a numeric value
2. **Brand Sentiment Analysis** - This is a chart showing sentiment distribution (part of "Position (% of total) & Brand Sentiment Analysis")
3. **Position (% of total)** - This is a chart showing position distribution (part of "Position (% of total) & Brand Sentiment Analysis")

## Notes
- The config box groups "Position (% of total)" and "Brand Sentiment Analysis" under one checkbox because they come from the same data source
- If you want to hide/show these charts, toggle the "Position (% of total) & Brand Sentiment Analysis" option in the config box
- The "Brand Sentiment Score" KPI is separate and controlled independently

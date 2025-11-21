// KPI Order and Metadata
export const KPI_ORDER = [
  // GA4 KPIs
  'users', 'sessions', 'new_users', 'engaged_sessions', 'bounce_rate', 'avg_session_duration', 'ga4_engagement_rate', 'conversions', 'revenue',
  // AgencyAnalytics KPIs
  'search_volume', 'avg_keyword_rank', 'ranking_change',
  // New/Updated Google Ranking KPIs
  'google_ranking_count', 'google_ranking', 'google_ranking_change', 'all_keywords_ranking', 'keyword_ranking_change_and_volume',
  // Scrunch KPIs
  'total_citations', 'brand_presence_rate', 'brand_sentiment_score', 'top10_prompt_percentage', 'prompt_search_volume',
  // New Scrunch KPIs
  'competitive_benchmarking'
]

export const KPI_METADATA = {
  // GA4 KPIs
  'users': { label: 'Users', source: 'GA4', icon: 'People' },
  'sessions': { label: 'Sessions', source: 'GA4', icon: 'BarChart' },
  'new_users': { label: 'New Users', source: 'GA4', icon: 'PersonAdd' },
  'engaged_sessions': { label: 'Engaged Sessions', source: 'GA4', icon: 'People' },
  'bounce_rate': { label: 'Bounce Rate', source: 'GA4', icon: 'TrendingDown' },
  'avg_session_duration': { label: 'Avg Session Duration', source: 'GA4', icon: 'AccessTime' },
  'ga4_engagement_rate': { label: 'Engagement Rate', source: 'GA4', icon: 'TrendingUp' },
  'conversions': { label: 'Conversions', source: 'GA4', icon: 'TrendingUp' },
  'revenue': { label: 'Revenue', source: 'GA4', icon: 'TrendingUp' },
  // AgencyAnalytics KPIs
  'search_volume': { label: 'Search Volume', source: 'AgencyAnalytics', icon: 'Search' },
  'avg_keyword_rank': { label: 'Avg Keyword Rank', source: 'AgencyAnalytics', icon: 'Search' },
  'ranking_change': { label: 'Avg Ranking Change', source: 'AgencyAnalytics', icon: 'TrendingUp' },
  // New/Updated Google Ranking KPIs
  'google_ranking_count': { label: 'Google Ranking Count', source: 'AgencyAnalytics', icon: 'Search' },
  'google_ranking': { label: 'Google Ranking', source: 'AgencyAnalytics', icon: 'Search' },
  'google_ranking_change': { label: 'Google Ranking Change', source: 'AgencyAnalytics', icon: 'TrendingUp' },
  'all_keywords_ranking': { label: 'All Keywords Ranking', source: 'AgencyAnalytics', icon: 'Search' },
  'keyword_ranking_change_and_volume': { label: 'Keyword Ranking Change & Volume', source: 'AgencyAnalytics', icon: 'Search' },
  // Scrunch KPIs
  'total_citations': { label: 'Total Citations', source: 'Scrunch', icon: 'Article' },
  'brand_presence_rate': { label: 'Brand Presence Rate', source: 'Scrunch', icon: 'SentimentSatisfied' },
  'brand_sentiment_score': { label: 'Brand Sentiment Score', source: 'Scrunch', icon: 'SentimentSatisfied' },
  'top10_prompt_percentage': { label: 'Top 10 Prompt %', source: 'Scrunch', icon: 'Article' },
  'prompt_search_volume': { label: 'Prompt Search Volume', source: 'Scrunch', icon: 'Search' },
  // New Scrunch KPIs
  'competitive_benchmarking': { label: 'Competitive Benchmarking', source: 'Scrunch', icon: 'TrendingUp' },
}

export const DATE_PRESETS = [
  { label: 'Last 7 days', days: 7 },
  { label: 'Last 30 days', days: 30 },
  { label: 'Last 90 days', days: 90 },
  { label: 'Last 6 months', days: 180 },
  { label: 'Last year', days: 365 },
]


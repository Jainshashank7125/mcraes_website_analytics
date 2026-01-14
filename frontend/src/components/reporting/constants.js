// Color palette for charts - modern, accessible colors
export const CHART_COLORS = {
  primary: '#1e77b9', // McRAE Primary Blue
  secondary: '#f4af46', // McRAE Secondary Orange
  success: '#10b981', // Emerald 500
  warning: '#f59e0b', // Amber 500
  error: '#ef4444', // Red 500
  info: '#3b82f6', // Blue 500
  
  // Extended palette for multiple series
  // First two colors are primary and secondary for two-data-point charts
  palette: [
    '#1e77b9', // McRAE Primary Blue - Primary
    '#f4af46', // McRAE Secondary Orange - Secondary
    '#3b82f6', // Blue 500
    '#10b981', // Emerald 500
    '#f59e0b', // Amber 500
    '#ef4444', // Red 500
    '#8b5cf6', // Violet 500
    '#ec4899', // Pink 500
    '#06b6d4', // Cyan 500
    '#84cc16', // Lime 500
    '#f97316', // Orange 500
  ],
  
  // GA4 specific colors
  ga4: {
    primary: '#4285F4', // Google Blue
    secondary: '#34A853', // Google Green
    accent: '#FBBC04', // Google Yellow
    error: '#EA4335', // Google Red
  },
  
  // AgencyAnalytics colors
  agencyAnalytics: {
    primary: '#34A853', // Green
    secondary: '#10b981', // Emerald
  },
  
  // Scrunch colors
  scrunch: {
    primary: '#FBBC04', // Yellow
    secondary: '#f59e0b', // Amber
  },
  
  // Comparison chart colors (for two-data-point charts like current vs previous)
  comparison: {
    current: '#1e77b9', // Current period - McRAE Primary Blue
    previous: '#f4af46', // Previous period - McRAE Secondary Orange
  },
}

// Chart configuration constants
export const CHART_CONFIG = {
  // Responsive heights based on breakpoints
  heights: {
    mobile: 250,
    tablet: 300,
    desktop: 400,
  },
  
  // Animation delays for staggered animations
  animation: {
    delay: 0.1,
    duration: 0.3,
  },
  
  // Tooltip styling
  tooltip: {
    borderRadius: 8,
    border: 'none',
    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
    backgroundColor: '#FFFFFF',
  },
  
  // Grid styling
  grid: {
    stroke: '#E4E4E7',
    strokeDasharray: '3 3',
  },
  
  // Axis styling
  axis: {
    stroke: '#71717A',
    fontSize: { mobile: 10, tablet: 11, desktop: 12 },
  },
}

// KPI Order - defines the order KPIs should appear
export const KPI_ORDER = [
  // GA4 KPIs
  "users",
  "sessions",
  "new_users",
  "engaged_sessions",
  "bounce_rate",
  "avg_session_duration",
  "ga4_engagement_rate",
  "conversions",
  "revenue",
  // AgencyAnalytics KPIs
  "search_volume",
  "avg_keyword_rank",
  "ranking_change",
  // New/Updated Google Ranking KPIs
  "google_ranking_count",
  "google_ranking",
  "google_ranking_change",
  "all_keywords_ranking",
  "average_google_ranking",
  "average_bing_ranking",
  "average_search_volume",
  "top_10_visibility_percentage",
  "improving_keywords_count",
  "declining_keywords_count",
  "stable_keywords_count",
  // Scrunch KPIs
  "total_citations",
  "brand_presence_rate",
  "brand_sentiment_score",
  "top10_prompt_percentage",
  "prompt_search_volume",
];

// KPI metadata for display
export const KPI_METADATA = {
  // GA4 KPIs
  users: { label: "Total Users", source: "GA4", icon: "People" },
  sessions: { label: "Sessions", source: "GA4", icon: "BarChart" },
  new_users: { label: "New Users", source: "GA4", icon: "PersonAdd" },
  engaged_sessions: {
    label: "Engaged Sessions",
    source: "GA4",
    icon: "People",
  },
  bounce_rate: { label: "Bounce Rate", source: "GA4", icon: "TrendingDown" },
  avg_session_duration: {
    label: "Avg Session Duration",
    source: "GA4",
    icon: "AccessTime",
  },
  ga4_engagement_rate: {
    label: "Engagement Rate",
    source: "GA4",
    icon: "TrendingUp",
  },
  conversions: { label: "Conversions", source: "GA4", icon: "TrendingUp" },
  revenue: { label: "Revenue", source: "GA4", icon: "TrendingUp" },
  // AgencyAnalytics KPIs
  search_volume: {
    label: "Search Volume",
    source: "AgencyAnalytics",
    icon: "Search",
  },
  avg_keyword_rank: {
    label: "Avg Keyword Rank",
    source: "AgencyAnalytics",
    icon: "Search",
  },
  ranking_change: {
    label: "Avg Ranking Change",
    source: "AgencyAnalytics",
    icon: "TrendingUp",
  },
  // New/Updated Google Ranking KPIs
  google_ranking_count: {
    label: "Google Ranking Count",
    source: "AgencyAnalytics",
    icon: "Search",
  },
  google_ranking: {
    label: "Google Ranking",
    source: "AgencyAnalytics",
    icon: "Search",
  },
  google_ranking_change: {
    label: "Google Ranking Change",
    source: "AgencyAnalytics",
    icon: "TrendingUp",
  },
  all_keywords_ranking: {
    label: "All Keywords Ranking",
    source: "AgencyAnalytics",
    icon: "List",
  },
  average_google_ranking: {
    label: "Avg Google Ranking",
    source: "AgencyAnalytics",
    icon: "Search",
  },
  average_bing_ranking: {
    label: "Avg Bing Ranking",
    source: "AgencyAnalytics",
    icon: "Search",
  },
  average_search_volume: {
    label: "Avg Search Volume",
    source: "AgencyAnalytics",
    icon: "Search",
  },
  top_10_visibility_percentage: {
    label: "Top 10 Visibility %",
    source: "AgencyAnalytics",
    icon: "TrendingUp",
  },
  improving_keywords_count: {
    label: "Improving Keywords",
    source: "AgencyAnalytics",
    icon: "TrendingUp",
  },
  declining_keywords_count: {
    label: "Declining Keywords",
    source: "AgencyAnalytics",
    icon: "TrendingDown",
  },
  stable_keywords_count: {
    label: "Stable Keywords",
    source: "AgencyAnalytics",
    icon: "Insights",
  },
  // Scrunch KPIs
  total_citations: {
    label: "Total Citations",
    source: "Scrunch",
    icon: "Link",
  },
  brand_presence_rate: {
    label: "Brand Presence Rate",
    source: "Scrunch",
    icon: "CheckCircle",
  },
  brand_sentiment_score: {
    label: "Brand Sentiment Score",
    source: "Scrunch",
    icon: "SentimentSatisfied",
  },
  top10_prompt_percentage: {
    label: "Top 10 Prompt",
    source: "Scrunch",
    icon: "Article",
  },
  prompt_search_volume: {
    label: "Prompt Search Volume",
    source: "Scrunch",
    icon: "Search",
  },
};

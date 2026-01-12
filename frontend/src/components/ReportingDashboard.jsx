import { useState, useEffect, useRef, useMemo, useCallback } from "react";
import { useLocation } from "react-router-dom";
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  CircularProgress,
  Alert,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  alpha,
  useTheme,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Checkbox,
  FormControlLabel,
  TextField,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  LinearProgress,
  Autocomplete,
  List,
  ListItem,
  ListItemText,
  Tabs,
  Tab,
} from "@mui/material";
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Settings as SettingsIcon,
  Refresh as RefreshIcon,
  BarChart as BarChartIcon,
  People as PeopleIcon,
  Visibility as VisibilityIcon,
  Search as SearchIcon,
  TrendingUp,
  CalendarToday as CalendarTodayIcon,
  PersonAdd as PersonAddIcon,
  AccessTime as AccessTimeIcon,
  Link as LinkIcon,
  CheckCircle as CheckCircleIcon,
  SentimentSatisfied as SentimentSatisfiedIcon,
  Article as ArticleIcon,
  Share as ShareIcon,
  ContentCopy as ContentCopyIcon,
  Check as CheckIcon,
  ExpandMore as ExpandMoreIcon,
  Analytics as AnalyticsIcon,
  Insights as InsightsIcon,
} from "@mui/icons-material";
import { motion } from "framer-motion";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { reportingAPI, syncAPI, clientAPI, openaiAPI } from "../services/api";
import { debugLog, debugWarn, debugError } from "../utils/debug";
import { useAuth } from "../contexts/AuthContext";
import ScrunchVisualizations from "./reporting/charts/ScrunchVisualizations";
import logoMacraesTransparent from "../assets/logo-macraes-transparent.png";
// Import reusable components and utilities
import ChartCard from "./reporting/ChartCard";
import SectionContainer from "./reporting/SectionContainer";
import KPICard from "./reporting/KPICard";
import KPIGrid from "./reporting/KPIGrid";
import PromptsAnalyticsTable from "./reporting/PromptsAnalyticsTable";
import KeywordsDashboard from "./KeywordsDashboard";
import ExecutiveSummary from "./reporting/ExecutiveSummary";
import {
  formatValue,
  getSourceColor,
  getSourceLabel,
  getMonthName,
  getChannelLabel,
  getChannelColor,
} from "./reporting/utils";
import { CHART_COLORS } from "./reporting/constants";
import {
  useChartData,
  formatDateForAxis,
  getDateRangeLabel as getDateRangeLabelUtil,
} from "./reporting/hooks/useChartData";
// Import enhanced chart components (keeping original Recharts imports for now to avoid breaking changes)
import LineChartEnhanced from "./reporting/charts/LineChart";
import BarChartEnhanced from "./reporting/charts/BarChart";
import PieChartEnhanced from "./reporting/charts/PieChart";

// Define all KPIs in order: GA4 (8), AgencyAnalytics (14), Scrunch (5)
const KPI_ORDER = [
  // GA4 KPIs
  "users",
  "sessions",
  "new_users",
  "engaged_sessions",
  "bounce_rate",
  "avg_session_duration",
  "ga4_engagement_rate",
  "conversions",
  // Note: revenue removed from GA4 section
  // AgencyAnalytics KPIs
  // 'impressions', 'clicks', 'ctr', // COMMENTED OUT: Estimated KPIs (not 100% accurate from source)
  "search_volume",
  "avg_keyword_rank",
  "ranking_change",
  // New/Updated Google Ranking KPIs
  "google_ranking_count",
  "google_ranking",
  "google_ranking_change",
  "all_keywords_ranking",
  // "keyword_ranking_change_and_volume",
  "average_google_ranking",
  "average_bing_ranking",
  "average_search_volume",
  "top_10_visibility_percentage",
  "improving_keywords_count",
  "declining_keywords_count",
  "stable_keywords_count",
  // Scrunch KPIs
  // 'influencer_reach', 'scrunch_engagement_rate', 'total_interactions', 'cost_per_engagement', // COMMENTED OUT: Estimated KPIs (not 100% accurate from source)
  "total_citations",
  "brand_presence_rate",
  "brand_sentiment_score",
  "top10_prompt_percentage",
  "prompt_search_volume",
  // New Scrunch KPIs
  // "competitive_benchmarking",
];

// KPI metadata for display
const KPI_METADATA = {
  // GA4 KPIs
  users: { label: "Users", source: "GA4", icon: "People" },
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
  // 'impressions': { label: 'Impressions', source: 'AgencyAnalytics', icon: 'Visibility' }, // COMMENTED OUT: Estimated KPI
  // 'clicks': { label: 'Clicks', source: 'AgencyAnalytics', icon: 'TrendingUp' }, // COMMENTED OUT: Estimated KPI
  // 'ctr': { label: 'CTR', source: 'AgencyAnalytics', icon: 'BarChart' }, // COMMENTED OUT: Estimated KPI
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
  // keyword_ranking_change_and_volume: {
  //   label: "Keyword Ranking Change and Volume",
  //   source: "AgencyAnalytics",
  //   icon: "BarChart",
  // },
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
  // 'influencer_reach': { label: 'Influencer Reach', source: 'Scrunch', icon: 'People' }, // COMMENTED OUT: Estimated KPI
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
  // 'scrunch_engagement_rate': { label: 'Engagement Rate', source: 'Scrunch', icon: 'TrendingUp' }, // COMMENTED OUT: Estimated KPI
  // 'total_interactions': { label: 'Total Interactions', source: 'Scrunch', icon: 'Visibility' }, // COMMENTED OUT: Estimated KPI
  // 'cost_per_engagement': { label: 'Cost per Engagement', source: 'Scrunch', icon: 'TrendingUp' }, // COMMENTED OUT: Estimated KPI
  top10_prompt_percentage: {
    label: "Top 10 Prompt",
    source: "Scrunch",
    icon: "Article",
  },
  prompt_search_volume: {
    label: "Prompt Search Volume",
    source: "Scrunch",
    icon: "TrendingUp",
  },
  // New Scrunch KPIs
  competitive_benchmarking: {
    label: "Competitive Benchmarking",
    source: "Scrunch",
    icon: "BarChart",
  },
};

// Date range presets
const DATE_PRESETS = [
  { label: "Last 7 days", days: 7 },
  { label: "Last 30 days", days: 30 },
  { label: "Last 90 days", days: 90 },
  { label: "Last 6 months", days: 180 },
  { label: "Last year", days: 365 },
];

// Helper function to get month name
// getMonthName is now imported from utils

function ReportingDashboard({
  publicSlug,
  brandInfo: publicBrandInfo,
  publicStartDate,
  publicEndDate,
}) {
  const { user } = useAuth();
  const isPublic = !!publicSlug;
  const location = useLocation();
  const hasHandledNavigationClientId = useRef(false); // Track if we've handled clientId from navigation state
  // Track previous client/brand IDs to detect actual client changes (not just date changes)
  // Dashboard links should persist when only dates change, but be cleared when client changes
  const prevClientIdRef = useRef(null);
  const prevBrandIdRef = useRef(null);
  const [clients, setClients] = useState([]);
  const [selectedClientId, setSelectedClientId] = useState(null);
  const [clientSearchTerm, setClientSearchTerm] = useState("");
  const [loadingClients, setLoadingClients] = useState(false);
  const [clientSearchTimeout, setClientSearchTimeout] = useState(null);
  const [selectedBrandId, setSelectedBrandId] = useState(null); // For backward compatibility with existing data loading
  const [dashboardData, setDashboardData] = useState(null);
  const [scrunchData, setScrunchData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingScrunch, setLoadingScrunch] = useState(false);
  const [error, setError] = useState(null);
  // Loading state for public reporting page
  const [isLoadingReport, setIsLoadingReport] = useState(false);
  const [loadingCaption, setLoadingCaption] = useState("");
  const [selectedKPIs, setSelectedKPIs] = useState(new Set(KPI_ORDER));
  const [tempSelectedKPIs, setTempSelectedKPIs] = useState(new Set(KPI_ORDER)); // For dialog
  // All Performance Metrics section KPI selections (independent from section-specific KPIs)
  const [selectedPerformanceMetricsKPIs, setSelectedPerformanceMetricsKPIs] =
    useState(new Set(KPI_ORDER));
  const [
    tempSelectedPerformanceMetricsKPIs,
    setTempSelectedPerformanceMetricsKPIs,
  ] = useState(new Set(KPI_ORDER)); // For dialog
  const [showKPISelector, setShowKPISelector] = useState(false);
  const [expandedSections, setExpandedSections] = useState(
    new Set([
      "ga4",
      "agency_analytics",
      "scrunch_ai",
      "all_performance_metrics",
    ])
  ); // Track expanded accordion sections - only 4 main sections
  // Initialize with "Last 30 days" as default
  const getDefaultDates = () => {
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - 30);
    return {
      start: start.toISOString().split("T")[0],
      end: end.toISOString().split("T")[0],
    };
  };

  const defaultDates = getDefaultDates();
  // Use public date range if provided (from URL params), otherwise use default
  const [startDate, setStartDate] = useState(
    publicStartDate || defaultDates.start
  );
  const [endDate, setEndDate] = useState(publicEndDate || defaultDates.end);
  const [datePreset, setDatePreset] = useState("Last 30 days");
  const currentMonthStr = useMemo(() => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(
      2,
      "0"
    )}`;
  }, []);
  // Dashboard Links Management
  const [dashboardLinks, setDashboardLinks] = useState([]);
  const [loadingLinks, setLoadingLinks] = useState(false);
  const [linkDialogOpen, setLinkDialogOpen] = useState(false);
  const [editingLink, setEditingLink] = useState(null);
  const [linkDialogTab, setLinkDialogTab] = useState(0); // 0 = Basic, 1 = Advanced
  const [linkFormData, setLinkFormData] = useState({
    name: "",
    description: "",
    start_date: "",
    end_date: "",
    enabled: true,
    expires_at: "",
    slug: "",
  });
  const [metricsDialogOpen, setMetricsDialogOpen] = useState(false);
  const [selectedLinkForMetrics, setSelectedLinkForMetrics] = useState(null);
  const [linkMetrics, setLinkMetrics] = useState(null);
  const [loadingMetrics, setLoadingMetrics] = useState(false);
  const [allLinksMetrics, setAllLinksMetrics] = useState(null);
  const [loadingAllMetrics, setLoadingAllMetrics] = useState(false);
  
  const [monthSelection, setMonthSelection] = useState(
    isPublic ? "" : currentMonthStr
  );
  const [brandAnalytics, setBrandAnalytics] = useState(null);
  const [loadingAnalytics, setLoadingAnalytics] = useState(false);
  const [selectedBrandSlug, setSelectedBrandSlug] = useState(null);
  const [selectedClientReportTitle, setSelectedClientReportTitle] =
    useState(null); // Store custom report title
  const [selectedClientLogoUrl, setSelectedClientLogoUrl] = useState(null); // Store client logo URL
  const [selectedClientName, setSelectedClientName] = useState(null); // Store client name for default title
  const [showOverviewDialog, setShowOverviewDialog] = useState(false);
  const [overviewData, setOverviewData] = useState(null);
  const [loadingOverview, setLoadingOverview] = useState(false);
  const [overviewCacheKey, setOverviewCacheKey] = useState(null); // Track cache key (clientId/brandId + date range)
  // Executive summary state (structured JSON, persisted per dashboard link)
  const [executiveSummary, setExecutiveSummary] = useState(null);
  const [executiveSummaryCacheKey, setExecutiveSummaryCacheKey] =
    useState(null);
  // Tab state for public dashboard
  const [activeTab, setActiveTab] = useState(0); // 0 = Executive Summary, 1 = Detailed Metrics
  const [expandedMetricsSources, setExpandedMetricsSources] = useState(
    new Set()
  ); // Track which metric sources are expanded
  // Pagination state for Scrunch AI Insights table
  const [insightsPage, setInsightsPage] = useState(0);
  const [insightsRowsPerPage, setInsightsRowsPerPage] = useState(10);
  // Public KPI selections (loaded from database for public view)
  const [publicKPISelections, setPublicKPISelections] = useState(null);
  // Public performance metrics KPIs (loaded from database for public view)
  const [publicPerformanceMetricsKPIs, setPublicPerformanceMetricsKPIs] =
    useState(null);
  // Section visibility state (for authenticated users to configure)
  // Only 4 main sections: ga4, agency_analytics, scrunch_ai, all_performance_metrics
  const [visibleSections, setVisibleSections] = useState(
    new Set([
      "ga4",
      "agency_analytics",
      "scrunch_ai",
      "all_performance_metrics",
    ])
  );
  const [tempVisibleSections, setTempVisibleSections] = useState(
    new Set([
      "ga4",
      "agency_analytics",
      "scrunch_ai",
      "all_performance_metrics",
    ])
  ); // For dialog
  // Chart/visualization selections (for each section)
  const [selectedCharts, setSelectedCharts] = useState(new Set());
  const [tempSelectedCharts, setTempSelectedCharts] = useState(new Set()); // For dialog
  // Show change period flags per section
  const [showChangePeriod, setShowChangePeriod] = useState({
    ga4: true,
    agency_analytics: true,
    scrunch_ai: true,
    all_performance_metrics: true
  });
  const [tempShowChangePeriod, setTempShowChangePeriod] = useState({
    ga4: true,
    agency_analytics: true,
    scrunch_ai: true,
    all_performance_metrics: true
  }); // For dialog
  // Public section visibility and chart selections (loaded from database for public view)
  const [publicVisibleSections, setPublicVisibleSections] = useState(null);
  const [publicSelectedCharts, setPublicSelectedCharts] = useState(null);
  const [publicShowChangePeriod, setPublicShowChangePeriod] = useState(null);
  const theme = useTheme();

  // Derive client id for prompts analytics in public mode (dashboard link slug) or auth mode
  const promptsClientId = useMemo(() => {
    if (selectedClientId) return selectedClientId;
    return (
      publicBrandInfo?.dashboard_link?.client_id ||
      publicBrandInfo?.clientData?.id ||
      null
    );
  }, [
    selectedClientId,
    publicBrandInfo?.dashboard_link?.client_id,
    publicBrandInfo?.clientData?.id,
  ]);

  // Apply month and reload dashboard (admin only)
  const handleApplyMonth = async () => {
    if (!monthSelection) return;
    const range = applyMonthSelection(monthSelection);
    if (!range) return;
    await loadAllData(range);
  };

  // Handle refresh button click - reloads all data and regenerates overview
  const handleRefresh = async () => {
    // Clear overview cache to force fresh fetch
    setOverviewData(null);
    setOverviewCacheKey(null);
    setExecutiveSummary(null);
    setExecutiveSummaryCacheKey(null);
    
    // Capture current client/brand IDs before reloading to ensure correct IDs are used
    const currentClientId = selectedClientId;
    const currentBrandId = selectedBrandId;
    
    // Reload all data (loadDashboardData will automatically call generateOverviewAutomatically)
    await loadAllData();
    
    // Explicitly call overview API after data is loaded to ensure it's refreshed
    // This is a safety measure in case auto-generation doesn't trigger
    if (!isPublic && (currentClientId || currentBrandId)) {
      // Wait for state to update after loadAllData completes
      setTimeout(() => {
        // generateOverviewAutomatically will use current state values if data is not provided
        // But we pass the captured IDs to ensure they match the loaded data
        generateOverviewAutomatically(null, currentClientId, currentBrandId);
      }, 400);
    }
  };

  // Helper to set dates based on month selection (admin only)
  const applyMonthSelection = useCallback((monthStr) => {
    if (!monthStr) return null;
    const [yearStr, monthPart] = monthStr.split("-");
    const year = Number(yearStr);
    const month = Number(monthPart);
    if (!year || !month) return null;

    const start = new Date(Date.UTC(year, month - 1, 1));
    const now = new Date();
    const monthEnd = new Date(Date.UTC(year, month, 0)); // last day of month
    const end =
      year === now.getUTCFullYear() && month === now.getUTCMonth() + 1
        ? new Date(Date.UTC(year, month - 1, now.getUTCDate()))
        : monthEnd;

    const startStr = start.toISOString().split("T")[0];
    const endStr = end.toISOString().split("T")[0];
    setStartDate(startStr);
    setEndDate(endStr);
    return { startDate: startStr, endDate: endStr };
  }, []);

  useEffect(() => {
    if (!isPublic && monthSelection) {
      applyMonthSelection(monthSelection);
    }
  }, [isPublic, monthSelection, applyMonthSelection]);

  // Load dashboard links when client changes (admin only) - for create link functionality
  useEffect(() => {
    if (!isPublic && selectedClientId) {
      loadDashboardLinks();
    }
  }, [selectedClientId, isPublic]);

  // Load executive summary and KPI selections from dashboard link (public mode)
  useEffect(() => {
    if (isPublic && publicBrandInfo?.dashboard_link) {
      const dashboardLink = publicBrandInfo.dashboard_link;

      if (dashboardLink.executive_summary) {
        // Executive summary exists, load it
        debugLog(
          "Loading executive summary from dashboard link (public view)",
          {
            linkId: dashboardLink.id,
          }
        );
        setExecutiveSummary(dashboardLink.executive_summary);
        setExecutiveSummaryCacheKey(`link-${dashboardLink.id}`);
        // Set default tab to Executive Summary for public view
        setActiveTab(0);
      } else {
        // No executive summary found, need to generate it
        debugLog(
          "No executive summary found in dashboard link (public view), will generate on demand",
          {
            linkId: dashboardLink.id,
          }
        );
        setExecutiveSummary(null);
        setExecutiveSummaryCacheKey(null);
        // Default to Executive Summary tab (will show "not available" message initially)
        setActiveTab(0);

        // Generate executive summary if dashboard data is available
        // This will be called when dashboardData is loaded
        if (
          dashboardData &&
          dashboardData.kpis &&
          Object.keys(dashboardData.kpis).length > 0
        ) {
          generateOverviewForPublicLink(dashboardLink.id);
        }
      }

      // Load KPI selections from dashboard link
      if (dashboardLink.kpi_selection) {
        const kpiSelection = dashboardLink.kpi_selection;
        
        if (kpiSelection.selected_kpis && Array.isArray(kpiSelection.selected_kpis)) {
          setPublicKPISelections(new Set(kpiSelection.selected_kpis));
        }
        
        if (kpiSelection.selected_performance_metrics_kpis && Array.isArray(kpiSelection.selected_performance_metrics_kpis)) {
          setPublicPerformanceMetricsKPIs(new Set(kpiSelection.selected_performance_metrics_kpis));
        }
        
        if (kpiSelection.visible_sections && Array.isArray(kpiSelection.visible_sections)) {
          setPublicVisibleSections(new Set(kpiSelection.visible_sections));
        }
        
        if (kpiSelection.selected_charts && Array.isArray(kpiSelection.selected_charts)) {
          setPublicSelectedCharts(new Set(kpiSelection.selected_charts));
        }

        // Load show_change_period flags
        if (kpiSelection.show_change_period) {
          setPublicShowChangePeriod(kpiSelection.show_change_period);
        }
      }
    }
  }, [isPublic, publicBrandInfo?.dashboard_link, dashboardData]);

  // Loading captions for public reporting page
  const loadingCaptions = [
    "Fetching the latest insights...",
    "Crunching numbers for clarity...",
    "Hang tight — building the report...",
    "Pulling public data — almost there!",
    "Preparing your public report...",
    "Analyzing performance metrics...",
    "Gathering analytics data...",
    "Compiling your insights...",
    "Processing report data...",
    "Loading comprehensive analytics...",
  ];

  // Get a random loading caption
  const getRandomCaption = () => {
    return loadingCaptions[Math.floor(Math.random() * loadingCaptions.length)];
  };

  // Read clientId from navigation state (when navigating from ClientsList)
  useEffect(() => {
    if (
      !isPublic &&
      location.state?.clientId &&
      !selectedClientId &&
      !hasHandledNavigationClientId.current
    ) {
      const clientIdFromState = location.state.clientId;
      hasHandledNavigationClientId.current = true; // Mark as handled
      setSelectedClientId(clientIdFromState);

      // Fetch the specific client data to ensure we have all metadata (slug, brand_id, etc.)
      const fetchClientData = async () => {
        try {
          const client = await clientAPI.getClient(clientIdFromState);
          if (client) {
            // Update clients list to include this client if not already present
            setClients((prevClients) => {
              const exists = prevClients.find(
                (c) => c.id === clientIdFromState
              );
              if (exists) {
                return prevClients;
              }
              return [client, ...prevClients];
            });
          }
        } catch (err) {
          debugError("Error fetching client data:", err);
        }
      };
      fetchClientData();
    }
  }, [location.state, isPublic, selectedClientId]);

  // KPI selections are NOT loaded on initial render - show all KPIs/charts by default
  // KPI selections are only loaded when a dashboard link is selected/edited (see handleEditLink)
  // This allows users to see all available data by default, and only apply saved selections when viewing a specific link

  // Initialize selectedCharts with all available charts on initial load (admin view only)
  useEffect(() => {
    if (isPublic || selectedCharts.size > 0) return; // Don't override if already set or in public view
    
    // Initialize with all available charts from all sections
    const allCharts = new Set();
    ["ga4", "agency_analytics", "scrunch_ai", "all_performance_metrics"].forEach((sectionKey) => {
      getDashboardSectionCharts(sectionKey).forEach((chart) => {
        allCharts.add(chart.key);
      });
    });
    
    if (allCharts.size > 0) {
      setSelectedCharts(allCharts);
      setTempSelectedCharts(allCharts);
      debugLog("Initialized selectedCharts with all available charts", { 
        chartCount: allCharts.size,
        charts: Array.from(allCharts),
        hasChannelPerformance: allCharts.has("ga4_channel_performance")
      });
    }
  }, [isPublic]); // Only run once on mount for admin view

  // Comprehensive data loading function - loads all dashboard data including KPI selections
  const loadAllData = async (overrideRange = null) => {
    // For public view, we can use slug even without selectedBrandId
    // For admin view, we need selectedClientId (client-centric) or selectedBrandId (fallback)
    if (!selectedClientId && !selectedBrandId && !(isPublic && publicSlug))
      return;

    // Set loading state for public mode
    if (isPublic) {
      setIsLoadingReport(true);
      setLoadingCaption(getRandomCaption());
    }

    try {
      // Load all data sources in parallel (respect override date range if provided)
      await Promise.all([
        loadDashboardData(overrideRange),
        loadScrunchData(overrideRange),
        // Load brand analytics for both public and authenticated views (needed for brand_analytics section)
        loadBrandAnalytics(overrideRange),
        // Client-level KPI selection removed - KPIs are now loaded from dashboard links
      ]);
    } finally {
      // Clear loading state for public mode
      if (isPublic) {
        setIsLoadingReport(false);
      }
    }
  };

  useEffect(() => {
    if (isPublic && publicSlug) {
      // Set loading state for initial public page load
      setIsLoadingReport(true);
      setLoadingCaption(getRandomCaption());

      // For public mode, try to fetch client by slug first, then fall back to brand
      const fetchPublicEntity = async () => {
        try {
          // Try client first (new client-centric approach)
          try {
            const client = await clientAPI.getClientBySlug(publicSlug);
            if (client && client.id) {
              // Always set selectedClientId (client-centric approach)
              setSelectedClientId(client.id);
              // Set selectedBrandId only if client has scrunch_brand_id (for backward compatibility)
              if (client.scrunch_brand_id) {
                setSelectedBrandId(client.scrunch_brand_id);
              }
              // Store report_title, logo_url, and company_name for public view
              setSelectedClientReportTitle(client.report_title || null);
              setSelectedClientLogoUrl(client.logo_url || null);
              setSelectedClientName(client.company_name || null);
              return;
            }
          } catch (clientErr) {
            // Client not found, try brand (backward compatibility)
            debugLog("Client not found by slug, trying brand...");
          }
          // Fallback to brand lookup for backward compatibility
          const brand = await reportingAPI.getBrandBySlug(publicSlug);

          // Check if brand has no_data flag (graceful degradation from backend)
          if (brand && brand.no_data) {
            // Still allow UI to render, but mark as no data
            if (brand.id) {
              setSelectedBrandId(brand.id);
            }
            // Don't set error - let the dashboard show "no data" message
          } else if (brand && brand.id) {
            setSelectedBrandId(brand.id);
          } else {
            // Only set error if it's a real error, not a graceful "no data" response
            setError("No data available for this slug");
            setIsLoadingReport(false);
          }
        } catch (err) {
          // Only set error for actual errors (non-200 status)
          if (err.response?.status !== 200) {
            setError(
              err.response?.data?.detail || "Failed to load client or brand"
            );
            setIsLoadingReport(false);
          } else {
            // If we get a 200 with no_data, handle it gracefully
            setError(null);
            setIsLoadingReport(false);
          }
        }
      };
      fetchPublicEntity();
    } else {
      // Load initial small set of clients (first 10) for admin view
      // Only load clients if no clientId is provided in navigation state
      // (If clientId is provided, we'll fetch that specific client in the other useEffect)
      // Also check the ref to ensure we don't load if we're handling navigation state
      if (!location.state?.clientId && !hasHandledNavigationClientId.current) {
        loadClients("", true);
      }
    }
  }, [isPublic, publicSlug, location.state]);

  // Update date range when public props change (from URL params)
  useEffect(() => {
    if (isPublic && publicStartDate && publicEndDate) {
      setStartDate(publicStartDate);
      setEndDate(publicEndDate);
    }
  }, [isPublic, publicStartDate, publicEndDate]);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (clientSearchTimeout) {
        clearTimeout(clientSearchTimeout);
      }
    };
  }, [clientSearchTimeout]);

  useEffect(() => {
    // For public mode, we can load data with just publicSlug
    // For admin mode, we need selectedClientId (client-centric) or selectedBrandId (fallback)
    if (selectedClientId || selectedBrandId || (isPublic && publicSlug)) {
      // Check if client/brand actually changed (not just date)
      const clientChanged = 
        prevClientIdRef.current !== selectedClientId || 
        prevBrandIdRef.current !== selectedBrandId;
      
      // Only clear dashboard links when client/brand changes, not when dates change
      // Dashboard links are client-specific and should persist across date changes
      if (clientChanged) {
        debugLog("Client changed - clearing dashboard links and resetting KPI selections", {
          previousClientId: prevClientIdRef.current,
          newClientId: selectedClientId,
          previousBrandId: prevBrandIdRef.current,
          newBrandId: selectedBrandId,
        });
        // Clear previous data when switching clients/brands
        // IMPORTANT: Clear executive summary FIRST to prevent showing old client's data
        setExecutiveSummary(null);
        setExecutiveSummaryCacheKey(null);
        setOverviewData(null);
        setOverviewCacheKey(null);
        // Clear dashboard links to prevent loading stale executive summaries from previous client
        setDashboardLinks([]);
        
        // Reset KPI selections to default (all KPIs and charts) when client changes
        // This ensures each client starts with a fresh view showing all available data
        setSelectedKPIs(new Set(KPI_ORDER));
        setTempSelectedKPIs(new Set(KPI_ORDER));
        setSelectedPerformanceMetricsKPIs(new Set(KPI_ORDER));
        setTempSelectedPerformanceMetricsKPIs(new Set(KPI_ORDER));
        
        // Reset to all sections visible
        setVisibleSections(
          new Set([
            "ga4",
            "agency_analytics",
            "scrunch_ai",
            "all_performance_metrics",
          ])
        );
        setTempVisibleSections(
          new Set([
            "ga4",
            "agency_analytics",
            "scrunch_ai",
            "all_performance_metrics",
          ])
        );
        
        // Reset to all charts selected
        const allCharts = new Set();
        ["ga4", "agency_analytics", "scrunch_ai", "all_performance_metrics"].forEach((sectionKey) => {
          getDashboardSectionCharts(sectionKey).forEach((chart) => {
            allCharts.add(chart.key);
          });
        });
        setSelectedCharts(allCharts);
        setTempSelectedCharts(new Set(allCharts));
        debugLog("Reset selectedCharts on client change", {
          chartCount: allCharts.size,
          charts: Array.from(allCharts),
          hasChannelPerformance: allCharts.has("ga4_channel_performance")
        });
        
        // Reset change period flags to all true
        const defaultShowChangePeriod = {
          ga4: true,
          agency_analytics: true,
          scrunch_ai: true,
          all_performance_metrics: true
        };
        setShowChangePeriod(defaultShowChangePeriod);
        setTempShowChangePeriod(defaultShowChangePeriod);
        
        // Update refs to track current client
        prevClientIdRef.current = selectedClientId;
        prevBrandIdRef.current = selectedBrandId;
      } else {
        // When only dates change, clear overview/executive summary but keep dashboard links
        debugLog("Only dates changed - keeping dashboard links", {
          clientId: selectedClientId,
          startDate,
          endDate,
          dashboardLinksCount: dashboardLinks.length,
        });
        setExecutiveSummary(null);
        setExecutiveSummaryCacheKey(null);
        setOverviewData(null);
        setOverviewCacheKey(null);
        // Dashboard links are NOT cleared - they persist across date changes
      }
      
      // Always clear data and reload when dates or client changes
      setDashboardData(null);
      setScrunchData(null);
      setBrandAnalytics(null);
      setError(null);
      // Reset pagination when data changes
      setInsightsPage(0);
      // Load all data sources in parallel including KPI selections
      loadAllData();
    }
  }, [
    selectedClientId,
    selectedBrandId,
    startDate,
    endDate,
    isPublic,
    publicSlug,
  ]);

  // Ensure overview API is called when client changes and data is loaded (admin view only)
  useEffect(() => {
    // Only trigger in admin view when we have data and client/brand ID
    if (
      !isPublic &&
      dashboardData &&
      dashboardData.kpis &&
      Object.keys(dashboardData.kpis).length > 0 &&
      (selectedClientId || selectedBrandId)
    ) {
      // Create cache key to check if overview already exists for this client/brand and date range
      const cacheKey = `${selectedClientId || selectedBrandId}-${startDate}-${endDate}`;
      
      // Only call overview API if we don't already have overview data for this cache key
      // and we're not already loading
      if (
        (!overviewData || overviewCacheKey !== cacheKey) &&
        !loadingOverview
      ) {
        // Use a small delay to avoid duplicate calls (since loadDashboardData also calls it)
        const timeoutId = setTimeout(() => {
          // Double-check conditions before calling (state might have changed)
          if (
            dashboardData &&
            dashboardData.kpis &&
            Object.keys(dashboardData.kpis).length > 0 &&
            (selectedClientId || selectedBrandId) &&
            (!overviewData || overviewCacheKey !== cacheKey) &&
            !loadingOverview
          ) {
            generateOverviewAutomatically(
              dashboardData,
              selectedClientId,
              selectedBrandId
            );
          }
        }, 200);

        return () => clearTimeout(timeoutId);
      }
    }
  }, [
    dashboardData,
    selectedClientId,
    selectedBrandId,
    startDate,
    endDate,
    isPublic,
    overviewData,
    overviewCacheKey,
    loadingOverview,
  ]);

  const loadClients = async (searchTerm = "", autoSelectFirst = false) => {
    // Don't load clients if we have a clientId from navigation state (to prevent unwanted dropdown updates)
    if (location.state?.clientId && !searchTerm) {
      return;
    }

    try {
      setLoadingClients(true);
      const data = await clientAPI.getClients(1, 25, searchTerm); // Get up to 50 clients based on search
      const clientsList = data.items || [];
      debugLog(
        "Loaded clients:",
        clientsList.map((c) => ({
          id: c.id,
          name: c.company_name,
          url_slug: c.url_slug,
          scrunch_brand_id: c.scrunch_brand_id,
        }))
      );
      setClients(clientsList);
      // Only auto-select first client if:
      // 1. autoSelectFirst is true
      // 2. We have clients
      // 3. No clientId is currently selected
      // 4. No clientId was provided in navigation state
      if (
        autoSelectFirst &&
        clientsList.length > 0 &&
        !selectedClientId &&
        !location.state?.clientId
      ) {
        const firstClient = clientsList[0];
        setSelectedClientId(firstClient.id);
        // Set brand_id from client's scrunch_brand_id for data loading
        if (firstClient.scrunch_brand_id) {
          setSelectedBrandId(firstClient.scrunch_brand_id);
        }
        // Set slug for first client
        if (firstClient.url_slug) {
          setSelectedBrandSlug(firstClient.url_slug);
        }
      }
    } catch (err) {
      debugError("Error loading clients:", err);
      setError(err.response?.data?.detail || "Failed to load clients");
    } finally {
      setLoadingClients(false);
    }
  };

  // Debounced client search
  const handleClientSearch = (searchValue) => {
    setClientSearchTerm(searchValue);

    // Clear existing timeout
    if (clientSearchTimeout) {
      clearTimeout(clientSearchTimeout);
    }

    // Set new timeout for debounced search
    const timeout = setTimeout(() => {
      loadClients(searchValue, false);
    }, 300); // 300ms debounce

    setClientSearchTimeout(timeout);
  };

  // Update slug, brand_id, and report_title when client changes
  useEffect(() => {
    if (selectedClientId && clients.length > 0) {
      const selectedClient = clients.find((c) => c.id === selectedClientId);
      if (selectedClient) {
        // Update slug from client
        if (selectedClient.url_slug) {
          setSelectedBrandSlug(selectedClient.url_slug);
        } else {
          setSelectedBrandSlug(null);
        }
        // Update brand_id from client's scrunch_brand_id for data loading
        if (selectedClient.scrunch_brand_id) {
          setSelectedBrandId(selectedClient.scrunch_brand_id);
        } else {
          setSelectedBrandId(null);
        }
        // Update report_title, logo_url, and company_name from client
        setSelectedClientReportTitle(selectedClient.report_title || null);
        setSelectedClientLogoUrl(selectedClient.logo_url || null);
        setSelectedClientName(selectedClient.company_name || null);
      }
    }
  }, [selectedClientId, clients]);

  // Auto-save executive summary to matching dashboard link
  const saveExecutiveSummaryToMatchingLink = async (summary) => {
    if (
      !selectedClientId ||
      !startDate ||
      !endDate ||
      !dashboardLinks ||
      dashboardLinks.length === 0
    ) {
      debugLog("Cannot auto-save executive summary - missing requirements", {
        hasClientId: !!selectedClientId,
        hasStartDate: !!startDate,
        hasEndDate: !!endDate,
        hasLinks: !!dashboardLinks,
        linksCount: dashboardLinks?.length || 0,
      });
      return;
    }

    try {
      // Find matching dashboard link by date range
      const matchingLink = dashboardLinks.find((link) => {
        const linkStart = link.start_date
          ? new Date(link.start_date).toISOString().split("T")[0]
          : null;
        const linkEnd = link.end_date
          ? new Date(link.end_date).toISOString().split("T")[0]
          : null;
        return linkStart === startDate && linkEnd === endDate;
      });

      if (matchingLink && matchingLink.id) {
        debugLog("Auto-saving executive summary to matching dashboard link", {
          linkId: matchingLink.id,
          slug: matchingLink.slug,
          startDate,
          endDate,
        });

        await clientAPI.updateDashboardLink(selectedClientId, matchingLink.id, {
          executive_summary: summary,
        });

        // Update the link in local state
        const updatedLinks = dashboardLinks.map((link) =>
          link.id === matchingLink.id
            ? { ...link, executive_summary: summary }
            : link
        );
        setDashboardLinks(updatedLinks);

        debugLog("Executive summary saved to dashboard link successfully", {
          linkId: matchingLink.id,
          slug: matchingLink.slug,
        });
      } else {
        debugLog("No matching dashboard link found for auto-save", {
          startDate,
          endDate,
          availableLinks: dashboardLinks.map((l) => ({
            id: l.id,
            slug: l.slug,
            start: l.start_date,
            end: l.end_date,
          })),
        });
      }
    } catch (err) {
      debugError("Error auto-saving executive summary to dashboard link:", err);
      // Don't throw - this is a convenience feature, not critical
    }
  };

  // Generate overview for public dashboard link and save it
  const generateOverviewForPublicLink = async (linkId) => {
    if (
      !dashboardData ||
      !dashboardData.kpis ||
      Object.keys(dashboardData.kpis).length === 0
    ) {
      return;
    }

    // Check if we already have executive summary for this link
    if (executiveSummary && executiveSummaryCacheKey === `link-${linkId}`) {
      debugLog("Executive summary already loaded for this link", { linkId });
      return;
    }

    // Don't fetch if already loading
    if (loadingOverview) {
      return;
    }

    // Set loading state
    setLoadingOverview(true);

    try {
      // Get client_id or brand_id from publicBrandInfo
      const clientId =
        publicBrandInfo?.clientData?.id ||
        publicBrandInfo?.dashboard_link?.client_id;
      const brandId = publicBrandInfo?.scrunch_brand_id || publicBrandInfo?.id;

      // Use dates ONLY from the dashboard link, not from URL params or state
      const linkStartDate = publicBrandInfo?.dashboard_link?.start_date;
      const linkEndDate = publicBrandInfo?.dashboard_link?.end_date;

      debugLog("Generating executive summary for public dashboard link", {
        linkId,
        clientId,
        brandId,
        startDate: linkStartDate,
        endDate: linkEndDate,
      });

      const overview = await openaiAPI.getOverallOverview(
        clientId || undefined,
        brandId || undefined,
        linkStartDate || undefined,
        linkEndDate || undefined
      );

      if (overview.executive_summary) {
        // Store executive summary in state
        setExecutiveSummary(overview.executive_summary);
        setExecutiveSummaryCacheKey(`link-${linkId}`);

        // Also set overviewData for consistency
        setOverviewData(overview);
        setOverviewCacheKey(`link-${linkId}`);

        // Try to save the executive summary to the dashboard link
        // Note: This requires authentication, so it will fail in public view
        // In that case, the summary will still be displayed for this session but not persisted
        // The summary should ideally be generated and saved by admins, not on-the-fly in public view
        // For now, we'll attempt to save but gracefully handle the failure
        if (clientId && linkId) {
          try {
            await clientAPI.updateDashboardLink(clientId, linkId, {
              executive_summary: overview.executive_summary,
            });
            debugLog("Executive summary saved to dashboard link", { linkId });
          } catch (saveErr) {
            // This is expected in public view - summary is displayed but not persisted
            // Admins should generate and save summaries when creating/updating links
            debugLog(
              "Could not save executive summary to dashboard link (authentication required). Summary is displayed for this session only.",
              {
                linkId,
                error: saveErr.message,
              }
            );
          }
        } else {
          debugLog(
            "Cannot save executive summary - missing clientId or linkId",
            { clientId, linkId }
          );
        }
      }
    } catch (err) {
      debugError("Error generating overview for public link:", err);
      // Don't set error here - just log it, user will see "not available" message
    } finally {
      setLoadingOverview(false);
    }
  };

  // Generate overview automatically when KPIs are loaded (admin view only)
  const generateOverviewAutomatically = async (kpiData = null, clientId = null, brandId = null) => {
    // Use provided data or current dashboardData
    const dataToUse = kpiData || dashboardData;
    if (
      !dataToUse ||
      !dataToUse.kpis ||
      Object.keys(dataToUse.kpis).length === 0
    ) {
      return;
    }

    // Use provided IDs or fall back to state values
    const effectiveClientId = clientId !== null ? clientId : selectedClientId;
    const effectiveBrandId = brandId !== null ? brandId : selectedBrandId;

    // Create cache key based on client/brand and date range
    // Use client_id first (client-centric), then fall back to brand_id
    const cacheKey = `${
      effectiveClientId || effectiveBrandId
    }-${startDate}-${endDate}`;

    // If we already have overview data for this EXACT cache key, don't fetch again
    // But if cache key doesn't match (e.g., different client), we should fetch
    if (overviewData && overviewCacheKey === cacheKey && !loadingOverview) {
      debugLog("Overview already exists for this cache key, skipping API call", {
        cacheKey,
        currentCacheKey: overviewCacheKey,
      });
      return;
    }

    // Don't fetch if already loading (unless cache key changed, which means different client)
    if (loadingOverview && overviewCacheKey === cacheKey) {
      debugLog("Overview already loading for this cache key", { cacheKey });
      return;
    }

    // Set loading state
    setLoadingOverview(true);

    try {
      const overview = await openaiAPI.getOverallOverview(
        effectiveClientId,
        effectiveBrandId,
        startDate || undefined,
        endDate || undefined
      );
      
      // Update overview state with the API response - ALWAYS replace previous data
      setOverviewData(overview);
      setOverviewCacheKey(cacheKey);
      setExpandedMetricsSources(new Set()); // Reset expanded state when new overview is loaded

      // ALWAYS update executive summary from API response, replacing any previous value
      // This ensures that when client changes, the new executive summary replaces the old one
      // Force update regardless of previous state to prevent stale data from persisting
      if (overview.executive_summary) {
        debugLog("Setting executive summary from overview API response", {
          clientId: effectiveClientId,
          brandId: effectiveBrandId,
          cacheKey,
          previousCacheKey: executiveSummaryCacheKey,
        });
        setExecutiveSummary(overview.executive_summary);
        setExecutiveSummaryCacheKey(cacheKey);

        // Auto-save executive summary to matching dashboard link (admin view only)
        if (
          !isPublic &&
          effectiveClientId &&
          startDate &&
          endDate &&
          dashboardLinks &&
          dashboardLinks.length > 0
        ) {
          saveExecutiveSummaryToMatchingLink(overview.executive_summary);
        }
      } else {
        // Clear executive summary if overview response doesn't include it
        setExecutiveSummary(null);
        setExecutiveSummaryCacheKey(null);
      }
      
      debugLog("Overview API response received and state updated", {
        clientId: effectiveClientId,
        brandId: effectiveBrandId,
        cacheKey,
        hasExecutiveSummary: !!overview.executive_summary,
      });
    } catch (err) {
      debugError("Error generating overview:", err);
      // Don't set error here - just log it, user can retry by clicking button
      setOverviewData(null);
      setOverviewCacheKey(null);
      setExecutiveSummary(null);
      setExecutiveSummaryCacheKey(null);
    } finally {
      setLoadingOverview(false);
    }
  };

  const handleOpenOverview = async () => {
    if (
      !dashboardData ||
      !dashboardData.kpis ||
      Object.keys(dashboardData.kpis).length === 0
    ) {
      setError(
        "No KPIs available to generate overview. Please load dashboard data first."
      );
      return;
    }

    // Check if we need to fetch overview data
    const cacheKey = `${
      selectedClientId || selectedBrandId
    }-${startDate}-${endDate}`;

    // First, check if executive summary exists in the currently editing dashboard link (admin view)
    // IMPORTANT: Only load if the link belongs to the current client
    if (
      !isPublic &&
      editingLink &&
      editingLink.executive_summary &&
      editingLink.client_id === selectedClientId
    ) {
      debugLog("Loading executive summary from editing dashboard link", {
        linkId: editingLink.id,
        linkClientId: editingLink.client_id,
        currentClientId: selectedClientId,
      });
      setExecutiveSummary(editingLink.executive_summary);
      setExecutiveSummaryCacheKey(`link-${editingLink.id}`);
      // Also set overviewData for backward compatibility with dialog
      setOverviewData({
        executive_summary: editingLink.executive_summary,
        date_range: { start_date: startDate, end_date: endDate },
        total_metrics_analyzed: dashboardData.kpis
          ? Object.keys(dashboardData.kpis).length
          : 0,
        metrics_by_source: {
          GA4: Object.values(dashboardData.kpis || {}).filter(
            (k) => k.source === "GA4"
          ).length,
          AgencyAnalytics: Object.values(dashboardData.kpis || {}).filter(
            (k) => k.source === "AgencyAnalytics"
          ).length,
          Scrunch: Object.values(dashboardData.kpis || {}).filter(
            (k) => k.source === "Scrunch"
          ).length,
        },
      });
      setOverviewCacheKey(cacheKey);
      setShowOverviewDialog(true);
      return;
    }

    // Check if there's a dashboard link with matching date range and client that has executive summary (admin view)
    if (
      !isPublic &&
      dashboardLinks &&
      dashboardLinks.length > 0 &&
      startDate &&
      endDate &&
      selectedClientId
    ) {
      const matchingLink = dashboardLinks.find((link) => {
        const linkStart = link.start_date
          ? new Date(link.start_date).toISOString().split("T")[0]
          : null;
        const linkEnd = link.end_date
          ? new Date(link.end_date).toISOString().split("T")[0]
          : null;
        return (
          link.client_id === selectedClientId &&
          linkStart === startDate &&
          linkEnd === endDate &&
          link.executive_summary
        );
      });

      if (matchingLink && matchingLink.executive_summary) {
        // Double-check that the link belongs to the current client
        // This prevents loading executive summary from a different client
        if (matchingLink.client_id !== selectedClientId) {
          debugLog(
            "Skipping dashboard link - client ID mismatch",
            {
              linkId: matchingLink.id,
              linkClientId: matchingLink.client_id,
              currentClientId: selectedClientId,
            }
          );
        } else {
          debugLog(
            "Loading executive summary from matching dashboard link by date range",
            {
              linkId: matchingLink.id,
              linkClientId: matchingLink.client_id,
              currentClientId: selectedClientId,
              startDate: startDate,
              endDate: endDate,
            }
          );
          setExecutiveSummary(matchingLink.executive_summary);
          setExecutiveSummaryCacheKey(`link-${matchingLink.id}`);
          // Also set overviewData for backward compatibility with dialog
          setOverviewData({
            executive_summary: matchingLink.executive_summary,
            date_range: { start_date: startDate, end_date: endDate },
            total_metrics_analyzed: dashboardData.kpis
              ? Object.keys(dashboardData.kpis).length
              : 0,
            metrics_by_source: {
              GA4: Object.values(dashboardData.kpis || {}).filter(
                (k) => k.source === "GA4"
              ).length,
              AgencyAnalytics: Object.values(dashboardData.kpis || {}).filter(
                (k) => k.source === "AgencyAnalytics"
              ).length,
              Scrunch: Object.values(dashboardData.kpis || {}).filter(
                (k) => k.source === "Scrunch"
              ).length,
            },
          });
          setOverviewCacheKey(cacheKey);
          setShowOverviewDialog(true);
          return;
        }
      }
    }

    // Check if we already have executive summary in state that matches cache key
    // IMPORTANT: Only use cached data if the cache key matches (which includes client ID)
    if (executiveSummary && executiveSummaryCacheKey === cacheKey) {
      debugLog("Using cached executive summary from state", {
        cacheKey,
        currentClientId: selectedClientId,
      });
      setShowOverviewDialog(true);
      return;
    }

    // If overview data exists and matches current cache key, just show dialog
    // IMPORTANT: Only use if cache key matches (which includes client ID)
    if (overviewData && overviewCacheKey === cacheKey) {
      // Ensure executiveSummary state is set if overviewData has it
      // But only if it matches the current client
      if (overviewData.executive_summary) {
        // Only set if we don't have one, or if the cache key matches (same client)
        if (!executiveSummary || executiveSummaryCacheKey === cacheKey) {
          setExecutiveSummary(overviewData.executive_summary);
          setExecutiveSummaryCacheKey(cacheKey);
        } else {
          debugLog("Skipping stale executive summary - cache key mismatch", {
            currentCacheKey: cacheKey,
            existingCacheKey: executiveSummaryCacheKey,
            currentClientId: selectedClientId,
          });
        }
      }
      setShowOverviewDialog(true);
      return;
    }

    // If overview is currently loading, show dialog with loading state
    if (loadingOverview) {
      setShowOverviewDialog(true);
      return;
    }

    // If no executive summary found, fetch it from API
    debugLog(
      "No executive summary found in dashboard link, calling API to generate"
    );
    setShowOverviewDialog(true);
    generateOverviewAutomatically();
  };

  const loadDashboardData = async (overrideRange = null) => {
    // For admin view, use selectedClientId if available, otherwise fall back to selectedBrandId
    // For public view, use publicSlug
    if (!selectedClientId && !selectedBrandId && !publicSlug) return;

    try {
      setLoading(true);
      setError(null);

      let data;
      const effectiveStart = overrideRange?.startDate || startDate || undefined;
      const effectiveEnd = overrideRange?.endDate || endDate || undefined;

      if (isPublic && publicSlug) {
        data = await reportingAPI.getReportingDashboardBySlug(
          publicSlug,
          effectiveStart,
          effectiveEnd
        );
      } else if (selectedClientId) {
        // Use client-based endpoint for admin view (client-centric)
        data = await reportingAPI.getReportingDashboardByClient(
          selectedClientId,
          effectiveStart,
          effectiveEnd
        );
      } else {
        // Fallback to brand-based endpoint
        data = await reportingAPI.getReportingDashboard(
          selectedBrandId,
          effectiveStart,
          effectiveEnd
        );
      }

      // Check if data has no_data flag (graceful degradation from backend)
      if (data && data.no_data) {
        // Set data with no_data flag so UI can show appropriate message
        debugLog(`No data available for slug/brand (graceful response)`);
        setDashboardData({
          ...data,
          kpis: data.kpis || {},
          chart_data: data.chart_data || {},
          no_data: true,
        });
      } else if (data && (data.kpis || data.chart_data || data.diagnostics)) {
        const scrunchKPIs = data.kpis
          ? Object.keys(data.kpis).filter(
              (k) => data.kpis[k]?.source === "Scrunch"
            )
          : [];
        debugLog(`Dashboard data loaded for brand ${selectedBrandId}:`, {
          hasKPIs: !!data.kpis,
          kpiCount: data.kpis ? Object.keys(data.kpis).length : 0,
          scrunchKPICount: scrunchKPIs.length,
          scrunchKPIs: scrunchKPIs,
          hasChartData: !!data.chart_data,
          hasDiagnostics: !!data.diagnostics,
          availableSources: data.available_sources,
          diagnostics: data.diagnostics,
        });
        setDashboardData(data);

        // On initial load, update selected KPIs to show all available KPIs from the data
        // This ensures we only show KPIs that are actually available, not all from KPI_ORDER
        // Only do this if we're still using the default (all KPIs from KPI_ORDER)
        // and we haven't loaded selections from a dashboard link
        if (data.kpis && !isPublic) {
          const availableKPIs = Object.keys(data.kpis).filter((k) =>
            KPI_ORDER.includes(k)
          );
          // Check if we're still using the default initialization (all KPIs from KPI_ORDER)
          // by comparing if selectedKPIs contains all KPIs from KPI_ORDER
          const isUsingDefaults = selectedKPIs.size === KPI_ORDER.length && 
            KPI_ORDER.every(kpi => selectedKPIs.has(kpi));
          
          if (isUsingDefaults && availableKPIs.length > 0) {
            // Update to use only available KPIs from the data
            setSelectedKPIs(new Set(availableKPIs));
            setTempSelectedKPIs(new Set(availableKPIs));
            // Also update performance metrics KPIs if they're still using defaults
            const isUsingDefaultPerfMetrics = selectedPerformanceMetricsKPIs.size === KPI_ORDER.length &&
              KPI_ORDER.every(kpi => selectedPerformanceMetricsKPIs.has(kpi));
            if (isUsingDefaultPerfMetrics) {
              setSelectedPerformanceMetricsKPIs(new Set(availableKPIs));
              setTempSelectedPerformanceMetricsKPIs(new Set(availableKPIs));
            }
          }
        }

        // Auto-generate overview when KPIs are available (only in admin view)
        // In public view, we check dashboard link first and only call API if summary doesn't exist
        if (data.kpis && Object.keys(data.kpis).length > 0 && !isPublic) {
          // Capture the client/brand IDs that were used to load this data
          // This ensures we use the correct IDs even if state changes before setTimeout executes
          const dataClientId = selectedClientId;
          const dataBrandId = selectedBrandId;
          // Call with a slight delay to ensure state is updated
          setTimeout(() => {
            generateOverviewAutomatically(data, dataClientId, dataBrandId);
          }, 100);
        }
      } else {
        // No data available for this brand
        debugWarn(`No data available for brand ${selectedBrandId}`);
        setDashboardData({ no_data: true, kpis: {}, chart_data: {} });
      }
    } catch (err) {
      debugError("Error loading dashboard data:", err);
      setDashboardData(null);
      // Don't set error here - let individual sections handle their own errors
    } finally {
      setLoading(false);
    }
  };

  const loadScrunchData = async (overrideRange = null) => {
    // For public view, we can use slug even without selectedBrandId
    // For admin view, we need selectedBrandId (which should be set from client's scrunch_brand_id)
    if (!selectedBrandId && !(isPublic && publicSlug)) return;

    try {
      setLoadingScrunch(true);
      // For public view, use slug-based endpoint if available, otherwise use brand_id
      let data;
      const effectiveStart = overrideRange?.startDate || startDate || undefined;
      const effectiveEnd = overrideRange?.endDate || endDate || undefined;

      if (isPublic && publicSlug) {
        // Use slug-based Scrunch endpoint for public view
        data = await reportingAPI.getScrunchDashboardBySlug(
          publicSlug,
          effectiveStart,
          effectiveEnd
        );
      } else {
        // Use brand_id (which comes from client's scrunch_brand_id)
        data = await reportingAPI.getScrunchDashboard(
          selectedBrandId,
          effectiveStart,
          effectiveEnd
        );
      }

      // Check if data has no_data flag (graceful degradation from backend)
      if (data && data.no_data) {
        // Set data with no_data flag so UI can show appropriate message
        debugLog(`No Scrunch data available (graceful response)`);
        setScrunchData({
          ...data,
          kpis: data.kpis || {},
          chart_data: data.chart_data || {},
          no_data: true,
        });
      } else if (data && (data.kpis || data.chart_data)) {
        const hasKPIs = data.kpis && Object.keys(data.kpis).length > 0;
        const hasChartData =
          data.chart_data &&
          ((data.chart_data.top_performing_prompts &&
            data.chart_data.top_performing_prompts.length > 0) ||
            (data.chart_data.scrunch_ai_insights &&
              data.chart_data.scrunch_ai_insights.length > 0));

        debugLog(`Scrunch data loaded for brand ${selectedBrandId}:`, {
          hasKPIs,
          kpiCount: data.kpis ? Object.keys(data.kpis).length : 0,
          hasChartData,
        });

        if (hasKPIs || hasChartData) {
          setScrunchData(data);
        } else {
          setScrunchData({ no_data: true, kpis: {}, chart_data: {} });
        }
      } else {
        setScrunchData({ no_data: true, kpis: {}, chart_data: {} });
      }
    } catch (err) {
      debugError("Error loading Scrunch data:", err);
      setScrunchData(null);
      // Don't set error - Scrunch section will handle its own display
    } finally {
      setLoadingScrunch(false);
    }
  };

  const loadBrandAnalytics = async (overrideRange = null) => {
    if (!selectedBrandId) return;

    try {
      setLoadingAnalytics(true);
      const response = await reportingAPI.getBrandAnalytics(
        selectedBrandId,
        overrideRange?.startDate || startDate || undefined,
        overrideRange?.endDate || endDate || undefined
      );
      setBrandAnalytics(response.global_analytics || null);
    } catch (err) {
      debugError("Failed to load brand analytics:", err);
      setBrandAnalytics(null);
    } finally {
      setLoadingAnalytics(false);
    }
  };

//  Normalizes the value 
  const normalizePercentage = (value) => {
    if (value === null || value === undefined || isNaN(value)) {
      return 0;
    }
    
    if (value > 100) {
      return value / 100;
    } else {
      return value;
    }
  };

  const formatValue = (kpi) => {
    const { value, format, display } = kpi;

    // If custom format with display text, use that
    if (format === "custom" && display) {
      return display;
    }

    // Handle custom format with object values
    if (format === "custom" && typeof value === "object" && value !== null) {
      // For competitive_benchmarking
      if (
        value.brand_visibility_percent !== undefined &&
        value.competitor_avg_visibility_percent !== undefined
      ) {
        return `Your brand's AI visibility: ${value.brand_visibility_percent.toFixed(
          1
        )}% vs competitor average: ${value.competitor_avg_visibility_percent.toFixed(
          1
        )}%`;
      }
      // For keyword_ranking_change_and_volume
      if (
        value.avg_ranking_change !== undefined &&
        value.total_search_volume !== undefined
      ) {
        return `Ranking change: ${
          value.avg_ranking_change
        } positions | Search volume: ${value.total_search_volume.toLocaleString()}`;
      }
      // For all_keywords_ranking (array of keywords)
      if (Array.isArray(value)) {
        return `${value.length} keywords tracked`;
      }
      // For null values (prompt_volume, citations_per_prompt)
      if (value === null) {
        return "Metric not available - no assumptions made";
      }
    }

    // Handle null values
    if (value === null || value === undefined) {
      return "Metric not available - no assumptions made";
    }

    if (format === "currency") {
      return `$${value.toLocaleString(undefined, {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      })}`;
    }

    if (format === "percentage") {
      const normalizedValue = normalizePercentage(value);
      return `${normalizedValue.toFixed(1)}%`;
    }

    if (format === "duration") {
      // Convert seconds to readable format (MM:SS or HH:MM:SS)
      const hours = Math.floor(value / 3600);
      const minutes = Math.floor((value % 3600) / 60);
      const seconds = Math.floor(value % 60);

      if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, "0")}:${seconds
          .toString()
          .padStart(2, "0")}`;
      } else {
        return `${minutes}:${seconds.toString().padStart(2, "0")}`;
      }
    }

    if (format === "number") {
      return value.toLocaleString();
    }

    return value.toLocaleString();
  };

  // Helper function to get simplified channel label
  const getChannelLabel = (source) => {
    if (!source) return source;
    const sourceLower = source.toLowerCase();

    if (sourceLower.includes("direct") || sourceLower.includes("(none)")) {
      return "Direct";
    } else if (sourceLower.includes("organic")) {
      return "Organic";
    } else if (
      sourceLower.includes("social") ||
      sourceLower.includes("paid_social") ||
      sourceLower.includes("facebook")
    ) {
      return "Social";
    } else if (
      sourceLower.includes("referral") ||
      sourceLower.includes("refer") ||
      sourceLower.includes("cpc")
    ) {
      return "Referral";
    }
    // Return original if no match
    return source;
  };

  // Helper function to get channel color
  const getChannelColor = (source) => {
    if (!source) return "rgba(59, 130, 246, 0.6)";
    const sourceLower = source.toLowerCase();

    if (sourceLower.includes("direct") || sourceLower.includes("(none)")) {
      return "rgba(20, 184, 166, 0.6)"; // Teal/Green for Direct
    } else if (
      sourceLower.includes("google") &&
      sourceLower.includes("organic")
    ) {
      return "rgba(59, 130, 246, 0.6)"; // Light blue for Google Organic
    } else if (
      sourceLower.includes("google") &&
      (sourceLower.includes("cpc") || sourceLower.includes("paid"))
    ) {
      return "rgba(68, 192, 237, 0.6)"; // Light blue for Google CPC
    } else if (
      sourceLower.includes("facebook") ||
      sourceLower.includes("social") ||
      sourceLower.includes("paid_social")
    ) {
      return "rgba(239, 68, 68, 0.6)"; // Orange-red for Social/Paid Social
    } else if (
      sourceLower.includes("referral") ||
      sourceLower.includes("refer")
    ) {
      return "rgba(251, 146, 60, 0.6)"; // Orange for Referral
    } else if (
      sourceLower.includes("organic") ||
      sourceLower.includes("search")
    ) {
      return "rgba(59, 130, 246, 0.6)"; // Light blue for Organic Search
    }
    // Default color
    return "rgba(59, 130, 246, 0.6)";
  };

  const getSourceColor = (source) => {
    switch (source) {
      case "GA4":
        return "#4285F4"; // Google blue
      case "AgencyAnalytics":
        return "#34A853"; // Google green
      case "Scrunch":
        return "#FBBC04"; // Google yellow
      default:
        return theme.palette.grey[500];
    }
  };

  const getSourceLabel = (source) => {
    // For public view, use generic KPI-focused labels
    if (isPublic) {
      switch (source) {
        case "GA4":
          return "Website Analytics";
        case "AgencyAnalytics":
          return "SEO Performance";
        case "Scrunch":
          return "AI Visibility";
        default:
          return source;
      }
    }
    // For authenticated view, show actual source names
    switch (source) {
      case "GA4":
        return "Google Analytics";
      case "AgencyAnalytics":
        return "Agency Analytics";
      case "Scrunch":
        return "Scrunch AI";
      default:
        return source;
    }
  };

  // Helper function to get generic badge label for public view
  const getBadgeLabel = (source) => {
    if (isPublic) {
      switch (source) {
        case "GA4":
          return "Analytics";
        case "AgencyAnalytics":
          return "SEO";
        case "Scrunch":
          return "Brand";
        default:
          return source;
      }
    }
    return source;
  };

  const handleDatePresetChange = (preset) => {
    if (preset === "") {
      setDatePreset("");
      return;
    }

    const presetData = DATE_PRESETS.find((p) => p.label === preset);
    if (presetData) {
      const end = new Date();
      const start = new Date();
      start.setDate(start.getDate() - presetData.days);

      setStartDate(start.toISOString().split("T")[0]);
      setEndDate(end.toISOString().split("T")[0]);
      setDatePreset(preset);
    }
  };

  // Get current date range label for charts
  const getDateRangeLabel = () => {
    if (datePreset) {
      return datePreset;
    }
    // Calculate days from startDate to endDate
    if (startDate && endDate) {
      const start = new Date(startDate);
      const end = new Date(endDate);
      const days = Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1;
      return `Last ${days} days`;
    }
    return "Last 7 days"; // Default fallback
  };

  const handleKPIChange = (kpiKey, checked) => {
    const newSelected = new Set(tempSelectedKPIs);
    if (checked) {
      newSelected.add(kpiKey);
    } else {
      newSelected.delete(kpiKey);
    }
    setTempSelectedKPIs(newSelected);
  };

  // Helper function to get KPIs for a section (for Performance Metrics)
  const getSectionKPIs = (sectionKey) => {
    switch (sectionKey) {
      case "GA4":
        return KPI_ORDER.filter((key) => {
          const metadata = KPI_METADATA[key];
          return metadata && metadata.source === "GA4";
        });
      case "AgencyAnalytics":
        return KPI_ORDER.filter((key) => {
          const metadata = KPI_METADATA[key];
          return metadata && metadata.source === "AgencyAnalytics";
        });
      case "Scrunch":
        return KPI_ORDER.filter((key) => {
          const metadata = KPI_METADATA[key];
          return metadata && metadata.source === "Scrunch";
        });
      case "AdvancedAnalytics":
        // Advanced Analytics Query might not have specific KPIs, return empty for now
        // Or you can add specific KPIs if needed
        return [];
      default:
        return [];
    }
  };

  // Helper function to get KPIs displayed in each dashboard section
  // Only 4 main sections: ga4, agency_analytics (keywords), scrunch_ai, all_performance_metrics
  const getDashboardSectionKPIs = (sectionKey) => {
    switch (sectionKey) {
      case "ga4":
        // GA4 section shows GA4 KPIs (Website Analytics)
        return KPI_ORDER.filter((key) => {
          const metadata = KPI_METADATA[key];
          return metadata && metadata.source === "GA4";
        });
      case "agency_analytics":
      case "keywords":
        // Agency Analytics/Keywords section shows AgencyAnalytics KPIs (Organic Visibility)
        // Both use the same KPIs - keywords is just the display name
        return KPI_ORDER.filter((key) => {
          const metadata = KPI_METADATA[key];
          return metadata && metadata.source === "AgencyAnalytics";
        });
      case "scrunch_ai":
        // Scrunch AI section shows Scrunch KPIs (AI Visibility)
        // Includes brand_analytics and advanced_analytics as sub-sections
        return KPI_ORDER.filter((key) => {
          const metadata = KPI_METADATA[key];
          return metadata && metadata.source === "Scrunch";
        });
      case "brand_analytics":
      case "advanced_analytics":
        // These are now sub-sections under scrunch_ai, no separate KPIs
        return [];
      default:
        return [];
    }
  };

  // Helper function to get charts/visualizations for each dashboard section
  // Only 4 main sections: ga4, agency_analytics (keywords), scrunch_ai, all_performance_metrics
  const getDashboardSectionCharts = (sectionKey) => {
    switch (sectionKey) {
      case "ga4":
        return [
          // {
          //   key: "ga4_traffic_overview",
          //   label: "Traffic Overview",
          //   description: "Overall traffic metrics",
          // },
          {
            key: "ga4_daily_comparison",
            label: "Daily Comparison",
            description: "Daily users, sessions, and conversions",
          },
          {
            key: "ga4_channel_performance",
            label: "Channel Performance",
            description: "Traffic by marketing channel",
          },
          {
            key: "ga4_traffic_sources_distribution",
            label: "Traffic Sources Distribution",
            description: "Donut chart showing traffic sources",
          },
          {
            key: "ga4_sessions_by_channel",
            label: "Sessions by Source",
            description: "Horizontal bar chart showing sessions by source",
          },
          {
            key: "ga4_top_pages",
            label: "Top Landing Pages",
            description: "Most visited pages",
          },
          {
            key: "ga4_geographic_distribution",
            label: "Geographic Distribution",
            description: "Bar chart showing traffic by country",
          },
          {
            key: "ga4_top_countries",
            label: "Top Countries",
            description: "Pie chart showing top countries",
          },
          {
            key: "bounce_rate_donut",
            label: "Bounce Rate Donut",
            description: "Bounce rate visualization",
          },
        ];
      case "agency_analytics":
      case "keywords":
        // Agency Analytics/Keywords section - both use same charts
        return [
          {
            key: "all_keywords_ranking",
            label: "Top Keywords Ranking",
            description: "SEO keyword rankings",
          },
          {
            key: "keyword_rankings_chart",
            label: "Rankings Distribution",
            description: "Google rankings distribution over time",
          },
          {
            key: "keyword_table",
            label: "Keyword Table",
            description: "Detailed keyword performance table",
          },
        ];
      case "scrunch_ai":
        // Scrunch AI section - includes brand_analytics and advanced_analytics as sub-sections
        return [
          {
            key: "top_performing_prompts",
            label: "Top Performing Prompts",
            description: "Best performing AI prompts",
          },
          {
            key: "scrunch_ai_insights",
            label: "Scrunch AI Insights",
            description: "AI-generated insights and recommendations",
          },
          {
            key: "brand_analytics_charts",
            label: "Brand Analytics Charts",
            description: "Platform distribution, funnel stages, and sentiment",
          },
          {
            key: "scrunch_visualizations",
            label: "Advanced Query Visualizations",
            description: "Query API-based visualizations",
          },
          {
            key: "brand_presence_rate_donut",
            label: "Brand Presence Rate Donut",
            description: "Brand presence rate visualization",
          },
        ];
      case "brand_analytics":
      case "advanced_analytics":
        // These are now sub-sections under scrunch_ai, handled via scrunch_ai charts
        return [];
      default:
        return [];
    }
  };

  // Helper functions for dashboard sections (similar to Performance Metrics)
  const areAllDashboardSectionKPIsSelected = (sectionKey) => {
    const sectionKPIs = getDashboardSectionKPIs(sectionKey);
    if (sectionKPIs.length === 0) return false;
    return sectionKPIs.every((kpi) => tempSelectedKPIs.has(kpi));
  };

  const areSomeDashboardSectionKPIsSelected = (sectionKey) => {
    const sectionKPIs = getDashboardSectionKPIs(sectionKey);
    if (sectionKPIs.length === 0) return false;
    const selectedCount = sectionKPIs.filter((kpi) =>
      tempSelectedKPIs.has(kpi)
    ).length;
    return selectedCount > 0 && selectedCount < sectionKPIs.length;
  };

  const handleDashboardSectionKPIsChange = (sectionKey, checked) => {
    const sectionKPIs = getDashboardSectionKPIs(sectionKey);
    const newSelected = new Set(tempSelectedKPIs);

    if (checked) {
      sectionKPIs.forEach((kpi) => {
        newSelected.add(kpi);
      });
    } else {
      sectionKPIs.forEach((kpi) => {
        newSelected.delete(kpi);
      });
    }

    setTempSelectedKPIs(newSelected);
  };

  // Helper function to check if all KPIs in a section are selected
  const areAllSectionKPIsSelected = (sectionKey) => {
    const sectionKPIs = getSectionKPIs(sectionKey);
    if (sectionKPIs.length === 0) return false;
    return sectionKPIs.every((kpi) => tempSelectedKPIs.has(kpi));
  };

  // Helper function to check if some KPIs in a section are selected (indeterminate state)
  const areSomeSectionKPIsSelected = (sectionKey) => {
    const sectionKPIs = getSectionKPIs(sectionKey);
    if (sectionKPIs.length === 0) return false;
    const selectedCount = sectionKPIs.filter((kpi) =>
      tempSelectedKPIs.has(kpi)
    ).length;
    return selectedCount > 0 && selectedCount < sectionKPIs.length;
  };

  // Handle parent section checkbox change
  const handleSectionKPIsChange = (sectionKey, checked) => {
    const sectionKPIs = getSectionKPIs(sectionKey);
    const newSelected = new Set(tempSelectedKPIs);

    if (checked) {
      // Select all KPIs in this section
      sectionKPIs.forEach((kpi) => {
        newSelected.add(kpi);
      });
    } else {
      // Deselect all KPIs in this section
      sectionKPIs.forEach((kpi) => {
        newSelected.delete(kpi);
      });
    }

    setTempSelectedKPIs(newSelected);
  };

  // Handle accordion expand/collapse
  const handleAccordionChange = (sectionKey) => (event, isExpanded) => {
    const newExpanded = new Set(expandedSections);
    if (isExpanded) {
      newExpanded.add(sectionKey);
    } else {
      newExpanded.delete(sectionKey);
    }
    setExpandedSections(newExpanded);
  };

  const handleSelectAll = () => {
    // Select all available KPIs
    const availableKPIs = dashboardData?.kpis
      ? Object.keys(dashboardData.kpis)
      : KPI_ORDER;
    setTempSelectedKPIs(new Set(availableKPIs));
  };

  const handleDeselectAll = () => {
    setTempSelectedKPIs(new Set());
  };

  const handleSaveKPISelection = async () => {
    // Only update state - don't save to database
    // KPI selections will be saved when creating/updating a dashboard link
    setSelectedKPIs(new Set(tempSelectedKPIs));
    setSelectedPerformanceMetricsKPIs(
      new Set(tempSelectedPerformanceMetricsKPIs)
    );
    setVisibleSections(new Set(tempVisibleSections));
    setSelectedCharts(new Set(tempSelectedCharts));
    setShowChangePeriod({ ...tempShowChangePeriod });
    setShowKPISelector(false);
    setError(null); // Clear any previous errors
    debugLog("KPI, section, and chart selections updated in state", {
      kpiCount: tempSelectedKPIs.size,
      performanceMetricsKPICount: tempSelectedPerformanceMetricsKPIs.size,
      sectionCount: tempVisibleSections.size,
      chartCount: tempSelectedCharts.size,
      showChangePeriod: tempShowChangePeriod,
    });
  };

  const handleOpenKPISelector = () => {
    // Initialize temp selection with current selection
    setTempSelectedKPIs(new Set(selectedKPIs));
    setTempSelectedPerformanceMetricsKPIs(
      new Set(selectedPerformanceMetricsKPIs)
    );
    setTempVisibleSections(new Set(visibleSections));
    
    // If no charts are selected, select all charts by default
    const chartsToSelect = selectedCharts.size > 0 
      ? new Set(selectedCharts)
      : (() => {
          const allCharts = new Set();
          ["ga4", "agency_analytics", "scrunch_ai", "all_performance_metrics"].forEach((sectionKey) => {
            getDashboardSectionCharts(sectionKey).forEach((chart) => {
              allCharts.add(chart.key);
            });
          });
          return allCharts;
        })();
    setTempSelectedCharts(chartsToSelect);
    
    setTempShowChangePeriod({ ...showChangePeriod });
    // Expand all sections by default
    setExpandedSections(
      new Set([
        "ga4",
        "agency_analytics",
        "scrunch_ai",
        "all_performance_metrics",
      ])
    );
    setShowKPISelector(true);
  };

  // Dashboard Link Management Functions
  const loadDashboardLinks = async () => {
    if (!selectedClientId || isPublic) return;
    setLoadingLinks(true);
    try {
      const response = await clientAPI.listDashboardLinks(selectedClientId);
      setDashboardLinks(response.items || []);
    } catch (err) {
      debugError("Error loading dashboard links:", err);
      setError("Failed to load dashboard links");
    } finally {
      setLoadingLinks(false);
    }
  };

  // Generate auto name and description based on date range and creator
  const generateAutoLinkName = (startDate, endDate) => {
    if (!startDate || !endDate) return "";
    try {
      const start = new Date(startDate);
      const end = new Date(endDate);
      const startStr = start.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
      const endStr = end.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
      return `Report: ${startStr} - ${endStr}`;
    } catch {
      return `Report: ${startDate} - ${endDate}`;
    }
  };

  const generateAutoLinkDescription = (startDate, endDate) => {
    if (!startDate || !endDate) return "";
    const creatorName = user?.email?.split("@")[0] || user?.full_name || "User";
    const creatorDisplay = creatorName.charAt(0).toUpperCase() + creatorName.slice(1);
    try {
      const start = new Date(startDate);
      const end = new Date(endDate);
      const startStr = start.toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" });
      const endStr = end.toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" });
      return `Created by ${creatorDisplay} | Period: ${startStr} to ${endStr}`;
    } catch {
      return `Created by ${creatorDisplay} | Period: ${startDate} to ${endDate}`;
    }
  };

  const handleCreateLink = () => {
    setEditingLink(null);
    setLinkDialogTab(0); // Reset to Basic tab
    // Clear executive summary when creating a new link (will be generated/saved when link is created)
    setExecutiveSummary(null);
    setExecutiveSummaryCacheKey(null);
    // Use current date range from dashboard (startDate and endDate are already strings)
    const currentStartDate = startDate || "";
    const currentEndDate = endDate || "";
    // Auto-generate name and description
    const autoName = generateAutoLinkName(currentStartDate, currentEndDate);
    const autoDescription = generateAutoLinkDescription(currentStartDate, currentEndDate);
    setLinkFormData({
      name: autoName,
      description: autoDescription,
      start_date: currentStartDate,
      end_date: currentEndDate,
      enabled: true,
      expires_at: "",
      slug: "",
    });
    setLinkDialogOpen(true);
  };

  // Reset KPI selections to default (all selected) and clear dropdown selection
  const handleResetKPISelections = () => {
    debugLog("Resetting KPI selections to default (all selected)");

    // Reset to all KPIs selected
    setSelectedKPIs(new Set(KPI_ORDER));
    setTempSelectedKPIs(new Set(KPI_ORDER));
    setSelectedPerformanceMetricsKPIs(new Set(KPI_ORDER));
    setTempSelectedPerformanceMetricsKPIs(new Set(KPI_ORDER));

    // Reset to all sections visible
    setVisibleSections(
      new Set([
        "ga4",
        "agency_analytics",
        "scrunch_ai",
        "all_performance_metrics",
      ])
    );

    // Select all charts by default
    const allCharts = new Set();
    ["ga4", "agency_analytics", "scrunch_ai", "all_performance_metrics"].forEach((sectionKey) => {
      getDashboardSectionCharts(sectionKey).forEach((chart) => {
        allCharts.add(chart.key);
      });
    });
    setSelectedCharts(allCharts);
    setTempSelectedCharts(new Set(allCharts));

    // Reset change period flags to all true
    const defaultShowChangePeriod = {
      ga4: true,
      agency_analytics: true,
      scrunch_ai: true,
      all_performance_metrics: true
    };
    setShowChangePeriod(defaultShowChangePeriod);
    setTempShowChangePeriod(defaultShowChangePeriod);

    // Clear executive summary
    setExecutiveSummary(null);
    setExecutiveSummaryCacheKey(null);

    // Clear dropdown selection
    setEditingLink(null);
    setLinkFormData({
      name: "",
      description: "",
      start_date: startDate || "",
      end_date: endDate || "",
      enabled: true,
      expires_at: "",
      slug: "",
    });

    // Close dialog if open
    setLinkDialogOpen(false);

    debugLog("KPI selections reset to default");
  };

  const handleEditLink = (link) => {
    setEditingLink(link);
    setLinkDialogTab(0); // Reset to Basic tab when editing

    // Load executive summary from the link if it exists
    // IMPORTANT: Only load if the link belongs to the current client
    if (link.executive_summary && link.client_id === selectedClientId) {
      debugLog("Loading executive summary from dashboard link for editing", {
        linkId: link.id,
        linkClientId: link.client_id,
        currentClientId: selectedClientId,
      });
      setExecutiveSummary(link.executive_summary);
      setExecutiveSummaryCacheKey(`link-${link.id}`);
    } else {
      // Clear executive summary if link doesn't have one or belongs to different client
      if (link.client_id !== selectedClientId) {
        debugLog(
          "Skipping executive summary - link belongs to different client",
          {
            linkId: link.id,
            linkClientId: link.client_id,
            currentClientId: selectedClientId,
          }
        );
      } else {
        debugLog(
          "No executive summary in dashboard link, will generate on demand",
          { linkId: link.id }
        );
      }
      setExecutiveSummary(null);
      setExecutiveSummaryCacheKey(null);
    }

    // Load KPI selections from the link and override current selections
    if (link.kpi_selection) {
      debugLog("Loading KPI selections from dashboard link", {
        linkId: link.id,
        selectedKPIs: link.kpi_selection.selected_kpis,
        visibleSections: link.kpi_selection.visible_sections,
        selectedCharts: link.kpi_selection.selected_charts,
        selectedPerformanceMetricsKPIs:
          link.kpi_selection.selected_performance_metrics_kpis,
      });

      // Override current KPI selections with link's selections
      if (
        link.kpi_selection.selected_kpis &&
        Array.isArray(link.kpi_selection.selected_kpis)
      ) {
        setSelectedKPIs(new Set(link.kpi_selection.selected_kpis));
        setTempSelectedKPIs(new Set(link.kpi_selection.selected_kpis));
      }

      if (
        link.kpi_selection.selected_performance_metrics_kpis &&
        Array.isArray(link.kpi_selection.selected_performance_metrics_kpis)
      ) {
        setSelectedPerformanceMetricsKPIs(
          new Set(link.kpi_selection.selected_performance_metrics_kpis)
        );
        setTempSelectedPerformanceMetricsKPIs(
          new Set(link.kpi_selection.selected_performance_metrics_kpis)
        );
      }

      if (
        link.kpi_selection.visible_sections &&
        Array.isArray(link.kpi_selection.visible_sections)
      ) {
        setVisibleSections(new Set(link.kpi_selection.visible_sections));
      }

      if (
        link.kpi_selection.selected_charts &&
        Array.isArray(link.kpi_selection.selected_charts)
      ) {
        setSelectedCharts(new Set(link.kpi_selection.selected_charts));
      }

      // Load show_change_period flags if available
      if (link.kpi_selection.show_change_period) {
        setShowChangePeriod(link.kpi_selection.show_change_period);
        setTempShowChangePeriod(link.kpi_selection.show_change_period);
      }
    } else {
      debugLog(
        "No KPI selections found in dashboard link, keeping current selections",
        { linkId: link.id }
      );
    }

    // Format expires_at for datetime-local input (YYYY-MM-DDTHH:mm)
    let expiresAtFormatted = "";
    if (link.expires_at) {
      const expiresDate = new Date(link.expires_at);
      const year = expiresDate.getFullYear();
      const month = String(expiresDate.getMonth() + 1).padStart(2, "0");
      const day = String(expiresDate.getDate()).padStart(2, "0");
      const hours = String(expiresDate.getHours()).padStart(2, "0");
      const minutes = String(expiresDate.getMinutes()).padStart(2, "0");
      expiresAtFormatted = `${year}-${month}-${day}T${hours}:${minutes}`;
    }
    // Format start_date and end_date for date input (YYYY-MM-DD)
    const formatDateForInput = (dateString) => {
      if (!dateString) return "";
      try {
        const date = new Date(dateString);
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, "0");
        const day = String(date.getDate()).padStart(2, "0");
        return `${year}-${month}-${day}`;
      } catch {
        return dateString.split("T")[0] || "";
      }
    };
    setLinkFormData({
      name: link.name || "",
      description: link.description || "",
      start_date: formatDateForInput(link.start_date),
      end_date: formatDateForInput(link.end_date),
      enabled: link.enabled !== undefined ? link.enabled : true,
      expires_at: expiresAtFormatted,
      slug: link.slug || "",
    });
    
    // Update the date range to match the link's date range
    if (link.start_date && link.end_date) {
      const formattedStartDate = formatDateForInput(link.start_date);
      const formattedEndDate = formatDateForInput(link.end_date);
      if (formattedStartDate && formattedEndDate) {
        setStartDate(formattedStartDate);
        setEndDate(formattedEndDate);
        debugLog("Updated date range from selected link", {
          linkId: link.id,
          startDate: formattedStartDate,
          endDate: formattedEndDate,
        });
      }
    }
    
    // Don't open dialog automatically - user will click "Edit Link" button to open it
  };

  // Open edit dialog for currently selected link
  const handleOpenEditDialog = () => {
    if (editingLink) {
      // Dialog form data is already set when link was selected
    setLinkDialogOpen(true);
    } else {
      // No link selected, create new one
      handleCreateLink();
    }
  };

  const handleSaveLink = async () => {
    if (!selectedClientId) return;
    if (!linkFormData.start_date || !linkFormData.end_date) {
      setError("Start date and end date are required");
      return;
    }
    
    setLoading(true);
    try {
      // Prepare payload - convert datetime-local to ISO string if expires_at is provided
      const payload = { ...linkFormData };
      if (payload.expires_at) {
        const dt = new Date(payload.expires_at);
        if (!isNaN(dt.getTime())) {
          payload.expires_at = dt.toISOString();
        } else {
          delete payload.expires_at;
        }
      } else {
        delete payload.expires_at;
      }
      
      // Include current KPI selections from state
      payload.selected_kpis = Array.from(selectedKPIs);
      payload.selected_performance_metrics_kpis = Array.from(
        selectedPerformanceMetricsKPIs
      );
      payload.visible_sections = Array.from(visibleSections);
      payload.selected_charts = Array.from(selectedCharts);
      payload.show_change_period = showChangePeriod;

      // Include executive summary if available (from local state or overviewData)
      // Check both executiveSummary state and overviewData.executive_summary
      const summaryToSave = executiveSummary || overviewData?.executive_summary;
      if (summaryToSave) {
        payload.executive_summary = summaryToSave;
        debugLog("Including executive summary in save payload", {
          hasExecutiveSummary: !!executiveSummary,
          hasOverviewData: !!overviewData?.executive_summary,
          linkId: editingLink?.id,
        });
      } else {
        debugLog("No executive summary available to save", {
          hasExecutiveSummary: !!executiveSummary,
          hasOverviewData: !!overviewData?.executive_summary,
          linkId: editingLink?.id,
        });
      }
      
      if (editingLink) {
        // Update existing link
        await clientAPI.updateDashboardLink(
          selectedClientId,
          editingLink.id,
          payload
        );
        setError(null);
        debugLog("Dashboard link updated successfully");
      } else {
        // Create new link
        await clientAPI.upsertDashboardLink(selectedClientId, payload);
        setError(null);
        debugLog("Dashboard link created successfully");
      }
      setLinkDialogOpen(false);
      // Reload links to get updated data (including KPI selections)
      await loadDashboardLinks();
      // If we just created a new link, clear editingLink so dropdown resets
      if (!editingLink) {
        setEditingLink(null);
      }
      // Note: editingLink is kept for updates so user can continue editing if needed
      // The dropdown will show the selected link, and clicking "Edit Link" will reopen the dialog
    } catch (err) {
      debugError("Error saving dashboard link:", err);
      setError(
        err.response?.data?.detail ||
          err.message ||
          "Failed to save dashboard link"
      );
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteLink = async (linkId) => {
    if (!selectedClientId) return;
    if (
      !window.confirm(
        "Are you sure you want to delete this dashboard link? This action cannot be undone."
      )
    ) {
      return;
    }
    
    setLoading(true);
    try {
      await clientAPI.deleteDashboardLink(selectedClientId, linkId);
      setError(null);
      await loadDashboardLinks();
    } catch (err) {
      debugError("Error deleting dashboard link:", err);
      setError(
        err.response?.data?.detail ||
          err.message ||
          "Failed to delete dashboard link"
      );
    } finally {
      setLoading(false);
    }
  };

  const handleToggleLinkEnabled = async (link) => {
    if (!selectedClientId) return;
    setLoading(true);
    try {
      await clientAPI.updateDashboardLink(selectedClientId, link.id, {
        enabled: !link.enabled,
      });
      setError(null);
      await loadDashboardLinks();
    } catch (err) {
      debugError("Error toggling link enabled:", err);
      setError(
        err.response?.data?.detail || err.message || "Failed to update link"
      );
    } finally {
      setLoading(false);
    }
  };

  const handleViewMetrics = async (link) => {
    if (!selectedClientId) return;
    setSelectedLinkForMetrics(link);
    setLoadingMetrics(true);
    setMetricsDialogOpen(true);
    try {
      const metrics = await clientAPI.getDashboardLinkMetrics(
        selectedClientId,
        link.id
      );
      setLinkMetrics(metrics);
    } catch (err) {
      debugError("Error loading link metrics:", err);
      setLinkMetrics(null);
    } finally {
      setLoadingMetrics(false);
    }
  };

  const handleViewAllMetrics = async () => {
    if (!selectedClientId) return;
    setLoadingAllMetrics(true);
    setMetricsDialogOpen(true);
    setSelectedLinkForMetrics(null);
    try {
      const metrics = await clientAPI.getDashboardLinksMetrics(
        selectedClientId
      );
      setAllLinksMetrics(metrics);
    } catch (err) {
      debugError("Error loading all links metrics:", err);
      setAllLinksMetrics(null);
    } finally {
      setLoadingAllMetrics(false);
    }
  };

  const handleCopyLinkUrl = (link) => {
    const baseUrl = window.location.origin;
    const url = `${baseUrl}/reporting/client/${link.slug}`;
    navigator.clipboard
      .writeText(url)
      .then(() => {
      setError(null);
      debugLog("Link URL copied to clipboard");
      })
      .catch(() => {
      setError("Failed to copy URL");
    });
  };

  // Helper function to check if a section should be visible
  const isSectionVisible = (sectionKey) => {
    // brand_analytics and advanced_analytics are now sub-sections under scrunch_ai
    if (
      sectionKey === "brand_analytics" ||
      sectionKey === "advanced_analytics"
    ) {
      return isSectionVisible("scrunch_ai");
    }
    
    if (isPublic) {
      // In public mode, use publicVisibleSections
      if (publicVisibleSections === null) {
        return true; // Show all if no selections saved (default behavior)
      }
      if (publicVisibleSections.size === 0) {
        return false; // Empty Set means admin explicitly deselected all sections
      }
      return publicVisibleSections.has(sectionKey); // Check if this specific section is selected
    } else {
      // In authenticated mode, always show (managers can see everything)
      return true;
    }
  };

  // Helper function to check if a chart should be visible in public view
  const isChartVisible = (chartKey) => {
    if (!isPublic) {
      // In authenticated mode, check selectedCharts state
      // If selectedCharts is empty, show all charts by default (initial state)
      if (selectedCharts.size === 0) {
        return true; // Show all charts when no selection has been made yet
      }
      return selectedCharts.has(chartKey);
    }
    // In public mode, check publicSelectedCharts from dashboard link
    if (publicSelectedCharts === null) {
      return true; // Show all charts if no selections saved (default behavior)
    }
    if (publicSelectedCharts.size === 0) {
      return false; // Empty Set means admin explicitly deselected all charts
    }
    return publicSelectedCharts.has(chartKey); // Check if this specific chart is selected
  };

  // Helper function to check if KPIs for a section should be shown
  const shouldShowSectionKPIs = (sectionKey) => {
    if (!isPublic) {
      // In authenticated mode, check if any KPIs for this section are selected in local state
      const sectionKPIs = getDashboardSectionKPIs(sectionKey);
      return sectionKPIs.some((kpiKey) => selectedKPIs.has(kpiKey));
    }
    // In public mode, check if any KPIs for this section are selected from dashboard link
    if (publicKPISelections === null) {
      return true; // Show all KPIs if no selections saved (default behavior)
    }
    if (publicKPISelections.size === 0) {
      return false; // Empty Set means admin explicitly deselected all KPIs
    }
    // Check if any KPIs for this section are selected
    const sectionKPIs = getDashboardSectionKPIs(sectionKey);
    return sectionKPIs.some((kpiKey) => publicKPISelections.has(kpiKey));
  };

  // Helper function to check if charts for a section should be shown
  const shouldShowSectionCharts = (sectionKey) => {
    if (!isPublic) {
      // In authenticated mode, check if any charts for this section are selected in local state
      const sectionCharts = getDashboardSectionCharts(sectionKey);
      return sectionCharts.some((chart) => selectedCharts.has(chart.key));
    }
    // In public mode, check if any charts for this section are selected from dashboard link
    if (publicSelectedCharts === null) {
      return true; // Show all charts if no selections saved (default behavior)
    }
    if (publicSelectedCharts.size === 0) {
      return false; // Empty Set means admin explicitly deselected all charts
    }
    // Check if any charts for this section are selected
    const sectionCharts = getDashboardSectionCharts(sectionKey);
    return sectionCharts.some((chart) => publicSelectedCharts.has(chart.key));
  };

  // Helper function to check if a specific KPI should be shown in public view
  // Helper function to check if change period should be shown for a section
  const shouldShowChangePeriod = (sectionKey) => {
    if (isPublic) {
      // In public mode, check publicShowChangePeriod from dashboard link
      if (publicShowChangePeriod === null) {
        return true; // Default to showing change period if not set
      }
      return publicShowChangePeriod[sectionKey] !== false; // Show if true or undefined
    } else {
      // In authenticated mode, check showChangePeriod state
      return showChangePeriod[sectionKey] !== false; // Show if true or undefined
    }
  };

  const shouldShowKPI = (kpiKey) => {
    if (!isPublic) {
      // In authenticated mode, always show KPIs (filtered by selectedKPIs)
      return selectedKPIs.has(kpiKey);
    }
    // In public mode, check publicKPISelections
    if (publicKPISelections === null) {
      return true; // Show all KPIs if no selections saved (default behavior)
    }
    if (publicKPISelections.size === 0) {
      return false; // Empty Set means admin explicitly deselected all KPIs
    }
    return publicKPISelections.has(kpiKey); // Check if this specific KPI is selected
  };

  const handleSectionChange = (sectionKey, checked) => {
    const newSections = new Set(tempVisibleSections);
    const newSelectedKPIs = new Set(tempSelectedKPIs);
    const newSelectedCharts = new Set(tempSelectedCharts);

    // Get all KPIs and charts for this section
    const sectionKPIs = getDashboardSectionKPIs(sectionKey);
    const sectionCharts = getDashboardSectionCharts(sectionKey);

    if (checked) {
      // Enable section and all its children (KPIs + charts)
      newSections.add(sectionKey);
      sectionKPIs.forEach((kpi) => newSelectedKPIs.add(kpi));
      sectionCharts.forEach((chart) => newSelectedCharts.add(chart.key));
    } else {
      // Disable section and all its children (KPIs + charts)
      newSections.delete(sectionKey);
      sectionKPIs.forEach((kpi) => newSelectedKPIs.delete(kpi));
      sectionCharts.forEach((chart) => newSelectedCharts.delete(chart.key));
    }

    setTempVisibleSections(newSections);
    setTempSelectedKPIs(newSelectedKPIs);
    setTempSelectedCharts(newSelectedCharts);
  };

  const handleSelectAllSections = () => {
    const allSections = new Set([
      "ga4",
      "agency_analytics",
      "scrunch_ai",
      "all_performance_metrics",
    ]);
    const allKPIs = new Set(KPI_ORDER);
    const allCharts = new Set();

    // Get all charts from all sections
    allSections.forEach((sectionKey) => {
      getDashboardSectionCharts(sectionKey).forEach((chart) => {
        allCharts.add(chart.key);
      });
    });

    setTempVisibleSections(allSections);
    setTempSelectedKPIs(allKPIs);
    setTempSelectedCharts(allCharts);
    // Also set all change period flags to true
    setTempShowChangePeriod({
      ga4: true,
      agency_analytics: true,
      scrunch_ai: true,
      all_performance_metrics: true
    });
  };

  const handleDeselectAllSections = () => {
    setTempVisibleSections(new Set());
    setTempSelectedKPIs(new Set());
    setTempSelectedCharts(new Set());
  };

  // Get KPIs in the correct order, filtered by selection
  // Merge scrunchData KPIs with dashboardData KPIs for display
  // In public mode, show all KPIs; otherwise filter by selection
  const allKPIs = {
    ...(dashboardData?.kpis || {}),
    ...(scrunchData?.kpis || {}), // scrunchData KPIs take precedence
  };

  // All Performance Metrics KPIs (independent selection from sections)
  const performanceMetricsKPIs =
    Object.keys(allKPIs).length > 0
      ? isPublic
        ? // Public mode: Read from dashboard link
          publicPerformanceMetricsKPIs === null
            ? // No selection saved - show all available KPIs (default)
            KPI_ORDER.filter((key) => allKPIs[key]).map((key) => [
              key,
              allKPIs[key],
            ])
            : publicPerformanceMetricsKPIs.size === 0
            ? // Empty selection - admin explicitly deselected all
              []
            : // Show only selected KPIs from link
            KPI_ORDER.filter(
              (key) => allKPIs[key] && publicPerformanceMetricsKPIs.has(key)
            ).map((key) => [key, allKPIs[key]])
        : // Admin mode: Use state (defaults to all KPIs)
          KPI_ORDER.filter(
            (key) =>
              allKPIs[key] &&
              selectedPerformanceMetricsKPIs.has(key) &&
              key !== "competitive_benchmarking"
          ).map((key) => [key, allKPIs[key]])
      : [];

  // Legacy displayedKPIs - kept for backward compatibility but now uses performanceMetricsKPIs
  const displayedKPIs = performanceMetricsKPIs;

  return (
    <Box sx={{ p: 3 }}>
      {/* Progress loader for public reporting page */}
      {isPublic && isLoadingReport && (
        <Box
          sx={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 9999,
            bgcolor: "background.paper",
          }}
          role="status"
          aria-live="polite"
          aria-label="Loading report data"
        >
          <CircularProgress size={60} sx={{ mb: 3 }} />
          <Typography
            variant="h2"
            color="text.secondary"
            sx={{ textAlign: "center" }}
          >
            &ldquo;{loadingCaption}&rdquo;
          </Typography>
        </Box>
      )}
      {/* Header */}
      <Box mb={4}>
        <Box
          display="flex"
          justifyContent="space-between"
          alignItems="center"
          mb={2}
          position="relative"
        >
          {/* MacRAS Logo - Left side */}
          <Box
            component="img"
            src={logoMacraesTransparent}
            alt="MacRAE'S"
            sx={{
              maxHeight: isPublic ? 500 : 48,
              maxWidth: isPublic ? 1000 : 600,
              height: "auto",
              width: "auto",
              objectFit: "contain",
              borderRadius: 1,
              flexShrink: 0,
            }}
          />

          {/* Main heading - Centered client business name */}
          <Typography
            variant="h4"
            fontWeight={700}
            sx={{
              fontSize: "1.75rem",
              letterSpacing: "-0.02em",
              color: "text.primary",
              position: "absolute",
              left: {
                xs: "80%",
                sm: "80%",
                md: "50%",
                lg: "50%",
              },
              transform: "translateX(-50%)",
              textAlign: "center",
            }}
          >
            {(() => {
              // First priority: custom report title
              if (selectedClientReportTitle) {
                return selectedClientReportTitle;
              }

              // Second priority: stored client name
              if (selectedClientName) {
                return selectedClientName;
              }

              // Third priority: client name from clients array (authenticated view)
              if (selectedClientId && clients.length > 0) {
                const selectedClient = clients.find(
                  (c) => c.id === selectedClientId
                );
                if (selectedClient?.company_name) {
                  return selectedClient.company_name;
                }
              }

              // Fourth priority: client name from publicBrandInfo (public view)
              if (isPublic && publicBrandInfo) {
                if (publicBrandInfo.clientData?.company_name) {
                  return publicBrandInfo.clientData.company_name;
                }
                if (publicBrandInfo.name) {
                  return publicBrandInfo.name;
                }
              }

              // Fallback: default title
              return "MacRAE'S Reporting Dashboard";
            })()}
          </Typography>

          {/* Buttons - Right side */}
          <Box display="flex" gap={1.5} sx={{ flexShrink: 0 }}>
            {/* AI Overview button - only show in admin view */}
            {!isPublic && (
            <Button
              variant="contained"
              size="small"
              startIcon={<InsightsIcon sx={{ fontSize: 16 }} />}
              onClick={handleOpenOverview}
              disabled={
                !dashboardData ||
                !dashboardData.kpis ||
                Object.keys(dashboardData.kpis).length === 0
              }
              sx={{
                borderRadius: 2,
                px: 2,
                py: 0.75,
                fontWeight: 600,
                textTransform: "none",
                bgcolor: theme.palette.primary.main,
                "&:hover": {
                  bgcolor: theme.palette.primary.dark,
                },
                "&:disabled": {
                  bgcolor: alpha(theme.palette.primary.main, 0.3),
                },
              }}
              title="AI Overview of all metrics"
            >
              AI Overview
            </Button>
            )}
            {!isPublic && (
              <IconButton
                onClick={handleOpenKPISelector}
                sx={{
                  border: `1px solid ${theme.palette.divider}`,
                  borderRadius: 2,
                  bgcolor: "background.paper",
                  "&:hover": {
                    bgcolor: alpha(theme.palette.primary.main, 0.05),
                  },
                }}
                title="Configure KPIs for Public View"
              >
                <SettingsIcon sx={{ fontSize: 20 }} />
              </IconButton>
            )}
            {/* Refresh button - only show in admin view */}
            {!isPublic && (
            <Button
              variant="outlined"
              size="small"
              startIcon={<RefreshIcon sx={{ fontSize: 16 }} />}
              onClick={handleRefresh}
              sx={{
                borderRadius: 2,
                px: 2,
                py: 0.75,
                fontWeight: 600,
                bgcolor: "background.paper",
              }}
            >
              Refresh
            </Button>
            )}
          </Box>
        </Box>

        {/* Filters - Hidden for public view since date range selector is commented out */}
        {!isPublic && (
          <Paper
            elevation={0}
            sx={{
              p: 2.5,
              display: "flex",
              gap: 2,
              flexWrap: "wrap",
              alignItems: "center",
              border: `1px solid ${theme.palette.divider}`,
              borderRadius: 2,
              bgcolor: "background.paper",
            }}
          >
            <Autocomplete
              size="small"
              sx={{ minWidth: 300 }}
              options={clients}
              getOptionLabel={(option) => option.company_name || ""}
              value={clients.find((c) => c.id === selectedClientId) || null}
              onChange={(event, newValue) => {
                if (newValue) {
                  setSelectedClientId(newValue.id);
                  // Update slug and brand_id when client changes
                  if (newValue.url_slug) {
                    setSelectedBrandSlug(newValue.url_slug);
                  } else {
                    setSelectedBrandSlug(null);
                  }
                  // Set brand_id from client's scrunch_brand_id for data loading
                  if (newValue.scrunch_brand_id) {
                    setSelectedBrandId(newValue.scrunch_brand_id);
                  } else {
                    setSelectedBrandId(null);
                  }
                } else {
                  setSelectedClientId(null);
                  setSelectedBrandSlug(null);
                  setSelectedBrandId(null);
                }
              }}
              onInputChange={(event, newInputValue) => {
                handleClientSearch(newInputValue);
              }}
              loading={loadingClients}
              loadingText="Loading clients..."
              noOptionsText={
                clientSearchTerm
                  ? `No clients found for "${clientSearchTerm}"`
                  : "Type to search for clients..."
              }
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Select Client"
                  placeholder="Search clients..."
                  InputProps={{
                    ...params.InputProps,
                    endAdornment: (
                      <>
                        {loadingClients ? (
                          <CircularProgress color="inherit" size={20} />
                        ) : null}
                        {params.InputProps.endAdornment}
                      </>
                    ),
                  }}
                />
              )}
              filterOptions={(options) => options} // Disable client-side filtering, use server-side search
            />

            {!isPublic && (
              <Box display="flex" alignItems="center" gap={2} flexWrap="wrap">
                {/* Date Range Inputs */}
                <Box display="flex" alignItems="center" gap={1}>
                  <CalendarTodayIcon
                    sx={{ fontSize: 18, color: "text.secondary" }}
                  />
                  <TextField
                    label="Start Date"
                    type="date"
                    size="small"
                    value={startDate || ""}
                    onChange={(e) => {
                      if (e.target.value) {
                        setStartDate(e.target.value);
                        setDatePreset("Custom Range");
                      }
                    }}
                    InputLabelProps={{ shrink: true }}
                    sx={{ minWidth: 150 }}
                  />
                  <TextField
                    label="End Date"
                    type="date"
                    size="small"
                    value={endDate || ""}
                    onChange={(e) => {
                      if (e.target.value) {
                        setEndDate(e.target.value);
                        setDatePreset("Custom Range");
                      }
                    }}
                    InputLabelProps={{ shrink: true }}
                    sx={{ minWidth: 150 }}
                  />
                </Box>
                
                {/* Dashboard Links Section */}
                {selectedClientId && (
                  <Box display="flex" alignItems="center" gap={2}>
                    <FormControl size="small" sx={{ minWidth: 280 }}>
                      <InputLabel>Select or Create Link</InputLabel>
                      <Select
                        value={editingLink?.id || ""}
                        label="Select or Create Link"
                        onChange={(e) => {
                          const linkId = e.target.value;
                          if (linkId === "new") {
                            // Create new link
                            handleCreateLink();
                          } else if (linkId) {
                            // Edit existing link - automatically open dialog
                            const selectedLink = dashboardLinks.find(
                              (link) => link.id === linkId
                            );
                            if (selectedLink) {
                              handleEditLink(selectedLink);
                            }
                          } else {
                            // Clear selection
                            setEditingLink(null);
                            setLinkFormData({
                              name: "",
                              description: "",
                              start_date: startDate || "",
                              end_date: endDate || "",
                              enabled: true,
                              expires_at: "",
                              slug: "",
                            });
                            // Close dialog if open
                            setLinkDialogOpen(false);
                          }
                        }}
                        sx={{ textTransform: "none" }}
                        disabled={loadingLinks}
                      >
                        <MenuItem value="new">
                          <Box display="flex" alignItems="center" gap={1}>
                            <LinkIcon fontSize="small" />
                            <Typography>Create New Link</Typography>
                          </Box>
                        </MenuItem>
                        {dashboardLinks.length > 0 && (
                          <MenuItem value="" disabled>
                            <Typography
                              variant="caption"
                              color="text.secondary"
                            >
                              ─── Existing Links ───
                            </Typography>
                          </MenuItem>
                        )}
                        {dashboardLinks.map((link) => (
                          <MenuItem key={link.id} value={link.id}>
                            <Box
                              display="flex"
                              flexDirection="column"
                              alignItems="flex-start"
                            >
                              <Typography variant="body2" fontWeight={500}>
                                {link.name || link.slug || `Link ${link.id}`}
                              </Typography>
                              {link.description && (
                                <Typography
                                  variant="caption"
                                  color="text.secondary"
                                  sx={{ fontSize: "0.7rem" }}
                                >
                                  {link.description.substring(0, 50)}
                                  {link.description.length > 50 ? "..." : ""}
                                </Typography>
                              )}
                            </Box>
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                      <Button
                      variant={editingLink ? "contained" : "outlined"}
                        size="small"
                      onClick={handleOpenEditDialog}
                        startIcon={<LinkIcon />}
                        sx={{ textTransform: "none" }}
                      >
                      {editingLink ? "Edit Link" : "Create Link"}
                      </Button>
                    {editingLink && (
                      <Button
                        variant="outlined"
                        size="small"
                        onClick={() => handleCopyLinkUrl(editingLink)}
                        startIcon={<ContentCopyIcon />}
                        sx={{ textTransform: "none" }}
                        title="Copy link URL to clipboard"
                      >
                        Copy Link
                      </Button>
                    )}
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={handleResetKPISelections}
                      startIcon={<RefreshIcon />}
                      sx={{ textTransform: "none" }}
                      title="Reset KPI selections to default (all selected) and clear link selection"
                    >
                      Reset
                    </Button>
                  </Box>
                )}
              </Box>
            )}
          </Paper>
        )}
      </Box>

      {error && (
        <Alert
          severity="error"
          sx={{ mb: 3, borderRadius: 2 }}
          onClose={() => setError(null)}
        >
          {error}
        </Alert>
      )}

      {/* No Data Available Message */}
      {dashboardData?.no_data && (
        <Alert severity="info" sx={{ mb: 3, borderRadius: 2 }}>
          <Typography variant="h6" gutterBottom>
            No Data Available
          </Typography>
          <Typography variant="body2">
            {dashboardData.message ||
              "No data is currently available for this dashboard. Please check back later or contact support if you believe this is an error."}
          </Typography>
        </Alert>
      )}

      {/* Diagnostic Information - Only show in admin view */}
      {!isPublic && dashboardData?.diagnostics && !dashboardData?.no_data && (
        <Box mb={3}>
          {(!dashboardData.diagnostics.ga4_configured ||
            !dashboardData.diagnostics.agency_analytics_configured) && (
            <Alert severity="info" sx={{ mb: 2, borderRadius: 2 }}>
              <Typography variant="subtitle2" fontWeight={600} mb={1}>
                Missing Data Sources
              </Typography>
              <Box component="ul" sx={{ m: 0, pl: 2 }}>
                {!dashboardData.diagnostics.ga4_configured && (
                  <li>
                    <Typography variant="body2">
                      <strong>
                        {isPublic
                          ? "Website Analytics - Acquisition & User Behavior Insights"
                          : "GA4"}
                        :
                      </strong>{" "}
                      {isPublic
                        ? "Website analytics data is not available."
                        : "No GA4 property ID configured. Configure it in the brands table or use the GA4 sync endpoint."}
                    </Typography>
                  </li>
                )}
                {!dashboardData.diagnostics.agency_analytics_configured && (
                  <li>
                    <Typography variant="body2">
                      <strong>
                        {isPublic ? "SEO Performance" : "AgencyAnalytics"}:
                      </strong>{" "}
                      {isPublic
                        ? "SEO performance data is not available."
                        : "No campaigns linked to this brand. Sync Agency Analytics data and link campaigns to brands."}
                    </Typography>
                  </li>
                )}
              </Box>
              {!isPublic && (
                <Typography
                  variant="caption"
                  color="text.secondary"
                  mt={1}
                  display="block"
                >
                  Currently showing: {dashboardData.diagnostics.kpi_counts.ga4}{" "}
                  GA4 KPIs,{" "}
                  {dashboardData.diagnostics.kpi_counts.agency_analytics}{" "}
                  AgencyAnalytics KPIs,{" "}
                  {dashboardData.diagnostics.kpi_counts.scrunch} Scrunch KPIs
                </Typography>
              )}
            </Alert>
          )}
        </Box>
      )}

      {/* Tab Navigation - Always show in public view */}
      {isPublic && (
        <Box sx={{ borderBottom: 1, borderColor: "divider", mb: 3, px: 3 }}>
          <Tabs
            value={activeTab}
            onChange={(e, newValue) => setActiveTab(newValue)}
            sx={{
              "& .MuiTab-root": {
                textTransform: "none",
                fontWeight: 600,
                minHeight: 48,
              },
            }}
          >
            <Tab label="Executive Summary" />
            <Tab label="Detailed Metrics" />
          </Tabs>
        </Box>
      )}

      {loading ? (
        <Box
          display="flex"
          justifyContent="center"
          alignItems="center"
          minHeight="50vh"
        >
          <CircularProgress size={40} thickness={4} />
        </Box>
      ) : dashboardData && !dashboardData.no_data ? (
        <>
          {/* Executive Summary Tab Content - Show in public view when tab 0 is active */}
          {isPublic && activeTab === 0 && (
            <Box sx={{ px: 3 }}>
              {executiveSummary ? (
                <ExecutiveSummary summary={executiveSummary} theme={theme} />
              ) : (
                <Alert severity="info" sx={{ borderRadius: 2 }}>
                  <Typography variant="h6" gutterBottom>
                    Executive Summary Not Available
                  </Typography>
                  <Typography variant="body2">
                    The executive summary for this reporting period is not yet
                    available. Please check the Detailed Metrics tab for current
                    performance data.
                  </Typography>
                </Alert>
              )}
            </Box>
          )}

          {/* Detailed Metrics Tab Content - Show when not public, or tab 1 is active in public view */}
          {(!isPublic || activeTab === 1) && (
        <>
          {/* Google Analytics 4 Section */}
          {isSectionVisible("ga4") &&
            // Show section if it has KPIs (and KPIs are selected in public view) OR charts (and charts are selected in public view)
            ((shouldShowSectionKPIs("ga4") &&
                  (dashboardData?.kpis?.users ||
                    dashboardData?.kpis?.sessions)) ||
              (shouldShowSectionCharts("ga4") &&
                    dashboardData?.chart_data?.ga4_daily_comparison)) && (
              <SectionContainer
                title={
                      isPublic ? "Website Analytics " : "Google Analytics 4"
                }
                description="Acquisition & User Behavior Insights"
                loading={loading}
              >
                {/* GA4 Charts and Visualizations */}
                <Box sx={{ mb: 4 }}>
                  {/* <Typography 
                  variant="h6" 
                  fontWeight={600} 
                  mb={3}
                  sx={{ fontSize: '1.125rem', letterSpacing: '-0.01em' }}
                >
                  Charts & Visualizations
                </Typography> */}

                  {/* Performance Metrics - Donut Charts */}
                  {/* Only show Performance Metrics section if KPIs are selected (in public view) */}
                  {shouldShowSectionKPIs("ga4") && (
                    <>
                          {/* <Typography
                        variant="h6"
                        fontWeight={600}
                        mb={2}
                        sx={{ fontSize: "1.125rem", letterSpacing: "-0.01em" }}
                      >
                        Performance Metrics
                      </Typography> */}
                      <Grid 
                        container 
                        spacing={{ xs: 2, sm: 2.5, md: 3 }} 
                        sx={{ mb: { xs: 3, sm: 4 } }}
                      >
                        {/* Users KPI */}
                        {dashboardData?.kpis?.users &&
                          shouldShowKPI("users") && (
                            <Grid item xs={6} sm={6} md={3}>
                              <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.3, delay: 0.1 }}
                              >
                                <Card
                                  sx={{
                                    background: "#FFFFFF",
                                    border: `1px solid ${theme.palette.divider}`,
                                    borderRadius: 2,
                                    boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
                                    transition: "all 0.2s ease-in-out",
                                    "&:hover": {
                                          boxShadow:
                                            "0 4px 12px rgba(0,0,0,0.08)",
                                    },
                                  }}
                                >
                                  <CardContent sx={{ p: { xs: 2, sm: 2.5 } }}>
                                    <Box
                                      display="flex"
                                      alignItems="center"
                                      justifyContent="space-between"
                                      mb={{ xs: 1, sm: 1.5 }}
                                    >
                                      <Typography
                                        variant="body2"
                                        color="text.secondary"
                                        sx={{
                                          fontSize: { xs: "0.75rem", sm: "0.875rem" },
                                          fontWeight: 500,
                                        }}
                                      >
                                        Active Users
                                      </Typography>
                                          <IconButton
                                            size="small"
                                            sx={{ p: 0.5 }}
                                          >
                                        <TrendingUpIcon
                                          sx={{
                                            fontSize: 16,
                                            color: "text.secondary",
                                          }}
                                        />
                                      </IconButton>
                                    </Box>
                                    <Typography
                                      variant="h4"
                                      fontWeight={700}
                                      sx={{
                                        fontSize: { xs: "1.5rem", sm: "1.75rem" },
                                        letterSpacing: "-0.02em",
                                        mb: { xs: 0.5, sm: 1 },
                                        color: "text.primary",
                                      }}
                                    >
                                      {(() => {
                                        const value =
                                              dashboardData.kpis.users.value ||
                                              0;
                                        if (value >= 1000) {
                                          return `${(value / 1000).toFixed(
                                            1
                                          )}K`;
                                        }
                                        return value.toLocaleString();
                                      })()}
                                    </Typography>
                                    <Box
                                      sx={{
                                        minHeight: { xs: "20px", sm: "24px" },
                                        display: "flex",
                                        alignItems: "center",
                                      }}
                                    >
                                      {shouldShowChangePeriod("ga4") &&
                                        dashboardData.kpis.users.change !==
                                        undefined &&
                                        dashboardData.kpis.users.change !==
                                          null &&
                                        dashboardData.kpis.users.change >=
                                          0 && (
                                          <Box
                                            display="flex"
                                            alignItems="center"
                                            gap={0.5}
                                          >
                                            <TrendingUpIcon
                                              sx={{
                                                fontSize: { xs: 12, sm: 14 },
                                                color: "#34A853",
                                              }}
                                            />
                                            <Typography
                                              variant="body2"
                                              sx={{
                                                fontSize: { xs: "0.75rem", sm: "0.875rem" },
                                                fontWeight: 600,
                                                color: "#34A853",
                                              }}
                                            >
                                              {Math.abs(
                                                    dashboardData.kpis.users
                                                      .change
                                              ).toFixed(1)}
                                              % vs prev.
                                            </Typography>
                                          </Box>
                                        )}
                                    </Box>
                                  </CardContent>
                                </Card>
                              </motion.div>
                            </Grid>
                          )}

                        {/* Sessions */}
                        {dashboardData?.kpis?.sessions &&
                          shouldShowKPI("sessions") && (
                            <Grid item xs={6} sm={6} md={3}>
                              <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.3, delay: 0.15 }}
                              >
                                <Card
                                  sx={{
                                    background: "#FFFFFF",
                                    border: `1px solid ${theme.palette.divider}`,
                                    borderRadius: 2,
                                    boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
                                    transition: "all 0.2s ease-in-out",
                                    "&:hover": {
                                          boxShadow:
                                            "0 4px 12px rgba(0,0,0,0.08)",
                                    },
                                  }}
                                >
                                  <CardContent sx={{ p: { xs: 2, sm: 2.5 } }}>
                                    <Box
                                      display="flex"
                                      alignItems="center"
                                      justifyContent="space-between"
                                      mb={{ xs: 1, sm: 1.5 }}
                                    >
                                      <Typography
                                        variant="body2"
                                        color="text.secondary"
                                        sx={{
                                          fontSize: { xs: "0.75rem", sm: "0.875rem" },
                                          fontWeight: 500,
                                        }}
                                      >
                                        Sessions
                                      </Typography>
                                          <IconButton
                                            size="small"
                                            sx={{ p: 0.5 }}
                                          >
                                        <BarChartIcon
                                          sx={{
                                            fontSize: 16,
                                            color: "text.secondary",
                                          }}
                                        />
                                      </IconButton>
                                    </Box>
                                    <Typography
                                      variant="h4"
                                      fontWeight={700}
                                      sx={{
                                        fontSize: { xs: "1.5rem", sm: "1.75rem" },
                                        letterSpacing: "-0.02em",
                                        mb: { xs: 0.5, sm: 1 },
                                        color: "text.primary",
                                      }}
                                    >
                                      {(() => {
                                        const value =
                                              dashboardData.kpis.sessions
                                                .value || 0;
                                        if (value >= 1000) {
                                          return `${(value / 1000).toFixed(
                                            1
                                          )}K`;
                                        }
                                        return value.toLocaleString();
                                      })()}
                                    </Typography>
                                    <Box
                                      sx={{
                                        minHeight: { xs: "20px", sm: "24px" },
                                        display: "flex",
                                        alignItems: "center",
                                      }}
                                    >
                                          {shouldShowChangePeriod("ga4") &&
                                            dashboardData.kpis.sessions
                                              .change !== undefined &&
                                            dashboardData.kpis.sessions
                                              .change !== null &&
                                            dashboardData.kpis.sessions
                                              .change >= 0 && (
                                          <Box
                                            display="flex"
                                            alignItems="center"
                                            gap={0.5}
                                          >
                                            <TrendingUpIcon
                                              sx={{
                                                fontSize: { xs: 12, sm: 14 },
                                                color: "#34A853",
                                              }}
                                            />
                                            <Typography
                                              variant="body2"
                                              sx={{
                                                fontSize: { xs: "0.75rem", sm: "0.875rem" },
                                                fontWeight: 600,
                                                color: "#34A853",
                                              }}
                                            >
                                              {Math.abs(
                                                dashboardData.kpis.sessions
                                                  .change
                                              ).toFixed(1)}
                                              % vs prev.
                                            </Typography>
                                          </Box>
                                        )}
                                    </Box>
                                  </CardContent>
                                </Card>
                              </motion.div>
                            </Grid>
                          )}

                        {/* New Users */}
                        {dashboardData?.kpis?.new_users &&
                          shouldShowKPI("new_users") && (
                            <Grid item xs={6} sm={6} md={3}>
                              <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.3, delay: 0.2 }}
                              >
                                <Card
                                  sx={{
                                    background: "#FFFFFF",
                                    border: `1px solid ${theme.palette.divider}`,
                                    borderRadius: 2,
                                    boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
                                    transition: "all 0.2s ease-in-out",
                                    "&:hover": {
                                          boxShadow:
                                            "0 4px 12px rgba(0,0,0,0.08)",
                                    },
                                  }}
                                >
                                  <CardContent sx={{ p: { xs: 2, sm: 2.5 } }}>
                                    <Box
                                      display="flex"
                                      alignItems="center"
                                      justifyContent="space-between"
                                      mb={{ xs: 1, sm: 1.5 }}
                                    >
                                      <Typography
                                        variant="body2"
                                        color="text.secondary"
                                        sx={{
                                          fontSize: { xs: "0.75rem", sm: "0.875rem" },
                                          fontWeight: 500,
                                        }}
                                      >
                                        New users
                                      </Typography>
                                          <IconButton
                                            size="small"
                                            sx={{ p: 0.5 }}
                                          >
                                        <PersonAddIcon
                                          sx={{
                                            fontSize: 16,
                                            color: "text.secondary",
                                          }}
                                        />
                                      </IconButton>
                                    </Box>
                                    <Typography
                                      variant="h4"
                                      fontWeight={700}
                                      sx={{
                                        fontSize: { xs: "1.5rem", sm: "1.75rem" },
                                        letterSpacing: "-0.02em",
                                        mb: { xs: 0.5, sm: 1 },
                                        color: "text.primary",
                                      }}
                                    >
                                      {(() => {
                                        const value =
                                              dashboardData.kpis.new_users
                                                .value || 0;
                                        if (value >= 1000) {
                                          return `${(value / 1000).toFixed(
                                            1
                                          )}K`;
                                        }
                                        return value.toLocaleString();
                                      })()}
                                    </Typography>
                                    <Box
                                      sx={{
                                        minHeight: { xs: "20px", sm: "24px" },
                                        display: "flex",
                                        alignItems: "center",
                                      }}
                                    >
                                          {shouldShowChangePeriod("ga4") &&
                                            dashboardData.kpis.new_users
                                              .change !== undefined &&
                                            dashboardData.kpis.new_users
                                              .change !== null &&
                                            dashboardData.kpis.new_users
                                              .change >= 0 && (
                                              <Box
                                                display="flex"
                                                alignItems="center"
                                                gap={0.5}
                                              >
                                                <TrendingUpIcon
                                                  sx={{
                                                    fontSize: { xs: 12, sm: 14 },
                                                    color: "#34A853",
                                                  }}
                                                />
                                                <Typography
                                                  variant="body2"
                                                  sx={{
                                                    fontSize: { xs: "0.75rem", sm: "0.875rem" },
                                                    fontWeight: 600,
                                                    color: "#34A853",
                                                  }}
                                                >
                                                  {Math.abs(
                                                    dashboardData.kpis.new_users
                                                      .change
                                                  ).toFixed(1)}
                                                  % vs prev.
                                                </Typography>
                                              </Box>
                                            )}
                                        </Box>
                                      </CardContent>
                                    </Card>
                                  </motion.div>
                                </Grid>
                              )}

                            {/* Engaged Sessions */}
                            {dashboardData?.kpis?.engaged_sessions &&
                              shouldShowKPI("engaged_sessions") && (
                                <Grid item xs={6} sm={6} md={3}>
                                  <motion.div
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ duration: 0.3, delay: 0.3 }}
                                  >
                                    <Card
                                      sx={{
                                        background: "#FFFFFF",
                                        border: `1px solid ${theme.palette.divider}`,
                                        borderRadius: 2,
                                        boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
                                        transition: "all 0.2s ease-in-out",
                                        "&:hover": {
                                          boxShadow:
                                            "0 4px 12px rgba(0,0,0,0.08)",
                                        },
                                      }}
                                    >
                                      <CardContent sx={{ p: { xs: 2, sm: 2.5 } }}>
                                        <Box
                                          display="flex"
                                          alignItems="center"
                                          justifyContent="space-between"
                                          mb={{ xs: 1, sm: 1.5 }}
                                        >
                                          <Typography
                                            variant="body2"
                                            color="text.secondary"
                                            sx={{
                                              fontSize: { xs: "0.75rem", sm: "0.875rem" },
                                              fontWeight: 500,
                                            }}
                                          >
                                            Engaged Sessions
                                          </Typography>
                                          <IconButton
                                            size="small"
                                            sx={{ p: 0.5 }}
                                          >
                                            <PeopleIcon
                                              sx={{
                                                fontSize: 16,
                                                color: "text.secondary",
                                              }}
                                            />
                                          </IconButton>
                                        </Box>
                                        <Typography
                                          variant="h4"
                                          fontWeight={700}
                                          sx={{
                                            fontSize: { xs: "1.5rem", sm: "1.75rem" },
                                            letterSpacing: "-0.02em",
                                            mb: { xs: 0.5, sm: 1 },
                                            color: "text.primary",
                                          }}
                                        >
                                          {(() => {
                                            const value =
                                              dashboardData.kpis
                                                .engaged_sessions.value || 0;
                                            if (value >= 1000) {
                                              return `${(value / 1000).toFixed(
                                                1
                                              )}K`;
                                            }
                                            return value.toLocaleString();
                                          })()}
                                        </Typography>
                                        <Box
                                          sx={{
                                            minHeight: { xs: "20px", sm: "24px" },
                                            display: "flex",
                                            alignItems: "center",
                                          }}
                                        >
                                          {shouldShowChangePeriod("ga4") &&
                                            dashboardData.kpis.engaged_sessions
                                              .change !== undefined &&
                                            dashboardData.kpis.engaged_sessions
                                              .change !== null &&
                                            dashboardData.kpis.engaged_sessions
                                              .change >= 0 && (
                                              <Box
                                                display="flex"
                                                alignItems="center"
                                                gap={0.5}
                                              >
                                                <TrendingUpIcon
                                                  sx={{
                                                    fontSize: { xs: 12, sm: 14 },
                                                    color: "#34A853",
                                                  }}
                                                />
                                                <Typography
                                                  variant="body2"
                                                  sx={{
                                                    fontSize: { xs: "0.75rem", sm: "0.875rem" },
                                                    fontWeight: 600,
                                                    color: "#34A853",
                                                  }}
                                                >
                                                  {Math.abs(
                                                    dashboardData.kpis
                                                      .engaged_sessions.change
                                                  ).toFixed(1)}
                                                  % vs prev.
                                                </Typography>
                                              </Box>
                                            )}
                                        </Box>
                                      </CardContent>
                                    </Card>
                                  </motion.div>
                                </Grid>
                              )}

                            {/* Bounce Rate */}
                            {dashboardData?.kpis?.bounce_rate &&
                              shouldShowKPI("bounce_rate") && (
                                <Grid item xs={6} sm={6} md={3}>
                                  <motion.div
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ duration: 0.3, delay: 0.35 }}
                                  >
                                    <Card
                                      sx={{
                                        background: "#FFFFFF",
                                        border: `1px solid ${theme.palette.divider}`,
                                        borderRadius: 2,
                                        boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
                                        transition: "all 0.2s ease-in-out",
                                        "&:hover": {
                                          boxShadow:
                                            "0 4px 12px rgba(0,0,0,0.08)",
                                        },
                                      }}
                                    >
                                      <CardContent sx={{ p: { xs: 2, sm: 2.5 } }}>
                                        <Box
                                          display="flex"
                                          alignItems="center"
                                          justifyContent="space-between"
                                          mb={{ xs: 1, sm: 1.5 }}
                                        >
                                          <Typography
                                            variant="body2"
                                            color="text.secondary"
                                            sx={{
                                              fontSize: { xs: "0.75rem", sm: "0.875rem" },
                                              fontWeight: 500,
                                            }}
                                          >
                                            Bounce Rate
                                          </Typography>
                                          <IconButton
                                            size="small"
                                            sx={{ p: 0.5 }}
                                          >
                                            <TrendingDownIcon
                                              sx={{
                                                fontSize: 16,
                                                color: "text.secondary",
                                              }}
                                            />
                                          </IconButton>
                                        </Box>
                                        <Typography
                                          variant="h4"
                                          fontWeight={700}
                                          sx={{
                                            fontSize: { xs: "1.5rem", sm: "1.75rem" },
                                            letterSpacing: "-0.02em",
                                            mb: { xs: 0.5, sm: 1 },
                                            color: "text.primary",
                                          }}
                                        >
                                          {(() => {
                                            const kpi =
                                              dashboardData.kpis.bounce_rate;
                                            const value = kpi.value || 0;
                                            const normalizedValue = normalizePercentage(value);
                                            return `${normalizedValue.toFixed(1)}%`;
                                          })()}
                                        </Typography>
                                        <Box
                                          sx={{
                                            minHeight: { xs: "20px", sm: "24px" },
                                            display: "flex",
                                            alignItems: "center",
                                          }}
                                        >
                                          {shouldShowChangePeriod("ga4") &&
                                            dashboardData.kpis.bounce_rate
                                              .change !== undefined &&
                                            dashboardData.kpis.bounce_rate
                                              .change !== null &&
                                            dashboardData.kpis.bounce_rate
                                              .change <= 0 && (
                                              <Box
                                                display="flex"
                                                alignItems="center"
                                                gap={0.5}
                                              >
                                                <TrendingDownIcon
                                                  sx={{
                                                    fontSize: { xs: 12, sm: 14 },
                                                    color: "#34A853",
                                                  }}
                                                />
                                                <Typography
                                                  variant="body2"
                                                  sx={{
                                                    fontSize: { xs: "0.75rem", sm: "0.875rem" },
                                                    fontWeight: 600,
                                                    color: "#34A853",
                                                  }}
                                                >
                                                  {(() => {
                                                    const change = dashboardData.kpis.bounce_rate.change || 0;
                                                    const absChange = Math.abs(change);
                                                    const normalizedChange = normalizePercentage(absChange);
                                                    return `${normalizedChange.toFixed(1)}%`;
                                                  })()}
                                                  {" "}vs prev.
                                                </Typography>
                                              </Box>
                                            )}
                                        </Box>
                                      </CardContent>
                                    </Card>
                                  </motion.div>
                                </Grid>
                              )}

                            {/* Avg Session Duration */}
                            {dashboardData?.kpis?.avg_session_duration &&
                              shouldShowKPI("avg_session_duration") && (
                                <Grid item xs={6} sm={6} md={3}>
                                  <motion.div
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ duration: 0.3, delay: 0.4 }}
                                  >
                                    <Card
                                      sx={{
                                        background: "#FFFFFF",
                                        border: `1px solid ${theme.palette.divider}`,
                                        borderRadius: 2,
                                        boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
                                        transition: "all 0.2s ease-in-out",
                                        "&:hover": {
                                          boxShadow:
                                            "0 4px 12px rgba(0,0,0,0.08)",
                                        },
                                      }}
                                    >
                                      <CardContent sx={{ p: { xs: 2, sm: 2.5 } }}>
                                        <Box
                                          display="flex"
                                          alignItems="center"
                                          justifyContent="space-between"
                                          mb={{ xs: 1, sm: 1.5 }}
                                        >
                                          <Typography
                                            variant="body2"
                                            color="text.secondary"
                                            sx={{
                                              fontSize: { xs: "0.75rem", sm: "0.875rem" },
                                              fontWeight: 500,
                                            }}
                                          >
                                            Avg Session Duration
                                          </Typography>
                                          <IconButton
                                            size="small"
                                            sx={{ p: 0.5 }}
                                          >
                                            <AccessTimeIcon
                                              sx={{
                                                fontSize: 16,
                                                color: "text.secondary",
                                              }}
                                            />
                                          </IconButton>
                                        </Box>
                                        <Typography
                                          variant="h4"
                                          fontWeight={700}
                                          sx={{
                                            fontSize: { xs: "1.5rem", sm: "1.75rem" },
                                            letterSpacing: "-0.02em",
                                            mb: { xs: 0.5, sm: 1 },
                                            color: "text.primary",
                                          }}
                                        >
                                          {(() => {
                                            const kpi =
                                              dashboardData.kpis
                                                .avg_session_duration;
                                            const duration = kpi.value || 0;
                                            if (kpi.format === "duration") {
                                              const minutes = Math.floor(
                                                duration / 60
                                              );
                                              const seconds = Math.floor(
                                                duration % 60
                                              );
                                              return `${minutes}:${seconds
                                                .toString()
                                                .padStart(2, "0")}`;
                                            }
                                            const minutes = Math.floor(
                                              duration / 60
                                            );
                                            const seconds = Math.floor(
                                              duration % 60
                                            );
                                            return `${minutes}:${seconds
                                              .toString()
                                              .padStart(2, "0")}`;
                                          })()}
                                        </Typography>
                                        <Box
                                          sx={{
                                            minHeight: { xs: "20px", sm: "24px" },
                                            display: "flex",
                                            alignItems: "center",
                                          }}
                                        >
                                          {shouldShowChangePeriod("ga4") &&
                                            dashboardData.kpis
                                              .avg_session_duration.change !==
                                        undefined &&
                                            dashboardData.kpis
                                              .avg_session_duration.change !==
                                          null &&
                                            dashboardData.kpis
                                              .avg_session_duration.change >=
                                          0 && (
                                          <Box
                                            display="flex"
                                            alignItems="center"
                                            gap={0.5}
                                          >
                                            <TrendingUpIcon
                                              sx={{
                                                fontSize: { xs: 12, sm: 14 },
                                                color: "#34A853",
                                              }}
                                            />
                                            <Typography
                                              variant="body2"
                                              sx={{
                                                fontSize: { xs: "0.75rem", sm: "0.875rem" },
                                                fontWeight: 600,
                                                color: "#34A853",
                                              }}
                                            >
                                              {Math.abs(
                                                      dashboardData.kpis
                                                        .avg_session_duration
                                                  .change
                                              ).toFixed(1)}
                                              % vs prev.
                                            </Typography>
                                          </Box>
                                        )}
                                    </Box>
                                      </CardContent>
                                    </Card>
                                  </motion.div>
                                </Grid>
                              )}

                            {/* Engagement Rate */}
                            {dashboardData?.kpis?.ga4_engagement_rate &&
                              shouldShowKPI("ga4_engagement_rate") && (
                                <Grid item xs={6} sm={6} md={3}>
                                  <motion.div
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ duration: 0.3, delay: 0.45 }}
                                  >
                                    <Card
                                      sx={{
                                        background: "#FFFFFF",
                                        border: `1px solid ${theme.palette.divider}`,
                                        borderRadius: 2,
                                        boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
                                        transition: "all 0.2s ease-in-out",
                                        "&:hover": {
                                          boxShadow:
                                            "0 4px 12px rgba(0,0,0,0.08)",
                                        },
                                      }}
                                    >
                                      <CardContent sx={{ p: { xs: 2, sm: 2.5 } }}>
                                        <Box
                                          display="flex"
                                          alignItems="center"
                                          justifyContent="space-between"
                                          mb={{ xs: 1, sm: 1.5 }}
                                        >
                                          <Typography
                                            variant="body2"
                                            color="text.secondary"
                                            sx={{
                                              fontSize: { xs: "0.75rem", sm: "0.875rem" },
                                              fontWeight: 500,
                                            }}
                                          >
                                            Engagement Rate
                                          </Typography>
                                          <IconButton
                                            size="small"
                                            sx={{ p: 0.5 }}
                                          >
                                            <TrendingUpIcon
                                              sx={{
                                                fontSize: 16,
                                                color: "text.secondary",
                                              }}
                                            />
                                          </IconButton>
                                        </Box>
                                        <Typography
                                          variant="h4"
                                          fontWeight={700}
                                          sx={{
                                            fontSize: { xs: "1.5rem", sm: "1.75rem" },
                                            letterSpacing: "-0.02em",
                                            mb: { xs: 0.5, sm: 1 },
                                            color: "text.primary",
                                          }}
                                        >
                                          {(() => {
                                            const kpi =
                                              dashboardData.kpis
                                                .ga4_engagement_rate;
                                            const value = kpi.value || 0;
                                            const normalizedValue = normalizePercentage(value);
                                            return `${normalizedValue.toFixed(1)}%`;
                                          })()}
                                        </Typography>
                                        <Box
                                          sx={{
                                            minHeight: { xs: "20px", sm: "24px" },
                                            display: "flex",
                                            alignItems: "center",
                                          }}
                                        >
                                          {shouldShowChangePeriod("ga4") &&
                                            dashboardData.kpis
                                              .ga4_engagement_rate.change !==
                                              undefined &&
                                            dashboardData.kpis
                                              .ga4_engagement_rate.change !==
                                              null &&
                                            dashboardData.kpis
                                              .ga4_engagement_rate.change >=
                                              0 && (
                                                <Box
                                                  display="flex"
                                                  alignItems="center"
                                                  gap={0.5}
                                                >
                                                  <TrendingUpIcon
                                                    sx={{
                                                      fontSize: { xs: 12, sm: 14 },
                                                      color: "#34A853",
                                                    }}
                                                  />
                                                  <Typography
                                                    variant="body2"
                                                    sx={{
                                                      fontSize: { xs: "0.75rem", sm: "0.875rem" },
                                                      fontWeight: 600,
                                                      color: "#34A853",
                                                    }}
                                                  >
                                                    {(() => {
                                                      const change = dashboardData.kpis.ga4_engagement_rate.change || 0;
                                                      // Divide by 100 if change appears to be already multiplied
                                                      const absChange = Math.abs(change);
                                                      const normalizedChange = normalizePercentage(absChange);
                                                      return `${normalizedChange.toFixed(1)}%`;
                                                    })()}
                                                    {" "}vs prev.
                                            </Typography>
                                          </Box>
                                        )}
                                    </Box>
                                  </CardContent>
                                </Card>
                              </motion.div>
                            </Grid>
                          )}

                        {/* Conversions */}
                        {dashboardData?.kpis?.conversions &&
                          shouldShowKPI("conversions") && (
                          <Grid item xs={6} sm={6} md={3}>
                            <motion.div
                              initial={{ opacity: 0, y: 20 }}
                              animate={{ opacity: 1, y: 0 }}
                                    transition={{ duration: 0.3, delay: 0.5 }}
                            >
                              <Card
                                sx={{
                                  background: "#FFFFFF",
                                  border: `1px solid ${theme.palette.divider}`,
                                  borderRadius: 2,
                                  boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
                                  transition: "all 0.2s ease-in-out",
                                  "&:hover": {
                                          boxShadow:
                                            "0 4px 12px rgba(0,0,0,0.08)",
                                  },
                                }}
                              >
                                <CardContent sx={{ p: { xs: 2, sm: 2.5 } }}>
                                  <Box
                                    display="flex"
                                    alignItems="center"
                                    justifyContent="space-between"
                                    mb={{ xs: 1, sm: 1.5 }}
                                  >
                                    <Typography
                                      variant="body2"
                                      color="text.secondary"
                                      sx={{
                                        fontSize: { xs: "0.75rem", sm: "0.875rem" },
                                        fontWeight: 500,
                                      }}
                                    >
                                      Conversions
                                    </Typography>
                                          <IconButton
                                            size="small"
                                            sx={{ p: 0.5 }}
                                          >
                                      <TrendingUpIcon
                                        sx={{
                                          fontSize: 16,
                                          color: "text.secondary",
                                        }}
                                      />
                                    </IconButton>
                                  </Box>
                                  <Typography
                                    variant="h4"
                                    fontWeight={700}
                                    sx={{
                                      fontSize: { xs: "1.5rem", sm: "1.75rem" },
                                      letterSpacing: "-0.02em",
                                      mb: { xs: 0.5, sm: 1 },
                                      color: "text.primary",
                                    }}
                                  >
                                    {(() => {
                                            const kpi =
                                              dashboardData.kpis.conversions;
                                      const value = kpi.value || 0;
                                      if (value >= 1000) {
                                              return `${(value / 1000).toFixed(
                                                1
                                              )}K`;
                                      }
                                      return value.toLocaleString();
                                    })()}
                                  </Typography>
                                  <Box
                                    sx={{
                                      minHeight: "24px",
                                      display: "flex",
                                      alignItems: "center",
                                    }}
                                  >
                                    {(() => {
                                            const kpi =
                                              dashboardData.kpis.conversions;
                                      return (
                                        shouldShowChangePeriod("ga4") &&
                                        kpi.change !== undefined &&
                                        kpi.change !== null &&
                                        kpi.change >= 0 && (
                                          <Box
                                            display="flex"
                                            alignItems="center"
                                            gap={0.5}
                                          >
                                            <TrendingUpIcon
                                              sx={{
                                                fontSize: 14,
                                                color: "#34A853",
                                              }}
                                            />
                                            <Typography
                                              variant="body2"
                                              sx={{
                                                fontSize: "0.875rem",
                                                fontWeight: 600,
                                                color: "#34A853",
                                              }}
                                            >
                                                    {Math.abs(
                                                      kpi.change
                                                    ).toFixed(1)}
                                                    %
                                            </Typography>
                                          </Box>
                                        )
                                      );
                                    })()}
                                  </Box>
                                </CardContent>
                              </Card>
                            </motion.div>
                          </Grid>
                        )}
                      </Grid>
                    </>
                  )}

                  {/* GA4 Traffic Overview Cards - Additional Metrics */}
                      {/* COMMENTED OUT: Traffic Overview cards moved to Performance Metrics section */}
                      {false &&
                        dashboardData?.chart_data?.ga4_traffic_overview &&
                    isChartVisible("ga4_traffic_overview") && (
                      <Grid container spacing={2.5} sx={{ mb: 4 }}>
                        {/* Total Sessions - Only show if sessions KPI is selected */}
                        {shouldShowKPI("sessions") && (
                          <Grid item xs={12} md={3}>
                            <motion.div
                              initial={{ opacity: 0, y: 20 }}
                              animate={{ opacity: 1, y: 0 }}
                              transition={{ duration: 0.5, delay: 0.5 }}
                            >
                              <Card
                                sx={{
                                  background:
                                    "linear-gradient(135deg, rgba(52, 199, 89, 0.04) 0%, rgba(90, 200, 250, 0.04) 100%)",
                                  border: `1px solid ${alpha(
                                    theme.palette.success.main,
                                    0.08
                                  )}`,
                                  borderRadius: 2,
                                  boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
                                }}
                              >
                                <CardContent sx={{ p: 3 }}>
                                  <Box
                                    display="flex"
                                    alignItems="center"
                                    justifyContent="space-between"
                                    mb={2}
                                  >
                                    <Typography
                                      variant="caption"
                                      color="text.secondary"
                                      sx={{
                                        fontSize: "11px",
                                        fontWeight: 600,
                                        textTransform: "uppercase",
                                        letterSpacing: "0.05em",
                                      }}
                                    >
                                      Total Sessions
                                    </Typography>
                                    <BarChartIcon
                                      sx={{
                                        fontSize: 20,
                                        color: "success.main",
                                        opacity: 0.6,
                                      }}
                                    />
                                  </Box>
                                  <Typography
                                    variant="h3"
                                    fontWeight={700}
                                    color="success.main"
                                    sx={{
                                      fontSize: "36px",
                                      letterSpacing: "-0.02em",
                                      mb: 1,
                                    }}
                                  >
                                    {dashboardData.chart_data.ga4_traffic_overview.sessions.toLocaleString()}
                                  </Typography>
                                  <Box
                                    sx={{
                                      minHeight: "24px",
                                      display: "flex",
                                      alignItems: "center",
                                    }}
                                  >
                                    {dashboardData.chart_data
                                          .ga4_traffic_overview
                                          .sessionsChange >= 0 && (
                                      <Box
                                        display="flex"
                                        alignItems="center"
                                        gap={0.5}
                                      >
                                        <TrendingUpIcon
                                          sx={{
                                            fontSize: 14,
                                            color: "success.main",
                                          }}
                                        />
                                        <Typography
                                          variant="body2"
                                          sx={{
                                            fontSize: "13px",
                                            fontWeight: 600,
                                            color: "success.main",
                                          }}
                                        >
                                          {Math.abs(
                                            dashboardData.chart_data
                                              .ga4_traffic_overview
                                              .sessionsChange
                                          ).toFixed(1)}
                                          %
                                        </Typography>
                                        <Typography
                                          variant="caption"
                                          color="text.secondary"
                                          sx={{ fontSize: "12px" }}
                                        >
                                          vs last period
                                        </Typography>
                                      </Box>
                                    )}
                                  </Box>
                                </CardContent>
                              </Card>
                            </motion.div>
                          </Grid>
                        )}

                        {/* Engaged Sessions - Only show if engaged_sessions KPI is selected */}
                        {shouldShowKPI("engaged_sessions") && (
                          <Grid item xs={12} md={3}>
                            <motion.div
                              initial={{ opacity: 0, y: 20 }}
                              animate={{ opacity: 1, y: 0 }}
                              transition={{ duration: 0.5, delay: 0.6 }}
                            >
                              <Card
                                sx={{
                                  background:
                                    "linear-gradient(135deg, rgba(0, 122, 255, 0.04) 0%, rgba(88, 86, 214, 0.04) 100%)",
                                  border: `1px solid ${alpha(
                                    theme.palette.primary.main,
                                    0.08
                                  )}`,
                                  borderRadius: 2,
                                  boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
                                }}
                              >
                                <CardContent sx={{ p: 3 }}>
                                  <Box
                                    display="flex"
                                    alignItems="center"
                                    justifyContent="space-between"
                                    mb={2}
                                  >
                                    <Typography
                                      variant="caption"
                                      color="text.secondary"
                                      sx={{
                                        fontSize: "11px",
                                        fontWeight: 600,
                                        textTransform: "uppercase",
                                        letterSpacing: "0.05em",
                                      }}
                                    >
                                      Engaged Sessions
                                    </Typography>
                                    <PeopleIcon
                                      sx={{
                                        fontSize: 20,
                                        color: "primary.main",
                                        opacity: 0.6,
                                      }}
                                    />
                                  </Box>
                                  <Typography
                                    variant="h3"
                                    fontWeight={700}
                                    sx={{
                                      fontSize: "36px",
                                      letterSpacing: "-0.02em",
                                      mb: 1,
                                    }}
                                  >
                                    {dashboardData.chart_data.ga4_traffic_overview.engagedSessions.toLocaleString()}
                                  </Typography>
                                  <Box
                                    sx={{
                                      minHeight: "24px",
                                      display: "flex",
                                      alignItems: "center",
                                    }}
                                  >
                                    {dashboardData.chart_data
                                      .ga4_traffic_overview
                                      .engagedSessionsChange >= 0 && (
                                      <Box
                                        display="flex"
                                        alignItems="center"
                                        gap={0.5}
                                      >
                                        <TrendingUpIcon
                                          sx={{
                                            fontSize: 14,
                                            color: "success.main",
                                          }}
                                        />
                                        <Typography
                                          variant="body2"
                                          sx={{
                                            fontSize: "13px",
                                            fontWeight: 600,
                                            color: "success.main",
                                          }}
                                        >
                                          {Math.abs(
                                            dashboardData.chart_data
                                              .ga4_traffic_overview
                                              .engagedSessionsChange
                                          ).toFixed(1)}
                                          %
                                        </Typography>
                                        <Typography
                                          variant="caption"
                                          color="text.secondary"
                                          sx={{ fontSize: "12px" }}
                                        >
                                          vs last period
                                        </Typography>
                                      </Box>
                                    )}
                                  </Box>
                                </CardContent>
                              </Card>
                            </motion.div>
                          </Grid>
                        )}

                        {/* Avg. Session Duration - Only show if avg_session_duration KPI is selected */}
                        {shouldShowKPI("avg_session_duration") && (
                          <Grid item xs={12} md={3}>
                            <motion.div
                              initial={{ opacity: 0, y: 20 }}
                              animate={{ opacity: 1, y: 0 }}
                              transition={{ duration: 0.5, delay: 0.7 }}
                            >
                              <Card
                                sx={{
                                  background:
                                    "linear-gradient(135deg, rgba(255, 149, 0, 0.04) 0%, rgba(255, 45, 85, 0.04) 100%)",
                                  border: `1px solid ${alpha(
                                    theme.palette.warning.main,
                                    0.08
                                  )}`,
                                  borderRadius: 2,
                                  boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
                                }}
                              >
                                <CardContent sx={{ p: 3 }}>
                                  <Box
                                    display="flex"
                                    alignItems="center"
                                    justifyContent="space-between"
                                    mb={2}
                                  >
                                    <Typography
                                      variant="caption"
                                      color="text.secondary"
                                      sx={{
                                        fontSize: "11px",
                                        fontWeight: 600,
                                        textTransform: "uppercase",
                                        letterSpacing: "0.05em",
                                      }}
                                    >
                                      Avg. Session Duration
                                    </Typography>
                                    <AccessTimeIcon
                                      sx={{
                                        fontSize: 20,
                                        color: "warning.main",
                                        opacity: 0.6,
                                      }}
                                    />
                                  </Box>
                                  <Typography
                                    variant="h3"
                                    fontWeight={700}
                                    color="warning.main"
                                    sx={{
                                      fontSize: "36px",
                                      letterSpacing: "-0.02em",
                                      mb: 1,
                                    }}
                                  >
                                    {(() => {
                                    })()}
                                  </Typography>
                                  <Box
                                    sx={{
                                      minHeight: "24px",
                                      display: "flex",
                                      alignItems: "center",
                                    }}
                                  >
                                    {dashboardData.chart_data
                                      .ga4_traffic_overview
                                      .avgSessionDurationChange >= 0 && (
                                      <Box
                                        display="flex"
                                        alignItems="center"
                                        gap={0.5}
                                      >
                                        <TrendingUpIcon
                                          sx={{
                                            fontSize: 14,
                                            color: "success.main",
                                          }}
                                        />
                                        <Typography
                                          variant="body2"
                                          sx={{
                                            fontSize: "13px",
                                            fontWeight: 600,
                                            color: "success.main",
                                          }}
                                        >
                                          {Math.abs(
                                            dashboardData.chart_data
                                              .ga4_traffic_overview
                                              .avgSessionDurationChange
                                          ).toFixed(1)}
                                          %
                                        </Typography>
                                        <Typography
                                          variant="caption"
                                          color="text.secondary"
                                          sx={{ fontSize: "12px" }}
                                        >
                                          vs last period
                                        </Typography>
                                      </Box>
                                    )}
                                  </Box>
                                </CardContent>
                              </Card>
                            </motion.div>
                          </Grid>
                        )}

                        {/* Engagement Rate - Only show if ga4_engagement_rate KPI is selected */}
                        {shouldShowKPI("ga4_engagement_rate") && (
                          <Grid item xs={12} md={3}>
                            <motion.div
                              initial={{ opacity: 0, y: 20 }}
                              animate={{ opacity: 1, y: 0 }}
                              transition={{ duration: 0.5, delay: 0.8 }}
                            >
                              <Card
                                sx={{
                                  background:
                                    "linear-gradient(135deg, rgba(88, 86, 214, 0.04) 0%, rgba(0, 122, 255, 0.04) 100%)",
                                  border: `1px solid ${alpha(
                                    theme.palette.secondary.main,
                                    0.08
                                  )}`,
                                  borderRadius: 2,
                                  boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
                                }}
                              >
                                <CardContent sx={{ p: 3 }}>
                                  <Box
                                    display="flex"
                                    alignItems="center"
                                    justifyContent="space-between"
                                    mb={2}
                                  >
                                    <Typography
                                      variant="caption"
                                      color="text.secondary"
                                      sx={{
                                        fontSize: "11px",
                                        fontWeight: 600,
                                        textTransform: "uppercase",
                                        letterSpacing: "0.05em",
                                      }}
                                    >
                                      Engagement Rate
                                    </Typography>
                                    <VisibilityIcon
                                      sx={{
                                        fontSize: 20,
                                        color: "secondary.main",
                                        opacity: 0.6,
                                      }}
                                    />
                                  </Box>
                                  <Typography
                                    variant="h3"
                                    fontWeight={700}
                                    color="secondary.main"
                                    sx={{
                                      fontSize: "36px",
                                      letterSpacing: "-0.02em",
                                      mb: 1,
                                    }}
                                  >
                                    {(() => {
                                    })()}
                                  </Typography>
                                  <Box
                                    sx={{
                                      minHeight: "24px",
                                      display: "flex",
                                      alignItems: "center",
                                    }}
                                  >
                                    {dashboardData.chart_data
                                      .ga4_traffic_overview
                                      .engagementRateChange >= 0 && (
                                      <Box
                                        display="flex"
                                        alignItems="center"
                                        gap={0.5}
                                      >
                                        <TrendingUpIcon
                                          sx={{
                                            fontSize: 14,
                                            color: "success.main",
                                          }}
                                        />
                                        <Typography
                                          variant="body2"
                                          sx={{
                                            fontSize: "13px",
                                            fontWeight: 600,
                                            color: "success.main",
                                          }}
                                        >
                                          {(() => {
                                          })()}
                                        </Typography>
                                        <Typography
                                          variant="caption"
                                          color="text.secondary"
                                          sx={{ fontSize: "12px" }}
                                        >
                                          vs last period
                                        </Typography>
                                      </Box>
                                    )}
                                  </Box>
                                </CardContent>
                              </Card>
                            </motion.div>
                          </Grid>
                        )}
                      </Grid>
                    )}

                  {/* GA4 Performance Charts - Prominent Line Graphs */}
                      {dashboardData.chart_data?.ga4_daily_comparison?.length >
                        0 &&
                    isChartVisible("ga4_daily_comparison") && (
                      <Box sx={{ mt: 4, mb: 4 }}>
                        <Grid container spacing={3}>
                          {/* Active Users Chart - Full Width (Primary Chart) */}
                          <Grid item xs={12}>
                            <ChartCard
                              title="Active Users"
                              badge={getBadgeLabel("GA4")}
                              badgeColor={CHART_COLORS.ga4.primary}
                              height={500}
                              animationDelay={0.3}
                            >
                              <LineChartEnhanced
                                data={
                                      dashboardData.chart_data
                                        .ga4_daily_comparison
                                }
                                dataKey="date"
                                lines={[
                                  {
                                    dataKey: "current_users",
                                    name: getDateRangeLabel(),
                                    color: CHART_COLORS.comparison.current,
                                    strokeWidth: 3,
                                  },
                                  ...(shouldShowChangePeriod("ga4") ? [{
                                    dataKey: "previous_users",
                                    name: "Previous period",
                                    color: CHART_COLORS.comparison.previous,
                                    strokeWidth: 2.5,
                                    strokeDasharray: "5 5",
                                  }] : []),
                                ]}
                                xAxisFormatter={formatDateForAxis}
                                formatter={(value) => [
                                  value.toLocaleString(),
                                  "Users",
                                ]}
                                labelFormatter={(label) => {
                                  if (label && label.length === 8) {
                                    const year = label.substring(0, 4);
                                    const month = label.substring(4, 6);
                                    const day = label.substring(6, 8);
                                    return `${day} ${getMonthName(
                                      parseInt(month)
                                    )} ${year}`;
                                  }
                                  return label;
                                }}
                                height={400}
                              />
                            </ChartCard>
                          </Grid>

                          {/* Sessions Comparison Chart */}
                          <Grid item xs={12} md={6}>
                            <ChartCard
                              title="Sessions"
                              badge={getBadgeLabel("GA4")}
                              badgeColor={CHART_COLORS.ga4.primary}
                              height={400}
                              animationDelay={0.35}
                            >
                              <LineChartEnhanced
                                data={
                                      dashboardData.chart_data
                                        .ga4_daily_comparison
                                }
                                dataKey="date"
                                lines={[
                                  {
                                    dataKey: "current_sessions",
                                    name: getDateRangeLabel(),
                                    color: CHART_COLORS.comparison.current,
                                    strokeWidth: 3,
                                  },
                                  ...(shouldShowChangePeriod("ga4") ? [{
                                    dataKey: "previous_sessions",
                                    name: "Previous period",
                                    color: CHART_COLORS.comparison.previous,
                                    strokeWidth: 2.5,
                                    strokeDasharray: "5 5",
                                  }] : []),
                                ]}
                                xAxisFormatter={formatDateForAxis}
                                formatter={(value) => [
                                  value.toLocaleString(),
                                  "Sessions",
                                ]}
                                labelFormatter={(label) => {
                                  if (label && label.length === 8) {
                                    const year = label.substring(0, 4);
                                    const month = label.substring(4, 6);
                                    const day = label.substring(6, 8);
                                    return `${day} ${getMonthName(
                                      parseInt(month)
                                    )} ${year}`;
                                  }
                                  return label;
                                }}
                                height={320}
                              />
                            </ChartCard>
                          </Grid>

                          {/* New Users Comparison Chart */}
                          <Grid item xs={12} md={6}>
                            <ChartCard
                              title="New Users"
                              badge={getBadgeLabel("GA4")}
                              badgeColor={CHART_COLORS.ga4.primary}
                              height={400}
                              animationDelay={0.4}
                            >
                              <LineChartEnhanced
                                data={
                                      dashboardData.chart_data
                                        .ga4_daily_comparison
                                }
                                dataKey="date"
                                lines={[
                                  {
                                    dataKey: "current_new_users",
                                    name: getDateRangeLabel(),
                                    color: CHART_COLORS.success,
                                    strokeWidth: 3,
                                  },
                                  ...(shouldShowChangePeriod("ga4") ? [{
                                    dataKey: "previous_new_users",
                                    name: "Previous period",
                                    color: CHART_COLORS.comparison.previous,
                                    strokeWidth: 2.5,
                                    strokeDasharray: "5 5",
                                  }] : []),
                                ]}
                                xAxisFormatter={formatDateForAxis}
                                formatter={(value) => [
                                  value.toLocaleString(),
                                  "New Users",
                                ]}
                                labelFormatter={(label) => {
                                  if (label && label.length === 8) {
                                    const year = label.substring(0, 4);
                                    const month = label.substring(4, 6);
                                    const day = label.substring(6, 8);
                                    return `${day} ${getMonthName(
                                      parseInt(month)
                                    )} ${year}`;
                                  }
                                  return label;
                                }}
                                height={320}
                              />
                            </ChartCard>
                          </Grid>

                          {/* Conversions Comparison Chart */}
                          {/* {dashboardData.chart_data.ga4_daily_comparison.some(
                            (d) =>
                              d.current_conversions > 0 ||
                              d.previous_conversions > 0
                          ) && (
                            <Grid item xs={12} md={6}>
                              <ChartCard
                                title="Conversions"
                                badge={getBadgeLabel("GA4")}
                                badgeColor={CHART_COLORS.ga4.primary}
                                height={400}
                                animationDelay={0.45}
                              >
                                <LineChartEnhanced
                                  data={
                                    dashboardData.chart_data
                                      .ga4_daily_comparison
                                  }
                                  dataKey="date"
                                  lines={[
                                    {
                                      dataKey: "current_conversions",
                                      name: getDateRangeLabel(),
                                      color: CHART_COLORS.warning,
                                      strokeWidth: 2.5,
                                    },
                                    ...(shouldShowChangePeriod("ga4") ? [{
                                      dataKey: "previous_conversions",
                                      name: "Previous period",
                                      color: CHART_COLORS.comparison.previous,
                                      strokeWidth: 2,
                                      strokeDasharray: "5 5",
                                    }] : []),
                                  ]}
                                  xAxisFormatter={(value) => {
                                    if (value && value.length === 8) {
                                      const day = value.substring(6, 8);
                                      return day;
                                    }
                                    return value;
                                  }}
                                  formatter={(value) => [
                                    value.toLocaleString(),
                                    "Conversions",
                                  ]}
                                  labelFormatter={(label) => {
                                    if (label && label.length === 8) {
                                      const year = label.substring(0, 4);
                                      const month = label.substring(4, 6);
                                      const day = label.substring(6, 8);
                                      return `${day} ${getMonthName(
                                        parseInt(month)
                                      )} ${year}`;
                                    }
                                    return label;
                                  }}
                                  height={320}
                                />
                              </ChartCard>
                            </Grid>
                          )} */}

                          {/* Revenue chart removed - revenue KPI removed from GA4 section */}
                        </Grid>
                      </Box>
                    )}

                  {/* Top Performing Pages - Horizontal Bar Chart */}
                  {dashboardData.chart_data?.top_pages &&
                    dashboardData.chart_data.top_pages.length > 0 &&
                    isChartVisible("ga4_top_pages") && (
                      <Box sx={{ mb: 4 }}>
                        <ChartCard
                          title="Top Performing Pages"
                          badge="Analytics"
                          badgeColor={CHART_COLORS.ga4.primary}
                          height={500}
                          animationDelay={0.9}
                        >
                        <BarChartEnhanced
                              data={dashboardData.chart_data.top_pages.slice(
                                0,
                                10
                              )}
                          dataKey="pagePath"
                          horizontal={true}
                          bars={[
                            {
                              dataKey: "views",
                              name: "Page Views",
                              color: CHART_COLORS.primary,
                            },
                          ]}
                          formatter={(value) => [
                            value.toLocaleString(),
                            "Views",
                          ]}
                          margin={{
                            top: 5,
                            right: 30,
                            left: 150,
                            bottom: 5,
                          }}
                          height={400}
                        />
                      </ChartCard>
                      </Box>
                    )}

                  {/* Sessions by Source - Donut Chart & Bar Chart */}
                  {dashboardData.chart_data?.traffic_sources &&
                    dashboardData.chart_data.traffic_sources.length > 0 && (
                      <Grid container spacing={3} sx={{ mb: 4 }}>
                        {/* Donut Chart */}
                        {isChartVisible("ga4_traffic_sources_distribution") && (
                        <Grid item xs={12} md={6}>
                          <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.5, delay: 1.0 }}
                          >
                            <Card
                              sx={{
                                height: "100%",
                                borderRadius: 2,
                                border: `1px solid ${theme.palette.divider}`,
                                boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
                              }}
                            >
                              <CardContent sx={{ p: 3 }}>
                                <Typography
                                  variant="h6"
                                  mb={2}
                                  fontWeight={600}
                                  sx={{
                                    fontSize: "1.125rem",
                                    letterSpacing: "-0.01em",
                                  }}
                                >
                                  Traffic Sources Distribution
                                </Typography>
                                <Box
                                  sx={{
                                    width: "100%",
                                    height: 300,
                                    padding: 2,
                                  }}
                                >
                                  <ResponsiveContainer
                                    width="100%"
                                    height="100%"
                                  >
                                    <PieChart
                                      margin={{
                                        top: 10,
                                        right: 10,
                                        bottom: 10,
                                        left: 10,
                                      }}
                                    >
                                      <Pie
                                        data={dashboardData.chart_data.traffic_sources
                                          .slice(0, 6)
                                          .map((item) => ({
                                            name: item.source || "Unknown",
                                            value: item.sessions || 0,
                                          }))}
                                        cx="50%"
                                        cy="50%"
                                        labelLine={false}
                                        label={false}
                                        outerRadius={90}
                                        innerRadius={50}
                                        fill="#8884d8"
                                        dataKey="value"
                                      >
                                        {dashboardData.chart_data.traffic_sources
                                          .slice(0, 6)
                                          .map((entry, index) => {
                                            const colors = [
                                              theme.palette.primary.main,
                                              theme.palette.secondary.main,
                                              theme.palette.success.main,
                                              theme.palette.warning.main,
                                              theme.palette.error.main,
                                              theme.palette.info.main,
                                            ];
                                            return (
                                              <Cell
                                                key={`cell-${index}`}
                                                fill={
                                                      colors[
                                                        index % colors.length
                                                      ]
                                                }
                                              />
                                            );
                                          })}
                                      </Pie>
                                      <Tooltip
                                        contentStyle={{
                                          borderRadius: "8px",
                                          border: "none",
                                          boxShadow:
                                            "0 4px 12px rgba(0,0,0,0.1)",
                                          backgroundColor: "#FFFFFF",
                                        }}
                                        formatter={(value) => [
                                          value.toLocaleString(),
                                          "Sessions",
                                        ]}
                                      />
                                      <Legend
                                        wrapperStyle={{
                                          paddingTop: "20px",
                                          paddingBottom: "10px",
                                        }}
                                        formatter={(value) =>
                                          value.length > 15
                                            ? value.substring(0, 15) + "..."
                                            : value
                                        }
                                      />
                                    </PieChart>
                                  </ResponsiveContainer>
                                </Box>
                              </CardContent>
                            </Card>
                          </motion.div>
                        </Grid>
                        )}

                        {/* Horizontal Bar Chart */}
                        {isChartVisible("ga4_sessions_by_channel") && (
                        <Grid item xs={12} md={6}>
                          <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.5, delay: 1.05 }}
                          >
                            <Card
                              sx={{
                                height: "100%",
                                borderRadius: 2,
                                border: `1px solid ${theme.palette.divider}`,
                                boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
                              }}
                            >
                              <CardContent sx={{ p: 3 }}>
                                <Typography
                                  variant="h6"
                                  mb={2}
                                  fontWeight={600}
                                  sx={{
                                    fontSize: "1.125rem",
                                    letterSpacing: "-0.01em",
                                  }}
                                >
                                  Sessions by Source
                                </Typography>
                                    <ResponsiveContainer
                                      width="100%"
                                      height={300}
                                    >
                                  <BarChart
                                    data={dashboardData.chart_data.traffic_sources.slice(
                                      0,
                                      8
                                    )}
                                    layout="vertical"
                                    margin={{
                                      top: 5,
                                      right: 30,
                                      left: 80,
                                      bottom: 5,
                                    }}
                                  >
                                    <CartesianGrid
                                      strokeDasharray="3 3"
                                      horizontal={false}
                                      stroke="#E4E4E7"
                                    />
                                    <XAxis
                                      type="number"
                                      tick={{ fontSize: 12 }}
                                      stroke="#71717A"
                                    />
                                    <YAxis
                                      dataKey="source"
                                      type="category"
                                      width={75}
                                      stroke="#71717A"
                                      tick={{ fontSize: 11 }}
                                    />
                                    <Tooltip
                                      contentStyle={{
                                        borderRadius: "8px",
                                        border: "none",
                                            boxShadow:
                                              "0 4px 12px rgba(0,0,0,0.1)",
                                        backgroundColor: "#FFFFFF",
                                      }}
                                      formatter={(value) => [
                                        value.toLocaleString(),
                                        "Sessions",
                                      ]}
                                    />
                                    <Legend />
                                    <Bar
                                      dataKey="sessions"
                                      radius={[0, 4, 4, 0]}
                                      fill={theme.palette.primary.main}
                                      name="Sessions"
                                    />
                                  </BarChart>
                                </ResponsiveContainer>
                              </CardContent>
                            </Card>
                          </motion.div>
                        </Grid>
                        )}
                      </Grid>
                    )}

                  {/* Stacked Bar Chart - Sessions vs Users by Source */}
                  {dashboardData.chart_data?.traffic_sources &&
                    dashboardData.chart_data.traffic_sources.length > 0 && isChartVisible("ga4_channel_performance") && (
                      <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5, delay: 1.1 }}
                      >
                        <Card
                          sx={{
                            mb: 3,
                            borderRadius: 2,
                            border: `1px solid ${theme.palette.divider}`,
                            boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
                          }}
                        >
                          <CardContent sx={{ p: 3 }}>
                            <Typography
                              variant="h6"
                              mb={2}
                              fontWeight={600}
                              sx={{
                                fontSize: "1.125rem",
                                letterSpacing: "-0.01em",
                              }}
                            >
                              Sessions vs Users by Source
                            </Typography>
                            <ResponsiveContainer width="100%" height={350}>
                              <BarChart
                                data={dashboardData.chart_data.traffic_sources.slice(
                                  0,
                                  8
                                )}
                                margin={{
                                  top: 5,
                                  right: 30,
                                  left: 20,
                                  bottom: 60,
                                }}
                              >
                                <CartesianGrid
                                  strokeDasharray="3 3"
                                  stroke="#E4E4E7"
                                />
                                <XAxis
                                  dataKey="source"
                                  tick={{ fontSize: 11 }}
                                  stroke="#71717A"
                                  angle={0}
                                  textAnchor="middle"
                                  height={50}
                                  interval="preserveStartEnd"
                                />
                                <YAxis
                                  tick={{ fontSize: 12 }}
                                  stroke="#71717A"
                                />
                                <Tooltip
                                  contentStyle={{
                                    borderRadius: "8px",
                                    border: "none",
                                    boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
                                    backgroundColor: "#FFFFFF",
                                  }}
                                  formatter={(value) => [
                                    value.toLocaleString(),
                                    "",
                                  ]}
                                />
                                <Legend />
                                <Bar
                                  dataKey="sessions"
                                  stackId="a"
                                  fill={theme.palette.primary.main}
                                  name="Sessions"
                                  radius={[0, 0, 0, 0]}
                                />
                                <Bar
                                  dataKey="users"
                                  stackId="a"
                                  fill={theme.palette.secondary.main}
                                  name="Users"
                                  radius={[4, 4, 0, 0]}
                                />
                              </BarChart>
                            </ResponsiveContainer>
                          </CardContent>
                        </Card>
                      </motion.div>
                    )}

                  {/* Geographic Breakdown - Bar Chart & Pie Chart */}
                  {dashboardData.chart_data?.geographic_breakdown &&
                        dashboardData.chart_data.geographic_breakdown.length >
                          0 && (
                      <Grid container spacing={3} sx={{ mb: 3 }}>
                        {/* Bar Chart */}
                        {isChartVisible("ga4_geographic_distribution") && (
                        <Grid item xs={12} md={7}>
                          <ChartCard
                            title="Geographic Distribution"
                            badge={getBadgeLabel("GA4")}
                            badgeColor={CHART_COLORS.ga4.primary}
                            height="100%"
                            animationDelay={1.2}
                          >
                            <BarChartEnhanced
                              data={dashboardData.chart_data.geographic_breakdown.slice(
                                0,
                                10
                              )}
                              dataKey="country"
                              bars={[
                                {
                                  dataKey: "users",
                                  name: "Users",
                                  color: CHART_COLORS.primary,
                                },
                              ]}
                              formatter={(value) => [
                                value.toLocaleString(),
                                "Users",
                              ]}
                              xAxisFormatter={(value) => value}
                              margin={{
                                top: 5,
                                right: 30,
                                left: 20,
                                bottom: 5,
                              }}
                              height={350}
                            />
                          </ChartCard>
                        </Grid>
                        )}

                        {/* Pie Chart */}
                        {isChartVisible("ga4_top_countries") && (
                        <Grid item xs={12} md={5}>
                          <ChartCard
                            title="Top Countries"
                            badge={getBadgeLabel("GA4")}
                            badgeColor={CHART_COLORS.ga4.primary}
                            height={450}
                            animationDelay={1.25}
                          >
                            <PieChartEnhanced
                              data={dashboardData.chart_data.geographic_breakdown
                                .slice(0, 6)
                                .map((item) => ({
                                  name: item.country || "Unknown",
                                  value: item.users || 0,
                                }))}
                              donut={false}
                              colors={CHART_COLORS.palette}
                              formatter={(value, name) => [
                                value.toLocaleString(),
                                "Users",
                              ]}
                              height={350}
                            />
                          </ChartCard>
                        </Grid>
                        )}
                      </Grid>
                    )}

                  {/* KPI Donut Charts - Bounce Rate, Engagement Rate, Brand Presence */}
                  {/* Only show if KPIs are selected (in public view) */}
                  {shouldShowSectionKPIs("ga4") && (
                    <Grid container spacing={3} sx={{ mb: 3 }}>
                      {/* Bounce Rate Donut */}
                      {dashboardData?.kpis?.bounce_rate &&
                        shouldShowKPI("bounce_rate") &&
                        isChartVisible("bounce_rate_donut") && (
                          <Grid item xs={12} sm={6} md={4}>
                            <ChartCard
                              title="Bounce Rate"
                              badge="Analytics"
                              badgeColor={CHART_COLORS.ga4.primary}
                              height="100%"
                              animationDelay={1.3}
                              sx={{ textAlign: "center" }}
                            >
                              <Box>
                                <PieChartEnhanced
                                  data={[
                                    {
                                      name: "Bounced",
                                      value:
                                            dashboardData.kpis.bounce_rate
                                              .value || 0,
                                    },
                                    {
                                      name: "Engaged",
                                      value:
                                        100 -
                                            (dashboardData.kpis.bounce_rate
                                              .value || 0),
                                    },
                                  ]}
                                  donut={true}
                                  innerRadius={60}
                                  outerRadius={90}
                                  colors={[
                                    CHART_COLORS.error,
                                    CHART_COLORS.success,
                                  ]}
                                  formatter={(value, name) => {
                                    const normalizedValue = normalizePercentage(value);
                                    return [`${normalizedValue.toFixed(1)}%`, name];
                                  }}
                                  showLabel={true}
                                  height={250}
                                />
                                <Box mt={2}>
                                  <Typography
                                    variant="h4"
                                    fontWeight={700}
                                    sx={{ fontSize: "2rem" }}
                                    color={
                                          dashboardData.kpis.bounce_rate.value >
                                          50
                                        ? "error.main"
                                        : "success.main"
                                    }
                                  >
                                    {(() => {
                                      const value = dashboardData.kpis.bounce_rate.value || 0;
                                      const normalizedValue = normalizePercentage(value);
                                      return `${normalizedValue.toFixed(1)}%`;
                                    })()}
                                  </Typography>
                                  <Typography
                                    variant="caption"
                                    color="text.secondary"
                                    sx={{
                                      fontSize: "0.75rem",
                                      display: "block",
                                      mt: 0.5,
                                    }}
                                  >
                                    Bounced Sessions
                                  </Typography>
                                </Box>
                              </Box>
                            </ChartCard>
                          </Grid>
                        )}

                      {/* Engagement Rate Donut
                  {dashboardData?.kpis?.ga4_engagement_rate && (
                    <Grid item xs={12} sm={6} md={4}>
                      <ChartCard
                        title="Engagement Rate"
                        badge="Analytics"
                        badgeColor={CHART_COLORS.ga4.primary}
                        height="100%"
                        animationDelay={1.35}
                        sx={{ textAlign: "center" }}
                      >
                        <Box>
                          <PieChartEnhanced
                                  data={[
                                    {
                                      name: "Engaged",
                                      value:
                                  (dashboardData.kpis.ga4_engagement_rate.value || 0),
                                    },
                                    {
                                      name: "Not Engaged",
                                      value:
                                        100 -
                                  (dashboardData.kpis.ga4_engagement_rate.value || 0),
                                    },
                                  ]}
                            donut={true}
                                  innerRadius={60}
                                  outerRadius={90}
                            colors={[CHART_COLORS.success, theme.palette.grey[300]]}
                                  formatter={(value, name) => {
                                    const normalizedValue = normalizePercentage(value);
                                    return [`${normalizedValue.toFixed(1)}%`, name];
                                  }}
                            showLabel={true}
                            height={250}
                          />
                            <Box mt={2}>
                              <Typography
                                variant="h4"
                                fontWeight={700}
                                sx={{ fontSize: "2rem" }}
                                color="success.main"
                              >
                                {(() => {
                                  const value = dashboardData.kpis.ga4_engagement_rate.value || 0;
                                  const normalizedValue = normalizePercentage(value);
                                  return `${normalizedValue.toFixed(1)}%`;
                                })()}
                              </Typography>
                              <Typography
                                variant="caption"
                                color="text.secondary"
                                sx={{
                                  fontSize: "0.75rem",
                                  display: "block",
                                  mt: 0.5,
                                }}
                              >
                                Engaged Sessions
                              </Typography>
                            </Box>
                        </Box>
                      </ChartCard>
                    </Grid>
                  )} */}

                      {/* Brand Presence Rate Donut
                  {dashboardData?.kpis?.brand_presence_rate && (
                    <Grid item xs={12} sm={6} md={4}>
                      <ChartCard
                        title="Brand Presence Rate"
                        badge={getBadgeLabel("Scrunch")}
                        badgeColor={CHART_COLORS.scrunch.primary}
                        height="100%"
                        animationDelay={1.4}
                        sx={{ textAlign: "center" }}
                      >
                        <Box>
                          <PieChartEnhanced
                                  data={[
                                    {
                                      name: "Present",
                                value: dashboardData.kpis.brand_presence_rate.value || 0,
                                    },
                                    {
                                      name: "Absent",
                                      value:
                                  100 - (dashboardData.kpis.brand_presence_rate.value || 0),
                                    },
                                  ]}
                            donut={true}
                                  innerRadius={60}
                                  outerRadius={90}
                            colors={[CHART_COLORS.success, theme.palette.grey[300]]}
                                  formatter={(value, name) => {
                                    const normalizedValue = normalizePercentage(value);
                                    return [`${normalizedValue.toFixed(1)}%`, name];
                                  }}
                            showLabel={true}
                            height={250}
                          />
                            <Box mt={2}>
                              <Typography
                                variant="h4"
                                fontWeight={700}
                                sx={{ fontSize: "2rem" }}
                                color="success.main"
                              >
                              {(() => {
                                const value = dashboardData.kpis.brand_presence_rate.value || 0;
                                const normalizedValue = normalizePercentage(value);
                                return `${normalizedValue.toFixed(1)}%`;
                              })()}
                              </Typography>
                              <Typography
                                variant="caption"
                                color="text.secondary"
                                sx={{
                                  fontSize: "0.75rem",
                                  display: "block",
                                  mt: 0.5,
                                }}
                              >
                                Brand Present in Responses
                              </Typography>
                            </Box>
                        </Box>
                      </ChartCard>
                    </Grid>
                  )} */}
                    </Grid>
                  )}
                </Box>
              </SectionContainer>
            )}

          {/* Scrunch AI Section */}

          <Box>
            {/* Scrunch AI Section - Show independently if Scrunch data is available */}
            {(() => {
              // Check section visibility first
              const sectionVisible = isSectionVisible("scrunch_ai");
              debugLog("Scrunch AI section visibility check:", {
                isPublic,
                sectionVisible,
                publicVisibleSections: publicVisibleSections
                  ? Array.from(publicVisibleSections)
                  : null,
                hasDashboardData: !!dashboardData,
                dashboardKPICount: dashboardData?.kpis
                  ? Object.keys(dashboardData.kpis).length
                  : 0,
              });

              if (!sectionVisible) {
                return null;
              }

              // Check if we have Scrunch data from separate endpoint
              const hasScrunchData =
                    scrunchData?.kpis &&
                    Object.keys(scrunchData.kpis).length > 0;
              const hasScrunchChartData =
                scrunchData?.chart_data &&
                    (scrunchData.chart_data.top_performing_prompts?.length >
                      0 ||
                  scrunchData.chart_data.scrunch_ai_insights?.length > 0);

              // Check if we have Scrunch data from main endpoint (fallback)
              const scrunchKPIsFromMain = dashboardData?.kpis
                ? Object.keys(dashboardData.kpis).filter((k) => {
                    const kpi = dashboardData.kpis[k];
                    return kpi?.source === "Scrunch";
                  })
                : [];
              const hasScrunchFromMain =
                scrunchKPIsFromMain.length > 0 ||
                    dashboardData?.chart_data?.top_performing_prompts?.length >
                      0 ||
                dashboardData?.chart_data?.scrunch_ai_insights?.length > 0;

              // Check if section has selected KPIs or charts
              const hasSelectedKPIs = shouldShowSectionKPIs("scrunch_ai");
                  const hasSelectedCharts =
                    shouldShowSectionCharts("scrunch_ai");

              const shouldShow =
                (loadingScrunch ||
                  hasScrunchData ||
                  hasScrunchChartData ||
                  hasScrunchFromMain) &&
                (hasSelectedKPIs || hasSelectedCharts);

              // Debug logging
              debugLog("Scrunch section data check:", {
                loadingScrunch,
                hasScrunchData,
                hasScrunchChartData,
                scrunchKPIsFromMain: scrunchKPIsFromMain.length,
                scrunchKPIsFromMainKeys: scrunchKPIsFromMain,
                hasScrunchFromMain,
                hasSelectedKPIs,
                hasSelectedCharts,
                shouldShow,
                dashboardDataKeys: dashboardData?.kpis
                  ? Object.keys(dashboardData.kpis)
                  : [],
                hasTopPrompts:
                      !!dashboardData?.chart_data?.top_performing_prompts
                        ?.length,
                hasInsights:
                  !!dashboardData?.chart_data?.scrunch_ai_insights?.length,
              });

              return shouldShow;
            })() && (
              <SectionContainer
                    title={isPublic ? "AI Visibility" : "Scrunch AI"}
                description="AI Search Presence & Competitor Insights"
                loading={loadingScrunch}
              >
                {/* Use scrunchData if available, otherwise fall back to dashboardData */}
                {(() => {
                  // Prefer scrunchData from separate endpoint (has better chart data)
                  // Fall back to dashboardData if scrunchData is not available
                  let scrunchKPIs = {};
                  let scrunchChartData = {};

                  // First, check if scrunchData has chart data (this is the key for public mode)
                  // scrunchData.chart_data has top_performing_prompts and scrunch_ai_insights
                  const hasScrunchChartData =
                    scrunchData?.chart_data &&
                    (scrunchData.chart_data.top_performing_prompts?.length >
                      0 ||
                          scrunchData.chart_data.scrunch_ai_insights?.length >
                            0);

                  // Use scrunchData if it has KPIs or chart data
                  if (
                    scrunchData &&
                    ((scrunchData.kpis &&
                      Object.keys(scrunchData.kpis).length > 0) ||
                      hasScrunchChartData)
                  ) {
                    scrunchKPIs = scrunchData.kpis || {};
                    scrunchChartData = scrunchData.chart_data || {};
                    debugLog(
                      `Using Scrunch data from separate endpoint ${
                        isPublic ? "(public mode)" : "(admin mode)"
                      }:`,
                      {
                        kpiCount: Object.keys(scrunchKPIs).length,
                        hasTopPrompts:
                          !!scrunchChartData.top_performing_prompts?.length,
                        hasInsights:
                          !!scrunchChartData.scrunch_ai_insights?.length,
                        topPromptsCount:
                              scrunchChartData.top_performing_prompts?.length ||
                              0,
                        insightsCount:
                          scrunchChartData.scrunch_ai_insights?.length || 0,
                      }
                    );
                  } else if (dashboardData?.kpis) {
                    // Fall back to dashboardData if scrunchData is not available
                    // Filter only Scrunch KPIs from dashboardData
                        const scrunchKeys = Object.keys(
                          dashboardData.kpis
                        ).filter((k) => {
                        const kpi = dashboardData.kpis[k];
                        return kpi?.source === "Scrunch";
                        });
                    if (scrunchKeys.length > 0) {
                      scrunchKPIs = {};
                      scrunchKeys.forEach((k) => {
                        scrunchKPIs[k] = dashboardData.kpis[k];
                      });
                      scrunchChartData = dashboardData.chart_data || {};
                      debugLog(
                        `Using Scrunch data from main endpoint ${
                          isPublic ? "(public mode fallback)" : "(fallback)"
                        }:`,
                        {
                          kpiCount: scrunchKeys.length,
                          hasTopPrompts:
                                !!scrunchChartData.top_performing_prompts
                                  ?.length,
                          hasInsights:
                            !!scrunchChartData.scrunch_ai_insights?.length,
                        }
                      );
                    } else {
                      debugWarn(
                        "No Scrunch KPIs found in dashboardData.kpis. Available KPIs:",
                        dashboardData.kpis
                          ? Object.keys(dashboardData.kpis)
                          : []
                      );
                    }
                  } else {
                    debugWarn("No dashboardData.kpis available");
                  }

                  // Check if scrunchData has no_data flag
                  if (scrunchData?.no_data) {
                    return (
                      <Box sx={{ p: 3, textAlign: "center" }}>
                        <Alert severity="info" sx={{ borderRadius: 2 }}>
                          <Typography variant="h6" gutterBottom>
                            No Data Available
                          </Typography>
                          <Typography variant="body2">
                            {scrunchData.message ||
                              "No Scrunch AI data is currently available. Please check back later."}
                          </Typography>
                        </Alert>
                      </Box>
                    );
                  }

                  // Only render if we have actual data
                  const hasData =
                    Object.keys(scrunchKPIs).length > 0 ||
                    scrunchChartData?.top_performing_prompts?.length > 0 ||
                    scrunchChartData?.scrunch_ai_insights?.length > 0;

                  if (!hasData) {
                    return (
                      <Box p={3}>
                        <Typography color="text.secondary">
                              No Scrunch data available for the selected date
                              range.
                        </Typography>
                      </Box>
                    );
                  }

                  return (
                    <>
                      {/* Brand Presence Rate Donut */}
                      {/* {scrunchKPIs?.brand_presence_rate && (
                            <Box sx={{ mb: 4 }}>
                              <Typography
                                variant="h6"
                                fontWeight={600}
                                mb={2}
                                sx={{
                                  fontSize: "1.125rem",
                                  letterSpacing: "-0.01em",
                                }}
                              >
                                Brand Presence Metrics
                              </Typography>
                              <Grid container spacing={3}>
                                {shouldShowKPI("brand_presence_rate") &&
                                  isChartVisible("brand_presence_rate_donut") && (
                                <Grid item xs={12} sm={6} md={4}>
                                  <ChartCard
                                    title="Brand Presence Rate"
                                    badge={getBadgeLabel("Scrunch")}
                                    badgeColor={CHART_COLORS.scrunch.primary}
                                    height="100%"
                                    animationDelay={0.1}
                                    sx={{ textAlign: "center" }}
                                  >
                                    <Box>
                                      <PieChartEnhanced
                                              data={[
                                                {
                                                  name: "Present",
                                                  value:
                                              scrunchKPIs.brand_presence_rate.value || 0,
                                                },
                                                {
                                                  name: "Absent",
                                                  value:
                                                    100 -
                                              (scrunchKPIs.brand_presence_rate.value || 0),
                                                },
                                              ]}
                                        donut={true}
                                              innerRadius={60}
                                              outerRadius={90}
                                        colors={[CHART_COLORS.success, theme.palette.grey[300]]}
                                              formatter={(value, name) => {
                                                const normalizedValue = normalizePercentage(value);
                                                return [`${normalizedValue.toFixed(1)}%`, name];
                                              }}
                                        showLabel={true}
                                        height={250}
                                      />
                                        <Box mt={2}>
                                          <Typography
                                            variant="h4"
                                            fontWeight={700}
                                            sx={{ fontSize: "2rem" }}
                                            color="success.main"
                                          >
                                            {(() => {
                                              const value = scrunchKPIs.brand_presence_rate.value || 0;
                                              const normalizedValue = normalizePercentage(value);
                                              return `${normalizedValue.toFixed(1)}%`;
                                            })()}
                                          </Typography>
                                          <Typography
                                            variant="caption"
                                            color="text.secondary"
                                            sx={{
                                              fontSize: "0.75rem",
                                              display: "block",
                                              mt: 0.5,
                                            }}
                                          >
                                            Brand Present in Responses
                                          </Typography>
                                        </Box>
                                    </Box>
                                  </ChartCard>
                                </Grid>
                                )}
                              </Grid>
                            </Box>
                          )} */}

                      {/* Top Performing Prompts Section */}
                      {(() => {
                        // Prioritize scrunchData.chart_data, then fall back to scrunchChartData (which may come from dashboardData)
                        const topPrompts =
                          scrunchData?.chart_data?.top_performing_prompts ||
                          scrunchChartData?.top_performing_prompts ||
                          [];

                        // Only show if chart is selected and data exists
                        if (
                          topPrompts.length === 0 ||
                          !isChartVisible("top_performing_prompts")
                        ) {
                          return null;
                        }

                        return (
                          <Box sx={{ mb: 4 }}>
                            <Typography
                              variant="h6"
                              fontWeight={600}
                              mb={2}
                              sx={{
                                fontSize: "1.125rem",
                                letterSpacing: "-0.01em",
                              }}
                            >
                              Top Performing Prompts
                            </Typography>

                            <motion.div
                              initial={{ opacity: 0, y: 20 }}
                              animate={{ opacity: 1, y: 0 }}
                              transition={{ duration: 0.5, delay: 0.3 }}
                            >
                              <Card
                                sx={{
                                  mb: 3,
                                  borderRadius: 2,
                                  border: `1px solid ${theme.palette.divider}`,
                                  boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
                                }}
                              >
                                <CardContent sx={{ p: 3 }}>
                                  <Grid container spacing={2}>
                                    {topPrompts.map((prompt) => (
                                      <Grid
                                        item
                                        xs={12}
                                        sm={6}
                                        md={4}
                                        key={prompt.id}
                                      >
                                        <Paper
                                          sx={{
                                            p: 2,
                                            borderLeft: `3px solid ${theme.palette.primary.main}`,
                                            borderRadius: 1.5,
                                            transition: "all 0.2s",
                                            "&:hover": {
                                              transform: "translateX(2px)",
                                              boxShadow:
                                                "0 2px 8px rgba(0, 0, 0, 0.06)",
                                            },
                                          }}
                                        >
                                          {/* <Box
                                            display="flex"
                                            alignItems="flex-start"
                                            justifyContent="space-between"
                                            mb={1}
                                          >
                                            <Box
                                              display="flex"
                                              alignItems="center"
                                              gap={1}
                                            >
                                              <Chip
                                                label={`Rank #${prompt.rank}`}
                                                size="small"
                                                sx={{
                                                  bgcolor: "primary.main",
                                                  color: "white",
                                                  fontWeight: 700,
                                                  fontSize: "11px",
                                                  height: 22,
                                                  minWidth: 50,
                                                }}
                                              />
                                            </Box>
                                          </Box> */}
                                          <Typography
                                            variant="body2"
                                            fontWeight={600}
                                            sx={{
                                              fontSize: "0.875rem",
                                              lineHeight: 1.4,
                                              display: "-webkit-box",
                                              WebkitLineClamp: 2,
                                              WebkitBoxOrient: "vertical",
                                              overflow: "hidden",
                                            }}
                                          >
                                            {prompt.text || "N/A"}
                                          </Typography>
                                              <Box
                                                display="flex"
                                                gap={2}
                                                mt={1.5}
                                              >
                                            <Typography
                                              variant="caption"
                                              color="text.secondary"
                                              sx={{
                                                fontSize: "11px",
                                                fontWeight: 500,
                                              }}
                                            >
                                              {prompt.responseCount?.toLocaleString() ||
                                                0}{" "}
                                              responses
                                            </Typography>
                                            <Typography
                                              variant="caption"
                                              color="text.secondary"
                                              sx={{
                                                fontSize: "11px",
                                                fontWeight: 500,
                                              }}
                                            >
                                                  {prompt.variants || 0}{" "}
                                                  variants
                                            </Typography>
                                          </Box>
                                        </Paper>
                                      </Grid>
                                    ))}
                                  </Grid>
                                </CardContent>
                              </Card>
                            </motion.div>
                          </Box>
                        );
                      })()}

                      {/* Scrunch AI Insights Section */}
                      {(() => {
                        // Prioritize scrunchData.chart_data, then fall back to dashboardData.chart_data
                        const insights =
                          scrunchData?.chart_data?.scrunch_ai_insights ||
                          dashboardData?.chart_data?.scrunch_ai_insights ||
                          [];

                        // Only show if chart is selected and data exists
                        if (
                          insights.length === 0 ||
                          !isChartVisible("scrunch_ai_insights")
                        ) {
                          return null;
                        }

                        // Get all insights data
                        const allInsights = insights;

                        // Calculate pagination
                        const totalInsights = allInsights.length;
                            const startIndex =
                              insightsPage * insightsRowsPerPage;
                        const endIndex = startIndex + insightsRowsPerPage;
                        const paginatedInsights = allInsights.slice(
                          startIndex,
                          endIndex
                        );

                        // Reset page if current page is out of bounds
                            if (
                              insightsPage > 0 &&
                              startIndex >= totalInsights
                            ) {
                          setInsightsPage(0);
                        }

                        return (
                          <Box sx={{ mb: 4 }}>
                            <motion.div
                              initial={{ opacity: 0, y: 20 }}
                              animate={{ opacity: 1, y: 0 }}
                              transition={{ duration: 0.5, delay: 0.4 }}
                            >
                              <Card
                                sx={{
                                  mb: 3,
                                  borderRadius: 2,
                                  border: `1px solid ${theme.palette.divider}`,
                                  boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
                                }}
                              >
                                <CardContent sx={{ p: 0 }}>
                                  <Box
                                    p={3}
                                    borderBottom="1px solid"
                                    borderColor="divider"
                                  >
                                    <Typography
                                      variant="h6"
                                      fontWeight={600}
                                      sx={{
                                        fontSize: "1.125rem",
                                        letterSpacing: "-0.01em",
                                      }}
                                    >
                                          AI Search Presence & Competitor
                                          Insights{" "}
                                    </Typography>
                                  </Box>
                                  <TableContainer>
                                    <Table>
                                      <TableHead>
                                        <TableRow
                                          sx={{
                                            bgcolor: alpha(
                                              theme.palette.primary.main,
                                              0.04
                                            ),
                                          }}
                                        >
                                          <TableCell
                                            sx={{
                                              fontWeight: 700,
                                              fontSize: "11px",
                                              textTransform: "uppercase",
                                              letterSpacing: "0.05em",
                                              py: 1.5,
                                              minWidth: 200,
                                            }}
                                          >
                                            Seed Prompt
                                          </TableCell>
                                          <TableCell
                                            sx={{
                                              fontWeight: 700,
                                              fontSize: "11px",
                                              textTransform: "uppercase",
                                              letterSpacing: "0.05em",
                                              py: 1.5,
                                              minWidth: 120,
                                            }}
                                          >
                                            Data
                                          </TableCell>
                                          <TableCell
                                            sx={{
                                              fontWeight: 700,
                                              fontSize: "11px",
                                              textTransform: "uppercase",
                                              letterSpacing: "0.05em",
                                              py: 1.5,
                                              minWidth: 120,
                                            }}
                                          >
                                            Presence
                                          </TableCell>
                                          <TableCell
                                            sx={{
                                              fontWeight: 700,
                                              fontSize: "11px",
                                              textTransform: "uppercase",
                                              letterSpacing: "0.05em",
                                              py: 1.5,
                                              minWidth: 100,
                                            }}
                                          >
                                            Citations
                                          </TableCell>
                                          <TableCell
                                            sx={{
                                              fontWeight: 700,
                                              fontSize: "11px",
                                              textTransform: "uppercase",
                                              letterSpacing: "0.05em",
                                              py: 1.5,
                                              minWidth: 100,
                                            }}
                                          >
                                            Competitors
                                          </TableCell>
                                          <TableCell
                                            sx={{
                                              fontWeight: 700,
                                              fontSize: "11px",
                                              textTransform: "uppercase",
                                              letterSpacing: "0.05em",
                                              py: 1.5,
                                              minWidth: 100,
                                            }}
                                          >
                                            Stage
                                          </TableCell>
                                        </TableRow>
                                      </TableHead>
                                      <TableBody>
                                            {paginatedInsights.map(
                                              (insight) => (
                                          <TableRow
                                            key={
                                                    insight.id ||
                                                    insight.seedPrompt
                                            }
                                            hover
                                            sx={{
                                              transition: "all 0.2s",
                                              "&:hover": {
                                                bgcolor: alpha(
                                                        theme.palette.primary
                                                          .main,
                                                  0.02
                                                ),
                                              },
                                            }}
                                          >
                                            <TableCell sx={{ py: 2 }}>
                                              <Box>
                                                <Typography
                                                  variant="body2"
                                                  fontWeight={600}
                                                  sx={{
                                                    fontSize: "0.875rem",
                                                    mb: 0.5,
                                                    lineHeight: 1.4,
                                                  }}
                                                >
                                                        {insight.seedPrompt
                                                          .length > 60
                                                    ? insight.seedPrompt.substring(
                                                        0,
                                                        60
                                                      ) + "..."
                                                    : insight.seedPrompt}
                                                </Typography>
                                                <Typography
                                                  variant="caption"
                                                  color="text.secondary"
                                                  sx={{
                                                    fontSize: "11px",
                                                    fontStyle: "italic",
                                                  }}
                                                >
                                                  {insight.category}
                                                </Typography>
                                              </Box>
                                            </TableCell>
                                            <TableCell sx={{ py: 2 }}>
                                              <Box>
                                                <Typography
                                                  variant="body2"
                                                  sx={{
                                                    fontSize: "0.875rem",
                                                    fontWeight: 600,
                                                    mb: 0.25,
                                                  }}
                                                >
                                                  {insight.variants?.toLocaleString() ||
                                                    0}{" "}
                                                  variants
                                                </Typography>
                                                <Typography
                                                  variant="caption"
                                                  color="text.secondary"
                                                  sx={{
                                                    fontSize: "0.75rem",
                                                  }}
                                                >
                                                  {insight.responses?.toLocaleString() ||
                                                    0}{" "}
                                                  responses
                                                </Typography>
                                              </Box>
                                            </TableCell>
                                            <TableCell sx={{ py: 2 }}>
                                              <Box>
                                                <Typography
                                                  variant="body2"
                                                  fontWeight={700}
                                                  sx={{
                                                    fontSize: "0.9375rem",
                                                    mb: 0.25,
                                                  }}
                                                >
                                                  {insight.presence}%
                                                </Typography>
                                              </Box>
                                            </TableCell>
                                            <TableCell sx={{ py: 2 }}>
                                              <Box>
                                                <Typography
                                                  variant="body2"
                                                  fontWeight={600}
                                                  sx={{
                                                    fontSize: "0.9375rem",
                                                    mb: 0.25,
                                                  }}
                                                >
                                                  {insight.citations || 0}
                                                </Typography>
                                              </Box>
                                            </TableCell>
                                            <TableCell sx={{ py: 2 }}>
                                              <Box>
                                                <Typography
                                                  variant="body2"
                                                  fontWeight={600}
                                                  sx={{
                                                    fontSize: "0.9375rem",
                                                    mb: 0.25,
                                                  }}
                                                >
                                                        {insight.competitors ||
                                                          0}{" "}
                                                  active
                                                </Typography>
                                              </Box>
                                            </TableCell>
                                            <TableCell sx={{ py: 2 }}>
                                              <Chip
                                                label={insight.stage}
                                                size="small"
                                                sx={{
                                                  bgcolor:
                                                    insight.stage ===
                                                    "Awareness"
                                                      ? alpha(
                                                                theme.palette
                                                                  .info.main,
                                                          0.1
                                                        )
                                                      : insight.stage ===
                                                        "Evaluation"
                                                      ? alpha(
                                                                theme.palette
                                                                  .warning.main,
                                                          0.1
                                                        )
                                                      : alpha(
                                                                theme.palette
                                                                  .success.main,
                                                          0.1
                                                        ),
                                                  color:
                                                    insight.stage ===
                                                    "Awareness"
                                                      ? "info.main"
                                                      : insight.stage ===
                                                        "Evaluation"
                                                      ? "warning.main"
                                                      : "success.main",
                                                  fontWeight: 600,
                                                  fontSize: "11px",
                                                  height: 24,
                                                }}
                                              />
                                            </TableCell>
                                          </TableRow>
                                              )
                                            )}
                                      </TableBody>
                                    </Table>
                                  </TableContainer>

                                  {/* Pagination - Only show if more than 10 rows */}
                                  {totalInsights > 10 && (
                                    <TablePagination
                                      component="div"
                                      count={totalInsights}
                                      page={insightsPage}
                                      onPageChange={(event, newPage) => {
                                        setInsightsPage(newPage);
                                      }}
                                      rowsPerPage={insightsRowsPerPage}
                                      onRowsPerPageChange={(event) => {
                                        setInsightsRowsPerPage(
                                          parseInt(event.target.value, 10)
                                        );
                                        setInsightsPage(0);
                                      }}
                                      rowsPerPageOptions={[5, 10, 25, 50]}
                                      sx={{
                                        borderTop: `1px solid ${theme.palette.divider}`,
                                        "& .MuiTablePagination-toolbar": {
                                          px: 2,
                                        },
                                            "& .MuiTablePagination-selectLabel":
                                              {
                                          fontSize: "0.875rem",
                                          color: "text.secondary",
                                        },
                                            "& .MuiTablePagination-displayedRows":
                                              {
                                          fontSize: "0.875rem",
                                        },
                                      }}
                                    />
                                  )}

                                  {totalInsights === 0 && (
                                    <Box p={4} textAlign="center">
                                      <Typography
                                        color="text.secondary"
                                        sx={{ fontSize: "0.875rem" }}
                                      >
                                        No insights available
                                      </Typography>
                                    </Box>
                                  )}
                                </CardContent>
                              </Card>
                            </motion.div>
                          </Box>
                        );
                      })()}

                      {/* Prompts Analytics Table - Scrunch-like interface */}
                      {/* Show if chart is visible or section has selected KPIs */}
                      {(isChartVisible("top_performing_prompts") ||
                        shouldShowSectionKPIs("scrunch_ai")) && (
                        <PromptsAnalyticsTable
                          clientId={promptsClientId}
                          slug={!promptsClientId ? publicSlug : null}
                          startDate={startDate}
                          endDate={endDate}
                        />
                      )}
                      {/* Brand Analytics Charts - Sub-section under Scrunch AI (no separate heading) */}
                      {brandAnalytics &&
                        isChartVisible("brand_analytics_charts") && (
                          <Box sx={{ mb: 4, mt: 4 }}>
                            <Grid container spacing={2.5} sx={{ mb: 3 }}>
                              {/* Platform Distribution - Donut Chart */}
                        {brandAnalytics.platform_distribution &&
                                    Object.keys(
                                      brandAnalytics.platform_distribution
                                    ).length > 0 && (
                            <Grid item xs={12} md={6}>
                              <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                          transition={{
                                            duration: 0.5,
                                            delay: 0.7,
                                          }}
                              >
                                <Card
                                  sx={{
                                    borderRadius: 2,
                                    border: `1px solid ${theme.palette.divider}`,
                                              boxShadow:
                                                "0 1px 3px rgba(0,0,0,0.05)",
                                  }}
                                >
                                  <CardContent sx={{ p: 3 }}>
                                    <Typography
                                      variant="h6"
                                      mb={3}
                                      fontWeight={600}
                                      sx={{ fontSize: "1rem" }}
                                    >
                                      Platform Distribution
                                    </Typography>
                                    <Box
                                      sx={{
                                        width: "100%",
                                        height: 350,
                                        padding: 2,
                                      }}
                                    >
                                      <ResponsiveContainer
                                        width="100%"
                                        height="100%"
                                      >
                                        <PieChart
                                          margin={{
                                            top: 10,
                                            right: 10,
                                            bottom: 50,
                                            left: 10,
                                          }}
                                        >
                                          <Pie
                                            data={Object.entries(
                                              brandAnalytics.platform_distribution
                                                      ).map(
                                                        ([name, value]) => ({
                                              name,
                                              value,
                                                        })
                                                      )}
                                            cx="50%"
                                            cy="45%"
                                            labelLine={false}
                                            label={false}
                                            outerRadius={80}
                                            innerRadius={45}
                                            fill="#8884d8"
                                            dataKey="value"
                                          >
                                            {Object.entries(
                                              brandAnalytics.platform_distribution
                                            ).map((entry, index) => {
                                              const softColors = [
                                                "rgba(0, 122, 255, 0.5)", // Blue
                                                "rgba(52, 199, 89, 0.5)", // Green
                                                "rgba(255, 149, 0, 0.5)", // Orange
                                                "rgba(255, 45, 85, 0.5)", // Red
                                                "rgba(88, 86, 214, 0.5)", // Purple
                                                "rgba(255, 193, 7, 0.5)", // Yellow
                                                "rgba(90, 200, 250, 0.5)", // Light Blue
                                              ];
                                              return (
                                                <Cell
                                                  key={`cell-${index}`}
                                                  fill={
                                                    softColors[
                                                                index %
                                                                  softColors.length
                                                    ]
                                                  }
                                                />
                                              );
                                            })}
                                          </Pie>
                                          <Tooltip
                                            contentStyle={{
                                              borderRadius: "8px",
                                              border: "none",
                                              boxShadow:
                                                "0 4px 12px rgba(0,0,0,0.1)",
                                                        backgroundColor:
                                                          "#FFFFFF",
                                            }}
                                          />
                                          <Legend
                                            wrapperStyle={{
                                              paddingTop: "10px",
                                              fontSize: "0.875rem",
                                            }}
                                            iconType="circle"
                                            formatter={(value) => {
                                              const maxLength = 20;
                                                        return value.length >
                                                          maxLength
                                                ? value.substring(
                                                    0,
                                                    maxLength
                                                  ) + "..."
                                                : value;
                                            }}
                                          />
                                        </PieChart>
                                      </ResponsiveContainer>
                                    </Box>
                                  </CardContent>
                                </Card>
                              </motion.div>
                            </Grid>
                          )}

                        {/* Stage Distribution - Pie Chart */}
                        {brandAnalytics.stage_distribution &&
                                    Object.keys(
                                      brandAnalytics.stage_distribution
                                    ).length > 0 && (
                            <Grid item xs={12} md={6}>
                              <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                          transition={{
                                            duration: 0.5,
                                            delay: 0.8,
                                          }}
                              >
                                <Card
                                  sx={{
                                    borderRadius: 2,
                                    border: `1px solid ${theme.palette.divider}`,
                                              boxShadow:
                                                "0 1px 3px rgba(0,0,0,0.05)",
                                  }}
                                >
                                  <CardContent sx={{ p: 3 }}>
                                    <Typography
                                      variant="h6"
                                      mb={3}
                                      fontWeight={600}
                                      sx={{ fontSize: "1rem" }}
                                    >
                                      Funnel Stage Distribution
                                    </Typography>
                                    <Box
                                      sx={{
                                        width: "100%",
                                        height: 350,
                                        padding: 2,
                                      }}
                                    >
                                      <ResponsiveContainer
                                        width="100%"
                                        height="100%"
                                      >
                                        <PieChart
                                          margin={{
                                            top: 10,
                                            right: 10,
                                            bottom: 50,
                                            left: 10,
                                          }}
                                        >
                                          <Pie
                                            data={Object.entries(
                                              brandAnalytics.stage_distribution
                                                      ).map(
                                                        ([name, value]) => ({
                                              name,
                                              value,
                                                        })
                                                      )}
                                            cx="50%"
                                            cy="45%"
                                            labelLine={false}
                                            label={false}
                                            outerRadius={80}
                                            fill="#8884d8"
                                            dataKey="value"
                                          >
                                            {Object.entries(
                                              brandAnalytics.stage_distribution
                                            ).map((entry, index) => {
                                              const softColors = [
                                                "rgba(59, 130, 246, 0.6)", // Light blue
                                                "rgba(20, 184, 166, 0.6)", // Teal/Green
                                                "rgba(251, 146, 60, 0.6)", // Orange
                                                "rgba(239, 68, 68, 0.6)", // Orange-red
                                                "rgba(88, 86, 214, 0.6)", // Purple
                                              ];
                                              return (
                                                <Cell
                                                  key={`cell-${index}`}
                                                  fill={
                                                    softColors[
                                                                index %
                                                                  softColors.length
                                                    ]
                                                  }
                                                />
                                              );
                                            })}
                                          </Pie>
                                          <Tooltip
                                            contentStyle={{
                                              borderRadius: "8px",
                                              border: "none",
                                              boxShadow:
                                                "0 4px 12px rgba(0,0,0,0.1)",
                                                        backgroundColor:
                                                          "#FFFFFF",
                                            }}
                                          />
                                          <Legend
                                            wrapperStyle={{
                                              paddingTop: "10px",
                                              fontSize: "0.875rem",
                                            }}
                                            iconType="circle"
                                            formatter={(value) => {
                                              const maxLength = 20;
                                                        return value.length >
                                                          maxLength
                                                ? value.substring(
                                                    0,
                                                    maxLength
                                                  ) + "..."
                                                : value;
                                            }}
                                          />
                                        </PieChart>
                                      </ResponsiveContainer>
                                    </Box>
                                  </CardContent>
                                </Card>
                              </motion.div>
                            </Grid>
                          )}

                        {/* Brand Sentiment - Donut Chart */}
                        {brandAnalytics.brand_sentiment &&
                                    Object.keys(
                                      brandAnalytics.brand_sentiment
                                    ).filter(
                                      (key) =>
                                        brandAnalytics.brand_sentiment[key] > 0
                          ).length > 0 && (
                            <Grid item xs={12} md={6}>
                              <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                          transition={{
                                            duration: 0.5,
                                            delay: 0.9,
                                          }}
                              >
                                <Card
                                  sx={{
                                    borderRadius: 2,
                                    border: `1px solid ${theme.palette.divider}`,
                                              boxShadow:
                                                "0 1px 3px rgba(0,0,0,0.05)",
                                  }}
                                >
                                  <CardContent sx={{ p: 3 }}>
                                    <Typography
                                      variant="h6"
                                      mb={3}
                                      fontWeight={600}
                                      sx={{ fontSize: "1rem" }}
                                    >
                                      Brand Sentiment
                                    </Typography>
                                    <Box
                                      sx={{
                                        width: "100%",
                                        height: 350,
                                        padding: 2,
                                      }}
                                    >
                                      <ResponsiveContainer
                                        width="100%"
                                        height="100%"
                                      >
                                        <PieChart
                                          margin={{
                                            top: 10,
                                            right: 10,
                                            bottom: 50,
                                            left: 10,
                                          }}
                                        >
                                          <Pie
                                            data={Object.entries(
                                              brandAnalytics.brand_sentiment
                                            )
                                              .filter(
                                                          ([name, value]) =>
                                                            value > 0
                                              )
                                                        .map(
                                                          ([name, value]) => ({
                                                name:
                                                              name
                                                                .charAt(0)
                                                                .toUpperCase() +
                                                  name.slice(1),
                                                value,
                                                          })
                                                        )}
                                            cx="50%"
                                            cy="45%"
                                            labelLine={false}
                                            label={false}
                                            outerRadius={80}
                                            innerRadius={45}
                                            fill="#8884d8"
                                            dataKey="value"
                                          >
                                            {Object.entries(
                                              brandAnalytics.brand_sentiment
                                            )
                                              .filter(
                                                          ([name, value]) =>
                                                            value > 0
                                              )
                                              .map((entry, index) => {
                                                const colors = {
                                                  positive:
                                                    "rgba(20, 184, 166, 0.6)", // Teal/Green
                                                  negative:
                                                    "rgba(239, 68, 68, 0.6)", // Orange-red
                                                  neutral:
                                                    "rgba(251, 146, 60, 0.6)", // Orange
                                                  null: "rgba(88, 86, 214, 0.6)", // Purple
                                                };
                                                const key =
                                                  entry[0].toLowerCase();
                                                return (
                                                  <Cell
                                                    key={`cell-${index}`}
                                                    fill={
                                                      colors[key] ||
                                                      "rgba(88, 86, 214, 0.6)"
                                                    }
                                                  />
                                                );
                                              })}
                                          </Pie>
                                          <Tooltip
                                            contentStyle={{
                                              borderRadius: "8px",
                                              border: "none",
                                              boxShadow:
                                                "0 4px 12px rgba(0,0,0,0.1)",
                                                        backgroundColor:
                                                          "#FFFFFF",
                                            }}
                                          />
                                          <Legend
                                            wrapperStyle={{
                                              paddingTop: "10px",
                                              fontSize: "0.875rem",
                                            }}
                                            iconType="circle"
                                            formatter={(value) => {
                                              const maxLength = 20;
                                                        return value.length >
                                                          maxLength
                                                ? value.substring(
                                                    0,
                                                    maxLength
                                                  ) + "..."
                                                : value;
                                            }}
                                          />
                                        </PieChart>
                                      </ResponsiveContainer>
                                    </Box>
                                  </CardContent>
                                </Card>
                              </motion.div>
                            </Grid>
                          )}
                      </Grid>

                      {/* Top Competitors - List */}
                      {brandAnalytics.top_competitors &&
                        brandAnalytics.top_competitors.length > 0 && (
                                    <Grid
                                      container
                                      spacing={2.5}
                                      sx={{ mb: 3 }}
                                    >
                            <Grid item xs={12} md={6}>
                              <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                          transition={{
                                            duration: 0.5,
                                            delay: 1.1,
                                          }}
                              >
                                <Card
                                  sx={{
                                    borderRadius: 2,
                                    border: `1px solid ${theme.palette.divider}`,
                                              boxShadow:
                                                "0 1px 3px rgba(0,0,0,0.05)",
                                  }}
                                >
                                  <CardContent sx={{ p: 3 }}>
                                    <Typography
                                      variant="h6"
                                      mb={2}
                                      fontWeight={600}
                                      sx={{ fontSize: "1rem" }}
                                    >
                                      Top Competitors
                                    </Typography>
                                    <Box
                                      display="flex"
                                      flexDirection="column"
                                      gap={1.5}
                                    >
                                      {brandAnalytics.top_competitors
                                        .slice(0, 10)
                                        .map((comp, idx) => (
                                          <Paper
                                            key={idx}
                                            sx={{
                                              p: 1.5,
                                              borderLeft: `3px solid ${theme.palette.primary.main}`,
                                              borderRadius: 1.5,
                                              transition: "all 0.2s",
                                              "&:hover": {
                                                          transform:
                                                            "translateX(2px)",
                                                boxShadow:
                                                  "0 2px 8px rgba(0,0,0,0.05)",
                                              },
                                            }}
                                          >
                                            <Box
                                              display="flex"
                                              justifyContent="space-between"
                                              alignItems="center"
                                            >
                                              <Box
                                                display="flex"
                                                alignItems="center"
                                                gap={1}
                                              >
                                                <Chip
                                                            label={`#${
                                                              idx + 1
                                                            }`}
                                                  size="small"
                                                  sx={{
                                                    bgcolor:
                                                                theme.palette
                                                                  .primary.main,
                                                    color: "white",
                                                    fontWeight: 700,
                                                              fontSize:
                                                                "0.7rem",
                                                    height: 20,
                                                    minWidth: 28,
                                                  }}
                                                />
                                                <Typography
                                                  variant="body2"
                                                  fontWeight={600}
                                                            sx={{
                                                              fontSize:
                                                                "0.875rem",
                                                            }}
                                                >
                                                  {comp.name}
                                                </Typography>
                                              </Box>
                                              <Typography
                                                variant="body2"
                                                fontWeight={700}
                                                color="primary.main"
                                                          sx={{
                                                            fontSize:
                                                              "0.875rem",
                                                          }}
                                              >
                                                {comp.count.toLocaleString()}
                                              </Typography>
                                            </Box>
                                          </Paper>
                                        ))}
                                    </Box>
                                  </CardContent>
                                </Card>
                              </motion.div>
                            </Grid>

                            {/* Top Topics - Chips List */}
                            {brandAnalytics.top_topics &&
                                        brandAnalytics.top_topics.length >
                                          0 && (
                                <Grid item xs={12} md={6}>
                                  <motion.div
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                              transition={{
                                                duration: 0.5,
                                                delay: 1.2,
                                              }}
                                  >
                                    <Card
                                      sx={{
                                        borderRadius: 2,
                                        border: `1px solid ${theme.palette.divider}`,
                                                  boxShadow:
                                                    "0 1px 3px rgba(0,0,0,0.05)",
                                      }}
                                    >
                                      <CardContent sx={{ p: 3 }}>
                                        <Typography
                                          variant="h6"
                                          mb={2}
                                          fontWeight={600}
                                          sx={{ fontSize: "1rem" }}
                                        >
                                          Top Topics
                                        </Typography>
                                        <Box
                                          display="flex"
                                          flexWrap="wrap"
                                          gap={1}
                                        >
                                          {brandAnalytics.top_topics
                                            .slice(0, 20)
                                            .map((topic, idx) => (
                                              <Chip
                                                key={idx}
                                                label={`${topic.topic} (${topic.count})`}
                                                size="small"
                                                sx={{
                                                  bgcolor: alpha(
                                                              theme.palette
                                                                .primary.main,
                                                    0.08
                                                  ),
                                                            color:
                                                              "primary.main",
                                                  fontWeight: 600,
                                                  fontSize: "0.75rem",
                                                  height: 28,
                                                  "&:hover": {
                                                    bgcolor: alpha(
                                                                theme.palette
                                                                  .primary.main,
                                                      0.15
                                                    ),
                                                  },
                                                }}
                                              />
                                            ))}
                                        </Box>
                                      </CardContent>
                                    </Card>
                                  </motion.div>
                                </Grid>
                              )}
                          </Grid>
                        )}
                          </Box>
                        )}

                      {/* Advanced Query Visualizations - Sub-section under Scrunch AI (no separate heading) */}
                      {selectedBrandId &&
                        isChartVisible("scrunch_visualizations") && (
                          <Box sx={{ mb: 4, mt: 4 }}>
                            <ScrunchVisualizations
                              brandId={selectedBrandId}
                              startDate={startDate}
                              endDate={endDate}
                            />
                          </Box>
                        )}
                    </>
                  );
                })()}
              </SectionContainer>
            )}

            {/* Agency Analytics / Keywords Section */}
            {isSectionVisible("agency_analytics") &&
              selectedClientId &&
              (shouldShowSectionKPIs("agency_analytics") ||
                shouldShowSectionCharts("agency_analytics")) && (
                <SectionContainer
                  title={
                        isPublic ? "Organic Visibility" : "Agency Analytics"
                  }
                  description="Keyword Ranking Trends, Growth & Position Insights"
                  descriptionSx={{ mb: { xs: 3, sm: 4 } }}
                >
                  <Box
                    sx={{
                      display: "flex",
                      flexDirection: "column",
                      gap: 3,
                    }}
                  >
                    {/* Top Keywords Ranking Chart */}
                    {dashboardData?.chart_data?.all_keywords_ranking &&
                      dashboardData.chart_data.all_keywords_ranking.length >
                        0 &&
                      isChartVisible("all_keywords_ranking") && (
                        <ChartCard
                          title="Top Keywords Ranking"
                          badge={getBadgeLabel("AgencyAnalytics")}
                          badgeColor={CHART_COLORS.agencyAnalytics.primary}
                          height={500}
                          animationDelay={0.2}
                        >
                          <BarChartEnhanced
                            data={dashboardData.chart_data.all_keywords_ranking.map(
                              (kw) => ({
                                keyword: kw.keyword || "Unknown",
                                avgRank: kw.average_ranking || 0,
                                avgVolume: kw.average_search_volume || 0,
                              })
                            )}
                            dataKey="keyword"
                            horizontal={true}
                            bars={[
                              {
                                dataKey: "avgRank",
                                name: "Avg Google Ranking",
                                color: CHART_COLORS.agencyAnalytics.primary,
                              },
                            ]}
                            formatter={(value, name) => {
                              if (name === "avgRank")
                                return [
                                  `Position ${value.toFixed(1)}`,
                                  "Avg Google Ranking",
                                ];
                              if (name === "avgVolume")
                                return [
                                  value.toLocaleString(),
                                  "Avg Search Volume",
                                ];
                              return [value, name];
                            }}
                            margin={{
                              top: 5,
                              right: 30,
                              left: 120,
                              bottom: 5,
                            }}
                            height={400}
                          />
                        </ChartCard>
                      )}

                    {/* Keywords Overview */}
                    <KeywordsDashboard
                      clientId={selectedClientId}
                      selectedKPIs={
                        isPublic
                          ? publicKPISelections || selectedKPIs
                          : selectedKPIs
                      }
                      startDate={startDate}
                      endDate={endDate}
                      isChartVisible={isChartVisible}
                    />
                  </Box>
                </SectionContainer>
              )}

            {/* General KPI Grid - All Other KPIs */}
            {/* "All Performance Metrics" section should always show if there are KPIs to display */}
            {/* It's a summary section, not a data source section, so it doesn't need to be in visible_sections */}
            {/* {displayedKPIs.length > 0 && (
              <SectionContainer title="All Performance Metrics">
                <Grid container spacing={2} sx={{ mb: 4 }}>
                  {displayedKPIs.map(([key, kpi], index) => (
                    <KPICard
                      key={key}
                      kpi={kpi}
                      kpiKey={key}
                      index={index}
                      theme={theme}
                      getSourceLabel={getSourceLabel}
                    />
                  ))}
                </Grid>
              </SectionContainer>
            )} */}
          </Box>
            </>
          )}
        </>
      ) : !loading &&
        (selectedBrandId || (isPublic && publicSlug)) &&
        dashboardData?.no_data ? (
        <Alert severity="info" sx={{ borderRadius: 2 }}>
          <Typography variant="h6" gutterBottom>
            No Data Available
          </Typography>
          <Typography variant="body2">
            {dashboardData.message ||
              "No data is currently available for this dashboard. Please check back later or contact support if you believe this is an error."}
          </Typography>
          {!isPublic && (
            <Box component="ul" sx={{ mt: 1, mb: 0, pl: 2 }}>
              <li>GA4: Configure GA4 property ID in brand settings</li>
              <li>
                Agency Analytics: Sync campaigns and link them to this brand
              </li>
              <li>Scrunch: Ensure brand is synced from Scrunch API</li>
            </Box>
          )}
        </Alert>
      ) : !loading && selectedBrandId && !dashboardData?.no_data ? (
        <Alert severity="info" sx={{ borderRadius: 2 }}>
          No data available for this brand. Please ensure the brand has data
          sources configured:
          <Box component="ul" sx={{ mt: 1, mb: 0, pl: 2 }}>
            <li>GA4: Configure GA4 property ID in brand settings</li>
            <li>
              Agency Analytics: Sync campaigns and link them to this brand
            </li>
            <li>Scrunch: Ensure brand is synced from Scrunch API</li>
          </Box>
        </Alert>
      ) : !loading ? (
        <Alert severity="info" sx={{ borderRadius: 2 }}>
          Please select a client to view the reporting dashboard.
        </Alert>
      ) : null}
      {/* KPI Selector Dialog */}
      <Dialog
        open={showKPISelector}
        onClose={() => setShowKPISelector(false)}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: { borderRadius: 2 },
        }}
      >
        <DialogTitle>
          <Box
            display="flex"
            justifyContent="space-between"
            alignItems="center"
          >
            <Typography variant="h6" fontWeight={600}>
              Select KPIs 
            </Typography>
          </Box>
        </DialogTitle>
        <DialogContent dividers sx={{ maxHeight: 600, overflow: "auto" }}>
          <Box>
            {/* Section Visibility Controls - Nested Structure */}
            <Box
              mb={4}
              pb={3}
              borderBottom={`1px solid ${theme.palette.divider}`}
            >
              <Box
                display="flex"
                justifyContent="space-between"
                alignItems="center"
                mb={2}
              >
                <Typography
                  variant="subtitle1"
                  fontWeight={700}
                  sx={{
                    fontSize: "1rem",
                    letterSpacing: "-0.01em",
                  }}
                >
                  Dashboard Sections
                </Typography>
                <Box display="flex" gap={1}>
                  <Button
                    size="small"
                    onClick={handleSelectAllSections}
                    variant="outlined"
                  >
                    Select All
                  </Button>
                  <Button
                    size="small"
                    onClick={handleDeselectAllSections}
                    variant="outlined"
                  >
                    Deselect All
                  </Button>
                </Box>
              </Box>
              <Typography
                variant="body2"
                color="text.secondary"
                mb={2}
                sx={{ fontSize: "0.875rem" }}
              >
                Choose which sections should be visible in the public dashboard
                view. Each section shows specific KPIs and visualizations.
              </Typography>

              {/* Nested Dashboard Section Selection with Accordion */}
              {[
                {
                  key: "ga4",
                  label: "Website Analytics",
                  description:
                    "Google Analytics 4 - Website traffic, engagement, and conversion metrics",
                  icon: AnalyticsIcon,
                  color: getSourceColor("GA4"),
                },
                {
                  key: "agency_analytics",
                  label: "Organic Visibility",
                  description:
                    "Agency Analytics - Keyword rankings, search volume, and SEO performance metrics",
                  icon: SearchIcon,
                  color: getSourceColor("AgencyAnalytics"),
                },
                {
                  key: "scrunch_ai",
                  label: "AI Visibility",
                  description:
                    "Scrunch AI - AI platform presence, engagement, competitor insights (includes Brand Analytics and Advanced Query Visualizations as sub-sections)",
                  icon: AnalyticsIcon,
                  color: getSourceColor("Scrunch"),
                },
                // {
                //   key: "all_performance_metrics",
                //   label: "All Performance Metrics",
                //   description:
                //     "Summary section - KPIs shown in the summary section (independent from source sections)",
                //   icon: AnalyticsIcon,
                //   color: theme.palette.primary.main,
                // },
              ].map((section) => {
                // For "All Performance Metrics", use all KPIs from KPI_ORDER
                const sectionKPIs =
                  section.key === "all_performance_metrics"
                  ? KPI_ORDER.filter((key) => {
                      const allKPIs = {
                        ...(dashboardData?.kpis || {}),
                        ...(scrunchData?.kpis || {}),
                      };
                        return (
                          allKPIs[key] && key !== "competitive_benchmarking"
                        );
                    })
                  : getDashboardSectionKPIs(section.key);
                const sectionCharts = getDashboardSectionCharts(section.key);
                // For "All Performance Metrics", use tempSelectedPerformanceMetricsKPIs
                const selectedKPICount =
                  section.key === "all_performance_metrics"
                    ? sectionKPIs.filter((k) =>
                        tempSelectedPerformanceMetricsKPIs.has(k)
                      ).length
                  : sectionKPIs.filter((k) => tempSelectedKPIs.has(k)).length;
                const totalKPICount = sectionKPIs.length;
                const selectedChartCount = sectionCharts.filter((c) =>
                  tempSelectedCharts.has(c.key)
                ).length;
                const totalChartCount = sectionCharts.length;
                const isExpanded = expandedSections.has(section.key);
                // For "All Performance Metrics", check tempSelectedPerformanceMetricsKPIs
                const allKPIsSelected =
                  section.key === "all_performance_metrics"
                    ? sectionKPIs.every((k) =>
                        tempSelectedPerformanceMetricsKPIs.has(k)
                      )
                  : areAllDashboardSectionKPIsSelected(section.key);
                const someKPIsSelected =
                  section.key === "all_performance_metrics"
                    ? sectionKPIs.some((k) =>
                        tempSelectedPerformanceMetricsKPIs.has(k)
                      ) && !allKPIsSelected
                  : areSomeDashboardSectionKPIsSelected(section.key);
                const allChartsSelected =
                  sectionCharts.length > 0 &&
                  sectionCharts.every((c) => tempSelectedCharts.has(c.key));
                const someChartsSelected =
                  sectionCharts.length > 0 &&
                  sectionCharts.some((c) => tempSelectedCharts.has(c.key)) &&
                  !allChartsSelected;
                const SectionIcon = section.icon;

                return (
                  <Accordion
                    key={section.key}
                    expanded={isExpanded}
                    onChange={handleAccordionChange(section.key)}
                    sx={{
                      mb: 1.5,
                      borderRadius: 2,
                      border: `1px solid ${theme.palette.divider}`,
                      boxShadow: "none",
                      "&:before": {
                        display: "none",
                      },
                      "&.Mui-expanded": {
                        margin: "0 0 12px 0",
                      },
                    }}
                  >
                    <AccordionSummary
                      expandIcon={
                        <ExpandMoreIcon sx={{ color: section.color }} />
                      }
                      sx={{
                        px: 2,
                        py: 1.5,
                        "&.Mui-expanded": {
                          minHeight: 48,
                        },
                        "& .MuiAccordionSummary-content": {
                          margin: "12px 0",
                          "&.Mui-expanded": {
                            margin: "12px 0",
                          },
                        },
                      }}
                    >
                      <Box
                        display="flex"
                        alignItems="center"
                        justifyContent="space-between"
                        width="100%"
                        pr={2}
                      >
                        <Box
                          display="flex"
                          alignItems="center"
                          gap={1.5}
                          flex={1}
                        >
                          {/* Only show section visibility checkbox for non-performance-metrics sections */}
                          {section.key !== "all_performance_metrics" && (
                            <Checkbox
                              checked={tempVisibleSections.has(section.key)}
                              onChange={(e) =>
                                handleSectionChange(
                                  section.key,
                                  e.target.checked
                                )
                              }
                              onClick={(e) => e.stopPropagation()}
                              sx={{
                                color: section.color,
                                "&.Mui-checked": {
                                  color: section.color,
                                },
                              }}
                            />
                          )}
                          {section.key === "all_performance_metrics" && (
                            <Box sx={{ width: 40 }} /> // Spacer for alignment
                          )}
                          <SectionIcon
                            sx={{
                              fontSize: 20,
                              color: section.color,
                            }}
                          />
                          <Box>
                            <Typography
                              variant="subtitle1"
                              fontWeight={600}
                              sx={{
                                fontSize: "0.9375rem",
                                color: "text.primary",
                              }}
                            >
                              {section.label}
                            </Typography>
                            <Typography
                              variant="caption"
                              color="text.secondary"
                              sx={{
                                fontSize: "0.75rem",
                              }}
                            >
                              {section.description}
                              {totalKPICount > 0 &&
                                ` • ${selectedKPICount} of ${totalKPICount} KPIs`}
                              {totalChartCount > 0 &&
                                ` • ${selectedChartCount} of ${totalChartCount} charts`}
                            </Typography>
                          </Box>
                        </Box>
                      </Box>
                    </AccordionSummary>
                    <AccordionDetails sx={{ px: 2, pb: 2, pt: 0 }}>
                      <Box sx={{ pl: 4.5 }}>
                        {/* KPIs Section */}
                        {sectionKPIs.length > 0 && (
                          <Box mb={sectionCharts.length > 0 ? 3 : 0}>
                            <Box
                              display="flex"
                              alignItems="center"
                              justifyContent="space-between"
                              mb={1.5}
                            >
                              <Typography
                                variant="body2"
                                fontWeight={600}
                                sx={{ fontSize: "0.875rem" }}
                              >
                                KPIs displayed in this section:
                              </Typography>
                              <Box display="flex" gap={1}>
                                <Checkbox
                                  checked={allKPIsSelected}
                                  indeterminate={someKPIsSelected}
                                  onChange={(e) => {
                                    if (
                                      section.key === "all_performance_metrics"
                                    ) {
                                      const newSelected = new Set(
                                        tempSelectedPerformanceMetricsKPIs
                                      );
                                      if (e.target.checked) {
                                        sectionKPIs.forEach((k) =>
                                          newSelected.add(k)
                                        );
                                      } else {
                                        sectionKPIs.forEach((k) =>
                                          newSelected.delete(k)
                                        );
                                      }
                                      setTempSelectedPerformanceMetricsKPIs(
                                        newSelected
                                      );
                                    } else {
                                      handleDashboardSectionKPIsChange(
                                        section.key,
                                        e.target.checked
                                      );
                                    }
                                  }}
                                  size="small"
                                  sx={{
                                    color: section.color,
                                    "&.Mui-checked": {
                                      color: section.color,
                                    },
                                    "&.MuiCheckbox-indeterminate": {
                                      color: section.color,
                                    },
                                  }}
                                />
                                <Typography
                                  variant="caption"
                                  color="text.secondary"
                                  sx={{ fontSize: "0.75rem" }}
                                >
                                  {allKPIsSelected
                                    ? "Deselect All"
                                    : someKPIsSelected
                                    ? "Select All"
                                    : "Select All"}
                                </Typography>
                              </Box>
                            </Box>
                            <Box display="flex" flexDirection="column" gap={1}>
                              {sectionKPIs.map((key) => {
                                const metadata = KPI_METADATA[key];
                                const kpi = dashboardData?.kpis?.[key];
                                // Auth view: always allow selecting KPIs (so user can configure public view)
                                // Public view: allow selection if KPI exists or is one of our agency/scrunch KPIs
                                const isAgencySection =
                                  section.key === "agency_analytics";
                                const isScrunchSection =
                                  section.key === "scrunch_ai";
                                const allowPublicOverride =
                                  isPublic &&
                                  (isAgencySection || isScrunchSection);
                                const isAvailable =
                                  !isPublic || !!kpi || allowPublicOverride;

                                return (
                                  <FormControlLabel
                                    key={key}
                                    control={
                                      <Checkbox
                                        checked={
                                          section.key ===
                                          "all_performance_metrics"
                                            ? tempSelectedPerformanceMetricsKPIs.has(
                                                key
                                              )
                                            : tempSelectedKPIs.has(key)
                                        }
                                        onChange={(e) => {
                                          if (
                                            section.key ===
                                            "all_performance_metrics"
                                          ) {
                                            const newSelected = new Set(
                                              tempSelectedPerformanceMetricsKPIs
                                            );
                                            if (e.target.checked) {
                                              newSelected.add(key);
                                            } else {
                                              newSelected.delete(key);
                                            }
                                            setTempSelectedPerformanceMetricsKPIs(
                                              newSelected
                                            );
                                          } else {
                                            handleKPIChange(
                                              key,
                                              e.target.checked
                                            );
                                          }
                                        }}
                                        disabled={!isAvailable}
                                        size="small"
                                        sx={{
                                          color: section.color,
                                          "&.Mui-checked": {
                                            color: section.color,
                                          },
                                          "&.Mui-disabled": {
                                            color: theme.palette.grey[400],
                                          },
                                        }}
                                      />
                                    }
                                    label={
                                      <Box
                                        display="flex"
                                        alignItems="center"
                                        justifyContent="space-between"
                                        width="100%"
                                      >
                                        <Box>
                                          <Typography
                                            variant="body2"
                                            fontWeight={500}
                                            sx={{ fontSize: "0.875rem" }}
                                          >
                                            {metadata.label}
                                          </Typography>
                                          <Typography
                                            variant="caption"
                                            color="text.secondary"
                                            sx={{ fontSize: "0.7rem" }}
                                          >
                                            {metadata.source}
                                          </Typography>
                                        </Box>
                                        {!isAvailable && (
                                          <Chip
                                            label="Not Available"
                                            size="small"
                                            sx={{
                                              height: 18,
                                              fontSize: "0.65rem",
                                              bgcolor: theme.palette.grey[100],
                                              color: theme.palette.grey[600],
                                            }}
                                          />
                                        )}
                                      </Box>
                                    }
                                    sx={{
                                      mb: 0.5,
                                      width: "100%",
                                      opacity: isAvailable ? 1 : 0.6,
                                      alignItems: "flex-start",
                                    }}
                                  />
                                );
                              })}
                            </Box>
                          </Box>
                        )}

                        {/* Charts/Visualizations Section */}
                        {sectionCharts.length > 0 && (
                          <Box>
                            <Box
                              display="flex"
                              alignItems="center"
                              justifyContent="space-between"
                              mb={1.5}
                            >
                              <Typography
                                variant="body2"
                                fontWeight={600}
                                sx={{ fontSize: "0.875rem" }}
                              >
                                Charts & Visualizations:
                              </Typography>
                              <Box display="flex" gap={1}>
                                <Checkbox
                                  checked={allChartsSelected}
                                  indeterminate={someChartsSelected}
                                  onChange={(e) => {
                                    const newSelected = new Set(
                                      tempSelectedCharts
                                    );
                                    if (e.target.checked) {
                                      sectionCharts.forEach((chart) =>
                                        newSelected.add(chart.key)
                                      );
                                    } else {
                                      sectionCharts.forEach((chart) =>
                                        newSelected.delete(chart.key)
                                      );
                                    }
                                    setTempSelectedCharts(newSelected);
                                  }}
                                  size="small"
                                  sx={{
                                    color: section.color,
                                    "&.Mui-checked": {
                                      color: section.color,
                                    },
                                    "&.MuiCheckbox-indeterminate": {
                                      color: section.color,
                                    },
                                  }}
                                />
                                <Typography
                                  variant="caption"
                                  color="text.secondary"
                                  sx={{ fontSize: "0.75rem" }}
                                >
                                  {allChartsSelected
                                    ? "Deselect All"
                                    : someChartsSelected
                                    ? "Select All"
                                    : "Select All"}
                                </Typography>
                              </Box>
                            </Box>
                            <Box display="flex" flexDirection="column" gap={1}>
                              {sectionCharts.map((chart, index) => {
                                const isChartSelected = tempSelectedCharts.has(
                                  chart.key
                                );
                                // Group sub-sections under scrunch_ai visually
                                const isSubSection =
                                  section.key === "scrunch_ai" &&
                                  (chart.key === "brand_analytics_charts" ||
                                    chart.key === "scrunch_visualizations");
                                const isFirstSubSection =
                                  isSubSection &&
                                  index > 0 && 
                                  !(
                                    sectionCharts[index - 1].key ===
                                      "brand_analytics_charts" ||
                                    sectionCharts[index - 1].key ===
                                      "scrunch_visualizations"
                                  );
                                
                                return (
                                  <Box key={chart.key}>
                                    {isFirstSubSection && (
                                      <Typography
                                        variant="caption"
                                        color="text.secondary"
                                        sx={{
                                          fontSize: "0.7rem",
                                          fontWeight: 600,
                                          textTransform: "uppercase",
                                          letterSpacing: "0.05em",
                                          mb: 0.5,
                                          mt: 1,
                                          display: "block",
                                        }}
                                      >
                                        Sub-sections:
                                      </Typography>
                                    )}
                                    <FormControlLabel
                                      control={
                                        <Checkbox
                                          checked={isChartSelected}
                                          onChange={(e) => {
                                            const newSelected = new Set(
                                              tempSelectedCharts
                                            );
                                            if (e.target.checked) {
                                              newSelected.add(chart.key);
                                            } else {
                                              newSelected.delete(chart.key);
                                            }
                                            setTempSelectedCharts(newSelected);
                                          }}
                                          size="small"
                                          sx={{
                                            color: section.color,
                                            "&.Mui-checked": {
                                              color: section.color,
                                            },
                                          }}
                                        />
                                      }
                                      label={
                                        <Box>
                                          <Box
                                            display="flex"
                                            alignItems="center"
                                            gap={0.5}
                                          >
                                            <Typography
                                              variant="body2"
                                              fontWeight={500}
                                              sx={{ fontSize: "0.875rem" }}
                                            >
                                              {chart.label}
                                            </Typography>
                                            {isSubSection && (
                                              <Chip
                                                label="Sub-section"
                                                size="small"
                                                sx={{
                                                  height: 16,
                                                  fontSize: "0.6rem",
                                                  bgcolor: alpha(
                                                    section.color,
                                                    0.1
                                                  ),
                                                  color: section.color,
                                                  fontWeight: 500,
                                                }}
                                              />
                                            )}
                                          </Box>
                                          <Typography
                                            variant="caption"
                                            color="text.secondary"
                                            sx={{ fontSize: "0.7rem" }}
                                          >
                                            {chart.description}
                                          </Typography>
                                        </Box>
                                      }
                                      sx={{
                                        mb: 0.5,
                                        width: "100%",
                                        alignItems: "flex-start",
                                        pl: isSubSection ? 2 : 0,
                                      }}
                                    />
                                  </Box>
                                );
                              })}
                            </Box>
                          </Box>
                        )}

                        {sectionKPIs.length === 0 &&
                          sectionCharts.length === 0 && (
                            <Typography
                              variant="body2"
                              color="text.secondary"
                              sx={{ fontSize: "0.875rem", fontStyle: "italic" }}
                            >
                              This section has no selectable KPIs or charts.
                            </Typography>
                          )}

                        {/* Show Change Period Toggle */}
                        <Box
                          mt={3}
                          pt={2}
                          borderTop={`1px solid ${theme.palette.divider}`}
                        >
                          <FormControlLabel
                            control={
                              <Checkbox
                                checked={tempShowChangePeriod[section.key] !== false}
                                onChange={(e) => {
                                  setTempShowChangePeriod({
                                    ...tempShowChangePeriod,
                                    [section.key]: e.target.checked,
                                  });
                                }}
                                size="small"
                                sx={{
                                  color: section.color,
                                  "&.Mui-checked": {
                                    color: section.color,
                                  },
                                }}
                              />
                            }
                            label={
                              <Box>
                                <Typography
                                  variant="body2"
                                  fontWeight={600}
                                  sx={{ fontSize: "0.875rem" }}
                                >
                                  Show Change Period
                                </Typography>
                                <Typography
                                  variant="caption"
                                  color="text.secondary"
                                  sx={{ fontSize: "0.75rem" }}
                                >
                                  Display percentage change indicators for KPIs in this section
                                </Typography>
                              </Box>
                            }
                            sx={{
                              width: "100%",
                              alignItems: "flex-start",
                            }}
                          />
                        </Box>
                      </Box>
                    </AccordionDetails>
                  </Accordion>
                );
              })}
            </Box>
          </Box>
        </DialogContent>
        <DialogActions
          sx={{ p: 2, borderTop: `1px solid ${theme.palette.divider}` }}
        >
          <Button
            onClick={() => {
              setTempSelectedKPIs(new Set(selectedKPIs));
              setTempSelectedPerformanceMetricsKPIs(
                new Set(selectedPerformanceMetricsKPIs)
              );
              setTempVisibleSections(new Set(visibleSections));
              setTempSelectedCharts(new Set(selectedCharts));
              setShowKPISelector(false);
            }}
            variant="outlined"
          >
            Cancel
          </Button>
          <Button
            onClick={handleSaveKPISelection}
            variant="contained"
            disabled={tempVisibleSections.size === 0}
            sx={{
              bgcolor: theme.palette.primary.main,
              "&:hover": {
                bgcolor: theme.palette.primary.dark,
              },
            }}
          >
            Save Changes
          </Button>
        </DialogActions>
      </Dialog>

      {/* Link Create/Edit Dialog */}
      <Dialog
        open={linkDialogOpen}
        onClose={() => {
          setLinkDialogOpen(false);
          // Don't clear editingLink here - keep it selected in dropdown
        }}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 2,
            boxShadow: "0 8px 32px rgba(0,0,0,0.12)",
          },
        }}
      >
        <DialogTitle>
          <Typography variant="h6" fontWeight={600}>
            {editingLink ? "Edit Dashboard Link" : "Create Dashboard Link"}
          </Typography>
        </DialogTitle>
        <DialogContent sx={{ position: "relative" }}>
          {loading && (
            <Box
              sx={{
                position: "absolute",
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                bgcolor: "rgba(255, 255, 255, 0.95)",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                zIndex: 1000,
                borderRadius: 2,
              }}
            >
              <CircularProgress size={40} sx={{ mb: 2 }} />
              <Typography variant="body1" color="text.secondary" fontWeight={500}>
                Generating AI overview...
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
                This may take a few moments
              </Typography>
            </Box>
          )}
          <Box sx={{ borderBottom: 1, borderColor: "divider", mb: 2 }}>
            <Tabs
              value={linkDialogTab}
              onChange={(e, newValue) => setLinkDialogTab(newValue)}
              sx={{ minHeight: 48 }}
              disabled={loading}
            >
              <Tab label="Basic" sx={{ textTransform: "none" }} />
              <Tab label="Advanced" sx={{ textTransform: "none" }} />
            </Tabs>
          </Box>
          {linkDialogTab === 0 && (
            <Box display="flex" flexDirection="column" gap={2} sx={{ opacity: loading ? 0.5 : 1 }}>
              <Box display="flex" gap={2}>
                <TextField
                  label="Start Date"
                  type="date"
                  value={linkFormData.start_date}
                  onChange={(e) => {
                    const newStartDate = e.target.value;
                    const newFormData = {
                      ...linkFormData,
                      start_date: newStartDate,
                    };
                    // Auto-update name and description when dates change (only for new links)
                    if (!editingLink) {
                      newFormData.name = generateAutoLinkName(newStartDate, linkFormData.end_date);
                      newFormData.description = generateAutoLinkDescription(newStartDate, linkFormData.end_date);
                    }
                    setLinkFormData(newFormData);
                  }}
                  fullWidth
                  required
                  InputLabelProps={{ shrink: true }}
                  disabled={loading}
                />
                <TextField
                  label="End Date"
                  type="date"
                  value={linkFormData.end_date}
                  onChange={(e) => {
                    const newEndDate = e.target.value;
                    const newFormData = {
                      ...linkFormData,
                      end_date: newEndDate,
                    };
                    // Auto-update name and description when dates change (only for new links)
                    if (!editingLink) {
                      newFormData.name = generateAutoLinkName(linkFormData.start_date, newEndDate);
                      newFormData.description = generateAutoLinkDescription(linkFormData.start_date, newEndDate);
                    }
                    setLinkFormData(newFormData);
                  }}
                  fullWidth
                  required
                  InputLabelProps={{ shrink: true }}
                  disabled={loading}
                />
              </Box>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={linkFormData.enabled}
                    onChange={(e) =>
                      setLinkFormData({
                        ...linkFormData,
                        enabled: e.target.checked,
                      })
                    }
                    disabled={loading}
                  />
                }
                label="Enabled"
              />
              {!editingLink && (
                <Alert severity="info">
                  <Typography variant="body2">
                    Link will be automatically named based on the date range and creator.
                    Current KPI selections will be saved with this link.
                  </Typography>
                </Alert>
              )}
              {editingLink && (
                <Alert severity="info">
                  <Typography variant="body2">
                    Current KPI selections will be saved with this link. You can
                    modify KPIs in the selector and update this link to save
                    changes.
                  </Typography>
                </Alert>
              )}
            </Box>
          )}
          {linkDialogTab === 1 && (
            <Box display="flex" flexDirection="column" gap={2} sx={{ opacity: loading ? 0.5 : 1 }}>
              <TextField
                label="Name"
                value={linkFormData.name}
                onChange={(e) =>
                  setLinkFormData({ ...linkFormData, name: e.target.value })
                }
                fullWidth
                helperText={editingLink ? "Friendly name for this link" : "Auto-generated based on date range. You can customize it here."}
                disabled={loading}
              />
              <TextField
                label="Description"
                value={linkFormData.description}
                onChange={(e) =>
                  setLinkFormData({
                    ...linkFormData,
                    description: e.target.value,
                  })
                }
                fullWidth
                multiline
                rows={2}
                helperText={editingLink ? "Optional description for this link" : "Auto-generated based on date range and creator. You can customize it here."}
                disabled={loading}
              />
              <TextField
                label="Slug (optional)"
                value={linkFormData.slug}
                onChange={(e) =>
                  setLinkFormData({ ...linkFormData, slug: e.target.value })
                }
                fullWidth
                helperText="Leave empty to auto-generate. Must be unique."
                disabled={loading}
              />
              <TextField
                label="Expires At (optional)"
                type="datetime-local"
                value={linkFormData.expires_at}
                onChange={(e) =>
                  setLinkFormData({ ...linkFormData, expires_at: e.target.value })
                }
                fullWidth
                InputLabelProps={{ shrink: true }}
                helperText="Optional expiration date and time"
                disabled={loading}
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button
            onClick={() => {
              setLinkDialogOpen(false);
              // Don't clear editingLink - keep it selected in dropdown
            }}
            sx={{ textTransform: "none" }}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSaveLink}
            variant="contained"
            disabled={
              loading || !linkFormData.start_date || !linkFormData.end_date
            }
            sx={{ textTransform: "none" }}
            startIcon={loading ? <CircularProgress size={16} color="inherit" /> : null}
          >
            {loading ? "Generating AI overview..." : editingLink ? "Update" : "Create"}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Metrics Dialog */}
      <Dialog
        open={metricsDialogOpen}
        onClose={() => {
          setMetricsDialogOpen(false);
          setLinkMetrics(null);
          setAllLinksMetrics(null);
          setSelectedLinkForMetrics(null);
        }}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 2,
            boxShadow: "0 8px 32px rgba(0,0,0,0.12)",
          },
        }}
      >
        <DialogTitle>
          <Typography variant="h6" fontWeight={600}>
            {selectedLinkForMetrics
              ? `Metrics: ${
                  selectedLinkForMetrics.name || selectedLinkForMetrics.slug
                }`
              : "All Links Metrics"}
          </Typography>
        </DialogTitle>
        <DialogContent>
          {loadingMetrics || loadingAllMetrics ? (
            <Box display="flex" justifyContent="center" py={4}>
              <CircularProgress size={40} />
            </Box>
          ) : selectedLinkForMetrics && linkMetrics ? (
            <Box>
              <Typography variant="h6" mb={2}>
                Total Opens: {linkMetrics.total_opens || 0}
              </Typography>
              {linkMetrics.recent_opens &&
                linkMetrics.recent_opens.length > 0 && (
                <Box>
                  <Typography variant="subtitle2" fontWeight={600} mb={1}>
                    Recent Opens
                  </Typography>
                  <List>
                      {linkMetrics.recent_opens
                        .slice(0, 10)
                        .map((open, idx) => (
                          <ListItem
                            key={idx}
                            sx={{
                              borderBottom: `1px solid ${theme.palette.divider}`,
                            }}
                          >
                        <ListItemText
                              primary={new Date(
                                open.opened_at
                              ).toLocaleString()}
                          secondary={
                            <Box>
                                  {open.ip_address && (
                                    <Typography
                                      variant="caption"
                                      display="block"
                                    >
                                      IP: {open.ip_address}
                                    </Typography>
                                  )}
                              {open.user_agent && (
                                    <Typography
                                      variant="caption"
                                      display="block"
                                      sx={{ wordBreak: "break-all" }}
                                    >
                                  {open.user_agent.substring(0, 100)}
                                </Typography>
                              )}
                            </Box>
                          }
                        />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}
            </Box>
          ) : allLinksMetrics ? (
            <Box>
              <Typography variant="h6" mb={2}>
                Total Opens: {allLinksMetrics.total_opens || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary" mb={2}>
                Across {allLinksMetrics.total_links || 0} links
              </Typography>
              {allLinksMetrics.opens_per_link &&
                allLinksMetrics.opens_per_link.length > 0 && (
                <Box>
                  <Typography variant="subtitle2" fontWeight={600} mb={1}>
                    Opens per Link
                  </Typography>
                  <List>
                    {allLinksMetrics.opens_per_link.map((linkData) => (
                        <ListItem
                          key={linkData.link_id}
                          sx={{
                            borderBottom: `1px solid ${theme.palette.divider}`,
                          }}
                        >
                        <ListItemText
                          primary={linkData.name || linkData.slug}
                          secondary={`${linkData.opens || 0} opens`}
                        />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}
            </Box>
          ) : (
            <Alert severity="info">No metrics available</Alert>
          )}
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button
            onClick={() => {
              setMetricsDialogOpen(false);
              setLinkMetrics(null);
              setAllLinksMetrics(null);
              setSelectedLinkForMetrics(null);
            }}
            sx={{ textTransform: "none" }}
          >
            Close
          </Button>
        </DialogActions>
      </Dialog>

      {/* AI Overview Dialog */}
      <Dialog
        open={showOverviewDialog}
        onClose={() => {
          setShowOverviewDialog(false);
          setExpandedMetricsSources(new Set()); // Reset expanded state when dialog closes
        }}
        maxWidth="lg"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 2,
            border: `1px solid ${theme.palette.divider}`,
          },
        }}
      >
        <DialogTitle
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 1,
            fontWeight: 600,
            pb: 1,
          }}
        >
          <InsightsIcon sx={{ color: theme.palette.primary.main }} />
          <Typography variant="h6" fontWeight={600}>
            {overviewData?.executive_summary
              ? "Executive Summary"
              : "AI Overview - All Metrics"}
          </Typography>
        </DialogTitle>
        <DialogContent>
          {loadingOverview ? (
            <Box
              display="flex"
              flexDirection="column"
              alignItems="center"
              justifyContent="center"
              py={4}
            >
              <CircularProgress size={40} />
              <Typography variant="body2" color="text.secondary" mt={2}>
                Generating AI overview...
              </Typography>
            </Box>
          ) : overviewData ? (
            <Box>
              {/* Overview Header Info */}
              <Box mb={3}>
                <Typography variant="body2" color="text.secondary" mb={1}>
                  <strong>Date Range:</strong>{" "}
                  {overviewData.date_range?.start_date || "N/A"} to{" "}
                  {overviewData.date_range?.end_date || "N/A"}
                </Typography>
                {/* <Typography variant="body2" color="text.secondary">
                  <strong>Metrics Analyzed:</strong>{" "}
                  {overviewData.total_metrics_analyzed} total
                  {overviewData.metrics_by_source && (
                    <>
                      {" "}
                      ({overviewData.metrics_by_source.GA4 || 0} GA4,{" "}
                      {overviewData.metrics_by_source.AgencyAnalytics || 0} SEO,{" "}
                      {overviewData.metrics_by_source.Scrunch || 0} Brand
                      Mentions)
                    </>
                  )}
                </Typography> */}
              </Box>

              {/* AI Generated Overview - Show Executive Summary if available, otherwise show old format */}
              {overviewData.executive_summary ? (
                <ExecutiveSummary
                  summary={overviewData.executive_summary}
                  theme={theme}
                />
              ) : overviewData.overview ? (
              <Paper
                elevation={0}
                sx={{
                  p: 3,
                  bgcolor: alpha(theme.palette.primary.main, 0.05),
                  border: `1px solid ${theme.palette.divider}`,
                  borderRadius: 2,
                  mb: 3,
                }}
              >
                <Typography
                  variant="body1"
                  sx={{
                    whiteSpace: "pre-line",
                    lineHeight: 1.8,
                    fontSize: "0.95rem",
                  }}
                >
                  {overviewData.overview}
                </Typography>
              </Paper>
              ) : (
                <Alert severity="info">
                  No overview data available. Please try again.
                </Alert>
              )}

              {/* Metrics Summary by Source - Only show if not showing Executive Summary */}
              {!overviewData.executive_summary &&
                overviewData.metrics &&
                overviewData.metrics.length > 0 && (
                <Box>
                  <Typography variant="subtitle1" fontWeight={600} mb={2}>
                    Metrics Summary
                  </Typography>
                  <Grid container spacing={2}>
                    {["GA4", "AgencyAnalytics", "Scrunch"].map((source) => {
                      const sourceMetrics = overviewData.metrics.filter(
                        (m) => m.source === source
                      );
                      if (sourceMetrics.length === 0) return null;

                      const isExpanded = expandedMetricsSources.has(source);
                      const metricsToShow = isExpanded
                        ? sourceMetrics
                        : sourceMetrics.slice(0, 5);
                      const hasMore = sourceMetrics.length > 5;

                      return (
                        <Grid item xs={12} md={4} key={source}>
                          <Paper
                            elevation={0}
                            sx={{
                              p: 2,
                              border: `1px solid ${theme.palette.divider}`,
                              borderRadius: 2,
                              bgcolor: "background.paper",
                            }}
                          >
                            <Typography
                              variant="subtitle2"
                              fontWeight={600}
                              mb={1.5}
                            >
                              {isPublic
                                ? source === "GA4"
                                  ? "Website Analytics - Acquisition & User Behavior Insights"
                                  : source === "AgencyAnalytics"
                                  ? "SEO Performance"
                                  : "AI Visibility - AI Search Presence & Competitor Insights"
                                : source === "GA4"
                                ? "Google Analytics 4"
                                : source === "AgencyAnalytics"
                                ? "SEO Rankings"
                                : "Brand Mentions"}
                            </Typography>
                            <Box component="ul" sx={{ m: 0, pl: 2 }}>
                              {metricsToShow.map((metric, idx) => (
                                <li key={idx}>
                                  <Typography
                                    variant="body2"
                                    sx={{ fontSize: "0.875rem" }}
                                  >
                                    <strong>{metric.metric}:</strong>{" "}
                                    {formatValue({
                                      value: metric.value,
                                      format: metric.format,
                                    })}
                                    {metric.change !== null &&
                                      metric.change !== undefined && (
                                        <span
                                          style={{
                                            color:
                                              metric.change > 0
                                                ? theme.palette.success.main
                                                : metric.change < 0
                                                ? theme.palette.error.main
                                                : "inherit",
                                            marginLeft: "8px",
                                          }}
                                        >
                                          (
                                          {metric.change > 0
                                            ? "↑"
                                            : metric.change < 0
                                            ? "↓"
                                            : "→"}{" "}
                                            {Math.abs(metric.change).toFixed(1)}
                                            %)
                                        </span>
                                      )}
                                  </Typography>
                                </li>
                              ))}
                              {hasMore && (
                                <Typography
                                  variant="caption"
                                  color="primary"
                                  onClick={() => {
                                    const newExpanded = new Set(
                                      expandedMetricsSources
                                    );
                                    if (isExpanded) {
                                      newExpanded.delete(source);
                                    } else {
                                      newExpanded.add(source);
                                    }
                                    setExpandedMetricsSources(newExpanded);
                                  }}
                                  sx={{
                                    cursor: "pointer",
                                    textDecoration: "underline",
                                    "&:hover": {
                                      color: theme.palette.primary.dark,
                                    },
                                    display: "block",
                                    mt: 0.5,
                                  }}
                                >
                                  {isExpanded
                                    ? "Show less"
                                    : `+${sourceMetrics.length - 5} more`}
                                </Typography>
                              )}
                            </Box>
                          </Paper>
                        </Grid>
                      );
                    })}
                  </Grid>
                </Box>
              )}
            </Box>
          ) : (
            <Alert severity="info">
              No overview data available. Please try again.
            </Alert>
          )}
        </DialogContent>
        <DialogActions
          sx={{ p: 2, borderTop: `1px solid ${theme.palette.divider}` }}
        >
          <Button
            onClick={() => setShowOverviewDialog(false)}
            variant="outlined"
          >
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default ReportingDashboard;

import { useState, useEffect, useMemo } from "react";
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  CircularProgress,
  Alert,
  Button,
  TextField,
  InputAdornment,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Checkbox,
  IconButton,
  Chip,
  useTheme,
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControlLabel,
  Divider,
} from "@mui/material";
import {
  Search as SearchIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon,
  FilterList as FilterListIcon,
  TrendingUp as TrendingUpIcon,
} from "@mui/icons-material";
import { useQuery } from "@tanstack/react-query";
import { keywordsAPI } from "../services/api";
import { queryKeys } from "../hooks/queryKeys";
import StackedBarChart from "./reporting/charts/StackedBarChart";
import ChartCard from "./reporting/ChartCard";
import { formatDateForAxis } from "./reporting/hooks/useChartData";

export default function KeywordsDashboard({ clientId, selectedKPIs }) {
  const theme = useTheme();
  const selectedKPISet = selectedKPIs instanceof Set ? selectedKPIs : new Set(selectedKPIs || []);
  const showKPI = (key) => {
    if (!selectedKPISet || selectedKPISet.size === 0) return true;
    return selectedKPISet.has(key);
  };
  
  // Return early if no clientId
  if (!clientId) {
    return (
      <Box p={3}>
        <Alert severity="info">Please select a client to view keywords.</Alert>
      </Box>
    );
  }
  
  // State for filters and pagination
  const [search, setSearch] = useState("");
  const [locationCountry, setLocationCountry] = useState("");
  const [sortBy, setSortBy] = useState("volume");
  const [sortOrder, setSortOrder] = useState("desc");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [selectedKeywords, setSelectedKeywords] = useState(new Set());
  const [favoriteKeywords, setFavoriteKeywords] = useState(new Set());
  
  // Advanced filter states
  const [showFilterDialog, setShowFilterDialog] = useState(false);
  const [filters, setFilters] = useState({
    campaign_id: "",
    location_country: "",
    location_region: "",
    location_city: "",
    volume_min: "",
    volume_max: "",
    google_ranking_min: "",
    google_ranking_max: "",
    bing_ranking_min: "",
    bing_ranking_max: "",
    competition_min: "",
    competition_max: "",
    primary_only: false,
    tags: "",
    language: "",
  });
  
  // Date range for chart (last 30 days)
  const endDate = new Date().toISOString().split('T')[0];
  const startDate = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
  
  // Build API filters object
  const apiFilters = {
    search: search || undefined,
    location_country: locationCountry || filters.location_country || undefined,
    location_region: filters.location_region || undefined,
    location_city: filters.location_city || undefined,
    campaign_id: filters.campaign_id || undefined,
    volume_min: filters.volume_min ? parseInt(filters.volume_min) : undefined,
    volume_max: filters.volume_max ? parseInt(filters.volume_max) : undefined,
    google_ranking_min: filters.google_ranking_min ? parseInt(filters.google_ranking_min) : undefined,
    google_ranking_max: filters.google_ranking_max ? parseInt(filters.google_ranking_max) : undefined,
    bing_ranking_min: filters.bing_ranking_min ? parseInt(filters.bing_ranking_min) : undefined,
    bing_ranking_max: filters.bing_ranking_max ? parseInt(filters.bing_ranking_max) : undefined,
    competition_min: filters.competition_min ? parseFloat(filters.competition_min) : undefined,
    competition_max: filters.competition_max ? parseFloat(filters.competition_max) : undefined,
    primary_only: filters.primary_only || undefined,
    tags: filters.tags || undefined,
    language: filters.language || undefined,
    start_date: startDate,
    end_date: endDate,
    // Fetch all rows and sort client-side by volume
    sort_by: "volume",
    sort_order: "desc",
    page: 1,
    page_size: 10000,
  };
  
  // Fetch keywords data
  const {
    data: keywordsData,
    isLoading: keywordsLoading,
    error: keywordsError,
  } = useQuery({
    queryKey: queryKeys.keywords.clientKeywords(clientId, apiFilters),
    queryFn: () => keywordsAPI.getClientKeywords(clientId, apiFilters),
    enabled: !!clientId,
  });
  
  // Fetch rankings over time for chart
  const {
    data: rankingsData,
    isLoading: rankingsLoading,
  } = useQuery({
    queryKey: queryKeys.keywords.clientRankingsOverTime(clientId, { start_date: startDate, end_date: endDate }),
    queryFn: () => keywordsAPI.getClientKeywordRankingsOverTime(clientId, {
      start_date: startDate,
      end_date: endDate,
      group_by: "day",
      engine: "google",
    }),
    enabled: !!clientId,
  });
  
  // Fetch summary KPIs
  const {
    data: summaryData,
    isLoading: summaryLoading,
  } = useQuery({
    queryKey: queryKeys.keywords.clientSummary(clientId, {}),
    queryFn: () => keywordsAPI.getClientKeywordSummary(clientId, {}),
    enabled: !!clientId,
  });
  
  // Handle pagination
  const handleChangePage = (event, newPage) => {
    setPage(newPage + 1);
  };
  
  const handleChangeRowsPerPage = (event) => {
    setPageSize(parseInt(event.target.value, 10));
    setPage(1);
  };
  
  // Handle sorting
  const handleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortBy(field);
      setSortOrder("desc");
    }
  };
  
  // Handle keyword selection
  const handleSelectAll = (event) => {
    if (event.target.checked) {
      const allIds = new Set(keywordsData?.keywords?.map(kw => kw.keyword_id) || []);
      setSelectedKeywords(allIds);
    } else {
      setSelectedKeywords(new Set());
    }
  };
  
  const handleSelectKeyword = (keywordId) => {
    const newSelected = new Set(selectedKeywords);
    if (newSelected.has(keywordId)) {
      newSelected.delete(keywordId);
    } else {
      newSelected.add(keywordId);
    }
    setSelectedKeywords(newSelected);
  };
  
  // Handle favorite toggle
  const handleToggleFavorite = (keywordId, event) => {
    event.stopPropagation();
    const newFavorites = new Set(favoriteKeywords);
    if (newFavorites.has(keywordId)) {
      newFavorites.delete(keywordId);
    } else {
      newFavorites.add(keywordId);
    }
    setFavoriteKeywords(newFavorites);
  };
  
  // Format ranking display
  const formatRanking = (ranking) => {
    if (ranking === null || ranking === undefined) {
      return "not found";
    }
    return ranking.toString();
  };
  
  // Format change display
  const formatChange = (change) => {
    if (change === null || change === undefined || change === 0) {
      return "0";
    }
    return change > 0 ? `+${change}` : change.toString();
  };
  
  // Count active filters
  const activeFiltersCount = Object.values(filters).filter((value) => {
    if (typeof value === "boolean") return value;
    if (typeof value === "string") return value.trim() !== "";
    return value !== null && value !== undefined;
  }).length;
  
  // Handle filter change
  const handleFilterChange = (key, value) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value,
    }));
  };
  
  // Apply filters
  const handleApplyFilters = () => {
    setPage(1); // Reset to first page when filters change
    setShowFilterDialog(false);
  };
  
  // Clear all filters
  const handleClearFilters = () => {
    setFilters({
      campaign_id: "",
      location_country: "",
      location_region: "",
      location_city: "",
      volume_min: "",
      volume_max: "",
      google_ranking_min: "",
      google_ranking_max: "",
      bing_ranking_min: "",
      bing_ranking_max: "",
      competition_min: "",
      competition_max: "",
      primary_only: false,
      tags: "",
      language: "",
    });
    setPage(1);
  };
  
  const keywords = keywordsData?.keywords || [];
  const sortedKeywords = useMemo(
    () => [...keywords].sort((a, b) => (b.search_volume || 0) - (a.search_volume || 0)),
    [keywords]
  );
  const pagination = {
    total: sortedKeywords.length,
    page,
    page_size: pageSize,
    total_pages: Math.max(1, Math.ceil(sortedKeywords.length / pageSize)),
  };
  // Use summaryData from the dedicated summary endpoint, fallback to keywordsData summary
  const summary = summaryData || keywordsData?.summary || {};

  const fmt = (val, digits = 0) => {
    if (val === null || val === undefined) return "0";
    const num = Number(val);
    if (Number.isNaN(num)) return "0";
    return digits > 0 ? num.toFixed(digits) : num.toString();
  };
  
  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Button
          variant="outlined"
          startIcon={<FilterListIcon />}
          onClick={() => setShowFilterDialog(true)}
          sx={{ textTransform: "none" }}
        >
          + Add Filter
          {activeFiltersCount > 0 && (
            <Chip
              label={activeFiltersCount}
              size="small"
              sx={{
                ml: 1,
                height: 20,
                minWidth: 20,
                fontSize: "0.7rem",
                bgcolor: theme.palette.primary.main,
                color: "white",
              }}
            />
          )}
        </Button>
      </Box>
      
      {/* KPI Summary Cards */}
      <Grid container spacing={2} mb={3}>
        {showKPI("average_google_ranking") && (
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ border: `1px solid ${theme.palette.divider}`, borderRadius: 2 }}>
              <CardContent>
                <Typography variant="caption" color="text.secondary">
                  Avg Google Ranking
                </Typography>
                <Typography variant="h4" fontWeight={700}>
                  {fmt(summary.average_google_ranking ?? summary.avg_google_ranking, 1)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        )}
        {showKPI("average_bing_ranking") && (
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ border: `1px solid ${theme.palette.divider}`, borderRadius: 2 }}>
              <CardContent>
                <Typography variant="caption" color="text.secondary">
                  Avg Bing Ranking
                </Typography>
                <Typography variant="h4" fontWeight={700}>
                  {fmt(summary.average_bing_ranking ?? summary.avg_bing_ranking, 1)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        )}
        {showKPI("average_search_volume") && (
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ border: `1px solid ${theme.palette.divider}`, borderRadius: 2 }}>
              <CardContent>
                <Typography variant="caption" color="text.secondary">
                  Avg Search Volume
                </Typography>
                <Typography variant="h4" fontWeight={700}>
                  {fmt(summary.average_search_volume ?? summary.avg_search_volume, 0)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        )}
        {showKPI("top_10_visibility_percentage") && (
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ border: `1px solid ${theme.palette.divider}`, borderRadius: 2 }}>
              <CardContent>
                <Typography variant="caption" color="text.secondary">
                  Top 10 Visibility %
                </Typography>
                <Typography variant="h4" fontWeight={700}>
                  {fmt(summary.top_10_visibility_percentage ?? summary.top10_visibility_percentage, 1)}%
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        )}
        {showKPI("improving_keywords_count") && (
          <Grid item xs={12} sm={6} md={4}>
            <Card sx={{ border: `1px solid ${theme.palette.divider}`, borderRadius: 2 }}>
              <CardContent>
                <Typography variant="caption" color="text.secondary">
                  Improving Keywords
                </Typography>
                <Typography variant="h4" fontWeight={700}>
                  {fmt(summary.improving_keywords_count ?? summary.improving_keywords, 0)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        )}
        {showKPI("declining_keywords_count") && (
          <Grid item xs={12} sm={6} md={4}>
            <Card sx={{ border: `1px solid ${theme.palette.divider}`, borderRadius: 2 }}>
              <CardContent>
                <Typography variant="caption" color="text.secondary">
                  Declining Keywords
                </Typography>
                <Typography variant="h4" fontWeight={700}>
                  {fmt(summary.declining_keywords_count ?? summary.declining_keywords, 0)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        )}
        {showKPI("stable_keywords_count") && (
          <Grid item xs={12} sm={6} md={4}>
            <Card sx={{ border: `1px solid ${theme.palette.divider}`, borderRadius: 2 }}>
              <CardContent>
                <Typography variant="caption" color="text.secondary">
                  Stable Keywords
                </Typography>
                <Typography variant="h4" fontWeight={700}>
                  {fmt(summary.stable_keywords_count ?? summary.stable_keywords, 0)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
      
      {/* Google Rankings Chart */}
      <Card sx={{ mb: 3, border: `1px solid ${theme.palette.divider}`, borderRadius: 2 }}>
        <CardContent>
          <Typography variant="h6" fontWeight={600} mb={2}>
            Google Rankings
          </Typography>
          {rankingsLoading ? (
            <Box display="flex" justifyContent="center" p={4}>
              <CircularProgress />
            </Box>
          ) : rankingsData?.data ? (
            <StackedBarChart
              data={rankingsData.data}
              engine="google"
              height={300}
            />
          ) : (
            <Box p={4} textAlign="center">
              <Typography color="text.secondary">No ranking data available</Typography>
            </Box>
          )}
        </CardContent>
      </Card>
      
      {/* Filters and Search */}
      <Box display="flex" gap={2} mb={2} flexWrap="wrap">
        <TextField
          placeholder="Search"
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
          sx={{ flexGrow: 1, minWidth: 200 }}
        />
        <FormControl sx={{ minWidth: 200 }}>
          <InputLabel>Location</InputLabel>
          <Select
            value={locationCountry}
            label="Location"
            onChange={(e) => {
              setLocationCountry(e.target.value);
              setPage(1);
            }}
          >
            <MenuItem value="">All Locations</MenuItem>
            {/* Location options would be populated from available data */}
          </Select>
        </FormControl>
        <FormControl sx={{ minWidth: 150 }}>
          <InputLabel>Sort By</InputLabel>
          <Select
            value={sortBy}
            label="Sort By"
            onChange={(e) => setSortBy(e.target.value)}
          >
            <MenuItem value="volume">Volume</MenuItem>
            <MenuItem value="google_ranking">Google Ranking</MenuItem>
            <MenuItem value="bing_ranking">Bing Ranking</MenuItem>
            <MenuItem value="keyword_phrase">Keyword</MenuItem>
          </Select>
        </FormControl>
      </Box>
      
      {/* Keywords Table */}
      <Card sx={{ border: `1px solid ${theme.palette.divider}`, borderRadius: 2 }}>
        <CardContent>
          {keywordsLoading ? (
            <Box display="flex" justifyContent="center" p={4}>
              <CircularProgress />
            </Box>
          ) : keywordsError ? (
            <Alert severity="error">Error loading keywords: {keywordsError.message}</Alert>
          ) : (
            <>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="body2" color="text.secondary">
                Showing {Math.min(pageSize, pagination.total - (page - 1) * pageSize)} of {pagination.total} Rows
              </Typography>
              </Box>
              
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell padding="checkbox">
                        <Checkbox
                          indeterminate={selectedKeywords.size > 0 && selectedKeywords.size < keywords.length}
                          checked={keywords.length > 0 && selectedKeywords.size === keywords.length}
                          onChange={handleSelectAll}
                        />
                      </TableCell>
                      <TableCell padding="checkbox"></TableCell>
                      <TableCell>
                        <Button
                          onClick={() => handleSort("keyword_phrase")}
                          sx={{ textTransform: "none", fontWeight: 600 }}
                        >
                          KEYWORD
                          {sortBy === "keyword_phrase" && (sortOrder === "asc" ? " ↑" : " ↓")}
                        </Button>
                      </TableCell>
                      <TableCell>
                        <Button
                          onClick={() => handleSort("google_ranking")}
                          sx={{ textTransform: "none", fontWeight: 600 }}
                        >
                          GOOGLE
                          {sortBy === "google_ranking" && (sortOrder === "asc" ? " ↑" : " ↓")}
                        </Button>
                      </TableCell>
                      <TableCell>
                        <Button
                          onClick={() => handleSort("google_ranking")}
                          sx={{ textTransform: "none", fontWeight: 600 }}
                        >
                          GOOGLE CHANGE
                          {sortBy === "google_ranking" && (sortOrder === "asc" ? " ↑" : " ↓")}
                        </Button>
                      </TableCell>
                      <TableCell>
                        <Button
                          onClick={() => handleSort("bing_ranking")}
                          sx={{ textTransform: "none", fontWeight: 600 }}
                        >
                          BING
                          {sortBy === "bing_ranking" && (sortOrder === "asc" ? " ↑" : " ↓")}
                        </Button>
                      </TableCell>
                      <TableCell>
                        <Button
                          onClick={() => handleSort("volume")}
                          sx={{ textTransform: "none", fontWeight: 600 }}
                        >
                          VOLUME
                          {sortBy === "volume" && (sortOrder === "asc" ? " ↑" : " ↓")}
                        </Button>
                      </TableCell>
                      <TableCell>LOCATION</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {sortedKeywords
                      .slice((page - 1) * pageSize, (page - 1) * pageSize + pageSize)
                      .map((keyword) => (
                      <TableRow key={keyword.keyword_id} hover>
                        <TableCell padding="checkbox">
                          <Checkbox
                            checked={selectedKeywords.has(keyword.keyword_id)}
                            onChange={() => handleSelectKeyword(keyword.keyword_id)}
                          />
                        </TableCell>
                        <TableCell padding="checkbox">
                          <IconButton
                            size="small"
                            onClick={(e) => handleToggleFavorite(keyword.keyword_id, e)}
                          >
                            {favoriteKeywords.has(keyword.keyword_id) ? (
                              <StarIcon sx={{ color: "#ffc107" }} />
                            ) : (
                              <StarBorderIcon />
                            )}
                          </IconButton>
                        </TableCell>
                        <TableCell>{keyword.keyword_phrase || ""}</TableCell>
                        <TableCell>{formatRanking(keyword.google_ranking)}</TableCell>
                        <TableCell>
                          <Chip
                            label={formatChange(keyword.google_change)}
                            size="small"
                            color={keyword.google_change > 0 ? "success" : keyword.google_change < 0 ? "error" : "default"}
                            sx={{ minWidth: 60 }}
                          />
                        </TableCell>
                        <TableCell>{formatRanking(keyword.bing_ranking)}</TableCell>
                        <TableCell>{keyword.search_volume || 0}</TableCell>
                        <TableCell>{keyword.search_location_formatted_name || ""}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
              
              <TablePagination
                component="div"
                count={pagination.total}
                page={pagination.page - 1}
                onPageChange={handleChangePage}
                rowsPerPage={pageSize}
                onRowsPerPageChange={handleChangeRowsPerPage}
                rowsPerPageOptions={[25, 50, 100]}
              />
            </>
          )}
        </CardContent>
      </Card>
      
      {/* Filter Dialog */}
      <Dialog
        open={showFilterDialog}
        onClose={() => setShowFilterDialog(false)}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: { borderRadius: 2 },
        }}
      >
        <DialogTitle>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h6" fontWeight={600}>
              Add Filters
            </Typography>
            {activeFiltersCount > 0 && (
              <Button
                size="small"
                onClick={handleClearFilters}
                sx={{ textTransform: "none" }}
              >
                Clear All
              </Button>
            )}
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          <Grid container spacing={3} sx={{ mt: 1 }}>
            {/* Campaign Filter */}
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Campaign ID"
                type="number"
                value={filters.campaign_id}
                onChange={(e) => handleFilterChange("campaign_id", e.target.value)}
                size="small"
                helperText="Filter by specific campaign"
              />
            </Grid>
            
            {/* Location Filters */}
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Country Code"
                value={filters.location_country}
                onChange={(e) => handleFilterChange("location_country", e.target.value)}
                size="small"
                placeholder="e.g., US, GB, CA"
                helperText="ISO country code"
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Region"
                value={filters.location_region}
                onChange={(e) => handleFilterChange("location_region", e.target.value)}
                size="small"
                placeholder="e.g., California, Ontario"
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="City"
                value={filters.location_city}
                onChange={(e) => handleFilterChange("location_city", e.target.value)}
                size="small"
                placeholder="e.g., New York, London"
              />
            </Grid>
            
            <Divider sx={{ my: 1, width: "100%" }} />
            
            {/* Volume Filters */}
            <Grid item xs={12}>
              <Typography variant="subtitle2" fontWeight={600} mb={1}>
                Search Volume
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Min Volume"
                type="number"
                value={filters.volume_min}
                onChange={(e) => handleFilterChange("volume_min", e.target.value)}
                size="small"
                InputProps={{ inputProps: { min: 0 } }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Max Volume"
                type="number"
                value={filters.volume_max}
                onChange={(e) => handleFilterChange("volume_max", e.target.value)}
                size="small"
                InputProps={{ inputProps: { min: 0 } }}
              />
            </Grid>
            
            <Divider sx={{ my: 1, width: "100%" }} />
            
            {/* Google Ranking Filters */}
            <Grid item xs={12}>
              <Typography variant="subtitle2" fontWeight={600} mb={1}>
                Google Ranking
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Min Google Ranking"
                type="number"
                value={filters.google_ranking_min}
                onChange={(e) => handleFilterChange("google_ranking_min", e.target.value)}
                size="small"
                InputProps={{ inputProps: { min: 1, max: 100 } }}
                helperText="1 = top position"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Max Google Ranking"
                type="number"
                value={filters.google_ranking_max}
                onChange={(e) => handleFilterChange("google_ranking_max", e.target.value)}
                size="small"
                InputProps={{ inputProps: { min: 1, max: 100 } }}
              />
            </Grid>
            
            <Divider sx={{ my: 1, width: "100%" }} />
            
            {/* Bing Ranking Filters */}
            <Grid item xs={12}>
              <Typography variant="subtitle2" fontWeight={600} mb={1}>
                Bing Ranking
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Min Bing Ranking"
                type="number"
                value={filters.bing_ranking_min}
                onChange={(e) => handleFilterChange("bing_ranking_min", e.target.value)}
                size="small"
                InputProps={{ inputProps: { min: 1, max: 100 } }}
                helperText="1 = top position"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Max Bing Ranking"
                type="number"
                value={filters.bing_ranking_max}
                onChange={(e) => handleFilterChange("bing_ranking_max", e.target.value)}
                size="small"
                InputProps={{ inputProps: { min: 1, max: 100 } }}
              />
            </Grid>
            
            <Divider sx={{ my: 1, width: "100%" }} />
            
            {/* Competition Filters */}
            <Grid item xs={12}>
              <Typography variant="subtitle2" fontWeight={600} mb={1}>
                Competition Score (0.0 - 1.0)
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Min Competition"
                type="number"
                value={filters.competition_min}
                onChange={(e) => handleFilterChange("competition_min", e.target.value)}
                size="small"
                InputProps={{ inputProps: { min: 0, max: 1, step: 0.1 } }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Max Competition"
                type="number"
                value={filters.competition_max}
                onChange={(e) => handleFilterChange("competition_max", e.target.value)}
                size="small"
                InputProps={{ inputProps: { min: 0, max: 1, step: 0.1 } }}
              />
            </Grid>
            
            <Divider sx={{ my: 1, width: "100%" }} />
            
            {/* Other Filters */}
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Tags"
                value={filters.tags}
                onChange={(e) => handleFilterChange("tags", e.target.value)}
                size="small"
                placeholder="Comma-separated tags"
                helperText="e.g., tag1, tag2, tag3"
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Language Code"
                value={filters.language}
                onChange={(e) => handleFilterChange("language", e.target.value)}
                size="small"
                placeholder="e.g., en, es, fr"
                helperText="ISO language code"
              />
            </Grid>
            
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={filters.primary_only}
                    onChange={(e) => handleFilterChange("primary_only", e.target.checked)}
                  />
                }
                label="Primary Keywords Only"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions sx={{ p: 2, borderTop: `1px solid ${theme.palette.divider}` }}>
          <Button
            onClick={() => setShowFilterDialog(false)}
            variant="outlined"
            sx={{ textTransform: "none" }}
          >
            Cancel
          </Button>
          <Button
            onClick={handleApplyFilters}
            variant="contained"
            sx={{ textTransform: "none" }}
          >
            Apply Filters
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}


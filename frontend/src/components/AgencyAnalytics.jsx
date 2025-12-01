import { useState, useEffect } from 'react'
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Paper,
  CircularProgress,
  Alert,
  Chip,
  alpha,
  useTheme,
  Autocomplete,
  TextField,
  LinearProgress
} from '@mui/material'
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Analytics as AnalyticsIcon
} from '@mui/icons-material'
import { agencyAnalyticsAPI } from '../services/api'

function AgencyAnalytics() {
  const [campaigns, setCampaigns] = useState([])
  const [selectedCampaign, setSelectedCampaign] = useState(null)
  const [rankings, setRankings] = useState([])
  const [keywordRankings, setKeywordRankings] = useState([])
  const [campaignLinks, setCampaignLinks] = useState([])
  const [loading, setLoading] = useState(false)
  const [loadingKeywords, setLoadingKeywords] = useState(false)
  const [error, setError] = useState(null)
  
  // Campaign search and pagination
  const [campaignSearchTerm, setCampaignSearchTerm] = useState('')
  const [campaignPage, setCampaignPage] = useState(1)
  const [campaignPageSize] = useState(50)
  const [campaignTotalCount, setCampaignTotalCount] = useState(0)
  const [loadingCampaigns, setLoadingCampaigns] = useState(false)
  const [campaignSearchTimeout, setCampaignSearchTimeout] = useState(null)
  
  // Rankings pagination
  const [rankingsPage, setRankingsPage] = useState(0)
  const [rankingsRowsPerPage, setRankingsRowsPerPage] = useState(25)
  const [rankingsTotalCount, setRankingsTotalCount] = useState(0)
  const [isFetchingRankings, setIsFetchingRankings] = useState(false)
  
  // Keyword rankings pagination
  const [keywordRankingsPage, setKeywordRankingsPage] = useState(0)
  const [keywordRankingsRowsPerPage, setKeywordRankingsRowsPerPage] = useState(25)
  const [keywordRankingsTotalCount, setKeywordRankingsTotalCount] = useState(0)
  const [keywordSearchTerm, setKeywordSearchTerm] = useState('')
  const [keywordSearchTimeout, setKeywordSearchTimeout] = useState(null)
  const [isFetchingKeywords, setIsFetchingKeywords] = useState(false)
  
  const theme = useTheme()

  useEffect(() => {
    loadCampaigns(campaignSearchTerm, campaignPage, true)
    loadCampaignLinks()
  }, [])

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (campaignSearchTimeout) {
        clearTimeout(campaignSearchTimeout)
      }
      if (keywordSearchTimeout) {
        clearTimeout(keywordSearchTimeout)
      }
    }
  }, [campaignSearchTimeout, keywordSearchTimeout])

  useEffect(() => {
    if (selectedCampaign) {
      loadRankings(selectedCampaign, rankingsPage + 1, rankingsRowsPerPage)
      loadKeywordRankings(selectedCampaign, keywordRankingsPage + 1, keywordRankingsRowsPerPage, keywordSearchTerm)
    }
  }, [selectedCampaign, rankingsPage, rankingsRowsPerPage, keywordRankingsPage, keywordRankingsRowsPerPage, keywordSearchTerm])

  const loadCampaigns = async (searchTerm = '', page = 1, autoSelectFirst = false) => {
    try {
      setLoadingCampaigns(true)
      setError(null)
      const response = await agencyAnalyticsAPI.getCampaigns(page, campaignPageSize, searchTerm)
      const campaignsList = response.items || []
      setCampaigns(campaignsList)
      setCampaignTotalCount(response.total_count || 0)
      
      if (autoSelectFirst && campaignsList.length > 0 && !selectedCampaign) {
        setSelectedCampaign(campaignsList[0].id)
      }
    } catch (err) {
      console.error('Error loading campaigns:', err)
      setError(err.response?.data?.detail || 'Failed to load campaigns')
      setCampaigns([])
    } finally {
      setLoadingCampaigns(false)
    }
  }

  // Debounced campaign search
  const handleCampaignSearch = (searchValue) => {
    setCampaignSearchTerm(searchValue)
    
    // Clear existing timeout
    if (campaignSearchTimeout) {
      clearTimeout(campaignSearchTimeout)
    }
    
    // Set new timeout for debounced search
    const timeout = setTimeout(() => {
      setCampaignPage(1)
      loadCampaigns(searchValue, 1, false)
    }, 300) // 300ms debounce
    
    setCampaignSearchTimeout(timeout)
  }

  const loadRankings = async (campaignId, page = 1, pageSize = 25) => {
    try {
      setIsFetchingRankings(true)
      setError(null)
      const response = await agencyAnalyticsAPI.getCampaignRankings(campaignId, null, null, page, pageSize)
      setRankings(response.rankings || [])
      setRankingsTotalCount(response.total_count || 0)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load rankings')
    } finally {
      setIsFetchingRankings(false)
    }
  }

  const loadKeywordRankings = async (campaignId, page = 1, pageSize = 25, search = '') => {
    try {
      setIsFetchingKeywords(true)
      const response = await agencyAnalyticsAPI.getCampaignKeywordRankingSummaries(campaignId, page, pageSize, search)
      setKeywordRankings(response.summaries || [])
      setKeywordRankingsTotalCount(response.total_count || 0)
    } catch (err) {
      console.error('Failed to load keyword rankings:', err)
      setKeywordRankings([])
    } finally {
      setIsFetchingKeywords(false)
    }
  }

  // Debounced keyword search
  const handleKeywordSearch = (searchValue) => {
    setKeywordSearchTerm(searchValue)
    
    // Clear existing timeout
    if (keywordSearchTimeout) {
      clearTimeout(keywordSearchTimeout)
    }
    
    // Set new timeout for debounced search
    const timeout = setTimeout(() => {
      setKeywordRankingsPage(0)
      if (selectedCampaign) {
        loadKeywordRankings(selectedCampaign, 1, keywordRankingsRowsPerPage, searchValue)
      }
    }, 300) // 300ms debounce
    
    setKeywordSearchTimeout(timeout)
  }

  const loadCampaignLinks = async () => {
    try {
      const response = await agencyAnalyticsAPI.getCampaignBrandLinks()
      setCampaignLinks(response.links || [])
    } catch (err) {
      console.error('Failed to load campaign links:', err)
    }
  }

  const getLinkedBrandId = (campaignId) => {
    const link = campaignLinks.find(l => l.campaign_id === campaignId)
    return link ? link.brand_id : null
  }

  const formatNumber = (num) => {
    if (num === null || num === undefined) return '0'
    return Number(num).toLocaleString()
  }

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A'
    try {
      const date = new Date(dateStr)
      return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
    } catch {
      return dateStr
    }
  }

  if (loading && campaigns.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="50vh">
        <CircularProgress size={40} thickness={4} />
      </Box>
    )
  }

  if (error && campaigns.length === 0) {
    return (
      <Alert 
        severity="error" 
        sx={{ 
          mb: 3,
          borderRadius: 2,
          fontSize: '13px',
        }}
        onClose={() => setError(null)}
      >
        {error}
      </Alert>
    )
  }

  return (
    <Box>
      <Box mb={4}>
        <Typography 
          variant="h4" 
          fontWeight={700} 
          mb={1}
          sx={{
            fontSize: '1.75rem',
            letterSpacing: '-0.02em',
            color: 'text.primary'
          }}
        >
          Agency Analytics
        </Typography>
        <Typography 
          variant="body1" 
          color="text.secondary"
          sx={{ fontSize: '0.875rem' }}
        >
          Campaign rankings and performance metrics
        </Typography>
      </Box>

      {error && (
        <Alert 
          severity="error" 
          sx={{ 
            mb: 3,
            borderRadius: 2,
            fontSize: '0.875rem',
          }}
          onClose={() => setError(null)}
        >
          {error}
        </Alert>
      )}

      <Card 
        sx={{ 
          mb: 3,
          borderRadius: 2,
          border: `1px solid ${theme.palette.divider}`,
          boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
        }}
      >
        <CardContent sx={{ p: 2.5 }}>
          <Autocomplete
            size="small"
            sx={{ width: '100%' }}
            options={campaigns}
            getOptionLabel={(option) => `${option.company || `Campaign ${option.id}`} - ${option.url || 'N/A'}`}
            value={campaigns.find((c) => c.id === selectedCampaign) || null}
            onChange={(event, newValue) => {
              if (newValue) {
                setSelectedCampaign(newValue.id)
              } else {
                setSelectedCampaign(null)
              }
            }}
            onInputChange={(event, newInputValue) => {
              handleCampaignSearch(newInputValue)
            }}
            loading={loadingCampaigns}
            loadingText="Loading campaigns..."
            noOptionsText={
              campaignSearchTerm
                ? `No campaigns found for "${campaignSearchTerm}"`
                : "Type to search for campaigns..."
            }
            renderInput={(params) => (
              <TextField
                {...params}
                label="Select Campaign"
                placeholder="Search campaigns..."
                InputProps={{
                  ...params.InputProps,
                  endAdornment: (
                    <>
                      {loadingCampaigns ? (
                        <CircularProgress color="inherit" size={20} />
                      ) : null}
                      {params.InputProps.endAdornment}
                    </>
                  ),
                }}
              />
            )}
            filterOptions={(options) => options} // Disable client-side filtering, use server-side search
            ListboxProps={{
              onScroll: (event) => {
                const listboxNode = event.currentTarget
                if (listboxNode.scrollTop + listboxNode.clientHeight >= listboxNode.scrollHeight - 10) {
                  // Load more campaigns if we're near the bottom and there are more to load
                  if (campaigns.length < campaignTotalCount && !loadingCampaigns) {
                    const nextPage = campaignPage + 1
                    setCampaignPage(nextPage)
                    agencyAnalyticsAPI.getCampaigns(nextPage, campaignPageSize, campaignSearchTerm).then((response) => {
                      setCampaigns((prev) => [...prev, ...(response.items || [])])
                    }).catch((err) => {
                      console.error('Error loading more campaigns:', err)
                    })
                  }
                }
              },
            }}
          />
        </CardContent>
      </Card>

      {selectedCampaign && (
        <Card
          sx={{
            borderRadius: 2,
            border: `1px solid ${theme.palette.divider}`,
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
          }}
        >
          <CardContent sx={{ p: 2.5 }}>
            <Typography 
              variant="h6" 
              fontWeight={600} 
              mb={3}
              sx={{ fontSize: '1rem' }}
            >
              Campaign Rankings (Quarterly)
            </Typography>

            {isFetchingRankings && rankings.length === 0 ? (
              <Box display="flex" justifyContent="center" py={4}>
                <CircularProgress size={40} thickness={4} />
              </Box>
            ) : rankings.length === 0 ? (
              <Alert severity="info" sx={{ borderRadius: 2 }}>
                No ranking data available for this campaign. Please sync Agency Analytics data first.
              </Alert>
            ) : (
              <>
                {isFetchingRankings && <LinearProgress sx={{ mb: 1 }} />}
                <TableContainer component={Paper} sx={{ borderRadius: 2 }}>
                  <Table>
                    <TableHead>
                      <TableRow sx={{ bgcolor: alpha(theme.palette.primary.main, 0.04) }}>
                        <TableCell sx={{ fontWeight: 700, fontSize: '13px' }}>Date</TableCell>
                        <TableCell align="right" sx={{ fontWeight: 700, fontSize: '13px' }}>Google Ranking Count</TableCell>
                        <TableCell align="right" sx={{ fontWeight: 700, fontSize: '13px' }}>Google Ranking Change</TableCell>
                        <TableCell align="right" sx={{ fontWeight: 700, fontSize: '13px' }}>Google Local Count</TableCell>
                        <TableCell align="right" sx={{ fontWeight: 700, fontSize: '13px' }}>Google Mobile Count</TableCell>
                        <TableCell align="right" sx={{ fontWeight: 700, fontSize: '13px' }}>Bing Ranking Count</TableCell>
                        <TableCell align="right" sx={{ fontWeight: 700, fontSize: '13px' }}>Ranking Average</TableCell>
                        <TableCell align="right" sx={{ fontWeight: 700, fontSize: '13px' }}>Search Volume</TableCell>
                        <TableCell align="right" sx={{ fontWeight: 700, fontSize: '13px' }}>Competition</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {rankings.map((row, idx) => (
                        <TableRow 
                          key={row.id || idx}
                          sx={{
                            '&:nth-of-type(odd)': {
                              bgcolor: alpha(theme.palette.primary.main, 0.02),
                            },
                            '&:hover': {
                              bgcolor: alpha(theme.palette.primary.main, 0.05),
                            },
                          }}
                        >
                          <TableCell sx={{ fontSize: '13px' }}>{formatDate(row.date)}</TableCell>
                          <TableCell align="right" sx={{ fontSize: '13px' }}>{formatNumber(row.google_ranking_count)}</TableCell>
                          <TableCell align="right" sx={{ fontSize: '13px' }}>
                            <Box display="flex" alignItems="center" justifyContent="flex-end" gap={0.5}>
                              {row.google_ranking_change > 0 ? (
                                <TrendingUpIcon sx={{ fontSize: 16, color: 'success.main' }} />
                              ) : row.google_ranking_change < 0 ? (
                                <TrendingDownIcon sx={{ fontSize: 16, color: 'error.main' }} />
                              ) : null}
                              {formatNumber(row.google_ranking_change)}
                            </Box>
                          </TableCell>
                          <TableCell align="right" sx={{ fontSize: '13px' }}>{formatNumber(row.google_local_count)}</TableCell>
                          <TableCell align="right" sx={{ fontSize: '13px' }}>{formatNumber(row.google_mobile_count)}</TableCell>
                          <TableCell align="right" sx={{ fontSize: '13px' }}>{formatNumber(row.bing_ranking_count)}</TableCell>
                          <TableCell align="right" sx={{ fontSize: '13px' }}>{formatNumber(row.ranking_average)}</TableCell>
                          <TableCell align="right" sx={{ fontSize: '13px' }}>{formatNumber(row.search_volume)}</TableCell>
                          <TableCell align="right" sx={{ fontSize: '13px' }}>{formatNumber(row.competition)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
                {rankingsTotalCount > rankingsRowsPerPage && (
                  <TablePagination
                    component="div"
                    count={rankingsTotalCount}
                    page={rankingsPage}
                    onPageChange={(event, newPage) => {
                      setRankingsPage(newPage)
                    }}
                    rowsPerPage={rankingsRowsPerPage}
                    onRowsPerPageChange={(event) => {
                      setRankingsRowsPerPage(parseInt(event.target.value, 10))
                      setRankingsPage(0)
                    }}
                    rowsPerPageOptions={[10, 25, 50, 100]}
                    disabled={isFetchingRankings}
                  />
                )}
              </>
            )}
          </CardContent>
        </Card>
      )}

      {selectedCampaign && (
        <Card 
          sx={{ 
            mt: 3,
            borderRadius: 2,
            border: `1px solid ${theme.palette.divider}`,
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
          }}
        >
          <CardContent sx={{ p: 2.5 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
              <Typography 
                variant="h6" 
                fontWeight={600} 
                sx={{ fontSize: '1rem' }}
              >
                Keyword Rankings
              </Typography>
              <TextField
                size="small"
                placeholder="Search keywords..."
                value={keywordSearchTerm}
                onChange={(e) => handleKeywordSearch(e.target.value)}
                sx={{ minWidth: 250 }}
                InputProps={{
                  endAdornment: isFetchingKeywords ? (
                    <CircularProgress size={20} />
                  ) : null,
                }}
              />
            </Box>

            {isFetchingKeywords && keywordRankings.length === 0 ? (
              <Box display="flex" justifyContent="center" py={4}>
                <CircularProgress size={40} thickness={4} />
              </Box>
            ) : keywordRankings.length === 0 ? (
              <Alert severity="info" sx={{ borderRadius: 2, fontSize: '0.875rem' }}>
                No keyword ranking data available for this campaign. Please sync Agency Analytics data first.
              </Alert>
            ) : (
              <>
                {isFetchingKeywords && <LinearProgress sx={{ mb: 1 }} />}
                <TableContainer 
                  component={Card}
                  sx={{ 
                    borderRadius: 2,
                    border: `1px solid ${theme.palette.divider}`,
                    boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                  }}
                >
                  <Table>
                    <TableHead>
                      <TableRow sx={{ bgcolor: alpha(theme.palette.primary.main, 0.04) }}>
                        <TableCell sx={{ fontWeight: 700, fontSize: '13px' }}>Keyword</TableCell>
                        <TableCell align="right" sx={{ fontWeight: 700, fontSize: '13px' }}>Google Ranking</TableCell>
                        <TableCell align="right" sx={{ fontWeight: 700, fontSize: '13px' }}>Google Mobile</TableCell>
                        <TableCell align="right" sx={{ fontWeight: 700, fontSize: '13px' }}>Google Local</TableCell>
                        <TableCell align="right" sx={{ fontWeight: 700, fontSize: '13px' }}>Bing Ranking</TableCell>
                        <TableCell align="right" sx={{ fontWeight: 700, fontSize: '13px' }}>Search Volume</TableCell>
                        <TableCell align="right" sx={{ fontWeight: 700, fontSize: '13px' }}>Competition</TableCell>
                        <TableCell align="right" sx={{ fontWeight: 700, fontSize: '13px' }}>Ranking Change</TableCell>
                        <TableCell sx={{ fontWeight: 700, fontSize: '13px' }}>Latest Date</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {keywordRankings.map((row, idx) => (
                        <TableRow 
                          key={row.keyword_id || idx}
                          sx={{
                            '&:nth-of-type(odd)': {
                              bgcolor: alpha(theme.palette.primary.main, 0.02),
                            },
                            '&:hover': {
                              bgcolor: alpha(theme.palette.primary.main, 0.05),
                            },
                          }}
                        >
                          <TableCell sx={{ fontSize: '13px', fontWeight: 500 }}>
                            {row.keyword_phrase || `Keyword ${row.keyword_id}`}
                          </TableCell>
                          <TableCell align="right" sx={{ fontSize: '13px' }}>
                            {row.google_ranking !== null && row.google_ranking !== undefined 
                              ? row.google_ranking 
                              : 'N/A'}
                          </TableCell>
                          <TableCell align="right" sx={{ fontSize: '13px' }}>
                            {row.google_mobile_ranking !== null && row.google_mobile_ranking !== undefined 
                              ? row.google_mobile_ranking 
                              : 'N/A'}
                          </TableCell>
                          <TableCell align="right" sx={{ fontSize: '13px' }}>
                            {row.google_local_ranking !== null && row.google_local_ranking !== undefined 
                              ? row.google_local_ranking 
                              : 'N/A'}
                          </TableCell>
                          <TableCell align="right" sx={{ fontSize: '13px' }}>
                            {row.bing_ranking !== null && row.bing_ranking !== undefined 
                              ? row.bing_ranking 
                              : 'N/A'}
                          </TableCell>
                          <TableCell align="right" sx={{ fontSize: '13px' }}>
                            {formatNumber(row.search_volume)}
                          </TableCell>
                          <TableCell align="right" sx={{ fontSize: '13px' }}>
                            {row.competition !== null && row.competition !== undefined 
                              ? Number(row.competition).toFixed(2)
                              : 'N/A'}
                          </TableCell>
                          <TableCell align="right" sx={{ fontSize: '13px' }}>
                            {row.ranking_change !== null && row.ranking_change !== undefined ? (
                              <Box display="flex" alignItems="center" justifyContent="flex-end" gap={0.5}>
                                {row.ranking_change > 0 ? (
                                  <TrendingUpIcon sx={{ fontSize: 16, color: 'success.main' }} />
                                ) : row.ranking_change < 0 ? (
                                  <TrendingDownIcon sx={{ fontSize: 16, color: 'error.main' }} />
                                ) : null}
                                {row.ranking_change > 0 ? '+' : ''}{formatNumber(row.ranking_change)}
                              </Box>
                            ) : 'N/A'}
                          </TableCell>
                          <TableCell sx={{ fontSize: '13px' }}>
                            {formatDate(row.date)}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
                {keywordRankingsTotalCount > keywordRankingsRowsPerPage && (
                  <TablePagination
                    component="div"
                    count={keywordRankingsTotalCount}
                    page={keywordRankingsPage}
                    onPageChange={(event, newPage) => {
                      setKeywordRankingsPage(newPage)
                    }}
                    rowsPerPage={keywordRankingsRowsPerPage}
                    onRowsPerPageChange={(event) => {
                      setKeywordRankingsRowsPerPage(parseInt(event.target.value, 10))
                      setKeywordRankingsPage(0)
                    }}
                    rowsPerPageOptions={[10, 25, 50, 100]}
                    disabled={isFetchingKeywords}
                  />
                )}
              </>
            )}
          </CardContent>
        </Card>
      )}
    </Box>
  )
}

export default AgencyAnalytics


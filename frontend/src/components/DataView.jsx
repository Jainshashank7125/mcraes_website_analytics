import { useState, useEffect } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Grid,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Tabs,
  Tab,
  Chip,
  alpha,
  useTheme,
  Pagination,
  Select,
  MenuItem,
  FormControl,
  InputLabel
} from '@mui/material'
import {
  Business as BusinessIcon,
  Article as ArticleIcon,
  ChatBubble as ChatBubbleIcon
} from '@mui/icons-material'
import { motion } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { dataAPI } from '../services/api'
import { queryKeys } from '../hooks/queryKeys'
import { usePrompts, useResponses } from '../hooks/useData'
import { useToast } from '../contexts/ToastContext'

function DataView() {
  const [dataType, setDataType] = useState('brands')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(50)
  const [filters, setFilters] = useState({
    stage: '',
    persona_id: '',
    platform: '',
    prompt_id: '',
    start_date: '',
    end_date: '',
  })
  const theme = useTheme()

  // Reset to first page when data type changes
  useEffect(() => {
    setPage(1)
  }, [dataType])

  // Use React Query hooks for data fetching
  const { data: brandsData = {}, isLoading: brandsLoading } = useQuery({
    queryKey: queryKeys.brands.list({ page, pageSize }),
    queryFn: async () => {
      const offset = (page - 1) * pageSize
      const response = await dataAPI.getBrands(pageSize, offset)
      return response
    },
    enabled: dataType === 'brands',
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  })

  const { data: promptsData, isLoading: promptsLoading } = usePrompts(
    {
      ...filters,
      page,
      pageSize,
    },
    {
      enabled: dataType === 'prompts',
    }
  )

  const { data: responsesData, isLoading: responsesLoading } = useResponses(
    {
      ...filters,
      page,
      pageSize,
    },
    {
      enabled: dataType === 'responses',
    }
  )

  // Determine which data to use based on dataType
  const getCurrentData = () => {
    switch (dataType) {
      case 'brands':
        return {
          data: brandsData.items || [],
          loading: brandsLoading,
          totalCount: brandsData.total_count || 0,
        }
      case 'prompts':
        return {
          data: promptsData?.items || [],
          loading: promptsLoading,
          totalCount: promptsData?.totalCount || 0,
        }
      case 'responses':
        return {
          data: responsesData?.items || [],
          loading: responsesLoading,
          totalCount: responsesData?.totalCount || 0,
        }
      default:
        return { data: [], loading: false, totalCount: 0 }
    }
  }

  const { data, loading, totalCount } = getCurrentData()

  const handlePageChange = (event, value) => {
    setPage(value)
  }

  const handlePageSizeChange = (event) => {
    setPageSize(event.target.value)
    setPage(1) // Reset to first page when page size changes
  }

  const totalPages = Math.ceil(totalCount / pageSize) || 1

  const renderTable = () => {
    if (data.length === 0) {
      return (
        <Card
          sx={{
            borderRadius: 2,
            border: `1px solid ${theme.palette.divider}`,
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
          }}
        >
          <CardContent sx={{ p: 4, textAlign: 'center' }}>
            <Typography 
              variant="h6" 
              color="text.secondary" 
              py={3}
              sx={{ fontSize: '1rem' }}
            >
              No data available. Sync data first to view it here.
            </Typography>
          </CardContent>
        </Card>
      )
    }

    if (dataType === 'brands') {
      return (
        <TableContainer 
          component={Card}
          sx={{
            borderRadius: 2,
            border: `1px solid ${theme.palette.divider}`,
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
            overflow: 'hidden',
          }}
        >
          <Table>
            <TableHead>
              <TableRow sx={{ bgcolor: alpha(theme.palette.primary.main, 0.04) }}>
                <TableCell sx={{ fontWeight: 700, fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', py: 1.5 }}>ID</TableCell>
                <TableCell sx={{ fontWeight: 700, fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', py: 1.5 }}>Name</TableCell>
                <TableCell sx={{ fontWeight: 700, fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', py: 1.5 }}>Website</TableCell>
                <TableCell sx={{ fontWeight: 700, fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', py: 1.5 }}>Created At</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data.map((item) => (
                <TableRow 
                  key={item.id} 
                  hover
                  sx={{
                    transition: 'all 0.2s',
                    '&:hover': {
                      bgcolor: alpha(theme.palette.primary.main, 0.02),
                    },
                  }}
                >
                  <TableCell sx={{ fontSize: '13px', fontWeight: 500, py: 1.5 }}>{item.id}</TableCell>
                  <TableCell sx={{ py: 1.5 }}>
                    <Box display="flex" alignItems="center">
                      <BusinessIcon sx={{ mr: 1, color: 'primary.main', fontSize: 18 }} />
                      <Typography variant="body2" sx={{ fontSize: '13px', fontWeight: 500 }}>
                        {item.name}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell sx={{ fontSize: '13px', py: 1.5 }}>{item.website || 'N/A'}</TableCell>
                  <TableCell sx={{ fontSize: '13px', py: 1.5 }}>
                    {item.created_at ? new Date(item.created_at).toLocaleDateString() : 'N/A'}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )
    }

    if (dataType === 'prompts') {
      return (
        <TableContainer 
          component={Card}
          sx={{
            borderRadius: 2,
            border: `1px solid ${theme.palette.divider}`,
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
            overflow: 'hidden',
          }}
        >
          <Table>
            <TableHead>
              <TableRow sx={{ bgcolor: alpha(theme.palette.primary.main, 0.04) }}>
                <TableCell sx={{ fontWeight: 700, fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', py: 1.5 }}>ID</TableCell>
                <TableCell sx={{ fontWeight: 700, fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', py: 1.5 }}>Text</TableCell>
                <TableCell sx={{ fontWeight: 700, fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', py: 1.5 }}>Stage</TableCell>
                <TableCell sx={{ fontWeight: 700, fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', py: 1.5 }}>Platforms</TableCell>
                <TableCell sx={{ fontWeight: 700, fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', py: 1.5 }}>Created At</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data.map((item) => (
                <TableRow 
                  key={item.id} 
                  hover
                  sx={{
                    transition: 'all 0.2s',
                    '&:hover': {
                      bgcolor: alpha(theme.palette.primary.main, 0.02),
                    },
                  }}
                >
                  <TableCell sx={{ fontSize: '13px', fontWeight: 500, py: 1.5 }}>{item.id}</TableCell>
                  <TableCell sx={{ maxWidth: 400, fontSize: '13px', py: 1.5 }}>
                    <Typography 
                      variant="body2" 
                      sx={{ 
                        fontSize: '13px',
                        lineHeight: 1.5,
                        display: '-webkit-box',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical',
                        overflow: 'hidden',
                      }}
                      title={item.text || item.prompt_text || 'N/A'}
                    >
                      {item.text || item.prompt_text || 'N/A'}
                    </Typography>
                  </TableCell>
                  <TableCell sx={{ py: 1.5 }}>
                    <Chip 
                      label={item.stage || 'N/A'} 
                      size="small" 
                      sx={{
                        bgcolor: alpha(theme.palette.primary.main, 0.08),
                        color: 'primary.main',
                        fontWeight: 600,
                        fontSize: '11px',
                        height: 22,
                      }}
                    />
                  </TableCell>
                  <TableCell sx={{ py: 1.5 }}>
                    <Box display="flex" flexWrap="wrap" gap={0.5}>
                      {item.platforms?.slice(0, 2).map((p) => (
                        <Chip 
                          key={p} 
                          label={p} 
                          size="small" 
                          sx={{
                            fontSize: '10px',
                            height: 20,
                            fontWeight: 500,
                          }}
                        />
                      ))}
                    </Box>
                  </TableCell>
                  <TableCell sx={{ fontSize: '13px', py: 1.5 }}>
                    {item.created_at ? new Date(item.created_at).toLocaleDateString() : 'N/A'}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )
    }

    if (dataType === 'responses') {
      return (
        <TableContainer 
          component={Card}
          sx={{
            borderRadius: 2,
            border: `1px solid ${theme.palette.divider}`,
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
            overflow: 'hidden',
          }}
        >
          <Table>
            <TableHead>
              <TableRow sx={{ bgcolor: alpha(theme.palette.primary.main, 0.04) }}>
                <TableCell sx={{ fontWeight: 700, fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', py: 1.5 }}>Platform</TableCell>
                <TableCell sx={{ fontWeight: 700, fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', py: 1.5 }}>Stage</TableCell>
                <TableCell sx={{ fontWeight: 700, fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', py: 1.5 }}>Brand Sentiment</TableCell>
                <TableCell sx={{ fontWeight: 700, fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', py: 1.5 }}>Competitors</TableCell>
                <TableCell sx={{ fontWeight: 700, fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', py: 1.5 }}>Citations</TableCell>
                <TableCell sx={{ fontWeight: 700, fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', py: 1.5 }}>Created At</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data.map((item) => (
                <TableRow 
                  key={item.id} 
                  hover
                  sx={{
                    transition: 'all 0.2s',
                    '&:hover': {
                      bgcolor: alpha(theme.palette.primary.main, 0.02),
                    },
                  }}
                >
                  <TableCell sx={{ py: 1.5 }}>
                    <Chip 
                      label={item.platform || 'N/A'} 
                      size="small"
                      sx={{
                        bgcolor: alpha(theme.palette.primary.main, 0.08),
                        color: 'primary.main',
                        fontWeight: 600,
                        fontSize: '11px',
                        height: 22,
                      }}
                    />
                  </TableCell>
                  <TableCell sx={{ py: 1.5 }}>
                    <Chip 
                      label={item.stage || 'N/A'} 
                      size="small" 
                      sx={{
                        bgcolor: alpha(theme.palette.secondary.main, 0.08),
                        color: 'secondary.main',
                        fontWeight: 600,
                        fontSize: '11px',
                        height: 22,
                      }}
                    />
                  </TableCell>
                  <TableCell sx={{ py: 1.5 }}>
                    {item.brand_sentiment ? (
                      <Chip
                        label={item.brand_sentiment}
                        size="small"
                        sx={{
                          bgcolor: item.brand_sentiment.toLowerCase().includes('positive') 
                            ? alpha(theme.palette.success.main, 0.1)
                            : alpha(theme.palette.error.main, 0.1),
                          color: item.brand_sentiment.toLowerCase().includes('positive')
                            ? 'success.main'
                            : 'error.main',
                          fontWeight: 600,
                          fontSize: '11px',
                          height: 22,
                        }}
                      />
                    ) : (
                      <Typography 
                        variant="caption" 
                        color="text.secondary"
                        sx={{ fontSize: '12px' }}
                      >
                        N/A
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell sx={{ py: 1.5 }}>
                    {item.competitors_present?.length > 0 ? (
                      <Box display="flex" flexWrap="wrap" gap={0.5}>
                        {item.competitors_present.slice(0, 2).map((comp) => (
                          <Chip 
                            key={comp} 
                            label={comp} 
                            size="small"
                            sx={{
                              fontSize: '10px',
                              height: 20,
                              fontWeight: 500,
                            }}
                          />
                        ))}
                      </Box>
                    ) : (
                      <Typography 
                        variant="caption" 
                        color="text.secondary"
                        sx={{ fontSize: '12px' }}
                      >
                        None
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell sx={{ py: 1.5 }}>
                    <Chip
                      label={item.citations?.length || 0}
                      size="small"
                      sx={{
                        bgcolor: alpha(theme.palette.info.main, 0.08),
                        color: 'info.main',
                        fontWeight: 600,
                        fontSize: '11px',
                        height: 22,
                      }}
                    />
                  </TableCell>
                  <TableCell sx={{ fontSize: '13px', py: 1.5 }}>
                    {item.created_at ? new Date(item.created_at).toLocaleDateString() : 'N/A'}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )
    }
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
          View Data
        </Typography>
        <Typography 
          variant="body1" 
          color="text.secondary"
          sx={{ fontSize: '0.875rem' }}
        >
          Browse synced data from Scrunch AI
        </Typography>
      </Box>

      <Card
        sx={{ 
          mb: 3,
          borderRadius: 2,
          border: `1px solid ${theme.palette.divider}`,
          boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
          overflow: 'hidden',
        }}
      >
        <Tabs
          value={dataType}
          onChange={(e, newValue) => setDataType(newValue)}
          sx={{
            borderBottom: `1px solid ${theme.palette.divider}`,
            '& .MuiTab-root': {
              minHeight: 40,
              fontSize: '0.875rem',
              fontWeight: 500,
              textTransform: 'none',
              borderRadius: 1.5,
              mx: 0.5,
              '&.Mui-selected': {
                color: 'primary.main',
                bgcolor: alpha(theme.palette.primary.main, 0.08),
              },
            },
            '& .MuiTabs-indicator': {
              display: 'none',
            },
          }}
        >
          <Tab 
            icon={<BusinessIcon sx={{ fontSize: 18 }} />} 
            iconPosition="start" 
            label="Brands" 
            value="brands"
            sx={{ px: 3 }}
          />
          <Tab 
            icon={<ArticleIcon sx={{ fontSize: 18 }} />} 
            iconPosition="start" 
            label="Prompts" 
            value="prompts"
            sx={{ px: 3 }}
          />
          <Tab 
            icon={<ChatBubbleIcon sx={{ fontSize: 18 }} />} 
            iconPosition="start" 
            label="Responses" 
            value="responses"
            sx={{ px: 3 }}
          />
        </Tabs>
      </Card>

      {(dataType === 'prompts' || dataType === 'responses') && (
        <Card 
          sx={{ 
            mb: 3,
            borderRadius: 2,
            border: `1px solid ${theme.palette.divider}`,
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
          }}
        >
          <CardContent sx={{ p: 2.5 }}>
            <Typography 
              variant="h6" 
              mb={2} 
              fontWeight={600}
              sx={{ fontSize: '1rem', letterSpacing: '-0.01em' }}
            >
              Filters
            </Typography>
            <Grid container spacing={2}>
              {dataType === 'prompts' && (
                <>
                  <Grid item xs={12} sm={6} md={3}>
                    <TextField
                      fullWidth
                      label="Stage"
                      size="small"
                      value={filters.stage}
                      onChange={(e) => setFilters({ ...filters, stage: e.target.value })}
                      sx={{ fontSize: '13px' }}
                    />
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <TextField
                      fullWidth
                      label="Persona ID"
                      type="number"
                      size="small"
                      value={filters.persona_id}
                      onChange={(e) => setFilters({ ...filters, persona_id: e.target.value })}
                    />
                  </Grid>
                </>
              )}
              {dataType === 'responses' && (
                <>
                  <Grid item xs={12} sm={6} md={3}>
                    <TextField
                      fullWidth
                      label="Platform"
                      size="small"
                      value={filters.platform}
                      onChange={(e) => setFilters({ ...filters, platform: e.target.value })}
                    />
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <TextField
                      fullWidth
                      label="Prompt ID"
                      type="number"
                      size="small"
                      value={filters.prompt_id}
                      onChange={(e) => setFilters({ ...filters, prompt_id: e.target.value })}
                    />
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <TextField
                      fullWidth
                      label="Start Date"
                      type="date"
                      size="small"
                      value={filters.start_date}
                      onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
                      InputLabelProps={{ shrink: true }}
                    />
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <TextField
                      fullWidth
                      label="End Date"
                      type="date"
                      size="small"
                      value={filters.end_date}
                      onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
                      InputLabelProps={{ shrink: true }}
                    />
                  </Grid>
                </>
              )}
              <Grid item xs={12} sm={6} md={3}>
                <FormControl fullWidth size="small">
                  <InputLabel>Items per page</InputLabel>
                  <Select
                    value={pageSize}
                    label="Items per page"
                    onChange={handlePageSizeChange}
                  >
                    <MenuItem value={25}>25</MenuItem>
                    <MenuItem value={50}>50</MenuItem>
                    <MenuItem value={100}>100</MenuItem>
                    <MenuItem value={200}>200</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Button 
                  variant="contained" 
                  fullWidth 
                  size="small"
                  onClick={() => {
                    setPage(1)
                  }}
                  sx={{
                    mt: 0.25,
                    borderRadius: 2,
                    px: 2,
                    py: 1,
                    fontSize: '13px',
                    fontWeight: 600,
                  }}
                >
                  Apply Filters
                </Button>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {loading ? (
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="40vh">
          <CircularProgress size={40} thickness={4} />
        </Box>
      ) : (
        <>
          {renderTable()}
          
          {/* Pagination */}
          {data.length > 0 && (
            <Box 
              mt={3} 
              display="flex" 
              justifyContent="space-between" 
              alignItems="center"
              flexWrap="wrap"
              gap={2}
            >
              <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.875rem' }}>
                Showing {((page - 1) * pageSize) + 1} to {Math.min(page * pageSize, totalCount)} of {totalCount} results
              </Typography>
              <Pagination
                count={totalPages}
                page={page}
                onChange={handlePageChange}
                color="primary"
                size="medium"
                showFirstButton
                showLastButton
                sx={{
                  '& .MuiPaginationItem-root': {
                    fontSize: '0.875rem',
                  },
                }}
              />
            </Box>
          )}
        </>
      )}
    </Box>
  )
}

export default DataView

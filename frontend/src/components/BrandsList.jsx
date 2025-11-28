import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  Avatar,
  Chip,
  CircularProgress,
  Button,
  alpha,
  useTheme,
  Skeleton,
  IconButton,
  Tooltip,
  TablePagination
} from '@mui/material'
import {
  Business as BusinessIcon,
  Language as LanguageIcon,
  ArrowForward as ArrowForwardIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material'
import { motion } from 'framer-motion'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { queryKeys } from '../hooks/queryKeys'
import { dataAPI } from '../services/api'

function BrandsList() {
  const [page, setPage] = useState(0)
  const [pageSize, setPageSize] = useState(25)
  const navigate = useNavigate()
  const theme = useTheme()
  const queryClient = useQueryClient()
  
  // Use React Query hook for brands with pagination
  const { data: brandsData = {}, isLoading: loading, error } = useQuery({
    queryKey: queryKeys.brands.list({ page, pageSize }),
    queryFn: async () => {
      const offset = page * pageSize
      const response = await dataAPI.getBrands(pageSize, offset)
      return response
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  })
  
  // Log error if any
  if (error) {
    console.error('Error loading brands:', error)
  }

  const brands = brandsData.items || []
  const totalCount = brandsData.total_count || 0

  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.brands.all })
  }

  const handleChangePage = (event, newPage) => {
    setPage(newPage)
  }

  const handleChangePageSize = (event) => {
    setPageSize(parseInt(event.target.value, 10))
    setPage(0)
  }


  if (loading) {
    return (
      <Box>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Skeleton variant="rectangular" width={150} height={32} sx={{ borderRadius: 1.5 }} />
          <Skeleton variant="rectangular" width={100} height={32} sx={{ borderRadius: 1.5 }} />
        </Box>
        <Grid container spacing={2.5}>
          {[1, 2, 3].map((i) => (
            <Grid item xs={12} sm={6} md={4} key={i}>
              <Skeleton variant="rectangular" height={200} sx={{ borderRadius: 2 }} />
            </Grid>
          ))}
        </Grid>
      </Box>
    )
  }

  if (!loading && brands.length === 0) {
    return (
      <Card
        sx={{
          borderRadius: 2,
          border: `1px solid ${theme.palette.divider}`,
          boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
        }}
      >
        <CardContent sx={{ p: 4, textAlign: 'center' }}>
          <BusinessIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2, opacity: 0.4 }} />
          <Typography variant="h6" fontWeight={600} mb={1} sx={{ fontSize: '1.125rem' }}>
            No brands available
          </Typography>
          <Typography variant="body2" color="text.secondary" mb={3} sx={{ fontSize: '0.875rem' }}>
            Sync data first to view brands
          </Typography>
          <Button 
            variant="contained" 
            size="small"
            onClick={handleRefresh}
            sx={{
              px: 2,
              py: 0.75,
              borderRadius: 1.5,
              fontSize: '0.875rem',
              fontWeight: 600,
              boxShadow: 'none',
              '&:hover': {
                boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
              },
            }}
          >
            Refresh
          </Button>
        </CardContent>
      </Card>
    )
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Box>
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
            Brands
          </Typography>
          <Typography 
            variant="body1" 
            color="text.secondary"
            sx={{ fontSize: '0.875rem' }}
          >
            {totalCount} {totalCount === 1 ? 'brand' : 'brands'} available
          </Typography>
        </Box>
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
            fontSize: '0.875rem',
            bgcolor: 'background.paper',
            borderColor: theme.palette.divider,
            '&:hover': {
              borderColor: theme.palette.divider,
              bgcolor: alpha(theme.palette.primary.main, 0.05),
            },
          }}
        >
          Refresh
        </Button>
      </Box>

      <Grid container spacing={2.5}>
        {brands.map((brand, index) => {
          return (
            <Grid item xs={12} sm={6} md={4} key={brand.id}>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
              >
                <Card
                  sx={{
                    height: '100%',
                    background: '#FFFFFF',
                    border: `1px solid ${theme.palette.divider}`,
                    borderRadius: 2,
                    boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                    transition: 'all 0.2s ease-in-out',
                    position: 'relative',
                    overflow: 'hidden',
                    '&:before': {
                      content: '""',
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      width: '4px',
                      height: '100%',
                      backgroundColor: theme.palette.primary.main,
                      opacity: 0,
                      transition: 'opacity 0.2s',
                    },
                    '&:hover': {
                      boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                      transform: 'translateY(-2px)',
                      borderColor: alpha(theme.palette.primary.main, 0.3),
                      '&:before': {
                        opacity: 1,
                      },
                      '& .brand-arrow': {
                        transform: 'translateX(2px)',
                        opacity: 1,
                      },
                    },
                  }}
                >
                    <CardContent sx={{ p: 2.5 }}>
                      <Box display="flex" alignItems="center" mb={2}>
                        {brand.logo_url ? (
                          <Box
                            component="img"
                            src={brand.logo_url}
                            alt={`${brand.name} logo`}
                            sx={{
                              width: 40,
                              height: 40,
                              mr: 1.5,
                              borderRadius: 1,
                              objectFit: 'contain',
                              bgcolor: 'transparent',
                              border: `1px solid ${theme.palette.divider}`,
                              p: 0.5,
                            }}
                          />
                        ) : (
                          <Avatar
                            sx={{
                              bgcolor: alpha(theme.palette.primary.main, 0.1),
                              color: theme.palette.primary.main,
                              width: 40,
                              height: 40,
                              mr: 1.5,
                              fontSize: '18px',
                              fontWeight: 600,
                            }}
                          >
                            {brand.name?.charAt(0) || <BusinessIcon />}
                          </Avatar>
                        )}
                        <Box flex={1}>
                          <Typography 
                            variant="h6" 
                            fontWeight={600}
                            sx={{ 
                              fontSize: '1rem',
                              letterSpacing: '-0.01em',
                              mb: 0.25,
                              lineHeight: 1.3,
                              color: 'text.primary',
                            }}
                          >
                            {brand.name}
                          </Typography>
                          {brand.website && (
                            <Box display="flex" alignItems="center">
                              <LanguageIcon 
                                sx={{ 
                                  fontSize: 12, 
                                  mr: 0.5, 
                                  color: 'text.secondary',
                                  opacity: 0.6
                                }} 
                              />
                              <Typography 
                                variant="caption" 
                                color="text.secondary"
                                sx={{ 
                                  fontSize: '0.75rem',
                                  fontWeight: 500,
                                }}
                              >
                                {brand.website.replace(/^https?:\/\//, '').replace(/\/$/, '')}
                              </Typography>
                            </Box>
                          )}
                        </Box>
                        <IconButton
                          className="brand-arrow"
                          size="small"
                          onClick={(e) => {
                            e.stopPropagation()
                            navigate(`/brands/${brand.id}`)
                          }}
                          sx={{
                            color: 'text.secondary',
                            transition: 'all 0.2s',
                            opacity: 0.6,
                            '&:hover': {
                              opacity: 1,
                              bgcolor: alpha(theme.palette.primary.main, 0.1),
                              color: theme.palette.primary.main,
                            },
                          }}
                        >
                          <ArrowForwardIcon sx={{ fontSize: 16 }} />
                        </IconButton>
                      </Box>
                    </CardContent>
                  </Card>
                </motion.div>
              </Grid>
            )
          })}
        </Grid>

        {brands.length > 0 && (
          <Box width="100%" mt={3}>
            <TablePagination
              component="div"
              count={totalCount}
              page={page}
              onPageChange={handleChangePage}
              rowsPerPage={pageSize}
              onRowsPerPageChange={handleChangePageSize}
              rowsPerPageOptions={[10, 25, 50, 100]}
            />
          </Box>
        )}
    </Box>
  )
}

export default BrandsList

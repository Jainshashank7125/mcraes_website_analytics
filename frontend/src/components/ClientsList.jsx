import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Typography,
  CircularProgress,
  Button,
  alpha,
  useTheme,
  Skeleton,
  IconButton,
  Tooltip,
  TextField,
  InputAdornment,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Avatar,
  TablePagination,
  Alert,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
} from '@mui/material'
import {
  Business as BusinessIcon,
  Language as LanguageIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  Campaign as CampaignIcon,
  Analytics as AnalyticsIcon,
  Link as LinkIcon,
  Search as SearchIcon,
  OpenInNew as OpenInNewIcon,
  Tag as TagIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material'
import { useQuery, useQueryClient, keepPreviousData } from '@tanstack/react-query'
import { clientAPI } from '../services/api'
import { debugError } from '../utils/debug'
import { queryKeys } from '../hooks/queryKeys'
import ClientManagement from './ClientManagement'

function ClientsList() {
  const [managementOpen, setManagementOpen] = useState(false)
  const [selectedClient, setSelectedClient] = useState(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [clientToDelete, setClientToDelete] = useState(null)
  const [deleting, setDeleting] = useState(false)
  const [page, setPage] = useState(0)
  const [pageSize, setPageSize] = useState(25)
  const [searchTerm, setSearchTerm] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [persistedTotalCount, setPersistedTotalCount] = useState(0)
  const [filters, setFilters] = useState({
    ga4: null, // null = all, true = has GA4, false = no GA4
    scrunch: null, // null = all, true = has Scrunch, false = no Scrunch
    active: true, // Default to true (active clients only), null = all, true = active, false = inactive
  })
  const navigate = useNavigate()
  const theme = useTheme()
  const queryClient = useQueryClient()
  
  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchTerm)
      setPage(0) // Reset to first page on search
    }, 300)
    return () => clearTimeout(timer)
  }, [searchTerm])
  
  // Reset page when filters change
  useEffect(() => {
    setPage(0)
  }, [filters.ga4, filters.scrunch, filters.active])
  
  // Use React Query hook for clients with pagination and filters
  const { data: clientsData = {}, isLoading: loading, isFetching, error } = useQuery({
    queryKey: queryKeys.clients.list({ 
      page: page + 1, 
      pageSize, 
      search: debouncedSearch,
      filters 
    }),
    queryFn: async () => {
      const response = await clientAPI.getClients(page + 1, pageSize, debouncedSearch, filters)
      return response
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    placeholderData: keepPreviousData, // Keep previous data while fetching new data (React Query v5)
  })

  // Persist total count - only update when we have new data
  useEffect(() => {
    if (clientsData.total_count !== undefined && clientsData.total_count !== null) {
      setPersistedTotalCount(clientsData.total_count)
    }
  }, [clientsData.total_count])

  // Clients are already filtered by the API, no need for client-side filtering
  const clients = clientsData.items || []
  
  // Helper function to get client stats (for display purposes)
  const getClientStats = (client) => {
    const campaigns = client.client_campaigns || []
    const hasGA4 = !!client.ga4_property_id
    const hasScrunch = !!client.scrunch_brand_id
    
    return {
      campaignCount: campaigns.length,
      hasGA4,
      hasScrunch,
      hasMappings: hasGA4 || hasScrunch
    }
  }
  
  // Use persisted count if current data doesn't have it (during loading)
  const totalCount = clientsData.total_count !== undefined && clientsData.total_count !== null 
    ? clientsData.total_count 
    : persistedTotalCount
  const totalPages = clientsData.total_pages || 0

  const handleManageClick = (e, client) => {
    e.stopPropagation()
    setSelectedClient(client)
    setManagementOpen(true)
  }

  const handleManagementClose = () => {
    setManagementOpen(false)
    setSelectedClient(null)
    queryClient.invalidateQueries({ queryKey: queryKeys.clients.all })
  }

  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.clients.all })
  }

  const handleChangePage = (event, newPage) => {
    setPage(newPage)
  }

  const handleChangePageSize = (event) => {
    setPageSize(parseInt(event.target.value, 10))
    setPage(0)
  }

  const handleSearchChange = (event) => {
    setSearchTerm(event.target.value)
  }

  const handleFilterChange = (filterType, value) => {
    setFilters((prev) => {
      const currentValue = prev[filterType]
      // If clicking the same value, deselect it (set to null)
      // Otherwise, set to the new value
      const newValue = currentValue === value ? null : value
      return {
        ...prev,
        [filterType]: newValue,
      }
    })
    setPage(0) // Reset to first page when filter changes
  }

  const handleDeleteClick = (e, client) => {
    e.stopPropagation()
    setClientToDelete(client)
    setDeleteDialogOpen(true)
  }

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false)
    setClientToDelete(null)
  }

  const handleDeleteConfirm = async () => {
    if (!clientToDelete) return
    
    setDeleting(true)
    try {
      await clientAPI.softDeleteClient(clientToDelete.id)
      queryClient.invalidateQueries({ queryKey: queryKeys.clients.all })
      setDeleteDialogOpen(false)
      setClientToDelete(null)
    } catch (error) {
      debugError('Failed to delete client:', error)
      // You might want to show an error toast here
    } finally {
      setDeleting(false)
    }
  }

  if (loading && page === 0) {
    return (
      <Box>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Skeleton variant="rectangular" width={200} height={40} sx={{ borderRadius: 1.5 }} />
          <Skeleton variant="rectangular" width={100} height={32} sx={{ borderRadius: 1.5 }} />
        </Box>
        <Skeleton variant="rectangular" height={400} sx={{ borderRadius: 2 }} />
      </Box>
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
            Clients
          </Typography>
          <Typography 
            variant="body1" 
            color="text.secondary"
            sx={{ fontSize: '0.875rem' }}
          >
            {clients.length} of {totalCount} {totalCount === 1 ? 'client' : 'clients'} 
            {debouncedSearch ? ` matching "${debouncedSearch}"` : ''}
            {(filters.ga4 !== null || filters.scrunch !== null || filters.active !== null) && ' (filtered)'}
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

      {/* Search Bar */}
      <Box mb={3}>
        <TextField
          fullWidth
          placeholder="Search by company name..."
          value={searchTerm}
          onChange={handleSearchChange}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon sx={{ color: 'text.secondary', fontSize: 20 }} />
              </InputAdornment>
            ),
          }}
          sx={{
            '& .MuiOutlinedInput-root': {
              borderRadius: 2,
              bgcolor: 'background.paper',
            },
          }}
        />
      </Box>

      {/* Filters */}
      <Box mb={3} display="flex" gap={1.5} flexWrap="wrap" alignItems="center">
        <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.875rem', fontWeight: 600, mr: 1 }}>
          Filters:
        </Typography>
        
        {/* GA4 Filter */}
        <Chip
          icon={<AnalyticsIcon sx={{ fontSize: 16 }} />}
          label="GA4 Assigned"
          onClick={() => handleFilterChange('ga4', true)}
          onDelete={filters.ga4 === true ? () => handleFilterChange('ga4', null) : undefined}
          color={filters.ga4 === true ? 'primary' : 'default'}
          variant={filters.ga4 === true ? 'filled' : 'outlined'}
          sx={{
            cursor: 'pointer',
            fontWeight: 500,
            '&:hover': {
              bgcolor: filters.ga4 === true 
                ? alpha(theme.palette.primary.main, 0.2)
                : alpha(theme.palette.primary.main, 0.1),
            },
          }}
        />

        {/* Scrunch Filter */}
        <Chip
          icon={<LinkIcon sx={{ fontSize: 16 }} />}
          label="Scrunch Assigned"
          onClick={() => handleFilterChange('scrunch', true)}
          onDelete={filters.scrunch === true ? () => handleFilterChange('scrunch', null) : undefined}
          color={filters.scrunch === true ? 'secondary' : 'default'}
          variant={filters.scrunch === true ? 'filled' : 'outlined'}
          sx={{
            cursor: 'pointer',
            fontWeight: 500,
            '&:hover': {
              bgcolor: filters.scrunch === true 
                ? alpha(theme.palette.secondary.main, 0.2)
                : alpha(theme.palette.secondary.main, 0.1),
            },
          }}
        />

        {/* Active Filter */}
        <Chip
          icon={<CampaignIcon sx={{ fontSize: 16 }} />}
          label="Active"
          onClick={() => handleFilterChange('active', true)}
          onDelete={filters.active === true ? () => handleFilterChange('active', null) : undefined}
          color={filters.active === true ? 'success' : 'default'}
          variant={filters.active === true ? 'filled' : 'outlined'}
          sx={{
            cursor: 'pointer',
            fontWeight: 500,
            '&:hover': {
              bgcolor: filters.active === true 
                ? alpha(theme.palette.success.main, 0.2)
                : alpha(theme.palette.success.main, 0.1),
            },
          }}
        />

        {/* Inactive Filter */}
        <Chip
          icon={<CampaignIcon sx={{ fontSize: 16 }} />}
          label="Inactive"
          onClick={() => handleFilterChange('active', false)}
          onDelete={filters.active === false ? () => handleFilterChange('active', null) : undefined}
          color={filters.active === false ? 'error' : 'default'}
          variant={filters.active === false ? 'filled' : 'outlined'}
          sx={{
            cursor: 'pointer',
            fontWeight: 500,
            '&:hover': {
              bgcolor: filters.active === false 
                ? alpha(theme.palette.error.main, 0.2)
                : alpha(theme.palette.error.main, 0.1),
            },
          }}
        />

        {/* Clear Filters Button */}
        {(filters.ga4 !== null || filters.scrunch !== null || filters.active !== null) && (
          <Button
            size="small"
            onClick={() => setFilters({ ga4: null, scrunch: null, active: null })}
            sx={{
              fontSize: '0.875rem',
              textTransform: 'none',
              color: 'text.secondary',
              ml: 1,
              '&:hover': {
                bgcolor: alpha(theme.palette.error.main, 0.1),
                color: theme.palette.error.main,
              },
            }}
          >
            Clear All
          </Button>
        )}
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          Failed to load clients. Please try again.
        </Alert>
      )}

      {!loading && clients.length === 0 && (
        <Paper
          sx={{
            borderRadius: 2,
            border: `1px solid ${theme.palette.divider}`,
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
            p: 4,
            textAlign: 'center',
          }}
        >
          <BusinessIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2, opacity: 0.4 }} />
          <Typography variant="h6" fontWeight={600} mb={1} sx={{ fontSize: '1.125rem' }}>
            {debouncedSearch ? 'No clients found' : 'No clients available'}
          </Typography>
          <Typography variant="body2" color="text.secondary" mb={3} sx={{ fontSize: '0.875rem' }}>
            {debouncedSearch 
              ? `No clients match "${debouncedSearch}". Try a different search term.`
              : 'Sync Agency Analytics data first to view clients'}
          </Typography>
          {!debouncedSearch && (
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
          )}
        </Paper>
      )}

      {(clients.length > 0 || loading || isFetching) && (
        <TableContainer 
          component={Paper}
          sx={{
            borderRadius: 2,
            border: `1px solid ${theme.palette.divider}`,
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
            overflow: 'hidden',
            position: 'relative',
          }}
        >
          {/* Linear progress bar at top of table when fetching */}
          {isFetching && (
            <LinearProgress 
              sx={{ 
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                zIndex: 10,
                height: 3,
              }} 
            />
          )}
          {/* Loading indicator overlay when fetching new page */}
          {isFetching && (
            <Box
              sx={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                zIndex: 9,
                bgcolor: alpha(theme.palette.background.paper, 0.7),
                backdropFilter: 'blur(2px)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Box display="flex" flexDirection="column" alignItems="center" gap={2}>
                <CircularProgress size={40} />
                <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.875rem' }}>
                  Loading clients...
                </Typography>
              </Box>
            </Box>
          )}
          <Table sx={{ position: 'relative', zIndex: 1 }}>
            <TableHead>
              <TableRow sx={{ bgcolor: alpha(theme.palette.primary.main, 0.02) }}>
                <TableCell sx={{ fontWeight: 600, fontSize: '0.875rem' }}>Company</TableCell>
                <TableCell sx={{ fontWeight: 600, fontSize: '0.875rem' }}>URL</TableCell>
                <TableCell sx={{ fontWeight: 600, fontSize: '0.875rem' }}>Campaigns</TableCell>
                <TableCell sx={{ fontWeight: 600, fontSize: '0.875rem' }}>Keywords</TableCell>
                <TableCell sx={{ fontWeight: 600, fontSize: '0.875rem' }}>Integrations</TableCell>
                <TableCell sx={{ fontWeight: 600, fontSize: '0.875rem' }}>Slug</TableCell>
                <TableCell align="right" sx={{ fontWeight: 600, fontSize: '0.875rem' }}>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading && page === 0 && clients.length === 0 ? (
                Array.from({ length: pageSize }).map((_, index) => (
                  <TableRow key={index}>
                    <TableCell><Skeleton variant="text" width={150} /></TableCell>
                    <TableCell><Skeleton variant="text" width={200} /></TableCell>
                    <TableCell><Skeleton variant="text" width={80} /></TableCell>
                    <TableCell><Skeleton variant="text" width={100} /></TableCell>
                    <TableCell><Skeleton variant="text" width={120} /></TableCell>
                    <TableCell><Skeleton variant="text" width={100} /></TableCell>
                    <TableCell align="right"><Skeleton variant="circular" width={32} height={32} /></TableCell>
                  </TableRow>
                ))
              ) : clients.length > 0 ? (
                clients.map((client) => {
                  const stats = getClientStats(client)
                  return (
                    <TableRow
                      key={client.id}
                      hover
                      sx={{
                        cursor: 'pointer',
                        '&:hover': {
                          bgcolor: alpha(theme.palette.primary.main, 0.02),
                        },
                      }}
                      onClick={() => {
                        // Navigate to reporting dashboard with client ID in state
                        navigate('/reporting', { 
                          state: { clientId: client.id } 
                        })
                      }}
                    >
                      <TableCell>
                        <Box display="flex" alignItems="center" gap={1.5}>
                          {client.logo_url ? (
                            <Box
                              component="img"
                              src={client.logo_url}
                              alt={`${client.company_name} logo`}
                              sx={{
                                width: 32,
                                height: 32,
                                borderRadius: 1,
                                objectFit: 'contain',
                                border: `1px solid ${theme.palette.divider}`,
                                p: 0.5,
                              }}
                            />
                          ) : (
                            <Avatar
                              sx={{
                                bgcolor: client.theme_color || alpha(theme.palette.primary.main, 0.1),
                                color: client.theme_color || theme.palette.primary.main,
                                width: 32,
                                height: 32,
                                fontSize: '14px',
                                fontWeight: 600,
                              }}
                            >
                              {client.company_name?.charAt(0) || <BusinessIcon />}
                            </Avatar>
                          )}
                          <Box>
                            <Typography variant="body2" fontWeight={600}>
                              {client.company_name}
                            </Typography>
                            {client.company_domain && (
                              <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
                                {client.company_domain}
                              </Typography>
                            )}
                          </Box>
                        </Box>
                      </TableCell>
                      <TableCell>
                        {client.url ? (
                          <Box display="flex" alignItems="center" gap={0.5}>
                            <LanguageIcon sx={{ fontSize: 14, color: 'text.secondary', opacity: 0.6 }} />
                            <Typography 
                              variant="body2" 
                              color="text.secondary"
                              sx={{ 
                                fontSize: '0.875rem',
                                maxWidth: 200,
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                whiteSpace: 'nowrap',
                              }}
                            >
                              {client.url.replace(/^https?:\/\//, '').replace(/\/$/, '')}
                            </Typography>
                          </Box>
                        ) : (
                          <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.875rem' }}>
                            -
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={stats.campaignCount}
                          size="small"
                          icon={<CampaignIcon sx={{ fontSize: 14 }} />}
                          sx={{
                            height: 24,
                            fontSize: '0.75rem',
                            fontWeight: 600,
                          }}
                        />
                      </TableCell>
                      <TableCell>
                        {client.keywords_count && client.keywords_count > 0 ? (
                          <Chip
                            label={client.keywords_count.toLocaleString()}
                            size="small"
                            icon={<TagIcon sx={{ fontSize: 14 }} />}
                            sx={{
                              height: 24,
                              fontSize: '0.75rem',
                              fontWeight: 600,
                            }}
                          />
                        ) : (
                          <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.875rem' }}>
                            -
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Box display="flex" gap={0.5} alignItems="center">
                          {stats.hasGA4 && (
                            <Tooltip title="GA4 Connected" arrow>
                              <Chip
                                label="GA4"
                                size="small"
                                icon={<AnalyticsIcon sx={{ fontSize: 14 }} />}
                                color="success"
                                sx={{ height: 24, fontSize: '0.7rem' }}
                              />
                            </Tooltip>
                          )}
                          {stats.hasScrunch && (
                            <Tooltip title="Scrunch Connected" arrow>
                              <Chip
                                label="Scrunch"
                                size="small"
                                icon={<LinkIcon sx={{ fontSize: 14 }} />}
                                color="info"
                                sx={{ height: 24, fontSize: '0.7rem' }}
                              />
                            </Tooltip>
                          )}
                          {!stats.hasMappings && (
                            <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
                              None
                            </Typography>
                          )}
                        </Box>
                      </TableCell>
                      <TableCell>
                        {client.url_slug ? (
                          <Typography 
                            variant="body2" 
                            sx={{ 
                              fontSize: '0.75rem',
                              fontFamily: 'monospace',
                              color: 'text.secondary',
                            }}
                          >
                            {client.url_slug.substring(0, 16)}...
                          </Typography>
                        ) : (
                          <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.875rem' }}>
                            -
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell align="right">
                        <Box display="flex" gap={0.5} justifyContent="flex-end">
                          <Tooltip title="Manage Client Settings" arrow>
                            <IconButton
                              size="small"
                              onClick={(e) => handleManageClick(e, client)}
                              sx={{
                                color: theme.palette.primary.main,
                                transition: 'all 0.2s',
                                '&:hover': {
                                  bgcolor: alpha(theme.palette.primary.main, 0.1),
                                },
                              }}
                            >
                              <SettingsIcon sx={{ fontSize: 18 }} />
                            </IconButton>
                          </Tooltip>
                          {client.url_slug && (
                            <Tooltip title="Open Public Report in New Tab" arrow>
                              <IconButton
                                size="small"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  const baseUrl = window.location.origin
                                  window.open(`${baseUrl}/reporting/client/${client.url_slug}`, '_blank')
                                }}
                                sx={{
                                  color: 'text.secondary',
                                  transition: 'all 0.2s',
                                  '&:hover': {
                                    bgcolor: alpha(theme.palette.primary.main, 0.1),
                                    color: theme.palette.primary.main,
                                  },
                                }}
                              >
                                <OpenInNewIcon sx={{ fontSize: 18 }} />
                              </IconButton>
                            </Tooltip>
                          )}
                          <Tooltip title="Delete Client" arrow>
                            <IconButton
                              size="small"
                              onClick={(e) => handleDeleteClick(e, client)}
                              sx={{
                                color: theme.palette.error.main,
                                transition: 'all 0.2s',
                                '&:hover': {
                                  bgcolor: alpha(theme.palette.error.main, 0.1),
                                },
                              }}
                            >
                              <DeleteIcon sx={{ fontSize: 18 }} />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </TableCell>
                    </TableRow>
                  )
                })
              ) : null}
            </TableBody>
          </Table>
          <TablePagination
            component="div"
            count={totalCount}
            page={page}
            onPageChange={handleChangePage}
            rowsPerPage={pageSize}
            onRowsPerPageChange={handleChangePageSize}
            rowsPerPageOptions={[10, 25, 50, 100]}
            disabled={isFetching}
            sx={{
              borderTop: `1px solid ${theme.palette.divider}`,
              opacity: isFetching ? 0.6 : 1,
              position: 'relative',
              zIndex: 1000, // Ensure pagination is above support widgets and overlays
              bgcolor: 'background.paper',
            }}
          />
        </TableContainer>
      )}

      <ClientManagement
        open={managementOpen}
        onClose={handleManagementClose}
        client={selectedClient}
      />

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={handleDeleteCancel}
        aria-labelledby="delete-dialog-title"
        aria-describedby="delete-dialog-description"
      >
        <DialogTitle id="delete-dialog-title">
          Delete Client
        </DialogTitle>
        <DialogContent>
          <DialogContentText id="delete-dialog-description">
            Are you sure you want to delete <strong>{clientToDelete?.company_name}</strong>? 
            This will perform a soft delete and the client will be hidden from the list. 
            This action can be reversed by changing the filter to show inactive clients.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeleteCancel} disabled={deleting}>
            Cancel
          </Button>
          <Button 
            onClick={handleDeleteConfirm} 
            color="error" 
            variant="contained"
            disabled={deleting}
          >
            {deleting ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default ClientsList

import { useState, useEffect } from 'react'
import {
  Box,
  Card,
  CardContent,
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
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  LinearProgress,
} from '@mui/material'
import {
  History as HistoryIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
} from '@mui/icons-material'
import { auditAPI } from '../services/api'

const ACTION_LABELS = {
  login: 'Login',
  logout: 'Logout',
  user_created: 'User Created',
  sync_brands: 'Sync Brands',
  sync_prompts: 'Sync Prompts',
  sync_responses: 'Sync Responses',
  sync_ga4: 'Sync GA4',
  sync_agency_analytics: 'Sync Agency Analytics',
  sync_all: 'Sync All',
}

const STATUS_COLORS = {
  success: 'success',
  error: 'error',
  partial: 'warning',
}

function AuditLogs() {
  const theme = useTheme()
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(25)
  const [totalCount, setTotalCount] = useState(0)
  const [isFetching, setIsFetching] = useState(false)
  
  // Filters
  const [actionFilter, setActionFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [userEmailFilter, setUserEmailFilter] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')

  useEffect(() => {
    loadLogs()
  }, [page, rowsPerPage, actionFilter, statusFilter, userEmailFilter, startDate, endDate])

  const loadLogs = async () => {
    try {
      setIsFetching(true)
      setError(null)
      const response = await auditAPI.getAuditLogs(
        actionFilter || null,
        userEmailFilter || null,
        statusFilter || null,
        startDate || null,
        endDate || null,
        page + 1,
        rowsPerPage
      )
      setLogs(response.items || [])
      setTotalCount(response.total || 0)
    } catch (err) {
      console.error('Error loading audit logs:', err)
      setError(err.response?.data?.detail || 'Failed to load audit logs')
      setLogs([])
    } finally {
      setIsFetching(false)
    }
  }

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A'
    try {
      const date = new Date(dateStr)
      return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    } catch {
      return dateStr
    }
  }

  const formatDetails = (details) => {
    if (!details || typeof details !== 'object') return 'N/A'
    try {
      // Format common details
      const parts = []
      if (details.total_count !== undefined) parts.push(`Total: ${details.total_count}`)
      if (details.brand_count !== undefined) parts.push(`Brands: ${details.brand_count}`)
      if (details.new_user_email) parts.push(`New User: ${details.new_user_email}`)
      if (details.self_registration !== undefined) parts.push(`Self-registered: ${details.self_registration ? 'Yes' : 'No'}`)
      
      return parts.length > 0 ? parts.join(', ') : JSON.stringify(details)
    } catch {
      return JSON.stringify(details)
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'success':
        return <CheckCircleIcon sx={{ fontSize: 16, color: 'success.main' }} />
      case 'error':
        return <ErrorIcon sx={{ fontSize: 16, color: 'error.main' }} />
      case 'partial':
        return <WarningIcon sx={{ fontSize: 16, color: 'warning.main' }} />
      default:
        return null
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
          Audit Logs
        </Typography>
        <Typography 
          variant="body1" 
          color="text.secondary"
          sx={{ fontSize: '0.875rem' }}
        >
          Track user actions, logins, and data sync operations
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

      {/* Filters */}
      <Card 
        sx={{ 
          mb: 3,
          borderRadius: 2,
          border: `1px solid ${theme.palette.divider}`,
          boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
        }}
      >
        <CardContent sx={{ p: 2.5 }}>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Action</InputLabel>
                <Select
                  value={actionFilter}
                  label="Action"
                  onChange={(e) => {
                    setActionFilter(e.target.value)
                    setPage(0)
                  }}
                >
                  <MenuItem value="">All Actions</MenuItem>
                  {Object.entries(ACTION_LABELS).map(([key, label]) => (
                    <MenuItem key={key} value={key}>{label}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Status</InputLabel>
                <Select
                  value={statusFilter}
                  label="Status"
                  onChange={(e) => {
                    setStatusFilter(e.target.value)
                    setPage(0)
                  }}
                >
                  <MenuItem value="">All Statuses</MenuItem>
                  <MenuItem value="success">Success</MenuItem>
                  <MenuItem value="error">Error</MenuItem>
                  <MenuItem value="partial">Partial</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                size="small"
                label="User Email"
                value={userEmailFilter}
                onChange={(e) => {
                  setUserEmailFilter(e.target.value)
                  setPage(0)
                }}
                placeholder="Filter by email..."
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                size="small"
                label="Start Date"
                type="date"
                value={startDate}
                onChange={(e) => {
                  setStartDate(e.target.value)
                  setPage(0)
                }}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                size="small"
                label="End Date"
                type="date"
                value={endDate}
                onChange={(e) => {
                  setEndDate(e.target.value)
                  setPage(0)
                }}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Logs Table */}
      <Card
        sx={{
          borderRadius: 2,
          border: `1px solid ${theme.palette.divider}`,
          boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
        }}
      >
        <CardContent sx={{ p: 0 }}>
          {isFetching && logs.length === 0 ? (
            <Box display="flex" justifyContent="center" py={4}>
              <CircularProgress size={40} thickness={4} />
            </Box>
          ) : logs.length === 0 ? (
            <Alert severity="info" sx={{ m: 2, borderRadius: 2 }}>
              No audit logs found for the selected filters.
            </Alert>
          ) : (
            <>
              {isFetching && <LinearProgress sx={{ mb: 1 }} />}
              <TableContainer component={Paper} sx={{ borderRadius: 2, boxShadow: 'none' }}>
                <Table>
                  <TableHead>
                    <TableRow sx={{ bgcolor: alpha(theme.palette.primary.main, 0.04) }}>
                      <TableCell sx={{ fontWeight: 700, fontSize: '13px' }}>Timestamp</TableCell>
                      <TableCell sx={{ fontWeight: 700, fontSize: '13px' }}>Action</TableCell>
                      <TableCell sx={{ fontWeight: 700, fontSize: '13px' }}>User</TableCell>
                      <TableCell sx={{ fontWeight: 700, fontSize: '13px' }}>Status</TableCell>
                      <TableCell sx={{ fontWeight: 700, fontSize: '13px' }}>IP Address</TableCell>
                      <TableCell sx={{ fontWeight: 700, fontSize: '13px' }}>Details</TableCell>
                      <TableCell sx={{ fontWeight: 700, fontSize: '13px' }}>Error</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {logs.map((log) => (
                      <TableRow 
                        key={log.id}
                        sx={{
                          '&:nth-of-type(odd)': {
                            bgcolor: alpha(theme.palette.primary.main, 0.02),
                          },
                          '&:hover': {
                            bgcolor: alpha(theme.palette.primary.main, 0.05),
                          },
                        }}
                      >
                        <TableCell sx={{ fontSize: '13px' }}>
                          {formatDate(log.created_at)}
                        </TableCell>
                        <TableCell sx={{ fontSize: '13px' }}>
                          <Chip
                            label={ACTION_LABELS[log.action] || log.action}
                            size="small"
                            sx={{
                              height: 24,
                              fontSize: '0.75rem',
                              fontWeight: 600,
                            }}
                          />
                        </TableCell>
                        <TableCell sx={{ fontSize: '13px' }}>
                          {log.user_email || log.user_id || 'N/A'}
                        </TableCell>
                        <TableCell sx={{ fontSize: '13px' }}>
                          {log.status ? (
                            <Box display="flex" alignItems="center" gap={0.5}>
                              {getStatusIcon(log.status)}
                              <Chip
                                label={log.status}
                                size="small"
                                color={STATUS_COLORS[log.status] || 'default'}
                                sx={{
                                  height: 24,
                                  fontSize: '0.75rem',
                                  fontWeight: 600,
                                }}
                              />
                            </Box>
                          ) : (
                            'N/A'
                          )}
                        </TableCell>
                        <TableCell sx={{ fontSize: '13px' }}>
                          {log.ip_address || 'N/A'}
                        </TableCell>
                        <TableCell sx={{ fontSize: '13px', maxWidth: 300 }}>
                          <Typography
                            variant="body2"
                            sx={{
                              fontSize: '0.75rem',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                            }}
                            title={formatDetails(log.details)}
                          >
                            {formatDetails(log.details)}
                          </Typography>
                        </TableCell>
                        <TableCell sx={{ fontSize: '13px', maxWidth: 200 }}>
                          {log.error_message ? (
                            <Typography
                              variant="body2"
                              color="error"
                              sx={{
                                fontSize: '0.75rem',
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                whiteSpace: 'nowrap',
                              }}
                              title={log.error_message}
                            >
                              {log.error_message}
                            </Typography>
                          ) : (
                            'N/A'
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
              {totalCount > rowsPerPage && (
                <TablePagination
                  component="div"
                  count={totalCount}
                  page={page}
                  onPageChange={(event, newPage) => {
                    setPage(newPage)
                  }}
                  rowsPerPage={rowsPerPage}
                  onRowsPerPageChange={(event) => {
                    setRowsPerPage(parseInt(event.target.value, 10))
                    setPage(0)
                  }}
                  rowsPerPageOptions={[10, 25, 50, 100]}
                  disabled={isFetching}
                />
              )}
            </>
          )}
        </CardContent>
      </Card>
    </Box>
  )
}

export default AuditLogs


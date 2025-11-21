import { useState, useEffect } from 'react'
import {
  Box,
  Card,
  CardContent,
  Button,
  Typography,
  Grid,
  CircularProgress,
  LinearProgress,
  alpha,
  useTheme,
  Chip
} from '@mui/material'
import {
  Sync as SyncIcon,
  CloudDownload as CloudDownloadIcon,
  Analytics as AnalyticsIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
} from '@mui/icons-material'
import { motion } from 'framer-motion'
import { syncAPI } from '../services/api'
import { useToast } from '../contexts/ToastContext'
import { useSyncStatus } from '../contexts/SyncStatusContext'
import { getErrorMessage } from '../utils/errorHandler'

function SyncPanel() {
  const [syncing, setSyncing] = useState(null)
  const theme = useTheme()
  const { showError, showSuccess } = useToast()
  const { activeJobs, addJob, refreshJobs } = useSyncStatus()

  // Poll for job updates
  useEffect(() => {
    if (!syncing) return // Don't poll if no job is being tracked

    const interval = setInterval(async () => {
      if (!syncing) {
        clearInterval(interval)
        return
      }

      try {
        const job = await syncAPI.getSyncJobStatus(syncing)
        if (job) {
          // Stop polling if job is completed or failed
          if (job.status === 'completed' || job.status === 'failed') {
            clearInterval(interval)
            
            if (job.status === 'completed') {
              const result = job.result || {}
              if (job.sync_type === 'sync_all') {
                const summary = result.summary || {}
                showSuccess(`Sync completed: Brands: ${summary.brands || 0}, Prompts: ${summary.total_prompts || 0}, Responses: ${summary.total_responses || 0}`)
              } else if (job.sync_type === 'sync_ga4') {
                const totalSynced = result.total_synced || {}
                showSuccess(`GA4 sync completed: Brands: ${totalSynced.brands || 0}`)
              } else if (job.sync_type === 'sync_agency_analytics') {
                const totalSynced = result.total_synced || {}
                showSuccess(`Agency Analytics sync completed: Campaigns: ${totalSynced.campaigns || 0}`)
              }
            } else if (job.status === 'failed') {
              showError(job.error_message || 'Sync failed')
            }
            
            setSyncing(null)
            refreshJobs()
          }
        }
      } catch (err) {
        console.error('Error checking job status:', err)
        // On error, stop polling to avoid infinite retries
        clearInterval(interval)
        setSyncing(null)
      }
    }, 2000) // Poll every 2 seconds

    return () => clearInterval(interval)
  }, [syncing, showSuccess, showError, refreshJobs])

  const handleSyncScrunch = async () => {
    try {
      setSyncing(null) // Reset
      
      const result = await syncAPI.syncAll()
      
      if (result.job_id) {
        setSyncing(result.job_id)
        addJob(result.job_id, 'sync_all')
        showSuccess('Sync started. You can continue using the app while it runs in the background.')
      } else {
        showError('Failed to start sync job')
      }
    } catch (err) {
      showError(getErrorMessage(err))
    }
  }

  const handleSyncGA4 = async () => {
    try {
      setSyncing(null) // Reset
      
      const result = await syncAPI.syncGA4()
      
      if (result.job_id) {
        setSyncing(result.job_id)
        addJob(result.job_id, 'sync_ga4')
        showSuccess('GA4 sync started. You can continue using the app while it runs in the background.')
      } else {
        showError('Failed to start GA4 sync job')
      }
    } catch (err) {
      showError(getErrorMessage(err))
    }
  }

  const handleSyncAgencyAnalytics = async () => {
    try {
      setSyncing(null) // Reset
      
      const result = await syncAPI.syncAgencyAnalytics()
      
      if (result.job_id) {
        setSyncing(result.job_id)
        addJob(result.job_id, 'sync_agency_analytics')
        showSuccess('Agency Analytics sync started. You can continue using the app while it runs in the background.')
      } else {
        showError('Failed to start Agency Analytics sync job')
      }
    } catch (err) {
      showError(getErrorMessage(err))
    }
  }

  // Get current job status
  const getCurrentJob = () => {
    if (!syncing) return null
    return activeJobs.find(j => j.job_id === syncing)
  }

  const currentJob = getCurrentJob()
  const isLoading = syncing !== null && currentJob && ['pending', 'running'].includes(currentJob.status)

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
          Sync Data
        </Typography>
        <Typography 
          variant="body1" 
          color="text.secondary"
          sx={{ fontSize: '0.875rem' }}
        >
          Sync data from Scrunch AI API, Google Analytics 4, and Agency Analytics to Supabase
        </Typography>
      </Box>

      <Grid container spacing={2.5}>
        <Grid item xs={12} md={4}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
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
                },
                '&:hover': {
                  boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                  transform: 'translateY(-2px)',
                },
              }}
            >
              <CardContent sx={{ p: 3, textAlign: 'center' }}>
                <Box
                  sx={{
                    p: 1.5,
                    borderRadius: 1.5,
                    background: alpha(theme.palette.primary.main, 0.1),
                    color: theme.palette.primary.main,
                    display: 'inline-flex',
                    mb: 2,
                  }}
                >
                  <CloudDownloadIcon sx={{ fontSize: 24 }} />
                </Box>
                <Typography 
                  variant="h6" 
                  fontWeight={600} 
                  mb={1}
                  sx={{ fontSize: '1rem' }}
                >
                  Sync Scrunch API Data
                </Typography>
                <Typography 
                  variant="body2" 
                  color="text.secondary" 
                  mb={3}
                  sx={{ fontSize: '0.875rem', lineHeight: 1.6 }}
                >
                  Sync all data from Scrunch AI API including brands, prompts, and responses to Supabase database.
                </Typography>
                <Button
                  variant="contained"
                  fullWidth
                  size="small"
                  onClick={handleSyncScrunch}
                  disabled={isLoading && currentJob?.sync_type === 'sync_all'}
                  startIcon={
                    isLoading && currentJob?.sync_type === 'sync_all' ? (
                      <CircularProgress size={16} thickness={4} sx={{ color: 'white' }} />
                    ) : (
                      <SyncIcon sx={{ fontSize: 16 }} />
                    )
                  }
                  sx={{
                    borderRadius: 1.5,
                    px: 2,
                    py: 0.75,
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    boxShadow: 'none',
                    '&:hover': {
                      boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
                    },
                  }}
                >
                  {isLoading && currentJob?.sync_type === 'sync_all' ? 'Syncing...' : 'Sync Scrunch Data'}
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        </Grid>

        <Grid item xs={12} md={4}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.1 }}
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
                  backgroundColor: theme.palette.success.main,
                },
                '&:hover': {
                  boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                  transform: 'translateY(-2px)',
                },
              }}
            >
              <CardContent sx={{ p: 3, textAlign: 'center' }}>
                <Box
                  sx={{
                    p: 1.5,
                    borderRadius: 1.5,
                    background: alpha(theme.palette.success.main, 0.1),
                    color: theme.palette.success.main,
                    display: 'inline-flex',
                    mb: 2,
                  }}
                >
                  <AnalyticsIcon sx={{ fontSize: 24 }} />
                </Box>
                <Typography 
                  variant="h6" 
                  fontWeight={600} 
                  mb={1}
                  sx={{ fontSize: '1rem' }}
                >
                  Sync GA4 Data
                </Typography>
                <Typography 
                  variant="body2" 
                  color="text.secondary" 
                  mb={3}
                  sx={{ fontSize: '0.875rem', lineHeight: 1.6 }}
                >
                  Sync Google Analytics 4 data for all brands with GA4 property IDs configured. Includes traffic overview, top pages, sources, geographic, devices, and conversions.
                </Typography>
                <Button
                  variant="contained"
                  fullWidth
                  size="small"
                  onClick={handleSyncGA4}
                  disabled={isLoading && currentJob?.sync_type === 'sync_ga4'}
                  startIcon={
                    isLoading && currentJob?.sync_type === 'sync_ga4' ? (
                      <CircularProgress size={16} thickness={4} sx={{ color: 'white' }} />
                    ) : (
                      <AnalyticsIcon sx={{ fontSize: 16 }} />
                    )
                  }
                  sx={{
                    borderRadius: 1.5,
                    px: 2,
                    py: 0.75,
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    bgcolor: theme.palette.success.main,
                    boxShadow: 'none',
                    '&:hover': {
                      bgcolor: theme.palette.success.dark,
                      boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
                    },
                  }}
                >
                  {isLoading && currentJob?.sync_type === 'sync_ga4' ? 'Syncing...' : 'Sync GA4 Data'}
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        </Grid>

        <Grid item xs={12} md={4}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.2 }}
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
                  backgroundColor: theme.palette.warning.main,
                },
                '&:hover': {
                  boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                  transform: 'translateY(-2px)',
                },
              }}
            >
              <CardContent sx={{ p: 3, textAlign: 'center' }}>
                <Box
                  sx={{
                    p: 1.5,
                    borderRadius: 1.5,
                    background: alpha(theme.palette.warning.main, 0.1),
                    color: theme.palette.warning.main,
                    display: 'inline-flex',
                    mb: 2,
                  }}
                >
                  <AnalyticsIcon sx={{ fontSize: 24 }} />
                </Box>
                <Typography 
                  variant="h6" 
                  fontWeight={600} 
                  mb={1}
                  sx={{ fontSize: '1rem' }}
                >
                  Sync Agency Analytics Data
                </Typography>
                <Typography 
                  variant="body2" 
                  color="text.secondary" 
                  mb={3}
                  sx={{ fontSize: '0.875rem', lineHeight: 1.6 }}
                >
                  Sync Agency Analytics campaigns and quarterly ranking data. Includes Google rankings, Bing rankings, search volume, and competition metrics.
                </Typography>
                <Button
                  variant="contained"
                  fullWidth
                  size="small"
                  onClick={handleSyncAgencyAnalytics}
                  disabled={isLoading && currentJob?.sync_type === 'sync_agency_analytics'}
                  startIcon={
                    isLoading && currentJob?.sync_type === 'sync_agency_analytics' ? (
                      <CircularProgress size={16} thickness={4} sx={{ color: 'white' }} />
                    ) : (
                      <AnalyticsIcon sx={{ fontSize: 16 }} />
                    )
                  }
                  sx={{
                    borderRadius: 1.5,
                    px: 2,
                    py: 0.75,
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    bgcolor: theme.palette.warning.main,
                    boxShadow: 'none',
                    '&:hover': {
                      bgcolor: theme.palette.warning.dark,
                      boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
                    },
                  }}
                >
                  {isLoading && currentJob?.sync_type === 'sync_agency_analytics' ? 'Syncing...' : 'Sync Agency Analytics'}
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        </Grid>
      </Grid>

      {currentJob && isLoading && (
        <Box mt={3}>
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
          >
            <Card
              sx={{
                borderRadius: 2,
                border: `1px solid ${theme.palette.divider}`,
                boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
              }}
            >
              <CardContent sx={{ p: 2.5 }}>
                <Box display="flex" alignItems="center" justifyContent="space-between" mb={1.5}>
                  <Box display="flex" alignItems="center" gap={1.5}>
                    <CircularProgress size={20} thickness={4} />
                    <Box>
                      <Typography 
                        variant="body2" 
                        sx={{ fontSize: '0.875rem', fontWeight: 600 }}
                      >
                        {currentJob.current_step || 'Syncing...'}
                      </Typography>
                      {currentJob.progress > 0 && (
                        <Typography 
                          variant="caption" 
                          color="text.secondary"
                          sx={{ fontSize: '0.75rem' }}
                        >
                          {currentJob.progress}% complete
                        </Typography>
                      )}
                    </Box>
                  </Box>
                  <Chip 
                    label={currentJob.status === 'running' ? 'Running' : 'Pending'}
                    size="small"
                    color="primary"
                    sx={{ fontSize: '0.75rem', height: 24 }}
                  />
                </Box>
                {currentJob.progress > 0 && (
                  <LinearProgress 
                    variant="determinate"
                    value={currentJob.progress}
                    sx={{ 
                      borderRadius: 1,
                      height: 6,
                    }}
                  />
                )}
              </CardContent>
            </Card>
          </motion.div>
        </Box>
      )}
    </Box>
  )
}

export default SyncPanel


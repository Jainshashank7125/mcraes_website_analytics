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
import { Tooltip } from '@mui/material'
import { motion } from 'framer-motion'
import { syncAPI } from '../services/api'
import { useToast } from '../contexts/ToastContext'
import { useSyncStatus } from '../contexts/SyncStatusContext'
import { getErrorMessage } from '../utils/errorHandler'
import { debugError } from '../utils/debug'

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
                showSuccess(`GA4 sync completed: Clients: ${totalSynced.clients || 0}`)
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
        debugError('Error checking job status:', err)
        // On error, stop polling to avoid infinite retries
        clearInterval(interval)
        setSyncing(null)
      }
    }, 45000) // Poll every 45 seconds

    return () => clearInterval(interval)
  }, [syncing, showSuccess, showError, refreshJobs])

  const handleSyncScrunch = async (syncMode = 'complete') => {
    try {
      setSyncing(null) // Reset
      
      const result = await syncAPI.syncAll(syncMode)
      
      if (result.job_id) {
        setSyncing(result.job_id)
        addJob(result.job_id, 'sync_all')
        showSuccess(`${syncMode === 'new' ? 'New' : 'Complete'} sync started. You can continue using the app while it runs in the background.`)
      } else {
        showError('Failed to start sync job')
      }
    } catch (err) {
      showError(getErrorMessage(err))
    }
  }

  const handleSyncGA4 = async (syncMode = 'complete') => {
    try {
      setSyncing(null) // Reset
      
      const result = await syncAPI.syncGA4(syncMode)
      
      if (result.job_id) {
        setSyncing(result.job_id)
        addJob(result.job_id, 'sync_ga4')
        showSuccess(`GA4 ${syncMode === 'new' ? 'New' : 'Complete'} sync started. You can continue using the app while it runs in the background.`)
      } else {
        showError('Failed to start GA4 sync job')
      }
    } catch (err) {
      showError(getErrorMessage(err))
    }
  }

  const handleSyncAgencyAnalytics = async (syncMode = 'complete') => {
    try {
      setSyncing(null) // Reset
      
      const result = await syncAPI.syncAgencyAnalytics(syncMode)
      
      if (result.job_id) {
        setSyncing(result.job_id)
        addJob(result.job_id, 'sync_agency_analytics')
        showSuccess(`Agency Analytics ${syncMode === 'new' ? 'New' : 'Complete'} sync started. You can continue using the app while it runs in the background.`)
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

      <Grid container spacing={{ xs: 2, sm: 2.5, md: 3 }} sx={{ display: 'flex' }}>
        <Grid item xs={12} sm={6} md={4} sx={{ display: 'flex' }}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            style={{ width: '100%', display: 'flex' }}
          >
            <Card
              sx={{
                width: '100%',
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
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
              <CardContent 
                sx={{ 
                  p: { xs: 2.5, sm: 3 },
                  textAlign: 'center',
                  display: 'flex',
                  flexDirection: 'column',
                  flex: 1,
                  height: '100%',
                }}
              >
                <Box
                  sx={{
                    p: 1.5,
                    borderRadius: 1.5,
                    background: alpha(theme.palette.primary.main, 0.1),
                    color: theme.palette.primary.main,
                    display: 'inline-flex',
                    mb: 2,
                    mx: 'auto',
                  }}
                >
                  <CloudDownloadIcon sx={{ fontSize: { xs: 22, sm: 24 } }} />
                </Box>
                <Typography 
                  variant="h6" 
                  fontWeight={600} 
                  mb={1}
                  sx={{ 
                    fontSize: { xs: '0.9375rem', sm: '1rem' },
                    minHeight: { xs: '24px', sm: '28px' },
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  Sync Scrunch API Data
                </Typography>
                <Typography 
                  variant="body2" 
                  color="text.secondary" 
                  mb={2}
                  sx={{ 
                    fontSize: { xs: '0.8125rem', sm: '0.875rem' },
                    lineHeight: 1.6,
                    flex: 1,
                    display: 'flex',
                    alignItems: 'center',
                    minHeight: { xs: '48px', sm: '56px' },
                  }}
                >
                  Sync all data from Scrunch AI API including brands, prompts, and responses to Supabase database.
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, mt: 'auto' }}>
                  <Tooltip 
                    title="New Sync: Only syncs brands that don't exist in the database. Use for regular operations." 
                    arrow
                    placement="top"
                  >
                    <Button
                      variant="outlined"
                      fullWidth
                      size="small"
                      onClick={() => handleSyncScrunch('new')}
                      disabled={isLoading && currentJob?.sync_type === 'sync_all'}
                      sx={{
                        borderRadius: 1.5,
                        px: 1.5,
                        py: 0.75,
                        fontSize: { xs: '0.75rem', sm: '0.8125rem' },
                        fontWeight: 600,
                        borderColor: theme.palette.primary.main,
                        color: theme.palette.primary.main,
                        '&:hover': {
                          borderColor: theme.palette.primary.dark,
                          bgcolor: alpha(theme.palette.primary.main, 0.05),
                        },
                      }}
                    >
                      New Sync
                    </Button>
                  </Tooltip>
                  <Tooltip 
                    title="Complete Sync: Syncs all brands, prompts, and responses. Use for initial onboarding or full refresh." 
                    arrow
                    placement="top"
                  >
                    <Button
                      variant="contained"
                      fullWidth
                      size="small"
                      onClick={() => handleSyncScrunch('complete')}
                      disabled={isLoading && currentJob?.sync_type === 'sync_all'}
                      startIcon={
                        isLoading && currentJob?.sync_type === 'sync_all' ? (
                          <CircularProgress size={14} thickness={4} sx={{ color: 'white' }} />
                        ) : (
                          <SyncIcon sx={{ fontSize: 14 }} />
                        )
                      }
                      sx={{
                        borderRadius: 1.5,
                        px: 1.5,
                        py: 0.75,
                        fontSize: { xs: '0.75rem', sm: '0.8125rem' },
                        fontWeight: 600,
                        boxShadow: 'none',
                        '&:hover': {
                          boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
                        },
                      }}
                    >
                      {isLoading && currentJob?.sync_type === 'sync_all' ? 'Syncing...' : 'Complete'}
                    </Button>
                  </Tooltip>
                </Box>
              </CardContent>
            </Card>
          </motion.div>
        </Grid>

        <Grid item xs={12} sm={6} md={4} sx={{ display: 'flex' }}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.1 }}
            style={{ width: '100%', display: 'flex' }}
          >
            <Card
              sx={{
                width: '100%',
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
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
              <CardContent 
                sx={{ 
                  p: { xs: 2.5, sm: 3 },
                  textAlign: 'center',
                  display: 'flex',
                  flexDirection: 'column',
                  flex: 1,
                  height: '100%',
                }}
              >
                <Box
                  sx={{
                    p: 1.5,
                    borderRadius: 1.5,
                    background: alpha(theme.palette.success.main, 0.1),
                    color: theme.palette.success.main,
                    display: 'inline-flex',
                    mb: 2,
                    mx: 'auto',
                  }}
                >
                  <AnalyticsIcon sx={{ fontSize: { xs: 22, sm: 24 } }} />
                </Box>
                <Typography 
                  variant="h6" 
                  fontWeight={600} 
                  mb={1}
                  sx={{ 
                    fontSize: { xs: '0.9375rem', sm: '1rem' },
                    minHeight: { xs: '24px', sm: '28px' },
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  Sync GA4 Data
                </Typography>
                <Typography 
                  variant="body2" 
                  color="text.secondary" 
                  mb={2}
                  sx={{ 
                    fontSize: { xs: '0.8125rem', sm: '0.875rem' },
                    lineHeight: 1.6,
                    flex: 1,
                    display: 'flex',
                    alignItems: 'center',
                    minHeight: { xs: '48px', sm: '56px' },
                  }}
                >
                  Sync Google Analytics 4 data for all clients with GA4 property IDs configured. Includes traffic overview, top pages, sources, geographic, devices, and conversions.
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, mt: 'auto' }}>
                  <Tooltip 
                    title="New Sync: Only syncs GA4 data for clients without existing GA4 data. Use for regular operations." 
                    arrow
                    placement="top"
                  >
                    <Button
                      variant="outlined"
                      fullWidth
                      size="small"
                      onClick={() => handleSyncGA4('new')}
                      disabled={isLoading && currentJob?.sync_type === 'sync_ga4'}
                      sx={{
                        borderRadius: 1.5,
                        px: 1.5,
                        py: 0.75,
                        fontSize: { xs: '0.75rem', sm: '0.8125rem' },
                        fontWeight: 600,
                        borderColor: theme.palette.success.main,
                        color: theme.palette.success.main,
                        '&:hover': {
                          borderColor: theme.palette.success.dark,
                          bgcolor: alpha(theme.palette.success.main, 0.05),
                        },
                      }}
                    >
                      New Sync
                    </Button>
                  </Tooltip>
                  <Tooltip 
                    title="Complete Sync: Syncs GA4 data for all clients with GA4 property IDs. Use for initial onboarding or full refresh." 
                    arrow
                    placement="top"
                  >
                    <Button
                      variant="contained"
                      fullWidth
                      size="small"
                      onClick={() => handleSyncGA4('complete')}
                      disabled={isLoading && currentJob?.sync_type === 'sync_ga4'}
                      startIcon={
                        isLoading && currentJob?.sync_type === 'sync_ga4' ? (
                          <CircularProgress size={14} thickness={4} sx={{ color: 'white' }} />
                        ) : (
                          <AnalyticsIcon sx={{ fontSize: 14 }} />
                        )
                      }
                      sx={{
                        borderRadius: 1.5,
                        px: 1.5,
                        py: 0.75,
                        fontSize: { xs: '0.75rem', sm: '0.8125rem' },
                        fontWeight: 600,
                        bgcolor: theme.palette.success.main,
                        boxShadow: 'none',
                        '&:hover': {
                          bgcolor: theme.palette.success.dark,
                          boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
                        },
                      }}
                    >
                      {isLoading && currentJob?.sync_type === 'sync_ga4' ? 'Syncing...' : 'Complete'}
                    </Button>
                  </Tooltip>
                </Box>
              </CardContent>
            </Card>
          </motion.div>
        </Grid>

        <Grid item xs={12} sm={6} md={4} sx={{ display: 'flex' }}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.2 }}
            style={{ width: '100%', display: 'flex' }}
          >
            <Card
              sx={{
                width: '100%',
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
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
              <CardContent 
                sx={{ 
                  p: { xs: 2.5, sm: 3 },
                  textAlign: 'center',
                  display: 'flex',
                  flexDirection: 'column',
                  flex: 1,
                  height: '100%',
                }}
              >
                <Box
                  sx={{
                    p: 1.5,
                    borderRadius: 1.5,
                    background: alpha(theme.palette.warning.main, 0.1),
                    color: theme.palette.warning.main,
                    display: 'inline-flex',
                    mb: 2,
                    mx: 'auto',
                  }}
                >
                  <AnalyticsIcon sx={{ fontSize: { xs: 22, sm: 24 } }} />
                </Box>
                <Typography 
                  variant="h6" 
                  fontWeight={600} 
                  mb={1}
                  sx={{ 
                    fontSize: { xs: '0.9375rem', sm: '1rem' },
                    minHeight: { xs: '24px', sm: '28px' },
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  Sync Agency Analytics Data
                </Typography>
                <Typography 
                  variant="body2" 
                  color="text.secondary" 
                  mb={2}
                  sx={{ 
                    fontSize: { xs: '0.8125rem', sm: '0.875rem' },
                    lineHeight: 1.6,
                    flex: 1,
                    display: 'flex',
                    alignItems: 'center',
                    minHeight: { xs: '48px', sm: '56px' },
                  }}
                >
                  Sync Agency Analytics campaigns and quarterly ranking data. Includes Google rankings, Bing rankings, search volume, and competition metrics.
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, mt: 'auto' }}>
                  <Tooltip 
                    title="New Sync: Only syncs campaigns that don't exist in the database. Use for regular operations." 
                    arrow
                    placement="top"
                  >
                    <Button
                      variant="outlined"
                      fullWidth
                      size="small"
                      onClick={() => handleSyncAgencyAnalytics('new')}
                      disabled={isLoading && currentJob?.sync_type === 'sync_agency_analytics'}
                      sx={{
                        borderRadius: 1.5,
                        px: 1.5,
                        py: 0.75,
                        fontSize: { xs: '0.75rem', sm: '0.8125rem' },
                        fontWeight: 600,
                        borderColor: theme.palette.warning.main,
                        color: theme.palette.warning.main,
                        '&:hover': {
                          borderColor: theme.palette.warning.dark,
                          bgcolor: alpha(theme.palette.warning.main, 0.05),
                        },
                      }}
                    >
                      New Sync
                    </Button>
                  </Tooltip>
                  <Tooltip 
                    title="Complete Sync: Syncs all campaigns, rankings, and keywords. May take >2 hours. Use for initial onboarding or full refresh." 
                    arrow
                    placement="top"
                  >
                    <Button
                      variant="contained"
                      fullWidth
                      size="small"
                      onClick={() => handleSyncAgencyAnalytics('complete')}
                      disabled={isLoading && currentJob?.sync_type === 'sync_agency_analytics'}
                      startIcon={
                        isLoading && currentJob?.sync_type === 'sync_agency_analytics' ? (
                          <CircularProgress size={14} thickness={4} sx={{ color: 'white' }} />
                        ) : (
                          <AnalyticsIcon sx={{ fontSize: 14 }} />
                        )
                      }
                      sx={{
                        borderRadius: 1.5,
                        px: 1.5,
                        py: 0.75,
                        fontSize: { xs: '0.75rem', sm: '0.8125rem' },
                        fontWeight: 600,
                        bgcolor: theme.palette.warning.main,
                        boxShadow: 'none',
                        '&:hover': {
                          bgcolor: theme.palette.warning.dark,
                          boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
                        },
                      }}
                    >
                      {isLoading && currentJob?.sync_type === 'sync_agency_analytics' ? 'Syncing...' : 'Complete'}
                    </Button>
                  </Tooltip>
                </Box>
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


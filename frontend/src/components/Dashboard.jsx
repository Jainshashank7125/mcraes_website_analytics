import { useEffect } from 'react'
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  CircularProgress,
  Button,
  Paper,
  alpha,
  useTheme
} from '@mui/material'
import {
  Business as BusinessIcon,
  Article as ArticleIcon,
  ChatBubble as ChatBubbleIcon,
  ArrowForward as ArrowForwardIcon,
  TrendingUp as TrendingUpIcon,
  Assessment as AssessmentIcon
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useAuth } from '../contexts/AuthContext'
import { useSyncStatus } from '../hooks/useSync'
import { useSyncStatus as useSyncStatusContext } from '../contexts/SyncStatusContext'
import {
  Sync as SyncIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  HourglassEmpty as HourglassEmptyIcon,
} from '@mui/icons-material'
import { Chip, LinearProgress } from '@mui/material'

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
}

const cardVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: {
      type: 'spring',
      stiffness: 100,
      damping: 15
    }
  }
}

const statCards = [
  {
    key: 'clients',
    icon: BusinessIcon,
    color: '#0f172a',
    gradient: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
    bgGradient: 'linear-gradient(135deg, rgba(15, 23, 42, 0.05) 0%, rgba(30, 41, 59, 0.05) 100%)',
    route: '/clients',
    label: 'Clients',
    action: 'View Details'
  },
  {
    key: 'prompts',
    icon: ArticleIcon,
    color: '#3b82f6',
    gradient: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
    bgGradient: 'linear-gradient(135deg, rgba(59, 130, 246, 0.05) 0%, rgba(37, 99, 235, 0.05) 100%)',
    route: '/data',
    label: 'Prompts',
    action: 'View Details'
  },
  {
    key: 'responses',
    icon: ChatBubbleIcon,
    color: '#10b981',
    gradient: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
    bgGradient: 'linear-gradient(135deg, rgba(16, 185, 129, 0.05) 0%, rgba(5, 150, 105, 0.05) 100%)',
    route: '/analytics',
    label: 'Responses',
    action: 'View Analytics'
  }
]

function Dashboard() {
  const navigate = useNavigate()
  const theme = useTheme()
  const { isAuthenticated, loading: authLoading } = useAuth()
  
  // Use React Query hook for sync status
  const { data: status, isLoading: loading } = useSyncStatus({
    enabled: isAuthenticated,
  })
  
  // Get active sync jobs from context
  const { activeJobs } = useSyncStatusContext()

  useEffect(() => {
    // Redirect to login if not authenticated
    if (!authLoading && !isAuthenticated) {
      navigate('/login', { replace: true })
      return
    }
  }, [isAuthenticated, authLoading, navigate])

  const getValue = (key) => {
    const mapping = {
      clients: status?.clients_count || 0,
      prompts: status?.prompts_count || 0,
      responses: status?.responses_count || 0
    }
    return mapping[key] || 0
  }

  // Show loading while checking authentication or loading data
  if (authLoading || loading) {
    return (
      <Box 
        display="flex" 
        justifyContent="center" 
        alignItems="center" 
        minHeight="50vh"
      >
        <CircularProgress size={40} thickness={4} />
      </Box>
    )
  }

  // Don't render if not authenticated (will redirect)
  if (!isAuthenticated) {
    return null
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      <Box>
        <Box mb={4}>
          <Typography 
            variant="h4" 
            fontWeight={700} 
            mb={1}
            sx={{
              fontSize: '1.75rem',
              letterSpacing: '-0.02em',
            }}
          >
            Dashboard Overview
          </Typography>
          <Typography 
            variant="body1" 
            color="text.secondary"
          >
            Monitor your brand performance and track insights across all platforms
          </Typography>
        </Box>

        <Grid container spacing={2.5} sx={{ mb: 4 }}>
          {statCards.map((card, index) => {
            const IconComponent = card.icon
            const value = getValue(card.key)
            
            return (
              <Grid item xs={12} sm={6} md={4} key={card.key} component={motion.div} variants={cardVariants}>
                <Card
                  sx={{
                    height: '100%',
                    cursor: 'pointer',
                    background: '#FFFFFF',
                    border: `1px solid ${theme.palette.divider}`,
                    borderRadius: 2,
                    boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                    position: 'relative',
                    overflow: 'hidden',
                    transition: 'all 0.2s ease-in-out',
                    '&:before': {
                      content: '""',
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      width: '4px',
                      height: '100%',
                      backgroundColor: card.color,
                    },
                    '&:hover': {
                      boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                      transform: 'translateY(-2px)',
                      borderColor: alpha(card.color, 0.3),
                    },
                  }}
                  onClick={() => navigate(card.route)}
                >
                  <CardContent sx={{ p: 2.5 }}>
                    <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                      <Box
                        sx={{
                          p: 1,
                          borderRadius: 1.5,
                          background: alpha(card.color, 0.1),
                          color: card.color,
                        }}
                      >
                        <IconComponent sx={{ fontSize: 20 }} />
                      </Box>
                      <ArrowForwardIcon 
                        sx={{ 
                          color: 'text.secondary',
                          fontSize: 16,
                          opacity: 0.4,
                          transition: 'all 0.2s',
                          '.MuiCard-root:hover &': {
                            transform: 'translateX(2px)',
                            opacity: 1,
                            color: card.color,
                          }
                        }} 
                      />
                    </Box>
                    <Typography 
                      variant="h4" 
                      fontWeight={700}
                      sx={{ 
                        mb: 0.5,
                        fontSize: '2rem',
                        letterSpacing: '-0.02em',
                        color: 'text.primary',
                      }}
                    >
                      {value.toLocaleString()}
                    </Typography>
                    <Typography 
                      variant="body2" 
                      color="text.secondary"
                      sx={{ 
                        fontWeight: 500,
                        fontSize: '0.875rem',
                      }}
                    >
                      {card.label}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            )
          })}
        </Grid>

        {/* Sync Status Card */}
        {activeJobs && activeJobs.length > 0 && (
          <motion.div variants={cardVariants} style={{ marginBottom: theme.spacing(2.5) }}>
            <Card
              sx={{
                borderRadius: 2,
                border: `1px solid ${theme.palette.divider}`,
                boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                bgcolor: alpha(theme.palette.info.main, 0.05),
              }}
            >
              <CardContent sx={{ p: 2.5 }}>
                <Box display="flex" alignItems="center" gap={1.5} mb={2}>
                  <SyncIcon sx={{ color: theme.palette.info.main, fontSize: 24 }} />
                  <Typography variant="h6" fontWeight={600} sx={{ fontSize: '1rem' }}>
                    Current Sync Status
                  </Typography>
                </Box>
                {activeJobs.map((job) => {
                  const syncTypeLabels = {
                    'sync_all': 'Scrunch Data',
                    'sync_ga4': 'GA4 Data',
                    'sync_agency_analytics': 'Agency Analytics',
                  }
                  const syncLabel = syncTypeLabels[job.sync_type] || job.sync_type
                  
                  return (
                    <Box key={job.job_id} sx={{ mb: 2, '&:last-child': { mb: 0 } }}>
                      <Box display="flex" alignItems="center" justifyContent="space-between" mb={1}>
                        <Typography variant="body2" fontWeight={600} sx={{ fontSize: '0.875rem' }}>
                          {syncLabel} Sync
                        </Typography>
                        <Chip
                          label={job.status === 'running' ? 'In Progress' : 'Pending'}
                          size="small"
                          color={job.status === 'running' ? 'primary' : 'default'}
                          icon={job.status === 'running' ? <HourglassEmptyIcon sx={{ fontSize: 14 }} /> : <HourglassEmptyIcon sx={{ fontSize: 14 }} />}
                          sx={{ fontSize: '0.75rem', height: 24 }}
                        />
                      </Box>
                      {job.current_step && (
                        <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.75rem', display: 'block', mb: 1 }}>
                          {job.current_step}
                        </Typography>
                      )}
                      {job.progress > 0 && (
                        <LinearProgress
                          variant="determinate"
                          value={job.progress}
                          sx={{
                            borderRadius: 1,
                            height: 6,
                            bgcolor: alpha(theme.palette.info.main, 0.1),
                            '& .MuiLinearProgress-bar': {
                              bgcolor: theme.palette.info.main,
                            },
                          }}
                        />
                      )}
                    </Box>
                  )
                })}
              </CardContent>
            </Card>
          </motion.div>
        )}

        <motion.div variants={cardVariants}>
          <Card
            sx={{
              borderRadius: 2,
              border: `1px solid ${theme.palette.divider}`,
              boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
            }}
          >
            <CardContent sx={{ p: 2.5 }}>
              <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                <Box>
                  <Typography 
                    variant="h6" 
                    fontWeight={600} 
                    mb={0.5}
                    sx={{ fontSize: '1rem' }}
                  >
                    Quick Actions
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.875rem' }}>
                    Access frequently used features
                  </Typography>
                </Box>
                <TrendingUpIcon sx={{ fontSize: 24, color: 'text.secondary', opacity: 0.3 }} />
              </Box>
              <Box display="flex" gap={1.5} flexWrap="wrap">
                <Button 
                  variant="contained" 
                  size="small"
                  onClick={() => navigate('/clients')}
                  sx={{
                    px: 2,
                    py: 0.75,
                    fontWeight: 600,
                    borderRadius: 1.5,
                    textTransform: 'none',
                    fontSize: '0.875rem',
                    boxShadow: 'none',
                    '&:hover': {
                      boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
                    },
                  }}
                >
                  View Clients
                </Button>
                <Button 
                  variant="outlined" 
                  size="small"
                  onClick={() => navigate('/agency-analytics')}
                  sx={{
                    px: 2,
                    py: 0.75,
                    fontWeight: 600,
                    borderRadius: 1.5,
                    textTransform: 'none',
                    fontSize: '0.875rem',
                    borderColor: theme.palette.divider,
                    '&:hover': {
                      borderColor: theme.palette.divider,
                      bgcolor: alpha(theme.palette.primary.main, 0.05),
                    },
                  }}
                >
                  View Analytics
                </Button>
                <Button 
                  variant="outlined" 
                  size="small"
                  onClick={() => navigate('/reporting')}
                  startIcon={<AssessmentIcon sx={{ fontSize: 16 }} />}
                  sx={{
                    px: 2,
                    py: 0.75,
                    fontWeight: 600,
                    borderRadius: 1.5,
                    textTransform: 'none',
                    fontSize: '0.875rem',
                    borderColor: theme.palette.divider,
                    '&:hover': {
                      borderColor: theme.palette.divider,
                      bgcolor: alpha(theme.palette.primary.main, 0.05),
                    },
                  }}
                >
                  Reporting Dashboard
                </Button>
                <Button 
                  variant="outlined" 
                  size="small"
                  onClick={() => navigate('/sync')}
                  sx={{
                    px: 2,
                    py: 0.75,
                    fontWeight: 600,
                    borderRadius: 1.5,
                    textTransform: 'none',
                    fontSize: '0.875rem',
                    borderColor: theme.palette.divider,
                    '&:hover': {
                      borderColor: theme.palette.divider,
                      bgcolor: alpha(theme.palette.primary.main, 0.05),
                    },
                  }}
                >
                  Sync Data
                </Button>
              </Box>
            </CardContent>
          </Card>
        </motion.div>
      </Box>
    </motion.div>
  )
}

export default Dashboard

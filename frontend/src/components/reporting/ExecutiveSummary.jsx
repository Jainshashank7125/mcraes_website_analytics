import React, { useState, useRef, useEffect } from 'react'
import {
  Box,
  Typography,
  Paper,
  Chip,
  useTheme,
  alpha,
  IconButton,
  Grid,
  Card,
  CardContent,
  useMediaQuery,
  Button
} from '@mui/material'
import {
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  ChevronLeft as ChevronLeftIcon,
  ChevronRight as ChevronRightIcon,
  CalendarToday as CalendarTodayIcon,
  AccessTime as AccessTimeIcon,
  TrendingUp as TrendingUpIcon,
  People as PeopleIcon,
  Analytics as AnalyticsIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon
} from '@mui/icons-material'
import { motion, AnimatePresence } from 'framer-motion'

// HighlightCard component with show more functionality
const HighlightCard = ({ highlight, theme, isMobile }) => {
  const [isExpanded, setIsExpanded] = useState(false)
  const [showButton, setShowButton] = useState(false)
  const contentRef = useRef(null)
  const maxHeight = isMobile ? 200 : 250

  useEffect(() => {
    const checkHeight = () => {
      if (contentRef.current) {
        const height = contentRef.current.scrollHeight
        setShowButton(height > maxHeight)
      }
    }
    
    checkHeight()
    // Recheck on window resize
    window.addEventListener('resize', checkHeight)
    return () => window.removeEventListener('resize', checkHeight)
  }, [highlight.content, maxHeight])

  const toggleExpand = () => {
    setIsExpanded(!isExpanded)
  }

  return (
    <Paper
      elevation={0}
      sx={{
        p: { xs: 2.5, sm: 3, md: 4 },
        bgcolor: 'background.paper',
        border: `1px solid ${theme.palette.divider}`,
        borderRadius: 3,
        minHeight: { xs: '200px', sm: '250px' }
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2, flexWrap: 'wrap' }}>
        <Chip
          label={highlight.tag}
          size="small"
          sx={{
            bgcolor: alpha(highlight.tagColor, 0.1),
            color: highlight.tagColor,
            fontWeight: 600,
            fontSize: '0.75rem',
            height: 24
          }}
        />
        <Typography 
          variant="h6" 
          sx={{ 
            fontWeight: 700,
            fontSize: { xs: '1rem', sm: '1.125rem' },
            color: 'text.primary'
          }}
        >
          {highlight.title}
        </Typography>
      </Box>
      
      <Box
        ref={contentRef}
        sx={{
          maxHeight: isExpanded ? 'none' : `${maxHeight}px`,
          overflow: 'hidden',
          position: 'relative',
          transition: 'max-height 0.3s ease-in-out',
          '&::after': showButton && !isExpanded ? {
            content: '""',
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            height: '60px',
            background: `linear-gradient(to bottom, transparent, ${theme.palette.background.paper})`,
            pointerEvents: 'none',
            zIndex: 1
          } : {}
        }}
      >
        {Array.isArray(highlight.content) ? (
          <Box component="ul" sx={{ m: 0, pl: { xs: 2, sm: 2.5 }, listStyle: 'none' }}>
            {highlight.content.map((item, idx) => (
              <Box
                key={idx}
                component="li"
                sx={{
                  position: 'relative',
                  pl: { xs: 1.5, sm: 2 },
                  mb: 1.5,
                  '&:before': {
                    content: '"•"',
                    position: 'absolute',
                    left: 0,
                    color: theme.palette.primary.main,
                    fontWeight: 'bold'
                  }
                }}
              >
                <Typography 
                  variant="body1" 
                  sx={{ 
                    lineHeight: 1.7,
                    fontSize: { xs: '0.875rem', sm: '1rem' },
                    color: 'text.primary'
                  }}
                >
                  {item}
                </Typography>
              </Box>
            ))}
          </Box>
        ) : (
          <Typography 
            variant="body1" 
            sx={{ 
              lineHeight: 1.8,
              fontSize: { xs: '0.875rem', sm: '1rem' },
              color: 'text.primary',
              whiteSpace: 'pre-line'
            }}
          >
            {highlight.content}
          </Typography>
        )}
      </Box>

      {showButton && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2, position: 'relative', zIndex: 2 }}>
          <Button
            onClick={toggleExpand}
            endIcon={isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            sx={{
              color: theme.palette.primary.main,
              textTransform: 'none',
              fontWeight: 600,
              fontSize: { xs: '0.875rem', sm: '0.9375rem' },
              px: 2,
              py: 0.75,
              '&:hover': {
                bgcolor: alpha(theme.palette.primary.main, 0.08)
              }
            }}
          >
            {isExpanded ? 'Show Less' : 'Show More'}
          </Button>
        </Box>
      )}

      {highlight.requiresAttention && (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 2, pt: 2, borderTop: `1px solid ${theme.palette.divider}` }}>
          <Box
            sx={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              bgcolor: theme.palette.warning.main
            }}
          />
          <Typography 
            variant="body2" 
            sx={{ 
              color: theme.palette.warning.main,
              fontWeight: 600,
              fontSize: { xs: '0.875rem', sm: '0.875rem' }
            }}
          >
            Requires Attention
          </Typography>
        </Box>
      )}
    </Paper>
  )
}

export default function ExecutiveSummary({ summary, theme, dashboardData }) {
  const [highlightIndex, setHighlightIndex] = useState(0)
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'))
  const isTablet = useMediaQuery(theme.breakpoints.down('md'))

  if (!summary) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="body1" color="text.secondary"> 
          No executive summary available.
        </Typography>
      </Box>
    )
  }

  const header = summary.header || {}
  const overallStatus = header.overall_status || ''
  
  // Determine status color and icon
  let statusColor = 'default'
  let StatusIcon = CheckCircleIcon
  if (overallStatus.includes('✅')) {
    statusColor = 'success'
    StatusIcon = CheckCircleIcon
  } else if (overallStatus.includes('⚠️')) {
    statusColor = 'warning'
    StatusIcon = WarningIcon
  } else if (overallStatus.includes('🔴')) {
    statusColor = 'error'
    StatusIcon = ErrorIcon
  }

  // Build highlights carousel items
  const highlights = []
  
  if (summary.executive_summary) {
    highlights.push({
      type: 'executive_summary',
      title: 'Executive Summary',
      content: summary.executive_summary,
      tag: 'analytics',
      tagColor: '#ff6b6b',
      requiresAttention: summary.executive_summary.toLowerCase().includes('drop') || 
                        summary.executive_summary.toLowerCase().includes('decline') ||
                        summary.executive_summary.toLowerCase().includes('decrease')
    })
  }

  if (summary.what_worked && summary.what_worked.length > 0) {
    highlights.push({
      type: 'what_worked',
      title: 'What Worked',
      content: summary.what_worked,
      tag: 'success',
      tagColor: '#10b981'
    })
  }

  if (summary.what_to_watch && summary.what_to_watch.length > 0) {
    highlights.push({
      type: 'what_to_watch',
      title: 'What to Watch',
      content: summary.what_to_watch,
      tag: 'warning',
      tagColor: '#f59e0b'
    })
  }

  const handleNextHighlight = () => {
    setHighlightIndex((prev) => (prev + 1) % highlights.length)
  }

  const handlePrevHighlight = () => {
    setHighlightIndex((prev) => (prev - 1 + highlights.length) % highlights.length)
  }

  const currentHighlight = highlights[highlightIndex]

  // Extract key metrics for "At a Glance" section
  const getKeyMetrics = () => {
    const metrics = []
    
    // Try to extract metrics from dashboardData if available
    if (dashboardData?.kpis) {
      if (dashboardData.kpis.avg_session_duration) {
        const duration = dashboardData.kpis.avg_session_duration.value
        const minutes = Math.floor(duration / 60)
        const seconds = Math.floor(duration % 60)
        metrics.push({
          label: 'Session Duration',
          value: `${minutes}m ${seconds}s`,
          icon: AccessTimeIcon
        })
      }
      
      if (dashboardData.kpis.sessions || dashboardData.kpis.users) {
        const value = dashboardData.kpis.sessions?.value || dashboardData.kpis.users?.value || 0
        const formatted = value >= 1000 ? `${(value / 1000).toFixed(1)}k` : value.toString()
        metrics.push({
          label: 'Traffic',
          value: formatted,
          icon: TrendingUpIcon
        })
      }
      
      if (dashboardData.kpis.bounce_rate) {
        metrics.push({
          label: 'Bounce Rate',
          value: `${dashboardData.kpis.bounce_rate.value?.toFixed(1) || 0}%`,
          icon: AnalyticsIcon
        })
      }
      
      if (dashboardData.kpis.conversions) {
        metrics.push({
          label: 'Conversions',
          value: dashboardData.kpis.conversions.value?.toLocaleString() || '0',
          icon: CheckCircleIcon
        })
      }
    }
    
    // Fallback to default metrics if no data available
    if (metrics.length === 0) {
      metrics.push(
        { label: 'Session Duration', value: '2m', icon: AccessTimeIcon },
        { label: 'Traffic', value: '1.2k', icon: TrendingUpIcon },
        { label: 'Users', value: '850', icon: PeopleIcon },
        { label: 'Engagement', value: '68%', icon: AnalyticsIcon }
      )
    }
    
    return metrics.slice(0, 4) // Limit to 4 metrics
  }

  const keyMetrics = getKeyMetrics()

  return (
    <Box sx={{ 
      width: '100%',
      maxWidth: '1200px',
      mx: 'auto',
      px: { xs: 2, sm: 3, md: 4 },
      py: { xs: 2, sm: 3 }
    }}>
      {/* Program Details Section - Light Blue Card */}
      <Paper
        elevation={0}
        sx={{
          p: { xs: 2, sm: 3 },
          mb: { xs: 3, sm: 4 },
          bgcolor: alpha(theme.palette.primary.main, 0.08),
          border: 'none',
          borderRadius: 3,
          background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.1)} 0%, ${alpha(theme.palette.primary.main, 0.05)} 100%)`
        }}
      >
        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, alignItems: { xs: 'flex-start', sm: 'center' }, gap: 2 }}>
          <Box sx={{ flex: 1 }}>
            <Typography 
              variant="h4" 
              component="h1" 
              sx={{ 
                fontWeight: 700,
                fontSize: { xs: '1.75rem', sm: '2rem', md: '2.25rem' },
                mb: 0.5,
                color: 'text.primary'
              }}
            >
              {header.client_name || 'Client'}
            </Typography>
            <Typography 
              variant="h6" 
              sx={{ 
                color: theme.palette.primary.main,
                fontWeight: 500,
                fontSize: { xs: '0.875rem', sm: '1rem' },
                mb: 1
              }}
            >
              {header.program_name || 'Digital Marketing Program'}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
              <CalendarTodayIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
              <Typography 
                variant="body2" 
                sx={{ 
                  color: 'text.secondary',
                  fontSize: { xs: '0.75rem', sm: '0.875rem' }
                }}
              >
                Reporting Period: {header.reporting_period || 'N/A'}
              </Typography>
            </Box>
          </Box>
          {overallStatus && statusColor !== 'warning' && statusColor !== 'error' && (
            <Chip
              icon={<StatusIcon />}
              label={overallStatus.replace(/[✅⚠️🔴]/g, '').trim()}
              color={statusColor}
              sx={{ fontWeight: 600 }}
            />
          )}
        </Box>
      </Paper>

      {/* Highlights Section with Carousel */}
      {highlights.length > 0 && (
        <Box sx={{ mb: { xs: 4, sm: 5 } }}>
          <Box sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'space-between',
            mb: 2
          }}>
            <Typography 
              variant="h5" 
              sx={{ 
                fontWeight: 700,
                fontSize: { xs: '1.25rem', sm: '1.5rem' },
                color: 'text.primary'
              }}
            >
              Highlights
            </Typography>
            {highlights.length > 1 && (
              <Box sx={{ display: 'flex', gap: 1 }}>
                <IconButton
                  onClick={handlePrevHighlight}
                  disabled={highlights.length <= 1}
                  sx={{
                    color: 'text.secondary',
                    '&:hover': { color: 'primary.main', bgcolor: alpha(theme.palette.primary.main, 0.08) },
                    '&.Mui-disabled': { opacity: 0.3 }
                  }}
                  size="small"
                >
                  <ChevronLeftIcon />
                </IconButton>
                <IconButton
                  onClick={handleNextHighlight}
                  disabled={highlights.length <= 1}
                  sx={{
                    color: 'text.secondary',
                    '&:hover': { color: 'primary.main', bgcolor: alpha(theme.palette.primary.main, 0.08) },
                    '&.Mui-disabled': { opacity: 0.3 }
                  }}
                  size="small"
                >
                  <ChevronRightIcon />
                </IconButton>
              </Box>
            )}
          </Box>

          <Box sx={{ position: 'relative', overflow: 'hidden' }}>
            <AnimatePresence mode="wait">
              {currentHighlight && (
                <motion.div
                  key={highlightIndex}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.3 }}
                >
                  <HighlightCard 
                    highlight={currentHighlight} 
                    theme={theme} 
                    isMobile={isMobile}
                  />
                </motion.div>
              )}
            </AnimatePresence>
          </Box>

          {/* Carousel Indicators */}
          {highlights.length > 1 && (
            <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1, mt: 2 }}>
              {highlights.map((_, index) => (
                <Box
                  key={index}
                  onClick={() => setHighlightIndex(index)}
                  sx={{
                    width: 8,
                    height: 8,
                    borderRadius: '50%',
                    bgcolor: index === highlightIndex 
                      ? theme.palette.primary.main 
                      : alpha(theme.palette.primary.main, 0.3),
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    '&:hover': {
                      bgcolor: index === highlightIndex 
                        ? theme.palette.primary.dark 
                        : alpha(theme.palette.primary.main, 0.5)
                    }
                  }}
                />
              ))}
            </Box>
          )}
        </Box>
      )}

      {/* At a Glance Section */}
      {/* <Box sx={{ mb: { xs: 4, sm: 5 } }}>
        <Typography 
          variant="h5" 
          sx={{ 
            fontWeight: 700,
            fontSize: { xs: '1.25rem', sm: '1.5rem' },
            mb: 3,
            color: 'text.primary'
          }}
        >
          At a Glance
        </Typography>
        
        <Grid container spacing={2}>
          {keyMetrics.map((metric, index) => {
            const IconComponent = metric.icon
            return (
              <Grid item xs={6} sm={4} md={3} key={index}>
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.1 }}
                >
                  <Card
                    elevation={0}
                    sx={{
                      bgcolor: 'background.paper',
                      border: `1px solid ${theme.palette.divider}`,
                      borderRadius: 2,
                      height: '100%',
                      transition: 'all 0.2s ease',
                      '&:hover': {
                        boxShadow: `0 4px 12px ${alpha(theme.palette.primary.main, 0.15)}`,
                        transform: 'translateY(-2px)'
                      }
                    }}
                  >
                    <CardContent sx={{ p: { xs: 2, sm: 2.5 } }}>
                      <Typography 
                        variant="body2" 
                        sx={{ 
                          color: 'text.secondary',
                          fontSize: { xs: '0.75rem', sm: '0.875rem' },
                          mb: 1,
                          fontWeight: 500
                        }}
                      >
                        {metric.label}
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <IconComponent 
                          sx={{ 
                            fontSize: { xs: 20, sm: 24 },
                            color: theme.palette.primary.main,
                            opacity: 0.7
                          }} 
                        />
                        <Typography 
                          variant="h4" 
                          sx={{ 
                            fontWeight: 700,
                            fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2rem' },
                            color: 'text.primary'
                          }}
                        >
                          {metric.value}
                        </Typography>
                      </Box>
                    </CardContent>
                  </Card>
                </motion.div>
              </Grid>
            )
          })}
        </Grid>
      </Box> */}

    </Box>
  )
}


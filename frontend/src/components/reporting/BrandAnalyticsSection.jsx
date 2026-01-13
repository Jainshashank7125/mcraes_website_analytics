import { Box, Card, CardContent, Grid, Typography } from '@mui/material'
import { motion } from 'framer-motion'
import { KPI_METADATA } from './constants'

export default function BrandAnalyticsSection({ brandAnalytics, theme }) {
  if (!brandAnalytics) {
    return null
  }

  return (
    <>
              <Typography 
                variant="h5" 
                fontWeight={700} 
                sx={{ 
                  mt: 5, 
                  mb: 3,
                  fontSize: '1.5rem',
                  letterSpacing: '-0.02em',
                  color: 'text.primary'
                }}
              >
                Brand Analytics Insights
              </Typography>

              <Grid container spacing={2.5} sx={{ mb: 3 }}>
                {/* Platform Distribution - Donut Chart */}
                {brandAnalytics.platform_distribution && Object.keys(brandAnalytics.platform_distribution).length > 0 && (
                  <Grid item xs={12} md={6}>
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.5, delay: 0.7 }}
                    >
                      <Card
                        sx={{
                          borderRadius: 2,
                          border: `1px solid ${theme.palette.divider}`,
                          boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                        }}
                      >
                        <CardContent sx={{ p: 3 }}>
                          <Typography variant="h6" mb={3} fontWeight={600} sx={{ fontSize: '1rem' }}>
                            Platform Distribution
                          </Typography>
                          <ResponsiveContainer width="100%" height={300}>
                            <PieChart>
                              <Pie
                                data={Object.entries(brandAnalytics.platform_distribution).map(([name, value]) => ({
                                  name,
                                  value
                                }))}
                                cx="50%"
                                cy="50%"
                                labelLine={false}
                                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                                outerRadius={100}
                                innerRadius={60}
                                fill="#8884d8"
                                dataKey="value"
                              >
                                {Object.entries(brandAnalytics.platform_distribution).map((entry, index) => {
                                  const softColors = [
                                    'rgba(0, 122, 255, 0.5)',      // Blue
                                    'rgba(52, 199, 89, 0.5)',      // Green
                                    'rgba(255, 149, 0, 0.5)',      // Orange
                                    'rgba(255, 45, 85, 0.5)',      // Red
                                    'rgba(88, 86, 214, 0.5)',      // Purple
                                    'rgba(255, 193, 7, 0.5)',      // Yellow
                                    'rgba(90, 200, 250, 0.5)',     // Light Blue
                                  ]
                                  return <Cell key={`cell-${index}`} fill={softColors[index % softColors.length]} />
                                })}
                              </Pie>
                              <Tooltip 
                                contentStyle={{ 
                                  borderRadius: '8px', 
                                  border: 'none', 
                                  boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                                  backgroundColor: '#FFFFFF'
                                }}
                              />
                            </PieChart>
                          </ResponsiveContainer>
                        </CardContent>
                      </Card>
                    </motion.div>
                  </Grid>
                )}

                {/* Stage Distribution - Pie Chart */}
                {brandAnalytics.stage_distribution && Object.keys(brandAnalytics.stage_distribution).length > 0 && (
                  <Grid item xs={12} md={6}>
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.5, delay: 0.8 }}
                    >
                      <Card
                        sx={{
                          borderRadius: 2,
                          border: `1px solid ${theme.palette.divider}`,
                          boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                        }}
                      >
                        <CardContent sx={{ p: 3 }}>
                          <Typography variant="h6" mb={3} fontWeight={600} sx={{ fontSize: '1rem' }}>
                            Funnel Stage Distribution
                          </Typography>
                          <ResponsiveContainer width="100%" height={300}>
                            <PieChart>
                              <Pie
                                data={Object.entries(brandAnalytics.stage_distribution).map(([name, value]) => ({
                                  name,
                                  value
                                }))}
                                cx="50%"
                                cy="50%"
                                labelLine={false}
                                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                                outerRadius={100}
                                fill="#8884d8"
                                dataKey="value"
                              >
                                {Object.entries(brandAnalytics.stage_distribution).map((entry, index) => {
                                  const softColors = [
                                    'rgba(59, 130, 246, 0.6)',      // Light blue
                                    'rgba(20, 184, 166, 0.6)',      // Teal/Green
                                    'rgba(251, 146, 60, 0.6)',      // Orange
                                    'rgba(239, 68, 68, 0.6)',       // Orange-red
                                    'rgba(88, 86, 214, 0.6)',       // Purple
                                  ]
                                  return <Cell key={`cell-${index}`} fill={softColors[index % softColors.length]} />
                                })}
                              </Pie>
                              <Tooltip 
                                contentStyle={{ 
                                  borderRadius: '8px', 
                                  border: 'none', 
                                  boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                                  backgroundColor: '#FFFFFF'
                                }}
                              />
                            </PieChart>
                          </ResponsiveContainer>
                        </CardContent>
                      </Card>
                    </motion.div>
                  </Grid>
                )}

                {/* Brand Sentiment - Donut Chart */}
                {brandAnalytics.brand_sentiment && Object.keys(brandAnalytics.brand_sentiment).filter(key => brandAnalytics.brand_sentiment[key] > 0).length > 0 && (
                  <Grid item xs={12} md={6}>
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.5, delay: 0.9 }}
                    >
                      <Card
                        sx={{
                          borderRadius: 2,
                          border: `1px solid ${theme.palette.divider}`,
                          boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                        }}
                      >
                        <CardContent sx={{ p: 3 }}>
                          <Typography variant="h6" mb={3} fontWeight={600} sx={{ fontSize: '1rem' }}>
                            Brand Sentiment
                          </Typography>
                          <ResponsiveContainer width="100%" height={300}>
                            <PieChart>
                              <Pie
                                data={Object.entries(brandAnalytics.brand_sentiment)
                                  .filter(([name, value]) => value > 0)
                                  .map(([name, value]) => ({
                                    name: name.charAt(0).toUpperCase() + name.slice(1),
                                    value
                                  }))}
                                cx="50%"
                                cy="50%"
                                labelLine={false}
                                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                                outerRadius={100}
                                innerRadius={60}
                                fill="#8884d8"
                                dataKey="value"
                              >
                                {Object.entries(brandAnalytics.brand_sentiment)
                                  .filter(([name, value]) => value > 0)
                                  .map((entry, index) => {
                                    const colors = {
                                      positive: 'rgba(20, 184, 166, 0.6)',      // Teal/Green
                                      negative: 'rgba(239, 68, 68, 0.6)',       // Orange-red
                                      neutral: 'rgba(251, 146, 60, 0.6)',       // Orange
                                      null: 'rgba(88, 86, 214, 0.6)',           // Purple
                                    }
                                    const key = entry[0].toLowerCase()
                                    return <Cell key={`cell-${index}`} fill={colors[key] || 'rgba(88, 86, 214, 0.6)'} />
                                  })}
                              </Pie>
                              <Tooltip 
                                contentStyle={{ 
                                  borderRadius: '8px', 
                                  border: 'none', 
                                  boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                                  backgroundColor: '#FFFFFF'
                                }}
                              />
                            </PieChart>
                          </ResponsiveContainer>
                        </CardContent>
                      </Card>
                    </motion.div>
                  </Grid>
                )}

              </Grid>

              {/* Top Competitors - List */}
              {brandAnalytics.top_competitors && brandAnalytics.top_competitors.length > 0 && (
                <Grid container spacing={2.5} sx={{ mb: 3 }}>
                  <Grid item xs={12} md={6}>
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.5, delay: 1.1 }}
                    >
                      <Card
                        sx={{
                          borderRadius: 2,
                          border: `1px solid ${theme.palette.divider}`,
                          boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                        }}
                      >
                        <CardContent sx={{ p: 3 }}>
                          <Typography variant="h6" mb={2} fontWeight={600} sx={{ fontSize: '1rem' }}>
                            Top Competitors
                          </Typography>
                          <Box display="flex" flexDirection="column" gap={1.5}>
                            {brandAnalytics.top_competitors.slice(0, 10).map((comp, idx) => (
                              <Paper
                                key={idx}
                                sx={{
                                  p: 1.5,
                                  borderLeft: `3px solid ${theme.palette.primary.main}`,
                                  borderRadius: 1.5,
                                  transition: 'all 0.2s',
                                  '&:hover': {
                                    transform: 'translateX(2px)',
                                    boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
                                  },
                                }}
                              >
                                <Box display="flex" justifyContent="space-between" alignItems="center">
                                  <Box display="flex" alignItems="center" gap={1}>
                                    <Chip
                                      label={`#${idx + 1}`}
                                      size="small"
                                      sx={{
                                        bgcolor: theme.palette.primary.main,
                                        color: 'white',
                                        fontWeight: 700,
                                        fontSize: '0.7rem',
                                        height: 20,
                                        minWidth: 28,
                                      }}
                                    />
                                    <Typography variant="body2" fontWeight={600} sx={{ fontSize: '0.875rem' }}>
                                      {comp.name}
                                    </Typography>
                                  </Box>
                                  <Typography variant="body2" fontWeight={700} color="primary.main" sx={{ fontSize: '0.875rem' }}>
                                    {comp.count.toLocaleString()}
                                  </Typography>
                                </Box>
                              </Paper>
                            ))}
                          </Box>
                        </CardContent>
                      </Card>
                    </motion.div>
                  </Grid>

                  {/* Top Topics - Chips List */}
                  {brandAnalytics.top_topics && brandAnalytics.top_topics.length > 0 && (
                    <Grid item xs={12} md={6}>
                      <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5, delay: 1.2 }}
                      >
                        <Card
                          sx={{
                            borderRadius: 2,
                            border: `1px solid ${theme.palette.divider}`,
                            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                          }}
                        >
                          <CardContent sx={{ p: 3 }}>
                            <Typography variant="h6" mb={2} fontWeight={600} sx={{ fontSize: '1rem' }}>
                              Top Topics
                            </Typography>
                            <Box display="flex" flexWrap="wrap" gap={1}>
                              {brandAnalytics.top_topics.slice(0, 20).map((topic, idx) => (
                                <Chip
                                  key={idx}
                                  label={`${topic.topic} (${topic.count})`}
                                  size="small"
                                  sx={{
                                    bgcolor: alpha(theme.palette.primary.main, 0.08),
                                    color: 'primary.main',
                                    fontWeight: 600,
                                    fontSize: '0.75rem',
                                    height: 28,
                                    '&:hover': {
                                      bgcolor: alpha(theme.palette.primary.main, 0.15),
                                    },
                                  }}
                                />
                              ))}
                            </Box>
                          </CardContent>
                        </Card>
                      </motion.div>
                    </Grid>
                  )}
                </Grid>
              )}
            </>
          )}

          {/* All KPI Blocks - Moved Below Charts */}
          {/* GA4 Summary Cards - Key Metrics */}
          {(dashboardData?.kpis?.users || dashboardData?.chart_data?.ga4_traffic_overview) && (
            <>
              <Typography 
                variant="h5" 
                fontWeight={700} 
                sx={{ 
                  mt: 5, 
                  mb: 3,
                  fontSize: '1.5rem',
                  letterSpacing: '-0.02em',
                  color: 'text.primary'
                }}
              >
                Google Analytics 4 - Key Metrics
              </Typography>
              
              {/* GA4 Summary Cards - Key Metrics */}
              <Grid container spacing={2.5} sx={{ mb: 4 }}>
                {/* Total Users */}
                {dashboardData?.kpis?.users && (
                  <Grid item xs={12} sm={6} md={3}>
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3, delay: 0.1 }}
                    >
                      <Card
                        sx={{
                          background: '#FFFFFF',
                          border: `1px solid ${theme.palette.divider}`,
                          borderRadius: 2,
                          boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                          transition: 'all 0.2s ease-in-out',
                          '&:hover': {
                            boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                          },
                        }}
                      >
                        <CardContent sx={{ p: 2.5 }}>
                          <Box display="flex" alignItems="center" justifyContent="space-between" mb={1.5}>
                            <Typography 
                              variant="body2" 
                              color="text.secondary"
                              sx={{ fontSize: '0.875rem', fontWeight: 500 }}
                            >
                              Total Users
                            </Typography>
                            <IconButton size="small" sx={{ p: 0.5 }}>
                              <TrendingUpIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
                            </IconButton>
                          </Box>
                          <Typography 
                            variant="h4" 
                            fontWeight={700}
                            sx={{ 
                              fontSize: '1.75rem',
                              letterSpacing: '-0.02em',
                              mb: 1,
                              color: 'text.primary'
                            }}
                          >
                            {(() => {
                              const value = dashboardData.kpis.users.value || 0
                              if (value >= 1000) {
                                return `${(value / 1000).toFixed(1)}K`
                              }
                              return value.toLocaleString()
                            })()}
                          </Typography>
                          {dashboardData.kpis.users.change !== undefined && dashboardData.kpis.users.change !== null && (
                            <Box display="flex" alignItems="center" gap={0.5}>
                              {dashboardData.kpis.users.change >= 0 ? (
                                <TrendingUpIcon sx={{ fontSize: 14, color: '#34A853' }} />
                              ) : (
                                <TrendingDownIcon sx={{ fontSize: 14, color: '#EA4335' }} />
                              )}
                              <Typography 
                                variant="body2" 
                                sx={{ 
                                  fontSize: '0.875rem',
                                  fontWeight: 600,
                                  color: dashboardData.kpis.users.change >= 0 ? '#34A853' : '#EA4335'
                                }}
                              >
                                {Math.abs(dashboardData.kpis.users.change).toFixed(1)}%
                              </Typography>
                            </Box>
                          )}
                        </CardContent>
                      </Card>
                    </motion.div>
                  </Grid>
                )}

                {/* Sessions */}
                {dashboardData?.kpis?.sessions && (
                  <Grid item xs={12} sm={6} md={3}>
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3, delay: 0.15 }}
                    >
                      <Card
                        sx={{
                          background: '#FFFFFF',
                          border: `1px solid ${theme.palette.divider}`,
                          borderRadius: 2,
                          boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                          transition: 'all 0.2s ease-in-out',
                          '&:hover': {
                            boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                          },
                        }}
                      >
                        <CardContent sx={{ p: 2.5 }}>
                          <Box display="flex" alignItems="center" justifyContent="space-between" mb={1.5}>
                            <Typography 
                              variant="body2" 
                              color="text.secondary"
                              sx={{ fontSize: '0.875rem', fontWeight: 500 }}
                            >
                              Sessions
                            </Typography>
                            <IconButton size="small" sx={{ p: 0.5 }}>
                              <BarChartIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
                            </IconButton>
                          </Box>
                          <Typography 
                            variant="h4" 
                            fontWeight={700}
                            sx={{ 
                              fontSize: '1.75rem',
                              letterSpacing: '-0.02em',
                              mb: 1,
                              color: 'text.primary'
                            }}
                          >
                            {(() => {
                              const value = dashboardData.kpis.sessions.value || 0
                              if (value >= 1000) {
                                return `${(value / 1000).toFixed(1)}K`
                              }
                              return value.toLocaleString()
                            })()}
                          </Typography>
                          {dashboardData.kpis.sessions.change !== undefined && dashboardData.kpis.sessions.change !== null && (
                            <Box display="flex" alignItems="center" gap={0.5}>
                              {dashboardData.kpis.sessions.change >= 0 ? (
                                <TrendingUpIcon sx={{ fontSize: 14, color: '#34A853' }} />
                              ) : (
                                <TrendingDownIcon sx={{ fontSize: 14, color: '#EA4335' }} />
                              )}
                              <Typography 
                                variant="body2" 
                                sx={{ 
                                  fontSize: '0.875rem',
                                  fontWeight: 600,
                                  color: dashboardData.kpis.sessions.change >= 0 ? '#34A853' : '#EA4335'
                                }}
                              >
                                {Math.abs(dashboardData.kpis.sessions.change).toFixed(1)}%
                              </Typography>
                            </Box>
                          )}
                        </CardContent>
                      </Card>
                    </motion.div>
                  </Grid>
                )}

                {/* New Users */}
                {dashboardData?.kpis?.new_users && (
                  <Grid item xs={12} sm={6} md={3}>
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3, delay: 0.2 }}
                    >
                      <Card
                        sx={{
                          background: '#FFFFFF',
                          border: `1px solid ${theme.palette.divider}`,
                          borderRadius: 2,
                          boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                          transition: 'all 0.2s ease-in-out',
                          '&:hover': {
                            boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                          },
                        }}
                      >
                        <CardContent sx={{ p: 2.5 }}>
                          <Box display="flex" alignItems="center" justifyContent="space-between" mb={1.5}>
                            <Typography 
                              variant="body2" 
                              color="text.secondary"
                              sx={{ fontSize: '0.875rem', fontWeight: 500 }}
                            >
                              New users
                            </Typography>
                            <IconButton size="small" sx={{ p: 0.5 }}>
                              <PersonAddIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
                            </IconButton>
                          </Box>
                          <Typography 
                            variant="h4" 
                            fontWeight={700}
                            sx={{ 
                              fontSize: '1.75rem',
                              letterSpacing: '-0.02em',
                              mb: 1,
                              color: 'text.primary'
                            }}
                          >
                            {(() => {
                              const value = dashboardData.kpis.new_users.value || 0
                              if (value >= 1000) {
                                return `${(value / 1000).toFixed(1)}K`
                              }
                              return value.toLocaleString()
                            })()}
                          </Typography>
                          {dashboardData.kpis.new_users.change !== undefined && dashboardData.kpis.new_users.change !== null && (
                            <Box display="flex" alignItems="center" gap={0.5}>
                              {dashboardData.kpis.new_users.change >= 0 ? (
                                <TrendingUpIcon sx={{ fontSize: 14, color: '#34A853' }} />
                              ) : (
                                <TrendingDownIcon sx={{ fontSize: 14, color: '#EA4335' }} />
                              )}
                              <Typography 
                                variant="body2" 
                                sx={{ 
                                  fontSize: '0.875rem',
                                  fontWeight: 600,
                                  color: dashboardData.kpis.new_users.change >= 0 ? '#34A853' : '#EA4335'
                                }}
                              >
                                {Math.abs(dashboardData.kpis.new_users.change).toFixed(1)}%
                              </Typography>
                            </Box>
                          )}
                        </CardContent>
                      </Card>
                    </motion.div>
                  </Grid>
                )}

                {/* Conversions or Revenue */}
                {(dashboardData?.kpis?.conversions || dashboardData?.kpis?.revenue) && (
                  <Grid item xs={12} sm={6} md={3}>
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3, delay: 0.25 }}
                    >
                      <Card
                        sx={{
                          background: '#FFFFFF',
                          border: `1px solid ${theme.palette.divider}`,
                          borderRadius: 2,
                          boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                          transition: 'all 0.2s ease-in-out',
                          '&:hover': {
                            boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                          },
                        }}
                      >
                        <CardContent sx={{ p: 2.5 }}>
                          <Box display="flex" alignItems="center" justifyContent="space-between" mb={1.5}>
                            <Typography 
                              variant="body2" 
                              color="text.secondary"
                              sx={{ fontSize: '0.875rem', fontWeight: 500 }}
                            >
                              {dashboardData.kpis.conversions ? 'Conversions' : 'Revenue'}
                            </Typography>
                            <IconButton size="small" sx={{ p: 0.5 }}>
                              <TrendingUpIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
                            </IconButton>
                          </Box>
                          <Typography 
                            variant="h4" 
                            fontWeight={700}
                            sx={{ 
                              fontSize: '1.75rem',
                              letterSpacing: '-0.02em',
                              mb: 1,
                              color: 'text.primary'
                            }}
                          >
                            {(() => {
                              const kpi = dashboardData.kpis.conversions || dashboardData.kpis.revenue
                              const value = kpi.value || 0
                              if (dashboardData.kpis.revenue) {
                                return `$${value.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
                              }
                              if (value >= 1000) {
                                return `${(value / 1000).toFixed(1)}K`
                              }
                              return value.toLocaleString()
                            })()}
                          </Typography>
                          {(() => {
                            const kpi = dashboardData.kpis.conversions || dashboardData.kpis.revenue
                            return kpi.change !== undefined && kpi.change !== null && (
                              <Box display="flex" alignItems="center" gap={0.5}>
                                {kpi.change >= 0 ? (
                                  <TrendingUpIcon sx={{ fontSize: 14, color: '#34A853' }} />
                                ) : (
                                  <TrendingDownIcon sx={{ fontSize: 14, color: '#EA4335' }} />
                                )}
                                <Typography 
                                  variant="body2" 
                                  sx={{ 
                                    fontSize: '0.875rem',
                                    fontWeight: 600,
                                    color: kpi.change >= 0 ? '#34A853' : '#EA4335'
                                  }}
                                >
                                  {Math.abs(kpi.change).toFixed(1)}%
                                </Typography>
                              </Box>
                            )
                          })()}
                        </CardContent>
                      </Card>
                    </motion.div>
                  </Grid>
                )}
              </Grid>

              {/* GA4 Traffic Overview Cards - Additional Metrics */}
              {dashboardData?.chart_data?.ga4_traffic_overview && (
                <Grid container spacing={2.5} sx={{ mb: 4 }}>
                  <Grid item xs={12} md={3}>
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.5, delay: 0.5 }}
                    >
                      <Card
                        sx={{
                          background: 'linear-gradient(135deg, rgba(52, 199, 89, 0.04) 0%, rgba(90, 200, 250, 0.04) 100%)',
                          border: `1px solid ${alpha(theme.palette.success.main, 0.08)}`,
                          borderRadius: 2,
                          boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                        }}
                      >
                        <CardContent sx={{ p: 3 }}>
                          <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                            <Typography 
                              variant="caption" 
                              color="text.secondary"
                              sx={{ fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}
                            >
                              Total Sessions
                            </Typography>
                            <BarChartIcon sx={{ fontSize: 20, color: 'success.main', opacity: 0.6 }} />
                          </Box>
                          <Typography 
                            variant="h3" 
                            fontWeight={700}
                            color="success.main"
                            sx={{ 
                              fontSize: '36px',
                              letterSpacing: '-0.02em',
                              mb: 1,
                            }}
                          >
                            {dashboardData.chart_data.ga4_traffic_overview.sessions.toLocaleString()}
                          </Typography>
                          <Box display="flex" alignItems="center" gap={0.5}>
                            {dashboardData.chart_data.ga4_traffic_overview.sessionsChange >= 0 ? (
                              <TrendingUpIcon sx={{ fontSize: 14, color: 'success.main' }} />
                            ) : (
                              <TrendingDownIcon sx={{ fontSize: 14, color: 'error.main' }} />
                            )}
                            <Typography 
                              variant="body2" 
                              sx={{ 
                                fontSize: '13px',
                                fontWeight: 600,
                                color: dashboardData.chart_data.ga4_traffic_overview.sessionsChange >= 0 ? 'success.main' : 'error.main'
                              }}
                            >
                              {Math.abs(dashboardData.chart_data.ga4_traffic_overview.sessionsChange).toFixed(1)}%
                            </Typography>
                            <Typography 
                              variant="caption" 
                              color="text.secondary"
                              sx={{ fontSize: '12px' }}
                            >
                              vs last period
                            </Typography>
                          </Box>
                        </CardContent>
                      </Card>
                    </motion.div>
                  </Grid>

                  <Grid item xs={12} md={3}>
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.5, delay: 0.6 }}
                    >
                      <Card
                        sx={{
                          background: 'linear-gradient(135deg, rgba(0, 122, 255, 0.04) 0%, rgba(88, 86, 214, 0.04) 100%)',
                          border: `1px solid ${alpha(theme.palette.primary.main, 0.08)}`,
                          borderRadius: 2,
                          boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                        }}
                      >
                        <CardContent sx={{ p: 3 }}>
                          <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                            <Typography 
                              variant="caption" 
                              color="text.secondary"
                              sx={{ fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}
                            >
                              Engaged Sessions
                            </Typography>
                            <PeopleIcon sx={{ fontSize: 20, color: 'primary.main', opacity: 0.6 }} />
                          </Box>
                          <Typography 
                            variant="h3" 
                            fontWeight={700}
                            sx={{ 
                              fontSize: '36px',
                              letterSpacing: '-0.02em',
                              mb: 1,
                            }}
                          >
                            {dashboardData.chart_data.ga4_traffic_overview.engagedSessions.toLocaleString()}
                          </Typography>
                          <Box display="flex" alignItems="center" gap={0.5}>
                            {dashboardData.chart_data.ga4_traffic_overview.engagedSessionsChange >= 0 ? (
                              <TrendingUpIcon sx={{ fontSize: 14, color: 'success.main' }} />
                            ) : (
                              <TrendingDownIcon sx={{ fontSize: 14, color: 'error.main' }} />
                            )}
                            <Typography 
                              variant="body2" 
                              sx={{ 
                                fontSize: '13px',
                                fontWeight: 600,
                                color: dashboardData.chart_data.ga4_traffic_overview.engagedSessionsChange >= 0 ? 'success.main' : 'error.main'
                              }}
                            >
                              {Math.abs(dashboardData.chart_data.ga4_traffic_overview.engagedSessionsChange).toFixed(1)}%
                            </Typography>
                            <Typography 
                              variant="caption" 
                              color="text.secondary"
                              sx={{ fontSize: '12px' }}
                            >
                              vs last period
                            </Typography>
                          </Box>
                        </CardContent>
                      </Card>
                    </motion.div>
                  </Grid>

                  <Grid item xs={12} md={3}>
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.5, delay: 0.7 }}
                    >
                      <Card
                        sx={{
                          background: 'linear-gradient(135deg, rgba(255, 149, 0, 0.04) 0%, rgba(255, 45, 85, 0.04) 100%)',
                          border: `1px solid ${alpha(theme.palette.warning.main, 0.08)}`,
                          borderRadius: 2,
                          boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                        }}
                      >
                        <CardContent sx={{ p: 3 }}>
                          <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                            <Typography 
                              variant="caption" 
                              color="text.secondary"
                              sx={{ fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}
                            >
                              Avg. Session Duration
                            </Typography>
                            <AccessTimeIcon sx={{ fontSize: 20, color: 'warning.main', opacity: 0.6 }} />
                          </Box>
                          <Typography 
                            variant="h3" 
                            fontWeight={700}
                            color="warning.main"
                            sx={{ 
                              fontSize: '36px',
                              letterSpacing: '-0.02em',
                              mb: 1,
                            }}
                          >
                            {(() => {
                              const duration = dashboardData.chart_data.ga4_traffic_overview.averageSessionDuration || 0
                              const minutes = Math.floor(duration / 60)
                              const seconds = Math.floor(duration % 60)
                              return `${minutes}:${seconds.toString().padStart(2, '0')}`
                            })()}
                          </Typography>
                          <Box display="flex" alignItems="center" gap={0.5}>
                            {dashboardData.chart_data.ga4_traffic_overview.avgSessionDurationChange >= 0 ? (
                              <TrendingUpIcon sx={{ fontSize: 14, color: 'success.main' }} />
                            ) : (
                              <TrendingDownIcon sx={{ fontSize: 14, color: 'error.main' }} />
                            )}
                            <Typography 
                              variant="body2" 
                              sx={{ 
                                fontSize: '13px',
                                fontWeight: 600,
                                color: dashboardData.chart_data.ga4_traffic_overview.avgSessionDurationChange >= 0 ? 'success.main' : 'error.main'
                              }}
                            >
                              {Math.abs(dashboardData.chart_data.ga4_traffic_overview.avgSessionDurationChange).toFixed(1)}%
                            </Typography>
                            <Typography 
                              variant="caption" 
                              color="text.secondary"
                              sx={{ fontSize: '12px' }}
                            >
                              vs last period
                            </Typography>
                          </Box>
                        </CardContent>
                      </Card>
                    </motion.div>
                  </Grid>

                  <Grid item xs={12} md={3}>
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.5, delay: 0.8 }}
                    >
                      <Card
                        sx={{
                          background: 'linear-gradient(135deg, rgba(88, 86, 214, 0.04) 0%, rgba(0, 122, 255, 0.04) 100%)',
                          border: `1px solid ${alpha(theme.palette.secondary.main, 0.08)}`,
                          borderRadius: 2,
                          boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                        }}
                      >
                        <CardContent sx={{ p: 3 }}>
                          <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                            <Typography 
                              variant="caption" 
                              color="text.secondary"
                              sx={{ fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}
                            >
                              Engagement Rate
                            </Typography>
                            <VisibilityIcon sx={{ fontSize: 20, color: 'secondary.main', opacity: 0.6 }} />
                          </Box>
                          <Typography 
                            variant="h3" 
                            fontWeight={700}
                            color="secondary.main"
                            sx={{ 
                              fontSize: '36px',
                              letterSpacing: '-0.02em',
                              mb: 1,
                            }}
                          >
                            {((dashboardData.chart_data.ga4_traffic_overview.engagementRate || 0) * 100).toFixed(1)}%
                          </Typography>
                          <Box display="flex" alignItems="center" gap={0.5}>
                            {dashboardData.chart_data.ga4_traffic_overview.engagementRateChange >= 0 ? (
                              <TrendingUpIcon sx={{ fontSize: 14, color: 'success.main' }} />
                            ) : (
                              <TrendingDownIcon sx={{ fontSize: 14, color: 'error.main' }} />
                            )}
                            <Typography 
                              variant="body2" 
                              sx={{ 
                                fontSize: '13px',
                                fontWeight: 600,
                                color: dashboardData.chart_data.ga4_traffic_overview.engagementRateChange >= 0 ? 'success.main' : 'error.main'
                              }}
                            >
                              {Math.abs(dashboardData.chart_data.ga4_traffic_overview.engagementRateChange).toFixed(1)}%
                            </Typography>
                            <Typography 
                              variant="caption" 
                              color="text.secondary"
                              sx={{ fontSize: '12px' }}
                            >
                              vs last period
                            </Typography>
                          </Box>
                        </CardContent>
                      </Card>
                    </motion.div>
                  </Grid>
                </Grid>
              )}
            </>
          )}

          {/* General KPI Grid - All Other KPIs */}
          {displayedKPIs.length > 0 && (
            <>
              <Typography 
                variant="h5" 
                fontWeight={700} 
                sx={{ 
                  mt: 5, 
                  mb: 3,
                  fontSize: '1.5rem',
                  letterSpacing: '-0.02em',
                  color: 'text.primary'
                }}
              >
                All Performance Metrics
              </Typography>
              
              <Grid container spacing={2} sx={{ mb: 4 }}>
                {displayedKPIs.map(([key, kpi], index) => {
                  const sourceColor = getSourceColor(kpi.source)
                  const sourceLabel = getSourceLabel(kpi.source)
                  
                  return (
                    <Grid item xs={12} sm={6} md={3} key={key}>
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
                            '&:hover': {
                              boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                              transform: 'translateY(-2px)',
                            }
                          }}
                        >
                          <CardContent sx={{ p: 2.5 }}>
                            {/* Source Label */}
                            <Box display="flex" justifyContent="flex-end" mb={1}>
                              <Chip
                                label={sourceLabel}
                                size="small"
                                sx={{
                                  bgcolor: alpha(sourceColor, 0.1),
                                  color: sourceColor,
                                  fontWeight: 600,
                                  fontSize: '10px',
                                  height: 20,
                                  borderRadius: '4px',
                                  border: `1px solid ${alpha(sourceColor, 0.2)}`
                                }}
                              />
                            </Box>
                            
                            {/* KPI Label */}
                            <Typography 
                              variant="caption" 
                              color="text.secondary"
                              sx={{ 
                                fontSize: '0.75rem', 
                                fontWeight: 500,
                                display: 'block',
                                mb: 0.5
                              }}
                            >
                              {KPI_METADATA[kpiKey]?.label || kpi.label}
                            </Typography>
                            
                            {/* KPI Value */}
                            <Typography 
                              variant="h5" 
                              fontWeight={700}
                              sx={{ 
                                fontSize: '1.5rem',
                                letterSpacing: '-0.02em',
                                mb: 1,
                                color: 'text.primary',
                              }}
                            >
                              {formatValue(kpi)}
                            </Typography>
                            
                            {/* Change Indicator */}
                            {kpi.change !== undefined && kpi.change !== null && 
                             !['impressions', 'clicks', 'ctr', 'influencer_reach', 'scrunch_engagement_rate', 'total_interactions', 'cost_per_engagement', 'all_keywords_ranking'].includes(key) &&
                             kpi.format !== 'custom' && typeof kpi.change === 'number' && (
                              <Box display="flex" alignItems="center" gap={0.5}>
                                {kpi.change >= 0 ? (
                                  <TrendingUpIcon sx={{ fontSize: 14, color: '#34A853' }} />
                                ) : (
                                  <TrendingDownIcon sx={{ fontSize: 14, color: '#EA4335' }} />
                                )}
                                <Typography 
                                  variant="caption" 
                                  sx={{ 
                                    fontWeight: 600,
                                    fontSize: '0.75rem',
                                    color: kpi.change >= 0 ? '#34A853' : '#EA4335'
                                  }}
                                >
                                  {kpi.change >= 0 ? '+' : ''}{kpi.change.toFixed(1)}%
                                </Typography>
                              </Box>
                            )}
                            {/* Handle custom format KPIs with object change values */}
                            {kpi.format === 'custom' && kpi.change && typeof kpi.change === 'object' && (
                              <Box display="flex" flexDirection="column" gap={0.5} mt={0.5}>
                                {key === 'competitive_benchmarking' && (
                                  <>
                                    {kpi.change.brand_visibility !== undefined && kpi.change.brand_visibility !== null && (
                                      <Box display="flex" alignItems="center" gap={0.5}>
                                        {kpi.change.brand_visibility >= 0 ? (
                                          <TrendingUpIcon sx={{ fontSize: 12, color: '#34A853' }} />
                                        ) : (
                                          <TrendingDownIcon sx={{ fontSize: 12, color: '#EA4335' }} />
                                        )}
                                        <Typography variant="caption" sx={{ fontSize: '0.7rem', color: kpi.change.brand_visibility >= 0 ? '#34A853' : '#EA4335' }}>
                                          Brand: {kpi.change.brand_visibility >= 0 ? '+' : ''}{kpi.change.brand_visibility.toFixed(1)}%
                                        </Typography>
                                      </Box>
                                    )}
                                    {kpi.change.competitor_avg_visibility !== undefined && kpi.change.competitor_avg_visibility !== null && (
                                      <Box display="flex" alignItems="center" gap={0.5}>
                                        {kpi.change.competitor_avg_visibility >= 0 ? (
                                          <TrendingUpIcon sx={{ fontSize: 12, color: '#34A853' }} />
                                        ) : (
                                          <TrendingDownIcon sx={{ fontSize: 12, color: '#EA4335' }} />
                                        )}
                                        <Typography variant="caption" sx={{ fontSize: '0.7rem', color: kpi.change.competitor_avg_visibility >= 0 ? '#34A853' : '#EA4335' }}>
                                          Competitor avg: {kpi.change.competitor_avg_visibility >= 0 ? '+' : ''}{kpi.change.competitor_avg_visibility.toFixed(1)}%
                                        </Typography>
                                      </Box>
                                    )}
                                  </>
                                )}
                              </Box>
                            )}
                            {/* Handle keyword_ranking_change_and_volume with object change values */}
                            {key === 'keyword_ranking_change_and_volume' && kpi.format === 'custom' && kpi.change && typeof kpi.change === 'object' && (
                              <Box display="flex" flexDirection="column" gap={0.5} mt={0.5}>
                                {kpi.change.ranking_change !== undefined && kpi.change.ranking_change !== null && (
                                  <Box display="flex" alignItems="center" gap={0.5}>
                                    {kpi.change.ranking_change >= 0 ? (
                                      <TrendingUpIcon sx={{ fontSize: 12, color: '#34A853' }} />
                                    ) : (
                                      <TrendingDownIcon sx={{ fontSize: 12, color: '#EA4335' }} />
                                    )}
                                    <Typography variant="caption" sx={{ fontSize: '0.7rem', color: kpi.change.ranking_change >= 0 ? '#34A853' : '#EA4335' }}>
                                      Ranking change: {kpi.change.ranking_change >= 0 ? '+' : ''}{kpi.change.ranking_change.toFixed(1)}%
                                    </Typography>
                                  </Box>
                                )}
                                {kpi.change.search_volume !== undefined && kpi.change.search_volume !== null && (
                                  <Box display="flex" alignItems="center" gap={0.5}>
                                    {kpi.change.search_volume >= 0 ? (
                                      <TrendingUpIcon sx={{ fontSize: 12, color: '#34A853' }} />
                                    ) : (
                                      <TrendingDownIcon sx={{ fontSize: 12, color: '#EA4335' }} />
                                    )}
                                    <Typography variant="caption" sx={{ fontSize: '0.7rem', color: kpi.change.search_volume >= 0 ? '#34A853' : '#EA4335' }}>
                                      Search volume: {kpi.change.search_volume >= 0 ? '+' : ''}{kpi.change.search_volume.toFixed(1)}%
                                    </Typography>
                                  </Box>
                                )}
                              </Box>
                            )}
                          </CardContent>
                        </Card>
                      </motion.div>
                    </Grid>
                  )
                })}
              </Grid>
    </>
  )
}

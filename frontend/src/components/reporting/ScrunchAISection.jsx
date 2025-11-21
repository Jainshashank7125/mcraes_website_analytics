import { Box, Card, CardContent, Grid, Typography, alpha } from '@mui/material'
import { Article as ArticleIcon, TrendingUp as TrendingUpIcon } from '@mui/icons-material'
import { motion } from 'framer-motion'
import { formatValue } from './utils'

export default function ScrunchAISection({ dashboardData, formatValue, theme }) {
  if (!dashboardData?.kpis?.total_citations && 
      !dashboardData?.kpis?.brand_presence_rate && 
      !dashboardData?.kpis?.competitive_benchmarking && 
      !dashboardData?.chart_data?.top_performing_prompts) {
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
        Scrunch AI
      </Typography>
      <Typography 
        variant="body2" 
        color="text.secondary"
        sx={{ 
          mb: 3,
          fontSize: '0.875rem'
        }}
      >
        AI platform presence and engagement metrics
      </Typography>

      {/* Brand Presence Rate Donut */}
      {dashboardData?.kpis?.brand_presence_rate && (
        <Box sx={{ mb: 4 }}>
          <Typography 
            variant="h6" 
            fontWeight={600} 
            mb={2}
            sx={{ fontSize: '1.125rem', letterSpacing: '-0.01em' }}
          >
            Brand Presence Metrics
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6} md={4}>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.1 }}
              >
                <Card sx={{ height: '100%', borderRadius: 2, border: `1px solid ${theme.palette.divider}`, boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
                  <CardContent sx={{ p: 3, textAlign: 'center' }}>
                    <Typography 
                      variant="h6" 
                      mb={2} 
                      fontWeight={600}
                      sx={{ fontSize: '1rem', letterSpacing: '-0.01em' }}
                    >
                      Brand Presence Rate
                    </Typography>
                    <ResponsiveContainer width="100%" height={250}>
                      <PieChart>
                        <Pie
                          data={[
                            { name: 'Present', value: dashboardData.kpis.brand_presence_rate.value || 0 },
                            { name: 'Absent', value: 100 - (dashboardData.kpis.brand_presence_rate.value || 0) }
                          ]}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={90}
                          startAngle={90}
                          endAngle={-270}
                          dataKey="value"
                          label={({ name, value }) => `${name}: ${value.toFixed(1)}%`}
                          labelLine={false}
                        >
                          <Cell fill={theme.palette.success.main} />
                          <Cell fill={theme.palette.grey[300]} />
                        </Pie>
                        <Tooltip 
                          contentStyle={{ 
                            borderRadius: '8px', 
                            border: 'none', 
                            boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                            backgroundColor: '#FFFFFF'
                          }}
                          formatter={(value, name) => [`${value.toFixed(1)}%`, name]}
                        />
                        <Legend 
                          wrapperStyle={{ paddingTop: '10px' }}
                          formatter={(value) => value}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                    <Box mt={2}>
                      <Typography 
                        variant="h4" 
                        fontWeight={700}
                        sx={{ fontSize: '2rem' }}
                        color="success.main"
                      >
                        {(dashboardData.kpis.brand_presence_rate.value || 0).toFixed(1)}%
                      </Typography>
                      <Typography 
                        variant="caption" 
                        color="text.secondary"
                        sx={{ fontSize: '0.75rem', display: 'block', mt: 0.5 }}
                      >
                        Brand Present in Responses
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              </motion.div>
            </Grid>
          </Grid>
        </Box>
      )}

      {/* Competitive Benchmarking Chart */}
      {dashboardData.kpis?.competitive_benchmarking && (
        <Box sx={{ mb: 4 }}>
          <Typography 
            variant="h6" 
            fontWeight={600} 
            mb={2}
            sx={{ fontSize: '1.125rem', letterSpacing: '-0.01em' }}
          >
            Competitive Analysis
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.15 }}
              >
                <Card sx={{ height: 400, borderRadius: 2, border: `1px solid ${theme.palette.divider}`, boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
                  <CardContent sx={{ p: 3 }}>
                    <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                      <Typography variant="h6" fontWeight={600}>
                        Competitive Benchmarking
                      </Typography>
                      <Chip
                        label="Scrunch"
                        size="small"
                        sx={{
                          bgcolor: alpha(theme.palette.secondary.main, 0.1),
                          color: theme.palette.secondary.main,
                          fontWeight: 600,
                          fontSize: '10px',
                          height: 20,
                          borderRadius: '4px',
                          border: `1px solid ${alpha(theme.palette.secondary.main, 0.2)}`
                        }}
                      />
                    </Box>
                    <ResponsiveContainer width="100%" height={320}>
                      <BarChart
                        data={[
                          {
                            name: 'Your Brand',
                            visibility: dashboardData.kpis.competitive_benchmarking.value?.brand_visibility_percent || 0,
                            fill: theme.palette.primary.main
                          },
                          {
                            name: 'Competitor Avg',
                            visibility: dashboardData.kpis.competitive_benchmarking.value?.competitor_avg_visibility_percent || 0,
                            fill: theme.palette.grey[400]
                          }
                        ]}
                        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke="#E4E4E7" />
                        <XAxis 
                          dataKey="name" 
                          tick={{ fontSize: 12 }}
                          stroke="#71717A"
                        />
                        <YAxis 
                          tick={{ fontSize: 12 }} 
                          stroke="#71717A"
                          label={{ value: 'Visibility (%)', angle: -90, position: 'insideLeft' }}
                        />
                        <Tooltip 
                          contentStyle={{ 
                            borderRadius: '8px', 
                            border: 'none', 
                            boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                            backgroundColor: '#FFFFFF'
                          }}
                          formatter={(value) => [`${value.toFixed(1)}%`, 'AI Visibility']}
                        />
                        <Legend />
                        <Bar 
                          dataKey="visibility" 
                          radius={[8, 8, 0, 0]}
                          name="AI Visibility"
                        >
                          {[
                            { fill: theme.palette.primary.main },
                            { fill: theme.palette.grey[400] }
                          ].map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.fill} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                    {/* Change indicators */}
                    {dashboardData.kpis.competitive_benchmarking.change && (
                      <Box display="flex" gap={2} mt={2} justifyContent="center">
                        {dashboardData.kpis.competitive_benchmarking.change.brand_visibility !== undefined && 
                         dashboardData.kpis.competitive_benchmarking.change.brand_visibility !== null && (
                          <Box display="flex" alignItems="center" gap={0.5}>
                            {dashboardData.kpis.competitive_benchmarking.change.brand_visibility >= 0 ? (
                              <TrendingUpIcon sx={{ fontSize: 14, color: '#34A853' }} />
                            ) : (
                              <TrendingDownIcon sx={{ fontSize: 14, color: '#EA4335' }} />
                            )}
                            <Typography variant="caption" sx={{ fontSize: '0.75rem', color: dashboardData.kpis.competitive_benchmarking.change.brand_visibility >= 0 ? '#34A853' : '#EA4335' }}>
                              Brand: {dashboardData.kpis.competitive_benchmarking.change.brand_visibility >= 0 ? '+' : ''}{dashboardData.kpis.competitive_benchmarking.change.brand_visibility.toFixed(1)}%
                            </Typography>
                          </Box>
                        )}
                        {dashboardData.kpis.competitive_benchmarking.change.competitor_avg_visibility !== undefined && 
                         dashboardData.kpis.competitive_benchmarking.change.competitor_avg_visibility !== null && (
                          <Box display="flex" alignItems="center" gap={0.5}>
                            {dashboardData.kpis.competitive_benchmarking.change.competitor_avg_visibility >= 0 ? (
                              <TrendingUpIcon sx={{ fontSize: 14, color: '#34A853' }} />
                            ) : (
                              <TrendingDownIcon sx={{ fontSize: 14, color: '#EA4335' }} />
                            )}
                            <Typography variant="caption" sx={{ fontSize: '0.75rem', color: dashboardData.kpis.competitive_benchmarking.change.competitor_avg_visibility >= 0 ? '#34A853' : '#EA4335' }}>
                              Competitor: {dashboardData.kpis.competitive_benchmarking.change.competitor_avg_visibility >= 0 ? '+' : ''}{dashboardData.kpis.competitive_benchmarking.change.competitor_avg_visibility.toFixed(1)}%
                            </Typography>
                          </Box>
                        )}
                      </Box>
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            </Grid>
          </Grid>
        </Box>
      )}

      {/* Top Performing Prompts Section */}
      {dashboardData?.chart_data?.top_performing_prompts && dashboardData.chart_data.top_performing_prompts.length > 0 && (
        <Box sx={{ mb: 4 }}>
          <Typography 
            variant="h6" 
            fontWeight={600} 
            mb={2}
            sx={{ fontSize: '1.125rem', letterSpacing: '-0.01em' }}
          >
            Top Performing Prompts
          </Typography>
      
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.3 }}
      >
        <Card sx={{ mb: 3, borderRadius: 2, border: `1px solid ${theme.palette.divider}`, boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
          <CardContent sx={{ p: 3 }}>
            <Grid container spacing={2}>
              {dashboardData.chart_data.top_performing_prompts.map((prompt) => (
                <Grid item xs={12} sm={6} md={4} key={prompt.id}>
                  <Paper
                    sx={{
                      p: 2,
                      borderLeft: `3px solid ${theme.palette.primary.main}`,
                      borderRadius: 1.5,
                      transition: 'all 0.2s',
                      '&:hover': {
                        transform: 'translateX(2px)',
                        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.06)',
                      },
                    }}
                  >
                    <Box display="flex" alignItems="flex-start" justifyContent="space-between" mb={1}>
                      <Box display="flex" alignItems="center" gap={1}>
                        <Chip
                          label={`Rank #${prompt.rank}`}
                          size="small"
                          sx={{
                            bgcolor: 'primary.main',
                            color: 'white',
                            fontWeight: 700,
                            fontSize: '11px',
                            height: 22,
                            minWidth: 50,
                          }}
                        />
                      </Box>
                    </Box>
                    <Typography 
                      variant="body2" 
                      fontWeight={600}
                      sx={{ 
                        fontSize: '0.875rem',
                        lineHeight: 1.4,
                        display: '-webkit-box',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical',
                        overflow: 'hidden',
                      }}
                    >
                      {prompt.text || 'N/A'}
                    </Typography>
                    <Box display="flex" gap={2} mt={1.5}>
                      <Typography 
                        variant="caption" 
                        color="text.secondary"
                        sx={{ fontSize: '11px', fontWeight: 500 }}
                      >
                        {prompt.responseCount?.toLocaleString() || 0} responses
                      </Typography>
                      <Typography 
                        variant="caption" 
                        color="text.secondary"
                        sx={{ fontSize: '11px', fontWeight: 500 }}
                      >
                        {prompt.variants || 0} variants
                      </Typography>
                    </Box>
                  </Paper>
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>
      </motion.div>
        </Box>
      )}

      {/* Scrunch AI Insights Section */}
      {dashboardData?.chart_data?.scrunch_ai_insights && dashboardData.chart_data.scrunch_ai_insights.length > 0 && (
        <Box sx={{ mb: 4 }}>
          <Typography 
            variant="h6" 
            fontWeight={600} 
            mb={2}
            sx={{ fontSize: '1.125rem', letterSpacing: '-0.01em' }}
          >
            Scrunch AI Insights
          </Typography>
      
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.4 }}
      >
        <Card sx={{ mb: 3, borderRadius: 2, border: `1px solid ${theme.palette.divider}`, boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
          <CardContent sx={{ p: 0 }}>
            <Box p={3} borderBottom="1px solid" borderColor="divider">
              <Typography 
                variant="h6" 
                fontWeight={600}
                sx={{ fontSize: '1.125rem', letterSpacing: '-0.01em' }}
              >
                Scrunch AI Insights
              </Typography>
            </Box>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow sx={{ bgcolor: alpha(theme.palette.primary.main, 0.04) }}>
                    <TableCell sx={{ fontWeight: 700, fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', py: 1.5, minWidth: 200 }}>
                      Seed Prompt
                    </TableCell>
                    <TableCell sx={{ fontWeight: 700, fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', py: 1.5, minWidth: 120 }}>
                      Data
                    </TableCell>
                    <TableCell sx={{ fontWeight: 700, fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', py: 1.5, minWidth: 120 }}>
                      Presence
                    </TableCell>
                    <TableCell sx={{ fontWeight: 700, fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', py: 1.5, minWidth: 100 }}>
                      Citations
                    </TableCell>
                    <TableCell sx={{ fontWeight: 700, fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', py: 1.5, minWidth: 100 }}>
                      Competitors
                    </TableCell>
                    <TableCell sx={{ fontWeight: 700, fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', py: 1.5, minWidth: 100 }}>
                      Stage
                    </TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {dashboardData.chart_data.scrunch_ai_insights.map((insight) => (
                    <TableRow 
                      key={insight.id || insight.seedPrompt}
                      hover
                      sx={{
                        transition: 'all 0.2s',
                        '&:hover': {
                          bgcolor: alpha(theme.palette.primary.main, 0.02),
                        },
                      }}
                    >
                      <TableCell sx={{ py: 2 }}>
                        <Box>
                          <Typography 
                            variant="body2" 
                            fontWeight={600}
                            sx={{ 
                              fontSize: '0.875rem',
                              mb: 0.5,
                              lineHeight: 1.4,
                            }}
                          >
                            {insight.seedPrompt.length > 60 
                              ? insight.seedPrompt.substring(0, 60) + '...' 
                              : insight.seedPrompt}
                          </Typography>
                          <Typography 
                            variant="caption" 
                            color="text.secondary"
                            sx={{ fontSize: '11px', fontStyle: 'italic' }}
                          >
                            {insight.category}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell sx={{ py: 2 }}>
                        <Box>
                          <Typography 
                            variant="body2" 
                            sx={{ fontSize: '0.875rem', fontWeight: 600, mb: 0.25 }}
                          >
                            {insight.variants?.toLocaleString() || 0} variants
                          </Typography>
                          <Typography 
                            variant="caption" 
                            color="text.secondary"
                            sx={{ fontSize: '0.75rem' }}
                          >
                            {insight.responses?.toLocaleString() || 0} responses
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell sx={{ py: 2 }}>
                        <Box>
                          <Typography 
                            variant="body2" 
                            fontWeight={700}
                            sx={{ fontSize: '0.9375rem', mb: 0.25 }}
                          >
                            {insight.presence}%
                          </Typography>
                          {insight.presenceChange !== undefined && (
                            <Box display="flex" alignItems="center" gap={0.5}>
                              {insight.presenceChange >= 0 ? (
                                <TrendingUpIcon sx={{ fontSize: 12, color: 'success.main' }} />
                              ) : (
                                <TrendingDownIcon sx={{ fontSize: 12, color: 'error.main' }} />
                              )}
                              <Typography 
                                variant="caption" 
                                sx={{ 
                                  fontSize: '11px',
                                  fontWeight: 600,
                                  color: insight.presenceChange >= 0 ? 'success.main' : 'error.main'
                                }}
                              >
                                {insight.presenceChange >= 0 ? '+' : ''}{insight.presenceChange.toFixed(1)}%
                              </Typography>
                            </Box>
                          )}
                        </Box>
                      </TableCell>
                      <TableCell sx={{ py: 2 }}>
                        <Box>
                          <Typography 
                            variant="body2" 
                            fontWeight={600}
                            sx={{ fontSize: '0.9375rem', mb: 0.25 }}
                          >
                            {insight.citations || 0}
                          </Typography>
                          {insight.citationsChange !== undefined && (
                            <Box display="flex" alignItems="center" gap={0.5}>
                              {insight.citationsChange >= 0 ? (
                                <TrendingUpIcon sx={{ fontSize: 12, color: 'success.main' }} />
                              ) : (
                                <TrendingDownIcon sx={{ fontSize: 12, color: 'error.main' }} />
                              )}
                              <Typography 
                                variant="caption" 
                                sx={{ 
                                  fontSize: '11px',
                                  fontWeight: 600,
                                  color: insight.citationsChange >= 0 ? 'success.main' : 'error.main'
                                }}
                              >
                                {insight.citationsChange >= 0 ? '+' : ''}{insight.citationsChange}
                              </Typography>
                            </Box>
                          )}
                        </Box>
                      </TableCell>
                      <TableCell sx={{ py: 2 }}>
                        <Box>
                          <Typography 
                            variant="body2" 
                            fontWeight={600}
                            sx={{ fontSize: '0.9375rem', mb: 0.25 }}
                          >
                            {insight.competitors || 0} active
                          </Typography>
                          {insight.competitorsChange !== undefined && (
                            <Typography 
                              variant="caption" 
                              color="text.secondary"
                              sx={{ fontSize: '11px' }}
                            >
                              {insight.competitorsChange >= 0 ? '+' : ''}{insight.competitorsChange}
                            </Typography>
                          )}
                        </Box>
                      </TableCell>
                      <TableCell sx={{ py: 2 }}>
                        <Chip
                          label={insight.stage}
                          size="small"
                          sx={{
                            bgcolor: insight.stage === 'Awareness' ? alpha(theme.palette.info.main, 0.1) :
                                     insight.stage === 'Evaluation' ? alpha(theme.palette.warning.main, 0.1) :
                                     alpha(theme.palette.success.main, 0.1),
                            color: insight.stage === 'Awareness' ? 'info.main' :
                                   insight.stage === 'Evaluation' ? 'warning.main' :
                                   'success.main',
                            fontWeight: 600,
                            fontSize: '11px',
                            height: 24,
                          }}
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
            {dashboardData.chart_data.scrunch_ai_insights.length === 0 && (
              <Box p={4} textAlign="center">
                <Typography color="text.secondary" sx={{ fontSize: '0.875rem' }}>
                  No insights available
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      </motion.div>
        </Box>
      )}
    </>
  )
}

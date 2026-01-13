import { Box, Card, CardContent, Chip, Grid, Typography, alpha } from '@mui/material'
import { TrendingUp as TrendingUpIcon, TrendingDown as TrendingDownIcon, BarChart as BarChartIcon, People as PeopleIcon, Visibility as VisibilityIcon, PersonAdd as PersonAddIcon, AccessTime as AccessTimeIcon } from '@mui/icons-material'
import { motion } from 'framer-motion'
import { 
  LineChart, Line,
  BarChart, Bar, 
  PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts'
import { getMonthName, getChannelLabel, getChannelColor, formatValue, getSourceColor, getSourceLabel } from './utils'

export default function GA4Section({ dashboardData, formatValue, getSourceColor, getSourceLabel, theme, getMonthName, getChannelLabel, getChannelColor, shouldShowChangePeriod }) {
  if (!dashboardData?.kpis?.users && !dashboardData?.chart_data?.ga4_traffic_overview) {
    return null
  }

  // Get current date range label for charts
  const getDateRangeLabel = () => {
    return 'Current Period' // TODO: Pass as prop or calculate from date range
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
        Google Analytics 4
      </Typography>
      <Typography 
        variant="body2" 
        color="text.secondary"
        sx={{ 
          mb: 3,
          fontSize: '0.875rem'
        }}
      >
        Website traffic and engagement metrics
      </Typography>

              {/* GA4 Charts and Visualizations */}
              <Box sx={{ mb: 4 }}>
                <Typography 
                  variant="h6" 
                  fontWeight={600} 
                  mb={3}
                  sx={{ fontSize: '1.125rem', letterSpacing: '-0.01em' }}
                >
                  Charts & Visualizations
                </Typography>

                {/* GA4 Daily Comparison Charts - Users, Sessions, New Users, Conversions */}
                {dashboardData.chart_data?.ga4_daily_comparison?.length > 0 && (
                  <Grid container spacing={3} sx={{ mb: 4 }}>
                    {/* Total Users Chart - Full Width (Primary Chart) */}
                    <Grid item xs={12}>
                      <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5, delay: 0.1 }}
                      >
                        <Card 
                          sx={{ 
                            height: 500,
                            border: `1px solid ${theme.palette.divider}`,
                            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                            mb: 3
                          }}
                        >
                          <CardContent sx={{ p: 3 }}>
                            <Box display="flex" alignItems="center" justifyContent="space-between" mb={3}>
                              <Typography variant="h6" fontWeight={600} sx={{ fontSize: '1.125rem' }}>
                                Total Users
                              </Typography>
                              <Chip
                                label="GA4"
                                size="small"
                                sx={{
                                  bgcolor: alpha(theme.palette.primary.main, 0.1),
                                  color: theme.palette.primary.main,
                                  fontWeight: 600,
                                  fontSize: '10px',
                                  height: 20,
                                  borderRadius: '4px',
                                  border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`
                                }}
                              />
                            </Box>
                            <ResponsiveContainer width="100%" height={400}>
                              <LineChart 
                                data={dashboardData.chart_data.ga4_daily_comparison}
                                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                              >
                                <CartesianGrid strokeDasharray="3 3" stroke="#E4E4E7" />
                                <XAxis 
                                  dataKey="date" 
                                  tick={{ fontSize: 12 }}
                                  stroke="#71717A"
                                  tickFormatter={(value) => {
                                    if (value && value.length === 8) {
                                      const month = value.substring(4, 6)
                                      const day = value.substring(6, 8)
                                      return `${day} ${getMonthName(parseInt(month))}`
                                    }
                                    return value
                                  }}
                                />
                                <YAxis 
                                  tick={{ fontSize: 12 }}
                                  stroke="#71717A"
                                />
                                <Tooltip 
                                  contentStyle={{ 
                                    borderRadius: '8px', 
                                    border: 'none', 
                                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                                    backgroundColor: '#FFFFFF'
                                  }}
                                  labelFormatter={(value) => {
                                    if (value && value.length === 8) {
                                      const year = value.substring(0, 4)
                                      const month = value.substring(4, 6)
                                      const day = value.substring(6, 8)
                                      return `${day} ${getMonthName(parseInt(month))} ${year}`
                                    }
                                    return value
                                  }}
                                />
                                <Legend 
                                  wrapperStyle={{ paddingTop: '20px' }}
                                />
                                <Line 
                                  type="monotone" 
                                  dataKey="current_users" 
                                  name={getDateRangeLabel()}
                                  stroke={theme.palette.primary.main} 
                                  strokeWidth={3}
                                  dot={{ fill: theme.palette.primary.main, r: 5 }}
                                  activeDot={{ r: 7 }}
                                />
                                {shouldShowChangePeriod && shouldShowChangePeriod("ga4") && (
                                  <Line 
                                    type="monotone" 
                                    dataKey="previous_users" 
                                    name="Previous period"
                                    stroke={theme.palette.grey[400]} 
                                    strokeWidth={2.5}
                                    strokeDasharray="5 5"
                                    dot={{ fill: theme.palette.grey[400], r: 4 }}
                                    activeDot={{ r: 6 }}
                                  />
                                )}
                              </LineChart>
                            </ResponsiveContainer>
                          </CardContent>
                        </Card>
                      </motion.div>
                    </Grid>

                    {/* Sessions Comparison Chart */}
                    <Grid item xs={12} md={6}>
                      <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5, delay: 0.15 }}
                      >
                        <Card 
                          sx={{ 
                            height: 400,
                            border: `1px solid ${theme.palette.divider}`,
                            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                            mb: 3
                          }}
                        >
                          <CardContent sx={{ p: 3 }}>
                            <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                              <Typography variant="h6" fontWeight={600} sx={{ fontSize: '1rem' }}>Sessions</Typography>
                              <Chip
                                label="GA4"
                                size="small"
                                sx={{
                                  bgcolor: alpha(theme.palette.primary.main, 0.1),
                                  color: theme.palette.primary.main,
                                  fontWeight: 600,
                                  fontSize: '10px',
                                  height: 20,
                                  borderRadius: '4px',
                                  border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`
                                }}
                              />
                            </Box>
                            <ResponsiveContainer width="100%" height={320}>
                              <LineChart 
                                data={dashboardData.chart_data.ga4_daily_comparison}
                                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                              >
                                <CartesianGrid strokeDasharray="3 3" stroke="#E4E4E7" />
                                <XAxis 
                                  dataKey="date" 
                                  tick={{ fontSize: 11 }}
                                  stroke="#71717A"
                                  tickFormatter={(value) => {
                                    if (value && value.length === 8) {
                                      const month = value.substring(4, 6)
                                      const day = value.substring(6, 8)
                                      return `${day} ${getMonthName(parseInt(month))}`
                                    }
                                    return value
                                  }}
                                />
                                <YAxis 
                                  tick={{ fontSize: 12 }}
                                  stroke="#71717A"
                                />
                                <Tooltip 
                                  contentStyle={{ 
                                    borderRadius: '8px', 
                                    border: 'none', 
                                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                                    backgroundColor: '#FFFFFF'
                                  }}
                                  labelFormatter={(value) => {
                                    if (value && value.length === 8) {
                                      const year = value.substring(0, 4)
                                      const month = value.substring(4, 6)
                                      const day = value.substring(6, 8)
                                      return `${day} ${getMonthName(parseInt(month))} ${year}`
                                    }
                                    return value
                                  }}
                                />
                                <Legend wrapperStyle={{ paddingTop: '10px' }} />
                                <Line 
                                  type="monotone" 
                                  dataKey="current_sessions" 
                                  name={getDateRangeLabel()}
                                  stroke={theme.palette.primary.main} 
                                  strokeWidth={3}
                                  dot={{ fill: theme.palette.primary.main, r: 4 }}
                                  activeDot={{ r: 6 }}
                                />
                                {shouldShowChangePeriod && shouldShowChangePeriod("ga4") && (
                                  <Line 
                                    type="monotone" 
                                    dataKey="previous_sessions" 
                                    name="Previous period"
                                    stroke={theme.palette.grey[400]} 
                                    strokeWidth={2.5}
                                    strokeDasharray="5 5"
                                    dot={{ fill: theme.palette.grey[400], r: 3 }}
                                    activeDot={{ r: 5 }}
                                  />
                                )}
                              </LineChart>
                            </ResponsiveContainer>
                          </CardContent>
                        </Card>
                      </motion.div>
                    </Grid>

                    {/* New Users Comparison Chart */}
                    <Grid item xs={12} md={6}>
                      <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5, delay: 0.2 }}
                      >
                        <Card 
                          sx={{ 
                            height: 400,
                            border: `1px solid ${theme.palette.divider}`,
                            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                            mb: 3
                          }}
                        >
                          <CardContent sx={{ p: 3 }}>
                            <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                              <Typography variant="h6" fontWeight={600} sx={{ fontSize: '1rem' }}>New Users</Typography>
                              <Chip
                                label="GA4"
                                size="small"
                                sx={{
                                  bgcolor: alpha(theme.palette.primary.main, 0.1),
                                  color: theme.palette.primary.main,
                                  fontWeight: 600,
                                  fontSize: '10px',
                                  height: 20,
                                  borderRadius: '4px',
                                  border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`
                                }}
                              />
                            </Box>
                            <ResponsiveContainer width="100%" height={320}>
                              <LineChart 
                                data={dashboardData.chart_data.ga4_daily_comparison}
                                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                              >
                                <CartesianGrid strokeDasharray="3 3" stroke="#E4E4E7" />
                                <XAxis 
                                  dataKey="date" 
                                  tick={{ fontSize: 11 }}
                                  stroke="#71717A"
                                  tickFormatter={(value) => {
                                    if (value && value.length === 8) {
                                      const day = value.substring(6, 8)
                                      return day
                                    }
                                    return value
                                  }}
                                />
                                <YAxis 
                                  tick={{ fontSize: 12 }}
                                  stroke="#71717A"
                                />
                                <Tooltip 
                                  contentStyle={{ 
                                    borderRadius: '8px', 
                                    border: 'none', 
                                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                                    backgroundColor: '#FFFFFF'
                                  }}
                                  labelFormatter={(value) => {
                                    if (value && value.length === 8) {
                                      const year = value.substring(0, 4)
                                      const month = value.substring(4, 6)
                                      const day = value.substring(6, 8)
                                      return `${day} ${getMonthName(parseInt(month))} ${year}`
                                    }
                                    return value
                                  }}
                                />
                                <Legend wrapperStyle={{ paddingTop: '10px' }} />
                                <Line 
                                  type="monotone" 
                                  dataKey="current_new_users" 
                                  name={getDateRangeLabel()}
                                  stroke={theme.palette.success.main} 
                                  strokeWidth={3}
                                  dot={{ fill: theme.palette.success.main, r: 4 }}
                                  activeDot={{ r: 6 }}
                                />
                                {shouldShowChangePeriod && shouldShowChangePeriod("ga4") && (
                                  <Line 
                                    type="monotone" 
                                    dataKey="previous_new_users" 
                                    name="Previous period"
                                    stroke={theme.palette.grey[400]} 
                                    strokeWidth={2.5}
                                    strokeDasharray="5 5"
                                    dot={{ fill: theme.palette.grey[400], r: 3 }}
                                    activeDot={{ r: 5 }}
                                  />
                                )}
                              </LineChart>
                            </ResponsiveContainer>
                          </CardContent>
                        </Card>
                      </motion.div>
                    </Grid>

                    {/* Conversions Chart */}
                    {dashboardData.chart_data.ga4_daily_comparison.some(d => d.current_conversions > 0 || d.previous_conversions > 0) && (
                      <Grid item xs={12} md={6}>
                        <motion.div
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ duration: 0.5, delay: 0.25 }}
                        >
                          <Card 
                            sx={{ 
                              height: 400,
                              border: `1px solid ${theme.palette.divider}`,
                              boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                              mb: 3
                            }}
                          >
                            <CardContent sx={{ p: 3 }}>
                              <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                                <Typography variant="h6" fontWeight={600} sx={{ fontSize: '1rem' }}>Conversions</Typography>
                                <Chip
                                  label="GA4"
                                  size="small"
                                  sx={{
                                    bgcolor: alpha(theme.palette.primary.main, 0.1),
                                    color: theme.palette.primary.main,
                                    fontWeight: 600,
                                    fontSize: '10px',
                                    height: 20,
                                    borderRadius: '4px',
                                    border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`
                                  }}
                                />
                              </Box>
                              <ResponsiveContainer width="100%" height={320}>
                                <LineChart 
                                  data={dashboardData.chart_data.ga4_daily_comparison}
                                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                                >
                                  <CartesianGrid strokeDasharray="3 3" stroke="#E4E4E7" />
                                  <XAxis 
                                    dataKey="date" 
                                    tick={{ fontSize: 11 }}
                                    stroke="#71717A"
                                    tickFormatter={(value) => {
                                      if (value && value.length === 8) {
                                        const day = value.substring(6, 8)
                                        return day
                                      }
                                      return value
                                    }}
                                  />
                                  <YAxis 
                                    tick={{ fontSize: 12 }}
                                    stroke="#71717A"
                                  />
                                  <Tooltip 
                                    contentStyle={{ 
                                      borderRadius: '8px', 
                                      border: 'none', 
                                      boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                                      backgroundColor: '#FFFFFF'
                                    }}
                                    labelFormatter={(value) => {
                                      if (value && value.length === 8) {
                                        const year = value.substring(0, 4)
                                        const month = value.substring(4, 6)
                                        const day = value.substring(6, 8)
                                        return `${day} ${getMonthName(parseInt(month))} ${year}`
                                      }
                                      return value
                                    }}
                                  />
                                  <Legend wrapperStyle={{ paddingTop: '10px' }} />
                                  <Line 
                                    type="monotone" 
                                    dataKey="current_conversions" 
                                    name={getDateRangeLabel()}
                                    stroke={theme.palette.warning.main} 
                                    strokeWidth={3}
                                    dot={{ fill: theme.palette.warning.main, r: 4 }}
                                    activeDot={{ r: 6 }}
                                  />
                                  {shouldShowChangePeriod && shouldShowChangePeriod("ga4") && (
                                    <Line 
                                      type="monotone" 
                                      dataKey="previous_conversions" 
                                      name="Previous period"
                                      stroke={theme.palette.grey[400]} 
                                      strokeWidth={2.5}
                                      strokeDasharray="5 5"
                                      dot={{ fill: theme.palette.grey[400], r: 3 }}
                                      activeDot={{ r: 5 }}
                                    />
                                  )}
                                </LineChart>
                              </ResponsiveContainer>
                            </CardContent>
                          </Card>
                        </motion.div>
                      </Grid>
                    )}

                    {/* Revenue Chart */}
                    {dashboardData.chart_data.ga4_daily_comparison.some(d => d.current_revenue > 0 || d.previous_revenue > 0) && (
                      <Grid item xs={12} md={6}>
                        <motion.div
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ duration: 0.5, delay: 0.3 }}
                        >
                          <Card 
                            sx={{ 
                              height: 400,
                              border: `1px solid ${theme.palette.divider}`,
                              boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                              mb: 3
                            }}
                          >
                            <CardContent sx={{ p: 3 }}>
                              <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                                <Typography variant="h6" fontWeight={600} sx={{ fontSize: '1rem' }}>Revenue</Typography>
                                <Chip
                                  label="GA4"
                                  size="small"
                                  sx={{
                                    bgcolor: alpha(theme.palette.primary.main, 0.1),
                                    color: theme.palette.primary.main,
                                    fontWeight: 600,
                                    fontSize: '10px',
                                    height: 20,
                                    borderRadius: '4px',
                                    border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`
                                  }}
                                />
                              </Box>
                              <ResponsiveContainer width="100%" height={320}>
                                <LineChart 
                                  data={dashboardData.chart_data.ga4_daily_comparison}
                                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                                >
                                  <CartesianGrid strokeDasharray="3 3" stroke="#E4E4E7" />
                                  <XAxis 
                                    dataKey="date" 
                                    tick={{ fontSize: 11 }}
                                    stroke="#71717A"
                                    tickFormatter={(value) => {
                                      if (value && value.length === 8) {
                                        const day = value.substring(6, 8)
                                        return day
                                      }
                                      return value
                                    }}
                                  />
                                  <YAxis 
                                    tick={{ fontSize: 12 }}
                                    stroke="#71717A"
                                    tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                                  />
                                  <Tooltip 
                                    contentStyle={{ 
                                      borderRadius: '8px', 
                                      border: 'none', 
                                      boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                                      backgroundColor: '#FFFFFF'
                                    }}
                                    labelFormatter={(value) => {
                                      if (value && value.length === 8) {
                                        const year = value.substring(0, 4)
                                        const month = value.substring(4, 6)
                                        const day = value.substring(6, 8)
                                        return `${day} ${getMonthName(parseInt(month))} ${year}`
                                      }
                                      return value
                                    }}
                                    formatter={(value) => `$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
                                  />
                                  <Legend wrapperStyle={{ paddingTop: '10px' }} />
                                  <Line 
                                    type="monotone" 
                                    dataKey="current_revenue" 
                                    name={getDateRangeLabel()}
                                    stroke={theme.palette.success.main} 
                                    strokeWidth={3}
                                    dot={{ fill: theme.palette.success.main, r: 4 }}
                                    activeDot={{ r: 6 }}
                                  />
                                  {shouldShowChangePeriod && shouldShowChangePeriod("ga4") && (
                                    <Line 
                                      type="monotone" 
                                      dataKey="previous_revenue" 
                                      name="Previous period"
                                      stroke={theme.palette.grey[400]} 
                                      strokeWidth={2.5}
                                      strokeDasharray="5 5"
                                      dot={{ fill: theme.palette.grey[400], r: 3 }}
                                      activeDot={{ r: 5 }}
                                    />
                                  )}
                                </LineChart>
                              </ResponsiveContainer>
                            </CardContent>
                          </Card>
                        </motion.div>
                      </Grid>
                    )}
                  </Grid>
                )}

                {/* Top Performing Pages - Horizontal Bar Chart */}
                {dashboardData.chart_data?.top_pages && dashboardData.chart_data.top_pages.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5, delay: 0.35 }}
                  >
                    <Card sx={{ mb: 3, borderRadius: 2, border: `1px solid ${theme.palette.divider}`, boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
                      <CardContent sx={{ p: 3 }}>
                        <Typography 
                          variant="h6" 
                          mb={2} 
                          fontWeight={600}
                          sx={{ fontSize: '1.125rem', letterSpacing: '-0.01em' }}
                        >
                          Top Performing Pages
                        </Typography>
                        <ResponsiveContainer width="100%" height={400}>
                          <BarChart
                            data={dashboardData.chart_data.top_pages.slice(0, 10)}
                            layout="vertical"
                            margin={{ top: 5, right: 30, left: 150, bottom: 5 }}
                          >
                            <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#E4E4E7" />
                            <XAxis type="number" tick={{ fontSize: 12 }} stroke="#71717A" />
                            <YAxis 
                              dataKey="pagePath" 
                              type="category" 
                              width={140} 
                              stroke="#71717A"
                              tick={{ fontSize: 10 }}
                              tickFormatter={(value) => {
                                if (!value) return 'N/A'
                                const path = value.length > 30 ? value.substring(0, 30) + '...' : value
                                return path
                              }}
                            />
                            <Tooltip 
                              contentStyle={{ 
                                borderRadius: '8px', 
                                border: 'none', 
                                boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                                backgroundColor: '#FFFFFF'
                              }}
                              formatter={(value) => [value.toLocaleString(), 'Views']}
                            />
                            <Legend />
                            <Bar 
                              dataKey="views" 
                              radius={[0, 4, 4, 0]}
                              fill={theme.palette.primary.main}
                              name="Page Views"
                            />
                          </BarChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>
                  </motion.div>
                )}

                {/* Sessions by Source - Donut Chart & Bar Chart */}
                {dashboardData.chart_data?.traffic_sources && dashboardData.chart_data.traffic_sources.length > 0 && (
                  <Grid container spacing={3} sx={{ mb: 3 }}>
                    {/* Donut Chart */}
                    <Grid item xs={12} md={6}>
                      <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5, delay: 0.4 }}
                      >
                        <Card sx={{ height: '100%', borderRadius: 2, border: `1px solid ${theme.palette.divider}`, boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
                          <CardContent sx={{ p: 3 }}>
                            <Typography 
                              variant="h6" 
                              mb={2} 
                              fontWeight={600}
                              sx={{ fontSize: '1.125rem', letterSpacing: '-0.01em' }}
                            >
                              Traffic Sources Distribution
                            </Typography>
                            <ResponsiveContainer width="100%" height={300}>
                              <PieChart>
                                <Pie
                                  data={dashboardData.chart_data.traffic_sources.slice(0, 6).map((item) => ({
                                    name: item.source || 'Unknown',
                                    value: item.sessions || 0,
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
                                  {dashboardData.chart_data.traffic_sources.slice(0, 6).map((entry, index) => {
                                    const colors = [
                                      theme.palette.primary.main,
                                      theme.palette.secondary.main,
                                      theme.palette.success.main,
                                      theme.palette.warning.main,
                                      theme.palette.error.main,
                                      theme.palette.info.main
                                    ]
                                    return <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                                  })}
                                </Pie>
                                <Tooltip 
                                  contentStyle={{ 
                                    borderRadius: '8px', 
                                    border: 'none', 
                                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                                    backgroundColor: '#FFFFFF'
                                  }}
                                  formatter={(value) => [value.toLocaleString(), 'Sessions']}
                                />
                                <Legend 
                                  wrapperStyle={{ paddingTop: '20px' }}
                                  formatter={(value) => value.length > 15 ? value.substring(0, 15) + '...' : value}
                                />
                              </PieChart>
                            </ResponsiveContainer>
                          </CardContent>
                        </Card>
                      </motion.div>
                    </Grid>

                    {/* Horizontal Bar Chart */}
                    <Grid item xs={12} md={6}>
                      <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5, delay: 0.45 }}
                      >
                        <Card sx={{ height: '100%', borderRadius: 2, border: `1px solid ${theme.palette.divider}`, boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
                          <CardContent sx={{ p: 3 }}>
                            <Typography 
                              variant="h6" 
                              mb={2} 
                              fontWeight={600}
                              sx={{ fontSize: '1.125rem', letterSpacing: '-0.01em' }}
                            >
                              Sessions by Channel
                            </Typography>
                            <ResponsiveContainer width="100%" height={300}>
                              <BarChart
                                data={dashboardData.chart_data.traffic_sources.slice(0, 8).map(item => ({
                                  ...item,
                                  displayName: item.channel || item.source || 'Unknown'
                                }))}
                                layout="vertical"
                                margin={{ top: 5, right: 30, left: 80, bottom: 5 }}
                              >
                                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#E4E4E7" />
                                <XAxis type="number" tick={{ fontSize: 12 }} stroke="#71717A" />
                                <YAxis 
                                  dataKey="displayName" 
                                  type="category" 
                                  width={75} 
                                  stroke="#71717A"
                                  tick={{ fontSize: 11 }}
                                />
                                <Tooltip 
                                  contentStyle={{ 
                                    borderRadius: '8px', 
                                    border: 'none', 
                                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                                    backgroundColor: '#FFFFFF'
                                  }}
                                  formatter={(value) => [value.toLocaleString(), 'Sessions']}
                                />
                                <Legend />
                                <Bar 
                                  dataKey="sessions" 
                                  radius={[0, 4, 4, 0]}
                                  fill={theme.palette.primary.main}
                                  name="Sessions"
                                />
                              </BarChart>
                            </ResponsiveContainer>
                          </CardContent>
                        </Card>
                      </motion.div>
                    </Grid>
                  </Grid>
                )}

                {/* Stacked Bar Chart - Sessions vs Users by Source */}
                {dashboardData.chart_data?.traffic_sources && dashboardData.chart_data.traffic_sources.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5, delay: 0.5 }}
                  >
                    <Card sx={{ mb: 3, borderRadius: 2, border: `1px solid ${theme.palette.divider}`, boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
                      <CardContent sx={{ p: 3 }}>
                        <Typography 
                          variant="h6" 
                          mb={2} 
                          fontWeight={600}
                          sx={{ fontSize: '1.125rem', letterSpacing: '-0.01em' }}
                        >
                          Sessions vs Users by Source
                        </Typography>
                        <ResponsiveContainer width="100%" height={350}>
                          <BarChart
                            data={dashboardData.chart_data.traffic_sources.slice(0, 8)}
                            margin={{ top: 5, right: 30, left: 20, bottom: 60 }}
                          >
                            <CartesianGrid strokeDasharray="3 3" stroke="#E4E4E7" />
                            <XAxis 
                              dataKey="source" 
                              tick={{ fontSize: 11 }}
                              stroke="#71717A"
                              angle={-45}
                              textAnchor="end"
                              height={80}
                            />
                            <YAxis tick={{ fontSize: 12 }} stroke="#71717A" />
                            <Tooltip 
                              contentStyle={{ 
                                borderRadius: '8px', 
                                border: 'none', 
                                boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                                backgroundColor: '#FFFFFF'
                              }}
                              formatter={(value) => [value.toLocaleString(), '']}
                            />
                            <Legend />
                            <Bar 
                              dataKey="sessions" 
                              stackId="a" 
                              fill={theme.palette.primary.main}
                              name="Sessions"
                              radius={[0, 0, 0, 0]}
                            />
                            <Bar 
                              dataKey="users" 
                              stackId="a" 
                              fill={theme.palette.secondary.main}
                              name="Users"
                              radius={[4, 4, 0, 0]}
                            />
                          </BarChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>
                  </motion.div>
                )}

                {/* Geographic Breakdown - Bar Chart & Pie Chart */}
                {dashboardData.chart_data?.geographic_breakdown && dashboardData.chart_data.geographic_breakdown.length > 0 && (
                  <Grid container spacing={3} sx={{ mb: 3 }}>
                    {/* Bar Chart */}
                    <Grid item xs={12} md={7}>
                      <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5, delay: 0.55 }}
                      >
                        <Card sx={{ height: '100%', borderRadius: 2, border: `1px solid ${theme.palette.divider}`, boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
                          <CardContent sx={{ p: 3 }}>
                            <Typography 
                              variant="h6" 
                              mb={2} 
                              fontWeight={600}
                              sx={{ fontSize: '1.125rem', letterSpacing: '-0.01em' }}
                            >
                              Geographic Distribution
                            </Typography>
                            <ResponsiveContainer width="100%" height={350}>
                              <BarChart
                                data={dashboardData.chart_data.geographic_breakdown.slice(0, 10)}
                                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                              >
                                <CartesianGrid strokeDasharray="3 3" stroke="#E4E4E7" />
                                <XAxis 
                                  dataKey="country" 
                                  tick={{ fontSize: 11 }}
                                  stroke="#71717A"
                                  angle={-45}
                                  textAnchor="end"
                                  height={80}
                                />
                                <YAxis tick={{ fontSize: 12 }} stroke="#71717A" />
                                <Tooltip 
                                  contentStyle={{ 
                                    borderRadius: '8px', 
                                    border: 'none', 
                                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                                    backgroundColor: '#FFFFFF'
                                  }}
                                  formatter={(value) => [value.toLocaleString(), 'Sessions']}
                                />
                                <Legend />
                                <Bar 
                                  dataKey="sessions" 
                                  radius={[4, 4, 0, 0]}
                                  fill={theme.palette.primary.main}
                                  name="Sessions"
                                />
                              </BarChart>
                            </ResponsiveContainer>
                          </CardContent>
                        </Card>
                      </motion.div>
                    </Grid>

                    {/* Pie Chart */}
                    <Grid item xs={12} md={5}>
                      <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5, delay: 0.6 }}
                      >
                        <Card sx={{ height: '100%', borderRadius: 2, border: `1px solid ${theme.palette.divider}`, boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
                          <CardContent sx={{ p: 3 }}>
                            <Typography 
                              variant="h6" 
                              mb={2} 
                              fontWeight={600}
                              sx={{ fontSize: '1.125rem', letterSpacing: '-0.01em' }}
                            >
                              Top Countries
                            </Typography>
                            <ResponsiveContainer width="100%" height={350}>
                              <PieChart>
                                <Pie
                                  data={dashboardData.chart_data.geographic_breakdown.slice(0, 6).map((item) => ({
                                    name: item.country || 'Unknown',
                                    value: item.sessions || 0,
                                  }))}
                                  cx="50%"
                                  cy="50%"
                                  labelLine={false}
                                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                                  outerRadius={100}
                                  fill="#8884d8"
                                  dataKey="value"
                                >
                                  {dashboardData.chart_data.geographic_breakdown.slice(0, 6).map((entry, index) => {
                                    const colors = [
                                      theme.palette.primary.main,
                                      theme.palette.secondary.main,
                                      theme.palette.success.main,
                                      theme.palette.warning.main,
                                      theme.palette.error.main,
                                      theme.palette.info.main
                                    ]
                                    return <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                                  })}
                                </Pie>
                                <Tooltip 
                                  contentStyle={{ 
                                    borderRadius: '8px', 
                                    border: 'none', 
                                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                                    backgroundColor: '#FFFFFF'
                                  }}
                                  formatter={(value) => [value.toLocaleString(), 'Users']}
                                />
                                <Legend 
                                  wrapperStyle={{ paddingTop: '20px' }}
                                />
                              </PieChart>
                            </ResponsiveContainer>
                          </CardContent>
                        </Card>
                      </motion.div>
                    </Grid>
                  </Grid>
                )}

                {/* Performance Metrics - Donut Charts */}
                <Typography 
                  variant="h6" 
                  fontWeight={600} 
                  mb={2}
                  sx={{ fontSize: '1.125rem', letterSpacing: '-0.01em' }}
                >
                  Performance Metrics
                </Typography>
                <Grid container spacing={3} sx={{ mb: 4 }}>
                  {/* Bounce Rate Donut */}
                  {dashboardData?.kpis?.bounce_rate && (
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

              {/* GA4 Performance Charts - Prominent Line Graphs */}
              {dashboardData.chart_data?.ga4_daily_comparison?.length > 0 && (
                <Box sx={{ mt: 4 }}>
                  <Grid container spacing={3}>
                    {/* Total Users Chart - Full Width (Primary Chart) */}
                    <Grid item xs={12}>
                      <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5, delay: 0.3 }}
                      >
                        <Card 
                          sx={{ 
                            height: 500,
                            border: `1px solid ${theme.palette.divider}`,
                            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                          }}
                        >
                          <CardContent sx={{ p: 3 }}>
                            <Box display="flex" alignItems="center" justifyContent="space-between" mb={3}>
                              <Typography variant="h6" fontWeight={600} sx={{ fontSize: '1.125rem' }}>
                                Total Users
                              </Typography>
                              <Chip
                                label="GA4"
                                size="small"
                                sx={{
                                  bgcolor: alpha(theme.palette.primary.main, 0.1),
                                  color: theme.palette.primary.main,
                                  fontWeight: 600,
                                  fontSize: '10px',
                                  height: 20,
                                  borderRadius: '4px',
                                  border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`
                                }}
                              />
                            </Box>
                            <ResponsiveContainer width="100%" height={400}>
                              <LineChart 
                                data={dashboardData.chart_data.ga4_daily_comparison}
                                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                              >
                                <CartesianGrid strokeDasharray="3 3" stroke="#E4E4E7" />
                                <XAxis 
                                  dataKey="date" 
                                  tick={{ fontSize: 12 }}
                                  stroke="#71717A"
                                  tickFormatter={(value) => {
                                    if (value && value.length === 8) {
                                      const month = value.substring(4, 6)
                                      const day = value.substring(6, 8)
                                      return `${day} ${getMonthName(parseInt(month))}`
                                    }
                                    return value
                                  }}
                                />
                                <YAxis 
                                  tick={{ fontSize: 12 }}
                                  stroke="#71717A"
                                />
                                <Tooltip 
                                  contentStyle={{ 
                                    borderRadius: '8px', 
                                    border: 'none', 
                                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                                    backgroundColor: '#FFFFFF'
                                  }}
                                  labelFormatter={(value) => {
                                    if (value && value.length === 8) {
                                      const year = value.substring(0, 4)
                                      const month = value.substring(4, 6)
                                      const day = value.substring(6, 8)
                                      return `${day} ${getMonthName(parseInt(month))} ${year}`
                                    }
                                    return value
                                  }}
                                />
                                <Legend 
                                  wrapperStyle={{ paddingTop: '20px' }}
                                />
                                <Line 
                                  type="monotone" 
                                  dataKey="current_users" 
                                  name={getDateRangeLabel()}
                                  stroke={theme.palette.primary.main} 
                                  strokeWidth={3}
                                  dot={{ fill: theme.palette.primary.main, r: 5 }}
                                  activeDot={{ r: 7 }}
                                />
                                {shouldShowChangePeriod && shouldShowChangePeriod("ga4") && (
                                  <Line 
                                    type="monotone" 
                                    dataKey="previous_users" 
                                    name="Previous period"
                                    stroke={theme.palette.grey[400]} 
                                    strokeWidth={2.5}
                                    strokeDasharray="5 5"
                                    dot={{ fill: theme.palette.grey[400], r: 4 }}
                                    activeDot={{ r: 6 }}
                                  />
                                )}
                              </LineChart>
                            </ResponsiveContainer>
                          </CardContent>
                        </Card>
                      </motion.div>
                    </Grid>

                    {/* Sessions Comparison Chart */}
                    <Grid item xs={12} md={6}>
                      <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5, delay: 0.35 }}
                      >
                        <Card 
                          sx={{ 
                            height: 400,
                            border: `1px solid ${theme.palette.divider}`,
                            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                          }}
                        >
                          <CardContent sx={{ p: 3 }}>
                            <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                              <Typography variant="h6" fontWeight={600} sx={{ fontSize: '1rem' }}>Sessions</Typography>
                              <Chip
                                label="GA4"
                                size="small"
                                sx={{
                                  bgcolor: alpha(theme.palette.primary.main, 0.1),
                                  color: theme.palette.primary.main,
                                  fontWeight: 600,
                                  fontSize: '10px',
                                  height: 20,
                                  borderRadius: '4px',
                                  border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`
                                }}
                              />
                            </Box>
                            <ResponsiveContainer width="100%" height={320}>
                              <LineChart 
                                data={dashboardData.chart_data.ga4_daily_comparison}
                                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                              >
                                <CartesianGrid strokeDasharray="3 3" stroke="#E4E4E7" />
                                <XAxis 
                                  dataKey="date" 
                                  tick={{ fontSize: 11 }}
                                  stroke="#71717A"
                                  tickFormatter={(value) => {
                                    if (value && value.length === 8) {
                                      const month = value.substring(4, 6)
                                      const day = value.substring(6, 8)
                                      return `${day} ${getMonthName(parseInt(month))}`
                                    }
                                    return value
                                  }}
                                />
                                <YAxis 
                                  tick={{ fontSize: 12 }}
                                  stroke="#71717A"
                                />
                                <Tooltip 
                                  contentStyle={{ 
                                    borderRadius: '8px', 
                                    border: 'none', 
                                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                                    backgroundColor: '#FFFFFF'
                                  }}
                                  labelFormatter={(value) => {
                                    if (value && value.length === 8) {
                                      const year = value.substring(0, 4)
                                      const month = value.substring(4, 6)
                                      const day = value.substring(6, 8)
                                      return `${day} ${getMonthName(parseInt(month))} ${year}`
                                    }
                                    return value
                                  }}
                                />
                                <Legend wrapperStyle={{ paddingTop: '10px' }} />
                                <Line 
                                  type="monotone" 
                                  dataKey="current_sessions" 
                                  name={getDateRangeLabel()}
                                  stroke={theme.palette.primary.main} 
                                  strokeWidth={3}
                                  dot={{ fill: theme.palette.primary.main, r: 4 }}
                                  activeDot={{ r: 6 }}
                                />
                                {shouldShowChangePeriod && shouldShowChangePeriod("ga4") && (
                                  <Line 
                                    type="monotone" 
                                    dataKey="previous_sessions" 
                                    name="Previous period"
                                    stroke={theme.palette.grey[400]} 
                                    strokeWidth={2.5}
                                    strokeDasharray="5 5"
                                    dot={{ fill: theme.palette.grey[400], r: 3 }}
                                    activeDot={{ r: 5 }}
                                  />
                                )}
                              </LineChart>
                            </ResponsiveContainer>
                          </CardContent>
                        </Card>
                      </motion.div>
                    </Grid>

                    {/* New Users Comparison Chart */}
                    <Grid item xs={12} md={6}>
                      <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5, delay: 0.4 }}
                      >
                        <Card 
                          sx={{ 
                            height: 400,
                            border: `1px solid ${theme.palette.divider}`,
                            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                          }}
                        >
                          <CardContent sx={{ p: 3 }}>
                            <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                              <Typography variant="h6" fontWeight={600} sx={{ fontSize: '1rem' }}>New Users</Typography>
                              <Chip
                                label="GA4"
                                size="small"
                                sx={{
                                  bgcolor: alpha(theme.palette.primary.main, 0.1),
                                  color: theme.palette.primary.main,
                                  fontWeight: 600,
                                  fontSize: '10px',
                                  height: 20,
                                  borderRadius: '4px',
                                  border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`
                                }}
                              />
                            </Box>
                            <ResponsiveContainer width="100%" height={320}>
                              <LineChart 
                                data={dashboardData.chart_data.ga4_daily_comparison}
                                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                              >
                                <CartesianGrid strokeDasharray="3 3" stroke="#E4E4E7" />
                                <XAxis 
                                  dataKey="date" 
                                  tick={{ fontSize: 11 }}
                                  stroke="#71717A"
                                  tickFormatter={(value) => {
                                    if (value && value.length === 8) {
                                      const month = value.substring(4, 6)
                                      const day = value.substring(6, 8)
                                      return `${day} ${getMonthName(parseInt(month))}`
                                    }
                                    return value
                                  }}
                                />
                                <YAxis 
                                  tick={{ fontSize: 12 }}
                                  stroke="#71717A"
                                />
                                <Tooltip 
                                  contentStyle={{ 
                                    borderRadius: '8px', 
                                    border: 'none', 
                                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                                    backgroundColor: '#FFFFFF'
                                  }}
                                  labelFormatter={(value) => {
                                    if (value && value.length === 8) {
                                      const year = value.substring(0, 4)
                                      const month = value.substring(4, 6)
                                      const day = value.substring(6, 8)
                                      return `${day} ${getMonthName(parseInt(month))} ${year}`
                                    }
                                    return value
                                  }}
                                />
                                <Legend wrapperStyle={{ paddingTop: '10px' }} />
                                <Line 
                                  type="monotone" 
                                  dataKey="current_new_users" 
                                  name={getDateRangeLabel()}
                                  stroke={theme.palette.success.main} 
                                  strokeWidth={3}
                                  dot={{ fill: theme.palette.success.main, r: 4 }}
                                  activeDot={{ r: 6 }}
                                />
                                {shouldShowChangePeriod && shouldShowChangePeriod("ga4") && (
                                  <Line 
                                    type="monotone" 
                                    dataKey="previous_new_users" 
                                    name="Previous period"
                                    stroke={theme.palette.grey[400]} 
                                    strokeWidth={2.5}
                                    strokeDasharray="5 5"
                                    dot={{ fill: theme.palette.grey[400], r: 3 }}
                                    activeDot={{ r: 5 }}
                                  />
                                )}
                              </LineChart>
                            </ResponsiveContainer>
                          </CardContent>
                        </Card>
                      </motion.div>
                    </Grid>

                    {/* Conversions Comparison Chart */}
                    {dashboardData.chart_data.ga4_daily_comparison.some(d => d.current_conversions > 0 || d.previous_conversions > 0) && (
                      <Grid item xs={12} md={6}>
                        <motion.div
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ duration: 0.5, delay: 0.45 }}
                        >
                          <Card sx={{ height: 400 }}>
                            <CardContent sx={{ p: 3 }}>
                              <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                                <Typography variant="h6" fontWeight={600}>Conversions</Typography>
                                <Chip
                                  label="GA4"
                                  size="small"
                                  sx={{
                                    bgcolor: alpha(theme.palette.primary.main, 0.1),
                                    color: theme.palette.primary.main,
                                    fontWeight: 600,
                                    fontSize: '10px',
                                    height: 20,
                                    borderRadius: '4px',
                                    border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`
                                  }}
                                />
                              </Box>
                              <ResponsiveContainer width="100%" height={320}>
                                <LineChart 
                                  data={dashboardData.chart_data.ga4_daily_comparison}
                                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                                >
                                  <CartesianGrid strokeDasharray="3 3" stroke="#E4E4E7" />
                                  <XAxis 
                                    dataKey="date" 
                                    tick={{ fontSize: 11 }}
                                    stroke="#71717A"
                                    tickFormatter={(value) => {
                                      if (value && value.length === 8) {
                                        const day = value.substring(6, 8)
                                        return day
                                      }
                                      return value
                                    }}
                                  />
                                  <YAxis 
                                    tick={{ fontSize: 12 }}
                                    stroke="#71717A"
                                  />
                                  <Tooltip 
                                    contentStyle={{ 
                                      borderRadius: '8px', 
                                      border: 'none', 
                                      boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                                      backgroundColor: '#FFFFFF'
                                    }}
                                    labelFormatter={(value) => {
                                      if (value && value.length === 8) {
                                        const year = value.substring(0, 4)
                                        const month = value.substring(4, 6)
                                        const day = value.substring(6, 8)
                                        return `${day} ${getMonthName(parseInt(month))} ${year}`
                                      }
                                      return value
                                    }}
                                  />
                                  <Legend />
                                  <Line 
                                    type="monotone" 
                                    dataKey="current_conversions" 
                                    name={getDateRangeLabel()}
                                    stroke={theme.palette.warning.main} 
                                    strokeWidth={2.5}
                                    dot={{ fill: theme.palette.warning.main, r: 3 }}
                                  />
                                    {shouldShowChangePeriod && shouldShowChangePeriod("ga4") && (
                                      <Line 
                                        type="monotone" 
                                        dataKey="previous_conversions" 
                                        name="Previous period"
                                        stroke={theme.palette.grey[400]} 
                                        strokeWidth={2}
                                        strokeDasharray="5 5"
                                        dot={{ fill: theme.palette.grey[400], r: 2 }}
                                      />
                                    )}
                                </LineChart>
                              </ResponsiveContainer>
                            </CardContent>
                          </Card>
                        </motion.div>
                      </Grid>
                    )}

                    {/* Revenue Comparison Chart */}
                    {dashboardData.chart_data.ga4_daily_comparison.some(d => d.current_revenue > 0 || d.previous_revenue > 0) && (
                      <Grid item xs={12} md={6}>
                        <motion.div
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ duration: 0.5, delay: 0.5 }}
                        >
                          <Card sx={{ height: 400 }}>
                            <CardContent sx={{ p: 3 }}>
                              <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                                <Typography variant="h6" fontWeight={600}>Revenue</Typography>
                                <Chip
                                  label="GA4"
                                  size="small"
                                  sx={{
                                    bgcolor: alpha(theme.palette.primary.main, 0.1),
                                    color: theme.palette.primary.main,
                                    fontWeight: 600,
                                    fontSize: '10px',
                                    height: 20,
                                    borderRadius: '4px',
                                    border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`
                                  }}
                                />
                              </Box>
                              <ResponsiveContainer width="100%" height={320}>
                                <LineChart 
                                  data={dashboardData.chart_data.ga4_daily_comparison}
                                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                                >
                                  <CartesianGrid strokeDasharray="3 3" stroke="#E4E4E7" />
                                  <XAxis 
                                    dataKey="date" 
                                    tick={{ fontSize: 11 }}
                                    stroke="#71717A"
                                    tickFormatter={(value) => {
                                      if (value && value.length === 8) {
                                        const day = value.substring(6, 8)
                                        return day
                                      }
                                      return value
                                    }}
                                  />
                                  <YAxis 
                                    tick={{ fontSize: 12 }}
                                    stroke="#71717A"
                                    tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                                  />
                                  <Tooltip 
                                    contentStyle={{ 
                                      borderRadius: '8px', 
                                      border: 'none', 
                                      boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                                      backgroundColor: '#FFFFFF'
                                    }}
                                    labelFormatter={(value) => {
                                      if (value && value.length === 8) {
                                        const year = value.substring(0, 4)
                                        const month = value.substring(4, 6)
                                        const day = value.substring(6, 8)
                                        return `${day} ${getMonthName(parseInt(month))} ${year}`
                                      }
                                      return value
                                    }}
                                    formatter={(value) => `$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
                                  />
                                  <Legend />
                                  <Line 
                                    type="monotone" 
                                    dataKey="current_revenue" 
                                    name={getDateRangeLabel()}
                                    stroke={theme.palette.success.main} 
                                    strokeWidth={2.5}
                                    dot={{ fill: theme.palette.success.main, r: 3 }}
                                  />
                                    {shouldShowChangePeriod && shouldShowChangePeriod("ga4") && (
                                      <Line 
                                        type="monotone" 
                                        dataKey="previous_revenue" 
                                        name="Previous period"
                                        stroke={theme.palette.grey[400]} 
                                        strokeWidth={2}
                                        strokeDasharray="5 5"
                                        dot={{ fill: theme.palette.grey[400], r: 2 }}
                                      />
                                    )}
                                </LineChart>
                              </ResponsiveContainer>
                            </CardContent>
                          </Card>
                        </motion.div>
                      </Grid>
                    )}
                  </Grid>
                </Box>
              )}

              {/* Top Performing Pages - Horizontal Bar Chart */}
              {dashboardData.chart_data?.top_pages && dashboardData.chart_data.top_pages.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: 0.9 }}
                >
                  <Card sx={{ mb: 3, borderRadius: 2, border: `1px solid ${theme.palette.divider}`, boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
                    <CardContent sx={{ p: 3 }}>
                      <Typography 
                        variant="h6" 
                        mb={2} 
                        fontWeight={600}
                        sx={{ fontSize: '1.125rem', letterSpacing: '-0.01em' }}
                      >
                        Top Performing Pages
                      </Typography>
                      <ResponsiveContainer width="100%" height={400}>
                        <BarChart
                          data={dashboardData.chart_data.top_pages.slice(0, 10)}
                          layout="vertical"
                          margin={{ top: 5, right: 30, left: 150, bottom: 5 }}
                        >
                          <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#E4E4E7" />
                          <XAxis type="number" tick={{ fontSize: 12 }} stroke="#71717A" />
                          <YAxis 
                            dataKey="pagePath" 
                            type="category" 
                            width={140} 
                            stroke="#71717A"
                            tick={{ fontSize: 10 }}
                            tickFormatter={(value) => {
                              if (!value) return 'N/A'
                              const path = value.length > 30 ? value.substring(0, 30) + '...' : value
                              return path
                            }}
                          />
                          <Tooltip 
                            contentStyle={{ 
                              borderRadius: '8px', 
                              border: 'none', 
                              boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                              backgroundColor: '#FFFFFF'
                            }}
                            formatter={(value) => [value.toLocaleString(), 'Views']}
                          />
                          <Legend />
                          <Bar 
                            dataKey="views" 
                            radius={[0, 4, 4, 0]}
                            fill={theme.palette.primary.main}
                            name="Page Views"
                          />
                        </BarChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>
                </motion.div>
              )}

              {/* Sessions by Source - Donut Chart & Bar Chart */}
              {dashboardData.chart_data?.traffic_sources && dashboardData.chart_data.traffic_sources.length > 0 && (
                <Grid container spacing={3} sx={{ mb: 3 }}>
                  {/* Donut Chart */}
                  <Grid item xs={12} md={6}>
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.5, delay: 1.0 }}
                    >
                      <Card sx={{ height: '100%', borderRadius: 2, border: `1px solid ${theme.palette.divider}`, boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
                        <CardContent sx={{ p: 3 }}>
                          <Typography 
                            variant="h6" 
                            mb={2} 
                            fontWeight={600}
                            sx={{ fontSize: '1.125rem', letterSpacing: '-0.01em' }}
                          >
                            Traffic Sources Distribution
                          </Typography>
                          <ResponsiveContainer width="100%" height={300}>
                            <PieChart>
                              <Pie
                                data={dashboardData.chart_data.traffic_sources.slice(0, 6).map((item) => ({
                                  name: item.source || 'Unknown',
                                  value: item.sessions || 0,
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
                                {dashboardData.chart_data.traffic_sources.slice(0, 6).map((entry, index) => {
                                  const colors = [
                                    theme.palette.primary.main,
                                    theme.palette.secondary.main,
                                    theme.palette.success.main,
                                    theme.palette.warning.main,
                                    theme.palette.error.main,
                                    theme.palette.info.main
                                  ]
                                  return <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                                })}
                              </Pie>
                              <Tooltip 
                                contentStyle={{ 
                                  borderRadius: '8px', 
                                  border: 'none', 
                                  boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                                  backgroundColor: '#FFFFFF'
                                }}
                                formatter={(value) => [value.toLocaleString(), 'Sessions']}
                              />
                              <Legend 
                                wrapperStyle={{ paddingTop: '20px' }}
                                formatter={(value) => value.length > 15 ? value.substring(0, 15) + '...' : value}
                              />
                            </PieChart>
                          </ResponsiveContainer>
                        </CardContent>
                      </Card>
                    </motion.div>
                  </Grid>

                  {/* Horizontal Bar Chart */}
                  <Grid item xs={12} md={6}>
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.5, delay: 1.05 }}
                    >
                      <Card sx={{ height: '100%', borderRadius: 2, border: `1px solid ${theme.palette.divider}`, boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
                        <CardContent sx={{ p: 3 }}>
                          <Typography 
                            variant="h6" 
                            mb={2} 
                            fontWeight={600}
                            sx={{ fontSize: '1.125rem', letterSpacing: '-0.01em' }}
                          >
                            Sessions by Source
                          </Typography>
                          <ResponsiveContainer width="100%" height={300}>
                            <BarChart
                              data={dashboardData.chart_data.traffic_sources.slice(0, 8)}
                              layout="vertical"
                              margin={{ top: 5, right: 30, left: 80, bottom: 5 }}
                            >
                              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#E4E4E7" />
                              <XAxis type="number" tick={{ fontSize: 12 }} stroke="#71717A" />
                              <YAxis 
                                dataKey="source" 
                                type="category" 
                                width={75} 
                                stroke="#71717A"
                                tick={{ fontSize: 11 }}
                              />
                              <Tooltip 
                                contentStyle={{ 
                                  borderRadius: '8px', 
                                  border: 'none', 
                                  boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                                  backgroundColor: '#FFFFFF'
                                }}
                                formatter={(value) => [value.toLocaleString(), 'Sessions']}
                              />
                              <Legend />
                              <Bar 
                                dataKey="sessions" 
                                radius={[0, 4, 4, 0]}
                                fill={theme.palette.primary.main}
                                name="Sessions"
                              />
                            </BarChart>
                          </ResponsiveContainer>
                        </CardContent>
                      </Card>
                    </motion.div>
                  </Grid>
                </Grid>
              )}

              {/* Stacked Bar Chart - Sessions vs Users by Source */}
              {dashboardData.chart_data?.traffic_sources && dashboardData.chart_data.traffic_sources.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: 1.1 }}
                >
                  <Card sx={{ mb: 3, borderRadius: 2, border: `1px solid ${theme.palette.divider}`, boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
                    <CardContent sx={{ p: 3 }}>
                      <Typography 
                        variant="h6" 
                        mb={2} 
                        fontWeight={600}
                        sx={{ fontSize: '1.125rem', letterSpacing: '-0.01em' }}
                      >
                        Sessions vs Users by Channel
                      </Typography>
                      <ResponsiveContainer width="100%" height={350}>
                        <BarChart
                          data={dashboardData.chart_data.traffic_sources.slice(0, 8).map(item => ({
                            ...item,
                            displayName: item.channel || item.source || 'Unknown'
                          }))}
                          margin={{ top: 5, right: 30, left: 20, bottom: 60 }}
                        >
                          <CartesianGrid strokeDasharray="3 3" stroke="#E4E4E7" />
                          <XAxis 
                            dataKey="displayName" 
                            tick={{ fontSize: 11 }}
                            stroke="#71717A"
                            angle={-45}
                            textAnchor="end"
                            height={80}
                          />
                          <YAxis tick={{ fontSize: 12 }} stroke="#71717A" />
                          <Tooltip 
                            contentStyle={{ 
                              borderRadius: '8px', 
                              border: 'none', 
                              boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                              backgroundColor: '#FFFFFF'
                            }}
                            formatter={(value) => [value.toLocaleString(), '']}
                          />
                          <Legend />
                          <Bar 
                            dataKey="sessions" 
                            stackId="a" 
                            fill={theme.palette.primary.main}
                            name="Sessions"
                            radius={[0, 0, 0, 0]}
                          />
                          <Bar 
                            dataKey="users" 
                            stackId="a" 
                            fill={theme.palette.secondary.main}
                            name="Users"
                            radius={[4, 4, 0, 0]}
                          />
                        </BarChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>
                </motion.div>
              )}

              {/* Geographic Breakdown - Bar Chart & Pie Chart */}
              {dashboardData.chart_data?.geographic_breakdown && dashboardData.chart_data.geographic_breakdown.length > 0 && (
                <Grid container spacing={3} sx={{ mb: 3 }}>
                  {/* Bar Chart */}
                  <Grid item xs={12} md={7}>
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.5, delay: 1.2 }}
                    >
                      <Card sx={{ height: '100%', borderRadius: 2, border: `1px solid ${theme.palette.divider}`, boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
                        <CardContent sx={{ p: 3 }}>
                          <Typography 
                            variant="h6" 
                            mb={2} 
                            fontWeight={600}
                            sx={{ fontSize: '1.125rem', letterSpacing: '-0.01em' }}
                          >
                            Geographic Distribution
                          </Typography>
                          <ResponsiveContainer width="100%" height={350}>
                            <BarChart
                              data={dashboardData.chart_data.geographic_breakdown.slice(0, 10)}
                              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                            >
                              <CartesianGrid strokeDasharray="3 3" stroke="#E4E4E7" />
                              <XAxis 
                                dataKey="country" 
                                tick={{ fontSize: 11 }}
                                stroke="#71717A"
                                angle={-45}
                                textAnchor="end"
                                height={80}
                              />
                              <YAxis tick={{ fontSize: 12 }} stroke="#71717A" />
                              <Tooltip 
                                contentStyle={{ 
                                  borderRadius: '8px', 
                                  border: 'none', 
                                  boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                                  backgroundColor: '#FFFFFF'
                                }}
                                formatter={(value) => [value.toLocaleString(), 'Sessions']}
                              />
                              <Legend />
                              <Bar 
                                dataKey="sessions" 
                                radius={[4, 4, 0, 0]}
                                fill={theme.palette.primary.main}
                                name="Sessions"
                              />
                            </BarChart>
                          </ResponsiveContainer>
                        </CardContent>
                      </Card>
                    </motion.div>
                  </Grid>

                  {/* Pie Chart */}
                  <Grid item xs={12} md={5}>
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.5, delay: 1.25 }}
                    >
                      <Card sx={{ height: '100%', borderRadius: 2, border: `1px solid ${theme.palette.divider}`, boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
                        <CardContent sx={{ p: 3 }}>
                          <Typography 
                            variant="h6" 
                            mb={2} 
                            fontWeight={600}
                            sx={{ fontSize: '1.125rem', letterSpacing: '-0.01em' }}
                          >
                            Top Countries
                          </Typography>
                          <ResponsiveContainer width="100%" height={350}>
                            <PieChart>
                              <Pie
                                data={dashboardData.chart_data.geographic_breakdown.slice(0, 6).map((item) => ({
                                  name: item.country || 'Unknown',
                                  value: item.sessions || 0,
                                }))}
                                cx="50%"
                                cy="50%"
                                labelLine={false}
                                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                                outerRadius={100}
                                fill="#8884d8"
                                dataKey="value"
                              >
                                {dashboardData.chart_data.geographic_breakdown.slice(0, 6).map((entry, index) => {
                                  const colors = [
                                    theme.palette.primary.main,
                                    theme.palette.secondary.main,
                                    theme.palette.success.main,
                                    theme.palette.warning.main,
                                    theme.palette.error.main,
                                    theme.palette.info.main
                                  ]
                                  return <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                                })}
                              </Pie>
                              <Tooltip 
                                contentStyle={{ 
                                  borderRadius: '8px', 
                                  border: 'none', 
                                  boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                                  backgroundColor: '#FFFFFF'
                                }}
                                formatter={(value) => [value.toLocaleString(), 'Sessions']}
                              />
                              <Legend 
                                wrapperStyle={{ paddingTop: '20px' }}
                              />
                            </PieChart>
                          </ResponsiveContainer>
                        </CardContent>
                      </Card>
                    </motion.div>
                  </Grid>
                </Grid>
              )}

              {/* KPI Donut Charts - Bounce Rate, Engagement Rate, Brand Presence */}
              <Grid container spacing={3} sx={{ mb: 3 }}>
                {/* Bounce Rate Donut */}
                {dashboardData?.kpis?.bounce_rate && (
                  <Grid item xs={12} sm={6} md={4}>
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.5, delay: 1.3 }}
                    >
                      <Card sx={{ height: '100%', borderRadius: 2, border: `1px solid ${theme.palette.divider}`, boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
                        <CardContent sx={{ p: 3, textAlign: 'center' }}>
                          <Typography 
                            variant="h6" 
                            mb={2} 
                            fontWeight={600}
                            sx={{ fontSize: '1rem', letterSpacing: '-0.01em' }}
                          >
                            Bounce Rate
                          </Typography>
                          <ResponsiveContainer width="100%" height={250}>
                            <PieChart>
                              <Pie
                                data={[
                                  { name: 'Bounced', value: dashboardData.kpis.bounce_rate.value || 0 },
                                  { name: 'Engaged', value: 100 - (dashboardData.kpis.bounce_rate.value || 0) }
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
                                <Cell fill={theme.palette.error.main} />
                                <Cell fill={theme.palette.success.main} />
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
                              color={dashboardData.kpis.bounce_rate.value > 50 ? 'error.main' : 'success.main'}
                            >
                              {(dashboardData.kpis.bounce_rate.value || 0).toFixed(1)}%
                            </Typography>
                            <Typography 
                              variant="caption" 
                              color="text.secondary"
                              sx={{ fontSize: '0.75rem', display: 'block', mt: 0.5 }}
                            >
                              Bounced Sessions
                            </Typography>
                          </Box>
                        </CardContent>
                      </Card>
                    </motion.div>
                  </Grid>
                )}

                {/* Engagement Rate Donut */}
                {dashboardData?.kpis?.ga4_engagement_rate && (
                  <Grid item xs={12} sm={6} md={4}>
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.5, delay: 1.35 }}
                    >
                      <Card sx={{ height: '100%', borderRadius: 2, border: `1px solid ${theme.palette.divider}`, boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
                        <CardContent sx={{ p: 3, textAlign: 'center' }}>
                          <Typography 
                            variant="h6" 
                            mb={2} 
                            fontWeight={600}
                            sx={{ fontSize: '1rem', letterSpacing: '-0.01em' }}
                          >
                            Engagement Rate
                          </Typography>
                          <ResponsiveContainer width="100%" height={250}>
                            <PieChart>
                              <Pie
                                data={[
                                  { name: 'Engaged', value: (dashboardData.kpis.ga4_engagement_rate.value || 0) * 100 },
                                  { name: 'Not Engaged', value: 100 - ((dashboardData.kpis.ga4_engagement_rate.value || 0) * 100) }
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
                              {((dashboardData.kpis.ga4_engagement_rate.value || 0) * 100).toFixed(1)}%
                            </Typography>
                            <Typography 
                              variant="caption" 
                              color="text.secondary"
                              sx={{ fontSize: '0.75rem', display: 'block', mt: 0.5 }}
                            >
                              Engaged Sessions
                            </Typography>
                          </Box>
                        </CardContent>
                      </Card>
                    </motion.div>
                  </Grid>
                )}

                {/* Brand Presence Rate Donut */}
                {dashboardData?.kpis?.brand_presence_rate && (
                  <Grid item xs={12} sm={6} md={4}>
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.5, delay: 1.4 }}
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
                )}
              </Grid>

              {/* Top Keywords Ranking - Bar Chart */}
              {dashboardData.chart_data?.all_keywords_ranking && dashboardData.chart_data.all_keywords_ranking.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: 0.2 }}
                >
                  <Card sx={{ mb: 3, borderRadius: 2, border: `1px solid ${theme.palette.divider}`, boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
                    <CardContent sx={{ p: 3 }}>
                      <Typography 
                        variant="h6" 
                        mb={2} 
                        fontWeight={600}
                        sx={{ fontSize: '1.125rem', letterSpacing: '-0.01em' }}
                      >
                        Top Keywords Ranking
                      </Typography>
                      <ResponsiveContainer width="100%" height={400}>
                        <BarChart
                          data={dashboardData.chart_data.all_keywords_ranking.slice(0, 15).map(kw => ({
                            keyword: kw.keyword || 'Unknown',
                            rank: kw.google_rank || 0,
                            searchVolume: kw.search_volume || 0
                          }))}
                          layout="vertical"
                          margin={{ top: 5, right: 30, left: 120, bottom: 5 }}
                        >
                          <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#E4E4E7" />
                          <XAxis 
                            type="number" 
                            tick={{ fontSize: 12 }} 
                            stroke="#71717A"
                            domain={[0, 100]}
                            reversed
                            label={{ value: 'Ranking Position (Lower is Better)', position: 'insideBottom', offset: -5 }}
                          />
                          <YAxis 
                            dataKey="keyword" 
                            type="category" 
                            width={110} 
                            stroke="#71717A"
                            tick={{ fontSize: 10 }}
                            tickFormatter={(value) => {
                              if (!value) return 'N/A'
                              return value.length > 20 ? value.substring(0, 20) + '...' : value
                            }}
                          />
                          <Tooltip 
                            contentStyle={{ 
                              borderRadius: '8px', 
                              border: 'none', 
                              boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                              backgroundColor: '#FFFFFF'
                            }}
                            formatter={(value, name) => {
                              if (name === 'rank') return [`Position ${value}`, 'Rank']
                              if (name === 'searchVolume') return [value.toLocaleString(), 'Search Volume']
                              return [value, name]
                            }}
                          />
                          <Legend />
                          <Bar 
                            dataKey="rank" 
                            radius={[0, 4, 4, 0]}
                            fill={theme.palette.primary.main}
                            name="Rank"
                          />
                        </BarChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>
                </motion.div>
              )}
    </>
  )
}

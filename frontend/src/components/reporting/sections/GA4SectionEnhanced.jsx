import { Grid, Box } from '@mui/material'
import { useTheme } from '@mui/material'
import SectionContainer from '../SectionContainer'
import ChartCard from '../ChartCard'
import LineChart from '../charts/LineChart'
import PieChart from '../charts/PieChart'
import { CHART_COLORS } from '../constants'
import { formatDateForAxis, getDateRangeLabel } from '../hooks/useChartData'
import { getChannelLabel, getChannelColor } from '../utils'

export default function GA4SectionEnhanced({ 
  dashboardData, 
  startDate, 
  endDate,
  loading = false 
}) {
  const theme = useTheme()

  if (!dashboardData?.kpis?.users && !dashboardData?.chart_data?.ga4_daily_comparison) {
    return null
  }

  const chartData = dashboardData?.chart_data
  const dateRangeLabel = getDateRangeLabel(startDate, endDate)

  // Prepare daily comparison data
  const dailyComparisonData = chartData?.ga4_daily_comparison || []

  // Prepare geographic breakdown
  const geographicData = chartData?.geographic_breakdown
    ?.slice(0, 6)
    .map((item) => ({
      name: item.country || 'Unknown',
      value: item.users || 0,
    })) || []

  // Prepare device breakdown
  const deviceData = chartData?.device_breakdown?.map((item) => ({
    name: item.device_category || 'Unknown',
    value: item.users || 0,
  })) || []

  // Prepare channel breakdown
  const channelData = chartData?.channel_breakdown?.map((item) => ({
    name: getChannelLabel(item.channel || 'Unknown'),
    value: item.users || 0,
    color: getChannelColor(item.channel),
  })) || []

  return (
    <SectionContainer
      title="Google Analytics 4"
      description="Website traffic and engagement metrics"
      loading={loading}
    >
      {/* Daily Comparison Charts */}
      {dailyComparisonData.length > 0 && (
        <Box sx={{ mb: 4 }}>
          <Grid container spacing={3}>
            {/* Users Comparison */}
            <Grid item xs={12} md={6}>
              <ChartCard
                title="Users"
                badge="GA4"
                badgeColor={CHART_COLORS.ga4.primary}
                height={400}
                animationDelay={0.1}
              >
                <LineChart
                  data={dailyComparisonData}
                  dataKey="date"
                  lines={[
                    {
                      dataKey: 'current_users',
                      name: dateRangeLabel,
                      color: CHART_COLORS.comparison.current,
                      strokeWidth: 3,
                    },
                    {
                      dataKey: 'previous_users',
                      name: 'Previous period',
                      color: CHART_COLORS.comparison.previous,
                      strokeWidth: 2.5,
                      strokeDasharray: '5 5',
                    },
                  ]}
                  xAxisFormatter={formatDateForAxis}
                  formatter={(value) => [value.toLocaleString(), 'Users']}
                  labelFormatter={(label) => {
                    if (label && label.length === 8) {
                      const year = label.substring(0, 4)
                      const month = label.substring(4, 6)
                      const day = label.substring(6, 8)
                      const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                      return `${day} ${monthNames[parseInt(month) - 1]} ${year}`
                    }
                    return label
                  }}
                />
              </ChartCard>
            </Grid>

            {/* Sessions Comparison */}
            <Grid item xs={12} md={6}>
              <ChartCard
                title="Sessions"
                badge="GA4"
                badgeColor={CHART_COLORS.ga4.primary}
                height={400}
                animationDelay={0.15}
              >
                <LineChart
                  data={dailyComparisonData}
                  dataKey="date"
                  lines={[
                    {
                      dataKey: 'current_sessions',
                      name: dateRangeLabel,
                      color: CHART_COLORS.comparison.current,
                      strokeWidth: 3,
                    },
                    {
                      dataKey: 'previous_sessions',
                      name: 'Previous period',
                      color: CHART_COLORS.comparison.previous,
                      strokeWidth: 2.5,
                      strokeDasharray: '5 5',
                    },
                  ]}
                  xAxisFormatter={formatDateForAxis}
                  formatter={(value) => [value.toLocaleString(), 'Sessions']}
                  labelFormatter={(label) => {
                    if (label && label.length === 8) {
                      const year = label.substring(0, 4)
                      const month = label.substring(4, 6)
                      const day = label.substring(6, 8)
                      const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                      return `${day} ${monthNames[parseInt(month) - 1]} ${year}`
                    }
                    return label
                  }}
                />
              </ChartCard>
            </Grid>

            {/* New Users Comparison */}
            <Grid item xs={12} md={6}>
              <ChartCard
                title="New Users"
                badge="GA4"
                badgeColor={CHART_COLORS.ga4.primary}
                height={400}
                animationDelay={0.2}
              >
                <LineChart
                  data={dailyComparisonData}
                  dataKey="date"
                  lines={[
                    {
                      dataKey: 'current_new_users',
                      name: dateRangeLabel,
                      color: CHART_COLORS.comparison.current,
                      strokeWidth: 3,
                    },
                    {
                      dataKey: 'previous_new_users',
                      name: 'Previous period',
                      color: CHART_COLORS.comparison.previous,
                      strokeWidth: 2.5,
                      strokeDasharray: '5 5',
                    },
                  ]}
                  xAxisFormatter={formatDateForAxis}
                  formatter={(value) => [value.toLocaleString(), 'New Users']}
                  labelFormatter={(label) => {
                    if (label && label.length === 8) {
                      const year = label.substring(0, 4)
                      const month = label.substring(4, 6)
                      const day = label.substring(6, 8)
                      const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                      return `${day} ${monthNames[parseInt(month) - 1]} ${year}`
                    }
                    return label
                  }}
                />
              </ChartCard>
            </Grid>

            {/* Conversions Comparison */}
            <Grid item xs={12} md={6}>
              <ChartCard
                title="Conversions"
                badge="GA4"
                badgeColor={CHART_COLORS.ga4.primary}
                height={400}
                animationDelay={0.25}
              >
                <LineChart
                  data={dailyComparisonData}
                  dataKey="date"
                  lines={[
                    {
                      dataKey: 'current_conversions',
                      name: dateRangeLabel,
                      color: CHART_COLORS.comparison.current,
                      strokeWidth: 3,
                    },
                    {
                      dataKey: 'previous_conversions',
                      name: 'Previous period',
                      color: CHART_COLORS.comparison.previous,
                      strokeWidth: 2.5,
                      strokeDasharray: '5 5',
                    },
                  ]}
                  xAxisFormatter={formatDateForAxis}
                  formatter={(value) => [value.toLocaleString(), 'Conversions']}
                  labelFormatter={(label) => {
                    if (label && label.length === 8) {
                      const year = label.substring(0, 4)
                      const month = label.substring(4, 6)
                      const day = label.substring(6, 8)
                      const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                      return `${day} ${monthNames[parseInt(month) - 1]} ${year}`
                    }
                    return label
                  }}
                />
              </ChartCard>
            </Grid>
          </Grid>
        </Box>
      )}

      {/* Breakdown Charts */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {/* Geographic Breakdown */}
        {geographicData.length > 0 && (
          <Grid item xs={12} md={6}>
            <ChartCard
              title="Top Countries"
              badge="GA4"
              badgeColor={CHART_COLORS.ga4.primary}
              height={350}
              animationDelay={0.3}
            >
              <PieChart
                data={geographicData}
                donut={true}
                innerRadius={60}
                outerRadius={100}
                colors={CHART_COLORS.palette}
                formatter={(value, name) => {
                  const total = geographicData.reduce((sum, item) => sum + item.value, 0)
                  const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0
                  return [`${value.toLocaleString()} (${percentage}%)`, name]
                }}
              />
            </ChartCard>
          </Grid>
        )}

        {/* Device Breakdown */}
        {deviceData.length > 0 && (
          <Grid item xs={12} md={6}>
            <ChartCard
              title="Device Breakdown"
              badge="GA4"
              badgeColor={CHART_COLORS.ga4.primary}
              height={350}
              animationDelay={0.35}
            >
              <PieChart
                data={deviceData}
                donut={true}
                innerRadius={60}
                outerRadius={100}
                colors={CHART_COLORS.palette}
                formatter={(value, name) => {
                  const total = deviceData.reduce((sum, item) => sum + item.value, 0)
                  const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0
                  return [`${value.toLocaleString()} (${percentage}%)`, name]
                }}
              />
            </ChartCard>
          </Grid>
        )}

        {/* Channel Breakdown */}
        {channelData.length > 0 && (
          <Grid item xs={12} md={6}>
            <ChartCard
              title="Traffic Sources"
              badge="GA4"
              badgeColor={CHART_COLORS.ga4.primary}
              height={350}
              animationDelay={0.4}
            >
              <PieChart
                data={channelData}
                donut={true}
                innerRadius={60}
                outerRadius={100}
                colors={channelData.map((item) => item.color || CHART_COLORS.primary)}
                formatter={(value, name) => {
                  const total = channelData.reduce((sum, item) => sum + item.value, 0)
                  const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0
                  return [`${value.toLocaleString()} (${percentage}%)`, name]
                }}
              />
            </ChartCard>
          </Grid>
        )}
      </Grid>
    </SectionContainer>
  )
}


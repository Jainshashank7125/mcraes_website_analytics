import { BarChart as RechartsBarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { useTheme, useMediaQuery } from '@mui/material'
import { CHART_CONFIG } from '../constants'

/**
 * Stacked Bar Chart Component for Keyword Rankings Distribution
 * 
 * Color scheme:
 * - Dark Green: Position 1-3
 * - Light Green: Position 4-10
 * - Yellow: Position 11-20
 * - Orange: Position 21-50
 * - Red: Position 51+
 * - Gray: Not Found
 * 
 * @param {Object} props
 * @param {Array} props.data - Array of data objects with date and position buckets
 * @param {string} props.engine - 'google' or 'bing' or 'both'
 * @param {string} props.title - Chart title
 * @param {number} props.height - Chart height (default: responsive)
 */
export default function StackedBarChart({
  data = [],
  engine = 'google',
  title = '',
  height,
  ...props
}) {
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'))
  const isTablet = useMediaQuery(theme.breakpoints.down('md'))
  
  // Responsive height
  const chartHeight = height || (isMobile ? 300 : isTablet ? 350 : 400)
  
  // Color scheme for position buckets
  const positionColors = {
    position_1_3: '#2e7d32',      // Dark Green
    position_4_10: '#66bb6a',      // Light Green
    position_11_20: '#ffc107',      // Yellow
    position_21_50: '#ff9800',      // Orange
    position_51_plus: '#f44336',    // Red
    not_found: '#9e9e9e',          // Gray
  }
  
  const positionLabels = {
    position_1_3: '1-3',
    position_4_10: '4-10',
    position_11_20: '11-20',
    position_21_50: '21-50',
    position_51_plus: '51+',
    not_found: 'Not Found',
  }
  
  // Prepare data for chart
  const chartData = data.map(item => {
    const result = {
      date: item.date,
    }
    
    if (engine === 'google' || engine === 'both') {
      const google = item.google || {}
      result['google_1_3'] = google.position_1_3 || 0
      result['google_4_10'] = google.position_4_10 || 0
      result['google_11_20'] = google.position_11_20 || 0
      result['google_21_50'] = google.position_21_50 || 0
      result['google_51_plus'] = google.position_51_plus || 0
      result['google_not_found'] = google.not_found || 0
    }
    
    if (engine === 'bing' || engine === 'both') {
      const bing = item.bing || {}
      result['bing_1_3'] = bing.position_1_3 || 0
      result['bing_4_10'] = bing.position_4_10 || 0
      result['bing_11_20'] = bing.position_11_20 || 0
      result['bing_21_50'] = bing.position_21_50 || 0
      result['bing_51_plus'] = bing.position_51_plus || 0
      result['bing_not_found'] = bing.not_found || 0
    }
    
    return result
  })
  
  // Format date for display
  const formatDate = (dateStr) => {
    try {
      const date = new Date(dateStr)
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    } catch {
      return dateStr
    }
  }
  
  if (!chartData || chartData.length === 0) {
    return (
      <div style={{ 
        height: chartHeight, 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center' 
      }}>
        <p style={{ 
          color: theme.palette.text.secondary,
          fontSize: isMobile ? '0.875rem' : '1rem'
        }}>
          No data available
        </p>
      </div>
    )
  }
  
  // Build bars configuration
  const bars = []
  if (engine === 'google' || engine === 'both') {
    bars.push(
      { dataKey: 'google_1_3', name: '1-3', fill: positionColors.position_1_3, stackId: 'google' },
      { dataKey: 'google_4_10', name: '4-10', fill: positionColors.position_4_10, stackId: 'google' },
      { dataKey: 'google_11_20', name: '11-20', fill: positionColors.position_11_20, stackId: 'google' },
      { dataKey: 'google_21_50', name: '21-50', fill: positionColors.position_21_50, stackId: 'google' },
      { dataKey: 'google_51_plus', name: '51+', fill: positionColors.position_51_plus, stackId: 'google' },
      { dataKey: 'google_not_found', name: 'Not Found', fill: positionColors.not_found, stackId: 'google' }
    )
  }
  if (engine === 'bing' || engine === 'both') {
    bars.push(
      { dataKey: 'bing_1_3', name: '1-3', fill: positionColors.position_1_3, stackId: 'bing' },
      { dataKey: 'bing_4_10', name: '4-10', fill: positionColors.position_4_10, stackId: 'bing' },
      { dataKey: 'bing_11_20', name: '11-20', fill: positionColors.position_11_20, stackId: 'bing' },
      { dataKey: 'bing_21_50', name: '21-50', fill: positionColors.position_21_50, stackId: 'bing' },
      { dataKey: 'bing_51_plus', name: '51+', fill: positionColors.position_51_plus, stackId: 'bing' },
      { dataKey: 'bing_not_found', name: 'Not Found', fill: positionColors.not_found, stackId: 'bing' }
    )
  }
  
  return (
    <ResponsiveContainer width="100%" height={chartHeight}>
      <RechartsBarChart
        data={chartData}
        margin={{
          top: 15,
          right: isMobile ? 15 : 40,
          left: isMobile ? 15 : 30,
          bottom: isMobile ? 70 : 60,
        }}
        {...props}
      >
        <CartesianGrid 
          strokeDasharray={CHART_CONFIG.grid.strokeDasharray} 
          stroke={CHART_CONFIG.grid.stroke}
          opacity={0.3}
        />
        <XAxis 
          dataKey="date"
          tick={{ 
            fontSize: isMobile ? 9 : isTablet ? 10 : 11,
            fill: CHART_CONFIG.axis.stroke
          }}
          stroke={CHART_CONFIG.axis.stroke}
          angle={0}
          textAnchor="middle"
          height={50}
          interval="preserveStartEnd"
          tickFormatter={formatDate}
        />
        <YAxis 
          tick={{ 
            fontSize: isMobile ? 10 : isTablet ? 11 : 12,
            fill: CHART_CONFIG.axis.stroke
          }} 
          stroke={CHART_CONFIG.axis.stroke}
          width={isMobile ? 40 : undefined}
          label={{ 
            value: 'Keywords', 
            angle: -90, 
            position: 'insideLeft',
            style: { textAnchor: 'middle', fill: CHART_CONFIG.axis.stroke }
          }}
        />
        <Tooltip 
          contentStyle={CHART_CONFIG.tooltip}
          formatter={(value, name) => [value, name]}
          labelFormatter={(label) => `Date: ${formatDate(label)}`}
          cursor={{ fill: 'rgba(0, 0, 0, 0.05)' }}
        />
        <Legend 
          wrapperStyle={{ 
            paddingTop: '15px',
            paddingBottom: '5px',
            fontSize: isMobile ? '0.75rem' : '0.875rem'
          }}
          iconType="rect"
        />
        {bars.map((bar, index) => (
          <Bar
            key={bar.dataKey}
            dataKey={bar.dataKey}
            name={bar.name}
            fill={bar.fill}
            stackId={bar.stackId}
            radius={index === bars.length - 1 ? [4, 4, 0, 0] : [0, 0, 0, 0]}
          />
        ))}
      </RechartsBarChart>
    </ResponsiveContainer>
  )
}


import { PieChart as RechartsPieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts'
import { useTheme, useMediaQuery } from '@mui/material'
import { CHART_COLORS, CHART_CONFIG } from '../constants'

/**
 * Enhanced Reusable Pie/Donut Chart Component with responsive design
 * 
 * @param {Object} props
 * @param {Array} props.data - Array of {name: string, value: number} objects
 * @param {string} props.title - Chart title
 * @param {number} props.height - Chart height (default: responsive)
 * @param {boolean} props.showLegend - Show legend (default: true)
 * @param {boolean} props.donut - Show as donut chart (default: false)
 * @param {number} props.innerRadius - Inner radius for donut (default: 60)
 * @param {number} props.outerRadius - Outer radius (default: responsive)
 * @param {Array} props.colors - Custom color array
 * @param {Function} props.formatter - Custom tooltip formatter
 * @param {Function} props.labelFormatter - Custom label formatter
 * @param {boolean} props.showLabel - Show labels on slices (default: true)
 */
export default function PieChart({
  data = [],
  title,
  height,
  showLegend = true,
  donut = false,
  innerRadius,
  outerRadius,
  colors,
  formatter,
  labelFormatter,
  showLabel = true,
  ...props
}) {
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'))
  const isTablet = useMediaQuery(theme.breakpoints.down('md'))
  
  // Responsive height
  const chartHeight = height || (isMobile ? CHART_CONFIG.heights.mobile : isTablet ? CHART_CONFIG.heights.tablet : CHART_CONFIG.heights.desktop)
  
  // Use provided colors or default palette
  const chartColors = colors || CHART_COLORS.palette
  
  // Responsive radius
  const defaultOuterRadius = isMobile ? 70 : isTablet ? 85 : 100
  const defaultInnerRadius = donut ? (innerRadius || (isMobile ? 40 : isTablet ? 50 : 60)) : 0
  
  // Default formatter
  const defaultFormatter = (value, name) => {
    const total = data.reduce((sum, item) => sum + (item.value || 0), 0)
    const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0
    return [`${value.toLocaleString()} (${percentage}%)`, name]
  }
  
  const tooltipFormatter = formatter || defaultFormatter
  
  // Default label formatter
  const defaultLabelFormatter = ({ name, percent }) => {
    if (percent < 0.05) return '' // Don't show labels for very small slices
    return `${name}: ${(percent * 100).toFixed(0)}%`
  }
  
  const sliceLabelFormatter = labelFormatter || (showLabel ? defaultLabelFormatter : false)
  
  if (!data || data.length === 0) {
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
  
  return (
    <ResponsiveContainer width="100%" height={chartHeight}>
      <RechartsPieChart {...props}>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={sliceLabelFormatter}
          outerRadius={outerRadius || defaultOuterRadius}
          innerRadius={defaultInnerRadius}
          fill={CHART_COLORS.primary}
          dataKey="value"
          paddingAngle={2}
        >
          {data.map((entry, index) => (
            <Cell 
              key={`cell-${index}`} 
              fill={chartColors[index % chartColors.length]}
              stroke="#FFFFFF"
              strokeWidth={2}
            />
          ))}
        </Pie>
        <Tooltip 
          contentStyle={CHART_CONFIG.tooltip}
          formatter={tooltipFormatter}
        />
        {showLegend && (
          <Legend 
            wrapperStyle={{ 
              paddingTop: '20px',
              fontSize: isMobile ? '0.75rem' : '0.875rem'
            }}
            formatter={(value) => {
              const maxLength = isMobile ? 12 : 15
              return value.length > maxLength ? value.substring(0, maxLength) + '...' : value
            }}
            iconType="circle"
          />
        )}
      </RechartsPieChart>
    </ResponsiveContainer>
  )
}


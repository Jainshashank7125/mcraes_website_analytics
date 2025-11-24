import { useState, useEffect } from 'react'
import { Box, Card, CardContent, Grid, Typography, CircularProgress, useTheme, alpha } from '@mui/material'
import { motion } from 'framer-motion'
import PieChart from './PieChart'
import BarChart from './BarChart'
import LineChart from './LineChart'
import ChartCard from '../ChartCard'
import { CHART_COLORS } from '../constants'
import { reportingAPI } from '../../../services/api'

/**
 * Scrunch AI Visualizations Component
 * Fetches and displays Query API-based visualizations
 */
export default function ScrunchVisualizations({ brandId, startDate, endDate }) {
  const theme = useTheme()
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState({
    positionDistribution: null,
    platformDistribution: null,
    sentimentDistribution: null,
    citationSourceBreakdown: null,
    competitorPresence: null,
    timeSeries: null
  })
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!brandId) return
    
    const fetchData = async () => {
      setLoading(true)
      setError(null)
      
      try {
        // Fetch all Query API data in parallel
        const [
          positionData,
          platformData,
          sentimentData,
          citationData,
          competitorData,
          timeSeriesData
        ] = await Promise.allSettled([
          // Position distribution
          reportingAPI.queryScrunchAnalytics(
            brandId,
            ['brand_position_score', 'responses'],
            startDate,
            endDate
          ),
          // Platform distribution
          reportingAPI.queryScrunchAnalytics(
            brandId,
            ['ai_platform', 'responses'],
            startDate,
            endDate
          ),
          // Sentiment distribution
          reportingAPI.queryScrunchAnalytics(
            brandId,
            ['brand_sentiment_score', 'responses'],
            startDate,
            endDate
          ),
          // Citation source breakdown
          reportingAPI.queryScrunchAnalytics(
            brandId,
            ['source_type', 'responses'],
            startDate,
            endDate
          ),
          // Competitor presence
          reportingAPI.queryScrunchAnalytics(
            brandId,
            ['competitor_name', 'competitor_presence_percentage', 'responses'],
            startDate,
            endDate
          ),
          // Time series
          reportingAPI.queryScrunchAnalytics(
            brandId,
            ['date_week', 'brand_presence_percentage', 'responses'],
            startDate,
            endDate
          )
        ])
        
        // Process results (handle both fulfilled and rejected promises)
        setData({
          positionDistribution: positionData.status === 'fulfilled' ? processPositionData(positionData.value) : null,
          platformDistribution: platformData.status === 'fulfilled' ? processPlatformData(platformData.value) : null,
          sentimentDistribution: sentimentData.status === 'fulfilled' ? processSentimentData(sentimentData.value) : null,
          citationSourceBreakdown: citationData.status === 'fulfilled' ? processCitationData(citationData.value) : null,
          competitorPresence: competitorData.status === 'fulfilled' ? processCompetitorData(competitorData.value) : null,
          timeSeries: timeSeriesData.status === 'fulfilled' ? processTimeSeriesData(timeSeriesData.value) : null
        })
      } catch (err) {
        console.error('Error fetching Scrunch visualizations:', err)
        // Don't show error if Query API is not available - just show empty state
        if (err.response?.status === 404 || err.response?.status === 403) {
          setError(null) // Query API might not be enabled for this brand
          setData({
            positionDistribution: null,
            platformDistribution: null,
            sentimentDistribution: null,
            citationSourceBreakdown: null,
            competitorPresence: null,
            timeSeries: null
          })
        } else {
          setError('Failed to load visualizations')
        }
      } finally {
        setLoading(false)
      }
    }
    
    fetchData()
  }, [brandId, startDate, endDate])

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress size={40} />
      </Box>
    )
  }

  if (error) {
    return (
      <Box p={3}>
        <Typography color="error">{error}</Typography>
      </Box>
    )
  }

  // Check if we have any data to display
  const hasData = Object.values(data).some(value => value !== null && (Array.isArray(value) ? value.length > 0 : true))
  
  if (!hasData) {
    return null // Don't show empty section
  }

  return (
    <Grid container spacing={3}>
      {/* Position Distribution */}
      {data.positionDistribution && (
        <Grid item xs={12} sm={6} md={4}>
          <ChartCard
            title="Brand Position Distribution"
            badge="Scrunch"
            badgeColor={CHART_COLORS.scrunch.primary}
            height="100%"
            animationDelay={0.1}
          >
            <Box>
              <Typography
                variant="body2"
                color="text.secondary"
                sx={{ mb: 2, fontSize: '0.875rem' }}
              >
                Distribution of your brand's position in AI responses (Top 67-100%, Middle 34-66%, Bottom 0-33%)
              </Typography>
              <PieChart
                data={data.positionDistribution}
                height={280}
                donut={true}
                innerRadius={70}
                outerRadius={100}
                colors={[
                  CHART_COLORS.success,
                  CHART_COLORS.warning,
                  CHART_COLORS.error,
                  CHART_COLORS.secondary
                ]}
                formatter={(value, name) => [
                  `${value.toLocaleString()} responses`,
                  name
                ]}
                showLegend={true}
              />
            </Box>
          </ChartCard>
        </Grid>
      )}

      {/* Sentiment Distribution */}
      {data.sentimentDistribution && (
        <Grid item xs={12} sm={6} md={4}>
          <ChartCard
            title="Brand Sentiment Analysis"
            badge="Scrunch"
            badgeColor={CHART_COLORS.scrunch.primary}
            height="100%"
            animationDelay={0.2}
          >
            <Box>
              <Typography
                variant="body2"
                color="text.secondary"
                sx={{ mb: 2, fontSize: '0.875rem' }}
              >
                Sentiment distribution across all AI responses mentioning your brand
              </Typography>
              <PieChart
                data={data.sentimentDistribution}
                height={280}
                donut={true}
                innerRadius={70}
                outerRadius={100}
                colors={[
                  CHART_COLORS.success, // Positive
                  CHART_COLORS.warning, // Mixed
                  CHART_COLORS.error,   // Negative
                  theme.palette.grey[400] // None
                ]}
                formatter={(value, name) => [
                  `${value.toLocaleString()} responses`,
                  name
                ]}
                showLegend={true}
              />
            </Box>
          </ChartCard>
        </Grid>
      )}

      {/* Platform Distribution */}
      {data.platformDistribution && (
        <Grid item xs={12} sm={6} md={4}>
          <ChartCard
            title="AI Platform Distribution"
            badge="Scrunch"
            badgeColor={CHART_COLORS.scrunch.primary}
            height="100%"
            animationDelay={0.3}
          >
            <Box>
              <Typography
                variant="body2"
                color="text.secondary"
                sx={{ mb: 2, fontSize: '0.875rem' }}
              >
                Distribution of responses across different AI platforms (ChatGPT, Perplexity, Google AI Overview, etc.)
              </Typography>
              <PieChart
                data={data.platformDistribution}
                height={280}
                donut={true}
                innerRadius={70}
                outerRadius={100}
                colors={CHART_COLORS.palette}
                formatter={(value, name) => [
                  `${value.toLocaleString()} responses`,
                  name
                ]}
                showLegend={true}
              />
            </Box>
          </ChartCard>
        </Grid>
      )}

      {/* Citation Source Breakdown
      {data.citationSourceBreakdown && (
        <Grid item xs={12} sm={6} md={4}>
          <ChartCard
            title="Citation Source Breakdown"
            badge="Scrunch"
            badgeColor={CHART_COLORS.scrunch.primary}
            height="100%"
            animationDelay={0.4}
          >
            <Box>
              <Typography
                variant="body2"
                color="text.secondary"
                sx={{ mb: 2, fontSize: '0.875rem' }}
              >
                Distribution of citations by source type (Your Brand, Competitors, Third Party)
              </Typography>
              <PieChart
                data={data.citationSourceBreakdown}
                height={280}
                donut={true}
                innerRadius={70}
                outerRadius={100}
                colors={[
                  CHART_COLORS.primary,  // Your Brand
                  CHART_COLORS.error,    // Competitors
                  CHART_COLORS.secondary // Third Party
                ]}
                formatter={(value, name) => [
                  `${value.toLocaleString()} citations`,
                  name
                ]}
                showLegend={true}
              />
            </Box>
          </ChartCard>
        </Grid>
      )} */}

      {/* Competitive Presence */}
      {data.competitorPresence && data.competitorPresence.length > 0 && (
        <Grid item xs={12} md={6}>
          <ChartCard
            title="Competitive Presence Analysis"
            badge="Scrunch"
            badgeColor={CHART_COLORS.scrunch.primary}
            height={450}
            animationDelay={0.5}
          >
            <Box>
              <Typography
                variant="body2"
                color="text.secondary"
                sx={{ mb: 2, fontSize: '0.875rem' }}
              >
                Brand presence percentage for your brand and top competitors in AI responses
              </Typography>
              <BarChart
                data={data.competitorPresence}
                dataKey="name"
                horizontal={true}
                bars={[{
                  dataKey: 'presence',
                  name: 'Presence %',
                  color: CHART_COLORS.scrunch.primary
                }]}
                formatter={(value) => [`${value.toFixed(2)}%`, 'Presence']}
                margin={{ top: 5, right: 30, left: 120, bottom: 5 }}
                height={350}
              />
            </Box>
          </ChartCard>
        </Grid>
      )}

      {/* Time Series Trends */}
      {data.timeSeries && data.timeSeries.length > 0 && (
        <Grid item xs={12} md={6}>
          <ChartCard
            title="Brand Presence Trend Over Time"
            badge="Scrunch"
            badgeColor={CHART_COLORS.scrunch.primary}
            height={450}
            animationDelay={0.6}
          >
            <Box>
              <Typography
                variant="body2"
                color="text.secondary"
                sx={{ mb: 2, fontSize: '0.875rem' }}
              >
                Weekly trend of your brand's presence percentage in AI responses
              </Typography>
              <LineChart
                data={data.timeSeries}
                dataKey="date"
                lines={[{
                  dataKey: 'presence',
                  name: 'Brand Presence %',
                  color: CHART_COLORS.scrunch.primary,
                  strokeWidth: 3,
                  showDot: true
                }]}
                formatter={(value) => [`${value.toFixed(2)}%`, 'Presence']}
                xAxisFormatter={(value) => {
                  // Format date_week (YYYY-MM-DD format)
                  if (value && value.length >= 10) {
                    const date = new Date(value)
                    const month = date.getMonth() + 1
                    const day = date.getDate()
                    return `${month}/${day}`
                  }
                  return value
                }}
                height={350}
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
              />
            </Box>
          </ChartCard>
        </Grid>
      )}
    </Grid>
  )
}

// Data processing functions
function processPositionData(data) {
  if (!data) return null
  
  const items = data.items || (Array.isArray(data) ? data : [])
  if (items.length === 0) return null
  
  // Categorize position scores: Top (67-100), Middle (34-66), Bottom (0-33)
  const distribution = { Top: 0, Middle: 0, Bottom: 0 }
  
  items.forEach(item => {
    const score = item.brand_position_score || 0
    const responses = item.responses || 0
    
    if (score >= 67) distribution.Top += responses
    else if (score >= 34) distribution.Middle += responses
    else distribution.Bottom += responses
  })
  
  return Object.entries(distribution)
    .filter(([_, value]) => value > 0)
    .map(([name, value]) => ({ name, value }))
}

function processPlatformData(data) {
  if (!data) return null
  
  const items = data.items || (Array.isArray(data) ? data : [])
  if (items.length === 0) return null
  
  return items
    .filter(item => item.responses > 0)
    .map(item => ({
      name: item.ai_platform || 'Unknown',
      value: item.responses || 0
    }))
}

function processSentimentData(data) {
  if (!data) return null
  
  const items = data.items || (Array.isArray(data) ? data : [])
  if (items.length === 0) return null
  
  // Categorize sentiment scores: Positive (67-100), Mixed (34-66), Negative (0-33), None (null)
  const distribution = { Positive: 0, Mixed: 0, Negative: 0, None: 0 }
  
  items.forEach(item => {
    const score = item.brand_sentiment_score
    const responses = item.responses || 0
    
    if (score === null || score === undefined) {
      distribution.None += responses
    } else if (score >= 67) {
      distribution.Positive += responses
    } else if (score >= 34) {
      distribution.Mixed += responses
    } else {
      distribution.Negative += responses
    }
  })
  
  return Object.entries(distribution)
    .filter(([_, value]) => value > 0)
    .map(([name, value]) => ({ name, value }))
}

function processCitationData(data) {
  if (!data) return null
  
  const items = data.items || (Array.isArray(data) ? data : [])
  if (items.length === 0) return null
  
  const sourceMap = {
    'Brand': 'Your Brand',
    'Competitor': 'Competitors',
    'Other': 'Third Party'
  }
  
  return items
    .filter(item => item.responses > 0)
    .map(item => ({
      name: sourceMap[item.source_type] || item.source_type || 'Unknown',
      value: item.responses || 0
    }))
}

function processCompetitorData(data) {
  if (!data) return null
  
  const items = data.items || (Array.isArray(data) ? data : [])
  if (items.length === 0) return null
  
  return items
    .filter(item => item.competitor_name && item.competitor_presence_percentage > 0)
    .sort((a, b) => (b.competitor_presence_percentage || 0) - (a.competitor_presence_percentage || 0))
    .slice(0, 10)
    .map(item => ({
      name: item.competitor_name,
      presence: item.competitor_presence_percentage || 0
    }))
}

function processTimeSeriesData(data) {
  if (!data) return null
  
  const items = data.items || (Array.isArray(data) ? data : [])
  if (items.length === 0) return null
  
  return items
    .filter(item => item.date_week && item.brand_presence_percentage !== undefined)
    .sort((a, b) => a.date_week.localeCompare(b.date_week))
    .map(item => ({
      date: item.date_week,
      presence: item.brand_presence_percentage || 0
    }))
}


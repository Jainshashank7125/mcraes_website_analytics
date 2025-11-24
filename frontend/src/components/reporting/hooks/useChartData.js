import { useMemo } from 'react'
import { getMonthName } from '../utils'

/**
 * Custom hook for transforming and preparing chart data
 */
export function useChartData(dashboardData, scrunchData, startDate, endDate) {
  const chartData = useMemo(() => {
    if (!dashboardData && !scrunchData) return null

    const data = {
      ga4: {
        dailyComparison: null,
        geographicBreakdown: null,
        deviceBreakdown: null,
        channelBreakdown: null,
      },
      agencyAnalytics: {
        keywordRanking: null,
        allKeywordsRanking: null,
      },
      scrunch: {
        topPerformingPrompts: null,
        scrunchAIInsights: null,
      },
    }

    // GA4 Chart Data
    if (dashboardData?.chart_data) {
      // Daily comparison data
      if (dashboardData.chart_data.ga4_daily_comparison) {
        data.ga4.dailyComparison = dashboardData.chart_data.ga4_daily_comparison.map(
          (item) => ({
            date: item.date,
            formattedDate: formatDate(item.date),
            users: item.current_users || 0,
            previousUsers: item.previous_users || 0,
            sessions: item.current_sessions || 0,
            previousSessions: item.previous_sessions || 0,
            newUsers: item.current_new_users || 0,
            previousNewUsers: item.previous_new_users || 0,
            conversions: item.current_conversions || 0,
            previousConversions: item.previous_conversions || 0,
          })
        )
      }

      // Geographic breakdown
      if (dashboardData.chart_data.geographic_breakdown) {
        data.ga4.geographicBreakdown = dashboardData.chart_data.geographic_breakdown
          .slice(0, 6)
          .map((item) => ({
            name: item.country || 'Unknown',
            value: item.users || 0,
          }))
      }

      // Device breakdown
      if (dashboardData.chart_data.device_breakdown) {
        data.ga4.deviceBreakdown = dashboardData.chart_data.device_breakdown.map(
          (item) => ({
            name: item.device_category || 'Unknown',
            value: item.users || 0,
          })
        )
      }

      // Channel breakdown
      if (dashboardData.chart_data.channel_breakdown) {
        data.ga4.channelBreakdown = dashboardData.chart_data.channel_breakdown.map(
          (item) => ({
            name: item.channel || 'Unknown',
            value: item.users || 0,
          })
        )
      }

      // Agency Analytics - Keyword Ranking
      if (dashboardData.chart_data.all_keywords_ranking) {
        data.agencyAnalytics.allKeywordsRanking = dashboardData.chart_data.all_keywords_ranking
          .slice(0, 15)
          .map((kw) => ({
            keyword: kw.keyword || 'Unknown',
            rank: kw.google_rank || 0,
            searchVolume: kw.search_volume || 0,
          }))
      }

      // Scrunch data from main endpoint
      if (dashboardData.chart_data.top_performing_prompts) {
        data.scrunch.topPerformingPrompts =
          dashboardData.chart_data.top_performing_prompts
      }

      if (dashboardData.chart_data.scrunch_ai_insights) {
        data.scrunch.scrunchAIInsights =
          dashboardData.chart_data.scrunch_ai_insights
      }
    }

    // Scrunch data from separate endpoint
    if (scrunchData?.chart_data) {
      if (scrunchData.chart_data.top_performing_prompts) {
        data.scrunch.topPerformingPrompts =
          scrunchData.chart_data.top_performing_prompts
      }

      if (scrunchData.chart_data.scrunch_ai_insights) {
        data.scrunch.scrunchAIInsights =
          scrunchData.chart_data.scrunch_ai_insights
      }
    }

    return data
  }, [dashboardData, scrunchData, startDate, endDate])

  return chartData
}

/**
 * Format date from YYYYMMDD format to readable string
 */
function formatDate(dateString) {
  if (!dateString || dateString.length !== 8) return dateString

  const year = dateString.substring(0, 4)
  const month = dateString.substring(4, 6)
  const day = dateString.substring(6, 8)

  return `${day} ${getMonthName(parseInt(month))} ${year}`
}

/**
 * Format date for X-axis labels (shorter format)
 */
export function formatDateForAxis(dateString) {
  if (!dateString || dateString.length !== 8) return dateString

  const month = dateString.substring(4, 6)
  const day = dateString.substring(6, 8)

  return `${day} ${getMonthName(parseInt(month))}`
}

/**
 * Get date range label for comparison charts
 */
export function getDateRangeLabel(startDate, endDate) {
  if (!startDate || !endDate) return 'Current period'

  const start = new Date(startDate)
  const end = new Date(endDate)

  const startFormatted = `${start.getDate()} ${getMonthName(
    start.getMonth() + 1
  )}`
  const endFormatted = `${end.getDate()} ${getMonthName(end.getMonth() + 1)}`

  return `${startFormatted} - ${endFormatted}`
}


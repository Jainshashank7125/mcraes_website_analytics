// Utility functions for Reporting Dashboard

export const formatValue = (kpi) => {
  const { value, format, display } = kpi
  
  // If custom format with display text, use that
  if (format === 'custom' && display) {
    return display
  }
  
  // Handle custom format with object values
  if (format === 'custom' && typeof value === 'object' && value !== null) {
    // For competitive_benchmarking
    if (value.brand_visibility_percent !== undefined && value.competitor_avg_visibility_percent !== undefined) {
      return `Your brand's AI visibility: ${value.brand_visibility_percent.toFixed(1)}% vs competitor average: ${value.competitor_avg_visibility_percent.toFixed(1)}%`
    }
    // For keyword_ranking_change_and_volume
    if (value.avg_ranking_change !== undefined && value.total_search_volume !== undefined) {
      return `Ranking change: ${value.avg_ranking_change} positions | Search volume: ${value.total_search_volume.toLocaleString()}`
    }
    // For all_keywords_ranking (array of keywords)
    if (Array.isArray(value)) {
      return `${value.length} keywords tracked`
    }
    // For null values (prompt_volume, citations_per_prompt)
    if (value === null) {
      return 'Metric not available - no assumptions made'
    }
  }
  
  // Handle null values
  if (value === null || value === undefined) {
    return 'Metric not available - no assumptions made'
  }
  
  if (format === 'currency') {
    return `$${value.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
  }
  
  if (format === 'percentage') {
    return `${value.toFixed(1)}%`
  }
  
  if (format === 'duration') {
    // Convert seconds to readable format (MM:SS or HH:MM:SS)
    const hours = Math.floor(value / 3600)
    const minutes = Math.floor((value % 3600) / 60)
    const seconds = Math.floor(value % 60)
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
    } else {
      return `${minutes}:${seconds.toString().padStart(2, '0')}`
    }
  }
  
  if (format === 'number') {
    return value.toLocaleString()
  }
  
  return value.toLocaleString()
}

export const getChannelLabel = (source) => {
  if (!source) return source
  const sourceLower = source.toLowerCase()
  
  if (sourceLower.includes('direct') || sourceLower.includes('(none)')) {
    return 'Direct'
  } else if (sourceLower.includes('organic')) {
    return 'Organic'
  } else if (sourceLower.includes('social') || sourceLower.includes('paid_social') || sourceLower.includes('facebook')) {
    return 'Social'
  } else if (sourceLower.includes('referral') || sourceLower.includes('refer') || sourceLower.includes('cpc')) {
    return 'Referral'
  }
  // Return original if no match
  return source
}

export const getChannelColor = (source) => {
  if (!source) return 'rgba(59, 130, 246, 0.6)'
  const sourceLower = source.toLowerCase()
  
  if (sourceLower.includes('direct') || sourceLower.includes('(none)')) {
    return 'rgba(20, 184, 166, 0.6)' // Teal/Green for Direct
  } else if (sourceLower.includes('google') && sourceLower.includes('organic')) {
    return 'rgba(59, 130, 246, 0.6)' // Light blue for Google Organic
  } else if (sourceLower.includes('google') && (sourceLower.includes('cpc') || sourceLower.includes('paid'))) {
    return 'rgba(68, 192, 237, 0.6)' // Light blue for Google CPC
  } else if (sourceLower.includes('facebook') || sourceLower.includes('social') || sourceLower.includes('paid_social')) {
    return 'rgba(239, 68, 68, 0.6)' // Orange-red for Social/Paid Social
  } else if (sourceLower.includes('referral') || sourceLower.includes('refer')) {
    return 'rgba(251, 146, 60, 0.6)' // Orange for Referral
  } else if (sourceLower.includes('organic') || sourceLower.includes('search')) {
    return 'rgba(59, 130, 246, 0.6)' // Light blue for Organic Search
  }
  // Default color
  return 'rgba(59, 130, 246, 0.6)'
}

export const getSourceColor = (source, theme) => {
  switch (source) {
    case 'GA4':
      return '#4285F4' // Google blue
    case 'AgencyAnalytics':
      return '#34A853' // Google green
    case 'Scrunch':
      return '#FBBC04' // Google yellow
    default:
      return theme.palette.grey[500]
  }
}

export const getSourceLabel = (source) => {
  switch (source) {
    case 'GA4':
      return 'GA4'
    case 'AgencyAnalytics':
      return 'AgencyAnalytics'
    case 'Scrunch':
      return 'Scrunch'
    default:
      return source
  }
}

export const getMonthName = (month) => {
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  return months[month - 1] || ''
}


/**
 * Token refresh service
 * Automatically refreshes access tokens every 3 hours (or slightly before expiration)
 */
import { authAPI } from './api'
import { debugLog, debugWarn, debugError } from '../utils/debug'

const TOKEN_REFRESH_INTERVAL = 3 * 60 * 60 * 1000 // 3 hours in milliseconds
const TOKEN_REFRESH_BUFFER = 5 * 60 * 1000 // Refresh 5 minutes before expiration

let refreshIntervalId = null
let refreshTimeoutId = null

/**
 * Calculate when the token should be refreshed (3 hours from now, minus buffer)
 */
const calculateRefreshTime = () => {
  const now = Date.now()
  const expiresAt = localStorage.getItem('token_expires_at')
  
  if (expiresAt) {
    const expiresTime = parseInt(expiresAt, 10)
    const timeUntilExpiry = expiresTime - now
    // Refresh 5 minutes before expiration, or immediately if already expired
    return Math.max(timeUntilExpiry - TOKEN_REFRESH_BUFFER, 0)
  }
  
  // If no expiration time stored, refresh in 3 hours minus buffer
  return TOKEN_REFRESH_INTERVAL - TOKEN_REFRESH_BUFFER
}

/**
 * Refresh the access token using the refresh token
 */
const refreshAccessToken = async () => {
  const refreshToken = localStorage.getItem('refresh_token')
  
  if (!refreshToken) {
    debugWarn('No refresh token available, cannot refresh access token')
    stopTokenRefresh()
    return false
  }

  try {
    const response = await authAPI.refreshToken(refreshToken)
    const { access_token, refresh_token: newRefreshToken, expires_in } = response

    // Update tokens in localStorage
    localStorage.setItem('access_token', access_token)
    if (newRefreshToken) {
      localStorage.setItem('refresh_token', newRefreshToken)
    }

    // Calculate and store expiration time
    if (expires_in) {
      const expiresAt = Date.now() + (expires_in * 1000)
      localStorage.setItem('token_expires_at', expiresAt.toString())
    } else {
      // Default to 3 hours if expires_in not provided
      const expiresAt = Date.now() + TOKEN_REFRESH_INTERVAL
      localStorage.setItem('token_expires_at', expiresAt.toString())
    }

    debugLog('Access token refreshed successfully')
    
    // Schedule next refresh
    scheduleTokenRefresh()
    
    return true
  } catch (error) {
    debugError('Failed to refresh access token:', error)
    // Clear tokens on refresh failure
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('token_expires_at')
    localStorage.removeItem('user')
    stopTokenRefresh()
    
    // Redirect to login if refresh token expired
    const currentPath = window.location.pathname
    const isPublicRoute = 
      currentPath === '/login' || 
      currentPath === '/signup' || 
      currentPath.startsWith('/reporting/')
    
    if (!isPublicRoute) {
      window.location.href = '/login'
    }
    
    return false
  }
}

/**
 * Schedule the next token refresh
 */
const scheduleTokenRefresh = () => {
  // Clear any existing timeouts/intervals
  if (refreshTimeoutId) {
    clearTimeout(refreshTimeoutId)
    refreshTimeoutId = null
  }
  if (refreshIntervalId) {
    clearInterval(refreshIntervalId)
    refreshIntervalId = null
  }

  const refreshTime = calculateRefreshTime()
  
  if (refreshTime <= 0) {
    // Token is expired or about to expire, refresh immediately
    refreshAccessToken()
    return
  }

  // Schedule refresh at the calculated time
  refreshTimeoutId = setTimeout(() => {
    refreshAccessToken()
  }, refreshTime)

  // Also set up an interval as a backup (every 3 hours)
  refreshIntervalId = setInterval(() => {
    refreshAccessToken()
  }, TOKEN_REFRESH_INTERVAL)

  debugLog(`Token refresh scheduled in ${Math.round(refreshTime / 1000 / 60)} minutes`)
}

/**
 * Start automatic token refresh
 * Call this after successful login
 */
export const startTokenRefresh = () => {
  const accessToken = localStorage.getItem('access_token')
  const refreshToken = localStorage.getItem('refresh_token')
  
  if (!accessToken || !refreshToken) {
    debugWarn('No tokens available, cannot start token refresh')
    return
  }

  // If token_expires_at is not set, set it to 3 hours from now
  if (!localStorage.getItem('token_expires_at')) {
    const expiresAt = Date.now() + TOKEN_REFRESH_INTERVAL
    localStorage.setItem('token_expires_at', expiresAt.toString())
  }

  scheduleTokenRefresh()
}

/**
 * Stop automatic token refresh
 * Call this on logout
 */
export const stopTokenRefresh = () => {
  if (refreshTimeoutId) {
    clearTimeout(refreshTimeoutId)
    refreshTimeoutId = null
  }
  if (refreshIntervalId) {
    clearInterval(refreshIntervalId)
    refreshIntervalId = null
  }
  debugLog('Token refresh stopped')
}

/**
 * Manually refresh the token (can be called by user action)
 */
export const manualRefresh = async () => {
  return await refreshAccessToken()
}

/**
 * Check if token is expired or about to expire
 */
export const isTokenExpired = () => {
  const expiresAt = localStorage.getItem('token_expires_at')
  if (!expiresAt) {
    return true
  }
  const expiresTime = parseInt(expiresAt, 10)
  const now = Date.now()
  // Consider expired if within 5 minutes of expiration
  return now >= (expiresTime - TOKEN_REFRESH_BUFFER)
}


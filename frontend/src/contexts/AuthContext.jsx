import { createContext, useContext, useState, useEffect } from 'react'
import { authAPI } from '../services/api'
import { getErrorMessage } from '../utils/errorHandler'
import { startTokenRefresh, stopTokenRefresh, isTokenExpired } from '../services/tokenRefresh'

const AuthContext = createContext(null)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  // Check if user is logged in on mount
  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem('access_token')
      const storedUser = localStorage.getItem('user')

      if (storedToken && storedUser) {
        try {
          // Check if token is expired
          if (isTokenExpired()) {
            // Try to refresh the token
            const refreshToken = localStorage.getItem('refresh_token')
            if (refreshToken) {
              try {
                const response = await authAPI.refreshToken(refreshToken)
                const { access_token, refresh_token: newRefreshToken, user: userData, expires_in } = response
                
                localStorage.setItem('access_token', access_token)
                if (newRefreshToken) {
                  localStorage.setItem('refresh_token', newRefreshToken)
                }
                if (userData) {
                  localStorage.setItem('user', JSON.stringify(userData))
                  setUser(userData)
                }
                
                // Calculate and store expiration time
                if (expires_in) {
                  const expiresAt = Date.now() + (expires_in * 1000)
                  localStorage.setItem('token_expires_at', expiresAt.toString())
                } else {
                  // Default to 3 hours if expires_in not provided
                  const expiresAt = Date.now() + (3 * 60 * 60 * 1000)
                  localStorage.setItem('token_expires_at', expiresAt.toString())
                }
                
                setIsAuthenticated(true)
                startTokenRefresh()
              } catch (refreshError) {
                // Refresh failed, clear storage
                localStorage.removeItem('access_token')
                localStorage.removeItem('refresh_token')
                localStorage.removeItem('user')
                localStorage.removeItem('token_expires_at')
                setUser(null)
                setIsAuthenticated(false)
                stopTokenRefresh()
                // Let ProtectedRoute handle redirect
              }
            } else {
              // No refresh token, clear storage
              localStorage.removeItem('access_token')
              localStorage.removeItem('refresh_token')
              localStorage.removeItem('user')
              localStorage.removeItem('token_expires_at')
              setUser(null)
              setIsAuthenticated(false)
              // Let ProtectedRoute handle redirect
            }
          } else {
            // Token is still valid, verify with API
            try {
              const userData = await authAPI.getCurrentUser()
              setUser(userData)
              setIsAuthenticated(true)
              startTokenRefresh()
            } catch (error) {
              // Token verification failed, clear storage
              localStorage.removeItem('access_token')
              localStorage.removeItem('refresh_token')
              localStorage.removeItem('user')
              localStorage.removeItem('token_expires_at')
              setUser(null)
              setIsAuthenticated(false)
              stopTokenRefresh()
              // Let ProtectedRoute handle redirect
            }
          }
        } catch (error) {
          // Error during initialization, clear storage
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          localStorage.removeItem('user')
          localStorage.removeItem('token_expires_at')
          setUser(null)
          setIsAuthenticated(false)
          stopTokenRefresh()
          // Let ProtectedRoute handle redirect
        }
      } else {
        // No tokens at all - user is not logged in
        setUser(null)
        setIsAuthenticated(false)
        stopTokenRefresh()
      }
      // Always set loading to false at the end
      setLoading(false)
    }

    initAuth()
    
    // Cleanup on unmount
    return () => {
      stopTokenRefresh()
    }
  }, [])

  const signin = async (email, password) => {
    try {
      const response = await authAPI.signin(email, password)
      const { access_token, refresh_token, user: userData, expires_in } = response

      localStorage.setItem('access_token', access_token)
      if (refresh_token) {
        localStorage.setItem('refresh_token', refresh_token)
      }
      localStorage.setItem('user', JSON.stringify(userData))

      // Calculate and store expiration time (3 hours from now)
      if (expires_in) {
        const expiresAt = Date.now() + (expires_in * 1000)
        localStorage.setItem('token_expires_at', expiresAt.toString())
      } else {
        // Default to 3 hours if expires_in not provided
        const expiresAt = Date.now() + (3 * 60 * 60 * 1000)
        localStorage.setItem('token_expires_at', expiresAt.toString())
      }

      setUser(userData)
      setIsAuthenticated(true)
      
      // Start automatic token refresh
      startTokenRefresh()
      
      return { success: true }
    } catch (error) {
      return {
        success: false,
        error: getErrorMessage(error),
      }
    }
  }

  const signup = async (email, password, fullName = null) => {
    try {
      const response = await authAPI.signup(email, password, fullName)
      
      // Signup should only return success message - no tokens
      // Do NOT update logged-in user state or store tokens
      if (response.success) {
        return { 
          success: true, 
          message: response.message || "Account created successfully. Please sign in to continue."
        }
      } else {
        return {
          success: false,
          error: response.message || "Failed to create account"
        }
      }
    } catch (error) {
      return {
        success: false,
        error: getErrorMessage(error),
      }
    }
  }

  const signout = async () => {
    try {
      await authAPI.signout()
    } catch (error) {
      console.error('Signout error:', error)
    } finally {
      setUser(null)
      setIsAuthenticated(false)
      stopTokenRefresh()
    }
  }

  const value = {
    user,
    isAuthenticated,
    loading,
    signin,
    signup,
    signout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}


import { createContext, useContext, useState, useEffect } from 'react'
import { authAPI } from '../services/api'
import { debugError } from '../utils/debug'
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

  // Helper function to get storage based on rememberMe preference
  const getStorage = () => {
    // Check if user previously chose "Remember me"
    const rememberMe = localStorage.getItem('remember_me') === 'true'
    return rememberMe ? localStorage : sessionStorage
  }

  // Helper function to set storage preference
  const setStoragePreference = (rememberMe) => {
    if (rememberMe) {
      localStorage.setItem('remember_me', 'true')
    } else {
      localStorage.removeItem('remember_me')
    }
  }

  // Check if user is logged in on mount
  useEffect(() => {
    const initAuth = async () => {
      // Check both localStorage and sessionStorage for tokens
      // Priority: check the storage based on remember_me preference first
      const storage = getStorage()
      let storedToken = storage.getItem('access_token')
      let storedUser = storage.getItem('user')
      
      // If not found in preferred storage, check the other one
      if (!storedToken) {
        const otherStorage = storage === localStorage ? sessionStorage : localStorage
        storedToken = otherStorage.getItem('access_token')
        storedUser = otherStorage.getItem('user')
        // If found in other storage, migrate to preferred storage
        if (storedToken && storedUser) {
          storage.setItem('access_token', storedToken)
          storage.setItem('user', storedUser)
          const refreshToken = otherStorage.getItem('refresh_token')
          const expiresAt = otherStorage.getItem('token_expires_at')
          if (refreshToken) storage.setItem('refresh_token', refreshToken)
          if (expiresAt) storage.setItem('token_expires_at', expiresAt)
          // Clear from other storage
          otherStorage.removeItem('access_token')
          otherStorage.removeItem('refresh_token')
          otherStorage.removeItem('user')
          otherStorage.removeItem('token_expires_at')
        }
      }

      if (storedToken && storedUser) {
        try {
          // Check if token is expired
          if (isTokenExpired()) {
            // Try to refresh the token
            const currentStorage = getStorage()
            const refreshToken = currentStorage.getItem('refresh_token') || localStorage.getItem('refresh_token')
            if (refreshToken) {
              try {
                const response = await authAPI.refreshToken(refreshToken)
                const { access_token, refresh_token: newRefreshToken, user: userData, expires_in } = response
                
                currentStorage.setItem('access_token', access_token)
                if (newRefreshToken) {
                  currentStorage.setItem('refresh_token', newRefreshToken)
                }
                if (userData) {
                  currentStorage.setItem('user', JSON.stringify(userData))
                  setUser(userData)
                }
                
                // Calculate and store expiration time
                if (expires_in) {
                  const expiresAt = Date.now() + (expires_in * 1000)
                  currentStorage.setItem('token_expires_at', expiresAt.toString())
                } else {
                  // Default to 3 hours if expires_in not provided
                  const expiresAt = Date.now() + (3 * 60 * 60 * 1000)
                  currentStorage.setItem('token_expires_at', expiresAt.toString())
                }
                
                setIsAuthenticated(true)
                startTokenRefresh()
              } catch (refreshError) {
                // Refresh failed, clear storage
                const clearStorage = (storage) => {
                  storage.removeItem('access_token')
                  storage.removeItem('refresh_token')
                  storage.removeItem('user')
                  storage.removeItem('token_expires_at')
                }
                clearStorage(localStorage)
                clearStorage(sessionStorage)
                setUser(null)
                setIsAuthenticated(false)
                stopTokenRefresh()
                // Let ProtectedRoute handle redirect
              }
            } else {
              // No refresh token, clear storage
              const clearStorage = (storage) => {
                storage.removeItem('access_token')
                storage.removeItem('refresh_token')
                storage.removeItem('user')
                storage.removeItem('token_expires_at')
              }
              clearStorage(localStorage)
              clearStorage(sessionStorage)
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
              const clearStorage = (storage) => {
                storage.removeItem('access_token')
                storage.removeItem('refresh_token')
                storage.removeItem('user')
                storage.removeItem('token_expires_at')
              }
              clearStorage(localStorage)
              clearStorage(sessionStorage)
              setUser(null)
              setIsAuthenticated(false)
              stopTokenRefresh()
              // Let ProtectedRoute handle redirect
            }
          }
        } catch (error) {
          // Error during initialization, clear storage
          const clearStorage = (storage) => {
            storage.removeItem('access_token')
            storage.removeItem('refresh_token')
            storage.removeItem('user')
            storage.removeItem('token_expires_at')
          }
          clearStorage(localStorage)
          clearStorage(sessionStorage)
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

  const signin = async (email, password, rememberMe = false) => {
    try {
      const response = await authAPI.signin(email, password)
      const { access_token, refresh_token, user: userData, expires_in } = response

      // Use localStorage if rememberMe is true, otherwise use sessionStorage
      const storage = rememberMe ? localStorage : sessionStorage
      
      // Store preference
      setStoragePreference(rememberMe)
      
      // Clear the other storage to avoid conflicts
      if (rememberMe) {
        sessionStorage.removeItem('access_token')
        sessionStorage.removeItem('refresh_token')
        sessionStorage.removeItem('user')
        sessionStorage.removeItem('token_expires_at')
      } else {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user')
        localStorage.removeItem('token_expires_at')
      }

      storage.setItem('access_token', access_token)
      if (refresh_token) {
        storage.setItem('refresh_token', refresh_token)
      }
      storage.setItem('user', JSON.stringify(userData))

      // Calculate and store expiration time (3 hours from now)
      if (expires_in) {
        const expiresAt = Date.now() + (expires_in * 1000)
        storage.setItem('token_expires_at', expiresAt.toString())
      } else {
        // Default to 3 hours if expires_in not provided
        const expiresAt = Date.now() + (3 * 60 * 60 * 1000)
        storage.setItem('token_expires_at', expiresAt.toString())
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
      debugError('Signout error:', error)
    } finally {
      // Clear both localStorage and sessionStorage
      const clearStorage = (storage) => {
        storage.removeItem('access_token')
        storage.removeItem('refresh_token')
        storage.removeItem('user')
        storage.removeItem('token_expires_at')
      }
      clearStorage(localStorage)
      clearStorage(sessionStorage)
      localStorage.removeItem('remember_me')
      
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


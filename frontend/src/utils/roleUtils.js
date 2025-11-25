/**
 * Utility functions for checking user roles
 */

/**
 * Check if user is admin or manager
 * @param {Object} user - User object from AuthContext
 * @returns {boolean} - True if user is admin or manager
 */
export const isAdminOrManager = (user) => {
  if (!user || !user.user_metadata) {
    return false
  }
  
  const role = user.user_metadata.role?.toLowerCase()
  return role === 'admin' || role === 'manager'
}

/**
 * Check if user is admin
 * @param {Object} user - User object from AuthContext
 * @returns {boolean} - True if user is admin
 */
export const isAdmin = (user) => {
  if (!user || !user.user_metadata) {
    return false
  }
  
  const role = user.user_metadata.role?.toLowerCase()
  return role === 'admin'
}

/**
 * Check if user is manager
 * @param {Object} user - User object from AuthContext
 * @returns {boolean} - True if user is manager
 */
export const isManager = (user) => {
  if (!user || !user.user_metadata) {
    return false
  }
  
  const role = user.user_metadata.role?.toLowerCase()
  return role === 'manager'
}


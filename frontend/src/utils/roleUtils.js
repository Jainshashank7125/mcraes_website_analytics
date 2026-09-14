/**
 * Utility functions for checking user roles
 */

/**
 * Check if user is admin
 * @param {Object} user - User object from AuthContext
 * @returns {boolean} - True if user is admin
 */
export const isAdmin = (user) => {
  return user?.role === 'admin'
}

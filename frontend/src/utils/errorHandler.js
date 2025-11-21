/**
 * Utility function to extract user-friendly error messages from API responses
 * Handles both old format (detail) and new format (error.message)
 */
export const getErrorMessage = (error) => {
  if (!error) {
    return 'An unexpected error occurred. Please try again.'
  }

  // Handle axios error response
  if (error.response?.data) {
    const data = error.response.data
    
    // New format: { error: { message: "...", error_code: "...", details: {} } }
    if (data.error?.message) {
      return data.error.message
    }
    
    // Old format: { detail: "..." }
    if (data.detail) {
      return data.detail
    }
    
    // Fallback: string message
    if (typeof data === 'string') {
      return data
    }
    
    // Object with message property
    if (data.message) {
      return data.message
    }
  }
  
  // Handle error object with message
  if (error.message) {
    return error.message
  }
  
  // Handle string errors
  if (typeof error === 'string') {
    return error
  }
  
  // Default fallback
  return 'Something went wrong. Please try again.'
}


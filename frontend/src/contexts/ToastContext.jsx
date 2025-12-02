import { createContext, useContext, useState, useCallback } from 'react'
import { Snackbar, Alert } from '@mui/material'

const ToastContext = createContext(null)

export const useToast = () => {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider')
  }
  return context
}

export const ToastProvider = ({ children }) => {
  const [toast, setToast] = useState({
    open: false,
    message: '',
    severity: 'info', // 'success', 'error', 'warning', 'info'
  })

  const showToast = useCallback((message, severity = 'info') => {
    setToast({
      open: true,
      message,
      severity,
    })
  }, [])

  const showError = useCallback((message) => {
    showToast(message, 'error')
  }, [showToast])

  const showSuccess = useCallback((message) => {
    showToast(message, 'success')
  }, [showToast])

  const showWarning = useCallback((message) => {
    showToast(message, 'warning')
  }, [showToast])

  const showInfo = useCallback((message) => {
    showToast(message, 'info')
  }, [showToast])

  const handleClose = useCallback((event, reason) => {
    if (reason === 'clickaway') {
      return
    }
    setToast((prev) => ({ ...prev, open: false }))
  }, [])

  return (
    <ToastContext.Provider value={{ showToast, showError, showSuccess, showWarning, showInfo }}>
      {children}
      <Snackbar
        open={toast.open}
        autoHideDuration={6000}
        onClose={handleClose}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
        sx={{ mt: '64px' }}
      >
        <Alert
          onClose={handleClose}
          severity={toast.severity}
          variant="filled"
          sx={{
            maxWidth: { xs: '90vw', sm: '400px', md: '500px' },
            width: '100%',
            borderRadius: 2,
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
            '& .MuiAlert-message': {
              wordWrap: 'break-word',
              whiteSpace: 'normal',
              overflowWrap: 'break-word',
              wordBreak: 'break-word',
              lineHeight: 1.5,
            },
          }}
        >
          {toast.message}
        </Alert>
      </Snackbar>
    </ToastContext.Provider>
  )
}


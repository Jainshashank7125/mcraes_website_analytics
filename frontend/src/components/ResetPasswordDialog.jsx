import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  TextField,
  Button,
  IconButton,
  InputAdornment,
  Alert,
} from '@mui/material'
import { Lock as LockIcon, Visibility, VisibilityOff } from '@mui/icons-material'
import { userAPI } from '../services/api'
import { useToast } from '../contexts/ToastContext'
import { getErrorMessage } from '../utils/errorHandler'

function ResetPasswordDialog({ open, onClose, user }) {
  const { showError, showSuccess } = useToast()
  const [newPassword, setNewPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (open) {
      setNewPassword('')
      setShowPassword(false)
      setError('')
    }
  }, [open])

  const handleClose = () => {
    if (saving) return
    onClose()
  }

  const handleReset = async () => {
    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters long.')
      return
    }

    setSaving(true)
    setError('')
    try {
      await userAPI.resetPassword(user.id, newPassword)
      showSuccess(`Password reset for ${user.email}. They have been signed out of all sessions.`)
      onClose(true)
    } catch (err) {
      const message = getErrorMessage(err)
      setError(message)
      showError(message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="xs" fullWidth>
      <DialogTitle>Reset Password</DialogTitle>
      <DialogContent>
        <DialogContentText sx={{ mb: 2.5 }}>
          Set a new password for <strong>{user?.email}</strong>. This cannot be undone, and the
          user will be signed out of all active sessions.
        </DialogContentText>

        {error && (
          <Alert severity="error" sx={{ mb: 2.5 }}>
            {error}
          </Alert>
        )}

        <TextField
          fullWidth
          autoFocus
          label="New Password"
          type={showPassword ? 'text' : 'password'}
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          helperText="Minimum 8 characters"
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <LockIcon sx={{ color: 'text.secondary', fontSize: 20 }} />
              </InputAdornment>
            ),
            endAdornment: (
              <InputAdornment position="end">
                <IconButton onClick={() => setShowPassword(!showPassword)} edge="end" size="small">
                  {showPassword ? <VisibilityOff /> : <Visibility />}
                </IconButton>
              </InputAdornment>
            ),
          }}
        />
      </DialogContent>
      <DialogActions sx={{ p: 2.5 }}>
        <Button onClick={handleClose} disabled={saving}>
          Cancel
        </Button>
        <Button onClick={handleReset} color="warning" variant="contained" disabled={saving}>
          {saving ? 'Resetting...' : 'Reset Password'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default ResetPasswordDialog

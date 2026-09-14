import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Typography,
  IconButton,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Switch,
  Alert,
  Divider,
  Tooltip,
  Box,
} from '@mui/material'
import {
  Close as CloseIcon,
  Email as EmailIcon,
  Lock as LockIcon,
  Person as PersonIcon,
  Visibility,
  VisibilityOff,
} from '@mui/icons-material'
import { userAPI } from '../services/api'
import { useToast } from '../contexts/ToastContext'
import { getErrorMessage } from '../utils/errorHandler'

function UserManagement({ open, onClose, user, currentUserId }) {
  const { showError, showSuccess } = useToast()
  const isEditMode = !!user
  const isEditingSelf = isEditMode && user.id === currentUserId

  const [email, setEmail] = useState('')
  const [fullName, setFullName] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [role, setRole] = useState('user')
  const [isActive, setIsActive] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (open) {
      setError('')
      setPassword('')
      setShowPassword(false)
      if (user) {
        setEmail(user.email || '')
        setFullName(user.full_name || '')
        setRole(user.role || 'user')
        setIsActive(user.is_active !== false)
      } else {
        setEmail('')
        setFullName('')
        setRole('user')
        setIsActive(true)
      }
    }
  }, [open, user])

  const handleClose = () => {
    if (saving) return
    onClose()
  }

  const handleSave = async () => {
    setError('')

    if (!email.trim()) {
      setError('Email is required.')
      return
    }
    if (!isEditMode && password.length < 8) {
      setError('Password must be at least 8 characters long.')
      return
    }

    setSaving(true)
    try {
      if (isEditMode) {
        if (email !== user.email || fullName !== (user.full_name || '')) {
          await userAPI.updateUser(user.id, { email, fullName })
        }
        if (role !== user.role) {
          await userAPI.setUserRole(user.id, role)
        }
        if (isActive !== user.is_active) {
          await userAPI.setUserActive(user.id, isActive)
        }
        showSuccess('User updated successfully.')
      } else {
        await userAPI.createUser({ email, password, fullName: fullName || null, role })
        showSuccess('User created successfully.')
      }
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
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography variant="h6" fontWeight={700} sx={{ fontSize: '1.25rem' }}>
          {isEditMode ? 'Edit User' : 'Create User'}
        </Typography>
        <IconButton size="small" onClick={handleClose} disabled={saving}>
          <CloseIcon fontSize="small" />
        </IconButton>
      </DialogTitle>
      <Divider />
      <DialogContent sx={{ pt: 3 }}>
        {error && (
          <Alert severity="error" sx={{ mb: 2.5 }}>
            {error}
          </Alert>
        )}

        <TextField
          fullWidth
          label="Full Name"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          sx={{ mb: 2.5 }}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <PersonIcon sx={{ color: 'text.secondary', fontSize: 20 }} />
              </InputAdornment>
            ),
          }}
        />

        <TextField
          fullWidth
          label="Email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          sx={{ mb: 2.5 }}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <EmailIcon sx={{ color: 'text.secondary', fontSize: 20 }} />
              </InputAdornment>
            ),
          }}
        />

        {!isEditMode && (
          <TextField
            fullWidth
            label="Password"
            type={showPassword ? 'text' : 'password'}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            helperText="Minimum 8 characters"
            sx={{ mb: 2.5 }}
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
        )}

        <FormControl fullWidth sx={{ mb: isEditMode ? 2.5 : 0 }}>
          <InputLabel id="user-role-label">Role</InputLabel>
          <Select
            labelId="user-role-label"
            label="Role"
            value={role}
            onChange={(e) => setRole(e.target.value)}
          >
            <MenuItem value="user">User</MenuItem>
            <MenuItem value="admin">Admin</MenuItem>
          </Select>
        </FormControl>

        {isEditMode && (
          <Box>
            <Tooltip title={isEditingSelf ? 'You cannot deactivate your own account.' : ''} arrow disableHoverListener={!isEditingSelf}>
              <span>
                <FormControlLabel
                  control={
                    <Switch
                      checked={isActive}
                      onChange={(e) => setIsActive(e.target.checked)}
                      disabled={isEditingSelf}
                    />
                  }
                  label={isActive ? 'Active' : 'Deactivated'}
                />
              </span>
            </Tooltip>
          </Box>
        )}
      </DialogContent>
      <Divider />
      <DialogActions sx={{ p: 2.5 }}>
        <Button onClick={handleClose} disabled={saving}>
          Cancel
        </Button>
        <Button onClick={handleSave} variant="contained" disabled={saving}>
          {saving ? 'Saving...' : isEditMode ? 'Save Changes' : 'Create User'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default UserManagement

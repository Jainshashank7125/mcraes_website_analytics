import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  useTheme,
  Container,
  InputAdornment,
  IconButton,
  CircularProgress,
} from '@mui/material'
import {
  Email as EmailIcon,
  Lock as LockIcon,
  Person as PersonIcon,
  Visibility,
  VisibilityOff,
} from '@mui/icons-material'
import { motion } from 'framer-motion'
import { useAuth } from '../contexts/AuthContext'
import { useToast } from '../contexts/ToastContext'

function CreateUser() {
  const theme = useTheme()
  const navigate = useNavigate()
  const { signup } = useAuth()
  const { showError, showSuccess } = useToast()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)

    const result = await signup(email, password, fullName || null)

    if (result.success) {
      if (result.requiresEmailConfirmation) {
        showSuccess('User created successfully. Please check email for confirmation.')
      } else {
        showSuccess('User created successfully!')
        // Reset form
        setEmail('')
        setPassword('')
        setFullName('')
        // Optionally navigate back or stay on page
        setTimeout(() => {
          navigate('/brands')
        }, 1500)
      }
    } else {
      showError(result.error || 'Failed to create user')
    }

    setLoading(false)
  }

  return (
    <Box sx={{ p: 3 }}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Card
          sx={{
            borderRadius: 3,
            border: `1px solid ${theme.palette.divider}`,
            boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
            maxWidth: 600,
            mx: 'auto',
          }}
        >
          <CardContent sx={{ p: 4 }}>
            <Typography
              variant="h4"
              fontWeight={700}
              textAlign="center"
              mb={1}
              sx={{
                fontSize: '1.75rem',
                letterSpacing: '-0.02em',
              }}
            >
              Create User
            </Typography>
            <Typography
              variant="body2"
              color="text.secondary"
              textAlign="center"
              mb={4}
            >
              Create a new user account
            </Typography>

            <Box component="form" onSubmit={handleSubmit}>
              <TextField
                fullWidth
                label="Full Name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                sx={{ mb: 2 }}
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
                sx={{ mb: 2 }}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <EmailIcon sx={{ color: 'text.secondary', fontSize: 20 }} />
                    </InputAdornment>
                  ),
                }}
              />

              <TextField
                fullWidth
                label="Password"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                sx={{ mb: 3 }}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <LockIcon sx={{ color: 'text.secondary', fontSize: 20 }} />
                    </InputAdornment>
                  ),
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={() => setShowPassword(!showPassword)}
                        edge="end"
                        size="small"
                      >
                        {showPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />

              <Button
                type="submit"
                fullWidth
                variant="contained"
                size="large"
                disabled={loading}
                sx={{
                  mb: 2,
                  py: 1.5,
                  borderRadius: 2,
                  fontWeight: 600,
                  textTransform: 'none',
                  fontSize: '1rem',
                }}
              >
                {loading ? (
                  <Box display="flex" alignItems="center" gap={1}>
                    <CircularProgress size={20} sx={{ color: 'white' }} />
                    <span>Creating user...</span>
                  </Box>
                ) : (
                  'Create User'
                )}
              </Button>
            </Box>
          </CardContent>
        </Card>
      </motion.div>
    </Box>
  )
}

export default CreateUser


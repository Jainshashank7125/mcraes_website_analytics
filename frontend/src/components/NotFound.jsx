import { useNavigate } from 'react-router-dom'
import { Box, Typography, Button, Container } from '@mui/material'
import { Home as HomeIcon } from '@mui/icons-material'

function NotFound() {
  const navigate = useNavigate()

  return (
    <Container maxWidth="md">
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          textAlign: 'center',
          py: 8,
        }}
      >
        <Typography
          variant="h1"
          sx={{
            fontSize: { xs: '4rem', sm: '6rem', md: '8rem' },
            fontWeight: 700,
            color: 'primary.main',
            mb: 2,
            lineHeight: 1,
          }}
        >
          404
        </Typography>
        <Typography
          variant="h4"
          sx={{
            fontWeight: 600,
            mb: 2,
            fontSize: { xs: '1.5rem', sm: '2rem' },
          }}
        >
          Page Not Found
        </Typography>
        <Typography
          variant="body1"
          color="text.secondary"
          sx={{
            mb: 4,
            maxWidth: 500,
            fontSize: { xs: '0.875rem', sm: '1rem' },
          }}
        >
          The page you're looking for doesn't exist or has been moved.
        </Typography>
        <Button
          variant="contained"
          size="large"
          startIcon={<HomeIcon />}
          onClick={() => navigate('/')}
          sx={{
            px: 4,
            py: 1.5,
            borderRadius: 2,
            fontSize: '1rem',
            fontWeight: 600,
            textTransform: 'none',
          }}
        >
          Go to Dashboard
        </Button>
      </Box>
    </Container>
  )
}

export default NotFound


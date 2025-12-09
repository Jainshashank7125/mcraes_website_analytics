import { useState, useEffect, useMemo } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import {
  Box,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
  alpha,
  useTheme,
  Container,
  ThemeProvider,
  CssBaseline,
} from '@mui/material'
import { createTheme } from '@mui/material/styles'
import { motion } from 'framer-motion'
import { reportingAPI, clientAPI } from '../services/api'
import ReportingDashboard from './ReportingDashboard'
import { theme as baseTheme } from '../theme'

function PublicReportingDashboard() {
  const { slug } = useParams()
  const [searchParams] = useSearchParams()
  const [brandInfo, setBrandInfo] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [linkExpired, setLinkExpired] = useState(false)
  const [linkDisabled, setLinkDisabled] = useState(false)
  const theme = useTheme()
  
  // Read date range from URL params, fallback to saved client dates
  // Accept both new `from`/`to` params and legacy `startDate`/`endDate`
  const urlStartDate = searchParams.get('from') || searchParams.get('startDate')
  const urlEndDate = searchParams.get('to') || searchParams.get('endDate')
  
  // Use saved client dates if URL params are not provided
  const effectiveStartDate = useMemo(() => {
    if (urlStartDate) return urlStartDate
    if (brandInfo?.dashboard_link?.start_date) return brandInfo.dashboard_link.start_date
    return brandInfo?.clientData?.report_start_date || undefined
  }, [urlStartDate, brandInfo?.dashboard_link?.start_date, brandInfo?.clientData?.report_start_date])
  
  const effectiveEndDate = useMemo(() => {
    if (urlEndDate) return urlEndDate
    if (brandInfo?.dashboard_link?.end_date) return brandInfo.dashboard_link.end_date
    return brandInfo?.clientData?.report_end_date || undefined
  }, [urlEndDate, brandInfo?.dashboard_link?.end_date, brandInfo?.clientData?.report_end_date])

  // Create custom theme based on brand theme - MUST be called before any conditional returns
  const brandTheme = useMemo(() => {
    if (!brandInfo?.theme || typeof brandInfo.theme !== 'object') {
      return baseTheme
    }

    const themeConfig = brandInfo.theme
    const primaryColor = themeConfig.primary_color || baseTheme.palette.primary.main
    const secondaryColor = themeConfig.secondary_color || baseTheme.palette.secondary.main
    const accentColor = themeConfig.accent_color || baseTheme.palette.info.main
    const fontFamily = themeConfig.font_family || baseTheme.typography.fontFamily

    return createTheme({
      ...baseTheme,
      palette: {
        ...baseTheme.palette,
        primary: {
          main: primaryColor,
          light: alpha(primaryColor, 0.7),
          dark: alpha(primaryColor, 0.9),
          contrastText: '#ffffff',
        },
        secondary: {
          main: secondaryColor,
          light: alpha(secondaryColor, 0.7),
          dark: alpha(secondaryColor, 0.9),
          contrastText: '#ffffff',
        },
        info: {
          main: accentColor,
          light: alpha(accentColor, 0.7),
          dark: alpha(accentColor, 0.9),
        },
      },
      typography: {
        ...baseTheme.typography,
        fontFamily: fontFamily || baseTheme.typography.fontFamily,
      },
    })
  }, [brandInfo?.theme])

  useEffect(() => {
    const fetchBrand = async () => {
      if (!slug) {
        setError('Invalid brand slug')
        setLoading(false)
        return
      }

      try {
        setLoading(true)
        setError(null)
        setLinkExpired(false)
        setLinkDisabled(false)

        let dashboardLink = null
        try {
          dashboardLink = await clientAPI.getDashboardLinkBySlug(slug)
        } catch (linkErr) {
          const status = linkErr.response?.status
          if (status === 403) {
            setLinkDisabled(true)
            setLoading(false)
            return
          }
          if (status === 410) {
            setLinkExpired(true)
            setLoading(false)
            return
          }
          if (status && status !== 404) {
            throw linkErr
          }
        }

        if (dashboardLink) {
          try {
            const brand = await reportingAPI.getBrandBySlug(slug)
            if (brand && brand.no_data) {
              setBrandInfo({ ...brand, no_data: true, dashboard_link: dashboardLink })
            } else {
              setBrandInfo({ ...brand, dashboard_link: dashboardLink })
            }
            return
          } catch (brandErr) {
            const status = brandErr.response?.status
            if (status === 403) {
              setLinkDisabled(true)
              setLoading(false)
              return
            }
            if (status === 410) {
              setLinkExpired(true)
              setLoading(false)
              return
            }
            throw brandErr
          }
        }

        // Legacy fallback to client-based slug logic
        let clientData = null
        try {
          const client = await clientAPI.getClientBySlug(slug)
          if (client && client.id) {
            clientData = client
            // Check if link is expired (48 hours from created_at or updated_at)
            const linkTimestamp = client.updated_at || client.created_at
            if (linkTimestamp) {
              const linkDate = new Date(linkTimestamp)
              const now = new Date()
              const hoursSinceCreation = (now - linkDate) / (1000 * 60 * 60) // Convert to hours
              
              if (hoursSinceCreation > 48) {
                setLinkExpired(true)
                setLoading(false)
                return
              }
            }
            
            // Link is valid, continue with brand fetch
            // Fetch brand info (which may use client data)
            const brand = await reportingAPI.getBrandBySlug(slug)
            
            // Check if brand has no_data flag (graceful degradation from backend)
            if (brand && brand.no_data) {
              // Still set brandInfo so UI can render, but mark it as no data
              setBrandInfo({ ...brand, no_data: true, clientData })
            } else {
              setBrandInfo({ ...brand, clientData })
            }
            return
          }
        } catch (clientErr) {
          console.log("Client not found by slug, trying brand...")
        }

        // Fallback to brand lookup for backward compatibility
        const brand = await reportingAPI.getBrandBySlug(slug)
        
        // Check if brand has no_data flag (graceful degradation from backend)
        if (brand && brand.no_data) {
          // Still set brandInfo so UI can render, but mark it as no data
          setBrandInfo({ ...brand, no_data: true })
        } else {
          setBrandInfo(brand)
        }
      } catch (err) {
        console.error('Error fetching brand:', err)
        // Only set error for actual errors, not for graceful "no data" responses
        if (err.response?.status !== 200) {
          setError(err.response?.data?.detail || err.message || 'Failed to load brand')
        } else {
          // If we get a 200 with no_data, handle it gracefully
          setBrandInfo({ no_data: true, message: 'No data available' })
        }
      } finally {
        setLoading(false)
      }
    }

    fetchBrand()
  }, [slug])

  if (loading) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          bgcolor: theme.palette.background.default,
        }}
      >
        <CircularProgress size={40} thickness={4} />
      </Box>
    )
  }

  if (linkExpired) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="warning" sx={{ borderRadius: 2 }}>
          <Typography variant="h6" gutterBottom>
            Link Expired
          </Typography>
          <Typography>
            This shareable link has expired. Please contact the report owner to generate a new link.
          </Typography>
        </Alert>
      </Container>
    )
  }

  if (linkDisabled) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="warning" sx={{ borderRadius: 2 }}>
          <Typography variant="h6" gutterBottom>
            Link Disabled
          </Typography>
          <Typography>
            This shareable link is currently disabled. Please contact the report owner to enable it.
          </Typography>
        </Alert>
      </Container>
    )
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error" sx={{ borderRadius: 2 }}>
          {error === 'Brand not found' ? (
            <>
              <Typography variant="h6" gutterBottom>
                Brand Not Found
              </Typography>
              <Typography>
                The brand you're looking for doesn't exist or the link is invalid.
              </Typography>
            </>
          ) : (
            <Typography>{error}</Typography>
          )}
        </Alert>
      </Container>
    )
  }

  if (!brandInfo) {
    return null
  }

  // Don't block rendering if no_data is set from brand endpoint
  // Let the dashboard endpoint check for Agency Analytics/GA4 data and show appropriate message
  // Only show "no data" message if dashboard endpoint also returns no_data

  // Render the ReportingDashboard component but override it to use slug-based data fetching
  // We'll create a wrapper that passes the brand_id to ReportingDashboard
  return (
    <ThemeProvider theme={brandTheme}>
      <CssBaseline />
      <Box
        sx={{
          minHeight: '100vh',
          bgcolor: brandTheme.palette.background.default,
          fontFamily: brandTheme.typography.fontFamily,
          // Apply theme colors globally
          color: brandTheme.palette.text.primary,
        }}
      >
        {/* Pass slug and date range to ReportingDashboard */}
        <ReportingDashboard 
          publicSlug={slug} 
          brandInfo={brandInfo}
          publicStartDate={effectiveStartDate || undefined}
          publicEndDate={effectiveEndDate || undefined}
        />
      </Box>
    </ThemeProvider>
  )
}

export default PublicReportingDashboard


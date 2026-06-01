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
  Tabs,
  Tab,
} from '@mui/material'
import { createTheme } from '@mui/material/styles'
import { motion } from 'framer-motion'
import { reportingAPI, clientAPI } from '../services/api'
import ReportingDashboard from './ReportingDashboard'
import { theme as baseTheme } from '../theme'
import { debugError, debugLog } from '../utils/debug'

function PublicReportingDashboard() {
  const { slug } = useParams()
  const [searchParams] = useSearchParams()
  const [brandInfo, setBrandInfo] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [linkExpired, setLinkExpired] = useState(false)
  const [linkDisabled, setLinkDisabled] = useState(false)
  const theme = useTheme()

  // Attached reports tab state
  const [activeReportIndex, setActiveReportIndex] = useState(0)
  const [activeSlug, setActiveSlug] = useState(null)
  const [activeLinkData, setActiveLinkData] = useState(null)
  const [activeTabLoading, setActiveTabLoading] = useState(false)
  
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
          // Track link open (fire and forget - don't block page load)
          clientAPI.trackDashboardLinkOpen(slug, {
            user_agent: navigator.userAgent,
            referer: document.referrer
          }).catch(err => {
            // Silently fail - don't block page load
            debugError('Failed to track link open:', err)
          })
          
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
          debugLog("Client not found by slug, trying brand...")
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
        debugError('Error fetching brand:', err)
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

  // Reset attached report tabs when the primary slug changes
  useEffect(() => {
    setActiveReportIndex(0)
    setActiveSlug(null)
    setActiveLinkData(null)
    setActiveTabLoading(false)
  }, [slug])

  const attachedLinks = brandInfo?.dashboard_link?.attached_links || []
  const hasMultipleReports = attachedLinks.length > 0

  // Generate a short label from a link's start_date, e.g. "Dec '25" or "Apr '26"
  const shortTabLabel = (link) => {
    const raw = link?.start_date
    if (!raw) return link?.name || 'Report'
    const d = new Date(String(raw).split('T')[0] + 'T00:00:00')
    if (isNaN(d.getTime())) return link?.name || 'Report'
    const month = d.toLocaleString('en-US', { month: 'short' })
    const year = String(d.getFullYear()).slice(2)
    return `${month} '${year}`
  }

  const tabLabels = hasMultipleReports
    ? [
        shortTabLabel(brandInfo?.dashboard_link),
        ...attachedLinks.map((l) => shortTabLabel(l)),
      ]
    : []

  const handleReportTabChange = async (event, newIndex) => {
    setActiveReportIndex(newIndex)
    if (newIndex === 0) {
      setActiveTabLoading(false)
      setActiveSlug(null)
      setActiveLinkData(null)
      return
    }
    const targetLink = attachedLinks[newIndex - 1]
    if (!targetLink) return

    // Show loading immediately — don't wait for the async fetch
    setActiveTabLoading(true)
    setActiveLinkData(null)

    try {
      const fetchedLink = await clientAPI.getDashboardLinkBySlug(targetLink.slug)
      setActiveSlug(targetLink.slug)
      setActiveLinkData({ ...brandInfo, dashboard_link: fetchedLink })
    } catch (err) {
      const status = err.response?.status
      if (status === 403) {
        setActiveLinkData({ __error: 'disabled' })
      } else if (status === 410) {
        setActiveLinkData({ __error: 'expired' })
      } else {
        setActiveLinkData({ __error: 'unavailable' })
      }
    } finally {
      setActiveTabLoading(false)
    }
  }

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

  // Determine the active link's start/end dates for the ReportingDashboard
  const activeStartDate = activeSlug
    ? (activeLinkData?.dashboard_link?.start_date?.split?.('T')?.[0] ?? activeLinkData?.dashboard_link?.start_date)
    : (effectiveStartDate || undefined)
  const activeEndDate = activeSlug
    ? (activeLinkData?.dashboard_link?.end_date?.split?.('T')?.[0] ?? activeLinkData?.dashboard_link?.end_date)
    : (effectiveEndDate || undefined)

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
          color: brandTheme.palette.text.primary,
        }}
      >
        {/* Top-level report tabs — only shown when attached links exist */}
        {hasMultipleReports && (
          <Box
            sx={{
              borderBottom: 1,
              borderColor: 'divider',
              bgcolor: 'background.paper',
              px: { xs: 1, sm: 3 },
            }}
          >
            <Tabs
              value={activeReportIndex}
              onChange={handleReportTabChange}
              variant="scrollable"
              scrollButtons="auto"
              allowScrollButtonsMobile
              sx={{
                '& .MuiTab-root': {
                  textTransform: 'none',
                  fontWeight: 600,
                  minWidth: 80,
                  fontSize: { xs: '0.75rem', sm: '0.875rem' },
                  px: { xs: 1.5, sm: 2 },
                },
                '& .MuiTabs-scrollButtons': { color: 'primary.main' },
              }}
            >
              {tabLabels.map((label, i) => (
                <Tab key={i} label={label} />
              ))}
            </Tabs>
          </Box>
        )}

        {/* Tab switch loading spinner — shown immediately on click, before data arrives */}
        {activeTabLoading ? (
          <Box
            sx={{
              minHeight: '60vh',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <CircularProgress size={44} thickness={4} />
          </Box>
        ) : activeLinkData?.__error ? (
          /* Error state for a disabled/expired attached link */
          <Container maxWidth="lg" sx={{ py: 4 }}>
            <Alert severity="warning" sx={{ borderRadius: 2 }}>
              <Typography>
                {activeLinkData.__error === 'disabled'
                  ? 'This attached report is currently disabled.'
                  : activeLinkData.__error === 'expired'
                  ? 'This attached report link has expired.'
                  : 'This attached report is unavailable.'}
              </Typography>
            </Alert>
          </Container>
        ) : (
          <ReportingDashboard
            publicSlug={activeSlug || slug}
            brandInfo={activeLinkData || brandInfo}
            publicStartDate={activeStartDate}
            publicEndDate={activeEndDate}
          />
        )}
      </Box>
    </ThemeProvider>
  )
}

export default PublicReportingDashboard


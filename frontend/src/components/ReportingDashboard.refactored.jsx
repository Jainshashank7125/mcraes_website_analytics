import { useState, useEffect } from 'react'
import {
  Box,
  Alert,
  Typography,
  useTheme,
} from '@mui/material'
import { reportingAPI, syncAPI } from '../services/api'
import { KPI_ORDER, DATE_PRESETS } from './reporting/constants'
import { formatValue, getSourceColor, getSourceLabel, getMonthName, getChannelLabel, getChannelColor } from './reporting/utils'
import ReportingDashboardHeader from './reporting/ReportingDashboardHeader'
import DashboardContent from './reporting/DashboardContent'
import KPISelectorDialog from './reporting/KPISelectorDialog'
import ShareDialog from './reporting/ShareDialog'

function ReportingDashboard({ publicSlug, brandInfo: publicBrandInfo }) {
  const isPublic = !!publicSlug
  const [brands, setBrands] = useState([])
  const [selectedBrandId, setSelectedBrandId] = useState(null)
  const [dashboardData, setDashboardData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [selectedKPIs, setSelectedKPIs] = useState(new Set(KPI_ORDER))
  const [tempSelectedKPIs, setTempSelectedKPIs] = useState(new Set(KPI_ORDER))
  const [showKPISelector, setShowKPISelector] = useState(false)
  
  const getDefaultDates = () => {
    const end = new Date()
    const start = new Date()
    start.setDate(start.getDate() - 7)
    return {
      start: start.toISOString().split('T')[0],
      end: end.toISOString().split('T')[0]
    }
  }
  
  const defaultDates = getDefaultDates()
  const [startDate, setStartDate] = useState(defaultDates.start)
  const [endDate, setEndDate] = useState(defaultDates.end)
  const [datePreset, setDatePreset] = useState('Last 7 days')
  const [brandAnalytics, setBrandAnalytics] = useState(null)
  const [loadingAnalytics, setLoadingAnalytics] = useState(false)
  const [showShareDialog, setShowShareDialog] = useState(false)
  const [shareableUrl, setShareableUrl] = useState('')
  const [copied, setCopied] = useState(false)
  const [selectedBrandSlug, setSelectedBrandSlug] = useState(null)
  const theme = useTheme()

  // Load saved KPI preferences from localStorage
  useEffect(() => {
    const savedKPIs = localStorage.getItem('reportingDashboardSelectedKPIs')
    if (savedKPIs) {
      try {
        const parsed = JSON.parse(savedKPIs)
        setSelectedKPIs(new Set(parsed))
        setTempSelectedKPIs(new Set(parsed))
      } catch (e) {
        console.error('Error loading saved KPIs:', e)
      }
    }
  }, [])

  useEffect(() => {
    if (isPublic && publicSlug) {
      const fetchPublicBrand = async () => {
        try {
          const brand = await reportingAPI.getBrandBySlug(publicSlug)
          setSelectedBrandId(brand.id)
        } catch (err) {
          setError(err.response?.data?.detail || 'Failed to load brand')
        }
      }
      fetchPublicBrand()
    } else {
      loadBrands()
    }
  }, [isPublic, publicSlug])

  useEffect(() => {
    if (selectedBrandId) {
      loadDashboardData()
      if (!isPublic) {
        loadBrandAnalytics()
      }
    }
  }, [selectedBrandId, startDate, endDate, isPublic])

  const loadBrands = async () => {
    try {
      const data = await syncAPI.getBrands()
      setBrands(data.items || [])
      if (data.items && data.items.length > 0) {
        setSelectedBrandId(data.items[0].id)
        if (data.items[0].slug) {
          setSelectedBrandSlug(data.items[0].slug)
        }
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load brands')
    }
  }

  useEffect(() => {
    if (selectedBrandId && brands.length > 0) {
      const selectedBrand = brands.find(b => b.id === selectedBrandId)
      if (selectedBrand?.slug) {
        setSelectedBrandSlug(selectedBrand.slug)
      } else {
        setSelectedBrandSlug(null)
      }
    }
  }, [selectedBrandId, brands])

  const handleOpenShareDialog = () => {
    if (selectedBrandSlug) {
      const baseUrl = window.location.origin
      const url = `${baseUrl}/reporting/${selectedBrandSlug}`
      setShareableUrl(url)
      setShowShareDialog(true)
      setCopied(false)
    } else {
      setError('Brand slug not available. Please ensure the brand has a slug configured.')
    }
  }

  const handleCopyUrl = async () => {
    try {
      await navigator.clipboard.writeText(shareableUrl)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy URL:', err)
      setError('Failed to copy URL to clipboard')
    }
  }

  const loadDashboardData = async () => {
    if (!selectedBrandId && !publicSlug) return
    
    try {
      setLoading(true)
      setError(null)
      
      let data
      if (isPublic && publicSlug) {
        data = await reportingAPI.getReportingDashboardBySlug(
          publicSlug,
          startDate || undefined,
          endDate || undefined
        )
      } else {
        data = await reportingAPI.getReportingDashboard(
          selectedBrandId,
          startDate || undefined,
          endDate || undefined
        )
      }
      
      setDashboardData(data)
      
      if (selectedKPIs.size === 0 && data.kpis) {
        setSelectedKPIs(new Set(Object.keys(data.kpis)))
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  const loadBrandAnalytics = async () => {
    if (!selectedBrandId) return
    
    try {
      setLoadingAnalytics(true)
      const response = await syncAPI.getBrandAnalytics(selectedBrandId)
      setBrandAnalytics(response.global_analytics || null)
    } catch (err) {
      console.error('Failed to load brand analytics:', err)
      setBrandAnalytics(null)
    } finally {
      setLoadingAnalytics(false)
    }
  }

  const handleDatePresetChange = (preset) => {
    if (preset === '') {
      setDatePreset('')
      return
    }
    
    const presetData = DATE_PRESETS.find(p => p.label === preset)
    if (presetData) {
      const end = new Date()
      const start = new Date()
      start.setDate(start.getDate() - presetData.days)
      
      setStartDate(start.toISOString().split('T')[0])
      setEndDate(end.toISOString().split('T')[0])
      setDatePreset(preset)
    }
  }

  const handleKPIChange = (kpiKey, checked) => {
    const newSelected = new Set(tempSelectedKPIs)
    if (checked) {
      newSelected.add(kpiKey)
    } else {
      newSelected.delete(kpiKey)
    }
    setTempSelectedKPIs(newSelected)
  }

  const handleSelectAll = () => {
    const availableKPIs = dashboardData?.kpis 
      ? Object.keys(dashboardData.kpis)
      : KPI_ORDER
    setTempSelectedKPIs(new Set(availableKPIs))
  }

  const handleDeselectAll = () => {
    setTempSelectedKPIs(new Set())
  }

  const handleSaveKPISelection = () => {
    setSelectedKPIs(new Set(tempSelectedKPIs))
    localStorage.setItem('reportingDashboardSelectedKPIs', JSON.stringify(Array.from(tempSelectedKPIs)))
    setShowKPISelector(false)
  }

  const handleOpenKPISelector = () => {
    setTempSelectedKPIs(new Set(selectedKPIs))
    setShowKPISelector(true)
  }

  const handleBrandChange = (brandId) => {
    setSelectedBrandId(brandId)
    const selectedBrand = brands.find(b => b.id === brandId)
    if (selectedBrand?.slug) {
      setSelectedBrandSlug(selectedBrand.slug)
    } else {
      setSelectedBrandSlug(null)
    }
  }

  // Get KPIs in the correct order, filtered by selection
  const displayedKPIs = dashboardData?.kpis 
    ? (isPublic 
        ? KPI_ORDER.filter(key => dashboardData.kpis[key] && key !== 'competitive_benchmarking')
            .map(key => [key, dashboardData.kpis[key]])
        : KPI_ORDER.filter(key => dashboardData.kpis[key] && selectedKPIs.has(key) && key !== 'competitive_benchmarking')
            .map(key => [key, dashboardData.kpis[key]]))
    : []

  return (
    <Box sx={{ p: 3 }}>
      <ReportingDashboardHeader
        isPublic={isPublic}
        publicBrandInfo={publicBrandInfo}
        onOpenKPISelector={handleOpenKPISelector}
        onOpenShareDialog={handleOpenShareDialog}
        onRefresh={loadDashboardData}
        selectedBrandSlug={selectedBrandSlug}
        brands={brands}
        selectedBrandId={selectedBrandId}
        onBrandChange={handleBrandChange}
        datePreset={datePreset}
        onDatePresetChange={handleDatePresetChange}
        startDate={startDate}
        onStartDateChange={(date) => {
          setStartDate(date)
          setDatePreset('')
        }}
        endDate={endDate}
        onEndDateChange={(date) => {
          setEndDate(date)
          setDatePreset('')
        }}
      />

      {error && (
        <Alert 
          severity="error" 
          sx={{ mb: 3, borderRadius: 2 }}
          onClose={() => setError(null)}
        >
          {error}
        </Alert>
      )}

      {/* Diagnostic Information */}
      {dashboardData?.diagnostics && (
        <Box mb={3}>
          {(!dashboardData.diagnostics.ga4_configured || !dashboardData.diagnostics.agency_analytics_configured) && (
            <Alert 
              severity="info" 
              sx={{ mb: 2, borderRadius: 2 }}
            >
              <Typography variant="subtitle2" fontWeight={600} mb={1}>
                Missing Data Sources
              </Typography>
              <Box component="ul" sx={{ m: 0, pl: 2 }}>
                {!dashboardData.diagnostics.ga4_configured && (
                  <li>
                    <Typography variant="body2">
                      <strong>GA4:</strong> No GA4 property ID configured. Configure it in the brands table or use the GA4 sync endpoint.
                    </Typography>
                  </li>
                )}
                {!dashboardData.diagnostics.agency_analytics_configured && (
                  <li>
                    <Typography variant="body2">
                      <strong>AgencyAnalytics:</strong> No campaigns linked to this brand. Sync Agency Analytics data and link campaigns to brands.
                    </Typography>
                  </li>
                )}
              </Box>
              <Typography variant="caption" color="text.secondary" mt={1} display="block">
                Currently showing: {dashboardData.diagnostics.kpi_counts.ga4} GA4 KPIs, {dashboardData.diagnostics.kpi_counts.agency_analytics} AgencyAnalytics KPIs, {dashboardData.diagnostics.kpi_counts.scrunch} Scrunch KPIs
              </Typography>
            </Alert>
          )}
        </Box>
      )}

      <DashboardContent
        loading={loading}
        dashboardData={dashboardData}
        brandAnalytics={brandAnalytics}
        isPublic={isPublic}
        selectedKPIs={selectedKPIs}
        displayedKPIs={displayedKPIs}
        formatValue={formatValue}
        getSourceColor={getSourceColor}
        getSourceLabel={getSourceLabel}
        theme={theme}
        getMonthName={getMonthName}
        getChannelLabel={getChannelLabel}
        getChannelColor={getChannelColor}
      />

      <KPISelectorDialog
        open={showKPISelector}
        onClose={() => setShowKPISelector(false)}
        tempSelectedKPIs={tempSelectedKPIs}
        dashboardData={dashboardData}
        onKPIChange={handleKPIChange}
        onSelectAll={handleSelectAll}
        onDeselectAll={handleDeselectAll}
        onSave={handleSaveKPISelection}
        selectedKPIs={selectedKPIs}
      />

      <ShareDialog
        open={showShareDialog}
        onClose={() => setShowShareDialog(false)}
        shareableUrl={shareableUrl}
        copied={copied}
        onCopyUrl={handleCopyUrl}
      />
    </Box>
  )
}

export default ReportingDashboard


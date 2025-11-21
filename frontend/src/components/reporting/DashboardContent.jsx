import { Box, CircularProgress, Alert } from '@mui/material'
import GA4Section from './GA4Section'
import ScrunchAISection from './ScrunchAISection'
import BrandAnalyticsSection from './BrandAnalyticsSection'
import KPIGrid from './KPIGrid'

export default function DashboardContent({
  loading,
  dashboardData,
  brandAnalytics,
  isPublic,
  selectedKPIs,
  displayedKPIs,
  formatValue,
  getSourceColor,
  getSourceLabel,
  theme,
  getMonthName,
  getChannelLabel,
  getChannelColor,
}) {
  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="50vh">
        <CircularProgress size={40} thickness={4} />
      </Box>
    )
  }

  if (!dashboardData) {
    return (
      <Alert severity="info" sx={{ borderRadius: 2 }}>
        Please select a brand to view the reporting dashboard.
      </Alert>
    )
  }

  return (
    <>
      {/* Google Analytics 4 Section */}
      <GA4Section
        dashboardData={dashboardData}
        formatValue={formatValue}
        getSourceColor={getSourceColor}
        getSourceLabel={getSourceLabel}
        theme={theme}
        getMonthName={getMonthName}
        getChannelLabel={getChannelLabel}
        getChannelColor={getChannelColor}
      />

      {/* Scrunch AI Section */}
      <ScrunchAISection
        dashboardData={dashboardData}
        formatValue={formatValue}
        theme={theme}
      />

      {/* Brand Analytics Charts Section */}
      {!isPublic && (
        <BrandAnalyticsSection
          brandAnalytics={brandAnalytics}
          theme={theme}
        />
      )}

      {/* General KPI Grid - All Other KPIs */}
      <KPIGrid
        displayedKPIs={displayedKPIs}
        formatValue={formatValue}
        getSourceColor={getSourceColor}
        getSourceLabel={getSourceLabel}
        theme={theme}
      />

      {/* Overall Performance Metrics Section */}
      {dashboardData?.kpis && (
        <Box sx={{ mt: 4 }}>
          {/* This section can be extracted later if needed */}
        </Box>
      )}
    </>
  )
}


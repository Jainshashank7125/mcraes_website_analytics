import {
  Box,
  Button,
  FormControl,
  IconButton,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  TextField,
  Typography,
  alpha,
  useTheme,
} from '@mui/material'
import {
  Settings as SettingsIcon,
  Share as ShareIcon,
  Refresh as RefreshIcon,
  CalendarToday as CalendarTodayIcon,
  Insights as InsightsIcon,
} from '@mui/icons-material'
import { DATE_PRESETS } from './constants'

export default function ReportingDashboardHeader({
  isPublic,
  publicBrandInfo,
  onOpenKPISelector,
  onOpenShareDialog,
  onOpenOverview,
  onRefresh,
  selectedBrandSlug,
  brands,
  selectedBrandId,
  onBrandChange,
  datePreset,
  onDatePresetChange,
  startDate,
  onStartDateChange,
  endDate,
  onEndDateChange,
}) {
  const theme = useTheme()

  return (
    <Box mb={4}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Box display="flex" alignItems="center" gap={2}>
          {isPublic && publicBrandInfo?.logo_url && (
            <Box
              component="img"
              src={publicBrandInfo.logo_url}
              alt={`${publicBrandInfo.name} logo`}
              sx={{
                maxHeight: 80,
                maxWidth: 300,
                objectFit: 'contain',
                borderRadius: 1,
              }}
            />
          )}
          <Typography 
            variant="h4" 
            fontWeight={700} 
            sx={{
              fontSize: '1.75rem',
              letterSpacing: '-0.02em',
              color: 'text.primary'
            }}
          >
            {isPublic && publicBrandInfo ? publicBrandInfo.name : 'Unified Reporting Dashboard'}
          </Typography>
        </Box>
        <Box display="flex" gap={1.5}>
          <Button
            variant="contained"
            size="small"
            startIcon={<InsightsIcon sx={{ fontSize: 16 }} />}
            onClick={onOpenOverview}
            sx={{
              borderRadius: 2,
              px: 2,
              py: 0.75,
              fontWeight: 600,
              textTransform: 'none',
            }}
            title="AI Overview of all metrics"
          >
            AI Overview
          </Button>
          <IconButton
            onClick={onOpenKPISelector}
            sx={{
              border: `1px solid ${theme.palette.divider}`,
              borderRadius: 2,
              bgcolor: 'background.paper',
              '&:hover': {
                bgcolor: alpha(theme.palette.primary.main, 0.05),
              }
            }}
            title="Configure KPIs"
          >
            <SettingsIcon sx={{ fontSize: 20 }} />
          </IconButton>
          {!isPublic && (
            <Button
              variant="outlined"
              size="small"
              startIcon={<ShareIcon sx={{ fontSize: 16 }} />}
              onClick={onOpenShareDialog}
              disabled={!selectedBrandSlug}
              sx={{
                borderRadius: 2,
                px: 2,
                py: 0.75,
                fontWeight: 600,
                bgcolor: 'background.paper',
              }}
              title={selectedBrandSlug ? 'Share public dashboard URL' : 'Brand slug not configured'}
            >
              Share
            </Button>
          )}
          <Button
            variant="outlined"
            size="small"
            startIcon={<RefreshIcon sx={{ fontSize: 16 }} />}
            onClick={onRefresh}
            sx={{
              borderRadius: 2,
              px: 2,
              py: 0.75,
              fontWeight: 600,
              bgcolor: 'background.paper',
            }}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {/* Filters */}
      <Paper 
        elevation={0} 
        sx={{ 
          p: 2.5, 
          display: 'flex', 
          gap: 2, 
          flexWrap: 'wrap', 
          alignItems: 'center',
          border: `1px solid ${theme.palette.divider}`,
          borderRadius: 2,
          bgcolor: 'background.paper'
        }}
      >
        {!isPublic && (
          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>Select Brand</InputLabel>
            <Select
              value={selectedBrandId || ''}
              label="Select Brand"
              onChange={(e) => onBrandChange(e.target.value)}
            >
              {brands.map((brand) => (
                <MenuItem key={brand.id} value={brand.id}>
                  {brand.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        )}

        <Box display="flex" alignItems="center" gap={1}>
          <CalendarTodayIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
          <FormControl size="small" sx={{ minWidth: 160 }}>
            <InputLabel>Date Range</InputLabel>
            <Select
              value={datePreset}
              label="Date Range"
              onChange={(e) => onDatePresetChange(e.target.value)}
            >
              <MenuItem value="">Custom Range</MenuItem>
              {DATE_PRESETS.map((preset) => (
                <MenuItem key={preset.label} value={preset.label}>
                  {preset.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>
        
        <TextField
          label="Start Date"
          type="date"
          size="small"
          value={startDate || ''}
          onChange={(e) => onStartDateChange(e.target.value)}
          InputLabelProps={{ shrink: true }}
          sx={{ minWidth: 150 }}
        />
        
        <TextField
          label="End Date"
          type="date"
          size="small"
          value={endDate || ''}
          onChange={(e) => onEndDateChange(e.target.value)}
          InputLabelProps={{ shrink: true }}
          sx={{ minWidth: 150 }}
        />
      </Paper>
    </Box>
  )
}


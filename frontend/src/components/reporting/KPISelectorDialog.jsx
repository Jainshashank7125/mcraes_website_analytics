import {
  Box,
  Button,
  Checkbox,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  Typography,
  useTheme,
} from '@mui/material'
import { KPI_METADATA, KPI_ORDER } from './constants'
import { getSourceColor } from './utils'

export default function KPISelectorDialog({
  open,
  onClose,
  tempSelectedKPIs,
  dashboardData,
  onKPIChange,
  onSelectAll,
  onDeselectAll,
  onSave,
  selectedKPIs,
}) {
  const theme = useTheme()

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: { borderRadius: 2 }
      }}
    >
      <DialogTitle>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h6" fontWeight={600}>
            Select KPIs to Display
          </Typography>
          <Box display="flex" gap={1}>
            <Button size="small" onClick={onSelectAll} variant="outlined">
              Select All
            </Button>
            <Button size="small" onClick={onDeselectAll} variant="outlined">
              Deselect All
            </Button>
          </Box>
        </Box>
      </DialogTitle>
      <DialogContent dividers sx={{ maxHeight: 500, overflow: 'auto' }}>
        <Box>
          {/* Group KPIs by source */}
          {['GA4', 'AgencyAnalytics', 'Scrunch'].map((source) => {
            const sourceKPIs = KPI_ORDER.filter(key => {
              const metadata = KPI_METADATA[key]
              return metadata && metadata.source === source
            })
            
            return (
              <Box key={source} mb={3}>
                <Typography 
                  variant="subtitle1" 
                  fontWeight={600} 
                  mb={1.5}
                  sx={{ 
                    color: getSourceColor(source, theme),
                    textTransform: 'uppercase',
                    fontSize: '0.75rem',
                    letterSpacing: '0.05em'
                  }}
                >
                  {source} ({sourceKPIs.filter(k => tempSelectedKPIs.has(k)).length} / {sourceKPIs.length})
                </Typography>
                <Box display="flex" flexDirection="column" gap={1}>
                  {sourceKPIs.map((key) => {
                    const metadata = KPI_METADATA[key]
                    const kpi = dashboardData?.kpis?.[key]
                    const isAvailable = !!kpi
                    
                    return (
                      <FormControlLabel
                        key={key}
                        control={
                          <Checkbox
                            checked={tempSelectedKPIs.has(key)}
                            onChange={(e) => onKPIChange(key, e.target.checked)}
                            disabled={!isAvailable}
                            sx={{
                              color: getSourceColor(source, theme),
                              '&.Mui-checked': {
                                color: getSourceColor(source, theme),
                              },
                              '&.Mui-disabled': {
                                color: theme.palette.grey[400],
                              },
                            }}
                          />
                        }
                        label={
                          <Box display="flex" alignItems="center" justifyContent="space-between" width="100%">
                            <Box>
                              <Typography variant="body2" fontWeight={600}>
                                {metadata.label}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {metadata.source}
                              </Typography>
                            </Box>
                            {!isAvailable && (
                              <Chip
                                label="Not Available"
                                size="small"
                                sx={{
                                  height: 20,
                                  fontSize: '0.7rem',
                                  bgcolor: theme.palette.grey[100],
                                  color: theme.palette.grey[600],
                                }}
                              />
                            )}
                          </Box>
                        }
                        sx={{ 
                          mb: 0.5, 
                          width: '100%',
                          opacity: isAvailable ? 1 : 0.6
                        }}
                      />
                    )
                  })}
                </Box>
              </Box>
            )
          })}
        </Box>
      </DialogContent>
      <DialogActions sx={{ p: 2, borderTop: `1px solid ${theme.palette.divider}` }}>
        <Button 
          onClick={() => {
            onClose()
          }}
          variant="outlined"
        >
          Cancel
        </Button>
        <Button 
          onClick={onSave} 
          variant="contained"
          disabled={tempSelectedKPIs.size === 0}
          sx={{
            bgcolor: theme.palette.primary.main,
            '&:hover': {
              bgcolor: theme.palette.primary.dark,
            }
          }}
        >
          Save Changes
        </Button>
      </DialogActions>
    </Dialog>
  )
}


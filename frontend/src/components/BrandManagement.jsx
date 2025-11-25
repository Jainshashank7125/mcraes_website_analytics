import { useState, useEffect } from 'react'
import {
  Box,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Typography,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  alpha,
  useTheme,
  Grid,
} from '@mui/material'
import {
  Close as CloseIcon,
  Link as LinkIcon,
  LinkOff as LinkOffIcon,
  Analytics as AnalyticsIcon,
  CheckCircle as CheckCircleIcon,
  Image as ImageIcon,
  Delete as DeleteIcon,
  Palette as PaletteIcon,
  Upload as UploadIcon,
} from '@mui/icons-material'
import { dataAPI } from '../services/api'
import { useToast } from '../contexts/ToastContext'
import { getErrorMessage } from '../utils/errorHandler'

function BrandManagement({ open, onClose, brand }) {
  const theme = useTheme()
  const { showError, showSuccess } = useToast()
  
  const [ga4PropertyId, setGa4PropertyId] = useState('')
  const [logoUrl, setLogoUrl] = useState('')
  const [logoFile, setLogoFile] = useState(null)
  const [brandTheme, setBrandTheme] = useState({
    primary_color: '',
    secondary_color: '',
    accent_color: '',
    font_family: '',
  })
  const [linkedCampaigns, setLinkedCampaigns] = useState([])
  const [availableCampaigns, setAvailableCampaigns] = useState([])
  const [selectedCampaignId, setSelectedCampaignId] = useState('')
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [campaignsLoading, setCampaignsLoading] = useState(false)

  useEffect(() => {
    if (open && brand) {
      loadBrandData()
    }
  }, [open, brand])

  const loadBrandData = async () => {
    if (!brand) return
    
    setLoading(true)
    try {
      // Load GA4 property ID from brand
      setGa4PropertyId(brand.ga4_property_id || '')
      
      // Load logo URL
      setLogoUrl(brand.logo_url || '')
      
      // Load theme
      if (brand.theme && typeof brand.theme === 'object') {
        setBrandTheme({
          primary_color: brand.theme.primary_color || '',
          secondary_color: brand.theme.secondary_color || '',
          accent_color: brand.theme.accent_color || '',
          font_family: brand.theme.font_family || '',
        })
      }
      
      // Load linked campaigns
      await loadLinkedCampaigns()
    } catch (err) {
      showError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  const loadLinkedCampaigns = async () => {
    if (!brand) return
    
    setCampaignsLoading(true)
    try {
      const data = await dataAPI.getBrandLinkedCampaigns(brand.id)
      setLinkedCampaigns(data.linked_campaigns || [])
      setAvailableCampaigns(data.available_campaigns || [])
    } catch (err) {
      showError(getErrorMessage(err))
    } finally {
      setCampaignsLoading(false)
    }
  }

  const handleSaveGA4PropertyId = async () => {
    if (!brand) return
    
    setSaving(true)
    try {
      await dataAPI.updateBrandGA4PropertyId(brand.id, ga4PropertyId || null)
      showSuccess('GA4 Property ID updated successfully')
      onClose()
    } catch (err) {
      showError(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  const handleLinkCampaign = async () => {
    if (!brand || !selectedCampaignId) return
    
    setSaving(true)
    try {
      await dataAPI.linkAgencyAnalyticsCampaign(brand.id, parseInt(selectedCampaignId))
      showSuccess('Campaign linked successfully')
      setSelectedCampaignId('')
      await loadLinkedCampaigns()
    } catch (err) {
      showError(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  const handleUnlinkCampaign = async (campaignId) => {
    if (!brand) return
    
    setSaving(true)
    try {
      await dataAPI.unlinkAgencyAnalyticsCampaign(brand.id, campaignId)
      showSuccess('Campaign unlinked successfully')
      await loadLinkedCampaigns()
    } catch (err) {
      showError(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  const getLinkedCampaignIds = () => {
    return new Set(linkedCampaigns.map(c => c.id))
  }

  const getUnlinkedCampaigns = () => {
    const linkedIds = getLinkedCampaignIds()
    return availableCampaigns.filter(c => !linkedIds.has(c.id))
  }

  const handleLogoUpload = async () => {
    if (!brand || !logoFile) return
    
    setSaving(true)
    try {
      const result = await dataAPI.uploadBrandLogo(brand.id, logoFile)
      setLogoUrl(result.logo_url)
      setLogoFile(null)
      showSuccess('Logo uploaded successfully')
    } catch (err) {
      showError(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  const handleLogoDelete = async () => {
    if (!brand) return
    
    setSaving(true)
    try {
      await dataAPI.deleteBrandLogo(brand.id)
      setLogoUrl('')
      setLogoFile(null)
      showSuccess('Logo deleted successfully')
    } catch (err) {
      showError(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  const handleThemeUpdate = async () => {
    if (!brand) return
    
    setSaving(true)
    try {
      await dataAPI.updateBrandTheme(brand.id, brandTheme)
      showSuccess('Theme updated successfully')
    } catch (err) {
      showError(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    if (file) {
      if (!file.type.startsWith('image/')) {
        showError('Please select an image file')
        return
      }
      setLogoFile(file)
    }
  }

  // Helper function to normalize hex color value
  const normalizeHexColor = (value) => {
    if (!value) return ''
    // Remove any whitespace
    value = value.trim()
    // If it doesn't start with #, add it
    if (!value.startsWith('#')) {
      value = '#' + value
    }
    // Ensure it's a valid hex format (max 6 hex digits after #)
    const hexMatch = value.match(/^#([0-9A-Fa-f]{0,6})$/)
    if (hexMatch) {
      return value.toUpperCase()
    }
    return value
  }

  const handleHexColorChange = (colorField, value) => {
    const normalized = normalizeHexColor(value)
    // Only update if it's a valid hex format or empty
    if (normalized === '' || /^#[0-9A-Fa-f]{1,6}$/.test(normalized)) {
      setBrandTheme({ ...brandTheme, [colorField]: normalized })
    }
  }

  if (!brand) return null

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 2,
          boxShadow: '0 8px 32px rgba(0,0,0,0.12)',
        },
      }}
    >
      <DialogTitle
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          pb: 1,
        }}
      >
        <Box display="flex" alignItems="center" gap={1}>
          <AnalyticsIcon sx={{ color: theme.palette.primary.main }} />
          <Typography variant="h6" fontWeight={600}>
            Manage {brand.name}
          </Typography>
        </Box>
        <IconButton
          onClick={onClose}
          size="small"
          sx={{
            color: 'text.secondary',
            '&:hover': {
              bgcolor: alpha(theme.palette.error.main, 0.1),
              color: theme.palette.error.main,
            },
          }}
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent>
        {loading ? (
          <Box display="flex" justifyContent="center" alignItems="center" py={4}>
            <CircularProgress size={40} />
          </Box>
        ) : (
          <Box>
            {/* Logo Section */}
            <Box mb={4}>
              <Typography variant="subtitle1" fontWeight={600} mb={2}>
                Brand Logo
              </Typography>
              {logoUrl ? (
                <Box mb={2}>
                  <Box
                    component="img"
                    src={logoUrl}
                    alt={`${brand.name} logo`}
                    sx={{
                      maxWidth: 200,
                      maxHeight: 200,
                      borderRadius: 1.5,
                      border: `1px solid ${theme.palette.divider}`,
                      mb: 2,
                    }}
                  />
                  <Box display="flex" gap={1}>
                    <Button
                      variant="outlined"
                      component="label"
                      startIcon={<UploadIcon />}
                      disabled={saving}
                      sx={{
                        borderRadius: 1.5,
                        textTransform: 'none',
                        fontWeight: 600,
                      }}
                    >
                      Replace Logo
                      <input
                        type="file"
                        hidden
                        accept="image/*"
                        onChange={handleFileChange}
                      />
                    </Button>
                    {logoFile && (
                      <Button
                        variant="contained"
                        onClick={handleLogoUpload}
                        disabled={saving}
                        startIcon={saving ? <CircularProgress size={16} /> : <CheckCircleIcon />}
                        sx={{
                          borderRadius: 1.5,
                          textTransform: 'none',
                          fontWeight: 600,
                        }}
                      >
                        {saving ? 'Uploading...' : 'Upload'}
                      </Button>
                    )}
                    <Button
                      variant="outlined"
                      color="error"
                      onClick={handleLogoDelete}
                      disabled={saving}
                      startIcon={<DeleteIcon />}
                      sx={{
                        borderRadius: 1.5,
                        textTransform: 'none',
                        fontWeight: 600,
                      }}
                    >
                      Delete
                    </Button>
                  </Box>
                </Box>
              ) : (
                <Box>
                  <Button
                    variant="outlined"
                    component="label"
                    startIcon={<ImageIcon />}
                    disabled={saving}
                    sx={{
                      borderRadius: 1.5,
                      textTransform: 'none',
                      fontWeight: 600,
                      mb: 2,
                    }}
                  >
                    Upload Logo
                    <input
                      type="file"
                      hidden
                      accept="image/*"
                      onChange={handleFileChange}
                    />
                  </Button>
                  {logoFile && (
                    <Box>
                      <Typography variant="body2" color="text.secondary" mb={1}>
                        Selected: {logoFile.name}
                      </Typography>
                      <Button
                        variant="contained"
                        onClick={handleLogoUpload}
                        disabled={saving}
                        startIcon={saving ? <CircularProgress size={16} /> : <CheckCircleIcon />}
                        sx={{
                          borderRadius: 1.5,
                          textTransform: 'none',
                          fontWeight: 600,
                        }}
                      >
                        {saving ? 'Uploading...' : 'Upload Logo'}
                      </Button>
                    </Box>
                  )}
                </Box>
              )}
            </Box>

            <Divider sx={{ my: 3 }} />

            {/* Theme Section */}
            <Box mb={4}>
              <Typography variant="subtitle1" fontWeight={600} mb={2}>
                Brand Theme
              </Typography>
              <Grid container spacing={2} mb={2}>
                <Grid item xs={12} sm={6}>
                  <Box display="flex" gap={1} alignItems="flex-end">
                    <TextField
                      fullWidth
                      label="Primary Color"
                      type="color"
                      value={brandTheme.primary_color || '#1976d2'}
                      onChange={(e) => setBrandTheme({ ...brandTheme, primary_color: e.target.value })}
                      InputLabelProps={{ shrink: true }}
                      sx={{ mb: 2 }}
                    />
                    <TextField
                      label="Hex Value"
                      value={brandTheme.primary_color || '#1976d2'}
                      onChange={(e) => handleHexColorChange('primary_color', e.target.value)}
                      onBlur={(e) => {
                        // Normalize on blur to ensure proper format
                        const normalized = normalizeHexColor(e.target.value)
                        if (normalized && /^#[0-9A-Fa-f]{6}$/.test(normalized)) {
                          setBrandTheme({ ...brandTheme, primary_color: normalized })
                        }
                      }}
                      placeholder="#1976d2"
                      size="small"
                      sx={{ mb: 2, minWidth: 120 }}
                      helperText="Enter hex value (e.g., #1976d2)"
                    />
                  </Box>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Box display="flex" gap={1} alignItems="flex-end">
                    <TextField
                      fullWidth
                      label="Secondary Color"
                      type="color"
                      value={brandTheme.secondary_color || '#dc004e'}
                      onChange={(e) => setBrandTheme({ ...brandTheme, secondary_color: e.target.value })}
                      InputLabelProps={{ shrink: true }}
                      sx={{ mb: 2 }}
                    />
                    <TextField
                      label="Hex Value"
                      value={brandTheme.secondary_color || '#dc004e'}
                      onChange={(e) => handleHexColorChange('secondary_color', e.target.value)}
                      onBlur={(e) => {
                        // Normalize on blur to ensure proper format
                        const normalized = normalizeHexColor(e.target.value)
                        if (normalized && /^#[0-9A-Fa-f]{6}$/.test(normalized)) {
                          setBrandTheme({ ...brandTheme, secondary_color: normalized })
                        }
                      }}
                      placeholder="#dc004e"
                      size="small"
                      sx={{ mb: 2, minWidth: 120 }}
                      helperText="Enter hex value (e.g., #dc004e)"
                    />
                  </Box>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Box display="flex" gap={1} alignItems="flex-end">
                    <TextField
                      fullWidth
                      label="Accent Color"
                      type="color"
                      value={brandTheme.accent_color || '#ff9800'}
                      onChange={(e) => setBrandTheme({ ...brandTheme, accent_color: e.target.value })}
                      InputLabelProps={{ shrink: true }}
                      sx={{ mb: 2 }}
                    />
                    <TextField
                      label="Hex Value"
                      value={brandTheme.accent_color || '#ff9800'}
                      onChange={(e) => handleHexColorChange('accent_color', e.target.value)}
                      onBlur={(e) => {
                        // Normalize on blur to ensure proper format
                        const normalized = normalizeHexColor(e.target.value)
                        if (normalized && /^#[0-9A-Fa-f]{6}$/.test(normalized)) {
                          setBrandTheme({ ...brandTheme, accent_color: normalized })
                        }
                      }}
                      placeholder="#ff9800"
                      size="small"
                      sx={{ mb: 2, minWidth: 120 }}
                      helperText="Enter hex value (e.g., #ff9800)"
                    />
                  </Box>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Font Family"
                    value={brandTheme.font_family}
                    onChange={(e) => setBrandTheme({ ...brandTheme, font_family: e.target.value })}
                    placeholder="e.g., 'Roboto', 'Arial', 'Inter'"
                    helperText="Enter font family name"
                    sx={{ mb: 2 }}
                  />
                </Grid>
              </Grid>
              <Button
                variant="contained"
                onClick={handleThemeUpdate}
                disabled={saving}
                startIcon={saving ? <CircularProgress size={16} /> : <PaletteIcon />}
                sx={{
                  borderRadius: 1.5,
                  textTransform: 'none',
                  fontWeight: 600,
                }}
              >
                {saving ? 'Saving...' : 'Save Theme'}
              </Button>
            </Box>

            <Divider sx={{ my: 3 }} />

            {/* GA4 Property ID Section */}
            <Box mb={4}>
              <Typography variant="subtitle1" fontWeight={600} mb={2}>
                Google Analytics 4 Property ID
              </Typography>
              <TextField
                fullWidth
                label="GA4 Property ID"
                value={ga4PropertyId}
                onChange={(e) => setGa4PropertyId(e.target.value)}
                placeholder="e.g., 123456789"
                helperText="Enter the GA4 Property ID for this brand. Leave empty to clear."
                sx={{ mb: 2 }}
              />
              <Button
                variant="contained"
                onClick={handleSaveGA4PropertyId}
                disabled={saving}
                startIcon={saving ? <CircularProgress size={16} /> : <CheckCircleIcon />}
                sx={{
                  borderRadius: 1.5,
                  textTransform: 'none',
                  fontWeight: 600,
                }}
              >
                {saving ? 'Saving...' : 'Save GA4 Property ID'}
              </Button>
            </Box>

            <Divider sx={{ my: 3 }} />

            {/* Agency Analytics Campaigns Section */}
            <Box>
              <Typography variant="subtitle1" fontWeight={600} mb={2}>
                Agency Analytics Campaigns
              </Typography>

              {/* Link New Campaign */}
              <Box mb={3}>
                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>Select Campaign to Link</InputLabel>
                  <Select
                    value={selectedCampaignId}
                    onChange={(e) => setSelectedCampaignId(e.target.value)}
                    label="Select Campaign to Link"
                    disabled={saving || campaignsLoading}
                  >
                    {getUnlinkedCampaigns().map((campaign) => (
                      <MenuItem key={campaign.id} value={campaign.id}>
                        <Box>
                          <Typography variant="body1" fontWeight={500}>
                            {campaign.company || campaign.url || `Campaign ${campaign.id}`}
                          </Typography>
                          {campaign.url && (
                            <Typography variant="caption" color="text.secondary">
                              {campaign.url}
                            </Typography>
                          )}
                        </Box>
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                <Button
                  variant="outlined"
                  onClick={handleLinkCampaign}
                  disabled={!selectedCampaignId || saving || campaignsLoading}
                  startIcon={<LinkIcon />}
                  sx={{
                    borderRadius: 1.5,
                    textTransform: 'none',
                    fontWeight: 600,
                  }}
                >
                  Link Campaign
                </Button>
              </Box>

              {/* Linked Campaigns List */}
              {campaignsLoading ? (
                <Box display="flex" justifyContent="center" py={2}>
                  <CircularProgress size={24} />
                </Box>
              ) : linkedCampaigns.length > 0 ? (
                <List
                  sx={{
                    bgcolor: alpha(theme.palette.primary.main, 0.02),
                    borderRadius: 1.5,
                    border: `1px solid ${theme.palette.divider}`,
                  }}
                >
                  {linkedCampaigns.map((campaign) => (
                    <ListItem
                      key={campaign.id}
                      sx={{
                        borderBottom: `1px solid ${theme.palette.divider}`,
                        '&:last-child': {
                          borderBottom: 'none',
                        },
                      }}
                    >
                      <ListItemText
                        primary={
                          <Box display="flex" alignItems="center" gap={1}>
                            <Typography variant="body1" fontWeight={500}>
                              {campaign.company || campaign.url || `Campaign ${campaign.id}`}
                            </Typography>
                            <Chip
                              label="Linked"
                              size="small"
                              color="success"
                              icon={<CheckCircleIcon />}
                              sx={{ height: 20, fontSize: '0.7rem' }}
                            />
                          </Box>
                        }
                        secondary={
                          campaign.url && (
                            <Typography variant="caption" color="text.secondary">
                              {campaign.url}
                            </Typography>
                          )
                        }
                      />
                      <ListItemSecondaryAction>
                        <IconButton
                          edge="end"
                          onClick={() => handleUnlinkCampaign(campaign.id)}
                          disabled={saving}
                          sx={{
                            color: theme.palette.error.main,
                            '&:hover': {
                              bgcolor: alpha(theme.palette.error.main, 0.1),
                            },
                          }}
                        >
                          <LinkOffIcon />
                        </IconButton>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Box
                  sx={{
                    p: 3,
                    textAlign: 'center',
                    bgcolor: alpha(theme.palette.primary.main, 0.02),
                    borderRadius: 1.5,
                    border: `1px dashed ${theme.palette.divider}`,
                  }}
                >
                  <Typography variant="body2" color="text.secondary">
                    No campaigns linked. Select a campaign above to link it to this brand.
                  </Typography>
                </Box>
              )}
            </Box>
          </Box>
        )}
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button
          onClick={onClose}
          disabled={saving}
          sx={{
            borderRadius: 1.5,
            textTransform: 'none',
            fontWeight: 600,
          }}
        >
          Close
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default BrandManagement


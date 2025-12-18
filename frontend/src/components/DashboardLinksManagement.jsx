import { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  IconButton,
  CircularProgress,
  Alert,
  Autocomplete,
  Button,
  alpha,
  useTheme,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Checkbox,
  FormControlLabel,
  Collapse,
} from '@mui/material';
import {
  Link as LinkIcon,
  ContentCopy as ContentCopyIcon,
  Check as CheckIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  FilterList as FilterListIcon,
  Clear as ClearIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  BarChart as BarChartIcon,
} from '@mui/icons-material';
import { clientAPI } from '../services/api';
import { debugLog, debugError } from '../utils/debug';

function DashboardLinksManagement() {
  const theme = useTheme();
  const [allLinks, setAllLinks] = useState([]);
  const [filteredLinks, setFilteredLinks] = useState([]);
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Filter states
  const [selectedClient, setSelectedClient] = useState(null);
  const [dateCreatedFrom, setDateCreatedFrom] = useState('');
  const [dateCreatedTo, setDateCreatedTo] = useState('');
  const [expirationDateFrom, setExpirationDateFrom] = useState('');
  const [expirationDateTo, setExpirationDateTo] = useState('');
  const [activeStatus, setActiveStatus] = useState('all'); // 'all', 'active', 'inactive'
  
  const [copiedLinkId, setCopiedLinkId] = useState(null);
  const [filtersExpanded, setFiltersExpanded] = useState(true);
  
  // Edit dialog states
  const [linkDialogOpen, setLinkDialogOpen] = useState(false);
  const [editingLink, setEditingLink] = useState(null);
  const [linkFormData, setLinkFormData] = useState({
    name: '',
    description: '',
    start_date: '',
    end_date: '',
    enabled: true,
    expires_at: '',
    slug: ''
  });
  const [saving, setSaving] = useState(false);

  // Tracking metrics dialog states
  const [trackingDialogOpen, setTrackingDialogOpen] = useState(false);
  const [trackingLink, setTrackingLink] = useState(null);
  const [trackingMetrics, setTrackingMetrics] = useState(null);
  const [loadingMetrics, setLoadingMetrics] = useState(false);

  // Load all clients and their dashboard links
  useEffect(() => {
    loadAllLinks();
  }, []);

  // Apply filters whenever filter states change
  useEffect(() => {
    applyFilters();
  }, [
    allLinks,
    selectedClient,
    dateCreatedFrom,
    dateCreatedTo,
    expirationDateFrom,
    expirationDateTo,
    activeStatus,
  ]);

  const loadAllLinks = async () => {
    setLoading(true);
    setError(null);
    try {
      // Load all clients and all dashboard links in parallel
      const [clientsResponse, linksResponse] = await Promise.all([
        clientAPI.getClients(1, 1000, ''), // Get up to 1000 clients
        clientAPI.listAllDashboardLinks() // Get all dashboard links in a single API call
      ]);
      
      const clientsList = clientsResponse.items || [];
      setClients(clientsList);

      // Create a map of client IDs to client names for quick lookup
      const clientsMap = new Map();
      clientsList.forEach(client => {
        clientsMap.set(client.id, client.company_name);
      });

      // Process links - KPI selections and client info are already included from backend
      const allLinks = (linksResponse.items || []).map((link) => ({
        ...link,
        // Ensure client_id and client_name are set (backend should provide these, but ensure they exist)
        client_id: link.client_id || null,
        client_name: link.client_name || clientsMap.get(link.client_id) || 'Unknown',
        // Use kpi_selection from backend response (already included)
        // Map to kpi_selections for consistency with component usage
        kpi_selections: link.kpi_selection || null,
      }));

      setAllLinks(allLinks);
      debugLog('Loaded all dashboard links:', allLinks.length);
    } catch (err) {
      debugError('Error loading dashboard links:', err);
      setError('Failed to load dashboard links');
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...allLinks];

    // Filter by client
    if (selectedClient) {
      filtered = filtered.filter(link => link.client_id === selectedClient.id);
    }

    // Filter by date created
    if (dateCreatedFrom) {
      filtered = filtered.filter(link => {
        if (!link.created_at) return false;
        const linkDate = new Date(link.created_at).toISOString().split('T')[0];
        return linkDate >= dateCreatedFrom;
      });
    }
    if (dateCreatedTo) {
      filtered = filtered.filter(link => {
        if (!link.created_at) return false;
        const linkDate = new Date(link.created_at).toISOString().split('T')[0];
        return linkDate <= dateCreatedTo;
      });
    }

    // Filter by expiration date
    if (expirationDateFrom) {
      filtered = filtered.filter(link => {
        if (!link.expires_at) return true; // Include links without expiration
        const linkDate = new Date(link.expires_at).toISOString().split('T')[0];
        return linkDate >= expirationDateFrom;
      });
    }
    if (expirationDateTo) {
      filtered = filtered.filter(link => {
        if (!link.expires_at) return true; // Include links without expiration
        const linkDate = new Date(link.expires_at).toISOString().split('T')[0];
        return linkDate <= expirationDateTo;
      });
    }

    // Filter by active status
    if (activeStatus === 'active') {
      filtered = filtered.filter(link => link.enabled === true);
    } else if (activeStatus === 'inactive') {
      filtered = filtered.filter(link => link.enabled === false);
    }

    setFilteredLinks(filtered);
  };

  const handleCopyLink = (link) => {
    const baseUrl = window.location.origin;
    const url = `${baseUrl}/reporting/client/${link.slug}`;
    navigator.clipboard.writeText(url).then(() => {
      setCopiedLinkId(link.id);
      setTimeout(() => setCopiedLinkId(null), 2000);
    }).catch(() => {
      setError('Failed to copy URL');
    });
  };

  const handleClearFilters = () => {
    setSelectedClient(null);
    setDateCreatedFrom('');
    setDateCreatedTo('');
    setExpirationDateFrom('');
    setExpirationDateTo('');
    setActiveStatus('all');
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleDateString();
    } catch {
      return dateString;
    }
  };

  const formatDateTime = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return dateString;
    }
  };

  const isExpired = (link) => {
    if (!link.expires_at) return false;
    return new Date(link.expires_at) < new Date();
  };

  const handleEditLink = (link) => {
    setEditingLink(link);
    // Format expires_at for datetime-local input (YYYY-MM-DDTHH:mm)
    let expiresAtFormatted = '';
    if (link.expires_at) {
      const expiresDate = new Date(link.expires_at);
      const year = expiresDate.getFullYear();
      const month = String(expiresDate.getMonth() + 1).padStart(2, '0');
      const day = String(expiresDate.getDate()).padStart(2, '0');
      const hours = String(expiresDate.getHours()).padStart(2, '0');
      const minutes = String(expiresDate.getMinutes()).padStart(2, '0');
      expiresAtFormatted = `${year}-${month}-${day}T${hours}:${minutes}`;
    }
    setLinkFormData({
      name: link.name || '',
      description: link.description || '',
      start_date: link.start_date ? link.start_date.split('T')[0] : '',
      end_date: link.end_date ? link.end_date.split('T')[0] : '',
      enabled: link.enabled !== undefined ? link.enabled : true,
      expires_at: expiresAtFormatted,
      slug: link.slug || ''
    });
    setLinkDialogOpen(true);
  };

  const handleSaveLink = async () => {
    if (!editingLink || !editingLink.client_id) return;
    if (!linkFormData.start_date || !linkFormData.end_date) {
      setError("Start date and end date are required");
      return;
    }
    
    setSaving(true);
    try {
      // Prepare payload - convert datetime-local to ISO string if expires_at is provided
      const payload = { ...linkFormData };
      if (payload.expires_at) {
        const dt = new Date(payload.expires_at);
        if (!isNaN(dt.getTime())) {
          payload.expires_at = dt.toISOString();
        } else {
          delete payload.expires_at;
        }
      } else {
        delete payload.expires_at;
      }
      
      // Update existing link (don't modify KPI selections from this view)
      await clientAPI.updateDashboardLink(editingLink.client_id, editingLink.id, payload);
      setError(null);
      setLinkDialogOpen(false);
      await loadAllLinks();
      debugLog("Dashboard link updated successfully");
    } catch (err) {
      debugError("Error saving dashboard link:", err);
      setError(err.response?.data?.detail || err.message || "Failed to save dashboard link");
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteLink = async (link) => {
    if (!link.client_id) return;
    if (!window.confirm(`Are you sure you want to delete this dashboard link "${link.name || link.slug}"? This action cannot be undone.`)) {
      return;
    }
    
    setLoading(true);
    try {
      await clientAPI.deleteDashboardLink(link.client_id, link.id);
      setError(null);
      await loadAllLinks();
      debugLog("Dashboard link deleted successfully");
    } catch (err) {
      debugError("Error deleting dashboard link:", err);
      setError(err.response?.data?.detail || err.message || "Failed to delete dashboard link");
    } finally {
      setLoading(false);
    }
  };

  const handleToggleLinkEnabled = async (link) => {
    if (!link.client_id) return;
    setLoading(true);
    try {
      await clientAPI.updateDashboardLink(link.client_id, link.id, {
        enabled: !link.enabled
      });
      setError(null);
      await loadAllLinks();
      debugLog("Dashboard link status toggled successfully");
    } catch (err) {
      debugError("Error toggling link enabled:", err);
      setError(err.response?.data?.detail || err.message || "Failed to update link");
    } finally {
      setLoading(false);
    }
  };

  const handleOpenTrackingDialog = async (link) => {
    if (!link.client_id) return;
    setTrackingLink(link);
    setTrackingDialogOpen(true);
    setLoadingMetrics(true);
    setTrackingMetrics(null);
    
    try {
      const metrics = await clientAPI.getDashboardLinkMetrics(link.client_id, link.id);
      setTrackingMetrics(metrics);
      debugLog("Tracking metrics loaded:", metrics);
    } catch (err) {
      debugError("Error loading tracking metrics:", err);
      setError(err.response?.data?.detail || err.message || "Failed to load tracking metrics");
      setTrackingMetrics({
        total_opens: 0,
        opens_over_time: [],
        recent_opens: []
      });
    } finally {
      setLoadingMetrics(false);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" fontWeight={700}>
          Dashboard Links Management
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Filters Section */}
      <Paper sx={{ p: 3, mb: 3, border: `1px solid ${theme.palette.divider}` }}>
        <Box 
          display="flex" 
          alignItems="center" 
          justifyContent="space-between"
        >
          <Box
            display="flex"
            alignItems="center"
            gap={1}
            sx={{ 
              cursor: 'pointer',
              userSelect: 'none',
            }}
            onClick={() => setFiltersExpanded(!filtersExpanded)}
          >
            <FilterListIcon />
            <Typography variant="h6" fontWeight={600}>
              Filters
            </Typography>
          </Box>
          <Box display="flex" alignItems="center" gap={1}>
            <Button
              variant="outlined"
              size="small"
              startIcon={<ClearIcon />}
              onClick={handleClearFilters}
              sx={{ textTransform: 'none' }}
            >
              Clear Filters
            </Button>
            <IconButton size="small" onClick={(e) => {
              e.stopPropagation();
              setFiltersExpanded(!filtersExpanded);
            }}>
              {filtersExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            </IconButton>
          </Box>
        </Box>
        <Collapse in={filtersExpanded}>
          <Box display="flex" gap={2} flexWrap="wrap" alignItems="center" mt={2}>
            <Autocomplete
              size="small"
              sx={{ minWidth: 250 }}
              options={clients}
              getOptionLabel={(option) => option.company_name || ''}
              value={selectedClient}
              onChange={(event, newValue) => setSelectedClient(newValue)}
              renderInput={(params) => (
                <TextField {...params} label="Client" />
              )}
            />
            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>Active Status</InputLabel>
              <Select
                value={activeStatus}
                label="Active Status"
                onChange={(e) => setActiveStatus(e.target.value)}
              >
                <MenuItem value="all">All</MenuItem>
                <MenuItem value="active">Active</MenuItem>
                <MenuItem value="inactive">Inactive</MenuItem>
              </Select>
            </FormControl>
            <TextField
              label="Date Created From"
              type="date"
              size="small"
              value={dateCreatedFrom}
              onChange={(e) => setDateCreatedFrom(e.target.value)}
              InputLabelProps={{ shrink: true }}
              sx={{ minWidth: 180 }}
            />
            <TextField
              label="Date Created To"
              type="date"
              size="small"
              value={dateCreatedTo}
              onChange={(e) => setDateCreatedTo(e.target.value)}
              InputLabelProps={{ shrink: true }}
              sx={{ minWidth: 180 }}
            />
            <TextField
              label="Expiration From"
              type="date"
              size="small"
              value={expirationDateFrom}
              onChange={(e) => setExpirationDateFrom(e.target.value)}
              InputLabelProps={{ shrink: true }}
              sx={{ minWidth: 180 }}
            />
            <TextField
              label="Expiration To"
              type="date"
              size="small"
              value={expirationDateTo}
              onChange={(e) => setExpirationDateTo(e.target.value)}
              InputLabelProps={{ shrink: true }}
              sx={{ minWidth: 180 }}
            />
          </Box>
        </Collapse>
      </Paper>

      {/* Results Summary */}
      <Box mb={2}>
        <Typography variant="body2" color="text.secondary">
          Showing {filteredLinks.length} of {allLinks.length} links
        </Typography>
      </Box>

      {/* Links Table */}
      {loading ? (
        <Box display="flex" justifyContent="center" py={4}>
          <CircularProgress />
        </Box>
      ) : filteredLinks.length === 0 ? (
        <Alert severity="info">No dashboard links found matching the filters.</Alert>
      ) : (
        <TableContainer component={Paper} sx={{ border: `1px solid ${theme.palette.divider}` }}>
          <Table>
            <TableHead>
              <TableRow sx={{ bgcolor: alpha(theme.palette.primary.main, 0.04) }}>
                <TableCell sx={{ fontWeight: 700 }}>Name</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Client</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Slug</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Date Created</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Expiration Date</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>KPI Selections</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredLinks.map((link) => (
                <TableRow key={link.id} hover>
                  <TableCell>
                    <Typography variant="body2" fontWeight={500}>
                      {link.name || `Link ${link.id}`}
                    </Typography>
                    {link.description && (
                      <Typography variant="caption" color="text.secondary">
                        {link.description}
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{link.client_name || 'N/A'}</Typography>
                  </TableCell>
                  <TableCell>
                    <Box display="flex" alignItems="center" gap={1}>
                      <Typography
                        variant="body2"
                        sx={{
                          fontFamily: 'monospace',
                          fontSize: '0.75rem',
                          maxWidth: 200,
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                        }}
                      >
                        {link.slug}
                      </Typography>
                      <Tooltip title={copiedLinkId === link.id ? 'Copied!' : 'Copy URL'}>
                        <IconButton
                          size="small"
                          onClick={() => handleCopyLink(link)}
                          sx={{ p: 0.5 }}
                        >
                          {copiedLinkId === link.id ? (
                            <CheckIcon fontSize="small" color="success" />
                          ) : (
                            <ContentCopyIcon fontSize="small" />
                          )}
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={link.enabled ? 'Active' : 'Inactive'}
                      size="small"
                      color={link.enabled ? 'success' : 'default'}
                      icon={link.enabled ? <VisibilityIcon /> : <VisibilityOffIcon />}
                      sx={{ fontWeight: 600 }}
                    />
                    {isExpired(link) && (
                      <Chip
                        label="Expired"
                        size="small"
                        color="error"
                        sx={{ ml: 0.5, fontWeight: 600 }}
                      />
                    )}
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{formatDate(link.created_at)}</Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {link.expires_at ? formatDateTime(link.expires_at) : 'Never'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {link.kpi_selections ? (
                      <Box>
                        <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 0.5 }}>
                          <strong>Sections:</strong> {link.kpi_selections.visible_sections?.length > 0 
                            ? link.kpi_selections.visible_sections.join(', ') 
                            : 'All'}
                        </Typography>
                        <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 0.5 }}>
                          <strong>Section KPIs:</strong> {link.kpi_selections.selected_kpis?.length > 0 
                            ? `${link.kpi_selections.selected_kpis.length} selected` 
                            : 'All'}
                        </Typography>
                        <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 0.5 }}>
                          <strong>Performance Metrics:</strong> {link.kpi_selections.selected_performance_metrics_kpis?.length > 0 
                            ? `${link.kpi_selections.selected_performance_metrics_kpis.length} selected` 
                            : 'All'}
                        </Typography>
                        <Typography variant="caption" color="text.secondary" display="block">
                          <strong>Charts:</strong> {link.kpi_selections.selected_charts?.length > 0 
                            ? `${link.kpi_selections.selected_charts.length} selected` 
                            : 'All'}
                        </Typography>
                      </Box>
                    ) : (
                      <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.75rem', fontStyle: 'italic' }}>
                        No selections saved
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    <Box display="flex" gap={0.5}>
                      <Tooltip title="View Link">
                        <IconButton
                          size="small"
                          onClick={() => {
                            const baseUrl = window.location.origin;
                            window.open(`${baseUrl}/reporting/client/${link.slug}`, '_blank');
                          }}
                        >
                          <LinkIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="View Tracking Metrics">
                        <IconButton
                          size="small"
                          onClick={() => handleOpenTrackingDialog(link)}
                          color="info"
                        >
                          <BarChartIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Edit Link">
                        <IconButton
                          size="small"
                          onClick={() => handleEditLink(link)}
                          color="primary"
                        >
                          <EditIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title={link.enabled ? "Disable Link" : "Enable Link"}>
                        <IconButton
                          size="small"
                          onClick={() => handleToggleLinkEnabled(link)}
                          color={link.enabled ? "warning" : "success"}
                        >
                          {link.enabled ? (
                            <VisibilityOffIcon fontSize="small" />
                          ) : (
                            <VisibilityIcon fontSize="small" />
                          )}
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete Link">
                        <IconButton
                          size="small"
                          onClick={() => handleDeleteLink(link)}
                          color="error"
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Edit Link Dialog */}
      <Dialog
        open={linkDialogOpen}
        onClose={() => setLinkDialogOpen(false)}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 2,
            boxShadow: '0 8px 32px rgba(0,0,0,0.12)',
          },
        }}
      >
        <DialogTitle>
          <Typography variant="h6" fontWeight={600}>
            Edit Dashboard Link
          </Typography>
        </DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} mt={1}>
            <TextField
              label="Name (optional)"
              value={linkFormData.name}
              onChange={(e) => setLinkFormData({ ...linkFormData, name: e.target.value })}
              fullWidth
              helperText="Friendly name for this link"
            />
            <TextField
              label="Description (optional)"
              value={linkFormData.description}
              onChange={(e) => setLinkFormData({ ...linkFormData, description: e.target.value })}
              fullWidth
              multiline
              rows={2}
              helperText="Optional description for this link"
            />
            <Box display="flex" gap={2}>
              <TextField
                label="Start Date"
                type="date"
                value={linkFormData.start_date}
                onChange={(e) => setLinkFormData({ ...linkFormData, start_date: e.target.value })}
                fullWidth
                required
                InputLabelProps={{ shrink: true }}
              />
              <TextField
                label="End Date"
                type="date"
                value={linkFormData.end_date}
                onChange={(e) => setLinkFormData({ ...linkFormData, end_date: e.target.value })}
                fullWidth
                required
                InputLabelProps={{ shrink: true }}
              />
            </Box>
            <TextField
              label="Slug (optional)"
              value={linkFormData.slug}
              onChange={(e) => setLinkFormData({ ...linkFormData, slug: e.target.value })}
              fullWidth
              helperText="Leave empty to auto-generate. Must be unique."
            />
            <TextField
              label="Expires At (optional)"
              type="datetime-local"
              value={linkFormData.expires_at}
              onChange={(e) => setLinkFormData({ ...linkFormData, expires_at: e.target.value })}
              fullWidth
              InputLabelProps={{ shrink: true }}
              helperText="Optional expiration date and time"
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={linkFormData.enabled}
                  onChange={(e) => setLinkFormData({ ...linkFormData, enabled: e.target.checked })}
                />
              }
              label="Enabled"
            />
            <Alert severity="info">
              <Typography variant="body2">
                Note: KPI selections can be updated from the Reporting Dashboard when viewing this link.
              </Typography>
            </Alert>
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button
            onClick={() => {
              setLinkDialogOpen(false);
              setEditingLink(null);
            }}
            sx={{ textTransform: 'none' }}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSaveLink}
            variant="contained"
            disabled={saving || !linkFormData.start_date || !linkFormData.end_date}
            sx={{ textTransform: 'none' }}
          >
            {saving ? 'Saving...' : 'Update'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Tracking Metrics Dialog */}
      <Dialog
        open={trackingDialogOpen}
        onClose={() => setTrackingDialogOpen(false)}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 2,
            boxShadow: '0 8px 32px rgba(0,0,0,0.12)',
          },
        }}
      >
        <DialogTitle>
          <Typography variant="h6" fontWeight={600}>
            Tracking Metrics - {trackingLink?.name || trackingLink?.slug || 'Dashboard Link'}
          </Typography>
          {trackingLink && (
            <Typography variant="caption" color="text.secondary">
              Client: {trackingLink.client_name || 'N/A'} | Slug: {trackingLink.slug}
            </Typography>
          )}
        </DialogTitle>
        <DialogContent>
          {loadingMetrics ? (
            <Box display="flex" justifyContent="center" py={4}>
              <CircularProgress />
            </Box>
          ) : trackingMetrics ? (
            <Box display="flex" flexDirection="column" gap={3} mt={1}>
              {/* Summary Cards */}
              <Box display="flex" gap={2}>
                <Paper
                  elevation={0}
                  sx={{
                    p: 2,
                    flex: 1,
                    bgcolor: alpha(theme.palette.primary.main, 0.08),
                    borderRadius: 2,
                  }}
                >
                  <Typography variant="h4" fontWeight={700} color="primary">
                    {trackingMetrics.total_opens || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Opens
                  </Typography>
                </Paper>
                <Paper
                  elevation={0}
                  sx={{
                    p: 2,
                    flex: 1,
                    bgcolor: alpha(theme.palette.success.main, 0.08),
                    borderRadius: 2,
                  }}
                >
                  <Typography variant="h4" fontWeight={700} color="success.main">
                    {trackingMetrics.recent_opens?.length || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Recent Opens (Last 50)
                  </Typography>
                </Paper>
              </Box>

              {/* Opens Over Time */}
              {trackingMetrics.opens_over_time && trackingMetrics.opens_over_time.length > 0 && (
                <Box>
                  <Typography variant="h6" fontWeight={600} gutterBottom>
                    Opens Over Time
                  </Typography>
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableHead>
                        <TableRow sx={{ bgcolor: alpha(theme.palette.primary.main, 0.04) }}>
                          <TableCell sx={{ fontWeight: 700 }}>Date</TableCell>
                          <TableCell sx={{ fontWeight: 700 }} align="right">Opens</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {trackingMetrics.opens_over_time.map((item, index) => (
                          <TableRow key={index} hover>
                            <TableCell>{formatDate(item.date)}</TableCell>
                            <TableCell align="right">{item.opens}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Box>
              )}

              {/* Recent Opens */}
              {trackingMetrics.recent_opens && trackingMetrics.recent_opens.length > 0 && (
                <Box>
                  <Typography variant="h6" fontWeight={600} gutterBottom>
                    Recent Opens
                  </Typography>
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableHead>
                        <TableRow sx={{ bgcolor: alpha(theme.palette.primary.main, 0.04) }}>
                          <TableCell sx={{ fontWeight: 700 }}>Opened At</TableCell>
                          <TableCell sx={{ fontWeight: 700 }}>IP Address</TableCell>
                          <TableCell sx={{ fontWeight: 700 }}>User Agent</TableCell>
                          <TableCell sx={{ fontWeight: 700 }}>Referer</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {trackingMetrics.recent_opens.map((open, index) => (
                          <TableRow key={index} hover>
                            <TableCell>
                              <Typography variant="body2">
                                {formatDateTime(open.opened_at)}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                                {open.ip_address || 'N/A'}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Tooltip title={open.user_agent || 'N/A'}>
                                <Typography
                                  variant="body2"
                                  sx={{
                                    maxWidth: 200,
                                    overflow: 'hidden',
                                    textOverflow: 'ellipsis',
                                    whiteSpace: 'nowrap',
                                  }}
                                >
                                  {open.user_agent || 'N/A'}
                                </Typography>
                              </Tooltip>
                            </TableCell>
                            <TableCell>
                              <Tooltip title={open.referer || 'N/A'}>
                                <Typography
                                  variant="body2"
                                  sx={{
                                    maxWidth: 200,
                                    overflow: 'hidden',
                                    textOverflow: 'ellipsis',
                                    whiteSpace: 'nowrap',
                                  }}
                                >
                                  {open.referer || 'N/A'}
                                </Typography>
                              </Tooltip>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Box>
              )}

              {(!trackingMetrics.recent_opens || trackingMetrics.recent_opens.length === 0) && 
               (!trackingMetrics.opens_over_time || trackingMetrics.opens_over_time.length === 0) && (
                <Alert severity="info">
                  No tracking data available for this dashboard link yet.
                </Alert>
              )}
            </Box>
          ) : (
            <Alert severity="error">
              Failed to load tracking metrics.
            </Alert>
          )}
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button
            onClick={() => setTrackingDialogOpen(false)}
            sx={{ textTransform: 'none' }}
          >
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default DashboardLinksManagement;


import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  Typography,
  alpha,
  useTheme,
} from '@mui/material'
import { Link as LinkIcon, Check as CheckIcon, ContentCopy as ContentCopyIcon } from '@mui/icons-material'

export default function ShareDialog({
  open,
  onClose,
  shareableUrl,
  copied,
  onCopyUrl,
}) {
  const theme = useTheme()

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 2,
          border: `1px solid ${theme.palette.divider}`,
        },
      }}
    >
      <DialogTitle sx={{ fontWeight: 600, pb: 1 }}>
        Share Public Dashboard
      </DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" mb={2}>
          Share this URL with clients to give them access to the public reporting dashboard for this brand.
        </Typography>
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            p: 1.5,
            borderRadius: 2,
            bgcolor: alpha(theme.palette.primary.main, 0.05),
            border: `1px solid ${theme.palette.divider}`,
          }}
        >
          <LinkIcon sx={{ color: 'text.secondary', fontSize: 20 }} />
          <Typography
            variant="body2"
            sx={{
              flex: 1,
              fontFamily: 'monospace',
              fontSize: '0.875rem',
              wordBreak: 'break-all',
              color: 'text.primary',
            }}
          >
            {shareableUrl}
          </Typography>
          <IconButton
            onClick={onCopyUrl}
            size="small"
            sx={{
              color: copied ? theme.palette.success.main : 'text.secondary',
              '&:hover': {
                bgcolor: alpha(theme.palette.primary.main, 0.1),
              },
            }}
            title={copied ? 'Copied!' : 'Copy URL'}
          >
            {copied ? <CheckIcon fontSize="small" /> : <ContentCopyIcon fontSize="small" />}
          </IconButton>
        </Box>
        {copied && (
          <Typography
            variant="caption"
            color="success.main"
            sx={{ mt: 1, display: 'block', fontWeight: 600 }}
          >
            URL copied to clipboard!
          </Typography>
        )}
      </DialogContent>
      <DialogActions sx={{ p: 2, pt: 1 }}>
        <Button
          onClick={onClose}
          variant="outlined"
          sx={{ borderRadius: 2, textTransform: 'none' }}
        >
          Close
        </Button>
      </DialogActions>
    </Dialog>
  )
}


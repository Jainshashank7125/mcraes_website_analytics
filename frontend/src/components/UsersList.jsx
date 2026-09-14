import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  CircularProgress,
  Button,
  alpha,
  useTheme,
  Skeleton,
  IconButton,
  Tooltip,
  TextField,
  InputAdornment,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Avatar,
  TablePagination,
  Alert,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
} from '@mui/material'
import {
  Search as SearchIcon,
  PersonAdd as PersonAddIcon,
  Edit as EditIcon,
  LockReset as LockResetIcon,
  Block as BlockIcon,
  CheckCircle as CheckCircleIcon,
  ManageAccounts as ManageAccountsIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material'
import { useQuery, useQueryClient, keepPreviousData } from '@tanstack/react-query'
import { userAPI } from '../services/api'
import { queryKeys } from '../hooks/queryKeys'
import { useAuth } from '../contexts/AuthContext'
import { useToast } from '../contexts/ToastContext'
import { getErrorMessage } from '../utils/errorHandler'
import UserManagement from './UserManagement'
import ResetPasswordDialog from './ResetPasswordDialog'

function UsersList() {
  const theme = useTheme()
  const queryClient = useQueryClient()
  const { user: currentUser } = useAuth()
  const { showError, showSuccess } = useToast()

  const [page, setPage] = useState(0)
  const [pageSize, setPageSize] = useState(25)
  const [searchTerm, setSearchTerm] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [activeFilter, setActiveFilter] = useState('active') // 'active' | 'inactive' | 'all'
  const [persistedTotalCount, setPersistedTotalCount] = useState(0)

  const [managementOpen, setManagementOpen] = useState(false)
  const [selectedUser, setSelectedUser] = useState(null)
  const [resetPasswordOpen, setResetPasswordOpen] = useState(false)
  const [userForPasswordReset, setUserForPasswordReset] = useState(null)
  const [statusDialogOpen, setStatusDialogOpen] = useState(false)
  const [userForStatusChange, setUserForStatusChange] = useState(null)
  const [statusChanging, setStatusChanging] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchTerm)
      setPage(0)
    }, 300)
    return () => clearTimeout(timer)
  }, [searchTerm])

  useEffect(() => {
    setPage(0)
  }, [activeFilter])

  const { data: usersData = {}, isLoading: loading, isFetching, error } = useQuery({
    queryKey: queryKeys.users.list({ page: page + 1, pageSize, search: debouncedSearch, activeFilter }),
    queryFn: async () => userAPI.getUsers(page + 1, pageSize, debouncedSearch, activeFilter),
    staleTime: 60 * 1000,
    gcTime: 5 * 60 * 1000,
    placeholderData: keepPreviousData,
  })

  useEffect(() => {
    if (usersData.total_count !== undefined && usersData.total_count !== null) {
      setPersistedTotalCount(usersData.total_count)
    }
  }, [usersData.total_count])

  const users = usersData.items || []
  const totalCount = usersData.total_count !== undefined && usersData.total_count !== null
    ? usersData.total_count
    : persistedTotalCount

  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.users.all })
  }

  const handleChangePage = (event, newPage) => {
    setPage(newPage)
  }

  const handleChangePageSize = (event) => {
    setPageSize(parseInt(event.target.value, 10))
    setPage(0)
  }

  const handleCreateClick = () => {
    setSelectedUser(null)
    setManagementOpen(true)
  }

  const handleEditClick = (targetUser) => {
    setSelectedUser(targetUser)
    setManagementOpen(true)
  }

  const handleManagementClose = (didSave) => {
    setManagementOpen(false)
    setSelectedUser(null)
    if (didSave) {
      queryClient.invalidateQueries({ queryKey: queryKeys.users.all })
    }
  }

  const handleResetPasswordClick = (targetUser) => {
    setUserForPasswordReset(targetUser)
    setResetPasswordOpen(true)
  }

  const handleResetPasswordClose = (didSave) => {
    setResetPasswordOpen(false)
    setUserForPasswordReset(null)
    if (didSave) {
      queryClient.invalidateQueries({ queryKey: queryKeys.users.all })
    }
  }

  const handleStatusToggleClick = (targetUser) => {
    setUserForStatusChange(targetUser)
    setStatusDialogOpen(true)
  }

  const handleStatusCancel = () => {
    setStatusDialogOpen(false)
    setUserForStatusChange(null)
  }

  const handleStatusConfirm = async () => {
    if (!userForStatusChange) return
    const nextActive = !userForStatusChange.is_active

    setStatusChanging(true)
    try {
      await userAPI.setUserActive(userForStatusChange.id, nextActive)
      showSuccess(nextActive ? 'User reactivated.' : 'User deactivated.')
      queryClient.invalidateQueries({ queryKey: queryKeys.users.all })
      setStatusDialogOpen(false)
      setUserForStatusChange(null)
    } catch (err) {
      showError(getErrorMessage(err))
    } finally {
      setStatusChanging(false)
    }
  }

  if (loading && page === 0) {
    return (
      <Box>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Skeleton variant="rectangular" width={200} height={40} sx={{ borderRadius: 1.5 }} />
          <Skeleton variant="rectangular" width={140} height={36} sx={{ borderRadius: 1.5 }} />
        </Box>
        <Skeleton variant="rectangular" height={400} sx={{ borderRadius: 2 }} />
      </Box>
    )
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Box>
          <Typography
            variant="h4"
            fontWeight={700}
            mb={1}
            sx={{ fontSize: '1.75rem', letterSpacing: '-0.02em', color: 'text.primary' }}
          >
            Users
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ fontSize: '0.875rem' }}>
            {users.length} of {totalCount} {totalCount === 1 ? 'user' : 'users'}
            {debouncedSearch ? ` matching "${debouncedSearch}"` : ''}
          </Typography>
        </Box>
        <Box display="flex" gap={1.5}>
          <Button
            variant="outlined"
            size="small"
            startIcon={<RefreshIcon sx={{ fontSize: 16 }} />}
            onClick={handleRefresh}
            sx={{
              borderRadius: 2,
              px: 2,
              py: 0.75,
              fontWeight: 600,
              fontSize: '0.875rem',
              bgcolor: 'background.paper',
              borderColor: theme.palette.divider,
              '&:hover': {
                borderColor: theme.palette.divider,
                bgcolor: alpha(theme.palette.primary.main, 0.05),
              },
            }}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            size="small"
            startIcon={<PersonAddIcon sx={{ fontSize: 16 }} />}
            onClick={handleCreateClick}
            sx={{
              borderRadius: 2,
              px: 2,
              py: 0.75,
              fontWeight: 600,
              fontSize: '0.875rem',
              boxShadow: 'none',
              '&:hover': { boxShadow: '0 2px 8px rgba(0,0,0,0.1)' },
            }}
          >
            New User
          </Button>
        </Box>
      </Box>

      {/* Search Bar */}
      <Box mb={3}>
        <TextField
          fullWidth
          placeholder="Search by name or email..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon sx={{ color: 'text.secondary', fontSize: 20 }} />
              </InputAdornment>
            ),
          }}
          sx={{
            '& .MuiOutlinedInput-root': {
              borderRadius: 2,
              bgcolor: 'background.paper',
            },
          }}
        />
      </Box>

      {/* Filters */}
      <Box mb={3} display="flex" gap={1.5} flexWrap="wrap" alignItems="center">
        <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.875rem', fontWeight: 600, mr: 1 }}>
          Filters:
        </Typography>

        <Chip
          label="Active"
          onClick={() => setActiveFilter('active')}
          color={activeFilter === 'active' ? 'success' : 'default'}
          variant={activeFilter === 'active' ? 'filled' : 'outlined'}
          sx={{ cursor: 'pointer', fontWeight: 500 }}
        />
        <Chip
          label="Inactive"
          onClick={() => setActiveFilter('inactive')}
          color={activeFilter === 'inactive' ? 'error' : 'default'}
          variant={activeFilter === 'inactive' ? 'filled' : 'outlined'}
          sx={{ cursor: 'pointer', fontWeight: 500 }}
        />
        <Chip
          label="All"
          onClick={() => setActiveFilter('all')}
          color={activeFilter === 'all' ? 'primary' : 'default'}
          variant={activeFilter === 'all' ? 'filled' : 'outlined'}
          sx={{ cursor: 'pointer', fontWeight: 500 }}
        />
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          Failed to load users. Please try again.
        </Alert>
      )}

      {!loading && users.length === 0 && (
        <Paper
          sx={{
            borderRadius: 2,
            border: `1px solid ${theme.palette.divider}`,
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
            p: 4,
            textAlign: 'center',
          }}
        >
          <ManageAccountsIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2, opacity: 0.4 }} />
          <Typography variant="h6" fontWeight={600} mb={1} sx={{ fontSize: '1.125rem' }}>
            {debouncedSearch ? 'No users found' : 'No users available'}
          </Typography>
          <Typography variant="body2" color="text.secondary" mb={3} sx={{ fontSize: '0.875rem' }}>
            {debouncedSearch
              ? `No users match "${debouncedSearch}". Try a different search term.`
              : 'Create the first user to get started.'}
          </Typography>
          {!debouncedSearch && (
            <Button
              variant="contained"
              size="small"
              onClick={handleCreateClick}
              sx={{ px: 2, py: 0.75, borderRadius: 1.5, fontSize: '0.875rem', fontWeight: 600, boxShadow: 'none' }}
            >
              New User
            </Button>
          )}
        </Paper>
      )}

      {(users.length > 0 || loading || isFetching) && (
        <TableContainer
          component={Paper}
          sx={{
            borderRadius: 2,
            border: `1px solid ${theme.palette.divider}`,
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
            overflow: 'hidden',
            position: 'relative',
          }}
        >
          {isFetching && (
            <LinearProgress sx={{ position: 'absolute', top: 0, left: 0, right: 0, zIndex: 10, height: 3 }} />
          )}
          <Table sx={{ position: 'relative', zIndex: 1 }}>
            <TableHead>
              <TableRow sx={{ bgcolor: alpha(theme.palette.primary.main, 0.02) }}>
                <TableCell sx={{ fontWeight: 600, fontSize: '0.875rem' }}>Name</TableCell>
                <TableCell sx={{ fontWeight: 600, fontSize: '0.875rem' }}>Email</TableCell>
                <TableCell sx={{ fontWeight: 600, fontSize: '0.875rem' }}>Role</TableCell>
                <TableCell sx={{ fontWeight: 600, fontSize: '0.875rem' }}>Status</TableCell>
                <TableCell sx={{ fontWeight: 600, fontSize: '0.875rem' }}>Created</TableCell>
                <TableCell align="right" sx={{ fontWeight: 600, fontSize: '0.875rem' }}>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading && page === 0 && users.length === 0 ? (
                Array.from({ length: pageSize }).map((_, index) => (
                  <TableRow key={index}>
                    <TableCell><Skeleton variant="text" width={150} /></TableCell>
                    <TableCell><Skeleton variant="text" width={200} /></TableCell>
                    <TableCell><Skeleton variant="text" width={80} /></TableCell>
                    <TableCell><Skeleton variant="text" width={80} /></TableCell>
                    <TableCell><Skeleton variant="text" width={100} /></TableCell>
                    <TableCell align="right"><Skeleton variant="circular" width={32} height={32} /></TableCell>
                  </TableRow>
                ))
              ) : (
                users.map((targetUser) => {
                  const isSelf = targetUser.id === currentUser?.id
                  return (
                    <TableRow
                      key={targetUser.id}
                      hover
                      sx={{ '&:hover': { bgcolor: alpha(theme.palette.primary.main, 0.02) } }}
                    >
                      <TableCell>
                        <Box display="flex" alignItems="center" gap={1.5}>
                          <Avatar
                            sx={{
                              bgcolor: alpha(theme.palette.primary.main, 0.1),
                              color: theme.palette.primary.main,
                              width: 32,
                              height: 32,
                              fontSize: '14px',
                              fontWeight: 600,
                            }}
                          >
                            {(targetUser.full_name || targetUser.email)?.charAt(0)?.toUpperCase()}
                          </Avatar>
                          <Typography variant="body2" fontWeight={600}>
                            {targetUser.full_name || '—'}
                            {isSelf && (
                              <Typography component="span" variant="caption" color="text.secondary" sx={{ ml: 0.75 }}>
                                (you)
                              </Typography>
                            )}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.875rem' }}>
                          {targetUser.email}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={targetUser.role === 'admin' ? 'Admin' : 'User'}
                          size="small"
                          color={targetUser.role === 'admin' ? 'primary' : 'default'}
                          sx={{ height: 24, fontSize: '0.75rem', fontWeight: 600 }}
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={targetUser.is_active ? 'Active' : 'Inactive'}
                          size="small"
                          color={targetUser.is_active ? 'success' : 'error'}
                          variant="outlined"
                          sx={{ height: 24, fontSize: '0.75rem', fontWeight: 600 }}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.8125rem' }}>
                          {targetUser.created_at ? new Date(targetUser.created_at).toLocaleDateString() : '—'}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Box display="flex" gap={0.5} justifyContent="flex-end">
                          <Tooltip title="Edit User" arrow>
                            <IconButton
                              size="small"
                              onClick={() => handleEditClick(targetUser)}
                              sx={{
                                color: theme.palette.primary.main,
                                '&:hover': { bgcolor: alpha(theme.palette.primary.main, 0.1) },
                              }}
                            >
                              <EditIcon sx={{ fontSize: 18 }} />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Reset Password" arrow>
                            <IconButton
                              size="small"
                              onClick={() => handleResetPasswordClick(targetUser)}
                              sx={{
                                color: theme.palette.warning.main,
                                '&:hover': { bgcolor: alpha(theme.palette.warning.main, 0.1) },
                              }}
                            >
                              <LockResetIcon sx={{ fontSize: 18 }} />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title={isSelf ? 'You cannot deactivate your own account' : (targetUser.is_active ? 'Deactivate User' : 'Reactivate User')} arrow>
                            <span>
                              <IconButton
                                size="small"
                                disabled={isSelf && targetUser.is_active}
                                onClick={() => handleStatusToggleClick(targetUser)}
                                sx={{
                                  color: targetUser.is_active ? theme.palette.error.main : theme.palette.success.main,
                                  '&:hover': {
                                    bgcolor: alpha(targetUser.is_active ? theme.palette.error.main : theme.palette.success.main, 0.1),
                                  },
                                }}
                              >
                                {targetUser.is_active ? <BlockIcon sx={{ fontSize: 18 }} /> : <CheckCircleIcon sx={{ fontSize: 18 }} />}
                              </IconButton>
                            </span>
                          </Tooltip>
                        </Box>
                      </TableCell>
                    </TableRow>
                  )
                })
              )}
            </TableBody>
          </Table>
          <TablePagination
            component="div"
            count={totalCount}
            page={page}
            onPageChange={handleChangePage}
            rowsPerPage={pageSize}
            onRowsPerPageChange={handleChangePageSize}
            rowsPerPageOptions={[10, 25, 50, 100]}
            disabled={isFetching}
            sx={{
              borderTop: `1px solid ${theme.palette.divider}`,
              opacity: isFetching ? 0.6 : 1,
              bgcolor: 'background.paper',
            }}
          />
        </TableContainer>
      )}

      <UserManagement
        open={managementOpen}
        onClose={handleManagementClose}
        user={selectedUser}
        currentUserId={currentUser?.id}
      />

      <ResetPasswordDialog
        open={resetPasswordOpen}
        onClose={handleResetPasswordClose}
        user={userForPasswordReset}
      />

      {/* Activate/Deactivate Confirmation Dialog */}
      <Dialog open={statusDialogOpen} onClose={handleStatusCancel}>
        <DialogTitle>
          {userForStatusChange?.is_active ? 'Deactivate User' : 'Reactivate User'}
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            {userForStatusChange?.is_active ? (
              <>
                Are you sure you want to deactivate <strong>{userForStatusChange?.email}</strong>?
                They will be immediately signed out and unable to log in until reactivated.
              </>
            ) : (
              <>
                Are you sure you want to reactivate <strong>{userForStatusChange?.email}</strong>?
                They will be able to log in again.
              </>
            )}
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleStatusCancel} disabled={statusChanging}>
            Cancel
          </Button>
          <Button
            onClick={handleStatusConfirm}
            color={userForStatusChange?.is_active ? 'error' : 'success'}
            variant="contained"
            disabled={statusChanging}
          >
            {statusChanging ? 'Saving...' : (userForStatusChange?.is_active ? 'Deactivate' : 'Reactivate')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default UsersList

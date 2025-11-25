import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { syncAPI } from '../services/api'
import { useAuth } from './AuthContext'

const SyncStatusContext = createContext()

export const useSyncStatus = () => {
  const context = useContext(SyncStatusContext)
  if (!context) {
    throw new Error('useSyncStatus must be used within SyncStatusProvider')
  }
  return context
}

export const SyncStatusProvider = ({ children }) => {
  const [activeJobs, setActiveJobs] = useState([])
  const [polling, setPolling] = useState(false)
  const { isAuthenticated } = useAuth()

  // Poll for active jobs status
  const pollActiveJobs = useCallback(async () => {
    // Only poll if user is authenticated
    if (!isAuthenticated) {
      setActiveJobs([])
      setPolling(false)
      return
    }

    try {
      const response = await syncAPI.getActiveSyncJobs()
      const jobs = response.items || []
      
      // Filter out completed and failed jobs
      const activeJobsOnly = jobs.filter(job => 
        job.status === 'pending' || job.status === 'running'
      )
      
      setActiveJobs(activeJobsOnly)
      
      // Continue polling only if there are truly active jobs
      if (activeJobsOnly.length > 0) {
        setPolling(true)
      } else {
        setPolling(false)
      }
    } catch (error) {
      // Silently fail if 403 (not authenticated) or other errors
      if (error.response?.status !== 403) {
        console.error('Error polling sync jobs:', error)
      }
      setPolling(false)
      setActiveJobs([])
    }
  }, [isAuthenticated])

  // Start polling when there are active jobs
  useEffect(() => {
    if (polling && isAuthenticated) {
      const interval = setInterval(pollActiveJobs, 2000) // Poll every 2 seconds
      return () => clearInterval(interval)
    }
  }, [polling, pollActiveJobs, isAuthenticated])

  // Initial poll and check for active jobs (only if authenticated)
  useEffect(() => {
    if (isAuthenticated) {
      pollActiveJobs()
    } else {
      setActiveJobs([])
      setPolling(false)
    }
  }, [pollActiveJobs, isAuthenticated])

  const addJob = useCallback((jobId, syncType) => {
    setActiveJobs(prev => {
      // Check if job already exists
      if (prev.find(j => j.job_id === jobId)) {
        return prev
      }
      return [...prev, {
        job_id: jobId,
        sync_type: syncType,
        status: 'pending',
        progress: 0,
        current_step: 'Starting...'
      }]
    })
    setPolling(true)
  }, [])

  const removeJob = useCallback((jobId) => {
    setActiveJobs(prev => prev.filter(j => j.job_id !== jobId))
  }, [])

  const refreshJobs = useCallback(() => {
    pollActiveJobs()
  }, [pollActiveJobs])

  return (
    <SyncStatusContext.Provider
      value={{
        activeJobs,
        addJob,
        removeJob,
        refreshJobs,
        hasActiveJobs: activeJobs.length > 0
      }}
    >
      {children}
    </SyncStatusContext.Provider>
  )
}


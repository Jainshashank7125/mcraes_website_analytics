import { useQuery } from '@tanstack/react-query'
import { syncAPI } from '../services/api'
import { queryKeys } from './queryKeys'

/**
 * Hook to fetch sync status
 */
export const useSyncStatus = (options = {}) => {
  return useQuery({
    queryKey: queryKeys.sync.status(),
    queryFn: async () => {
      return await syncAPI.getStatus()
    },
    staleTime: 30 * 1000, // 30 seconds - status changes frequently
    refetchInterval: 60 * 1000, // Refetch every minute
    ...options,
  })
}


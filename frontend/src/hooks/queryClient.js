import { QueryClient } from '@tanstack/react-query'

/**
 * Create and configure React Query client with default options
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Stale time: how long data is considered fresh
      staleTime: 2 * 60 * 1000, // 2 minutes default
      
      // Garbage collection time: how long unused data stays in cache
      gcTime: 5 * 60 * 1000, // 5 minutes (formerly cacheTime)
      
      // Retry failed requests
      retry: 1,
      
      // Refetch on window focus (can be disabled per query)
      refetchOnWindowFocus: true,
      
      // Refetch on reconnect
      refetchOnReconnect: true,
      
      // Don't refetch on mount if data is fresh
      refetchOnMount: true,
    },
    mutations: {
      // Retry failed mutations
      retry: 0,
    },
  },
})


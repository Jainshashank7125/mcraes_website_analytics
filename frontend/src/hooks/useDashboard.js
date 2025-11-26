import { useQuery, useQueryClient } from '@tanstack/react-query'
import { reportingAPI } from '../services/api'
import { queryKeys } from './queryKeys'

/**
 * Hook to fetch reporting dashboard data
 */
export const useReportingDashboard = (brandId, startDate, endDate, options = {}) => {
  return useQuery({
    queryKey: queryKeys.dashboard.detail(brandId, startDate, endDate),
    queryFn: async () => {
      return await reportingAPI.getReportingDashboard(
        brandId,
        startDate || undefined,
        endDate || undefined
      )
    },
    enabled: !!brandId && (options.enabled !== false),
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 5 * 60 * 1000, // 5 minutes
    ...options,
  })
}

/**
 * Hook to fetch reporting dashboard by slug (public access)
 */
export const useReportingDashboardBySlug = (slug, startDate, endDate, options = {}) => {
  return useQuery({
    queryKey: queryKeys.dashboard.bySlug(slug, startDate, endDate),
    queryFn: async () => {
      return await reportingAPI.getReportingDashboardBySlug(
        slug,
        startDate || undefined,
        endDate || undefined
      )
    },
    enabled: !!slug && (options.enabled !== false),
    staleTime: 2 * 60 * 1000,
    gcTime: 5 * 60 * 1000,
    ...options,
  })
}

/**
 * Hook to fetch Scrunch data
 */
export const useScrunchData = (brandId, options = {}) => {
  return useQuery({
    queryKey: queryKeys.dashboard.scrunch(brandId),
    queryFn: async () => {
      return await reportingAPI.getScrunchDashboard(brandId)
    },
    enabled: !!brandId && (options.enabled !== false),
    staleTime: 5 * 60 * 1000,
    ...options,
  })
}

/**
 * Hook to fetch KPI selections
 */
export const useKPISelections = (brandId, options = {}) => {
  return useQuery({
    queryKey: queryKeys.dashboard.kpiSelections(brandId),
    queryFn: async () => {
      return await reportingAPI.getKPISelections(brandId)
    },
    enabled: !!brandId && (options.enabled !== false),
    staleTime: 10 * 60 * 1000, // 10 minutes - KPI selections don't change often
    ...options,
  })
}

/**
 * Hook to invalidate dashboard cache
 */
export const useInvalidateDashboard = () => {
  const queryClient = useQueryClient()

  return {
    invalidate: (brandId, startDate, endDate) => {
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.dashboard.detail(brandId, startDate, endDate) 
      })
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.dashboard.scrunch(brandId) 
      })
    },
    invalidateBySlug: (slug, startDate, endDate) => {
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.dashboard.bySlug(slug, startDate, endDate) 
      })
    },
  }
}


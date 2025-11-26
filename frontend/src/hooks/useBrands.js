import { useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { syncAPI, dataAPI } from '../services/api'
import { queryKeys } from './queryKeys'
import { useToast } from '../contexts/ToastContext'
import { getErrorMessage } from '../utils/errorHandler'

/**
 * Hook to fetch all brands
 */
export const useBrands = () => {
  return useQuery({
    queryKey: queryKeys.brands.lists(),
    queryFn: async () => {
      const response = await syncAPI.getBrands()
      return response.items || response || []
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
  })
}

/**
 * Hook to fetch brand by ID
 */
export const useBrand = (brandId) => {
  return useQuery({
    queryKey: queryKeys.brands.detail(brandId),
    queryFn: async () => {
      const brands = await syncAPI.getBrands()
      const brandsList = brands.items || brands || []
      return brandsList.find(b => b.id === brandId) || null
    },
    enabled: !!brandId,
    staleTime: 5 * 60 * 1000,
  })
}

/**
 * Hook to fetch brand by slug
 */
export const useBrandBySlug = (slug) => {
  return useQuery({
    queryKey: queryKeys.brands.bySlug(slug),
    queryFn: async () => {
      const { reportingAPI } = await import('../services/api')
      return await reportingAPI.getBrandBySlug(slug)
    },
    enabled: !!slug,
    staleTime: 5 * 60 * 1000,
  })
}

/**
 * Hook to fetch brand analytics
 */
export const useBrandAnalytics = () => {
  return useQuery({
    queryKey: queryKeys.brands.analytics(),
    queryFn: async () => {
      try {
        return await syncAPI.getBrandAnalytics()
      } catch (error) {
        // Return null if analytics not available
        return null
      }
    },
    staleTime: 5 * 60 * 1000,
  })
}

/**
 * Hook to fetch brands with analytics merged
 */
export const useBrandsWithAnalytics = () => {
  const { data: brands = [], isLoading: brandsLoading } = useBrands()
  const { data: analytics, isLoading: analyticsLoading } = useBrandAnalytics()

  const brandsWithAnalytics = useMemo(() => {
    if (!analytics?.brands || !Array.isArray(analytics.brands)) {
      return brands.map(brand => ({ ...brand, analytics: null }))
    }

    const analyticsMap = new Map()
    analytics.brands.forEach(brandWithAnalytics => {
      analyticsMap.set(brandWithAnalytics.id, brandWithAnalytics.analytics)
    })

    return brands.map(brand => ({
      ...brand,
      analytics: analyticsMap.get(brand.id) || null
    }))
  }, [brands, analytics])

  return {
    data: brandsWithAnalytics,
    isLoading: brandsLoading || analyticsLoading,
  }
}

/**
 * Hook to update brand GA4 property ID
 */
export const useUpdateBrandGA4PropertyId = () => {
  const queryClient = useQueryClient()
  const { showSuccess, showError } = useToast()

  return useMutation({
    mutationFn: async ({ brandId, ga4PropertyId }) => {
      return await dataAPI.updateBrandGA4PropertyId(brandId, ga4PropertyId || null)
    },
    onSuccess: (data, variables) => {
      // Invalidate brand queries
      queryClient.invalidateQueries({ queryKey: queryKeys.brands.detail(variables.brandId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.brands.lists() })
      showSuccess('GA4 Property ID updated successfully')
    },
    onError: (error) => {
      showError(getErrorMessage(error))
    },
  })
}

/**
 * Hook to upload brand logo
 */
export const useUploadBrandLogo = () => {
  const queryClient = useQueryClient()
  const { showSuccess, showError } = useToast()

  return useMutation({
    mutationFn: async ({ brandId, file }) => {
      return await dataAPI.uploadBrandLogo(brandId, file)
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.brands.detail(variables.brandId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.brands.lists() })
      showSuccess('Logo uploaded successfully')
    },
    onError: (error) => {
      showError(getErrorMessage(error))
    },
  })
}

/**
 * Hook to delete brand logo
 */
export const useDeleteBrandLogo = () => {
  const queryClient = useQueryClient()
  const { showSuccess, showError } = useToast()

  return useMutation({
    mutationFn: async (brandId) => {
      return await dataAPI.deleteBrandLogo(brandId)
    },
    onSuccess: (data, brandId) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.brands.detail(brandId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.brands.lists() })
      showSuccess('Logo deleted successfully')
    },
    onError: (error) => {
      showError(getErrorMessage(error))
    },
  })
}

/**
 * Hook to update brand theme
 */
export const useUpdateBrandTheme = () => {
  const queryClient = useQueryClient()
  const { showSuccess, showError } = useToast()

  return useMutation({
    mutationFn: async ({ brandId, theme }) => {
      return await dataAPI.updateBrandTheme(brandId, theme)
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.brands.detail(variables.brandId) })
      // Invalidate all brand queries
      queryClient.invalidateQueries({ queryKey: queryKeys.brands.all })
      queryClient.invalidateQueries({ queryKey: queryKeys.brands.lists() })
      showSuccess('Theme updated successfully')
    },
    onError: (error) => {
      showError(getErrorMessage(error))
    },
  })
}


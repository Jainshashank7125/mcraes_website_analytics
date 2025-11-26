import { useQuery } from '@tanstack/react-query'
import { syncAPI } from '../services/api'
import { queryKeys } from './queryKeys'

/**
 * Hook to fetch prompts with filters
 */
export const usePrompts = (filters = {}, options = {}) => {
  const { page = 1, pageSize = 50, ...otherFilters } = filters
  const offset = (page - 1) * pageSize

  return useQuery({
    queryKey: queryKeys.data.prompts({ ...otherFilters, page, pageSize }),
    queryFn: async () => {
      const result = await syncAPI.getPrompts({
        stage: otherFilters.stage || undefined,
        persona_id: otherFilters.persona_id || undefined,
        limit: pageSize,
        offset: offset,
      })
      return {
        items: Array.isArray(result) ? result : result.items || [],
        totalCount: result.total_count !== undefined ? result.total_count : (Array.isArray(result) ? result.length : result.items?.length || 0),
      }
    },
    staleTime: 2 * 60 * 1000,
    ...options,
  })
}

/**
 * Hook to fetch responses with filters
 */
export const useResponses = (filters = {}, options = {}) => {
  const { page = 1, pageSize = 50, ...otherFilters } = filters
  const offset = (page - 1) * pageSize

  return useQuery({
    queryKey: queryKeys.data.responses({ ...otherFilters, page, pageSize }),
    queryFn: async () => {
      const result = await syncAPI.getResponses({
        platform: otherFilters.platform || undefined,
        prompt_id: otherFilters.prompt_id || undefined,
        start_date: otherFilters.start_date || undefined,
        end_date: otherFilters.end_date || undefined,
        limit: pageSize,
        offset: offset,
      })
      return {
        items: Array.isArray(result) ? result : result.items || [],
        totalCount: result.total_count !== undefined ? result.total_count : (Array.isArray(result) ? result.length : result.items?.length || 0),
      }
    },
    staleTime: 2 * 60 * 1000,
    ...options,
  })
}


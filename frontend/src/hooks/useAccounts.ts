import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'

/** Fetch all accounts (read-only). */
export function useAccounts() {
  return useQuery({
    queryKey: ['accounts'],
    queryFn: async () => {
      const { data, error } = await api.GET('/accounts/')
      if (error) throw new Error('Failed to load accounts')
      return data
    },
  })
}

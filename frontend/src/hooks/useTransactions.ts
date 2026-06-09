import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'

/** Fetch transactions, optionally filtered by account. */
export function useTransactions(accountId?: string, limit = 100) {
  return useQuery({
    queryKey: ['transactions', accountId ?? null, limit],
    queryFn: async () => {
      const { data, error } = await api.GET('/transactions/', {
        params: { query: { account_id: accountId, limit } },
      })
      if (error) throw new Error('Failed to load transactions')
      return data
    },
  })
}

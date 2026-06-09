import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'

const TASKS_KEY = ['tasks']
const ACTIVE_STATUSES = new Set(['pending', 'running'])
const POLL_MS = 2000

/** List recent tasks. Polls every 2s while any task is pending/running. */
export function useTasks(limit = 20) {
  return useQuery({
    queryKey: [...TASKS_KEY, limit],
    queryFn: async () => {
      const { data, error } = await api.GET('/tasks/', { params: { query: { limit } } })
      if (error) throw new Error('Failed to load tasks')
      return data
    },
    refetchInterval: (query) => {
      const tasks = query.state.data?.tasks ?? []
      return tasks.some((t) => ACTIVE_STATUSES.has(t.status)) ? POLL_MS : false
    },
  })
}

/** Enqueue an accounts sync. */
export function useSyncAccounts() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      const { data, error } = await api.POST('/sync/accounts')
      if (error) throw new Error('Failed to enqueue accounts sync')
      return data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: TASKS_KEY }),
  })
}

/** Enqueue a transactions sync for the last `days` days. */
export function useSyncTransactions() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (days: number) => {
      const { data, error } = await api.POST('/sync/transactions', {
        body: { days },
      })
      if (error) throw new Error('Failed to enqueue transactions sync')
      return data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: TASKS_KEY }),
  })
}

import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'

/** Fetch the monthly budget report for `month` (format: YYYY-MM). */
export function useMonthlyReport(month: string) {
  return useQuery({
    queryKey: ['monthly-report', month],
    queryFn: async () => {
      const { data, error } = await api.GET('/reports/monthly', {
        params: { query: { month } },
      })
      if (error) throw new Error('Failed to load monthly report')
      return data
    },
  })
}

import { useQuery } from '@tanstack/react-query'
import { qk } from '@/lib/queryClient'
import { scoringService } from '@/services/scoringService'

export function useLeaderboard(period: 'all' | 'year' | 'month' | 'week') {
  return useQuery({
    queryKey: qk.leaderboard(period),
    queryFn: () => scoringService.leaderboard(period),
  })
}

export function useContribution() {
  return useQuery({ queryKey: qk.contribution, queryFn: scoringService.contribution })
}

export function useBadges() {
  return useQuery({ queryKey: qk.badges, queryFn: scoringService.badges })
}

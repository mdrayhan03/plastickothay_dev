import { api } from '@/lib/api'
import type { Contribution, EarnedBadge, Leaderboard } from '@/types'

export const scoringService = {
  async leaderboard(period: 'all' | 'year' | 'month' | 'week') {
    const { data } = await api.get<Leaderboard>('/leaderboard/', { params: { period } })
    return data
  },
  async contribution() {
    const { data } = await api.get<Contribution>('/me/contribution/')
    return data
  },
  async badges() {
    const { data } = await api.get<EarnedBadge[]>('/me/badges/')
    return data
  },
}

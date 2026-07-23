import { api } from '@/lib/api'
import type { SiteConfig } from '@/types'

export const configService = {
  async siteConfig() {
    const { data } = await api.get<SiteConfig>('/site-config/')
    return data
  },
}

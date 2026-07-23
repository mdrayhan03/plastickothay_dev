import { useQuery } from '@tanstack/react-query'
import { qk } from '@/lib/queryClient'
import { configService } from '@/services/configService'

/** Public site config, fetched on boot — site name, logo, map defaults, feature flags. */
export function useSiteConfig() {
  return useQuery({
    queryKey: qk.siteConfig,
    queryFn: configService.siteConfig,
    staleTime: 5 * 60_000,
  })
}

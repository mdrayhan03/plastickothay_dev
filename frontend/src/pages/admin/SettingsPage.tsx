import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Lock } from 'lucide-react'
import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { Btn } from '@/components/Btn'
import { FormField } from '@/components/FormField'
import { useAuth } from '@/context/auth-context'
import { useSiteConfig } from '@/hooks/useSiteConfig'
import { apiErrorMessage } from '@/lib/api'
import { qk } from '@/lib/queryClient'
import { cn } from '@/lib/utils'
import { adminService } from '@/services/adminService'

export function SettingsPage() {
  const { data: config } = useSiteConfig()
  const { user: me } = useAuth()
  const isAdmin = me?.role === 'admin'
  const qc = useQueryClient()
  const [form, setForm] = useState({
    week_start: 'monday',
    site_name: '',
    tagline: '',
    map_lat: '',
    map_lon: '',
    map_zoom: 12,
  })

  useEffect(() => {
    if (config)
      setForm({
        week_start: config.week_start,
        site_name: config.site_name,
        tagline: config.tagline,
        map_lat: config.map_center ? String(config.map_center.lat) : '',
        map_lon: config.map_center ? String(config.map_center.lon) : '',
        map_zoom: config.map_zoom,
      })
  }, [config])

  const save = useMutation({
    mutationFn: () =>
      adminService.updateSiteConfig({
        week_start: form.week_start,
        site_name: form.site_name,
        tagline: form.tagline,
        map_lat: form.map_lat ? Number(form.map_lat) : null,
        map_lon: form.map_lon ? Number(form.map_lon) : null,
        map_zoom: Number(form.map_zoom),
        flags: config?.flags ?? {},
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.siteConfig })
      toast.success('Settings saved')
    },
    onError: (e) => toast.error(apiErrorMessage(e)),
  })

  if (!isAdmin)
    return (
      <div className="max-w-xl space-y-6">
        <h1 className="font-display text-2xl font-extrabold">Site settings</h1>
        <div className="grid place-items-center rounded-2xl border border-line bg-surface p-14 text-center">
          <Lock className="mb-3 size-8 text-ink-3" />
          <div className="font-bold text-ink">Admins only</div>
          <p className="mt-1 max-w-sm text-sm text-ink-2">
            Site settings can be changed by admins. Staff can moderate reports and manage the
            community, but not edit site configuration.
          </p>
        </div>
      </div>
    )

  return (
    <div className="max-w-xl space-y-6">
      <h1 className="font-display text-2xl font-extrabold">Site settings</h1>

      <div className="space-y-4 rounded-2xl border border-line bg-surface p-5 shadow-sm">
        <FormField label="Site name" value={form.site_name} onChange={(e) => setForm({ ...form, site_name: e.target.value })} />
        <FormField label="Tagline" value={form.tagline} onChange={(e) => setForm({ ...form, tagline: e.target.value })} />

        <div>
          <label className="mb-2 block text-[12.5px] font-bold text-ink-2">Week starts on</label>
          <div className="flex gap-2">
            {['monday', 'sunday'].map((d) => (
              <button
                key={d}
                onClick={() => setForm({ ...form, week_start: d })}
                className={cn(
                  'flex-1 rounded-xl border py-2.5 text-sm font-bold capitalize',
                  form.week_start === d ? 'border-brand bg-brand-soft text-brand-deep' : 'border-line-2 bg-surface text-ink-2',
                )}
              >
                {d}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-3 gap-3">
          <FormField label="Map lat" value={form.map_lat} onChange={(e) => setForm({ ...form, map_lat: e.target.value })} />
          <FormField label="Map lon" value={form.map_lon} onChange={(e) => setForm({ ...form, map_lon: e.target.value })} />
          <FormField label="Zoom" type="number" value={form.map_zoom} onChange={(e) => setForm({ ...form, map_zoom: Number(e.target.value) })} />
        </div>

        <Btn onClick={() => save.mutate()} loading={save.isPending} className="mt-2">
          Save settings
        </Btn>
      </div>

      <p className="text-sm text-ink-3">
        Point, level and badge rules are edited in the{' '}
        <a href="/django-admin/" className="font-bold text-brand">
          Django admin
        </a>
        .
      </p>
    </div>
  )
}

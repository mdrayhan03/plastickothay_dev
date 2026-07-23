import { Award, Camera, CheckCircle2, MapPin } from 'lucide-react'
import { LogoMark } from '@/components/Logo'
import { TopBar } from '@/components/layout/TopBar'
import { useSiteConfig } from '@/hooks/useSiteConfig'

const STEPS = [
  { icon: Camera, title: 'Spot & snap', body: 'See plastic pollution? Photograph it and set the location.' },
  { icon: CheckCircle2, title: 'We review it', body: 'Our team verifies each report before it appears on the public map.' },
  { icon: MapPin, title: 'It hits the map', body: 'Approved reports build a live picture of where plastic collects.' },
  { icon: Award, title: 'You earn points', body: 'Approved reports and likes earn points, levels and badges.' },
]

export function AboutPage() {
  const { data: config } = useSiteConfig()
  const name = config?.site_name || 'PlasticKothay'
  const tagline = config?.tagline || 'Map plastic pollution. Clean up your city, together.'

  return (
    <>
      <TopBar title="About" />

      <div className="px-4.5 pb-8 pt-5">
        <div className="flex flex-col items-center text-center">
          <span className="grid size-16 place-items-center rounded-2xl bg-brand-soft text-brand">
            <LogoMark className="size-9" />
          </span>
          <h1 className="mt-3 font-display text-2xl font-extrabold">{name}</h1>
          <p className="font-bengali text-sm text-ink-2">প্লাস্টিক কোথায়?</p>
          <p className="mt-2 max-w-xs text-[13.5px] text-ink-2">{tagline}</p>
        </div>

        <section className="mt-7">
          <h2 className="mb-3 font-display text-lg font-bold">How it works</h2>
          <div className="space-y-3">
            {STEPS.map((s, i) => (
              <div key={i} className="flex gap-3.5 rounded-[18px] border border-line bg-surface p-4 shadow-sm">
                <span className="grid size-10 flex-none place-items-center rounded-[12px] bg-brand-soft text-brand-deep">
                  <s.icon className="size-5" />
                </span>
                <div>
                  <div className="font-bold">{s.title}</div>
                  <p className="mt-0.5 text-[13px] leading-snug text-ink-2">{s.body}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="mt-7 rounded-[18px] border border-line bg-surface p-5 shadow-sm">
          <h2 className="font-display text-base font-bold">Our mission</h2>
          <p className="mt-1.5 text-[13.5px] leading-relaxed text-ink-2">
            Dhaka generates more plastic waste than its systems can clear. {name} turns everyday
            people into the eyes of the city — a shared, verified map of where plastic pollution is
            worst, so communities and authorities can act where it matters most.
          </p>
        </section>

        <p className="mt-6 text-center text-xs text-ink-3">{name} · v1.0 · Made in Dhaka 🇧🇩</p>
      </div>
    </>
  )
}

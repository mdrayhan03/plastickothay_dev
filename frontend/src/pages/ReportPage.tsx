import { Camera, Loader2, MapPin, Send } from 'lucide-react'
import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { Btn } from '@/components/Btn'
import { FormField } from '@/components/FormField'
import { TopBar } from '@/components/layout/TopBar'
import { useAuth } from '@/context/auth-context'
import { useSubmitReport } from '@/hooks/usePosts'
import { apiErrorMessage } from '@/lib/api'
import { cn } from '@/lib/utils'
import { severityClass, severityLabel } from '@/lib/severity'
import type { Severity } from '@/types'

export function ReportPage() {
  const { status } = useAuth()
  const isAuthed = status === 'authed'
  const navigate = useNavigate()
  const submit = useSubmitReport()
  const fileRef = useRef<HTMLInputElement>(null)

  const [photo, setPhoto] = useState<string | null>(null)
  const [severity, setSeverity] = useState<Severity>(3)
  const [description, setDescription] = useState('')
  const [coords, setCoords] = useState<{ lat: number; lon: number } | null>(null)
  const [locating, setLocating] = useState(false)
  const [contact, setContact] = useState({ name: '', email: '', phone: '' })

  function pickPhoto(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = () => setPhoto(reader.result as string)
    reader.readAsDataURL(file)
  }

  function locate() {
    setLocating(true)
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setCoords({ lat: pos.coords.latitude, lon: pos.coords.longitude })
        setLocating(false)
      },
      () => {
        toast.error('Could not get your location. Enable location and try again.')
        setLocating(false)
      },
      { enableHighAccuracy: true, timeout: 10000 },
    )
  }

  async function onSubmit() {
    if (!photo) return toast.error('Add a photo of the pollution.')
    if (!coords) return toast.error('Set the location first.')
    if (!isAuthed && (!contact.name || !contact.email)) {
      return toast.error('Add your name and email so we can follow up.')
    }
    try {
      await submit.mutateAsync({
        severity,
        lat: coords.lat,
        lon: coords.lon,
        photo,
        description,
        ...(isAuthed ? {} : contact),
      })
      toast.success('Report submitted — thank you!')
      navigate('/')
    } catch (e) {
      toast.error(apiErrorMessage(e, 'Could not submit'))
    }
  }

  return (
    <>
      <TopBar title="Report plastic" />

      {/* capture */}
      <input ref={fileRef} type="file" accept="image/*" capture="environment" hidden onChange={pickPhoto} />
      <button
        type="button"
        onClick={() => fileRef.current?.click()}
        className="relative mx-4.5 mt-4 grid h-65 w-[calc(100%-2.25rem)] place-items-center overflow-hidden rounded-3xl bg-[linear-gradient(160deg,#12312a,#0a1512)] shadow-md"
      >
        {photo ? (
          <img src={photo} alt="captured" className="size-full object-cover" />
        ) : (
          <div className="text-center text-white/85">
            <Camera className="mx-auto mb-2.5 size-13 opacity-90" strokeWidth={1.6} />
            <span className="text-[13px] font-semibold">Tap to capture the pollution</span>
          </div>
        )}
      </button>

      {/* severity */}
      <div className="mx-4.5 mt-4">
        <label className="mb-2 block text-[12.5px] font-bold text-ink-2">How severe is it?</label>
        <div className="flex gap-2">
          {([1, 2, 3, 4, 5] as Severity[]).map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => setSeverity(s)}
              className={cn(
                'relative h-13 flex-1 rounded-[13px] border-[1.5px] text-[15px] font-extrabold transition-transform',
                severity === s
                  ? `${severityClass[s]} -translate-y-0.5 border-transparent text-white`
                  : 'border-line-2 bg-surface text-ink-2',
              )}
            >
              {s}
              <span className="absolute inset-x-0 -bottom-4.5 text-[9.5px] font-bold uppercase tracking-wide text-ink-3">
                {severityLabel[s]}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* location */}
      <div className="mx-4.5 mt-9">
        <label className="mb-2 block text-[12.5px] font-bold text-ink-2">Location</label>
        <button
          type="button"
          onClick={locate}
          className="flex w-full items-center gap-2.5 rounded-[14px] bg-brand-soft px-3.5 py-3 text-left text-brand-deep"
        >
          {locating ? <Loader2 className="size-5 animate-spin" /> : <MapPin className="size-5" />}
          <div className="flex-1">
            {coords ? (
              <>
                <b className="text-sm">Location set</b>
                <span className="block text-xs opacity-85 tnum">
                  {coords.lat.toFixed(4)}, {coords.lon.toFixed(4)}
                </span>
              </>
            ) : (
              <b className="text-sm">{locating ? 'Getting your location…' : 'Use my current location'}</b>
            )}
          </div>
        </button>
      </div>

      {/* description */}
      <div className="mx-4.5 mt-4">
        <label className="mb-2 block text-[12.5px] font-bold text-ink-2">Description</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="What did you see? (optional)"
          className="min-h-21 w-full resize-none rounded-[14px] border border-line-2 bg-surface p-3.5 text-[15px] shadow-sm outline-none focus:border-brand"
        />
      </div>

      {/* guest contact */}
      {!isAuthed && (
        <div className="mx-4.5 mt-4 flex flex-col gap-3">
          <label className="text-[12.5px] font-bold text-ink-2">Your contact details</label>
          <FormField label="Full name" value={contact.name} onChange={(e) => setContact({ ...contact, name: e.target.value })} />
          <FormField label="Email" type="email" value={contact.email} onChange={(e) => setContact({ ...contact, email: e.target.value })} />
          <FormField label="Phone" type="tel" value={contact.phone} onChange={(e) => setContact({ ...contact, phone: e.target.value })} />
          <p className="text-[11.5px] leading-relaxed text-ink-3">
            Only used to follow up on your report — never shown publicly.
          </p>
        </div>
      )}

      <div className="mx-4.5 mt-5">
        <Btn onClick={onSubmit} loading={submit.isPending}>
          <Send className="size-5" />
          Submit report
        </Btn>
        <p className="mt-3 text-center text-xs text-ink-2">
          {isAuthed
            ? 'Your report earns points once approved.'
            : 'Reporting as a guest — sign in to earn points.'}
        </p>
      </div>
    </>
  )
}

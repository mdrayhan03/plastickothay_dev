import { Camera, Crosshair, Loader2, Send } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { Btn } from '@/components/Btn'
import { CameraCapture } from '@/components/CameraCapture'
import { FormField } from '@/components/FormField'
import { LazyLocationPicker } from '@/components/map/LazyLocationPicker'
import { TopBar } from '@/components/layout/TopBar'
import { useAuth } from '@/context/auth-context'
import { useSubmitReport } from '@/hooks/usePosts'
import { useSiteConfig } from '@/hooks/useSiteConfig'
import { apiErrorMessage } from '@/lib/api'
import { cn } from '@/lib/utils'
import { severityClass, severityLabel } from '@/lib/severity'
import { geocodeService } from '@/services/geocodeService'
import type { Severity } from '@/types'

export function ReportPage() {
  const { status } = useAuth()
  const isAuthed = status === 'authed'
  const navigate = useNavigate()
  const submit = useSubmitReport()
  const { data: config } = useSiteConfig()

  const [photo, setPhoto] = useState<string | null>(null)
  const [cameraOpen, setCameraOpen] = useState(false)
  const [severity, setSeverity] = useState<Severity>(3)
  const [description, setDescription] = useState('')
  const [coords, setCoords] = useState<{ lat: number; lon: number } | null>(null)
  const [locating, setLocating] = useState(false)
  const [placeName, setPlaceName] = useState('')
  const [geocoding, setGeocoding] = useState(false)
  const [contact, setContact] = useState({ name: '', email: '', phone: '' })

  const mapCenter: [number, number] = config?.map_center
    ? [config.map_center.lat, config.map_center.lon]
    : [23.8103, 90.4125]

  async function applyLocation(lat: number, lon: number) {
    setCoords({ lat, lon })
    setGeocoding(true)
    const name = await geocodeService.reverse(lat, lon)
    if (name) setPlaceName(name)
    setGeocoding(false)
  }

  function locate() {
    setLocating(true)
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLocating(false)
        applyLocation(pos.coords.latitude, pos.coords.longitude)
      },
      (err) => {
        setLocating(false)
        const denied = err.code === err.PERMISSION_DENIED
        toast.error(
          denied
            ? 'Location is off. Turn on location access for this site, or drop a pin on the map.'
            : 'Couldn’t get your location. Drop a pin on the map instead.',
          { action: { label: 'Try again', onClick: locate } },
        )
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
        place_name: placeName.trim() || undefined,
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

      {cameraOpen && (
        <CameraCapture
          onCapture={(dataUrl) => {
            setPhoto(dataUrl)
            setCameraOpen(false)
          }}
          onClose={() => setCameraOpen(false)}
        />
      )}

      {/* capture */}
      <button
        type="button"
        onClick={() => setCameraOpen(true)}
        className="relative mx-4.5 mt-4 grid h-65 w-[calc(100%-2.25rem)] place-items-center overflow-hidden rounded-3xl bg-[linear-gradient(160deg,#12312a,#0a1512)] shadow-md"
      >
        {photo ? (
          <>
            <img src={photo} alt="captured" className="size-full object-cover" />
            <span className="absolute bottom-3 right-3 rounded-full bg-black/55 px-3 py-1.5 text-[12px] font-bold text-white">
              Retake
            </span>
          </>
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
        <div className="mb-2 flex items-center justify-between">
          <label className="text-[12.5px] font-bold text-ink-2">Location</label>
          <button
            type="button"
            onClick={locate}
            className="inline-flex items-center gap-1.5 rounded-full bg-brand-soft px-3 py-1.5 text-[12px] font-bold text-brand-deep"
          >
            {locating ? <Loader2 className="size-4 animate-spin" /> : <Crosshair className="size-4" />}
            Use my location
          </button>
        </div>

        <div className="h-52 overflow-hidden rounded-[16px] border border-line shadow-sm">
          <LazyLocationPicker center={mapCenter} value={coords} onChange={applyLocation} />
        </div>
        <p className="mt-1.5 text-[11.5px] text-ink-3">
          {coords ? 'Drag the pin or tap the map to adjust.' : 'Tap the map to drop a pin, or use your location.'}
        </p>

        {coords && (
          <div className="relative mt-2.5">
            <input
              value={placeName}
              onChange={(e) => setPlaceName(e.target.value)}
              placeholder={geocoding ? 'Finding place name…' : 'Place name (e.g. Hatirjheel, Dhaka)'}
              className="w-full rounded-[14px] border border-line-2 bg-surface px-3.5 py-3 pr-10 text-[15px] shadow-sm outline-none focus:border-brand"
            />
            {geocoding && (
              <Loader2 className="absolute right-3.5 top-1/2 size-4.5 -translate-y-1/2 animate-spin text-ink-3" />
            )}
          </div>
        )}
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

import { CameraOff, Image, RefreshCw, X } from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { toast } from 'sonner'
import { readImageAsDataUrl } from '@/lib/image'
import { cn } from '@/lib/utils'

const MAX_WIDTH = 1280 // downscale so the base64 payload stays reasonable

type Status = 'loading' | 'ready' | 'denied' | 'missing'

/** Full-screen live camera with gallery fallback and robust video binding. */
export function CameraCapture({
  onCapture,
  onClose,
}: {
  onCapture: (dataUrl: string) => void
  onClose: () => void
}) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [status, setStatus] = useState<Status>('loading')

  const stop = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop())
      streamRef.current = null
    }
  }, [])

  const start = useCallback(async () => {
    setStatus('loading')
    if (!navigator.mediaDevices?.getUserMedia) {
      setStatus('missing')
      return
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: 'environment' } },
        audio: false,
      })
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        videoRef.current.play().catch(() => {})
      }
      setStatus('ready')
    } catch (err) {
      const name = (err as DOMException)?.name
      if (name === 'NotFoundError' || name === 'OverconstrainedError') {
        setStatus('missing')
        toast.error('No camera found on this device.')
      } else {
        setStatus('denied')
        toast.error('Camera is blocked. Allow camera access to take a photo.')
      }
    }
  }, [])

  useEffect(() => {
    start()
    return stop
  }, [start, stop])

  useEffect(() => {
    if (status === 'ready' && videoRef.current && streamRef.current) {
      videoRef.current.srcObject = streamRef.current
      videoRef.current.play().catch(() => {})
    }
  }, [status])

  function close() {
    stop()
    onClose()
  }

  function shoot() {
    const video = videoRef.current
    if (!video || status !== 'ready') return
    const width = video.videoWidth || 640
    const height = video.videoHeight || 480
    const scale = Math.min(1, MAX_WIDTH / width)
    const canvas = document.createElement('canvas')
    canvas.width = Math.round(width * scale)
    canvas.height = Math.round(height * scale)
    canvas.getContext('2d')?.drawImage(video, 0, 0, canvas.width, canvas.height)
    stop()
    onCapture(canvas.toDataURL('image/jpeg', 0.82))
  }

  async function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    try {
      const dataUrl = await readImageAsDataUrl(file, MAX_WIDTH)
      stop()
      onCapture(dataUrl)
    } catch {
      toast.error('Could not load the selected photo.')
    }
  }

  return (
    <div className="fixed inset-0 z-[9999] flex flex-col bg-black">
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleFileSelect}
      />

      <div className="flex items-center justify-between p-4 text-white">
        <button
          onClick={close}
          aria-label="Close camera"
          className="grid size-10 place-items-center rounded-full bg-white/15"
        >
          <X className="size-5" />
        </button>
        <span className="text-sm font-semibold">Capture the pollution</span>
        <button
          onClick={() => fileInputRef.current?.click()}
          aria-label="Upload photo from gallery"
          className="grid size-10 place-items-center rounded-full bg-white/15 text-white"
          title="Choose photo from device"
        >
          <Image className="size-5" />
        </button>
      </div>

      <div className="relative flex-1 bg-black">
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          onLoadedMetadata={() => videoRef.current?.play().catch(() => {})}
          className={cn('size-full object-cover', status !== 'ready' && 'hidden')}
        />

        {status === 'loading' && (
          <div className="grid h-full place-items-center text-white/70">
            <RefreshCw className="size-7 animate-spin" />
          </div>
        )}

        {(status === 'denied' || status === 'missing') && (
          <div className="grid h-full place-items-center px-8 text-center text-white/90">
            <div>
              <CameraOff className="mx-auto mb-3 size-12 opacity-70" strokeWidth={1.4} />
              <p className="text-[15px] font-bold">
                {status === 'denied' ? 'Camera access is off' : 'No camera available'}
              </p>
              <p className="mx-auto mt-1.5 max-w-xs text-[13px] text-white/70">
                {status === 'denied'
                  ? 'Reports need a live photo. Enable camera access or choose a photo from your gallery.'
                  : 'No usable camera was detected on this device. You can select a photo from your device.'}
              </p>
              <div className="mt-4 flex flex-wrap items-center justify-center gap-3">
                {status === 'denied' && (
                  <button
                    onClick={start}
                    className="inline-flex items-center gap-2 rounded-full bg-white px-5 py-2.5 text-sm font-bold text-black"
                  >
                    <RefreshCw className="size-4" /> Enable camera
                  </button>
                )}
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="inline-flex items-center gap-2 rounded-full border border-white/30 bg-white/10 px-5 py-2.5 text-sm font-bold text-white backdrop-blur-sm"
                >
                  <Image className="size-4" /> Upload from gallery
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {status === 'ready' && (
        <div className="flex items-center justify-around p-6">
          <button
            onClick={() => fileInputRef.current?.click()}
            className="flex flex-col items-center gap-1 text-xs font-semibold text-white/80"
          >
            <div className="grid size-11 place-items-center rounded-full bg-white/20">
              <Image className="size-5" />
            </div>
            Gallery
          </button>
          <button
            onClick={shoot}
            aria-label="Take photo"
            className="size-18 rounded-full border-4 border-white/40 bg-white ring-2 ring-white active:scale-95"
          />
          <div className="w-11" />
        </div>
      )}
    </div>
  )
}

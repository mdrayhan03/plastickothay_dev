import { CameraOff, RefreshCw, X } from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { toast } from 'sonner'

const MAX_WIDTH = 1280 // downscale so the base64 payload stays reasonable

type Status = 'loading' | 'ready' | 'denied' | 'missing'

/** Full-screen live camera. No gallery/upload — reports must be shot in real time. */
export function CameraCapture({
  onCapture,
  onClose,
}: {
  onCapture: (dataUrl: string) => void
  onClose: () => void
}) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const [status, setStatus] = useState<Status>('loading')

  const stop = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop())
    streamRef.current = null
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
      if (videoRef.current) videoRef.current.srcObject = stream
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

  function close() {
    stop()
    onClose()
  }

  function shoot() {
    const video = videoRef.current
    if (!video || status !== 'ready') return
    const scale = Math.min(1, MAX_WIDTH / video.videoWidth)
    const canvas = document.createElement('canvas')
    canvas.width = video.videoWidth * scale
    canvas.height = video.videoHeight * scale
    canvas.getContext('2d')?.drawImage(video, 0, 0, canvas.width, canvas.height)
    stop()
    onCapture(canvas.toDataURL('image/jpeg', 0.82))
  }

  return (
    <div className="fixed inset-0 z-[999] flex flex-col bg-black">
      <div className="flex items-center justify-between p-4 text-white">
        <button onClick={close} aria-label="Close camera" className="grid size-10 place-items-center rounded-full bg-white/15">
          <X className="size-5" />
        </button>
        <span className="text-sm font-semibold">Capture the pollution</span>
        <span className="size-10" />
      </div>

      <div className="relative flex-1">
        {status === 'ready' && (
          <video ref={videoRef} autoPlay playsInline muted className="size-full object-cover" />
        )}

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
                  ? 'Reports need a live photo. Allow camera access for this site, then try again. If the prompt doesn’t appear, enable the camera in your browser’s site settings.'
                  : 'This device has no usable camera, so a report can’t be photographed here.'}
              </p>
              {status === 'denied' && (
                <button
                  onClick={start}
                  className="mt-4 inline-flex items-center gap-2 rounded-full bg-white px-5 py-2.5 text-sm font-bold text-black"
                >
                  <RefreshCw className="size-4" /> Enable camera
                </button>
              )}
            </div>
          </div>
        )}
      </div>

      {status === 'ready' && (
        <div className="flex items-center justify-center p-6">
          <button
            onClick={shoot}
            aria-label="Take photo"
            className="size-18 rounded-full border-4 border-white/40 bg-white ring-2 ring-white active:scale-95"
          />
        </div>
      )}
    </div>
  )
}

import { Camera, Images, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

const MAX_WIDTH = 1280 // downscale so the base64 payload stays reasonable

/** Full-screen camera using getUserMedia, with a gallery/file fallback when it's unavailable. */
export function CameraCapture({
  onCapture,
  onClose,
}: {
  onCapture: (dataUrl: string) => void
  onClose: () => void
}) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    let cancelled = false
    async function start() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: { ideal: 'environment' } },
          audio: false,
        })
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop())
          return
        }
        streamRef.current = stream
        if (videoRef.current) videoRef.current.srcObject = stream
      } catch {
        setError(true)
      }
    }
    start()
    return () => {
      cancelled = true
      streamRef.current?.getTracks().forEach((t) => t.stop())
    }
  }, [])

  function stop() {
    streamRef.current?.getTracks().forEach((t) => t.stop())
  }

  function shoot() {
    const video = videoRef.current
    if (!video) return
    const scale = Math.min(1, MAX_WIDTH / video.videoWidth)
    const canvas = document.createElement('canvas')
    canvas.width = video.videoWidth * scale
    canvas.height = video.videoHeight * scale
    canvas.getContext('2d')?.drawImage(video, 0, 0, canvas.width, canvas.height)
    stop()
    onCapture(canvas.toDataURL('image/jpeg', 0.82))
  }

  function pickFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = () => onCapture(reader.result as string)
    reader.readAsDataURL(file)
  }

  return (
    <div className="fixed inset-0 z-[999] flex flex-col bg-black">
      <input ref={fileRef} type="file" accept="image/*" hidden onChange={pickFile} />

      <div className="flex items-center justify-between p-4 text-white">
        <button onClick={() => { stop(); onClose() }} aria-label="Close camera" className="grid size-10 place-items-center rounded-full bg-white/15">
          <X className="size-5" />
        </button>
        <span className="text-sm font-semibold">Capture the pollution</span>
        <span className="size-10" />
      </div>

      <div className="relative flex-1">
        {error ? (
          <div className="grid h-full place-items-center px-8 text-center text-white/85">
            <div>
              <Camera className="mx-auto mb-3 size-12 opacity-70" strokeWidth={1.4} />
              <p className="text-sm">Camera unavailable or permission denied.</p>
              <button
                onClick={() => fileRef.current?.click()}
                className="mt-4 inline-flex items-center gap-2 rounded-full bg-white px-5 py-2.5 text-sm font-bold text-black"
              >
                <Images className="size-4" /> Choose from gallery
              </button>
            </div>
          </div>
        ) : (
          <video ref={videoRef} autoPlay playsInline muted className="size-full object-cover" />
        )}
      </div>

      {!error && (
        <div className="flex items-center justify-center gap-8 p-6">
          <button onClick={() => fileRef.current?.click()} aria-label="Choose from gallery" className="grid size-12 place-items-center rounded-full bg-white/15 text-white">
            <Images className="size-6" />
          </button>
          <button onClick={shoot} aria-label="Take photo" className="size-18 rounded-full border-4 border-white/40 bg-white ring-2 ring-white active:scale-95" />
          <span className="size-12" />
        </div>
      )}
    </div>
  )
}

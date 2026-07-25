import { Camera } from 'lucide-react'
import { useRef } from 'react'
import { toast } from 'sonner'
import { Avatar } from '@/components/Avatar'
import { readImageAsDataUrl } from '@/lib/image'

/** Circular avatar with a camera overlay — tap to pick and downscale a profile photo. */
export function AvatarPicker({
  name,
  value,
  onChange,
}: {
  name?: string
  value: string | null
  onChange: (dataUrl: string) => void
}) {
  const fileRef = useRef<HTMLInputElement>(null)

  async function pick(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file) return
    try {
      onChange(await readImageAsDataUrl(file, 256))
    } catch {
      toast.error('Could not use that image.')
    }
  }

  return (
    <div className="flex justify-center">
      <button
        type="button"
        onClick={() => fileRef.current?.click()}
        className="relative"
        aria-label="Choose profile photo"
      >
        <Avatar name={name} src={value} className="size-22 text-2xl ring-2 ring-line" />
        <span className="absolute bottom-0 right-0 grid size-7 place-items-center rounded-full border-2 border-surface bg-brand text-white">
          <Camera className="size-3.5" />
        </span>
      </button>
      <input ref={fileRef} type="file" accept="image/*" hidden onChange={pick} />
    </div>
  )
}

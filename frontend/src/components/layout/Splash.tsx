import { LogoMark } from '@/components/Logo'

/** Shown while the boot refresh resolves auth state. */
export function Splash() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-4">
      <div className="grid size-16 animate-pulse place-items-center rounded-[20px] bg-[linear-gradient(150deg,var(--brand-2),var(--brand-deep))]">
        <LogoMark className="size-8 text-white" />
      </div>
      <div className="font-display text-lg font-bold text-brand">PlasticKothay</div>
    </div>
  )
}

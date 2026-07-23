import { lazy, Suspense } from 'react'

const LocationPicker = lazy(() =>
  import('./LocationPicker').then((m) => ({ default: m.LocationPicker })),
)

interface Props {
  center: [number, number]
  value: { lat: number; lon: number } | null
  onChange: (lat: number, lon: number) => void
}

export function LazyLocationPicker(props: Props) {
  return (
    <Suspense fallback={<div className="size-full animate-pulse bg-surface-2" />}>
      <LocationPicker {...props} />
    </Suspense>
  )
}

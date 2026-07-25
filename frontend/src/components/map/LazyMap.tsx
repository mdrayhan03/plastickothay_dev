import { lazy, Suspense } from 'react'
import type { MapMarker } from '@/types'

// Leaflet is heavy - load it only when the map actually renders.
const ReportMap = lazy(() => import('./ReportMap').then((m) => ({ default: m.ReportMap })))

interface Props {
  center: [number, number]
  zoom: number
  markers: MapMarker[]
  onMarkerClick?: (id: number) => void
}

export function LazyMap(props: Props) {
  return (
    <Suspense fallback={<div className="size-full animate-pulse bg-surface-2" />}>
      <ReportMap {...props} />
    </Suspense>
  )
}

import 'leaflet/dist/leaflet.css'
import { Circle, Marker, MapContainer, TileLayer, Tooltip } from 'react-leaflet'
import { createComboMarkerIcon } from '@/lib/marker'
import type { MapMarker } from '@/types'

/** Group markers into a coarse grid and surface cells with many reports as hotspot circles.
 *  (Client-side until BE-3 gives an all-status admin marker endpoint.) */
function hotspots(markers: MapMarker[]) {
  const cell = 0.012 // ~1.3km
  const buckets = new Map<string, { lat: number; lon: number; n: number }>()
  for (const m of markers) {
    const key = `${Math.round(m.lat / cell)}:${Math.round(m.lon / cell)}`
    const b = buckets.get(key) ?? { lat: 0, lon: 0, n: 0 }
    b.lat += m.lat
    b.lon += m.lon
    b.n += 1
    buckets.set(key, b)
  }
  return [...buckets.values()]
    .filter((b) => b.n >= 3)
    .map((b) => ({ lat: b.lat / b.n, lon: b.lon / b.n, n: b.n }))
}

export function DensityMap({
  center,
  zoom,
  markers,
}: {
  center: [number, number]
  zoom: number
  markers: MapMarker[]
}) {
  const spots = hotspots(markers)
  return (
    <MapContainer center={center} zoom={zoom} attributionControl={false} className="h-full w-full">
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      {spots.map((s, i) => (
        <Circle
          key={i}
          center={[s.lat, s.lon]}
          radius={220 + s.n * 30}
          pathOptions={{ color: '#E5484D', weight: 1, fillColor: '#E5484D', fillOpacity: 0.12 }}
        >
          <Tooltip direction="top">{s.n} reports</Tooltip>
        </Circle>
      ))}
      {markers.map((m) => (
        <Marker
          key={m.id}
          position={[m.lat, m.lon]}
          icon={createComboMarkerIcon(m)}
        />
      ))}
    </MapContainer>
  )
}


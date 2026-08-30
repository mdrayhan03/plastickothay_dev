import 'leaflet/dist/leaflet.css'
import { Marker, MapContainer, TileLayer } from 'react-leaflet'
import { createComboMarkerIcon } from '@/lib/marker'
import type { MapMarker } from '@/types'

interface Props {
  center: [number, number]
  zoom: number
  markers: MapMarker[]
  onMarkerClick?: (id: number) => void
}

export function ReportMap({ center, zoom, markers, onMarkerClick }: Props) {
  return (
    <MapContainer
      center={center}
      zoom={zoom}
      zoomControl={false}
      attributionControl={false}
      className="size-full"
    >
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      {markers.map((m) => (
        <Marker
          key={m.id}
          position={[m.lat, m.lon]}
          icon={createComboMarkerIcon(m)}
          eventHandlers={{ click: () => onMarkerClick?.(m.id) }}
        />
      ))}
    </MapContainer>
  )
}


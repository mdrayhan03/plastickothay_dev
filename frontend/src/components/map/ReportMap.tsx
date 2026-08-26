import 'leaflet/dist/leaflet.css'
import { CircleMarker, MapContainer, TileLayer } from 'react-leaflet'
import { severityColor } from '@/lib/severity'
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
        <CircleMarker
          key={m.id}
          center={[m.lat, m.lon]}
          radius={8}
          pathOptions={{
            color: '#fff',
            weight: 2,
            fillColor: severityColor[m.severity],
            fillOpacity: 0.95,
          }}
          eventHandlers={{ click: () => onMarkerClick?.(m.id) }}
        />
      ))}
    </MapContainer>
  )
}

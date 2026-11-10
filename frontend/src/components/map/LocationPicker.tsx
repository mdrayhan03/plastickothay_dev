import 'leaflet/dist/leaflet.css'
import L from 'leaflet'
import { Marker, MapContainer, TileLayer, useMapEvents } from 'react-leaflet'

// HTML pin as a divIcon - avoids the bundler/marker-image issue entirely.
const pinIcon = L.divIcon({
  className: '',
  html: `<div style="width:26px;height:26px;transform:translate(-13px,-26px)">
    <svg viewBox="0 0 24 24" width="26" height="26" fill="#0A9C74" stroke="#fff" stroke-width="1.5">
      <path d="M12 2a7 7 0 0 0-7 7c0 5 7 13 7 13s7-8 7-13a7 7 0 0 0-7-7z"/>
      <circle cx="12" cy="9" r="2.6" fill="#fff" stroke="none"/>
    </svg></div>`,
  iconSize: [26, 26],
  iconAnchor: [0, 0],
})

function Events({ onPick }: { onPick: (lat: number, lon: number) => void }) {
  useMapEvents({ click: (e) => onPick(e.latlng.lat, e.latlng.lng) })
  return null
}

/** Tap or drag to set the report's exact location. */
export function LocationPicker({
  center,
  value,
  onChange,
}: {
  center: [number, number]
  value: { lat: number; lon: number } | null
  onChange: (lat: number, lon: number) => void
}) {
  return (
    <MapContainer
      center={value ? [value.lat, value.lon] : center}
      zoom={value ? 16 : 12}
      attributionControl={false}
      className="h-full w-full"
    >
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      <Events onPick={onChange} />
      {value && (
        <Marker
          position={[value.lat, value.lon]}
          icon={pinIcon}
          draggable
          eventHandlers={{
            dragend: (e) => {
              const p = e.target.getLatLng()
              onChange(p.lat, p.lng)
            },
          }}
        />
      )}
    </MapContainer>
  )
}

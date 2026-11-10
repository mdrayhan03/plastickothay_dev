import L from 'leaflet'
import { severityColor } from '@/lib/severity'

export interface MarkerData {
  severity: number
  image_url?: string
}

export function createComboMarkerIcon(data: MarkerData) {
  const color = severityColor[data.severity as keyof typeof severityColor] || '#2FA96A'
  const isUrgent = data.severity >= 4 // Severity 4 (High) & 5 (Critical) get the glowing pulse ring

  const pulseHtml = isUrgent
    ? `<div class="marker-pulse-ring" style="background:${color}"></div>`
    : ''

  const photoHtml = data.image_url
    ? `<img src="${data.image_url}" alt="" class="size-full object-cover" />`
    : `<div class="size-2.5 rounded-full" style="background:#ffffff"></div>`

  const html = `
    <div class="marker-pin-wrapper">
      ${pulseHtml}
      <div class="marker-pin-head" style="background:${color}">
        <div class="marker-pin-inner">
          ${photoHtml}
        </div>
      </div>
    </div>
  `

  return L.divIcon({
    className: '',
    html: html,
    iconSize: [22, 26],
    iconAnchor: [11, 26],
  })
}

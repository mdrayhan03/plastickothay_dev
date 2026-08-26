/**
 * Reverse geocoding via Nominatim (OpenStreetMap) - free, no API key, matches the OSM/Carto
 * map stack. Policy: ~1 req/sec, identify via a descriptive request, attribute OSM. We only call
 * it once per report submission (a human action), which stays well within that limit.
 *
 * This is deliberately best-effort: any failure resolves to '' so submitting a report never
 * depends on the geocoder being reachable.
 */

interface NominatimAddress {
  neighbourhood?: string
  suburb?: string
  quarter?: string
  road?: string
  city?: string
  town?: string
  city_district?: string
  state?: string
}

/** Build a short, human label like "Hatirjheel, Dhaka" from Nominatim's address parts. */
function shortLabel(a: NominatimAddress): string {
  const local = a.neighbourhood || a.suburb || a.quarter || a.road
  const area = a.city || a.town || a.city_district || a.state
  return [local, area].filter(Boolean).join(', ')
}

export const geocodeService = {
  async reverse(lat: number, lon: number): Promise<string> {
    try {
      const url = `https://nominatim.openstreetmap.org/reverse?format=jsonv2&zoom=16&lat=${lat}&lon=${lon}`
      const res = await fetch(url, { headers: { 'Accept-Language': 'en' } })
      if (!res.ok) return ''
      const data = (await res.json()) as { address?: NominatimAddress; display_name?: string }
      return shortLabel(data.address ?? {}) || data.display_name?.split(',').slice(0, 2).join(',') || ''
    } catch {
      return ''
    }
  },
}

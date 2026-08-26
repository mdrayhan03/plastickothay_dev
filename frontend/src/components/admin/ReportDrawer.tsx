import 'leaflet/dist/leaflet.css'
import { Check, Clock, Eye, EyeOff, Heart, Mail, MapPin, Phone, X } from 'lucide-react'
import { CircleMarker, MapContainer, TileLayer } from 'react-leaflet'
import { Drawer } from '@/components/admin/Drawer'
import { SeverityChip, StatusChip } from '@/components/admin/Chips'
import { severityColor } from '@/lib/severity'
import type { AdminPost, ModerationAction } from '@/types'

function Row({ icon: Icon, children }: { icon: typeof Mail; children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2.5 text-[13px] text-ink-2">
      <Icon className="size-4 shrink-0 text-ink-3" />
      <span className="min-w-0 truncate">{children}</span>
    </div>
  )
}

export function ReportDrawer({
  post,
  onClose,
  onAct,
  busy,
}: {
  post: AdminPost | null
  onClose: () => void
  onAct: (id: number, action: ModerationAction) => void
  busy: boolean
}) {
  return (
    <Drawer
      open={!!post}
      onClose={onClose}
      title={post ? `Report #${post.id}` : ''}
      footer={
        post && (
          <div className="flex flex-wrap gap-2">
            {post.status === 2 && (
              <>
                <button
                  disabled={busy}
                  onClick={() => onAct(post.id, 'approve')}
                  className="flex flex-1 items-center justify-center gap-1.5 rounded-xl bg-brand py-2.5 text-[13px] font-bold text-white disabled:opacity-50"
                >
                  <Check className="size-4" /> Approve
                </button>
                <button
                  disabled={busy}
                  onClick={() => onAct(post.id, 'reject')}
                  className="flex flex-1 items-center justify-center gap-1.5 rounded-xl bg-sev-5 py-2.5 text-[13px] font-bold text-white disabled:opacity-50"
                >
                  <X className="size-4" /> Reject
                </button>
              </>
            )}
            {post.status === 1 && (
              <button
                disabled={busy}
                onClick={() => onAct(post.id, 'hide')}
                className="flex flex-1 items-center justify-center gap-1.5 rounded-xl border border-line-2 py-2.5 text-[13px] font-bold disabled:opacity-50"
              >
                <EyeOff className="size-4" /> Hide from map
              </button>
            )}
            {post.status === 3 && (
              <button
                disabled={busy}
                onClick={() => onAct(post.id, 'unhide')}
                className="flex flex-1 items-center justify-center gap-1.5 rounded-xl bg-brand py-2.5 text-[13px] font-bold text-white disabled:opacity-50"
              >
                <Eye className="size-4" /> Unhide
              </button>
            )}
          </div>
        )
      }
    >
      {post && (
        <div className="space-y-5">
          <img
            src={post.image_url}
            alt=""
            className="h-52 w-full rounded-2xl object-cover"
            style={{ background: 'var(--surface-2)' }}
          />
          <div className="flex flex-wrap items-center gap-2">
            <StatusChip status={post.status} />
            <SeverityChip severity={post.severity} />
            <span className="ml-auto inline-flex items-center gap-1 text-[12px] font-semibold text-ink-3">
              <Heart className="size-3.5" /> {post.likes}
            </span>
          </div>

          {post.description && <p className="text-[14px] leading-relaxed text-ink">{post.description}</p>}

          <div className="h-40 overflow-hidden rounded-2xl border border-line">
            <MapContainer
              center={[post.lat, post.lon]}
              zoom={15}
              attributionControl={false}
              dragging={false}
              scrollWheelZoom={false}
              className="h-full w-full"
            >
              <TileLayer url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png" />
              <CircleMarker
                center={[post.lat, post.lon]}
                radius={9}
                pathOptions={{ color: '#fff', weight: 2, fillColor: severityColor[post.severity], fillOpacity: 1 }}
              />
            </MapContainer>
          </div>
          <Row icon={MapPin}>
            {post.place_name ? (
              <span>
                {post.place_name}{' '}
                <span className="text-ink-3 tnum">· {post.lat.toFixed(4)}, {post.lon.toFixed(4)}</span>
              </span>
            ) : (
              <span className="tnum">
                {post.lat.toFixed(5)}, {post.lon.toFixed(5)}
              </span>
            )}
          </Row>

          <div className="rounded-2xl border border-line bg-surface-2 p-4">
            <div className="mb-2.5 text-[11px] font-extrabold uppercase tracking-wide text-ink-3">
              Reporter (admin only)
            </div>
            <div className="mb-2 font-bold">{post.reporter_name}</div>
            <div className="space-y-1.5">
              {post.reporter_email && (
                <Row icon={Mail}>
                  <a className="hover:text-brand" href={`mailto:${post.reporter_email}`}>
                    {post.reporter_email}
                  </a>
                </Row>
              )}
              {post.reporter_phone && <Row icon={Phone}>{post.reporter_phone}</Row>}
            </div>
          </div>

          <div>
            <div className="mb-2 text-[11px] font-extrabold uppercase tracking-wide text-ink-3">
              History
            </div>
            <Row icon={Clock}>Submitted {new Date(post.created).toLocaleString()}</Row>
            {post.approved_at && (
              <div className="mt-1.5">
                <Row icon={Check}>Approved {new Date(post.approved_at).toLocaleString()}</Row>
              </div>
            )}
            <p className="mt-2 text-[11.5px] text-ink-3">
              Full moderation history needs the audit endpoint (BE-1).
            </p>
          </div>
        </div>
      )}
    </Drawer>
  )
}

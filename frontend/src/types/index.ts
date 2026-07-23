/**
 * API contract types — hand-mirrored from the backend serializers.
 * A backend change surfaces here as a type error, which is the point.
 */

export type Role = 'user' | 'staff' | 'admin'
export type WeekStart = 'monday' | 'sunday'
export type Severity = 1 | 2 | 3 | 4 | 5
export type PostStatus = 0 | 1 | 2 | 3 // rejected | approved | pending | hidden

// --- auth ---
export interface AuthUser {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  phone: string
  role: Role
  is_verified: boolean
}

export interface LoginResponse {
  access: string
  user: AuthUser
}

export interface RefreshResponse {
  access: string
}

// --- reports ---
export interface PublicPost {
  id: number
  reporter_name: string
  severity: Severity
  image_url: string
  lat: number
  lon: number
  // Reverse-geocoded label (e.g. "Hatirjheel, Dhaka"). Optional until the backend
  // `place_name` field ships — see admin_backend_todo.md (BE-8). Falls back to coords.
  place_name?: string
  description: string
  created: string
  likes: number
  liked_by_me: boolean
}

export interface OwnPost extends PublicPost {
  status: PostStatus
}

export interface MapMarker {
  id: number
  lat: number
  lon: number
  severity: Severity
}

export interface AdminPost extends PublicPost {
  reporter_email: string
  reporter_phone: string
  reporter_id: number | null
  status: PostStatus
  approved_at: string | null
}

export type ModerationAction = 'approve' | 'reject' | 'hide' | 'unhide'

/** Audit-log row — surfaces the backend's PostModerationLog (endpoint BE-1, pending). */
export interface AuditEntry {
  id: number
  admin: string
  action: ModerationAction
  post_id: number
  reason: string
  at: string
}

// --- scoring ---
export interface LeaderboardRow {
  rank: number
  user_id: number
  username: string
  full_name: string
  points: number
}

export interface Leaderboard {
  period: 'all' | 'year' | 'month' | 'week'
  results: LeaderboardRow[]
  next_cursor: string | null
}

export interface Contribution {
  total_points: number
  posts_approved: number
  likes_received: number
  likes_given: number
  level: number
  level_title: string
  points_to_next_level: number | null
  progress_percentage: number
  referrals: number
}

export interface EarnedBadge {
  code: string
  name: string
  description: string
  icon: string
  earned_at: string
}

// --- content / config ---
export interface SiteConfig {
  week_start: WeekStart
  site_name: string
  tagline: string
  logo_url: string | null
  map_center: { lat: number; lon: number } | null
  map_zoom: number
  flags: Record<string, boolean>
}

export interface ContactPage {
  heading: string
  intro: string
  email: string
  phone: string
  address: string
  map_lat: number | null
  map_lon: number | null
  socials: { platform: string; url: string; order: number }[]
}

// --- admin ---
export interface AdminStats {
  pending: number
  approved: number
  hidden: number
  rejected: number
  total: number
}

export interface AdminUser {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  phone: string
  role: Role
  is_verified: boolean
  is_active: boolean
}

/** User + contribution stats for the profile drawer (endpoint BE-4, pending). */
export interface AdminUserDetail extends AdminUser {
  posts_approved: number
  likes_received: number
  total_points: number
}

export interface ContactMessage {
  id: number
  name: string
  email: string
  phone: string
  subject: string
  message: string
  status: string
  created: string
}

export interface FeedbackItem {
  id: number
  name: string
  email: string
  rating: number
  comment: string
  created: string
}

// --- shared ---
export interface Page<T> {
  results: T[]
  next_cursor: string | null
}

export interface ApiError {
  error: { code: string; message: string; details: Record<string, unknown> }
}

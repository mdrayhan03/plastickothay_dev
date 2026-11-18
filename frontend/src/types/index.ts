/**
 * API contract types - hand-mirrored from the backend serializers.
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
  // Uploaded profile photo. Optional until the backend `avatar` field ships (BE-9);
  // the Avatar component falls back to initials when absent.
  avatar_url?: string | null
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
  reporter_id: number | null // the author's user id; null for anonymous reports
  severity: Severity
  image_url: string
  lat: number
  lon: number
  // Reverse-geocoded label (e.g. "Hatirjheel, Dhaka"). Falls back to coords when blank.
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
  image_url?: string
}

export interface AdminPost extends PublicPost {
  reporter_email: string
  reporter_phone: string
  status: PostStatus
  approved_at: string | null
}

/** Admin density-map marker - all statuses, unlike the approved-only public map (BE-3). */
export interface AdminMapMarker {
  id: number
  lat: number
  lon: number
  severity: Severity
  status: PostStatus
}

/** Dashboard analytics (BE-5): weekly submissions vs approvals + active contributors. */
export interface WeeklyPoint {
  week: string // ISO date, the Monday the week starts on
  submitted: number
  approved: number
}
export interface AdminAnalytics {
  over_time: WeeklyPoint[]
  active_users: number
}

export type ModerationAction = 'approve' | 'reject' | 'hide' | 'unhide'

/** Audit-log row - surfaces the backend's PostModerationLog (endpoint BE-1, pending). */
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
  avatar_url?: string | null
}

/** Public, privacy-limited profile of any user (endpoint BE-10, pending). */
export interface PublicProfile {
  id: number
  username: string
  full_name: string
  avatar_url: string | null
  level: number
  level_title: string
  total_points: number
  posts_approved: number
  likes_received: number
  badges: { code: string; name: string; icon: string }[]
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
  level?: number
  level_title?: string
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

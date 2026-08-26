import type { AdminUser } from '@/types'

/** Delete is admin-only, only for an already-inactive account, never yourself (AD-4, AD-5, BE-2). */
export function canDeleteUser(viewerIsAdmin: boolean, target: AdminUser, isSelf: boolean): boolean {
  return viewerIsAdmin && !target.is_active && !isSelf
}

/** Role changes are admin-only and never on your own account (AD-5, BE-0). */
export function canChangeRole(viewerIsAdmin: boolean, isSelf: boolean): boolean {
  return viewerIsAdmin && !isSelf
}

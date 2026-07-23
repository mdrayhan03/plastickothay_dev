import { describe, expect, it } from 'vitest'
import type { AdminUser } from '@/types'
import { canChangeRole, canDeleteUser } from './permissions'

function user(over: Partial<AdminUser> = {}): AdminUser {
  return {
    id: 1,
    username: 'u',
    email: 'u@x.com',
    first_name: 'U',
    last_name: 'Ser',
    phone: '',
    role: 'user',
    is_verified: true,
    is_active: true,
    ...over,
  }
}

describe('canDeleteUser (AD-4: inactive-only, admin-only, not self)', () => {
  it('allows an admin to delete an inactive other user', () => {
    expect(canDeleteUser(true, user({ is_active: false }), false)).toBe(true)
  })
  it('refuses deleting an active user, even as admin', () => {
    expect(canDeleteUser(true, user({ is_active: true }), false)).toBe(false)
  })
  it('refuses staff (non-admin) entirely', () => {
    expect(canDeleteUser(false, user({ is_active: false }), false)).toBe(false)
  })
  it('refuses self-delete', () => {
    expect(canDeleteUser(true, user({ is_active: false }), true)).toBe(false)
  })
})

describe('canChangeRole (AD-5: admin-only, not self)', () => {
  it('allows an admin to change another user’s role', () => {
    expect(canChangeRole(true, false)).toBe(true)
  })
  it('refuses staff', () => {
    expect(canChangeRole(false, false)).toBe(false)
  })
  it('refuses changing your own role', () => {
    expect(canChangeRole(true, true)).toBe(false)
  })
})

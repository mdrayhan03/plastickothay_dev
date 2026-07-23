import { describe, expect, it } from 'vitest'
import { loginSchema, otpSchema, registerSchema, resetSchema } from './schemas'

describe('loginSchema', () => {
  it('accepts a filled form', () => {
    expect(loginSchema.safeParse({ username: 'rahim', password: 'secret' }).success).toBe(true)
  })
  it('rejects empty username', () => {
    const r = loginSchema.safeParse({ username: '', password: 'x' })
    expect(r.success).toBe(false)
  })
})

describe('registerSchema', () => {
  const valid = {
    first_name: 'Rahim',
    last_name: 'Uddin',
    username: 'rahim',
    email: 'rahim@example.com',
    phone: '+8801700000000',
    password: 's3cretpass',
  }
  it('accepts a valid registration', () => {
    expect(registerSchema.safeParse(valid).success).toBe(true)
  })
  it('rejects a short password', () => {
    expect(registerSchema.safeParse({ ...valid, password: 'short' }).success).toBe(false)
  })
  it('rejects a bad email', () => {
    expect(registerSchema.safeParse({ ...valid, email: 'not-an-email' }).success).toBe(false)
  })
  it('rejects a 2-char username', () => {
    expect(registerSchema.safeParse({ ...valid, username: 'ab' }).success).toBe(false)
  })
})

describe('otpSchema', () => {
  it('accepts 6 digits', () => {
    expect(otpSchema.safeParse({ code: '123456' }).success).toBe(true)
  })
  it('rejects letters', () => {
    expect(otpSchema.safeParse({ code: '12345a' }).success).toBe(false)
  })
  it('rejects the wrong length', () => {
    expect(otpSchema.safeParse({ code: '123' }).success).toBe(false)
  })
})

describe('resetSchema', () => {
  it('requires an 8-char new password', () => {
    expect(resetSchema.safeParse({ code: '123456', new_password: 'short' }).success).toBe(false)
    expect(resetSchema.safeParse({ code: '123456', new_password: 'longenough' }).success).toBe(true)
  })
})

import { z } from 'zod'

export const loginSchema = z.object({
  username: z.string().min(1, 'Enter your username or email'),
  password: z.string().min(1, 'Enter your password'),
})

export const registerSchema = z.object({
  first_name: z.string().min(1, 'Required'),
  last_name: z.string().min(1, 'Required'),
  username: z.string().min(3, 'At least 3 characters'),
  email: z.string().email('Enter a valid email'),
  phone: z.string().min(6, 'Enter your phone number'),
  password: z.string().min(8, 'At least 8 characters'),
})

export const otpSchema = z.object({
  code: z
    .string()
    .length(6, 'The code is 6 digits')
    .regex(/^\d+$/, 'Digits only'),
})

export const forgotSchema = z.object({
  username: z.string().min(1, 'Enter your username'),
})

export const resetSchema = z.object({
  code: z.string().length(6, 'The code is 6 digits').regex(/^\d+$/, 'Digits only'),
  new_password: z.string().min(8, 'At least 8 characters'),
})

export const reportSchema = z.object({
  severity: z.number().min(1).max(5),
  description: z.string().max(500).optional().default(''),
  name: z.string().optional().default(''),
  email: z.string().email('Enter a valid email').or(z.literal('')).optional(),
  phone: z.string().optional().default(''),
})

export const profileSchema = z.object({
  first_name: z.string().min(1, 'Required'),
  last_name: z.string().min(1, 'Required'),
  phone: z.string().optional(),
})

export const contactSchema = z.object({
  name: z.string().min(1, 'Your name helps us reply'),
  email: z.string().email('Enter a valid email'),
  phone: z.string().optional(),
  subject: z.string().min(1, 'Add a subject'),
  message: z.string().min(5, 'Tell us a little more'),
})

export const feedbackSchema = z.object({
  rating: z.number().min(1, 'Pick a rating').max(5),
  comment: z.string().max(1000).optional(),
  name: z.string().optional(),
  email: z.string().email('Enter a valid email').or(z.literal('')).optional(),
})

export type ProfileInput = z.infer<typeof profileSchema>
export type ContactInput = z.infer<typeof contactSchema>
export type FeedbackInput = z.infer<typeof feedbackSchema>

export type LoginInput = z.infer<typeof loginSchema>
export type RegisterInput = z.infer<typeof registerSchema>
export type OtpInput = z.infer<typeof otpSchema>
export type ForgotInput = z.infer<typeof forgotSchema>
export type ResetInput = z.infer<typeof resetSchema>
export type ReportInput = z.infer<typeof reportSchema>

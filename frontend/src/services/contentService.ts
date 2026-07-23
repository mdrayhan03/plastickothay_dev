import { api } from '@/lib/api'
import type { ContactPage } from '@/types'

export interface ContactMessagePayload {
  subject: string
  message: string
  name?: string
  email?: string
  phone?: string
}

export interface FeedbackPayload {
  rating: number
  comment?: string
  name?: string
  email?: string
}

export const contentService = {
  async contactPage() {
    const { data } = await api.get<ContactPage>('/contact-page/')
    return data
  },
  async submitContactMessage(payload: ContactMessagePayload) {
    const { data } = await api.post<{ detail: string }>('/contact-messages/', payload)
    return data
  },
  async submitFeedback(payload: FeedbackPayload) {
    const { data } = await api.post<{ detail: string }>('/feedback/', payload)
    return data
  },
}

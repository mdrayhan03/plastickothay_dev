import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { ReactNode } from 'react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AuthContext } from '@/context/auth-context'
import { contentService } from '@/services/contentService'
import { ContactPage } from './ContactPage'
import { FeedbackFormPage } from './FeedbackFormPage'

vi.mock('@/services/contentService', () => ({
  contentService: {
    contactPage: vi.fn(),
    submitContactMessage: vi.fn(),
    submitFeedback: vi.fn(),
  },
}))

const anon = {
  user: null,
  status: 'anon' as const,
  login: vi.fn(),
  logout: vi.fn(),
  setUser: vi.fn(),
  isStaff: false,
}

function renderPage(ui: ReactNode) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <AuthContext.Provider value={anon}>{ui}</AuthContext.Provider>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => vi.clearAllMocks())

describe('FeedbackFormPage', () => {
  it('requires a rating before submitting', async () => {
    renderPage(<FeedbackFormPage />)
    await userEvent.click(screen.getByRole('button', { name: /send feedback/i }))
    expect(await screen.findByText(/pick a rating/i)).toBeInTheDocument()
    expect(contentService.submitFeedback).not.toHaveBeenCalled()
  })

  it('submits the chosen star rating', async () => {
    vi.mocked(contentService.submitFeedback).mockResolvedValue({ detail: 'ok' })
    renderPage(<FeedbackFormPage />)
    await userEvent.click(screen.getByRole('button', { name: /^4 stars$/i }))
    await userEvent.click(screen.getByRole('button', { name: /send feedback/i }))
    await waitFor(() =>
      expect(contentService.submitFeedback).toHaveBeenCalledWith(expect.objectContaining({ rating: 4 })),
    )
  })
})

describe('ContactPage', () => {
  it('validates and then submits a message', async () => {
    vi.mocked(contentService.contactPage).mockResolvedValue({
      heading: 'Reach us',
      intro: '',
      email: 'hi@pk.org',
      phone: '',
      address: '',
      map_lat: null,
      map_lon: null,
      socials: [],
    })
    vi.mocked(contentService.submitContactMessage).mockResolvedValue({ detail: 'sent' })
    renderPage(<ContactPage />)

    await userEvent.click(screen.getByRole('button', { name: /send message/i }))
    expect(await screen.findByText(/add a subject/i)).toBeInTheDocument()
    expect(contentService.submitContactMessage).not.toHaveBeenCalled()

    await userEvent.type(screen.getByLabelText(/your name/i), 'Rahim')
    await userEvent.type(screen.getByLabelText(/^email$/i), 'rahim@example.com')
    await userEvent.type(screen.getByLabelText(/subject/i), 'Broken bin')
    await userEvent.type(screen.getByLabelText(/message/i), 'There is a lot of plastic here.')
    await userEvent.click(screen.getByRole('button', { name: /send message/i }))

    await waitFor(() =>
      expect(contentService.submitContactMessage).toHaveBeenCalledWith(
        expect.objectContaining({ subject: 'Broken bin', name: 'Rahim' }),
      ),
    )
  })
})

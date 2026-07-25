import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import type { ReactNode } from 'react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AuthContext } from '@/context/auth-context'
import { userService } from '@/services/userService'
import type { PublicProfile } from '@/types'
import { ProfilePage } from './ProfilePage'

vi.mock('@/services/userService', () => ({
  userService: { profile: vi.fn(), posts: vi.fn() },
}))

const anon = {
  user: null,
  status: 'anon' as const,
  login: vi.fn(),
  logout: vi.fn(),
  setUser: vi.fn(),
  isStaff: false,
}

function renderAt(id: number) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={qc}>
      <AuthContext.Provider value={anon}>
        <MemoryRouter initialEntries={[`/u/${id}`]}>
          <Routes>
            <Route path="/u/:id" element={children} />
          </Routes>
        </MemoryRouter>
      </AuthContext.Provider>
    </QueryClientProvider>
  )
  render(<ProfilePage />, { wrapper })
}

const profile: PublicProfile = {
  id: 5,
  username: 'rahim',
  full_name: 'Rahim Uddin',
  avatar_url: null,
  level: 3,
  level_title: 'Guardian',
  total_points: 420,
  posts_approved: 7,
  likes_received: 30,
  badges: [{ code: 'first_report', name: 'First Report', icon: '🌱' }],
}

beforeEach(() => vi.clearAllMocks())

describe('ProfilePage', () => {
  it('shows a pending state when the profile endpoint 404s (BE-10)', async () => {
    vi.mocked(userService.profile).mockRejectedValue(new Error('404'))
    vi.mocked(userService.posts).mockRejectedValue(new Error('404'))
    renderAt(5)
    expect(await screen.findByText(/profiles aren’t available yet/i)).toBeInTheDocument()
  })

  it('renders the profile with name, stats and badges', async () => {
    vi.mocked(userService.profile).mockResolvedValue(profile)
    vi.mocked(userService.posts).mockResolvedValue({ results: [], next_cursor: null })
    renderAt(5)
    expect(await screen.findByText('Rahim Uddin')).toBeInTheDocument()
    expect(screen.getByText('@rahim')).toBeInTheDocument()
    expect(screen.getByText('First Report')).toBeInTheDocument()
  })
})

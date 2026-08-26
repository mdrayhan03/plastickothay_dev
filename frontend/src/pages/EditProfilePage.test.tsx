import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AuthContext } from '@/context/auth-context'
import { authService } from '@/services/authService'
import type { AuthUser } from '@/types'
import { EditProfilePage } from './EditProfilePage'

vi.mock('@/services/authService', () => ({
  authService: { updateProfile: vi.fn() },
}))

const user: AuthUser = {
  id: 1,
  username: 'rahim',
  email: 'rahim@example.com',
  first_name: 'Rahim',
  last_name: 'Uddin',
  phone: '0170000000',
  role: 'user',
  is_verified: true,
}

function renderPage(setUser = vi.fn()) {
  render(
    <MemoryRouter>
      <AuthContext.Provider
        value={{ user, status: 'authed', login: vi.fn(), logout: vi.fn(), setUser, isStaff: false }}
      >
        <EditProfilePage />
      </AuthContext.Provider>
    </MemoryRouter>,
  )
  return { setUser }
}

beforeEach(() => vi.clearAllMocks())

describe('EditProfilePage', () => {
  it('prefills the editable fields and keeps username/email read-only', () => {
    renderPage()
    expect(screen.getByLabelText(/first name/i)).toHaveValue('Rahim')
    expect(screen.getByLabelText(/phone/i)).toHaveValue('0170000000')
    // Username/email are shown as text, not as editable inputs.
    expect(screen.queryByLabelText(/username/i)).not.toBeInTheDocument()
    expect(screen.getByText('rahim@example.com')).toBeInTheDocument()
  })

  it('saves the three editable fields and updates the cached user', async () => {
    const updated = { ...user, first_name: 'Karim' }
    vi.mocked(authService.updateProfile).mockResolvedValue(updated)
    const { setUser } = renderPage()

    const first = screen.getByLabelText(/first name/i)
    await userEvent.clear(first)
    await userEvent.type(first, 'Karim')
    await userEvent.click(screen.getByRole('button', { name: /save changes/i }))

    await waitFor(() =>
      expect(authService.updateProfile).toHaveBeenCalledWith({
        first_name: 'Karim',
        last_name: 'Uddin',
        phone: '0170000000',
      }),
    )
    expect(setUser).toHaveBeenCalledWith(updated)
  })
})

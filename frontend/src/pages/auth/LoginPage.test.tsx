import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { ReactNode } from 'react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { AuthContext } from '@/context/auth-context'
import { LoginPage } from './LoginPage'

function renderLogin(login = vi.fn()) {
  const qc = new QueryClient()
  const authValue = {
    user: null,
    status: 'anon' as const,
    login,
    logout: vi.fn(),
    isStaff: false,
  }
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <AuthContext.Provider value={authValue}>{children}</AuthContext.Provider>
      </MemoryRouter>
    </QueryClientProvider>
  )
  render(<LoginPage />, { wrapper })
  return { login }
}

describe('LoginPage', () => {
  it('renders the sign-in form', () => {
    renderLogin()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
    expect(screen.getByText(/report without an account/i)).toBeInTheDocument()
  })

  it('shows validation errors on empty submit and does not call login', async () => {
    const { login } = renderLogin()
    await userEvent.click(screen.getByRole('button', { name: /sign in/i }))
    expect(await screen.findByText(/enter your username/i)).toBeInTheDocument()
    expect(login).not.toHaveBeenCalled()
  })

  it('calls login with the entered credentials', async () => {
    const login = vi.fn().mockResolvedValue(undefined)
    renderLogin(login)
    const username = screen.getByRole('textbox') // the only text input; password isn't a textbox
    const password = document.querySelector('input[type="password"]') as HTMLInputElement
    await userEvent.type(username, 'rahim')
    await userEvent.type(password, 's3cretpass')
    await userEvent.click(screen.getByRole('button', { name: /sign in/i }))
    await waitFor(() => expect(login).toHaveBeenCalledWith('rahim', 's3cretpass'))
  })
})

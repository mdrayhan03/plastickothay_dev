import { Component, type ReactNode } from 'react'

interface Props {
  children: ReactNode
}
interface State {
  hasError: boolean
}

/** Catches render errors and shows a friendly recovery screen instead of a blank page. */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false }

  static getDerivedStateFromError(): State {
    return { hasError: true }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-dvh flex-col items-center justify-center gap-4 bg-ground p-8 text-center text-ink">
          <div className="font-display text-2xl font-extrabold text-brand">Something went wrong</div>
          <p className="max-w-xs text-sm text-ink-2">
            The app hit an unexpected error. Reloading usually fixes it.
          </p>
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="rounded-[14px] bg-[linear-gradient(152deg,var(--brand-2),var(--brand-deep))] px-6 py-3 text-sm font-bold text-white"
          >
            Reload
          </button>
        </div>
      )
    }
    return this.props.children
  }
}

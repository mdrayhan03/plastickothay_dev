import { useEffect, useState } from 'react'

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed'; platform: string }>
}

// Capture the event even if it fires before React mounts
let savedPrompt: BeforeInstallPromptEvent | null = null
const listeners = new Set<(e: BeforeInstallPromptEvent | null) => void>()

if (typeof window !== 'undefined') {
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault()
    savedPrompt = e as BeforeInstallPromptEvent
    listeners.forEach((cb) => cb(savedPrompt))
  })

  window.addEventListener('appinstalled', () => {
    savedPrompt = null
    listeners.forEach((cb) => cb(null))
  })
}

export function usePWAInstall() {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(
    () => savedPrompt
  )
  const [isInstalled, setIsInstalled] = useState(() =>
    typeof window !== 'undefined'
      ? window.matchMedia('(display-mode: standalone)').matches
      : false
  )

  useEffect(() => {
    const sync = (prompt: BeforeInstallPromptEvent | null) => {
      setDeferredPrompt(prompt)
      if (!prompt && window.matchMedia('(display-mode: standalone)').matches) {
        setIsInstalled(true)
      }
    }
    listeners.add(sync)
    return () => {
      listeners.delete(sync)
    }
  }, [])

  const promptInstall = async () => {
    if (!deferredPrompt) return false
    await deferredPrompt.prompt()
    const { outcome } = await deferredPrompt.userChoice
    savedPrompt = null
    setDeferredPrompt(null)
    if (outcome === 'accepted') setIsInstalled(true)
    return outcome === 'accepted'
  }

  return {
    canInstall: Boolean(deferredPrompt) && !isInstalled,
    isInstalled,
    promptInstall,
  }
}
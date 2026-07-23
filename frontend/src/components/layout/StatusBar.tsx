/** Faux iOS status bar — sells the native-app feel on desktop; on mobile the OS covers it. */
export function StatusBar() {
  return (
    <div className="flex h-13 flex-none items-end justify-between px-6.5 pb-1.5 text-[13px] font-bold text-ink">
      <span className="tnum">9:41</span>
      <span className="flex items-center gap-1.5">
        <svg viewBox="0 0 24 24" fill="currentColor" className="size-4">
          <path d="M2 20h3v-6H2v6Zm5 0h3V8H7v12Zm5 0h3V4h-3v16Zm5 0h3v-9h-3v9Z" />
        </svg>
        <svg viewBox="0 0 24 24" fill="currentColor" className="size-4">
          <path d="M12 6c3.9 0 7.4 1.6 9.9 4.2l-1.4 1.4A11.9 11.9 0 0 0 12 8a11.9 11.9 0 0 0-8.5 3.6L2 10.2A13.9 13.9 0 0 1 12 6Zm0 8c1.1 0 2.1.4 2.8 1.2L12 18l-2.8-2.8A4 4 0 0 1 12 14Z" />
        </svg>
        <svg viewBox="0 0 26 24" fill="currentColor" className="h-4 w-5">
          <rect x="1" y="7" width="19" height="11" rx="3" stroke="currentColor" strokeWidth="1.6" fill="none" />
          <rect x="3" y="9" width="14" height="7" rx="1.5" />
          <rect x="21" y="10" width="2.5" height="5" rx="1" />
        </svg>
      </span>
    </div>
  )
}

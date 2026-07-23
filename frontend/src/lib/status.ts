import type { PostStatus } from '@/types'

/** PostStatus: 0 rejected · 1 approved · 2 pending · 3 hidden */
export const statusMeta: Record<PostStatus, { label: string; cls: string; dot: string }> = {
  2: { label: 'Pending', cls: 'bg-gold-soft text-[#9A6B12]', dot: 'var(--gold)' },
  1: { label: 'Approved', cls: 'bg-brand-soft text-brand-deep', dot: 'var(--brand)' },
  3: { label: 'Hidden', cls: 'bg-surface-2 text-ink-2', dot: 'var(--ink-3)' },
  0: { label: 'Rejected', cls: 'bg-[#fdecec] text-[#c02c31] dark:bg-[#3a1f1f] dark:text-[#f0a3a3]', dot: 'var(--sev-5)' },
}

/** Review-queue tab key ↔ the status filter the API expects. */
export const statusFromTab: Record<string, PostStatus> = {
  pending: 2,
  approved: 1,
  hidden: 3,
  rejected: 0,
}

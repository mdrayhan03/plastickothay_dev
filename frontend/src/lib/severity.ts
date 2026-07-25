import type { Severity } from '@/types'

export const severityColor: Record<Severity, string> = {
  1: '#2fa96a',
  2: '#8cb93b',
  3: '#f2a93b',
  4: '#f0801e',
  5: '#e5484d',
}

export const severityLabel: Record<Severity, string> = {
  1: 'Low',
  2: 'Minor',
  3: 'Moderate',
  4: 'High',
  5: 'Critical',
}

export const severityClass: Record<Severity, string> = {
  1: 'bg-sev-1',
  2: 'bg-sev-2',
  3: 'bg-sev-3',
  4: 'bg-sev-4',
  5: 'bg-sev-5',
}

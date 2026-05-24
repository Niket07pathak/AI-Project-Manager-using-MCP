const colors: Record<string, string> = {
  created: 'bg-slate-100 text-slate-700 ring-slate-200',
  running: 'bg-blue-50 text-blue-700 ring-blue-200',
  success: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  failed: 'bg-red-50 text-red-700 ring-red-200',
  uploaded: 'bg-amber-50 text-amber-700 ring-amber-200',
  processed: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  pending_approval: 'bg-amber-50 text-amber-700 ring-amber-200',
  approved: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  rejected: 'bg-red-50 text-red-700 ring-red-200',
  high: 'bg-red-50 text-red-700 ring-red-200',
  medium: 'bg-blue-50 text-blue-700 ring-blue-200',
  low: 'bg-slate-100 text-slate-700 ring-slate-200',
}

interface StatusBadgeProps {
  value?: string | boolean | null
}

export function StatusBadge({ value }: StatusBadgeProps) {
  const label = typeof value === 'boolean' ? (value ? 'approved' : 'not approved') : value || 'unknown'
  const key = String(label).toLowerCase()
  const className = colors[key] ?? 'bg-slate-100 text-slate-700 ring-slate-200'

  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${className}`}>
      {String(label).replace(/_/g, ' ')}
    </span>
  )
}

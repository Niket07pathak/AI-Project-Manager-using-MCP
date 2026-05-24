import { Loader2 } from 'lucide-react'

interface LoadingStateProps {
  label?: string
}

export function LoadingState({ label = 'Loading' }: LoadingStateProps) {
  return (
    <div className="flex min-h-48 items-center justify-center rounded-lg border border-dashed border-slate-300 bg-white/70 p-8 text-slate-600">
      <Loader2 className="mr-2 h-5 w-5 animate-spin text-blue-600" />
      <span className="text-sm font-medium">{label}</span>
    </div>
  )
}

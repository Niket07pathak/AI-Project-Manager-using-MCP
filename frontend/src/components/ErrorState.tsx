import { AlertTriangle } from 'lucide-react'

interface ErrorStateProps {
  message: string
  onRetry?: () => void
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-800">
      <div className="flex items-start gap-3">
        <AlertTriangle className="mt-0.5 h-5 w-5 flex-none" />
        <div className="min-w-0">
          <p className="text-sm font-semibold">Something went wrong</p>
          <p className="mt-1 break-words text-sm">{message}</p>
          {onRetry ? (
            <button className="btn btn-secondary mt-3 border-red-200 text-red-700" onClick={onRetry}>
              Try again
            </button>
          ) : null}
        </div>
      </div>
    </div>
  )
}

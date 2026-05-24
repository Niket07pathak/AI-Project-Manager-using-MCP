import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <div className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-3xl flex-col items-center justify-center px-4 text-center">
      <p className="text-sm font-semibold text-blue-700">404</p>
      <h1 className="mt-2 text-4xl font-black text-slate-950">Page not found</h1>
      <p className="mt-3 text-slate-600">That route does not exist in this dashboard.</p>
      <Link to="/dashboard" className="btn btn-primary mt-6">
        Back to dashboard
      </Link>
    </div>
  )
}

import { useAuth } from '@clerk/clerk-react'
import { Navigate, useLocation } from 'react-router-dom'
import { LoadingState } from './LoadingState'

interface ProtectedRouteProps {
  children: React.ReactNode
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isLoaded, isSignedIn } = useAuth()
  const location = useLocation()

  if (!isLoaded) return <LoadingState label="Checking session" />

  if (!isSignedIn) {
    return <Navigate to="/" replace state={{ from: location.pathname }} />
  }

  return children
}

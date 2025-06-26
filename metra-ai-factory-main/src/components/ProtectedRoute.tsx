import { Navigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'

interface ProtectedRouteProps {
  children: React.ReactNode
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { user, token } = useAuthStore()

  if (!user || !token) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
} 
import { ReactNode } from 'react'
// import { Navigate } from 'react-router-dom'
// import { useAuthStore } from '@/stores/authStore'

interface ProtectedRouteProps {
  children: ReactNode
}

const ProtectedRoute = ({ children }: ProtectedRouteProps) => {
  // const { token } = useAuthStore()
  
  // if (!token) {
  //   return <Navigate to="/login" replace />
  // }
  
  // 暂时禁用认证，直接返回子组件
  return <>{children}</>
}

export default ProtectedRoute 
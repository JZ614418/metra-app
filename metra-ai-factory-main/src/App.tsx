import { Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import { useAuthStore } from '@/stores/authStore'
import { api } from '@/lib/api'

// Pages
import Index from '@/pages/Index'
import Dashboard from '@/pages/Dashboard'
import Login from '@/pages/Login'
import Register from '@/pages/Register'
import NotFound from '@/pages/NotFound'
import ModelSelection from '@/pages/ModelSelection'

// Components
import ProtectedRoute from '@/components/ProtectedRoute'
import { Toaster } from '@/components/ui/toaster'

function App() {
  const { token, setUser, setToken } = useAuthStore()

  useEffect(() => {
    // Check if user is logged in on app load
    const checkAuth = async () => {
      if (token) {
        try {
          const user = await api.getMe()
          setUser(user)
        } catch (error) {
          // Token is invalid
          setToken(null)
          setUser(null)
        }
      }
    }
    
    checkAuth()
  }, [])

  return (
    <Routes>
      {/* Public routes */}
      <Route path="/" element={<Index />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      
      {/* Protected routes */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      
      <Route path="/model-selection" element={<ProtectedRoute><ModelSelection /></ProtectedRoute>} />
      
      {/* 404 */}
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}

export default App

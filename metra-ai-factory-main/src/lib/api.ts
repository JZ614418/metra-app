import { useAuthStore } from '@/stores/authStore'

const API_URL = '/api' // All requests will now go to /api, which will be proxied by Vercel

interface User {
  id: string
  email: string
  full_name?: string
  is_active: boolean
  created_at: string
}

class ApiClient {
  private getHeaders(): HeadersInit {
    const token = useAuthStore.getState().token
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    }
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    
    return headers
  }

  async request<T>(
    endpoint: string, 
    options: RequestInit = {},
    isStream: boolean = false
  ): Promise<T> {
    const response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers: {
        ...this.getHeaders(),
        ...options.headers,
      },
    })

    if (response.status === 401) {
      // Token expired or invalid
      useAuthStore.getState().logout()
      window.location.href = '/login'
    }

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Something went wrong')
    }

    if (isStream) {
      return response.body as T;
    }

    return response.json()
  }

  async post<T>(endpoint: string, data: any, isStream: boolean = false) {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    }, isStream);
  }

  // Auth endpoints
  async register(email: string, password: string, fullName?: string, invitationCode?: string) {
    return this.request<User>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({
        email,
        password,
        username: email.split('@')[0],
        full_name: fullName,
        invitation_code: invitationCode,
      }),
    })
  }

  async login(email: string, password: string) {
    const response = await fetch(`${API_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: email,
        password: password,
      }),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Login failed')
    }

    return response.json()
  }

  async getMe() {
    return this.request<User>('/auth/me')
  }

  async updateMe(data: { email?: string; full_name?: string; password?: string }) {
    return this.request<User>('/auth/me', {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async getUsageStats() {
    return this.request('/auth/me/usage')
  }

  async forgotPassword(email: string) {
    return this.request('/auth/forgot-password', {
      method: 'POST',
      body: JSON.stringify({ email }),
    })
  }
}

export const api = new ApiClient() 
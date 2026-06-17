import React, { createContext, useContext, useState, useCallback } from 'react'
import axios from 'axios'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('admin_token'))
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('admin_user')
    return saved ? JSON.parse(saved) : null
  })

  const login = useCallback(async (email, password) => {
    const response = await axios.post('/api/v1/auth/login', { email, password })
    const { access_token, refresh_token } = response.data
    localStorage.setItem('admin_token', access_token)
    localStorage.setItem('refresh_token', refresh_token)
    localStorage.setItem('admin_user', JSON.stringify({ email }))
    setToken(access_token)
    setUser({ email })
    // Set default auth header
    axios.defaults.headers.common['Authorization'] = `******
    return response.data
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('admin_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('admin_user')
    delete axios.defaults.headers.common['Authorization']
    setToken(null)
    setUser(null)
  }, [])

  // Set auth header on load
  if (token) {
    axios.defaults.headers.common['Authorization'] = `******
  }

  return (
    <AuthContext.Provider value={{ token, user, isAuthenticated: !!token, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}

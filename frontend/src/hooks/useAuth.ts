// useAuth hook - wrapper around useAuthStore for convenience
import { useEffect } from 'react'
import { useAuthStore } from '../stores/useAuthStore'

export function useAuth() {
  const { user, isAuthenticated, isLoading, checkAuth, login, logout } = useAuthStore()

  useEffect(() => {
    // Check auth on mount
    checkAuth()
  }, [checkAuth])

  return {
    user,
    isAuthenticated,
    isLoading,
    checkAuth,
    login,
    logout,
  }
}

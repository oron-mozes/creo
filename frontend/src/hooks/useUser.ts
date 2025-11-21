// useUser hook - wrapper around useUserStore for convenience
import { useEffect } from 'react'
import { useUserStore } from '../stores/useUserStore'
import { useAuthStore } from '../stores/useAuthStore'

export function useUser() {
  const { user } = useAuthStore()
  const { userId, isAnonymous, sessions, initializeUserId, saveSession, loadSessions, clearSessions } = useUserStore()

  useEffect(() => {
    // Initialize user ID based on auth state
    initializeUserId(user?.user_id)
  }, [user, initializeUserId])

  useEffect(() => {
    // Load sessions on mount
    loadSessions()
  }, [loadSessions])

  return {
    userId,
    isAnonymous,
    sessions,
    saveSession,
    clearSessions,
  }
}

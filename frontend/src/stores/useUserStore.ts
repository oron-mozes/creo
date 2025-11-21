// User store for user ID and session management
import { create } from 'zustand'
import { storageService, STORAGE_KEYS } from '../services/storageService'
import type { Session } from '../types'

interface UserState {
  userId: string
  isAnonymous: boolean
  sessions: Session[]

  // Actions
  initializeUserId: (authenticatedUserId?: string) => void
  saveSession: (sessionId: string, title: string) => void
  loadSessions: () => void
  clearSessions: () => void
}

// Generate or get anonymous user ID
const getOrCreateAnonId = (): string => {
  let anonId = storageService.get<string>(STORAGE_KEYS.ANON_USER_ID)
  if (!anonId) {
    anonId = `anon_${Math.random().toString(36).substr(2, 12)}`
    storageService.set(STORAGE_KEYS.ANON_USER_ID, anonId)
  }
  return anonId
}

export const useUserStore = create<UserState>((set, get) => ({
  userId: getOrCreateAnonId(),
  isAnonymous: true,
  sessions: [],

  initializeUserId: (authenticatedUserId?: string) => {
    if (authenticatedUserId) {
      set({ userId: authenticatedUserId, isAnonymous: false })
    } else {
      set({ userId: getOrCreateAnonId(), isAnonymous: true })
    }
  },

  saveSession: (sessionId: string, title: string) => {
    const sessions = storageService.get<Session[]>(STORAGE_KEYS.SESSIONS, [])
    const existingIndex = sessions.findIndex(s => s.id === sessionId)

    const session: Session = {
      id: sessionId,
      title: title || 'New Chat',
      timestamp: Date.now(),
    }

    if (existingIndex >= 0) {
      sessions[existingIndex] = session
    } else {
      sessions.unshift(session)
    }

    // Keep only last 50 sessions
    if (sessions.length > 50) {
      sessions.length = 50
    }

    storageService.set(STORAGE_KEYS.SESSIONS, sessions)
    set({ sessions })
  },

  loadSessions: () => {
    const sessions = storageService.get<Session[]>(STORAGE_KEYS.SESSIONS, [])
    set({ sessions })
  },

  clearSessions: () => {
    storageService.remove(STORAGE_KEYS.SESSIONS)
    set({ sessions: [] })
  },
}))

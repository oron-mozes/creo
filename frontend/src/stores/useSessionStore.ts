// Session store for managing chat sessions and active session
import { create } from 'zustand'
import { apiService } from '../services/apiService'
import type { Session } from '../types'

interface SessionState {
  // All sessions loaded from backend
  sessions: Session[]

  // Currently active session being displayed
  activeSessionId: string | null

  // Loading states
  isLoadingSessions: boolean

  // Actions
  fetchSessions: (userId: string) => Promise<void>
  setActiveSession: (sessionId: string) => void
  addSession: (session: Session) => void
  updateSession: (sessionId: string, updates: Partial<Session>) => void
  removeSession: (sessionId: string) => void
  clearSessions: () => void
}

export const useSessionStore = create<SessionState>((set, get) => ({
  sessions: [],
  activeSessionId: null,
  isLoadingSessions: false,

  fetchSessions: async (userId: string) => {
    set({ isLoadingSessions: true })
    try {
      const sessions = await apiService.getSessions(userId)
      set({ sessions, isLoadingSessions: false })
    } catch (error) {
      console.error('Failed to fetch sessions:', error)
      set({ isLoadingSessions: false })
    }
  },

  setActiveSession: (sessionId: string) => {
    set({ activeSessionId: sessionId })
  },

  addSession: (session: Session) => {
    const { sessions } = get()
    // Check if session already exists
    const existingIndex = sessions.findIndex(s => s.id === session.id)

    if (existingIndex >= 0) {
      // Update existing session
      const updatedSessions = [...sessions]
      updatedSessions[existingIndex] = session
      set({ sessions: updatedSessions })
    } else {
      // Add new session to the beginning
      set({ sessions: [session, ...sessions] })
    }
  },

  updateSession: (sessionId: string, updates: Partial<Session>) => {
    const { sessions } = get()
    const updatedSessions = sessions.map(s =>
      s.id === sessionId ? { ...s, ...updates } : s
    )
    set({ sessions: updatedSessions })
  },

  removeSession: (sessionId: string) => {
    const { sessions, activeSessionId } = get()
    const updatedSessions = sessions.filter(s => s.id !== sessionId)

    // If the removed session was active, clear active session
    if (activeSessionId === sessionId) {
      set({ sessions: updatedSessions, activeSessionId: null })
    } else {
      set({ sessions: updatedSessions })
    }
  },

  clearSessions: () => {
    set({ sessions: [], activeSessionId: null })
  },
}))

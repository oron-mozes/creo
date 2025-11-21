// Chat store for chat state management
import { create } from 'zustand'
import type { Message, BusinessCard } from '../types'

interface ChatState {
  // State per session
  sessions: Map<string, {
    messages: Message[]
    isLoading: boolean
    streamingMessage: string
    businessCard: BusinessCard | null
    error: string | null
  }>

  // Current session
  currentSessionId: string | null

  // Actions
  setCurrentSession: (sessionId: string) => void
  addMessage: (sessionId: string, message: Message) => void
  setMessages: (sessionId: string, messages: Message[]) => void
  setLoading: (sessionId: string, isLoading: boolean) => void
  setStreamingMessage: (sessionId: string, chunk: string, append?: boolean) => void
  setBusinessCard: (sessionId: string, card: BusinessCard) => void
  setError: (sessionId: string, error: string | null) => void
  clearSession: (sessionId: string) => void
  getSessionState: (sessionId: string) => ChatState['sessions'] extends Map<string, infer T> ? T : never
}

const defaultSessionState = {
  messages: [],
  isLoading: false,
  streamingMessage: '',
  businessCard: null,
  error: null,
}

export const useChatStore = create<ChatState>((set, get) => ({
  sessions: new Map(),
  currentSessionId: null,

  setCurrentSession: (sessionId: string) => {
    set({ currentSessionId: sessionId })
    // Initialize session if it doesn't exist
    const state = get()
    if (!state.sessions.has(sessionId)) {
      const newSessions = new Map(state.sessions)
      newSessions.set(sessionId, { ...defaultSessionState })
      set({ sessions: newSessions })
    }
  },

  addMessage: (sessionId: string, message: Message) => {
    const state = get()
    const sessionState = state.sessions.get(sessionId) || { ...defaultSessionState }
    const newSessions = new Map(state.sessions)
    newSessions.set(sessionId, {
      ...sessionState,
      messages: [...sessionState.messages, message],
    })
    set({ sessions: newSessions })
  },

  setMessages: (sessionId: string, messages: Message[]) => {
    const state = get()
    const sessionState = state.sessions.get(sessionId) || { ...defaultSessionState }
    const newSessions = new Map(state.sessions)
    newSessions.set(sessionId, {
      ...sessionState,
      messages,
    })
    set({ sessions: newSessions })
  },

  setLoading: (sessionId: string, isLoading: boolean) => {
    const state = get()
    const sessionState = state.sessions.get(sessionId) || { ...defaultSessionState }
    const newSessions = new Map(state.sessions)
    newSessions.set(sessionId, {
      ...sessionState,
      isLoading,
    })
    set({ sessions: newSessions })
  },

  setStreamingMessage: (sessionId: string, chunk: string, append = true) => {
    const state = get()
    const sessionState = state.sessions.get(sessionId) || { ...defaultSessionState }
    const newSessions = new Map(state.sessions)
    newSessions.set(sessionId, {
      ...sessionState,
      streamingMessage: append ? sessionState.streamingMessage + chunk : chunk,
    })
    set({ sessions: newSessions })
  },

  setBusinessCard: (sessionId: string, card: BusinessCard) => {
    const state = get()
    const sessionState = state.sessions.get(sessionId) || { ...defaultSessionState }
    const newSessions = new Map(state.sessions)
    newSessions.set(sessionId, {
      ...sessionState,
      businessCard: card,
    })
    set({ sessions: newSessions })
  },

  setError: (sessionId: string, error: string | null) => {
    const state = get()
    const sessionState = state.sessions.get(sessionId) || { ...defaultSessionState }
    const newSessions = new Map(state.sessions)
    newSessions.set(sessionId, {
      ...sessionState,
      error,
    })
    set({ sessions: newSessions })
  },

  clearSession: (sessionId: string) => {
    const state = get()
    const newSessions = new Map(state.sessions)
    newSessions.delete(sessionId)
    set({ sessions: newSessions })
  },

  getSessionState: (sessionId: string) => {
    const state = get()
    return state.sessions.get(sessionId) || { ...defaultSessionState }
  },
}))

// Auth store using Zustand
import { create } from 'zustand'
import { apiService } from '../services/apiService'
import { storageService, STORAGE_KEYS } from '../services/storageService'
import type { User } from '../types'

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean

  // Actions
  checkAuth: () => Promise<void>
  login: (token: string) => void
  logout: () => void
  setUser: (user: User | null) => void
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,

  checkAuth: async () => {
    try {
      const token = storageService.get<string>(STORAGE_KEYS.AUTH_TOKEN)
      if (!token) {
        set({ isLoading: false })
        return
      }

      const userData = await apiService.checkAuth()
      if (userData) {
        set({ user: userData, isAuthenticated: true })
      }
    } catch (error) {
      console.error('Auth check failed:', error)
      storageService.remove(STORAGE_KEYS.AUTH_TOKEN)
    } finally {
      set({ isLoading: false })
    }
  },

  login: (token: string) => {
    storageService.set(STORAGE_KEYS.AUTH_TOKEN, token)
    get().checkAuth()
  },

  logout: () => {
    storageService.remove(STORAGE_KEYS.AUTH_TOKEN)
    set({ user: null, isAuthenticated: false })
  },

  setUser: (user: User | null) => {
    set({ user, isAuthenticated: !!user })
  },
}))

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
  login: () => Promise<void>
  logout: () => void
  setUser: (user: User | null) => void
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,

  checkAuth: async () => {
    try {
      const userData = await apiService.checkAuth()
      if (userData) {
        set({ user: userData, isAuthenticated: true })
        storageService.set(STORAGE_KEYS.ANON_REGISTERED, true)
      } else {
        set({ user: null, isAuthenticated: false })
        storageService.remove(STORAGE_KEYS.ANON_REGISTERED)
      }
    } catch (error) {
      console.error('Auth check failed:', error)
      storageService.remove(STORAGE_KEYS.AUTH_TOKEN)
      set({ user: null, isAuthenticated: false })
      storageService.remove(STORAGE_KEYS.ANON_REGISTERED)
    } finally {
      set({ isLoading: false })
    }
  },

  login: async () => {
    await get().checkAuth()

    // If authenticated, migrate any anon sessions on the client side
    const { user, isAuthenticated } = get()
    if (isAuthenticated && user) {
      const anonId = storageService.get<string>(STORAGE_KEYS.ANON_USER_ID)
      const alreadyMigrated = storageService.get<boolean>(STORAGE_KEYS.ANON_REGISTERED)
      if (anonId && !alreadyMigrated) {
        try {
          await apiService.migrateAnonymousUser(anonId)
          storageService.set(STORAGE_KEYS.ANON_REGISTERED, true)
        } catch (err) {
          console.warn('Anonymous migration failed', err)
        }
      }
    }
  },

  logout: () => {
    storageService.remove(STORAGE_KEYS.AUTH_TOKEN)
    storageService.remove(STORAGE_KEYS.ANON_REGISTERED)
    apiService.logout().catch(err => console.error('Logout failed:', err))
    set({ user: null, isAuthenticated: false })
    // Hard reload to clear any in-memory state and start fresh
    window.location.reload()
  },

  setUser: (user: User | null) => {
    set({ user, isAuthenticated: !!user })
  },
}))

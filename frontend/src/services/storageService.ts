// LocalStorage service for persistent data

class StorageService {
  get<T>(key: string, defaultValue?: T): T | null {
    try {
      const item = localStorage.getItem(key)
      return item ? JSON.parse(item) : defaultValue ?? null
    } catch (error) {
      console.error(`Error reading from localStorage: ${key}`, error)
      return defaultValue ?? null
    }
  }

  set<T>(key: string, value: T): void {
    try {
      localStorage.setItem(key, JSON.stringify(value))
    } catch (error) {
      console.error(`Error writing to localStorage: ${key}`, error)
    }
  }

  remove(key: string): void {
    try {
      localStorage.removeItem(key)
    } catch (error) {
      console.error(`Error removing from localStorage: ${key}`, error)
    }
  }

  clear(): void {
    try {
      localStorage.clear()
    } catch (error) {
      console.error('Error clearing localStorage', error)
    }
  }
}

export const storageService = new StorageService()

// Storage keys
export const STORAGE_KEYS = {
  AUTH_TOKEN: 'creo_auth_token',
  ANON_USER_ID: 'creo_anon_user_id',
  ANON_REGISTERED: 'creo_anon_user_registered',
  SESSIONS: 'creo_sessions',
} as const

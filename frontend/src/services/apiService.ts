// API service for backend communication
import { storageService, STORAGE_KEYS } from './storageService'
import type { User, Suggestion, Session as SessionType } from '../types'

class ApiService {
  private getAuthHeaders(): HeadersInit {
    const token = storageService.get<string>(STORAGE_KEYS.AUTH_TOKEN)
    return token ? { Authorization: `Bearer ${token}` } : {}
  }

  async fetch<T>(url: string, options: RequestInit = {}): Promise<T> {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...this.getAuthHeaders(),
        ...options.headers,
      },
    })

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`)
    }

    return response.json()
  }

  // Health check
  async checkHealth(): Promise<{ status: string; agent?: string }> {
    return this.fetch('/health')
  }

  // Auth endpoints
  async checkAuth(): Promise<User | null> {
    try {
      return await this.fetch('/api/auth/me')
    } catch {
      return null
    }
  }

  // Session endpoints
  async getSessions(userId: string): Promise<SessionType[]> {
    const response = await this.fetch<{ sessions: Array<{ id: string; title: string; timestamp: string }> }>(`/api/sessions?user_id=${userId}`)
    // Convert backend response to frontend Session type
    return response.sessions.map(s => ({
      id: s.id,
      title: s.title,
      timestamp: new Date(s.timestamp).getTime()
    }))
  }

  async createSession(
    message: string,
    userId: string,
    sessionId?: string
  ): Promise<{ session_id: string; user_id: string }> {
    return this.fetch('/api/sessions', {
      method: 'POST',
      body: JSON.stringify({
        message,
        user_id: userId,
        session_id: sessionId,
      }),
    })
  }

  async getSessionMessages(sessionId: string): Promise<{
    messages: Array<{ role: string; content: string }>
    session_id: string
  }> {
    return this.fetch(`/api/sessions/${sessionId}/messages`)
  }

  // Suggestions endpoint
  async getSuggestions(userId?: string): Promise<{
    welcome_message: string
    suggestions: Suggestion[]
  }> {
    return this.fetch('/api/suggestions', {
      method: 'POST',
      body: JSON.stringify({
        user_id: userId,
      }),
    })
  }

  // User migration
  async migrateAnonymousUser(anonymousUserId: string): Promise<void> {
    return this.fetch('/api/users/migrate', {
      method: 'POST',
      body: JSON.stringify({ anonymous_user_id: anonymousUserId }),
    })
  }
}

export const apiService = new ApiService()

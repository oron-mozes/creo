// API service for backend communication
import type { User, Suggestion, Session as SessionType } from '../types'

class ApiService {
  async fetch<T>(url: string, options: RequestInit = {}): Promise<T> {
    const response = await fetch(url, {
      ...options,
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
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
      const res = await this.fetch<{ authenticated: boolean; user: User | null }>('/api/auth/check')
      return res.authenticated ? res.user : null
    } catch {
      return null
    }
  }

  async getAuthToken(): Promise<string | null> {
    try {
      const res = await this.fetch<{ token: string }>('/api/auth/token')
      return res.token
    } catch {
      return null
    }
  }

  async logout(): Promise<void> {
    await this.fetch('/api/auth/logout', { method: 'POST' })
  }

  async devLogin(): Promise<void> {
    await this.fetch('/api/auth/dev/login', { method: 'POST' })
  }

  // Session endpoints
  async getSessions(userId: string): Promise<SessionType[]> {
    try {
      const response = await this.fetch<{ sessions: Array<{ id: string; title: string; timestamp: string }> }>(
        `/api/sessions?user_id=${userId}`
      )
      // Convert backend response to frontend Session type
      return response.sessions.map(s => ({
        id: s.id,
        title: s.title,
        timestamp: new Date(s.timestamp).getTime()
      }))
    } catch (err) {
      // If blocked due to auth (e.g., anon id linked to user), return empty list
      console.warn('Session fetch blocked or failed', err)
      return []
    }
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

  async getCreators(sessionId: string): Promise<Array<{
    id: string
    name: string
    platform?: string
    category?: string
    email?: string
    status?: string
    response?: string | null
    profile_url?: string
  }>> {
    const res = await this.fetch<{ creators: any[] }>(`/api/creators?session_id=${encodeURIComponent(sessionId)}`)
    return res.creators || []
  }
}

export const apiService = new ApiService()

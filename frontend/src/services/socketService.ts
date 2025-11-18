// Socket.IO service for real-time communication
import { io, Socket } from 'socket.io-client'
import type { SocketEvents } from '../types'

class SocketService {
  private socket: Socket | null = null

  connect(): Socket {
    if (this.socket?.connected) {
      return this.socket
    }

    // In development, use relative path which will be proxied by Vite
    // In production, use the backend URL from environment variable
    const socketUrl = import.meta.env.DEV
      ? '/' // Use Vite proxy in dev mode
      : (import.meta.env.VITE_API_URL || 'http://localhost:8000')

    console.log('[SocketService] Connecting to:', socketUrl)
    this.socket = io(socketUrl, {
      path: '/socket.io',
      transports: ['websocket', 'polling'],
    })
    return this.socket
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }
  }

  getSocket(): Socket | null {
    return this.socket
  }

  isConnected(): boolean {
    return this.socket?.connected ?? false
  }

  // Emit events
  emit<K extends keyof SocketEvents>(
    event: K,
    data: SocketEvents[K]
  ): void {
    if (!this.socket) {
      console.error('Socket not connected')
      return
    }
    this.socket.emit(event as string, data)
  }

  // Listen to events
  on<K extends keyof SocketEvents>(
    event: K,
    callback: (data: SocketEvents[K]) => void
  ): void {
    if (!this.socket) {
      console.error('Socket not connected')
      return
    }
    this.socket.on(event as string, callback)
  }

  // Remove event listener
  off<K extends keyof SocketEvents>(
    event: K,
    callback?: (data: SocketEvents[K]) => void
  ): void {
    if (!this.socket) return
    if (callback) {
      this.socket.off(event as string, callback)
    } else {
      this.socket.off(event as string)
    }
  }

  // Convenience methods
  joinSession(sessionId: string, token: string | null, userId: string): void {
    this.emit('join_session', { session_id: sessionId, token, user_id: userId })
  }

  sendMessage(message: string, sessionId: string, token: string | null, userId: string): void {
    this.emit('send_message', { message, session_id: sessionId, token, user_id: userId })
  }
}

export const socketService = new SocketService()

// Common types used across the application

export interface User {
  user_id: string
  email: string
  name: string
  picture?: string
  isAnonymous?: boolean
}

export interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp?: number
  messageId?: string
  widget?: string
  auth_required?: boolean
}

export interface Session {
  id: string
  title: string
  timestamp: number
}

export interface BusinessCard {
  name: string
  website?: string
  social_links?: string
  location: string
  service_type: string
}

export interface Suggestion {
  text: string
  icon?: string
}

export interface ChatHistory {
  messages: Message[]
  session_id: string
}

export interface SocketEvents {
  // Emit events
  join_session: {
    session_id: string
    token: string | null
    user_id: string
  }
  send_message: {
    message: string
    session_id: string
    token: string | null
    user_id: string
  }

  // Listen events
  connect: void
  disconnect: void
  chat_history: ChatHistory
  agent_thinking: { session_id: string }
  message_chunk: {
    chunk: string
    session_id: string
    message_id: string
  }
  message_complete: {
    message: string
    session_id: string
    message_id: string
    business_card?: BusinessCard
    is_error?: boolean
    auth_required?: boolean
    widget?: string
  }
  error: { error: string }
}

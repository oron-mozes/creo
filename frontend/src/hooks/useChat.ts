// useChat hook - integrates socket events with chat store
import { useEffect, useCallback, useRef } from 'react'
import { useSocket } from './useSocket'
import { useChatStore } from '../stores/useChatStore'
import { useSessionStore } from '../stores/useSessionStore'
import { apiService } from '../services/apiService'
import { storageService, STORAGE_KEYS } from '../services/storageService'
import type { Message, BusinessCard } from '../types'

interface UseChatOptions {
  sessionId: string
  userId: string
  onNewMessage?: (message: Message) => void
}

export function useChat({ sessionId, userId, onNewMessage }: UseChatOptions) {
  const { isConnected, on, off, emit } = useSocket()
  const {
    setCurrentSession,
    addMessage,
    setMessages,
    setLoading,
    setStreamingMessage,
    setBusinessCard,
    setError,
    getSessionState,
  } = useChatStore()

  // Get current session state
  const sessionState = getSessionState(sessionId)

  // Use ref for callback to avoid recreating effect
  const onNewMessageRef = useRef(onNewMessage)
  useEffect(() => {
    onNewMessageRef.current = onNewMessage
  }, [onNewMessage])

  // Track if we've already joined this session
  const hasJoinedRef = useRef(false)

  // Initialize session when component mounts
  useEffect(() => {
    setCurrentSession(sessionId)
    hasJoinedRef.current = false // Reset on session change
  }, [sessionId, setCurrentSession])

  // Join session when socket connects - ONLY ONCE per connection/session
  useEffect(() => {
    if (!isConnected || !sessionId || hasJoinedRef.current) return

    console.log('[useChat] Joining session:', sessionId)
    hasJoinedRef.current = true

    const token = storageService.get<string>(STORAGE_KEYS.AUTH_TOKEN)
    emit('join_session', {
      session_id: sessionId,
      token,
      user_id: userId,
    })

    // Handle chat history
    const handleChatHistory = (data: { messages: Message[]; session_id: string }) => {
      setMessages(data.session_id, data.messages)
    }

    // Handle agent thinking (loading state)
    const handleAgentThinking = () => {
      setLoading(sessionId, true)
      setStreamingMessage(sessionId, '', false) // Clear streaming message
    }

    // Handle message chunks (streaming)
    const handleMessageChunk = (data: { chunk: string }) => {
      setStreamingMessage(sessionId, data.chunk, true) // Append chunk
    }

    // Handle message complete
    const handleMessageComplete = (data: {
      message: string
      business_card?: BusinessCard
      is_error?: boolean
    }) => {
      setLoading(sessionId, false)

      const newMessage: Message = {
        role: 'assistant',
        content: data.message,
        timestamp: Date.now(),
      }

      addMessage(sessionId, newMessage)
      setStreamingMessage(sessionId, '', false) // Clear streaming message

      if (data.business_card) {
        setBusinessCard(sessionId, data.business_card)
      }

      if (data.is_error) {
        setError(sessionId, data.message)
      }

      onNewMessageRef.current?.(newMessage)
    }

    // Handle errors
    const handleError = (data: { error: string }) => {
      setLoading(sessionId, false)
      setError(sessionId, data.error)
    }

    on('chat_history', handleChatHistory)
    on('agent_thinking', handleAgentThinking)
    on('message_chunk', handleMessageChunk)
    on('message_complete', handleMessageComplete)
    on('error', handleError)

    return () => {
      off('chat_history', handleChatHistory)
      off('agent_thinking', handleAgentThinking)
      off('message_chunk', handleMessageChunk)
      off('message_complete', handleMessageComplete)
      off('error', handleError)
    }
  }, [isConnected, sessionId, userId, on, off, emit, setMessages, setLoading, setStreamingMessage, setBusinessCard, setError, addMessage])

  const sendMessage = useCallback(async (message: string) => {
    if (!message.trim() || !sessionId) return

    // Add user message to store immediately
    const userMessage: Message = {
      role: 'user',
      content: message,
      timestamp: Date.now(),
    }
    addMessage(sessionId, userMessage)
    setError(sessionId, null)

    // Check if this is first message (no messages in session yet)
    const isFirstMessage = sessionState.messages.length === 0

    if (isFirstMessage) {
      // Create session via API first (this just stores the session)
      try {
        await apiService.createSession(message, userId, sessionId)

        // Save session to session store
        const { addSession } = useSessionStore.getState()
        addSession({
          id: sessionId,
          title: message.slice(0, 50), // Use first 50 chars as title
          timestamp: Date.now(),
        })

        // Now send via Socket.IO to trigger the orchestrator
        const token = storageService.get<string>(STORAGE_KEYS.AUTH_TOKEN)
        emit('send_message', {
          message,
          session_id: sessionId,
          token,
          user_id: userId,
        })
      } catch (err) {
        setError(sessionId, 'Failed to create session')
        console.error(err)
        return
      }
    } else {
      // Send via Socket.IO for subsequent messages
      const token = storageService.get<string>(STORAGE_KEYS.AUTH_TOKEN)
      emit('send_message', {
        message,
        session_id: sessionId,
        token,
        user_id: userId,
      })
    }

    setLoading(sessionId, true)
  }, [sessionId, userId, emit, sessionState.messages.length, addMessage, setError, setLoading])

  const clearError = useCallback(() => {
    setError(sessionId, null)
  }, [sessionId, setError])

  return {
    messages: sessionState.messages,
    isLoading: sessionState.isLoading,
    streamingMessage: sessionState.streamingMessage,
    businessCard: sessionState.businessCard,
    error: sessionState.error,
    sendMessage,
    clearError,
    isConnected,
  }
}

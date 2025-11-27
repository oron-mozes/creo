// ChatView page - main chat interface
import React, { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useChat } from '../hooks/useChat'
import { useUser } from '../hooks/useUser'
import { useSessionStore } from '../stores/useSessionStore'
import { useAuth } from '../hooks/useAuth'
import { Header } from '../components/layout'
import { Sidebar } from '../components/layout'
import { MessageList, MessageInput, BusinessCardDisplay } from '../components/chat'
import { Spinner } from '../components/ui'
import { apiService } from '../services/apiService'
import { AuthModal } from '../components/auth'
import { AuthGateNotice } from '../components/chat/AuthGateNotice'

export function ChatView() {
  const navigate = useNavigate()
  const { userId } = useUser()
  const { isAuthenticated } = useAuth()
  const { activeSessionId, setActiveSession, fetchSessions } = useSessionStore()
  const [showAuthModal, setShowAuthModal] = useState(false)
  const [showAuthGate, setShowAuthGate] = useState(false)
  const [hasShownSoftGate, setHasShownSoftGate] = useState(false)
  const [pendingMessage, setPendingMessage] = useState<string | null>(null)
  const lastUserMessageRef = useRef<string | null>(null)

  // Initialize: Get session from URL or use active session
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const urlSessionId = params.get('session')

    if (urlSessionId) {
      setActiveSession(urlSessionId)
    } else if (activeSessionId) {
      // Update URL to reflect active session
      navigate(`/chat?session=${activeSessionId}`, { replace: true })
    } else {
      // No session in URL or store - create new one
      const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      setActiveSession(newSessionId)
      navigate(`/chat?session=${newSessionId}`, { replace: true })
    }

    // Fetch sessions on mount
    fetchSessions(userId)
  }, []) // Only run on mount

  // Update active session when URL changes
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const urlSessionId = params.get('session')
    if (urlSessionId && urlSessionId !== activeSessionId) {
      setActiveSession(urlSessionId)
    }
  }, [window.location.search])

  // Only use chat hook if we have an active session
  const {
    messages,
    isLoading,
    streamingMessage,
    businessCard,
    error,
    sendMessage,
    clearError,
    isConnected,
  } = useChat({
    sessionId: activeSessionId || '',
    userId,
    onAuthRequired: () => {
      setShowAuthGate(true)
      setShowAuthModal(true)
      setPendingMessage(lastUserMessageRef.current)
    }
  })

  // Show auth gate when outreach is blocked or when user explicitly requests auth
  useEffect(() => {
    if (!isAuthenticated && error && error.toLowerCase().includes('authentication required')) {
      setShowAuthGate(true)
    }
  }, [isAuthenticated, error])

  // Soft prompt: once the user has given enough info (business card present + a few messages), nudge login
  useEffect(() => {
    if (hasShownSoftGate || isAuthenticated) return

    // As soon as we have a saved business card, prompt sign-in so we can run outreach later
    if (businessCard) {
      setShowAuthGate(true)
      setHasShownSoftGate(true)
      return
    }

    // Fallback: after a few messages, nudge login
    if (messages.length >= 4) {
      setShowAuthGate(true)
      setHasShownSoftGate(true)
    }
  }, [businessCard, messages.length, isAuthenticated, hasShownSoftGate])

  // Hard prompt when the assistant starts talking about creators/outreach while unauthenticated
  useEffect(() => {
    if (isAuthenticated || messages.length === 0) return
    const lastMessage = messages[messages.length - 1]
    if (lastMessage.role !== 'assistant') return
    const text = (lastMessage.content || '').toLowerCase()
    const shouldPrompt =
      text.includes('looking for creator') ||
      text.includes('start looking for') ||
      text.includes('outreach') ||
      text.includes('send email') ||
      text.includes('reach out') ||
      text.includes('find the perfect creator')
    if (shouldPrompt) {
      setShowAuthGate(true)
    }
  }, [messages, isAuthenticated])

  // Replay pending message after successful login
  useEffect(() => {
    if (isAuthenticated && pendingMessage) {
      sendMessage(pendingMessage)
      setPendingMessage(null)
      setShowAuthGate(false)
      setShowAuthModal(false)
    }
  }, [isAuthenticated, pendingMessage, sendMessage])

  const handleSendMessage = (msg: string) => {
    lastUserMessageRef.current = msg
    sendMessage(msg)
  }

  const handleNewChat = async () => {
    try {
      const res = await apiService.createSession('New chat', userId)
      setActiveSession(res.session_id)
      // Refresh past sessions list after creating a new one
      fetchSessions(userId)
      navigate(`/chat?session=${res.session_id}`)
    } catch (err) {
      console.error('Failed to create new session', err)
    }
  }

  const handleSelectSession = (selectedSessionId: string) => {
    setActiveSession(selectedSessionId)
    navigate(`/chat?session=${selectedSessionId}`)
  }

  if (!activeSessionId) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="text-center">
          <Spinner size="lg" />
          <p className="mt-4 text-gray-600">Loading session...</p>
        </div>
      </div>
    )
  }

  if (!isConnected) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="text-center">
          <Spinner size="lg" />
          <p className="mt-4 text-gray-600">Connecting to server...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-screen flex flex-col">
      <AuthModal open={showAuthModal} onClose={() => setShowAuthModal(false)} />
      <Header onNewChat={handleNewChat} onShowAuth={() => setShowAuthModal(true)} />

      <div className="flex flex-1 min-h-0 overflow-hidden">
        <Sidebar currentSessionId={sessionId} onSelectSession={handleSelectSession} />

        <main className="flex-1 min-h-0 flex flex-col overflow-hidden">
          {/* Error Banner */}
          {error && (
            <div className="bg-red-50 border-b border-red-200 px-4 py-3 flex items-center justify-between">
              <p className="text-red-800">{error}</p>
              <button
                onClick={clearError}
                className="text-red-600 hover:text-red-800 font-medium"
              >
                Dismiss
              </button>
            </div>
          )}

          {/* Auth gate for outreach */}
          {showAuthGate && !isAuthenticated && (
            <div className="px-4 pt-4">
              <AuthGateNotice
                onSignIn={() => setShowAuthModal(true)}
                onDismiss={() => setShowAuthGate(false)}
                message="We need your email to send outreach and notify you about creator replies. Please sign in to continue."
              />
            </div>
          )}

          {/* Messages */}
          <MessageList
            messages={messages}
            streamingMessage={streamingMessage}
            isLoading={isLoading}
          />

          {/* Business Card */}
          {businessCard && (
            <div className="px-4 pb-4">
              <BusinessCardDisplay businessCard={businessCard} />
            </div>
          )}

          {/* Message Input */}
          <MessageInput
            onSendMessage={handleSendMessage}
            disabled={isLoading}
            placeholder="Ask me to find a creator..."
          />
        </main>
      </div>
    </div>
  )
}

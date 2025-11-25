// ChatView page - main chat interface
import React, { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useChat } from '../hooks/useChat'
import { useUser } from '../hooks/useUser'
import { useSessionStore } from '../stores/useSessionStore'
import { Header } from '../components/layout'
import { Sidebar } from '../components/layout'
import { MessageList, MessageInput, BusinessCardDisplay } from '../components/chat'
import { Spinner } from '../components/ui'
import { apiService } from '../services/apiService'

export function ChatView() {
  const navigate = useNavigate()
  const { userId } = useUser()
  const { activeSessionId, setActiveSession, fetchSessions } = useSessionStore()

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
  })

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
      <Header onNewChat={handleNewChat} />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar currentSessionId={sessionId} onSelectSession={handleSelectSession} />

        <main className="flex-1 flex flex-col overflow-hidden">
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
            onSendMessage={sendMessage}
            disabled={isLoading}
            placeholder="Ask me to find a creator..."
          />
        </main>
      </div>
    </div>
  )
}

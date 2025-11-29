// HomePage - exact copy of app.html design
import React, { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useChat } from '../hooks/useChat'
import { useUser } from '../hooks/useUser'
import { useAuth } from '../hooks/useAuth'
import { useSessionStore } from '../stores/useSessionStore'
import { apiService } from '../services/apiService'
import { HomepageQuickStartCard } from '../components/layout/HomepageQuickStartCard'
import { ChatPastChatsCard } from '../components/layout/ChatPastChatsCard'
import { ChatHelpfulTipsCard } from '../components/layout/ChatHelpfulTipsCard'
import { MessageList, MessageInput, BusinessCardDisplay } from '../components/chat'
import { AuthModal } from '../components/auth'
import { storageService, STORAGE_KEYS } from '../services/storageService'

interface HomePageProps {
  initialShowAuthModal?: boolean
}

export function HomePage({ initialShowAuthModal = false }: HomePageProps) {
  const navigate = useNavigate()
  const { user, isAuthenticated, logout } = useAuth()
  const { userId, saveSession } = useUser()
  const { sessions, fetchSessions, setActiveSession } = useSessionStore()
  const [sessionId, setSessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`)
  const [welcomeText, setWelcomeText] = useState('')
  const [message, setMessage] = useState('')
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [showAuthModal, setShowAuthModal] = useState(initialShowAuthModal)
  const chatRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const sendButtonRef = useRef<HTMLButtonElement>(null)
  const chatBottomRef = useRef<HTMLDivElement>(null)
  const [isNearBottom, setIsNearBottom] = useState(true)
  const [fabNeedsAttention, setFabNeedsAttention] = useState(false)

  const {
    messages,
    isLoading,
    streamingMessage,
    sendMessage: sendChatMessage,
  } = useChat({
    sessionId,
    userId,
    onNewMessage: (msg) => {
      if (msg.role === 'assistant' && messages.length <= 2) {
        const firstUserMessage = messages.find(m => m.role === 'user')
        const title = firstUserMessage?.content.slice(0, 50) || 'New Chat'
        saveSession(sessionId, title)
      }
    },
  })

  const isAssistantStreaming = isLoading || !!streamingMessage

  // Load welcome message and suggestions
  useEffect(() => {
    const loadData = async () => {
      try {
        console.log('[HomePage] Fetching suggestions for user:', userId)
        const data = await apiService.getSuggestions(userId)
        console.log('[HomePage] Suggestions response:', data)
        // Type out welcome message
        const fullText = data.welcome_message
        let index = 0
        const interval = setInterval(() => {
          if (index <= fullText.length) {
            setWelcomeText(fullText.slice(0, index))
            index++
          } else {
            clearInterval(interval)
          }
        }, 30)
        
        const fetchedSuggestions = data.suggestions || []
        console.log('[HomePage] Parsed suggestions:', fetchedSuggestions)
        setSuggestions(fetchedSuggestions)
        // Cache suggestions for quick-start cards
        storageService.set(STORAGE_KEYS.SUGGESTIONS, fetchedSuggestions)
      } catch (error) {
        console.error('Failed to load suggestions:', error)
        setWelcomeText("Hi! I'm Creo, your AI assistant for finding the perfect creators and influencers. Tell me about your business and what you're looking for!")
      }
    }
    loadData()

    // Load past sessions
    fetchSessions(userId)
  }, [userId, fetchSessions])

  // Auto-grow textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px'

      if (sendButtonRef.current) {
        if (isAssistantStreaming || !message.trim()) {
          sendButtonRef.current.style.backgroundColor = 'rgba(0, 160, 235, 0.4)'
        } else {
          sendButtonRef.current.style.backgroundColor = 'rgb(0, 160, 235)'
        }
      }
    }
  }, [message, isAssistantStreaming])

  const scrollToChat = () => {
    if (chatRef.current) {
      chatRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
    if (textareaRef.current) {
      try {
        textareaRef.current.focus({ preventScroll: true })
      } catch {
        textareaRef.current.focus()
      }
    }
  }

  const handleSendMessage = () => {
    if (!message.trim() || isAssistantStreaming) return
    sendChatMessage(message)
    setMessage('')
    if (isNearBottom) {
      requestAnimationFrame(scrollToChatBottom)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const setQuickMessage = (text: string) => {
    setMessage(text)
    textareaRef.current?.focus()
  }

  const startFresh = async () => {
    try {
      await fetchSessions(userId)
    } catch (err) {
      console.error('Failed to refresh sessions before starting fresh', err)
    }
    window.location.reload()
  }

  const handleLoadSession = async (selectedSessionId: string) => {
    // Set as active session
    setActiveSession(selectedSessionId)
    setSessionId(selectedSessionId)

    // Scroll to chat
    chatRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const scrollToChatBottom = () => {
    if (chatBottomRef.current) {
      chatBottomRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' })
    }
    setFabNeedsAttention(false)
  }

  useEffect(() => {
    if (!messages.length) return
    const latest = messages[messages.length - 1]
    if (latest.role === 'user' && isNearBottom) {
      scrollToChatBottom()
      return
    }

    // If assistant replied and user isn't at bottom, nudge the FAB to show new content
    if (latest.role === 'assistant' && !isNearBottom) {
      setFabNeedsAttention(true)
    }
  }, [messages, isNearBottom])

  // Track scroll position to see if user is near the bottom
  useEffect(() => {
    const handleScroll = () => {
      const scrollY = window.scrollY
      const viewport = window.innerHeight
      const docHeight = document.documentElement.scrollHeight
      const distanceFromBottom = docHeight - (scrollY + viewport)
      const nearBottom = distanceFromBottom < 120
      setIsNearBottom(nearBottom)
      if (nearBottom) {
        setFabNeedsAttention(false)
      }
    }

    handleScroll()
    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <div className="min-h-screen bg-white">
      <AuthModal open={showAuthModal} onClose={() => setShowAuthModal(false)} />
      {/* Header */}
      <header className="border-b bg-white/95 backdrop-blur-sm sticky top-0 z-10">
        <div className="container mx-auto px-4 py-2">
          <div className="flex items-center justify-between">
            <a href="/" className="pl-2">
              <img src="/static/creo-logo-BesatB3H.png" alt="Creo" style={{ height: '3rem' }} />
            </a>

            <div className="pr-4 flex items-center gap-3">
              {messages.length > 0 && (
                <button
                  onClick={startFresh}
                  className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                  style={{ color: 'rgb(0, 0, 0)' }}
                  onMouseOver={(e) => { e.currentTarget.style.backgroundColor = 'rgb(0, 160, 235)'; e.currentTarget.style.color = 'white' }}
                  onMouseOut={(e) => { e.currentTarget.style.backgroundColor = 'transparent'; e.currentTarget.style.color = 'rgb(0, 0, 0)' }}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
                    <path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z"></path>
                    <path d="M20 3v4"></path>
                    <path d="M22 5h-4"></path>
                    <path d="M4 17v2"></path>
                    <path d="M5 18H3"></path>
                  </svg>
                  Start Fresh
                </button>
              )}

              {!isAuthenticated ? (
                <button
                  onClick={() => setShowAuthModal(true)}
                  className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                  style={{ color: 'rgb(0, 0, 0)', border: '1px solid rgba(0, 160, 235, 0.3)' }}
                  onMouseOver={(e) => { e.currentTarget.style.backgroundColor = 'rgb(0, 160, 235)'; e.currentTarget.style.color = 'white'; e.currentTarget.style.borderColor = 'rgb(0, 160, 235)' }}
                  onMouseOut={(e) => { e.currentTarget.style.backgroundColor = 'transparent'; e.currentTarget.style.color = 'rgb(0, 0, 0)'; e.currentTarget.style.borderColor = 'rgba(0, 160, 235, 0.3)' }}
                >
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
                  </svg>
                  Sign In
                </button>
              ) : (
                <div className="flex items-center gap-3">
                  <span className="text-sm font-medium text-gray-700">{user?.email}</span>
                  <button
                    onClick={logout}
                    className="flex items-center justify-center h-10 w-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 text-white font-semibold text-sm"
                  >
                    {user?.email?.charAt(0).toUpperCase()}
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br via-gray-50 to-purple-50" style={{ backgroundImage: 'linear-gradient(to bottom right, rgba(0, 160, 235, 0.05), rgb(249, 250, 251), rgb(250, 245, 255))' }}>
        <div className="container mx-auto px-6 py-20 md:py-28">
          <div className="grid lg:grid-cols-2 gap-16 items-center max-w-6xl mx-auto">
            {/* Left Column */}
            <div className="space-y-8 animate-fade-in">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium" style={{ backgroundColor: 'rgba(0, 160, 235, 0.1)', color: 'rgb(0, 160, 235)' }}>
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                </svg>
                Powered by Best-in-Class AI Agents
              </div>

              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold leading-tight text-gray-900">
                Bring the creator magic to your business
              </h1>

              <p className="text-xl md:text-2xl text-gray-700 leading-relaxed font-medium">
                You run the business. Creo brings the creator magic — our trusted AI agents handle every step: match, plan, launch, track.
              </p>

              <div className="space-y-3">
                {['No forms. No dashboards - just chat with Creo', 'Fully handle it all end to end: match, plan, launch, track', 'Safe, trusted AI agents verify every creator'].map((text, i) => (
                  <div key={i} className="flex items-center gap-3 text-gray-700">
                    <div className="flex h-9 w-9 items-center justify-center rounded-full" style={{ backgroundColor: 'rgba(0, 160, 235, 0.1)' }}>
                      <svg className="h-4 w-4" style={{ color: 'rgb(0, 160, 235)' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d={i === 0 ? "M5 13l4 4L19 7" : i === 1 ? "M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" : "M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"} />
                      </svg>
                    </div>
                    <span className="text-base">{text}</span>
                  </div>
                ))}
              </div>

              <button
                onClick={scrollToChat}
                data-testid="tell-us-button"
                className="inline-flex items-center justify-center gap-2 text-white text-lg px-8 py-4 rounded-full font-medium transition-colors animate-scale-in"
                style={{ backgroundColor: 'rgb(0, 160, 235)' }}
                onMouseOver={(e) => e.currentTarget.style.backgroundColor = 'rgb(0, 144, 211)'}
                onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'rgb(0, 160, 235)'}
              >
                Tell Us What You Need!
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                </svg>
              </button>
            </div>

            {/* Right Column - Video */}
            <div className="relative animate-fade-in" style={{ animationDelay: '0.2s' }}>
              <div className="relative rounded-3xl overflow-hidden shadow-2xl">
                <video className="w-full h-full object-cover" autoPlay loop muted playsInline>
                  <source src="/static/creo-teaser-CBjoFzhL.mp4" type="video/mp4" />
                </video>
              </div>
              <div className="absolute -bottom-4 -right-4 w-32 h-32 rounded-full blur-3xl opacity-50" style={{ backgroundColor: 'rgba(0, 160, 235, 0.2)' }}></div>
              <div className="absolute -top-4 -left-4 w-40 h-40 bg-purple-200 rounded-full blur-3xl opacity-50"></div>
            </div>
          </div>
        </div>

        {/* Scroll Indicator */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce">
          <svg className="h-6 w-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
        </div>
      </section>

      {/* Main Content */}
      <main ref={chatRef} className="container mx-auto px-6 py-12 md:py-16 max-w-6xl">
        <div className="grid lg:grid-cols-[2fr,1fr] gap-8">
          {/* Chat Area */}
          <div className="space-y-6">
            <div className="space-y-4">
              {/* Welcome Message */}
              {messages.length === 0 && (
                <div className="flex gap-4 p-5 rounded-3xl bg-white border border-gray-200 mr-12 md:mr-20 animate-fade-in">
                  <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-white" style={{ background: 'linear-gradient(to bottom right, rgb(0, 160, 235), rgb(0, 144, 211))' }}>
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <div className="flex-1 space-y-2">
                    <p className="text-sm font-medium text-gray-500">Creo Assistant</p>
                    <div className="text-base leading-relaxed" style={{ color: 'rgba(31, 41, 55, 0.9)' }}>
                      {welcomeText || (
                        <>
                          <span className="typing-dot"></span>
                          <span className="typing-dot"></span>
                          <span className="typing-dot"></span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Messages */}
              {messages.map((msg, i) => (
                <div key={i} className={`flex gap-4 p-5 rounded-3xl transition-all ${msg.role === 'user' ? 'ml-12 md:ml-20' : 'mr-12 md:mr-20'} mb-6`} style={msg.role === 'user' ? { backgroundColor: 'rgba(0, 160, 235, 0.05)' } : { backgroundColor: 'rgba(255, 255, 255, 0.8)', backdropFilter: 'blur(4px)', border: '1px solid rgba(229, 231, 235, 0.5)' }}>
                  <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-white" style={msg.role === 'user' ? { backgroundColor: 'rgb(0, 160, 235)', color: 'white' } : { background: 'linear-gradient(135deg, rgb(0, 160, 235), rgb(0, 144, 211))' }}>
                    {msg.role === 'user' ? (
                      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5">
                        <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"></path>
                        <circle cx="12" cy="7" r="4"></circle>
                      </svg>
                    ) : (
                      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                      </svg>
                    )}
                  </div>
                  <div className="flex-1 space-y-2">
                    <p className="text-sm font-medium" style={{ color: 'rgba(31, 41, 55, 0.7)' }}>{msg.role === 'user' ? 'You' : 'Creo Assistant'}</p>
                    <div className="text-base leading-relaxed whitespace-pre-wrap break-words" style={{ color: 'rgba(31, 41, 55, 0.9)' }}>{msg.content}</div>
                  </div>
                </div>
              ))}

              {/* Streaming Message */}
              {(isLoading || streamingMessage) && (
                <div className="flex gap-4 p-5 rounded-3xl transition-all mr-12 md:mr-20 mb-6" style={{ backgroundColor: 'rgba(255, 255, 255, 0.8)', backdropFilter: 'blur(4px)', border: '1px solid rgba(229, 231, 235, 0.5)' }}>
                  <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-white" style={{ background: 'linear-gradient(135deg, rgb(0, 160, 235), rgb(0, 144, 211))' }}>
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <div className="flex-1 space-y-2">
                    <p className="text-sm font-medium text-gray-500">Creo Assistant</p>
                    {streamingMessage ? (
                      <div className="text-base leading-relaxed" style={{ color: 'rgba(31, 41, 55, 0.9)' }}>{streamingMessage}</div>
                    ) : (
                      <div className="flex items-center gap-2">
                        <span className="typing-dot"></span>
                        <span className="typing-dot"></span>
                        <span className="typing-dot"></span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Input Area */}
            <div className="bg-white p-5 sticky bottom-4 shadow-2xl border border-gray-200 rounded-3xl animate-fade-in">
              <div className="flex gap-4 items-end">
                <textarea
                  ref={textareaRef}
                  data-testid="chat-textarea"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyDown={handleKeyDown}
                  rows={1}
                  className="flex-1 resize-none text-base border-0 focus:ring-0 focus:outline-none p-3 rounded-lg placeholder-ellipsis"
                  placeholder="Type here... (e.g., 'I have a small bakery in Manchester')"
                  style={{ maxHeight: '200px', overflowY: 'auto', overflowX: 'hidden' }}
                />
                <button
                  ref={sendButtonRef}
                  onClick={handleSendMessage}
                  disabled={isAssistantStreaming || !message.trim()}
                  className="inline-flex items-center justify-center gap-2 text-white px-6 py-4 rounded-2xl font-medium transition-all shrink-0"
                  style={{ backgroundColor: 'rgba(0, 160, 235, 0.4)' }}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5">
                    <path d="M14.536 21.686a.5.5 0 0 0 .937-.024l6.5-19a.496.496 0 0 0-.635-.635l-19 6.5a.5.5 0 0 0-.024.937l7.93 3.18a2 2 0 0 1 1.112 1.11z"></path>
                    <path d="m21.854 2.147-10.94 10.939"></path>
                  </svg>
                </button>
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="lg:sticky lg:top-24 space-y-6 h-fit">
            <ChatPastChatsCard onSelectSession={handleLoadSession} />
            <HomepageQuickStartCard onSelect={setQuickMessage} fallbackSuggestions={suggestions} />
            <ChatHelpfulTipsCard />
          </div>
        </div>
        <div ref={chatBottomRef} />
      </main>

      {/* Scroll to bottom FAB */}
      <button
        onClick={scrollToChatBottom}
        data-testid="scroll-to-bottom-fab"
        className={`fixed bottom-6 right-6 z-20 inline-flex h-12 w-12 items-center justify-center rounded-full shadow-lg transition-colors text-white ${fabNeedsAttention ? 'fab-attention' : ''}`}
        style={{ backgroundColor: 'rgb(0, 160, 235)' }}
        aria-label="Scroll to bottom"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={`h-6 w-6 fab-arrow`}>
          <path d="m7 13 5 5 5-5" />
          <path d="M12 18V6" />
        </svg>
      </button>
    </div>
  )
}

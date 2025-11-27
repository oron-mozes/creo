// MessageList component for displaying chat messages with auto-scroll
import React, { useEffect, useRef, useState } from 'react'
import { Message } from './Message'
import { StreamingMessage } from './StreamingMessage'
import type { Message as MessageType } from '../../types'

interface MessageListProps {
  messages: MessageType[]
  streamingMessage?: string
  isLoading?: boolean
  className?: string
}

export function MessageList({
  messages,
  streamingMessage = '',
  isLoading = false,
  className = '',
}: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const prevMessageCountRef = useRef(messages.length)
  const prevNearBottomRef = useRef(true)
  const [isNearBottom, setIsNearBottom] = useState(true)
  const [unreadCount, setUnreadCount] = useState(0)

  const scrollToBottom = (behavior: ScrollBehavior = 'auto') => {
    const container = containerRef.current
    if (!container) return
    container.scrollTo({
      top: container.scrollHeight,
      behavior,
    })
  }

  // Track whether user is near the bottom (within 120px)
  const handleScroll = () => {
    const container = containerRef.current
    if (!container) return
    const distanceFromBottom =
      container.scrollHeight - container.scrollTop - container.clientHeight
    const nearBottom = distanceFromBottom < 120
    setIsNearBottom(nearBottom)
    if (nearBottom) {
      setUnreadCount(0)
    }
  }

  // Auto-scroll to bottom when new messages arrive (only if we were near bottom before)
  useEffect(() => {
    const newMessages = messages.length - prevMessageCountRef.current
    const hasNewMessage = newMessages > 0
    const wasNearBottom = prevNearBottomRef.current

    if (hasNewMessage) {
      if (wasNearBottom) {
        scrollToBottom('auto')  // snap to bottom to avoid oscillation
      } else {
        setUnreadCount(count => count + newMessages)
      }
    } else if (streamingMessage && wasNearBottom) {
      scrollToBottom('auto')
    }

    prevMessageCountRef.current = messages.length
    prevNearBottomRef.current = isNearBottom
  }, [messages.length, streamingMessage, isNearBottom])

  // Listen to scroll position to determine "near bottom"
  useEffect(() => {
    const container = containerRef.current
    if (!container) return
    handleScroll()
    container.addEventListener('scroll', handleScroll)
    return () => container.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <div
      ref={containerRef}
      className={`relative flex-1 min-h-0 overflow-y-auto px-4 py-6 space-y-4 ${className}`}
    >
      {messages.length === 0 && !isLoading && !streamingMessage && (
        <div className="flex items-center justify-center h-full text-gray-400 text-center">
          <p>No messages yet. Start a conversation!</p>
        </div>
      )}

      {messages.map((message, index) => (
        <Message key={`${message.timestamp}-${index}`} message={message} />
      ))}

      {/* Show streaming message */}
      {(streamingMessage || isLoading) && (
        <StreamingMessage content={streamingMessage} isThinking={isLoading} />
      )}

      {/* Scroll anchor */}
      <div ref={messagesEndRef} />

      {/* Unread banner */}
      {!isNearBottom && unreadCount > 0 && (
        <div className="pointer-events-none absolute inset-x-0 bottom-4 flex justify-center">
          <button
            type="button"
            className="pointer-events-auto rounded-full bg-gray-900 text-white text-xs font-semibold px-4 py-2 shadow-lg hover:bg-gray-800 transition"
            onClick={() => {
              setUnreadCount(0)
              scrollToBottom()
            }}
          >
            {unreadCount} new message{unreadCount > 1 ? 's' : ''} — Jump to latest
          </button>
        </div>
      )}
    </div>
  )
}

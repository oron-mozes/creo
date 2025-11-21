// MessageList component for displaying chat messages with auto-scroll
import React, { useEffect, useRef } from 'react'
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

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingMessage])

  return (
    <div
      ref={containerRef}
      className={`flex-1 overflow-y-auto px-4 py-6 space-y-4 ${className}`}
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
    </div>
  )
}

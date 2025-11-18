// MessageInput component for sending messages
import React, { useState, KeyboardEvent } from 'react'

interface MessageInputProps {
  onSendMessage: (message: string) => void
  disabled?: boolean
  placeholder?: string
  className?: string
}

export function MessageInput({
  onSendMessage,
  disabled = false,
  placeholder = 'Type your message...',
  className = '',
}: MessageInputProps) {
  const [message, setMessage] = useState('')

  const handleSend = () => {
    if (!message.trim() || disabled) return

    onSendMessage(message.trim())
    setMessage('')
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Send on Enter, new line on Shift+Enter
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className={`mt-6 ${className}`}>
      <div className="flex gap-3 items-end p-4 bg-white rounded-3xl border border-gray-200 shadow-sm">
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          rows={1}
          className="flex-1 resize-none outline-none text-base text-gray-900 placeholder-gray-400 bg-transparent"
          style={{ maxHeight: '200px', overflowY: 'auto' }}
        />
        <button
          onClick={handleSend}
          disabled={disabled || !message.trim()}
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-primary to-primary-dark text-white transition-opacity disabled:opacity-50 hover:opacity-90"
        >
          <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
        </button>
      </div>
      <p className="text-xs text-gray-500 mt-2 text-center">
        Press Enter to send, Shift+Enter for new line
      </p>
    </div>
  )
}

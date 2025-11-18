// Message component for displaying user and assistant messages
import React from 'react'
import type { Message as MessageType } from '../../types'

interface MessageProps {
  message: MessageType
  className?: string
}

export function Message({ message, className = '' }: MessageProps) {
  const isUser = message.role === 'user'

  if (isUser) {
    // User message - right-aligned with light blue background
    return (
      <div className={`flex gap-4 p-5 rounded-3xl transition-all ml-12 md:ml-20 mb-6 ${className}`} style={{ backgroundColor: 'rgba(0, 160, 235, 0.05)' }}>
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full" style={{ backgroundColor: 'rgb(0, 160, 235)', color: 'white' }}>
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5">
            <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"></path>
            <circle cx="12" cy="7" r="4"></circle>
          </svg>
        </div>
        <div className="flex-1 space-y-2">
          <p className="text-sm font-medium" style={{ color: 'rgba(31, 41, 55, 0.7)' }}>You</p>
          <div className="text-base leading-relaxed whitespace-pre-wrap break-words" style={{ color: 'rgba(31, 41, 55, 0.9)' }}>
            {message.content}
          </div>
        </div>
      </div>
    )
  }

  // Assistant message - left-aligned with frosted glass effect
  return (
    <div className={`flex gap-4 p-5 rounded-3xl transition-all mr-12 md:mr-20 mb-6 ${className}`} style={{ backgroundColor: 'rgba(255, 255, 255, 0.8)', backdropFilter: 'blur(4px)', border: '1px solid rgba(229, 231, 235, 0.5)' }}>
      <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-white" style={{ background: 'linear-gradient(135deg, rgb(0, 160, 235), rgb(0, 144, 211))' }}>
        <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
      </div>
      <div className="flex-1 space-y-2">
        <p className="text-sm font-medium text-gray-500">Creo Assistant</p>
        <div className="text-base leading-relaxed whitespace-pre-wrap break-words" style={{ color: 'rgba(31, 41, 55, 0.9)' }}>
          {message.content}
        </div>
      </div>
    </div>
  )
}

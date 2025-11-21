// StreamingMessage component for displaying real-time streaming text
import React from 'react'
import { LoadingIndicator } from '../ui'

interface StreamingMessageProps {
  content: string
  isThinking?: boolean
  className?: string
}

export function StreamingMessage({ content, isThinking = false, className = '' }: StreamingMessageProps) {
  if (isThinking && !content) {
    return (
      <div className={`flex gap-4 p-5 rounded-3xl transition-all mr-12 md:mr-20 mb-6 ${className}`} style={{ backgroundColor: 'rgba(255, 255, 255, 0.8)', backdropFilter: 'blur(4px)', border: '1px solid rgba(229, 231, 235, 0.5)' }}>
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-white" style={{ background: 'linear-gradient(135deg, rgb(0, 160, 235), rgb(0, 144, 211))' }}>
          <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        </div>
        <div className="flex-1 space-y-2">
          <p className="text-sm font-medium text-gray-500">Creo Assistant</p>
          <LoadingIndicator />
        </div>
      </div>
    )
  }

  if (!content) return null

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
          {content}
          {/* Blinking cursor to indicate streaming */}
          <span className="inline-block w-0.5 h-5 ml-1 bg-gray-900 animate-pulse"></span>
        </div>
      </div>
    </div>
  )
}

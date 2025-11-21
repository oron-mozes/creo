// Loading indicator with typing animation
import React from 'react'

interface LoadingIndicatorProps {
  text?: string
  className?: string
}

export function LoadingIndicator({ text = 'Thinking', className = '' }: LoadingIndicatorProps) {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <span className="text-gray-600">{text}</span>
      <div className="flex gap-1">
        <div className="w-2 h-2 bg-gray-400 rounded-full animate-typing-dot" style={{ animationDelay: '0ms' }}></div>
        <div className="w-2 h-2 bg-gray-400 rounded-full animate-typing-dot" style={{ animationDelay: '200ms' }}></div>
        <div className="w-2 h-2 bg-gray-400 rounded-full animate-typing-dot" style={{ animationDelay: '400ms' }}></div>
      </div>
    </div>
  )
}

export function Spinner({ className = '', size = 'md' }: { className?: string; size?: 'sm' | 'md' | 'lg' }) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
  }

  return (
    <div className={`flex items-center justify-center ${className}`}>
      <svg
        className={`animate-spin ${sizeClasses[size]} text-primary`}
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        ></path>
      </svg>
    </div>
  )
}

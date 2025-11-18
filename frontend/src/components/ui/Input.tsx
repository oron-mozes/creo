// Reusable Input component (auto-growing textarea)
import React, { useRef, useEffect } from 'react'

interface InputProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  value: string
  onValueChange: (value: string) => void
  maxRows?: number
}

export function Input({
  value,
  onValueChange,
  maxRows = 5,
  className = '',
  ...props
}: InputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current
    if (!textarea) return

    // Reset height to get accurate scrollHeight
    textarea.style.height = 'auto'

    // Calculate new height
    const lineHeight = 24 // Approximate line height in pixels
    const maxHeight = lineHeight * maxRows
    const newHeight = Math.min(textarea.scrollHeight, maxHeight)

    textarea.style.height = `${newHeight}px`
  }, [value, maxRows])

  return (
    <textarea
      ref={textareaRef}
      value={value}
      onChange={(e) => onValueChange(e.target.value)}
      className={`w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent resize-none ${className}`}
      rows={1}
      {...props}
    />
  )
}

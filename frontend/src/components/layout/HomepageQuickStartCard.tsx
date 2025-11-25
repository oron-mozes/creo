import React, { useEffect, useState } from 'react'
import { storageService, STORAGE_KEYS } from '../../services/storageService'

type Props = {
  onSelect: (text: string) => void
  fallbackSuggestions?: string[]
}

const DEFAULTS = [
  'I have a local coffee shop',
  'I sell handmade jewelry online',
  'I run a small gym',
  'I own a boutique hotel',
]

export function HomepageQuickStartCard({ onSelect, fallbackSuggestions = DEFAULTS }: Props) {
  const [suggestions, setSuggestions] = useState<string[]>(fallbackSuggestions)

  useEffect(() => {
    // Try to load cached suggestions from storage
    const cached = storageService.get<string[]>(STORAGE_KEYS.SUGGESTIONS, [])
    if (cached && cached.length) {
      setSuggestions(cached)
    }
  }, [])

  return (
    <div className="bg-white p-6 border border-gray-200 rounded-3xl animate-fade-in">
      <h3 className="font-semibold mb-5 flex items-center gap-2 text-lg">
        <svg className="h-5 w-5" style={{ color: 'rgb(0, 160, 235)' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
        </svg>
        Quick Start
      </h3>
      <p className="text-sm text-gray-500 mb-4">Click to try:</p>
      <div className="space-y-3">
        {suggestions.length > 0 ? suggestions.map((suggestion, i) => (
          <button
            key={i}
            onClick={() => onSelect(suggestion)}
            className="w-full text-left p-4 text-base rounded-2xl"
            style={{ appearance: 'button', backgroundColor: 'rgb(255, 255, 255)', border: '1px solid rgb(229, 231, 235)', borderRadius: '16px', transition: 'all 0.2s' }}
            onMouseOver={(e) => { e.currentTarget.style.backgroundColor = 'rgba(0, 160, 235, 0.05)'; e.currentTarget.style.borderColor = 'rgba(0, 160, 235, 0.3)' }}
            onMouseOut={(e) => { e.currentTarget.style.backgroundColor = 'rgb(255, 255, 255)'; e.currentTarget.style.borderColor = 'rgb(229, 231, 235)' }}
          >
            💬 {suggestion}
          </button>
        )) : (
          <div className="text-sm text-gray-400">Loading suggestions...</div>
        )}
      </div>
    </div>
  )
}

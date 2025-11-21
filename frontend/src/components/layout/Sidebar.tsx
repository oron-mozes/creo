// Sidebar component for displaying session history
import React from 'react'
import { useSessionStore } from '../../stores/useSessionStore'
import { Button } from '../ui'
import type { Session } from '../../types'

interface SidebarProps {
  onSelectSession?: (sessionId: string) => void
  currentSessionId?: string
  className?: string
}

export function Sidebar({ onSelectSession, currentSessionId, className = '' }: SidebarProps) {
  const { sessions, clearSessions } = useSessionStore()

  const handleSessionClick = (session: Session) => {
    onSelectSession?.(session.id)
  }

  return (
    <aside className={`w-64 bg-gray-50 border-r border-gray-200 flex flex-col ${className}`}>
      {/* Sidebar Header */}
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">Chat History</h2>
      </div>

      {/* Session List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {sessions.length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-8">No previous chats</p>
        ) : (
          sessions.map((session) => (
            <button
              key={session.id}
              onClick={() => handleSessionClick(session)}
              className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                currentSessionId === session.id
                  ? 'bg-primary text-white'
                  : 'bg-white text-gray-900 hover:bg-gray-100'
              }`}
            >
              <p className="font-medium text-sm truncate">{session.title}</p>
              <p
                className={`text-xs mt-1 ${
                  currentSessionId === session.id ? 'text-blue-100' : 'text-gray-500'
                }`}
              >
                {new Date(session.timestamp).toLocaleDateString()}
              </p>
            </button>
          ))
        )}
      </div>

      {/* Sidebar Footer */}
      {sessions.length > 0 && (
        <div className="p-4 border-t border-gray-200">
          <Button variant="ghost" size="sm" onClick={clearSessions} className="w-full">
            Clear History
          </Button>
        </div>
      )}
    </aside>
  )
}

import React, { useEffect } from 'react'
import { useSessionStore } from '../../stores/useSessionStore'
import { useUser } from '../../hooks/useUser'

type Props = {
  onSelectSession: (sessionId: string) => void
}

export function ChatPastChatsCard({ onSelectSession }: Props) {
  const { userId } = useUser()
  const { sessions, isLoadingSessions, fetchSessions } = useSessionStore()

  useEffect(() => {
    if (userId) {
      fetchSessions(userId)
    }
  }, [userId, fetchSessions])

  if (isLoadingSessions) {
    return (
      <div className="bg-white p-6 border border-gray-200 rounded-3xl shadow-sm animate-fade-in">
        <div className="text-sm text-gray-500">Loading past chats...</div>
      </div>
    )
  }

  if (!sessions.length) return null

  return (
    <div className="bg-white p-6 border border-gray-200 rounded-3xl animate-fade-in">
      <h3 className="font-semibold mb-5 flex items-center gap-2 text-lg text-gray-900">
        <svg className="h-5 w-5" style={{ color: 'rgb(0, 160, 235)' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
        Past Chats
      </h3>
      <p className="text-sm text-gray-500 mb-4">Click to continue:</p>
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {sessions.slice(0, 10).map((session) => (
          <button
            key={session.id}
            onClick={() => onSelectSession(session.id)}
            className="w-full text-left p-4 text-base rounded-2xl border border-gray-200 bg-white transition-colors"
            onMouseOver={(e) => {
              e.currentTarget.style.backgroundColor = 'rgba(0, 160, 235, 0.05)'
              e.currentTarget.style.borderColor = 'rgba(0, 160, 235, 0.3)'
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.backgroundColor = 'rgb(255, 255, 255)'
              e.currentTarget.style.borderColor = 'rgb(229, 231, 235)'
            }}
          >
            <div className="font-medium truncate">💬 {session.title}</div>
            <div className="text-xs mt-1" style={{ color: '#9CA3AF' }}>
              {new Date(session.timestamp).toLocaleDateString()}
            </div>
            <div className="mt-2 flex items-center gap-2 text-xs text-blue-600">
              <a
                href={`/creators?session_id=${session.id}`}
                className="inline-flex items-center gap-1 hover:underline"
                onClick={(e) => e.stopPropagation()}
              >
                <span role="img" aria-label="creators">👥</span>
                View creators
              </a>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}

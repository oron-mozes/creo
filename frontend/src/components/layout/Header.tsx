// Header component with logo and user profile
import React from 'react'
import { useAuth } from '../../hooks/useAuth'
import { Button } from '../ui'

interface HeaderProps {
  onNewChat?: () => void
  className?: string
  onShowAuth?: () => void
}

export function Header({ onNewChat, className = '', onShowAuth }: HeaderProps) {
  const { user, isAuthenticated, logout } = useAuth()

  return (
    <header className={`bg-white border-b border-gray-200 px-6 py-4 ${className}`}>
      <div className="flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center text-white font-bold text-xl">
            C
          </div>
          <h1 className="text-xl font-bold text-gray-900">Creator Finder</h1>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-4">
          {onNewChat && (
            <Button variant="secondary" size="sm" onClick={onNewChat}>
              New Chat
            </Button>
          )}

          {isAuthenticated && user ? (
            <div className="flex items-center gap-3">
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900">
                  {user.name || user.email}
                </p>
                <p className="text-xs text-gray-500">{user.email}</p>
              </div>
              {user.picture ? (
                <img
                  src={user.picture}
                  alt={user.name || user.email}
                  className="h-10 w-10 rounded-full object-cover border border-gray-200"
                />
              ) : (
                <div className="h-10 w-10 rounded-full bg-gray-100 border border-gray-200 flex items-center justify-center text-sm font-semibold text-gray-700">
                  {(user.name || user.email || '?')
                    .split(' ')
                    .map(part => part[0])
                    .join('')
                    .toUpperCase()
                    .slice(0, 2)}
                </div>
              )}
              <Button variant="ghost" size="sm" onClick={logout}>
                Logout
              </Button>
            </div>
          ) : (
            <Button variant="primary" size="sm" onClick={onShowAuth}>
              Sign In
            </Button>
          )}
        </div>
      </div>
    </header>
  )
}

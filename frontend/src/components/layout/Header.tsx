// Header component with logo and user profile
import React from 'react'
import { useAuth } from '../../hooks/useAuth'
import { Button } from '../ui'

interface HeaderProps {
  onNewChat?: () => void
  className?: string
}

export function Header({ onNewChat, className = '' }: HeaderProps) {
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
                <p className="text-sm font-medium text-gray-900">{user.email}</p>
                <p className="text-xs text-gray-500">
                  {user.is_anonymous ? 'Anonymous' : 'Authenticated'}
                </p>
              </div>
              <Button variant="ghost" size="sm" onClick={logout}>
                Logout
              </Button>
            </div>
          ) : (
            <Button variant="primary" size="sm">
              Sign In
            </Button>
          )}
        </div>
      </div>
    </header>
  )
}

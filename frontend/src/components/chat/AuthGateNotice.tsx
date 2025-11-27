import React from 'react'
import { Button } from '../ui'

interface AuthGateNoticeProps {
  onSignIn: () => void
  onDismiss?: () => void
  message?: string
}

export function AuthGateNotice({
  onSignIn,
  onDismiss,
  message = 'Please sign in to contact creators and send outreach emails.',
}: AuthGateNoticeProps) {
  return (
    <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 flex flex-col gap-3 text-sm text-amber-900 shadow-sm">
      <div className="flex items-start gap-2">
        <span className="text-lg">🔒</span>
        <div className="flex-1">
          <p className="font-semibold text-amber-900">Sign in required for outreach</p>
          <p className="text-amber-800">{message}</p>
        </div>
      </div>
      <div className="flex gap-2">
        <Button variant="primary" size="sm" className="flex-1" onClick={onSignIn}>
          Continue with Google
        </Button>
        {onDismiss && (
          <Button variant="ghost" size="sm" onClick={onDismiss}>
            Not now
          </Button>
        )}
      </div>
    </div>
  )
}

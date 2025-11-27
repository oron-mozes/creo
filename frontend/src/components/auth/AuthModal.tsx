import React from 'react'
import { Button } from '../ui'

interface AuthModalProps {
  open: boolean
  onClose: () => void
}

export function AuthModal({ open, onClose }: AuthModalProps) {
  if (!open) return null

  const handleGoogleLogin = () => {
    const returnUrl = window.location.href
    window.location.href = `/api/auth/login/google?return_url=${encodeURIComponent(returnUrl)}`
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <div className="w-full max-w-md rounded-2xl bg-white shadow-2xl border border-gray-200 p-6 relative">
        <button
          onClick={onClose}
          className="absolute right-3 top-3 text-gray-400 hover:text-gray-600"
          aria-label="Close"
        >
          ✕
        </button>
        <div className="flex flex-col items-center text-center space-y-4">
          <div className="w-14 h-14 rounded-full bg-gradient-to-br from-sky-500 to-purple-500 flex items-center justify-center text-white text-2xl font-bold">
            G
          </div>
          <div className="space-y-1">
            <h2 className="text-xl font-semibold text-gray-900">Sign in to continue</h2>
            <p className="text-sm text-gray-600">
              Use Google to secure your sessions and unlock outreach.
            </p>
          </div>
          <Button
            data-testid="google-login-button"
            variant="primary"
            className="w-full flex items-center justify-center gap-3 bg-[#4285F4] hover:bg-[#356ac3] text-white"
            onClick={handleGoogleLogin}
          >
            <span className="flex items-center justify-center w-8 h-8 rounded-full bg-white">
              <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
                <path
                  fill="#4285F4"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                />
                <path
                  fill="#EA4335"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                />
              </svg>
            </span>
            Continue with Google
          </Button>
          <p className="text-xs text-gray-500 leading-relaxed">
            We’ll redirect you to Google for secure sign-in, then bring you back here.
          </p>
        </div>
      </div>
    </div>
  )
}

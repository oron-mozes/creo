// AuthSignInWidget component for rendering sign-in button in chat
import React from 'react'

interface AuthSignInWidgetProps {
    message: string
}

export function AuthSignInWidget({ message }: AuthSignInWidgetProps) {
    const handleSignIn = () => {
        // Redirect to Google OAuth login
        window.location.href = '/api/auth/login'
    }

    return (
        <div className="space-y-4">
            <div className="text-base leading-relaxed whitespace-pre-wrap break-words" style={{ color: 'rgba(31, 41, 55, 0.9)' }}>
                {message}
            </div>
            <button
                onClick={handleSignIn}
                className="inline-flex items-center gap-2 px-6 py-3 rounded-full font-medium text-white transition-all hover:shadow-lg"
                style={{
                    background: 'linear-gradient(135deg, rgb(0, 160, 235), rgb(0, 144, 211))',
                    boxShadow: '0 4px 12px rgba(0, 160, 235, 0.3)',
                }}
            >
                <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12.545,10.239v3.821h5.445c-0.712,2.315-2.647,3.972-5.445,3.972c-3.332,0-6.033-2.701-6.033-6.032s2.701-6.032,6.033-6.032c1.498,0,2.866,0.549,3.921,1.453l2.814-2.814C17.503,2.988,15.139,2,12.545,2C7.021,2,2.543,6.477,2.543,12s4.478,10,10.002,10c8.396,0,10.249-7.85,9.426-11.748L12.545,10.239z" />
                </svg>
                Sign In with Google
            </button>
        </div>
    )
}

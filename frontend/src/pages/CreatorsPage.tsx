import React, { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { apiService } from '../services/apiService'
import { Header } from '../components/layout'
import { Spinner } from '../components/ui'
import { AuthModal } from '../components/auth'

interface Creator {
  id: string
  name: string
  platform?: string
  category?: string
  email?: string
  status?: string
  response?: string | null
  profile_url?: string
}

export function CreatorsPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const params = new URLSearchParams(location.search)
  const sessionId = params.get('session_id') || ''

  const { isAuthenticated, isLoading: authLoading, user, checkAuth } = useAuth()
  const [creators, setCreators] = useState<Creator[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showAuthModal, setShowAuthModal] = useState(false)

  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  useEffect(() => {
    if (!sessionId) {
      setError('Missing session_id')
      return
    }
    const load = async () => {
      setIsLoading(true)
      setError(null)
      try {
        const data = await apiService.getCreators(sessionId)
        setCreators(data)
      } catch (e: any) {
        setError(e?.message || 'Failed to load creators')
        if ((e as any)?.message?.toLowerCase()?.includes('401')) {
          setShowAuthModal(true)
        }
      } finally {
        setIsLoading(false)
      }
    }
    load()
  }, [sessionId])

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <AuthModal open={showAuthModal} onClose={() => setShowAuthModal(false)} />
      <Header onShowAuth={() => setShowAuthModal(true)} />

      <main className="flex-1 max-w-4xl mx-auto w-full px-4 py-8">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Creators for Session</h1>
            <p className="text-gray-600">Session ID: {sessionId || 'Missing'}</p>
          </div>
          <button
            className="text-blue-600 hover:underline text-sm"
            onClick={() => navigate(-1)}
          >
            ← Back
          </button>
        </div>

        {authLoading || isLoading ? (
          <div className="flex items-center gap-3 text-gray-600">
            <Spinner size="sm" />
            <span>Loading creators...</span>
          </div>
        ) : error ? (
          <div className="text-red-600">{error}</div>
        ) : creators.length === 0 ? (
          <div className="text-gray-600">No creators stored for this session yet.</div>
        ) : (
          <div className="space-y-3">
            {creators.map((c) => (
              <div key={c.id} className="rounded-2xl border border-gray-200 bg-white p-4">
                <div className="flex items-center justify-between">
                  <div className="font-semibold text-gray-900">{c.name}</div>
                  <div className="text-xs text-gray-600">Status: {c.status || 'pending'}</div>
                </div>
                <div className="text-sm text-gray-700 mt-2">
                  {[c.platform, c.category].filter(Boolean).join(' · ')}
                </div>
                {c.email && <div className="text-sm text-gray-700">Email: {c.email}</div>}
                {c.profile_url && (
                  <div className="text-sm">
                    Profile:{' '}
                    <a href={c.profile_url} className="text-blue-600 hover:underline" target="_blank" rel="noopener">
                      Link
                    </a>
                  </div>
                )}
                {c.response && <div className="text-sm text-gray-700">Response: {c.response}</div>}
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}

import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { HomePage, ChatView } from './pages'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/chat" element={<ChatView />} />
        <Route path="*" element={<LegacyRedirect />} />
      </Routes>
    </Router>
  )
}

function LegacyRedirect() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4 text-gray-900">Page Not Found</h1>
        <p className="text-gray-600 mb-6">The page you're looking for doesn't exist.</p>
        <div className="space-x-4">
          <a
            href="/"
            className="inline-block px-6 py-3 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors"
          >
            Go Home
          </a>
          <a
            href="/static/app.html"
            className="inline-block px-6 py-3 bg-gray-200 text-gray-900 rounded-lg hover:bg-gray-300 transition-colors"
          >
            Legacy App
          </a>
        </div>
      </div>
    </div>
  )
}

export default App

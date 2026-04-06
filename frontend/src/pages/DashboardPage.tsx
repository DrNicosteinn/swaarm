import { useAuth } from '@/hooks/useAuth'
import { useNavigate } from 'react-router-dom'

export function DashboardPage() {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()

  const handleSignOut = async () => {
    await signOut()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-900">Swaarm</h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-500">{user?.email}</span>
            <button
              onClick={handleSignOut}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              Abmelden
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
          <p className="text-gray-500 mt-1">Willkommen bei Swaarm</p>
        </div>

        {/* Empty State */}
        <div className="bg-white rounded-xl shadow-sm border p-12 text-center">
          <div className="text-gray-400 text-5xl mb-4">○</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Keine Simulationen
          </h3>
          <p className="text-gray-500 mb-6">
            Starte deine erste Simulation um zu sehen, wie die Öffentlichkeit auf deine Kommunikation reagiert.
          </p>
          <button
            disabled
            className="bg-gray-900 text-white px-6 py-2.5 rounded-lg font-medium opacity-50 cursor-not-allowed"
          >
            Neue Simulation (bald verfügbar)
          </button>
        </div>
      </main>
    </div>
  )
}

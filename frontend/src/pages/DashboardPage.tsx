import { useEffect, useState } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { useNavigate } from 'react-router-dom'

interface SimulationItem {
  simulation_id: string
  status: string
  current_round: number
  total_rounds: number
}

const statusLabels: Record<string, string> = {
  pending: 'Wartend',
  running: 'Läuft',
  completed: 'Abgeschlossen',
  failed: 'Fehlgeschlagen',
  paused: 'Pausiert',
}

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-700',
  running: 'bg-blue-100 text-blue-700',
  completed: 'bg-green-100 text-green-700',
  failed: 'bg-red-100 text-red-700',
  paused: 'bg-gray-100 text-gray-700',
}

export function DashboardPage() {
  const { user, session, signOut } = useAuth()
  const navigate = useNavigate()
  const [simulations, setSimulations] = useState<SimulationItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!session?.access_token) return

    fetch('/api/simulation/list', {
      headers: { Authorization: `Bearer ${session.access_token}` },
    })
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => setSimulations(data))
      .catch(() => setSimulations([]))
      .finally(() => setLoading(false))
  }, [session?.access_token])

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
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
            <p className="text-gray-500 mt-1">
              {simulations.length > 0
                ? `${simulations.length} Simulation${simulations.length !== 1 ? 'en' : ''}`
                : 'Willkommen bei Swaarm'}
            </p>
          </div>
          <button
            onClick={() => navigate('/simulation/new')}
            className="bg-gray-900 text-white px-5 py-2.5 rounded-lg font-medium hover:bg-gray-800 text-sm"
          >
            Neue Simulation
          </button>
        </div>

        {loading ? (
          <div className="text-center py-12 text-gray-400">Laden...</div>
        ) : simulations.length === 0 ? (
          /* Empty State */
          <div className="bg-white rounded-xl shadow-sm border p-12 text-center">
            <div className="text-gray-300 text-6xl mb-4">◎</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Keine Simulationen</h3>
            <p className="text-gray-500 mb-6 max-w-md mx-auto">
              Starte deine erste Simulation um zu sehen, wie die Öffentlichkeit auf deine
              Kommunikation reagiert.
            </p>
          </div>
        ) : (
          /* Simulation List */
          <div className="space-y-3">
            {simulations.map((sim) => (
              <div
                key={sim.simulation_id}
                onClick={() => navigate(`/simulation/${sim.simulation_id}`)}
                className="bg-white rounded-xl shadow-sm border p-5 flex items-center justify-between cursor-pointer hover:border-gray-300 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <div>
                    <h3 className="font-medium text-gray-900">
                      {sim.simulation_id.slice(0, 16)}
                    </h3>
                    <p className="text-sm text-gray-500">
                      Runde {sim.current_round}/{sim.total_rounds}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  {/* Progress */}
                  {sim.total_rounds > 0 && (
                    <div className="w-24 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-gray-900 h-2 rounded-full"
                        style={{
                          width: `${(sim.current_round / sim.total_rounds) * 100}%`,
                        }}
                      />
                    </div>
                  )}

                  {/* Status Badge */}
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium ${
                      statusColors[sim.status] || 'bg-gray-100 text-gray-700'
                    }`}
                  >
                    {statusLabels[sim.status] || sim.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}

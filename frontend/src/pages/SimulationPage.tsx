import { useParams } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { useSimulationStream } from '@/hooks/useSimulationStream'
import { LiveFeed } from '@/components/simulation/LiveFeed'
import { MetricsBar } from '@/components/simulation/MetricsBar'

export function SimulationPage() {
  const { id } = useParams<{ id: string }>()
  const { session } = useAuth()
  const token = session?.access_token || null

  const stream = useSimulationStream(id || null, token)

  const lastActiveCount =
    stream.activeCounts.length > 0
      ? stream.activeCounts[stream.activeCounts.length - 1]
      : 0

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-bold text-gray-900">Swaarm</h1>
          <span className="text-gray-300">|</span>
          <span className="text-sm text-gray-500">Simulation {id?.slice(0, 12)}</span>
        </div>
        <a href="/dashboard" className="text-sm text-gray-500 hover:text-gray-700">
          Dashboard
        </a>
      </header>

      {/* Metrics Bar */}
      <MetricsBar
        currentRound={stream.currentRound}
        totalRounds={stream.totalRounds || 50}
        avgSentiment={stream.avgSentiment}
        activeAgents={lastActiveCount}
        status={stream.status}
      />

      {/* Main Content: Graph + Feed */}
      <div className="flex flex-1 overflow-hidden">
        {/* Network Graph (left, 60%) */}
        <div className="w-3/5 bg-gray-900 flex items-center justify-center">
          <div className="text-center text-gray-500">
            <div className="text-6xl mb-4 opacity-30">◉</div>
            <p className="text-sm">Netzwerk-Graph</p>
            <p className="text-xs text-gray-600 mt-1">
              {stream.status === 'connected'
                ? `${lastActiveCount} aktive Agents`
                : 'Warte auf Verbindung...'}
            </p>
          </div>
        </div>

        {/* Right panel: Feed + Metrics */}
        <div className="w-2/5 flex flex-col border-l">
          {/* Live Feed (top 70%) */}
          <div className="flex-1 overflow-hidden bg-gray-50">
            <div className="px-3 py-2 border-b bg-white">
              <h3 className="text-sm font-medium text-gray-700">Live-Feed</h3>
            </div>
            <LiveFeed actions={stream.actions} />
          </div>

          {/* Mini Stats (bottom 30%) */}
          <div className="h-1/3 border-t bg-white p-4">
            <h3 className="text-sm font-medium text-gray-700 mb-3">Statistiken</h3>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <span className="text-gray-500">Posts</span>
                <p className="text-lg font-bold text-gray-900">
                  {stream.actions.filter((a) => a.action_type === 'create_post').length}
                </p>
              </div>
              <div>
                <span className="text-gray-500">Kommentare</span>
                <p className="text-lg font-bold text-gray-900">
                  {stream.actions.filter((a) => a.action_type === 'comment').length}
                </p>
              </div>
              <div>
                <span className="text-gray-500">Likes</span>
                <p className="text-lg font-bold text-gray-900">
                  {stream.actions.filter((a) => a.action_type === 'like_post').length}
                </p>
              </div>
              <div>
                <span className="text-gray-500">Sentiment</span>
                <p className={`text-lg font-bold ${
                  stream.avgSentiment > 0.2
                    ? 'text-green-600'
                    : stream.avgSentiment < -0.2
                      ? 'text-red-600'
                      : 'text-gray-600'
                }`}>
                  {stream.avgSentiment > 0 ? '+' : ''}
                  {stream.avgSentiment.toFixed(2)}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

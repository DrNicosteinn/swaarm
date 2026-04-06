import { useParams } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { useSimulationStatus } from '@/hooks/useSimulationStatus'

function PhaseIndicator({
  label,
  isActive,
  isDone,
  progress,
  detail,
}: {
  label: string
  isActive: boolean
  isDone: boolean
  progress?: string
  detail?: string
}) {
  return (
    <div
      className={`flex items-center gap-3 px-4 py-3 rounded-lg ${
        isActive ? 'bg-blue-50 border border-blue-200' : isDone ? 'bg-green-50' : 'bg-gray-50'
      }`}
    >
      <div
        className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
          isDone
            ? 'bg-green-500 text-white'
            : isActive
              ? 'bg-blue-500 text-white animate-pulse'
              : 'bg-gray-300 text-gray-600'
        }`}
      >
        {isDone ? '✓' : isActive ? '...' : '○'}
      </div>
      <div className="flex-1">
        <div className="text-sm font-medium text-gray-900">{label}</div>
        {detail && <div className="text-xs text-gray-500">{detail}</div>}
      </div>
      {progress && (
        <div className="text-sm font-mono text-gray-600">{progress}</div>
      )}
    </div>
  )
}

export function SimulationPage() {
  const { id } = useParams<{ id: string }>()
  const { session } = useAuth()
  const token = session?.access_token || null

  const { status, error } = useSimulationStatus(id || null, token)

  const phase = status?.phase || 'initializing'
  const isDone = status?.status === 'completed'
  const isFailed = status?.status === 'failed'

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-bold text-gray-900">Swaarm</h1>
          <span className="text-gray-300">|</span>
          <span className="text-sm text-gray-500">Simulation {id?.slice(0, 16)}</span>
        </div>
        <a href="/dashboard" className="text-sm text-gray-500 hover:text-gray-700">
          Dashboard
        </a>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8">
        {error && (
          <div className="bg-red-50 text-red-700 px-4 py-3 rounded-lg text-sm mb-6">{error}</div>
        )}

        {isFailed && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-6 mb-6 text-center">
            <div className="text-3xl mb-2">✕</div>
            <h3 className="text-lg font-medium text-red-800">Simulation fehlgeschlagen</h3>
            <p className="text-sm text-red-600 mt-1">{status?.phase_detail}</p>
          </div>
        )}

        {/* Phase Indicators */}
        <div className="bg-white rounded-xl shadow-sm border p-6 mb-6">
          <h2 className="text-lg font-bold text-gray-900 mb-4">Fortschritt</h2>
          <div className="space-y-2">
            <PhaseIndicator
              label="1. Personas generieren"
              isActive={phase === 'generating_personas'}
              isDone={
                phase === 'simulating' || phase === 'generating_report' || phase === 'done'
              }
              progress={
                status?.personas_generated
                  ? `${status.personas_generated}/${status.total_agents}`
                  : undefined
              }
              detail={
                phase === 'generating_personas'
                  ? status?.phase_detail
                  : phase === 'initializing'
                    ? 'Warte...'
                    : undefined
              }
            />
            <PhaseIndicator
              label="2. Simulation durchfuehren"
              isActive={phase === 'simulating'}
              isDone={phase === 'generating_report' || phase === 'done'}
              progress={
                status?.current_round
                  ? `Runde ${status.current_round}/${status.total_rounds}`
                  : undefined
              }
              detail={phase === 'simulating' ? status?.phase_detail : undefined}
            />
            <PhaseIndicator
              label="3. Report erstellen"
              isActive={phase === 'generating_report'}
              isDone={phase === 'done'}
              detail={phase === 'done' ? 'Abgeschlossen' : undefined}
            />
          </div>

          {/* Overall progress bar */}
          {status && !isDone && !isFailed && (
            <div className="mt-4">
              <div className="flex justify-between text-xs text-gray-500 mb-1">
                <span>{status.phase_detail}</span>
                {status.cost_usd > 0 && <span>${status.cost_usd.toFixed(4)}</span>}
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                  style={{
                    width: `${_computeOverallProgress(status)}%`,
                  }}
                />
              </div>
            </div>
          )}

          {isDone && (
            <div className="mt-4 bg-green-50 rounded-lg p-4 text-center">
              <span className="text-green-700 font-medium">
                Simulation abgeschlossen — ${status?.cost_usd?.toFixed(4) || '0'}
              </span>
            </div>
          )}
        </div>

        {/* Stats Grid */}
        {status && (status.posts_created > 0 || status.comments_created > 0) && (
          <div className="bg-white rounded-xl shadow-sm border p-6 mb-6">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Statistiken</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard label="Posts" value={status.posts_created} />
              <StatCard label="Kommentare" value={status.comments_created} />
              <StatCard label="Likes" value={status.likes_created} />
              <StatCard
                label="Sentiment"
                value={status.avg_sentiment.toFixed(2)}
                color={
                  status.avg_sentiment > 0.2
                    ? 'text-green-600'
                    : status.avg_sentiment < -0.2
                      ? 'text-red-600'
                      : 'text-gray-600'
                }
              />
            </div>
          </div>
        )}

        {/* Waiting state */}
        {!status && !error && (
          <div className="text-center py-12 text-gray-400">Lade Simulation...</div>
        )}
      </main>
    </div>
  )
}

function StatCard({
  label,
  value,
  color,
}: {
  label: string
  value: string | number
  color?: string
}) {
  return (
    <div className="text-center">
      <div className="text-xs text-gray-500 mb-1">{label}</div>
      <div className={`text-2xl font-bold ${color || 'text-gray-900'}`}>{value}</div>
    </div>
  )
}

function _computeOverallProgress(status: {
  phase: string
  personas_generated: number
  total_agents: number
  current_round: number
  total_rounds: number
}): number {
  // Phase weights: personas=30%, simulation=60%, report=10%
  if (status.phase === 'initializing') return 2
  if (status.phase === 'generating_personas') {
    const pct = status.total_agents > 0 ? status.personas_generated / status.total_agents : 0
    return 5 + pct * 25 // 5-30%
  }
  if (status.phase === 'simulating') {
    const pct = status.total_rounds > 0 ? status.current_round / status.total_rounds : 0
    return 30 + pct * 60 // 30-90%
  }
  if (status.phase === 'generating_report') return 92
  if (status.phase === 'done') return 100
  return 0
}

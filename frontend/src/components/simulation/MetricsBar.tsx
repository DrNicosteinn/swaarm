interface MetricsBarProps {
  currentRound: number
  totalRounds: number
  avgSentiment: number
  activeAgents: number
  status: string
}

export function MetricsBar({
  currentRound,
  totalRounds,
  avgSentiment,
  activeAgents,
  status,
}: MetricsBarProps) {
  const progress = totalRounds > 0 ? (currentRound / totalRounds) * 100 : 0

  const sentimentLabel =
    avgSentiment > 0.2 ? 'Positiv' : avgSentiment < -0.2 ? 'Negativ' : 'Neutral'

  const sentimentColor =
    avgSentiment > 0.2
      ? 'text-green-600'
      : avgSentiment < -0.2
        ? 'text-red-600'
        : 'text-gray-600'

  const statusLabel: Record<string, string> = {
    connecting: 'Verbinde...',
    connected: 'Live',
    disconnected: 'Getrennt',
    error: 'Fehler',
  }

  const statusColor: Record<string, string> = {
    connecting: 'bg-yellow-500',
    connected: 'bg-green-500',
    disconnected: 'bg-gray-400',
    error: 'bg-red-500',
  }

  return (
    <div className="bg-white border-b px-4 py-3">
      <div className="flex items-center gap-6 text-sm">
        {/* Status */}
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${statusColor[status] || 'bg-gray-400'}`} />
          <span className="text-gray-600">{statusLabel[status] || status}</span>
        </div>

        {/* Progress */}
        <div className="flex items-center gap-2 flex-1 max-w-xs">
          <span className="text-gray-500 whitespace-nowrap">
            Runde {currentRound}/{totalRounds}
          </span>
          <div className="flex-1 bg-gray-200 rounded-full h-2">
            <div
              className="bg-gray-900 h-2 rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
          <span className="text-gray-400 text-xs">{Math.round(progress)}%</span>
        </div>

        {/* Sentiment */}
        <div className="flex items-center gap-1">
          <span className="text-gray-500">Stimmung:</span>
          <span className={`font-medium ${sentimentColor}`}>{sentimentLabel}</span>
        </div>

        {/* Active Agents */}
        <div className="flex items-center gap-1">
          <span className="text-gray-500">Aktiv:</span>
          <span className="font-medium text-gray-900">{activeAgents}</span>
        </div>
      </div>
    </div>
  )
}

import { useMemo } from 'react'

interface StatsPanelProps {
  currentRound: number
  totalRounds: number
  totalAgents: number
  activeAgents: number
  postsCreated: number
  commentsCreated: number
  likesCreated: number
  avgSentiment: number
  costUsd: number
  sentimentHistory: number[]
  activeHistory: number[]
}

function MiniChart({ data, color, height = 40 }: { data: number[]; color: string; height?: number }) {
  if (data.length < 2) return null

  const min = Math.min(...data)
  const max = Math.max(...data)
  const range = max - min || 1
  const width = 120

  const points = data.map((v, i) => {
    const x = (i / (data.length - 1)) * width
    const y = height - ((v - min) / range) * (height - 4) - 2
    return `${x},${y}`
  }).join(' ')

  return (
    <svg width={width} height={height} className="overflow-visible">
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* Glow effect */}
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="4"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity="0.15"
      />
    </svg>
  )
}

function SentimentBar({ value }: { value: number }) {
  // Maps -1..1 to 0..100
  const pct = ((value + 1) / 2) * 100

  return (
    <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden relative">
      {/* Gradient background: red → gray → green */}
      <div className="absolute inset-0 bg-gradient-to-r from-red-500 via-gray-600 to-green-500 opacity-30" />
      {/* Indicator */}
      <div
        className="absolute top-0 h-full w-1.5 bg-white rounded-full shadow-sm transition-all duration-700"
        style={{ left: `calc(${pct}% - 3px)` }}
      />
    </div>
  )
}

function StatTile({
  label,
  value,
  sub,
  color,
}: {
  label: string
  value: string | number
  sub?: string
  color?: string
}) {
  return (
    <div className="bg-gray-900/60 rounded-lg p-3 border border-gray-800">
      <div className="text-[10px] uppercase tracking-wider text-gray-500 mb-1">{label}</div>
      <div className={`text-xl font-bold tabular-nums ${color || 'text-white'}`}>{value}</div>
      {sub && <div className="text-[10px] text-gray-600 mt-0.5">{sub}</div>}
    </div>
  )
}

export function StatsPanel({
  currentRound,
  totalRounds,
  totalAgents,
  activeAgents,
  postsCreated,
  commentsCreated,
  likesCreated,
  avgSentiment,
  costUsd,
  sentimentHistory,
  activeHistory,
}: StatsPanelProps) {
  const progress = totalRounds > 0 ? (currentRound / totalRounds) * 100 : 0

  const sentimentLabel = useMemo(() => {
    if (avgSentiment > 0.3) return { text: 'Sehr positiv', color: 'text-green-400' }
    if (avgSentiment > 0.1) return { text: 'Positiv', color: 'text-green-400' }
    if (avgSentiment < -0.3) return { text: 'Sehr negativ', color: 'text-red-400' }
    if (avgSentiment < -0.1) return { text: 'Negativ', color: 'text-red-400' }
    return { text: 'Neutral', color: 'text-gray-400' }
  }, [avgSentiment])

  const totalEngagement = postsCreated + commentsCreated + likesCreated

  return (
    <div className="flex flex-col h-full p-3 space-y-3 overflow-y-auto">
      {/* Progress */}
      <div className="bg-gray-900/60 rounded-lg p-3 border border-gray-800">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-gray-400">Fortschritt</span>
          <span className="text-xs font-mono text-gray-400">
            Runde {currentRound}/{totalRounds}
          </span>
        </div>
        <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full bg-gradient-to-r from-blue-600 to-blue-400 transition-all duration-700"
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className="flex items-center justify-between mt-1.5">
          <span className="text-[10px] text-gray-600">{Math.round(progress)}%</span>
          {costUsd > 0 && (
            <span className="text-[10px] text-gray-600">${costUsd.toFixed(4)}</span>
          )}
        </div>
      </div>

      {/* Sentiment */}
      <div className="bg-gray-900/60 rounded-lg p-3 border border-gray-800">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-gray-400">Stimmung</span>
          <span className={`text-xs font-medium ${sentimentLabel.color}`}>
            {sentimentLabel.text}
          </span>
        </div>
        <SentimentBar value={avgSentiment} />
        <div className="flex items-center justify-between mt-1.5">
          <span className="text-[10px] text-gray-600">Negativ</span>
          <span className="text-[10px] font-mono text-gray-500">
            {avgSentiment > 0 ? '+' : ''}{avgSentiment.toFixed(3)}
          </span>
          <span className="text-[10px] text-gray-600">Positiv</span>
        </div>
        {sentimentHistory.length > 1 && (
          <div className="mt-2 flex justify-center">
            <MiniChart data={sentimentHistory} color="#60a5fa" />
          </div>
        )}
      </div>

      {/* Grid stats */}
      <div className="grid grid-cols-2 gap-2">
        <StatTile
          label="Personas"
          value={totalAgents}
          sub={`${activeAgents} aktiv`}
        />
        <StatTile
          label="Engagement"
          value={totalEngagement}
          sub={`${postsCreated}P ${commentsCreated}K ${likesCreated}L`}
        />
      </div>

      {/* Activity chart */}
      {activeHistory.length > 1 && (
        <div className="bg-gray-900/60 rounded-lg p-3 border border-gray-800">
          <div className="text-[10px] uppercase tracking-wider text-gray-500 mb-2">
            Aktivitaet pro Runde
          </div>
          <div className="flex justify-center">
            <MiniChart data={activeHistory} color="#a78bfa" height={32} />
          </div>
        </div>
      )}
    </div>
  )
}

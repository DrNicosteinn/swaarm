import { useEffect, useMemo, useRef, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { useSimulationStatus } from '@/hooks/useSimulationStatus'
import { useSimulationStream } from '@/hooks/useSimulationStream'
import { NetworkGraph } from '@/components/simulation/graph/NetworkGraph'
import { PersonaDetailPanel } from '@/components/simulation/graph/panel/PersonaDetailPanel'
import { streamNodeToSimNode, streamLinkToSimLink, type SimNode } from '@/components/simulation/graph/types'
import { LiveFeed } from '@/components/simulation/LiveFeed'
import type { FeedEvent } from '@/components/simulation/LiveFeed'
import { StatsPanel } from '@/components/simulation/StatsPanel'
import { PhaseTimeline } from '@/components/simulation/PhaseTimeline'

export function SimulationPage() {
  const { id } = useParams<{ id: string }>()
  const { session } = useAuth()
  const token = session?.access_token || null

  // Polling for status (phase tracking, persona counts)
  const { status, error } = useSimulationStatus(id || null, token)

  // WebSocket for live events (actions, graph updates)
  const stream = useSimulationStream(id || null, token)

  // Graph container sizing
  const graphContainerRef = useRef<HTMLDivElement>(null)
  const [graphSize, setGraphSize] = useState({ width: 800, height: 600 })

  useEffect(() => {
    const el = graphContainerRef.current
    if (!el) return

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect
        setGraphSize({ width: Math.floor(width), height: Math.floor(height) })
      }
    })
    observer.observe(el)
    return () => observer.disconnect()
  }, [])

  // Selected node (for detail panel)
  const [selectedNode, setSelectedNode] = useState<SimNode | null>(null)

  const simNodes = useMemo(
    () => stream.nodes.map(streamNodeToSimNode),
    [stream.nodes],
  )
  const simLinks = useMemo(
    () => stream.links.map(streamLinkToSimLink),
    [stream.links],
  )

  // Configuration state
  const [configPlatform, setConfigPlatform] = useState<'public' | 'professional'>('public')
  const [configRounds, setConfigRounds] = useState(50)
  const [isStartingSimulation, setIsStartingSimulation] = useState(false)

  // Derive state
  const phase = stream.currentPhase !== 'connecting' ? stream.currentPhase : (status?.phase || 'analyzing')
  const isDone = status?.status === 'completed' || stream.isComplete
  const isFailed = status?.status === 'failed'
  const isConfiguring = stream.isConfiguring || status?.phase === 'configuring'
  const hasGraphData = stream.nodes.length > 0

  // Update recommended platform when it arrives
  useEffect(() => {
    if (stream.recommendedPlatform) {
      setConfigPlatform(stream.recommendedPlatform as 'public' | 'professional')
    }
  }, [stream.recommendedPlatform])

  // Build feed events from stream
  const feedEvents: FeedEvent[] = [
    ...stream.feedEvents,
    ...(isDone
      ? [{
          kind: 'phase_change' as const,
          phase: 'done',
          detail: `${status?.posts_created || 0} Posts, ${status?.comments_created || 0} Kommentare`,
        }]
      : []),
  ]

  const personaCountForDisplay = stream.personaCount || status?.personas_generated || 0
  const totalAgentsForDisplay = status?.total_agents || stream.nodes.length || 0

  // Handle simulation start after configuration
  const handleStartSimulation = async () => {
    if (!token || !id) return
    setIsStartingSimulation(true)
    try {
      await fetch(`/api/simulation/configure/${id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          platform: configPlatform,
          round_count: configRounds,
        }),
      })
    } catch {
      // Error will be picked up by status polling
    }
    setIsStartingSimulation(false)
  }

  return (
    <div className="h-screen flex flex-col bg-gray-50 text-gray-900 overflow-hidden">
      {/* Top bar */}
      <header className="flex items-center justify-between px-4 py-2 bg-white/90 border-b border-gray-200 backdrop-blur-sm z-10">
        <div className="flex items-center gap-4">
          <Link to="/dashboard" className="text-sm font-bold text-gray-900 hover:text-gray-700 transition-colors">
            Swaarm
          </Link>
          <div className="w-px h-5 bg-gray-200" />
          <PhaseTimeline
            currentPhase={phase}
            phaseDetail={status?.phase_detail || ''}
            personasGenerated={personaCountForDisplay}
            totalAgents={totalAgentsForDisplay}
            currentRound={stream.currentRound || status?.current_round || 0}
            totalRounds={stream.totalRounds || status?.total_rounds || 0}
            isDone={isDone}
            isFailed={isFailed}
          />
        </div>

        {/* Connection status */}
        <div className="flex items-center gap-2">
          {stream.status === 'connected' && (
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              <span className="text-xs text-green-400">Live</span>
            </div>
          )}
          {stream.status === 'connecting' && (
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-yellow-500 animate-pulse" />
              <span className="text-xs text-yellow-400">Verbinde...</span>
            </div>
          )}
          {error && (
            <span className="text-xs text-red-400">{error}</span>
          )}
        </div>
      </header>

      {/* Main content: 3-column layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: Network Graph (60%) */}
        <div ref={graphContainerRef} className="flex-[6] relative min-w-0">
          {hasGraphData || phase === 'analyzing' ? (
            <>
              <NetworkGraph
                nodes={stream.nodes}
                links={stream.links}
                activeNodeIds={stream.activeNodeIds}
                width={graphSize.width}
                height={graphSize.height}
                onNodeSelect={setSelectedNode}
              />
              {selectedNode && (
                <PersonaDetailPanel
                  node={selectedNode}
                  allNodes={simNodes}
                  allLinks={simLinks}
                  onClose={() => setSelectedNode(null)}
                />
              )}
            </>
          ) : (
            <PreSimulationView
              phase={phase}
              isFailed={isFailed}
              personasGenerated={personaCountForDisplay}
              totalAgents={totalAgentsForDisplay}
              phaseDetail={status?.phase_detail || ''}
            />
          )}
        </div>

        {/* Right panel: Feed + Config or Stats */}
        <div className="flex-[4] flex flex-col border-l border-gray-200 bg-gray-50 min-w-[320px] max-w-[500px]">
          {isConfiguring ? (
            /* Configuration panel (after persona generation) */
            <div className="flex flex-col h-full">
              <div className="flex-1 overflow-y-auto">
                {/* Feed with preparation events */}
                <div className="flex-[60] min-h-0 border-b border-gray-200">
                  <LiveFeed events={feedEvents} maxItems={50} />
                </div>
              </div>

              {/* Config panel at bottom */}
              <div className="border-t border-gray-200 p-4 space-y-4 bg-white/90">
                <div className="text-center">
                  <div className="text-3xl font-bold text-gray-900">{personaCountForDisplay}</div>
                  <div className="text-xs text-gray-500 mt-1">Personas generiert</div>
                </div>

                <div>
                  <label className="text-xs text-gray-500 mb-1.5 block">Plattform</label>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setConfigPlatform('public')}
                      className={`flex-1 py-2 rounded-lg text-xs font-medium border transition-colors ${
                        configPlatform === 'public'
                          ? 'bg-indigo-600 text-white border-indigo-600'
                          : 'bg-gray-100 text-gray-600 border-gray-200 hover:border-gray-400'
                      }`}
                    >
                      Oeffentlich
                    </button>
                    <button
                      onClick={() => setConfigPlatform('professional')}
                      className={`flex-1 py-2 rounded-lg text-xs font-medium border transition-colors ${
                        configPlatform === 'professional'
                          ? 'bg-indigo-600 text-white border-indigo-600'
                          : 'bg-gray-100 text-gray-600 border-gray-200 hover:border-gray-400'
                      }`}
                    >
                      Professionell
                    </button>
                  </div>
                </div>

                <div>
                  <label className="text-xs text-gray-500 mb-1.5 block">Runden</label>
                  <div className="grid grid-cols-4 gap-2">
                    {[10, 25, 50, 100].map((r) => (
                      <button
                        key={r}
                        onClick={() => setConfigRounds(r)}
                        className={`py-2 rounded-lg text-xs font-medium border transition-colors ${
                          configRounds === r
                            ? 'bg-indigo-600 text-white border-indigo-600'
                            : 'bg-gray-100 text-gray-600 border-gray-200 hover:border-gray-400'
                        }`}
                      >
                        {r}
                      </button>
                    ))}
                  </div>
                </div>

                <button
                  onClick={handleStartSimulation}
                  disabled={isStartingSimulation}
                  className="w-full bg-indigo-600 text-white py-3 rounded-lg font-medium hover:bg-indigo-500 disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
                >
                  {isStartingSimulation ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Starte...
                    </>
                  ) : (
                    'Simulation starten'
                  )}
                </button>
              </div>
            </div>
          ) : (
            /* Normal mode: Feed + Stats */
            <>
              <div className="flex-[65] min-h-0 border-b border-gray-200">
                <LiveFeed events={feedEvents} />
              </div>
              <div className="flex-[35] min-h-0">
                <StatsPanel
                  currentRound={stream.currentRound || status?.current_round || 0}
                  totalRounds={stream.totalRounds || status?.total_rounds || 0}
                  totalAgents={totalAgentsForDisplay}
                  activeAgents={stream.activeCounts.length > 0 ? stream.activeCounts[stream.activeCounts.length - 1] : 0}
                  postsCreated={status?.posts_created || 0}
                  commentsCreated={status?.comments_created || 0}
                  likesCreated={status?.likes_created || 0}
                  avgSentiment={stream.avgSentiment || status?.avg_sentiment || 0}
                  costUsd={status?.cost_usd || 0}
                  sentimentHistory={stream.sentimentHistory}
                  activeHistory={stream.activeCounts}
                />
              </div>
            </>
          )}
        </div>
      </div>

      {/* Completion overlay */}
      {isDone && (
        <CompletionOverlay
          postsCreated={status?.posts_created || 0}
          commentsCreated={status?.comments_created || 0}
          likesCreated={status?.likes_created || 0}
          avgSentiment={status?.avg_sentiment || 0}
          costUsd={status?.cost_usd || 0}
          totalAgents={totalAgentsForDisplay}
        />
      )}

      {/* Failed overlay */}
      {isFailed && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-40">
          <div className="bg-white border border-red-500/30 rounded-2xl p-8 max-w-md text-center">
            <div className="w-16 h-16 rounded-full bg-red-500/20 flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Simulation fehlgeschlagen</h3>
            <p className="text-sm text-gray-600 mb-6">{status?.phase_detail || 'Ein unbekannter Fehler ist aufgetreten.'}</p>
            <Link
              to="/dashboard"
              className="inline-block bg-indigo-600 text-white px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-indigo-500 transition-colors"
            >
              Zurueck zum Dashboard
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}

// Pre-simulation view: shown during persona generation and init
function PreSimulationView({
  phase,
  isFailed,
  personasGenerated,
  totalAgents,
  phaseDetail,
}: {
  phase: string
  isFailed: boolean
  personasGenerated: number
  totalAgents: number
  phaseDetail: string
}) {
  if (isFailed) return null

  const progress = totalAgents > 0 ? (personasGenerated / totalAgents) * 100 : 0

  return (
    <div className="flex flex-col items-center justify-center h-full bg-gray-50">
      {phase === 'initializing' && (
        <>
          <div className="relative w-24 h-24 mb-6">
            <div className="absolute inset-0 rounded-full border-2 border-gray-200" />
            <div className="absolute inset-0 rounded-full border-2 border-t-blue-500 animate-spin" />
            <div className="absolute inset-3 rounded-full border-2 border-gray-200" />
            <div className="absolute inset-3 rounded-full border-2 border-t-blue-400 animate-spin" style={{ animationDirection: 'reverse', animationDuration: '1.5s' }} />
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Simulation wird vorbereitet</h2>
          <p className="text-sm text-gray-500">Konfiguration und LLM-Verbindung werden initialisiert...</p>
        </>
      )}

      {phase === 'generating_personas' && (
        <>
          {/* Animated persona generation */}
          <div className="relative w-48 h-48 mb-8">
            {/* Orbiting dots representing personas being created */}
            {Array.from({ length: Math.min(personasGenerated, 20) }).map((_, i) => {
              const angle = (i / 20) * 2 * Math.PI
              const radius = 60 + (i % 3) * 20
              const delay = i * 0.15
              return (
                <div
                  key={i}
                  className="absolute w-3 h-3 rounded-full animate-pulse"
                  style={{
                    left: `calc(50% + ${Math.cos(angle) * radius}px - 6px)`,
                    top: `calc(50% + ${Math.sin(angle) * radius}px - 6px)`,
                    backgroundColor: `hsl(${220 + i * 15}, 70%, 60%)`,
                    animationDelay: `${delay}s`,
                    opacity: 0.6 + (i / 20) * 0.4,
                  }}
                />
              )
            })}
            {/* Center count */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <div className="text-4xl font-bold text-gray-900 tabular-nums">{personasGenerated}</div>
                <div className="text-xs text-gray-500">von {totalAgents}</div>
              </div>
            </div>
          </div>

          <h2 className="text-xl font-semibold text-gray-900 mb-2">Personas werden generiert</h2>
          <p className="text-sm text-gray-500 mb-6 max-w-md text-center">{phaseDetail}</p>

          {/* Progress bar */}
          <div className="w-64">
            <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full bg-gradient-to-r from-indigo-600 to-blue-500 transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
            <div className="flex justify-between mt-1.5 text-[10px] text-gray-400">
              <span>{Math.round(progress)}%</span>
              <span>{totalAgents - personasGenerated} verbleibend</span>
            </div>
          </div>
        </>
      )}

      {phase === 'generating_report' && (
        <>
          <div className="relative w-24 h-24 mb-6">
            <svg className="w-full h-full text-blue-500 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1}>
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
              <line x1="10" y1="9" x2="8" y2="9" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Report wird erstellt</h2>
          <p className="text-sm text-gray-500">Ergebnisse werden analysiert und zusammengefasst...</p>
        </>
      )}
    </div>
  )
}

// Completion overlay — shown briefly when simulation finishes
function CompletionOverlay({
  postsCreated,
  commentsCreated,
  likesCreated,
  avgSentiment,
  costUsd,
  totalAgents,
}: {
  postsCreated: number
  commentsCreated: number
  likesCreated: number
  avgSentiment: number
  costUsd: number
  totalAgents: number
}) {
  const [visible, setVisible] = useState(true)

  if (!visible) return null

  const sentimentLabel =
    avgSentiment > 0.2 ? 'Positiv' :
    avgSentiment < -0.2 ? 'Negativ' : 'Neutral'

  const sentimentColor =
    avgSentiment > 0.2 ? 'text-green-500' :
    avgSentiment < -0.2 ? 'text-red-500' : 'text-gray-500'

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-40 animate-fade-in">
      <div className="bg-white border border-gray-200 rounded-2xl p-8 max-w-lg w-full mx-4 shadow-2xl">
        <div className="text-center mb-6">
          <div className="w-16 h-16 rounded-full bg-green-500/20 flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2.5}>
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-gray-900">Simulation abgeschlossen</h3>
        </div>

        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{postsCreated}</div>
            <div className="text-xs text-gray-500">Posts</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{commentsCreated}</div>
            <div className="text-xs text-gray-500">Kommentare</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{likesCreated}</div>
            <div className="text-xs text-gray-500">Likes</div>
          </div>
        </div>

        <div className="flex items-center justify-between text-sm mb-6 px-4">
          <div>
            <span className="text-gray-500">Stimmung: </span>
            <span className={`font-medium ${sentimentColor}`}>{sentimentLabel}</span>
          </div>
          <div>
            <span className="text-gray-500">Agenten: </span>
            <span className="text-gray-900 font-medium">{totalAgents}</span>
          </div>
          <div>
            <span className="text-gray-500">Kosten: </span>
            <span className="text-gray-900 font-medium">${costUsd.toFixed(4)}</span>
          </div>
        </div>

        <div className="flex gap-3">
          <button
            onClick={() => setVisible(false)}
            className="flex-1 bg-gray-100 text-gray-700 px-4 py-2.5 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors"
          >
            Graph anzeigen
          </button>
          <Link
            to="/dashboard"
            className="flex-1 bg-indigo-600 text-white px-4 py-2.5 rounded-lg text-sm font-medium hover:bg-indigo-500 transition-colors text-center"
          >
            Zum Dashboard
          </Link>
        </div>
      </div>
    </div>
  )
}

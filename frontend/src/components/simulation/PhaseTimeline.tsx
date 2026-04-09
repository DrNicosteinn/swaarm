interface PhaseTimelineProps {
  currentPhase: string
  phaseDetail: string
  personasGenerated: number
  totalAgents: number
  currentRound: number
  totalRounds: number
  isDone: boolean
  isFailed: boolean
}

const PHASES = [
  { key: 'analyzing', label: 'Analyse', icon: 'search' },
  { key: 'extracting_entities', label: 'Entitaeten', icon: 'search' },
  { key: 'enriching', label: 'Recherche', icon: 'globe' },
  { key: 'generating_personas', label: 'Personas', icon: 'users' },
  { key: 'simulating', label: 'Simulation', icon: 'activity' },
  { key: 'done', label: 'Fertig', icon: 'check' },
] as const

function getPhaseIndex(phase: string): number {
  const idx = PHASES.findIndex((p) => p.key === phase)
  if (idx >= 0) return idx
  if (phase === 'configuring') return 4 // Between personas and simulating
  if (phase === 'initializing') return -1
  return 0
}

function PhaseIcon({ icon, isDone }: { icon: string; isActive: boolean; isDone: boolean }) {
  const baseClass = 'w-4 h-4'

  if (isDone) {
    return (
      <svg className={baseClass} fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2.5}>
        <polyline points="20 6 9 17 4 12" />
      </svg>
    )
  }

  switch (icon) {
    case 'search':
      return (
        <svg className={baseClass} fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
          <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
      )
    case 'globe':
      return (
        <svg className={baseClass} fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
          <circle cx="12" cy="12" r="10" /><line x1="2" y1="12" x2="22" y2="12" />
          <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
        </svg>
      )
    case 'users':
      return (
        <svg className={baseClass} fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" />
          <path d="M23 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" />
        </svg>
      )
    case 'activity':
      return (
        <svg className={baseClass} fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
        </svg>
      )
    case 'file-text':
      return (
        <svg className={baseClass} fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" />
          <line x1="16" y1="17" x2="8" y2="17" />
        </svg>
      )
    case 'check':
      return (
        <svg className={baseClass} fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2.5}>
          <polyline points="20 6 9 17 4 12" />
        </svg>
      )
    default:
      return <div className="w-4 h-4 rounded-full bg-current" />
  }
}

export function PhaseTimeline({
  currentPhase,
  phaseDetail,
  personasGenerated,
  totalAgents,
  currentRound,
  totalRounds,
  isDone,
  isFailed,
}: PhaseTimelineProps) {
  const activeIdx = getPhaseIndex(currentPhase)

  return (
    <div className="flex items-center gap-1 px-2">
      {PHASES.map((phase, idx) => {
        const isActive = phase.key === currentPhase
        const phaseDone = isDone || idx < activeIdx
        // Progress text for active phase
        let progressText = ''
        if (isActive && phase.key === 'generating_personas' && totalAgents > 0) {
          progressText = `${personasGenerated}/${totalAgents}`
        } else if (isActive && phase.key === 'simulating' && totalRounds > 0) {
          progressText = `${currentRound}/${totalRounds}`
        }

        return (
          <div key={phase.key} className="flex items-center gap-1">
            {/* Phase pill */}
            <div
              className={`
                flex items-center gap-1.5 px-2.5 py-1.5 rounded-full text-xs font-medium transition-all duration-500
                ${isFailed && isActive
                  ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                  : phaseDone
                    ? 'bg-green-500/15 text-green-400 border border-green-500/20'
                    : isActive
                      ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                      : 'bg-gray-800/50 text-gray-600 border border-gray-800'
                }
              `}
            >
              <div className={isActive && !isDone && !isFailed ? 'animate-pulse' : ''}>
                <PhaseIcon icon={phase.icon} isActive={isActive} isDone={phaseDone} />
              </div>
              <span>{phase.label}</span>
              {progressText && (
                <span className="font-mono text-[10px] opacity-75">{progressText}</span>
              )}
            </div>

            {/* Connector line */}
            {idx < PHASES.length - 1 && (
              <div
                className={`w-6 h-px transition-colors duration-500 ${
                  idx < activeIdx || isDone ? 'bg-green-500/40' : 'bg-gray-800'
                }`}
              />
            )}
          </div>
        )
      })}

      {/* Detail text */}
      {phaseDetail && !isDone && !isFailed && (
        <span className="text-[10px] text-gray-600 ml-2 truncate max-w-[200px]">
          {phaseDetail}
        </span>
      )}
    </div>
  )
}

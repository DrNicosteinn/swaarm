import type { SimNode, SimLink } from '../types'
import { entityTypeColor, entityTypeLabel, sentimentColor, personaSourceColor, THEME } from '../utils/colors'

interface PersonaDetailPanelProps {
  node: SimNode | null
  allNodes: SimNode[]
  allLinks: SimLink[]
  onClose: () => void
}

export function PersonaDetailPanel({ node, allNodes, allLinks, onClose }: PersonaDetailPanelProps) {
  if (!node) return null

  const nodeById = new Map(allNodes.map(n => [n.id, n]))

  // Compute 1-hop neighbors
  const neighbors = new Map<string, { node: SimNode; label?: string }>()
  allLinks.forEach(link => {
    const src = typeof link.source === 'string' ? link.source : link.source.id
    const tgt = typeof link.target === 'string' ? link.target : link.target.id
    if (src === node.id) {
      const neighbor = nodeById.get(tgt)
      if (neighbor) neighbors.set(tgt, { node: neighbor, label: link.label })
    } else if (tgt === node.id) {
      const neighbor = nodeById.get(src)
      if (neighbor) neighbors.set(src, { node: neighbor, label: link.label })
    }
  })

  const sourceColor = personaSourceColor(node.personaSource)
  const nodeColor = node.isEntity
    ? entityTypeColor(node.entityType)
    : sentimentColor(node.sentiment)

  const sourceLabel =
    node.personaSource === 'real_enriched'
      ? 'REAL'
      : node.personaSource === 'real_minimal'
      ? 'REAL'
      : node.personaSource === 'role_based'
      ? 'ROLLE'
      : null

  return (
    <div
      className="absolute top-0 left-0 h-full flex flex-col overflow-hidden"
      style={{
        width: 320,
        backgroundColor: THEME.white,
        borderRight: `1px solid ${THEME.border}`,
        boxShadow: '4px 0 16px rgba(0,0,0,0.04)',
        animation: 'slideInLeft 0.25s ease-out',
      }}
      onClick={e => e.stopPropagation()}
    >
      <style>{`
        @keyframes slideInLeft {
          from { transform: translateX(-100%); }
          to { transform: translateX(0); }
        }
      `}</style>

      {/* Header */}
      <div
        className="p-4 flex items-start gap-3 border-b"
        style={{ borderColor: THEME.border }}
      >
        <div
          className="w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0 text-white font-bold text-sm"
          style={{ backgroundColor: nodeColor }}
        >
          {getInitials(node.label)}
        </div>
        <div className="flex-1 min-w-0">
          <div
            className="font-semibold text-base leading-tight"
            style={{ color: THEME.text }}
          >
            {node.label}
          </div>
          {(node.occupation || node.subType) && (
            <div className="text-xs mt-0.5" style={{ color: THEME.textMuted }}>
              {node.occupation || node.subType}
            </div>
          )}
          <div className="flex items-center gap-1.5 mt-1.5">
            {sourceLabel && (
              <span
                className="text-[9px] px-1.5 py-0.5 rounded font-bold"
                style={{
                  backgroundColor: `${sourceColor}20`,
                  color: sourceColor ?? THEME.textMuted,
                  border: `1px solid ${sourceColor}40`,
                }}
              >
                {sourceLabel}
              </span>
            )}
            {node.isEntity && (
              <span
                className="text-[9px] px-1.5 py-0.5 rounded"
                style={{ backgroundColor: THEME.borderLight, color: THEME.textMuted }}
              >
                {entityTypeLabel(node.entityType)}
              </span>
            )}
          </div>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="w-6 h-6 flex items-center justify-center rounded-full text-sm"
          style={{ color: THEME.textMuted, backgroundColor: THEME.borderLight }}
          aria-label="Schliessen"
        >
          ×
        </button>
      </div>

      {/* Body (scrollable) */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Sentiment */}
        {!node.isEntity && (
          <Section title="Stimmung">
            <div className="flex items-center gap-3">
              <div
                className="flex-1 h-2 rounded-full overflow-hidden"
                style={{ backgroundColor: THEME.borderLight }}
              >
                <div
                  className="h-full transition-all"
                  style={{
                    width: `${((node.sentiment + 1) / 2) * 100}%`,
                    backgroundColor: sentimentColor(node.sentiment),
                  }}
                />
              </div>
              <span
                className="text-xs font-mono tabular-nums"
                style={{ color: sentimentColor(node.sentiment) }}
              >
                {node.sentiment > 0 ? '+' : ''}{node.sentiment.toFixed(2)}
              </span>
            </div>
          </Section>
        )}

        {/* Role */}
        {node.role && (
          <Section title="Rolle">
            <div className="text-sm" style={{ color: THEME.text }}>
              {node.role}
            </div>
          </Section>
        )}

        {/* Follower count */}
        {!node.isEntity && (
          <Section title="Follower">
            <div className="text-sm font-semibold" style={{ color: THEME.text }}>
              {node.followerCount}
            </div>
          </Section>
        )}

        {/* Relationships */}
        {neighbors.size > 0 && (
          <Section title={`Beziehungen (${neighbors.size})`}>
            <div className="space-y-1.5">
              {Array.from(neighbors.values()).slice(0, 10).map(({ node: nb, label }) => (
                <div
                  key={nb.id}
                  className="flex items-center gap-2 text-xs p-2 rounded"
                  style={{ backgroundColor: THEME.borderLight }}
                >
                  <div
                    className="w-2 h-2 rounded-full flex-shrink-0"
                    style={{
                      backgroundColor: nb.isEntity
                        ? entityTypeColor(nb.entityType)
                        : sentimentColor(nb.sentiment),
                    }}
                  />
                  <div className="flex-1 min-w-0">
                    <div className="font-medium truncate" style={{ color: THEME.text }}>
                      {nb.label}
                    </div>
                    {label && (
                      <div className="text-[10px] truncate" style={{ color: THEME.textMuted }}>
                        {label}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {neighbors.size > 10 && (
                <div className="text-[10px] text-center" style={{ color: THEME.textMuted }}>
                  +{neighbors.size - 10} weitere
                </div>
              )}
            </div>
          </Section>
        )}
      </div>
    </div>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <div
        className="text-[10px] font-bold uppercase tracking-wider mb-2"
        style={{ color: THEME.textMuted }}
      >
        {title}
      </div>
      {children}
    </div>
  )
}

function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/)
  if (parts.length === 0) return '?'
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
}

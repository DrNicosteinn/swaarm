import { useMemo } from 'react'
import type { SimNode } from '../types'
import { entityTypeColor, entityTypeLabel, THEME } from '../utils/colors'

interface EntityLegendProps {
  nodes: SimNode[]
  hiddenTypes: Set<string>
  onToggle: (type: string) => void
}

export function EntityLegend({ nodes, hiddenTypes, onToggle }: EntityLegendProps) {
  const counts = useMemo(() => {
    const map = new Map<string, number>()
    nodes.forEach(n => {
      if (n.isEntity && n.entityType) {
        map.set(n.entityType, (map.get(n.entityType) ?? 0) + 1)
      }
    })
    return map
  }, [nodes])

  if (counts.size === 0) return null

  return (
    <div
      className="absolute bottom-4 left-4 rounded-lg"
      style={{
        backgroundColor: THEME.white,
        border: `1px solid ${THEME.border}`,
        boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
        padding: '12px 16px',
        maxWidth: 320,
      }}
      onClick={e => e.stopPropagation()}
    >
      <div
        className="text-[10px] font-bold uppercase tracking-wider mb-2"
        style={{ color: THEME.accent }}
      >
        Entities
      </div>
      <div className="flex flex-wrap gap-x-3 gap-y-1.5">
        {Array.from(counts.entries()).map(([type, count]) => {
          const hidden = hiddenTypes.has(type)
          return (
            <button
              key={type}
              type="button"
              onClick={() => onToggle(type)}
              className="flex items-center gap-1.5 text-[11px] transition-opacity"
              style={{
                opacity: hidden ? 0.35 : 1,
                color: THEME.text,
              }}
              title={hidden ? 'Einblenden' : 'Ausblenden'}
            >
              <div
                className="w-2.5 h-2.5 rounded-full"
                style={{ backgroundColor: entityTypeColor(type) }}
              />
              <span className={hidden ? 'line-through' : ''}>
                {entityTypeLabel(type)}
              </span>
              <span style={{ color: THEME.textMuted }}>{count}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}

import { useMemo, useRef, useCallback } from 'react'
import type { SimNode } from '../types'
import { entityTypeColor, sentimentColor, THEME } from '../utils/colors'

interface MiniMapProps {
  nodes: SimNode[]
  viewport: { x: number; y: number; width: number; height: number }
  onViewportChange: (cx: number, cy: number) => void
}

const MINIMAP_WIDTH = 180
const MINIMAP_HEIGHT = 120

export function MiniMap({ nodes, viewport, onViewportChange }: MiniMapProps) {
  const svgRef = useRef<SVGSVGElement>(null)

  const bounds = useMemo(() => {
    if (nodes.length === 0) {
      return { minX: 0, maxX: MINIMAP_WIDTH, minY: 0, maxY: MINIMAP_HEIGHT }
    }
    const xs = nodes.map(n => n.x ?? 0)
    const ys = nodes.map(n => n.y ?? 0)
    return {
      minX: Math.min(...xs) - 50,
      maxX: Math.max(...xs) + 50,
      minY: Math.min(...ys) - 50,
      maxY: Math.max(...ys) + 50,
    }
  }, [nodes])

  const worldWidth = bounds.maxX - bounds.minX
  const worldHeight = bounds.maxY - bounds.minY
  const scaleX = MINIMAP_WIDTH / worldWidth
  const scaleY = MINIMAP_HEIGHT / worldHeight
  const scale = Math.min(scaleX, scaleY)

  const toMini = (x: number, y: number): [number, number] => [
    (x - bounds.minX) * scale,
    (y - bounds.minY) * scale,
  ]

  const handleClick = useCallback(
    (e: React.MouseEvent<SVGSVGElement>) => {
      if (!svgRef.current) return
      const rect = svgRef.current.getBoundingClientRect()
      const miniX = e.clientX - rect.left
      const miniY = e.clientY - rect.top
      const worldX = miniX / scale + bounds.minX
      const worldY = miniY / scale + bounds.minY
      onViewportChange(worldX, worldY)
    },
    [scale, bounds, onViewportChange],
  )

  return (
    <div
      className="absolute bottom-4 right-4 rounded-lg overflow-hidden"
      style={{
        backgroundColor: THEME.white,
        border: `1px solid ${THEME.border}`,
        boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
      }}
      onClick={e => e.stopPropagation()}
    >
      <svg
        ref={svgRef}
        width={MINIMAP_WIDTH}
        height={MINIMAP_HEIGHT}
        onClick={handleClick}
        style={{ cursor: 'pointer', backgroundColor: THEME.bg }}
      >
        {/* Dots for personas (small) */}
        {nodes.filter(n => !n.isEntity).map(n => {
          if (n.x == null || n.y == null) return null
          const [mx, my] = toMini(n.x, n.y)
          return (
            <circle
              key={n.id}
              cx={mx}
              cy={my}
              r={1}
              fill={sentimentColor(n.sentiment)}
              opacity={0.6}
            />
          )
        })}
        {/* Entities (larger colored dots) */}
        {nodes.filter(n => n.isEntity).map(n => {
          if (n.x == null || n.y == null) return null
          const [mx, my] = toMini(n.x, n.y)
          return (
            <circle
              key={n.id}
              cx={mx}
              cy={my}
              r={3}
              fill={entityTypeColor(n.entityType)}
              stroke={THEME.white}
              strokeWidth={0.5}
            />
          )
        })}
        {/* Viewport rectangle */}
        <rect
          x={(viewport.x - bounds.minX) * scale}
          y={(viewport.y - bounds.minY) * scale}
          width={viewport.width * scale}
          height={viewport.height * scale}
          fill="none"
          stroke={THEME.accent}
          strokeWidth={1.5}
        />
      </svg>
    </div>
  )
}

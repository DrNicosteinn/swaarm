import { memo } from 'react'
import type { SimNode, SimLink, ZoomLevel } from '../types'
import { entityTypeColor, THEME } from '../utils/colors'

interface EdgesLayerProps {
  links: SimLink[]
  nodes: SimNode[]
  zoomLevel: ZoomLevel
  focusedIds: Set<string> | null
  hoveredLinkIds: Set<string>
}

export const EdgesLayer = memo(function EdgesLayer({
  links,
  nodes,
  zoomLevel,
  focusedIds,
  hoveredLinkIds,
}: EdgesLayerProps) {
  const nodeById = new Map(nodes.map(n => [n.id, n]))

  // Group edges by node pair to compute curvature for multi-edges
  const pairCounts = new Map<string, number>()
  const pairIndex = new Map<string, number>()
  links.forEach(link => {
    const src = typeof link.source === 'string' ? link.source : link.source.id
    const tgt = typeof link.target === 'string' ? link.target : link.target.id
    const pairKey = [src, tgt].sort().join('|')
    pairCounts.set(pairKey, (pairCounts.get(pairKey) ?? 0) + 1)
  })

  // In aggregated view, only show entity-entity edges
  const visibleLinks =
    zoomLevel === 'aggregated'
      ? links.filter(l => l.type === 'entity_relation')
      : links

  return (
    <g className="edges-layer">
      {visibleLinks.map((link, i) => {
        const src = typeof link.source === 'string' ? link.source : link.source.id
        const tgt = typeof link.target === 'string' ? link.target : link.target.id
        const sourceNode = nodeById.get(src)
        const targetNode = nodeById.get(tgt)

        if (!sourceNode || !targetNode) return null
        if (sourceNode.x == null || targetNode.x == null) return null

        const linkKey = `${src}-${tgt}-${i}`
        const pairKey = [src, tgt].sort().join('|')
        const pairTotal = pairCounts.get(pairKey) ?? 1
        const pairI = pairIndex.get(pairKey) ?? 0
        pairIndex.set(pairKey, pairI + 1)

        // Dim non-focused edges
        const isDimmed =
          focusedIds != null &&
          !(focusedIds.has(src) && focusedIds.has(tgt))
        const isHovered = hoveredLinkIds.has(linkKey)

        return (
          <EdgeRenderer
            key={linkKey}
            link={link}
            sourceNode={sourceNode}
            targetNode={targetNode}
            pairIndex={pairI}
            pairTotal={pairTotal}
            isDimmed={isDimmed}
            isHovered={isHovered}
            zoomLevel={zoomLevel}
          />
        )
      })}
    </g>
  )
})

interface EdgeRendererProps {
  link: SimLink
  sourceNode: SimNode
  targetNode: SimNode
  pairIndex: number
  pairTotal: number
  isDimmed: boolean
  isHovered: boolean
  zoomLevel: ZoomLevel
}

function EdgeRenderer({
  link,
  sourceNode,
  targetNode,
  pairIndex,
  pairTotal,
  isDimmed,
  isHovered,
  zoomLevel,
}: EdgeRendererProps) {
  const sx = sourceNode.x!
  const sy = sourceNode.y!
  const tx = targetNode.x!
  const ty = targetNode.y!

  // Compute bezier curve for multi-edges
  let path: string
  let midX: number
  let midY: number

  if (pairTotal === 1) {
    // Straight line
    path = `M ${sx} ${sy} L ${tx} ${ty}`
    midX = (sx + tx) / 2
    midY = (sy + ty) / 2
  } else {
    // Bezier curve with perpendicular offset
    const curvature = ((pairIndex / (pairTotal - 1)) - 0.5) * 0.6
    const dx = tx - sx
    const dy = ty - sy
    const dist = Math.hypot(dx, dy)
    const offsetX = (-dy / dist) * curvature * dist
    const offsetY = (dx / dist) * curvature * dist
    const cx = (sx + tx) / 2 + offsetX
    const cy = (sy + ty) / 2 + offsetY
    path = `M ${sx} ${sy} Q ${cx} ${cy} ${tx} ${ty}`
    midX = 0.25 * sx + 0.5 * cx + 0.25 * tx
    midY = 0.25 * sy + 0.5 * cy + 0.25 * ty
  }

  // Style based on link type
  let stroke: string
  let strokeWidth: number
  let opacity: number
  let label = link.label

  switch (link.type) {
    case 'entity_relation':
      stroke = entityTypeColor(sourceNode.entityType)
      strokeWidth = 2.5
      opacity = 0.7
      break
    case 'persona_entity':
      stroke = THEME.border
      strokeWidth = 0.8
      opacity = 0.5
      label = undefined
      break
    case 'persona_relation':
      stroke = '#94A3B8'
      strokeWidth = 1.2
      opacity = 0.6
      // Labels only when zoomed in
      if (zoomLevel !== 'full' && zoomLevel !== 'detail') {
        label = undefined
      }
      break
    case 'follow':
    default:
      stroke = THEME.border
      strokeWidth = 0.6
      opacity = 0.4
      label = undefined
  }

  if (isHovered) {
    stroke = THEME.accent
    strokeWidth += 1
    opacity = 1
  }

  const finalOpacity = isDimmed ? opacity * 0.3 : opacity

  return (
    <g style={{ transition: 'opacity 0.2s' }}>
      <path
        d={path}
        fill="none"
        stroke={stroke}
        strokeWidth={strokeWidth}
        opacity={finalOpacity}
      />
      {label && link.type === 'entity_relation' && (
        <EdgeLabel x={midX} y={midY} text={label} opacity={finalOpacity} />
      )}
      {label && link.type === 'persona_relation' && (
        <EdgeLabel x={midX} y={midY} text={label} opacity={finalOpacity} size="sm" />
      )}
    </g>
  )
}

interface EdgeLabelProps {
  x: number
  y: number
  text: string
  opacity: number
  size?: 'sm' | 'md'
}

function EdgeLabel({ x, y, text, opacity, size = 'md' }: EdgeLabelProps) {
  const fontSize = size === 'sm' ? 9 : 11
  const padH = 6
  const padV = 3
  // Estimate text width (since we can't measure without rendering)
  const textWidth = text.length * (fontSize * 0.55)

  return (
    <g transform={`translate(${x},${y})`} style={{ pointerEvents: 'none' }} opacity={opacity}>
      <rect
        x={-textWidth / 2 - padH}
        y={-fontSize / 2 - padV}
        width={textWidth + padH * 2}
        height={fontSize + padV * 2}
        fill="white"
        stroke={THEME.border}
        strokeWidth={0.5}
        rx={3}
      />
      <text
        textAnchor="middle"
        dominantBaseline="middle"
        fontSize={fontSize}
        fontWeight={500}
        fill={THEME.text}
        style={{ userSelect: 'none' }}
      >
        {text}
      </text>
    </g>
  )
}

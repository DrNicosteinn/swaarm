import { memo } from 'react'
import type { SimNode, ZoomLevel } from '../types'
import {
  entityTypeColor,
  sentimentColor,
  personaSourceColor,
  THEME,
} from '../utils/colors'

interface NodesLayerProps {
  nodes: SimNode[]
  zoomLevel: ZoomLevel
  hoveredId: string | null
  selectedId: string | null
  activeIds: Set<string>
  focusedIds: Set<string> | null // null = no focus mode, show all
  onNodeClick: (node: SimNode) => void
  onNodeHover: (node: SimNode | null) => void
}

const TIER_RADIUS: Record<string, number> = {
  power_creator: 7,
  active_responder: 5,
  selective_engager: 4,
  observer: 3,
}

export const NodesLayer = memo(function NodesLayer({
  nodes,
  zoomLevel,
  hoveredId,
  selectedId,
  activeIds,
  focusedIds,
  onNodeClick,
  onNodeHover,
}: NodesLayerProps) {
  return (
    <g className="nodes-layer">
      {nodes.map(node => {
        if (node.x == null || node.y == null) return null

        const isHovered = hoveredId === node.id
        const isSelected = selectedId === node.id
        const isActive = activeIds.has(node.id)
        const isDimmed = focusedIds != null && !focusedIds.has(node.id)
        const opacity = isDimmed ? 0.15 : 1

        if (node.isEntity) {
          return (
            <EntityNode
              key={node.id}
              node={node}
              isHovered={isHovered}
              isSelected={isSelected}
              zoomLevel={zoomLevel}
              opacity={opacity}
              onClick={() => onNodeClick(node)}
              onMouseEnter={() => onNodeHover(node)}
              onMouseLeave={() => onNodeHover(null)}
            />
          )
        }

        return (
          <PersonaNode
            key={node.id}
            node={node}
            isHovered={isHovered}
            isSelected={isSelected}
            isActive={isActive}
            zoomLevel={zoomLevel}
            opacity={opacity}
            onClick={() => onNodeClick(node)}
            onMouseEnter={() => onNodeHover(node)}
            onMouseLeave={() => onNodeHover(null)}
          />
        )
      })}
    </g>
  )
})

interface EntityNodeProps {
  node: SimNode
  isHovered: boolean
  isSelected: boolean
  zoomLevel: ZoomLevel
  opacity: number
  onClick: () => void
  onMouseEnter: () => void
  onMouseLeave: () => void
}

function EntityNode({
  node,
  isHovered,
  isSelected,
  zoomLevel,
  opacity,
  onClick,
  onMouseEnter,
  onMouseLeave,
}: EntityNodeProps) {
  const color = entityTypeColor(node.entityType)
  const importance = node.importance ?? 0.5
  const scale = 0.7 + importance * 0.6 // 0.7 to 1.3
  const isDiamond = node.entityType === 'real_person' || node.entityType === 'real_company'

  return (
    <g
      transform={`translate(${node.x},${node.y})`}
      style={{ opacity, cursor: 'pointer', transition: 'opacity 0.2s' }}
      onClick={onClick}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    >
      {/* Glow ring for selected */}
      {isSelected && (
        <circle r={24 * scale + 6} fill="none" stroke={THEME.accent} strokeWidth={2.5} />
      )}
      {/* Hover ring */}
      {isHovered && !isSelected && (
        <circle r={24 * scale + 3} fill="none" stroke={THEME.accent} strokeWidth={1.5} opacity={0.6} />
      )}

      {isDiamond ? (
        <rect
          x={-12 * scale}
          y={-12 * scale}
          width={24 * scale}
          height={24 * scale}
          fill={color}
          stroke={THEME.white}
          strokeWidth={2}
          transform="rotate(45)"
          filter="url(#entity-shadow)"
        />
      ) : (
        <circle
          r={16 * scale}
          fill={color}
          stroke={THEME.white}
          strokeWidth={2}
          filter="url(#entity-shadow)"
        />
      )}

      {/* Label — always visible for entities */}
      <text
        y={24 * scale + 14}
        textAnchor="middle"
        fontSize={13}
        fontWeight={600}
        fill={THEME.text}
        style={{ pointerEvents: 'none', userSelect: 'none' }}
      >
        {node.label}
      </text>
      {node.subType && zoomLevel !== 'aggregated' && (
        <text
          y={24 * scale + 28}
          textAnchor="middle"
          fontSize={10}
          fill={THEME.textMuted}
          style={{ pointerEvents: 'none', userSelect: 'none' }}
        >
          {node.subType}
        </text>
      )}
    </g>
  )
}

interface PersonaNodeProps {
  node: SimNode
  isHovered: boolean
  isSelected: boolean
  isActive: boolean
  zoomLevel: ZoomLevel
  opacity: number
  onClick: () => void
  onMouseEnter: () => void
  onMouseLeave: () => void
}

function PersonaNode({
  node,
  isHovered,
  isSelected,
  isActive,
  zoomLevel,
  opacity,
  onClick,
  onMouseEnter,
  onMouseLeave,
}: PersonaNodeProps) {
  const fillColor = sentimentColor(node.sentiment)
  const r = TIER_RADIUS[node.tier] ?? 4
  const sourceColor = personaSourceColor(node.personaSource)

  // In aggregated view, personas are hidden (rendered as entity bubbles instead)
  if (zoomLevel === 'aggregated') return null

  const showLabel =
    zoomLevel === 'full' ||
    (zoomLevel === 'detail' && node.tier === 'power_creator') ||
    isHovered ||
    isSelected

  return (
    <g
      transform={`translate(${node.x},${node.y})`}
      style={{ opacity, cursor: 'pointer', transition: 'opacity 0.2s' }}
      onClick={onClick}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    >
      {/* Selection ring */}
      {isSelected && (
        <circle r={r + 5} fill="none" stroke={THEME.accent} strokeWidth={2} />
      )}
      {/* Pulse on active */}
      {isActive && (
        <circle r={r + 2} fill={fillColor} opacity={0.3}>
          <animate
            attributeName="r"
            values={`${r};${r * 2.5};${r}`}
            dur="1.5s"
            repeatCount="indefinite"
          />
          <animate
            attributeName="opacity"
            values="0.5;0;0.5"
            dur="1.5s"
            repeatCount="indefinite"
          />
        </circle>
      )}

      {/* Main circle */}
      <circle
        r={r}
        fill={fillColor}
        stroke={THEME.white}
        strokeWidth={1.5}
      />

      {/* Persona source badge (for non-generated) */}
      {sourceColor && (
        <circle
          cx={r * 0.7}
          cy={-r * 0.7}
          r={2}
          fill={sourceColor}
          stroke={THEME.white}
          strokeWidth={0.5}
        />
      )}

      {/* Label (zoom-dependent) */}
      {showLabel && node.label && (
        <g transform={`translate(0, ${r + 12})`} style={{ pointerEvents: 'none' }}>
          <rect
            x={-(node.label.length * 3.5)}
            y={-8}
            width={node.label.length * 7}
            height={14}
            fill="rgba(255,255,255,0.9)"
            stroke={THEME.border}
            strokeWidth={0.5}
            rx={3}
          />
          <text
            textAnchor="middle"
            dy={3}
            fontSize={10}
            fontWeight={500}
            fill={THEME.text}
            style={{ userSelect: 'none' }}
          >
            {node.label}
          </text>
        </g>
      )}
    </g>
  )
}

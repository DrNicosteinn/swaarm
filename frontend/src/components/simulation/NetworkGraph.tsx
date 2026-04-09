import { useCallback, useEffect, useRef, useState } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import type { GraphNode, GraphLink } from '@/lib/ws-events'

interface NetworkGraphProps {
  nodes: GraphNode[]
  links: GraphLink[]
  activeNodeIds: Set<string>
  hoveredNodeId: string | null
  onNodeHover: (node: GraphNode | null) => void
  onNodeClick: (node: GraphNode) => void
  width: number
  height: number
  isPulsing?: boolean // Pulse animation during LLM calls
}

const COMMUNITY_COLORS = [
  '#6366f1', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6',
  '#06b6d4', '#f97316', '#ec4899', '#14b8a6', '#84cc16',
]

// Entity type colors (used during preparation phase)
const ENTITY_TYPE_COLORS: Record<string, string> = {
  real_person: '#10b981',
  real_company: '#6366f1',
  role: '#f59e0b',
  institution: '#8b5cf6',
  media_outlet: '#ec4899',
  product: '#06b6d4',
  event: '#f97316',
}

// Persona source badge colors
const PERSONA_SOURCE_COLORS: Record<string, string> = {
  real_enriched: '#10b981',
  real_minimal: '#6ee7b7',
  role_based: '#f59e0b',
  generated: '#94a3b8',
}

function sentimentToColor(sentiment: number): string {
  if (sentiment > 0.3) return '#4ade80'
  if (sentiment > 0.1) return '#86efac'
  if (sentiment < -0.3) return '#f87171'
  if (sentiment < -0.1) return '#fca5a5'
  return '#cbd5e1'
}

function tierToSize(tier: string, followerCount: number): number {
  const base = Math.max(2.5, Math.min(7, Math.sqrt(followerCount + 1) * 0.8))
  switch (tier) {
    case 'power_creator': return base * 2
    case 'active_responder': return base * 1.5
    case 'selective_engager': return base * 1.2
    default: return base
  }
}

function paintNode(
  node: any,
  ctx: CanvasRenderingContext2D,
  globalScale: number,
  isActive: boolean,
  isHovered: boolean,
  pulsePhase: number,
) {
  const visualScale = 1 / Math.pow(Math.max(globalScale, 0.2), 1.1)
  const x = node.x
  const y = node.y
  if (x == null || y == null) return

  const isEntity = node.isEntity === true

  if (isEntity) {
    // ── Entity node: larger, entity-type color, always show label ──
    const importance = node.importance ?? 0.5
    const size = (8 + importance * 12) * visualScale
    const color = ENTITY_TYPE_COLORS[node.entityType] || '#6366f1'

    // Glow for entities
    ctx.beginPath()
    ctx.arc(x, y, size + 4 * visualScale, 0, 2 * Math.PI)
    ctx.fillStyle = color.replace(')', ', 0.15)').replace('rgb', 'rgba')
    ctx.fillStyle = `${color}26` // 15% opacity hex
    ctx.fill()

    // Main node — diamond shape for real entities, circle for roles
    if (node.entityType === 'real_person' || node.entityType === 'real_company') {
      // Diamond shape
      ctx.beginPath()
      ctx.moveTo(x, y - size)
      ctx.lineTo(x + size, y)
      ctx.lineTo(x, y + size)
      ctx.lineTo(x - size, y)
      ctx.closePath()
    } else {
      // Circle
      ctx.beginPath()
      ctx.arc(x, y, size, 0, 2 * Math.PI)
    }
    ctx.fillStyle = color
    ctx.fill()
    ctx.strokeStyle = '#ffffff'
    ctx.lineWidth = 2 * visualScale
    ctx.stroke()

    // Always show label for entities
    const label = node.label
    const fontSize = Math.max(8, Math.min(14, size * 0.7))
    ctx.font = `600 ${fontSize}px Inter, system-ui, sans-serif`
    ctx.textAlign = 'center'
    ctx.textBaseline = 'top'
    // Background for readability
    const metrics = ctx.measureText(label)
    const bgPad = 2
    ctx.fillStyle = 'rgba(0, 0, 0, 0.6)'
    ctx.fillRect(
      x - metrics.width / 2 - bgPad,
      y + size + 3 - bgPad,
      metrics.width + bgPad * 2,
      fontSize + bgPad * 2,
    )
    ctx.fillStyle = '#ffffff'
    ctx.fillText(label, x, y + size + 3)

    // Sub-type label below name
    if (node.subType) {
      const subFontSize = Math.max(6, fontSize * 0.7)
      ctx.font = `${subFontSize}px Inter, system-ui, sans-serif`
      ctx.fillStyle = 'rgba(255, 255, 255, 0.6)'
      ctx.fillText(node.subType, x, y + size + 3 + fontSize + 2)
    }
  } else {
    // ── Persona node: sentiment color, tier size, persona source badge ──
    const size = tierToSize(node.tier, node.followerCount) * visualScale
    const sentColor = sentimentToColor(node.sentiment)
    const communityColor = COMMUNITY_COLORS[node.communityId % COMMUNITY_COLORS.length]

    // Activity glow (active agents in current round)
    if (isActive) {
      const glowSize = size + 5 * visualScale + Math.sin(pulsePhase * 4) * 2 * visualScale
      ctx.beginPath()
      ctx.arc(x, y, glowSize, 0, 2 * Math.PI)
      ctx.fillStyle = 'rgba(99, 102, 241, 0.2)'
      ctx.fill()
    }

    if (isHovered) {
      ctx.beginPath()
      ctx.arc(x, y, size + 3 * visualScale, 0, 2 * Math.PI)
      ctx.strokeStyle = '#e91e63'
      ctx.lineWidth = 3 * visualScale
      ctx.stroke()
    }

    // Main circle
    ctx.beginPath()
    ctx.arc(x, y, size, 0, 2 * Math.PI)
    ctx.fillStyle = sentColor
    ctx.fill()
    ctx.strokeStyle = '#ffffff'
    ctx.lineWidth = 2 * visualScale
    ctx.stroke()

    // Community ring
    ctx.beginPath()
    ctx.arc(x, y, size + 1.5 * visualScale, 0, 2 * Math.PI)
    ctx.strokeStyle = communityColor
    ctx.lineWidth = 1 * visualScale
    ctx.stroke()

    // Persona source badge (small colored dot at top-right)
    const sourceColor = PERSONA_SOURCE_COLORS[node.personaSource || 'generated']
    if (sourceColor && node.personaSource !== 'generated') {
      const badgeSize = Math.max(2, size * 0.3)
      const badgeX = x + size * 0.7
      const badgeY = y - size * 0.7
      ctx.beginPath()
      ctx.arc(badgeX, badgeY, badgeSize, 0, 2 * Math.PI)
      ctx.fillStyle = sourceColor
      ctx.fill()
      ctx.strokeStyle = '#1f2937'
      ctx.lineWidth = 1 * visualScale
      ctx.stroke()
    }

    // Label (zoom-adaptive)
    const visualSize = size * globalScale
    if (visualSize > 8) {
      const label = node.label.split(' ')[0]
      const fontSize = Math.max(6, Math.min(12, size * 0.8))
      ctx.font = `${fontSize}px Inter, system-ui, sans-serif`
      ctx.textAlign = 'center'
      ctx.textBaseline = 'top'
      ctx.fillStyle = 'rgba(255,255,255,0.85)'
      ctx.fillText(label, x, y + size + 3)
    }
  }
}

function paintLink(
  link: any,
  ctx: CanvasRenderingContext2D,
  globalScale: number,
) {
  const source = link.source
  const target = link.target
  if (!source?.x || !target?.x) return

  const isEntityRelation = link.type === 'entity_relation'
  const label = link.label

  // Draw line
  ctx.beginPath()
  ctx.moveTo(source.x, source.y)
  ctx.lineTo(target.x, target.y)
  ctx.strokeStyle = isEntityRelation
    ? 'rgba(148, 163, 184, 0.5)'
    : 'rgba(148, 163, 184, 0.12)'
  ctx.lineWidth = isEntityRelation ? 2 / globalScale : 0.5 / globalScale
  ctx.stroke()

  // Draw label on entity relation edges (always) or persona edges (zoom-adaptive)
  if (label && (isEntityRelation || globalScale > 2.0)) {
    const midX = (source.x + target.x) / 2
    const midY = (source.y + target.y) / 2
    const angle = Math.atan2(target.y - source.y, target.x - source.x)

    // Flip text if it would be upside down
    const flipped = angle > Math.PI / 2 || angle < -Math.PI / 2
    const drawAngle = flipped ? angle + Math.PI : angle

    const fontSize = Math.max(7, Math.min(11, 10 / globalScale))
    ctx.save()
    ctx.translate(midX, midY)
    ctx.rotate(drawAngle)

    ctx.font = `${fontSize}px Inter, system-ui, sans-serif`
    const metrics = ctx.measureText(label)
    const pad = 3

    // Background rectangle
    ctx.fillStyle = 'rgba(15, 23, 42, 0.85)'
    ctx.fillRect(
      -metrics.width / 2 - pad,
      -fontSize / 2 - pad,
      metrics.width + pad * 2,
      fontSize + pad * 2,
    )

    // Text
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillStyle = isEntityRelation ? 'rgba(148, 163, 184, 0.9)' : 'rgba(148, 163, 184, 0.6)'
    ctx.fillText(label, 0, 0)

    ctx.restore()
  }
}

export function NetworkGraph({
  nodes,
  links,
  activeNodeIds,
  hoveredNodeId,
  onNodeHover,
  onNodeClick,
  width,
  height,
  isPulsing = false,
}: NetworkGraphProps) {
  const fgRef = useRef<any>(null)
  const stableNodesRef = useRef(new Map<string, any>())
  const linkSetRef = useRef(new Set<string>())
  const stableLinksRef = useRef<any[]>([])
  const forcesSetRef = useRef(false)
  const pulseRef = useRef(0)

  // Pulse animation counter
  useEffect(() => {
    if (!isPulsing && activeNodeIds.size === 0) return
    let frame: number
    const animate = () => {
      pulseRef.current += 0.05
      frame = requestAnimationFrame(animate)
    }
    frame = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(frame)
  }, [isPulsing, activeNodeIds.size])

  const [graphData, setGraphData] = useState<{ nodes: any[]; links: any[] }>({ nodes: [], links: [] })

  useEffect(() => {
    const stableNodes = stableNodesRef.current
    const linkSet = linkSetRef.current
    let changed = false

    for (const node of nodes) {
      const existing = stableNodes.get(node.id)
      if (existing) {
        existing.sentiment = node.sentiment
        // Update entity-specific fields if they changed
        if (node.label) existing.label = node.label
        if (node.occupation) existing.occupation = node.occupation
      } else {
        let initX = (Math.random() - 0.5) * 200
        let initY = (Math.random() - 0.5) * 200

        for (const link of links) {
          const neighborId =
            link.source === node.id ? link.target :
            link.target === node.id ? link.source : null
          if (neighborId) {
            const neighbor = stableNodes.get(neighborId as string)
            if (neighbor?.x != null) {
              initX = neighbor.x + (Math.random() - 0.5) * 50
              initY = neighbor.y + (Math.random() - 0.5) * 50
              break
            }
          }
        }

        const stableNode = { ...node, x: initX, y: initY }
        stableNodes.set(node.id, stableNode)
        changed = true
      }
    }

    for (const link of links) {
      const srcId = typeof link.source === 'string' ? link.source : (link.source as any)?.id
      const tgtId = typeof link.target === 'string' ? link.target : (link.target as any)?.id
      const key = `${srcId}->${tgtId}`
      if (!linkSet.has(key) && stableNodes.has(srcId) && stableNodes.has(tgtId)) {
        linkSet.add(key)
        stableLinksRef.current.push({
          source: srcId,
          target: tgtId,
          type: link.type,
          label: link.label || '',
        })
        changed = true
      }
    }

    if (changed) {
      setGraphData({
        nodes: Array.from(stableNodes.values()),
        links: [...stableLinksRef.current],
      })
    }
  }, [nodes, links])

  // Configure forces
  useEffect(() => {
    const fg = fgRef.current
    if (!fg || forcesSetRef.current) return
    forcesSetRef.current = true
    fg.d3Force('charge')?.strength(-250)
    fg.d3Force('link')?.distance(100).strength(0.2)
    fg.d3Force('center')?.strength(0.04)
  }, [])

  // Zoom to fit
  const hasZoomedRef = useRef(false)
  useEffect(() => {
    const fg = fgRef.current
    if (!fg || hasZoomedRef.current || nodes.length < 3) return
    hasZoomedRef.current = true
    setTimeout(() => fg.zoomToFit?.(400, 60), 500)
  }, [nodes.length])

  const nodeCanvasObject = useCallback(
    (node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
      paintNode(node, ctx, globalScale, activeNodeIds.has(node.id), hoveredNodeId === node.id, pulseRef.current)
    },
    [activeNodeIds, hoveredNodeId],
  )

  const linkCanvasObject = useCallback(
    (link: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
      paintLink(link, ctx, globalScale)
    },
    [],
  )

  const entityCount = nodes.filter(n => n.isEntity).length
  const personaCount = nodes.filter(n => !n.isEntity).length

  return (
    <div className="relative w-full h-full bg-gray-950 rounded-xl overflow-hidden">
      {/* Dot grid background */}
      <div
        className="absolute inset-0 opacity-15 pointer-events-none"
        style={{
          backgroundImage: 'radial-gradient(circle, rgba(148,163,184,0.3) 1px, transparent 1px)',
          backgroundSize: '24px 24px',
        }}
      />

      {/* Pulse overlay during LLM processing */}
      {isPulsing && (
        <div className="absolute inset-0 pointer-events-none z-10">
          <div className="absolute inset-0 animate-pulse bg-gradient-radial from-indigo-500/5 to-transparent" />
        </div>
      )}

      <ForceGraph2D
        ref={fgRef}
        graphData={graphData}
        width={width}
        height={height}
        nodeCanvasObject={nodeCanvasObject}
        nodePointerAreaPaint={(node: any, color: string, ctx: CanvasRenderingContext2D, globalScale: number) => {
          const visualScale = 1 / Math.pow(Math.max(globalScale, 0.2), 1.1)
          const size = node.isEntity
            ? (8 + (node.importance ?? 0.5) * 12) * visualScale
            : tierToSize(node.tier, node.followerCount) * visualScale
          ctx.beginPath()
          ctx.arc(node.x, node.y, size + 4, 0, 2 * Math.PI)
          ctx.fillStyle = color
          ctx.fill()
        }}
        linkCanvasObject={linkCanvasObject}
        linkCanvasObjectMode={() => 'replace'}
        onNodeHover={(node: any) => onNodeHover(node || null)}
        onNodeClick={(node: any) => { if (node) onNodeClick(node) }}
        enableNodeDrag={true}
        enableZoomInteraction={true}
        cooldownTime={1500}
        warmupTicks={30}
        d3AlphaDecay={0.08}
        d3VelocityDecay={0.45}
        backgroundColor="transparent"
        minZoom={0.3}
        maxZoom={5}
      />

      {/* Legend */}
      <div className="absolute bottom-3 left-3 bg-gray-900/80 backdrop-blur-sm rounded-lg px-3 py-1.5 text-xs text-gray-400">
        {entityCount > 0 && <span>{entityCount} Entitaeten</span>}
        {entityCount > 0 && personaCount > 0 && <span> &middot; </span>}
        {personaCount > 0 && <span>{personaCount} Personas</span>}
        <span> &middot; {links.length} Verbindungen</span>
      </div>
    </div>
  )
}

export function NodeTooltip({ node, position }: { node: GraphNode | null; position: { x: number; y: number } }) {
  if (!node) return null

  const tierLabels: Record<string, string> = {
    power_creator: 'Meinungsfuehrer',
    active_responder: 'Aktiver Teilnehmer',
    selective_engager: 'Gelegentlicher Teilnehmer',
    observer: 'Beobachter',
  }

  const entityTypeLabels: Record<string, string> = {
    real_person: 'Person',
    real_company: 'Unternehmen',
    role: 'Rolle',
    institution: 'Institution',
    media_outlet: 'Medium',
    product: 'Produkt',
    event: 'Ereignis',
  }

  const personaSourceLabels: Record<string, string> = {
    real_enriched: 'Real (recherchiert)',
    real_minimal: 'Real (minimal)',
    role_based: 'Rollenbasiert',
    generated: 'Generiert',
  }

  const sentimentLabel =
    node.sentiment > 0.3 ? 'Sehr positiv' :
    node.sentiment > 0.1 ? 'Positiv' :
    node.sentiment < -0.3 ? 'Sehr negativ' :
    node.sentiment < -0.1 ? 'Negativ' : 'Neutral'

  const sentimentTextColor =
    node.sentiment > 0.1 ? 'text-green-400' :
    node.sentiment < -0.1 ? 'text-red-400' : 'text-gray-400'

  return (
    <div
      className="fixed z-50 pointer-events-none"
      style={{
        left: position.x + 16,
        top: position.y - 8,
        transform: position.x > window.innerWidth / 2 ? 'translateX(calc(-100% - 32px))' : undefined,
      }}
    >
      <div className="bg-gray-900 border border-gray-700 rounded-xl shadow-2xl p-4 min-w-[220px]">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-3 h-3 rounded-full" style={{ backgroundColor: sentimentToColor(node.sentiment) }} />
          <span className="font-semibold text-white text-sm">{node.label}</span>
          {node.personaSource && node.personaSource !== 'generated' && (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400">REAL</span>
          )}
        </div>
        <div className="space-y-1.5 text-xs">
          {node.isEntity && node.entityType && (
            <div className="flex justify-between">
              <span className="text-gray-500">Entity-Typ</span>
              <span className="text-gray-300">{entityTypeLabels[node.entityType] || node.entityType}</span>
            </div>
          )}
          {node.subType && (
            <div className="flex justify-between">
              <span className="text-gray-500">Sub-Typ</span>
              <span className="text-gray-300">{node.subType}</span>
            </div>
          )}
          {node.occupation && (
            <div className="flex justify-between">
              <span className="text-gray-500">Beruf</span>
              <span className="text-gray-300">{node.occupation}</span>
            </div>
          )}
          {node.role && (
            <div className="flex justify-between">
              <span className="text-gray-500">Rolle</span>
              <span className="text-gray-300">{node.role}</span>
            </div>
          )}
          {!node.isEntity && (
            <div className="flex justify-between">
              <span className="text-gray-500">Typ</span>
              <span className="text-gray-300">{tierLabels[node.tier] || node.tier}</span>
            </div>
          )}
          {node.personaSource && (
            <div className="flex justify-between">
              <span className="text-gray-500">Quelle</span>
              <span className="text-gray-300">{personaSourceLabels[node.personaSource] || node.personaSource}</span>
            </div>
          )}
          <div className="flex justify-between">
            <span className="text-gray-500">Stimmung</span>
            <span className={sentimentTextColor}>{sentimentLabel}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Follower</span>
            <span className="text-gray-300">{node.followerCount}</span>
          </div>
        </div>
      </div>
    </div>
  )
}

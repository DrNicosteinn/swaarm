import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { select } from 'd3-selection'
import 'd3-transition' // Augments d3-selection with .transition()
import { zoom as d3zoom, zoomIdentity, type ZoomTransform } from 'd3-zoom'
import type { GraphNode as StreamNode, GraphLink as StreamLink } from '@/lib/ws-events'
import {
  type SimNode,
  type SimLink,
  type ZoomLevel,
  streamNodeToSimNode,
  streamLinkToSimLink,
  zoomLevelFromScale,
} from './types'
import { useForceGraph } from './hooks/useForceGraph'
import { ClusterHulls } from './layers/ClusterHulls'
import { EdgesLayer } from './layers/EdgesLayer'
import { NodesLayer } from './layers/NodesLayer'
import { THEME } from './utils/colors'
import { GraphControls } from './controls/GraphControls'
import { SearchBox } from './controls/SearchBox'
import { EntityLegend } from './controls/EntityLegend'
import { MiniMap } from './controls/MiniMap'

export interface NetworkGraphProps {
  nodes: StreamNode[]
  links: StreamLink[]
  activeNodeIds: Set<string>
  width: number
  height: number
  onNodeSelect: (node: SimNode | null) => void
}

export function NetworkGraph({
  nodes: streamNodes,
  links: streamLinks,
  activeNodeIds,
  width,
  height,
  onNodeSelect,
}: NetworkGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const zoomBehaviorRef = useRef<ReturnType<typeof d3zoom<SVGSVGElement, unknown>> | null>(null)
  const [transform, setTransform] = useState<ZoomTransform>(zoomIdentity)

  const [hoveredId, setHoveredId] = useState<string | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [hiddenTypes, setHiddenTypes] = useState<Set<string>>(new Set())

  const handleToggleType = useCallback((type: string) => {
    setHiddenTypes(prev => {
      const next = new Set(prev)
      if (next.has(type)) next.delete(type)
      else next.add(type)
      return next
    })
  }, [])

  // Convert stream nodes to sim nodes (stable: only when count changes)
  const simNodes: SimNode[] = useMemo(
    () => streamNodes.map(streamNodeToSimNode),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [streamNodes.length],
  )

  const simLinks: SimLink[] = useMemo(
    () => streamLinks.map(streamLinkToSimLink),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [streamLinks.length],
  )

  // Update sentiments in-place on existing nodes (avoids re-creating simulation)
  useEffect(() => {
    const sentimentById = new Map(streamNodes.map(n => [n.id, n.sentiment]))
    simNodes.forEach(n => {
      const newSentiment = sentimentById.get(n.id)
      if (newSentiment != null) n.sentiment = newSentiment
    })
  }, [streamNodes, simNodes])

  // Run force simulation
  const { positionedNodes, positionedLinks } = useForceGraph(simNodes, simLinks, {
    width,
    height,
  })

  const visibleNodes = useMemo(() => {
    if (hiddenTypes.size === 0) return positionedNodes
    const hiddenEntityIds = new Set(
      positionedNodes.filter(n => n.isEntity && n.entityType && hiddenTypes.has(n.entityType)).map(n => n.id)
    )
    const personaHiddenLinks = new Map<string, number>()
    const personaVisibleLinks = new Map<string, number>()
    positionedLinks.forEach(link => {
      if (link.type !== 'persona_entity') return
      const src = typeof link.source === 'string' ? link.source : link.source.id
      const tgt = typeof link.target === 'string' ? link.target : link.target.id
      const personaId = hiddenEntityIds.has(src) ? tgt : hiddenEntityIds.has(tgt) ? src : null
      if (personaId) {
        personaHiddenLinks.set(personaId, (personaHiddenLinks.get(personaId) ?? 0) + 1)
      }
      const isVisible = !hiddenEntityIds.has(src) && !hiddenEntityIds.has(tgt)
      if (isVisible) {
        const srcNode = positionedNodes.find(n => n.id === src)
        const nonEntityId = srcNode?.isEntity ? tgt : src
        personaVisibleLinks.set(nonEntityId, (personaVisibleLinks.get(nonEntityId) ?? 0) + 1)
      }
    })
    return positionedNodes.filter(n => {
      if (n.isEntity) {
        return !n.entityType || !hiddenTypes.has(n.entityType)
      }
      const hidden = personaHiddenLinks.get(n.id) ?? 0
      const visible = personaVisibleLinks.get(n.id) ?? 0
      return visible > 0 || hidden === 0
    })
  }, [positionedNodes, positionedLinks, hiddenTypes])

  const visibleNodeIds = useMemo(() => new Set(visibleNodes.map(n => n.id)), [visibleNodes])

  const visibleLinks = useMemo(() => {
    if (hiddenTypes.size === 0) return positionedLinks
    return positionedLinks.filter(link => {
      const src = typeof link.source === 'string' ? link.source : link.source.id
      const tgt = typeof link.target === 'string' ? link.target : link.target.id
      return visibleNodeIds.has(src) && visibleNodeIds.has(tgt)
    })
  }, [positionedLinks, visibleNodeIds, hiddenTypes])

  // Initialize d3-zoom on mount
  useEffect(() => {
    if (!svgRef.current) return
    const svg = select(svgRef.current)

    const zoomBehavior = d3zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.2, 5])
      .on('zoom', event => {
        setTransform(event.transform)
      })

    svg.call(zoomBehavior)
    zoomBehaviorRef.current = zoomBehavior

    return () => {
      svg.on('.zoom', null)
    }
  }, [])

  // Compute zoom level from current scale
  const zoomLevel: ZoomLevel = zoomLevelFromScale(transform.k)

  // Focus mode — hovered node shows its 1-hop neighborhood
  const focusedIds = useMemo((): Set<string> | null => {
    if (!hoveredId) return null
    const ids = new Set<string>([hoveredId])
    positionedLinks.forEach(link => {
      const src = typeof link.source === 'string' ? link.source : link.source.id
      const tgt = typeof link.target === 'string' ? link.target : link.target.id
      if (src === hoveredId) ids.add(tgt)
      if (tgt === hoveredId) ids.add(src)
    })
    return ids
  }, [hoveredId, positionedLinks])

  const viewport = useMemo(() => {
    const k = transform.k
    return {
      x: -transform.x / k,
      y: -transform.y / k,
      width: width / k,
      height: height / k,
    }
  }, [transform, width, height])

  const handleMiniMapChange = useCallback(
    (worldX: number, worldY: number) => {
      if (!svgRef.current || !zoomBehaviorRef.current) return
      const scale = transform.k
      const tx = width / 2 - worldX * scale
      const ty = height / 2 - worldY * scale
      select(svgRef.current)
        .transition()
        .duration(200)
        .call(
          zoomBehaviorRef.current.transform,
          zoomIdentity.translate(tx, ty).scale(scale),
        )
    },
    [transform.k, width, height],
  )

  const handleNodeClick = useCallback((node: SimNode) => {
    setSelectedId(prev => (prev === node.id ? null : node.id))
    onNodeSelect(node)
  }, [onNodeSelect])

  const handleBackgroundClick = useCallback(() => {
    setSelectedId(null)
    onNodeSelect(null)
  }, [onNodeSelect])

  const handleZoomIn = useCallback(() => {
    if (!svgRef.current || !zoomBehaviorRef.current) return
    select(svgRef.current)
      .transition()
      .duration(250)
      .call(zoomBehaviorRef.current.scaleBy, 1.4)
  }, [])

  const handleZoomOut = useCallback(() => {
    if (!svgRef.current || !zoomBehaviorRef.current) return
    select(svgRef.current)
      .transition()
      .duration(250)
      .call(zoomBehaviorRef.current.scaleBy, 0.7)
  }, [])

  const handleReset = useCallback(() => {
    if (!svgRef.current || !zoomBehaviorRef.current) return
    select(svgRef.current)
      .transition()
      .duration(400)
      .call(zoomBehaviorRef.current.transform, zoomIdentity)
  }, [])

  const handleFitToContent = useCallback(() => {
    if (!svgRef.current || !zoomBehaviorRef.current || positionedNodes.length === 0) return
    const xs = positionedNodes.map(n => n.x ?? 0)
    const ys = positionedNodes.map(n => n.y ?? 0)
    const minX = Math.min(...xs)
    const maxX = Math.max(...xs)
    const minY = Math.min(...ys)
    const maxY = Math.max(...ys)
    const contentW = maxX - minX + 120
    const contentH = maxY - minY + 120
    const scale = Math.min(width / contentW, height / contentH, 2)
    const tx = width / 2 - ((minX + maxX) / 2) * scale
    const ty = height / 2 - ((minY + maxY) / 2) * scale
    select(svgRef.current)
      .transition()
      .duration(500)
      .call(
        zoomBehaviorRef.current.transform,
        zoomIdentity.translate(tx, ty).scale(scale),
      )
  }, [positionedNodes, width, height])

  const handleSearchSelect = useCallback((node: SimNode) => {
    if (!svgRef.current || !zoomBehaviorRef.current || node.x == null || node.y == null) return
    const targetScale = 2
    const tx = width / 2 - node.x * targetScale
    const ty = height / 2 - node.y * targetScale
    select(svgRef.current)
      .transition()
      .duration(500)
      .call(
        zoomBehaviorRef.current.transform,
        zoomIdentity.translate(tx, ty).scale(targetScale),
      )
    setSelectedId(node.id)
    onNodeSelect(node)
  }, [width, height, onNodeSelect])

  return (
    <div
      className="relative w-full h-full overflow-hidden"
      style={{
        backgroundColor: THEME.bg,
        backgroundImage: `radial-gradient(${THEME.dotGrid} 1.5px, transparent 1.5px)`,
        backgroundSize: '24px 24px',
      }}
    >
      <svg
        ref={svgRef}
        width={width}
        height={height}
        onClick={handleBackgroundClick}
      >
        <defs>
          <filter id="entity-shadow">
            <feDropShadow dx="0" dy="2" stdDeviation="4" floodOpacity="0.12" />
          </filter>
        </defs>

        <g transform={`translate(${transform.x},${transform.y}) scale(${transform.k})`}>
          <ClusterHulls
            nodes={visibleNodes}
            links={visibleLinks}
            zoomLevel={zoomLevel}
          />
          <EdgesLayer
            links={visibleLinks}
            nodes={visibleNodes}
            zoomLevel={zoomLevel}
            focusedIds={focusedIds}
            hoveredLinkIds={new Set()}
          />
          <NodesLayer
            nodes={visibleNodes}
            zoomLevel={zoomLevel}
            hoveredId={hoveredId}
            selectedId={selectedId}
            activeIds={activeNodeIds}
            focusedIds={focusedIds}
            onNodeClick={(node) => {
              handleNodeClick(node)
            }}
            onNodeHover={(node) => setHoveredId(node?.id ?? null)}
          />
        </g>

        {/* Footer stats */}
        <g transform={`translate(16, ${height - 24})`}>
          <rect x={-4} y={-14} width={200} height={20} rx={6} fill="rgba(255,255,255,0.9)" stroke={THEME.border} />
          <text fontSize={11} fill={THEME.textMuted} style={{ userSelect: 'none' }}>
            {visibleNodes.filter(n => n.isEntity).length} Entitäten · {visibleNodes.filter(n => !n.isEntity).length} Personas · {visibleLinks.length} Verbindungen
          </text>
        </g>
      </svg>
      <SearchBox nodes={visibleNodes} onSelect={handleSearchSelect} />
      <EntityLegend
        nodes={positionedNodes}
        hiddenTypes={hiddenTypes}
        onToggle={handleToggleType}
      />
      <GraphControls
        onZoomIn={handleZoomIn}
        onZoomOut={handleZoomOut}
        onFitToContent={handleFitToContent}
        onReset={handleReset}
      />
      <MiniMap
        nodes={visibleNodes}
        viewport={viewport}
        onViewportChange={handleMiniMapChange}
      />
    </div>
  )
}

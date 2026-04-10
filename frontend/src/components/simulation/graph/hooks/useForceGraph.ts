import { useEffect, useRef, useState } from 'react'
import {
  forceSimulation,
  forceLink,
  forceManyBody,
  forceCollide,
  forceRadial,
  type Simulation,
} from 'd3-force'
import type { SimNode, SimLink } from '../types'
import { computeSkeletonLayout } from '../utils/skeletonLayout'

export interface ForceGraphConfig {
  width: number
  height: number
}

export interface ForceGraphResult {
  positionedNodes: SimNode[]
  positionedLinks: SimLink[]
}

/**
 * Custom hook that runs a D3 force simulation on a set of nodes and links.
 *
 * Layout strategy:
 * 1. Entities are placed at fixed positions via computeSkeletonLayout
 * 2. Entities are pinned via fx/fy so force simulation can't move them
 * 3. Personas orbit their linked entity via forceRadial
 * 4. forceCollide prevents node overlap
 * 5. forceManyBody provides gentle repulsion
 */
export function useForceGraph(
  nodes: SimNode[],
  links: SimLink[],
  config: ForceGraphConfig,
): ForceGraphResult {
  const simulationRef = useRef<Simulation<SimNode, SimLink> | null>(null)
  const [, setVersion] = useState(0)
  const nodesRef = useRef<SimNode[]>([])
  const linksRef = useRef<SimLink[]>([])

  useEffect(() => {
    if (nodes.length === 0) {
      nodesRef.current = []
      linksRef.current = []
      setVersion(v => v + 1)
      return
    }

    // Separate entities and personas
    const entities = nodes.filter(n => n.isEntity)
    const personas = nodes.filter(n => !n.isEntity)

    // Compute fixed positions for entities
    const entityPositions = computeSkeletonLayout(entities, config.width, config.height)
    entities.forEach((e, i) => {
      e.fx = entityPositions[i].x
      e.fy = entityPositions[i].y
      e.x = entityPositions[i].x
      e.y = entityPositions[i].y
    })

    // Initialize persona positions near their linked entity
    const entityById = new Map(entities.map(e => [e.id, e]))
    personas.forEach(p => {
      if (p.x != null && p.y != null) return

      const linkedEntity = links.find(l => {
        const src = typeof l.source === 'string' ? l.source : l.source.id
        const tgt = typeof l.target === 'string' ? l.target : l.target.id
        return (src === p.id && entityById.has(tgt)) || (tgt === p.id && entityById.has(src))
      })

      if (linkedEntity) {
        const src = typeof linkedEntity.source === 'string' ? linkedEntity.source : linkedEntity.source.id
        const tgt = typeof linkedEntity.target === 'string' ? linkedEntity.target : linkedEntity.target.id
        const entityId = entityById.has(src) ? src : tgt
        const entity = entityById.get(entityId)!
        const angle = Math.random() * 2 * Math.PI
        const radius = 100 + Math.random() * 50
        p.x = entity.fx! + Math.cos(angle) * radius
        p.y = entity.fy! + Math.sin(angle) * radius
      } else {
        p.x = config.width / 2 + (Math.random() - 0.5) * 200
        p.y = config.height / 2 + (Math.random() - 0.5) * 200
      }
    })

    // Build link objects for d3-force (it mutates source/target to node refs)
    const simLinks = links.map(l => ({
      ...l,
      source: typeof l.source === 'string' ? l.source : l.source.id,
      target: typeof l.target === 'string' ? l.target : l.target.id,
    }))

    // Stop previous simulation
    if (simulationRef.current) {
      simulationRef.current.stop()
    }

    // Create new simulation
    const simulation = forceSimulation<SimNode>(nodes)
      .force(
        'link',
        forceLink<SimNode, SimLink>(simLinks as unknown as SimLink[])
          .id(d => d.id)
          .strength(0.3)
          .distance(80),
      )
      .force('charge', forceManyBody().strength(-80))
      .force('collide', forceCollide(14))
      .alpha(0.8)
      .alphaDecay(0.05)

    // Add per-entity radial force
    entities.forEach(entity => {
      const linkedPersonaIds = new Set<string>()
      simLinks.forEach(l => {
        const src = l.source as string
        const tgt = l.target as string
        if (src === entity.id) linkedPersonaIds.add(tgt)
        if (tgt === entity.id) linkedPersonaIds.add(src)
      })

      if (linkedPersonaIds.size > 0) {
        const radius = 80 + Math.sqrt(linkedPersonaIds.size) * 10
        const radialForce = forceRadial<SimNode>(
          radius,
          entity.fx!,
          entity.fy!,
        ).strength((d) => (linkedPersonaIds.has(d.id) ? 0.5 : 0))
        simulation.force(`radial-${entity.id}`, radialForce)
      }
    })

    simulation.on('tick', () => {
      nodesRef.current = [...nodes]
      linksRef.current = simLinks as unknown as SimLink[]
      setVersion(v => v + 1)
    })

    // Initial snapshot so tests can read positions before ticks fire
    nodesRef.current = [...nodes]
    linksRef.current = simLinks as unknown as SimLink[]

    simulationRef.current = simulation

    return () => {
      simulation.stop()
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes.length, links.length, config.width, config.height])

  return {
    positionedNodes: nodesRef.current.length > 0 ? nodesRef.current : nodes,
    positionedLinks: linksRef.current.length > 0 ? linksRef.current : links,
  }
}

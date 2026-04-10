import type { SimulationNodeDatum, SimulationLinkDatum } from 'd3-force'
import type { GraphNode as StreamNode, GraphLink as StreamLink } from '@/lib/ws-events'

/**
 * Internal graph node used by the force simulation.
 * Extends SimulationNodeDatum for d3-force compatibility.
 */
export interface SimNode extends SimulationNodeDatum {
  id: string
  label: string
  // Entity-specific
  isEntity: boolean
  entityType?: string
  subType?: string
  importance?: number
  // Persona-specific
  communityId?: number
  sentiment: number
  followerCount: number
  tier: string
  role?: string
  occupation?: string
  personaSource?: string
  // Simulation state (populated by d3-force)
  x?: number
  y?: number
  vx?: number
  vy?: number
  fx?: number | null
  fy?: number | null
}

export type EdgeKind = 'persona_entity' | 'entity_relation' | 'persona_relation' | 'follow'

export interface SimLink extends SimulationLinkDatum<SimNode> {
  source: string | SimNode
  target: string | SimNode
  type: EdgeKind
  label?: string
}

export type ZoomLevel = 'aggregated' | 'structure' | 'detail' | 'full'

export interface GraphBounds {
  minX: number
  maxX: number
  minY: number
  maxY: number
}

export function streamNodeToSimNode(node: StreamNode): SimNode {
  return {
    id: node.id,
    label: node.label,
    isEntity: node.isEntity ?? false,
    entityType: node.entityType,
    subType: node.subType,
    importance: node.importance,
    communityId: node.communityId,
    sentiment: node.sentiment,
    followerCount: node.followerCount,
    tier: node.tier,
    role: node.role,
    occupation: node.occupation,
    personaSource: node.personaSource,
    x: node.x,
    y: node.y,
  }
}

export function streamLinkToSimLink(link: StreamLink): SimLink {
  return {
    source: link.source,
    target: link.target,
    type: link.type as EdgeKind,
    label: link.label,
  }
}

export function zoomLevelFromScale(scale: number): ZoomLevel {
  if (scale < 0.6) return 'aggregated'
  if (scale < 1.5) return 'structure'
  if (scale < 2.5) return 'detail'
  return 'full'
}

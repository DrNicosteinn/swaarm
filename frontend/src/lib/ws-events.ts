/**
 * WebSocket event types for simulation live-streaming.
 */

export interface AgentActionEvent {
  agent_id: string
  agent_name: string
  action_type: string
  content: string | null
  target_post_id: string | null
  target_user_id: string | null
  sentiment: number
}

export interface GraphNode {
  id: string
  label: string
  communityId: number
  sentiment: number
  followerCount: number
  tier: string
  role?: string
  occupation?: string
  // Entity-pipeline fields
  entityType?: string       // "real_person", "real_company", "role", etc.
  subType?: string          // "CEO", "Journalist", "Kunde"
  personaSource?: string    // "real_enriched", "role_based", "generated"
  isEntity?: boolean        // true for entity nodes (before persona phase)
  importance?: number       // 0-1, for node size in entity phase
  x?: number
  y?: number
}

export interface GraphLink {
  source: string
  target: string
  type: string
  label?: string            // "ist CEO von", "konkurriert mit"
}

// ── Existing event types ────────────────────────────────────────────

export interface RoundCompleteEvent {
  type: 'round_complete'
  round: number
  data: {
    active_agents: number
    posts_created: number
    avg_sentiment: number
    cost_usd: number
    actions: AgentActionEvent[]
    new_nodes: GraphNode[]
    new_links: GraphLink[]
  }
}

export interface SimulationCompleteEvent {
  type: 'simulation_complete'
  round: number
  data: {
    status: string
    completed_rounds: number
    total_cost_usd: number
    duration_seconds: number
  }
}

export interface SnapshotEvent {
  type: 'snapshot'
  data: {
    current_round: number
    total_rounds: number
    nodes: GraphNode[]
    links: GraphLink[]
  }
}

// ── New entity-pipeline event types ─────────────────────────────────

export interface PhaseChangedEvent {
  type: 'phase_changed'
  data: {
    phase: string
    detail: string
    persona_count?: number
    recommended_platform?: string
  }
}

export interface EntityExtractedEvent {
  type: 'entity_extracted'
  data: {
    node: GraphNode
    links: GraphLink[]
  }
}

export interface EntityEnrichedEvent {
  type: 'entity_enriched'
  data: {
    entity_name: string
    node: Partial<GraphNode>
  }
}

export interface EnrichmentFailedEvent {
  type: 'enrichment_failed'
  data: {
    entity_name: string
    reason: string
  }
}

export interface PersonaBatchEvent {
  type: 'persona_batch'
  data: {
    nodes: GraphNode[]
    links: GraphLink[]
  }
}

export type SimulationEvent =
  | RoundCompleteEvent
  | SimulationCompleteEvent
  | SnapshotEvent
  | PhaseChangedEvent
  | EntityExtractedEvent
  | EntityEnrichedEvent
  | EnrichmentFailedEvent
  | PersonaBatchEvent
  | { type: 'pong' }

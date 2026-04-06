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
  x?: number
  y?: number
}

export interface GraphLink {
  source: string
  target: string
  type: string
}

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

export type SimulationEvent =
  | RoundCompleteEvent
  | SimulationCompleteEvent
  | SnapshotEvent
  | { type: 'pong' }

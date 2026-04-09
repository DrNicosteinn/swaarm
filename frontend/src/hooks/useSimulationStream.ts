import { useCallback, useEffect, useRef, useState } from 'react'
import type { SimulationEvent, AgentActionEvent, GraphNode, GraphLink } from '@/lib/ws-events'
import type { FeedEvent } from '@/components/simulation/LiveFeed'

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error'

const PING_INTERVAL_MS = 30000
const MAX_RECONNECT = 10
const MAX_FEED_EVENTS = 500

function getBackoffDelay(attempt: number): number {
  const delay = Math.min(1000 * 2 ** attempt, 30000)
  return delay + Math.random() * delay * 0.3
}

export type SimulationPhase =
  | 'connecting'
  | 'analyzing'
  | 'extracting_entities'
  | 'enriching'
  | 'generating_personas'
  | 'configuring'
  | 'simulating'
  | 'done'

export interface SimulationStreamState {
  status: ConnectionStatus
  currentRound: number
  totalRounds: number
  actions: AgentActionEvent[]
  avgSentiment: number
  activeCounts: number[]
  // Graph data
  nodes: GraphNode[]
  links: GraphLink[]
  activeNodeIds: Set<string>
  // Feed events (unified)
  feedEvents: FeedEvent[]
  // Sentiment history per round
  sentimentHistory: number[]
  // Counters
  isComplete: boolean
  // Entity-pipeline state
  currentPhase: SimulationPhase
  phaseDetail: string
  entityCount: number
  enrichedCount: number
  personaCount: number
  recommendedPlatform: string
  isConfiguring: boolean
}

export function useSimulationStream(simulationId: string | null, token: string | null) {
  const [state, setState] = useState<SimulationStreamState>({
    status: 'disconnected',
    currentRound: 0,
    totalRounds: 0,
    actions: [],
    avgSentiment: 0,
    activeCounts: [],
    nodes: [],
    links: [],
    activeNodeIds: new Set(),
    feedEvents: [],
    sentimentHistory: [],
    isComplete: false,
    currentPhase: 'connecting',
    phaseDetail: '',
    entityCount: 0,
    enrichedCount: 0,
    personaCount: 0,
    recommendedPlatform: 'public',
    isConfiguring: false,
  })

  const wsRef = useRef<WebSocket | null>(null)
  const attemptRef = useRef(0)
  const pingRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const cleanup = useCallback(() => {
    if (pingRef.current) clearInterval(pingRef.current)
    if (wsRef.current) {
      wsRef.current.onclose = null
      wsRef.current.close()
      wsRef.current = null
    }
  }, [])

  const connect = useCallback(() => {
    if (!simulationId || !token) return
    cleanup()

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const url = `${protocol}//${host}/ws/simulation/${simulationId}?token=${token}`

    setState((s) => ({ ...s, status: 'connecting' }))
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      setState((s) => ({ ...s, status: 'connected' }))
      attemptRef.current = 0
      pingRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) ws.send('ping')
      }, PING_INTERVAL_MS)
    }

    ws.onmessage = (msg) => {
      try {
        const event: SimulationEvent = JSON.parse(msg.data)
        if (event.type === 'pong') return

        if (event.type === 'phase_changed') {
          const { phase, detail, persona_count, recommended_platform } = event.data
          const feedEvent: FeedEvent = { kind: 'phase_change', phase, detail }
          setState((s) => ({
            ...s,
            currentPhase: phase as SimulationPhase,
            phaseDetail: detail,
            isConfiguring: phase === 'configuring',
            personaCount: persona_count ?? s.personaCount,
            recommendedPlatform: recommended_platform ?? s.recommendedPlatform,
            feedEvents: [...s.feedEvents, feedEvent].slice(-MAX_FEED_EVENTS),
          }))
        } else if (event.type === 'entity_extracted') {
          const { node, links } = event.data
          const feedEvent: FeedEvent = {
            kind: 'entity_found',
            entityName: node.label,
            entityType: node.entityType ?? '',
            subType: node.subType ?? '',
          }
          setState((s) => ({
            ...s,
            nodes: [...s.nodes, node],
            links: [...s.links, ...links],
            entityCount: s.entityCount + 1,
            feedEvents: [...s.feedEvents, feedEvent].slice(-MAX_FEED_EVENTS),
          }))
        } else if (event.type === 'entity_enriched') {
          const { entity_name, node: partialNode } = event.data
          const feedEvent: FeedEvent = {
            kind: 'entity_enriched',
            entityName: entity_name,
          }
          setState((s) => ({
            ...s,
            enrichedCount: s.enrichedCount + 1,
            nodes: s.nodes.map((n) =>
              n.id === partialNode.id
                ? { ...n, ...partialNode }
                : n
            ),
            feedEvents: [...s.feedEvents, feedEvent].slice(-MAX_FEED_EVENTS),
          }))
        } else if (event.type === 'enrichment_failed') {
          const feedEvent: FeedEvent = {
            kind: 'enrichment_failed',
            entityName: event.data.entity_name,
            reason: event.data.reason,
          }
          setState((s) => ({
            ...s,
            feedEvents: [...s.feedEvents, feedEvent].slice(-MAX_FEED_EVENTS),
          }))
        } else if (event.type === 'persona_batch') {
          const { nodes: newNodes, links: newLinks } = event.data
          setState((s) => ({
            ...s,
            nodes: mergeNodes(s.nodes, newNodes),
            links: [...s.links, ...newLinks],
            personaCount: s.personaCount + newNodes.length,
          }))
        } else if (event.type === 'round_complete') {
          const { actions, new_nodes, new_links, active_agents, avg_sentiment } = event.data
          const activeIds = new Set(actions.map((a) => a.agent_id))

          const newFeedEvents: FeedEvent[] = []
          newFeedEvents.push({
            kind: 'round_marker',
            round: event.round,
            activeAgents: active_agents,
          })

          if (new_nodes && new_nodes.length > 0) {
            for (const node of new_nodes) {
              newFeedEvents.push({ kind: 'persona_spawned', data: node })
            }
          }

          for (const action of actions) {
            if (action.action_type !== 'do_nothing') {
              newFeedEvents.push({ kind: 'action', data: action, round: event.round })
            }
          }

          setState((s) => ({
            ...s,
            currentRound: event.round,
            currentPhase: 'simulating',
            avgSentiment: avg_sentiment,
            actions: [...s.actions, ...actions].slice(-200),
            activeCounts: [...s.activeCounts, active_agents],
            nodes: new_nodes && new_nodes.length > 0
              ? mergeNodes(s.nodes, new_nodes)
              : updateNodeSentiments(s.nodes, actions),
            links: new_links && new_links.length > 0
              ? [...s.links, ...new_links]
              : s.links,
            activeNodeIds: activeIds,
            feedEvents: [...s.feedEvents, ...newFeedEvents].slice(-MAX_FEED_EVENTS),
            sentimentHistory: [...s.sentimentHistory, avg_sentiment],
          }))
        } else if (event.type === 'simulation_complete') {
          setState((s) => ({
            ...s,
            currentRound: event.data.completed_rounds,
            currentPhase: 'done',
            status: 'disconnected',
            isComplete: true,
            activeNodeIds: new Set(),
          }))
        } else if (event.type === 'snapshot') {
          const feedEvent: FeedEvent = {
            kind: 'phase_change',
            phase: 'simulating',
            detail: `Runde ${event.data.current_round}/${event.data.total_rounds}`,
          }
          setState((s) => ({
            ...s,
            currentRound: event.data.current_round,
            totalRounds: event.data.total_rounds,
            nodes: event.data.nodes || s.nodes,
            links: event.data.links || s.links,
            feedEvents: [...s.feedEvents, feedEvent],
          }))
        }
      } catch {
        // ignore malformed
      }
    }

    ws.onclose = (e) => {
      setState((s) => ({ ...s, status: 'disconnected' }))
      if (pingRef.current) clearInterval(pingRef.current)
      if (e.code === 4001) {
        setState((s) => ({ ...s, status: 'error' }))
        return
      }
      if (attemptRef.current < MAX_RECONNECT) {
        const delay = getBackoffDelay(attemptRef.current)
        attemptRef.current += 1
        setTimeout(connect, delay)
      }
    }

    ws.onerror = () => {}
  }, [simulationId, token, cleanup])

  useEffect(() => {
    if (simulationId && token) {
      connect()
    }
    return cleanup
  }, [simulationId, token, connect, cleanup])

  return state
}

function mergeNodes(existing: GraphNode[], incoming: GraphNode[]): GraphNode[] {
  const map = new Map(existing.map((n) => [n.id, n]))
  for (const node of incoming) {
    if (!map.has(node.id)) {
      map.set(node.id, node)
    }
  }
  return Array.from(map.values())
}

function updateNodeSentiments(nodes: GraphNode[], actions: AgentActionEvent[]): GraphNode[] {
  const sentimentMap = new Map<string, number>()
  for (const a of actions) {
    sentimentMap.set(a.agent_id, a.sentiment)
  }

  if (sentimentMap.size === 0) return nodes

  return nodes.map((n) => {
    const newSentiment = sentimentMap.get(n.id)
    if (newSentiment !== undefined) {
      return { ...n, sentiment: newSentiment }
    }
    return n
  })
}

import { useCallback, useEffect, useRef, useState } from 'react'
import type { SimulationEvent, AgentActionEvent } from '@/lib/ws-events'

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error'

const PING_INTERVAL_MS = 30000
const MAX_RECONNECT = 10

function getBackoffDelay(attempt: number): number {
  const delay = Math.min(1000 * 2 ** attempt, 30000)
  return delay + Math.random() * delay * 0.3
}

interface SimulationStreamState {
  status: ConnectionStatus
  currentRound: number
  totalRounds: number
  actions: AgentActionEvent[]
  avgSentiment: number
  activeCounts: number[]
}

export function useSimulationStream(simulationId: string | null, token: string | null) {
  const [state, setState] = useState<SimulationStreamState>({
    status: 'disconnected',
    currentRound: 0,
    totalRounds: 0,
    actions: [],
    avgSentiment: 0,
    activeCounts: [],
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

        if (event.type === 'round_complete') {
          setState((s) => ({
            ...s,
            currentRound: event.round,
            avgSentiment: event.data.avg_sentiment,
            actions: [...s.actions, ...event.data.actions].slice(-200),
            activeCounts: [...s.activeCounts, event.data.active_agents],
          }))
        } else if (event.type === 'simulation_complete') {
          setState((s) => ({
            ...s,
            currentRound: event.data.completed_rounds,
            status: 'disconnected',
          }))
        } else if (event.type === 'snapshot') {
          setState((s) => ({
            ...s,
            currentRound: event.data.current_round,
            totalRounds: event.data.total_rounds,
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

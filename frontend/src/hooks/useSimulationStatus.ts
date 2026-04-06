import { useEffect, useRef, useState } from 'react'

export interface SimulationStatus {
  simulation_id: string
  status: string
  phase: string
  phase_detail: string
  current_round: number
  total_rounds: number
  total_agents: number
  personas_generated: number
  posts_created: number
  comments_created: number
  likes_created: number
  avg_sentiment: number
  cost_usd: number
}

const POLL_INTERVAL_MS = 2000

export function useSimulationStatus(
  simulationId: string | null,
  token: string | null
) {
  const [status, setStatus] = useState<SimulationStatus | null>(null)
  const [error, setError] = useState<string | null>(null)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    if (!simulationId || !token) return

    const fetchStatus = async () => {
      try {
        const res = await fetch(`/api/simulation/status/${simulationId}`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (!res.ok) {
          setError('Status konnte nicht abgerufen werden')
          return
        }
        const data: SimulationStatus = await res.json()
        setStatus(data)

        // Stop polling when done or failed
        if (data.status === 'completed' || data.status === 'failed') {
          if (intervalRef.current) {
            clearInterval(intervalRef.current)
            intervalRef.current = null
          }
        }
      } catch {
        setError('Verbindungsfehler')
      }
    }

    // Initial fetch
    fetchStatus()

    // Poll every 2 seconds
    intervalRef.current = setInterval(fetchStatus, POLL_INTERVAL_MS)

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [simulationId, token])

  return { status, error }
}

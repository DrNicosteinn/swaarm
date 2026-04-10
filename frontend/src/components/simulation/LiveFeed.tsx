import { useEffect, useRef, useState } from 'react'
import type { AgentActionEvent, GraphNode } from '@/lib/ws-events'

// A feed event can be an action, a persona spawn, a round marker, or an entity event
export type FeedEvent =
  | { kind: 'action'; data: AgentActionEvent; round: number }
  | { kind: 'persona_spawned'; data: GraphNode }
  | { kind: 'round_marker'; round: number; activeAgents: number }
  | { kind: 'phase_change'; phase: string; detail: string }
  | { kind: 'entity_found'; entityName: string; entityType: string; subType: string }
  | { kind: 'entity_enriched'; entityName: string }
  | { kind: 'enrichment_failed'; entityName: string; reason: string }

interface LiveFeedProps {
  events: FeedEvent[]
  maxItems?: number
}

const actionLabels: Record<string, string> = {
  create_post: 'hat gepostet',
  create_article: 'hat einen Artikel geschrieben',
  like_post: 'hat geliked',
  react_like: 'hat reagiert',
  react_celebrate: 'feiert',
  react_insightful: 'findet aufschlussreich',
  react_funny: 'findet lustig',
  react_love: 'liebt das',
  react_support: 'unterstuetzt das',
  comment: 'hat kommentiert',
  reply: 'hat geantwortet',
  repost: 'hat geteilt',
  share: 'hat geteilt',
  follow_user: 'folgt jetzt',
  connect: 'hat sich vernetzt mit',
  endorse: 'hat empfohlen',
  do_nothing: 'beobachtet',
}

const actionIcons: Record<string, string> = {
  create_post: 'edit',
  create_article: 'article',
  like_post: 'heart',
  react_like: 'thumbs-up',
  react_celebrate: 'party',
  react_insightful: 'lightbulb',
  comment: 'message',
  reply: 'corner-down-right',
  repost: 'repeat',
  share: 'share',
  follow_user: 'user-plus',
  connect: 'link',
  endorse: 'award',
}

function sentimentColor(s: number): string {
  if (s > 0.2) return 'text-green-400'
  if (s < -0.2) return 'text-red-400'
  return 'text-gray-500'
}

function sentimentBg(s: number): string {
  if (s > 0.2) return 'bg-green-500/10 border-green-500/20'
  if (s < -0.2) return 'bg-red-500/10 border-red-500/20'
  return 'bg-gray-500/10 border-gray-500/20'
}

function ActionIcon({ type }: { type: string }) {
  const icon = actionIcons[type]
  // Simple SVG icons inline for zero-dependency
  switch (icon) {
    case 'edit':
      return (
        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
        </svg>
      )
    case 'heart':
      return (
        <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
        </svg>
      )
    case 'message':
      return (
        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
        </svg>
      )
    case 'repeat':
    case 'share':
      return (
        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
          <path d="M17 1l4 4-4 4" /><path d="M3 11V9a4 4 0 0 1 4-4h14" />
          <path d="M7 23l-4-4 4-4" /><path d="M21 13v2a4 4 0 0 1-4 4H3" />
        </svg>
      )
    case 'user-plus':
    case 'link':
      return (
        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
          <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
          <circle cx="8.5" cy="7" r="4" /><line x1="20" y1="8" x2="20" y2="14" /><line x1="23" y1="11" x2="17" y2="11" />
        </svg>
      )
    default:
      return (
        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
          <circle cx="12" cy="12" r="3" />
        </svg>
      )
  }
}

function ActionFeedItem({ event }: { event: FeedEvent & { kind: 'action' } }) {
  const action = event.data
  return (
    <div className={`border rounded-lg p-3 ${sentimentBg(action.sentiment)} animate-feed-in`}>
      <div className="flex items-start gap-2">
        <div className="mt-0.5 text-gray-600">
          <ActionIcon type={action.action_type} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium text-gray-900 text-sm">{action.agent_name}</span>
            <span className="text-gray-500 text-xs">
              {actionLabels[action.action_type] || action.action_type}
            </span>
            <span className={`ml-auto text-xs font-mono ${sentimentColor(action.sentiment)}`}>
              {action.sentiment > 0 ? '+' : ''}{action.sentiment.toFixed(2)}
            </span>
          </div>
          {action.content && (
            <p className="text-gray-700 text-xs leading-relaxed mt-1.5 line-clamp-3">
              {action.content}
            </p>
          )}
        </div>
      </div>
      <div className="flex items-center gap-2 mt-2 text-[10px] text-gray-400">
        <span>Runde {event.round}</span>
      </div>
    </div>
  )
}

function PersonaSpawnItem({ node }: { node: GraphNode }) {
  // Show role or occupation if available, fallback to tier
  const detail = node.role || node.occupation || (() => {
    const tierLabel: Record<string, string> = {
      power_creator: 'Meinungsfuehrer',
      active_responder: 'Aktiv',
      selective_engager: 'Gelegentlich',
      observer: 'Beobachter',
    }
    return tierLabel[node.tier] || node.tier
  })()

  return (
    <div className="flex items-center gap-2 px-3 py-1.5 animate-feed-in">
      <div className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse" />
      <span className="text-gray-600 text-xs">
        <span className="text-indigo-500 font-medium">{node.label}</span>
        {' '}ist dem Netzwerk beigetreten
        <span className="text-gray-400 ml-1">
          ({detail})
        </span>
      </span>
    </div>
  )
}

function RoundMarkerItem({ round, activeAgents }: { round: number; activeAgents: number }) {
  return (
    <div className="flex items-center gap-3 px-3 py-2 my-1">
      <div className="flex-1 h-px bg-gray-200" />
      <span className="text-xs font-medium text-gray-500 whitespace-nowrap">
        Runde {round} &middot; {activeAgents} aktiv
      </span>
      <div className="flex-1 h-px bg-gray-200" />
    </div>
  )
}

function PhaseChangeItem({ phase, detail }: { phase: string; detail: string }) {
  const phaseLabels: Record<string, string> = {
    analyzing: 'Analyse',
    extracting_entities: 'Entitaeten erkannt',
    enriching: 'Web-Recherche',
    generating_personas: 'Personas generieren',
    configuring: 'Bereit',
    simulating: 'Simulation laeuft',
    done: 'Abgeschlossen',
  }

  return (
    <div className="flex items-center gap-3 px-3 py-2 my-1 bg-blue-500/10 rounded-lg border border-blue-500/20 animate-feed-in">
      <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
      <div>
        <span className="text-blue-500 text-xs font-medium">
          {phaseLabels[phase] || phase}
        </span>
        {detail && (
          <span className="text-gray-500 text-xs ml-2">{detail}</span>
        )}
      </div>
    </div>
  )
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

function EntityFoundItem({ entityName, entityType, subType }: { entityName: string; entityType: string; subType: string }) {
  return (
    <div className="flex items-center gap-2 px-3 py-1.5 animate-feed-in">
      <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
      <span className="text-gray-600 text-xs">
        <span className="text-emerald-500 font-medium">{entityName}</span>
        {' '}erkannt
        <span className="text-gray-400 ml-1">
          ({entityTypeLabels[entityType] || entityType}{subType ? ` — ${subType}` : ''})
        </span>
      </span>
    </div>
  )
}

function EntityEnrichedItem({ entityName }: { entityName: string }) {
  return (
    <div className="flex items-center gap-2 px-3 py-1.5 animate-feed-in">
      <div className="w-2 h-2 rounded-full bg-cyan-500" />
      <span className="text-gray-600 text-xs">
        <span className="text-cyan-500 font-medium">{entityName}</span>
        {' '}angereichert
      </span>
    </div>
  )
}

function EnrichmentFailedItem({ entityName }: { entityName: string }) {
  return (
    <div className="flex items-center gap-2 px-3 py-1.5 animate-feed-in">
      <div className="w-2 h-2 rounded-full bg-amber-500" />
      <span className="text-gray-600 text-xs">
        <span className="text-amber-500 font-medium">{entityName}</span>
        {' '}— Recherche fehlgeschlagen
      </span>
    </div>
  )
}

export function LiveFeed({ events, maxItems = 100 }: LiveFeedProps) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const [autoScroll, setAutoScroll] = useState(true)
  const prevLengthRef = useRef(0)

  // Auto-scroll to bottom on new events
  useEffect(() => {
    if (autoScroll && scrollRef.current && events.length > prevLengthRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
    prevLengthRef.current = events.length
  }, [events, autoScroll])

  // Detect manual scroll
  const handleScroll = () => {
    if (!scrollRef.current) return
    const { scrollTop, scrollHeight, clientHeight } = scrollRef.current
    const atBottom = scrollHeight - scrollTop - clientHeight < 40
    setAutoScroll(atBottom)
  }

  const displayEvents = events.slice(-maxItems)

  if (displayEvents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-400 gap-2">
        <div className="w-8 h-8 border-2 border-gray-200 border-t-gray-500 rounded-full animate-spin" />
        <span className="text-sm">Warte auf Aktivitaet...</span>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-gray-200">
        <span className="text-xs font-medium text-gray-600">Live Feed</span>
        {!autoScroll && (
          <button
            onClick={() => {
              setAutoScroll(true)
              if (scrollRef.current) {
                scrollRef.current.scrollTop = scrollRef.current.scrollHeight
              }
            }}
            className="text-[10px] text-blue-400 hover:text-blue-300"
          >
            Zum Ende scrollen
          </button>
        )}
      </div>

      {/* Scrollable feed */}
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto space-y-1 p-2 scroll-smooth"
      >
        {displayEvents.map((event, i) => {
          switch (event.kind) {
            case 'action':
              return <ActionFeedItem key={`a-${i}`} event={event} />
            case 'persona_spawned':
              return <PersonaSpawnItem key={`p-${event.data.id}`} node={event.data} />
            case 'round_marker':
              return <RoundMarkerItem key={`r-${event.round}`} round={event.round} activeAgents={event.activeAgents} />
            case 'phase_change':
              return <PhaseChangeItem key={`ph-${i}`} phase={event.phase} detail={event.detail} />
            case 'entity_found':
              return <EntityFoundItem key={`ef-${i}`} entityName={event.entityName} entityType={event.entityType} subType={event.subType} />
            case 'entity_enriched':
              return <EntityEnrichedItem key={`ee-${i}`} entityName={event.entityName} />
            case 'enrichment_failed':
              return <EnrichmentFailedItem key={`ex-${i}`} entityName={event.entityName} />
          }
        })}
      </div>
    </div>
  )
}

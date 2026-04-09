/**
 * DEV-ONLY: Preview page for SimulationPage with mock data.
 *
 * Szenario: SwissBank Krise — 2000 Entlassungen angekuendigt.
 *
 * Netzwerk-Modell: Hierarchischer Stakeholder-Graph
 * - Organisations-Hubs als zentrale Knoten
 * - Personen verbunden mit EINER Organisation (arbeitet bei / Kunde von / ...)
 * - Wenige explizite Person→Person-Beziehungen (Familie, Quelle, Vorgesetzter)
 * - Max 1-3 Kanten pro Person → visuell klar lesbar
 */
import { useEffect, useRef, useState } from 'react'
import { NetworkGraph, NodeTooltip } from '@/components/simulation/NetworkGraph'
import { LiveFeed } from '@/components/simulation/LiveFeed'
import type { FeedEvent } from '@/components/simulation/LiveFeed'
import { StatsPanel } from '@/components/simulation/StatsPanel'
import { PhaseTimeline } from '@/components/simulation/PhaseTimeline'
import type { GraphNode, GraphLink, AgentActionEvent } from '@/lib/ws-events'

// ──────────────────────────────────────────────────────
// Communities:
//   0 = SwissBank (Organisation + Mitarbeiter)
//   1 = Kunden & Anleger
//   2 = Medien
//   3 = Familie & Umfeld
//   4 = Regulierer & Politik
// ──────────────────────────────────────────────────────

interface PersonaDef {
  id: string
  name: string
  role: string
  occupation: string
  communityId: number
  tier: string
  followerCount: number
  sentimentBias: number
  isOrg?: boolean // Organisation node (hub)
}

interface RelationDef {
  from: string  // persona id
  to: string    // persona id
  label: string // relationship label shown on hover
}

// ── Personas: Organisationen zuerst, dann Personen ──

const PERSONAS: PersonaDef[] = [
  // Organisations-Hubs (large, central)
  { id: 'swissbank',    name: 'SwissBank AG',        role: 'Unternehmen',    occupation: 'Grossbank',               communityId: 0, tier: 'power_creator',    followerCount: 900, sentimentBias: -0.1, isOrg: true },
  { id: 'betriebsrat',  name: 'Betriebsrat SB',      role: 'Gremium',        occupation: 'Arbeitnehmervertretung',   communityId: 0, tier: 'power_creator',    followerCount: 200, sentimentBias: -0.8, isOrg: true },
  { id: 'unia',         name: 'Gewerkschaft Unia',    role: 'Gewerkschaft',   occupation: 'Arbeitnehmergewerkschaft', communityId: 4, tier: 'power_creator',    followerCount: 350, sentimentBias: -0.7, isOrg: true },
  { id: 'finma',        name: 'FINMA',                role: 'Regulierer',     occupation: 'Finanzmarktaufsicht',      communityId: 4, tier: 'active_responder', followerCount: 400, sentimentBias: 0.0,  isOrg: true },
  { id: 'bankverein',   name: 'Bankiervereinigung',   role: 'Verband',        occupation: 'Schweiz. Bankierverein.', communityId: 4, tier: 'selective_engager', followerCount: 250, sentimentBias: 0.1,  isOrg: true },
  { id: 'betroffene',   name: 'Betroffene Familien',  role: 'Gruppe',         occupation: 'Selbsthilfegruppe',       communityId: 3, tier: 'active_responder', followerCount: 45,  sentimentBias: -0.9, isOrg: true },

  // SwissBank Mitarbeiter → jeweils verbunden mit swissbank
  { id: 'ceo',      name: 'Marcus Weber',    role: 'CEO',            occupation: 'CEO SwissBank',              communityId: 0, tier: 'power_creator',    followerCount: 450, sentimentBias: 0.2 },
  { id: 'hr',       name: 'Sabine Keller',   role: 'HR-Leiterin',    occupation: 'Head of HR',                 communityId: 0, tier: 'active_responder', followerCount: 120, sentimentBias: -0.3 },
  { id: 'analyst',  name: 'Thomas Brunner',  role: 'Analyst',        occupation: 'Analyst, Private Banking',   communityId: 0, tier: 'active_responder', followerCount: 85,  sentimentBias: -0.5 },
  { id: 'it',       name: 'Lisa Hofmann',    role: 'IT-Leiterin',    occupation: 'IT-Projektleiterin',         communityId: 0, tier: 'selective_engager', followerCount: 60,  sentimentBias: -0.6 },
  { id: 'berater',  name: 'Ralf Steiner',    role: 'Kundenberater',  occupation: 'Kundenberater',              communityId: 0, tier: 'selective_engager', followerCount: 45,  sentimentBias: -0.4 },
  { id: 'pm',       name: 'Patrick Huber',   role: 'Manager',        occupation: 'Portfoliomanager',           communityId: 0, tier: 'active_responder', followerCount: 70,  sentimentBias: -0.3 },
  { id: 'compliance', name: 'Nina Gerber',   role: 'Compliance',     occupation: 'Compliance Officer',         communityId: 0, tier: 'observer',          followerCount: 30,  sentimentBias: -0.2 },
  { id: 'assistenz', name: 'Claudia Meier',  role: 'Assistentin',    occupation: 'Assistentin Vorstand',       communityId: 0, tier: 'observer',          followerCount: 15,  sentimentBias: -0.7 },

  // Kunden → jeweils verbunden mit swissbank
  { id: 'kmu',       name: 'Werner Schulz',    role: 'Geschaeftskunde', occupation: 'Unternehmer, KMU',          communityId: 1, tier: 'active_responder', followerCount: 95,  sentimentBias: -0.3 },
  { id: 'rentnerin', name: 'Monika Fischer',   role: 'Privatkundin',    occupation: 'Rentnerin, Anlegerin',      communityId: 1, tier: 'selective_engager', followerCount: 20,  sentimentBias: -0.5 },
  { id: 'steuer',    name: 'Stefan Baumann',   role: 'Geschaeftskunde', occupation: 'Steuerberater',             communityId: 1, tier: 'active_responder', followerCount: 110, sentimentBias: -0.2 },
  { id: 'investor',  name: 'Helmut Brandt',    role: 'Aktionaer',       occupation: 'Privatinvestor',            communityId: 1, tier: 'active_responder', followerCount: 150, sentimentBias: -0.4 },
  { id: 'aerztin',   name: 'Andrea Lenz',      role: 'Privatkundin',    occupation: 'Aerztin',                   communityId: 1, tier: 'observer',          followerCount: 10,  sentimentBias: -0.1 },

  // Medien → verbunden mit swissbank/ceo/betriebsrat (Quellen)
  { id: 'nzz',      name: 'Eva Hartmann',      role: 'Journalistin',  occupation: 'Wirtschaftsredakteurin NZZ', communityId: 2, tier: 'power_creator',    followerCount: 520, sentimentBias: -0.1 },
  { id: 'tagi',     name: 'Joerg Zimmermann',  role: 'Journalist',    occupation: 'Finanzjournalist Tagi',      communityId: 2, tier: 'power_creator',    followerCount: 380, sentimentBias: -0.3 },
  { id: 'blog',     name: 'Sandra Klein',      role: 'Bloggerin',     occupation: 'Finanzbloggerin',            communityId: 2, tier: 'active_responder', followerCount: 250, sentimentBias: -0.2 },
  { id: 'srf',      name: 'Marcel Roth',       role: 'TV-Reporter',   occupation: 'TV-Reporter SRF',            communityId: 2, tier: 'power_creator',    followerCount: 600, sentimentBias: 0.0 },

  // Familie → verbunden mit EINEM Mitarbeiter
  { id: 'frau-thomas', name: 'Julia Brunner',   role: 'Ehefrau',    occupation: 'Lehrerin',            communityId: 3, tier: 'selective_engager', followerCount: 35,  sentimentBias: -0.7 },
  { id: 'sohn-thomas', name: 'Max Brunner',     role: 'Sohn',       occupation: 'Student ETH',         communityId: 3, tier: 'observer',          followerCount: 80,  sentimentBias: -0.5 },
  { id: 'schwester',   name: 'Anna Hofmann',    role: 'Schwester',  occupation: 'Grafikerin',          communityId: 3, tier: 'active_responder', followerCount: 95,  sentimentBias: -0.6 },
  { id: 'bruder',      name: 'Peter Huber',     role: 'Bruder',     occupation: 'Handwerker',          communityId: 3, tier: 'observer',          followerCount: 25,  sentimentBias: -0.4 },
  { id: 'frau-ralf',   name: 'Maria Steiner',   role: 'Ehefrau',    occupation: 'Pflegefachfrau',      communityId: 3, tier: 'observer',          followerCount: 15,  sentimentBias: -0.5 },

  // Regulierer & Politik → verbunden mit finma/unia
  { id: 'prof',     name: 'Prof. Dr. Richter', role: 'Experte',     occupation: 'Wirtschaftsprof. HSG',    communityId: 4, tier: 'power_creator',    followerCount: 320, sentimentBias: 0.1 },
  { id: 'ubsanalyst', name: 'Dr. Urs Wyss',   role: 'Analyst',     occupation: 'Bankanalyst UBS Research', communityId: 4, tier: 'active_responder', followerCount: 180, sentimentBias: 0.2 },
  { id: 'politikerin', name: 'Kathrin Ammann', role: 'Politikerin', occupation: 'Nationalraetin SP',       communityId: 4, tier: 'active_responder', followerCount: 280, sentimentBias: -0.5 },
]

// ── Beziehungen: Jede Kante hat einen Grund ──
// Prinzip: Max 1-3 Kanten pro Person. Organisationen haben mehr (Hub).

const RELATIONS: RelationDef[] = [
  // Mitarbeiter → SwissBank (arbeitet bei)
  { from: 'ceo',        to: 'swissbank',   label: 'leitet' },
  { from: 'hr',         to: 'swissbank',   label: 'arbeitet bei' },
  { from: 'analyst',    to: 'swissbank',   label: 'arbeitet bei' },
  { from: 'it',         to: 'swissbank',   label: 'arbeitet bei' },
  { from: 'berater',    to: 'swissbank',   label: 'arbeitet bei' },
  { from: 'pm',         to: 'swissbank',   label: 'arbeitet bei' },
  { from: 'compliance', to: 'swissbank',   label: 'arbeitet bei' },
  { from: 'assistenz',  to: 'ceo',         label: 'Assistentin von' },

  // Betriebsrat → SwissBank + vertritt Mitarbeiter
  { from: 'betriebsrat', to: 'swissbank',  label: 'vertritt AN bei' },
  { from: 'betriebsrat', to: 'hr',         label: 'verhandelt mit' },

  // Kunden → SwissBank (Kunde von)
  { from: 'kmu',       to: 'swissbank',   label: 'Geschaeftskunde' },
  { from: 'rentnerin', to: 'berater',     label: 'wird beraten von' },
  { from: 'steuer',    to: 'swissbank',   label: 'Geschaeftskunde' },
  { from: 'investor',  to: 'swissbank',   label: 'Aktionaer' },
  { from: 'aerztin',   to: 'berater',     label: 'wird beraten von' },

  // Journalisten → Quellen (Interviews/Recherche)
  { from: 'nzz',  to: 'ceo',         label: 'interviewt' },
  { from: 'nzz',  to: 'betriebsrat', label: 'Quelle' },
  { from: 'tagi', to: 'ceo',         label: 'interviewt' },
  { from: 'tagi', to: 'unia',        label: 'Quelle' },
  { from: 'srf',  to: 'swissbank',   label: 'berichtet ueber' },
  { from: 'blog', to: 'nzz',         label: 'zitiert' },
  { from: 'blog', to: 'prof',        label: 'zitiert' },

  // Familie → ihr Angehoeriger
  { from: 'frau-thomas', to: 'analyst',    label: 'Ehefrau von' },
  { from: 'sohn-thomas', to: 'analyst',    label: 'Sohn von' },
  { from: 'frau-thomas', to: 'sohn-thomas', label: 'Mutter von' },
  { from: 'schwester',   to: 'it',         label: 'Schwester von' },
  { from: 'bruder',      to: 'pm',         label: 'Bruder von' },
  { from: 'frau-ralf',   to: 'berater',    label: 'Ehefrau von' },

  // Familie → Selbsthilfegruppe
  { from: 'frau-thomas', to: 'betroffene', label: 'Mitglied' },
  { from: 'schwester',   to: 'betroffene', label: 'Mitglied' },
  { from: 'frau-ralf',   to: 'betroffene', label: 'Mitglied' },

  // Regulierer/Politik
  { from: 'finma',       to: 'swissbank',  label: 'beaufsichtigt' },
  { from: 'bankverein',  to: 'swissbank',  label: 'Mitglied' },
  { from: 'prof',        to: 'finma',      label: 'beraet' },
  { from: 'ubsanalyst',  to: 'swissbank',  label: 'analysiert' },
  { from: 'ubsanalyst',  to: 'investor',   label: 'beraet' },
  { from: 'politikerin', to: 'unia',       label: 'unterstuetzt' },
  { from: 'politikerin', to: 'betriebsrat', label: 'solidarisiert sich' },

  // Gewerkschaft
  { from: 'unia', to: 'betriebsrat',  label: 'unterstuetzt' },
  { from: 'unia', to: 'betroffene',   label: 'vertritt' },
]

// ── Content per role ──

const CONTENT_BY_ROLE: Record<string, string[]> = {
  CEO: [
    'Die Restrukturierung ist schmerzhaft, aber notwendig fuer die Zukunft der Bank.',
    'Wir investieren gleichzeitig in 500 neue digitale Stellen.',
  ],
  'HR-Leiterin': [
    'Wir bieten jedem Betroffenen ein faires Abfindungspaket und Outplacement-Beratung.',
  ],
  Analyst: [
    'Das Management hat den Kontakt zur Belegschaft komplett verloren.',
    'Nach 12 Jahren bei der SwissBank erfahre ich per Mail von der Kuendigung.',
  ],
  'IT-Leiterin': [
    'In meiner Abteilung wurden 8 von 15 Stellen gestrichen. Die Stimmung ist am Boden.',
  ],
  Kundenberater: [
    'Meine Kunden rufen an und fragen, ob ihr Geld sicher ist. Das ist doch absurd.',
  ],
  Geschaeftskunde: [
    'Als langjaeehriger Geschaeftskunde ueberlege ich ernsthaft, die Bank zu wechseln.',
    'Wenn eine Bank so mit ihren Leuten umgeht — wie geht sie dann mit meinem Geld um?',
  ],
  Privatkundin: [
    'Meine Beraterin wurde entlassen. Wer kuemmert sich jetzt um mein Portfolio?',
  ],
  Aktionaer: [
    'Kurzfristig gut fuer die Bilanz, aber der Reputationsschaden ist enorm.',
  ],
  Journalistin: [
    'SwissBank streicht 2000 Stellen — groesste Entlassungswelle im Bankensektor seit 2008.',
  ],
  Journalist: [
    'CEO Weber verteidigt die Massnahmen als "zukunftssichernd".',
  ],
  'TV-Reporter': [
    'Live vor der SwissBank-Zentrale: Mitarbeiter verlassen mit Kartons das Gebaeude.',
  ],
  Bloggerin: [
    'Die Zahlen sprechen eine klare Sprache: SwissBank hat ein strukturelles Problem.',
  ],
  Ehefrau: [
    'Mein Mann kommt jeden Abend zerstoert nach Hause. Die Ungewissheit macht uns fertig.',
  ],
  Sohn: [
    'Mein Vater hat sein ganzes Berufsleben fuer diese Bank gegeben. Und jetzt das.',
  ],
  Schwester: [
    'Meine Schwester weint jeden Tag. Sie hatte gerade ein Haus gekauft.',
  ],
  Experte: [
    'Die Restrukturierung war ueberfaellig, aber die soziale Abfederung ist ungenuegend.',
  ],
  Politikerin: [
    'Wir fordern einen Sozialplan und brauchen Antworten vom Verwaltungsrat.',
  ],
}

function getContentForRole(role: string): string {
  const options = CONTENT_BY_ROLE[role]
  if (!options) return 'Die Situation bei der SwissBank ist besorgniserregend.'
  return options[Math.floor(Math.random() * options.length)]
}

const ACTION_TYPES = ['create_post', 'comment', 'like_post', 'repost']

function randomSentimentNear(base: number): number {
  return Math.max(-1, Math.min(1, base + (Math.random() - 0.5) * 0.3))
}

function toGraphNode(p: PersonaDef): GraphNode {
  return {
    id: p.id,
    label: p.name,
    communityId: p.communityId,
    sentiment: randomSentimentNear(p.sentimentBias),
    followerCount: p.followerCount,
    tier: p.tier,
    role: p.role,
    occupation: p.occupation,
  }
}

function toGraphLinks(rels: RelationDef[]): GraphLink[] {
  return rels.map(r => ({ source: r.from, target: r.to, type: r.label }))
}

function generateAction(nodes: GraphNode[]): AgentActionEvent {
  const node = nodes[Math.floor(Math.random() * nodes.length)]
  const def = PERSONAS.find(p => p.id === node.id)
  const actionType = ACTION_TYPES[Math.floor(Math.random() * ACTION_TYPES.length)]
  const hasContent = actionType === 'create_post' || actionType === 'comment'
  return {
    agent_id: node.id,
    agent_name: node.label,
    action_type: actionType,
    content: hasContent && def ? getContentForRole(def.role) : null,
    target_post_id: null,
    target_user_id: null,
    sentiment: randomSentimentNear(def?.sentimentBias ?? 0),
  }
}

// ──────────────────────────────────────────────────────
// Spawn order: Organisations first, then persons by community
// This gives a natural tree-building feel
// ──────────────────────────────────────────────────────

function buildSpawnOrder(): { persona: PersonaDef; linksToAdd: RelationDef[] }[] {
  const order: { persona: PersonaDef; linksToAdd: RelationDef[] }[] = []
  const spawned = new Set<string>()

  // 1. Spawn organisations first
  for (const p of PERSONAS) {
    if (p.isOrg) {
      const links = RELATIONS.filter(
        r => (r.from === p.id || r.to === p.id) && (spawned.has(r.from) || spawned.has(r.to))
      )
      order.push({ persona: p, linksToAdd: links })
      spawned.add(p.id)
    }
  }

  // 2. Spawn persons, grouped by community
  const communities = [0, 1, 2, 3, 4]
  for (const cid of communities) {
    const members = PERSONAS.filter(p => p.communityId === cid && !p.isOrg)
    for (const p of members) {
      // Only add links where both endpoints are already spawned (or will be spawned now)
      spawned.add(p.id)
      const links = RELATIONS.filter(
        r => (r.from === p.id && spawned.has(r.to)) || (r.to === p.id && spawned.has(r.from))
      )
      order.push({ persona: p, linksToAdd: links })
    }
  }

  return order
}

// ──────────────────────────────────────────────────────
// Component
// ──────────────────────────────────────────────────────

export function PreviewSimulationPage() {
  const totalAgents = PERSONAS.length
  const totalRounds = 15
  const spawnOrderRef = useRef(buildSpawnOrder())

  const [phase, setPhase] = useState<string>('initializing')
  const [personasGenerated, setPersonasGenerated] = useState(0)
  const [currentRound, setCurrentRound] = useState(0)
  const [nodes, setNodes] = useState<GraphNode[]>([])
  const [links, setLinks] = useState<GraphLink[]>([])
  const [activeNodeIds, setActiveNodeIds] = useState<Set<string>>(new Set())
  const [feedEvents, setFeedEvents] = useState<FeedEvent[]>([])
  const [sentimentHistory, setSentimentHistory] = useState<number[]>([])
  const [activeHistory, setActiveHistory] = useState<number[]>([])
  const [avgSentiment, setAvgSentiment] = useState(0)

  const graphContainerRef = useRef<HTMLDivElement>(null)
  const [graphSize, setGraphSize] = useState({ width: 800, height: 600 })
  useEffect(() => {
    const el = graphContainerRef.current
    if (!el) return
    const obs = new ResizeObserver(([e]) => setGraphSize({ width: Math.floor(e.contentRect.width), height: Math.floor(e.contentRect.height) }))
    obs.observe(el)
    return () => obs.disconnect()
  }, [])

  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null)
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 })
  useEffect(() => {
    const h = (e: MouseEvent) => setTooltipPos({ x: e.clientX, y: e.clientY })
    window.addEventListener('mousemove', h)
    return () => window.removeEventListener('mousemove', h)
  }, [])

  // Phase 1: Init
  useEffect(() => {
    const t = setTimeout(() => {
      setPhase('generating_personas')
      setFeedEvents([{ kind: 'phase_change', phase: 'generating_personas', detail: 'Personas werden generiert...' }])
    }, 1000)
    return () => clearTimeout(t)
  }, [])

  // Phase 2: Spawn personas one by one with their links
  useEffect(() => {
    if (phase !== 'generating_personas') return
    let idx = 0
    const order = spawnOrderRef.current

    const interval = setInterval(() => {
      if (idx >= order.length) {
        clearInterval(interval)
        setTimeout(() => {
          setPhase('simulating')
          setFeedEvents(prev => [...prev, { kind: 'phase_change', phase: 'simulating', detail: 'Runde 1 beginnt...' }])
        }, 600)
        return
      }

      const entry = order[idx]
      idx++
      setPersonasGenerated(idx)

      const newNode = toGraphNode(entry.persona)
      setNodes(prev => [...prev, newNode])

      if (entry.linksToAdd.length > 0) {
        setLinks(prev => [...prev, ...toGraphLinks(entry.linksToAdd)])
      }

      // Show in feed (first 12)
      if (idx <= 12) {
        setFeedEvents(prev => [...prev, { kind: 'persona_spawned' as const, data: newNode }])
      }
    }, 400) // one persona every 400ms

    return () => clearInterval(interval)
  }, [phase])

  // Phase 3: Simulation rounds
  const nodesRef = useRef<GraphNode[]>([])
  nodesRef.current = nodes

  useEffect(() => {
    if (phase !== 'simulating') return
    let round = 0

    const interval = setInterval(() => {
      round++
      if (round > totalRounds) {
        clearInterval(interval)
        setPhase('done')
        setFeedEvents(prev => [...prev, { kind: 'phase_change', phase: 'done', detail: 'Simulation abgeschlossen' }])
        setActiveNodeIds(new Set())
        return
      }

      const currentNodes = nodesRef.current
      setCurrentRound(round)

      // Gentle sentiment drift
      setNodes(prev => prev.map(n => ({
        ...n,
        sentiment: Math.max(-1, Math.min(1, n.sentiment + (Math.random() - 0.5) * 0.08)),
      })))

      const activeCount = Math.floor(Math.random() * 10) + 4
      const roundActions: AgentActionEvent[] = []
      const activeIds = new Set<string>()

      for (let i = 0; i < activeCount; i++) {
        const action = generateAction(currentNodes)
        roundActions.push(action)
        activeIds.add(action.agent_id)
      }
      setActiveNodeIds(activeIds)

      const roundSentiment = Math.round((Math.random() * 0.6 - 0.3) * 1000) / 1000
      setAvgSentiment(roundSentiment)
      setSentimentHistory(prev => [...prev, roundSentiment])
      setActiveHistory(prev => [...prev, activeCount])

      const newFeedEvents: FeedEvent[] = [
        { kind: 'round_marker' as const, round, activeAgents: activeCount },
        ...roundActions
          .filter(a => a.action_type !== 'do_nothing')
          .map((a): FeedEvent => ({ kind: 'action' as const, data: a, round })),
      ]
      setFeedEvents(prev => [...prev, ...newFeedEvents].slice(-500))
    }, 2500)

    return () => clearInterval(interval)
  }, [phase, totalRounds])

  const showGraph = phase !== 'initializing'

  return (
    <div className="h-screen flex flex-col bg-gray-950 text-white overflow-hidden">
      <header className="flex items-center justify-between px-4 py-2 bg-gray-900/80 border-b border-gray-800 backdrop-blur-sm z-10">
        <div className="flex items-center gap-4">
          <span className="text-sm font-bold text-white">Swaarm</span>
          <div className="w-px h-5 bg-gray-700" />
          <PhaseTimeline
            currentPhase={phase}
            phaseDetail={
              phase === 'generating_personas' ? `${personasGenerated}/${totalAgents} generiert` :
              phase === 'simulating' ? `Runde ${currentRound}` : ''
            }
            personasGenerated={personasGenerated}
            totalAgents={totalAgents}
            currentRound={currentRound}
            totalRounds={totalRounds}
            isDone={phase === 'done'}
            isFailed={false}
          />
        </div>
        <div className="flex items-center gap-1.5">
          <div className={`w-2 h-2 rounded-full ${phase === 'done' ? 'bg-green-500' : 'bg-green-500 animate-pulse'}`} />
          <span className="text-xs text-green-400">{phase === 'done' ? 'Fertig' : 'Live'}</span>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        <div ref={graphContainerRef} className="flex-[6] relative min-w-0">
          {showGraph ? (
            <NetworkGraph
              nodes={nodes}
              links={links}
              activeNodeIds={activeNodeIds}
              hoveredNodeId={hoveredNode?.id || null}
              onNodeHover={setHoveredNode}
              onNodeClick={() => {}}
              width={graphSize.width}
              height={graphSize.height}
            />
          ) : (
            <div className="flex flex-col items-center justify-center h-full">
              <div className="relative w-24 h-24 mb-6">
                <div className="absolute inset-0 rounded-full border-2 border-gray-800" />
                <div className="absolute inset-0 rounded-full border-2 border-t-blue-500 animate-spin" />
              </div>
              <h2 className="text-xl font-semibold text-white mb-2">Simulation wird vorbereitet</h2>
              <p className="text-sm text-gray-500">Initialisierung...</p>
            </div>
          )}
        </div>

        <div className="flex-[4] flex flex-col border-l border-gray-800 bg-gray-950 min-w-[320px] max-w-[500px]">
          <div className="flex-[65] min-h-0 border-b border-gray-800">
            <LiveFeed events={feedEvents} />
          </div>
          <div className="flex-[35] min-h-0">
            <StatsPanel
              currentRound={currentRound}
              totalRounds={totalRounds}
              totalAgents={personasGenerated}
              activeAgents={activeHistory.length > 0 ? activeHistory[activeHistory.length - 1] : 0}
              postsCreated={Math.floor(currentRound * 3)}
              commentsCreated={Math.floor(currentRound * 6)}
              likesCreated={Math.floor(currentRound * 10)}
              avgSentiment={avgSentiment}
              costUsd={currentRound * 0.0003}
              sentimentHistory={sentimentHistory}
              activeHistory={activeHistory}
            />
          </div>
        </div>
      </div>

      <NodeTooltip node={hoveredNode} position={tooltipPos} />
    </div>
  )
}

# SwarmSight AI - Task Plan

## Goal
Build SwarmSight AI from scratch — a SaaS platform for multi-agent social media simulation targeting PR agencies and brand consultancies in the DACH market.

## Status: Phase 1 - Discovery & Requirements

## Phases

### Phase 1: Discovery & Requirements Grilling `status: complete`
- [ ] Grill-me interview to stress-test all architectural & product decisions
- [ ] Clarify tech stack choices
- [ ] Clarify MVP scope vs. full vision
- [ ] Clarify deployment & infrastructure decisions
- [ ] Clarify pricing/billing implementation

### Phase 2: PRD Creation `status: complete`
- [x] Write comprehensive PRD based on grill-me findings
- [x] Submit as GitHub issue (#1)

### Phase 3: Architecture Design `status: pending`
- [ ] Define system architecture
- [ ] Define data models
- [ ] Define API contracts
- [ ] Define frontend structure

### Phase 4: Issue Breakdown `status: complete`
- [x] Break PRD into 13 vertical-slice GitHub issues (#2-#14)
- [x] Prioritize and order issues (dependency graph established)

### Phase 5: Implementation `status: pending`
- [ ] TDD-driven development of each issue
- [ ] Iterative build & test cycles

## Key Documents
- Businessplan: `Businessplan_SwarmSight_AI.docx`
- Competitor Research: `competitor_research_pricing.md`
- Working Notes: `WORKING_NOTES.md`

## Decisions Made
1. MVP = Pipeline Stufen 1-4 (ohne Agent-Chat), nur Twitter-Simulation, kein A/B-Testing, kein Mid-Sim-Intervention
2. Custom Simulation Engine (OASIS-inspiriert, MIT-lizenziert), keine OASIS-Dependency
3. Architektur auf 50'000+ Agents auslegen, Pricing gestaffelt (Starter 1k, Pro 5-10k, Enterprise 50k+)
4. Output = vergleichende Szenario-Analyse, nicht quantitative Vorhersagen
5. LLM: GPT-4o-mini als Standard, provider-agnostisch bauen (Upgrade-Option auf Claude/GPT-4o für Enterprise)
6. Backend: Python + FastAPI + Pydantic, SQLite für Simulation, PostgreSQL für App-DB
7. Frontend: React + Vite + Tailwind + shadcn/ui (kein Next.js, SPA-Dashboard)
8. Auth + App-DB: Supabase (Auth + PostgreSQL)
9. Simulation: Async Background Job + Realtime WebSocket-Streaming pro Runde
10. Live-Visualisierung im MVP: Netzwerk-Graph (D3.js) + Live-Feed, Agents/Interaktionen in Echtzeit
11. Deployment: Railway (Backend) + Vercel (Frontend)
12. Persona-Generierung: ~500 LLM-generierte Basis-Personas + parametrische Variation für den Rest (DACH-kalibriert)
13. Report: Interaktives Dashboard + LLM-generierter Summary-Report als PDF-Export
14. Input: Hybrid — Freitext → LLM extrahiert Struktur + zeigt Lücken/Vorschläge → User ergänzt → Bestätigung → Start
15. Billing: Stripe (CHF, Subscriptions + Metered Billing für Pay-per-Simulation)
16. Plattformen: Twitter + LinkedIn im MVP (LinkedIn = USP, niemand hat das)
17. Positioning: "Pre-Testing Platform for Strategic Communications" (nicht "Social Media Simulation")
18. Von Socialtrait übernehmen: Willingness Scoring, Persistent Agent Memory, Vector-basierte Persona-Selektion, KV-Caching
19. LinkedIn-Personas: Prompt-Engineering (kein Fine-Tuning), demografische Kalibrierung via BFS/Destatis/LinkedIn Workforce Reports
20. LinkedIn Engine: Eigene Feed-Simulation (360Brew-inspiriert), 15 Action Types, Dwell-Time + Comment-weighted
21. Pricing angehoben: Starter CHF 199, Pro CHF 999, Enterprise CHF 2'999, Per-Simulation CHF 2k-15k
22. Auth: Email + Passwort (Supabase Auth), kein OAuth im MVP
23. DB: SQLite pro Simulation (Speed, Isolation) → Ergebnisse nach Abschluss in PostgreSQL (Supabase) persistieren
24. API: FastAPI REST + FastAPI WebSocket (ein Backend, zwei Protokolle)
25. Landing Page: Teil der React-App (öffentliche Routes /, /pricing, /use-cases + geschützte Routes /dashboard, /simulation)
26. Sprache: App-UI auf Deutsch, DACH-first. i18n-ready bauen für spätere Expansion
27. Job Queue: ARQ (async Redis queue) für Background-Simulationen
28. Monitoring: Sentry + Loguru + LLM-Token-Usage-Tracking pro Simulation
29. Plattform-Namen im UI: "Öffentliches Netzwerk" (Twitter) + "Professionelles Netzwerk" (LinkedIn)

## Errors Encountered
(none yet)

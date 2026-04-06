# Swaarm — Technische Dokumentation

**Letzte Aktualisierung:** 2026-04-06
**Autor:** Claude Opus 4 (KI-Entwicklungsassistent), im Auftrag von Nico Pfammatter
**Versionierung:** Alle Änderungen sind in Git versioniert (https://github.com/DrNicosteinn/swaarm)

---

## 1. Systemübersicht

### 1.1 Was ist Swaarm?
Swaarm ist eine SaaS-Plattform die mittels Multi-Agent-Simulation vorhersagt, wie die Öffentlichkeit auf Unternehmenskommunikation reagiert. KI-gesteuerte Personas interagieren auf simulierten Social-Media-Plattformen (Twitter-ähnlich + LinkedIn-ähnlich).

### 1.2 Architektur-Diagramm

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│   Frontend       │────▶│   Backend (API)       │────▶│   Supabase       │
│   React + Vite   │◀────│   FastAPI + Python    │◀────│   PostgreSQL     │
│   Port 5173      │     │   Port 8000           │     │   + Auth         │
└─────────────────┘     └──────────┬───────────┘     └─────────────────┘
                                   │
                          ┌────────┴────────┐
                          │ Simulation       │
                          │ Engine           │
                          │ (SQLite pro Sim) │
                          └────────┬────────┘
                                   │
                          ┌────────┴────────┐
                          │ OpenAI API       │
                          │ GPT-4o-mini      │
                          └─────────────────┘
```

### 1.3 Tech-Stack

| Komponente | Technologie | Version | Warum gewählt |
|-----------|-------------|---------|---------------|
| Backend | Python + FastAPI | 3.12+ | Bestes async-Ökosystem für LLM-Calls, Pydantic-Integration |
| Frontend | React + Vite + Tailwind | 18+ | Grösstes UI-Ökosystem, D3.js kompatibel |
| App-Datenbank | Supabase (PostgreSQL) | — | Auth + DB in einem Service, generous Free Tier |
| Sim-Datenbank | SQLite (pro Simulation) | — | Speed + Isolation, WAL Mode für Concurrency |
| LLM | OpenAI GPT-4o-mini | — | Bestes Preis-Leistungs-Verhältnis, gutes Deutsch, Function Calling |
| Graphen | networkx | 3.4+ | Standard für Netzwerkanalyse in Python |
| Numerik | numpy | 2.4+ | Vectorized Scoring für 50k+ Agents |
| Job Queue | ARQ (Redis) | — | Async-native, leichtgewichtig |
| Deployment | Railway + Vercel | — | Einfachstes Deploy für Backend + Frontend |
| Monitoring | Sentry + Loguru | — | Error-Tracking + strukturiertes Logging |
| Billing | Stripe | — | Industrie-Standard für SaaS-Billing |

---

## 2. Entwicklungsprozess & Entscheidungen

### 2.1 Planungsphase

**Methode:** Strukturiertes Interview ("Grill-me" Skill) mit 29 Architektur-Entscheidungen, dokumentiert in `task_plan.md`.

**Ergebnis:** PRD (Product Requirements Document) mit 45 User Stories, zerlegt in 13 GitHub Issues (vertikale Slices).

**Alle Entscheidungen sind nachvollziehbar in:**
- `task_plan.md` — alle 29 Entscheidungen mit Begründung
- `PRD.md` — vollständiges Product Requirements Document
- `SIMULATION_ENGINE_BLUEPRINT.md` — 22-teiliger technischer Bauplan
- `findings.md` — alle Recherche-Ergebnisse mit Quellen

### 2.2 Entwicklungs-Workflow

- **Feature-Branches:** Jedes Issue wird auf einem eigenen Branch entwickelt
- **Commits pro Teilschritt:** Jeder logische Teilschritt ist ein eigener Commit (rollback-fähig)
- **Tests vor Commit:** Jeder Commit wird erst nach bestandenen Tests erstellt
- **Automatische Code-Qualität:** Ruff (Python Linter + Formatter), ESLint + Prettier (TypeScript)

---

## 3. Implementierte Module (Detail)

### 3.1 Datenmodelle (`backend/app/models/`)

**Datei: `persona.py`**
- **Was:** Definiert eine simulierte Person (Persona) mit allen Attributen
- **Warum:** Pydantic-Modelle stellen sicher, dass alle Daten typsicher und validiert sind
- **Enthält:**
  - `BigFive` — 5 Persönlichkeits-Dimensionen (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism), je 0.0-1.0
  - `PostingStyle` — Posting-Frequenz, Tonalität, typische Themen
  - `OpinionSeeds` — Meinungs-Dimensionen (Vertrauen, Umwelt, Tech, Wirtschaft, Progressivität)
  - `Persona` — Komplett-Profil inkl. Demografie, Beruf, Sinus-Milieu, Stakeholder-Rolle
  - `AgentTier` — Aktivitäts-Stufe (Power Creator / Active Responder / Selective Engager / Observer)

**Datei: `agent.py`**
- **Was:** Dynamischer Zustand eines Agents während der Simulation
- **Enthält:**
  - `AgentMemory` — Sliding Window (letzte 5 Beobachtungen), wichtige Erinnerungen, komprimierte Zusammenfassung
  - `AgentState` — Sentiment, Meinungsänderungen, Cooldown-Timer, Aktivitäts-Statistiken

**Datei: `actions.py`**
- **Was:** Alle möglichen Aktionen auf den simulierten Plattformen
- **Enthält:**
  - `PublicNetworkAction` — 6 Aktionen (Post, Like, Repost, Comment, Follow, Do Nothing)
  - `ProfessionalNetworkAction` — 15 Aktionen (Post, Article, 6 Reaktionstypen, Comment, Reply, Share, Connect, Follow, Endorse, Do Nothing)
  - `AgentAction` — Einzelne Aktion mit Agent-ID, Runde, Ziel, Inhalt
  - `FeedItem` — Ein Post im Feed eines Agents

**Datei: `simulation.py`**
- **Was:** Konfigurations- und Ergebnis-Modelle für Simulationen
- **Enthält:**
  - `SimulationConfig` — Alle Parameter (Agent-Anzahl, Runden, Plattform, Kontroversität)
  - `TierDistribution` — Dynamische Verteilung der Agent-Tiers je nach Szenario-Kontroversität
  - `RoundMetrics` — Metriken pro Runde (Sentiment, Engagement, Kosten)
  - `QualityMetrics` — Qualitäts-Badge (Shannon-Entropie, Gini-Koeffizient, Trigram-Uniqueness)
  - `SimulationResult` — Komplett-Ergebnis mit Status, Metriken, Kosten

**Tests:** 18 Tests in `tests/test_models.py`

---

### 3.2 SQLite-Datenbank (`backend/app/simulation/database.py`)

**Was:** Jede Simulation bekommt eine eigene SQLite-Datei für maximale Performance und Isolation.

**Warum SQLite statt PostgreSQL für Simulationen?**
- Eine Simulation erzeugt hunderttausende Schreib-Operationen (Posts, Likes, Follows)
- SQLite ist 10-100x schneller für lokale Schreib-Operationen
- Keine Netzwerk-Latenz (Datei liegt lokal)
- Isolation: Simulationen beeinflussen sich nicht gegenseitig
- Nach Abschluss werden die Ergebnisse in PostgreSQL (Supabase) persistiert

**Schema (9 Tabellen):**
- `users` — Simulierte Personas
- `posts` — Erstelle Posts mit Hashtags, Engagement-Zähler
- `comments` — Kommentare auf Posts
- `likes` — Likes/Reaktionen (UNIQUE constraint verhindert Duplikate)
- `follows` — Follow-Beziehungen
- `reposts` — Reposts/Shares
- `action_log` — Audit Trail aller Agent-Aktionen (für Analyse)
- `round_metrics` — Aggregierte Metriken pro Runde
- `checkpoints` — Simulation-Zustand für Resume nach Crash

**Performance-Optimierungen:**
- WAL Mode (Write-Ahead Logging) für concurrent reads/writes
- `synchronous=NORMAL` (Kompromiss zwischen Safety und Speed)
- 64MB Cache Size
- 5s Busy Timeout
- Batch Inserts via `executemany` (100x schneller als Einzel-Inserts)

**Tests:** 11 Tests in `tests/test_database.py`

---

### 3.3 Social Graph (`backend/app/simulation/graph.py`)

**Was:** Verwaltet das soziale Netzwerk der Simulation (wer folgt/kennt wen).

**Bibliothek:** networkx (Python-Standard für Netzwerkanalyse)

**Wie wird der Graph generiert?**
1. Personas werden nach Stakeholder-Rollen in Communities gruppiert (z.B. Mitarbeiter, Kunden, Journalisten)
2. Intra-Community: 15-35% der Community-Mitglieder sind untereinander verbunden (dichte Cluster)
3. Inter-Community: ~5-10% Verbindungen zwischen Communities (Granovetter "Weak Ties")
4. Influencer-Hubs: Power Creators bekommen 2-3x mehr Verbindungen, auch cross-community

**Plattform-Unterschiede:**
- Öffentliches Netzwerk (Twitter): Directed Graph (Follow ≠ Follow-back)
- Professionelles Netzwerk (LinkedIn): Undirected Graph (Connection = bilateral)

**Determinismus:** Gleicher Seed → gleicher Graph (reproduzierbar für Tests und Vergleiche)

**Tests:** 14 Tests in `tests/test_graph.py`

---

### 3.4 LLM Adapter (`backend/app/llm/`)

**Was:** Provider-agnostische Abstraktionsschicht für KI-Modell-Aufrufe.

**Warum abstrakt?** Wir wollen nicht an OpenAI gebunden sein. Morgen könnte Anthropic Claude günstiger sein, oder Google Gemini besser auf Deutsch. Durch das Interface können wir den Provider wechseln ohne den Rest des Codes zu ändern.

**Dateien:**
- `base.py` — Abstrakte Klasse `LLMProvider` die jeder Provider implementieren muss
- `openai.py` — OpenAI-Implementation mit:
  - Async Client (nicht-blockierend)
  - Function Calling Support (für strukturierte Agent-Aktionen)
  - Prompt Caching Tracking (OpenAI cached automatisch statische Prompt-Prefixe)
  - Retry mit Exponential Backoff + Full Jitter (5 Versuche)
  - Fehler-Klassifizierung: Rate Limit → Retry, Bad Request → Permanent Fail, Timeout → Retry

**Kosten-Tracking (`LLMUsageTracker`):**
- Zählt Input/Output/Cached Tokens pro Simulation
- Berechnet Kosten in USD basierend auf Modell-Pricing
- Unterstützt verschiedene Pricing-Tiers (GPT-4o-mini vs. GPT-4o)

**Tests:** 10 Tests in `tests/test_llm.py`

---

### 3.5 Willingness Scoring (`backend/app/simulation/willingness.py`)

**Was:** Bestimmt welche Agents in jeder Runde aktiv werden. Nicht alle 50'000 Agents posten jede Runde.

**Algorithmus (Socialtrait-Patent-inspiriert, eigene Implementierung):**

```
s_unified = s_persona × exp(-λ × (s_context - s_persona))
```

- `s_persona`: Statischer Score basierend auf Persönlichkeit (Extraversion, Posting-Frequenz, Meinungsstärke, Agent-Tier)
- `s_context`: Dynamischer Score pro Runde (Themen-Relevanz, Netzwerk-Aktivität, emotionale Valenz)
- `λ = 1.5`: Dampening-Parameter — verhindert dass bei kontroversen Themen ALLE posten

**Dynamische Szenario-Anpassung:**
- Routine (z.B. Thought-Leadership): 20-30% aktiv
- Standard (z.B. Produktlaunch): 40-50% aktiv
- Krise (z.B. Entlassungen): 70-80%+ aktiv

**Performance:** Vectorized numpy — <5ms für 50'000 Agents. Kein LLM-Call nötig.

**Cooldown-System:**
- Power Creator: 2 Runden Pause nach Aktion
- Active Responder: 3 Runden
- Selective Engager: 5 Runden
- Observer: 12 Runden

**Tests:** 10 Tests in `tests/test_willingness.py`

---

### 3.6 Plattform-Modul: Öffentliches Netzwerk (`backend/app/simulation/platforms/`)

**Was:** Simuliert ein Twitter-ähnliches öffentliches Netzwerk.

**Architektur:** Abstrakte Basisklasse `PlatformBase` → konkrete Implementation `PublicNetworkPlatform`. Neue Plattformen (LinkedIn) implementieren dasselbe Interface.

**Feed-Algorithmus (basierend auf Twitter Open-Source):**
- Engagement-Gewichte: Like=1x, Retweet=20x, Reply=13.5x, Bookmark=10x
- Recency Decay: Halbwertszeit 3 Runden (alte Posts verschwinden schnell)
- Social Proximity: Direct Follow=1.0, Same Community=0.3, Other=0.1
- Topic Relevance: Hashtag-Overlap zwischen Agent-Interessen und Post-Hashtags
- Link Penalty: Posts mit externen Links bekommen 0.4x Score

**Feed-Assembly:** 85% relevanteste Posts + 15% Serendipity (Posts aus anderen Communities, verhindert Echo-Kammern)

**6 Aktionen:** create_post, like_post, repost, comment, follow_user, do_nothing — alle als OpenAI Function Calling Tools definiert.

**Tests:** 13 Tests in `tests/test_platform_public.py`

---

### 3.7 Authentifizierung (`backend/app/core/auth.py`)

**Was:** Schützt API-Endpoints. Nur eingeloggte User dürfen Simulationen starten.

**Methode:** Supabase Auth (Email + Passwort). JWT-Token wird im Frontend gespeichert und bei jedem API-Call mitgesendet. Backend validiert den Token via Supabase SDK.

---

## 4. Regulatorische Überlegungen

### 4.1 EU AI Act
- Swaarm fällt voraussichtlich unter **"Limited Risk"** (Transparenzpflichten, nicht High Risk)
- Alle KI-generierten Inhalte werden als solche gekennzeichnet
- Rein synthetische Personas ohne Bezug zu echten Personen → kein Social Scoring
- Pflichten ab August 2026: Technische Dokumentation (dieses Dokument), Transparenz-Kennzeichnung

### 4.2 DSGVO / nDSG
- Rein synthetische Personas → wahrscheinlich ausserhalb DSGVO-Scope
- Keine echten Social-Media-Daten werden genutzt
- Privacy-by-Design: Jede Simulation ist isoliert (eigene SQLite-Datei)
- Kunden-Daten (Email, Billing) in Supabase (GDPR-konform)

### 4.3 Trademark
- Simulierte Plattformen heissen "Öffentliches Netzwerk" und "Professionelles Netzwerk"
- Keine Twitter/LinkedIn Logos oder Markenzeichen im UI
- Nominative Fair Use in Marketing-Texten ("simuliert Twitter/LinkedIn-ähnliche Dynamiken")

---

## 5. Qualitätssicherung

### 5.1 Automatisierte Tests
Alle Module haben automatisierte Tests. Aktueller Stand: **66 Tests, alle grün.**

### 5.2 Code-Qualität
- **Ruff** (Python): Linting + automatische Formatierung bei jedem Datei-Edit (via Hook)
- **ESLint + Prettier** (TypeScript): Automatische Formatierung
- **Type Hints:** Überall in Python (Ruff checkt das)
- **Pydantic:** Alle Daten werden validiert — ungültige Eingaben werden abgefangen

### 5.3 Simulations-Qualität
Jede Simulation wird automatisch auf Qualität geprüft (Quality Badge System):
- Shannon-Entropie (Meinungsdiversität)
- Gini-Koeffizient (Engagement-Verteilung)
- Content-Uniqueness (keine Wiederholungen)
- Persona-Konsistenz (Agents bleiben in Charakter)

---

## 6. Dateiverzeichnis

```
swaarm/
├── CLAUDE.md                           # KI-Entwicklungsregeln und Architektur
├── PRD.md                              # Product Requirements Document
├── SIMULATION_ENGINE_BLUEPRINT.md      # Technischer Bauplan (22 Teile)
├── BAUPLAN_ERKLAERT.md / .docx         # Nicht-technische Erklärung
├── TECHNICAL_DOCUMENTATION.md          # Dieses Dokument
├── task_plan.md                        # Entscheidungen und Fortschritt
├── findings.md                         # Recherche-Ergebnisse
├── progress.md                         # Entwicklungs-Log
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI App Entry Point
│   │   ├── api/
│   │   │   ├── health.py               # Health Check Endpoint
│   │   │   └── auth.py                 # Auth Endpoint (/api/auth/me)
│   │   ├── core/
│   │   │   ├── config.py               # Pydantic Settings (Env Variables)
│   │   │   ├── auth.py                 # JWT Validation Middleware
│   │   │   └── supabase.py             # Supabase Client
│   │   ├── models/
│   │   │   ├── persona.py              # Persona + BigFive + Tier Models
│   │   │   ├── agent.py                # AgentState + Memory Models
│   │   │   ├── actions.py              # Action + FeedItem Models
│   │   │   └── simulation.py           # Config + Metrics + Result Models
│   │   ├── simulation/
│   │   │   ├── database.py             # SQLite DB (Schema + CRUD)
│   │   │   ├── graph.py                # Social Graph (networkx)
│   │   │   ├── willingness.py          # Agent Activation Scoring (numpy)
│   │   │   └── platforms/
│   │   │       ├── base.py             # Abstract Platform Interface
│   │   │       └── public.py           # Twitter-like Platform
│   │   └── llm/
│   │       ├── base.py                 # Abstract LLM Interface
│   │       └── openai.py               # OpenAI Implementation
│   └── tests/
│       ├── test_health.py              # API Health Check Test
│       ├── test_models.py              # Data Model Tests (18)
│       ├── test_database.py            # SQLite Tests (11)
│       ├── test_graph.py               # Social Graph Tests (14)
│       ├── test_llm.py                 # LLM Adapter Tests (10)
│       ├── test_willingness.py         # Willingness Scoring Tests (10)
│       └── test_platform_public.py     # Public Platform Tests (13)
├── frontend/
│   └── src/
│       ├── App.tsx                     # Router + Route Definitions
│       ├── main.tsx                    # Entry Point
│       ├── lib/supabase.ts             # Supabase Client
│       ├── hooks/useAuth.ts            # Auth Hook (signIn/signUp/signOut)
│       ├── components/ProtectedRoute.tsx
│       └── pages/
│           ├── LoginPage.tsx           # Login Form (Deutsch)
│           ├── RegisterPage.tsx        # Registration Form (Deutsch)
│           └── DashboardPage.tsx       # Dashboard (Empty State)
```

---

## 7. Changelog

| Datum | Commit | Was |
|-------|--------|-----|
| 2026-04-06 | `0579866` | Issue #2: Projekt-Setup & Infrastruktur |
| 2026-04-06 | `5f651b4` | Issue #3: Auth mit Supabase |
| 2026-04-06 | `157345d` | Engine Step 1: Datenmodelle |
| 2026-04-06 | `c17752e` | Engine Step 2: SQLite Schema & CRUD |
| 2026-04-06 | `86bf0c2` | Engine Step 3: Social Graph |
| 2026-04-06 | `f24b068` | Engine Step 4: LLM Adapter |
| 2026-04-06 | `b6c0152` | Engine Step 5: Willingness Scoring |
| 2026-04-06 | `d6dd567` | Engine Step 6: Public Network Platform |

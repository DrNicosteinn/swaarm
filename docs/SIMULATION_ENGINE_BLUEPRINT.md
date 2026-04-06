# Swaarm Simulation Engine — Detaillierter Bauplan

## Übersicht

Die Simulation Engine ist das Herzstück von Swaarm. Sie orchestriert tausende KI-Agenten die auf simulierten Social-Media-Plattformen interagieren. Dieser Bauplan basiert auf Research von OASIS, Stanford Generative Agents, S3, Socialtrait (Patent), und Best Practices aus der akademischen Literatur.

## Architektur-Prinzipien

1. **Tiered Agent Architecture:** Nicht alle Agents brauchen volle LLM-Calls. 3 Tiers reduzieren Kosten um 80-90%.
2. **Vectorized Activation:** Willingness Scoring über numpy Arrays — <5ms für 50k Agents.
3. **Prompt Caching:** Statischer Prefix (Persona + Rules) cacheable, dynamischer Suffix (Feed + Memory) minimal.
4. **Platform Abstraction:** Öffentliches und Professionelles Netzwerk hinter einem gemeinsamen Interface.
5. **Event-Driven:** Jede Runde emittiert Events für Live-Streaming.

---

## Teil 1: Agent State Model

### Persona (statisch, einmal generiert)

```python
class Persona(BaseModel):
    """Statischer Teil eines Agents — ändert sich nie während Simulation."""
    id: str
    name: str
    age: int
    gender: str
    location: str  # z.B. "Zürich, CH"
    occupation: str

    # Big Five Persönlichkeit (je 0.0-1.0)
    openness: float
    conscientiousness: float
    extraversion: float
    agreeableness: float
    neuroticism: float

    # Soziale Rolle
    agent_tier: Literal["creator", "contributor", "lurker"]  # 1/9/90 Verteilung

    # Meinungen & Interessen
    opinions: dict[str, float]  # z.B. {"climate": 0.8, "tech": -0.3} (-1 bis 1)
    interests: list[str]
    posting_style: str  # z.B. "sarkastisch und kurz" oder "analytisch und ausführlich"

    # Professionell (nur LinkedIn)
    job_title: str | None = None
    seniority: str | None = None  # "Junior", "Mid", "Senior", "C-Level"
    industry: str | None = None
    company_size: str | None = None

    # Verhalten
    posting_frequency: float  # Posts pro Tag (0.1 = selten, 5.0 = power user)
    activity_hours: list[int]  # Stunden am Tag wo aktiv (z.B. [8,9,12,13,18,19,20])
```

### Agent State (dynamisch, ändert sich jede Runde)

```python
class AgentState(BaseModel):
    """Dynamischer Zustand eines Agents während der Simulation."""
    persona_id: str

    # Memory (sliding window + important memories)
    recent_observations: list[str]  # Letzte 3-5 Beobachtungen
    important_memories: list[str]   # High-importance Erinnerungen (max 5)
    memory_summary: str             # Komprimierte Zusammenfassung aller Erinnerungen

    # Zustand
    current_sentiment: float        # -1.0 bis 1.0
    opinion_shifts: dict[str, float]  # Meinungsänderungen seit Start
    posts_created: int
    last_active_round: int
    total_engagement_received: int  # Likes + Comments auf eigene Posts

    # Cooldown
    cooldown_until: int             # Runde bis Agent wieder aktiv sein kann
```

### Verteilung der Agent Tiers (DYNAMISCH je nach Szenario)

Die Verteilung ist NICHT fix — sie wird automatisch vom Prompt Builder basierend auf der
Kontroversität/Relevanz des Szenarios bestimmt.

| Tier | Krise (80%+ aktiv) | Standard (50% aktiv) | Routine (30% aktiv) |
|------|-------------------|---------------------|-------------------|
| Power Creator | 10% | 5% | 3% |
| Active Responder | 40% | 25% | 12% |
| Selective Engager | 30% | 20% | 15% |
| Observer | 20% | 50% | 70% |

| Tier | LLM-Nutzung | Verhalten |
|------|-------------|-----------|
| Power Creator | Voller LLM-Call | Erstellen Posts, Threads, Artikel, lange Kommentare |
| Active Responder | Voller LLM-Call | Kommentare, Reaktionen, Shares, Follows |
| Selective Engager | Vereinfachter LLM-Call | Reagiert nur bei hoher Relevanz, kurze Kommentare |
| Observer | Minimaler LLM-Call oder regelbasiert | Liest, liked gelegentlich |

**Szenario-Erkennung durch Prompt Builder:**
- Input-Analyse: Kontroversität, Betroffenheit, Emotionalität → Score 0-1
- Score 0.0-0.3 = Routine-Verteilung (30% aktiv)
- Score 0.3-0.6 = Standard-Verteilung (50% aktiv)
- Score 0.6-1.0 = Krisen-Verteilung (80%+ aktiv)

**Kostenimpact bei 10'000 Agents × 50 Runden:**
- Krise (80% aktiv): ~120k LLM-Calls → ~$24
- Standard (50% aktiv): ~60k LLM-Calls → ~$12
- Routine (30% aktiv): ~30k LLM-Calls → ~$6

---

## Teil 2: Willingness Scoring (Agent-Aktivierung)

### Grundprinzip

Nicht alle Agents sind jede Runde aktiv. Ein Willingness Score bestimmt die Wahrscheinlichkeit, dass ein Agent in einer bestimmten Runde handelt.

### Scoring-Formel (Socialtrait-inspiriert, eigene Implementierung)

```python
import numpy as np

def compute_activation(
    agents: np.ndarray,          # (n_agents, n_features)
    context: RoundContext,
    rng: np.random.Generator,
) -> np.ndarray:                 # Boolean mask: wer ist aktiv
    """Berechne Aktivierung für alle Agents in einer Runde. Vectorized."""

    n = len(agents)

    # 1. Persona-basierte Grundwilligkeit (statisch pro Agent)
    #    Gewichtet: Extraversion (0.30) + Tier-Bonus (0.25) +
    #    Posting-Frequenz (0.20) + Meinungsstärke (0.15) + Neurotizismus (0.10)
    s_persona = (
        0.30 * agents[:, IDX_EXTRAVERSION] +
        0.25 * agents[:, IDX_TIER_BONUS] +      # Creator=0.8, Contributor=0.3, Lurker=0.02
        0.20 * agents[:, IDX_POST_FREQ_NORM] +
        0.15 * agents[:, IDX_OPINION_STRENGTH] +
        0.10 * agents[:, IDX_NEUROTICISM]
    )

    # 2. Kontext-basierte Willigkeit (dynamisch pro Runde)
    #    Gewichtet: Topic-Relevanz (0.30) + Netzwerk-Aktivität (0.25) +
    #    Emotionale Valenz (0.20) + Konversations-Momentum (0.15) + Neuheit (0.10)
    s_context = (
        0.30 * context.topic_relevance_scores +    # Cosine similarity Agent-Interessen vs. aktuelle Themen
        0.25 * context.network_activity_scores +   # Haben Followees gepostet?
        0.20 * context.emotional_valence +          # Kontroversität des aktuellen Diskurses
        0.15 * context.conversation_momentum +      # Anzahl Interaktionen letzte Runde
        0.10 * context.novelty_scores               # Neue Themen vs. Wiederholung
    )

    # 3. Unified Score (Socialtrait-inspiriert)
    lambda_ = 1.5  # Decay-Parameter
    s_unified = s_persona * np.exp(-lambda_ * (s_context - s_persona))

    # 4. Cooldown-Multiplikator
    rounds_since_active = context.current_round - agents[:, IDX_LAST_ACTIVE]
    cooldown_factor = np.where(
        agents[:, IDX_TIER] == TIER_CREATOR,
        np.minimum(rounds_since_active / 2, 1.0),      # Creator: 2 Runden Cooldown
        np.where(
            agents[:, IDX_TIER] == TIER_CONTRIBUTOR,
            np.minimum(rounds_since_active / 4, 1.0),  # Contributor: 4 Runden
            np.minimum(rounds_since_active / 15, 1.0),  # Lurker: 15 Runden
        )
    )
    s_unified *= cooldown_factor

    # 5. Stochastische Aktivierung (Bernoulli Sampling)
    #    Score als Wahrscheinlichkeit interpretieren
    s_unified = np.clip(s_unified, 0.0, 0.95)  # Max 95% Wahrscheinlichkeit
    activated = rng.random(n) < s_unified

    return activated
```

### Erwartete Aktivierung pro Runde

| Simulation | Total Agents | Erwartete Aktive | Davon Creators | Davon Contributors | Davon Lurkers |
|------------|-------------|-----------------|----------------|-------------------|---------------|
| 1'000 | 1'000 | 30-80 | 5-10 | 20-50 | 5-20 |
| 10'000 | 10'000 | 150-400 | 30-60 | 100-250 | 20-90 |
| 50'000 | 50'000 | 500-1'500 | 100-250 | 300-800 | 100-450 |

---

## Teil 3: Simulation Loop

### Ablauf einer Runde

```
Runde N:
│
├── 1. AKTIVIERUNG (< 5ms, vectorized numpy)
│   └── Willingness Scoring → Boolean Mask aktiver Agents
│
├── 2. FEED GENERATION (< 50ms, SQL + numpy)
│   ├── Für jeden aktiven Agent: relevante Posts aus DB laden
│   ├── Feed-Algorithmus anwenden (plattformspezifisch)
│   └── Feed in kompaktes Textformat serialisieren
│
├── 3. LLM DECISION (bottleneck, async parallel)
│   ├── Tier 1 (Creators): Voller LLM-Call mit Function Calling
│   │   ├── System Prompt: Persona + Plattform-Regeln + Tool-Schema (~1100 tokens, CACHED)
│   │   ├── User Prompt: Memory + Feed + "Was willst du tun?" (~400 tokens)
│   │   └── Response: Action + Content (z.B. CREATE_POST + Posttext)
│   ├── Tier 2 (Contributors): Vereinfachter LLM-Call
│   │   ├── Kürzerer Prompt (~600 tokens total)
│   │   └── Response: Einfache Action (LIKE, COMMENT mit kurzem Text)
│   └── Tier 3 (Lurkers): KEIN LLM-Call
│       └── Regelbasiert: Like mit P(sentiment_match > 0.7)
│
├── 4. ACTION EXECUTION (< 20ms, SQLite writes)
│   ├── Posts in DB schreiben
│   ├── Likes, Comments, Follows in DB schreiben
│   ├── Social Graph updaten (neue Follows/Connects)
│   └── Agent State updaten (Memory, Sentiment, Cooldown)
│
├── 5. METRICS COLLECTION (< 10ms)
│   ├── Sentiment-Aggregation pro Runde
│   ├── Engagement-Zähler updaten
│   ├── Narrative/Topic-Tracking
│   └── Token-Usage loggen
│
└── 6. EVENT EMISSION (< 5ms)
    ├── Neue Posts/Likes/Follows als Events verpacken
    ├── Graph-Änderungen als Events
    ├── Sentiment-Update als Event
    └── Via Callback an WebSocket-Handler senden
```

### Gesamtdauer pro Runde (geschätzt)

| Scale | Aktivierung | Feed Gen | LLM Calls (30 concurrent) | Actions | Total |
|-------|------------|----------|--------------------------|---------|-------|
| 1'000 Agents | <1ms | ~5ms | ~3-8s | ~2ms | ~5-10s |
| 10'000 Agents | ~2ms | ~20ms | ~15-40s | ~10ms | ~20-45s |
| 50'000 Agents | ~5ms | ~100ms | ~60-180s | ~50ms | ~1-3min |

---

## Teil 4: Prompt-Architektur

### System Prompt (CACHED — ~1'100 tokens)

```
Du bist {name}, {age} Jahre alt, {occupation} aus {location}.

PERSÖNLICHKEIT:
- Extraversion: {extraversion_text} (z.B. "eher introvertiert, postest selten")
- Meinungsstärke: {opinion_strength_text}
- Kommunikationsstil: {posting_style}

DEINE MEINUNGEN:
- {topic1}: {opinion_text1} (z.B. "Klimaschutz: stark dafür")
- {topic2}: {opinion_text2}

WICHTIGE REGELN:
- Du postest NUR wenn du wirklich etwas zu sagen hast
- Dein Stil ist IMMER {posting_style}
- Du änderst deine Grundmeinungen NICHT leichtfertig
- Du reagierst auf kontroverse Themen {reactivity_text}

PLATTFORM: {platform_name} (z.B. "Öffentliches Netzwerk")
VERFÜGBARE AKTIONEN: [via Function Calling Tools definiert]
```

### User Prompt (DYNAMISCH — ~400 tokens)

```
ERINNERUNGEN:
{memory_summary}
{recent_observation_1}
{recent_observation_2}

DEIN FEED (aktuelle Posts):
[P1] @Max_Mueller (vor 5min): "Die neue Entlassungswelle bei SwissBank..."
  ↳ 12 Likes, 3 Kommentare | Sentiment: negativ
[P2] @Anna_Tech (vor 12min): "Employer Branding ist..."
  ↳ 5 Likes, 1 Kommentar | Sentiment: neutral

RUNDE: {current_round}/{total_rounds}
WAS WILLST DU TUN?
```

### Function Calling Tools (Öffentliches Netzwerk)

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "create_post",
            "description": "Erstelle einen neuen Post",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Der Posttext (max 280 Zeichen)"},
                    "hashtags": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "like_post",
            "description": "Like einen Post",
            "parameters": {
                "type": "object",
                "properties": {
                    "post_id": {"type": "string"},
                },
                "required": ["post_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "comment",
            "description": "Kommentiere einen Post",
            "parameters": {
                "type": "object",
                "properties": {
                    "post_id": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["post_id", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "repost",
            "description": "Teile einen Post",
            "parameters": {
                "type": "object",
                "properties": {
                    "post_id": {"type": "string"},
                },
                "required": ["post_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "follow_user",
            "description": "Folge einem User",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                },
                "required": ["user_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "do_nothing",
            "description": "Nichts tun, nur beobachten",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]
```

---

## Teil 5: Memory System

### Lightweight Design (kein Embedding-basiertes Retrieval im MVP)

```
Pro Agent, pro Runde:

1. BEOBACHTUNG speichern:
   - Was hat der Agent in seinem Feed gesehen?
   - Kompakt: "Runde 5: Sah 3 negative Posts über Entlassungen bei SwissBank"

2. SLIDING WINDOW (letzte 3-5 Beobachtungen):
   - Direkt im Prompt als "Erinnerungen"
   - Älteste wird entfernt wenn Fenster voll

3. IMPORTANCE SCORING:
   - Eigener Post mit >10 Likes = wichtig (behalten)
   - Kontroverse Diskussion = wichtig
   - Routine-Like = unwichtig (nicht speichern)
   - Schwelle: importance > 5 (Skala 1-10, vom LLM in Action-Response mitgeliefert)

4. MEMORY SUMMARY (alle 5 Runden):
   - LLM fasst alle Erinnerungen in 2-3 Sätze zusammen
   - Ersetzt die detaillierten Erinnerungen
   - Spart Tokens, behält Kern-Informationen
```

### Token-Budget pro Agent-Call

| Komponente | Tokens | Cacheable? |
|-----------|--------|-----------|
| System Prompt (Persona + Rules + Tools) | ~1'100 | JA (50% Rabatt) |
| Memory Summary | ~60 | Nein |
| Recent Observations (3 Stück) | ~90 | Nein |
| Feed (3-5 Posts kompakt) | ~200 | Nein |
| Action Prompt | ~50 | Nein |
| **Total Input** | **~1'500** | **73% cacheable** |
| Output (Action + Content) | ~100-200 | — |

### Kosten pro Simulation (mit Caching)

| Scale | Aktive Calls (50 Runden) | Input Tokens | Output Tokens | Kosten (GPT-4o-mini) |
|-------|------------------------|-------------|---------------|---------------------|
| 1'000 Agents | ~2'500 | ~3.75M (73% cached) | ~375K | ~$0.60 |
| 10'000 Agents | ~15'000 | ~22.5M (73% cached) | ~2.25M | ~$3.50 |
| 50'000 Agents | ~50'000 | ~75M (73% cached) | ~7.5M | ~$12.00 |

---

## Teil 6: Social Graph

### Struktur

```python
import networkx as nx

class SocialGraph:
    """Social Graph für die Simulation."""

    def __init__(self, platform_type: str):
        if platform_type == "public":
            # Twitter: Directed Graph (Follow ≠ Follow-back)
            self.graph = nx.DiGraph()
        else:
            # LinkedIn: Undirected Graph (Connection = bilateral)
            self.graph = nx.Graph()

    def initialize(self, agents: list[Persona], config: GraphConfig):
        """Erstelle initialen Graph mit Community-Struktur."""
        # 1. Alle Agents als Nodes hinzufügen
        # 2. Communities bilden (basierend auf Interessen/Branche)
        # 3. Intra-Community Edges (dicht verbunden)
        # 4. Inter-Community Edges (schwache Verbindungen, ~5-10%)
        # 5. Influencer-Hub Connections (Creators folgen/verbinden mit vielen)
```

### Community-Generierung

```
Für ein Szenario "SwissBank Entlassungen":

Community 1: SwissBank-Mitarbeiter (15%)
  - Intern stark vernetzt
  - Wenige Verbindungen nach aussen

Community 2: Finanzbranche-Analysten (10%)
  - Folgen Mitarbeitern + Journalisten

Community 3: Tech/HR-Professionals (15%)
  - Diskutieren Employer Branding

Community 4: Journalisten/Medien (5%)
  - Werden von vielen gefolgt (Hub-Nodes)

Community 5: Allgemeine Öffentlichkeit (55%)
  - Lose verbunden, folgen Influencern

Inter-Community Links: ~5-10% der Edges
→ Erzeugt realistische Echo-Chambers mit Bridges
```

---

## Teil 7: Plattform-Abstraction

### Interface

```python
from abc import ABC, abstractmethod

class PlatformBase(ABC):
    """Gemeinsames Interface für alle simulierten Plattformen."""

    @abstractmethod
    def get_action_types(self) -> list[ActionType]: ...

    @abstractmethod
    def generate_feed(self, agent_id: str, round: int) -> list[FeedItem]: ...

    @abstractmethod
    def execute_action(self, agent_id: str, action: Action) -> ActionResult: ...

    @abstractmethod
    def get_tools_schema(self) -> list[dict]: ...

    @abstractmethod
    def format_feed_for_prompt(self, feed: list[FeedItem]) -> str: ...

    @abstractmethod
    def compute_feed_scores(self, posts: list, agent: Persona) -> np.ndarray: ...
```

### Öffentliches Netzwerk (Twitter-like)

```
Actions: CREATE_POST, LIKE, REPOST, COMMENT, FOLLOW, DO_NOTHING
Feed: Follower-Posts + Trending + Random Discovery
Scoring: Engagement * Recency * Follower-Nähe
Viralität: Hoch (Repost-Kaskaden möglich)
```

### Professionelles Netzwerk (LinkedIn-like)

```
Actions: POST, ARTICLE, 6x REACT (Like/Celebrate/Insightful/Funny/Love/Support),
         COMMENT, REPLY, SHARE, CONNECT, FOLLOW, ENDORSE, DO_NOTHING
Feed: 360Brew-inspiriert: Relevanz + Expertise + Dwell-Time
Scoring: Comment-Weight 15x > Reaction, Dwell-Time stärkster Faktor
Viralität: Niedrig (24-48h Distribution Window)
```

---

## Teil 8: Event System (für Live-Streaming)

### Event Types

```python
class SimulationEvent(BaseModel):
    round: int
    timestamp: datetime
    event_type: Literal[
        "post_created",
        "post_liked",
        "post_reposted",
        "post_commented",
        "user_followed",
        "user_connected",
        "sentiment_update",
        "round_complete",
        "simulation_complete",
    ]
    data: dict  # Event-spezifische Daten
```

### Callback-Mechanismus

```python
class SimulationEngine:
    def __init__(self, config, event_callback=None):
        self.event_callback = event_callback  # z.B. WebSocket-Handler

    async def emit_event(self, event: SimulationEvent):
        if self.event_callback:
            await self.event_callback(event)
```

---

## Teil 9: Meinungsdiversität & Anti-Sycophancy

### Problem
LLMs neigen zu "sycophancy" — sie stimmen zu statt zu widersprechen. Ohne Gegenmassnahmen konvergieren alle Agents zu einer Meinung.

### Gegenmassnahmen

1. **Explizite Meinungs-Verankerung:** Jede Persona hat feste Meinungswerte (-1 bis +1) die im System-Prompt stehen.

2. **Meinungs-Inertia:** Meinungen ändern sich nur langsam:
   ```
   new_opinion = 0.8 * current_opinion + 0.2 * influence
   ```
   → 80% Trägheit, 20% Einfluss pro Interaktion

3. **Zealot-Agents (5-10%):** Agents deren Meinung sich NIEMALS ändert. Dienen als Anker für Diversität.

4. **Bounded Confidence:** Agents ignorieren Posts die >0.5 von ihrer eigenen Meinung entfernt sind. Erzeugt natürliche Echo-Chambers.

5. **Contrarian-Persönlichkeitstyp:** ~5% der Agents widersprechen grundsätzlich der Mehrheitsmeinung.

6. **Verteilungs-Vorgabe:** Bei Persona-Generierung: 30% positiv / 40% neutral / 30% negativ zum Thema.

---

## Teil 10: Implementierungs-Reihenfolge (Teilschritte)

### Schritt 1: Datenmodelle (1 Tag)
- [ ] Pydantic Models: Persona, AgentState, Action, ActionResult, FeedItem, SimulationEvent
- [ ] SimulationConfig Model (agent_count, round_count, platform, scenario)
- [ ] Tests: Modelle validieren, Serialisierung

### Schritt 2: SQLite Schema & CRUD (1 Tag)
- [ ] Schema: users, posts, likes, comments, reposts, follows/connections
- [ ] Async CRUD Operationen (aiosqlite)
- [ ] Tests: CRUD Operationen

### Schritt 3: Social Graph (1 Tag)
- [ ] SocialGraph Klasse (networkx)
- [ ] Community-Generierung mit Inter-Community-Bridges
- [ ] Follow/Connect/Unfollow Operationen
- [ ] Feed-Generation (Posts von Followees)
- [ ] Tests: Graph-Operationen, Community-Struktur

### Schritt 4: LLM Adapter (1 Tag)
- [ ] Abstract LLM Interface
- [ ] OpenAI Implementation (async, Function Calling, structured output)
- [ ] Token-Usage Tracking
- [ ] Retry mit Exponential Backoff
- [ ] Tests: Mock-LLM für deterministische Tests

### Schritt 5: Willingness Scoring (1 Tag)
- [ ] Vectorized numpy Scoring
- [ ] Persona-basierte + Kontext-basierte Komponenten
- [ ] Cooldown-System per Tier
- [ ] Stochastische Aktivierung (Bernoulli)
- [ ] Tests: Verteilung der Aktivierung, Tier-Verhalten

### Schritt 6: Plattform Module — Öffentliches Netzwerk (2 Tage)
- [ ] PlatformBase Interface
- [ ] PublicNetwork Implementation
- [ ] 6 Action Types + Function Calling Tools (strict: true)
- [ ] Feed-Algorithmus (Twitter-Gewichte: Like 1x, RT 20x, Reply 13.5x, Recency Half-Life 3)
- [ ] Feed-Assembly (85% relevant + 15% serendipity, Pre-Filter für Effizienz)
- [ ] Feed-zu-Prompt Serialisierung (kompaktes Textformat, 3-5 Posts, ~200 Tokens)
- [ ] Tests: Actions, Feed-Ranking, Feed-Diversity

### Schritt 7: Agent Memory System (1 Tag)
- [ ] Sliding Window (letzte 3-5 Beobachtungen)
- [ ] Importance Scoring
- [ ] Memory Summary (alle 5 Runden)
- [ ] Token-Budget Management
- [ ] Tests: Memory-Operationen

### Schritt 8: Simulation Loop (2 Tage)
- [ ] Haupt-Loop: Aktivierung → Feed → LLM → Actions → Metrics → Events
- [ ] Async Concurrency (Semaphore für LLM-Calls)
- [ ] Tier-basierte Verarbeitung (Tier 1 voll, Tier 2 vereinfacht, Tier 3 regelbasiert)
- [ ] Event Emission Callback
- [ ] Graceful Error Handling (einzelner Agent-Fehler stoppt nicht die Simulation)
- [ ] Tests: Komplette Mini-Simulation (10 Agents, 3 Runden)

### Schritt 9: Metrics & Quality Assurance (1.5 Tage)
- [ ] Sentiment-Aggregation pro Runde
- [ ] Engagement-Tracking (Posts, Likes, Comments, Shares pro Runde)
- [ ] Narrative-Tracking (häufige Themen/Keywords)
- [ ] Token-Usage + Kosten-Logging
- [ ] Quality Metrics: Shannon-Entropie, Gini-Koeffizient, Trigram-Uniqueness
- [ ] Quality Badge System (Grün/Gelb/Rot)
- [ ] Tests: Metriken-Berechnung, Quality-Thresholds

### Schritt 10: Error Handling & Resilience (1 Tag)
- [ ] Retry mit Exponential Backoff + Full Jitter
- [ ] Circuit Breaker (15% Failure → Pause)
- [ ] Agent-Degradation bei Fehler (→ Observer)
- [ ] Pydantic-Validation + Fallback für ungültige LLM-Responses
- [ ] Budget-Safety (Ceiling pro Simulation)
- [ ] Partial Results (is_usable Flag)
- [ ] Tests: Fehler-Szenarien, Degradation

### Schritt 11: Checkpoint & Recovery (0.5 Tage)
- [ ] Checkpoint alle 5 Runden in SQLite
- [ ] Resume-Logik (letzten Checkpoint laden, fortfahren)
- [ ] Letzte 3 Checkpoints behalten
- [ ] Tests: Save/Load Checkpoint, Resume

### Schritt 12: Integration Test (1 Tag)
- [ ] End-to-End Simulation mit echtem LLM (10 Agents, 5 Runden)
- [ ] Ergebnisse in SQLite verifizieren
- [ ] Events korrekt emittiert
- [ ] Quality Metrics im grünen Bereich
- [ ] Error Handling funktioniert (simulierter API-Fehler)
- [ ] Checkpoint + Resume funktioniert
- [ ] Performance-Messung
- [ ] Kosten-Tracking verifizieren

---

## Teil 11: Quality Assurance System

### Automatische Qualitätsmetriken (pro Simulation)

| Metrik | Was sie misst | Gesund | Warnung | Kritisch |
|--------|-------------|--------|---------|----------|
| Shannon-Entropie (Sentiment) | Meinungsdiversität | 0.5-0.8 | 0.3-0.5 | <0.3 (Mode Collapse) |
| Engagement Gini-Koeffizient | Power-Law-Verteilung | 0.5-0.8 | >0.9 | <0.3 (unrealistisch gleich) |
| Unique-Trigram-Ratio | Content-Vielfalt | >0.6 | 0.4-0.6 | <0.4 (Wiederholung) |
| Persona-Konsistenz (Stichprobe) | Bleiben Agents in Charakter? | >0.7 | 0.5-0.7 | <0.5 (Drift) |
| Clustering-Koeffizient | Realistische Community-Struktur | 0.1-0.5 | <0.05 | >0.8 (unrealistisch) |

### Quality Badge System

- **GRÜN:** Alle Metriken im gesunden Bereich → "Hohe Simulationsqualität"
- **GELB:** 1-2 Metriken im Warnbereich → "Simulation nutzbar, eingeschränkte Diversität"
- **ROT:** Metriken im kritischen Bereich → "Simulation möglicherweise unzuverlässig"

Badge wird im Report angezeigt. Transparenz statt inflationärer Accuracy-Claims.

### Validierungsstrategie (nach MVP)

1. **Phase 1 (MVP):** Automatische Metriken + Quality Badge
2. **Phase 2:** Retrospektive Validierung gegen 10-20 historische PR-Events
3. **Phase 3:** Prospektive Validierung mit Kundenpartnerschaften

---

## Teil 12: Error Handling & Resilience

### Retry-Strategie

Exponential Backoff mit Full Jitter, max 5 Retries. Fehler-Klassifizierung:

| Fehlertyp | Aktion | Retry? |
|-----------|--------|--------|
| Rate Limit (429) | Backoff, Retry-After Header respektieren | Ja |
| Timeout | Retry mit gleichem Request | Ja |
| Server Error (500/502/503) | Retry mit Backoff | Ja (max 3) |
| Token Limit (400) | Input kürzen, einmal retry | Einmal |
| Content Filter (400) | Loggen, Fallback-Response | Nein |
| Auth Error (401/403) | Simulation stoppen | Nein |

### Circuit Breaker

- Einzelner Agent-Fehler → Agent wird zum Observer degradiert (nicht Simulation stoppen)
- >15% Agent-Fehler in einer Runde → Simulation pausieren, Alert senden
- >50 konsekutive Rate Limits → Concurrency automatisch reduzieren

### Graceful Degradation

- LLM liefert ungültigen Output → Pydantic-Validation → JSON-Extraction Fallback → "Observe" Default
- Simulation crasht bei Runde 25/50 → Ergebnisse bis Runde 25 sind nutzbar (`is_usable: true` wenn >60% complete)
- Budget überschritten → Simulation sauber beenden, Teilergebnis liefern

---

## Teil 13: Checkpoint & Recovery

### Was wird gespeichert (alle 5 Runden)

- Agent States (Memory, Sentiment, Cooldowns)
- Social Graph (Edges + Weights)
- Platform State (Posts, Comments, Engagement Counts)
- RNG State (für Reproduzierbarkeit)
- Kosten-Tracking (Total Tokens, Total Cost)

### Resume-Logik

Bei Neustart: Letzten Checkpoint aus SQLite laden → State wiederherstellen → Ab nächster Runde fortfahren.
Letzte 3 Checkpoints behalten, ältere löschen.

---

## Teil 14: Concurrency & Rate Limiting

### Dual Token-Bucket Rate Limiter

Zwei Buckets gleichzeitig: Requests/Minute UND Tokens/Minute.
Backpressure via async wait wenn Bucket leer.

### Batched Task Execution

Nicht alle 50k Agents gleichzeitig launchen:
- Batches von 500 Agents via TaskGroup (Python 3.12)
- Max 200 concurrent in-flight LLM Calls (Semaphore)
- Jede Coroutine: ~2-3KB RAM → 500 Batch = ~1.5MB aktiv

### SQLite Performance

- WAL Mode (Write-Ahead Logging) mandatory für concurrent reads/writes
- Batch Inserts via executemany (100x schneller als Einzel-Inserts)
- Single Writer + Reader Pool (4 Connections)
- Cache Size: 64MB, Memory-Mapped I/O: 256MB

---

## Teil 15: Observability

### Structured Logging

Jede Runde loggt: Anzahl aktive Agents, Actions, Fehler, LLM-Calls, Kosten, Dauer.
Kontext: simulation_id + round_number in jedem Log-Entry.

### Real-Time Progress via WebSocket

Pro Runde an Frontend pushen:
- Fortschritt (Runde X/Y, % complete, geschätzte Restzeit)
- Kosten bisher (USD)
- Gesundheit (Error Rate, Latenz, Failed Agents)
- Throughput (LLM Calls/s, Tokens used)

### Budget-Safety

Token-Usage pro Call tracken. Budget-Ceiling pro Simulation.
Wenn überschritten → Simulation sauber beenden, nicht crashen.

---

## Teil 16: Erkenntnisse von MiroFish & Anderen

### Von MiroFish übernehmen
- **GraphRAG als Fundament:** Entitäten aus dem Seed-Dokument extrahieren BEVOR Personas generiert werden. Agents sind im tatsächlichen Kontext verankert.
- **Action-as-FunctionTool:** Plattform-Actions via OpenAI Function Calling exponieren. Sauber und erweiterbar.

### Von Stanford Generative Agents
- **Memory Scoring:** score = alpha * recency + beta * importance + gamma * relevance
- **Reflection Triggers:** Wenn kumulative Importance > 150, dann 2-3 Reflections generieren

### Von S3 Social Simulation
- **Markov-Pipeline pro Tick:** Emotion Update → Attitude Update → Interaction Decision → Content Generation

### Von AgentSociety
- **Mind-Behavior Coupling:** Agents in Verhaltensforschungs-Theorien verankern, nicht nur Persönlichkeits-Prompts

### NICHT übernehmen
- **Prompt Batching** (mehrere Agents in einem Call): Verursacht Cross-Kontamination und Cache-Invalidierung
- **Subprocess-Isolation** (MiroFish): Unnötige Komplexität für unseren Use Case

---

## Teil 17: DACH Persona-Sprache

### Grundregel: Hochdeutsch als Basis, regional differenziert über Vokabular

GPT-4o-mini handelt Deutsch gut (87% MGSM Benchmark). Aber: Schweizerdeutsch ist unmöglich (~4% Accuracy).
Das ist kein Problem — echte DACH-User schreiben auf Social Media Hochdeutsch mit regionalen Markern.

| Region | Sprachstrategie | Marker |
|--------|----------------|--------|
| Deutschland | Standard Hochdeutsch + regionale Referenzen | Moin (Nord), Digga, t3n, Heise, BfDI |
| Österreich | Hochdeutsch + österreichisches Vokabular | Jänner, heuer, Matura, AK, WKO, Der Standard |
| Schweiz | Hochdeutsch + Helvetismen | Velo, parkieren, Natel (ironisch), NZZ, SRF, FINMA |

### Prompt-Sprache: Hybrid

- **Englisch** für: Struktur, Constraints, Action-Schema, Output-Format
- **Deutsch** für: Persona-Biografie, kultureller Kontext, Stil-Beispiele, Anti-Patterns

### Anti-Patterns in Prompts (kritisch für Authentizität)

Jede Persona braucht negative Beispiele:
- "Schreibe NICHT wie ein Marketing-Bot"
- "Keine Floskeln wie 'In der heutigen schnelllebigen Welt...'"
- "Keine übertriebenen Regional-Klischees (Schokolade, Berge, Sachertorte)"
- "Maximal 1-2 Emojis (DACH nutzt weniger Emojis als US)"

### Register explizit verankern

Jede Persona muss definieren: du/Sie, Emoji-Dichte, Post-Länge, Abkürzungs-Toleranz.
GPT-4o-mini wählt NICHT automatisch den richtigen Register.

---

## Teil 18: Narrative Detection & Topic Clustering

### Ansatz: Embedding-Clustering + LLM-Labeling (Hybrid)

**Tier 1 — Leichtgewichtiges Clustering (jede Runde):**
- Alle neuen Posts mit `paraphrase-multilingual-MiniLM-L12-v2` embedden (lokal, ~50ms für 1000 Posts)
- Agglomerative Clustering mit Cosine Distance (scikit-learn)
- Neue Cluster mit bestehenden Narrativen matchen via Centroid-Cosine-Similarity

**Tier 2 — LLM-Labeling (nur bei neuen/geänderten Clustern):**
- Top 10 Posts eines neuen Clusters an GPT-4o-mini senden
- Prompt: "Fasse das Narrativ in 3-5 Wörtern auf Deutsch zusammen"
- Labels cachen, nur bei signifikanter Cluster-Veränderung neu generieren

### Narrative-Lifecycle

| Status | Definition |
|--------|-----------|
| Emerging | Neues Cluster, kein Match zu bestehenden Narrativen |
| Active | Cluster existiert seit 2+ Runden, wächst oder stabil |
| Declining | Cluster-Grösse schrumpft 2+ Runden in Folge |
| Dead | Kein Post in 3+ aufeinanderfolgenden Runden |

### Tracking pro Runde

Pro Narrativ: Post-Count, Unique Agents, Durchschnitts-Sentiment, Growth-Rate, Top 5 Posts.
Ermöglicht im Report: "Narrativ 'Kritik an Preiserhöhung' entstand in Runde 8, wuchs bis Runde 15, dann abnehmend."

### Dependencies

```toml
sentence-transformers = ">=3.0"   # Lokales Embedding, ~500MB Modell
scikit-learn = ">=1.4"            # AgglomerativeClustering
```

---

## Teil 19: Feed-Algorithmen (Detail)

### Twitter-Like Scoring

```
score = log(1 + engagement_weighted) × recency_decay × social_proximity × topic_relevance × boosts

Engagement-Gewichte (aus Twitter Open Source):
  Like = 1x, Retweet = 20x, Reply = 13.5x, Bookmark = 10x, Quote = 15x

Recency: Half-Life 3 Runden (schneller Decay)
Social Proximity: Direct Follow = 1.0, 2-Hop = 0.3, Same Cluster = 0.15, None = 0.05
Boosts: Verified 1.5x, Media 1.2x
Penalties: External Link 0.4x
```

### LinkedIn-Like Scoring (360Brew-inspiriert)

```
score = log(1 + sqrt(engagement)) × slow_recency × professional_proximity × expertise_alignment × dwell_prediction × format_mult × virality_dampener

Engagement-Gewichte:
  Like = 1x, Short Comment = 2x, Long Comment (15+ Wörter) = 4x,
  Comment Reply = 4.8x, Save = 5x, Share = 3x

Recency: Half-Life 8 Runden (langsamer Decay — professioneller Content lebt länger)
Expertise Alignment: Passt der Autor zum Thema? (360Brew Cross-Reference)
Dwell Prediction: Content-Länge × Topic-Match × Format-Faktor
Format Multiplier: Carousel 2.4x, Video 3x, Image 1.2x, Text 1x, Link 0.5x
Virality Dampener: Bewusst keine virale Verbreitung (LinkedIn-Design)
```

### Feed-Assembly (beide Plattformen)

Pro Agent pro Runde: 3-5 Posts. Zusammengesetzt aus:
- 85% relevanteste Posts (nach Score)
- 15% Serendipity (Cross-Cluster Discovery, verhindert Echo-Chambers)

Effizienz bei 50k Agents: Nicht jeder Agent gegen jeden Post scoren.
Pre-Filter: Connection-Posts + Top-100-Trending + 25 Random Out-of-Network.

---

## Teil 20: Persona-Generierung (Detail)

### Pipeline

```
1. Szenario-Input → LLM: Stakeholder-Rollen identifizieren (1 Call)
2. Stakeholder-Mix × DACH-Demografie → 50 Batch-Constraints generieren (Code)
3. 50 Batch-Calls à 10 Personas → 500 Basis-Personas ($0.07 total)
4. Diversitäts-Validierung (Code: Verteilungen prüfen)
5. Parametrische Variation → 500 auf 10k-50k skalieren (Code, $0)
```

### DACH-Kalibrierung (Sinus-Milieus)

| Milieu | Anteil | Personas (von 500) |
|--------|--------|-------------------|
| Konservativ-Gehobenes | 11% | 55 |
| Postmaterielles | 12% | 60 |
| Performer | 10% | 50 |
| Expeditives | 10% | 50 |
| Neo-Ökologisches | 8% | 40 |
| Adaptiv-Pragmatische Mitte | 12% | 60 |
| Konsum-Hedonistisches | 8% | 40 |
| Prekäres | 9% | 45 |
| Nostalgisch-Bürgerliches | 11% | 55 |
| Traditionelles | 9% | 45 |

### Szenario-spezifische Stakeholder-Templates

Vordefinierte Templates für häufige Szenarien (anpassbar):
- **Unternehmenskrise:** 15% Mitarbeiter, 25% Kunden, 5% Journalisten, 3% Konkurrenz, 5% Investoren, 35% Öffentlichkeit, 5% Aktivisten, 5% Politiker, 2% Regulatoren
- **Produktlaunch:** 35% Zielkunden, 20% Bestandskunden, 10% Influencer, 5% Journalisten, 5% Konkurrenz-Fans, 20% Öffentlichkeit, 5% Analysten
- **Policy-Ankündigung:** 30% Direkt-Betroffene, 25% Öffentlichkeit, 8% Medien, 7% Politiker, 10% Industrie, 5% NGOs, 5% Akademiker, 10% Aktivisten

### Parametrische Variation (500 → 50'000)

| Parameter | Variation | Begründung |
|-----------|-----------|-----------|
| Alter | ±5 Jahre | Reicht für Lebensphasen-Shift |
| Big Five | std 0.08 | ~1σ auf 0-1 Skala, behält Archetyp |
| Opinions | std 0.10 | Etwas mehr Varianz als Persönlichkeit |
| Post-Frequenz | 20% Shift-Chance | Meiste bleiben in ihrem Band |
| Ton | 15% Shift-Chance | Relativ stabil |
| Name | Immer neu | Einzigartigkeit |
| Region | Gleich | Regionale Identität ist Kern |

### Kosten

| Phase | Calls | Kosten |
|-------|-------|--------|
| Stakeholder Discovery | 1 | ~$0.001 |
| 500 Personas (50 Batches) | 50 | ~$0.07 |
| Skalierung 500→50k | 0 | $0 (Code) |
| **Total** | **51** | **~$0.07** |

---

## Teil 21: Social Graph Generation

### Algorithmus: LFR Benchmark (networkx)

LFR erzeugt gleichzeitig Power-Law Degree Distribution UND Community-Struktur.
Verfügbar als `networkx.generators.community.LFR_benchmark_graph()`.

### Plattform-spezifische Parameter

| Parameter | Twitter-like | LinkedIn-like |
|-----------|-------------|---------------|
| tau1 (Degree-Exponent) | 2.1 | 2.7 |
| tau2 (Community-Size-Exponent) | 1.5 | 1.5 |
| mu (Mixing-Parameter) | 0.15 (starke Communities) | 0.25 (mehr Cross-Community) |
| average_degree | 8 | 12 |
| Graph-Typ | Directed (Follow) | Undirected (Connection) |

### Post-Processing

1. **Influencer-Hubs:** Top-Creator Agents bekommen extra Cross-Community-Edges
2. **Weak Ties:** 5-10% zusätzliche Edges zwischen Communities (Granovetter Bridges)
3. **Validierung:** Clustering-Koeffizient, Degree-Distribution, Average Path Length prüfen

### Performance

- 10k Nodes: ~5-30s Generation (networkx)
- 50k Nodes: networkx generiert, optional igraph für Runtime-Queries (10-100x schneller)
- Graph einmal generieren und cachen/picklen

---

## Teil 22: Performance-Optimierungen (für Skalierung)

- **Prompt Caching:** System-Prompt als statischen Prefix strukturieren (>1024 tokens für Auto-Cache). 73% cacheable → 50% Rabatt auf cached Tokens.
- **Agent-Archetype-Batching:** 20-30 Persona-Templates die Cache-Prefix teilen
- **Multi-API-Key Rotation:** Über mehrere OpenAI Keys für höhere Rate Limits
- **OpenAI Batch API:** Für nicht-realtime Simulationen 50% Rabatt (24h Turnaround)
- **Tiered Processing:** Observer-Agents brauchen minimale/keine LLM-Calls

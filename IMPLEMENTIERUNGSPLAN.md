# Implementierungsplan: Entity-basierte Persona-Pipeline

## Design-Entscheidungen (aus Grill-Session)

| # | Entscheidung | Ergebnis |
|---|---|---|
| 1 | Entity-Modell | `smart_decision.py` erweitern, nicht neu bauen |
| 2 | Entity-Types | Feste Basis-Types + dynamische Sub-Types vom LLM |
| 3 | Web Enrichment | Serper.dev von Anfang an |
| 4 | Enrichment-Tiefe | Snippets + Top-3 Seiten fetchen (10K Zeichen/Seite, 5s Timeout) |
| 5 | Persona-Mix | LLM entscheidet frei, keine festen Grenzen |
| 6 | Start-Flow | Ein Call `/quick-start`, alles ueber WebSocket streamen |
| 7 | Graph-Component | Ein Component, zwei Modi (Vorbereitung + Simulation) |
| 8 | Edge Labels | Immer auf Entity-Edges, zoom-adaptiv auf Persona-Edges |
| 9 | Document Upload | Spaeter — Freitext only, Token-Limit hochsetzen |
| 10 | Quick vs Advanced Mode | Nur Quick Mode fuer ersten Release |
| 11 | Lade-Feedback | Split-View: Graph waechst live, Pulse waehrend LLM-Calls, 200ms Stagger fuer Entities |
| 12 | Persona-Generierung | Getrennte Pipelines: Real zuerst aus Enrichment, dann Generated ueber bestehenden Generator |
| 13 | Defamation Guard | Nur Label/Badge, keine Verhaltenseinschraenkung |
| 14 | Fehlender Kontext | Gefuehrte Fragen, dynamisch vom LLM generiert |
| 15 | Seitenwechsel | Zusammenfassung + "Simulation vorbereiten" → Split-View |
| 16 | Plattform/Runden-Wahl | Rechtes Panel nach Persona-Generierung |
| 17 | Graph waehrend Simulation | Sentiment-Updates + Aktivitaets-Glow |
| 18 | Rechtes Panel Simulation | Stats-Header oben + Live-Feed unten |

---

## Phase 1: Smart Decision erweitern + Entity Relationships

**Ziel:** `smart_decision.py` wird zum zentralen Analyse-Modul. Entity-Modell bekommt Relationships und dynamische Sub-Types.

### 1.1 Entity-Modell erweitern

**Datei:** `backend/app/services/smart_decision.py`

Neue Felder auf `ExtractedEntity`:
```python
class ExtractedEntity(BaseModel):
    # Bestehende Felder bleiben:
    name: str
    entity_type: EntityType          # Feste Basis-Types (real_person, real_company, role, ...)
    importance: float
    role_in_scenario: str
    enrichment: EnrichmentDecision
    enrichment_reason: str
    persona_count: int

    # NEU:
    sub_type: str = ""               # Dynamisch vom LLM: "CEO", "Journalist", "Kunde", "Investor"
    sentiment_toward_scenario: float = 0.0  # -1 bis +1
    context_snippet: str = ""        # Textstelle wo Entity gefunden wurde
    relationships: list[EntityRelationship] = []
```

Neues Model:
```python
class EntityRelationship(BaseModel):
    target_entity_name: str          # Name der Ziel-Entity
    relation_type: str               # "leadership", "employment", "competition", "customer"
    label: str                       # "ist CEO von", "arbeitet bei", "konkurriert mit"
    strength: float = 0.5            # 0-1
```

`SimulationDecision` erweitern:
```python
class SimulationDecision(BaseModel):
    # Bestehend bleibt alles
    # NEU:
    follow_up_questions: list[str] = []  # Dynamische Fragen bei fehlendem Kontext
```

### 1.2 Prompt erweitern

**Datei:** `backend/app/services/smart_decision.py`

`DECISION_SYSTEM_PROMPT` erweitern um:
- Relationship-Extraction: "Erkenne Beziehungen zwischen Entities (CEO von, arbeitet bei, Konkurrent, Kunde)"
- Sub-Type-Vergabe: "Vergib jedem Entity einen spezifischen sub_type (z.B. 'Tech-Journalist', 'Langzeit-Kunde', 'Finanzanalyst')"
- Sentiment-Scoring: "Schaetze die Haltung jeder Entity zum Szenario (-1 bis +1)"
- Follow-up-Fragen: "Falls wichtiger Kontext fehlt, generiere 2-3 spezifische Fragen"

`DECISION_USER_PROMPT` erweitern:
- `follow_up_questions` Feld im JSON-Schema
- `relationships` Array pro Entity
- `sub_type` und `sentiment_toward_scenario` pro Entity

Few-Shot-Beispiele anpassen mit den neuen Feldern.

Token-Limit des User-Inputs von 3'000 auf 50'000 Zeichen erhoehen.

### 1.3 Tests

**Datei:** `backend/tests/test_smart_decision.py` (neu)

- Test: Entity-Extraction mit Relationships
- Test: Follow-up-Fragen werden generiert bei unvollstaendigem Input
- Test: Sub-Types werden vergeben
- Test: Sentiment-Scoring funktioniert
- Test: Fallback-Decision hat sinnvolle Defaults fuer neue Felder
- Test: Token-Limit Erhoehung funktioniert

### Abhaengigkeiten
- Keine — kann sofort starten

### Dateien
- MODIFIZIEREN: `backend/app/services/smart_decision.py`
- NEU: `backend/tests/test_smart_decision.py`

---

## Phase 2: Serper Web Enrichment Service

**Ziel:** Neuer Service der Entities ueber Serper.dev + Page-Fetching + LLM-Extraktion anreichert.

### 2.1 Config erweitern

**Datei:** `backend/app/core/config.py`

```python
# Serper
serper_api_key: str = ""
```

### 2.2 Enrichment Service

**Datei:** `backend/app/services/entity_enricher.py` (neu)

```python
class EnrichmentResult(BaseModel):
    entity_name: str
    success: bool
    verified_name: str = ""
    verified_title: str = ""
    verified_company: str = ""
    industry: str = ""
    location: str = ""
    communication_style: str = ""     # formal, casual, provokativ
    known_positions: list[str] = []   # Bekannte oeffentliche Positionen
    influence_level: str = "medium"   # high, medium, low
    recent_context: str = ""          # "Kuerzlich in den Nachrichten wegen..."
    sources: list[str] = []           # URLs der verwendeten Quellen

class EntityEnricher:
    def __init__(self, llm: LLMProvider, usage_tracker: LLMUsageTracker):
        ...

    async def enrich_entity(self, entity: ExtractedEntity, scenario_context: str) -> EnrichmentResult:
        """Pipeline pro Entity:
        1. Serper-Suche: "{entity.name} {entity.role_in_scenario}" → 10 Ergebnisse
        2. Top-3 Seiten parallel fetchen (httpx, 5s Timeout, max 10K Zeichen/Seite)
        3. LLM-Call: Snippets + Seitentext → strukturierte EnrichmentResult
        """

    async def enrich_batch(
        self,
        entities: list[ExtractedEntity],
        scenario_context: str,
        on_progress: Callable | None = None,  # Callback pro fertige Entity
        max_concurrent: int = 3,
    ) -> list[EnrichmentResult]:
        """Enriched alle Entities parallel (max 3 gleichzeitig).
        Ruft on_progress Callback pro fertiger Entity auf.
        """
```

**Serper-Integration:**
- `POST https://google.serper.dev/search`
- Header: `X-API-KEY: {serper_api_key}`
- Body: `{"q": "...", "gl": "ch", "hl": "de", "num": 10}`
- Response: `organic[].{title, snippet, link}`

**Page-Fetching:**
- `httpx.AsyncClient` mit 5s Timeout
- HTML → Text Konversion (einfaches Tag-Stripping, kein BeautifulSoup noetig)
- Max 10'000 Zeichen pro Seite
- Top 3 Seiten fetchen, bei 403/Timeout naechste nehmen (max 5 Versuche)
- User-Agent: generischer Browser-String

**LLM-Extraction-Call:**
- Input: Serper-Snippets + bis zu 3 Seiten-Texte (~30K Zeichen)
- Output: Strukturierte `EnrichmentResult`
- Temperature: 0.0 (faktische Extraktion)
- Prompt: "Extrahiere verifizierte Informationen ueber {entity_name}. Nur Fakten, keine Spekulation."

### 2.3 Fallback-Logik

- Serper-Call scheitert → Entity bleibt unangereichert, `persona_source = "role_based"`
- Alle 5 Seiten-Fetches scheitern → nur Snippets an LLM (degraded quality)
- LLM-Extraction scheitert → Entity bleibt unangereichert
- Kein Serper API Key konfiguriert → Enrichment komplett ueberspringen, loggen

### 2.4 Tests

**Datei:** `backend/tests/test_entity_enricher.py` (neu)

- Test: Serper-Response wird korrekt geparsed (Mock)
- Test: Page-Fetching mit Timeout/403 Fallback
- Test: LLM-Extraction gibt strukturiertes Ergebnis
- Test: Batch-Enrichment mit Concurrency-Limit
- Test: Fallback wenn Serper scheitert
- Test: Callback wird pro Entity aufgerufen

### Abhaengigkeiten
- Phase 1 (erweitertes Entity-Modell)

### Dateien
- MODIFIZIEREN: `backend/app/core/config.py`
- NEU: `backend/app/services/entity_enricher.py`
- NEU: `backend/tests/test_entity_enricher.py`

---

## Phase 3: Persona-Model erweitern

**Ziel:** Personas bekommen eine `persona_source` die anzeigt ob sie echt, rollenbasiert oder generiert sind.

### 3.1 Model-Erweiterung

**Datei:** `backend/app/models/persona.py`

```python
class PersonaSource(StrEnum):
    REAL_ENRICHED = "real_enriched"   # Reale Person, mit Web-Daten angereichert
    REAL_MINIMAL = "real_minimal"     # Im Dokument erwaehnt, wenig Daten
    ROLE_BASED = "role_based"         # Typische Rolle, keine echte Person
    GENERATED = "generated"           # Komplett synthetisch

# Auf Persona Model hinzufuegen:
persona_source: PersonaSource = PersonaSource.GENERATED
source_entity_name: str | None = None     # Link zur ExtractedEntity
enrichment_sources: list[str] = []        # z.B. ["web_search", "document"]
```

### 3.2 GraphNode erweitern

**Datei:** `frontend/src/lib/ws-events.ts`

```typescript
export interface GraphNode {
    // Bestehend:
    id: string
    label: string
    communityId: number
    sentiment: number
    followerCount: number
    tier: string
    role?: string
    occupation?: string

    // NEU:
    entityType?: string       // "real_person", "real_company", "role", etc.
    subType?: string          // "CEO", "Journalist", "Kunde"
    personaSource?: string    // "real_enriched", "role_based", "generated"
    isEntity?: boolean        // true fuer Entity-Nodes (vor Persona-Phase)
    importance?: number       // 0-1, fuer Node-Groesse in Entity-Phase
}

export interface GraphLink {
    source: string
    target: string
    type: string
    label?: string            // NEU: "ist CEO von", "konkurriert mit"
}
```

### 3.3 Tests

- Bestehende Persona-Tests erweitern: neue Felder haben sinnvolle Defaults
- Serialisierung/Deserialisierung der neuen Felder

### Abhaengigkeiten
- Keine (kann parallel zu Phase 1+2 starten)

### Dateien
- MODIFIZIEREN: `backend/app/models/persona.py`
- MODIFIZIEREN: `frontend/src/lib/ws-events.ts`

---

## Phase 4: Persona Generator anpassen

**Ziel:** Getrennte Pipelines fuer Real-Personas (aus Enrichment-Daten) und Generated/Role-based (bestehender Generator).

### 4.1 Real-Persona-Pipeline

**Datei:** `backend/app/simulation/personas.py`

Neue Methode:
```python
async def create_real_personas(
    self,
    entities: list[ExtractedEntity],
    enrichment_results: list[EnrichmentResult],
    scenario_context: str,
) -> list[Persona]:
    """Erstellt Personas direkt aus angereicherten Entity-Daten.

    Pro real_person Entity: 1 Persona mit:
    - Name, Titel, Firma aus EnrichmentResult
    - Big Five + PostingStyle ueber einen kleinen LLM-Call
    - persona_source = REAL_ENRICHED (oder REAL_MINIMAL wenn nicht angereichert)

    Pro real_company Entity: 3-5 assoziierte Personas (CEO, Sprecher, Mitarbeiter)
    via einen LLM-Call der die Firmen-Daten als Kontext bekommt.
    """
```

### 4.2 Generator-Integration

**Datei:** `backend/app/simulation/personas.py`

`generate()` Methode erweitern:
```python
async def generate(
    self,
    scenario: StructuredScenario,
    decision: SimulationDecision | None = None,     # NEU
    enrichment_results: list[EnrichmentResult] | None = None,  # NEU
    target_count: int = 200,
    on_progress: Callable | None = None,
    on_batch: Callable | None = None,
) -> list[Persona]:
    """
    1. Wenn decision + enrichment_results vorhanden:
       a. Real-Personas aus Enrichment-Daten erstellen (create_real_personas)
       b. on_batch Callback fuer sofortige Graph-Updates
    2. RESEARCH_PROMPT erweitern: "Es gibt bereits diese realen Personas: [...]"
    3. Restliche Personas generieren (role_based + generated) mit bestehendem Flow
    4. persona_source korrekt setzen auf allen Personas
    """
```

### 4.3 RESEARCH_PROMPT erweitern

Den bestehenden `RESEARCH_PROMPT` anpassen:
- Kontext ueber bereits existierende Real-Personas
- Anweisung: "Generiere ergaenzende Personas die zu diesem Mix passen"
- Entity-Beziehungen als Kontext: "Firma X hat CEO Y, Konkurrent Z"

### 4.4 Tests

**Datei:** `backend/tests/test_personas.py` (erweitern)

- Test: Real-Personas werden aus Enrichment-Daten erstellt
- Test: persona_source wird korrekt gesetzt
- Test: Company-Entities generieren mehrere assoziierte Personas
- Test: Generator funktioniert weiterhin ohne decision/enrichment (Rueckwaertskompatibilitaet)
- Test: Gesamtzahl stimmt (Real + Role-based + Generated = target_count)

### Abhaengigkeiten
- Phase 1 (Entity-Modell)
- Phase 2 (EnrichmentResult)
- Phase 3 (PersonaSource auf Persona)

### Dateien
- MODIFIZIEREN: `backend/app/simulation/personas.py`
- MODIFIZIEREN: `backend/tests/test_personas.py`

---

## Phase 5: Quick-Start Endpoint + WebSocket Events

**Ziel:** Ein einziger API-Call startet die gesamte Pipeline. Fortschritt wird ueber WebSocket gestreamt.

### 5.1 Neue WebSocket Events

**Datei:** `backend/app/services/simulation_service.py`

Neue Event-Typen die ueber den bestehenden `ws_broadcast` Callback gesendet werden:

```python
# Phase-Wechsel
{"type": "phase_changed", "data": {"phase": "analyzing", "detail": "Analysiere Fragestellung..."}}
{"type": "phase_changed", "data": {"phase": "extracting_entities", "detail": "Extrahiere Entitaeten..."}}
{"type": "phase_changed", "data": {"phase": "enriching", "detail": "Recherchiere Hintergrundinformationen..."}}
{"type": "phase_changed", "data": {"phase": "generating_personas", "detail": "Generiere Personas..."}}
{"type": "phase_changed", "data": {"phase": "configuring", "detail": "Bereit fuer Simulation"}}
{"type": "phase_changed", "data": {"phase": "simulating", "detail": "Simulation laeuft..."}}

# Entity-Events (mit 200ms Stagger nach LLM-Call)
{"type": "entity_extracted", "data": {"node": GraphNode, "links": GraphLink[]}}

# Enrichment-Events (echt asynchron, kommen einzeln)
{"type": "entity_enriched", "data": {"entity_name": "...", "node": GraphNode}}  # Node-Update mit reicheren Daten
{"type": "enrichment_failed", "data": {"entity_name": "...", "reason": "..."}}

# Persona-Events (bestehend, erweitert)
{"type": "persona_batch", "data": {"nodes": GraphNode[], "links": GraphLink[]}}

# Bestehende Events bleiben:
# round_complete, simulation_complete, snapshot
```

### 5.2 Quick-Start Endpoint

**Datei:** `backend/app/api/simulation.py`

```python
@router.post("/quick-start")
async def quick_start(request: QuickStartRequest, background_tasks: BackgroundTasks):
    """Ein Call fuer den gesamten Flow:
    1. Smart Decision (Analyse + Entity-Extraction)
    2. Web Enrichment (Serper + Page-Fetch + LLM)
    3. Persona Generation (Real + Generated)
    4. Simulation
    """
```

```python
class QuickStartRequest(BaseModel):
    input_text: str                    # Freitext oder beantwortete Fragen
    additional_context: str = ""       # Antworten auf Follow-up-Fragen
    platform: PlatformType | None = None  # Optional, sonst LLM-Empfehlung
    round_count: int = 50             # Vom User gewaehlt nach Persona-Generierung
```

### 5.3 Analyse-Endpoint erweitern

**Datei:** `backend/app/api/simulation.py`

Bestehender `/analyze-input` Endpoint wird erweitert:
- Nutzt jetzt `SmartDecisionEngine` statt nur `PromptBuilder`
- Response enthaelt `follow_up_questions` und `SimulationDecision`
- Frontend kann die Fragen anzeigen und Antworten sammeln

### 5.4 SimulationService erweitern

**Datei:** `backend/app/services/simulation_service.py`

`run_simulation_job()` wird erweitert fuer den neuen Flow:

```python
async def run_simulation_job(self, ...):
    # Phase 1: Smart Decision (wenn nicht schon gelaufen)
    broadcast(phase_changed: "analyzing")
    decision = await smart_decision.analyze(input_text)

    # Phase 2: Entity-Nodes im Graph anzeigen (200ms Stagger)
    broadcast(phase_changed: "extracting_entities")
    for entity in decision.entities:
        broadcast(entity_extracted: node + links)
        await asyncio.sleep(0.2)

    # Phase 3: Web Enrichment
    broadcast(phase_changed: "enriching")
    enricher = EntityEnricher(llm, usage)
    enrichment_results = await enricher.enrich_batch(
        entities=[e for e in decision.entities if e.enrichment == "enrich"],
        scenario_context=input_text,
        on_progress=lambda result: broadcast(entity_enriched/enrichment_failed)
    )

    # Phase 4: Persona Generation
    broadcast(phase_changed: "generating_personas")
    personas = await persona_gen.generate(
        scenario=scenario,
        decision=decision,
        enrichment_results=enrichment_results,
        on_batch=lambda nodes, links: broadcast(persona_batch)
    )

    # Phase 5: Warte auf User-Konfiguration (Platform + Runden)
    broadcast(phase_changed: "configuring")
    # ... User waehlt Platform + Runden im Frontend ...

    # Phase 6: Simulation
    broadcast(phase_changed: "simulating")
    # ... bestehender Engine-Flow ...
```

### 5.5 Zwei-Phasen-Start

Die Simulation hat jetzt einen Zwischenstopp nach Persona-Generierung:

1. `POST /quick-start` → startet Analyse + Enrichment + Persona-Generierung
2. Frontend zeigt Split-View mit wachsendem Graph
3. Personas fertig → Backend sendet `phase_changed: "configuring"` mit Persona-Count + empfohlener Platform
4. User waehlt Platform + Runden im rechten Panel
5. `POST /simulation/{id}/configure` → startet die eigentliche Simulation
   ```python
   class SimulationConfigRequest(BaseModel):
       platform: PlatformType
       round_count: int
   ```

### 5.6 Frontend Event-Typen

**Datei:** `frontend/src/lib/ws-events.ts`

Neue Event-Interfaces:
```typescript
interface PhaseChangedEvent {
    type: 'phase_changed'
    data: { phase: string; detail: string }
}

interface EntityExtractedEvent {
    type: 'entity_extracted'
    data: { node: GraphNode; links: GraphLink[] }
}

interface EntityEnrichedEvent {
    type: 'entity_enriched'
    data: { entity_name: string; node: GraphNode }
}

interface EnrichmentFailedEvent {
    type: 'enrichment_failed'
    data: { entity_name: string; reason: string }
}

interface PersonaBatchEvent {
    type: 'persona_batch'
    data: { nodes: GraphNode[]; links: GraphLink[] }
}
```

### 5.7 Tests

- Test: Quick-Start-Flow komplett (Mock LLM + Mock Serper)
- Test: WebSocket Events werden in richtiger Reihenfolge gesendet
- Test: Entity-Stagger hat korrektes Timing
- Test: Configure-Endpoint startet Simulation korrekt
- Test: Fallback wenn Serper-Key nicht konfiguriert

### Abhaengigkeiten
- Phase 1-4 muessen fertig sein

### Dateien
- MODIFIZIEREN: `backend/app/api/simulation.py`
- MODIFIZIEREN: `backend/app/services/simulation_service.py`
- MODIFIZIEREN: `frontend/src/lib/ws-events.ts`
- NEU: Tests

---

## Phase 6: Frontend — Split-View mit wachsendem Graph

**Ziel:** Neue Simulations-Seite mit Split-View. Links Graph, rechts Fortschritt/Konfiguration/Feed.

### 6.1 NetworkGraph erweitern

**Datei:** `frontend/src/components/simulation/NetworkGraph.tsx`

Zwei-Phasen-Rendering:

**Vorbereitungs-Phase (isEntity-Nodes):**
- Grosse Nodes, Labels immer sichtbar
- Farbe nach Entity-Type (real_person=Gruen, real_company=Blau, role=Amber, institution=Lila, media_outlet=Pink, product=Cyan, event=Orange)
- Quadratische Nodes fuer reale Entities, runde fuer rollenbasierte
- Entity-zu-Entity Edges mit Labels (immer sichtbar)
- Pulse-Animation waehrend LLM-Calls aktiv
- Wenige Nodes (5-20), uebersichtlich

**Simulations-Phase (Persona-Nodes dazu):**
- Entity-Nodes bleiben als "Kerne", schrumpfen leicht
- Persona-Nodes erscheinen drumherum (in Naehe ihrer source_entity)
- Farbe wechselt zu Sentiment-Encoding (bestehende Logik)
- Edge Labels nur beim Reinzoomen (zoom-adaptiv)
- Aktivitaets-Glow fuer aktive Agents pro Runde
- Badge-Indikator fuer persona_source (kleines Icon/Farbe am Node-Rand)

**Neuer `paintNode`:**
```
if (node.isEntity) {
    // Grosse Node, Entity-Type-Farbe, immer Label
    // Quadratisch wenn real_person/real_company, rund wenn role/etc.
} else {
    // Bestehende Logik (Sentiment-Farbe, Tier-Groesse)
    // Plus: persona_source Badge (farbiger Ring)
    // Plus: Glow wenn aktiv in aktueller Runde
}
```

**Neuer Link-Renderer:**
```
if (link.label && (link.type === 'entity_relation' || globalScale > 2.0)) {
    // Label auf die Linie zeichnen, rotiert entlang der Edge
    // Hintergrund-Rechteck fuer Lesbarkeit
}
```

**Legend Panel (unten links):**
- Entity-Type Farben + Anzahl
- Persona-Source Badges erklaert
- Umschaltet automatisch zwischen Entity-Legende und Simulations-Legende

### 6.2 useSimulationStream erweitern

**Datei:** `frontend/src/hooks/useSimulationStream.ts`

Neue Event-Handler:
```typescript
// phase_changed → State-Update fuer Phase-Anzeige
// entity_extracted → Node + Links zum Graph hinzufuegen
// entity_enriched → bestehenden Node updaten (reichere Tooltip-Daten)
// enrichment_failed → Node markieren (gestrichelt oder ausgegraut)
// persona_batch → Nodes + Links zum Graph hinzufuegen
```

Neuer State:
```typescript
currentPhase: string          // "analyzing" | "extracting_entities" | "enriching" | ...
phaseDetail: string           // Menschenlesbare Beschreibung
entityCount: number           // Anzahl extrahierter Entities
enrichedCount: number         // Anzahl angereicherter Entities
personaCount: number          // Anzahl generierter Personas
recommendedPlatform: string   // LLM-Empfehlung
isConfiguring: boolean        // true wenn User Platform/Runden waehlen soll
```

### 6.3 SimulationPage Rewrite

**Datei:** `frontend/src/pages/SimulationPage.tsx`

Neues Layout:
```
+--------------------------------------------------+
|  Phase-Indikator (oben, horizontal)               |
+------------------------+-------------------------+
|                        |                         |
|                        |   Rechtes Panel:        |
|     NetworkGraph       |   - Vorbereitungs-Feed  |
|     (wachsend)         |   - Konfigurations-UI   |
|                        |   - Stats + Live-Feed   |
|                        |                         |
+------------------------+-------------------------+
```

**Rechtes Panel — drei Zustaende:**

1. **Vorbereitung** (phase: analyzing → generating_personas):
   - Event-Feed: "Analysiere Fragestellung...", "3 Entities erkannt", "Tim Cook wird recherchiert...", "12 Personas generiert"
   - Animierte Eintraege mit Icons pro Event-Typ
   - Fortschrittsanzeige pro Phase

2. **Konfiguration** (phase: configuring):
   - Zusammenfassung: "{N} Personas generiert"
   - Empfohlene Plattform (vorausgewaehlt, aenderbar)
   - Runden-Auswahl: 10 / 25 / 50 / 100
   - "Simulation starten" Button

3. **Simulation** (phase: simulating):
   - Stats-Header oben (Runde X/Y, Sentiment-Sparkline, Post-Counter, Kosten)
   - Live-Feed darunter (Posts, Kommentare, Likes — scrollbar)
   - persona_source Badge neben jedem Post im Feed

### 6.4 Phase-Indikator

**Datei:** `frontend/src/components/simulation/PhaseTimeline.tsx` (erweitern)

Neue Phasen:
```
Analyse → Entities → Enrichment → Personas → [Konfiguration] → Simulation → Fertig
```

Jede Phase zeigt:
- Icon + Titel
- Status: wartend (grau) / aktiv (blau, pulse) / fertig (gruen)
- Kurzinfo: "3 Entities" / "5 angereichert" / "187 Personas"

### Abhaengigkeiten
- Phase 5 (WebSocket Events muessen definiert sein)

### Dateien
- MODIFIZIEREN: `frontend/src/components/simulation/NetworkGraph.tsx`
- MODIFIZIEREN: `frontend/src/hooks/useSimulationStream.ts`
- MODIFIZIEREN: `frontend/src/pages/SimulationPage.tsx`
- MODIFIZIEREN: `frontend/src/components/simulation/PhaseTimeline.tsx`
- MODIFIZIEREN: `frontend/src/components/simulation/LiveFeed.tsx` (persona_source Badge)
- MODIFIZIEREN: `frontend/src/components/simulation/StatsPanel.tsx`

---

## Phase 7: Frontend — Input-Flow (Fragestellung + Gefuehrte Fragen)

**Ziel:** Neuer Input-Flow: Fragestellung → Gefuehrte Fragen → Zusammenfassung → Split-View.

### 7.1 NewSimulationPage Rewrite

**Datei:** `frontend/src/pages/NewSimulationPage.tsx`

**Step 1: Fragestellung**
- Grosses Textfeld (min 3 Zeilen, max unbegrenzt)
- Placeholder: "Beschreibe dein Szenario oder stelle eine Frage..."
- Beispiele als klickbare Chips darunter:
  - "Wie reagiert die Oeffentlichkeit auf...?"
  - "Teste diese Marketingkampagne..."
  - "Wie kommt dieses LinkedIn-Post an?"
- "Analysieren" Button → POST `/analyze-input`

**Step 2: Gefuehrte Fragen**
- Zeigt `follow_up_questions` aus der Analyse-Response
- Pro Frage: die Frage als Label + Textfeld fuer die Antwort
- "Ueberspringen" Link pro Frage (optional)
- "Weiter" Button sammelt Antworten

**Step 3: Zusammenfassung**
- Kompakte Zusammenfassung des Szenarios (1-2 Saetze, vom LLM generiert)
- Gefundene Entities als kleine Pills/Chips (farbig nach Entity-Type)
- "[N] Entities werden recherchiert" Hinweis
- "Simulation vorbereiten" Button → POST `/quick-start` → Redirect zu SimulationPage

### 7.2 API-Integration

- Step 1 → `POST /analyze-input` (bestehend, erweitert mit SmartDecision)
- Step 2 → kein API-Call, nur Frontend-State
- Step 3 → `POST /quick-start` mit `input_text` + `additional_context` (Antworten auf Fragen)

### Abhaengigkeiten
- Phase 5 (quick-start Endpoint)

### Dateien
- MODIFIZIEREN: `frontend/src/pages/NewSimulationPage.tsx`

---

## Implementierungs-Reihenfolge

```
Woche 1:
  Phase 1: Smart Decision erweitern (Entity Relationships, Sub-Types, Follow-up Questions)
  Phase 3: Persona-Model erweitern (PersonaSource, GraphNode-Felder) [parallel]

Woche 2:
  Phase 2: Serper Web Enrichment Service
  Phase 4: Persona Generator anpassen (Real-Pipeline + Integration)

Woche 3:
  Phase 5: Quick-Start Endpoint + WebSocket Events

Woche 4:
  Phase 6: Frontend Split-View mit wachsendem Graph
  Phase 7: Frontend Input-Flow [parallel]
```

### Commit-Strategie

Feature Branch: `feat/entity-pipeline`

Commits nach jedem Teilschritt:
- `feat: extend smart decision with entity relationships and follow-up questions`
- `feat: add persona source field to persona model`
- `feat: add serper web enrichment service`
- `feat: entity-aware persona generation pipeline`
- `feat: quick-start endpoint with websocket streaming`
- `feat: split-view graph with entity visualization`
- `feat: guided question input flow`

### Tests vor jedem Commit

```bash
cd backend && uv run pytest
cd backend && uv run ruff check .
```

### Kosten pro Simulation (nach Implementierung)

| Schritt | LLM Calls | Web Searches | Page Fetches | Kosten |
|---------|-----------|--------------|-------------|--------|
| Smart Decision | 1 | 0 | 0 | ~$0.002 |
| Web Enrichment (10 Entities) | 10 | 10 | 30 | ~$0.02 |
| Real Personas (~10) | 2-3 | 0 | 0 | ~$0.005 |
| Generated Personas (~190) | 1 Research + 20 Batch | 0 | 0 | ~$0.07 |
| Simulation (200 Agents, 50 Runden) | ~15'000 | 0 | 0 | ~$3.50 |
| **Total** | | | | **~$3.60** |

Entity-Pipeline fuegt ~$0.03 zu den bestehenden Kosten hinzu.

# Swaarm — Überarbeitungsplan: Entity-basierte Persona-Pipeline

## Zusammenfassung

Komplette Überarbeitung der Persona-Generierung und des Input-Flows. Statt generischer Personas aus einem Freitext werden jetzt **Entitäten aus Dokumenten extrahiert**, echte Personen via **Web-Suche angereichert**, und eine **Mischung aus echten + rollenbasierten + generierten Personas** erstellt.

**Kern-Änderung:** Von "LLM erfindet Personas" zu "LLM extrahiert reale Entitäten + generiert kontextspezifische Personas drum herum".

---

## Phase 1: Document Upload & Text Extraction

### Was gebaut werden muss

**Backend:**
- Neuer Endpoint `POST /api/simulation/upload` — akzeptiert PDF, DOCX, TXT, MD
- `backend/app/services/document_parser.py` — Text-Extraktion aus verschiedenen Formaten
- PDF: `pymupdf4llm` (Markdown-Output, optimiert für LLMs)
- DOCX: `python-docx` (bereits installiert)
- TXT/MD: direkt lesen
- Max. Dateigrösse: 10 MB
- MIME-Type Validierung server-seitig
- Keine persistente Speicherung — in-memory verarbeiten, danach verwerfen

**Frontend:**
- `frontend/src/components/simulation/DocumentUpload.tsx` — Drag-and-Drop Zone
- Library: `react-dropzone` (3KB, zero deps)
- Tab-Toggle in `NewSimulationPage.tsx`: "Freitext" | "Dokument hochladen"
- Upload-Progress, Dateiname-Anzeige, Fehlerhandling

**Dependencies hinzufügen:**
- Backend: `pymupdf4llm>=0.0.17` in pyproject.toml
- Frontend: `npm install react-dropzone`

### Wie es funktioniert
1. User zieht PDF in die Drop-Zone oder klickt "Datei auswählen"
2. Frontend sendet File an `/api/simulation/upload`
3. Backend extrahiert Text, gibt ihn zurück
4. Text wird in den bestehenden `inputText` State gesetzt
5. Ab hier: gleicher Flow wie bei Freitext (→ Analyse)

### Token-Limit
- Aktuell: `analyze_input()` truncated auf 2'000 Zeichen (viel zu wenig für Dokumente)
- Ändern auf: 50'000 Zeichen (~15'000 Tokens, passt in GPT-4o-mini's 128K Kontext)
- Für Dokumente >50'000 Zeichen: Chunking mit 20'000 Zeichen Chunks, 2'000 Overlap

---

## Phase 2: Entity Extraction Pipeline

### Was gebaut werden muss

**Backend:**
- `backend/app/services/entity_extractor.py` — neue Klasse `EntityExtractor`
- `backend/app/models/entity.py` — Pydantic Models für extrahierte Entitäten

### Entity-Modelle (Pydantic)

```python
class EntityType(StrEnum):
    PERSON = "person"
    COMPANY = "company"
    ORGANIZATION = "organization"
    PRODUCT = "product"
    EVENT = "event"
    LOCATION = "location"

class PublicFigureSignal(StrEnum):
    NAMED_EXECUTIVE = "named_executive"
    POLITICIAN = "politician"
    MEDIA_PERSONALITY = "media_personality"
    NONE = "none"

class ExtractedEntity(BaseModel):
    id: str
    name: str
    type: EntityType
    role_description: str  # "CEO von toxic.fm"
    sentiment_toward_scenario: float  # -1 bis +1
    public_figure_signal: PublicFigureSignal
    needs_web_enrichment: bool
    confidence: float  # 0-1
    context_snippet: str  # Textstelle wo Entity gefunden wurde
    relationships: list[EntityRelationship]

class EntityRelationship(BaseModel):
    target_id: str
    relation_type: str  # "leadership", "employment", "competition"
    label: str  # "ist CEO von", "arbeitet bei"
    strength: float  # 0-1

class ScenarioClassification(BaseModel):
    involves_public_figures: bool
    involves_specific_companies: bool
    scenario_type: str  # corporate_crisis, product_launch, etc.
    controversity_estimate: float

class DocumentExtractionResult(BaseModel):
    reasoning: str
    entities: list[ExtractedEntity]
    classification: ScenarioClassification
    key_topics: list[str]
    missing_context: list[str]
```

### Extraction Prompt

Ein einzelner LLM-Call (GPT-4o-mini, temperature=0.0, structured output) der:
1. Alle Entitäten aus dem Dokument extrahiert
2. Beziehungen zwischen Entitäten erkennt
3. Für jede Entität entscheidet: braucht diese Web-Enrichment?
4. Das Szenario klassifiziert (Typ, Kontroversität)
5. Fehlende Informationen identifiziert

**Entscheidungslogik für Web-Enrichment:**
- Person MIT vollem Namen UND konkreter Position → `needs_web_enrichment = true`
- Bekannte Organisation/Firma → `needs_web_enrichment = true` (für Kontext)
- Nur Rolle ohne Namen ("der CEO", "Kunden") → `needs_web_enrichment = false`
- Abstrakte Konzepte → `needs_web_enrichment = false`

**Kosten:** ~$0.002 pro Extraction (2'000 Input + 3'000 Output Tokens)

### Integration mit bestehendem Code

- `PromptBuilder.analyze_input()` wird erweitert um auch Entities zu extrahieren
- ODER: neuer `EntityExtractor` der nach `analyze_input()` läuft
- Empfehlung: **Kombinierter Call** — ein Prompt der Szenario-Analyse UND Entity-Extraktion macht
- Dafür `ANALYSIS_PROMPT` erweitern und `StructuredScenario` um `entities: list[ExtractedEntity]` ergänzen

---

## Phase 3: Web Enrichment Service

### Was gebaut werden muss

**Backend:**
- `backend/app/services/entity_enricher.py` — Web-Suche + LLM-Extraktion

### Web Search API

**Empfehlung: Serper.dev** ($1/1000 Queries, 2'500 Free)
- Google-Ergebnisse, schnell (1-2s), JSON API
- Alternative: Tavily (besser für RAG, aber 5-8x teurer)

### Pipeline pro Entity

```
1. Web-Suche: "{entity_name} {context}" → 5 Google-Ergebnisse
2. LLM-Call: Ergebnisse → strukturierte Persona-Daten extrahieren
3. Rückgabe: Name, Titel, Firma, Branche, Kommunikationsstil, bekannte Positionen
```

### Was extrahiert wird

**Pro realer Person:**
- Verifizierter Name, Titel, Firma
- Branche, Standort
- Kommunikationsstil (formal, casual, provokativ)
- Bekannte öffentliche Positionen zu relevanten Themen
- Einfluss-Level (hoch/mittel/niedrig)
- Kurzer aktueller Kontext ("kürzlich in den Nachrichten wegen...")

**Pro realer Firma:**
- Branche, Grösse, Standort
- Kernprodukte/-dienstleistungen
- Aktuelle Nachrichten/Kontroversen
- Öffentliche Reputation

### Kosten
- Serper: $0.001 pro Suche
- LLM-Extraktion: $0.0005 pro Entity
- Total für 10 Entities: ~$0.015

### Fallback wenn Suche scheitert
- Confidence < 0.5 → Persona wird "role_based" statt "real"
- Person nicht gefunden → generischer Name + Rolle behalten
- Kein Internet → komplett überspringen, nur generierte Personas

### Privacy & GDPR
- NUR öffentlich verfügbare Daten verwenden
- Persona als "inspiriert von" labeln, nicht "ist"
- Keine LinkedIn-Profile scrapen (ToS-Verletzung)
- Rohe Suchergebnisse sofort verwerfen, nur extrahierte Daten behalten
- Hinweistext im UI: "Basierend auf öffentlich verfügbaren Informationen"

---

## Phase 4: Persona-Kategorisierung (Echt vs. Fiktiv)

### Vier-Stufen-System

| Kategorie | Label (DE) | Badge | Farbe | Beschreibung |
|-----------|-----------|-------|-------|------------|
| `real_enriched` | Reale Person (angereichert) | **REAL** | Blau #2563EB | Namentlich, mit Web-Daten |
| `real_minimal` | Reale Person (Basisdaten) | **REAL** | Hellblau #60A5FA | Im Dokument genannt, wenig Daten |
| `role_based` | Rollenbasiert | **ROLLE** | Amber #F59E0B | Typische Rolle, keine echte Person |
| `generated` | Generiert | **GEN** | Grau #9CA3AF | Komplett synthetisch |

### Persona-Model Erweiterung

```python
# In persona.py hinzufügen:
class PersonaSource(StrEnum):
    REAL_ENRICHED = "real_enriched"
    REAL_MINIMAL = "real_minimal"
    ROLE_BASED = "role_based"
    GENERATED = "generated"

# Auf Persona Model:
persona_source: PersonaSource = PersonaSource.GENERATED
source_entity_id: str | None = None  # Link zur ExtractedEntity
enrichment_sources: list[str] = []  # z.B. ["web_search", "document"]
```

### Verhaltensunterschiede in der Simulation

- **Real Enriched:** Prompt enthält "Du simulierst [Name]. Nur Meinungen äussern die zu bekannten öffentlichen Positionen passen."
- **Real Minimal:** Prompt enthält "Du weisst dass [Name] [Position] bei [Firma] ist. Darüber hinaus keine spezifischen Meinungen erfinden."
- **Role Based:** Volle kreative Freiheit innerhalb der Rolle
- **Generated:** Volle kreative Freiheit innerhalb der demografischen Parameter

### UI-Darstellung

- Persona-Karten mit farbigem Badge und Rahmen
- Im Live-Feed: Badge neben jedem Post/Kommentar
- Disclaimer-Banner: "Diese Simulation enthält X reale und Y generierte Personas. Alle Reaktionen sind KI-generiert."
- Defamation-Guard: Posts von "real" Personas mit starkem Sentiment werden mit ⚠ markiert

---

## Phase 5: Neuer Input Flow (Frontend)

### Quick Mode (Standard)
```
Eingabe (Text/Datei) → [auto] Analyse → [auto] Enrichment → Konfiguration → Start
```
User sieht nur: Eingabe → Loading (3-5s) → Parameterauswahl → Start

### Advanced Mode
```
Eingabe → Analyse → Entity-Review → Enrichment → Persona-Preview → Konfiguration → Start
```
User sieht alle Schritte mit voller Kontrolle

### Neue Frontend-Komponenten

| Datei | Was |
|-------|-----|
| `DocumentUpload.tsx` | Drag-and-Drop File Upload |
| `StepIndicator.tsx` | Horizontaler Fortschrittsbalken |
| `EntityReview.tsx` | Entity-Liste mit Mini-Graph |
| `EntityCard.tsx` | Einzelne Entity als Pill/Chip |
| `PersonaPreview.tsx` | Persona-Mix Balken + Karten |
| `PersonaCard.tsx` | Einzelne Persona-Vorschau |

### API-Endpoints (erweitert)

| Endpoint | Methode | Was |
|----------|---------|-----|
| `/api/simulation/upload` | POST | Datei hochladen, Text extrahieren |
| `/api/simulation/analyze` | POST | Szenario + Entities extrahieren (kombiniert) |
| `/api/simulation/enrich-entities` | POST | Web-Enrichment (SSE streaming) |
| `/api/simulation/generate-personas` | POST | Persona-Mix generieren (SSE streaming) |
| `/api/simulation/start` | POST | Simulation starten (bestehend, erweitert) |
| `/api/simulation/quick-start` | POST | Quick Mode: alles in einem Call |

---

## Phase 6: Persona Generator Überarbeitung

### Aktuelle Probleme
1. Personas werden rein aus Freitext generiert — kein Dokumentkontext
2. Keine echten Personen — alles ist fiktiv
3. Keine Entity-Beziehungen fliessen in den Graph ein

### Neue Pipeline

```
Document/Freitext
  → Entity Extraction (1 LLM Call)
    → Für jede Entity mit needs_web_enrichment=true:
      → Web Search (Serper, $0.001)
      → LLM Extraction (strukturierte Daten, $0.0005)
    → Smart Decision: Persona-Mix berechnen
      → ~10% Real (aus angereicherten Entities)
      → ~20% Role-based (aus Entity-Kontext)
      → ~70% Generated (aus DACH-Demografie)
    → PersonaGenerator.generate() mit Entity-Daten als Seed
```

### Code-Änderungen in personas.py

1. `generate()` akzeptiert optional `entities: list[ExtractedEntity]`
2. Für Entities mit `type=person` + `enriched=true`: erzeugt "real_enriched" Persona
3. Für Entities mit `type=company`: erzeugt 3-5 assoziierte Personas (CEO, Sprecher, Mitarbeiter)
4. `RESEARCH_PROMPT` wird erweitert: "Berücksichtige folgende reale Entitäten: ..."
5. Rest wird wie bisher mit parametrischer Variation aufgefüllt

---

## Phase 7: LinkedIn CSV Import (Späterer Ausbau)

### Flow
1. User exportiert Connections aus LinkedIn (Settings → Data Privacy → Get a copy)
2. Upload der `Connections.csv` in Swaarm
3. Parsing: First Name, Last Name, Company, Position → Personas
4. Seniority-Inferenz via Keyword-Matching (CEO→C_LEVEL, Senior→SENIOR, etc.)
5. Keine Web-Suche nötig — CSV-Daten reichen für realistische Personas

### Kosten: $0 (kein LLM, kein Web Search, reines CSV-Parsing)

### Privacy: User lädt seine eigenen exportierten Daten hoch, keine fremden Profile

---

## Phase 8: Graph-Visualisierung verbessern

### Von MiroFish lernen

1. **Entity-Type Farben** statt nur Sentiment-Farben
   - Mitarbeiter=Blau, Kunde=Grün, Journalist=Lila, Investor=Amber, etc.
   - Dreifach-Encoding: Fill=Rolle, Border=Sentiment, Size=Einfluss

2. **Entity Type Legend** Panel (unten links im Graph)
   - Farbige Punkte + Rollenname + Anzahl

3. **Edge Labels** toggle (wie MiroFish "Show Edge Labels")
   - Beziehungstypen an den Kanten: "CEO von", "Konkurrent", "Kunde"

4. **Real vs. Generated** visuell unterscheiden
   - Real: Quadratische Nodes
   - Generated: Runde Nodes
   - Oder: Real mit solidem Rahmen, Generated mit gestricheltem

5. **Persona Workbench** bei Klick auf Node
   - Voller Persona-Steckbrief: Name, Rolle, Big Five, Meinungen, Posts

---

## Dateien — Übersicht aller Änderungen

### Neue Dateien

| Datei | Zweck |
|-------|-------|
| `backend/app/models/entity.py` | Entity + Relationship Pydantic Models |
| `backend/app/services/document_parser.py` | PDF/DOCX/TXT Text-Extraktion |
| `backend/app/services/entity_extractor.py` | Entity Extraction via LLM |
| `backend/app/services/entity_enricher.py` | Web Search + Enrichment |
| `backend/app/services/smart_decision.py` | Entscheidungslogik: was für Personas brauchen wir? |
| `frontend/src/components/simulation/DocumentUpload.tsx` | File Upload UI |
| `frontend/src/components/simulation/StepIndicator.tsx` | Fortschrittsbalken |
| `frontend/src/components/simulation/EntityReview.tsx` | Entity-Review UI |
| `frontend/src/components/simulation/PersonaPreview.tsx` | Persona-Mix Preview |

### Zu modifizierende Dateien

| Datei | Änderung |
|-------|----------|
| `backend/app/services/prompt_builder.py` | ANALYSIS_PROMPT erweitern für Entity-Extraktion |
| `backend/app/simulation/personas.py` | Entity-basierte Persona-Generierung |
| `backend/app/models/persona.py` | `persona_source`, `source_entity_id` hinzufügen |
| `backend/app/api/simulation.py` | Neue Endpoints (upload, enrich, quick-start) |
| `backend/app/services/simulation_service.py` | Entity-Pipeline integrieren |
| `backend/app/core/config.py` | Serper API Key Config |
| `backend/pyproject.toml` | pymupdf4llm Dependency |
| `frontend/src/pages/NewSimulationPage.tsx` | Kompletter Rewrite mit Multi-Step Flow |
| `frontend/src/components/simulation/NetworkGraph.tsx` | Entity-Type Farben, Labels |
| `frontend/src/lib/ws-events.ts` | `stakeholderRole`, `isReal` auf GraphNode |
| `frontend/package.json` | react-dropzone |

---

## Kosten pro Simulation (mit neuer Pipeline)

| Schritt | LLM Calls | Web Searches | Kosten |
|---------|-----------|--------------|--------|
| Text-Extraktion | 0 | 0 | $0 |
| Entity Extraction | 1 | 0 | $0.002 |
| Web Enrichment (10 Entities) | 10 | 10 | $0.015 |
| Persona Generation (200) | 1 Research + 20 Batch | 0 | $0.07 |
| Simulation (200 Agents, 50 Runden) | ~15'000 | 0 | $3.50 |
| Report | 1 | 0 | $0.002 |
| **Total** | | | **~$3.59** |

Die Entity-Pipeline fügt nur **~$0.017** zu den bestehenden Kosten hinzu — vernachlässigbar.

---

## Implementierungs-Reihenfolge

| Priorität | Phase | Aufwand |
|-----------|-------|---------|
| 1 | Phase 2: Entity Extraction (Backend) | 2 Tage |
| 2 | Phase 4: Persona-Kategorisierung | 1 Tag |
| 3 | Phase 6: Persona Generator Überarbeitung | 2 Tage |
| 4 | Phase 1: Document Upload | 1 Tag |
| 5 | Phase 3: Web Enrichment | 2 Tage |
| 6 | Phase 5: Frontend Input Flow | 3 Tage |
| 7 | Phase 8: Graph-Visualisierung | 2 Tage |
| 8 | Phase 7: LinkedIn CSV Import | 1 Tag |
| **Total** | | **~14 Tage** |

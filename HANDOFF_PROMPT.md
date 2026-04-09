# Handoff Prompt für neuen Claude Code Chat

Kopiere diesen gesamten Text in einen neuen Claude Code Chat:

---

## Kontext

Du arbeitest am Projekt **Swaarm** — einer SaaS-Plattform die mit KI-Agenten simuliert, wie die Öffentlichkeit auf Unternehmenskommunikation reagiert. Das Projekt ist bereits funktional (187 Tests, 11 Issues abgeschlossen), aber die Persona-Generierung und der Input-Flow müssen grundlegend überarbeitet werden.

## Deine Aufgabe

Implementiere die **Entity-basierte Persona-Pipeline** gemäss dem Überarbeitungsplan in `UEBERARBEITUNGSPLAN.md`. Das ist eine grosse Überarbeitung die mehrere Tage dauert. Arbeite Schritt für Schritt, committe nach jedem grösseren Teilschritt, und teste alles.

## Lies zuerst diese Dateien (in dieser Reihenfolge)

1. `UEBERARBEITUNGSPLAN.md` — der ausführliche Plan was gebaut werden muss
2. `CLAUDE.md` — Architektur-Regeln und Code-Standards
3. `progress.md` — was bisher gebaut wurde
4. `PRD.md` — das Product Requirements Document
5. `docs/SIMULATION_ENGINE_BLUEPRINT.md` — technischer Bauplan der Engine

## Was sich ändern muss (Zusammenfassung)

### Backend (Python + FastAPI)

1. **Document Upload** (`backend/app/services/document_parser.py` — NEU):
   - PDF-Extraktion mit `pymupdf4llm`, DOCX mit `python-docx`
   - Neuer API Endpoint `POST /api/simulation/upload`
   - Dependency hinzufügen: `pymupdf4llm` in pyproject.toml

2. **Entity Extraction** (`backend/app/services/entity_extractor.py` — NEU):
   - Neues Pydantic Model `backend/app/models/entity.py` mit ExtractedEntity, EntityRelationship, ScenarioClassification
   - LLM-basierte Extraktion aller Personen, Firmen, Beziehungen aus Dokumenttext
   - Entscheidungslogik: braucht eine Entity Web-Enrichment? (public_figure_signal)
   - Structured Output (Pydantic response_format), temperature=0.0

3. **Web Enrichment** (`backend/app/services/entity_enricher.py` — NEU):
   - Web-Suche via Serper.dev API (oder Tavily als Alternative)
   - Pro Entity: 1 Web-Suche + 1 LLM-Call zur Datenextraktion
   - Config: `SERPER_API_KEY` in Settings + .env
   - Fallback: wenn Suche scheitert, Persona wird "role_based" statt "real"

4. **Persona-Kategorisierung** (persona.py MODIFIZIEREN):
   - Neues Feld `persona_source: PersonaSource` (real_enriched / real_minimal / role_based / generated)
   - Neues Feld `source_entity_id: str | None`
   - Neues Feld `enrichment_sources: list[str]`

5. **Persona Generator** (personas.py MODIFIZIEREN):
   - `generate()` akzeptiert optional `entities: list[ExtractedEntity]`
   - Real Entities → "real_enriched" Personas mit eingeschränktem Verhalten
   - Company Entities → mehrere assoziierte Personas (CEO, Sprecher, Mitarbeiter)
   - RESEARCH_PROMPT erweitern: reale Entities als Seed-Daten einbeziehen

6. **Prompt Builder** (prompt_builder.py MODIFIZIEREN):
   - ANALYSIS_PROMPT erweitern um auch Entities zu extrahieren
   - Token-Limit von 2'000 auf 50'000 Zeichen erhöhen
   - StructuredScenario um `entities` Feld erweitern

7. **API Endpoints** (simulation.py MODIFIZIEREN):
   - `POST /api/simulation/upload` — Dokument hochladen
   - `POST /api/simulation/enrich-entities` — Web Enrichment (optional SSE streaming)
   - Bestehende Endpoints erweitern für Entity-Daten

### Frontend (React + TypeScript)

8. **Document Upload** (`DocumentUpload.tsx` — NEU):
   - `react-dropzone` für Drag-and-Drop
   - Akzeptiert PDF, DOCX, TXT, MD
   - Dependency: `npm install react-dropzone`

9. **NewSimulationPage** (REWRITE):
   - Quick Mode: Eingabe → Loading → Konfiguration → Start
   - Advanced Mode: Eingabe → Entity-Review → Enrichment → Persona-Preview → Start
   - Tab-Toggle: "Freitext" | "Dokument hochladen"

10. **Graph-Visualisierung** (NetworkGraph.tsx MODIFIZIEREN):
    - Entity-Type Farben (Mitarbeiter=Blau, Kunde=Grün, Journalist=Lila etc.)
    - Dreifach-Encoding: Fill=Rolle, Border=Sentiment, Size=Einfluss
    - Legend Panel unten links
    - Real vs. Generated visuell unterscheiden (quadratisch vs. rund)

## Architektur-Regeln (WICHTIG)

- Provider-agnostisch: LLM-Calls über Adapter-Interface
- Pydantic everywhere: Alle Datenmodelle als Pydantic Models
- Async-first: Alle IO-Operationen async
- Deutsche UI: Alle User-facing Strings auf Deutsch
- Code/Comments auf Englisch
- Tests: Verhalten testen, nicht Implementierung
- Deep Modules: Wenige Module mit einfachen Interfaces
- Commits: Konventionelle Commit Messages (feat:, fix:, refactor:)
- Feature Branches: Für jedes grössere Feature einen Branch, dann merge in main
- Immer testen (pytest) und linten (ruff) vor jedem Commit

## Reihenfolge der Implementierung

1. **Phase 2: Entity Extraction** (Backend Models + Service) — starte hier
2. **Phase 4: Persona-Kategorisierung** (Model-Erweiterung)
3. **Phase 6: Persona Generator** (Überarbeitung mit Entity-Input)
4. **Phase 1: Document Upload** (Backend + Frontend)
5. **Phase 3: Web Enrichment** (Service + API)
6. **Phase 5: Frontend Input Flow** (NewSimulationPage Rewrite)
7. **Phase 8: Graph-Visualisierung** (Entity-Type Farben)

## Kontext aus der Recherche

### MiroFish (Referenz-Implementierung)
- 4-Stufen Pipeline: Text → Ontology → Knowledge Graph → OASIS Profiles
- Nutzt 10 Entity-Types (8 dynamisch + Person + Organization als Fallback)
- Graph-Visualisierung: D3.js force-directed, 10-Farben-Palette, Entity Type Legend
- Persona-Format: 2000-Zeichen `persona` Feld + kurzes `bio`

### Graphiti (Open-Source Knowledge Graph Engine)
- Entity Extraction: 1 LLM Call pro Text-Chunk
- Entity Deduplication: 3-stufig (exact match → MinHash/LSH → LLM)
- Relationship Extraction: Separater LLM Call
- Für Swaarm: Vereinfachte Version reicht (1 kombinierter LLM Call)

### Web Enrichment
- Serper.dev: $0.001/Query, 2'500 Free, Google-Ergebnisse
- Pro Entity: Web-Suche + LLM-Extraktion = ~$0.0015
- Total für 10 Entities: ~$0.015 (vernachlässigbar)

### Persona Labeling
- 4 Kategorien: real_enriched, real_minimal, role_based, generated
- EU AI Act Art. 50: KI-generierte Inhalte müssen gekennzeichnet werden
- Defamation Guard: Posts von "real" Personas mit starkem Sentiment markieren

## Status des bestehenden Codes

- 187 Tests, 0 Lint-Fehler
- Backend: FastAPI + Python 3.12 + Pydantic + asyncio + networkx + SQLite
- Frontend: React 19 + Vite + Tailwind CSS + TypeScript
- Supabase: Auth + PostgreSQL
- LLM: GPT-4o-mini (via provider-agnostischem Adapter)
- Simulation Engine: 12-Schritt-Pipeline mit Willingness Scoring, Memory, etc.
- Beide Plattformen: Öffentlich (Twitter) + Professionell (LinkedIn)

## WICHTIG

- Lies `UEBERARBEITUNGSPLAN.md` KOMPLETT bevor du anfängst zu coden
- Frage mich wenn etwas unklar ist
- Committe nach jedem grösseren Teilschritt (Feature Branch)
- Teste alles (pytest + ruff check)
- Dokumentiere was du gebaut hast in progress.md und docs/ENGINE_STEPS_ERKLAERT.md
- Pushe erst wenn ich sage

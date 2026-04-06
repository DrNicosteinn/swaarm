# Swaarm — Verbesserungspotenzial & Technische Schulden

Dieses Dokument hält fest was während des Bauens aufgefallen ist und später verbessert werden sollte.

## Priorität 1 (vor Launch)

### Szenario-Injektion in Simulation
**Problem:** Live-Test zeigte dass Posts zu generisch sind und sich nicht auf das eingegebene Szenario beziehen.
**Lösung:** Der Prompt Builder (Issue #6) muss "Seed Posts" ins Szenario injizieren — z.B. ein offizielles Statement das als erster Post erscheint, damit Agents darauf reagieren.
**Betrifft:** `engine.py`, `create_and_run_simulation()`

### DB Connection Pooling
**Problem:** Jede Methode in `SimulationDB` öffnet eine neue `aiosqlite.connect()`. Bei 50k Agents × 50 Runden sind das tausende Connection Open/Close Zyklen.
**Lösung:** Persistent Connection pro Simulation-Instanz oder Connection Pool (single writer + reader pool).
**Betrifft:** `database.py`

### datetime.utcnow() Deprecation
**Problem:** 49 Deprecation Warnings bei Tests: `datetime.datetime.utcnow()` ist deprecated in Python 3.12.
**Lösung:** Ersetze `datetime.utcnow()` mit `datetime.now(datetime.UTC)` in Pydantic Model defaults.
**Betrifft:** `simulation.py` (SimulationResult.created_at default)

### Content-Längenbegrenzung
**Problem:** `insert_post()` hat kein Limit auf `content` — ein fehlerhafter LLM-Response könnte Megabytes in SQLite schreiben.
**Lösung:** Content auf max 5000 Zeichen truncaten in `execute_action()`.
**Betrifft:** `platforms/public.py`

## Priorität 2 (nach Launch)

### Sentiment-Analyse Integration
**Problem:** Sentiment-Werte werden aktuell nicht aus den generierten Posts berechnet — sie stehen immer auf 0.0.
**Lösung:** Sentiment vom LLM mit jeder Action mitliefern lassen (via zusätzliches Feld in der Tool-Response), oder nachträglich per Batch analysieren.
**Betrifft:** `engine.py`, `platforms/public.py`, Action-Schema

### HealthMonitor Integration in Engine
**Problem:** `HealthMonitor` und `CheckpointManager` sind gebaut aber noch nicht in die Simulation Engine integriert.
**Lösung:** In `_run_round()` den HealthMonitor aufrufen, Checkpoints alle N Runden speichern.
**Betrifft:** `engine.py`

### Persona-Konsistenz-Metrik
**Problem:** `QualityMetrics.persona_consistency` ist auf 0.0 gesetzt — kein Consistency-Check implementiert.
**Lösung:** Stichprobenartig (5-10 Agents) einen LLM-Call machen der prüft ob die Posts zur Persona passen.
**Betrifft:** `metrics.py`

### Clustering-Koeffizient-Metrik
**Problem:** `QualityMetrics.clustering_coefficient` ist auf 0.0 gesetzt.
**Lösung:** Nach Simulation `nx.average_clustering()` auf dem finalen Graph berechnen.
**Betrifft:** `metrics.py`, `graph.py`

### Topic-Relevanz für Willingness Scoring
**Problem:** `topic_relevance` und `network_activity` werden als Default-Werte (0.5/0.3) übergeben, nicht dynamisch berechnet.
**Lösung:** Pro Runde die tatsächliche Topic-Relevanz berechnen (Cosine Similarity Agent-Interessen vs. aktuelle Posts).
**Betrifft:** `engine.py`, `willingness.py`

## Priorität 3 (Optimierungen)

### Prompt Caching Maximierung
**Aktuell:** System-Prompts sind ~400-600 Tokens. OpenAI cached ab 1024 Tokens.
**Verbesserung:** System-Prompts auf >1024 Tokens erweitern (mehr Persona-Details, Beispiele) für automatisches Caching.

### Agent-Archetype Batching
**Aktuell:** Jeder Agent hat einen individuellen System-Prompt.
**Verbesserung:** 20-30 Persona-Templates die den gleichen Cache-Prefix teilen. Variationen nur im User-Prompt.

### Batch-Insert für Actions
**Aktuell:** Jede Action wird einzeln in DB geschrieben.
**Verbesserung:** Alle Actions einer Runde als Batch-Insert (`executemany`).

### Memory Summary mit Batch-LLM
**Aktuell:** Memory-Summarization für jeden Agent einzeln.
**Verbesserung:** Batch-Summarization: 10-20 Agent-Memories in einem LLM-Call zusammenfassen.

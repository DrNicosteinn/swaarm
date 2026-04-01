# SwarmSight AI - Working Notes

## Kritische technische Erkenntnisse

### OASIS Integration (aus MiroFish-Analyse)
- Package: `camel-oasis==0.2.5` + `camel-ai==0.2.78`
- Install via `uv sync` (pyproject.toml)
- Imports: `from oasis import ActionType, LLMAction, ManualAction, generate_twitter_agent_graph`
- Core Flow: `generate_agent_graph()` -> `oasis.make(agent_graph, platform, db_path)` -> `env.reset()` -> `env.step(actions)` loop -> `env.close()`
- Output: `actions.jsonl` (eine Aktion pro Zeile) + SQLite DB
- Env Vars: `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL_NAME`, `ZEP_API_KEY`
- Twitter Actions: CREATE_POST, LIKE_POST, REPOST, FOLLOW, DO_NOTHING, QUOTE_POST
- Reddit Actions: LIKE_POST, DISLIKE_POST, CREATE_POST, CREATE_COMMENT, LIKE_COMMENT, DISLIKE_COMMENT, SEARCH_POSTS, etc.
- Semaphore default: 30 concurrent LLM calls
- Profile Format: CSV (Twitter), JSON (Reddit)

### MiroFish Pipeline (5 Stufen)
1. Ontology Generation (LLM -> JSON schema mit Entity/Edge types)
2. Graph Construction (Text chunks -> Zep Cloud -> Knowledge Graph)
3. Entity -> Agent Profile Generation (Graph entities -> OASIS profiles)
4. Simulation (OASIS subprocess, parallel Twitter+Reddit)
5. Report Generation (ReACT pattern, search tools against graph)

### MiroFish Frontend
- Vue 3 + Vite + Vue Router + Axios + D3.js
- KEIN State Management (Vuex/Pinia) - alles lokaler Component State
- Polling-basiert (kein WebSocket), 2s intervals
- 5-Step Wizard UI
- Split-View: Graph links, Workbench rechts
- ~20 API Endpoints

### Kosten pro Simulation
- 200 Agents x 50 Rounds = 10'000 LLM Calls
- GPT-4o-mini: $1.95/Run (Batch: $0.98)
- Gemini Flash: $1.30/Run
- Mit Prompt Caching: 40-60% weniger

### Artificial Societies (NICHT direkte Konkurrenz)
- Macht KEINE Runden-basierte Simulation
- Einmaliger Durchlauf durch Social-Graph-Modell (~30 Sek)
- Output: Scores + 10 Varianten, KEIN sichtbarer Feed
- Kein zeitlicher Verlauf, keine emergenten Narrative
- Unser Differenzierungsmerkmal: echte Multi-Round Social-Media-Simulation

## Offene Fragen
- [ ] OASIS lokal zum Laufen bringen und testen
- [ ] Zep Cloud Free Tier Limits verifizieren
- [ ] LLM Provider fuer DACH evaluieren (Latenz, Kosten)
- [ ] DACH-spezifische Persona-Templates erstellen

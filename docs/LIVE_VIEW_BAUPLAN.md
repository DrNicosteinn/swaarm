# Issue #8: Live-View — Detaillierter Bauplan

## Zusammenfassung der Recherche

### MiroFish als Referenz
MiroFish zeigt während der Simulation **nur einen scrollenden Feed** — KEINEN Live-Netzwerk-Graph. Der Knowledge Graph wird nur in der Vorbereitungsphase angezeigt. Das ist eine grosse Differenzierungs-Chance für Swaarm: wir zeigen beides gleichzeitig.

### Library-Entscheidung

| Library | Renderer | Max Nodes (flüssig) | Empfehlung |
|---------|----------|---------------------|------------|
| D3.js raw (SVG) | SVG | ~300 | Zu langsam |
| react-force-graph-2d | Canvas | ~5'000 | **Unsere Wahl** |
| Sigma.js | WebGL | ~50'000 | Overkill, später wenn nötig |

**Entscheidung: `react-force-graph-2d`** — Canvas-basiert, d3-force Physik, React-native, handles 1000+ Nodes flüssig. Simples API, built-in Zoom/Pan/Drag.

### WebSocket-Strategie

- **FastAPI native WebSocket** (kein Socket.IO — unnötiger Overhead)
- **JWT Auth via Query-Parameter** (`ws://host/ws/sim/123?token=JWT`)
- **Events per Runde gebatcht** (nicht pro Aktion)
- **ConnectionManager** mit per-Client Queue + Backpressure
- **React Hook** mit Auto-Reconnect + Exponential Backoff

---

## Architektur

```
┌─────────────────────────────────────────────────────────────┐
│ Frontend (React)                                             │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │  NetworkGraph     │  │  LiveFeed         │                │
│  │  (react-force-    │  │  (scrollende      │                │
│  │   graph-2d)       │  │   Post-Liste)     │                │
│  │                   │  │                   │                │
│  │  Nodes = Agents   │  │  Posts kommen     │                │
│  │  Edges = Follows  │  │  in Echtzeit      │                │
│  │  Farbe = Sentiment│  │  rein             │                │
│  └──────────────────┘  └──────────────────┘                 │
│                                                              │
│  ┌──────────────────────────────────────────┐               │
│  │  MetricsBar                               │               │
│  │  Runde 23/50 | 45% | Sentiment ████░ |    │               │
│  │  Kosten: $0.02 | 142 aktive Agents        │               │
│  └──────────────────────────────────────────┘               │
│                          ↕ WebSocket                         │
└──────────────────────────┼──────────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────────┐
│ Backend (FastAPI)        │                                   │
│                          │                                   │
│  ┌───────────────────────▼──────────────────┐               │
│  │  WebSocket Endpoint                       │               │
│  │  /ws/simulation/{id}?token=JWT            │               │
│  │                                           │               │
│  │  ConnectionManager (per-Client Queue)     │               │
│  └───────────────────────▲──────────────────┘               │
│                          │                                   │
│  ┌───────────────────────┴──────────────────┐               │
│  │  Simulation Engine                        │               │
│  │  event_callback → broadcast per Runde     │               │
│  └──────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementierungs-Schritte

### Schritt 1: Backend WebSocket (ConnectionManager + Endpoint)

**Dateien:**
- `backend/app/services/ws_manager.py` — ConnectionManager Singleton
- `backend/app/api/ws.py` — WebSocket Endpoint

**ConnectionManager:**
- Dict von `simulation_id → Set[ConnectedClient]`
- Jeder Client hat eine `asyncio.Queue(maxsize=256)`
- Background Task pro Client draint die Queue und sendet via WebSocket
- Wenn Queue voll (langsamer Client): älteste Message droppen
- Send Timeout: 5 Sekunden, danach Client disconnecten

**WebSocket Endpoint:**
- JWT Auth via `?token=` Query Parameter (validate vor `accept()`)
- Bei Connect: Client in ConnectionManager registrieren
- Bei Disconnect: Client entfernen
- Ping/Pong Keepalive (30s Intervall)

### Schritt 2: Event-Format definieren

**Event-Typen:**
- `simulation_started` — Simulation beginnt (total_rounds, agent_count)
- `round_completed` — Runde fertig (alle Actions dieser Runde, Metriken)
- `metrics_update` — Sentiment-Verteilung, Engagement, Top-Topics
- `simulation_completed` — Simulation beendet (Summary)
- `state_snapshot` — Kompletter Zustand (für Late-Joiner / Reconnect)
- `error` — Fehler aufgetreten

**Batching:** Alle Events einer Runde werden in EINER Message gesendet. Kein Event pro Action — das wäre zu viel Traffic.

### Schritt 3: Engine ↔ WebSocket verbinden

Die Simulation Engine hat bereits einen `event_callback`. Wir verbinden ihn mit dem ConnectionManager:

```python
async def on_simulation_event(event):
    await ws_manager.broadcast(simulation_id, event.model_dump_json())
```

### Schritt 4: Frontend — Netzwerk-Graph

**Library:** `react-force-graph-2d`
**Rendering:** Canvas (nicht SVG)

**Graph-Daten:**
- Nodes: `{ id, label, communityId, sentiment, sentimentColor, followerCount }`
- Links: `{ source, target, type (follow/like/comment) }`

**Features:**
- Nodes erscheinen mit Animation (scale from 0)
- Farbe = Sentiment (rot negativ, grün positiv, grau neutral)
- Grösse = Follower-Count (Influencer sind grösser)
- Community-Clustering via `forceX/forceY` mit vorberechneten Community-Zentren
- Hover: Tooltip mit Persona-Info
- Click: Details-Panel

**Performance-Tricks:**
- `requestAnimationFrame`-Batching: WebSocket-Events werden gesammelt und pro Frame angewendet
- Farb-Transitionen: Interpolation über mehrere Frames (smooth, nicht abrupt)
- Warm Start: Bei Reconnect sendet Backend Snapshot mit aktuellen Node-Positionen

### Schritt 5: Frontend — Live-Feed

**Einfache scrollende Liste:**
- Neue Posts/Kommentare erscheinen oben
- Auto-Scroll (kann pausiert werden)
- Jeder Post zeigt: Agent-Name, Inhalt, Engagement-Zahlen
- Sentiment-Farbe am Rand
- Max 100 Posts im DOM (ältere werden entfernt)

### Schritt 6: Frontend — Metrics Bar

**Am oberen Rand:**
- Fortschritt: "Runde 23 von 50" + Progress Bar
- Geschätzte Restzeit
- Sentiment-Verteilung als Mini-Bar (rot/grau/grün)
- Aktive Agents diese Runde
- Bisherige Kosten

### Schritt 7: Frontend — SimulationPage (alles zusammen)

**Route:** `/simulation/:id`

**Layout:** Split-View
- Links: NetworkGraph (60% Breite)
- Rechts oben: LiveFeed (40% Breite, 70% Höhe)
- Rechts unten: MetricsPanel (40% Breite, 30% Höhe)
- Oben: Toolbar mit Rundenzähler

### Schritt 8: Tests

**Backend:**
- ConnectionManager: connect, disconnect, broadcast, slow client handling
- WebSocket Endpoint: Auth, message delivery

**Frontend:**
- useSimulationStream Hook: connect, reconnect, event parsing
- Graph-Komponente: Node-Rendering, Event-Processing

---

## Dependencies zu installieren

**Backend:** Keine neuen (FastAPI WebSocket ist built-in)

**Frontend:**
```bash
npm install react-force-graph-2d d3-force d3-interpolate
npm install -D @types/d3-force @types/d3-interpolate
```

---

## Geschätzter Aufwand

| Schritt | Aufwand |
|---------|---------|
| 1. WebSocket Backend | 0.5 Tage |
| 2. Event-Format | 0.5 Tage |
| 3. Engine-Integration | 0.5 Tage |
| 4. Netzwerk-Graph | 1.5 Tage |
| 5. Live-Feed | 0.5 Tage |
| 6. Metrics Bar | 0.5 Tage |
| 7. SimulationPage | 0.5 Tage |
| 8. Tests | 0.5 Tage |
| **Total** | **~5 Tage** |

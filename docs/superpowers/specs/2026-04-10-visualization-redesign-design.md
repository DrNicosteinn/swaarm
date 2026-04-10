# Live-Simulation-Visualisierung — Redesign Spec

**Datum:** 2026-04-10
**Status:** Design genehmigt
**Autor:** Brainstorming-Session Nico + Claude

## Problem-Statement

Die aktuelle Live-Simulation-Visualisierung (`NetworkGraph.tsx` + `SimulationPage.tsx`) hat mehrere signifikante Schwächen:

1. **Kein Überblick beim Zoom-Out** — 200+ Personas werden zu unleserlichen Punkten ohne Struktur
2. **Entities gehen im Pool unter** — Novartis-Entity wird visuell gleich behandelt wie Personas
3. **Keine Edge-Labels auf Persona-Verbindungen** — man sieht Linien aber nicht was sie bedeuten
4. **Schlechte Navigation** — keine Mini-Map, keine Suche, kein Filter, kein Fit-to-Content
5. **Personas schweben lose** — keine visuelle Gruppenzugehörigkeit zu ihrer Source-Entity
6. **Unlebendig** — keine Aktivitäts-Anzeige während der Simulation läuft
7. **Dark-Theme wirkt "underground"** — soll professioneller werden

## Ziele

**Primär (Option A):** Netzwerk-Struktur verstehen. "Wer ist in der Simulation, wie gehören sie zusammen?"
**Sekundär (Option C):** Einzelne Personas per Klick erkunden — maximale Details.

Der Graph ist eine **Stakeholder-Karte mit Live-Update**, kein Aktivitäts-Dashboard. Die Aktivität wird im rechten Feed-Panel primär kommuniziert, auf dem Graph nur sekundär angedeutet.

## Scope

**In Scope:**
- Kompletter Rewrite von `NetworkGraph.tsx` (Canvas → SVG + D3-Force)
- Update von `SimulationPage.tsx` (Layout, Detail-Panel, Navigation-Controls)
- Neue Komponenten: `Minimap`, `GraphControls`, `PersonaDetailPanel`, `SearchBox`, `EntityLegend`
- Light-Theme Migration für Simulation-Views (NewSimulationPage, SimulationPage)
- Aktivitäts-Animationen (Pulse, Ripple, Sentiment-Flow)

**Out of Scope:**
- Theme-Migration von Login/Register/Dashboard (separate Migration)
- Backend-Änderungen (WebSocket-Events bleiben identisch)
- Persona-Generierungs-Logik (bleibt wie ist)

---

## Teil 1 — Technologie

### Canvas → SVG via D3-Force

**Wechsel von `react-force-graph-2d` (Canvas) zu custom D3-Force + SVG + React.**

**Begründung:**
- CSS-Animationen (Pulse, Ripple) trivial in SVG
- Label-Backgrounds als `<rect>` + `<text>` Paare einfach
- Filter, Gradients, Masks, drop-shadow nativ
- React rendert SVG-Elemente → individuelle Updates ohne Full-Repaint
- Performance bis ~500 Nodes ausreichend

**Implementierung:**
- `d3-force` für Layout-Simulation
- Reines React für DOM-Rendering (kein D3 `select`/`append`)
- Custom Hook `useForceGraph(nodes, links, config)` kapselt Simulation
- ~500 Zeilen Custom-Code statt Library-Zwänge

**Abhängigkeiten:**
```json
{
  "d3-force": "^3.0.0",
  "d3-polygon": "^3.0.1",
  "d3-shape": "^3.2.0",
  "d3-zoom": "^3.0.0",
  "d3-selection": "^3.0.0"
}
```

Entfernt: `react-force-graph-2d`.

---

## Teil 2 — Visual Design

### Canvas & Theme

**Hintergrund:** `#FAFAFA` + MiroFish Dot-Grid:
```css
background-image: radial-gradient(#D0D0D0 1.5px, transparent 1.5px);
background-size: 24px 24px;
```

### Farb-Palette

**Entity-Typen:**

| Type | Farbe | Hex |
|---|---|---|
| real_person | Emerald | `#059669` |
| real_company | Indigo | `#4F46E5` |
| role | Amber | `#D97706` |
| institution | Violet | `#7C3AED` |
| media_outlet | Pink | `#DB2777` |
| product | Cyan | `#0891B2` |
| event | Orange | `#EA580C` |

**Sentiment (Personas):**

| Sentiment | Farbe | Hex |
|---|---|---|
| >0.3 (sehr positiv) | `#10B981` |
| 0.1 bis 0.3 | `#6EE7B7` |
| -0.1 bis 0.1 | `#CBD5E1` |
| -0.3 bis -0.1 | `#FCA5A5` |
| <-0.3 (sehr negativ) | `#EF4444` |

**Akzent (Hover/Active):** `#E91E63` (MiroFish-Pink)

### Layout — Entity-Orbital mit Skelett

**Layer 1 — Entity-Skelett (fest positioniert):**

Entities werden NICHT durch Force-Simulation positioniert, sondern durch ein deterministisches geometrisches Layout:

- 1 Entity: Zentrum
- 2 Entities: Horizontal, `[-200, 0]` und `[+200, 0]`
- 3 Entities: Gleichseitiges Dreieck, radius `220`
- 4 Entities: Quadrat, radius `240`
- 5-7 Entities: Regelmässiges Polygon, radius `260-280`
- 8+ Entities: Zwei konzentrische Ringe (wichtigere innen)

Wichtigkeit wird durch `entity.importance` bestimmt — wichtigere Entities bekommen zentralere Positionen.

**Layer 2 — Persona-Orbits:**

Pro Entity wird ein `d3.forceRadial` aufgesetzt:
```javascript
forceRadial(
  radius = 80 + Math.sqrt(personaCount) * 10,
  cx = entity.x,
  cy = entity.y,
).strength(0.5)
```

**Force-Konfiguration:**
```javascript
simulation
  .force("link", forceLink(personaToEntityEdges).strength(0.8).distance(d => d.radius))
  .force("radial", forceRadial(...))  // pro Entity
  .force("collide", forceCollide(12))
  .force("charge", forceManyBody().strength(-80))
```

Keine `forceCenter` (Entities sind schon fest). Keine `forceX/Y` (radial übernimmt das).

### Cluster-Hüllen (Convex Hulls)

Pro Entity wird eine "weiche Hülle" um ihre Persona-Gruppe gezeichnet:

```javascript
const points = personas.map(p => [p.x, p.y])
const hull = d3.polygonHull(points)
// Expand hull by 20px for padding
// Render as path with curveCatmullRomClosed for smooth curves
```

SVG:
```jsx
<path
  d={smoothHullPath}
  fill={entity.color}
  fillOpacity={0.08}
  stroke={entity.color}
  strokeOpacity={0.2}
  strokeWidth={1}
/>
```

### Node-Rendering

**Entities:**

```jsx
{entity.entityType === 'real_person' || entity.entityType === 'real_company' ? (
  // Diamond
  <rect
    x={-12} y={-12} width={24} height={24}
    fill={entityColor}
    stroke="white" strokeWidth={2}
    transform={`rotate(45) scale(${importanceScale})`}
    filter="url(#entity-shadow)"
  />
) : (
  // Circle
  <circle
    r={16 * importanceScale}
    fill={entityColor}
    stroke="white" strokeWidth={2}
    filter="url(#entity-shadow)"
  />
)}

<text
  y={28} textAnchor="middle"
  fontSize={13} fontWeight={600}
  fill="#1E293B"
>{entity.name}</text>

<text
  y={42} textAnchor="middle"
  fontSize={10} fill="#64748B"
>{entity.subType}</text>
```

Filter-Definition:
```xml
<filter id="entity-shadow">
  <feDropShadow dx="0" dy="2" stdDeviation="4" floodOpacity="0.12"/>
</filter>
```

**Personas:**

```jsx
<g className={isActive ? 'pulse-active' : ''}>
  {isActive && <circle r={radius + 4} fill={color} opacity={0.3} className="ripple"/>}
  <circle
    r={tierRadius[tier]}  // 7/5/4/3
    fill={sentimentColor}
    stroke="white" strokeWidth={1.5}
  />
  {personaSource !== 'generated' && (
    <circle
      cx={5} cy={-5} r={2}
      fill={sourceColor}  // green/amber/slate
      stroke="white" strokeWidth={0.5}
    />
  )}
</g>
```

**CSS:**
```css
@keyframes pulse-active {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.3); }
}
.pulse-active { animation: pulse-active 1.2s ease-in-out infinite; }

@keyframes ripple {
  0% { r: var(--base-r); opacity: 0.4; }
  100% { r: calc(var(--base-r) * 3); opacity: 0; }
}
.ripple { animation: ripple 1.5s ease-out infinite; }
```

### Edge-Rendering

**Persona → Entity (Orbit-Edges):**
```jsx
<line x1={p.x} y1={p.y} x2={e.x} y2={e.y}
  stroke="#CBD5E1" strokeWidth={0.8} strokeOpacity={0.5}/>
```
Keine Labels.

**Entity → Entity (Relationship-Edges):**
```jsx
<path d={bezierPath} fill="none"
  stroke={sourceEntityColor} strokeWidth={2.5} strokeOpacity={0.7}/>
{label && (
  <g transform={`translate(${midX},${midY})`}>
    <rect x={-labelWidth/2} y={-9} width={labelWidth} height={18}
      fill="white" stroke="#E5E7EB" rx={3}/>
    <text textAnchor="middle" dy={4} fontSize={11} fontWeight={500} fill="#475569">
      {label}
    </text>
  </g>
)}
```

**Multi-Edge Curvature:**
- Wenn mehrere Edges zwischen gleichem Paar (source, target), werden Kurven ausgefächert
- Formel (aus MiroFish): `curvature = ((i / (total - 1)) - 0.5) * curvatureRange * 2`
- Direction Normalization via Node-ID-Compare verhindert Flipping

**Persona → Persona (aus Orchestrator):**
```jsx
<line x1={p1.x} y1={p1.y} x2={p2.x} y2={p2.y}
  stroke="#94A3B8" strokeWidth={1.2} strokeOpacity={0.6}/>
```
Label nur bei `zoom >= 2` oder Hover.

### Semantic Zoom

**Zoom-Schwellen und Rendering:**

| Zoom | Modus | Was sichtbar ist |
|---|---|---|
| `< 0.6` | **Aggregated** | Nur Entity-Blasen mit Counts + Sentiment-Bar |
| `0.6 - 1.5` | **Structure** | Entities voll, Personas als Punkte, Cluster-Hulls |
| `1.5 - 2.5` | **Detail** | Entity + Power-Creator Labels, Entity-Edge-Labels |
| `≥ 2.5` | **Full** | Alle Persona-Labels, Sub-Types, Persona-Edge-Labels |

**Aggregated View** ersetzt jede Persona-Gruppe durch eine Blase:

```jsx
<g transform={`translate(${entity.x},${entity.y})`}>
  <circle
    r={20 + Math.sqrt(personaCount) * 8}
    fill={entityColor}
    fillOpacity={0.15}
    stroke={entityColor}
    strokeWidth={2}
  />
  <circle r={18} fill={entityColor} stroke="white" strokeWidth={2}/>
  <text textAnchor="middle" dy={6} fontSize={16} fontWeight={700} fill="white">
    {personaCount}
  </text>
  <text y={40} textAnchor="middle" fontSize={12} fontWeight={600} fill="#1E293B">
    {entity.name}
  </text>
  {/* Sentiment Mini-Bar */}
  <g transform="translate(-24, 48)">
    <rect width={48} height={4} rx={2} fill="#E5E7EB"/>
    <rect width={avgSentimentWidth} height={4} rx={2} fill={sentimentColor}/>
  </g>
</g>
```

Übergänge zwischen Modi sind mit CSS-Transitions animiert (`opacity 0.3s`, `r 0.3s`).

---

## Teil 3 — Interaktion

### Navigation-Controls (fixiert am Viewport)

**Oben rechts:** Zoom-Button-Gruppe (80px breit)
```jsx
<div className="absolute top-4 right-4 flex flex-col gap-1 bg-white rounded-lg shadow-sm border border-gray-200">
  <button title="Vergrössern">+</button>
  <button title="Verkleinern">−</button>
  <button title="Alles anzeigen">⛶</button>
  <button title="Zurücksetzen">↻</button>
</div>
```

**Oben links:** Suchfeld
```jsx
<div className="absolute top-4 left-4 w-80">
  <input
    placeholder="Persona oder Entity suchen..."
    className="w-full px-4 py-2 bg-white border border-gray-200 rounded-full shadow-sm"
  />
  {/* Dropdown mit Ergebnissen */}
</div>
```

Suche durchläuft alle Nodes, matched auf `name` und `occupation`. Bei Treffer: Fokussieren + Zoom zum Node + Highlight in Pink.

**Unten links:** Entity-Legende mit Filter
```jsx
<div className="absolute bottom-4 left-4 bg-white rounded-lg shadow-sm border border-gray-200 p-3">
  <div className="text-xs font-bold text-pink-600 uppercase tracking-wide mb-2">
    ENTITIES
  </div>
  <div className="flex flex-wrap gap-2 max-w-xs">
    {entityTypes.map(type => (
      <button
        className={cn("flex items-center gap-1.5 text-xs", filtered[type] && "opacity-30")}
        onClick={() => toggleFilter(type)}
      >
        <div className="w-3 h-3 rounded-full" style={{backgroundColor: typeColors[type]}}/>
        {typeLabels[type]}
        <span className="text-slate-400">{counts[type]}</span>
      </button>
    ))}
  </div>
</div>
```

**Unten rechts:** Mini-Map
```jsx
<div className="absolute bottom-4 right-4 w-48 h-32 bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
  <svg viewBox={fullGraphBounds}>
    {/* Mini-Rendering: Entities als Punkte, keine Personas */}
    {entities.map(e => <circle key={e.id} cx={e.x} cy={e.y} r={3} fill={e.color}/>)}
    {/* Roter Ausschnitts-Rahmen */}
    <rect
      x={viewport.x} y={viewport.y} width={viewport.w} height={viewport.h}
      fill="none" stroke="#E91E63" strokeWidth={2}
    />
  </svg>
</div>
```

Mini-Map ist klick-/drag-bar → Ausschnitt im Haupt-Graph wird synchron bewegt.

### Fokus-Modus (Hover)

Beim Hover über einen Node:
- Alle Nicht-verbundenen Nodes: `opacity: 0.15`
- Hovered Node + direkte Nachbarn: voll sichtbar
- Verbindungen vom Hovered Node: gehighlightet in Pink
- Labels auf den verbundenen Edges werden sichtbar (auch wenn normalerweise ausgeblendet)

Mouse leave → alles zurück.

### Click-Interaktionen

**Klick auf Persona/Entity:**
- Öffnet das linke Detail-Panel (slide-in von links, 320px breit)
- Graph-Bereich schrumpft, Right-Panel bleibt unverändert
- Node bekommt Pink-Ring als Selection-Indicator
- Alle verbundenen Edges werden leicht hervorgehoben

**Klick auf leeren Canvas:**
- Schliesst Detail-Panel
- Entfernt Selection-Highlights

**Klick auf Entity-Entity-Edge:**
- Zeigt kleines Popup mit Beziehungs-Details (Typ, Stärke, Beschreibung)

### Detail-Panel (Side-Panel von links)

**Struktur:**
```
┌─────────────────────────────┐
│ [Avatar] Name               │
│          Role · Entity      │
│          [REAL Badge]       │
├─────────────────────────────┤
│ STIMMUNG                    │
│ ━━━━━━━━━━━▓▓▓▓▓▓▓            │ (Sentiment-Bar)
├─────────────────────────────┤
│ BIO                         │
│ 2-3 Zeilen Text...          │
├─────────────────────────────┤
│ BEZIEHUNGEN                 │
│ ┌─────────────────────────┐ │
│ │  Mini-Network-Graph     │ │ (Ego-Netzwerk)
│ │  mit 1-hop Nachbarn     │ │
│ └─────────────────────────┘ │
├─────────────────────────────┤
│ LETZTE POSTS                │
│ "Der Abbau ist..."          │
│ "Wir werden die..."         │
├─────────────────────────────┤
│ PERSONALITY                 │
│ Openness:        ▓▓▓▓▓░░░░░ │
│ Conscientious:   ▓▓▓▓▓▓▓░░░ │
│ Extraversion:    ▓▓▓░░░░░░░ │
│ Agreeableness:   ▓▓▓▓▓░░░░░ │
│ Neuroticism:     ▓▓░░░░░░░░ │
└─────────────────────────────┘
```

Enthält:
- Avatar (Initialen-Circle oder echtes Bild bei real_enriched)
- Name + Rolle + Source-Badge (REAL/ROLE/GEN)
- Sentiment-Bar
- Bio-Text
- **Mini-Beziehungs-Graph** (1-hop Ego-Network)
- Letzte Posts (aus Simulation)
- Big Five Bars
- Persona-Quelle (bei real_enriched: Quellen-URLs als Links)

Scrollbar wenn Content überläuft. Close-Button (×) oben rechts.

### Aktivitäts-Visualisierung

**Während der Simulation:**

1. **Pulse auf aktiven Personas:** Wenn Persona X in Runde N postet/kommentiert/liked, bekommt der Node 1.2s Pulse-Animation (`scale 1.0 → 1.3 → 1.0`).

2. **Ripple-Effekt bei Sentiment-Änderung:** Wenn Sentiment eines Nodes um mehr als 0.2 wechselt, wird ein 1.5s Ripple-Ring in der neuen Sentiment-Farbe ausgesendet.

3. **Entity Sentiment-Bar:** Jede Entity hat eine Mini-Bar unter ihrem Label die den durchschnittlichen Sentiment ihrer Persona-Gruppe zeigt. Animiert bei Änderungen.

4. **Cluster-Hull Atmung:** Die Convex Hulls "atmen" leicht (opacity 0.06 → 0.12 → 0.06) im 3s-Rhythmus während Simulation läuft. Stoppt nach Abschluss.

5. **Kein Chaos:** KEINE temporären Aktivitäts-Edges (Option C wurde verworfen — zu unübersichtlich).

### Tastatur-Shortcuts

- `Cmd/Ctrl + F` — Fokus ins Suchfeld
- `Esc` — Detail-Panel schliessen, Selection entfernen
- `F` — Fit to Content
- `+` / `−` — Zoom in/out
- `Space` (halten) — Pan-Modus

---

## Teil 4 — Architektur

### Komponenten-Struktur

**Neue Dateien:**

```
frontend/src/
├── components/simulation/graph/
│   ├── NetworkGraph.tsx           (Haupt-Component, replaced old)
│   ├── hooks/
│   │   └── useForceGraph.ts       (Custom D3-Force Hook)
│   ├── layers/
│   │   ├── ClusterHulls.tsx       (Convex Hulls pro Entity)
│   │   ├── EdgesLayer.tsx         (alle Edges + Labels)
│   │   ├── NodesLayer.tsx         (alle Nodes)
│   │   └── ActivityLayer.tsx      (Pulse + Ripple Overlays)
│   ├── controls/
│   │   ├── GraphControls.tsx      (Zoom-Buttons)
│   │   ├── MiniMap.tsx            (Übersichtskarte)
│   │   ├── SearchBox.tsx          (Suchfeld)
│   │   └── EntityLegend.tsx       (Legende mit Filter)
│   ├── panel/
│   │   └── PersonaDetailPanel.tsx (Side-Panel links)
│   └── utils/
│       ├── skeletonLayout.ts      (Entity-Skelett-Positionen)
│       ├── convexHull.ts          (Hull-Berechnung)
│       └── colors.ts              (Farb-Paletten)
```

**Modifiziert:**
```
frontend/src/pages/SimulationPage.tsx   (Layout mit Detail-Panel-Integration)
frontend/src/hooks/useSimulationStream.ts  (unchanged — Events bleiben gleich)
frontend/src/lib/ws-events.ts              (unchanged)
```

**Entfernt:**
- `react-force-graph-2d` dependency
- Alter `NetworkGraph.tsx` (Canvas-Version)

### State-Management

**In `NetworkGraph.tsx`:**
```typescript
const {
  nodes, links,            // aus useSimulationStream
  zoom, transform,         // D3 zoom state
  selectedNode,            // für Detail-Panel
  hoveredNode,             // für Fokus-Modus
  filters,                 // entity type filters
  searchQuery,             // search state
  activeNodeIds,           // für Pulse-Animationen
} = useGraphState()
```

**Force-Simulation läuft in `useForceGraph` Hook:**
```typescript
function useForceGraph(nodes, links, { width, height }) {
  const simulationRef = useRef<Simulation>()
  const [positionedNodes, setPositionedNodes] = useState(nodes)

  useEffect(() => {
    // Separate entities from personas
    const entities = nodes.filter(n => n.isEntity)
    const personas = nodes.filter(n => !n.isEntity)

    // Fix entity positions using skeleton layout
    const entityPositions = computeSkeletonLayout(entities, width, height)
    entities.forEach((e, i) => {
      e.fx = entityPositions[i].x
      e.fy = entityPositions[i].y
    })

    // Run force simulation on personas only
    const simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).strength(0.8).distance(d => d.distance || 60))
      .force("radial", ...)  // per-entity radial forces
      .force("collide", d3.forceCollide(12))
      .force("charge", d3.forceManyBody().strength(-80))
      .on("tick", () => setPositionedNodes([...nodes]))

    return () => simulation.stop()
  }, [nodes, links, width, height])

  return { positionedNodes }
}
```

### Data Flow

```
WebSocket Event
      ↓
useSimulationStream (existing)
      ↓
NetworkGraph receives {nodes, links}
      ↓
useForceGraph runs force simulation
      ↓
Rendered Layers (Hulls → Edges → Nodes → Activity)
      ↓
User interactions update local state
      ↓
Re-render with new selection/filter/zoom
```

WebSocket-Events bleiben IDENTISCH zum Status quo — keine Backend-Änderungen nötig.

### Migration-Strategie

**Schrittweise, nicht Big-Bang:**

1. **Commit 1:** D3 dependencies + Farb-Paletten + Utils (keine visuelle Änderung)
2. **Commit 2:** Skeleton Layout + neue `NetworkGraph.tsx` mit Entities nur (Personas kommen rein aber ohne Hülle/Semantic Zoom)
3. **Commit 3:** Persona-Orbits + Cluster-Hulls
4. **Commit 4:** Semantic Zoom mit Aggregated View
5. **Commit 5:** Edge-Labels + Multi-Edge Curvature
6. **Commit 6:** Navigation-Controls (Zoom-Buttons, Fit, Reset)
7. **Commit 7:** Mini-Map
8. **Commit 8:** SearchBox + Filter + Entity-Legende
9. **Commit 9:** Fokus-Modus (Hover-Highlighting)
10. **Commit 10:** PersonaDetailPanel (Side-Panel)
11. **Commit 11:** Aktivitäts-Animationen (Pulse, Ripple, Sentiment-Bar)
12. **Commit 12:** Light-Theme Migration für Simulation-Views
13. **Commit 13:** Cleanup — alter Code entfernen

Zwischen jedem Commit läuft der Build und die Basis-Funktionalität bleibt erhalten. Kein Feature-Flag nötig.

### Testing

**Unit-Tests (Vitest):**
- `skeletonLayout.ts` — geometrische Positionen für 1-10 Entities
- `convexHull.ts` — Hull-Berechnung für verschiedene Punkt-Wolken
- `colors.ts` — Sentiment → Farbe Mapping

**Component-Tests (Vitest + RTL):**
- `SearchBox` — Eingabe matched korrekte Nodes
- `EntityLegend` — Filter toggled korrekt
- `PersonaDetailPanel` — rendert alle Persona-Felder korrekt

**Integration-Tests (manuell im Browser):**
- Kompletter Flow: Input → Analyse → Entity-Phase → Persona-Phase → Simulation läuft
- Interaktionen: Hover-Fokus, Click-Detail, Search, Filter, Zoom
- Performance: 200 Personas flüssig (>30fps)

**Visual Regression (optional später):**
- Playwright Screenshots pro Zoom-Level

### Performance-Considerations

- `useForceGraph` Hook verwendet `useRef` für Simulation (keine Re-Creation)
- Simulation-Ticks setzen State via `setPositionedNodes([...nodes])` — aber React-Reconciler sollte unchanged nodes nicht re-rendern
- Edges und Nodes als separate Components mit `React.memo`
- Labels werden per CSS display-none ausgeblendet (nicht unmounted) um Re-Render zu vermeiden
- Bei >300 Nodes: optional `willChange: transform` CSS-Hint

### Error Handling

- Wenn WebSocket disconnected: Graph zeigt bestehende Nodes, Controls bleiben funktional
- Wenn nodes Array leer: Centered Loading-Spinner mit Text "Warte auf Daten..."
- Wenn Force-Simulation failed: Fallback auf statisches Grid-Layout

---

## Out-of-Scope Entscheidungen (Future Work)

- **Rechtsklick-Kontextmenü** — Power-User-Feature, später
- **Node-Pinning via Drag** — später
- **Temporäre Aktivitäts-Edges** — verworfen (zu unübersichtlich)
- **Modal-Detail-View** — verworfen (Side-Panel ist besser)
- **Light-Theme für Login/Dashboard** — separates Migration-Projekt
- **Keyboard-Navigation** (Tab durch Nodes) — Accessibility, später

## Annahmen

- Browser mit moderner SVG + CSS Support (alle Chromium + Firefox + Safari aktuelle Versionen)
- WebSocket-Infrastruktur funktioniert (bestehend)
- Backend liefert Entity/Persona-Daten im bestehenden Format
- Max ~300 gleichzeitige Personas (realistischer Use-Case)

## Entscheidungen-Log

| # | Frage | Entscheidung |
|---|---|---|
| 1 | Primärer Job des Graphs | A (Netzwerk verstehen) + sekundär C (Details per Klick) |
| 2 | Layout-Struktur | B (Entity-Orbital mit forceRadial + Convex Hulls) |
| 3 | Zoom-Verhalten / LOD | B (Semantic Zoom mit Entity-Blasen) |
| 4 | Detail-Panel-Style | A (Side-Panel von links) |
| 5 | Navigation-Features | Zoom-Buttons + Mini-Map + Suche + Filter + Fokus-Modus |
| 6 | Live-Aktivität | B (Pulse + Sentiment-Flow + Ripple) |
| 7 | Farb-Theme | Light, professionell (wie MiroFish) |
| Tech | Canvas vs SVG | SVG + D3-Force (Custom Hook) |

# Live-Simulation-Visualisierung Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Kompletter Rewrite der Live-Simulation-Visualisierung mit SVG+D3-Force, Entity-Orbital-Layout, Semantic Zoom und Light-Theme.

**Architecture:** Canvas → SVG + D3-Force (custom React Hook). Entities fest positioniert via geometrischem Skelett, Personas orbitieren via `forceRadial`, Convex Hulls zeigen Gruppen. Semantic Zoom mit 4 Stufen. Side-Panel für Details, Mini-Map + Suche + Filter + Fokus-Modus für Navigation. Pulse/Ripple-Animationen für Live-Aktivität. Light-Theme `#FAFAFA` mit Dot-Grid.

**Tech Stack:** React 19, TypeScript, Vite, Tailwind v4, d3-force v3, d3-polygon, d3-shape, d3-zoom, d3-selection, Vitest + @testing-library/react.

**Related Spec:** `docs/superpowers/specs/2026-04-10-visualization-redesign-design.md`

---

## File Structure

### Neue Dateien

```
frontend/
├── vitest.config.ts                                    (NEU - test config)
└── src/
    ├── components/simulation/graph/
    │   ├── NetworkGraph.tsx                            (NEU - replaces old Canvas version)
    │   ├── types.ts                                    (NEU - graph-specific types)
    │   ├── hooks/
    │   │   ├── useForceGraph.ts                        (NEU - D3 force simulation)
    │   │   └── useForceGraph.test.ts                   (NEU)
    │   ├── layers/
    │   │   ├── ClusterHulls.tsx                        (NEU)
    │   │   ├── EdgesLayer.tsx                          (NEU)
    │   │   ├── NodesLayer.tsx                          (NEU)
    │   │   └── ActivityLayer.tsx                       (NEU)
    │   ├── controls/
    │   │   ├── GraphControls.tsx                       (NEU - zoom buttons)
    │   │   ├── MiniMap.tsx                             (NEU)
    │   │   ├── SearchBox.tsx                           (NEU)
    │   │   └── EntityLegend.tsx                        (NEU)
    │   ├── panel/
    │   │   └── PersonaDetailPanel.tsx                  (NEU)
    │   └── utils/
    │       ├── colors.ts                               (NEU)
    │       ├── colors.test.ts                          (NEU)
    │       ├── skeletonLayout.ts                       (NEU)
    │       ├── skeletonLayout.test.ts                  (NEU)
    │       ├── convexHull.ts                           (NEU)
    │       └── convexHull.test.ts                      (NEU)
    └── test/
        └── setup.ts                                    (NEU - vitest setup)
```

### Modifizierte Dateien

```
frontend/package.json                                   (add deps + scripts)
frontend/tsconfig.json                                  (possibly add types)
frontend/src/pages/SimulationPage.tsx                   (integrate new graph + detail panel + light theme)
frontend/src/pages/NewSimulationPage.tsx                (light theme)
```

### Entfernte Dateien

```
frontend/src/components/simulation/NetworkGraph.tsx     (DELETE - old Canvas version)
```

### Entfernte Dependencies

```
react-force-graph-2d
```

---

## Task 0: Setup — Vitest + D3 Dependencies

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/vitest.config.ts`
- Create: `frontend/src/test/setup.ts`

- [ ] **Step 1: Install test and D3 dependencies**

```bash
cd /Users/nicopfammatter/Documents/swaarm/frontend
npm install --save-dev vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom @types/d3-force @types/d3-polygon @types/d3-shape @types/d3-zoom @types/d3-selection
npm install d3-force d3-polygon d3-shape d3-zoom d3-selection
```

Expected: packages added to `package.json`, no errors.

- [ ] **Step 2: Add test scripts to package.json**

Edit `frontend/package.json` scripts section:
```json
"scripts": {
  "dev": "vite",
  "build": "tsc -b && vite build",
  "lint": "eslint .",
  "preview": "vite preview",
  "test": "vitest",
  "test:run": "vitest run"
}
```

- [ ] **Step 3: Create vitest config**

Create `frontend/vitest.config.ts`:
```typescript
/// <reference types="vitest" />
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
```

- [ ] **Step 4: Create test setup file**

Create `frontend/src/test/setup.ts`:
```typescript
import '@testing-library/jest-dom'
import { afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'

afterEach(() => {
  cleanup()
})
```

- [ ] **Step 5: Verify vitest runs (with no tests yet)**

Run: `cd frontend && npm run test:run`
Expected: exits cleanly with "No test files found".

- [ ] **Step 6: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/vitest.config.ts frontend/src/test/setup.ts
git commit -m "chore: add vitest and d3 dependencies for graph redesign"
```

---

## Task 1: Graph Types Definition

**Files:**
- Create: `frontend/src/components/simulation/graph/types.ts`

- [ ] **Step 1: Create types file**

Create `frontend/src/components/simulation/graph/types.ts`:
```typescript
import type { SimulationNodeDatum, SimulationLinkDatum } from 'd3-force'
import type { GraphNode as StreamNode, GraphLink as StreamLink } from '@/lib/ws-events'

/**
 * Internal graph node used by the force simulation.
 * Extends SimulationNodeDatum for d3-force compatibility.
 */
export interface SimNode extends SimulationNodeDatum {
  id: string
  label: string
  // Entity-specific
  isEntity: boolean
  entityType?: string
  subType?: string
  importance?: number
  // Persona-specific
  communityId?: number
  sentiment: number
  followerCount: number
  tier: string
  role?: string
  occupation?: string
  personaSource?: string
  // Simulation state (populated by d3-force)
  x?: number
  y?: number
  vx?: number
  vy?: number
  fx?: number | null
  fy?: number | null
}

export type EdgeKind = 'persona_entity' | 'entity_relation' | 'persona_relation' | 'follow'

export interface SimLink extends SimulationLinkDatum<SimNode> {
  source: string | SimNode
  target: string | SimNode
  type: EdgeKind
  label?: string
}

export type ZoomLevel = 'aggregated' | 'structure' | 'detail' | 'full'

export interface GraphBounds {
  minX: number
  maxX: number
  minY: number
  maxY: number
}

export function streamNodeToSimNode(node: StreamNode): SimNode {
  return {
    id: node.id,
    label: node.label,
    isEntity: node.isEntity ?? false,
    entityType: node.entityType,
    subType: node.subType,
    importance: node.importance,
    communityId: node.communityId,
    sentiment: node.sentiment,
    followerCount: node.followerCount,
    tier: node.tier,
    role: node.role,
    occupation: node.occupation,
    personaSource: node.personaSource,
    x: node.x,
    y: node.y,
  }
}

export function streamLinkToSimLink(link: StreamLink): SimLink {
  return {
    source: link.source,
    target: link.target,
    type: link.type as EdgeKind,
    label: link.label,
  }
}

export function zoomLevelFromScale(scale: number): ZoomLevel {
  if (scale < 0.6) return 'aggregated'
  if (scale < 1.5) return 'structure'
  if (scale < 2.5) return 'detail'
  return 'full'
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/simulation/graph/types.ts
git commit -m "feat(graph): add graph type definitions"
```

---

## Task 2: Color Utilities

**Files:**
- Create: `frontend/src/components/simulation/graph/utils/colors.ts`
- Create: `frontend/src/components/simulation/graph/utils/colors.test.ts`

- [ ] **Step 1: Write failing test**

Create `frontend/src/components/simulation/graph/utils/colors.test.ts`:
```typescript
import { describe, it, expect } from 'vitest'
import {
  entityTypeColor,
  sentimentColor,
  personaSourceColor,
  ENTITY_COLORS,
  SENTIMENT_COLORS,
} from './colors'

describe('entityTypeColor', () => {
  it('returns emerald for real_person', () => {
    expect(entityTypeColor('real_person')).toBe('#059669')
  })

  it('returns indigo for real_company', () => {
    expect(entityTypeColor('real_company')).toBe('#4F46E5')
  })

  it('returns fallback for unknown type', () => {
    expect(entityTypeColor('unknown')).toBe('#64748B')
  })
})

describe('sentimentColor', () => {
  it('returns strong green for sentiment > 0.3', () => {
    expect(sentimentColor(0.5)).toBe('#10B981')
  })

  it('returns light green for 0.1 < sentiment <= 0.3', () => {
    expect(sentimentColor(0.2)).toBe('#6EE7B7')
  })

  it('returns slate for neutral', () => {
    expect(sentimentColor(0.05)).toBe('#CBD5E1')
    expect(sentimentColor(-0.05)).toBe('#CBD5E1')
  })

  it('returns light red for -0.3 <= sentiment < -0.1', () => {
    expect(sentimentColor(-0.2)).toBe('#FCA5A5')
  })

  it('returns strong red for sentiment < -0.3', () => {
    expect(sentimentColor(-0.5)).toBe('#EF4444')
  })
})

describe('personaSourceColor', () => {
  it('returns green for real_enriched', () => {
    expect(personaSourceColor('real_enriched')).toBe('#10B981')
  })

  it('returns amber for role_based', () => {
    expect(personaSourceColor('role_based')).toBe('#D97706')
  })

  it('returns null for generated (no badge)', () => {
    expect(personaSourceColor('generated')).toBe(null)
  })
})

describe('palette exports', () => {
  it('exports all 7 entity type colors', () => {
    expect(Object.keys(ENTITY_COLORS)).toHaveLength(7)
  })

  it('exports sentiment color constants', () => {
    expect(SENTIMENT_COLORS.strongPositive).toBe('#10B981')
    expect(SENTIMENT_COLORS.neutral).toBe('#CBD5E1')
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm run test:run src/components/simulation/graph/utils/colors.test.ts`
Expected: FAIL with "Cannot find module './colors'"

- [ ] **Step 3: Write implementation**

Create `frontend/src/components/simulation/graph/utils/colors.ts`:
```typescript
/**
 * Color palette for the visualization.
 * Values are from the design spec 2026-04-10-visualization-redesign-design.md.
 */

export const ENTITY_COLORS: Record<string, string> = {
  real_person: '#059669',   // Emerald
  real_company: '#4F46E5',  // Indigo
  role: '#D97706',          // Amber
  institution: '#7C3AED',   // Violet
  media_outlet: '#DB2777',  // Pink
  product: '#0891B2',       // Cyan
  event: '#EA580C',         // Orange
}

export const SENTIMENT_COLORS = {
  strongPositive: '#10B981',  // >0.3
  positive: '#6EE7B7',        // 0.1 - 0.3
  neutral: '#CBD5E1',         // -0.1 to 0.1
  negative: '#FCA5A5',        // -0.3 to -0.1
  strongNegative: '#EF4444',  // <-0.3
}

export const PERSONA_SOURCE_COLORS: Record<string, string | null> = {
  real_enriched: '#10B981',
  real_minimal: '#6EE7B7',
  role_based: '#D97706',
  generated: null, // no badge for generated
}

export const THEME = {
  bg: '#FAFAFA',
  bgDark: '#F3F4F6',
  dotGrid: '#D0D0D0',
  text: '#1E293B',
  textMuted: '#64748B',
  border: '#E5E7EB',
  borderLight: '#F1F5F9',
  accent: '#E91E63',
  white: '#FFFFFF',
}

const FALLBACK_COLOR = '#64748B'

export function entityTypeColor(type: string | undefined): string {
  if (!type) return FALLBACK_COLOR
  return ENTITY_COLORS[type] ?? FALLBACK_COLOR
}

export function sentimentColor(sentiment: number): string {
  if (sentiment > 0.3) return SENTIMENT_COLORS.strongPositive
  if (sentiment > 0.1) return SENTIMENT_COLORS.positive
  if (sentiment < -0.3) return SENTIMENT_COLORS.strongNegative
  if (sentiment < -0.1) return SENTIMENT_COLORS.negative
  return SENTIMENT_COLORS.neutral
}

export function personaSourceColor(source: string | undefined): string | null {
  if (!source) return null
  return PERSONA_SOURCE_COLORS[source] ?? null
}

export const ENTITY_TYPE_LABELS: Record<string, string> = {
  real_person: 'Person',
  real_company: 'Unternehmen',
  role: 'Rolle',
  institution: 'Institution',
  media_outlet: 'Medium',
  product: 'Produkt',
  event: 'Ereignis',
}

export function entityTypeLabel(type: string | undefined): string {
  if (!type) return 'Unbekannt'
  return ENTITY_TYPE_LABELS[type] ?? type
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npm run test:run src/components/simulation/graph/utils/colors.test.ts`
Expected: PASS all assertions.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/simulation/graph/utils/colors.ts frontend/src/components/simulation/graph/utils/colors.test.ts
git commit -m "feat(graph): add color palette utilities"
```

---

## Task 3: Skeleton Layout Utility

**Files:**
- Create: `frontend/src/components/simulation/graph/utils/skeletonLayout.ts`
- Create: `frontend/src/components/simulation/graph/utils/skeletonLayout.test.ts`

- [ ] **Step 1: Write failing test**

Create `frontend/src/components/simulation/graph/utils/skeletonLayout.test.ts`:
```typescript
import { describe, it, expect } from 'vitest'
import { computeSkeletonLayout } from './skeletonLayout'
import type { SimNode } from '../types'

function makeEntity(id: string, importance = 0.5): SimNode {
  return {
    id, label: id, isEntity: true, importance,
    sentiment: 0, followerCount: 0, tier: 'power_creator',
  }
}

describe('computeSkeletonLayout', () => {
  const width = 1000
  const height = 800

  it('places single entity at center', () => {
    const entities = [makeEntity('a')]
    const positions = computeSkeletonLayout(entities, width, height)
    expect(positions).toHaveLength(1)
    expect(positions[0]).toEqual({ x: 500, y: 400 })
  })

  it('places 2 entities horizontally', () => {
    const entities = [makeEntity('a'), makeEntity('b')]
    const positions = computeSkeletonLayout(entities, width, height)
    expect(positions).toHaveLength(2)
    expect(positions[0].x).toBeLessThan(500)
    expect(positions[1].x).toBeGreaterThan(500)
    expect(positions[0].y).toBe(400)
    expect(positions[1].y).toBe(400)
  })

  it('places 3 entities as equilateral triangle', () => {
    const entities = [makeEntity('a'), makeEntity('b'), makeEntity('c')]
    const positions = computeSkeletonLayout(entities, width, height)
    expect(positions).toHaveLength(3)
    // All entities should be equidistant from center
    const distances = positions.map(p => Math.hypot(p.x - 500, p.y - 400))
    expect(distances[0]).toBeCloseTo(distances[1], 0)
    expect(distances[1]).toBeCloseTo(distances[2], 0)
  })

  it('places 7 entities in a single ring', () => {
    const entities = Array.from({ length: 7 }, (_, i) => makeEntity(String(i)))
    const positions = computeSkeletonLayout(entities, width, height)
    expect(positions).toHaveLength(7)
    // All should be same distance from center
    const distances = positions.map(p => Math.hypot(p.x - 500, p.y - 400))
    const maxDist = Math.max(...distances)
    const minDist = Math.min(...distances)
    expect(maxDist - minDist).toBeLessThan(1)
  })

  it('places 10 entities in two rings when count > 7', () => {
    const entities = Array.from({ length: 10 }, (_, i) => makeEntity(String(i), i < 4 ? 0.9 : 0.4))
    const positions = computeSkeletonLayout(entities, width, height)
    expect(positions).toHaveLength(10)
    // First 4 (high importance) should be in inner ring (smaller distance)
    const innerDist = Math.hypot(positions[0].x - 500, positions[0].y - 400)
    const outerDist = Math.hypot(positions[5].x - 500, positions[5].y - 400)
    expect(innerDist).toBeLessThan(outerDist)
  })

  it('handles empty array', () => {
    expect(computeSkeletonLayout([], width, height)).toEqual([])
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm run test:run src/components/simulation/graph/utils/skeletonLayout.test.ts`
Expected: FAIL with "Cannot find module './skeletonLayout'"

- [ ] **Step 3: Write implementation**

Create `frontend/src/components/simulation/graph/utils/skeletonLayout.ts`:
```typescript
import type { SimNode } from '../types'

export interface Position {
  x: number
  y: number
}

/**
 * Compute fixed geometric positions for entities.
 * Entities are placed in a stable layout (center, line, polygon, rings)
 * so they remain visually dominant and don't get pushed around by force simulation.
 *
 * Layout rules:
 * - 1 entity: center
 * - 2 entities: horizontal line, ±220px from center
 * - 3-7 entities: regular polygon, radius 220-280
 * - 8+ entities: two concentric rings (inner = high importance, outer = lower)
 */
export function computeSkeletonLayout(
  entities: SimNode[],
  width: number,
  height: number,
): Position[] {
  if (entities.length === 0) return []

  const cx = width / 2
  const cy = height / 2

  if (entities.length === 1) {
    return [{ x: cx, y: cy }]
  }

  if (entities.length === 2) {
    return [
      { x: cx - 220, y: cy },
      { x: cx + 220, y: cy },
    ]
  }

  if (entities.length <= 7) {
    // Regular polygon
    const radius = 220 + (entities.length - 3) * 15
    return entities.map((_, i) => {
      // Start at top (-π/2), go clockwise
      const angle = -Math.PI / 2 + (i * 2 * Math.PI) / entities.length
      return {
        x: cx + radius * Math.cos(angle),
        y: cy + radius * Math.sin(angle),
      }
    })
  }

  // 8+ entities: two concentric rings
  // Split by importance: top 40% go to inner ring
  const sortedByImportance = [...entities]
    .map((e, i) => ({ entity: e, originalIndex: i }))
    .sort((a, b) => (b.entity.importance ?? 0.5) - (a.entity.importance ?? 0.5))

  const innerCount = Math.ceil(entities.length * 0.4)
  const outerCount = entities.length - innerCount

  const innerRadius = 180
  const outerRadius = 320

  const positions: Position[] = new Array(entities.length)

  sortedByImportance.slice(0, innerCount).forEach((item, i) => {
    const angle = -Math.PI / 2 + (i * 2 * Math.PI) / innerCount
    positions[item.originalIndex] = {
      x: cx + innerRadius * Math.cos(angle),
      y: cy + innerRadius * Math.sin(angle),
    }
  })

  sortedByImportance.slice(innerCount).forEach((item, i) => {
    const angle = -Math.PI / 2 + (i * 2 * Math.PI) / outerCount
    positions[item.originalIndex] = {
      x: cx + outerRadius * Math.cos(angle),
      y: cy + outerRadius * Math.sin(angle),
    }
  })

  return positions
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npm run test:run src/components/simulation/graph/utils/skeletonLayout.test.ts`
Expected: PASS all assertions.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/simulation/graph/utils/skeletonLayout.ts frontend/src/components/simulation/graph/utils/skeletonLayout.test.ts
git commit -m "feat(graph): add skeleton layout for entity positioning"
```

---

## Task 4: Convex Hull Utility

**Files:**
- Create: `frontend/src/components/simulation/graph/utils/convexHull.ts`
- Create: `frontend/src/components/simulation/graph/utils/convexHull.test.ts`

- [ ] **Step 1: Write failing test**

Create `frontend/src/components/simulation/graph/utils/convexHull.test.ts`:
```typescript
import { describe, it, expect } from 'vitest'
import { computeHullPath } from './convexHull'

describe('computeHullPath', () => {
  it('returns empty string for less than 3 points', () => {
    expect(computeHullPath([[0, 0]])).toBe('')
    expect(computeHullPath([[0, 0], [1, 1]])).toBe('')
  })

  it('returns a valid SVG path for 3+ points', () => {
    const points: [number, number][] = [
      [0, 0], [100, 0], [50, 100],
    ]
    const path = computeHullPath(points, 0)
    expect(path).toMatch(/^M/) // Starts with Move
    expect(path.length).toBeGreaterThan(10)
  })

  it('expands hull by padding amount', () => {
    const points: [number, number][] = [
      [0, 0], [100, 0], [100, 100], [0, 100],
    ]
    const noPadding = computeHullPath(points, 0)
    const withPadding = computeHullPath(points, 20)
    // With padding should produce different (larger) path
    expect(withPadding).not.toBe(noPadding)
    expect(withPadding.length).toBeGreaterThan(0)
  })

  it('handles collinear points', () => {
    const points: [number, number][] = [
      [0, 0], [50, 0], [100, 0],
    ]
    // Collinear points have no real hull
    const path = computeHullPath(points, 0)
    // Should return empty or minimal path
    expect(typeof path).toBe('string')
  })

  it('handles many points', () => {
    const points: [number, number][] = []
    for (let i = 0; i < 20; i++) {
      points.push([Math.random() * 200, Math.random() * 200])
    }
    const path = computeHullPath(points, 10)
    expect(path).toMatch(/^M/)
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm run test:run src/components/simulation/graph/utils/convexHull.test.ts`
Expected: FAIL with "Cannot find module './convexHull'"

- [ ] **Step 3: Write implementation**

Create `frontend/src/components/simulation/graph/utils/convexHull.ts`:
```typescript
import { polygonHull, polygonCentroid } from 'd3-polygon'
import { line as d3Line, curveCatmullRomClosed } from 'd3-shape'

/**
 * Compute a smooth, padded SVG path around a set of points.
 * Used to draw cluster hulls around persona groups.
 *
 * @param points Array of [x, y] coordinates
 * @param padding Distance to expand the hull outward (px)
 * @returns SVG path d-attribute string, or '' if fewer than 3 points
 */
export function computeHullPath(
  points: [number, number][],
  padding = 20,
): string {
  if (points.length < 3) return ''

  const hull = polygonHull(points)
  if (!hull || hull.length < 3) return ''

  // Expand hull outward by padding
  const expanded = padding > 0 ? expandHull(hull, padding) : hull

  // Close the loop for Catmull-Rom curve
  const lineGenerator = d3Line<[number, number]>()
    .x(d => d[0])
    .y(d => d[1])
    .curve(curveCatmullRomClosed.alpha(0.5))

  return lineGenerator(expanded) ?? ''
}

/**
 * Expand a convex hull outward by moving each point away from the centroid.
 */
function expandHull(
  hull: [number, number][],
  padding: number,
): [number, number][] {
  const centroid = polygonCentroid(hull)
  return hull.map(([x, y]) => {
    const dx = x - centroid[0]
    const dy = y - centroid[1]
    const dist = Math.hypot(dx, dy)
    if (dist === 0) return [x, y]
    const scale = (dist + padding) / dist
    return [centroid[0] + dx * scale, centroid[1] + dy * scale]
  })
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npm run test:run src/components/simulation/graph/utils/convexHull.test.ts`
Expected: PASS all assertions.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/simulation/graph/utils/convexHull.ts frontend/src/components/simulation/graph/utils/convexHull.test.ts
git commit -m "feat(graph): add convex hull path utility"
```

---

## Task 5: useForceGraph Hook

**Files:**
- Create: `frontend/src/components/simulation/graph/hooks/useForceGraph.ts`
- Create: `frontend/src/components/simulation/graph/hooks/useForceGraph.test.ts`

- [ ] **Step 1: Write failing test**

Create `frontend/src/components/simulation/graph/hooks/useForceGraph.test.ts`:
```typescript
import { describe, it, expect } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useForceGraph } from './useForceGraph'
import type { SimNode, SimLink } from '../types'

function makeEntity(id: string, importance = 0.5): SimNode {
  return {
    id, label: id, isEntity: true, importance,
    sentiment: 0, followerCount: 0, tier: 'power_creator',
  }
}

function makePersona(id: string, sentiment = 0): SimNode {
  return {
    id, label: id, isEntity: false,
    sentiment, followerCount: 10, tier: 'active_responder',
  }
}

describe('useForceGraph', () => {
  it('positions single entity at center', () => {
    const entities = [makeEntity('e1')]
    const { result } = renderHook(() =>
      useForceGraph(entities, [], { width: 1000, height: 800 })
    )

    const entity = result.current.positionedNodes.find(n => n.id === 'e1')
    expect(entity).toBeDefined()
    expect(entity?.fx).toBe(500)
    expect(entity?.fy).toBe(400)
  })

  it('fixes entity positions via fx/fy', () => {
    const entities = [makeEntity('e1'), makeEntity('e2')]
    const { result } = renderHook(() =>
      useForceGraph(entities, [], { width: 1000, height: 800 })
    )

    const e1 = result.current.positionedNodes.find(n => n.id === 'e1')
    const e2 = result.current.positionedNodes.find(n => n.id === 'e2')
    expect(e1?.fx).toBeDefined()
    expect(e2?.fx).toBeDefined()
    expect(e1?.fx).not.toBe(e2?.fx)
  })

  it('returns both entities and personas in positionedNodes', () => {
    const nodes = [makeEntity('e1'), makePersona('p1'), makePersona('p2')]
    const links: SimLink[] = [
      { source: 'p1', target: 'e1', type: 'persona_entity' },
      { source: 'p2', target: 'e1', type: 'persona_entity' },
    ]
    const { result } = renderHook(() =>
      useForceGraph(nodes, links, { width: 1000, height: 800 })
    )

    expect(result.current.positionedNodes).toHaveLength(3)
  })

  it('handles empty node array', () => {
    const { result } = renderHook(() =>
      useForceGraph([], [], { width: 1000, height: 800 })
    )
    expect(result.current.positionedNodes).toEqual([])
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm run test:run src/components/simulation/graph/hooks/useForceGraph.test.ts`
Expected: FAIL with "Cannot find module './useForceGraph'"

- [ ] **Step 3: Write implementation**

Create `frontend/src/components/simulation/graph/hooks/useForceGraph.ts`:
```typescript
import { useEffect, useRef, useState } from 'react'
import {
  forceSimulation,
  forceLink,
  forceManyBody,
  forceCollide,
  forceRadial,
  type Simulation,
} from 'd3-force'
import type { SimNode, SimLink } from '../types'
import { computeSkeletonLayout } from '../utils/skeletonLayout'

export interface ForceGraphConfig {
  width: number
  height: number
}

export interface ForceGraphResult {
  positionedNodes: SimNode[]
  positionedLinks: SimLink[]
}

/**
 * Custom hook that runs a D3 force simulation on a set of nodes and links.
 *
 * Layout strategy:
 * 1. Entities are placed at fixed positions via computeSkeletonLayout
 * 2. Entities are pinned via fx/fy so force simulation can't move them
 * 3. Personas orbit their linked entity via forceRadial
 * 4. forceCollide prevents node overlap
 * 5. forceManyBody provides gentle repulsion
 *
 * The simulation runs continuously via d3-force ticks, updating
 * node positions in-place. State updates trigger React re-renders.
 */
export function useForceGraph(
  nodes: SimNode[],
  links: SimLink[],
  config: ForceGraphConfig,
): ForceGraphResult {
  const simulationRef = useRef<Simulation<SimNode, SimLink> | null>(null)
  const [version, setVersion] = useState(0)
  const nodesRef = useRef<SimNode[]>([])
  const linksRef = useRef<SimLink[]>([])

  useEffect(() => {
    if (nodes.length === 0) {
      nodesRef.current = []
      linksRef.current = []
      setVersion(v => v + 1)
      return
    }

    // Separate entities and personas
    const entities = nodes.filter(n => n.isEntity)
    const personas = nodes.filter(n => !n.isEntity)

    // Compute fixed positions for entities
    const entityPositions = computeSkeletonLayout(entities, config.width, config.height)
    entities.forEach((e, i) => {
      e.fx = entityPositions[i].x
      e.fy = entityPositions[i].y
      e.x = entityPositions[i].x
      e.y = entityPositions[i].y
    })

    // Initialize persona positions near their linked entity (avoids chaotic startup)
    const entityById = new Map(entities.map(e => [e.id, e]))
    personas.forEach(p => {
      if (p.x != null && p.y != null) return // already positioned

      // Find linked entity from links
      const linkedEntity = links.find(l => {
        const src = typeof l.source === 'string' ? l.source : l.source.id
        const tgt = typeof l.target === 'string' ? l.target : l.target.id
        return (src === p.id && entityById.has(tgt)) || (tgt === p.id && entityById.has(src))
      })

      if (linkedEntity) {
        const src = typeof linkedEntity.source === 'string' ? linkedEntity.source : linkedEntity.source.id
        const tgt = typeof linkedEntity.target === 'string' ? linkedEntity.target : linkedEntity.target.id
        const entityId = entityById.has(src) ? src : tgt
        const entity = entityById.get(entityId)!
        const angle = Math.random() * 2 * Math.PI
        const radius = 100 + Math.random() * 50
        p.x = entity.fx! + Math.cos(angle) * radius
        p.y = entity.fy! + Math.sin(angle) * radius
      } else {
        p.x = config.width / 2 + (Math.random() - 0.5) * 200
        p.y = config.height / 2 + (Math.random() - 0.5) * 200
      }
    })

    // Build link strings to ID references for d3-force
    const simLinks = links.map(l => ({
      ...l,
      source: typeof l.source === 'string' ? l.source : l.source.id,
      target: typeof l.target === 'string' ? l.target : l.target.id,
    }))

    // Stop previous simulation
    if (simulationRef.current) {
      simulationRef.current.stop()
    }

    // Create new simulation
    const simulation = forceSimulation<SimNode>(nodes)
      .force(
        'link',
        forceLink<SimNode, SimLink>(simLinks)
          .id(d => d.id)
          .strength(0.3)
          .distance(80),
      )
      .force('charge', forceManyBody().strength(-80))
      .force('collide', forceCollide(14))
      .alpha(0.8)
      .alphaDecay(0.05)

    // Add per-entity radial force so personas orbit their entity
    entities.forEach(entity => {
      const linkedPersonas = personas.filter(p => {
        return simLinks.some(l => {
          const src = l.source as string
          const tgt = l.target as string
          return (src === p.id && tgt === entity.id) || (tgt === p.id && src === entity.id)
        })
      })

      if (linkedPersonas.length > 0) {
        const radius = 80 + Math.sqrt(linkedPersonas.length) * 10
        const radialForce = forceRadial<SimNode>(
          radius,
          entity.fx!,
          entity.fy!,
        ).strength((d) => (linkedPersonas.some(p => p.id === d.id) ? 0.5 : 0))
        simulation.force(`radial-${entity.id}`, radialForce)
      }
    })

    simulation.on('tick', () => {
      nodesRef.current = [...nodes]
      linksRef.current = simLinks as SimLink[]
      setVersion(v => v + 1)
    })

    simulationRef.current = simulation

    return () => {
      simulation.stop()
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes.length, links.length, config.width, config.height])

  return {
    positionedNodes: nodesRef.current.length > 0 ? nodesRef.current : nodes,
    positionedLinks: linksRef.current.length > 0 ? linksRef.current : links,
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npm run test:run src/components/simulation/graph/hooks/useForceGraph.test.ts`
Expected: PASS all assertions.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/simulation/graph/hooks/
git commit -m "feat(graph): add useForceGraph hook with entity skeleton + persona orbits"
```

---

## Task 6: NodesLayer Component

**Files:**
- Create: `frontend/src/components/simulation/graph/layers/NodesLayer.tsx`

- [ ] **Step 1: Create component**

Create `frontend/src/components/simulation/graph/layers/NodesLayer.tsx`:
```typescript
import { memo } from 'react'
import type { SimNode, ZoomLevel } from '../types'
import {
  entityTypeColor,
  sentimentColor,
  personaSourceColor,
  THEME,
} from '../utils/colors'

interface NodesLayerProps {
  nodes: SimNode[]
  zoomLevel: ZoomLevel
  hoveredId: string | null
  selectedId: string | null
  activeIds: Set<string>
  focusedIds: Set<string> | null // null = no focus mode, show all
  onNodeClick: (node: SimNode) => void
  onNodeHover: (node: SimNode | null) => void
}

const TIER_RADIUS: Record<string, number> = {
  power_creator: 7,
  active_responder: 5,
  selective_engager: 4,
  observer: 3,
}

export const NodesLayer = memo(function NodesLayer({
  nodes,
  zoomLevel,
  hoveredId,
  selectedId,
  activeIds,
  focusedIds,
  onNodeClick,
  onNodeHover,
}: NodesLayerProps) {
  return (
    <g className="nodes-layer">
      {nodes.map(node => {
        if (node.x == null || node.y == null) return null

        const isHovered = hoveredId === node.id
        const isSelected = selectedId === node.id
        const isActive = activeIds.has(node.id)
        const isDimmed = focusedIds != null && !focusedIds.has(node.id)
        const opacity = isDimmed ? 0.15 : 1

        if (node.isEntity) {
          return (
            <EntityNode
              key={node.id}
              node={node}
              isHovered={isHovered}
              isSelected={isSelected}
              zoomLevel={zoomLevel}
              opacity={opacity}
              onClick={() => onNodeClick(node)}
              onMouseEnter={() => onNodeHover(node)}
              onMouseLeave={() => onNodeHover(null)}
            />
          )
        }

        return (
          <PersonaNode
            key={node.id}
            node={node}
            isHovered={isHovered}
            isSelected={isSelected}
            isActive={isActive}
            zoomLevel={zoomLevel}
            opacity={opacity}
            onClick={() => onNodeClick(node)}
            onMouseEnter={() => onNodeHover(node)}
            onMouseLeave={() => onNodeHover(null)}
          />
        )
      })}
    </g>
  )
})

interface EntityNodeProps {
  node: SimNode
  isHovered: boolean
  isSelected: boolean
  zoomLevel: ZoomLevel
  opacity: number
  onClick: () => void
  onMouseEnter: () => void
  onMouseLeave: () => void
}

function EntityNode({
  node,
  isHovered,
  isSelected,
  zoomLevel,
  opacity,
  onClick,
  onMouseEnter,
  onMouseLeave,
}: EntityNodeProps) {
  const color = entityTypeColor(node.entityType)
  const importance = node.importance ?? 0.5
  const scale = 0.7 + importance * 0.6 // 0.7 to 1.3
  const isDiamond = node.entityType === 'real_person' || node.entityType === 'real_company'

  return (
    <g
      transform={`translate(${node.x},${node.y})`}
      style={{ opacity, cursor: 'pointer', transition: 'opacity 0.2s' }}
      onClick={onClick}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    >
      {/* Glow ring for selected */}
      {isSelected && (
        <circle r={24 * scale + 6} fill="none" stroke={THEME.accent} strokeWidth={2.5} />
      )}
      {/* Hover ring */}
      {isHovered && !isSelected && (
        <circle r={24 * scale + 3} fill="none" stroke={THEME.accent} strokeWidth={1.5} opacity={0.6} />
      )}

      {isDiamond ? (
        <rect
          x={-12 * scale}
          y={-12 * scale}
          width={24 * scale}
          height={24 * scale}
          fill={color}
          stroke={THEME.white}
          strokeWidth={2}
          transform="rotate(45)"
          filter="url(#entity-shadow)"
        />
      ) : (
        <circle
          r={16 * scale}
          fill={color}
          stroke={THEME.white}
          strokeWidth={2}
          filter="url(#entity-shadow)"
        />
      )}

      {/* Label — always visible for entities */}
      <text
        y={24 * scale + 14}
        textAnchor="middle"
        fontSize={13}
        fontWeight={600}
        fill={THEME.text}
        style={{ pointerEvents: 'none', userSelect: 'none' }}
      >
        {node.label}
      </text>
      {node.subType && zoomLevel !== 'aggregated' && (
        <text
          y={24 * scale + 28}
          textAnchor="middle"
          fontSize={10}
          fill={THEME.textMuted}
          style={{ pointerEvents: 'none', userSelect: 'none' }}
        >
          {node.subType}
        </text>
      )}
    </g>
  )
}

interface PersonaNodeProps {
  node: SimNode
  isHovered: boolean
  isSelected: boolean
  isActive: boolean
  zoomLevel: ZoomLevel
  opacity: number
  onClick: () => void
  onMouseEnter: () => void
  onMouseLeave: () => void
}

function PersonaNode({
  node,
  isHovered,
  isSelected,
  isActive,
  zoomLevel,
  opacity,
  onClick,
  onMouseEnter,
  onMouseLeave,
}: PersonaNodeProps) {
  const fillColor = sentimentColor(node.sentiment)
  const r = TIER_RADIUS[node.tier] ?? 4
  const sourceColor = personaSourceColor(node.personaSource)

  // In aggregated view, personas are hidden (rendered as entity bubbles instead)
  if (zoomLevel === 'aggregated') return null

  const showLabel =
    zoomLevel === 'full' ||
    (zoomLevel === 'detail' && node.tier === 'power_creator') ||
    isHovered ||
    isSelected

  return (
    <g
      transform={`translate(${node.x},${node.y})`}
      style={{ opacity, cursor: 'pointer', transition: 'opacity 0.2s' }}
      onClick={onClick}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    >
      {/* Selection ring */}
      {isSelected && (
        <circle r={r + 5} fill="none" stroke={THEME.accent} strokeWidth={2} />
      )}
      {/* Pulse on active */}
      {isActive && (
        <circle r={r + 2} fill={fillColor} opacity={0.3} className="pulse-ring">
          <animate
            attributeName="r"
            values={`${r};${r * 2.5};${r}`}
            dur="1.5s"
            repeatCount="indefinite"
          />
          <animate
            attributeName="opacity"
            values="0.5;0;0.5"
            dur="1.5s"
            repeatCount="indefinite"
          />
        </circle>
      )}

      {/* Main circle */}
      <circle
        r={r}
        fill={fillColor}
        stroke={THEME.white}
        strokeWidth={1.5}
      />

      {/* Persona source badge (for non-generated) */}
      {sourceColor && (
        <circle
          cx={r * 0.7}
          cy={-r * 0.7}
          r={2}
          fill={sourceColor}
          stroke={THEME.white}
          strokeWidth={0.5}
        />
      )}

      {/* Label (zoom-dependent) */}
      {showLabel && node.label && (
        <g transform={`translate(0, ${r + 12})`} style={{ pointerEvents: 'none' }}>
          <rect
            x={-(node.label.length * 3.5)}
            y={-8}
            width={node.label.length * 7}
            height={14}
            fill="rgba(255,255,255,0.9)"
            stroke={THEME.border}
            strokeWidth={0.5}
            rx={3}
          />
          <text
            textAnchor="middle"
            dy={3}
            fontSize={10}
            fontWeight={500}
            fill={THEME.text}
            style={{ userSelect: 'none' }}
          >
            {node.label}
          </text>
        </g>
      )}
    </g>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/simulation/graph/layers/NodesLayer.tsx
git commit -m "feat(graph): add NodesLayer with entity and persona rendering"
```

---

## Task 7: EdgesLayer Component

**Files:**
- Create: `frontend/src/components/simulation/graph/layers/EdgesLayer.tsx`

- [ ] **Step 1: Create component**

Create `frontend/src/components/simulation/graph/layers/EdgesLayer.tsx`:
```typescript
import { memo } from 'react'
import type { SimNode, SimLink, ZoomLevel } from '../types'
import { entityTypeColor, THEME } from '../utils/colors'

interface EdgesLayerProps {
  links: SimLink[]
  nodes: SimNode[]
  zoomLevel: ZoomLevel
  focusedIds: Set<string> | null
  hoveredLinkIds: Set<string>
}

export const EdgesLayer = memo(function EdgesLayer({
  links,
  nodes,
  zoomLevel,
  focusedIds,
  hoveredLinkIds,
}: EdgesLayerProps) {
  const nodeById = new Map(nodes.map(n => [n.id, n]))

  // Group edges by node pair to compute curvature for multi-edges
  const pairCounts = new Map<string, number>()
  const pairIndex = new Map<string, number>()
  links.forEach(link => {
    const src = typeof link.source === 'string' ? link.source : link.source.id
    const tgt = typeof link.target === 'string' ? link.target : link.target.id
    const pairKey = [src, tgt].sort().join('|')
    pairCounts.set(pairKey, (pairCounts.get(pairKey) ?? 0) + 1)
  })

  // In aggregated view, only show entity-entity edges
  const visibleLinks =
    zoomLevel === 'aggregated'
      ? links.filter(l => l.type === 'entity_relation')
      : links

  return (
    <g className="edges-layer">
      {visibleLinks.map((link, i) => {
        const src = typeof link.source === 'string' ? link.source : link.source.id
        const tgt = typeof link.target === 'string' ? link.target : link.target.id
        const sourceNode = nodeById.get(src)
        const targetNode = nodeById.get(tgt)

        if (!sourceNode || !targetNode) return null
        if (sourceNode.x == null || targetNode.x == null) return null

        const linkKey = `${src}-${tgt}-${i}`
        const pairKey = [src, tgt].sort().join('|')
        const pairTotal = pairCounts.get(pairKey) ?? 1
        const pairI = pairIndex.get(pairKey) ?? 0
        pairIndex.set(pairKey, pairI + 1)

        // Dim non-focused edges
        const isDimmed =
          focusedIds != null &&
          !(focusedIds.has(src) && focusedIds.has(tgt))
        const isHovered = hoveredLinkIds.has(linkKey)

        return (
          <EdgeRenderer
            key={linkKey}
            link={link}
            sourceNode={sourceNode}
            targetNode={targetNode}
            pairIndex={pairI}
            pairTotal={pairTotal}
            isDimmed={isDimmed}
            isHovered={isHovered}
            zoomLevel={zoomLevel}
          />
        )
      })}
    </g>
  )
})

interface EdgeRendererProps {
  link: SimLink
  sourceNode: SimNode
  targetNode: SimNode
  pairIndex: number
  pairTotal: number
  isDimmed: boolean
  isHovered: boolean
  zoomLevel: ZoomLevel
}

function EdgeRenderer({
  link,
  sourceNode,
  targetNode,
  pairIndex,
  pairTotal,
  isDimmed,
  isHovered,
  zoomLevel,
}: EdgeRendererProps) {
  const sx = sourceNode.x!
  const sy = sourceNode.y!
  const tx = targetNode.x!
  const ty = targetNode.y!

  // Compute bezier curve for multi-edges
  let path: string
  let midX: number
  let midY: number

  if (pairTotal === 1) {
    // Straight line
    path = `M ${sx} ${sy} L ${tx} ${ty}`
    midX = (sx + tx) / 2
    midY = (sy + ty) / 2
  } else {
    // Bezier curve with perpendicular offset
    const curvature = ((pairIndex / (pairTotal - 1)) - 0.5) * 0.6
    const dx = tx - sx
    const dy = ty - sy
    const dist = Math.hypot(dx, dy)
    const offsetX = (-dy / dist) * curvature * dist
    const offsetY = (dx / dist) * curvature * dist
    const cx = (sx + tx) / 2 + offsetX
    const cy = (sy + ty) / 2 + offsetY
    path = `M ${sx} ${sy} Q ${cx} ${cy} ${tx} ${ty}`
    midX = 0.25 * sx + 0.5 * cx + 0.25 * tx
    midY = 0.25 * sy + 0.5 * cy + 0.25 * ty
  }

  // Style based on link type
  let stroke: string
  let strokeWidth: number
  let opacity: number
  let label = link.label

  switch (link.type) {
    case 'entity_relation':
      stroke = entityTypeColor(sourceNode.entityType)
      strokeWidth = 2.5
      opacity = 0.7
      break
    case 'persona_entity':
      stroke = THEME.border
      strokeWidth = 0.8
      opacity = 0.5
      label = undefined
      break
    case 'persona_relation':
      stroke = '#94A3B8'
      strokeWidth = 1.2
      opacity = 0.6
      // Labels only when zoomed in
      if (zoomLevel !== 'full' && zoomLevel !== 'detail') {
        label = undefined
      }
      break
    case 'follow':
    default:
      stroke = THEME.border
      strokeWidth = 0.6
      opacity = 0.4
      label = undefined
  }

  if (isHovered) {
    stroke = THEME.accent
    strokeWidth += 1
    opacity = 1
  }

  const finalOpacity = isDimmed ? opacity * 0.3 : opacity

  return (
    <g style={{ transition: 'opacity 0.2s' }}>
      <path
        d={path}
        fill="none"
        stroke={stroke}
        strokeWidth={strokeWidth}
        opacity={finalOpacity}
      />
      {label && link.type === 'entity_relation' && (
        <EdgeLabel x={midX} y={midY} text={label} opacity={finalOpacity} />
      )}
      {label && link.type === 'persona_relation' && (
        <EdgeLabel x={midX} y={midY} text={label} opacity={finalOpacity} size="sm" />
      )}
    </g>
  )
}

interface EdgeLabelProps {
  x: number
  y: number
  text: string
  opacity: number
  size?: 'sm' | 'md'
}

function EdgeLabel({ x, y, text, opacity, size = 'md' }: EdgeLabelProps) {
  const fontSize = size === 'sm' ? 9 : 11
  const padH = 6
  const padV = 3
  // Estimate text width (since we can't measure without rendering)
  const textWidth = text.length * (fontSize * 0.55)

  return (
    <g transform={`translate(${x},${y})`} style={{ pointerEvents: 'none' }} opacity={opacity}>
      <rect
        x={-textWidth / 2 - padH}
        y={-fontSize / 2 - padV}
        width={textWidth + padH * 2}
        height={fontSize + padV * 2}
        fill="white"
        stroke={THEME.border}
        strokeWidth={0.5}
        rx={3}
      />
      <text
        textAnchor="middle"
        dominantBaseline="middle"
        fontSize={fontSize}
        fontWeight={500}
        fill={THEME.text}
        style={{ userSelect: 'none' }}
      >
        {text}
      </text>
    </g>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/simulation/graph/layers/EdgesLayer.tsx
git commit -m "feat(graph): add EdgesLayer with multi-edge curves and labels"
```

---

## Task 8: ClusterHulls Component

**Files:**
- Create: `frontend/src/components/simulation/graph/layers/ClusterHulls.tsx`

- [ ] **Step 1: Create component**

Create `frontend/src/components/simulation/graph/layers/ClusterHulls.tsx`:
```typescript
import { memo, useMemo } from 'react'
import type { SimNode, SimLink, ZoomLevel } from '../types'
import { entityTypeColor } from '../utils/colors'
import { computeHullPath } from '../utils/convexHull'

interface ClusterHullsProps {
  nodes: SimNode[]
  links: SimLink[]
  zoomLevel: ZoomLevel
}

/**
 * Renders soft background "clouds" around personas belonging to each entity.
 * Uses convex hull of persona positions, smoothed with Catmull-Rom curves.
 */
export const ClusterHulls = memo(function ClusterHulls({
  nodes,
  links,
  zoomLevel,
}: ClusterHullsProps) {
  const hulls = useMemo(() => {
    if (zoomLevel === 'aggregated') return []

    const entities = nodes.filter(n => n.isEntity)
    const nodeById = new Map(nodes.map(n => [n.id, n]))
    const result: Array<{ entityId: string; color: string; path: string }> = []

    for (const entity of entities) {
      // Find all personas linked to this entity via persona_entity edges
      const linkedPersonaIds = new Set<string>()
      links.forEach(l => {
        if (l.type !== 'persona_entity') return
        const src = typeof l.source === 'string' ? l.source : l.source.id
        const tgt = typeof l.target === 'string' ? l.target : l.target.id
        if (src === entity.id) linkedPersonaIds.add(tgt)
        if (tgt === entity.id) linkedPersonaIds.add(src)
      })

      if (linkedPersonaIds.size < 3) continue

      // Collect positions including the entity itself
      const points: [number, number][] = []
      if (entity.x != null && entity.y != null) {
        points.push([entity.x, entity.y])
      }
      linkedPersonaIds.forEach(pid => {
        const p = nodeById.get(pid)
        if (p?.x != null && p?.y != null) {
          points.push([p.x, p.y])
        }
      })

      if (points.length < 3) continue

      const path = computeHullPath(points, 25)
      if (!path) continue

      result.push({
        entityId: entity.id,
        color: entityTypeColor(entity.entityType),
        path,
      })
    }

    return result
  }, [nodes, links, zoomLevel])

  return (
    <g className="cluster-hulls-layer">
      {hulls.map(hull => (
        <path
          key={hull.entityId}
          d={hull.path}
          fill={hull.color}
          fillOpacity={0.08}
          stroke={hull.color}
          strokeOpacity={0.2}
          strokeWidth={1}
          style={{ transition: 'opacity 0.3s' }}
        />
      ))}
    </g>
  )
})
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/simulation/graph/layers/ClusterHulls.tsx
git commit -m "feat(graph): add ClusterHulls layer for entity grouping"
```

---

## Task 9: NetworkGraph Main Component

**Files:**
- Create: `frontend/src/components/simulation/graph/NetworkGraph.tsx`

- [ ] **Step 1: Create main NetworkGraph component**

Create `frontend/src/components/simulation/graph/NetworkGraph.tsx`:
```typescript
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { select } from 'd3-selection'
import { zoom as d3zoom, zoomIdentity, type ZoomTransform } from 'd3-zoom'
import type { GraphNode as StreamNode, GraphLink as StreamLink } from '@/lib/ws-events'
import {
  type SimNode,
  type SimLink,
  type ZoomLevel,
  streamNodeToSimNode,
  streamLinkToSimLink,
  zoomLevelFromScale,
} from './types'
import { useForceGraph } from './hooks/useForceGraph'
import { ClusterHulls } from './layers/ClusterHulls'
import { EdgesLayer } from './layers/EdgesLayer'
import { NodesLayer } from './layers/NodesLayer'
import { THEME } from './utils/colors'

export interface NetworkGraphProps {
  nodes: StreamNode[]
  links: StreamLink[]
  activeNodeIds: Set<string>
  width: number
  height: number
  onNodeSelect: (node: SimNode | null) => void
}

export function NetworkGraph({
  nodes: streamNodes,
  links: streamLinks,
  activeNodeIds,
  width,
  height,
  onNodeSelect,
}: NetworkGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const zoomBehaviorRef = useRef<ReturnType<typeof d3zoom<SVGSVGElement, unknown>> | null>(null)
  const [transform, setTransform] = useState<ZoomTransform>(zoomIdentity)

  const [hoveredId, setHoveredId] = useState<string | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)

  // Convert stream nodes to sim nodes (stable: only when count changes)
  const simNodes: SimNode[] = useMemo(
    () => streamNodes.map(streamNodeToSimNode),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [streamNodes.length],
  )

  const simLinks: SimLink[] = useMemo(
    () => streamLinks.map(streamLinkToSimLink),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [streamLinks.length],
  )

  // Update sentiments in-place on existing nodes (avoids re-creating simulation)
  useEffect(() => {
    const sentimentById = new Map(streamNodes.map(n => [n.id, n.sentiment]))
    simNodes.forEach(n => {
      const newSentiment = sentimentById.get(n.id)
      if (newSentiment != null) n.sentiment = newSentiment
    })
  }, [streamNodes, simNodes])

  // Run force simulation
  const { positionedNodes, positionedLinks } = useForceGraph(simNodes, simLinks, {
    width,
    height,
  })

  // Initialize d3-zoom on mount
  useEffect(() => {
    if (!svgRef.current) return
    const svg = select(svgRef.current)

    const zoomBehavior = d3zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.2, 5])
      .on('zoom', event => {
        setTransform(event.transform)
      })

    svg.call(zoomBehavior)
    zoomBehaviorRef.current = zoomBehavior

    return () => {
      svg.on('.zoom', null)
    }
  }, [])

  // Compute zoom level from current scale
  const zoomLevel: ZoomLevel = zoomLevelFromScale(transform.k)

  // Focus mode — hovered node shows its 1-hop neighborhood
  const focusedIds = useMemo((): Set<string> | null => {
    if (!hoveredId) return null
    const ids = new Set<string>([hoveredId])
    positionedLinks.forEach(link => {
      const src = typeof link.source === 'string' ? link.source : link.source.id
      const tgt = typeof link.target === 'string' ? link.target : link.target.id
      if (src === hoveredId) ids.add(tgt)
      if (tgt === hoveredId) ids.add(src)
    })
    return ids
  }, [hoveredId, positionedLinks])

  const handleNodeClick = useCallback((node: SimNode) => {
    setSelectedId(prev => (prev === node.id ? null : node.id))
    onNodeSelect(node)
  }, [onNodeSelect])

  const handleBackgroundClick = useCallback(() => {
    setSelectedId(null)
    onNodeSelect(null)
  }, [onNodeSelect])

  return (
    <div
      className="relative w-full h-full overflow-hidden"
      style={{
        backgroundColor: THEME.bg,
        backgroundImage: `radial-gradient(${THEME.dotGrid} 1.5px, transparent 1.5px)`,
        backgroundSize: '24px 24px',
      }}
    >
      <svg
        ref={svgRef}
        width={width}
        height={height}
        onClick={handleBackgroundClick}
      >
        <defs>
          <filter id="entity-shadow">
            <feDropShadow dx="0" dy="2" stdDeviation="4" floodOpacity="0.12" />
          </filter>
        </defs>

        <g transform={`translate(${transform.x},${transform.y}) scale(${transform.k})`}>
          <ClusterHulls
            nodes={positionedNodes}
            links={positionedLinks}
            zoomLevel={zoomLevel}
          />
          <EdgesLayer
            links={positionedLinks}
            nodes={positionedNodes}
            zoomLevel={zoomLevel}
            focusedIds={focusedIds}
            hoveredLinkIds={new Set()}
          />
          <NodesLayer
            nodes={positionedNodes}
            zoomLevel={zoomLevel}
            hoveredId={hoveredId}
            selectedId={selectedId}
            activeIds={activeNodeIds}
            focusedIds={focusedIds}
            onNodeClick={(node) => {
              handleNodeClick(node)
            }}
            onNodeHover={(node) => setHoveredId(node?.id ?? null)}
          />
        </g>

        {/* Footer stats */}
        <g transform={`translate(16, ${height - 24})`}>
          <rect x={-4} y={-14} width={200} height={20} rx={6} fill="rgba(255,255,255,0.9)" stroke={THEME.border} />
          <text fontSize={11} fill={THEME.textMuted} style={{ userSelect: 'none' }}>
            {positionedNodes.filter(n => n.isEntity).length} Entitäten · {positionedNodes.filter(n => !n.isEntity).length} Personas · {positionedLinks.length} Verbindungen
          </text>
        </g>
      </svg>
    </div>
  )
}
```

- [ ] **Step 2: Verify build passes**

Run: `cd frontend && npm run build`
Expected: TypeScript compiles successfully.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/simulation/graph/NetworkGraph.tsx
git commit -m "feat(graph): add main NetworkGraph SVG component with d3-zoom"
```

---

## Task 10: GraphControls (Zoom Buttons)

**Files:**
- Create: `frontend/src/components/simulation/graph/controls/GraphControls.tsx`

- [ ] **Step 1: Create component**

Create `frontend/src/components/simulation/graph/controls/GraphControls.tsx`:
```typescript
import { THEME } from '../utils/colors'

interface GraphControlsProps {
  onZoomIn: () => void
  onZoomOut: () => void
  onFitToContent: () => void
  onReset: () => void
}

export function GraphControls({
  onZoomIn,
  onZoomOut,
  onFitToContent,
  onReset,
}: GraphControlsProps) {
  return (
    <div
      className="absolute top-4 right-4 flex flex-col gap-1 rounded-lg overflow-hidden"
      style={{
        backgroundColor: THEME.white,
        border: `1px solid ${THEME.border}`,
        boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
      }}
    >
      <ControlButton title="Vergrössern" onClick={onZoomIn} ariaLabel="Zoom in">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
          <line x1="12" y1="5" x2="12" y2="19" />
          <line x1="5" y1="12" x2="19" y2="12" />
        </svg>
      </ControlButton>
      <Divider />
      <ControlButton title="Verkleinern" onClick={onZoomOut} ariaLabel="Zoom out">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
          <line x1="5" y1="12" x2="19" y2="12" />
        </svg>
      </ControlButton>
      <Divider />
      <ControlButton title="Alles anzeigen" onClick={onFitToContent} ariaLabel="Fit to content">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
          <polyline points="4 14 4 20 10 20" />
          <polyline points="20 10 20 4 14 4" />
          <line x1="14" y1="10" x2="21" y2="3" />
          <line x1="3" y1="21" x2="10" y2="14" />
        </svg>
      </ControlButton>
      <Divider />
      <ControlButton title="Zurücksetzen" onClick={onReset} ariaLabel="Reset view">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
          <polyline points="1 4 1 10 7 10" />
          <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
        </svg>
      </ControlButton>
    </div>
  )
}

interface ControlButtonProps {
  title: string
  ariaLabel: string
  onClick: () => void
  children: React.ReactNode
}

function ControlButton({ title, ariaLabel, onClick, children }: ControlButtonProps) {
  return (
    <button
      type="button"
      title={title}
      aria-label={ariaLabel}
      onClick={onClick}
      className="w-8 h-8 flex items-center justify-center transition-colors"
      style={{ color: THEME.text }}
      onMouseEnter={e => {
        e.currentTarget.style.backgroundColor = THEME.borderLight
      }}
      onMouseLeave={e => {
        e.currentTarget.style.backgroundColor = 'transparent'
      }}
    >
      {children}
    </button>
  )
}

function Divider() {
  return <div style={{ height: 1, backgroundColor: THEME.border }} />
}
```

- [ ] **Step 2: Wire up GraphControls in NetworkGraph**

Edit `frontend/src/components/simulation/graph/NetworkGraph.tsx`. Add import at top:
```typescript
import { GraphControls } from './controls/GraphControls'
```

In the `useEffect` that sets up zoom, expose the zoom behavior to enable programmatic zoom. Also add zoom handler functions. Locate the zoom useEffect and add these handlers after it:

```typescript
const handleZoomIn = useCallback(() => {
  if (!svgRef.current || !zoomBehaviorRef.current) return
  select(svgRef.current).transition().duration(250).call(
    zoomBehaviorRef.current.scaleBy,
    1.4,
  )
}, [])

const handleZoomOut = useCallback(() => {
  if (!svgRef.current || !zoomBehaviorRef.current) return
  select(svgRef.current).transition().duration(250).call(
    zoomBehaviorRef.current.scaleBy,
    0.7,
  )
}, [])

const handleReset = useCallback(() => {
  if (!svgRef.current || !zoomBehaviorRef.current) return
  select(svgRef.current).transition().duration(400).call(
    zoomBehaviorRef.current.transform,
    zoomIdentity,
  )
}, [])

const handleFitToContent = useCallback(() => {
  if (!svgRef.current || !zoomBehaviorRef.current || positionedNodes.length === 0) return
  const xs = positionedNodes.map(n => n.x ?? 0)
  const ys = positionedNodes.map(n => n.y ?? 0)
  const minX = Math.min(...xs)
  const maxX = Math.max(...xs)
  const minY = Math.min(...ys)
  const maxY = Math.max(...ys)
  const contentW = maxX - minX + 120
  const contentH = maxY - minY + 120
  const scale = Math.min(width / contentW, height / contentH, 2)
  const tx = width / 2 - (minX + maxX) / 2 * scale
  const ty = height / 2 - (minY + maxY) / 2 * scale
  select(svgRef.current).transition().duration(500).call(
    zoomBehaviorRef.current.transform,
    zoomIdentity.translate(tx, ty).scale(scale),
  )
}, [positionedNodes, width, height])
```

Add `<GraphControls>` inside the outer div, AFTER the `<svg>` closing tag:

```tsx
<GraphControls
  onZoomIn={handleZoomIn}
  onZoomOut={handleZoomOut}
  onFitToContent={handleFitToContent}
  onReset={handleReset}
/>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/simulation/graph/controls/GraphControls.tsx frontend/src/components/simulation/graph/NetworkGraph.tsx
git commit -m "feat(graph): add GraphControls with zoom/fit/reset"
```

---

## Task 11: SearchBox Component

**Files:**
- Create: `frontend/src/components/simulation/graph/controls/SearchBox.tsx`

- [ ] **Step 1: Create component**

Create `frontend/src/components/simulation/graph/controls/SearchBox.tsx`:
```typescript
import { useMemo, useState, useRef, useEffect } from 'react'
import type { SimNode } from '../types'
import { THEME, entityTypeColor, sentimentColor } from '../utils/colors'

interface SearchBoxProps {
  nodes: SimNode[]
  onSelect: (node: SimNode) => void
}

export function SearchBox({ nodes, onSelect }: SearchBoxProps) {
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  const results = useMemo(() => {
    if (!query.trim()) return []
    const q = query.toLowerCase()
    return nodes
      .filter(n =>
        n.label.toLowerCase().includes(q) ||
        n.occupation?.toLowerCase().includes(q) ||
        n.subType?.toLowerCase().includes(q)
      )
      .slice(0, 8)
  }, [query, nodes])

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleSelect = (node: SimNode) => {
    onSelect(node)
    setQuery('')
    setOpen(false)
  }

  return (
    <div
      ref={containerRef}
      className="absolute top-4 left-4 w-72"
      onClick={e => e.stopPropagation()}
    >
      <div
        className="flex items-center gap-2 px-4 py-2 rounded-full"
        style={{
          backgroundColor: THEME.white,
          border: `1px solid ${THEME.border}`,
          boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
        }}
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={THEME.textMuted} strokeWidth={2.5}>
          <circle cx="11" cy="11" r="8" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
        <input
          type="text"
          placeholder="Persona oder Entity suchen..."
          value={query}
          onChange={e => {
            setQuery(e.target.value)
            setOpen(true)
          }}
          onFocus={() => setOpen(true)}
          className="flex-1 outline-none bg-transparent text-sm"
          style={{ color: THEME.text }}
        />
        {query && (
          <button
            type="button"
            onClick={() => {
              setQuery('')
              setOpen(false)
            }}
            className="text-xs"
            style={{ color: THEME.textMuted }}
          >
            ×
          </button>
        )}
      </div>

      {open && results.length > 0 && (
        <div
          className="absolute top-full left-0 right-0 mt-1 rounded-lg overflow-hidden"
          style={{
            backgroundColor: THEME.white,
            border: `1px solid ${THEME.border}`,
            boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
          }}
        >
          {results.map(node => (
            <button
              key={node.id}
              type="button"
              onClick={() => handleSelect(node)}
              className="w-full flex items-center gap-2 px-4 py-2 text-left transition-colors"
              style={{ color: THEME.text }}
              onMouseEnter={e => {
                e.currentTarget.style.backgroundColor = THEME.borderLight
              }}
              onMouseLeave={e => {
                e.currentTarget.style.backgroundColor = 'transparent'
              }}
            >
              <div
                className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                style={{
                  backgroundColor: node.isEntity
                    ? entityTypeColor(node.entityType)
                    : sentimentColor(node.sentiment),
                }}
              />
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium truncate">{node.label}</div>
                {(node.occupation || node.subType) && (
                  <div className="text-xs truncate" style={{ color: THEME.textMuted }}>
                    {node.occupation || node.subType}
                  </div>
                )}
              </div>
              {node.isEntity && (
                <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ backgroundColor: THEME.borderLight, color: THEME.textMuted }}>
                  Entity
                </span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Integrate SearchBox into NetworkGraph**

Edit `frontend/src/components/simulation/graph/NetworkGraph.tsx`. Add import:
```typescript
import { SearchBox } from './controls/SearchBox'
```

Add a handler for search selection that pans to the selected node:
```typescript
const handleSearchSelect = useCallback((node: SimNode) => {
  if (!svgRef.current || !zoomBehaviorRef.current || node.x == null || node.y == null) return
  const targetScale = 2
  const tx = width / 2 - node.x * targetScale
  const ty = height / 2 - node.y * targetScale
  select(svgRef.current).transition().duration(500).call(
    zoomBehaviorRef.current.transform,
    zoomIdentity.translate(tx, ty).scale(targetScale),
  )
  setSelectedId(node.id)
  onNodeSelect(node)
}, [width, height, onNodeSelect])
```

Add `<SearchBox>` inside the outer div, before `<GraphControls>`:
```tsx
<SearchBox nodes={positionedNodes} onSelect={handleSearchSelect} />
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/simulation/graph/controls/SearchBox.tsx frontend/src/components/simulation/graph/NetworkGraph.tsx
git commit -m "feat(graph): add SearchBox with zoom-to-node"
```

---

## Task 12: EntityLegend with Filters

**Files:**
- Create: `frontend/src/components/simulation/graph/controls/EntityLegend.tsx`

- [ ] **Step 1: Create component**

Create `frontend/src/components/simulation/graph/controls/EntityLegend.tsx`:
```typescript
import { useMemo } from 'react'
import type { SimNode } from '../types'
import { entityTypeColor, entityTypeLabel, THEME } from '../utils/colors'

interface EntityLegendProps {
  nodes: SimNode[]
  hiddenTypes: Set<string>
  onToggle: (type: string) => void
}

export function EntityLegend({ nodes, hiddenTypes, onToggle }: EntityLegendProps) {
  const counts = useMemo(() => {
    const map = new Map<string, number>()
    nodes.forEach(n => {
      if (n.isEntity && n.entityType) {
        map.set(n.entityType, (map.get(n.entityType) ?? 0) + 1)
      }
    })
    return map
  }, [nodes])

  if (counts.size === 0) return null

  return (
    <div
      className="absolute bottom-4 left-4 rounded-lg"
      style={{
        backgroundColor: THEME.white,
        border: `1px solid ${THEME.border}`,
        boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
        padding: '12px 16px',
        maxWidth: 320,
      }}
      onClick={e => e.stopPropagation()}
    >
      <div
        className="text-[10px] font-bold uppercase tracking-wider mb-2"
        style={{ color: THEME.accent }}
      >
        Entities
      </div>
      <div className="flex flex-wrap gap-x-3 gap-y-1.5">
        {Array.from(counts.entries()).map(([type, count]) => {
          const hidden = hiddenTypes.has(type)
          return (
            <button
              key={type}
              type="button"
              onClick={() => onToggle(type)}
              className="flex items-center gap-1.5 text-[11px] transition-opacity"
              style={{
                opacity: hidden ? 0.35 : 1,
                color: THEME.text,
              }}
              title={hidden ? 'Einblenden' : 'Ausblenden'}
            >
              <div
                className="w-2.5 h-2.5 rounded-full"
                style={{ backgroundColor: entityTypeColor(type) }}
              />
              <span className={hidden ? 'line-through' : ''}>
                {entityTypeLabel(type)}
              </span>
              <span style={{ color: THEME.textMuted }}>{count}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Wire up EntityLegend in NetworkGraph**

Edit `frontend/src/components/simulation/graph/NetworkGraph.tsx`. Add import:
```typescript
import { EntityLegend } from './controls/EntityLegend'
```

Add state for hidden types:
```typescript
const [hiddenTypes, setHiddenTypes] = useState<Set<string>>(new Set())

const handleToggleType = useCallback((type: string) => {
  setHiddenTypes(prev => {
    const next = new Set(prev)
    if (next.has(type)) next.delete(type)
    else next.add(type)
    return next
  })
}, [])
```

Filter visible nodes/links based on hiddenTypes:
```typescript
const visibleNodes = useMemo(() => {
  if (hiddenTypes.size === 0) return positionedNodes
  // Find all entity IDs that should be hidden
  const hiddenEntityIds = new Set(
    positionedNodes.filter(n => n.isEntity && n.entityType && hiddenTypes.has(n.entityType)).map(n => n.id)
  )
  // Find persona IDs linked ONLY to hidden entities
  const personaHiddenLinks = new Map<string, number>()
  const personaVisibleLinks = new Map<string, number>()
  positionedLinks.forEach(link => {
    if (link.type !== 'persona_entity') return
    const src = typeof link.source === 'string' ? link.source : link.source.id
    const tgt = typeof link.target === 'string' ? link.target : link.target.id
    const personaId = hiddenEntityIds.has(src) ? tgt : hiddenEntityIds.has(tgt) ? src : null
    if (personaId) {
      personaHiddenLinks.set(personaId, (personaHiddenLinks.get(personaId) ?? 0) + 1)
    }
    const isVisible = !hiddenEntityIds.has(src) && !hiddenEntityIds.has(tgt)
    if (isVisible) {
      const nonEntityId = positionedNodes.find(n => n.id === src)?.isEntity ? tgt : src
      personaVisibleLinks.set(nonEntityId, (personaVisibleLinks.get(nonEntityId) ?? 0) + 1)
    }
  })
  return positionedNodes.filter(n => {
    if (n.isEntity) {
      return !n.entityType || !hiddenTypes.has(n.entityType)
    }
    // Persona: hide if linked only to hidden entities
    const hidden = personaHiddenLinks.get(n.id) ?? 0
    const visible = personaVisibleLinks.get(n.id) ?? 0
    return visible > 0 || hidden === 0
  })
}, [positionedNodes, positionedLinks, hiddenTypes])

const visibleNodeIds = useMemo(() => new Set(visibleNodes.map(n => n.id)), [visibleNodes])

const visibleLinks = useMemo(() => {
  if (hiddenTypes.size === 0) return positionedLinks
  return positionedLinks.filter(link => {
    const src = typeof link.source === 'string' ? link.source : link.source.id
    const tgt = typeof link.target === 'string' ? link.target : link.target.id
    return visibleNodeIds.has(src) && visibleNodeIds.has(tgt)
  })
}, [positionedLinks, visibleNodeIds, hiddenTypes])
```

Replace `positionedNodes` and `positionedLinks` with `visibleNodes` and `visibleLinks` in the `<ClusterHulls>`, `<EdgesLayer>`, and `<NodesLayer>` props.

Add `<EntityLegend>` inside the outer div:
```tsx
<EntityLegend
  nodes={positionedNodes}
  hiddenTypes={hiddenTypes}
  onToggle={handleToggleType}
/>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/simulation/graph/controls/EntityLegend.tsx frontend/src/components/simulation/graph/NetworkGraph.tsx
git commit -m "feat(graph): add EntityLegend with entity type filters"
```

---

## Task 13: MiniMap Component

**Files:**
- Create: `frontend/src/components/simulation/graph/controls/MiniMap.tsx`

- [ ] **Step 1: Create component**

Create `frontend/src/components/simulation/graph/controls/MiniMap.tsx`:
```typescript
import { useMemo, useRef, useCallback } from 'react'
import type { SimNode } from '../types'
import { entityTypeColor, sentimentColor, THEME } from '../utils/colors'

interface MiniMapProps {
  nodes: SimNode[]
  viewport: { x: number; y: number; width: number; height: number }
  onViewportChange: (cx: number, cy: number) => void
}

const MINIMAP_WIDTH = 180
const MINIMAP_HEIGHT = 120

export function MiniMap({ nodes, viewport, onViewportChange }: MiniMapProps) {
  const svgRef = useRef<SVGSVGElement>(null)

  const bounds = useMemo(() => {
    if (nodes.length === 0) {
      return { minX: 0, maxX: MINIMAP_WIDTH, minY: 0, maxY: MINIMAP_HEIGHT }
    }
    const xs = nodes.map(n => n.x ?? 0)
    const ys = nodes.map(n => n.y ?? 0)
    return {
      minX: Math.min(...xs) - 50,
      maxX: Math.max(...xs) + 50,
      minY: Math.min(...ys) - 50,
      maxY: Math.max(...ys) + 50,
    }
  }, [nodes])

  const worldWidth = bounds.maxX - bounds.minX
  const worldHeight = bounds.maxY - bounds.minY
  const scaleX = MINIMAP_WIDTH / worldWidth
  const scaleY = MINIMAP_HEIGHT / worldHeight
  const scale = Math.min(scaleX, scaleY)

  const toMini = (x: number, y: number): [number, number] => [
    (x - bounds.minX) * scale,
    (y - bounds.minY) * scale,
  ]

  const handleClick = useCallback(
    (e: React.MouseEvent<SVGSVGElement>) => {
      if (!svgRef.current) return
      const rect = svgRef.current.getBoundingClientRect()
      const miniX = e.clientX - rect.left
      const miniY = e.clientY - rect.top
      const worldX = miniX / scale + bounds.minX
      const worldY = miniY / scale + bounds.minY
      onViewportChange(worldX, worldY)
    },
    [scale, bounds, onViewportChange],
  )

  return (
    <div
      className="absolute bottom-4 right-4 rounded-lg overflow-hidden"
      style={{
        backgroundColor: THEME.white,
        border: `1px solid ${THEME.border}`,
        boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
      }}
      onClick={e => e.stopPropagation()}
    >
      <svg
        ref={svgRef}
        width={MINIMAP_WIDTH}
        height={MINIMAP_HEIGHT}
        onClick={handleClick}
        style={{ cursor: 'pointer', backgroundColor: THEME.bg }}
      >
        {/* Dots for personas (small) */}
        {nodes.filter(n => !n.isEntity).map(n => {
          if (n.x == null || n.y == null) return null
          const [mx, my] = toMini(n.x, n.y)
          return (
            <circle
              key={n.id}
              cx={mx}
              cy={my}
              r={1}
              fill={sentimentColor(n.sentiment)}
              opacity={0.6}
            />
          )
        })}
        {/* Entities (larger colored dots) */}
        {nodes.filter(n => n.isEntity).map(n => {
          if (n.x == null || n.y == null) return null
          const [mx, my] = toMini(n.x, n.y)
          return (
            <circle
              key={n.id}
              cx={mx}
              cy={my}
              r={3}
              fill={entityTypeColor(n.entityType)}
              stroke={THEME.white}
              strokeWidth={0.5}
            />
          )
        })}
        {/* Viewport rectangle */}
        <rect
          x={(viewport.x - bounds.minX) * scale}
          y={(viewport.y - bounds.minY) * scale}
          width={viewport.width * scale}
          height={viewport.height * scale}
          fill="none"
          stroke={THEME.accent}
          strokeWidth={1.5}
        />
      </svg>
    </div>
  )
}
```

- [ ] **Step 2: Wire up MiniMap in NetworkGraph**

Edit `frontend/src/components/simulation/graph/NetworkGraph.tsx`. Add import:
```typescript
import { MiniMap } from './controls/MiniMap'
```

Add viewport calculation from current transform:
```typescript
const viewport = useMemo(() => {
  const k = transform.k
  return {
    x: -transform.x / k,
    y: -transform.y / k,
    width: width / k,
    height: height / k,
  }
}, [transform, width, height])

const handleMiniMapChange = useCallback(
  (worldX: number, worldY: number) => {
    if (!svgRef.current || !zoomBehaviorRef.current) return
    const scale = transform.k
    const tx = width / 2 - worldX * scale
    const ty = height / 2 - worldY * scale
    select(svgRef.current).transition().duration(200).call(
      zoomBehaviorRef.current.transform,
      zoomIdentity.translate(tx, ty).scale(scale),
    )
  },
  [transform.k, width, height],
)
```

Add `<MiniMap>` inside the outer div:
```tsx
<MiniMap
  nodes={visibleNodes}
  viewport={viewport}
  onViewportChange={handleMiniMapChange}
/>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/simulation/graph/controls/MiniMap.tsx frontend/src/components/simulation/graph/NetworkGraph.tsx
git commit -m "feat(graph): add MiniMap with viewport tracking and click-to-navigate"
```

---

## Task 14: PersonaDetailPanel

**Files:**
- Create: `frontend/src/components/simulation/graph/panel/PersonaDetailPanel.tsx`

- [ ] **Step 1: Create component**

Create `frontend/src/components/simulation/graph/panel/PersonaDetailPanel.tsx`:
```typescript
import type { SimNode, SimLink } from '../types'
import { entityTypeColor, entityTypeLabel, sentimentColor, personaSourceColor, THEME } from '../utils/colors'

interface PersonaDetailPanelProps {
  node: SimNode | null
  allNodes: SimNode[]
  allLinks: SimLink[]
  onClose: () => void
}

export function PersonaDetailPanel({ node, allNodes, allLinks, onClose }: PersonaDetailPanelProps) {
  if (!node) return null

  const nodeById = new Map(allNodes.map(n => [n.id, n]))

  // Compute 1-hop neighbors
  const neighbors = new Map<string, { node: SimNode; label?: string }>()
  allLinks.forEach(link => {
    const src = typeof link.source === 'string' ? link.source : link.source.id
    const tgt = typeof link.target === 'string' ? link.target : link.target.id
    if (src === node.id) {
      const neighbor = nodeById.get(tgt)
      if (neighbor) neighbors.set(tgt, { node: neighbor, label: link.label })
    } else if (tgt === node.id) {
      const neighbor = nodeById.get(src)
      if (neighbor) neighbors.set(src, { node: neighbor, label: link.label })
    }
  })

  const sourceColor = personaSourceColor(node.personaSource)
  const nodeColor = node.isEntity
    ? entityTypeColor(node.entityType)
    : sentimentColor(node.sentiment)

  const sourceLabel =
    node.personaSource === 'real_enriched'
      ? 'REAL'
      : node.personaSource === 'real_minimal'
      ? 'REAL'
      : node.personaSource === 'role_based'
      ? 'ROLLE'
      : null

  return (
    <div
      className="absolute top-0 left-0 h-full flex flex-col overflow-hidden"
      style={{
        width: 320,
        backgroundColor: THEME.white,
        borderRight: `1px solid ${THEME.border}`,
        boxShadow: '4px 0 16px rgba(0,0,0,0.04)',
        animation: 'slideInLeft 0.25s ease-out',
      }}
      onClick={e => e.stopPropagation()}
    >
      <style>{`
        @keyframes slideInLeft {
          from { transform: translateX(-100%); }
          to { transform: translateX(0); }
        }
      `}</style>

      {/* Header */}
      <div
        className="p-4 flex items-start gap-3 border-b"
        style={{ borderColor: THEME.border }}
      >
        <div
          className="w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0 text-white font-bold text-sm"
          style={{ backgroundColor: nodeColor }}
        >
          {getInitials(node.label)}
        </div>
        <div className="flex-1 min-w-0">
          <div
            className="font-semibold text-base leading-tight"
            style={{ color: THEME.text }}
          >
            {node.label}
          </div>
          {(node.occupation || node.subType) && (
            <div className="text-xs mt-0.5" style={{ color: THEME.textMuted }}>
              {node.occupation || node.subType}
            </div>
          )}
          <div className="flex items-center gap-1.5 mt-1.5">
            {sourceLabel && (
              <span
                className="text-[9px] px-1.5 py-0.5 rounded font-bold"
                style={{
                  backgroundColor: `${sourceColor}20`,
                  color: sourceColor ?? THEME.textMuted,
                  border: `1px solid ${sourceColor}40`,
                }}
              >
                {sourceLabel}
              </span>
            )}
            {node.isEntity && (
              <span
                className="text-[9px] px-1.5 py-0.5 rounded"
                style={{ backgroundColor: THEME.borderLight, color: THEME.textMuted }}
              >
                {entityTypeLabel(node.entityType)}
              </span>
            )}
          </div>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="w-6 h-6 flex items-center justify-center rounded-full text-sm"
          style={{ color: THEME.textMuted, backgroundColor: THEME.borderLight }}
          aria-label="Schliessen"
        >
          ×
        </button>
      </div>

      {/* Body (scrollable) */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Sentiment */}
        {!node.isEntity && (
          <Section title="Stimmung">
            <div className="flex items-center gap-3">
              <div
                className="flex-1 h-2 rounded-full overflow-hidden"
                style={{ backgroundColor: THEME.borderLight }}
              >
                <div
                  className="h-full transition-all"
                  style={{
                    width: `${((node.sentiment + 1) / 2) * 100}%`,
                    backgroundColor: sentimentColor(node.sentiment),
                  }}
                />
              </div>
              <span
                className="text-xs font-mono tabular-nums"
                style={{ color: sentimentColor(node.sentiment) }}
              >
                {node.sentiment > 0 ? '+' : ''}{node.sentiment.toFixed(2)}
              </span>
            </div>
          </Section>
        )}

        {/* Role */}
        {node.role && (
          <Section title="Rolle">
            <div className="text-sm" style={{ color: THEME.text }}>
              {node.role}
            </div>
          </Section>
        )}

        {/* Follower count */}
        {!node.isEntity && (
          <Section title="Follower">
            <div className="text-sm font-semibold" style={{ color: THEME.text }}>
              {node.followerCount}
            </div>
          </Section>
        )}

        {/* Relationships */}
        {neighbors.size > 0 && (
          <Section title={`Beziehungen (${neighbors.size})`}>
            <div className="space-y-1.5">
              {Array.from(neighbors.values()).slice(0, 10).map(({ node: nb, label }) => (
                <div
                  key={nb.id}
                  className="flex items-center gap-2 text-xs p-2 rounded"
                  style={{ backgroundColor: THEME.borderLight }}
                >
                  <div
                    className="w-2 h-2 rounded-full flex-shrink-0"
                    style={{
                      backgroundColor: nb.isEntity
                        ? entityTypeColor(nb.entityType)
                        : sentimentColor(nb.sentiment),
                    }}
                  />
                  <div className="flex-1 min-w-0">
                    <div className="font-medium truncate" style={{ color: THEME.text }}>
                      {nb.label}
                    </div>
                    {label && (
                      <div className="text-[10px] truncate" style={{ color: THEME.textMuted }}>
                        {label}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {neighbors.size > 10 && (
                <div className="text-[10px] text-center" style={{ color: THEME.textMuted }}>
                  +{neighbors.size - 10} weitere
                </div>
              )}
            </div>
          </Section>
        )}
      </div>
    </div>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <div
        className="text-[10px] font-bold uppercase tracking-wider mb-2"
        style={{ color: THEME.textMuted }}
      >
        {title}
      </div>
      {children}
    </div>
  )
}

function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/)
  if (parts.length === 0) return '?'
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/simulation/graph/panel/PersonaDetailPanel.tsx
git commit -m "feat(graph): add PersonaDetailPanel with ego-network and sentiment"
```

---

## Task 15: Integrate New Graph into SimulationPage

**Files:**
- Modify: `frontend/src/pages/SimulationPage.tsx`

- [ ] **Step 1: Read current SimulationPage to understand structure**

Run: `cat frontend/src/pages/SimulationPage.tsx | head -60`
Expected: See current imports and state setup.

- [ ] **Step 2: Replace NetworkGraph import and usage**

Edit `frontend/src/pages/SimulationPage.tsx`:

Find:
```typescript
import { NetworkGraph, NodeTooltip } from '@/components/simulation/NetworkGraph'
```

Replace with:
```typescript
import { NetworkGraph } from '@/components/simulation/graph/NetworkGraph'
import { PersonaDetailPanel } from '@/components/simulation/graph/panel/PersonaDetailPanel'
import type { SimNode, SimLink } from '@/components/simulation/graph/types'
import { streamNodeToSimNode, streamLinkToSimLink } from '@/components/simulation/graph/types'
```

- [ ] **Step 3: Replace graph state and hover handlers**

Find existing graph-related state:
```typescript
const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null)
const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 })
```

Replace with:
```typescript
const [selectedNode, setSelectedNode] = useState<SimNode | null>(null)

const simNodes = useMemo(
  () => stream.nodes.map(streamNodeToSimNode),
  [stream.nodes],
)
const simLinks = useMemo(
  () => stream.links.map(streamLinkToSimLink),
  [stream.links],
)
```

Add `useMemo` to the React imports at the top.

Remove the `handleNodeHover`, `handleNodeClick`, tooltip mousemove effect, and `<NodeTooltip>` component — they're handled internally now.

- [ ] **Step 4: Replace graph rendering**

Find the old `<NetworkGraph>` usage and replace with:
```tsx
<NetworkGraph
  nodes={stream.nodes}
  links={stream.links}
  activeNodeIds={stream.activeNodeIds}
  width={graphSize.width}
  height={graphSize.height}
  onNodeSelect={setSelectedNode}
/>
{selectedNode && (
  <PersonaDetailPanel
    node={selectedNode}
    allNodes={simNodes}
    allLinks={simLinks}
    onClose={() => setSelectedNode(null)}
  />
)}
```

- [ ] **Step 5: Verify build**

Run: `cd frontend && npm run build`
Expected: TypeScript compiles successfully.

- [ ] **Step 6: Start dev server and verify graph renders**

Run: `preview_start` with name "frontend" (via the preview tool).

Open the simulation flow: login → create simulation → wait until entities appear.
Expected: Light-theme graph renders with entities as diamonds/circles, personas in orbit, cluster hulls around them, zoom/search/legend/minimap controls visible.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/pages/SimulationPage.tsx
git commit -m "feat(simulation): integrate new graph + persona detail panel"
```

---

## Task 16: Light-Theme Migration for SimulationPage

**Files:**
- Modify: `frontend/src/pages/SimulationPage.tsx`

- [ ] **Step 1: Replace dark background colors**

In `frontend/src/pages/SimulationPage.tsx`, change the outer container background and layout colors from dark to light.

Find the main container `className` with `bg-gray-950 text-white` and replace with `bg-gray-50 text-gray-900`.

Update top bar from `bg-gray-900/80 border-b border-gray-800` to `bg-white border-b border-gray-200`.

Update right panel containers from `bg-gray-950 border-l border-gray-800` to `bg-white border-l border-gray-200`.

Update text colors:
- `text-white` → `text-gray-900`
- `text-gray-400` → `text-gray-600`
- `text-gray-500` → `text-gray-500` (keep)
- `text-gray-600` → `text-gray-500`

- [ ] **Step 2: Update feed event styling**

In `frontend/src/components/simulation/LiveFeed.tsx`, change:
- `bg-gray-800` / `bg-gray-900` → `bg-gray-100`
- `text-white` → `text-gray-900`
- `text-gray-400` → `text-gray-600`
- `border-gray-800` → `border-gray-200`

- [ ] **Step 3: Update StatsPanel styling**

In `frontend/src/components/simulation/StatsPanel.tsx`, similar dark → light replacements.

- [ ] **Step 4: Update PhaseTimeline styling**

In `frontend/src/components/simulation/PhaseTimeline.tsx`:
- `bg-gray-800/50` → `bg-gray-100`
- `text-gray-600` (inactive pills) → `text-gray-400`
- `text-white` → `text-gray-900`

- [ ] **Step 5: Verify in browser**

Restart dev server, navigate to simulation page.
Expected: Entire simulation view is light-themed, no dark patches remain.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/SimulationPage.tsx frontend/src/components/simulation/LiveFeed.tsx frontend/src/components/simulation/StatsPanel.tsx frontend/src/components/simulation/PhaseTimeline.tsx
git commit -m "style(simulation): migrate simulation views to light theme"
```

---

## Task 17: Light-Theme Migration for NewSimulationPage

**Files:**
- Modify: `frontend/src/pages/NewSimulationPage.tsx`

- [ ] **Step 1: Verify current state**

Run: `grep -n 'bg-gray-50\|bg-white\|text-gray-900' frontend/src/pages/NewSimulationPage.tsx | head`
Expected: NewSimulationPage already uses light colors (`bg-gray-50`, `bg-white`).

- [ ] **Step 2: Ensure consistency with new theme tokens**

If the file already uses light theme, skip to commit. Otherwise:
- Replace any remaining `bg-gray-950` / `bg-gray-900` with `bg-white` / `bg-gray-50`
- Replace `text-white` with `text-gray-900`
- Ensure borders use `border-gray-200`

- [ ] **Step 3: Commit (only if changes made)**

```bash
git add frontend/src/pages/NewSimulationPage.tsx
git commit -m "style(simulation): verify NewSimulationPage light theme consistency"
```

---

## Task 18: Remove Old NetworkGraph Component and Dependency

**Files:**
- Delete: `frontend/src/components/simulation/NetworkGraph.tsx`
- Modify: `frontend/package.json`

- [ ] **Step 1: Check for remaining references to old NetworkGraph**

Run: `grep -r "from '@/components/simulation/NetworkGraph'" frontend/src/`
Expected: No results (all imports moved to `graph/NetworkGraph`).

If any results: update those imports to the new path before proceeding.

- [ ] **Step 2: Delete old file**

```bash
rm frontend/src/components/simulation/NetworkGraph.tsx
```

- [ ] **Step 3: Remove react-force-graph-2d dependency**

Run: `cd frontend && npm uninstall react-force-graph-2d`
Expected: Package removed from package.json, no errors.

- [ ] **Step 4: Run build to verify nothing broke**

Run: `cd frontend && npm run build`
Expected: Build succeeds.

- [ ] **Step 5: Run tests to verify nothing broke**

Run: `cd frontend && npm run test:run`
Expected: All tests pass.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "chore: remove old Canvas NetworkGraph and react-force-graph-2d"
```

---

## Task 19: Final Verification in Browser

**Files:** none (manual testing)

- [ ] **Step 1: Start backend**

Run: `preview_start` with name "backend" via the preview tool.
Expected: Backend server running on port 8000.

- [ ] **Step 2: Start frontend**

Run: `preview_start` with name "frontend" via the preview tool.
Expected: Frontend dev server running on port 5173.

- [ ] **Step 3: Full flow test**

Navigate to http://localhost:5173, log in, create new simulation with Novartis scenario, wait for entities + enrichment + orchestrator + generation.

Verify checklist:
- [ ] Light theme throughout (no dark patches)
- [ ] Entity-Orbital layout: entities fixed in center, personas orbiting
- [ ] Cluster hulls visible around persona groups
- [ ] Edge labels on entity-entity edges always visible
- [ ] Semantic zoom: zoom out → aggregated entity bubbles with counts + sentiment bars
- [ ] Semantic zoom: zoom in → full persona labels
- [ ] Search: type "Novartis" → node highlights and pans to it
- [ ] Filter: click "Medium" in legend → media entities hidden
- [ ] Mini-map: shows overview, viewport rectangle visible, click navigates
- [ ] Zoom controls: +/-/fit/reset all work
- [ ] Hover focus: hover a node → 1-hop neighbors highlighted, rest dimmed
- [ ] Click: node opens left detail panel with ego-network and relationships
- [ ] Close detail panel: × button or click empty canvas
- [ ] Activity: during simulation, active personas pulse

- [ ] **Step 4: Commit final verification summary**

```bash
git add docs/superpowers/plans/
git commit --allow-empty -m "chore: visualization redesign verified end-to-end"
```

---

## Self-Review Checklist

Before marking this plan complete, verify:

**Spec Coverage:**
- [x] Canvas → SVG migration (Task 0, 5-9)
- [x] Entity-Orbital layout with forceRadial (Task 5)
- [x] Convex hulls (Task 8)
- [x] Semantic zoom with 4 levels (Task 6-7, 9)
- [x] Light theme (Task 16-17)
- [x] Color palette (Task 2)
- [x] Edge labels with backgrounds (Task 7)
- [x] Multi-edge curves (Task 7)
- [x] Zoom controls (Task 10)
- [x] Search (Task 11)
- [x] Entity legend + filters (Task 12)
- [x] Mini-map (Task 13)
- [x] Focus mode / hover (Task 9 — integrated into NetworkGraph)
- [x] PersonaDetailPanel (Task 14)
- [x] Pulse animation (Task 6 — in PersonaNode)
- [x] Integration (Task 15)
- [x] Cleanup (Task 18)
- [x] Verification (Task 19)

**Placeholder Scan:** None found. All code blocks are complete.

**Type Consistency:** All files use `SimNode`, `SimLink`, `ZoomLevel` from `types.ts` consistently.

**Ambiguity Check:** Each step specifies exact file paths, exact commands, and complete code.

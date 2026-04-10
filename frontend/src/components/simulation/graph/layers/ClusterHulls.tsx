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

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

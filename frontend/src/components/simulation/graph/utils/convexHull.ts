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

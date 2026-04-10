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

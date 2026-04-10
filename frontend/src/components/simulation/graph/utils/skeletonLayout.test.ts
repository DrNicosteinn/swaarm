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

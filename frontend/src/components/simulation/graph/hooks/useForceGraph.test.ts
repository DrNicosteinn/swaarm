import { describe, it, expect } from 'vitest'
import { renderHook } from '@testing-library/react'
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

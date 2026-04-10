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

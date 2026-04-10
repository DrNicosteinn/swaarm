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

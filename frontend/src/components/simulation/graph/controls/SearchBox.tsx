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

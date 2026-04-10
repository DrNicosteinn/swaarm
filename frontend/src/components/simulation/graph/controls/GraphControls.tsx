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

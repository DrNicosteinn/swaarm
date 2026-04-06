import type { AgentActionEvent } from '@/lib/ws-events'

interface LiveFeedProps {
  actions: AgentActionEvent[]
}

const actionLabels: Record<string, string> = {
  create_post: 'hat gepostet',
  like_post: 'hat geliked',
  comment: 'hat kommentiert',
  repost: 'hat geteilt',
  follow_user: 'folgt jetzt',
  do_nothing: 'beobachtet',
}

function sentimentColor(s: number): string {
  if (s > 0.2) return 'text-green-600'
  if (s < -0.2) return 'text-red-600'
  return 'text-gray-500'
}

function sentimentBorder(s: number): string {
  if (s > 0.2) return 'border-l-green-400'
  if (s < -0.2) return 'border-l-red-400'
  return 'border-l-gray-300'
}

export function LiveFeed({ actions }: LiveFeedProps) {
  const displayActions = actions
    .filter((a) => a.action_type !== 'do_nothing')
    .slice(-50)
    .reverse()

  if (displayActions.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400 text-sm">
        Warte auf Aktivitaet...
      </div>
    )
  }

  return (
    <div className="overflow-y-auto h-full space-y-2 p-3">
      {displayActions.map((action, i) => (
        <div
          key={`${action.agent_id}-${i}`}
          className={`border-l-4 ${sentimentBorder(action.sentiment)} bg-white rounded-r-lg p-3 shadow-sm text-sm`}
        >
          <div className="flex items-center gap-2 mb-1">
            <span className="font-medium text-gray-900">{action.agent_name}</span>
            <span className="text-gray-400 text-xs">
              {actionLabels[action.action_type] || action.action_type}
            </span>
            <span className={`ml-auto text-xs ${sentimentColor(action.sentiment)}`}>
              {action.sentiment > 0 ? '+' : ''}
              {action.sentiment.toFixed(1)}
            </span>
          </div>
          {action.content && (
            <p className="text-gray-700 text-sm leading-relaxed">
              {action.content.slice(0, 280)}
            </p>
          )}
        </div>
      ))}
    </div>
  )
}

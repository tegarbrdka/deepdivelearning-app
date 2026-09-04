import { useState } from 'react'

/**
 * RecommendationBox - Grouped, expandable recommendations by priority
 * Requirements: 8.1, 8.6
 *
 * recommendation shape: { priority: 'high'|'medium'|'low', category, issue, suggestion }
 */
const PRIORITY_CONFIG = {
  high:   { emoji: '🔴', label: 'Prioritas Tinggi', cls: 'text-red-400',   border: 'border-red-500/30',   bg: 'bg-red-500/10' },
  medium: { emoji: '🟡', label: 'Prioritas Sedang', cls: 'text-amber-400', border: 'border-amber-500/30', bg: 'bg-amber-500/10' },
  low:    { emoji: '🔵', label: 'Prioritas Rendah', cls: 'text-blue-400',  border: 'border-blue-500/30',  bg: 'bg-blue-500/10' },
}

function RecommendationItem({ rec, config }) {
  const [open, setOpen] = useState(false)

  return (
    <div className={`rounded-xl border ${config.border} overflow-hidden`}>
      {/* Header — always visible */}
      <button
        onClick={() => setOpen(o => !o)}
        className={`w-full flex items-start gap-3 p-4 text-left ${config.bg} hover:brightness-110 transition-all`}
      >
        <span className="text-base flex-shrink-0 mt-0.5">{config.emoji}</span>
        <div className="flex-1 min-w-0">
          <p className={`text-xs font-bold uppercase tracking-wide ${config.cls}`}>{rec.category}</p>
          <p className="text-sm text-slate-600 mt-0.5 leading-snug">{rec.issue}</p>
        </div>
        <svg
          width="16" height="16" viewBox="0 0 24 24" fill="none"
          stroke="#64748b" strokeWidth="2"
          className={`flex-shrink-0 mt-1 transition-transform ${open ? 'rotate-180' : ''}`}
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {/* Suggestion — expandable */}
      {open && (
        <div className="px-4 pb-4 pt-2 bg-slate-50">
          <p className="text-xs text-slate-500 leading-relaxed whitespace-pre-line">{rec.suggestion}</p>
        </div>
      )}
    </div>
  )
}

export default function RecommendationBox({ recommendations = [] }) {
  if (!recommendations.length) return null

  // Group by priority
  const grouped = { high: [], medium: [], low: [] }
  recommendations.forEach(r => {
    if (grouped[r.priority]) grouped[r.priority].push(r)
  })

  return (
    <div className="space-y-4">
      {['high', 'medium', 'low'].map(priority => {
        const items = grouped[priority]
        if (!items.length) return null
        const config = PRIORITY_CONFIG[priority]

        return (
          <div key={priority}>
            <div className="flex items-center gap-2 mb-2">
              <span>{config.emoji}</span>
              <span className={`text-xs font-bold uppercase tracking-wide ${config.cls}`}>
                {config.label}
              </span>
              <span className="text-xs text-slate-500">({items.length})</span>
            </div>
            <div className="space-y-2">
              {items.map((rec, i) => (
                <RecommendationItem key={i} rec={rec} config={config} />
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}

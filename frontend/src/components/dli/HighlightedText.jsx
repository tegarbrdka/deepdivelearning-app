import DOMPurify from 'dompurify'

/**
 * HighlightedText - Renders color-coded RPP text with legend and stats
 * Requirements: 6.1, 6.6, 7.1, 7.2
 *
 * Expects CSS classes: highlight-green, highlight-red, highlight-blue, highlight-yellow
 * defined in index.css
 */
const LEGEND = [
  { color: 'green', emoji: '🟢', label: 'Deep Learning', cls: 'text-teal-400' },
  { color: 'red',   emoji: '🔴', label: 'Surface Learning', cls: 'text-red-400' },
  { color: 'blue',  emoji: '🔵', label: 'Digital', cls: 'text-blue-400' },
  { color: 'yellow',emoji: '🟡', label: 'Medium', cls: 'text-amber-400' },
]

export default function HighlightedText({ html = '', statistics = {}, keywordsFound = {} }) {
  // Sanitize HTML to prevent XSS
  const safeHtml = DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['span', 'p', 'br', 'div'],
    ALLOWED_ATTR: ['class'],
  })

  return (
    <div className="space-y-4">
      {/* Legend */}
      <div className="flex flex-wrap gap-3">
        {LEGEND.map(({ color, emoji, label, cls }) => (
          <div key={color} className="flex items-center gap-1.5">
            <span>{emoji}</span>
            <span className={`text-xs font-medium ${cls}`}>{label}</span>
            {statistics[color] !== undefined && (
              <span className="text-xs text-slate-500">({statistics[color]})</span>
            )}
          </div>
        ))}
      </div>

      {/* Keyword stats chips */}
      {Object.values(statistics).some(v => v > 0) && (
        <div className="flex flex-wrap gap-2">
          {LEGEND.map(({ color, label, cls }) =>
            statistics[color] > 0 ? (
              <span
                key={color}
                className={`text-xs px-2.5 py-1 rounded-full bg-slate-50 border border-slate-300 ${cls}`}
              >
                {statistics[color]} kata {label.toLowerCase()}
              </span>
            ) : null
          )}
        </div>
      )}

      {/* Highlighted text */}
      <div
        className="text-sm text-slate-600 leading-relaxed whitespace-pre-wrap p-4 rounded-xl bg-slate-50 border border-slate-200 max-h-[600px] overflow-y-auto"
        // eslint-disable-next-line react/no-danger
        dangerouslySetInnerHTML={{ __html: safeHtml }}
      />
    </div>
  )
}

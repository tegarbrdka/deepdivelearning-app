/**
 * AlertCard - Displays a single DLI alert with severity styling
 * Requirements: 5.3, 5.4
 *
 * alert shape: { aspect, score, level: 'critical'|'warning', message }
 */
const ASPECT_NAMES = {
  mindful: 'Mindful',
  meaningful: 'Meaningful',
  joyful: 'Joyful',
  pedagogis: 'Pedagogis',
  digital: 'Akselerasi Digital',
}

export default function AlertCard({ alert }) {
  const isCritical = alert.level === 'critical'

  return (
    <div
      className={`flex items-start gap-3 p-4 rounded-xl border ${
        isCritical
          ? 'bg-red-500/10 border-red-500/30'
          : 'bg-amber-500/10 border-amber-500/30'
      }`}
    >
      {/* Icon */}
      <span className="text-lg flex-shrink-0 mt-0.5">
        {isCritical ? '🔴' : '⚠️'}
      </span>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span
            className={`text-sm font-semibold ${
              isCritical ? 'text-red-700 dark:text-red-300' : 'text-amber-800 dark:text-amber-300'
            }`}
          >
            {ASPECT_NAMES[alert.aspect] ?? alert.aspect}
          </span>
          <span
            className={`text-xs px-2 py-0.5 rounded-full font-mono ${
              isCritical
                ? 'bg-red-500/20 text-red-700 dark:text-red-400'
                : 'bg-amber-500/20 text-amber-800 dark:text-amber-400'
            }`}
          >
            {alert.score?.toFixed(1)}%
          </span>
          <span
            className={`text-xs px-2 py-0.5 rounded-full uppercase font-bold tracking-wide ${
              isCritical
                ? 'bg-red-500/20 text-red-700 dark:text-red-400'
                : 'bg-amber-500/20 text-amber-800 dark:text-amber-400'
            }`}
          >
            {isCritical ? 'Kritis' : 'Peringatan'}
          </span>
        </div>
        <p
          className={`text-xs mt-1.5 leading-relaxed ${
            isCritical ? 'text-red-600 dark:text-red-200/70' : 'text-amber-700 dark:text-amber-200/70'
          }`}
        >
          {alert.message}
        </p>
      </div>
    </div>
  )
}

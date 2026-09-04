import { RadialBarChart, RadialBar, ResponsiveContainer } from 'recharts'

/**
 * GaugeChart - Circular gauge for DLI score display
 * Requirements: 3.1, 3.2, 3.3
 *
 * Color coding:
 *   red    (<40%)  → Perlu Revisi Besar
 *   yellow (40-70%) → Perlu Perbaikan
 *   green  (≥70%)  → Siap Implementasi
 */
function getGaugeColor(score) {
  if (score >= 70) return '#2dd4bf'   // teal/green
  if (score >= 40) return '#fbbf24'   // amber/yellow
  return '#f87171'                     // red
}

function getStatusLabel(score) {
  if (score >= 70) return 'Siap Implementasi'
  if (score >= 40) return 'Perlu Perbaikan'
  return 'Perlu Revisi Besar'
}

export default function GaugeChart({ score = 0, size = 200, showLabel = true }) {
  const color = getGaugeColor(score)
  const label = getStatusLabel(score)

  const data = [
    { value: score, fill: color },
    { value: 100 - score, fill: 'rgba(255,255,255,0.04)' },
  ]

  return (
    <div className="flex flex-col items-center gap-3">
      <div style={{ width: size, height: size }} className="relative">
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart
            cx="50%" cy="50%"
            innerRadius="68%" outerRadius="100%"
            startAngle={220} endAngle={-40}
            data={data}
            barSize={14}
          >
            <RadialBar
              dataKey="value"
              cornerRadius={7}
              background={{ fill: 'rgba(255,255,255,0.03)' }}
            />
          </RadialBarChart>
        </ResponsiveContainer>

        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-display text-3xl font-bold text-slate-900 leading-none">
            {score.toFixed(1)}
          </span>
          <span className="text-xs text-slate-500 mt-1">DLI Score</span>
        </div>
      </div>

      {showLabel && (
        <span
          className="text-sm font-semibold px-4 py-1.5 rounded-full border"
          style={{
            color,
            borderColor: `${color}40`,
            backgroundColor: `${color}15`,
          }}
        >
          {label}
        </span>
      )}
    </div>
  )
}

import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis,
  PolarRadiusAxis, ResponsiveContainer, Tooltip,
} from 'recharts'

/**
 * SpiderChart - Radar chart for 5-aspect DLI scores
 * Requirements: 4.1, 4.2, 4.3, 4.4
 */
const ASPECT_LABELS = {
  mindful: 'Mindful',
  meaningful: 'Meaningful',
  joyful: 'Joyful',
  pedagogis: 'Pedagogis',
  digital: 'Digital',
}

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null
  const { subject, value } = payload[0].payload
  return (
    <div className="bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs">
      <p className="text-slate-600 font-semibold">{subject}</p>
      <p className="text-teal-400 font-bold mt-0.5">{value.toFixed(1)}%</p>
    </div>
  )
}

export default function SpiderChart({ scores = {}, size = 300 }) {
  const data = Object.entries(ASPECT_LABELS).map(([key, label]) => ({
    subject: label,
    value: scores[key] ?? 0,
    fullMark: 100,
  }))

  return (
    <div style={{ width: size, height: size }}>
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data} margin={{ top: 10, right: 30, bottom: 10, left: 30 }}>
          <PolarGrid stroke="rgba(255,255,255,0.08)" />
          <PolarAngleAxis
            dataKey="subject"
            tick={{ fill: '#94a3b8', fontSize: 11, fontWeight: 500 }}
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 100]}
            tick={{ fill: '#475569', fontSize: 9 }}
            tickCount={5}
          />
          <Radar
            name="DLI"
            dataKey="value"
            stroke="#2dd4bf"
            fill="#2dd4bf"
            fillOpacity={0.18}
            strokeWidth={2}
          />
          <Tooltip content={<CustomTooltip />} />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  )
}

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer, Tooltip,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, LineChart, Line, Legend, Cell
} from 'recharts'
import api from '../../services/api'
import { useLang } from '../../contexts/LanguageContext'

const GRADE_CONFIG = {
  grade4: { label: 'Grade 4 (≥70%)', color: '#2dd4bf', bg: 'bg-teal-400/10', border: 'border-teal-400/30', text: 'text-teal-600' },
  grade3: { label: 'Grade 3 (55-70%)', color: '#60a5fa', bg: 'bg-blue-400/10', border: 'border-blue-400/30', text: 'text-blue-600' },
  grade2: { label: 'Grade 2 (40-55%)', color: '#fbbf24', bg: 'bg-amber-400/10', border: 'border-amber-400/30', text: 'text-amber-600' },
  grade1: { label: 'Grade 1 (<40%)', color: '#f87171', bg: 'bg-red-400/10', border: 'border-red-400/30', text: 'text-red-600' },
}

const ASPECT_COLORS = {
  mindful: '#a78bfa', meaningful: '#2dd4bf', joyful: '#fb923c', pedagogis: '#60a5fa', digital: '#34d399'
}

function StatCard({ label, value, sub, color = 'text-slate-900', delay = 0 }) {
  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay }} className="card p-5">
      <p className="text-slate-500 text-xs mb-1">{label}</p>
      <p className={`font-display text-3xl font-bold ${color}`}>{value}</p>
      {sub && <p className="text-slate-600 text-xs mt-0.5">{sub}</p>}
    </motion.div>
  )
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs shadow-xl">
      <p className="text-slate-500 mb-1">{label}</p>
      {payload.map(p => <p key={p.dataKey} style={{ color: p.color }}>{p.name}: {p.value?.toFixed(1)}%</p>)}
    </div>
  )
}

export default function DLIDashboard() {
  const { t } = useLang()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/admin/dli/dashboard')
      .then(r => setData(r.data))
      .catch(err => {
        console.error('DLI Dashboard error:', err.response?.data || err.message)
        setData(null)
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="space-y-4 max-w-6xl">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => <div key={i} className="card h-24 animate-pulse bg-slate-50" />)}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {[...Array(4)].map((_, i) => <div key={i} className="card h-64 animate-pulse bg-slate-50" />)}
      </div>
    </div>
  )

  if (!data || data.total === 0) return (
    <div className="max-w-6xl space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-slate-900">{t('dliDashboard.title')}</h1>
        <p className="text-slate-500 mt-1">{t('dliDashboard.subtitle')}</p>
      </div>
      <div className="card p-16 text-center">
        <div className="text-5xl mb-4">📊</div>
        <p className="text-slate-500">{t('dliDashboard.noData')}</p>
      </div>
    </div>
  )

  const gradeData = Object.entries(GRADE_CONFIG).map(([key, cfg]) => ({
    name: cfg.label,
    value: data.grade_distribution[key] || 0,
    color: cfg.color,
    pct: data.total > 0 ? Math.round((data.grade_distribution[key] / data.total) * 100) : 0,
  }))

  const aspectRadarData = Object.entries(data.aspect_averages).map(([aspect, avg]) => ({
    aspect: t(`dli.aspects.${aspect}`),
    score: avg,
  }))

  const aspectBarData = Object.entries(data.aspect_averages).map(([aspect, avg]) => ({
    name: t(`dli.aspects.${aspect}`),
    score: avg,
    color: ASPECT_COLORS[aspect],
  }))

  const trendData = data.recent_trend.map((d, i) => ({
    name: d.file.length > 12 ? d.file.slice(0, 12) + '…' : d.file,
    score: d.score,
    date: d.date,
  }))

  const scoreColor = data.avg_score >= 70 ? 'text-teal-600' : data.avg_score >= 55 ? 'text-blue-600' : data.avg_score >= 40 ? 'text-amber-600' : 'text-red-600'

  return (
    <div className="max-w-6xl space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-slate-900">{t('dliDashboard.title')}</h1>
        <p className="text-slate-500 mt-1">{t('dliDashboard.subtitle')}</p>
      </div>

      {/* Top stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label={t('dliDashboard.totalAnalyses')} value={data.total} color="text-slate-900" delay={0.05} />
        <StatCard label={t('dliDashboard.avgScore')} value={`${data.avg_score}%`} color={scoreColor} delay={0.1} />
        <StatCard
          label={t('dliDashboard.topGrade')}
          value={data.grade_distribution.grade4}
          sub={`${Math.round((data.grade_distribution.grade4 / data.total) * 100)}% Grade 4`}
          color="text-teal-600" delay={0.15}
        />
        <StatCard
          label={t('dliDashboard.needsWork')}
          value={data.grade_distribution.grade1 + data.grade_distribution.grade2}
          sub={`Grade 1 + 2`}
          color="text-amber-600" delay={0.2}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Grade distribution bar */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }} className="card p-6">
          <h3 className="font-display font-semibold text-slate-900 mb-4">{t('dliDashboard.gradeDistribution')}</h3>
          <div className="space-y-3">
            {gradeData.map(g => (
              <div key={g.name}>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-500">{g.name}</span>
                  <span className="font-mono font-semibold" style={{ color: g.color }}>{g.value} ({g.pct}%)</span>
                </div>
                <div className="h-2.5 bg-slate-50 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${g.pct}%` }}
                    transition={{ duration: 0.8, ease: 'easeOut', delay: 0.3 }}
                    className="h-full rounded-full"
                    style={{ backgroundColor: g.color }}
                  />
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Aspect radar */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="card p-6">
          <h3 className="font-display font-semibold text-slate-900 mb-2">{t('dliDashboard.aspectProfile')}</h3>
          <ResponsiveContainer width="100%" height={220}>
            <RadarChart data={aspectRadarData}>
              <PolarGrid stroke="#e2e8f0" />
              <PolarAngleAxis dataKey="aspect" tick={{ fill: '#64748b', fontSize: 10 }} />
              <Radar name="Avg Score" dataKey="score" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.25} />
              <Tooltip formatter={v => [`${v.toFixed(1)}%`]} contentStyle={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 12, fontSize: 12 }} />
            </RadarChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Aspect bar chart */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35 }} className="card p-6">
          <h3 className="font-display font-semibold text-slate-900 mb-4">{t('dliDashboard.aspectAverages')}</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={aspectBarData} barSize={28}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
              <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis domain={[0, 100]} tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="score" name="Avg Score" radius={[4, 4, 0, 0]}>
                {aspectBarData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Recent trend */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }} className="card p-6">
          <h3 className="font-display font-semibold text-slate-900 mb-4">{t('dliDashboard.recentTrend')}</h3>
          {trendData.length < 2 ? (
            <div className="h-[200px] flex items-center justify-center text-slate-600 text-sm">{t('dliDashboard.notEnoughData')}</div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 9 }} axisLine={false} tickLine={false} />
                <YAxis domain={[0, 100]} tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Line type="monotone" dataKey="score" name="DLI Score" stroke="#8b5cf6" dot={{ fill: '#8b5cf6', r: 3 }} strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </motion.div>
      </div>

      {/* Weakest & Strongest aspects */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.45 }} className="card p-5">
          <h3 className="font-display font-semibold text-slate-900 mb-3 flex items-center gap-2">
            <span className="text-lg">⚠️</span> {t('dliDashboard.weakestAspects')}
          </h3>
          <div className="space-y-2">
            {data.weakest_aspects.map((a, i) => (
              <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-red-500/10 border border-red-500/20">
                <span className="text-slate-600 text-sm capitalize">{t(`dli.aspects.${a.aspect}`)}</span>
                <span className="font-mono font-bold text-red-600">{a.avg}%</span>
              </div>
            ))}
          </div>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }} className="card p-5">
          <h3 className="font-display font-semibold text-slate-900 mb-3 flex items-center gap-2">
            <span className="text-lg">✅</span> {t('dliDashboard.strongestAspects')}
          </h3>
          <div className="space-y-2">
            {data.strongest_aspects.map((a, i) => (
              <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-teal-500/10 border border-teal-500/20">
                <span className="text-slate-600 text-sm capitalize">{t(`dli.aspects.${a.aspect}`)}</span>
                <span className="font-mono font-bold text-teal-600">{a.avg}%</span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  )
}

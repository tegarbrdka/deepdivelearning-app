import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import api from '../../services/api'
import { useLang } from '../../contexts/LanguageContext'

const ASPECTS = ['mindful', 'meaningful', 'joyful', 'pedagogis', 'digital']
const GRADES = ['grade4', 'grade3', 'grade2', 'grade1']
const GRADE_LABELS = { grade4: 'Grade 4', grade3: 'Grade 3', grade2: 'Grade 2', grade1: 'Grade 1' }
const GRADE_COLORS = { grade4: '#2dd4bf', grade3: '#60a5fa', grade2: '#fbbf24', grade1: '#f87171' }

function heatColor(score) {
  if (score >= 70) return 'bg-teal-500/30 text-teal-700'
  if (score >= 55) return 'bg-blue-500/30 text-blue-700'
  if (score >= 40) return 'bg-amber-500/30 text-amber-700'
  if (score > 0)   return 'bg-red-500/30 text-red-700'
  return 'bg-slate-50 text-slate-600'
}

export default function DLIAnalytics() {
  const { t } = useLang()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/admin/dli/analytics')
      .then(r => setData(r.data))
      .catch(err => {
        console.error('DLI Analytics error:', err.response?.data || err.message)
        setData({ heatmap: {}, keyword_effectiveness: [], grade_counts: {} })
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="space-y-4 max-w-6xl">
      {[...Array(3)].map((_, i) => <div key={i} className="card h-48 animate-pulse bg-slate-50" />)}
    </div>
  )

  if (!data || Object.keys(data.heatmap).length === 0) return (
    <div className="max-w-6xl space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-slate-900">{t('dliAnalytics.title')}</h1>
        <p className="text-slate-500 mt-1">{t('dliAnalytics.subtitle')}</p>
      </div>
      <div className="card p-16 text-center">
        <div className="text-5xl mb-4">🔬</div>
        <p className="text-slate-500">{t('dliAnalytics.noData')}</p>
      </div>
    </div>
  )

  const kwData = (data.keyword_effectiveness || []).slice(0, 15).map(k => ({
    name: k.keyword.length > 20 ? k.keyword.slice(0, 20) + '…' : k.keyword,
    count: k.count,
  }))

  return (
    <div className="max-w-6xl space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-slate-900">{t('dliAnalytics.title')}</h1>
        <p className="text-slate-500 mt-1">{t('dliAnalytics.subtitle')}</p>
      </div>

      {/* Heatmap */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="card p-6">
        <h3 className="font-display font-semibold text-slate-900 mb-1">{t('dliAnalytics.heatmapTitle')}</h3>
        <p className="text-slate-500 text-xs mb-4">{t('dliAnalytics.heatmapDesc')}</p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr>
                <th className="text-left py-2 pr-4 text-xs text-slate-500 uppercase w-24">Grade</th>
                {ASPECTS.map(a => (
                  <th key={a} className="text-center py-2 px-3 text-xs text-slate-500 uppercase capitalize">{t(`dli.aspects.${a}`)}</th>
                ))}
                <th className="text-center py-2 px-3 text-xs text-slate-500 uppercase">Count</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-navy-800">
              {GRADES.map(grade => {
                const row = data.heatmap[grade] || {}
                const count = data.grade_counts?.[grade] || 0
                return (
                  <tr key={grade}>
                    <td className="py-3 pr-4">
                      <span className="text-xs font-semibold px-2 py-1 rounded-full border"
                        style={{ color: GRADE_COLORS[grade], borderColor: GRADE_COLORS[grade] + '50', background: GRADE_COLORS[grade] + '15' }}>
                        {GRADE_LABELS[grade]}
                      </span>
                    </td>
                    {ASPECTS.map(a => (
                      <td key={a} className="py-3 px-3 text-center">
                        <span className={`inline-block px-3 py-1.5 rounded-lg text-xs font-mono font-bold ${heatColor(row[a] || 0)}`}>
                          {row[a] || 0}%
                        </span>
                      </td>
                    ))}
                    <td className="py-3 px-3 text-center text-slate-500 text-xs font-mono">{count}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
        {/* Legend */}
        <div className="flex gap-3 mt-4 flex-wrap">
          {[
            { label: '≥70%', cls: 'bg-teal-500/30 text-teal-700' },
            { label: '55-70%', cls: 'bg-blue-500/30 text-blue-700' },
            { label: '40-55%', cls: 'bg-amber-500/30 text-amber-700' },
            { label: '<40%', cls: 'bg-red-500/30 text-red-700' },
          ].map(l => (
            <span key={l.label} className={`text-xs px-2 py-1 rounded ${l.cls}`}>{l.label}</span>
          ))}
        </div>
      </motion.div>

      {/* Keyword effectiveness */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }} className="card p-6">
        <h3 className="font-display font-semibold text-slate-900 mb-1">{t('dliAnalytics.keywordTitle')}</h3>
        <p className="text-slate-500 text-xs mb-4">{t('dliAnalytics.keywordDesc')}</p>
        {kwData.length === 0 ? (
          <p className="text-slate-600 text-sm italic">{t('dliAnalytics.noKeywordData')}</p>
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={kwData} layout="vertical" barSize={14}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
              <XAxis type="number" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="name" tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} width={140} />
              <Tooltip
                contentStyle={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 12, fontSize: 12 }}
                formatter={v => [v, 'Frekuensi']}
              />
              <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                {kwData.map((_, i) => <Cell key={i} fill={`hsl(${160 + i * 8}, 60%, 55%)`} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </motion.div>
    </div>
  )
}

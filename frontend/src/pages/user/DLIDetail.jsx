import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import api from '../../services/api'
import GaugeChart from '../../components/dli/GaugeChart'
import { useLang } from '../../contexts/LanguageContext'

const ASPECT_CONFIG = {
  mindful:    { color: '#a78bfa', sub: { aktivasi_fokus: true, metakognisi: true, kesadaran_fisik: true } },
  meaningful: { color: '#2dd4bf', sub: { linking: true, realworld: true, asesmen: true } },
  joyful:     { color: '#fb923c', sub: { flow: true, kolaborasi: true } },
  pedagogis:  { color: '#60a5fa', sub: {} },
  digital:    { color: '#34d399', sub: {} },
}

function detectImbalances(scores, dliScore, t) {
  if (!scores) return []
  const notices = []
  const entries = Object.entries(scores)
  const maxAsp = entries.reduce((a, b) => b[1] > a[1] ? b : a)
  const minAsp = entries.reduce((a, b) => b[1] < a[1] ? b : a)
  const gap = maxAsp[1] - minAsp[1]

  if (dliScore >= 70) {
    const weakOnes = entries.filter(([, v]) => v < 70)
    if (weakOnes.length > 0)
      notices.push({
        type: 'warning',
        message: t('dliDetail.imbalance.grade4Weak'),
        detail: t('dliDetail.imbalance.grade4WeakDetail').replace('{aspects}', weakOnes.map(([k]) => t(`dli.aspects.${k}`)).join(', ')),
      })
  }

  if (dliScore < 40) {
    const strongOnes = entries.filter(([, v]) => v > 60)
    if (strongOnes.length > 0)
      notices.push({
        type: 'info',
        message: t('dliDetail.imbalance.grade1Strong'),
        detail: t('dliDetail.imbalance.grade1StrongDetail').replace('{aspects}', strongOnes.map(([k]) => t(`dli.aspects.${k}`)).join(', ')),
      })
  }

  if (gap > 60)
    notices.push({
      type: 'imbalance',
      message: t('dliDetail.imbalance.imbalance'),
      detail: t('dliDetail.imbalance.imbalanceDetail')
        .replace('{max}', t(`dli.aspects.${maxAsp[0]}`))
        .replace('{maxScore}', maxAsp[1].toFixed(1))
        .replace('{min}', t(`dli.aspects.${minAsp[0]}`))
        .replace('{minScore}', minAsp[1].toFixed(1)),
    })

  return notices
}

function ImbalanceNotice({ notice }) {
  const cfg = {
    warning:   { icon: '⚠️', border: 'border-amber-500/30', bg: 'bg-amber-500/10', text: 'text-amber-800 dark:text-amber-300',  sub: 'text-amber-700 dark:text-amber-200/70' },
    info:      { icon: '💡', border: 'border-blue-500/30',  bg: 'bg-blue-500/10',  text: 'text-blue-800 dark:text-blue-300',   sub: 'text-blue-700 dark:text-blue-200/70' },
    imbalance: { icon: '⚖️', border: 'border-violet-500/30',bg: 'bg-violet-500/10',text: 'text-violet-800 dark:text-violet-300', sub: 'text-violet-700 dark:text-violet-200/70' },
  }[notice.type]
  return (
    <div className={`flex items-start gap-3 p-4 rounded-xl border ${cfg.border} ${cfg.bg}`}>
      <span className="text-lg flex-shrink-0 mt-0.5">{cfg.icon}</span>
      <div>
        <p className={`text-sm font-semibold ${cfg.text}`}>{notice.message}</p>
        <p className={`text-xs mt-1 leading-relaxed ${cfg.sub}`}>{notice.detail}</p>
      </div>
    </div>
  )
}

function SubAspectBar({ label, score, color }) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between items-center">
        <span className="text-xs text-slate-500">{label}</span>
        <span className="text-xs font-mono font-semibold" style={{ color }}>{score?.toFixed(1)}%</span>
      </div>
      <div className="h-1.5 bg-slate-50 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${score}%` }}
          transition={{ duration: 0.7, ease: 'easeOut' }}
          className="h-full rounded-full"
          style={{ backgroundColor: color }}
        />
      </div>
    </div>
  )
}

function AspectCard({ aspect, score, subScores, config, t }) {
  return (
    <div className="card p-5 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="font-display font-semibold text-slate-900">{t(`dli.aspects.${aspect}`)}</h4>
          {Object.keys(config.sub).length > 0 && (
            <p className="text-xs text-slate-500 mt-0.5">{Object.keys(config.sub).length} {t('dliDetail.subAspects')}</p>
          )}
        </div>
        <GaugeChart score={score} size={80} showLabel={false} />
      </div>
      {Object.keys(config.sub).length > 0 && subScores && (
        <div className="space-y-2.5 pt-2 border-t border-slate-200">
          {Object.keys(config.sub).map((key) => (
            <SubAspectBar key={key} label={t(`dliDetail.subAspectLabels.${key}`)} score={subScores[key] ?? 0} color={config.color} />
          ))}
        </div>
      )}
    </div>
  )
}

export default function DLIDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { t } = useLang()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get(`/predict/document/${id}/dli`)
      .then(r => setData(r.data))
      .catch(() => { toast.error(t('dliDetail.loadError')); navigate('/dli-analysis') })
      .finally(() => setLoading(false))
  }, [id, navigate, t])

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-8 h-8 border-2 border-teal-400/30 border-t-teal-400 rounded-full animate-spin" />
    </div>
  )

  if (!data) return null

  const notices = detectImbalances(data.scores, data.dli_score, t)

  return (
    <div className="max-w-5xl space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-slate-500">
        <button onClick={() => navigate('/dli-analysis')} className="hover:text-teal-400 transition-colors">{t('dli.title')}</button>
        <span>/</span>
        <span className="text-slate-600 truncate max-w-xs">{data.file_name}</span>
        <span>/</span>
        <span className="text-slate-600">{t('dliDetail.breadcrumbDetail')}</span>
      </div>

      <div>
        <h1 className="font-display text-2xl font-bold text-slate-900">{t('dliDetail.title')}</h1>
        <p className="text-slate-500 mt-1 truncate">{data.file_name}</p>
      </div>

      {/* Overall score */}
      <div className="card p-6 flex items-center gap-6">
        <GaugeChart score={data.dli_score} size={140} />
        <div>
          <p className="text-slate-500 text-sm">{t('dliDetail.overallScore')}</p>
          <p className="font-display text-4xl font-bold text-slate-900 mt-1">{data.dli_score?.toFixed(1)}%</p>
          <p className="text-teal-400 font-semibold mt-1">{data.dli_category}</p>
        </div>
      </div>

      {/* Imbalance notices */}
      {notices.length > 0 && (
        <div className="space-y-2">
          {notices.map((n, i) => <ImbalanceNotice key={i} notice={n} />)}
        </div>
      )}

      {/* Aspect cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Object.entries(ASPECT_CONFIG).map(([aspect, config]) => (
          <AspectCard
            key={aspect}
            aspect={aspect}
            score={data.scores?.[aspect] ?? 0}
            subScores={data.sub_scores?.[aspect]}
            config={config}
            t={t}
          />
        ))}
      </div>

      {/* Navigation */}
      <div className="flex gap-3">
        <button onClick={() => navigate('/dli-analysis')} className="btn-secondary">{t('dliDetail.back')}</button>
        <button onClick={() => navigate(`/dli-analysis/${id}/text`)} className="btn-primary">📝 {t('dliDetail.viewTextAnalysis')}</button>
      </div>
    </div>
  )
}

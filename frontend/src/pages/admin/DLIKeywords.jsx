import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'
import api from '../../services/api'
import { useLang } from '../../contexts/LanguageContext'

const ASPECTS = ['mindful', 'meaningful', 'joyful', 'pedagogis', 'digital']

const ASPECT_COLORS = {
  mindful:    { dot: 'bg-violet-400', badge: 'bg-violet-400/15 text-violet-600 border-violet-400/30' },
  meaningful: { dot: 'bg-teal-400',   badge: 'bg-teal-400/15 text-teal-600 border-teal-400/30' },
  joyful:     { dot: 'bg-orange-400', badge: 'bg-orange-400/15 text-orange-300 border-orange-400/30' },
  pedagogis:  { dot: 'bg-blue-400',   badge: 'bg-blue-400/15 text-blue-600 border-blue-400/30' },
  digital:    { dot: 'bg-emerald-400',badge: 'bg-emerald-400/15 text-emerald-800 dark:text-emerald-300 border-emerald-400/30' },
}

const STRENGTH_CONFIG = {
  strong: { label: 'Strong', color: 'bg-teal-500/20 text-teal-600 border-teal-500/30', dot: 'bg-teal-400', points: '+4' },
  medium: { label: 'Medium', color: 'bg-amber-500/20 text-amber-600 border-amber-500/30', dot: 'bg-amber-400', points: '+3' },
  weak:   { label: 'Weak',   color: 'bg-red-500/20 text-red-600 border-red-500/30',     dot: 'bg-red-400',  points: '-2' },
}

function KeywordTag({ keyword, onRemove }) {
  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-50 border border-slate-200 text-slate-600 text-xs group">
      {keyword}
      <button
        onClick={() => onRemove(keyword)}
        className="text-slate-600 hover:text-red-600 transition-colors opacity-0 group-hover:opacity-100"
      >
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </span>
  )
}

function AddKeywordInput({ onAdd }) {
  const [value, setValue] = useState('')

  const handleAdd = () => {
    const trimmed = value.trim()
    if (!trimmed) return
    onAdd(trimmed)
    setValue('')
  }

  return (
    <div className="flex gap-2 mt-2">
      <input
        value={value}
        onChange={e => setValue(e.target.value)}
        onKeyDown={e => e.key === 'Enter' && handleAdd()}
        placeholder="Tambah keyword..."
        className="input-field text-xs py-1.5 flex-1"
      />
      <button
        onClick={handleAdd}
        disabled={!value.trim()}
        className="px-3 py-1.5 rounded-lg bg-teal-600 hover:bg-teal-700 text-white text-xs font-medium transition-all disabled:opacity-40"
      >
        + Add
      </button>
    </div>
  )
}

function SubAspectCard({ subAspect, data, onChange }) {
  const handleRemove = (strength, keyword) => {
    const updated = { ...data }
    updated[strength] = (updated[strength] || []).filter(k => k !== keyword)
    onChange(updated)
  }

  const handleAdd = (strength, keyword) => {
    const updated = { ...data }
    if (!updated[strength]) updated[strength] = []
    if (!updated[strength].includes(keyword)) {
      updated[strength] = [...updated[strength], keyword]
      onChange(updated)
    } else {
      toast.error('Keyword sudah ada')
    }
  }

  return (
    <div className="card p-4 space-y-3">
      <h4 className="font-semibold text-slate-900 text-sm capitalize">{subAspect.replace(/_/g, ' ')}</h4>
      {['strong', 'medium', 'weak'].map(strength => {
        const cfg = STRENGTH_CONFIG[strength]
        const keywords = data[strength] || []
        return (
          <div key={strength}>
            <div className="flex items-center gap-2 mb-1.5">
              <div className={`w-2 h-2 rounded-full ${cfg.dot}`} />
              <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${cfg.color}`}>
                {cfg.label} ({cfg.points})
              </span>
              <span className="text-slate-600 text-xs">{keywords.length} keywords</span>
            </div>
            <div className="flex flex-wrap gap-1.5 min-h-[28px]">
              {keywords.length === 0 ? (
                <span className="text-slate-600 text-xs italic">Belum ada keyword</span>
              ) : (
                keywords.map(kw => (
                  <KeywordTag key={kw} keyword={kw} onRemove={kw => handleRemove(strength, kw)} />
                ))
              )}
            </div>
            <AddKeywordInput onAdd={kw => handleAdd(strength, kw)} />
          </div>
        )
      })}
    </div>
  )
}

export default function DLIKeywords() {
  const { t } = useLang()
  const [activeAspect, setActiveAspect] = useState('mindful')
  const [keywords, setKeywords] = useState({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [dirty, setDirty] = useState(false)

  useEffect(() => {
    setLoading(true)
    api.get('/admin/dli/keywords')
      .then(r => setKeywords(r.data))
      .catch(() => toast.error('Gagal memuat keywords'))
      .finally(() => setLoading(false))
  }, [])

  const handleSubAspectChange = (subAspect, newData) => {
    setKeywords(prev => ({
      ...prev,
      [activeAspect]: {
        ...prev[activeAspect],
        [subAspect]: newData,
      }
    }))
    setDirty(true)
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      await api.put(`/admin/dli/keywords/${activeAspect}`, keywords[activeAspect])
      toast.success(`Keywords '${activeAspect}' berhasil disimpan`)
      setDirty(false)
    } catch {
      toast.error('Gagal menyimpan keywords')
    } finally {
      setSaving(false)
    }
  }

  const handleSaveAll = async () => {
    setSaving(true)
    try {
      await Promise.all(
        ASPECTS.map(aspect => api.put(`/admin/dli/keywords/${aspect}`, keywords[aspect]))
      )
      toast.success('Semua keywords berhasil disimpan')
      setDirty(false)
    } catch {
      toast.error('Gagal menyimpan beberapa keywords')
    } finally {
      setSaving(false)
    }
  }

  const totalKeywords = (aspect) => {
    if (!keywords[aspect]) return 0
    return Object.values(keywords[aspect]).reduce((sum, sub) => {
      return sum + Object.values(sub).reduce((s, arr) => s + (arr?.length || 0), 0)
    }, 0)
  }

  const aspectData = keywords[activeAspect] || {}

  return (
    <div className="max-w-5xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold text-slate-900">
            {t('dliKeywords.title')}
          </h1>
          <p className="text-slate-500 mt-1">{t('dliKeywords.subtitle')}</p>
        </div>
        <div className="flex gap-2">
          {dirty && (
            <button
              onClick={handleSave}
              disabled={saving}
              className="btn-primary text-sm flex items-center gap-2"
            >
              {saving ? <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : null}
              {t('dliKeywords.saveAspect')}
            </button>
          )}
          <button
            onClick={handleSaveAll}
            disabled={saving}
            className="btn-secondary text-sm flex items-center gap-2"
          >
            {saving ? <span className="w-3.5 h-3.5 border-2 border-slate-400/30 border-t-slate-400 rounded-full animate-spin" /> : null}
            {t('dliKeywords.saveAll')}
          </button>
        </div>
      </div>

      {/* Scoring legend */}
      <div className="card p-4 flex flex-wrap gap-4 text-xs">
        <span className="text-slate-500 font-semibold">{t('dliKeywords.scoringLegend')}:</span>
        {Object.entries(STRENGTH_CONFIG).map(([s, cfg]) => (
          <div key={s} className="flex items-center gap-1.5">
            <div className={`w-2 h-2 rounded-full ${cfg.dot}`} />
            <span className={`px-2 py-0.5 rounded-full border ${cfg.color}`}>{cfg.label} {cfg.points} pts</span>
          </div>
        ))}
      </div>

      {/* Aspect tabs */}
      <div className="flex gap-2 flex-wrap">
        {ASPECTS.map(aspect => {
          const col = ASPECT_COLORS[aspect]
          const isActive = activeAspect === aspect
          return (
            <button
              key={aspect}
              onClick={() => setActiveAspect(aspect)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all border ${
                isActive
                  ? `${col.badge} border-current`
                  : 'bg-slate-50 text-slate-500 border-slate-200 hover:text-slate-700'
              }`}
            >
              <div className={`w-2 h-2 rounded-full ${col.dot}`} />
              <span className="capitalize">{t(`dli.aspects.${aspect}`)}</span>
              <span className="text-xs opacity-60">({totalKeywords(aspect)})</span>
            </button>
          )
        })}
      </div>

      {/* Sub-aspect cards */}
      {loading ? (
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => <div key={i} className="card h-40 animate-pulse bg-slate-50" />)}
        </div>
      ) : (
        <AnimatePresence mode="wait">
          <motion.div
            key={activeAspect}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="space-y-4"
          >
            {Object.entries(aspectData).map(([subAspect, data]) => (
              <SubAspectCard
                key={subAspect}
                subAspect={subAspect}
                data={data}
                onChange={newData => handleSubAspectChange(subAspect, newData)}
              />
            ))}
          </motion.div>
        </AnimatePresence>
      )}

      {dirty && (
        <div className="fixed bottom-6 right-6 z-50">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            className="card p-4 flex items-center gap-3 shadow-2xl border border-amber-500/30 bg-amber-500/10"
          >
            <div className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
            <span className="text-amber-600 text-sm">{t('dliKeywords.unsavedChanges')}</span>
            <button onClick={handleSave} disabled={saving} className="btn-primary text-xs py-1.5 px-3">
              {t('dliKeywords.saveAspect')}
            </button>
          </motion.div>
        </div>
      )}
    </div>
  )
}

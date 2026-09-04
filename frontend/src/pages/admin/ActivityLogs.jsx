import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { format } from 'date-fns'
import { id } from 'date-fns/locale'
import toast from 'react-hot-toast'
import api from '../../services/api'
import { useLang } from '../../contexts/LanguageContext'

const actionColors = {
  login: 'bg-teal-400/15 text-teal-600',
  register: 'bg-blue-400/15 text-blue-600',
  predict: 'bg-violet-500/15 text-violet-600',
  logout: 'bg-slate-500/15 text-slate-500',
}

export default function ActivityLogs() {
  const { t } = useLang()
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [filterAction, setFilterAction] = useState('all')

  const fetchLogs = () => {
    setLoading(true)
    api.get('/admin/logs?limit=200').then(r => setLogs(r.data)).finally(() => setLoading(false))
  }
  useEffect(() => { fetchLogs() }, [])

  const handleExport = async () => {
    try {
      const res = await api.get('/admin/export/logs', { responseType: 'blob' })
      const url = URL.createObjectURL(res.data)
      const a = document.createElement('a'); a.href = url; a.download = 'logs.csv'; a.click()
      URL.revokeObjectURL(url)
      toast.success(t('activityLogs.exportSuccess'))
    } catch { toast.error(t('activityLogs.exportError')) }
  }

  const filtered = logs.filter(l => {
    const matchSearch = l.username?.toLowerCase().includes(search.toLowerCase()) || l.detail?.toLowerCase().includes(search.toLowerCase())
    const matchAction = filterAction === 'all' || l.action === filterAction
    return matchSearch && matchAction
  })

  const uniqueActions = [...new Set(logs.map(l => l.action))]

  return (
    <div className="max-w-6xl space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold text-slate-900">{t('activityLogs.title')}</h1>
          <p className="text-slate-500 mt-1">{t('activityLogs.subtitle')}</p>
        </div>
        <motion.button whileTap={{ scale: 0.97 }} onClick={handleExport} className="btn-secondary flex items-center gap-2">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          {t('activityLogs.exportCsv')}
        </motion.button>
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder={t('activityLogs.searchPlaceholder')} className="input-field pl-9" />
        </div>
        <select value={filterAction} onChange={e => setFilterAction(e.target.value)} className="input-field sm:w-40">
          <option value="all">{t('activityLogs.allActions')}</option>
          {uniqueActions.map(a => <option key={a} value={a}>{a}</option>)}
        </select>
      </div>

      <div className="card overflow-hidden">
        {loading ? (
          <div className="p-6 space-y-2">{[...Array(8)].map((_, i) => <div key={i} className="h-10 bg-slate-50 rounded-lg animate-pulse" />)}</div>
        ) : filtered.length === 0 ? (
          <div className="p-12 text-center text-slate-500">{t('activityLogs.noLogs')}</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead><tr className="border-b border-slate-200">
                <th className="text-left px-6 py-3 text-xs text-slate-500 uppercase">{t('activityLogs.time')}</th>
                <th className="text-left px-4 py-3 text-xs text-slate-500 uppercase">{t('activityLogs.user')}</th>
                <th className="text-left px-4 py-3 text-xs text-slate-500 uppercase">{t('activityLogs.action')}</th>
                <th className="text-left px-4 py-3 text-xs text-slate-500 uppercase">{t('activityLogs.detail')}</th>
              </tr></thead>
              <tbody className="divide-y divide-navy-800">
                {filtered.map((l, i) => (
                  <motion.tr key={l.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: Math.min(i * 0.02, 0.3) }} className="hover:bg-slate-50/30 transition-colors">
                    <td className="px-6 py-3 text-slate-500 text-xs whitespace-nowrap font-mono">
                      {l.created_at ? format(new Date(l.created_at), 'd MMM yyyy HH:mm:ss', { locale: id }) : '—'}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-6 h-6 rounded-full bg-navy-700 flex items-center justify-center text-xs font-bold text-slate-500">
                          {l.username?.[0]?.toUpperCase() || '?'}
                        </div>
                        <span className="text-slate-900 text-sm">{l.username || '—'}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`text-xs font-semibold px-2 py-1 rounded-full ${actionColors[l.action] || 'bg-slate-500/15 text-slate-500'}`}>
                        {l.action}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-500 text-xs max-w-xs truncate">{l.detail || '—'}</td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      <p className="text-slate-600 text-xs text-right">
        {t('activityLogs.showing').replace('{filtered}', filtered.length).replace('{total}', logs.length)}
      </p>
    </div>
  )
}

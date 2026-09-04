import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { format } from 'date-fns'
import { id } from 'date-fns/locale'
import toast from 'react-hot-toast'
import api from '../../services/api'
import { useLang } from '../../contexts/LanguageContext'

const GRADE_COLORS = {
  grade4: 'text-teal-600 bg-teal-400/10 border-teal-400/30',
  grade3: 'text-blue-600 bg-blue-400/10 border-blue-400/30',
  grade2: 'text-amber-600 bg-amber-400/10 border-amber-400/30',
  grade1: 'text-red-600 bg-red-400/10 border-red-400/30',
}

function scoreColor(s) {
  if (s >= 70) return 'text-teal-600'
  if (s >= 55) return 'text-blue-600'
  if (s >= 40) return 'text-amber-600'
  return 'text-red-600'
}

export default function DLIHistory() {
  const { t } = useLang()
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({ grade: '', date_from: '', date_to: '' })
  const [exporting, setExporting] = useState(false)

  const fetchData = () => {
    setLoading(true)
    const params = new URLSearchParams()
    if (filters.grade) params.append('grade', filters.grade)
    if (filters.date_from) params.append('date_from', filters.date_from)
    if (filters.date_to) params.append('date_to', filters.date_to)
    params.append('limit', '200')
    api.get(`/admin/dli/history?${params}`)
      .then(r => setRows(r.data))
      .catch(() => toast.error('Gagal memuat data'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetchData() }, [])

  const handleExport = async () => {
    setExporting(true)
    try {
      const params = new URLSearchParams()
      if (filters.grade) params.append('grade', filters.grade)
      if (filters.date_from) params.append('date_from', filters.date_from)
      if (filters.date_to) params.append('date_to', filters.date_to)
      const res = await api.get(`/admin/dli/history/export?${params}`, { responseType: 'blob' })
      const url = URL.createObjectURL(res.data)
      const a = document.createElement('a'); a.href = url; a.download = 'dli_history.xlsx'; a.click()
      URL.revokeObjectURL(url)
      toast.success('Export berhasil')
    } catch { toast.error('Export gagal') }
    finally { setExporting(false) }
  }

  const ASPECTS = ['mindful', 'meaningful', 'joyful', 'pedagogis', 'digital']

  return (
    <div className="max-w-7xl space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="font-display text-2xl font-bold text-slate-900">{t('dliHistory.title')}</h1>
          <p className="text-slate-500 mt-1">{t('dliHistory.subtitle')}</p>
        </div>
        <button onClick={handleExport} disabled={exporting} className="btn-secondary text-sm flex items-center gap-2">
          {exporting ? <span className="w-3.5 h-3.5 border-2 border-slate-400/30 border-t-slate-400 rounded-full animate-spin" /> : null}
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          {t('dliHistory.exportExcel')}
        </button>
      </div>

      {/* Filters */}
      <div className="card p-4 flex flex-wrap gap-3 items-end">
        <div>
          <label className="text-xs text-slate-500 block mb-1">{t('dliHistory.filterGrade')}</label>
          <select value={filters.grade} onChange={e => setFilters(f => ({ ...f, grade: e.target.value }))}
            className="input-field text-sm py-1.5 w-40">
            <option value="">{t('dliHistory.allGrades')}</option>
            <option value="grade4">Grade 4 (≥70%)</option>
            <option value="grade3">Grade 3 (55-70%)</option>
            <option value="grade2">Grade 2 (40-55%)</option>
            <option value="grade1">Grade 1 (&lt;40%)</option>
          </select>
        </div>
        <div>
          <label className="text-xs text-slate-500 block mb-1">{t('dliHistory.dateFrom')}</label>
          <input type="date" value={filters.date_from} onChange={e => setFilters(f => ({ ...f, date_from: e.target.value }))}
            className="input-field text-sm py-1.5" />
        </div>
        <div>
          <label className="text-xs text-slate-500 block mb-1">{t('dliHistory.dateTo')}</label>
          <input type="date" value={filters.date_to} onChange={e => setFilters(f => ({ ...f, date_to: e.target.value }))}
            className="input-field text-sm py-1.5" />
        </div>
        <button onClick={fetchData} className="btn-primary text-sm py-1.5 px-4">{t('dliHistory.apply')}</button>
        <button onClick={() => { setFilters({ grade: '', date_from: '', date_to: '' }); setTimeout(fetchData, 0) }}
          className="btn-secondary text-sm py-1.5 px-4">{t('dliHistory.reset')}</button>
      </div>

      <div className="card overflow-hidden">
        <div className="px-6 py-3 border-b border-slate-200 flex items-center justify-between">
          <span className="text-slate-500 text-sm">{rows.length} {t('dliHistory.records')}</span>
        </div>
        {loading ? (
          <div className="p-6 space-y-2">{[...Array(6)].map((_, i) => <div key={i} className="h-10 bg-slate-50 rounded animate-pulse" />)}</div>
        ) : rows.length === 0 ? (
          <div className="p-12 text-center text-slate-500">{t('dliHistory.noData')}</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="border-b border-slate-200">
                <th className="text-left px-4 py-3 text-xs text-slate-500 uppercase">{t('dliHistory.file')}</th>
                <th className="text-left px-4 py-3 text-xs text-slate-500 uppercase">{t('dliHistory.user')}</th>
                <th className="text-left px-4 py-3 text-xs text-slate-500 uppercase">DLI</th>
                {ASPECTS.map(a => <th key={a} className="text-left px-3 py-3 text-xs text-slate-500 uppercase capitalize">{a.slice(0,4)}</th>)}
                <th className="text-left px-4 py-3 text-xs text-slate-500 uppercase">{t('dliHistory.date')}</th>
              </tr></thead>
              <tbody className="divide-y divide-navy-800">
                {rows.map((r, i) => (
                  <motion.tr key={r.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: Math.min(i * 0.02, 0.3) }}
                    className="hover:bg-slate-50/30 transition-colors">
                    <td className="px-4 py-2.5 text-slate-900 max-w-[200px] truncate">{r.file_name}</td>
                    <td className="px-4 py-2.5 text-slate-500">{r.username || '—'}</td>
                    <td className="px-4 py-2.5">
                      <span className={`font-mono font-bold ${scoreColor(r.dli_score)}`}>{r.dli_score}%</span>
                    </td>
                    {ASPECTS.map(a => (
                      <td key={a} className={`px-3 py-2.5 font-mono text-xs ${scoreColor(r[a])}`}>{r[a]}%</td>
                    ))}
                    <td className="px-4 py-2.5 text-slate-500 text-xs whitespace-nowrap">{r.created_at?.slice(0, 10)}</td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

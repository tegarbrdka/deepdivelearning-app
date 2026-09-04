import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { format } from 'date-fns'
import { id } from 'date-fns/locale'
import toast from 'react-hot-toast'
import api from '../../services/api'
import { useLang } from '../../contexts/LanguageContext'

function LabelBadge({ label, fileType }) {
  const map = {
    'Deep Learning': 'badge-deep-learning',
    'Bukan Deep Learning': 'badge-bukan',
    'Baik': 'badge-baik',
    'Cukup': 'badge-cukup',
    'Kurang': 'badge-kurang',
  }
  return <span className={map[label] || 'badge-bukan'}>{label}</span>
}

function DetailModal({ prediction, onClose }) {
  if (!prediction) return null
  
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.95, y: 20 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.95, y: 20 }}
        onClick={e => e.stopPropagation()}
        className="card p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto"
      >
        <div className="flex items-start justify-between mb-6">
          <div>
            <h3 className="font-display text-xl font-bold text-slate-900">Detail Prediksi</h3>
            <p className="text-slate-500 text-sm mt-1">Informasi lengkap hasil prediksi</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-50 rounded-lg transition-colors"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-slate-50 rounded-xl p-4">
              <p className="text-xs text-slate-500 mb-1">Jenis File</p>
              <p className="text-slate-900 font-semibold capitalize">{prediction.file_type}</p>
            </div>
            <div className="bg-slate-50 rounded-xl p-4">
              <p className="text-xs text-slate-500 mb-1">Nama File</p>
              <p className="text-slate-900 font-semibold truncate">{prediction.file_name || '—'}</p>
            </div>
          </div>

          <div className="bg-slate-50 rounded-xl p-4">
            <p className="text-xs text-slate-500 mb-2">Hasil Prediksi</p>
            <div className="flex items-center gap-3">
              <LabelBadge label={prediction.label} fileType={prediction.file_type} />
              <span className="text-slate-500">•</span>
              <span className="text-slate-900 font-mono">{prediction.confidence?.toFixed(2)}% confidence</span>
            </div>
          </div>

          <div className="bg-slate-50 rounded-xl p-4">
            <p className="text-xs text-slate-500 mb-1">Waktu Prediksi</p>
            <p className="text-slate-900">
              {prediction.created_at ? format(new Date(prediction.created_at), 'EEEE, d MMMM yyyy • HH:mm:ss', { locale: id }) : '—'}
            </p>
          </div>

          {prediction.file_path && (
            <div className="bg-slate-50 rounded-xl p-4">
              <p className="text-xs text-slate-500 mb-2">File Path</p>
              <p className="text-slate-500 text-sm font-mono break-all">{prediction.file_path}</p>
              <a
                href={prediction.file_path.replace('backend', '')}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-3 inline-flex items-center gap-2 text-sm text-violet-400 hover:text-violet-800 dark:text-violet-300 transition-colors"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/>
                </svg>
                Download File
              </a>
            </div>
          )}
        </div>

        <button
          onClick={onClose}
          className="btn-primary w-full mt-6"
        >
          Tutup
        </button>
      </motion.div>
    </motion.div>
  )
}

export default function PredictionHistory() {
  const { t } = useLang()
  const [predictions, setPredictions] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [filterType, setFilterType] = useState('all')
  const [filterLabel, setFilterLabel] = useState('all')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [sortBy, setSortBy] = useState('date-desc')
  const [selectedPrediction, setSelectedPrediction] = useState(null)
  const [exporting, setExporting] = useState(false)
  const [selectMode, setSelectMode] = useState(false)
  const [selectedIds, setSelectedIds] = useState([])

  useEffect(() => {
    api.get('/predict/history')
      .then(r => setPredictions(r.data))
      .finally(() => setLoading(false))
  }, [])

  const filtered = predictions.filter(p => {
    const matchSearch = p.file_name?.toLowerCase().includes(search.toLowerCase()) ||
      p.label?.toLowerCase().includes(search.toLowerCase())
    const matchType = filterType === 'all' || p.file_type === filterType
    const matchLabel = filterLabel === 'all' || p.label === filterLabel
    
    // Date range filter
    let matchDate = true
    if (dateFrom || dateTo) {
      const pDate = new Date(p.created_at)
      if (dateFrom) matchDate = matchDate && pDate >= new Date(dateFrom)
      if (dateTo) matchDate = matchDate && pDate <= new Date(dateTo + 'T23:59:59')
    }
    
    return matchSearch && matchType && matchLabel && matchDate
  })

  // Sorting
  const sorted = [...filtered].sort((a, b) => {
    switch (sortBy) {
      case 'date-desc':
        return new Date(b.created_at) - new Date(a.created_at)
      case 'date-asc':
        return new Date(a.created_at) - new Date(b.created_at)
      case 'confidence-desc':
        return b.confidence - a.confidence
      case 'confidence-asc':
        return a.confidence - b.confidence
      case 'name-asc':
        return (a.file_name || '').localeCompare(b.file_name || '')
      case 'name-desc':
        return (b.file_name || '').localeCompare(a.file_name || '')
      default:
        return 0
    }
  })

  const handleSelectAll = (e) => {
    if (e.target.checked) {
      setSelectedIds(sorted.map(p => p.id))
    } else {
      setSelectedIds([])
    }
  }

  const handleSelectOne = (id) => {
    setSelectedIds(prev => 
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    )
  }

  const handleBulkDelete = async () => {
    if (selectedIds.length === 0) return
    
    const confirmed = await new Promise(resolve => {
      toast((t) => (
        <div className="flex flex-col gap-3">
          <p className="text-slate-900 font-semibold">Hapus {selectedIds.length} prediksi?</p>
          <p className="text-slate-500 text-sm">Aksi ini tidak dapat dibatalkan</p>
          <div className="flex gap-2">
            <button
              onClick={() => { toast.dismiss(t.id); resolve(true) }}
              className="px-3 py-1.5 bg-red-500 hover:bg-red-600 text-white rounded-lg text-sm font-medium transition-colors"
            >
              Ya, Hapus
            </button>
            <button
              onClick={() => { toast.dismiss(t.id); resolve(false) }}
              className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-900 rounded-lg text-sm font-medium transition-colors"
            >
              Batal
            </button>
          </div>
        </div>
      ), { duration: Infinity })
    })

    if (!confirmed) return

    try {
      await Promise.all(selectedIds.map(id => api.delete(`/predict/${id}`)))
      setPredictions(prev => prev.filter(p => !selectedIds.includes(p.id)))
      setSelectedIds([])
      setSelectMode(false)
      toast.success(`${selectedIds.length} prediksi berhasil dihapus`)
    } catch (err) {
      toast.error('Gagal menghapus prediksi')
    }
  }

  const handleExport = async (format) => {
    setExporting(true)
    try {
      const res = await api.get(`/predict/export?format=${format}`, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `prediction_history.${format === 'excel' ? 'xlsx' : 'csv'}`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      toast.success(`Riwayat berhasil diexport ke ${format.toUpperCase()}`)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Export gagal')
    } finally {
      setExporting(false)
    }
  }

  return (
    <div className="max-w-5xl space-y-5">
      <AnimatePresence>
        {selectedPrediction && (
          <DetailModal
            prediction={selectedPrediction}
            onClose={() => setSelectedPrediction(null)}
          />
        )}
      </AnimatePresence>

      <div className="flex items-start justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold text-slate-900">{t('history.title')}</h1>
          <p className="text-slate-500 mt-1">{t('history.subtitle')}</p>
        </div>
        <div className="flex gap-2">
          {selectMode ? (
            <>
              <button
                onClick={() => { setSelectMode(false); setSelectedIds([]) }}
                className="btn-secondary flex items-center gap-2"
              >
                Batal
              </button>
              {selectedIds.length > 0 && (
                <button
                  onClick={handleBulkDelete}
                  className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
                  </svg>
                  Hapus ({selectedIds.length})
                </button>
              )}
            </>
          ) : (
            <>
              <button
                onClick={() => setSelectMode(true)}
                disabled={predictions.length === 0}
                className="btn-secondary flex items-center gap-2"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/>
                </svg>
                Pilih Multiple
              </button>
              <button
                onClick={() => handleExport('csv')}
                disabled={exporting || predictions.length === 0}
                className="btn-secondary flex items-center gap-2"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/>
                </svg>
                {exporting ? 'Exporting...' : 'CSV'}
              </button>
              <button
                onClick={() => handleExport('excel')}
                disabled={exporting || predictions.length === 0}
                className="btn-secondary flex items-center gap-2"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/>
                </svg>
                {exporting ? 'Exporting...' : 'Excel'}
              </button>
            </>
          )}
        </div>
      </div>

      {/* Filters */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="space-y-3"
      >
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Cari nama file atau label..."
              className="input-field pl-9"
            />
          </div>
          <select
            value={filterType}
            onChange={e => setFilterType(e.target.value)}
            className="input-field sm:w-48"
          >
            <option value="all">Semua Jenis</option>
            <option value="video">Video</option>
            <option value="document">Dokumen</option>
          </select>
          <select
            value={filterLabel}
            onChange={e => setFilterLabel(e.target.value)}
            className="input-field sm:w-48"
          >
            <option value="all">Semua Label</option>
            <option value="Deep Learning">Deep Learning</option>
            <option value="Bukan Deep Learning">Bukan Deep Learning</option>
            <option value="Baik">Baik</option>
            <option value="Cukup">Cukup</option>
            <option value="Kurang">Kurang</option>
          </select>
        </div>
        
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="flex items-center gap-2 flex-1">
            <label className="text-sm text-slate-500 whitespace-nowrap">Dari:</label>
            <input
              type="date"
              value={dateFrom}
              onChange={e => setDateFrom(e.target.value)}
              className="input-field flex-1"
            />
          </div>
          <div className="flex items-center gap-2 flex-1">
            <label className="text-sm text-slate-500 whitespace-nowrap">Sampai:</label>
            <input
              type="date"
              value={dateTo}
              onChange={e => setDateTo(e.target.value)}
              className="input-field flex-1"
            />
          </div>
          <select
            value={sortBy}
            onChange={e => setSortBy(e.target.value)}
            className="input-field sm:w-56"
          >
            <option value="date-desc">Terbaru</option>
            <option value="date-asc">Terlama</option>
            <option value="confidence-desc">Confidence Tertinggi</option>
            <option value="confidence-asc">Confidence Terendah</option>
            <option value="name-asc">Nama A-Z</option>
            <option value="name-desc">Nama Z-A</option>
          </select>
        </div>
      </motion.div>

      {/* Table */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="card overflow-hidden"
      >
        {loading ? (
          <div className="p-8 space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-12 bg-slate-50 rounded-xl animate-pulse" />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="p-16 text-center">
            <svg className="w-14 h-14 text-slate-700 mx-auto mb-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <p className="text-slate-500 font-medium">Tidak ada data ditemukan</p>
            <p className="text-slate-600 text-sm mt-1">Coba ubah filter atau upload file baru</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-200">
                  {selectMode && (
                    <th className="text-left px-4 py-3">
                      <input
                        type="checkbox"
                        checked={selectedIds.length === sorted.length && sorted.length > 0}
                        onChange={handleSelectAll}
                        className="w-4 h-4 rounded border-slate-200 bg-slate-50 text-violet-600 focus:ring-violet-600 focus:ring-offset-0"
                      />
                    </th>
                  )}
                  <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">#</th>
                  <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">File</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Jenis</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Label</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Confidence</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Waktu</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Aksi</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-navy-800">
                {sorted.map((p, i) => (
                  <motion.tr
                    key={p.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.03 }}
                    className="hover:bg-slate-50/40 transition-colors"
                  >
                    {selectMode && (
                      <td className="px-4 py-3">
                        <input
                          type="checkbox"
                          checked={selectedIds.includes(p.id)}
                          onChange={() => handleSelectOne(p.id)}
                          className="w-4 h-4 rounded border-slate-200 bg-slate-50 text-violet-600 focus:ring-violet-600 focus:ring-offset-0"
                        />
                      </td>
                    )}
                    <td className="px-6 py-3 text-slate-600 text-sm">{i + 1}</td>
                    <td className="px-6 py-3">
                      <div className="flex items-center gap-3">
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${p.file_type === 'video' ? 'bg-violet-500/20' : 'bg-amber-400/15'}`}>
                          {p.file_type === 'video'
                            ? <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#a78bfa" strokeWidth="2"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2"/></svg>
                            : <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#fbbf24" strokeWidth="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                          }
                        </div>
                        <span className="text-slate-900 text-sm font-medium truncate max-w-[200px]">{p.file_name || '—'}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-xs text-slate-500 capitalize">{p.file_type}</span>
                    </td>
                    <td className="px-4 py-3">
                      <LabelBadge label={p.label} fileType={p.file_type} />
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 bg-slate-50 rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full bg-gradient-to-r from-violet-600 to-teal-500"
                            style={{ width: `${p.confidence}%` }}
                          />
                        </div>
                        <span className="text-slate-600 text-sm font-mono">{p.confidence?.toFixed(1)}%</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-slate-500 text-xs whitespace-nowrap">
                      {p.created_at ? format(new Date(p.created_at), 'd MMM yyyy, HH:mm', { locale: id }) : '—'}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => setSelectedPrediction(p)}
                        className="p-2 text-slate-500 hover:text-violet-400 hover:bg-violet-400/10 rounded-lg transition-all"
                        title="Lihat Detail"
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                          <circle cx="12" cy="12" r="3"/>
                        </svg>
                      </button>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </motion.div>

      {!loading && (
        <p className="text-slate-600 text-sm text-right">{sorted.length} dari {predictions.length} prediksi ditampilkan</p>
      )}
    </div>
  )
}

import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'
import api from '../../services/api'
import { useLang } from '../../contexts/LanguageContext'

const ASPECT_COLORS = {
  mindful: '#a78bfa', meaningful: '#2dd4bf', joyful: '#fb923c', pedagogis: '#60a5fa', digital: '#34d399'
}

function scoreColor(s) {
  if (s >= 70) return 'text-teal-600'
  if (s >= 55) return 'text-blue-600'
  if (s >= 40) return 'text-amber-600'
  return 'text-red-600'
}

function AspectMiniBar({ aspect, score }) {
  const color = ASPECT_COLORS[aspect] || '#8b5cf6'
  return (
    <div className="space-y-0.5">
      <div className="flex justify-between text-xs">
        <span className="text-slate-500 capitalize">{aspect.slice(0, 4)}</span>
        <span className="font-mono" style={{ color }}>{score}%</span>
      </div>
      <div className="h-1 bg-slate-50 rounded-full overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${score}%`, backgroundColor: color }} />
      </div>
    </div>
  )
}

export default function DLIBulkAnalysis() {
  const { t } = useLang()
  const [files, setFiles] = useState([])
  const [analyzing, setAnalyzing] = useState(false)
  const [results, setResults] = useState(null)
  const [progress, setProgress] = useState(0)

  const onDrop = useCallback(accepted => {
    setFiles(prev => [...prev, ...accepted.filter(f => !prev.find(p => p.name === f.name))])
    setResults(null)
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'], 'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'] },
    multiple: true,
  })

  const handleAnalyze = async () => {
    if (!files.length) return
    setAnalyzing(true)
    setProgress(0)
    const form = new FormData()
    files.forEach(f => form.append('files', f))
    try {
      const res = await api.post('/admin/dli/bulk-analyze', form, {
        onUploadProgress: e => setProgress(Math.round((e.loaded / e.total) * 60)),
        timeout: 300000,
      })
      setProgress(100)
      setResults(res.data)
      toast.success(`${res.data.success}/${res.data.total} ${t('dliAnalysisBulk.successMsg')}`)
    } catch (err) {
      toast.error(err.response?.data?.detail || t('dliAnalysisBulk.errorMsg'))
    } finally {
      setAnalyzing(false)
    }
  }

  const handleExportExcel = async () => {
    if (!results) return
    try {
      // Build CSV from results
      const ASPECTS = ['mindful', 'meaningful', 'joyful', 'pedagogis', 'digital']
      const header = ['File', 'DLI Score', 'Category', ...ASPECTS].join(',')
      const rows = results.results
        .filter(r => !r.error)
        .map(r => [
          `"${r.file}"`, r.dli_score, `"${r.dli_category}"`,
          ...ASPECTS.map(a => r.scores?.[a]?.toFixed(1) || 0)
        ].join(','))
      const csv = [header, ...rows].join('\n')
      const blob = new Blob([csv], { type: 'text/csv' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a'); a.href = url; a.download = 'bulk_dli_results.csv'; a.click()
      URL.revokeObjectURL(url)
      toast.success('Export berhasil')
    } catch { toast.error('Export gagal') }
  }

  const ASPECTS = ['mindful', 'meaningful', 'joyful', 'pedagogis', 'digital']

  return (
    <div className="max-w-6xl space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-slate-900">{t('dliAnalysisBulk.title')}</h1>
        <p className="text-slate-500 mt-1">{t('dliAnalysisBulk.subtitle')}</p>
      </div>

      {/* Upload zone */}
      {!results && (
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
          <div
            {...getRootProps()}
            className={`card p-10 flex flex-col items-center justify-center cursor-pointer transition-all border-2 border-dashed
              ${isDragActive ? 'border-teal-500 bg-teal-500/5' : 'border-slate-200 hover:border-teal-600/50'}`}
          >
            <input {...getInputProps()} />
            <div className="text-4xl mb-3">📂</div>
            <p className="text-slate-900 font-semibold">{isDragActive ? t('dliAnalysisBulk.dropHere') : t('dliAnalysisBulk.dragDrop')}</p>
            <p className="text-slate-500 text-sm mt-1">{t('dliAnalysisBulk.supported')}</p>
          </div>

          {files.length > 0 && (
            <div className="card p-4 space-y-2">
              <div className="flex items-center justify-between mb-2">
                <span className="text-slate-600 text-sm font-semibold">{files.length} {t('dliAnalysisBulk.filesSelected')}</span>
                <button onClick={() => setFiles([])} className="text-xs text-slate-500 hover:text-red-600 transition-colors">
                  {t('dliAnalysisBulk.clearAll')}
                </button>
              </div>
              <div className="max-h-48 overflow-y-auto space-y-1.5">
                {files.map((f, i) => (
                  <div key={i} className="flex items-center justify-between p-2 rounded-lg bg-slate-50">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">{f.name.endsWith('.pdf') ? '📄' : '📝'}</span>
                      <span className="text-slate-600 text-sm truncate max-w-xs">{f.name}</span>
                    </div>
                    <button onClick={() => setFiles(prev => prev.filter((_, j) => j !== i))}
                      className="text-slate-600 hover:text-red-600 transition-colors text-xs">✕</button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {analyzing && (
            <div className="card p-4 space-y-2">
              <div className="flex items-center gap-3">
                <span className="w-4 h-4 border-2 border-teal-400/30 border-t-teal-400 rounded-full animate-spin" />
                <span className="text-slate-600 text-sm">{t('dliAnalysisBulk.analyzing')}</span>
                <span className="text-teal-600 text-sm ml-auto font-mono">{progress}%</span>
              </div>
              <div className="h-2 bg-slate-50 rounded-full overflow-hidden">
                <motion.div animate={{ width: `${progress}%` }} transition={{ duration: 0.3 }}
                  className="h-full bg-gradient-to-r from-teal-600 to-violet-500 rounded-full" />
              </div>
            </div>
          )}

          {files.length > 0 && !analyzing && (
            <button onClick={handleAnalyze} className="btn-primary w-full py-3 text-base">
              🔍 {t('dliAnalysisBulk.startAnalysis')} ({files.length} {t('dliAnalysisBulk.files')})
            </button>
          )}
        </motion.div>
      )}

      {/* Results */}
      <AnimatePresence>
        {results && (
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
            <div className="flex items-center justify-between flex-wrap gap-3">
              <div className="flex items-center gap-3">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-400/10 border border-teal-400/20 text-teal-600 text-xs font-semibold">
                  ✓ {results.success}/{results.total} {t('dliAnalysisBulk.analyzed')}
                </div>
              </div>
              <div className="flex gap-2">
                <button onClick={handleExportExcel} className="btn-secondary text-sm">
                  📊 {t('dliAnalysisBulk.exportCsv')}
                </button>
                <button onClick={() => { setResults(null); setFiles([]) }} className="btn-secondary text-sm">
                  {t('dliAnalysisBulk.analyzeMore')}
                </button>
              </div>
            </div>

            {/* Summary stats */}
            {results.results.filter(r => !r.error).length > 0 && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {(() => {
                  const ok = results.results.filter(r => !r.error)
                  const avg = ok.reduce((s, r) => s + r.dli_score, 0) / ok.length
                  const g4 = ok.filter(r => r.dli_score >= 70).length
                  const g1 = ok.filter(r => r.dli_score < 40).length
                  return [
                    { label: t('dliAnalysisBulk.avgScore'), value: `${avg.toFixed(1)}%`, color: scoreColor(avg) },
                    { label: 'Grade 4 (≥70%)', value: g4, color: 'text-teal-600' },
                    { label: 'Grade 1 (<40%)', value: g1, color: 'text-red-600' },
                    { label: t('dliAnalysisBulk.errors'), value: results.total - results.success, color: 'text-slate-500' },
                  ].map(s => (
                    <div key={s.label} className="card p-4 text-center">
                      <p className={`font-display text-2xl font-bold ${s.color}`}>{s.value}</p>
                      <p className="text-xs text-slate-500 mt-0.5">{s.label}</p>
                    </div>
                  ))
                })()}
              </div>
            )}

            {/* Result cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {results.results.map((r, i) => (
                <motion.div key={i} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}
                  className={`card p-4 space-y-3 ${r.error ? 'border border-red-500/20' : ''}`}>
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-slate-900 text-sm font-medium truncate flex-1">{r.file}</p>
                    {r.error
                      ? <span className="text-xs px-2 py-0.5 rounded-full bg-red-500/15 text-red-600 border border-red-500/20 flex-shrink-0">Error</span>
                      : <span className={`text-xs font-mono font-bold flex-shrink-0 ${scoreColor(r.dli_score)}`}>{r.dli_score}%</span>
                    }
                  </div>
                  {r.error ? (
                    <p className="text-red-600 text-xs">{r.error}</p>
                  ) : (
                    <>
                      <p className="text-slate-500 text-xs">{r.dli_category}</p>
                      <div className="space-y-1.5">
                        {ASPECTS.map(a => (
                          <AspectMiniBar key={a} aspect={a} score={r.scores?.[a]?.toFixed(1) || 0} />
                        ))}
                      </div>
                    </>
                  )}
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

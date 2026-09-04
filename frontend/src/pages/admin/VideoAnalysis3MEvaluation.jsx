import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useLang } from '../../contexts/LanguageContext'
import api from '../../services/api'
import toast from 'react-hot-toast'

export default function VideoAnalysis3MEvaluation() {
  const { t } = useLang()
  const [jobs, setJobs] = useState([])
  const [selectedJob, setSelectedJob] = useState('')
  const [loadingJobs, setLoadingJobs] = useState(true)
  const [evaluating, setEvaluating] = useState(false)
  const [result, setResult] = useState(null)
  
  const fileInputRef = useRef(null)

  useEffect(() => {
    // Fetch completed jobs for dropdown
    api.get('/video-analysis/history', { params: { limit: 100, status: 'complete' } })
      .then(res => {
        setJobs(res.data.items || [])
        if (res.data.items?.length > 0) {
          setSelectedJob(res.data.items[0].job_id)
        }
      })
      .catch(err => {
        console.error('Failed to fetch jobs:', err)
        toast.error('Gagal memuat daftar analisis')
      })
      .finally(() => setLoadingJobs(false))
  }, [])

  const handleDownloadTemplate = async () => {
    if (!selectedJob) return
    try {
      const res = await api.get(`/evaluation/template/${selectedJob}`, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `template_ground_truth_${selectedJob.substring(0, 8)}.csv`)
      document.body.appendChild(link)
      link.click()
      link.parentNode.removeChild(link)
    } catch (err) {
      console.error(err)
      toast.error('Gagal mendownload template')
    }
  }

  const handleFileChange = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    if (!selectedJob) {
      toast.error('Pilih job terlebih dahulu')
      return
    }

    const formData = new FormData()
    formData.append('csv_file', file)

    setEvaluating(true)
    setResult(null)
    const toastId = toast.loading(t('video3m.evalCalculating') || 'Menghitung metrik...')

    try {
      // 1. Upload CSV
      const uploadRes = await api.post(`/evaluation/annotations/csv`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      
      if (uploadRes.data.errors && uploadRes.data.errors.length > 0) {
        toast.error(`Beberapa baris gagal: ${uploadRes.data.errors[0]}`, { id: toastId })
        return
      }

      toast.loading('CSV berhasil diunggah. Menjalankan benchmark...', { id: toastId })

      // 2. Run Benchmark
      const benchmarkRes = await api.post(`/evaluation/benchmark/${selectedJob}`)
      
      // 3. Fetch Full Report
      const reportRes = await api.get(`/evaluation/report/${selectedJob}`)
      setResult({ ...reportRes.data, files: benchmarkRes.data.files })
      toast.success('Evaluasi berhasil!', { id: toastId })
    } catch (err) {
      console.error(err)
      const msg = err.response?.data?.detail || 'Gagal melakukan evaluasi'
      toast.error(msg, { id: toastId })
    } finally {
      setEvaluating(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const handleDragOver = (e) => {
    e.preventDefault()
  }

  const handleDrop = (e) => {
    e.preventDefault()
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0]
      const dt = new DataTransfer()
      dt.items.add(file)
      if (fileInputRef.current) {
        fileInputRef.current.files = dt.files
        const event = new Event('change', { bubbles: true })
        fileInputRef.current.dispatchEvent(event)
      }
    }
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="font-display text-2xl font-bold text-slate-900">{t('video3m.evalTitle') || 'Validasi & Metrik 3M'}</h1>
        <p className="text-slate-500 mt-1">{t('video3m.evalSubtitle') || 'Bandingkan hasil analisis komputer dengan penilaian manusia (Observer) untuk jurnal ilmiah.'}</p>
      </motion.div>

      {/* Control Panel */}
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="grid grid-cols-1 md:grid-cols-3 gap-4">
        
        {/* Step 1: Select Job */}
        <div className="card p-5 border-l-4 border-l-violet-500">
          <h3 className="font-semibold text-slate-900 mb-2 flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-violet-100 text-violet-700 flex items-center justify-center text-xs">1</span>
            {t('video3m.evalSelectJob') || 'Pilih Video'}
          </h3>
          <p className="text-xs text-slate-500 mb-3">{t('video3m.evalSelectJobHint') || 'Pilih analisis selesai'}</p>
          <select
            className="w-full text-sm rounded-xl border-slate-200 focus:border-violet-500 focus:ring-violet-500"
            value={selectedJob}
            onChange={e => setSelectedJob(e.target.value)}
            disabled={loadingJobs}
          >
            {loadingJobs ? <option>Loading...</option> : jobs.length === 0 ? <option>Tidak ada data</option> : null}
            {jobs.map(job => (
              <option key={job.job_id} value={job.job_id}>
                {job.video_name} ({new Date(job.created_at).toLocaleDateString()})
              </option>
            ))}
          </select>
        </div>

        {/* Step 2: Download Template */}
        <div className="card p-5 border-l-4 border-l-blue-500">
          <h3 className="font-semibold text-slate-900 mb-2 flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-xs">2</span>
            {t('video3m.evalDownloadTemplate') || 'Download Template'}
          </h3>
          <p className="text-xs text-slate-500 mb-3 line-clamp-2">{t('video3m.evalDownloadDesc') || 'Berikan ke Observer untuk diisi'}</p>
          <button
            onClick={handleDownloadTemplate}
            disabled={!selectedJob}
            className="w-full py-2 bg-blue-50 text-blue-700 hover:bg-blue-100 font-medium rounded-xl text-sm transition-colors disabled:opacity-50"
          >
            Download CSV
          </button>
        </div>

        {/* Step 3: Upload Ground Truth */}
        <div 
          className="card p-5 border-l-4 border-l-teal-500 border-2 border-dashed border-teal-200 hover:border-teal-400 transition-colors cursor-pointer"
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <h3 className="font-semibold text-slate-900 mb-2 flex items-center gap-2 pointer-events-none">
            <span className="w-6 h-6 rounded-full bg-teal-100 text-teal-700 flex items-center justify-center text-xs">3</span>
            {t('video3m.evalUploadTruth') || 'Upload Ground Truth'}
          </h3>
          <div className="flex flex-col items-center justify-center py-2 pointer-events-none">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" className="text-teal-500 mb-2" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
            <p className="text-xs font-medium text-slate-600">{t('video3m.evalDropzone') || 'Drag & drop CSV'}</p>
          </div>
          <input 
            type="file" 
            accept=".csv" 
            className="hidden" 
            ref={fileInputRef}
            onChange={handleFileChange}
          />
        </div>

      </motion.div>

      {/* Results Section */}
      <AnimatePresence mode="wait">
        {result && (
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="space-y-6">
            
            <div className="flex items-center justify-between border-b border-slate-200 pb-2">
              <h2 className="text-lg font-bold text-slate-900">{t('video3m.evalResultsTitle') || 'Hasil Evaluasi Metrik'}</h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              {/* Classification Metrics */}
              <div className="card p-5">
                <h3 className="font-semibold text-slate-800 mb-4">{t('video3m.evalTabClassification') || 'Metrik Klasifikasi'} (Overall)</h3>
                <div className="space-y-4">
                  {(() => {
                    const overallCm = result.confusion_matrices?.find(cm => cm.component === 'Overall 3M Score') || result.confusion_matrices?.[0];
                    return overallCm ? (
                      <>
                        <MetricRow label={t('video3m.evalAccuracy') || 'Akurasi'} value={overallCm.accuracy} />
                        <MetricRow label={t('video3m.evalPrecision') || 'Precision (Macro)'} value={overallCm.precision} />
                        <MetricRow label={t('video3m.evalRecall') || 'Recall (Macro)'} value={overallCm.recall} />
                        <MetricRow label={t('video3m.evalF1') || 'F1-Score (Macro)'} value={overallCm.f1_score} highlight />
                      </>
                    ) : <p className="text-sm text-slate-500">Data tidak tersedia</p>
                  })()}
                </div>
              </div>

              {/* Agreement Metrics */}
              <div className="card p-5">
                <h3 className="font-semibold text-slate-800 mb-4">{t('video3m.evalTabAgreement') || 'Metrik Kesepakatan'}</h3>
                <div className="space-y-4">
                  {(() => {
                    const overallCorr = result.correlation_metrics?.find(c => c.component === 'Overall 3M Score') || result.correlation_metrics?.[0];
                    const overallCm = result.confusion_matrices?.find(cm => cm.component === 'Overall 3M Score') || result.confusion_matrices?.[0];
                    return overallCorr ? (
                      <>
                        <MetricRow 
                          label={t('video3m.evalPearson') || 'Pearson r'} 
                          value={overallCorr.pearson_r} 
                          desc={t('video3m.evalPearsonDesc')}
                          highlight
                        />
                        <MetricRow 
                          label={t('video3m.evalKappa') || "Cohen's Kappa"} 
                          value={overallCm?.cohen_kappa} 
                          desc={t('video3m.evalKappaDesc')}
                        />
                        <MetricRow 
                          label="Mean Absolute Error (MAE)" 
                          value={overallCorr.mae} 
                          inverse
                        />
                        <MetricRow 
                          label="Root Mean Squared Error (RMSE)" 
                          value={overallCorr.rmse} 
                          inverse
                        />
                      </>
                    ) : <p className="text-sm text-slate-500">Data tidak tersedia</p>
                  })()}
                </div>
              </div>

            </div>

            {/* Visualizations */}
            <div>
              <h3 className="font-semibold text-slate-800 mb-4">{t('video3m.evalVisualizations') || 'Visualisasi Data'}</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="card p-4 flex flex-col items-center">
                  <p className="text-sm font-medium text-slate-600 mb-3">{t('video3m.evalConfusionMatrix') || 'Confusion Matrix Heatmap'}</p>
                  <img 
                    src={result.files?.['cm_Overall 3M Score']?.replace('backend/uploads', '/uploads') || ''} 
                    alt="Confusion Matrix" 
                    className="max-w-full h-auto rounded-lg border border-slate-100"
                    onError={(e) => { e.target.style.display = 'none'; e.target.nextElementSibling.style.display = 'block'; }}
                  />
                  <div style={{display: 'none'}} className="text-xs text-slate-400 p-4">Gambar tidak tersedia</div>
                </div>
                
                <div className="card p-4 flex flex-col items-center">
                  <p className="text-sm font-medium text-slate-600 mb-3">{t('video3m.evalScatterPlot') || 'Scatter Plot Korelasi'}</p>
                  <img 
                    src={result.files?.['scatter_Overall 3M Score']?.replace('backend/uploads', '/uploads') || ''} 
                    alt="Scatter Plot" 
                    className="max-w-full h-auto rounded-lg border border-slate-100"
                    onError={(e) => { e.target.style.display = 'none'; e.target.nextElementSibling.style.display = 'block'; }}
                  />
                  <div style={{display: 'none'}} className="text-xs text-slate-400 p-4">Gambar tidak tersedia</div>
                </div>
              </div>
            </div>

          </motion.div>
        )}
      </AnimatePresence>

    </div>
  )
}

function MetricRow({ label, value, desc, highlight = false, inverse = false }) {
  if (value === undefined || value === null) return null
  
  // Format based on value
  const numValue = typeof value === 'number' ? value : parseFloat(value)
  let formatted = numValue.toFixed(3)
  
  // Determine color
  let colorClass = 'text-slate-700 bg-slate-100'
  if (highlight) {
    if (inverse) {
      // Lower is better
      if (numValue < 0.1) colorClass = 'text-teal-700 bg-teal-100'
      else if (numValue < 0.2) colorClass = 'text-blue-700 bg-blue-100'
      else if (numValue < 0.3) colorClass = 'text-amber-700 bg-amber-100'
      else colorClass = 'text-red-700 bg-red-100'
    } else {
      // Higher is better
      if (numValue >= 0.8) colorClass = 'text-teal-700 bg-teal-100'
      else if (numValue >= 0.6) colorClass = 'text-blue-700 bg-blue-100'
      else if (numValue >= 0.4) colorClass = 'text-amber-700 bg-amber-100'
      else colorClass = 'text-red-700 bg-red-100'
    }
  }

  return (
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm font-medium text-slate-700">{label}</p>
        {desc && <p className="text-xs text-slate-500">{desc}</p>}
      </div>
      <span className={`px-3 py-1 rounded-lg text-sm font-bold font-mono ${colorClass}`}>
        {formatted}
      </span>
    </div>
  )
}

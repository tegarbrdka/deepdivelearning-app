import { useState, useCallback, useEffect } from 'react'
import { useDropzone } from 'react-dropzone'
import { motion, AnimatePresence } from 'framer-motion'
import { RadialBarChart, RadialBar, ResponsiveContainer } from 'recharts'
import { format } from 'date-fns'
import { id } from 'date-fns/locale'
import toast from 'react-hot-toast'
import api from '../../services/api'
import { useLang } from '../../contexts/LanguageContext'

function ConfidenceGauge({ confidence, label, fileType }) {
  const color = fileType === 'video'
    ? (label === 'Deep Learning' ? '#8b5cf6' : '#64748b')
    : (label === 'Baik' ? '#2dd4bf' : label === 'Cukup' ? '#fbbf24' : '#f87171')

  const data = [
    { value: confidence, fill: color },
    { value: 100 - confidence, fill: 'rgba(255,255,255,0.05)' },
  ]

  return (
    <div className="relative w-48 h-48 mx-auto">
      <ResponsiveContainer width="100%" height="100%">
        <RadialBarChart
          cx="50%" cy="50%"
          innerRadius="70%" outerRadius="100%"
          startAngle={220} endAngle={-40}
          data={data}
          barSize={12}
        >
          <RadialBar dataKey="value" cornerRadius={6} background={{ fill: 'rgba(255,255,255,0.03)' }} />
        </RadialBarChart>
      </ResponsiveContainer>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-display text-3xl font-bold text-slate-900">{confidence?.toFixed(1)}%</span>
        <span className="text-xs text-slate-500 mt-0.5">Confidence</span>
      </div>
    </div>
  )
}

function LabelBadgeLarge({ label, fileType }) {
  const styles = {
    'Deep Learning': 'bg-violet-500/20 text-violet-800 dark:text-violet-300 border-violet-500/40',
    'Bukan Deep Learning': 'bg-slate-500/20 text-slate-600 border-slate-500/40',
    'Baik': 'bg-teal-400/20 text-teal-800 dark:text-teal-300 border-teal-400/40',
    'Cukup': 'bg-amber-400/20 text-amber-800 dark:text-amber-300 border-amber-400/40',
    'Kurang': 'bg-red-400/20 text-red-800 dark:text-red-300 border-red-400/40',
  }
  return (
    <span className={`text-sm font-bold px-4 py-1.5 rounded-full border ${styles[label] || 'bg-slate-500/20 text-slate-600 border-slate-500/40'}`}>
      {label}
    </span>
  )
}

export default function UploadPredict() {
  const { t } = useLang()
  const [file, setFile] = useState(null)
  const [filePreview, setFilePreview] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState(null)
  const [recentHistory, setRecentHistory] = useState([])

  // Fetch recent history
  useEffect(() => {
    api.get('/predict/history')
      .then(r => setRecentHistory(r.data.slice(0, 3)))
      .catch(() => {})
  }, [result])

  // Calculate estimated time based on file size
  const getEstimatedTime = (bytes) => {
    if (!bytes) return null
    const mb = bytes / (1024 * 1024)
    // Rough estimate: 2 seconds per MB for video, 1 second per MB for documents
    const isVideo = file?.name.toLowerCase().endsWith('.mp4')
    const seconds = Math.ceil(mb * (isVideo ? 2 : 1))
    if (seconds < 60) return `~${seconds} detik`
    return `~${Math.ceil(seconds / 60)} menit`
  }

  const onDrop = useCallback((accepted) => {
    if (accepted[0]) {
      const droppedFile = accepted[0]
      setFile(droppedFile)
      setResult(null)
      
      // Generate preview for video
      if (droppedFile.type.startsWith('video/')) {
        const url = URL.createObjectURL(droppedFile)
        setFilePreview(url)
      } else {
        setFilePreview(null)
      }
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'video/mp4': ['.mp4'],
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    maxFiles: 1,
  })

  const handlePredict = async () => {
    if (!file) return
    setUploading(true)
    setProgress(0)
    setResult(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await api.post('/predict', formData, {
        onUploadProgress: (e) => {
          setProgress(Math.round((e.loaded / e.total) * 80))
        },
      })
      setProgress(100)
      setResult(res.data)
      toast.success('Prediksi berhasil!')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Prediksi gagal')
    } finally {
      setUploading(false)
    }
  }

  const getFileIcon = (f) => {
    if (!f) return null
    const name = f.name.toLowerCase()
    if (name.endsWith('.mp4')) return '🎬'
    if (name.endsWith('.pdf')) return '📄'
    return '📝'
  }

  const formatSize = (bytes) => {
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  }

  return (
    <div className="flex gap-6 max-w-7xl">
      {/* Main content */}
      <div className="flex-1 space-y-6">
        <div>
          <h1 className="font-display text-2xl font-bold text-slate-900">{t('uploadPredict.title')}</h1>
          <p className="text-slate-500 mt-1">{t('uploadPredict.subtitle')}</p>
        </div>

      {/* Dropzone */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        {...getRootProps()}
        className={`card p-10 flex flex-col items-center justify-center cursor-pointer transition-all duration-200 border-2 border-dashed
          ${isDragActive ? 'border-violet-500 bg-violet-500/5' : 'border-slate-200 hover:border-violet-600/50 hover:bg-slate-50/40'}`}
      >
        <input {...getInputProps()} />
        <motion.div
          animate={{ scale: isDragActive ? 1.1 : 1 }}
          className="w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-600/30 to-teal-500/20 flex items-center justify-center mb-4"
        >
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#8b5cf6" strokeWidth="1.5">
            <path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/>
          </svg>
        </motion.div>
        <p className="text-slate-900 font-semibold text-lg">
          {isDragActive ? 'Lepaskan file di sini' : 'Drag & drop atau klik untuk pilih'}
        </p>
        <p className="text-slate-500 text-sm mt-2">Mendukung: .mp4, .pdf, .docx • Maks 500MB</p>

        <div className="flex gap-3 mt-5">
          {[
            { icon: '🎬', label: 'Video (.mp4)', desc: 'Klasifikasi Deep Learning' },
            { icon: '📄', label: 'PDF (.pdf)', desc: 'Deteksi kualitas dokumen' },
            { icon: '📝', label: 'Word (.docx)', desc: 'Deteksi kualitas dokumen' },
          ].map((t) => (
            <div key={t.label} className="px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 text-center">
              <div className="text-lg">{t.icon}</div>
              <div className="text-xs text-slate-600 font-medium mt-0.5">{t.label}</div>
              <div className="text-xs text-slate-500">{t.desc}</div>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Selected file with preview */}
      <AnimatePresence>
        {file && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="card p-4"
          >
            <div className="flex items-start gap-4">
              {/* Preview thumbnail */}
              {filePreview ? (
                <div className="w-24 h-24 rounded-xl overflow-hidden bg-slate-50 flex-shrink-0">
                  <video src={filePreview} className="w-full h-full object-cover" />
                </div>
              ) : (
                <div className="w-24 h-24 rounded-xl bg-slate-50 flex items-center justify-center text-4xl flex-shrink-0">
                  {getFileIcon(file)}
                </div>
              )}
              
              {/* File info */}
              <div className="flex-1 min-w-0">
                <p className="text-slate-900 font-medium truncate">{file.name}</p>
                <p className="text-slate-500 text-sm mt-1">{formatSize(file.size)}</p>
                {getEstimatedTime(file.size) && (
                  <div className="flex items-center gap-2 mt-2">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#64748b" strokeWidth="2">
                      <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
                    </svg>
                    <span className="text-xs text-slate-500">Estimasi: {getEstimatedTime(file.size)}</span>
                  </div>
                )}
              </div>
              
              <button 
                onClick={() => { 
                  setFile(null)
                  setResult(null)
                  if (filePreview) URL.revokeObjectURL(filePreview)
                  setFilePreview(null)
                }} 
                className="text-slate-500 hover:text-red-400 transition-colors"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Upload progress */}
      <AnimatePresence>
        {uploading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="card p-4 space-y-3"
          >
            <div className="flex items-center gap-3">
              <div className="w-5 h-5 border-2 border-violet-400/30 border-t-violet-400 rounded-full animate-spin" />
              <span className="text-slate-600 text-sm">
                {progress < 80 ? 'Mengupload file...' : 'Model sedang memproses...'}
              </span>
              <span className="text-violet-400 text-sm ml-auto font-mono">{progress}%</span>
            </div>
            <div className="h-2 bg-slate-50 rounded-full overflow-hidden">
              <motion.div
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.3 }}
                className="h-full bg-gradient-to-r from-violet-600 to-teal-500 rounded-full"
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Predict button */}
      {file && !uploading && !result && (
        <motion.button
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          onClick={handlePredict}
          className="btn-primary w-full py-3 text-base"
        >
          🚀 Mulai Prediksi
        </motion.button>
      )}

      {/* Result */}
      <AnimatePresence>
        {result && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="card p-8"
          >
            <div className="text-center mb-6">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-400/10 border border-teal-400/20 text-teal-400 text-xs font-semibold mb-3">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="20 6 9 17 4 12"/></svg>
                Prediksi Selesai
              </div>
              <h3 className="font-display text-xl font-bold text-slate-900 mb-1">Hasil Klasifikasi</h3>
              <p className="text-slate-500 text-sm">{result.file_name}</p>
            </div>

            <div className="flex flex-col items-center gap-6">
              <ConfidenceGauge
                confidence={result.confidence}
                label={result.label}
                fileType={result.file_type}
              />

              <div className="text-center">
                <p className="text-slate-500 text-sm mb-2">Label Klasifikasi</p>
                <LabelBadgeLarge label={result.label} fileType={result.file_type} />
              </div>

              {result.low_confidence && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="w-full max-w-md p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-start gap-3"
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fbbf24" strokeWidth="2" className="flex-shrink-0 mt-0.5">
                    <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
                    <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
                  </svg>
                  <div className="flex-1">
                    <p className="text-amber-800 dark:text-amber-300 font-semibold text-sm">Confidence Rendah</p>
                    <p className="text-amber-700/70 dark:text-amber-200/70 text-xs mt-1">
                      Hasil prediksi di bawah threshold {result.threshold}%. Model kurang yakin dengan klasifikasi ini.
                    </p>
                  </div>
                </motion.div>
              )}

              <div className="grid grid-cols-2 gap-4 w-full max-w-xs">
                <div className="card p-3 text-center bg-slate-50">
                  <p className="text-xs text-slate-500 mb-1">Jenis File</p>
                  <p className="text-sm font-semibold text-slate-900 capitalize">{result.file_type}</p>
                </div>
                <div className="card p-3 text-center bg-slate-50">
                  <p className="text-xs text-slate-500 mb-1">Confidence</p>
                  <p className="text-sm font-semibold text-slate-900 font-mono">{result.confidence?.toFixed(2)}%</p>
                </div>
              </div>

              <button
                onClick={() => { setFile(null); setResult(null) }}
                className="btn-secondary"
              >
                Upload File Baru
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      </div>

      {/* Sidebar - Recent History */}
      {recentHistory.length > 0 && (
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="w-80 flex-shrink-0"
        >
          <div className="card p-4 sticky top-24">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-display font-semibold text-slate-900 text-sm">{t('uploadPredict.recentPredictions')}</h3>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#64748b" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
              </svg>
            </div>
            <div className="space-y-3">
              {recentHistory.map((p) => (
                <div key={p.id} className="p-3 rounded-lg bg-slate-50 hover:bg-navy-750 transition-colors">
                  <div className="flex items-start gap-3">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                      p.file_type === 'video' ? 'bg-violet-500/20' : 'bg-amber-400/20'
                    }`}>
                      {p.file_type === 'video' ? (
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#a78bfa" strokeWidth="2">
                          <polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2"/>
                        </svg>
                      ) : (
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#fbbf24" strokeWidth="2">
                          <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                          <polyline points="14 2 14 8 20 8"/>
                        </svg>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-slate-900 text-xs font-medium truncate">{p.file_name}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className={`text-xs px-2 py-0.5 rounded-full ${
                          p.label === 'Deep Learning' || p.label === 'Baik' 
                            ? 'bg-teal-400/10 text-teal-400' 
                            : p.label === 'Cukup'
                            ? 'bg-amber-400/10 text-amber-400'
                            : 'bg-slate-500/10 text-slate-500'
                        }`}>
                          {p.label}
                        </span>
                        <span className="text-xs text-slate-500">{p.confidence?.toFixed(0)}%</span>
                      </div>
                      <p className="text-xs text-slate-600 mt-1">
                        {p.created_at ? format(new Date(p.created_at), 'd MMM, HH:mm', { locale: id }) : '-'}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      )}
    </div>
  )
}

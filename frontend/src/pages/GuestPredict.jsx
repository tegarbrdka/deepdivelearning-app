import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import api from '../services/api'

export default function GuestPredict() {
  const navigate = useNavigate()
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [limits, setLimits] = useState(null)
  const [estimatedTime, setEstimatedTime] = useState(0)

  useEffect(() => {
    fetchLimits()
  }, [])

  const fetchLimits = async () => {
    try {
      const res = await api.get('/guest/limits')
      setLimits(res.data)
    } catch (err) {
      console.error('Failed to fetch limits:', err)
    }
  }

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0]
    if (!selectedFile) return

    // Check file size
    const maxSize = (limits?.max_file_size_mb || 50) * 1024 * 1024
    if (selectedFile.size > maxSize) {
      toast.error(`File terlalu besar! Maksimal ${limits?.max_file_size_mb || 50}MB untuk mode guest`)
      return
    }

    setFile(selectedFile)
    setResult(null)

    // Estimate processing time
    const sizeMB = selectedFile.size / (1024 * 1024)
    const isVideo = selectedFile.name.toLowerCase().endsWith('.mp4')
    const estimate = isVideo ? sizeMB * 2 : sizeMB * 1
    setEstimatedTime(Math.ceil(estimate))

    // Preview for video
    if (isVideo) {
      const url = URL.createObjectURL(selectedFile)
      setPreview(url)
    } else {
      setPreview(null)
    }
  }

  const handlePredict = async () => {
    if (!file) {
      toast.error('Pilih file terlebih dahulu')
      return
    }

    if (!limits?.is_allowed) {
      toast.error('Batas prediksi guest tercapai. Silakan daftar untuk akses unlimited.')
      return
    }

    setLoading(true)
    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await api.post('/guest/predict', formData)
      setResult(res.data)
      await fetchLimits() // Update remaining count
      toast.success('Prediksi berhasil!')
    } catch (err) {
      const msg = err.response?.data?.detail || 'Gagal melakukan prediksi'
      toast.error(msg)
      if (err.response?.status === 429) {
        await fetchLimits()
      }
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setFile(null)
    setPreview(null)
    setResult(null)
    setEstimatedTime(0)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-navy-900 via-navy-800 to-navy-900">
      {/* Header */}
      <div className="bg-slate-50/50 border-b border-slate-200 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-600 to-teal-500 flex items-center justify-center">
              <span className="text-slate-900 font-bold text-lg">D</span>
            </div>
            <div>
              <h1 className="font-display text-xl font-bold text-slate-900">DeepDiveLearning</h1>
              <p className="text-xs text-slate-500">Mode Guest</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/login')}
              className="px-4 py-2 text-sm text-slate-600 hover:text-slate-900 transition-colors"
            >
              Masuk
            </button>
            <button
              onClick={() => navigate('/register')}
              className="px-4 py-2 text-sm bg-gradient-to-r from-violet-600 to-teal-500 text-slate-900 rounded-lg hover:shadow-lg transition-all"
            >
              Daftar Gratis
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-12">
        {/* Limits Banner */}
        {limits && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className={`mb-6 p-4 rounded-xl border ${
              limits.remaining_predictions > 0
                ? 'bg-teal-500/10 border-teal-500/30'
                : 'bg-red-500/10 border-red-500/30'
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-lg ${
                  limits.remaining_predictions > 0 ? 'bg-teal-500/20' : 'bg-red-500/20'
                } flex items-center justify-center`}>
                  <span className={`text-2xl ${
                    limits.remaining_predictions > 0 ? 'text-teal-400' : 'text-red-400'
                  }`}>
                    {limits.remaining_predictions > 0 ? '✓' : '✗'}
                  </span>
                </div>
                <div>
                  <p className="text-slate-900 font-semibold">
                    {limits.remaining_predictions} / {limits.max_predictions} Prediksi Tersisa
                  </p>
                  <p className="text-xs text-slate-500">
                    Mode guest dibatasi {limits.max_predictions} prediksi per {limits.rate_limit_window_minutes} menit
                  </p>
                </div>
              </div>
              {limits.remaining_predictions === 0 && (
                <button
                  onClick={() => navigate('/register')}
                  className="px-4 py-2 bg-gradient-to-r from-violet-600 to-teal-500 text-slate-900 text-sm rounded-lg hover:shadow-lg transition-all"
                >
                  Daftar untuk Unlimited
                </button>
              )}
            </div>
          </motion.div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Upload Section */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="card p-6 space-y-5"
          >
            <div>
              <h2 className="font-display text-xl font-bold text-slate-900 mb-1">Coba Prediksi</h2>
              <p className="text-sm text-slate-500">Upload video (.mp4) atau dokumen (.pdf, .docx)</p>
            </div>

            <div className="space-y-4">
              <div className="border-2 border-dashed border-slate-200 rounded-xl p-8 text-center hover:border-violet-500 transition-colors">
                <input
                  type="file"
                  accept=".mp4,.pdf,.docx"
                  onChange={handleFileChange}
                  className="hidden"
                  id="guest-file-input"
                  disabled={loading || !limits?.is_allowed}
                />
                <label htmlFor="guest-file-input" className="cursor-pointer">
                  <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-slate-50 flex items-center justify-center">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#8b5cf6" strokeWidth="2">
                      <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12"/>
                    </svg>
                  </div>
                  <p className="text-slate-900 font-semibold mb-1">
                    {file ? file.name : 'Klik untuk upload file'}
                  </p>
                  <p className="text-xs text-slate-500">
                    Maksimal {limits?.max_file_size_mb || 50}MB • MP4, PDF, DOCX
                  </p>
                </label>
              </div>

              {file && preview && (
                <div className="rounded-xl overflow-hidden bg-slate-50">
                  <video src={preview} controls className="w-full max-h-48" />
                </div>
              )}

              {file && estimatedTime > 0 && (
                <div className="bg-slate-50 rounded-xl p-3 text-xs text-slate-500">
                  ⏱️ Estimasi waktu proses: ~{estimatedTime} detik
                </div>
              )}

              <div className="flex gap-3">
                <motion.button
                  whileTap={{ scale: 0.97 }}
                  onClick={handlePredict}
                  disabled={!file || loading || !limits?.is_allowed}
                  className="flex-1 btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? (
                    <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Memproses...</>
                  ) : (
                    <>🚀 Prediksi Sekarang</>
                  )}
                </motion.button>
                {file && (
                  <button
                    onClick={handleReset}
                    className="px-4 py-2 bg-slate-50 text-slate-600 rounded-lg hover:bg-navy-700 transition-colors"
                  >
                    Reset
                  </button>
                )}
              </div>
            </div>

            {/* Info */}
            <div className="bg-slate-50 rounded-xl p-4 space-y-2 text-xs text-slate-500">
              <p className="font-semibold text-slate-600">ℹ️ Mode Guest:</p>
              <ul className="space-y-1 ml-4">
                <li>• Maksimal {limits?.max_predictions || 5} prediksi per jam</li>
                <li>• Ukuran file maksimal {limits?.max_file_size_mb || 50}MB</li>
                <li>• Hasil tidak disimpan</li>
                <li>• Daftar untuk fitur lengkap</li>
              </ul>
            </div>
          </motion.div>

          {/* Result Section */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="card p-6"
          >
            <h3 className="font-display text-xl font-bold text-slate-900 mb-5">Hasil Prediksi</h3>

            <AnimatePresence mode="wait">
              {!result ? (
                <motion.div
                  key="empty"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex flex-col items-center justify-center py-16 text-center"
                >
                  <div className="w-20 h-20 rounded-2xl bg-slate-50 flex items-center justify-center mb-4">
                    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#4a5568" strokeWidth="1.5">
                      <circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>
                    </svg>
                  </div>
                  <p className="text-slate-500">Upload file dan klik prediksi untuk melihat hasil</p>
                </motion.div>
              ) : (
                <motion.div
                  key="result"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="space-y-4"
                >
                  {/* Low confidence warning */}
                  {result.low_confidence && (
                    <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4">
                      <div className="flex items-start gap-3">
                        <span className="text-2xl">⚠️</span>
                        <div className="flex-1">
                          <p className="text-amber-800 dark:text-amber-300 font-semibold text-sm mb-1">Confidence Rendah</p>
                          <p className="text-xs text-amber-700/70 dark:text-amber-200/70">
                            Confidence di bawah threshold ({result.confidence_threshold}%). Hasil mungkin kurang akurat.
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Result card */}
                  <div className="bg-gradient-to-br from-violet-500/10 to-teal-500/10 border border-violet-500/30 rounded-xl p-6">
                    <div className="text-center mb-4">
                      <p className="text-sm text-slate-500 mb-2">Label Prediksi</p>
                      <p className="font-display text-3xl font-bold text-slate-900 mb-1">{result.label}</p>
                      <p className="text-sm text-slate-500">
                        Confidence: <span className="text-violet-800 dark:text-violet-300 font-semibold">{result.confidence}%</span>
                      </p>
                    </div>
                    <div className="h-2 bg-slate-50 rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${result.confidence}%` }}
                        transition={{ duration: 1, ease: "easeOut" }}
                        className="h-full bg-gradient-to-r from-violet-500 to-teal-500"
                      />
                    </div>
                  </div>

                  {/* File info */}
                  <div className="bg-slate-50 rounded-xl p-4 space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-500">File:</span>
                      <span className="text-slate-900">{result.file_name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Tipe:</span>
                      <span className="text-slate-900 capitalize">{result.file_type}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Sisa Prediksi:</span>
                      <span className="text-teal-800 dark:text-teal-300 font-semibold">{result.remaining_predictions}</span>
                    </div>
                  </div>

                  {/* CTA */}
                  <div className="bg-gradient-to-r from-violet-600/20 to-teal-600/20 border border-violet-500/30 rounded-xl p-5 text-center">
                    <p className="text-slate-900 font-semibold mb-2">💎 Upgrade ke Akun Penuh</p>
                    <p className="text-xs text-slate-500 mb-4">
                      Dapatkan prediksi unlimited, simpan riwayat, export hasil, dan fitur lengkap lainnya
                    </p>
                    <button
                      onClick={() => navigate('/register')}
                      className="w-full py-2.5 bg-gradient-to-r from-violet-600 to-teal-500 text-slate-900 rounded-lg hover:shadow-lg transition-all font-semibold"
                    >
                      Daftar Gratis Sekarang
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </div>
      </div>
    </div>
  )
}

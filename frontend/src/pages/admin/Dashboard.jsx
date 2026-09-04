import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell
} from 'recharts'
import api from '../../services/api'
import { useLang } from '../../contexts/LanguageContext'
import useAuthStore from '../../stores/authStore'

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs shadow-xl">
      <p className="text-slate-500 mb-1">{label}</p>
      <p className="text-violet-600 font-semibold">{payload[0].value} prediksi</p>
    </div>
  )
}

function StatCard({ label, value, sub, icon, color, delay, onClick }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      onClick={onClick}
      className={`card p-5 relative overflow-hidden ${onClick ? 'cursor-pointer hover:ring-1 hover:ring-violet-500/40 transition-all' : ''}`}
    >
      <div className={`absolute -top-6 -right-6 w-20 h-20 rounded-full ${color} blur-2xl opacity-20`} />
      <div className="relative z-10 flex items-start justify-between">
        <div>
          <p className="text-slate-500 text-xs mb-2">{label}</p>
          <p className="font-display text-3xl font-bold text-slate-900">{value ?? '—'}</p>
          {sub && <p className="text-slate-600 text-xs mt-1">{sub}</p>}
        </div>
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${color} bg-opacity-15`}>
          {icon}
        </div>
      </div>
    </motion.div>
  )
}

function QuickLink({ label, sub, path, icon, color }) {
  const navigate = useNavigate()
  return (
    <motion.div
      whileHover={{ y: -2 }}
      whileTap={{ scale: 0.98 }}
      onClick={() => navigate(path)}
      className="card p-4 cursor-pointer hover:ring-1 hover:ring-violet-500/30 transition-all group"
    >
      <div className={`w-9 h-9 rounded-xl ${color} flex items-center justify-center mb-3`}>
        {icon}
      </div>
      <p className="text-slate-900 text-sm font-semibold">{label}</p>
      {sub && <p className="text-slate-600 text-xs mt-0.5">{sub}</p>}
    </motion.div>
  )
}

export default function AdminDashboard() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const { t } = useLang()
  const { user } = useAuthStore()

  useEffect(() => {
    api.get('/admin/stats')
      .then(r => setStats(r.data))
      .catch(() => setStats({
        total_predictions: 0, total_users: 0, total_video_dataset: 0,
        cnn_accuracy: null, cnn_f1: null, cnn_version: null, cnn_versions: 0,
        daily_predictions: [], dli_total: 0, dli_avg_score: null,
        label_distribution: { deep_learning: 0, not_deep_learning: 0 },
      }))
      .finally(() => setLoading(false))
  }, [])

  const maxBar = Math.max(...(stats?.daily_predictions?.map(d => d.count) || [1]), 1)
  const totalLabels = (stats?.label_distribution?.deep_learning || 0) + (stats?.label_distribution?.not_deep_learning || 0)

  const now = new Date()
  const hour = now.getHours()
  const greeting = hour < 12 ? '🌤️ Selamat pagi' : hour < 17 ? '☀️ Selamat siang' : '🌙 Selamat malam'

  return (
    <div className="space-y-6 max-w-6xl">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} className="flex items-start justify-between">
        <div>
          <p className="text-slate-500 text-sm">{greeting}, <span className="text-slate-600 font-medium">{user?.username}</span></p>
          <h1 className="font-display text-2xl font-bold text-slate-900 mt-0.5">{t('adminDashboard.title')}</h1>
          <p className="text-slate-500 text-sm mt-1">{t('adminDashboard.subtitle')}</p>
        </div>
        <div className="text-right text-xs text-slate-600">
          <p>{now.toLocaleDateString('id-ID', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}</p>
        </div>
      </motion.div>

      {/* Stat cards */}
      {loading ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <div key={i} className="card h-28 animate-pulse bg-slate-50" />)}
        </div>
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            label={t('adminDashboard.totalPredictions')} value={stats?.total_predictions}
            sub={`${stats?.label_distribution?.deep_learning || 0} DL · ${stats?.label_distribution?.not_deep_learning || 0} Non-DL`}
            color="bg-violet-500" delay={0.05}
            icon={<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#a78bfa" strokeWidth="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>}
          />
          <StatCard
            label={t('adminDashboard.totalUsers')} value={stats?.total_users}
            color="bg-teal-500" delay={0.1}
            icon={<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2dd4bf" strokeWidth="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/></svg>}
          />
          <StatCard
            label={t('adminDashboard.videoDataset')} value={stats?.total_video_dataset}
            color="bg-blue-500" delay={0.15}
            icon={<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" strokeWidth="2"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2"/></svg>}
          />
          <StatCard
            label="DLI Dianalisis" value={stats?.dli_total}
            sub={stats?.dli_avg_score ? `Rata-rata skor: ${stats.dli_avg_score}%` : 'Belum ada data'}
            color="bg-amber-500" delay={0.2}
            icon={<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fbbf24" strokeWidth="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>}
          />
        </div>
      )}

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Daily predictions bar chart */}
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }} className="card p-6 lg:col-span-2">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className="font-display font-semibold text-slate-900">{t('adminDashboard.last7Days')}</h3>
              <p className="text-slate-600 text-xs mt-0.5">Total: {stats?.total_predictions || 0} prediksi</p>
            </div>
            <div className="w-8 h-8 rounded-lg bg-violet-500/10 flex items-center justify-center">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#a78bfa" strokeWidth="2"><rect x="18" y="3" width="4" height="18"/><rect x="10" y="8" width="4" height="13"/><rect x="2" y="13" width="4" height="8"/></svg>
            </div>
          </div>
          {loading ? (
            <div className="h-[180px] flex items-center justify-center">
              <div className="w-6 h-6 border-2 border-violet-400/30 border-t-violet-400 rounded-full animate-spin" />
            </div>
          ) : stats?.daily_predictions?.length > 0 ? (
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={stats.daily_predictions} barSize={28}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(139,92,246,0.05)' }} />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {stats.daily_predictions.map((entry, i) => (
                    <Cell key={i} fill={entry.count === maxBar ? '#8b5cf6' : '#312e81'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[180px] flex items-center justify-center text-slate-600 text-sm">{t('adminDashboard.noPredictionData')}</div>
          )}
        </motion.div>

        {/* CNN Model status */}
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="card p-6 flex flex-col">
          <div className="flex items-center justify-between mb-5">
            <h3 className="font-display font-semibold text-slate-900">Model CNN</h3>
            <span className={`text-xs px-2 py-1 rounded-full font-semibold ${stats?.cnn_accuracy ? 'bg-teal-400/10 text-teal-600 border border-teal-400/20' : 'bg-slate-700 text-slate-500'}`}>
              {stats?.cnn_version || 'Tidak ada'}
            </span>
          </div>
          {loading ? (
            <div className="flex-1 flex items-center justify-center">
              <div className="w-6 h-6 border-2 border-teal-400/30 border-t-teal-400 rounded-full animate-spin" />
            </div>
          ) : stats?.cnn_accuracy ? (
            <div className="flex-1 space-y-4">
              {[
                { label: 'Accuracy', value: stats.cnn_accuracy, color: 'bg-violet-500', text: 'text-violet-600' },
                { label: 'F1 Score', value: stats.cnn_f1, color: 'bg-teal-500', text: 'text-teal-600' },
              ].map(m => (
                <div key={m.label}>
                  <div className="flex justify-between text-xs mb-1.5">
                    <span className="text-slate-500">{m.label}</span>
                    <span className={`font-mono font-bold ${m.text}`}>{m.value?.toFixed(1)}%</span>
                  </div>
                  <div className="h-2.5 bg-slate-50 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${m.value || 0}%` }}
                      transition={{ duration: 1, ease: 'easeOut', delay: 0.4 }}
                      className={`h-full ${m.color} rounded-full`}
                    />
                  </div>
                </div>
              ))}
              <div className="pt-2 border-t border-slate-200">
                <p className="text-xs text-slate-600">{stats.cnn_versions} versi tersimpan</p>
              </div>
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-center gap-2">
              <div className="w-12 h-12 rounded-xl bg-slate-50 flex items-center justify-center">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#4a5568" strokeWidth="1.5"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/></svg>
              </div>
              <p className="text-slate-600 text-xs">Belum ada model aktif</p>
            </div>
          )}
        </motion.div>
      </div>

      {/* Label distribution + Quick links */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Label distribution */}
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35 }} className="card p-6">
          <h3 className="font-display font-semibold text-slate-900 mb-4">Distribusi Label</h3>
          {totalLabels > 0 ? (
            <div className="space-y-4">
              {[
                { label: 'Deep Learning', count: stats?.label_distribution?.deep_learning || 0, color: 'bg-violet-500', text: 'text-violet-600' },
                { label: 'Bukan DL', count: stats?.label_distribution?.not_deep_learning || 0, color: 'bg-slate-600', text: 'text-slate-500' },
              ].map(item => {
                const pct = totalLabels > 0 ? Math.round((item.count / totalLabels) * 100) : 0
                return (
                  <div key={item.label}>
                    <div className="flex justify-between text-xs mb-1.5">
                      <span className="text-slate-500">{item.label}</span>
                      <span className={`font-mono font-semibold ${item.text}`}>{item.count} ({pct}%)</span>
                    </div>
                    <div className="h-2.5 bg-slate-50 rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${pct}%` }}
                        transition={{ duration: 0.8, ease: 'easeOut', delay: 0.45 }}
                        className={`h-full ${item.color} rounded-full`}
                      />
                    </div>
                  </div>
                )
              })}
              <div className="pt-2 border-t border-slate-200 flex items-center justify-between text-xs">
                <span className="text-slate-600">Total prediksi</span>
                <span className="text-slate-500 font-mono font-semibold">{totalLabels}</span>
              </div>
            </div>
          ) : (
            <div className="h-24 flex items-center justify-center text-slate-600 text-sm">Belum ada data</div>
          )}
        </motion.div>

        {/* Quick links */}
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }} className="lg:col-span-2">
          <p className="text-xs text-slate-600 font-semibold uppercase tracking-wider mb-3">Akses Cepat</p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <QuickLink
              label="Dataset Video" sub="Kelola data training"
              path="/admin/cnn/dataset"
              color="bg-violet-500/10"
              icon={<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#a78bfa" strokeWidth="2"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2"/></svg>}
            />
            <QuickLink
              label="Training CNN" sub="Latih model baru"
              path="/admin/cnn/train"
              color="bg-blue-500/10"
              icon={<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" strokeWidth="2"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/></svg>}
            />
            <QuickLink
              label="Monitor Model" sub="Lihat performa"
              path="/admin/cnn/models"
              color="bg-teal-500/10"
              icon={<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2dd4bf" strokeWidth="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>}
            />
            <QuickLink
              label="Dashboard DLI" sub="Analitik dokumen"
              path="/admin/dli/dashboard"
              color="bg-amber-500/10"
              icon={<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fbbf24" strokeWidth="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>}
            />
          </div>
        </motion.div>
      </div>
    </div>
  )
}

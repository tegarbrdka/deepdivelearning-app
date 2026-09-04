import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import api from '../../services/api'
import useAuthStore from '../../stores/authStore'
import { format } from 'date-fns'
import { id } from 'date-fns/locale'
import { useLang } from '../../contexts/LanguageContext'

function StatCard({ label, value, icon, color, delay, trend, change }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      className="card p-6 relative overflow-hidden"
    >
      <div className="flex items-center justify-between mb-4">
        <div className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 ${color}`}>
          {icon}
        </div>
        {change !== undefined && (
          <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-semibold ${
            change >= 0 ? 'bg-teal-400/10 text-teal-400' : 'bg-red-400/10 text-red-400'
          }`}>
            {change >= 0 ? (
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <polyline points="18 15 12 9 6 15"/>
              </svg>
            ) : (
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <polyline points="6 9 12 15 18 9"/>
              </svg>
            )}
            {Math.abs(change)}%
          </div>
        )}
      </div>
      <div>
        <p className="font-display text-3xl font-bold text-slate-900 mb-1">{value}</p>
        <p className="text-slate-500 text-sm">{label}</p>
      </div>
      {trend && trend.length > 0 && (
        <div className="mt-4 h-12">
          <svg className="w-full h-full" viewBox="0 0 140 48" preserveAspectRatio="none">
            <defs>
              <linearGradient id={`gradient-${label}`} x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="currentColor" stopOpacity="0.3" />
                <stop offset="100%" stopColor="currentColor" stopOpacity="0" />
              </linearGradient>
            </defs>
            {/* Area fill */}
            <path
              d={`M 0 48 ${trend.map((val, i) => {
                const x = (i / (trend.length - 1)) * 140
                const maxVal = Math.max(...trend, 1)
                const y = 48 - (val / maxVal) * 40
                return `L ${x} ${y}`
              }).join(' ')} L 140 48 Z`}
              fill={`url(#gradient-${label})`}
              className="text-violet-400"
            />
            {/* Line */}
            <path
              d={`M ${trend.map((val, i) => {
                const x = (i / (trend.length - 1)) * 140
                const maxVal = Math.max(...trend, 1)
                const y = 48 - (val / maxVal) * 40
                return `${x} ${y}`
              }).join(' L ')}`}
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="text-violet-400"
            />
          </svg>
        </div>
      )}
    </motion.div>
  )
}

function LabelBadge({ label, fileType }) {
  if (fileType === 'video') {
    return label === 'Deep Learning'
      ? <span className="badge-deep-learning">{label}</span>
      : <span className="badge-bukan">{label}</span>
  }
  if (label === 'Baik') return <span className="badge-baik">{label}</span>
  if (label === 'Cukup') return <span className="badge-cukup">{label}</span>
  return <span className="badge-kurang">{label}</span>
}

export default function UserDashboard() {
  const { t } = useLang()
  const { user } = useAuthStore()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/user/dashboard')
      .then(r => setData(r.data))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[1,2,3].map(i => <div key={i} className="card p-6 h-24 animate-pulse bg-slate-50" />)}
      </div>
      <div className="card p-6 h-64 animate-pulse bg-slate-50" />
    </div>
  )

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Welcome */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mb-2">
        <h1 className="font-display text-2xl font-bold text-slate-900">
          {t('userDashboard.welcome')}, <span className="text-violet-400">{user?.username}</span> 👋
        </h1>
        <p className="text-slate-500 mt-1">{t('userDashboard.subtitle')}</p>
      </motion.div>

      {/* Weekly comparison banner */}
      {data?.this_week_count !== undefined && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="grid grid-cols-1 gap-4"
        >
          {/* Weekly stats */}
          <div className="card p-4 bg-gradient-to-r from-violet-600/10 to-teal-500/10 border-violet-500/20">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-violet-500/20 flex items-center justify-center">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#a78bfa" strokeWidth="2">
                    <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
                  </svg>
                </div>
                <div>
                  <p className="text-slate-900 font-semibold text-sm">Minggu Ini</p>
                  <p className="text-slate-500 text-xs">vs minggu lalu</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-slate-900 font-bold text-xl">{data.this_week_count}</p>
                <div className={`flex items-center gap-1 text-xs font-semibold ${
                  data.change_percent >= 0 ? 'text-teal-400' : 'text-red-400'
                }`}>
                  {data.change_percent >= 0 ? '↑' : '↓'} {Math.abs(data.change_percent)}%
                  <span className="text-slate-500">({data.last_week_count})</span>
                </div>
              </div>
            </div>
          </div>


        </motion.div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          label="Total Prediksi"
          value={data?.total_predictions ?? 0}
          color="bg-violet-600/20"
          delay={0.1}
          trend={data?.trend_data}
          change={data?.change_percent}
          icon={<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#a78bfa" strokeWidth="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>}
        />
        <StatCard
          label="Prediksi Video"
          value={data?.video_predictions ?? 0}
          color="bg-teal-400/20"
          delay={0.2}
          icon={<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2dd4bf" strokeWidth="2"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2"/></svg>}
        />
        <StatCard
          label="Prediksi Dokumen"
          value={data?.document_predictions ?? 0}
          color="bg-amber-400/20"
          delay={0.3}
          icon={<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#fbbf24" strokeWidth="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>}
        />
      </div>

      {/* Quick actions */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.35 }}
        className="grid grid-cols-1 sm:grid-cols-2 gap-4"
      >
        <Link to="/predict">
          <div className="card p-6 hover:border-violet-600/50 hover:bg-slate-50 transition-all cursor-pointer group">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-violet-600 to-teal-500 flex items-center justify-center shadow-lg shadow-violet-500/20 group-hover:scale-105 transition-transform">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2"><path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>
              </div>
              <div>
                <p className="font-semibold text-slate-900">{t('userDashboard.uploadPredict')}</p>
                <p className="text-slate-500 text-sm">{t('userDashboard.uploadPredictDesc')}</p>
              </div>
            </div>
          </div>
        </Link>
        <Link to="/history">
          <div className="card p-6 hover:border-teal-400/30 hover:bg-slate-50 transition-all cursor-pointer group">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-teal-400/15 border border-teal-400/20 flex items-center justify-center group-hover:scale-105 transition-transform">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2dd4bf" strokeWidth="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              </div>
              <div>
                <p className="font-semibold text-slate-900">{t('userDashboard.predictionHistory')}</p>
                <p className="text-slate-500 text-sm">{t('userDashboard.predictionHistoryDesc')}</p>
              </div>
            </div>
          </div>
        </Link>
      </motion.div>

      {/* Label Distribution */}
      {data?.label_distribution && Object.keys(data.label_distribution).length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="card p-6"
        >
          <h3 className="font-display font-semibold text-slate-900 mb-4">{t('userDashboard.labelDistribution')}</h3>
          <div className="space-y-3">
            {Object.entries(data.label_distribution).map(([label, count], i) => {
              const percentage = ((count / data.total_predictions) * 100).toFixed(1)
              const colors = {
                'Deep Learning': { bg: 'bg-violet-500', text: 'text-violet-400' },
                'Bukan Deep Learning': { bg: 'bg-slate-500', text: 'text-slate-500' },
                'Baik': { bg: 'bg-teal-500', text: 'text-teal-400' },
                'Cukup': { bg: 'bg-amber-500', text: 'text-amber-400' },
                'Kurang': { bg: 'bg-red-500', text: 'text-red-400' },
              }
              const color = colors[label] || { bg: 'bg-slate-500', text: 'text-slate-500' }
              
              return (
                <div key={label}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-slate-600">{label}</span>
                    <div className="flex items-center gap-2">
                      <span className={`text-sm font-semibold ${color.text}`}>{count}</span>
                      <span className="text-xs text-slate-500">({percentage}%)</span>
                    </div>
                  </div>
                  <div className="h-2 bg-slate-50 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${percentage}%` }}
                      transition={{ duration: 0.8, delay: 0.5 + i * 0.1 }}
                      className={`h-full ${color.bg} rounded-full`}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </motion.div>
      )}

      {/* Achievements */}
      {data?.achievements && data.achievements.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.42 }}
          className="card p-6"
        >
          <h3 className="font-display font-semibold text-slate-900 mb-4">Pencapaian</h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {data.achievements.map((achievement, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.5 + i * 0.1 }}
                className="p-4 rounded-xl bg-gradient-to-br from-violet-600/10 to-teal-500/10 border border-violet-500/20 text-center"
              >
                <div className="text-3xl mb-2">{achievement.icon}</div>
                <p className="text-slate-900 font-semibold text-sm">{achievement.title}</p>
                <p className="text-slate-500 text-xs mt-1">{achievement.desc}</p>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Recent predictions */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.45 }}
        className="card overflow-hidden"
      >
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <h3 className="font-display font-semibold text-slate-900">Prediksi Terbaru</h3>
          <Link to="/history" className="text-violet-400 hover:text-violet-800 dark:text-violet-300 text-sm">Lihat semua →</Link>
        </div>
        {data?.recent?.length === 0 ? (
          <div className="p-12 text-center">
            <svg className="w-12 h-12 text-slate-600 mx-auto mb-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="12" cy="12" r="10"/><path d="M8 12h8M12 8v8"/></svg>
            <p className="text-slate-500">Belum ada prediksi. Coba upload file pertama Anda!</p>
          </div>
        ) : (
          <div className="divide-y divide-navy-800">
            {data?.recent?.map((p) => (
              <div key={p.id} className="px-6 py-3 flex items-center gap-4 hover:bg-slate-50/50 transition-colors">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${p.file_type === 'video' ? 'bg-violet-500/20' : 'bg-amber-400/20'}`}>
                  {p.file_type === 'video'
                    ? <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#a78bfa" strokeWidth="2"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2"/></svg>
                    : <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#fbbf24" strokeWidth="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                  }
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-slate-900 truncate">{p.file_name}</p>
                  <p className="text-xs text-slate-500">{p.created_at ? format(new Date(p.created_at), 'd MMM yyyy, HH:mm', { locale: id }) : '-'}</p>
                </div>
                <LabelBadge label={p.label} fileType={p.file_type} />
                <span className="text-sm font-mono text-slate-500">{p.confidence?.toFixed(1)}%</span>
              </div>
            ))}
          </div>
        )}
      </motion.div>
    </div>
  )
}

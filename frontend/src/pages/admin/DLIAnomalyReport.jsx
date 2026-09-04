import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import api from '../../services/api'
import { useLang } from '../../contexts/LanguageContext'
import { exportToPDF, exportToWord } from '../../utils/exportDLIAnomaly'

const GRADE_CONFIG = {
  4: { label: 'Grade 4', color: 'text-teal-600', bg: 'bg-teal-400/10', border: 'border-teal-400/30' },
  3: { label: 'Grade 3', color: 'text-blue-600',  bg: 'bg-blue-400/10',  border: 'border-blue-400/30' },
  2: { label: 'Grade 2', color: 'text-amber-600', bg: 'bg-amber-400/10', border: 'border-amber-400/30' },
  1: { label: 'Grade 1', color: 'text-red-600',   bg: 'bg-red-400/10',   border: 'border-red-400/30' },
}

function StatCard({ label, value, color = 'text-slate-900' }) {
  return (
    <div className="card p-4 text-center">
      <p className={`font-display text-2xl font-bold ${color}`}>{value}</p>
      <p className="text-xs text-slate-500 mt-1">{label}</p>
    </div>
  )
}

function AnomalySection({ title, description, icon, items, renderItem, emptyMsg, casesLabel }) {
  return (
    <div className="card p-5 space-y-3">
      <div className="flex items-start gap-3">
        <span className="text-xl">{icon}</span>
        <div>
          <h3 className="font-display font-semibold text-slate-900">{title}</h3>
          <p className="text-xs text-slate-500 mt-0.5">{description}</p>
        </div>
        <span className="ml-auto text-xs font-bold px-2 py-1 rounded-full bg-slate-50 text-slate-500">
          {items.length} {casesLabel}
        </span>
      </div>
      {items.length === 0 ? (
        <p className="text-xs text-slate-600 italic pl-8">{emptyMsg}</p>
      ) : (
        <div className="space-y-2 pl-8">
          {items.map((item, i) => renderItem(item, i))}
        </div>
      )}
    </div>
  )
}

export default function DLIAnomalyReport() {
  const { t } = useLang()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [exporting, setExporting] = useState(false)

  const fetchReport = () => {
    setLoading(true)
    setError(null)
    api.get('/admin/dli/anomaly-report')
      .then(r => setData(r.data))
      .catch(e => setError(e.response?.data?.detail || t('anomalyReport.loadError')))
      .finally(() => setLoading(false))
  }

  const handleExportPDF = async () => {
    if (!data) return
    setExporting(true)
    try {
      await exportToPDF(data, t)
      toast.success(t('anomalyReport.exportSuccess') || 'Export PDF berhasil!')
    } catch (err) {
      toast.error(t('anomalyReport.exportError') || 'Export PDF gagal')
      console.error(err)
    } finally {
      setExporting(false)
    }
  }

  const handleExportWord = async () => {
    if (!data) return
    setExporting(true)
    try {
      await exportToWord(data, t)
      toast.success(t('anomalyReport.exportSuccess') || 'Export Word berhasil!')
    } catch (err) {
      toast.error(t('anomalyReport.exportError') || 'Export Word gagal')
      console.error(err)
    } finally {
      setExporting(false)
    }
  }

  useEffect(() => { fetchReport() }, [])

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-8 h-8 border-2 border-teal-400/30 border-t-teal-400 rounded-full animate-spin" />
    </div>
  )

  if (error) return (
    <div className="card p-6 text-center text-red-600">{error}</div>
  )

  const r = data?.ringkasan

  return (
    <div className="max-w-5xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold text-slate-900">{t('anomalyReport.title')}</h1>
          <p className="text-slate-500 mt-1">{t('anomalyReport.subtitle')}</p>
        </div>
        <div className="flex items-center gap-2">
          <button 
            onClick={handleExportPDF} 
            disabled={exporting || !data}
            className="btn-secondary text-sm flex items-center gap-2 disabled:opacity-50"
          >
            {exporting ? (
              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              '📄'
            )}
            {t('anomalyReport.exportPDF') || 'Export PDF'}
          </button>
          <button 
            onClick={handleExportWord} 
            disabled={exporting || !data}
            className="btn-secondary text-sm flex items-center gap-2 disabled:opacity-50"
          >
            {exporting ? (
              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              '📝'
            )}
            {t('anomalyReport.exportWord') || 'Export Word'}
          </button>
          <button onClick={fetchReport} className="btn-secondary text-sm">
            🔄 {t('anomalyReport.refresh')}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <StatCard label={t('anomalyReport.totalDli')} value={r.total_prediksi_dli} />
        <StatCard label={t('anomalyReport.grade4')} value={r.grade_4} color="text-teal-600" />
        <StatCard label={t('anomalyReport.grade3')} value={r.grade_3} color="text-blue-600" />
        <StatCard label={t('anomalyReport.grade2')} value={r.grade_2} color="text-amber-600" />
        <StatCard label={t('anomalyReport.grade1')} value={r.grade_1} color="text-red-600" />
      </div>

      <div className="flex flex-wrap gap-2">
        {[
          { label: 'Ketimpangan Skor', count: r.total_anomali_1, color: 'text-orange-600 bg-orange-400/10 border-orange-400/30' },
          { label: 'Skor Tidak Wajar', count: r.total_anomali_2, color: 'text-red-600 bg-red-400/10 border-red-400/30' },
          { label: 'Ketidakseimbangan Mayor', count: r.total_anomali_3, color: 'text-amber-600 bg-amber-400/10 border-amber-400/30' },
        ].map(a => (
          <span key={a.label} className={`text-xs font-semibold px-3 py-1.5 rounded-full border ${a.color}`}>
            {a.label}: {a.count} {t('anomalyReport.cases')}
          </span>
        ))}
      </div>

      <AnomalySection
        icon="⚠️"
        title={t('anomalyReport.anomaly1Title')}
        description={t('anomalyReport.anomaly1Desc')}
        items={data.anomali_1_grade4_aspek_lemah}
        emptyMsg={t('anomalyReport.noAnomaly')}
        casesLabel={t('anomalyReport.cases')}
        renderItem={(item, i) => (
          <motion.div key={i} initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            className="p-3 rounded-lg bg-white border border-orange-500/20 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono text-white bg-teal-600 px-2 py-0.5 rounded font-bold">DLI {item.dli_score?.toFixed(1)}%</span>
                <span className="text-sm font-semibold text-slate-700 truncate max-w-md">{item.file}</span>
              </div>
              <div className="flex flex-wrap items-center gap-1.5">
                {['mindful', 'meaningful', 'joyful', 'pedagogis', 'digital'].map(asp => {
                  const sc = item.all_scores?.[asp];
                  if (sc === undefined) return null;
                  const isWeak = item.weak_aspects?.[asp] !== undefined;
                  return (
                    <span key={asp} className={`text-[10px] px-1.5 py-0.5 rounded border ${isWeak ? 'bg-red-500/15 text-red-700 border-red-500/30 font-bold' : 'bg-slate-100 text-slate-500 border-slate-200'}`}>
                      {asp}: {sc.toFixed(1)}%
                    </span>
                  )
                })}
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
               <button className="btn-secondary text-[11px] py-1.5 px-3 whitespace-nowrap shadow-sm hover:shadow" onClick={() => window.location.href = '/admin/dli/history'}>🔍 Cek di Riwayat</button>
            </div>
          </motion.div>
        )}
      />

      <AnomalySection
        icon="🔴"
        title={t('anomalyReport.anomaly2Title')}
        description={t('anomalyReport.anomaly2Desc')}
        items={data.anomali_2_grade1_aspek_kuat}
        emptyMsg={t('anomalyReport.noAnomaly')}
        casesLabel={t('anomalyReport.cases')}
        renderItem={(item, i) => (
          <motion.div key={i} initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            className="p-3 rounded-lg bg-white border border-red-500/20 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono text-white bg-red-600 px-2 py-0.5 rounded font-bold">DLI {item.dli_score?.toFixed(1)}%</span>
                <span className="text-sm font-semibold text-slate-700 truncate max-w-md">{item.file}</span>
              </div>
              <div className="flex flex-wrap items-center gap-1.5">
                {['mindful', 'meaningful', 'joyful', 'pedagogis', 'digital'].map(asp => {
                  const sc = item.all_scores?.[asp];
                  if (sc === undefined) return null;
                  const isStrong = item.strong_aspects?.[asp] !== undefined;
                  return (
                    <span key={asp} className={`text-[10px] px-1.5 py-0.5 rounded border ${isStrong ? 'bg-teal-500/15 text-teal-700 border-teal-500/30 font-bold' : 'bg-slate-100 text-slate-500 border-slate-200'}`}>
                      {asp}: {sc.toFixed(1)}%
                    </span>
                  )
                })}
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
               <button className="btn-secondary text-[11px] py-1.5 px-3 whitespace-nowrap shadow-sm hover:shadow" onClick={() => window.location.href = '/admin/dli/history'}>🔍 Cek di Riwayat</button>
            </div>
          </motion.div>
        )}
      />

      <AnomalySection
        icon="🟡"
        title={t('anomalyReport.anomaly3Title')}
        description={t('anomalyReport.anomaly3Desc')}
        items={data.anomali_3_grade23_aspek_sangat_kuat}
        emptyMsg={t('anomalyReport.noAnomaly')}
        casesLabel={t('anomalyReport.cases')}
        renderItem={(item, i) => (
          <motion.div key={i} initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            className="p-3 rounded-lg bg-white border border-amber-500/20 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className={`text-xs font-mono font-bold px-2 py-0.5 rounded text-white ${GRADE_CONFIG[item.grade]?.bg.replace('/10','')} ${GRADE_CONFIG[item.grade]?.color.replace('text-','bg-')}`}>
                  Grade {item.grade} — DLI {item.dli_score?.toFixed(1)}%
                </span>
                <span className="text-sm font-semibold text-slate-700 truncate max-w-md">{item.file}</span>
              </div>
              <div className="flex flex-wrap items-center gap-1.5">
                {['mindful', 'meaningful', 'joyful', 'pedagogis', 'digital'].map(asp => {
                  const sc = item.all_scores?.[asp];
                  if (sc === undefined) return null;
                  const isVeryStrong = item.very_strong_aspects?.[asp] !== undefined;
                  return (
                    <span key={asp} className={`text-[10px] px-1.5 py-0.5 rounded border ${isVeryStrong ? 'bg-amber-500/15 text-amber-700 border-amber-500/30 font-bold' : 'bg-slate-100 text-slate-500 border-slate-200'}`}>
                      {asp}: {sc.toFixed(1)}%
                    </span>
                  )
                })}
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
               <button className="btn-secondary text-[11px] py-1.5 px-3 whitespace-nowrap shadow-sm hover:shadow" onClick={() => window.location.href = '/admin/dli/history'}>🔍 Cek di Riwayat</button>
            </div>
          </motion.div>
        )}
      />

      {/* Anomali 4 */}
      <div className="card p-5 space-y-3">
        <div className="flex items-start gap-3">
          <span className="text-xl">🔍</span>
          <div>
            <h3 className="font-display font-semibold text-slate-900">{t('anomalyReport.anomaly4Title')}</h3>
            <p className="text-xs text-slate-500 mt-0.5">{t('anomalyReport.anomaly4Desc')}</p>
          </div>
        </div>
        {data.anomali_4_keyword_jarang_grade4.length === 0 ? (
          <p className="text-xs text-slate-600 italic pl-8">{t('anomalyReport.noGrade4Data')}</p>
        ) : (
          <div className="pl-8 space-y-1.5">
            {data.anomali_4_keyword_jarang_grade4.map((kw, i) => (
              <div key={i} className="flex items-center gap-3">
                <span className="text-xs text-slate-600 font-mono bg-slate-50 px-2 py-1 rounded">
                  "{kw.keyword}"
                </span>
                <div className="flex-1 h-1.5 bg-slate-50 rounded-full overflow-hidden">
                  <div className="h-full bg-violet-500/60 rounded-full"
                    style={{ width: `${Math.min(kw.persen_dokumen_grade4, 100)}%` }} />
                </div>
                <span className="text-xs text-slate-500 w-24 text-right">
                  {kw.frekuensi}x ({kw.persen_dokumen_grade4}%)
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Anomali 5 */}
      <div className="card p-5 space-y-3">
        <div className="flex items-start gap-3">
          <span className="text-xl">💬</span>
          <div>
            <h3 className="font-display font-semibold text-slate-900">{t('anomalyReport.anomaly5Title')}</h3>
            <p className="text-xs text-slate-500 mt-0.5">{t('anomalyReport.anomaly5Desc')}</p>
          </div>
          <span className="ml-auto text-xs font-bold px-2 py-1 rounded-full bg-slate-50 text-slate-500">
            {data.anomali_5_keyword_gap?.length ?? 0} {t('anomalyReport.candidates')}
          </span>
        </div>
        {!data.anomali_5_keyword_gap?.length ? (
          <p className="text-xs text-slate-600 italic pl-8">{t('anomalyReport.noGapData')}</p>
        ) : (
          <div className="pl-8 space-y-2">
            {data.anomali_5_keyword_gap.map((item, i) => (
              <div key={i} className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-200">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-emerald-600 font-mono">"{item.frasa}"</span>
                  <span className="text-xs text-slate-500">muncul {item.frekuensi}x</span>
                </div>
                <span className="text-xs text-slate-600 italic">{item.saran}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

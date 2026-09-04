import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import api from '../../services/api'
import { useLang } from '../../contexts/LanguageContext'

const CONFIG_KEYS = ['confidence_threshold', 'max_video_size_mb', 'max_doc_size_mb']

export default function SystemConfig() {
  const { t } = useLang()
  const [config, setConfig] = useState({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState({})
  const { register, handleSubmit, setValue } = useForm()

  useEffect(() => {
    api.get('/admin/config').then(r => {
      setConfig(r.data)
      Object.entries(r.data).forEach(([k, v]) => setValue(k, v))
    }).finally(() => setLoading(false))
  }, [])

  const saveKey = async (key, value) => {
    setSaving(s => ({ ...s, [key]: true }))
    try {
      await api.post('/admin/config', { key, value: String(value) })
      setConfig(c => ({ ...c, [key]: value }))
      toast.success(t('systemConfig.saveSuccess').replace('{key}', key))
    } catch {
      toast.error(t('systemConfig.saveError'))
    } finally {
      setSaving(s => ({ ...s, [key]: false }))
    }
  }

  const fieldType = (key) => ['confidence_threshold', 'max_video_size_mb', 'max_doc_size_mb'].includes(key) ? 'number' : 'text'
  const fieldMin = (key) => key === 'confidence_threshold' ? 0 : key.includes('size') ? 1 : undefined
  const fieldMax = (key) => key === 'confidence_threshold' ? 100 : undefined

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-slate-900">{t('systemConfig.title')}</h1>
        <p className="text-slate-500 mt-1">{t('systemConfig.subtitle')}</p>
      </div>

      {loading ? (
        <div className="space-y-4">{[...Array(5)].map((_, i) => <div key={i} className="card h-24 animate-pulse bg-slate-50" />)}</div>
      ) : (
        <div className="space-y-4">
          {CONFIG_KEYS.map((key, i) => {
            const field = t(`systemConfig.fields.${key}`)
            return (
              <motion.div key={key} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.07 }} className="card p-5">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <label className="font-semibold text-slate-900 text-sm">{field?.label || key}</label>
                    <p className="text-slate-500 text-xs mt-0.5">{field?.desc}</p>
                    <div className="mt-3 flex gap-2">
                      <input
                        {...register(key)}
                        type={fieldType(key)}
                        min={fieldMin(key)}
                        max={fieldMax(key)}
                        defaultValue={config[key]}
                        className="input-field flex-1 max-w-xs py-2 text-sm"
                      />
                      <motion.button
                        whileTap={{ scale: 0.95 }}
                        onClick={handleSubmit(data => saveKey(key, data[key]))}
                        disabled={saving[key]}
                        className="btn-primary py-2 px-4 text-sm flex items-center gap-1.5 disabled:opacity-60"
                      >
                        {saving[key]
                          ? <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                          : <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12"/></svg>}
                        {t('systemConfig.save')}
                      </motion.button>
                    </div>
                  </div>
                  <div className="flex-shrink-0">
                    <div className="px-2.5 py-1 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-500 font-mono">
                      {t('systemConfig.currentValue')}<span className="text-slate-600">{config[key] ?? '—'}</span>
                    </div>
                  </div>
                </div>
              </motion.div>
            )
          })}
        </div>
      )}

      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }} className="card p-6">
        <h3 className="font-display font-semibold text-slate-900 mb-1">{t('systemConfig.exportData')}</h3>
        <p className="text-slate-500 text-sm mb-4">{t('systemConfig.exportDataDesc')}</p>
        <div className="flex flex-wrap gap-3">
          <motion.button
            whileTap={{ scale: 0.97 }}
            onClick={async () => {
              try {
                const res = await api.get('/admin/export/dataset', { responseType: 'blob' })
                const url = URL.createObjectURL(res.data)
                const a = document.createElement('a'); a.href = url; a.download = 'dataset.xlsx'; a.click()
                URL.revokeObjectURL(url)
                toast.success(t('systemConfig.exportDatasetSuccess'))
              } catch { toast.error(t('systemConfig.exportError')) }
            }}
            className="btn-secondary flex items-center gap-2"
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            {t('systemConfig.exportDataset')}
          </motion.button>
          <motion.button
            whileTap={{ scale: 0.97 }}
            onClick={async () => {
              try {
                const res = await api.get('/admin/export/logs', { responseType: 'blob' })
                const url = URL.createObjectURL(res.data)
                const a = document.createElement('a'); a.href = url; a.download = 'logs.csv'; a.click()
                URL.revokeObjectURL(url)
                toast.success(t('systemConfig.exportLogsSuccess'))
              } catch { toast.error(t('systemConfig.exportError')) }
            }}
            className="btn-secondary flex items-center gap-2"
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            {t('systemConfig.exportLogs')}
          </motion.button>
        </div>
      </motion.div>
    </div>
  )
}

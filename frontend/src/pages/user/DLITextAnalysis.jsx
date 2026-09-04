import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import api from '../../services/api'
import HighlightedText from '../../components/dli/HighlightedText'
import RecommendationBox from '../../components/dli/RecommendationBox'
import { useLang } from '../../contexts/LanguageContext'

export default function DLITextAnalysis() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { t } = useLang()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('text')

  useEffect(() => {
    api.get(`/predict/document/${id}/dli`)
      .then(r => setData(r.data))
      .catch(() => {
        toast.error(t('dliText.loadError'))
        navigate('/dli-analysis')
      })
      .finally(() => setLoading(false))
  }, [id, navigate, t])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-teal-400/30 border-t-teal-400 rounded-full animate-spin" />
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="max-w-5xl space-y-6">
      <div className="flex items-center gap-2 text-sm text-slate-500">
        <button onClick={() => navigate('/dli-analysis')} className="hover:text-teal-400 transition-colors">
          {t('dli.title')}
        </button>
        <span>/</span>
        <button onClick={() => navigate(`/dli-analysis/${id}`)} className="hover:text-teal-400 transition-colors truncate max-w-xs">
          {data.file_name}
        </button>
        <span>/</span>
        <span className="text-slate-600">{t('dliText.breadcrumbText')}</span>
      </div>

      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="font-display text-2xl font-bold text-slate-900">{t('dliText.title')}</h1>
          <p className="text-slate-500 mt-1 truncate max-w-lg">{data.file_name}</p>
        </div>
        <button onClick={() => navigate(`/dli-analysis/${id}`)} className="btn-secondary text-sm">
          {t('dliText.backToDetail')}
        </button>
      </div>

      <div className="card p-4 flex items-center gap-4 flex-wrap">
        <div className="flex items-center gap-2">
          <span className="text-slate-500 text-sm">{t('dliText.dliScore')}:</span>
          <span className="font-display font-bold text-slate-900 text-lg">{data.dli_score?.toFixed(1)}%</span>
        </div>
        <div className="w-px h-5 bg-navy-700" />
        <span className="text-teal-400 text-sm font-semibold">{data.dli_category}</span>
        {data.keyword_statistics && (
          <>
            <div className="w-px h-5 bg-navy-700" />
            <div className="flex gap-3 text-xs">
              <span className="text-teal-400">🟢 {data.keyword_statistics.green ?? 0}</span>
              <span className="text-red-400">🔴 {data.keyword_statistics.red ?? 0}</span>
              <span className="text-blue-400">🔵 {data.keyword_statistics.blue ?? 0}</span>
              <span className="text-amber-400">🟡 {data.keyword_statistics.yellow ?? 0}</span>
            </div>
          </>
        )}
      </div>

      <div className="flex gap-1 p-1 bg-slate-50 rounded-xl w-fit">
        {[
          { key: 'text', label: `📝 ${t('dliText.tabText')}` },
          { key: 'recommendations', label: `💡 ${t('dliText.tabRecommendations')} (${data.recommendations?.length ?? 0})` },
        ].map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === tab.key ? 'bg-white text-white shadow' : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <motion.div key={activeTab} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }}>
        {activeTab === 'text' ? (
          <div className="card p-6">
            <HighlightedText
              html={data.highlighted_text ?? ''}
              statistics={data.keyword_statistics ?? {}}
              keywordsFound={data.keywords_found ?? {}}
            />
          </div>
        ) : (
          <div className="card p-6">
            <h3 className="font-display font-semibold text-slate-900 mb-4">{t('dliText.recommendations')}</h3>
            <RecommendationBox recommendations={data.recommendations ?? []} />
          </div>
        )}
      </motion.div>
    </div>
  )
}

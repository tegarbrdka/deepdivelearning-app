import { useState, useEffect, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import { format } from 'date-fns'
import { id } from 'date-fns/locale'
import api from '../../services/api'
import { useLang } from '../../contexts/LanguageContext'

export function DocumentDataset() {
  const [dataset, setDataset] = useState([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [label, setLabel] = useState('Baik')
  const [files, setFiles] = useState([])
  const [uploadType, setUploadType] = useState('file')
  const [groupName, setGroupName] = useState('Default')
  const [filterGroup, setFilterGroup] = useState('all')
  const [selectedIds, setSelectedIds] = useState([])
  const [selectMode, setSelectMode] = useState(false)
  const { t } = useLang()

  const fetchData = () => {
    setLoading(true)
    api.get('/admin/dataset/document').then(r => setDataset(r.data)).finally(() => setLoading(false))
  }
  useEffect(() => { fetchData() }, [])

  const onDrop = useCallback((accepted) => { setFiles(prev => [...prev, ...accepted]) }, [])
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: uploadType === 'csv' 
      ? { 'text/csv': ['.csv'] }
      : { 'application/pdf': ['.pdf'], 'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'] },
    multiple: true,
  })

  const handleUpload = async () => {
    if (!files.length) return toast.error(t('documentDataset.selectFileFirst'))
    setUploading(true)
    let success = 0
    for (const file of files) {
      const form = new FormData()
      form.append('file', file)
      form.append('group_name', groupName)
      if (uploadType === 'file') form.append('label', label)
      try {
        await api.post('/admin/dataset/document', form)
        success++
      } catch (err) {
        toast.error(`${file.name}: ${err.response?.data?.detail || t('documentDataset.uploadError')}`)
      }
    }
    if (success > 0) toast.success(t('documentDataset.uploadSuccess').replace('{count}', success))
    setFiles([]); fetchData(); setUploading(false)
  }

  const uniqueGroups = [...new Set(dataset.map(d => d.group_name || 'Default'))]
  const filteredDataset = filterGroup === 'all' ? dataset : dataset.filter(d => (d.group_name || 'Default') === filterGroup)

  const handleDelete = async (did) => {
    toast((t_toast) => (
      <div className="flex items-center gap-3">
        <div>
          <p className="font-semibold text-slate-900">{t('documentDataset.deleteConfirm')}</p>
          <p className="text-xs text-slate-500 mt-1">{t('documentDataset.deleteWarning')}</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => {
              toast.dismiss(t_toast.id)
              toast.promise(
                api.delete(`/admin/dataset/document/${did}`),
                {
                  loading: '...',
                  success: () => { fetchData(); return t('documentDataset.deleteSuccess') },
                  error: t('documentDataset.deleteError')
                }
              )
            }}
            className="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white text-sm rounded-lg transition-colors"
          >
            {t('documentDataset.deleteBtn')}
          </button>
          <button
            onClick={() => toast.dismiss(t_toast.id)}
            className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-900 text-sm rounded-lg transition-colors"
          >
            {t('documentDataset.cancelBtn')}
          </button>
        </div>
      </div>
    ), { duration: Infinity, style: { maxWidth: '500px' } })
  }

  const handleBulkDelete = async () => {
    if (selectedIds.length === 0) return toast.error(t('documentDataset.selectFileFirst'))
    
    toast((t_toast) => (
      <div className="flex items-center gap-3">
        <div>
          <p className="font-semibold text-slate-900">{t('documentDataset.deleteBulkConfirm').replace('{count}', selectedIds.length)}</p>
          <p className="text-xs text-slate-500 mt-1">{t('documentDataset.deleteWarning')}</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={async () => {
              toast.dismiss(t_toast.id)
              const deletePromises = selectedIds.map(id => api.delete(`/admin/dataset/document/${id}`))
              toast.promise(
                Promise.all(deletePromises),
                {
                  loading: `...`,
                  success: () => { 
                    setSelectedIds([])
                    setSelectMode(false)
                    fetchData()
                    return t('documentDataset.deleteBulkSuccess').replace('{count}', selectedIds.length)
                  },
                  error: t('documentDataset.deleteBulkError')
                }
              )
            }}
            className="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white text-sm rounded-lg transition-colors"
          >
            {t('documentDataset.deleteBulkBtn')}
          </button>
          <button
            onClick={() => toast.dismiss(t_toast.id)}
            className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-900 text-sm rounded-lg transition-colors"
          >
            {t('documentDataset.cancelBtn')}
          </button>
        </div>
      </div>
    ), { duration: Infinity, style: { maxWidth: '500px' } })
  }

  const toggleSelect = (id) => {
    setSelectedIds(prev => 
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    )
  }

  const toggleSelectAll = () => {
    if (selectedIds.length === filteredDataset.length) {
      setSelectedIds([])
    } else {
      setSelectedIds(filteredDataset.map(d => d.id))
    }
  }

  const labelCounts = { total: dataset.length, Baik: 0, Cukup: 0, Kurang: 0 }
  dataset.forEach(d => { if (labelCounts[d.label] !== undefined) labelCounts[d.label]++ })

  return (
    <div className="max-w-5xl space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-slate-900">{t('documentDataset.title')}</h1>
        <p className="text-slate-500 mt-1">{t('documentDataset.subtitle')}</p>
      </div>

      <div className="grid grid-cols-4 gap-4">
        {[
          { label: 'Total', value: labelCounts.total, color: 'text-slate-900' },
          { label: 'Baik', value: labelCounts.Baik, color: 'text-teal-600' },
          { label: 'Cukup', value: labelCounts.Cukup, color: 'text-amber-600' },
          { label: 'Kurang', value: labelCounts.Kurang, color: 'text-red-600' },
        ].map(s => (
          <div key={s.label} className="card p-4 text-center">
            <p className={`font-display text-2xl font-bold ${s.color}`}>{s.value}</p>
            <p className="text-xs text-slate-500 mt-0.5">{s.label}</p>
          </div>
        ))}
      </div>

      <div className="card p-6 space-y-4">
        <h3 className="font-display font-semibold text-slate-900">{t('documentDataset.addData')}</h3>
        
        <div className="flex gap-2 p-1 bg-slate-50 rounded-lg">
          <button
            onClick={() => { setUploadType('file'); setFiles([]) }}
            className={`flex-1 py-2 px-3 rounded-md text-sm font-medium transition-all ${uploadType === 'file' ? 'bg-teal-600 text-white' : 'text-slate-500 hover:text-white'}`}
          >
            📄 PDF/DOCX
          </button>
          <button
            onClick={() => { setUploadType('csv'); setFiles([]) }}
            className={`flex-1 py-2 px-3 rounded-md text-sm font-medium transition-all ${uploadType === 'csv' ? 'bg-teal-600 text-white' : 'text-slate-500 hover:text-white'}`}
          >
            📊 CSV Dataset
          </button>
        </div>

        {uploadType === 'csv' && (
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-500">
            <p className="font-semibold text-slate-600 mb-1">{t('documentDataset.csvFormat')}</p>
            <code className="text-teal-600">text,label</code>
            <p className="mt-1">"Teks dokumen...",Baik</p>
            <p className="text-slate-500 mt-2">{t('documentDataset.csvLabels')}</p>
          </div>
        )}

        <div {...getRootProps()} className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${isDragActive ? 'border-teal-400 bg-teal-400/5' : 'border-slate-200 hover:border-teal-400/40'}`}>
          <input {...getInputProps()} />
          <div className="text-3xl mb-2">{uploadType === 'csv' ? '📊' : '📄'}</div>
          <p className="text-slate-600 text-sm">
            {files.length > 0 ? `${files.length} file dipilih` : `Drag & drop atau klik pilih ${uploadType === 'csv' ? '.csv' : '.pdf atau .docx'} (bisa banyak file)`}
          </p>        </div>
        <div className="flex gap-3">
          <div className="flex-1">
            <label className="text-sm text-slate-500 block mb-1.5">{t('documentDataset.groupName')}</label>
            <input
              value={groupName}
              onChange={e => setGroupName(e.target.value)}
              className="input-field"
              placeholder={t('documentDataset.groupNamePlaceholder')}
            />
          </div>
          {uploadType === 'file' && (
            <div className="flex-1">
              <label className="text-sm text-slate-500 block mb-1.5">{t('documentDataset.qualityLabel')}</label>
              <select value={label} onChange={e => setLabel(e.target.value)} className="input-field">
                <option value="Baik">Baik</option>
                <option value="Cukup">Cukup</option>
                <option value="Kurang">Kurang</option>
              </select>
            </div>
          )}
          <div className={`flex items-end ${uploadType === 'csv' && 'flex-1'}`}>
            <motion.button onClick={handleUpload} disabled={uploading || !files.length} whileTap={{ scale: 0.97 }}
              className="btn-primary flex items-center gap-2 disabled:opacity-60 w-full"
              style={{ background: 'linear-gradient(135deg, #0f766e, #0d9488)' }}>
              {uploading ? <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> {t('documentDataset.uploading')}</> : `Upload${files.length > 1 ? ` (${files.length})` : ''}`}
            </motion.button>
          </div>
        </div>
      </div>

      <div className="card overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h3 className="font-display font-semibold text-slate-900">{t('documentDataset.listTitle')} ({filteredDataset.length})</h3>
            <select
              value={filterGroup}
              onChange={e => setFilterGroup(e.target.value)}
              className="text-xs px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-slate-600"
            >
              <option value="all">{t('documentDataset.allGroups')} ({dataset.length})</option>
              {uniqueGroups.map(g => (
                <option key={g} value={g}>{g} ({dataset.filter(d => (d.group_name || 'Default') === g).length})</option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-2">
            {selectMode && selectedIds.length > 0 && (
              <button
                onClick={handleBulkDelete}
                className="text-xs px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-700 text-white transition-all flex items-center gap-1.5"
              >
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/>
                </svg>
                {t('documentDataset.deleteBtn')} ({selectedIds.length})
              </button>
            )}
            <button
              onClick={() => {
                setSelectMode(!selectMode)
                setSelectedIds([])
              }}
              className={`text-xs px-3 py-1.5 rounded-lg transition-all ${
                selectMode 
                  ? 'bg-teal-600 hover:bg-teal-700 text-white' 
                  : 'bg-slate-50 hover:bg-navy-700 text-slate-600'
              }`}
            >
              {selectMode ? t('documentDataset.cancelSelect') : t('documentDataset.selectMultiple')}
            </button>
            <button
              onClick={async () => {
                try {
                  const res = await api.get('/admin/dataset/export-csv', { responseType: 'blob' })
                  const url = window.URL.createObjectURL(new Blob([res.data]))
                  const link = document.createElement('a')
                  link.href = url
                  link.setAttribute('download', 'dataset_documents.csv')
                  document.body.appendChild(link)
                  link.click()
                  link.remove()
                  toast.success(t('documentDataset.exportSuccess'))
                } catch (err) {
                  toast.error(err.response?.data?.detail || t('documentDataset.exportError'))
                }
              }}
              className="text-xs px-3 py-1.5 rounded-lg bg-slate-50 hover:bg-navy-700 text-teal-600 transition-all flex items-center gap-1.5"
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>
              {t('documentDataset.exportCsv')}
            </button>
          </div>
        </div>
        {loading ? (
          <div className="p-6 space-y-2">{[...Array(4)].map((_, i) => <div key={i} className="h-10 bg-slate-50 rounded-lg animate-pulse" />)}</div>
        ) : filteredDataset.length === 0 ? (
          <div className="p-12 text-center text-slate-500">{t('documentDataset.noData')}</div>
        ) : (
          <table className="w-full">
            <thead><tr className="border-b border-slate-200">
              {selectMode && (
                <th className="text-left px-4 py-3">
                  <input
                    type="checkbox"
                    checked={selectedIds.length === filteredDataset.length && filteredDataset.length > 0}
                    onChange={toggleSelectAll}
                    className="w-4 h-4 rounded border-slate-200 bg-slate-50 text-teal-600 focus:ring-teal-500 focus:ring-offset-navy-900"
                  />
                </th>
              )}
              <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">#</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">{t('documentDataset.fileName')}</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase">{t('documentDataset.group')}</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase">{t('documentDataset.label')}</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase">{t('documentDataset.date')}</th>
              <th className="text-right px-4 py-3 text-xs font-semibold text-slate-500 uppercase">{t('documentDataset.action')}</th>
            </tr></thead>
            <tbody className="divide-y divide-navy-800">
              {filteredDataset.map((d, i) => (
                <tr key={d.id} className="hover:bg-slate-50/30 transition-colors">
                  {selectMode && (
                    <td className="px-4 py-3">
                      <input
                        type="checkbox"
                        checked={selectedIds.includes(d.id)}
                        onChange={() => toggleSelect(d.id)}
                        className="w-4 h-4 rounded border-slate-200 bg-slate-50 text-teal-600 focus:ring-teal-500 focus:ring-offset-navy-900"
                      />
                    </td>
                  )}
                  <td className="px-6 py-3 text-slate-600 text-sm">{i + 1}</td>
                  <td className="px-6 py-3 text-slate-900 text-sm">{d.file_name}</td>
                  <td className="px-4 py-3">
                    <span className="text-xs px-2 py-1 rounded-md bg-slate-50 text-slate-500">{d.group_name || 'Default'}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={d.label === 'Baik' ? 'badge-baik' : d.label === 'Cukup' ? 'badge-cukup' : d.label.startsWith('CSV') ? 'badge-csv' : 'badge-kurang'}>{d.label}</span>
                  </td>
                  <td className="px-4 py-3 text-slate-500 text-xs">{d.created_at ? format(new Date(d.created_at), 'd MMM yyyy', { locale: id }) : '—'}</td>
                  <td className="px-4 py-3 text-right">
                    {!selectMode && (
                      <button onClick={() => handleDelete(d.id)} className="p-1.5 text-slate-600 hover:text-red-600 hover:bg-red-400/10 rounded-lg transition-all">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M9 6V4h6v2"/></svg>
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

export default DocumentDataset

import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import { format } from 'date-fns'
import { id } from 'date-fns/locale'
import api from '../../services/api'
import useAuthStore from '../../stores/authStore'
import { useLang } from '../../contexts/LanguageContext'

export default function Profile() {
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [updating, setUpdating] = useState(false)
  const [storageStats, setStorageStats] = useState(null)
  const [cleaningUp, setCleaningUp] = useState(false)
  const { user, login } = useAuthStore()
  const { t } = useLang()
  
  const { register, handleSubmit, formState: { errors }, reset, watch } = useForm()

  useEffect(() => {
    api.get('/auth/profile')
      .then(r => {
        setProfile(r.data)
        reset({
          username: r.data.username,
          email: r.data.email
        })
      })
      .finally(() => setLoading(false))
    
    // Fetch storage stats
    api.get('/storage/stats')
      .then(r => setStorageStats(r.data))
      .catch(() => {})
  }, [reset])

  const onSubmit = async (data) => {
    setUpdating(true)
    try {
      const payload = {}
      if (data.username !== profile.username) payload.username = data.username
      if (data.email !== profile.email) payload.email = data.email
      if (data.new_password) {
        payload.current_password = data.current_password
        payload.new_password = data.new_password
      }

      if (Object.keys(payload).length === 0) {
        toast.error(t('profile.noChanges'))
        return
      }

      const res = await api.put('/auth/profile', payload)
      
      if (payload.username) {
        login(localStorage.getItem('token'), { ...user, username: res.data.username })
      }
      
      toast.success(t('profile.updateSuccess'))
      setProfile({ ...profile, ...res.data })
      reset({
        username: res.data.username,
        email: res.data.email,
        current_password: '',
        new_password: '',
        confirm_password: ''
      })
    } catch (err) {
      toast.error(err.response?.data?.detail || t('profile.updateError'))
    } finally {
      setUpdating(false)
    }
  }

  const newPassword = watch('new_password')

  const handleCleanup = async () => {
    const confirmed = await new Promise(resolve => {
      toast((t_toast) => (
        <div className="flex flex-col gap-3">
          <p className="text-slate-900 font-semibold">{t('profile.cleanupConfirmTitle')}</p>
          <p className="text-slate-500 text-sm">{t('profile.cleanupConfirmDesc')}</p>
          <div className="flex gap-2">
            <button
              onClick={() => { toast.dismiss(t_toast.id); resolve(true) }}
              className="px-3 py-1.5 bg-violet-500 hover:bg-violet-600 text-white rounded-lg text-sm font-medium transition-colors"
            >
              {t('profile.cleanupConfirmBtn')}
            </button>
            <button
              onClick={() => { toast.dismiss(t_toast.id); resolve(false) }}
              className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-900 rounded-lg text-sm font-medium transition-colors"
            >
              {t('profile.cleanupCancelBtn')}
            </button>
          </div>
        </div>
      ), { duration: Infinity })
    })

    if (!confirmed) return

    setCleaningUp(true)
    try {
      const res = await api.post('/storage/cleanup?keep_count=50')
      toast.success(res.data.message)
      
      // Refresh storage stats
      const statsRes = await api.get('/storage/stats')
      setStorageStats(statsRes.data)
    } catch (err) {
      toast.error(t('profile.updateError'))
    } finally {
      setCleaningUp(false)
    }
  }

  if (loading) {
    return (
      <div className="max-w-2xl space-y-4">
        <div className="h-8 w-48 bg-slate-50 rounded animate-pulse" />
        <div className="card p-6 space-y-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-12 bg-slate-50 rounded animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-slate-900">{t('profile.title')}</h1>
        <p className="text-slate-500 mt-1">{t('profile.subtitle')}</p>
      </div>

      {/* Account Info */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="card p-6"
      >
        <h3 className="font-display font-semibold text-slate-900 mb-4">{t('profile.accountInfo')}</h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-slate-50 rounded-xl p-4">
            <p className="text-xs text-slate-500 mb-1">{t('profile.role')}</p>
            <p className="text-slate-900 font-semibold capitalize">{profile?.role}</p>
          </div>
          <div className="bg-slate-50 rounded-xl p-4">
            <p className="text-xs text-slate-500 mb-1">{t('profile.joinedSince')}</p>
            <p className="text-slate-900 font-semibold">
              {profile?.created_at ? format(new Date(profile.created_at), 'd MMM yyyy', { locale: id }) : '—'}
            </p>
          </div>
        </div>
      </motion.div>

      {/* Storage Stats */}
      {storageStats && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="card p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-display font-semibold text-slate-900">{t('profile.storageUsage')}</h3>
            <button
              onClick={handleCleanup}
              disabled={cleaningUp}
              className="btn-secondary text-sm flex items-center gap-2"
            >
              {cleaningUp ? (
                <>
                  <span className="w-3 h-3 border-2 border-slate-400/30 border-t-slate-400 rounded-full animate-spin" />
                  {t('profile.cleaning')}
                </>
              ) : (
                <>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
                  </svg>
                  {t('profile.cleanup')}
                </>
              )}
            </button>
          </div>
          
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div className="bg-slate-50 rounded-xl p-4 text-center">
              <p className="text-2xl font-bold text-violet-400">{storageStats.total_size_mb}</p>
              <p className="text-xs text-slate-500 mt-1">{t('profile.mbTotal')}</p>
            </div>
            <div className="bg-slate-50 rounded-xl p-4 text-center">
              <p className="text-2xl font-bold text-teal-400">{storageStats.video_count}</p>
              <p className="text-xs text-slate-500 mt-1">{t('profile.video')}</p>
            </div>
            <div className="bg-slate-50 rounded-xl p-4 text-center">
              <p className="text-2xl font-bold text-amber-400">{storageStats.document_count}</p>
              <p className="text-xs text-slate-500 mt-1">{t('profile.document')}</p>
            </div>
          </div>
          
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-500">{t('profile.video')}</span>
              <span className="text-slate-900 font-mono">{storageStats.video_size_mb} MB</span>
            </div>
            <div className="h-2 bg-slate-50 rounded-full overflow-hidden">
              <div 
                className="h-full bg-violet-500 rounded-full transition-all duration-500"
                style={{ width: `${(storageStats.video_size_mb / storageStats.total_size_mb) * 100}%` }}
              />
            </div>
            
            <div className="flex items-center justify-between text-sm pt-2">
              <span className="text-slate-500">{t('profile.document')}</span>
              <span className="text-slate-900 font-mono">{storageStats.document_size_mb} MB</span>
            </div>
            <div className="h-2 bg-slate-50 rounded-full overflow-hidden">
              <div 
                className="h-full bg-amber-500 rounded-full transition-all duration-500"
                style={{ width: `${(storageStats.document_size_mb / storageStats.total_size_mb) * 100}%` }}
              />
            </div>
          </div>
          
          <p className="text-xs text-slate-600 mt-4">
            💡 {t('profile.cleanupHint')}
          </p>
        </motion.div>
      )}

      {/* Edit Form */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="card p-6"
      >
        <h3 className="font-display font-semibold text-slate-900 mb-4">{t('profile.editProfile')}</h3>
        
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="text-sm text-slate-500 block mb-1.5">{t('profile.username')}</label>
            <input
              {...register('username', { required: t('profile.usernameRequired') })}
              className="input-field"
              placeholder="Username"
            />
            {errors.username && <p className="text-red-400 text-xs mt-1">{errors.username.message}</p>}
          </div>

          <div>
            <label className="text-sm text-slate-500 block mb-1.5">{t('profile.email')}</label>
            <input
              {...register('email', { 
                required: t('profile.emailRequired'),
                pattern: { value: /^\S+@\S+$/i, message: t('profile.emailInvalid') }
              })}
              type="email"
              className="input-field"
              placeholder="email@example.com"
            />
            {errors.email && <p className="text-red-400 text-xs mt-1">{errors.email.message}</p>}
          </div>

          <div className="pt-4 border-t border-slate-200">
            <h4 className="text-sm font-semibold text-slate-900 mb-3">{t('profile.changePassword')}</h4>
            
            <div className="space-y-4">
              <div>
                <label className="text-sm text-slate-500 block mb-1.5">{t('profile.currentPassword')}</label>
                <input
                  {...register('current_password', {
                    validate: value => !newPassword || value || t('profile.currentPasswordRequired')
                  })}
                  type="password"
                  className="input-field"
                  placeholder={t('profile.currentPassword')}
                />
                {errors.current_password && <p className="text-red-400 text-xs mt-1">{errors.current_password.message}</p>}
              </div>

              <div>
                <label className="text-sm text-slate-500 block mb-1.5">{t('profile.newPassword')}</label>
                <input
                  {...register('new_password', {
                    minLength: { value: 6, message: t('profile.passwordMinLength') }
                  })}
                  type="password"
                  className="input-field"
                  placeholder={t('profile.newPassword')}
                />
                {errors.new_password && <p className="text-red-400 text-xs mt-1">{errors.new_password.message}</p>}
              </div>

              <div>
                <label className="text-sm text-slate-500 block mb-1.5">{t('profile.confirmPassword')}</label>
                <input
                  {...register('confirm_password', {
                    validate: value => !newPassword || value === newPassword || t('profile.passwordMismatch')
                  })}
                  type="password"
                  className="input-field"
                  placeholder={t('profile.confirmPassword')}
                />
                {errors.confirm_password && <p className="text-red-400 text-xs mt-1">{errors.confirm_password.message}</p>}
              </div>
            </div>
          </div>

          <motion.button
            type="submit"
            disabled={updating}
            whileTap={{ scale: 0.97 }}
            className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-60"
          >
            {updating ? (
              <>
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                {t('profile.saving')}
              </>
            ) : (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z"/>
                  <polyline points="17 21 17 13 7 13 7 21"/>
                  <polyline points="7 3 7 8 15 8"/>
                </svg>
                {t('profile.saveChanges')}
              </>
            )}
          </motion.button>
        </form>
      </motion.div>
    </div>
  )
}

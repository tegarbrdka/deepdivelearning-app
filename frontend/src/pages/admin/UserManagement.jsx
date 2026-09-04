import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'
import { format } from 'date-fns'
import { id } from 'date-fns/locale'
import api from '../../services/api'
import { useLang } from '../../contexts/LanguageContext'

export default function UserManagement() {
  const { t } = useLang()
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [showAdd, setShowAdd] = useState(false)
  const { register, handleSubmit, reset } = useForm()

  const fetchUsers = () => {
    setLoading(true)
    api.get('/admin/users').then(r => setUsers(r.data)).finally(() => setLoading(false))
  }
  useEffect(() => { fetchUsers() }, [])

  const onAddUser = async (data) => {
    try {
      await api.post('/admin/users', data)
      toast.success(t('userManagement.addSuccess'))
      reset(); setShowAdd(false); fetchUsers()
    } catch (err) {
      toast.error(err.response?.data?.detail || t('userManagement.addError'))
    }
  }

  const handleDelete = async (uid, username) => {
    toast((t_toast) => (
      <div className="flex items-center gap-3">
        <div>
          <p className="font-semibold text-slate-900">{t('userManagement.deleteConfirm').replace('{username}', username)}</p>
          <p className="text-xs text-slate-500 mt-1">{t('userManagement.deleteWarning')}</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => {
              toast.dismiss(t_toast.id)
              toast.promise(
                api.delete(`/admin/users/${uid}`),
                {
                  loading: '...',
                  success: () => { fetchUsers(); return t('userManagement.deleteSuccess') },
                  error: t('userManagement.deleteError'),
                }
              )
            }}
            className="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white text-sm rounded-lg transition-colors"
          >
            {t('userManagement.deleteBtn')}
          </button>
          <button onClick={() => toast.dismiss(t_toast.id)} className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-900 text-sm rounded-lg transition-colors">
            {t('userManagement.cancelBtn')}
          </button>
        </div>
      </div>
    ), { duration: Infinity, style: { maxWidth: '500px' } })
  }

  const handleRoleChange = async (uid, newRole) => {
    try {
      await api.patch(`/admin/users/${uid}`, { role: newRole })
      toast.success(t('userManagement.roleUpdated')); fetchUsers()
    } catch { toast.error(t('userManagement.roleUpdateError')) }
  }

  return (
    <div className="max-w-5xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold text-slate-900">{t('userManagement.title')}</h1>
          <p className="text-slate-500 mt-1">{t('userManagement.subtitle')}</p>
        </div>
        <motion.button whileTap={{ scale: 0.97 }} onClick={() => setShowAdd(!showAdd)} className="btn-primary flex items-center gap-2">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          {t('userManagement.addUser')}
        </motion.button>
      </div>

      <AnimatePresence>
        {showAdd && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="card p-6 overflow-hidden">
            <h3 className="font-display font-semibold text-slate-900 mb-4">{t('userManagement.addUserTitle')}</h3>
            <form onSubmit={handleSubmit(onAddUser)} className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-slate-500 block mb-1.5">{t('userManagement.username')}</label>
                <input {...register('username', { required: true })} className="input-field" placeholder="Username" />
              </div>
              <div>
                <label className="text-sm text-slate-500 block mb-1.5">{t('userManagement.email')}</label>
                <input {...register('email', { required: true })} type="email" className="input-field" placeholder="email@domain.com" />
              </div>
              <div>
                <label className="text-sm text-slate-500 block mb-1.5">{t('userManagement.password')}</label>
                <input {...register('password', { required: true, minLength: 6 })} type="password" className="input-field" placeholder={t('userManagement.passwordPlaceholder')} />
              </div>
              <div>
                <label className="text-sm text-slate-500 block mb-1.5">{t('userManagement.role')}</label>
                <select {...register('role')} className="input-field">
                  <option value="user">User</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <div className="col-span-2 flex gap-3 justify-end pt-2">
                <button type="button" onClick={() => { setShowAdd(false); reset() }} className="btn-secondary">{t('userManagement.cancel')}</button>
                <button type="submit" className="btn-primary">{t('userManagement.saveUser')}</button>
              </div>
            </form>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="card overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200">
          <h3 className="font-display font-semibold text-slate-900">{t('userManagement.userList')} ({users.length})</h3>
        </div>
        {loading ? (
          <div className="p-6 space-y-2">{[...Array(5)].map((_, i) => <div key={i} className="h-12 bg-slate-50 rounded-lg animate-pulse" />)}</div>
        ) : (
          <table className="w-full">
            <thead><tr className="border-b border-slate-200">
              <th className="text-left px-6 py-3 text-xs text-slate-500 uppercase">#</th>
              <th className="text-left px-6 py-3 text-xs text-slate-500 uppercase">{t('userManagement.username')}</th>
              <th className="text-left px-4 py-3 text-xs text-slate-500 uppercase">{t('userManagement.email')}</th>
              <th className="text-left px-4 py-3 text-xs text-slate-500 uppercase">{t('userManagement.role')}</th>
              <th className="text-left px-4 py-3 text-xs text-slate-500 uppercase">{t('userManagement.joinedDate')}</th>
              <th className="text-right px-4 py-3 text-xs text-slate-500 uppercase">{t('userManagement.action')}</th>
            </tr></thead>
            <tbody className="divide-y divide-navy-800">
              {users.map((u, i) => (
                <tr key={u.id} className="hover:bg-slate-50/30 transition-colors">
                  <td className="px-6 py-3 text-slate-600 text-sm">{i + 1}</td>
                  <td className="px-6 py-3">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-600 to-teal-500 flex items-center justify-center text-slate-900 text-xs font-bold">
                        {u.username[0].toUpperCase()}
                      </div>
                      <span className="text-slate-900 font-medium text-sm">{u.username}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-slate-500 text-sm">{u.email}</td>
                  <td className="px-4 py-3">
                    <select
                      value={u.role}
                      onChange={e => handleRoleChange(u.id, e.target.value)}
                      className={`text-xs font-semibold px-2 py-1 rounded-full border bg-transparent cursor-pointer outline-none
                        ${u.role === 'admin' ? 'text-violet-600 border-violet-500/30 bg-violet-500/10' : 'text-teal-600 border-teal-400/30 bg-teal-400/10'}`}
                    >
                      <option value="user">User</option>
                      <option value="admin">Admin</option>
                    </select>
                  </td>
                  <td className="px-4 py-3 text-slate-500 text-xs">{u.created_at ? format(new Date(u.created_at), 'd MMM yyyy', { locale: id }) : '—'}</td>
                  <td className="px-4 py-3 text-right">
                    <button onClick={() => handleDelete(u.id, u.username)} className="p-1.5 text-slate-600 hover:text-red-600 hover:bg-red-400/10 rounded-lg transition-all">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M9 6V4h6v2"/></svg>
                    </button>
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

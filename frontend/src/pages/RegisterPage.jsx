import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import api from '../services/api'
import useAuthStore from '../stores/authStore'

export default function RegisterPage() {
  const [loading, setLoading] = useState(false)
  const { register, handleSubmit, watch, formState: { errors } } = useForm()
  const { login } = useAuthStore()
  const navigate = useNavigate()

  const onSubmit = async (data) => {
    setLoading(true)
    try {
      const res = await api.post('/auth/register', {
        username: data.username,
        email: data.email,
        password: data.password,
      })
      login(res.data.access_token, { username: res.data.username, role: res.data.role })
      toast.success('Akun berhasil dibuat!')
      navigate('/dashboard')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Registrasi gagal')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center relative overflow-hidden">
      <div className="absolute inset-0 bg-grid-pattern opacity-30" />
      <div className="absolute top-[-20%] right-[-10%] w-[600px] h-[600px] rounded-full bg-teal-400/8 blur-[120px]" />
      <div className="absolute bottom-[-20%] left-[-10%] w-[500px] h-[500px] rounded-full bg-violet-600/10 blur-[100px]" />

      <div className="relative z-10 w-full max-w-md px-6">
        <motion.div
          initial={{ opacity: 0, y: -30 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-violet-600 to-teal-500 mb-4 shadow-lg shadow-violet-500/30">
            <svg width="28" height="28" viewBox="0 0 32 32" fill="none">
              <path d="M8 8h16v4H8zM8 14h10v4H8zM8 20h12v4H8z" fill="white" opacity="0.9"/>
            </svg>
          </div>
          <h1 className="font-display text-3xl font-bold text-slate-900">DeepDiveLearning</h1>
          <p className="text-slate-500 text-sm mt-1">Buat akun baru</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="card p-8"
        >
          <h2 className="font-display text-xl font-semibold text-slate-900 mb-6">Daftar Akun</h2>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="text-sm text-slate-500 mb-1.5 block">Username</label>
              <input
                {...register('username', { required: 'Username wajib', minLength: { value: 3, message: 'Min 3 karakter' } })}
                className="input-field"
                placeholder="Masukkan username"
              />
              {errors.username && <p className="text-red-400 text-xs mt-1">{errors.username.message}</p>}
            </div>

            <div>
              <label className="text-sm text-slate-500 mb-1.5 block">Email</label>
              <input
                {...register('email', { required: 'Email wajib', pattern: { value: /^\S+@\S+\.\S+$/, message: 'Format email tidak valid' } })}
                type="email"
                className="input-field"
                placeholder="email@example.com"
              />
              {errors.email && <p className="text-red-400 text-xs mt-1">{errors.email.message}</p>}
            </div>

            <div>
              <label className="text-sm text-slate-500 mb-1.5 block">Password</label>
              <input
                {...register('password', { required: 'Password wajib', minLength: { value: 6, message: 'Min 6 karakter' } })}
                type="password"
                className="input-field"
                placeholder="Min 6 karakter"
              />
              {errors.password && <p className="text-red-400 text-xs mt-1">{errors.password.message}</p>}
            </div>

            <div>
              <label className="text-sm text-slate-500 mb-1.5 block">Konfirmasi Password</label>
              <input
                {...register('confirm', {
                  required: 'Konfirmasi password wajib',
                  validate: v => v === watch('password') || 'Password tidak cocok'
                })}
                type="password"
                className="input-field"
                placeholder="Ulangi password"
              />
              {errors.confirm && <p className="text-red-400 text-xs mt-1">{errors.confirm.message}</p>}
            </div>

            <motion.button
              type="submit"
              disabled={loading}
              whileTap={{ scale: 0.97 }}
              className="btn-primary w-full mt-2 flex items-center justify-center gap-2 disabled:opacity-60"
            >
              {loading ? (
                <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Memproses...</>
              ) : 'Daftar Sekarang'}
            </motion.button>
          </form>

          <p className="text-slate-500 text-sm text-center mt-6">
            Sudah punya akun?{' '}
            <Link to="/login" className="text-violet-400 hover:text-violet-800 dark:text-violet-300 font-medium">Masuk di sini</Link>
          </p>
        </motion.div>
      </div>
    </div>
  )
}

import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import api from '../services/api'
import useAuthStore from '../stores/authStore'

export default function LoginPage() {
  const [loading, setLoading] = useState(false)
  const { register, handleSubmit, formState: { errors } } = useForm()
  const { login } = useAuthStore()
  const navigate = useNavigate()

  const onSubmit = async (data) => {
    setLoading(true)
    try {
      const res = await api.post('/auth/login', data)
      const { access_token, username, role } = res.data
      login(access_token, { username, role })
      // ensure token is persisted before navigating
      await new Promise(r => setTimeout(r, 50))
      toast.success(`Selamat datang, ${username}!`)
      navigate(role === 'admin' ? '/admin/dashboard' : '/dashboard')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Login gagal')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center relative overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-0 bg-grid-pattern opacity-30" />
      <div className="absolute top-[-20%] left-[-10%] w-[600px] h-[600px] rounded-full bg-violet-600/10 blur-[120px]" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[500px] h-[500px] rounded-full bg-teal-400/8 blur-[100px]" />

      <div className="relative z-10 w-full max-w-md px-6">
        {/* Logo */}
        <motion.div
          initial={{ opacity: 0, y: -30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-10"
        >
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-600 to-teal-500 mb-4 shadow-lg shadow-violet-500/30">
            <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
              <path d="M8 8h16v4H8zM8 14h10v4H8zM8 20h12v4H8z" fill="white" opacity="0.9"/>
              <circle cx="24" cy="22" r="6" fill="white" opacity="0.15"/>
              <path d="M22 22l2 2 4-4" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <h1 className="font-display text-3xl font-bold text-slate-900">DeepDiveLearning</h1>
          <p className="text-slate-500 text-sm mt-1">Sistem Klasifikasi Pembelajaran Berbasis AI</p>
        </motion.div>

        {/* Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.15 }}
          className="card p-8"
        >
          <h2 className="font-display text-xl font-semibold text-slate-900 mb-6">Masuk ke Akun</h2>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="text-sm text-slate-500 mb-1.5 block">Username</label>
              <input
                {...register('username', { required: 'Username wajib diisi' })}
                className="input-field"
                placeholder="Masukkan username"
              />
              {errors.username && <p className="text-red-400 text-xs mt-1">{errors.username.message}</p>}
            </div>

            <div>
              <label className="text-sm text-slate-500 mb-1.5 block">Password</label>
              <input
                {...register('password', { required: 'Password wajib diisi' })}
                type="password"
                className="input-field"
                placeholder="Masukkan password"
              />
              {errors.password && <p className="text-red-400 text-xs mt-1">{errors.password.message}</p>}
            </div>

            <motion.button
              type="submit"
              disabled={loading}
              whileTap={{ scale: 0.97 }}
              className="btn-primary w-full mt-2 flex items-center justify-center gap-2 disabled:opacity-60"
            >
              {loading ? (
                <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Memproses...</>
              ) : 'Masuk'}
            </motion.button>
          </form>

          <p className="text-slate-500 text-sm text-center mt-6">
            Belum punya akun?{' '}
            <Link to="/register" className="text-violet-400 hover:text-violet-800 dark:text-violet-300 font-medium">Daftar sekarang</Link>
          </p>
          
          <div className="mt-4 pt-4 border-t border-slate-200">
            <Link
              to="/guest"
              className="block w-full py-2.5 text-center text-sm text-teal-400 hover:text-teal-800 dark:text-teal-300 font-medium transition-colors"
            >
              🎯 Coba Mode Guest (Tanpa Daftar)
            </Link>
          </div>
        </motion.div>

      </div>
    </div>
  )
}

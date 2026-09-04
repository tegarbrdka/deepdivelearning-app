import { useState } from 'react'
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import useAuthStore from '../../stores/authStore'
import toast from 'react-hot-toast'
import { useTheme } from '../../contexts/ThemeContext'
import { useLang } from '../../contexts/LanguageContext'

export default function AppLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const { logout, user } = useAuthStore()
  const { lang, toggleLang, t } = useLang()
  const navigate = useNavigate()
  const location = useLocation()
  const isAdmin = user?.role === 'admin'

  const userNav = [
    { path: '/dashboard', label: t('nav.dashboard'), icon: HomeIcon },
    { path: '/predict', label: t('nav.uploadPredict'), icon: UploadIcon },
    { path: '/dli-analysis', label: t('nav.dliAnalysis'), icon: DLIIcon },
    { path: '/history', label: t('nav.history'), icon: HistoryIcon },
    { label: t('video3m.navUpload'), divider: true },
    { path: '/video-analysis-3m', label: t('video3m.navUpload'), icon: VideoIcon },
    { path: '/video-analysis-3m/history', label: t('video3m.navHistory'), icon: HistoryIcon },
    { label: t('nav.account'), divider: true },
    { path: '/profile', label: t('nav.profile'), icon: SettingsIcon },
  ]

  const adminNav = [
    { path: '/admin/dashboard', label: t('nav.dashboard'), icon: HomeIcon },

    { label: 'DLI', divider: true },
    { path: '/admin/dli/dashboard', label: t('nav.dliDashboard'), icon: DLIIcon },
    { path: '/admin/dli/bulk', label: t('nav.dliBulk'), icon: UploadIcon },
    { path: '/admin/dli/analytics', label: t('nav.dliAnalytics'), icon: ChartIcon },
    { path: '/admin/dli/history', label: t('nav.dliHistory'), icon: HistoryIcon },
    { path: '/admin/dli/anomaly', label: t('nav.dliAnomaly'), icon: ChartIcon },
    { path: '/admin/dli/keywords', label: t('nav.dliKeywords'), icon: KeyIcon },
    { label: t('video3m.navUpload'), divider: true },
    { path: '/admin/video-analysis-3m', label: t('video3m.navAdminDashboard'), icon: ChartIcon },
    { path: '/admin/video-analysis-3m/evaluation', label: t('video3m.navEvaluation'), icon: DocIcon },
    { path: '/video-analysis-3m', label: t('video3m.navUpload'), icon: VideoIcon },
    { path: '/video-analysis-3m/history', label: t('video3m.navHistory'), icon: HistoryIcon },
    { label: t('nav.system'), divider: true },
    { path: '/admin/users', label: t('nav.userManagement'), icon: UsersIcon },
    { path: '/admin/logs', label: t('nav.activityLogs'), icon: LogIcon },
    { path: '/admin/config', label: t('nav.systemConfig'), icon: SettingsIcon },
  ]

  const navItems = isAdmin ? adminNav : userNav

  const handleLogout = () => {
    logout()
    toast.success(t('nav.logoutSuccess'))
    navigate('/login')
  }

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden">
      {/* Sidebar */}
      <motion.aside
        animate={{ width: collapsed ? 72 : 256 }}
        transition={{ duration: 0.25, ease: 'easeInOut' }}
        className="flex-shrink-0 bg-white border-r border-slate-200 flex flex-col overflow-hidden"
      >
        {/* Logo */}
        <div className="h-16 flex items-center px-4 border-b border-slate-200 gap-3">
          <div className="w-9 h-9 flex-shrink-0 rounded-xl bg-gradient-to-br from-violet-600 to-teal-500 flex items-center justify-center shadow-lg shadow-violet-500/20">
            <svg width="18" height="18" viewBox="0 0 32 32" fill="none">
              <path d="M8 8h16v4H8zM8 14h10v4H8zM8 20h12v4H8z" fill="white"/>
            </svg>
          </div>
          <AnimatePresence>
            {!collapsed && (
              <motion.span
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                className="font-display font-bold text-slate-900 text-lg whitespace-nowrap"
              >
                DeepDiveLearning
              </motion.span>
            )}
          </AnimatePresence>
        </div>

        {/* Role badge */}
        <AnimatePresence>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="mx-3 mt-3 px-3 py-2 rounded-xl bg-slate-50 border border-slate-200"
            >
              <p className="text-xs text-slate-500">Login sebagai</p>
              <p className="text-sm font-semibold text-slate-900 truncate">{user?.username}</p>
              <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${isAdmin ? 'bg-violet-100 text-violet-700 border border-violet-200' : 'bg-teal-100 text-teal-700 border border-teal-200'}`}>
                {isAdmin ? 'Administrator' : 'User'}
              </span>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-0.5">
          {navItems.map((item, i) => {
            if (item.divider) {
              return !collapsed ? (
                <motion.p key={i} initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-xs font-semibold text-slate-600 uppercase tracking-wider px-3 pt-4 pb-1">
                  {item.label}
                </motion.p>
              ) : <div key={i} className="my-2 border-t border-slate-200" />
            }
            const Icon = item.icon
            const active = location.pathname === item.path
            return (
              <NavLink key={item.path} to={item.path}>
                <motion.div
                  whileHover={{ x: collapsed ? 0 : 3 }}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all cursor-pointer ${
                    active
                      ? 'bg-violet-100 text-violet-700 border border-violet-200 shadow-sm'
                      : 'text-slate-500 hover:text-slate-900 hover:bg-slate-50'
                  }`}
                >
                  <Icon size={18} className="flex-shrink-0" />
                  <AnimatePresence>
                    {!collapsed && (
                      <motion.span
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="text-sm font-medium whitespace-nowrap"
                      >
                        {item.label}
                      </motion.span>
                    )}
                  </AnimatePresence>
                </motion.div>
              </NavLink>
            )
          })}
        </nav>

        {/* Bottom */}
        <div className="p-2 border-t border-slate-200 space-y-1">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-red-600 hover:bg-red-50 hover:text-red-700 transition-all"
          >
            <LogoutIcon size={18} className="flex-shrink-0" />
            {!collapsed && <span className="text-sm font-medium">{t('nav.logout')}</span>}
          </button>
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="w-full flex items-center justify-center py-2 text-slate-500 hover:text-slate-600 transition-all"
          >
            <ChevronIcon size={16} className={`transition-transform duration-300 ${collapsed ? 'rotate-180' : ''}`} />
          </button>
        </div>
      </motion.aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto bg-slate-50">
        {/* Top bar */}
        <div className="sticky top-0 z-10 h-16 bg-slate-50/80 backdrop-blur border-b border-slate-200 flex items-center px-6 gap-4">
          <div className="flex-1">
            <h2 className="font-display text-slate-900 font-semibold text-lg capitalize">
              {location.pathname.split('/').pop().replace('-', ' ') || 'Dashboard'}
            </h2>
          </div>
          <div className="flex items-center gap-3">
            {/* Language toggle */}
            <button
              onClick={toggleLang}
              className="w-9 h-9 rounded-lg bg-slate-50 hover:bg-slate-200 border border-slate-200 flex items-center justify-center transition-all text-xs font-bold text-slate-600 shadow-sm"
              title={lang === 'id' ? 'Switch to English' : 'Ganti ke Indonesia'}
            >
              {lang === 'id' ? 'EN' : 'ID'}
            </button>
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-600 to-teal-500 flex items-center justify-center text-slate-900 text-sm font-bold">
              {user?.username?.[0]?.toUpperCase()}
            </div>
          </div>
        </div>

        {/* Page content */}
        <motion.div
          key={location.pathname}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25 }}
          className="p-6"
        >
          <Outlet />
        </motion.div>
      </main>
    </div>
  )
}

// Icon components (inline SVG)
function HomeIcon({ size = 20, className = '' }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}><path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>
}
function UploadIcon({ size = 20, className = '' }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}><path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>
}
function HistoryIcon({ size = 20, className = '' }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
}
function VideoIcon({ size = 20, className = '' }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/></svg>
}
function DocIcon({ size = 20, className = '' }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
}
function CpuIcon({ size = 20, className = '' }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/></svg>
}
function BrainIcon({ size = 20, className = '' }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}><path d="M9.5 2A2.5 2.5 0 0112 4.5v15a2.5 2.5 0 01-4.96-.46 2.5 2.5 0 01-1.07-4.8 3 3 0 01-.34-5.58 2.5 2.5 0 013.87-3.16zm5 0a2.5 2.5 0 00-2.5 2.5v15a2.5 2.5 0 004.96-.46 2.5 2.5 0 001.07-4.8 3 3 0 00.34-5.58A2.5 2.5 0 0014.5 2z"/></svg>
}
function ChartIcon({ size = 20, className = '' }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
}
function UsersIcon({ size = 20, className = '' }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>
}
function LogIcon({ size = 20, className = '' }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><line x1="8" y1="12" x2="16" y2="12"/><line x1="8" y1="16" x2="12" y2="16"/><polyline points="14 2 14 8 20 8"/></svg>
}
function SettingsIcon({ size = 20, className = '' }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/></svg>
}
function LogoutIcon({ size = 20, className = '' }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
}
function ChevronIcon({ size = 16, className = '' }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}><polyline points="15 18 9 12 15 6"/></svg>
}

function DLIIcon({ size = 20, className = '' }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}><path d="M2 20h20M6 20V10l6-6 6 6v10"/><path d="M10 20v-5h4v5"/></svg>
}

function KeyIcon({ size = 20, className = '' }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}><circle cx="7.5" cy="15.5" r="5.5"/><path d="M21 2l-9.6 9.6"/><path d="M15.5 7.5l3 3L22 7l-3-3"/></svg>
}

import { useEffect, useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import useAuthStore from '../stores/authStore'

const shortcuts = [
  { key: 'Ctrl+K', action: 'Search / Command Palette', path: null },
  { key: 'Ctrl+H', action: 'Go to History', path: '/history' },
  { key: 'Ctrl+U', action: 'Go to Upload', path: '/predict' },
  { key: 'Ctrl+D', action: 'Go to Dashboard', path: '/dashboard' },
  { key: '?', action: 'Show Shortcuts Help', path: null },
  { key: 'Esc', action: 'Close Modal/Dialog', path: null },
]

const adminShortcuts = [
  { key: 'Ctrl+Shift+V', action: 'Video Dataset', path: '/admin/dataset/video' },
  { key: 'Ctrl+Shift+D', action: 'Document Dataset', path: '/admin/dataset/document' },
  { key: 'Ctrl+Shift+U', action: 'User Management', path: '/admin/users' },
]

export default function KeyboardShortcuts() {
  const [showHelp, setShowHelp] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const { user } = useAuthStore()
  const isAdmin = user?.role === 'admin'

  useEffect(() => {
    const handleKeyDown = (e) => {
      // Show help modal
      if (e.key === '?' && !e.ctrlKey && !e.metaKey) {
        e.preventDefault()
        setShowHelp(true)
        return
      }

      // Close modal with Escape
      if (e.key === 'Escape') {
        setShowHelp(false)
        return
      }

      // Ctrl/Cmd shortcuts
      if (e.ctrlKey || e.metaKey) {
        // Prevent default for our shortcuts
        const key = e.key.toLowerCase()

        if (key === 'k') {
          e.preventDefault()
          // Could implement command palette here
          setShowHelp(true)
        } else if (key === 'h') {
          e.preventDefault()
          navigate('/history')
        } else if (key === 'u' && !e.shiftKey) {
          e.preventDefault()
          navigate('/predict')
        } else if (key === 'd' && !e.shiftKey) {
          e.preventDefault()
          navigate(isAdmin ? '/admin/dashboard' : '/dashboard')
        }

        // Admin shortcuts
        if (isAdmin && e.shiftKey) {
          if (key === 'v') {
            e.preventDefault()
            navigate('/admin/dataset/video')
          } else if (key === 'd') {
            e.preventDefault()
            navigate('/admin/dataset/document')
          } else if (key === 'u') {
            e.preventDefault()
            navigate('/admin/users')
          }
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [navigate, isAdmin, location.pathname])

  return (
    <AnimatePresence>
      {showHelp && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={() => setShowHelp(false)}
        >
          <motion.div
            initial={{ scale: 0.95, y: 20 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.95, y: 20 }}
            onClick={e => e.stopPropagation()}
            className="card p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto"
          >
            <div className="flex items-start justify-between mb-6">
              <div>
                <h3 className="font-display text-xl font-bold text-slate-900">Keyboard Shortcuts</h3>
                <p className="text-slate-500 text-sm mt-1">Navigasi cepat dengan keyboard</p>
              </div>
              <button
                onClick={() => setShowHelp(false)}
                className="p-2 hover:bg-slate-50 rounded-lg transition-colors"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>

            <div className="space-y-6">
              {/* General shortcuts */}
              <div>
                <h4 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-3">General</h4>
                <div className="space-y-2">
                  {shortcuts.map((s, i) => (
                    <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-slate-50 hover:bg-navy-700 transition-colors">
                      <span className="text-slate-600 text-sm">{s.action}</span>
                      <kbd className="px-2 py-1 text-xs font-mono bg-white border border-slate-200 rounded text-violet-800 dark:text-violet-300">
                        {s.key}
                      </kbd>
                    </div>
                  ))}
                </div>
              </div>

              {/* Admin shortcuts */}
              {isAdmin && (
                <div>
                  <h4 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-3">Admin Only</h4>
                  <div className="space-y-2">
                    {adminShortcuts.map((s, i) => (
                      <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-slate-50 hover:bg-navy-700 transition-colors">
                        <span className="text-slate-600 text-sm">{s.action}</span>
                        <kbd className="px-2 py-1 text-xs font-mono bg-white border border-slate-200 rounded text-teal-800 dark:text-teal-300">
                          {s.key}
                        </kbd>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="mt-6 pt-4 border-t border-slate-200">
              <p className="text-xs text-slate-500 text-center">
                Press <kbd className="px-1.5 py-0.5 bg-slate-50 border border-slate-200 rounded text-violet-800 dark:text-violet-300">?</kbd> anytime to show this help
              </p>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

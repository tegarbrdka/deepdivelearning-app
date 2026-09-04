import { createContext, useContext, useState, useCallback } from 'react'
import id from '../i18n/id'
import en from '../i18n/en'

const translations = { id, en }

const LanguageContext = createContext(null)

export function LanguageProvider({ children }) {
  const [lang, setLang] = useState(() => localStorage.getItem('lang') || 'id')

  const toggleLang = useCallback(() => {
    setLang(prev => {
      const next = prev === 'id' ? 'en' : 'id'
      localStorage.setItem('lang', next)
      return next
    })
  }, [])

  const t = useCallback((key) => {
    const keys = key.split('.')
    let val = translations[lang]
    for (const k of keys) {
      val = val?.[k]
      if (val === undefined) return key
    }
    return val
  }, [lang])

  return (
    <LanguageContext.Provider value={{ lang, toggleLang, t }}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLang() {
  const ctx = useContext(LanguageContext)
  if (!ctx) throw new Error('useLang must be used within LanguageProvider')
  return ctx
}

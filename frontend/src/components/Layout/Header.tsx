/**
 * App header with branding, theme toggle, and status indicator.
 */

import { Sun, Moon, Activity, Github } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAppStore } from '@/store'
import { useState, useEffect } from 'react'
import { checkHealth } from '@/lib/api'

function ThemeToggle() {
  const { isDark, toggleDark } = useAppStore()
  return (
    <button
      id="theme-toggle"
      onClick={toggleDark}
      className={cn(
        'w-9 h-9 rounded-xl flex items-center justify-center transition-all duration-300',
        'hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500 dark:text-slate-400',
        'hover:text-slate-700 dark:hover:text-slate-200',
      )}
      title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
    </button>
  )
}

function ApiStatus() {
  const [status, setStatus] = useState<'checking' | 'ok' | 'error'>('checking')

  useEffect(() => {
    const check = async () => {
      try {
        await checkHealth()
        setStatus('ok')
      } catch {
        setStatus('error')
      }
    }
    check()
    const interval = setInterval(check, 30_000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="flex items-center gap-1.5">
      <div
        className={cn(
          'w-2 h-2 rounded-full',
          status === 'ok' && 'bg-emerald-400',
          status === 'error' && 'bg-red-400',
          status === 'checking' && 'bg-amber-400 animate-pulse',
        )}
      />
      <span className="text-xs text-slate-500 dark:text-slate-400 hidden sm:block">
        {status === 'ok' ? 'API Connected' : status === 'error' ? 'API Offline' : 'Connecting…'}
      </span>
    </div>
  )
}

export function Header() {
  return (
    <header className="h-14 flex items-center justify-between px-6 border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-gray-950/80 backdrop-blur-md sticky top-0 z-50">
      {/* Logo */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-xl gradient-brand flex items-center justify-center shadow-md shadow-brand-500/20">
          <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4 text-white">
            <path d="M4 4h8l4 4v10H4V4z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/>
            <path d="M12 4v4h4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M6 11h8M6 14h5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
        </div>
        <div>
          <h1 className="text-base font-bold text-slate-900 dark:text-white leading-none">
            DocuMind
          </h1>
          <p className="text-[10px] text-slate-400 leading-none mt-0.5">
            AI Document Chat
          </p>
        </div>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-3">
        <ApiStatus />
        <div className="w-px h-5 bg-slate-200 dark:bg-slate-700" />
        <ThemeToggle />
      </div>
    </header>
  )
}

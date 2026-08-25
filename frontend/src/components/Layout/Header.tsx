import { useState, useEffect } from 'react'
import { Sun, Moon, Database, FileText, Sparkles } from 'lucide-react'
import { useAppStore } from '@/store'
import { checkHealth } from '@/lib/api'

interface HeaderProps {
  onOpenSpecs: () => void
  onOpenDrawer: () => void
  onOpenGlobalChat: () => void
  isGlobalChatActive: boolean
}

export function Header({
  onOpenSpecs,
  onOpenDrawer,
  onOpenGlobalChat,
  isGlobalChatActive,
}: HeaderProps) {
  const { themeMode, setThemeMode, documents, selectedDocument, selectDocument } = useAppStore()
  const [apiOk, setApiOk] = useState<boolean | null>(null)

  useEffect(() => {
    const check = async () => {
      try {
        await checkHealth()
        setApiOk(true)
      } catch {
        setApiOk(false)
      }
    }
    check()
    const interval = setInterval(check, 30_000)
    return () => clearInterval(interval)
  }, [])

  const toggleTheme = () => {
    setThemeMode(themeMode === 'seamless' ? 'obsidian' : 'seamless')
  }

  return (
    <header className="h-16 flex items-center justify-between px-6 sm:px-10 md:px-14 border-b border-white/10 select-none bg-[#111116]/80 backdrop-blur-xl text-white z-30">
      {/* Brand logo */}
      <div className="flex items-center gap-6">
        <button
          onClick={() => selectDocument(null)}
          className="flex items-center gap-2.5 group text-left"
        >
          {/* Geometric asterisk icon */}
          <span className="font-mono text-xl font-black group-hover:rotate-45 transition-transform duration-300 text-white">
            ✻
          </span>
          <div className="flex items-baseline gap-2">
            <span className="font-display font-black tracking-widest text-base sm:text-lg uppercase text-white">
              LIMITLESS
            </span>
            <span className="text-[10px] font-mono tracking-widest hidden sm:inline uppercase text-white/50">
              // RAG 2.0
            </span>
          </div>
        </button>

        {/* Live system state dot */}
        <div className="hidden lg:flex items-center gap-2 px-2.5 py-1 rounded-full border border-white/10 text-[11px] font-mono bg-white/[0.06] text-white/70">
          <div
            className={`w-1.5 h-1.5 rounded-full ${
              apiOk === true
                ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.9)]'
                : apiOk === false
                ? 'bg-red-400'
                : 'bg-amber-400 animate-pulse'
            }`}
          />
          <span>{apiOk ? 'SYSTEM OPTIMAL' : 'CONNECTING API'}</span>
        </div>
      </div>

      {/* Navigation Links */}
      <div className="hidden md:flex items-center gap-8 text-xs font-sans font-medium text-white/70">
        <button
          onClick={() => selectDocument(null)}
          className={`transition-colors underline-offset-4 ${
            !selectedDocument && !isGlobalChatActive
              ? 'underline font-bold text-white'
              : 'hover:text-white'
          }`}
        >
          Overview
        </button>

        <button
          onClick={onOpenSpecs}
          className="transition-colors underline-offset-4 hover:underline hover:text-white"
        >
          Specifications
        </button>

        <button
          onClick={onOpenDrawer}
          className="transition-colors flex items-center gap-1.5 underline-offset-4 hover:underline hover:text-white"
        >
          <span>Corpus ({documents.length})</span>
        </button>

        <button
          onClick={onOpenGlobalChat}
          className={`transition-colors flex items-center gap-1.5 underline-offset-4 hover:underline ${
            isGlobalChatActive ? 'underline font-bold text-white' : 'hover:text-white'
          }`}
        >
          <Database className="w-3.5 h-3.5" />
          <span>Multi-Doc Search</span>
        </button>
      </div>

      {/* Right controls: Theme Toggle, Upload Trigger & Menu */}
      <div className="flex items-center gap-3">
        {/* Active Theme Toggle Button */}
        <button
          onClick={toggleTheme}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-mono font-medium transition-all bg-white/10 hover:bg-white/20 text-white border border-white/10 shadow-sm"
          title="Click to toggle between Seamless Halo and Deep Obsidian"
        >
          <Sparkles className="w-3 h-3 text-amber-400" />
          <span className="capitalize">
            {themeMode === 'seamless' ? 'Seamless Halo' : 'Deep Obsidian'}
          </span>
        </button>

        <button
          onClick={onOpenDrawer}
          className="hidden sm:flex items-center gap-1.5 px-4 py-2 rounded-full text-xs font-mono font-bold uppercase tracking-wider transition-opacity shadow-md bg-white text-black hover:bg-white/90"
        >
          <FileText className="w-3.5 h-3.5" />
          <span>Upload PDF</span>
        </button>

        {/* Minimalist Inspiration double-line hamburger icon '=' */}
        <button
          onClick={onOpenDrawer}
          className="w-9 h-9 rounded-full flex flex-col items-center justify-center gap-1 transition-colors text-white hover:bg-white/10"
          title="Open drawer menu"
        >
          <div className="w-4 h-[1.5px] bg-current rounded-full" />
          <div className="w-4 h-[1.5px] bg-current rounded-full" />
        </button>
      </div>
    </header>
  )
}

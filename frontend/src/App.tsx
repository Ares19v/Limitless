/**
 * Main App component — two-panel layout: sidebar + chat.
 */

import { useEffect } from 'react'
import { MessageSquarePlus, FileText } from 'lucide-react'
import { Header } from '@/components/Layout/Header'
import { Sidebar } from '@/components/Sidebar/Sidebar'
import { ChatWindow } from '@/components/ChatWindow/ChatWindow'
import { useAppStore } from '@/store'
import { cn } from '@/lib/utils'

function WelcomePane() {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-8 p-12 text-center">
      {/* Animated background blobs */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/3 w-96 h-96 bg-brand-200/30 dark:bg-brand-900/20 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-1/3 right-1/4 w-80 h-80 bg-purple-200/20 dark:bg-purple-900/10 rounded-full blur-3xl animate-pulse delay-1000" />
      </div>

      <div className="relative z-10 flex flex-col items-center gap-6 max-w-md">
        {/* Icon */}
        <div className="relative">
          <div className="w-24 h-24 rounded-3xl gradient-brand flex items-center justify-center shadow-2xl shadow-brand-500/30">
            <MessageSquarePlus className="w-12 h-12 text-white" />
          </div>
          <div className="absolute -top-1 -right-1 w-6 h-6 bg-emerald-400 rounded-full border-2 border-white dark:border-gray-950 flex items-center justify-center">
            <span className="text-xs">✨</span>
          </div>
        </div>

        {/* Copy */}
        <div>
          <h2 className="text-3xl font-bold text-slate-900 dark:text-white mb-3">
            Chat with your PDFs
          </h2>
          <p className="text-base text-slate-500 dark:text-slate-400 leading-relaxed">
            Upload any PDF document on the left and ask questions about it.
            Limitless uses AI to find the most relevant passages and give you
            accurate, cited answers.
          </p>
        </div>

        {/* Features */}
        <div className="grid grid-cols-1 gap-3 w-full text-left">
          {[
            { icon: '🔍', title: 'Semantic Search', desc: 'Finds meaning, not just keywords' },
            { icon: '📄', title: 'Source Citations', desc: 'Every answer links to the source page' },
            { icon: '⚡', title: 'Streaming Responses', desc: 'Real-time AI generation' },
          ].map((f) => (
            <div
              key={f.title}
              className="flex items-start gap-3 p-3 rounded-xl bg-white/60 dark:bg-white/5 border border-slate-200 dark:border-slate-700"
            >
              <span className="text-xl">{f.icon}</span>
              <div>
                <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">{f.title}</p>
                <p className="text-xs text-slate-500 dark:text-slate-400">{f.desc}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Hint */}
        <div className="flex items-center gap-2 text-sm text-slate-400">
          <FileText className="w-4 h-4" />
          <span>Select a document from the sidebar to begin</span>
        </div>
      </div>
    </div>
  )
}

export default function App() {
  const { selectedDocument, isDark } = useAppStore()

  // Apply dark mode class on mount and when toggled
  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDark)
  }, [isDark])

  return (
    <div className={cn('flex flex-col h-screen bg-slate-50 dark:bg-gray-950')}>
      <Header />

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside
          className={cn(
            'w-80 flex-shrink-0 border-r border-slate-200 dark:border-slate-800',
            'bg-slate-50 dark:bg-gray-950 overflow-y-auto',
          )}
        >
          <Sidebar />
        </aside>

        {/* Main content */}
        <main className="flex-1 overflow-hidden relative bg-white dark:bg-gray-900">
          {selectedDocument ? (
            <ChatWindow
              documentId={selectedDocument.id}
              documentName={selectedDocument.filename}
            />
          ) : (
            <WelcomePane />
          )}
        </main>
      </div>
    </div>
  )
}

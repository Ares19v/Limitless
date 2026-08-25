/**
 * Limitless Main Application — High-end cybernetic editorial interface.
 */

import { useState, useEffect } from 'react'
import { Header } from '@/components/Layout/Header'
import { WelcomePane } from '@/components/Hero/WelcomePane'
import { ChatWindow } from '@/components/ChatWindow/ChatWindow'
import { SpecificationsModal } from '@/components/Modals/SpecificationsModal'
import { UploadDrawer } from '@/components/Modals/UploadDrawer'
import { useAppStore } from '@/store'
import { useDocuments } from '@/hooks/useDocuments'

export default function App() {
  const { selectedDocument, selectDocument, isDark, isFullScreen } = useAppStore()
  const { documents } = useDocuments()

  const [isSpecsOpen, setIsSpecsOpen] = useState(false)
  const [isDrawerOpen, setIsDrawerOpen] = useState(false)
  const [isGlobalChatActive, setIsGlobalChatActive] = useState(false)

  // Sync dark class on html
  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDark)
  }, [isDark])

  const handleOpenGlobalChat = () => {
    selectDocument(null)
    setIsGlobalChatActive(true)
  }

  return (
    <div
      className={`min-h-screen w-full bg-[#08090C] font-sans antialiased transition-all duration-300 ${
        isFullScreen
          ? 'p-0 flex flex-col h-screen'
          : 'p-2 sm:p-4 md:p-6 flex items-center justify-center'
      }`}
    >
      {/* ── Monolithic Physical Frame / Kiosk Container (or full window) ── */}
      <div
        className={`relative w-full flex flex-col overflow-hidden transition-all duration-300 ${
          isFullScreen
            ? 'h-screen max-w-none rounded-none border-none shadow-none'
            : 'max-w-[1440px] h-[calc(100vh-16px)] sm:h-[calc(100vh-32px)] md:h-[calc(100vh-48px)] rounded-[24px] sm:rounded-[32px] md:rounded-[38px] border-2 border-[#33333E] shadow-[0_30px_90px_rgba(0,0,0,0.85)]'
        }`}
      >
        
        {/* Top Header (Hidden in chat mode) */}
        {!isGlobalChatActive && !selectedDocument && (
          <Header
            onOpenSpecs={() => setIsSpecsOpen(true)}
            onOpenDrawer={() => setIsDrawerOpen(true)}
            onOpenGlobalChat={handleOpenGlobalChat}
            isGlobalChatActive={isGlobalChatActive}
          />
        )}

        {/* Viewport Core Content */}
        <main className="relative flex-1 overflow-hidden">
          {isGlobalChatActive ? (
            <ChatWindow
              isGlobal
              documentName="Global Multi-Document Corpus"
              onClose={() => setIsGlobalChatActive(false)}
            />
          ) : selectedDocument ? (
            <ChatWindow
              documentId={selectedDocument.id}
              documentName={selectedDocument.filename}
              onClose={() => selectDocument(null)}
            />
          ) : (
            <WelcomePane
              onOpenSpecs={() => setIsSpecsOpen(true)}
              onOpenDrawer={() => setIsDrawerOpen(true)}
            />
          )}
        </main>
      </div>

      {/* ── Modals & Drawers ── */}
      <SpecificationsModal
        isOpen={isSpecsOpen}
        onClose={() => setIsSpecsOpen(false)}
      />

      <UploadDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
      />
    </div>
  )
}

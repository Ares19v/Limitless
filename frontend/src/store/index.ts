/**
 * Zustand store — global application state.
 */

import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import type { ChatMessage, Document, SourceChunk } from '@/types'

interface AppState {
  // ── Theme ──────────────────────────────────────────────────────────────
  isDark: boolean
  toggleDark: () => void

  // ── Documents ──────────────────────────────────────────────────────────
  documents: Document[]
  selectedDocument: Document | null
  isLoadingDocuments: boolean
  setDocuments: (docs: Document[]) => void
  addDocument: (doc: Document) => void
  updateDocument: (id: string, patch: Partial<Document>) => void
  removeDocument: (id: string) => void
  selectDocument: (doc: Document | null) => void
  setLoadingDocuments: (v: boolean) => void

  // ── Chat ───────────────────────────────────────────────────────────────
  messagesByDocument: Record<string, ChatMessage[]>
  isStreaming: boolean
  streamingSources: SourceChunk[]
  addMessage: (documentId: string, message: ChatMessage) => void
  updateLastAssistantMessage: (documentId: string, patch: Partial<ChatMessage>) => void
  setStreaming: (v: boolean) => void
  setStreamingSources: (sources: SourceChunk[]) => void
  clearChat: (documentId: string) => void

  // ── Upload state ────────────────────────────────────────────────────────
  uploadProgress: Record<string, number>
  setUploadProgress: (filename: string, pct: number) => void
  clearUploadProgress: (filename: string) => void
}

const prefersDark =
  typeof window !== 'undefined' &&
  window.matchMedia('(prefers-color-scheme: dark)').matches

export const useAppStore = create<AppState>()(
  devtools(
    (set, get) => ({
      // ── Theme ────────────────────────────────────────────────────────
      isDark: prefersDark,
      toggleDark: () => {
        const next = !get().isDark
        set({ isDark: next })
        document.documentElement.classList.toggle('dark', next)
      },

      // ── Documents ─────────────────────────────────────────────────────
      documents: [],
      selectedDocument: null,
      isLoadingDocuments: false,
      setDocuments: (docs) => set({ documents: docs }),
      addDocument: (doc) =>
        set((s) => ({ documents: [doc, ...s.documents] })),
      updateDocument: (id, patch) =>
        set((s) => ({
          documents: s.documents.map((d) => (d.id === id ? { ...d, ...patch } : d)),
          selectedDocument:
            s.selectedDocument?.id === id
              ? { ...s.selectedDocument, ...patch }
              : s.selectedDocument,
        })),
      removeDocument: (id) =>
        set((s) => ({
          documents: s.documents.filter((d) => d.id !== id),
          selectedDocument: s.selectedDocument?.id === id ? null : s.selectedDocument,
        })),
      selectDocument: (doc) => set({ selectedDocument: doc }),
      setLoadingDocuments: (v) => set({ isLoadingDocuments: v }),

      // ── Chat ──────────────────────────────────────────────────────────
      messagesByDocument: {},
      isStreaming: false,
      streamingSources: [],
      addMessage: (documentId, message) =>
        set((s) => ({
          messagesByDocument: {
            ...s.messagesByDocument,
            [documentId]: [...(s.messagesByDocument[documentId] ?? []), message],
          },
        })),
      updateLastAssistantMessage: (documentId, patch) =>
        set((s) => {
                  const msgs = [...(s.messagesByDocument[documentId] ?? [])]
          const lastIdx = msgs.reduce(
            (acc, m: ChatMessage, i) => (m.role === 'assistant' ? i : acc),
            -1,
          )
          if (lastIdx === -1) return s
          msgs[lastIdx] = { ...msgs[lastIdx], ...patch }
          return {
            messagesByDocument: { ...s.messagesByDocument, [documentId]: msgs },
          }
        }),
      setStreaming: (v) => set({ isStreaming: v }),
      setStreamingSources: (sources) => set({ streamingSources: sources }),
      clearChat: (documentId) =>
        set((s) => ({
          messagesByDocument: { ...s.messagesByDocument, [documentId]: [] },
        })),

      // ── Upload ─────────────────────────────────────────────────────────
      uploadProgress: {},
      setUploadProgress: (filename, pct) =>
        set((s) => ({
          uploadProgress: { ...s.uploadProgress, [filename]: pct },
        })),
      clearUploadProgress: (filename) =>
        set((s) => {
          const { [filename]: _, ...rest } = s.uploadProgress
          return { uploadProgress: rest }
        }),
    }),
    { name: 'DocuMindStore' },
  ),
)

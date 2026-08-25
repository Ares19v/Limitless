import { useState } from 'react'
import { X, FileText, Trash2, CheckCircle2, XCircle, Loader2, Sparkles, Plus, RefreshCw } from 'lucide-react'
import { FileUpload } from '@/components/FileUpload/FileUpload'
import { useAppStore } from '@/store'
import { useDocuments } from '@/hooks/useDocuments'
import { deleteDocument } from '@/lib/api'
import { formatBytes, formatRelativeTime } from '@/lib/utils'
import type { Document } from '@/types'

interface UploadDrawerProps {
  isOpen: boolean
  onClose: () => void
}

export function UploadDrawer({ isOpen, onClose }: UploadDrawerProps) {
  const { selectedDocument, selectDocument, removeDocument } = useAppStore()
  const { documents, isLoadingDocuments, refresh } = useDocuments()
  const [activeTab, setActiveTab] = useState<'upload' | 'library'>('library')
  const [deletingId, setDeletingId] = useState<string | null>(null)

  if (!isOpen) return null

  const handleDelete = async (doc: Document, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      setDeletingId(doc.id)
      await deleteDocument(doc.id)
      removeDocument(doc.id)
    } catch {
      // ignore
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm animate-fade-in">
      <div 
        className="w-full max-w-lg h-full bg-[#EAEAEA] dark:bg-[#18181C] text-[#121212] dark:text-[#EAEAEA] border-l-2 border-[#161616] dark:border-[#33333F] shadow-2xl flex flex-col p-6 md:p-8 animate-slide-in-right overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Top bar */}
        <div className="flex items-center justify-between pb-4 border-b border-[#161616]/15 dark:border-white/10 mb-6">
          <div>
            <span className="text-[11px] font-mono tracking-widest text-[#666666] dark:text-[#888899]">
              DOCUMENTS HUB // 01/07
            </span>
            <h2 className="text-2xl font-black tracking-tight font-display text-[#111111] dark:text-white">
              CORPUS MANAGEMENT
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-full hover:bg-black/10 dark:hover:bg-white/10 text-[#111111] dark:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab switch */}
        <div className="flex p-1 bg-black/5 dark:bg-white/5 rounded-full mb-6 border border-[#161616]/10 dark:border-white/10">
          <button
            onClick={() => setActiveTab('library')}
            className={`flex-1 py-2 rounded-full text-xs font-bold uppercase tracking-wider transition-all ${
              activeTab === 'library'
                ? 'bg-[#161616] text-white dark:bg-white dark:text-[#161616] shadow-sm'
                : 'text-[#666666] dark:text-[#888899] hover:text-black dark:hover:text-white'
            }`}
          >
            Library ({documents.length})
          </button>
          <button
            onClick={() => setActiveTab('upload')}
            className={`flex-1 py-2 rounded-full text-xs font-bold uppercase tracking-wider transition-all flex items-center justify-center gap-1.5 ${
              activeTab === 'upload'
                ? 'bg-[#161616] text-white dark:bg-white dark:text-[#161616] shadow-sm'
                : 'text-[#666666] dark:text-[#888899] hover:text-black dark:hover:text-white'
            }`}
          >
            <Plus className="w-3.5 h-3.5" />
            Upload PDF
          </button>
        </div>

        {/* Tab content */}
        {activeTab === 'upload' ? (
          <div className="flex-1">
            <FileUpload />
          </div>
        ) : (
          <div className="flex-1 flex flex-col">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-mono text-[#555555] dark:text-[#888899]">
                STORED DOCUMENTS
              </span>
              <button
                onClick={refresh}
                disabled={isLoadingDocuments}
                className="p-1 rounded hover:bg-black/5 dark:hover:bg-white/5 text-[#555555] dark:text-[#888899]"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isLoadingDocuments ? 'animate-spin' : ''}`} />
              </button>
            </div>

            {isLoadingDocuments && documents.length === 0 ? (
              <div className="py-12 flex flex-col items-center justify-center gap-2">
                <Loader2 className="w-6 h-6 animate-spin text-[#161616] dark:text-white" />
                <span className="text-xs font-mono text-[#666666]">INDEXING CORPUS...</span>
              </div>
            ) : documents.length === 0 ? (
              <div className="py-12 text-center rounded-2xl border border-dashed border-[#161616]/20 dark:border-white/20 p-6">
                <FileText className="w-8 h-8 mx-auto text-[#888888] mb-2" />
                <p className="text-sm font-bold text-[#111111] dark:text-white">No documents loaded yet</p>
                <p className="text-xs text-[#666666] dark:text-[#888899] mt-1 mb-4">
                  Upload a PDF document to begin chatting with it.
                </p>
                <button
                  onClick={() => setActiveTab('upload')}
                  className="px-4 py-2 rounded-full bg-[#161616] text-white dark:bg-white dark:text-[#161616] text-xs font-bold uppercase tracking-wider"
                >
                  Upload First PDF
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                {documents.map((doc) => {
                  const isSelected = selectedDocument?.id === doc.id
                  return (
                    <div
                      key={doc.id}
                      onClick={() => {
                        if (doc.status === 'ready') {
                          selectDocument(doc)
                          onClose()
                        }
                      }}
                      className={`group relative p-4 rounded-2xl border transition-all cursor-pointer ${
                        isSelected
                          ? 'border-[#161616] bg-white dark:bg-[#202026] dark:border-white shadow-md'
                          : 'border-[#161616]/10 dark:border-white/10 bg-white/60 dark:bg-white/5 hover:border-[#161616]/30 dark:hover:border-white/20'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex items-start gap-3 min-w-0">
                          <div className="w-9 h-9 rounded-xl bg-black/5 dark:bg-white/10 flex items-center justify-center flex-shrink-0">
                            <FileText className="w-4 h-4 text-[#111111] dark:text-white" />
                          </div>
                          <div className="min-w-0">
                            <p className="font-bold text-sm text-[#111111] dark:text-white truncate">
                              {doc.filename}
                            </p>
                            <div className="flex items-center gap-2 mt-1 text-[11px] font-mono text-[#666666] dark:text-[#888899]">
                              <span>{doc.chunk_count ? `${doc.chunk_count} chunks` : 'Parsing'}</span>
                              <span>•</span>
                              <span>{doc.file_size ? formatBytes(doc.file_size) : ''}</span>
                              <span>•</span>
                              <span>{formatRelativeTime(doc.created_at)}</span>
                            </div>
                          </div>
                        </div>

                        {/* Status / Delete */}
                        <div className="flex items-center gap-1.5 flex-shrink-0">
                          {doc.status === 'ready' && (
                            <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                          )}
                          {doc.status === 'processing' && (
                            <Loader2 className="w-4 h-4 animate-spin text-amber-600 dark:text-amber-400" />
                          )}
                          {doc.status === 'error' && (
                            <XCircle className="w-4 h-4 text-red-600 dark:text-red-400" />
                          )}
                          <button
                            onClick={(e) => handleDelete(doc, e)}
                            disabled={deletingId === doc.id}
                            className="p-1.5 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-red-500/10 hover:text-red-600 text-[#888888] transition-all"
                            title="Delete document"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>

                      {doc.summary && (
                        <div className="mt-3 pt-2.5 border-t border-[#161616]/10 dark:border-white/10 text-[11px] text-[#444444] dark:text-[#AAAAAA] line-clamp-2">
                          <span className="font-mono text-emerald-600 dark:text-emerald-400 font-medium">SUMMARY: </span>
                          {doc.summary.replace(/•/g, '').trim()}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

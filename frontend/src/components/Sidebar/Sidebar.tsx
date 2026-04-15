/**
 * Document Sidebar — lists uploaded docs with status indicators.
 */

import { useState } from 'react'
import {
  FileText,
  Trash2,
  ChevronRight,
  RefreshCw,
  Clock,
  CheckCircle2,
  XCircle,
  Loader2,
} from 'lucide-react'
import { cn, formatBytes, formatRelativeTime } from '@/lib/utils'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { FileUpload } from '@/components/FileUpload/FileUpload'
import { useAppStore } from '@/store'
import { useDocuments } from '@/hooks/useDocuments'
import { deleteDocument } from '@/lib/api'
import type { Document } from '@/types'

const STATUS_ICON = {
  processing: <Loader2 className="w-4 h-4 animate-spin text-amber-500" />,
  ready: <CheckCircle2 className="w-4 h-4 text-emerald-500" />,
  error: <XCircle className="w-4 h-4 text-red-500" />,
}

function DocumentItem({
  doc,
  isSelected,
  onSelect,
  onDelete,
}: {
  doc: Document
  isSelected: boolean
  onSelect: () => void
  onDelete: () => void
}) {
  const [confirming, setConfirming] = useState(false)

  return (
    <li
      className={cn(
        'group relative rounded-xl transition-all duration-200 cursor-pointer',
        'border',
        isSelected
          ? 'bg-brand-50 dark:bg-brand-950/30 border-brand-200 dark:border-brand-800'
          : 'bg-white dark:bg-gray-900 border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700',
      )}
    >
      <div
        className="flex items-start gap-3 p-3"
        onClick={doc.status === 'ready' ? onSelect : undefined}
      >
        {/* File icon */}
        <div
          className={cn(
            'flex-shrink-0 w-9 h-9 rounded-lg flex items-center justify-center',
            isSelected ? 'bg-brand-100 dark:bg-brand-900/50' : 'bg-slate-100 dark:bg-slate-800',
          )}
        >
          <FileText
            className={cn(
              'w-5 h-5',
              isSelected ? 'text-brand-600 dark:text-brand-400' : 'text-slate-500 dark:text-slate-400',
            )}
          />
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-slate-800 dark:text-slate-200 truncate">
            {doc.filename}
          </p>
          <div className="flex items-center gap-2 mt-1 flex-wrap">
            <Badge
              variant={doc.status === 'processing' ? 'processing' : doc.status === 'ready' ? 'ready' : 'error'}
            >
              {STATUS_ICON[doc.status]}
              <span className="capitalize">{doc.status}</span>
            </Badge>
            {doc.file_size && (
              <span className="text-xs text-slate-400">{formatBytes(doc.file_size)}</span>
            )}
          </div>
          <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">
            {formatRelativeTime(doc.created_at)}
          </p>
          {doc.status === 'ready' && (
            <p className="text-xs text-slate-400 dark:text-slate-500">
              {doc.chunk_count} chunks indexed
            </p>
          )}
        </div>

        {/* Selected indicator */}
        {isSelected && (
          <ChevronRight className="flex-shrink-0 w-4 h-4 text-brand-500 self-center" />
        )}
      </div>

      {/* Delete button */}
      {!confirming ? (
        <button
          onClick={(e) => { e.stopPropagation(); setConfirming(true) }}
          className={cn(
            'absolute top-2 right-2 p-1.5 rounded-lg',
            'opacity-0 group-hover:opacity-100 transition-opacity duration-200',
            'hover:bg-red-50 dark:hover:bg-red-950/30 text-slate-400 hover:text-red-500',
          )}
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      ) : (
        <div className="absolute top-2 right-2 flex gap-1 bg-white dark:bg-gray-900 shadow-lg rounded-lg p-1 border border-slate-200 dark:border-slate-700">
          <button
            onClick={(e) => { e.stopPropagation(); onDelete() }}
            className="px-2 py-1 text-xs font-medium text-red-600 hover:bg-red-50 dark:hover:bg-red-950/30 rounded"
          >
            Delete
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); setConfirming(false) }}
            className="px-2 py-1 text-xs font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded"
          >
            Cancel
          </button>
        </div>
      )}

      {/* Error message */}
      {doc.status === 'error' && doc.error_message && (
        <div className="px-3 pb-3">
          <p className="text-xs text-red-500 bg-red-50 dark:bg-red-950/20 rounded-lg px-2 py-1">
            {doc.error_message}
          </p>
        </div>
      )}
    </li>
  )
}

export function Sidebar() {
  const { selectedDocument, selectDocument, removeDocument } = useAppStore()
  const { documents, isLoadingDocuments, refresh } = useDocuments()

  const handleDelete = async (doc: Document) => {
    try {
      await deleteDocument(doc.id)
      removeDocument(doc.id)
    } catch {
      // TODO: show toast
    }
  }

  return (
    <aside className="flex flex-col h-full">
      {/* Upload section */}
      <div className="p-4 border-b border-slate-200 dark:border-slate-800">
        <h2 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-3">
          Upload Documents
        </h2>
        <FileUpload />
      </div>

      {/* Documents list */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
            My Documents ({documents.length})
          </h2>
          <button
            onClick={refresh}
            disabled={isLoadingDocuments}
            className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-600 transition-colors"
          >
            <RefreshCw className={cn('w-3.5 h-3.5', isLoadingDocuments && 'animate-spin')} />
          </button>
        </div>

        {isLoadingDocuments && documents.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 gap-3">
            <Loader2 className="w-6 h-6 text-brand-500 animate-spin" />
            <p className="text-sm text-slate-400">Loading documents…</p>
          </div>
        ) : documents.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 gap-3 text-center">
            <div className="w-14 h-14 rounded-2xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center">
              <FileText className="w-7 h-7 text-slate-300 dark:text-slate-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-500 dark:text-slate-400">No documents yet</p>
              <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">
                Upload a PDF to get started
              </p>
            </div>
          </div>
        ) : (
          <ul className="space-y-2">
            {documents.map((doc) => (
              <DocumentItem
                key={doc.id}
                doc={doc}
                isSelected={selectedDocument?.id === doc.id}
                onSelect={() => selectDocument(doc)}
                onDelete={() => handleDelete(doc)}
              />
            ))}
          </ul>
        )}
      </div>
    </aside>
  )
}

/**
 * FileUpload — Drag-and-drop zone for PDF files.
 */

import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { CloudUpload, X, FileText, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react'
import { cn, formatBytes } from '@/lib/utils'
import { Progress } from '@/components/ui/Progress'
import { Button } from '@/components/ui/Button'
import { useUpload } from '@/hooks/useUpload'

const MAX_SIZE = 50 * 1024 * 1024 // 50MB
const ACCEPT = { 'application/pdf': ['.pdf'] }

export function FileUpload() {
  const { queue, upload, removeFromQueue, clearQueue, isUploading } = useUpload()

  const onDrop = useCallback(
    (accepted: File[]) => {
      const valid = accepted.filter(
        (f) => !queue.some((q) => q.file.name === f.name && q.status !== 'error'),
      )
      if (valid.length) upload(valid)
    },
    [queue, upload],
  )

  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    accept: ACCEPT,
    maxSize: MAX_SIZE,
    multiple: true,
  })

  return (
    <div className="flex flex-col gap-4">
      {/* Drop zone */}
      <div
        {...getRootProps()}
        className={cn(
          'drop-zone p-8 flex flex-col items-center justify-center gap-4 rounded-2xl',
          'min-h-[200px] select-none',
          isDragActive && 'active',
        )}
      >
        <input {...getInputProps()} />

        <div
          className={cn(
            'w-16 h-16 rounded-2xl gradient-brand flex items-center justify-center',
            'transition-transform duration-300',
            isDragActive && 'scale-110 rotate-6',
          )}
        >
          <CloudUpload className="w-8 h-8 text-white" />
        </div>

        <div className="text-center">
          <p className="text-base font-semibold text-slate-700 dark:text-slate-200">
            {isDragActive ? 'Drop your PDFs here' : 'Drag & drop PDFs here'}
          </p>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            or <span className="text-brand-500 font-medium cursor-pointer hover:underline">browse to upload</span>
          </p>
          <p className="text-xs text-slate-400 dark:text-slate-500 mt-2">
            PDF only · Max {MAX_SIZE / 1024 / 1024}MB per file · Multiple files supported
          </p>
        </div>
      </div>

      {/* Rejections */}
      {fileRejections.length > 0 && (
        <div className="rounded-xl bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800 p-3">
          {fileRejections.map(({ file, errors }) => (
            <p key={file.name} className="text-xs text-red-600 dark:text-red-400">
              <strong>{file.name}</strong>: {errors.map((e) => e.message).join(', ')}
            </p>
          ))}
        </div>
      )}

      {/* Upload queue */}
      {queue.length > 0 && (
        <div className="rounded-2xl border border-slate-200 dark:border-slate-700 overflow-hidden">
          <div className="flex items-center justify-between px-4 py-2 bg-slate-50 dark:bg-slate-800/50 border-b border-slate-200 dark:border-slate-700">
            <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Upload Queue ({queue.length})
            </p>
            {!isUploading && (
              <Button variant="ghost" size="sm" onClick={clearQueue}>
                Clear all
              </Button>
            )}
          </div>

          <ul className="divide-y divide-slate-100 dark:divide-slate-800">
            {queue.map((item) => (
              <li key={item.file.name} className="flex items-center gap-3 p-3">
                {/* Status icon */}
                <div className="flex-shrink-0">
                  {item.status === 'done' && <CheckCircle2 className="w-5 h-5 text-emerald-500" />}
                  {item.status === 'error' && <AlertCircle className="w-5 h-5 text-red-500" />}
                  {item.status === 'uploading' && (
                    <Loader2 className="w-5 h-5 text-brand-500 animate-spin" />
                  )}
                  {item.status === 'pending' && (
                    <FileText className="w-5 h-5 text-slate-400" />
                  )}
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-700 dark:text-slate-200 truncate">
                    {item.file.name}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <p className="text-xs text-slate-400">
                      {formatBytes(item.file.size)}
                    </p>
                    {item.status === 'error' && (
                      <p className="text-xs text-red-500">{item.error}</p>
                    )}
                  </div>
                  {item.status === 'uploading' && (
                    <Progress value={item.progress} className="mt-2" />
                  )}
                </div>

                {/* Remove */}
                {item.status !== 'uploading' && (
                  <button
                    onClick={() => removeFromQueue(item.file)}
                    className="p-1 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-400 hover:text-slate-600 transition-colors"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

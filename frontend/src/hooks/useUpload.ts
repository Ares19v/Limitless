import { useCallback, useState } from 'react'
import { uploadPDF } from '@/lib/api'
import { useAppStore } from '@/store'
import { generateId } from '@/lib/utils'

interface UploadItem {
  file: File
  progress: number
  status: 'pending' | 'uploading' | 'done' | 'error'
  error?: string
  documentId?: string
}

export function useUpload() {
  const { addDocument, setUploadProgress, clearUploadProgress } = useAppStore()
  const [queue, setQueue] = useState<UploadItem[]>([])
  const [isUploading, setIsUploading] = useState(false)

  const updateItem = (file: File, patch: Partial<UploadItem>) =>
    setQueue((q) => q.map((item) => (item.file === file ? { ...item, ...patch } : item)))

  const upload = useCallback(
    async (files: File[]) => {
      if (isUploading) return

      const newItems: UploadItem[] = files.map((f) => ({
        file: f,
        progress: 0,
        status: 'pending',
      }))
      setQueue((q) => [...q, ...newItems])
      setIsUploading(true)

      for (const item of newItems) {
        updateItem(item.file, { status: 'uploading' })
        try {
          const result = await uploadPDF(item.file, (pct) => {
            updateItem(item.file, { progress: pct })
            setUploadProgress(item.file.name, pct)
          })

          // Optimistically add document to sidebar as 'processing'
          addDocument({
            id: result.document_id,
            filename: result.filename,
            file_size: item.file.size,
            status: 'processing',
            chunk_count: 0,
            created_at: new Date().toISOString(),
            error_message: null,
            summary: null,
          })

          updateItem(item.file, { status: 'done', progress: 100, documentId: result.document_id })
          clearUploadProgress(item.file.name)
        } catch (err: unknown) {
          const msg = err instanceof Error ? err.message : 'Upload failed'
          updateItem(item.file, { status: 'error', error: msg })
          clearUploadProgress(item.file.name)
        }
      }

      setIsUploading(false)
    },
    [isUploading, addDocument, setUploadProgress, clearUploadProgress],
  )

  const clearQueue = () => setQueue([])
  const removeFromQueue = (file: File) =>
    setQueue((q) => q.filter((i) => i.file !== file))

  return { queue, isUploading, upload, clearQueue, removeFromQueue }
}

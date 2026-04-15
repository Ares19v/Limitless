import { useCallback, useEffect, useRef } from 'react'
import { fetchDocument, fetchDocuments } from '@/lib/api'
import { useAppStore } from '@/store'

const POLL_INTERVAL = 4000 // ms

/** Fetches and keeps documents in sync, polls processing docs. */
export function useDocuments() {
  const { documents, setDocuments, updateDocument, isLoadingDocuments, setLoadingDocuments } =
    useAppStore()
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const load = useCallback(async () => {
    setLoadingDocuments(true)
    try {
      const res = await fetchDocuments(50)
      setDocuments(res.documents)
    } catch {
      // silently fail — user can refresh
    } finally {
      setLoadingDocuments(false)
    }
  }, [setDocuments, setLoadingDocuments])

  // Poll documents that are currently processing
  const pollProcessing = useCallback(async () => {
    const processingDocs = documents.filter((d) => d.status === 'processing')
    for (const doc of processingDocs) {
      try {
        const updated = await fetchDocument(doc.id)
        if (updated.status !== doc.status) {
          updateDocument(doc.id, updated)
        }
      } catch {
        // ignore
      }
    }
  }, [documents, updateDocument])

  useEffect(() => {
    load()
  }, [load])

  useEffect(() => {
    const hasProcessing = documents.some((d) => d.status === 'processing')
    if (hasProcessing) {
      pollRef.current = setInterval(pollProcessing, POLL_INTERVAL)
    } else {
      if (pollRef.current) {
        clearInterval(pollRef.current)
        pollRef.current = null
      }
    }
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [documents, pollProcessing])

  return { documents, isLoadingDocuments, refresh: load }
}

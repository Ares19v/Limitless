import { useCallback, useEffect, useRef } from 'react'
import { fetchChatStream } from '@/lib/api'
import { useAppStore } from '@/store'
import { generateId } from '@/lib/utils'
import type { SourceChunk } from '@/types'

export function useChat(documentId: string | null) {
  const {
    messagesByDocument,
    isStreaming,
    streamingSources,
    addMessage,
    updateLastAssistantMessage,
    setStreaming,
    setStreamingSources,
    clearChat,
  } = useAppStore()

  const messages = documentId ? (messagesByDocument[documentId] ?? []) : []
  const abortRef = useRef<AbortController | null>(null)

  const sendMessage = useCallback(
    async (text: string) => {
      if (!documentId || isStreaming || !text.trim()) return

      // Add user message
      const userMsg = {
        id: generateId(),
        role: 'user' as const,
        content: text.trim(),
        timestamp: new Date().toISOString(),
      }
      addMessage(documentId, userMsg)

      // Add placeholder assistant message
      const assistantMsgId = generateId()
      addMessage(documentId, {
        id: assistantMsgId,
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString(),
        isStreaming: true,
        sources: [],
      })

      setStreaming(true)
      setStreamingSources([])

      // Build history for context
      const history = messages
        .slice(-10)
        .map((m) => ({ role: m.role, content: m.content }))

      try {
        let accumulated = ''
        for await (const event of fetchChatStream(documentId, text.trim(), history)) {
          if (event.type === 'token') {
            accumulated += event.data
            updateLastAssistantMessage(documentId, {
              content: accumulated,
              isStreaming: true,
            })
          } else if (event.type === 'sources') {
            try {
              const sources: SourceChunk[] = JSON.parse(event.data)
              setStreamingSources(sources)
              updateLastAssistantMessage(documentId, { sources })
            } catch {
              // ignore parse errors
            }
          } else if (event.type === 'done') {
            updateLastAssistantMessage(documentId, { isStreaming: false })
            break
          }
        }
      } catch (err: unknown) {
        const errorMsg =
          err instanceof Error ? err.message : 'An error occurred. Please try again.'
        updateLastAssistantMessage(documentId, {
          content: `❌ ${errorMsg}`,
          isStreaming: false,
        })
      } finally {
        setStreaming(false)
      }
    },
    [documentId, isStreaming, messages, addMessage, updateLastAssistantMessage, setStreaming, setStreamingSources],
  )

  const stopStreaming = useCallback(() => {
    abortRef.current?.abort()
    setStreaming(false)
    updateLastAssistantMessage(documentId ?? '', { isStreaming: false })
  }, [documentId, setStreaming, updateLastAssistantMessage])

  return {
    messages,
    isStreaming,
    streamingSources,
    sendMessage,
    stopStreaming,
    clearChat: () => documentId && clearChat(documentId),
  }
}

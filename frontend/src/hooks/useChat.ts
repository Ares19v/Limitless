import { useCallback, useRef } from 'react'
import { fetchChatStream, fetchAgentStream, fetchGlobalChatStream } from '@/lib/api'
import { useAppStore } from '@/store'
import { generateId } from '@/lib/utils'
import type { AgentStep, SourceChunk } from '@/types'

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

  const docKey = documentId ?? 'global'
  const messages = messagesByDocument[docKey] ?? []
  const abortRef = useRef<AbortController | null>(null)

  const sendMessage = useCallback(
    async (text: string, isAgent: boolean = false) => {
      if (isStreaming || !text.trim()) return

      // Add user message
      const userMsg = {
        id: generateId(),
        role: 'user' as const,
        content: text.trim(),
        timestamp: new Date().toISOString(),
      }
      addMessage(docKey, userMsg)

      // Add placeholder assistant message
      const assistantMsgId = generateId()
      addMessage(docKey, {
        id: assistantMsgId,
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString(),
        isStreaming: true,
        sources: [],
        agentSteps: [],
      })

      setStreaming(true)
      setStreamingSources([])

      // Build history for context
      const history = messages
        .slice(-10)
        .map((m) => ({ role: m.role, content: m.content }))

      try {
        let accumulated = ''
        const accumulatedSteps: AgentStep[] = []

        if (!documentId) {
          // Global Multi-Doc Chat
          for await (const event of fetchGlobalChatStream(text.trim())) {
            if (event.type === 'token') {
              accumulated += event.data
              updateLastAssistantMessage(docKey, {
                content: accumulated,
                isStreaming: true,
              })
            } else if (event.type === 'sources') {
              try {
                const sources: SourceChunk[] = JSON.parse(event.data)
                setStreamingSources(sources)
                updateLastAssistantMessage(docKey, { sources })
              } catch {
                // ignore
              }
            } else if (event.type === 'done') {
              updateLastAssistantMessage(docKey, { isStreaming: false })
              break
            }
          }
        } else if (isAgent) {
          // Autonomous ReAct Agent Mode
          for await (const event of fetchAgentStream(documentId, text.trim())) {
            if (event.type === 'token') {
              accumulated += event.data
              updateLastAssistantMessage(docKey, {
                content: accumulated,
                isStreaming: true,
              })
            } else if (event.type === 'step') {
              try {
                const stepData: AgentStep = JSON.parse(event.data)
                accumulatedSteps.push(stepData)
                updateLastAssistantMessage(docKey, {
                  agentSteps: [...accumulatedSteps],
                })
              } catch {
                // ignore
              }
            } else if (event.type === 'done') {
              updateLastAssistantMessage(docKey, { isStreaming: false })
              break
            }
          }
        } else {
          // Standard Single-Doc Hybrid RAG
          for await (const event of fetchChatStream(documentId, text.trim(), history)) {
            if (event.type === 'token') {
              accumulated += event.data
              updateLastAssistantMessage(docKey, {
                content: accumulated,
                isStreaming: true,
              })
            } else if (event.type === 'sources') {
              try {
                const sources: SourceChunk[] = JSON.parse(event.data)
                setStreamingSources(sources)
                updateLastAssistantMessage(docKey, { sources })
              } catch {
                // ignore
              }
            } else if (event.type === 'done') {
              updateLastAssistantMessage(docKey, { isStreaming: false })
              break
            }
          }
        }
      } catch (err: unknown) {
        const errorMsg =
          err instanceof Error ? err.message : 'An error occurred. Please try again.'
        updateLastAssistantMessage(docKey, {
          content: `❌ ${errorMsg}`,
          isStreaming: false,
        })
      } finally {
        setStreaming(false)
      }
    },
    [docKey, documentId, isStreaming, messages, addMessage, updateLastAssistantMessage, setStreaming, setStreamingSources],
  )

  const stopStreaming = useCallback(() => {
    abortRef.current?.abort()
    setStreaming(false)
    updateLastAssistantMessage(docKey, { isStreaming: false })
  }, [docKey, setStreaming, updateLastAssistantMessage])

  return {
    messages,
    isStreaming,
    streamingSources,
    sendMessage,
    stopStreaming,
    clearChat: () => clearChat(docKey),
  }
}

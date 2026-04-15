/// <reference types="vite/client" />
import axios from 'axios'

import type {
  Document,
  DocumentListResponse,
  UploadResponse,
  HealthResponse,
} from '@/types'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export const api = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  timeout: 30_000,
})

// ── Document endpoints ────────────────────────────────────────────────────

export async function fetchDocuments(limit = 20, offset = 0): Promise<DocumentListResponse> {
  const { data } = await api.get<DocumentListResponse>('/documents', {
    params: { limit, offset },
  })
  return data
}

export async function fetchDocument(id: string): Promise<Document> {
  const { data } = await api.get<Document>(`/documents/${id}`)
  return data
}

export async function deleteDocument(id: string): Promise<void> {
  await api.delete(`/documents/${id}`)
}

// ── Upload endpoint ───────────────────────────────────────────────────────

export async function uploadPDF(
  file: File,
  onProgress?: (percent: number) => void,
): Promise<UploadResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const { data } = await api.post<UploadResponse>('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (onProgress && e.total) {
        onProgress(Math.round((e.loaded / e.total) * 100))
      }
    },
  })
  return data
}

// ── Chat (SSE) ────────────────────────────────────────────────────────────

export function createChatStream(
  documentId: string,
  message: string,
  history: { role: string; content: string }[],
): EventSource {
  // SSE via POST requires a workaround — we use fetch + ReadableStream
  // This is handled in useChat hook; this function is kept for reference.
  throw new Error('Use fetchChatStream instead')
}

export async function* fetchChatStream(
  documentId: string,
  message: string,
  history: { role: string; content: string }[],
): AsyncGenerator<{ type: 'token' | 'sources' | 'done'; data: string }> {
  const url = `${BASE_URL}/api/v1/chat/${documentId}`
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
    },
    body: JSON.stringify({ document_id: documentId, message, history }),
  })

  if (!response.ok) {
    throw new Error(`Chat error: ${response.status} ${response.statusText}`)
  }

  const reader = response.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''

    let eventType = 'message'
    for (const line of lines) {
      if (line.startsWith('event: ')) {
        eventType = line.slice(7).trim()
      } else if (line.startsWith('data: ')) {
        const data = line.slice(6)
        if (eventType === 'sources') {
          yield { type: 'sources', data }
        } else if (data === '[DONE]') {
          yield { type: 'done', data: '' }
          return
        } else {
          yield { type: 'token', data }
        }
        eventType = 'message'
      }
    }
  }
}

// ── Health ────────────────────────────────────────────────────────────────

export async function checkHealth(): Promise<HealthResponse> {
  const { data } = await axios.get<HealthResponse>(`${BASE_URL}/health`)
  return data
}

// ── History ───────────────────────────────────────────────────────────────

export async function fetchHistory(
  documentId: string,
): Promise<{ role: string; content: string }[]> {
  const { data } = await api.get(`/history/${documentId}`)
  return data
}

export async function clearHistory(documentId: string): Promise<void> {
  await api.delete(`/history/${documentId}`)
}

// ── Global Chat (SSE) ────────────────────────────────────────────────────

export async function* fetchGlobalChatStream(
  message: string,
): AsyncGenerator<{ type: 'token' | 'sources' | 'done'; data: string }> {
  const url = `${BASE_URL}/api/v1/chat/global`
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
    body: JSON.stringify({ message }),
  })
  if (!response.ok) throw new Error(`Global chat error: ${response.status}`)
  yield* _readSSEStream(response)
}

// ── Agent Chat (SSE) ─────────────────────────────────────────────────────

export async function* fetchAgentStream(
  documentId: string,
  message: string,
): AsyncGenerator<{ type: 'token' | 'step' | 'done'; data: string }> {
  const url = `${BASE_URL}/api/v1/agent/${documentId}`
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
    body: JSON.stringify({ message }),
  })
  if (!response.ok) throw new Error(`Agent error: ${response.status}`)

  const reader = response.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let eventType = 'message'

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''
    for (const line of lines) {
      if (line.startsWith('event: ')) {
        eventType = line.slice(7).trim()
      } else if (line.startsWith('data: ')) {
        const data = line.slice(6)
        if (data === '[DONE]') { yield { type: 'done', data: '' }; return }
        if (eventType === 'step') yield { type: 'step', data }
        else yield { type: 'token', data }
        eventType = 'message'
      }
    }
  }
}

// ── Shared SSE reader ─────────────────────────────────────────────────────

async function* _readSSEStream(
  response: Response,
): AsyncGenerator<{ type: 'token' | 'sources' | 'done'; data: string }> {
  const reader = response.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let eventType = 'message'

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''
    for (const line of lines) {
      if (line.startsWith('event: ')) {
        eventType = line.slice(7).trim()
      } else if (line.startsWith('data: ')) {
        const data = line.slice(6)
        if (eventType === 'sources') { yield { type: 'sources', data }; }
        else if (data === '[DONE]') { yield { type: 'done', data: '' }; return }
        else yield { type: 'token', data }
        eventType = 'message'
      }
    }
  }
}

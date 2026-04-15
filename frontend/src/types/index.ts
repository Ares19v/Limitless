// TypeScript interfaces mirroring backend Pydantic schemas

export type DocumentStatus = 'processing' | 'ready' | 'error'

export interface Document {
  id: string
  filename: string
  file_size: number | null
  status: DocumentStatus
  chunk_count: number
  created_at: string
  error_message: string | null
  summary?: string | null
}

export interface DocumentListResponse {
  documents: Document[]
  total: number
}

export interface UploadResponse {
  document_id: string
  filename: string
  message: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  sources?: SourceChunk[]
  isStreaming?: boolean
  agentSteps?: AgentStep[]
}

export interface SourceChunk {
  content: string
  page: number | null
  score: number
}

export interface ChatRequest {
  document_id: string
  message: string
  history: { role: string; content: string }[]
}

export interface HealthResponse {
  status: string
  version: string
  timestamp: string
}

export interface AgentStep {
  tool: string
  input: string
  emoji: string
}

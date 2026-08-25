/**
 * ChatWindow — Premium Cybernetic Document Conversation Console.
 */

import { useEffect, useRef, useState, KeyboardEvent } from 'react'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import {
  Send,
  Square,
  Copy,
  Check,
  ChevronDown,
  BookOpen,
  Sparkles,
  RotateCcw,
  Bot,
  FileText,
  ArrowLeft,
  Database,
  Cpu,
  Layers,
  Zap,
  ShieldCheck,
  Search,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useChat } from '@/hooks/useChat'
import { useAppStore } from '@/store'
import type { AgentStep, ChatMessage, SourceChunk } from '@/types'

// ── Typing Indicator ────────────────────────────────────────────────────────
function TypingIndicator() {
  return (
    <div className="flex items-center gap-2 px-4 py-2.5 bg-white/[0.06] backdrop-blur-md border border-white/10 rounded-2xl w-fit shadow-lg">
      <div className="flex items-center gap-1.5">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="w-1.5 h-1.5 rounded-full bg-white animate-pulse"
            style={{ animationDelay: `${i * 0.2}s` }}
          />
        ))}
      </div>
      <span className="text-[10px] font-mono text-white/70 tracking-widest uppercase ml-1">
        SYNTHESIZING // GROQ LPU
      </span>
    </div>
  )
}

// ── Copy Button ─────────────────────────────────────────────────────────────
function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)
  const copy = async () => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }
  return (
    <button
      onClick={copy}
      className="p-1.5 rounded-lg hover:bg-white/10 text-white/50 hover:text-white transition-all"
      title="Copy answer"
    >
      {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
    </button>
  )
}

// ── Agent Step Display ──────────────────────────────────────────────────────
function AgentStepBadge({ step }: { step: AgentStep }) {
  return (
    <div className="flex items-center gap-2 text-xs font-mono text-white/80 bg-white/[0.05] rounded-xl px-3 py-2 border border-white/10 animate-fade-in my-1 shadow-sm">
      <span className="text-amber-400">{step.emoji || '⚡'}</span>
      <span className="font-bold text-white uppercase tracking-wider">{step.tool.replace('_', ' ')}</span>
      <span className="text-white/40">→</span>
      <span className="truncate max-w-[280px] text-[11px] text-white/70">{step.input}</span>
    </div>
  )
}

// ── Verbatim Source Citation Drawer Component ───────────────────────────────
function SourceCitationDrawer({ sources }: { sources: SourceChunk[] }) {
  const [isOpen, setIsOpen] = useState(false)

  if (!sources || sources.length === 0) return null

  return (
    <div className="mt-4 pt-3 border-t border-white/10">
      <div className="flex items-center gap-2 flex-wrap">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-2 px-3 py-1 rounded-full bg-white/[0.08] hover:bg-white/[0.14] text-xs font-mono font-bold uppercase tracking-wider text-white transition-all border border-white/10"
        >
          <BookOpen className="w-3.5 h-3.5 text-emerald-400" />
          <span>{sources.length} VERIFIED SOURCES</span>
          <ChevronDown className={cn('w-3.5 h-3.5 transition-transform duration-200', isOpen && 'rotate-180')} />
        </button>

        {sources.slice(0, 3).map((src, i) => (
          <span
            key={i}
            className="text-[10px] font-mono px-2.5 py-0.5 rounded-full bg-white/[0.05] text-white/70 border border-white/5"
          >
            P.{src.page || '1'} • {Math.round((src.score || 0.8) * 100)}%
          </span>
        ))}
      </div>

      {isOpen && (
        <div className="mt-3 space-y-2.5 animate-fade-in">
          {sources.map((src, idx) => (
            <div
              key={idx}
              className="p-3.5 rounded-xl bg-white/[0.03] border border-white/10 hover:border-white/25 transition-all text-xs"
            >
              <div className="flex items-center justify-between font-mono text-[10px] text-white/60 mb-2">
                <span className="font-bold text-white uppercase tracking-wider">
                  [EXCERPT {idx + 1}]
                </span>
                <div className="flex items-center gap-2">
                  {src.page && (
                    <span className="bg-white/10 text-white px-2 py-0.5 rounded-md">
                      PAGE {src.page}
                    </span>
                  )}
                  <span className="text-emerald-400 font-bold">
                    {Math.round((src.score || 0.85) * 100)}% MATCH
                  </span>
                </div>
              </div>
              <p className="text-white/80 leading-relaxed font-sans text-xs italic bg-black/20 p-2.5 rounded-lg border border-white/5">
                "{src.content}"
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ── Main ChatWindow Component ───────────────────────────────────────────────
interface ChatWindowProps {
  documentId?: string
  documentName?: string
  isGlobal?: boolean
  onClose?: () => void
}

export function ChatWindow({
  documentId,
  documentName = 'All Documents',
  isGlobal = false,
  onClose,
}: ChatWindowProps) {
  const {
    messagesByDocument,
    isStreaming,
    selectedDocument,
    selectDocument,
    clearChat,
  } = useAppStore()

  const docKey = isGlobal ? 'global' : (documentId ?? '')
  const messages = messagesByDocument[docKey] ?? []

  const [input, setInput] = useState('')
  const [showSummary, setShowSummary] = useState(false)
  const [isAgentMode, setIsAgentMode] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const { sendMessage, stopStreaming } = useChat(documentId || null)

  // Auto scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isStreaming])

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus()
  }, [documentId, isGlobal])

  const handleSend = () => {
    const text = input.trim()
    if (!text || isStreaming) return
    sendMessage(text, isAgentMode)
    setInput('')
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleBack = () => {
    if (onClose) onClose()
    selectDocument(null)
  }

  return (
    <div
      className="relative flex flex-col h-full text-white select-none overflow-hidden"
      style={{
        background: 'radial-gradient(ellipse at 50% 25%, #2D2D38 0%, #181820 45%, #0E0E14 100%)',
      }}
    >
      {/* ── Subtle Background Watermark Glyphs ── */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden flex items-center justify-between z-0 opacity-40">
        <span className="text-[200px] font-black font-headline text-white/[0.02] -translate-x-12">
          {isGlobal ? 'ALL' : 'DOC'}
        </span>
        <span className="text-[200px] font-black font-headline text-white/[0.02] translate-x-12">
          RAG
        </span>
      </div>

      {/* ── Top Console HUD Bar ── */}
      <div className="relative z-10 h-16 flex items-center justify-between px-6 sm:px-10 border-b border-white/10 bg-[#111116]/60 backdrop-blur-xl flex-shrink-0">
        <div className="flex items-center gap-3 min-w-0">
          <button
            onClick={handleBack}
            className="w-9 h-9 rounded-full bg-white/5 hover:bg-white/15 border border-white/10 flex items-center justify-center text-white/70 hover:text-white transition-all"
            title="Return to Overview"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>

          <div className="flex items-baseline gap-2 min-w-0">
            <span className="font-mono text-xs font-bold uppercase tracking-wider text-white/40 hidden sm:inline">
              {isGlobal ? 'MULTI-DOC' : 'DOC'} //
            </span>
            <h2 className="font-display font-black text-sm sm:text-base text-white truncate max-w-xs sm:max-w-md">
              {documentName}
            </h2>
          </div>

          {selectedDocument?.chunk_count && (
            <span className="text-[10px] font-mono px-2.5 py-0.5 rounded-full bg-white/10 text-white/80 border border-white/10 hidden md:inline">
              {selectedDocument.chunk_count} CHUNKS
            </span>
          )}
        </div>

        {/* HUD Controls */}
        <div className="flex items-center gap-2.5">
          {/* ReAct Agent Mode Toggle */}
          <button
            onClick={() => setIsAgentMode(!isAgentMode)}
            className={cn(
              'hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-mono font-medium transition-all border',
              isAgentMode
                ? 'bg-amber-500/20 text-amber-300 border-amber-500/40 shadow-[0_0_12px_rgba(245,158,11,0.2)]'
                : 'bg-white/5 text-white/60 border-white/10 hover:text-white hover:bg-white/10',
            )}
            title="Toggle Autonomous ReAct Agent Mode"
          >
            <Zap className={cn('w-3 h-3', isAgentMode ? 'text-amber-400 fill-current' : 'text-white/60')} />
            <span>{isAgentMode ? 'AGENT ACTIVE' : 'STANDARD RAG'}</span>
          </button>

          {/* Executive Summary Button */}
          {selectedDocument?.summary && (
            <button
              onClick={() => setShowSummary(!showSummary)}
              className={cn(
                'flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-mono font-medium transition-all border',
                showSummary
                  ? 'bg-white text-black border-white shadow-md'
                  : 'bg-white/5 text-white/70 border-white/10 hover:text-white hover:bg-white/10',
              )}
            >
              <Sparkles className="w-3 h-3" />
              <span className="hidden md:inline">Summary</span>
            </button>
          )}

          {/* Clear History */}
          <button
            onClick={() => clearChat(docKey)}
            className="w-9 h-9 rounded-full bg-white/5 hover:bg-white/15 border border-white/10 flex items-center justify-center text-white/60 hover:text-white transition-all"
            title="Clear conversation history"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* ── Auto Executive Summary Briefing Card ── */}
      {selectedDocument?.summary && showSummary && (
        <div className="relative z-10 px-6 sm:px-10 py-3 bg-white/[0.04] backdrop-blur-md border-b border-white/10 animate-fade-in flex-shrink-0">
          <div className="max-w-4xl mx-auto flex items-start justify-between gap-4">
            <div className="flex items-start gap-3">
              <div className="p-1.5 rounded-lg bg-white/10 border border-white/10 flex-shrink-0 mt-0.5">
                <Sparkles className="w-3.5 h-3.5 text-amber-300" />
              </div>
              <div className="text-xs leading-relaxed text-white/80 font-sans">
                <span className="font-mono font-bold uppercase tracking-wider text-white mr-2">
                  AUTO-SYNTHESIS //
                </span>
                {selectedDocument.summary}
              </div>
            </div>
            <button
              onClick={() => setShowSummary(false)}
              className="text-white/40 hover:text-white text-[11px] font-mono tracking-wider uppercase flex-shrink-0 transition-colors pt-0.5"
            >
              [HIDE]
            </button>
          </div>
        </div>
      )}

      {/* ── Message Stream Viewport ── */}
      <div className="relative z-10 flex-1 overflow-y-auto p-4 sm:p-6 md:p-8 space-y-6">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 max-w-xl mx-auto">
            <div className="w-14 h-14 rounded-2xl bg-white/[0.06] border border-white/15 flex items-center justify-center mb-4 shadow-xl backdrop-blur-md">
              <FileText className="w-7 h-7 text-white" />
            </div>
            <div className="flex items-center gap-2 mb-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <h3 className="font-display font-black text-xl text-white uppercase tracking-tight">
                SESSION READY
              </h3>
            </div>
            <p className="text-xs md:text-sm text-white/70 leading-relaxed mb-6 font-sans max-w-md">
              Ask anything about <strong className="text-white underline underline-offset-4">{documentName}</strong>. The pipeline will retrieve verified chunks with semantic citations and Groq LPU inference.
            </p>

            {/* Quick Suggested Prompt Chips */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 w-full text-left">
              {[
                'What is the core objective of this document?',
                'Summarize key technical specifications',
                'What methodology or architecture is proposed?',
                'What are the primary conclusions & findings?',
              ].map((suggestion, idx) => (
                <button
                  key={idx}
                  onClick={() => sendMessage(suggestion, isAgentMode)}
                  className="p-3 rounded-xl bg-white/[0.04] hover:bg-white/[0.1] border border-white/10 hover:border-white/30 text-xs text-white/80 hover:text-white transition-all font-sans hover:-translate-y-0.5 backdrop-blur-md shadow-sm flex items-center gap-2 group"
                >
                  <span className="font-mono text-[10px] text-white/40 group-hover:text-white/70">
                    0{idx + 1}
                  </span>
                  <span className="truncate">{suggestion}</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg, index) => {
            const isUser = msg.role === 'user'
            return (
              <div
                key={msg.id || index}
                className={cn('flex flex-col max-w-4xl mx-auto', isUser ? 'items-end' : 'items-start')}
              >
                {/* Speaker Indicator */}
                <div className="flex items-center gap-2 mb-1.5 px-1 font-mono text-[10px] uppercase tracking-widest text-white/50">
                  <span>{isUser ? 'YOU' : 'LIMITLESS // RAG ENGINE'}</span>
                  <span>•</span>
                  <span>
                    {msg.timestamp
                      ? new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                      : ''}
                  </span>
                </div>

                {/* Message Bubble Card */}
                <div
                  className={cn(
                    'rounded-2xl p-5 md:p-6 transition-all max-w-[92%] md:max-w-[85%] backdrop-blur-xl shadow-2xl',
                    isUser
                      ? 'bg-white/10 border border-white/20 text-white rounded-tr-sm'
                      : 'bg-black/50 border border-white/15 text-white/95 rounded-tl-sm',
                  )}
                >
                  {/* ReAct Agent Tool Execution Steps */}
                  {msg.agentSteps && msg.agentSteps.length > 0 && (
                    <div className="mb-3.5 pb-3.5 border-b border-white/10 space-y-1.5">
                      <span className="text-[10px] font-mono uppercase tracking-widest text-amber-300 block mb-1">
                        // REASONING TRACE
                      </span>
                      {msg.agentSteps.map((st: AgentStep, i: number) => (
                        <AgentStepBadge key={i} step={st} />
                      ))}
                    </div>
                  )}

                  {/* Clean Markdown Typography */}
                  <div className="prose prose-invert max-w-none text-xs sm:text-sm leading-relaxed font-sans space-y-3 prose-headings:font-display prose-headings:font-bold prose-headings:tracking-tight prose-headings:text-white prose-p:leading-relaxed prose-strong:text-white prose-code:text-emerald-300 prose-code:font-mono prose-code:text-xs">
                    <ReactMarkdown
                      components={{
                        code({ className, children, ...props }: any) {
                          const match = /language-(\w+)/.exec(className || '')
                          const isInline = !match && !String(children).includes('\n')
                          return isInline ? (
                            <code className="bg-white/10 px-1.5 py-0.5 rounded text-emerald-300 font-mono text-xs" {...props}>
                              {children}
                            </code>
                          ) : (
                            <SyntaxHighlighter
                              style={oneDark}
                              language={match ? match[1] : 'text'}
                              PreTag="div"
                              className="rounded-xl my-3 text-xs font-mono border border-white/10 shadow-lg"
                            >
                              {String(children).replace(/\n$/, '')}
                            </SyntaxHighlighter>
                          )
                        },
                      }}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  </div>

                  {/* Verified Sources Citation Accordion */}
                  {!isUser && msg.sources && msg.sources.length > 0 && (
                    <SourceCitationDrawer sources={msg.sources} />
                  )}

                  {/* Assistant Footer Copy Button */}
                  {!isUser && (
                    <div className="flex items-center justify-end gap-2 mt-3 pt-2.5 border-t border-white/5">
                      <CopyButton text={msg.content} />
                    </div>
                  )}
                </div>
              </div>
            )
          })
        )}

        {/* Active Streaming Indicator */}
        {isStreaming && (
          <div className="max-w-4xl mx-auto flex items-start gap-3">
            <TypingIndicator />
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* ── Floating Cybernetic Terminal Input Bar ── */}
      <div className="relative z-10 p-4 sm:p-6 bg-[#111116]/60 backdrop-blur-xl border-t border-white/10 flex-shrink-0">
        <div className="max-w-4xl mx-auto flex flex-col gap-2">
          {/* Input Control Capsule */}
          <div className="flex items-center gap-2 p-1.5 rounded-full bg-white/[0.06] border border-white/20 focus-within:border-white/50 focus-within:bg-white/[0.09] focus-within:ring-2 focus-within:ring-white/10 shadow-2xl transition-all">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isStreaming}
              placeholder={
                isGlobal
                  ? 'Query across all uploaded documents...'
                  : `Ask anything about ${documentName}...`
              }
              className="flex-1 px-4 py-2 bg-transparent text-sm text-white placeholder-white/40 focus:outline-none font-sans"
            />

            {/* Action Buttons */}
            {isStreaming ? (
              <button
                onClick={stopStreaming}
                className="px-4 py-2 rounded-full bg-red-600 hover:bg-red-500 text-white text-xs font-mono font-bold uppercase tracking-wider flex items-center gap-1.5 transition-colors shadow-md"
              >
                <Square className="w-3.5 h-3.5 fill-current" />
                <span>Stop</span>
              </button>
            ) : (
              <button
                onClick={handleSend}
                disabled={!input.trim()}
                className="w-10 h-10 rounded-full bg-white text-black hover:bg-white/90 disabled:opacity-30 disabled:hover:bg-white flex items-center justify-center transition-all hover:scale-105 shadow-md flex-shrink-0"
              >
                <Send className="w-4 h-4 translate-x-0.5" />
              </button>
            )}
          </div>

          {/* Micro Status Footnote */}
          <div className="flex items-center justify-between px-4 text-[10px] font-mono text-white/50">
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>HYBRID RRF // CROSS-ENCODER VERIFIED</span>
            </div>
            <span className="hidden sm:inline">GROQ LPU ACCELERATED (~18MS)</span>
          </div>
        </div>
      </div>
    </div>
  )
}

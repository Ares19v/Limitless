/**
 * ChatWindow v2 — Real-time streaming chat with:
 *  - Agent Mode toggle (uses ReAct agent with tools)
 *  - Global Search toggle (search all documents)
 *  - Citation drawer with highlighted source excerpts
 *  - Persistent conversation history (loaded from backend)
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
  MessageSquare,
  RotateCcw,
  Bot,
  Globe,
  X,
  FileSearch,
} from 'lucide-react'
import { cn, truncate } from '@/lib/utils'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { useChat } from '@/hooks/useChat'
import { fetchAgentStream, fetchGlobalChatStream, clearHistory } from '@/lib/api'
import { useAppStore } from '@/store'
import { generateId } from '@/lib/utils'
import type { AgentStep, ChatMessage, SourceChunk } from '@/types'

// ── Typing dots ──────────────────────────────────────────────────────────────
function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 px-1 py-2">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="w-2 h-2 rounded-full bg-brand-400 animate-pulse-dot"
          style={{ animationDelay: `${i * 0.2}s` }}
        />
      ))}
    </div>
  )
}

// ── Copy button ───────────────────────────────────────────────────────────────
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
      className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-400 hover:text-slate-600 transition-all"
    >
      {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
    </button>
  )
}

// ── Agent step display ────────────────────────────────────────────────────────
function AgentStepBadge({ step }: { step: AgentStep }) {
  return (
    <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-800 rounded-lg px-3 py-1.5 border border-slate-200 dark:border-slate-700 animate-fade-in">
      <span>{step.emoji}</span>
      <span className="font-medium text-slate-600 dark:text-slate-300">{step.tool.replace('_', ' ')}</span>
      <span className="text-slate-400">→</span>
      <span className="truncate max-w-[200px]">{step.input}</span>
    </div>
  )
}

// ── Source citation with drawer ───────────────────────────────────────────────
function SourceList({ sources }: { sources: SourceChunk[] }) {
  const [open, setOpen] = useState(false)
  const [selected, setSelected] = useState<SourceChunk | null>(null)
  if (!sources.length) return null

  return (
    <div className="mt-3 border-t border-slate-100 dark:border-slate-700 pt-3">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 text-xs font-medium text-slate-500 dark:text-slate-400 hover:text-brand-500 transition-colors"
      >
        <BookOpen className="w-3.5 h-3.5" />
        {sources.length} source{sources.length > 1 ? 's' : ''}
        <ChevronDown className={cn('w-3 h-3 transition-transform', open && 'rotate-180')} />
      </button>

      {open && (
        <div className="mt-2 space-y-1.5 animate-fade-in">
          {sources.map((src, i) => (
            <button
              key={i}
              onClick={() => setSelected(selected?.content === src.content ? null : src)}
              className={cn(
                'w-full text-left rounded-lg border px-3 py-2 transition-all duration-200',
                selected?.content === src.content
                  ? 'border-brand-300 bg-brand-50 dark:bg-brand-950/20 dark:border-brand-700'
                  : 'border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 hover:border-brand-200',
              )}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-medium text-brand-500">Excerpt {i + 1}</span>
                {src.page && (
                  <span className="text-xs text-slate-400 bg-slate-100 dark:bg-slate-700 px-1.5 rounded">
                    Page {src.page}
                  </span>
                )}
                <span className="ml-auto text-xs text-slate-400">
                  {Math.round(src.score * 100)}% match
                </span>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                {truncate(src.content, 200)}
              </p>

              {/* Expanded excerpt drawer */}
              {selected?.content === src.content && (
                <div className="mt-2 pt-2 border-t border-brand-200 dark:border-brand-800">
                  <div className="flex items-center gap-1 text-xs text-brand-500 mb-1">
                    <FileSearch className="w-3 h-3" />
                    Full excerpt
                  </div>
                  <p className="text-xs text-slate-700 dark:text-slate-200 leading-relaxed whitespace-pre-line">
                    {src.content}
                  </p>
                </div>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

// ── Message bubble ──────────────────────────────────────────────────────────
function MessageBubble({ message }: { message: ChatMessage & { agentSteps?: AgentStep[] } }) {
  const isUser = message.role === 'user'

  return (
    <div className={cn('flex gap-3 animate-slide-up', isUser ? 'flex-row-reverse' : 'flex-row')}>
      {/* Avatar */}
      <div
        className={cn(
          'flex-shrink-0 w-8 h-8 rounded-xl flex items-center justify-center text-sm',
          isUser
            ? 'gradient-brand text-white'
            : 'bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400',
        )}
      >
        {isUser ? '👤' : <Sparkles className="w-4 h-4 text-brand-500" />}
      </div>

      {/* Bubble */}
      <div
        className={cn(
          'group relative max-w-[80%] rounded-2xl px-4 py-3',
          isUser
            ? 'gradient-brand text-white rounded-tr-sm'
            : 'bg-white dark:bg-gray-900 border border-slate-200 dark:border-slate-700 rounded-tl-sm',
        )}
      >
        {/* Agent steps display */}
        {!isUser && message.agentSteps && message.agentSteps.length > 0 && (
          <div className="mb-3 space-y-1.5">
            {message.agentSteps.map((step, i) => (
              <AgentStepBadge key={i} step={step} />
            ))}
            <div className="text-xs text-slate-400 pl-1">↳ Final answer:</div>
          </div>
        )}

        {message.content === '' && message.isStreaming ? (
          <TypingIndicator />
        ) : (
          <>
            <div className={cn('prose-chat', isUser ? 'text-white' : 'text-slate-800 dark:text-slate-200')}>
              <ReactMarkdown
                components={{
                  code({ node, className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || '')
                    const inline = !match
                    return inline ? (
                      <code className={cn('font-mono text-xs rounded px-1', isUser ? 'bg-white/20' : 'bg-slate-100 dark:bg-slate-800')} {...props}>
                        {children}
                      </code>
                    ) : (
                      <SyntaxHighlighter
                        style={oneDark}
                        language={match[1]}
                        PreTag="div"
                        className="rounded-xl text-xs my-2"
                      >
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                    )
                  },
                }}
              >
                {message.content}
              </ReactMarkdown>
              {message.isStreaming && (
                <span className="inline-block w-0.5 h-4 bg-brand-400 animate-pulse ml-0.5" />
              )}
            </div>

            {!isUser && !message.isStreaming && (
              <div className="flex justify-end mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <CopyButton text={message.content} />
              </div>
            )}

            {!isUser && message.sources && message.sources.length > 0 && (
              <SourceList sources={message.sources} />
            )}
          </>
        )}
      </div>
    </div>
  )
}

// ── Empty state ───────────────────────────────────────────────────────────────
function EmptyChat({ docName }: { docName: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-6 p-8 text-center">
      <div className="w-20 h-20 rounded-3xl gradient-brand flex items-center justify-center shadow-xl shadow-brand-500/20 animate-bounce-subtle">
        <MessageSquare className="w-10 h-10 text-white" />
      </div>
      <div>
        <h3 className="text-xl font-bold text-slate-800 dark:text-slate-200 mb-2">Ready to chat!</h3>
        <p className="text-sm text-slate-500 dark:text-slate-400 max-w-sm">
          Ask anything about <strong className="text-slate-700 dark:text-slate-300">{docName}</strong>.
          I'll find the relevant passages and answer accurately.
        </p>
      </div>
      <div className="grid grid-cols-1 gap-2 w-full max-w-sm">
        {['Summarize this document', 'What are the key points?', 'Find any dates or numbers mentioned'].map(
          (q) => (
            <button
              key={q}
              className="text-left px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 text-sm text-slate-600 dark:text-slate-400 hover:border-brand-300 hover:bg-brand-50 dark:hover:bg-brand-950/20 hover:text-brand-600 dark:hover:text-brand-400 transition-all duration-200"
            >
              {q}
            </button>
          ),
        )}
      </div>
    </div>
  )
}

// ── Main ChatWindow ───────────────────────────────────────────────────────────
interface ChatWindowProps {
  documentId: string
  documentName: string
}

export function ChatWindow({ documentId, documentName }: ChatWindowProps) {
  const { messages, isStreaming, sendMessage, stopStreaming, clearChat } = useChat(documentId)
  const { addMessage, updateLastAssistantMessage, setStreaming } = useAppStore()
  const [input, setInput] = useState('')
  const [agentMode, setAgentMode] = useState(false)
  const [globalMode, setGlobalMode] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || isStreaming) return
    const text = input.trim()
    setInput('')

    if (agentMode) {
      // Agent mode: uses ReAct agent with tools
      const userMsg = { id: generateId(), role: 'user' as const, content: text, timestamp: new Date().toISOString() }
      addMessage(documentId, userMsg)
      const assistantId = generateId()
      const agentSteps: AgentStep[] = []
      addMessage(documentId, { id: assistantId, role: 'assistant', content: '', timestamp: new Date().toISOString(), isStreaming: true })
      setStreaming(true)
      try {
        let accumulated = ''
        for await (const event of fetchAgentStream(documentId, text)) {
          if (event.type === 'step') {
            const step: AgentStep = JSON.parse(event.data)
            agentSteps.push(step)
            updateLastAssistantMessage(documentId, { agentSteps: [...agentSteps], isStreaming: true })
          } else if (event.type === 'token') {
            accumulated += event.data
            updateLastAssistantMessage(documentId, { content: accumulated, agentSteps: [...agentSteps], isStreaming: true })
          } else if (event.type === 'done') {
            updateLastAssistantMessage(documentId, { isStreaming: false })
            break
          }
        }
      } catch (err) {
        updateLastAssistantMessage(documentId, { content: `❌ Agent error. Please try again.`, isStreaming: false })
      } finally {
        setStreaming(false)
      }
      return
    }

    if (globalMode) {
      // Global mode: search across all documents
      const userMsg = { id: generateId(), role: 'user' as const, content: `🌐 ${text}`, timestamp: new Date().toISOString() }
      addMessage(documentId, userMsg)
      addMessage(documentId, { id: generateId(), role: 'assistant', content: '', timestamp: new Date().toISOString(), isStreaming: true })
      setStreaming(true)
      try {
        let accum = ''
        const sources: SourceChunk[] = []
        for await (const event of fetchGlobalChatStream(text)) {
          if (event.type === 'token') {
            accum += event.data
            updateLastAssistantMessage(documentId, { content: accum, isStreaming: true })
          } else if (event.type === 'sources') {
            try { sources.push(...JSON.parse(event.data)) } catch {}
            updateLastAssistantMessage(documentId, { sources })
          } else if (event.type === 'done') {
            updateLastAssistantMessage(documentId, { isStreaming: false })
            break
          }
        }
      } catch (err) {
        updateLastAssistantMessage(documentId, { content: `❌ Global search failed.`, isStreaming: false })
      } finally {
        setStreaming(false)
      }
      return
    }

    // Default: standard RAG chat
    sendMessage(text)
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
  }

  const handleClear = async () => {
    clearChat()
    try { await clearHistory(documentId) } catch {}
  }

  return (
    <div className="flex flex-col h-full">
      {/* Chat header */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-slate-200 dark:border-slate-800">
        <div>
          <h2 className="text-sm font-semibold text-slate-800 dark:text-slate-200 truncate max-w-xs">
            {documentName}
          </h2>
          <p className="text-xs text-slate-400 dark:text-slate-500">
            {messages.length > 0 ? `${messages.length} messages` : 'Start a conversation'}
          </p>
        </div>

        {/* Mode toggles */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => { setGlobalMode(false); setAgentMode(v => !v) }}
            title="Agent Mode — uses tools (web, calculator, document search)"
            className={cn(
              'flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all',
              agentMode
                ? 'bg-purple-100 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 border border-purple-300 dark:border-purple-700'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-500 hover:text-slate-700 border border-transparent',
            )}
          >
            <Bot className="w-3.5 h-3.5" />
            Agent
          </button>
          <button
            onClick={() => { setAgentMode(false); setGlobalMode(v => !v) }}
            title="Global Mode — search across all documents"
            className={cn(
              'flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all',
              globalMode
                ? 'bg-emerald-100 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-700'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-500 hover:text-slate-700 border border-transparent',
            )}
          >
            <Globe className="w-3.5 h-3.5" />
            All Docs
          </button>
          {messages.length > 0 && (
            <Button variant="ghost" size="sm" onClick={handleClear} className="text-slate-400 hover:text-red-500">
              <RotateCcw className="w-3.5 h-3.5" />
              Clear
            </Button>
          )}
        </div>
      </div>

      {/* Mode indicator banner */}
      {(agentMode || globalMode) && (
        <div className={cn(
          'flex items-center gap-2 px-6 py-2 text-xs font-medium border-b',
          agentMode
            ? 'bg-purple-50 dark:bg-purple-950/20 text-purple-700 dark:text-purple-300 border-purple-200 dark:border-purple-800'
            : 'bg-emerald-50 dark:bg-emerald-950/20 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800',
        )}>
          {agentMode ? <Bot className="w-3.5 h-3.5" /> : <Globe className="w-3.5 h-3.5" />}
          {agentMode
            ? '🤖 Agent Mode — I can search the web, run calculations, and read your document'
            : '🌐 Global Mode — searching across ALL your uploaded documents'}
          <button onClick={() => { setAgentMode(false); setGlobalMode(false) }} className="ml-auto">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          <EmptyChat docName={documentName} />
        ) : (
          messages.map((msg) => <MessageBubble key={msg.id} message={msg as any} />)
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div className="p-4 border-t border-slate-200 dark:border-slate-800">
        <div className="flex items-center gap-3">
          <Input
            id="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              agentMode
                ? 'Ask the agent (it can search the web and calculate)…'
                : globalMode
                ? 'Search across all your documents…'
                : 'Ask a question about this document…'
            }
            disabled={isStreaming}
            className="flex-1"
          />
          {isStreaming ? (
            <Button variant="danger" size="icon" onClick={stopStreaming} title="Stop generating">
              <Square className="w-4 h-4" />
            </Button>
          ) : (
            <Button id="send-button" variant="primary" size="icon" onClick={handleSend} disabled={!input.trim()} title="Send message">
              <Send className="w-4 h-4" />
            </Button>
          )}
        </div>
        <p className="text-xs text-center text-slate-400 dark:text-slate-500 mt-2">
          Press <kbd className="px-1 py-0.5 rounded bg-slate-100 dark:bg-slate-700 font-mono text-xs">Enter</kbd> to send
        </p>
      </div>
    </div>
  )
}

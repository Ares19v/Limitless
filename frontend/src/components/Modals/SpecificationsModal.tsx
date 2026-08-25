import { X, Cpu, Database, Search, Sparkles, ShieldCheck, Zap } from 'lucide-react'

interface SpecificationsModalProps {
  isOpen: boolean
  onClose: () => void
}

export function SpecificationsModal({ isOpen, onClose }: SpecificationsModalProps) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div 
        className="relative w-full max-w-2xl max-h-[85vh] overflow-y-auto bg-[#EAEAEA] dark:bg-[#18181C] text-[#121212] dark:text-[#EAEAEA] rounded-[28px] border-2 border-[#161616] dark:border-[#33333F] shadow-2xl p-6 md:p-8"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between pb-4 mb-6 border-b border-[#161616]/15 dark:border-white/10">
          <div>
            <div className="flex items-center gap-2 mb-1 text-xs font-mono tracking-widest text-[#666666] dark:text-[#888899]">
              <span>SPEC // 01.07</span>
              <span>•</span>
              <span className="text-emerald-600 dark:text-emerald-400">STATUS: PRODUCTION READY</span>
            </div>
            <h2 className="text-2xl md:text-3xl font-black tracking-tight font-display text-[#111111] dark:text-white">
              SYSTEM ARCHITECTURE & SPECS
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-full hover:bg-black/10 dark:hover:bg-white/10 text-[#111111] dark:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Specs Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div className="p-4 rounded-2xl bg-white/70 dark:bg-white/5 border border-[#161616]/10 dark:border-white/10">
            <div className="flex items-center gap-2 mb-2 font-mono text-xs text-[#555555] dark:text-[#9999AA]">
              <Cpu className="w-4 h-4 text-[#111111] dark:text-white" />
              <span>INFERENCE ENGINE</span>
            </div>
            <p className="font-bold text-sm text-[#111111] dark:text-white">Groq LPU Acceleration</p>
            <p className="text-xs text-[#666666] dark:text-[#888899] mt-1">
              Primary: <code className="px-1 py-0.5 rounded bg-black/5 dark:bg-white/10">openai/gpt-oss-120b</code>
              <br />
              Sub-second first-token latency, streaming via Server-Sent Events.
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-white/70 dark:bg-white/5 border border-[#161616]/10 dark:border-white/10">
            <div className="flex items-center gap-2 mb-2 font-mono text-xs text-[#555555] dark:text-[#9999AA]">
              <Database className="w-4 h-4 text-[#111111] dark:text-white" />
              <span>VECTOR PERSISTENCE</span>
            </div>
            <p className="font-bold text-sm text-[#111111] dark:text-white">Pinecone Serverless</p>
            <p className="text-xs text-[#666666] dark:text-[#888899] mt-1">
              384-dimensional cosine similarity indexing. Local dense embeddings via <code className="px-1 py-0.5 rounded bg-black/5 dark:bg-white/10">all-MiniLM-L6-v2</code>.
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-white/70 dark:bg-white/5 border border-[#161616]/10 dark:border-white/10">
            <div className="flex items-center gap-2 mb-2 font-mono text-xs text-[#555555] dark:text-[#9999AA]">
              <Search className="w-4 h-4 text-[#111111] dark:text-white" />
              <span>HYBRID RETRIEVAL</span>
            </div>
            <p className="font-bold text-sm text-[#111111] dark:text-white">BM25 + Dense RRF</p>
            <p className="text-xs text-[#666666] dark:text-[#888899] mt-1">
              Reciprocal Rank Fusion compiles top 15 candidate matches from keyword + vector space.
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-white/70 dark:bg-white/5 border border-[#161616]/10 dark:border-white/10">
            <div className="flex items-center gap-2 mb-2 font-mono text-xs text-[#555555] dark:text-[#9999AA]">
              <Sparkles className="w-4 h-4 text-[#111111] dark:text-white" />
              <span>CROSS-ENCODER RERANKING</span>
            </div>
            <p className="font-bold text-sm text-[#111111] dark:text-white">ms-marco-MiniLM-L-6-v2</p>
            <p className="text-xs text-[#666666] dark:text-[#888899] mt-1">
              Neural cross-attention scores full prompt against candidate chunks, distilling to top 5 verified excerpts.
            </p>
          </div>
        </div>

        {/* Technical Capabilities List */}
        <div className="p-4 rounded-2xl bg-[#DFDFDF] dark:bg-[#141418] border border-[#161616]/10 dark:border-white/10 mb-6">
          <h3 className="text-xs font-mono uppercase tracking-widest text-[#444444] dark:text-[#888899] mb-3">
            BENCHMARK CAPABILITIES
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
              <span>Zero-Hallucination Grounding</span>
            </div>
            <div className="flex items-center gap-2">
              <Zap className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />
              <span>ReAct Tool Routing & Web Search</span>
            </div>
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
              <span>SQLite Persistent Conversation State</span>
            </div>
            <div className="flex items-center gap-2">
              <Zap className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />
              <span>Auto 3-Bullet AI Executive Summaries</span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end">
          <button
            onClick={onClose}
            className="px-6 py-2.5 rounded-full bg-[#161616] dark:bg-white text-white dark:text-[#161616] text-xs font-bold uppercase tracking-wider hover:opacity-90 transition-opacity"
          >
            Close Blueprint
          </button>
        </div>
      </div>
    </div>
  )
}

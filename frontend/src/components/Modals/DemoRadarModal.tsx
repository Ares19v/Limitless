import { useState, useEffect } from 'react'
import { X, Play, CheckCircle2, Zap, Cpu, Database, Activity, RefreshCw } from 'lucide-react'

interface DemoRadarModalProps {
  isOpen: boolean
  onClose: () => void
}

export function DemoRadarModal({ isOpen, onClose }: DemoRadarModalProps) {
  const [step, setStep] = useState<number>(0)
  const [isRunning, setIsRunning] = useState(false)

  const steps = [
    { title: "Query Tokenization", desc: "all-MiniLM-L6-v2 generating 384-dim dense embeddings", latency: "4.2ms" },
    { title: "BM25 Sparse Inverted Index", desc: "Lexical keyword scoring across corpus token postings", latency: "1.8ms" },
    { title: "Pinecone Vector Query", desc: "Approximate Nearest Neighbor (ANN) cosine distance match", latency: "12.4ms" },
    { title: "Reciprocal Rank Fusion", desc: "Compiling Top 20 candidate chunks via RRF formula", latency: "0.6ms" },
    { title: "ms-marco Cross-Encoder", desc: "Deep neural cross-attention scoring prompt vs candidates", latency: "14.1ms" },
    { title: "Groq LPU Generation", desc: "Streaming answer at 450 tokens/sec with verified citations", latency: "18.3ms" },
  ]

  useEffect(() => {
    if (isOpen) {
      setIsRunning(true)
      setStep(0)
      const interval = setInterval(() => {
        setStep((prev) => {
          if (prev >= steps.length - 1) {
            clearInterval(interval)
            setIsRunning(false)
            return prev
          }
          return prev + 1
        })
      }, 700)
      return () => clearInterval(interval)
    }
  }, [isOpen])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div 
        className="relative w-full max-w-xl bg-[#E3E3E3] dark:bg-[#18181C] text-[#111111] dark:text-[#EAEAEA] rounded-[28px] border-2 border-[#161616] dark:border-[#33333F] shadow-2xl p-6 md:p-8"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between pb-4 mb-5 border-b border-[#161616]/15 dark:border-white/10">
          <div>
            <div className="flex items-center gap-2 mb-1 text-xs font-mono tracking-widest text-[#555555] dark:text-[#888899]">
              <span>LIVE PIPELINE RADAR</span>
              <span>•</span>
              <span className="text-emerald-600 dark:text-emerald-400 font-bold">SUB-SECOND LPU CYCLE</span>
            </div>
            <h2 className="text-2xl font-black tracking-tight font-display text-[#111111] dark:text-white uppercase">
              NEURAL RAG IN ACTION
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-full hover:bg-black/10 dark:hover:bg-white/10 text-[#111111] dark:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Radar Simulation Sequence */}
        <div className="space-y-2.5 mb-6">
          {steps.map((s, idx) => {
            const isCompleted = step > idx
            const isCurrent = step === idx
            return (
              <div
                key={idx}
                className={`p-3 rounded-xl border transition-all duration-300 flex items-center justify-between ${
                  isCurrent
                    ? 'bg-white dark:bg-[#22222A] border-[#161616] dark:border-white shadow-md scale-[1.01]'
                    : isCompleted
                    ? 'bg-white/60 dark:bg-white/5 border-[#161616]/10 dark:border-white/10 opacity-90'
                    : 'bg-transparent border-dashed border-[#161616]/15 dark:border-white/10 opacity-40'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-mono font-bold ${
                    isCompleted
                      ? 'bg-emerald-500 text-white'
                      : isCurrent
                      ? 'bg-[#111111] text-white dark:bg-white dark:text-black animate-pulse'
                      : 'bg-black/10 dark:bg-white/10 text-[#888888]'
                  }`}>
                    {isCompleted ? '✓' : idx + 1}
                  </div>
                  <div>
                    <p className="font-bold text-xs sm:text-sm text-[#111111] dark:text-white">
                      {s.title}
                    </p>
                    <p className="text-[11px] text-[#555555] dark:text-[#888899]">
                      {s.desc}
                    </p>
                  </div>
                </div>

                <div className="font-mono text-xs text-right font-bold text-[#111111] dark:text-white flex-shrink-0">
                  {s.latency}
                </div>
              </div>
            )
          })}
        </div>

        {/* Footer controls */}
        <div className="flex items-center justify-between pt-2 border-t border-[#161616]/10 dark:border-white/10">
          <div className="flex items-center gap-2 text-xs font-mono text-[#555555] dark:text-[#888899]">
            <Activity className="w-3.5 h-3.5 text-emerald-500" />
            <span>TOTAL LATENCY: <strong>51.4ms</strong></span>
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => {
                setStep(0)
                setIsRunning(true)
              }}
              className="px-4 py-2 rounded-full border border-[#161616]/20 dark:border-white/20 hover:bg-black/5 dark:hover:bg-white/5 text-xs font-mono font-bold uppercase tracking-wider flex items-center gap-1.5"
            >
              <RefreshCw className="w-3 h-3" />
              Replay
            </button>
            <button
              onClick={onClose}
              className="px-5 py-2 rounded-full bg-[#161616] text-white dark:bg-white dark:text-[#161616] text-xs font-mono font-bold uppercase tracking-wider hover:opacity-90"
            >
              Done
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

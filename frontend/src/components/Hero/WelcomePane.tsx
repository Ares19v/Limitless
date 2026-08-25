import { useState, MouseEvent } from 'react'
import { Play, UploadCloud, Database, Cpu, Search, Sparkles, Activity, ShieldCheck, Zap, Info } from 'lucide-react'
import { useAppStore } from '@/store'
import { DemoRadarModal } from '@/components/Modals/DemoRadarModal'

interface WelcomePaneProps {
  onOpenSpecs: () => void
  onOpenDrawer: () => void
}

export function WelcomePane({ onOpenSpecs, onOpenDrawer }: WelcomePaneProps) {
  const { documents, selectDocument, themeMode, isFullScreen, toggleFullScreen } = useAppStore()
  const [sliderPosition, setSliderPosition] = useState<number>(70)
  const [isRadarOpen, setIsRadarOpen] = useState(false)
  const [tilt, setTilt] = useState({ x: 0, y: 0 })

  // 3D Parallax mouse move handler
  const handleMouseMove = (e: MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect()
    const x = ((e.clientX - rect.left) / rect.width - 0.5) * 14
    const y = ((e.clientY - rect.top) / rect.height - 0.5) * -14
    setTilt({ x, y })
  }

  const handleMouseLeave = () => {
    setTilt({ x: 0, y: 0 })
  }

  // Dynamic retrieval weights
  const denseWeight = (sliderPosition / 100).toFixed(2)
  const sparseWeight = ((100 - sliderPosition) / 100).toFixed(2)

  const isSeamless = themeMode === 'seamless'

  return (
    <div
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className="relative w-full h-full min-h-[640px] flex flex-col justify-between p-6 sm:p-10 md:p-14 select-none overflow-hidden transition-all duration-500 text-white"
      style={
        isSeamless
          ? {
              backgroundImage: 'url(/avatar-full-bleed.jpg)',
              backgroundPosition: 'center 45%',
              backgroundSize: 'cover',
              backgroundRepeat: 'no-repeat',
            }
          : {
              background: 'radial-gradient(ellipse at 50% 36%, #5C5C68 0%, #30303A 38%, #18181F 75%, #0F0F14 100%)',
            }
      }
    >
      {/* Seamless Theme Ambient Subtle Vignette */}
      {isSeamless && (
        <div className="absolute inset-0 bg-gradient-to-b from-black/30 via-transparent to-black/40 pointer-events-none" />
      )}

      {/* ── Giant Ghost Watermark Typography (RAG on left, 09 on right) ── */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden flex items-end justify-between z-0">
        <span className="text-[130px] sm:text-[170px] md:text-[210px] lg:text-[270px] font-black tracking-tighter font-headline select-none leading-none -translate-x-4 sm:-translate-x-8 translate-y-2 sm:translate-y-4 text-white/[0.04]">
          RAG
        </span>

        <span className="text-[130px] sm:text-[170px] md:text-[210px] lg:text-[270px] font-black tracking-tighter font-headline select-none leading-none translate-x-4 sm:translate-x-8 translate-y-2 sm:translate-y-4 text-white/[0.04]">
          09
        </span>
      </div>

      {/* ── Top Level Grid ── */}
      <div className="relative z-10 grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
        {/* Left: 01/07 & Main Bold Editorial Headline */}
        <div className="md:col-span-7 flex flex-col items-start">
          <div className="flex items-center gap-3 mb-3 text-xs sm:text-sm font-sans font-bold">
            <span className="font-mono text-white">01/07</span>
            <span className="text-[10px] font-mono tracking-widest uppercase text-white/60">
              // NEURAL COGNITIVE RAG
            </span>
          </div>

          <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-[56px] font-black tracking-tight font-display leading-[1.03] uppercase max-w-lg text-white drop-shadow-[0_2px_12px_rgba(0,0,0,0.8)]">
            CHANGING<br />
            YOUR IDEA OF<br />
            WHAT AI RAG<br />
            CAN DO
          </h1>
        </div>

        {/* Right: Sub-Navigation 2-Column Menu */}
        <div className="hidden md:flex md:col-span-5 justify-end gap-12 text-xs font-sans text-white/90 drop-shadow">
          {/* Column 1 */}
          <div className="flex flex-col gap-1.5 items-start">
            <button
              onClick={onOpenSpecs}
              className="hover:underline underline-offset-4 font-medium hover:text-white"
            >
              Architecture
            </button>
            <button
              onClick={onOpenSpecs}
              className="underline underline-offset-4 font-bold text-white"
            >
              Specifications
            </button>
          </div>

          {/* Column 2 */}
          <div className="flex flex-col gap-1.5 items-start">
            <button
              onClick={onOpenSpecs}
              className="opacity-70 hover:opacity-100 transition-opacity hover:underline underline-offset-4"
            >
              Pinecone Index
            </button>
            <button
              onClick={onOpenSpecs}
              className="opacity-70 hover:opacity-100 transition-opacity hover:underline underline-offset-4"
            >
              Groq LPU
            </button>
            <button
              onClick={onOpenDrawer}
              className="opacity-70 hover:opacity-100 transition-opacity hover:underline underline-offset-4"
            >
              Corpus ({documents.length})
            </button>
            <button
              onClick={() => setIsRadarOpen(true)}
              className="opacity-70 hover:opacity-100 transition-opacity hover:underline underline-offset-4"
            >
              Benchmarks
            </button>
          </div>
        </div>
      </div>

      {/* ── Centerpiece Layer (Rendered in Obsidian mode with 3D Parallax tilt) ── */}
      {!isSeamless && (
        <div className="relative z-10 flex-1 flex items-center justify-center my-2 sm:my-3 pointer-events-none">
          <div
            style={{
              transform: `perspective(1000px) rotateX(${tilt.y}deg) rotateY(${tilt.x}deg)`,
              transition: 'transform 0.15s ease-out',
            }}
            className="relative w-[280px] sm:w-[350px] md:w-[420px] lg:w-[460px] max-w-full aspect-[682/1024] flex items-center justify-center"
          >
            <img
              src="/avatar-blend.png"
              alt="Centerpiece AI Avatar"
              className="w-full h-full object-contain filter drop-shadow-[0_15px_30px_rgba(0,0,0,0.5)] select-none"
            />
          </div>
        </div>
      )}

      {/* Center Spacer for Seamless Mode */}
      {isSeamless && <div className="flex-1 pointer-events-none" />}

      {/* ── Mid-Right Section: Interactive N —————— P Slider & Real-time Metrics ── */}
      <div className="relative z-20 md:absolute md:top-[44%] md:right-10 lg:right-14 md:max-w-xs flex flex-col items-start md:items-start text-left gap-3">
        {/* Linear N ──────── P Slider */}
        <div className="w-full max-w-[240px] sm:max-w-[280px] flex flex-col gap-1.5 p-3 rounded-2xl backdrop-blur-md border bg-black/40 border-white/15 shadow-xl">
          <div className="flex items-center justify-between text-[11px] font-mono text-white/70">
            <span>N (NEURAL)</span>
            <span>P (PRECISION)</span>
          </div>

          <div className="flex items-center justify-between gap-3">
            <span className="font-sans font-bold text-base">N</span>
            <div className="relative flex-1 h-[2px] flex items-center bg-white/30">
              <input
                type="range"
                min="10"
                max="90"
                value={sliderPosition}
                onChange={(e) => setSliderPosition(Number(e.target.value))}
                className="absolute inset-0 w-full opacity-0 cursor-pointer z-10"
                title="Adjust Neural vs Precision balance"
              />
              <div
                className="w-3.5 h-3.5 rounded-full border shadow-[0_0_10px_rgba(255,255,255,0.9)] bg-white border-black pointer-events-none transition-all"
                style={{ left: `calc(${sliderPosition}% - 7px)`, position: 'absolute' }}
              />
            </div>
            <span className="font-sans font-bold text-base">P</span>
          </div>

          {/* Real-time Dynamic Metrics Ticker */}
          <div className="flex items-center justify-between text-[10px] font-mono font-medium pt-1 border-t text-white/90 border-white/10">
            <span>DENSE: {denseWeight}</span>
            <span>•</span>
            <span>SPARSE: {sparseWeight}</span>
            <span>•</span>
            <span className="text-emerald-400 font-bold">~18MS</span>
          </div>
        </div>

        {/* Editorial Description */}
        <p className="text-xs sm:text-[13px] leading-snug font-sans max-w-[260px] sm:max-w-[290px] text-white/80 drop-shadow">
          Grasp, synthesize, extract, and index high-dimensional knowledge with 6-degrees of semantic retrieval and Groq LPU inference.
        </p>

        {/* Interactive Quick Documents Chip Bar */}
        <div className="flex flex-col gap-1.5 w-full max-w-[290px] pt-1">
          <span className="text-[10px] font-mono uppercase tracking-widest text-white/60">
            READY DOCUMENTS ({documents.length})
          </span>
          <div className="flex flex-wrap gap-1.5">
            {documents.length > 0 ? (
              documents.slice(0, 3).map((doc) => (
                <button
                  key={doc.id}
                  onClick={() => selectDocument(doc)}
                  className="px-2.5 py-1 rounded-lg text-xs font-mono border transition-all truncate max-w-[220px] bg-black/40 hover:bg-white hover:text-black text-white border-white/20 backdrop-blur-md shadow-sm"
                >
                  {doc.filename.replace('.pdf', '')}
                </button>
              ))
            ) : (
              <button
                onClick={onOpenDrawer}
                className="px-3 py-1.5 rounded-lg text-xs font-mono font-bold uppercase tracking-wider flex items-center gap-1.5 shadow-md bg-white text-black hover:bg-white/90"
              >
                <UploadCloud className="w-3.5 h-3.5" />
                Upload PDF
              </button>
            )}
          </div>
        </div>
      </div>

      {/* ── Bottom Section: Standalone Info Logo (Left) & Vertical 'Full Screen' Marker (Right) ── */}
      <div className="relative z-20 flex items-end justify-between pt-2">
        {/* Bottom Left Standalone Minimalist Info Logo */}
        <button
          onClick={() => setIsRadarOpen(true)}
          className="w-8 h-8 rounded-full flex items-center justify-center text-white/60 hover:text-white transition-colors cursor-pointer"
          title="System Architecture & Neural Radar Specs"
        >
          <Info className="w-5 h-5" />
        </button>

        {/* Bottom Right Full Screen Option (Exact same font, size, color, uppercase, and line as scroll) */}
        <button
          onClick={toggleFullScreen}
          className="hidden sm:flex items-center gap-2 text-xs font-sans text-white/60 hover:text-white transition-colors cursor-pointer group"
          title={isFullScreen ? "Exit Full Screen" : "Enter Full Screen"}
        >
          <span className="text-[11px] tracking-widest font-mono uppercase group-hover:underline underline-offset-4">
            {isFullScreen ? "EXIT FULL SCREEN" : "FULL SCREEN"}
          </span>
          <div className="w-5 h-[1.5px] bg-current transition-all group-hover:w-8" />
        </button>
      </div>

      {/* Live Neural Radar Simulation Modal */}
      <DemoRadarModal
        isOpen={isRadarOpen}
        onClose={() => setIsRadarOpen(false)}
      />
    </div>
  )
}

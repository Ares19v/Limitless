import * as React from 'react'
import { cn } from '@/lib/utils'

interface ProgressProps {
  value: number
  max?: number
  className?: string
  showLabel?: boolean
}

export function Progress({ value, max = 100, className, showLabel }: ProgressProps) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100))
  return (
    <div className={cn('relative h-2 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700', className)}>
      <div
        className="h-full rounded-full gradient-brand transition-all duration-300 ease-out"
        style={{ width: `${pct}%` }}
      />
      {showLabel && (
        <span className="absolute right-0 top-4 text-xs text-slate-500">{Math.round(pct)}%</span>
      )}
    </div>
  )
}

import * as React from 'react'
import { cn } from '@/lib/utils'

const Badge = React.forwardRef<
  HTMLSpanElement,
  React.HTMLAttributes<HTMLSpanElement> & { variant?: 'default' | 'secondary' | 'processing' | 'ready' | 'error' }
>(({ className, variant = 'default', ...props }, ref) => (
  <span
    ref={ref}
    className={cn(
      'inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium',
      variant === 'default' && 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
      variant === 'secondary' && 'bg-slate-200 text-slate-600 dark:bg-slate-700 dark:text-slate-400',
      variant === 'processing' && 'status-processing animate-pulse',
      variant === 'ready' && 'status-ready',
      variant === 'error' && 'status-error',
      className,
    )}
    {...props}
  />
))
Badge.displayName = 'Badge'

export { Badge }

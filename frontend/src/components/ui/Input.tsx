import * as React from 'react'
import { cn } from '@/lib/utils'

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        'w-full rounded-xl border border-slate-200 dark:border-slate-700',
        'bg-white dark:bg-gray-900',
        'px-4 py-2.5 text-sm text-slate-900 dark:text-slate-100',
        'placeholder:text-slate-400 dark:placeholder:text-slate-600',
        'transition-all duration-200',
        'focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent',
        'disabled:cursor-not-allowed disabled:opacity-50',
        className,
      )}
      {...props}
    />
  ),
)
Input.displayName = 'Input'

export { Input }

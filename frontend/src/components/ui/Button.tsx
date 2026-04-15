import * as React from 'react'
import { cn } from '@/lib/utils'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg' | 'icon'
  isLoading?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', isLoading, children, disabled, ...props }, ref) => {
    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(
          'inline-flex items-center justify-center gap-2 rounded-xl font-medium transition-all duration-200',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2',
          'disabled:pointer-events-none disabled:opacity-50',
          // Variants
          variant === 'primary' && [
            'gradient-brand text-white shadow-md shadow-brand-500/25',
            'hover:shadow-lg hover:shadow-brand-500/30 hover:-translate-y-0.5 active:translate-y-0',
          ],
          variant === 'secondary' && [
            'bg-white dark:bg-gray-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300',
            'hover:bg-slate-50 dark:hover:bg-gray-700 hover:border-slate-300 dark:hover:border-slate-600',
          ],
          variant === 'ghost' && [
            'text-slate-600 dark:text-slate-400',
            'hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-100',
          ],
          variant === 'danger' && [
            'bg-red-500 text-white',
            'hover:bg-red-600 active:bg-red-700',
          ],
          // Sizes
          size === 'sm' && 'h-8 px-3 text-xs rounded-lg',
          size === 'md' && 'h-10 px-4 text-sm',
          size === 'lg' && 'h-12 px-6 text-base',
          size === 'icon' && 'h-9 w-9 p-0 rounded-lg',
          className,
        )}
        {...props}
      >
        {isLoading && (
          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        )}
        {children}
      </button>
    )
  },
)
Button.displayName = 'Button'

export { Button }

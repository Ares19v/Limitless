/**
 * Frontend component tests using Vitest + React Testing Library.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

// ── Mock modules ──────────────────────────────────────────────────────────────
vi.mock('@/lib/api', () => ({
  fetchDocuments: vi.fn().mockResolvedValue({ documents: [], total: 0 }),
  fetchDocument: vi.fn(),
  deleteDocument: vi.fn(),
  uploadPDF: vi.fn(),
  checkHealth: vi.fn().mockResolvedValue({ status: 'ok', version: '1.0.0' }),
  fetchChatStream: vi.fn(),
}))

// ── FileUpload tests ──────────────────────────────────────────────────────────
describe('FileUpload component', () => {
  it('renders the drop zone with correct text', async () => {
    const { FileUpload } = await import('@/components/FileUpload/FileUpload')
    render(<FileUpload />)
    expect(screen.getByText(/drag & drop pdfs here/i)).toBeInTheDocument()
    expect(screen.getByText(/browse to upload/i)).toBeInTheDocument()
  })

  it('shows file size limit info', async () => {
    const { FileUpload } = await import('@/components/FileUpload/FileUpload')
    render(<FileUpload />)
    expect(screen.getByText(/50MB/i)).toBeInTheDocument()
  })
})

// ── Badge tests ────────────────────────────────────────────────────────────────
describe('Badge component', () => {
  it('renders children', async () => {
    const { Badge } = await import('@/components/ui/Badge')
    render(<Badge>Ready</Badge>)
    expect(screen.getByText('Ready')).toBeInTheDocument()
  })

  it('applies correct status class', async () => {
    const { Badge } = await import('@/components/ui/Badge')
    const { container } = render(<Badge variant="ready">Ready</Badge>)
    expect(container.firstChild).toHaveClass('status-ready')
  })
})

// ── Button tests ──────────────────────────────────────────────────────────────
describe('Button component', () => {
  it('renders label correctly', async () => {
    const { Button } = await import('@/components/ui/Button')
    render(<Button>Click me</Button>)
    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument()
  })

  it('is disabled when isLoading is true', async () => {
    const { Button } = await import('@/components/ui/Button')
    render(<Button isLoading>Submit</Button>)
    expect(screen.getByRole('button')).toBeDisabled()
  })

  it('calls onClick handler', async () => {
    const { Button } = await import('@/components/ui/Button')
    const handler = vi.fn()
    render(<Button onClick={handler}>Click</Button>)
    await userEvent.click(screen.getByRole('button'))
    expect(handler).toHaveBeenCalledOnce()
  })
})

// ── Utility function tests ─────────────────────────────────────────────────────
describe('lib/utils', () => {
  it('formatBytes formats correctly', async () => {
    const { formatBytes } = await import('@/lib/utils')
    expect(formatBytes(0)).toBe('0 B')
    expect(formatBytes(1024)).toBe('1 KB')
    expect(formatBytes(1024 * 1024)).toBe('1 MB')
    expect(formatBytes(1536)).toBe('1.5 KB')
  })

  it('truncate shortens strings', async () => {
    const { truncate } = await import('@/lib/utils')
    expect(truncate('hello world', 5)).toBe('hello…')
    expect(truncate('hi', 10)).toBe('hi')
  })

  it('cn merges classes correctly', async () => {
    const { cn } = await import('@/lib/utils')
    expect(cn('px-4', 'py-2')).toBe('px-4 py-2')
    expect(cn('text-red-500', 'text-blue-500')).toBe('text-blue-500')
  })
})

/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ['class'],
  content: [
    './index.html',
    './src/**/*.{ts,tsx,js,jsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'Inter', 'system-ui', '-apple-system', 'sans-serif'],
        display: ['Syne', 'Space Grotesk', 'Plus Jakarta Sans', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      colors: {
        canvas: {
          DEFAULT: '#ECECEC',
          dark: '#111111',
          light: '#F4F4F4',
        },
        bezel: {
          DEFAULT: '#161616',
          border: '#242424',
          subtle: '#333333',
        },
        brand: {
          50:  '#f0f4ff',
          100: '#dde6ff',
          200: '#c1d0ff',
          300: '#97b2ff',
          400: '#6488ff',
          500: '#111111',
          600: '#1a1a1a',
          700: '#000000',
          800: '#111111',
          900: '#0a0a0a',
          950: '#050505',
        },
        surface: {
          DEFAULT: 'hsl(var(--surface))',
          hover:   'hsl(var(--surface-hover))',
          border:  'hsl(var(--surface-border))',
        },
      },
      animation: {
        'fade-in':       'fadeIn 0.3s ease-out',
        'slide-up':      'slideUp 0.4s cubic-bezier(0.16,1,0.3,1)',
        'slide-in-left': 'slideInLeft 0.3s ease-out',
        'pulse-dot':     'pulseDot 1.4s ease-in-out infinite',
        'shimmer':       'shimmer 2s linear infinite',
        'bounce-subtle': 'bounceSlight 1s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%':   { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%':   { opacity: '0', transform: 'translateY(16px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideInLeft: {
          '0%':   { opacity: '0', transform: 'translateX(-16px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        pulseDot: {
          '0%, 80%, 100%': { transform: 'scale(0)', opacity: '0.3' },
          '40%':           { transform: 'scale(1)', opacity: '1' },
        },
        shimmer: {
          '0%':   { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        bounceSlight: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%':      { transform: 'translateY(-4px)' },
        },
      },
      backgroundImage: {
        'shimmer-gradient': 'linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.08) 50%, transparent 100%)',
        'grid-pattern':     "url(\"data:image/svg+xml,%3Csvg width='40' height='40' viewBox='0 0 40 40' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='%236488ff' fill-opacity='0.03' fill-rule='evenodd'%3E%3Cpath d='M0 40L40 0H20L0 20M40 40V20L20 40'/%3E%3C/g%3E%3C/svg%3E\")",
      },
    },
  },
  plugins: [],
}

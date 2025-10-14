/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        bronze: {
          50: '#fdf8f4',
          100: '#f8ede4',
          200: '#e9d8c6',
          300: '#d7bfa4',
          400: '#b99479',
          500: '#8b5e3c', // primary
          600: '#744a2d',
          700: '#603b1f', // dark variant
          800: '#4a2f15',
          900: '#3a230e',
        },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'Segoe UI', 'Roboto', 'Helvetica', 'Arial'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        card: '0 8px 24px rgba(18,24,40,.06)',
        focus: '0 0 0 3px rgba(197,165,114,.35)',
      },
      borderRadius: { xl2: '1.25rem' },
      transitionTimingFunction: { smooth: 'cubic-bezier(.2,.8,.2,1)' },
      animation: {
        'pulse-slow': 'pulse 3s ease-in-out infinite',
      },
    },
  },
  plugins: [require('@tailwindcss/forms'), require('@tailwindcss/typography')],
}

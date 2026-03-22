/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        navy: {
          50:  '#eef1f8',
          100: '#dde4f0',
          200: '#b8c4de',
          300: '#8a9cc4',
          400: '#5b73a8',
          500: '#2a3a66',
          600: '#1e2d52',
          700: '#152040',
          800: '#0f1729',
          900: '#0a0f1c',
        },
        gold: {
          50:  '#fdf8ef',
          100: '#f8edda',
          200: '#f0d9b0',
          300: '#e8c98e',
          400: '#d4ad6e',
          500: '#c8a96e',
          600: '#a8894e',
          700: '#876d3e',
          800: '#66522e',
          900: '#45371e',
        },
        accent: {
          indigo: '#4f56c2',
          violet: '#7c5cbf',
          cyan:   '#0899b5',
          amber:  '#d48f0b',
          red:    '#d44040',
          green:  '#0ea572',
          pink:   '#c94088',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Playfair Display', 'Georgia', 'serif'],
      },
    },
  },
  plugins: [],
}

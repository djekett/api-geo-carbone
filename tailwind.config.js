/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './frontend/templates/**/*.html',
    './frontend/static/js/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        forest: { 50:'#f0fdf4',100:'#dcfce7',200:'#bbf7d0',300:'#86efac',400:'#4ade80',500:'#22c55e',600:'#16a34a',700:'#15803d',800:'#166534',900:'#14532d',950:'#052e16' },
        earth:  { 50:'#fdf8f0',100:'#f5ead6',200:'#e8d5b0',300:'#d4b882',400:'#c09b5a',500:'#a67c3d',600:'#8b6332',700:'#6d4d28',800:'#503a20',900:'#3a2a18' },
      },
      fontFamily: {
        display: ['DM Serif Display','Georgia','serif'],
        body:    ['DM Sans','system-ui','sans-serif'],
      },
    },
  },
  plugins: [],
}

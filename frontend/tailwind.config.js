/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        ocean: {
          950: '#030712',
          900: '#071328',
          800: '#0c2340',
          700: '#143864',
          600: '#1e528e',
          500: '#2b73be',
          400: '#4898e6',
          300: '#7cb5f2',
          200: '#b4d7fa',
          100: '#e1effe',
          50: '#f0f7ff',
        },
        sonar: {
          highlight: '#facc15',
          shadow: '#090d16',
          alert: '#ef4444',
          review: '#f97316',
          natural: '#10b981',
          cyan: '#06b6d4',
        }
      },
    },
  },
  plugins: [],
}

/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: {
          bg: '#f5f5f5',
          card: '#ffffff',
          muted: '#888888',
          accent: '#2563eb',
        },
      },
    },
  },
  plugins: [],
}

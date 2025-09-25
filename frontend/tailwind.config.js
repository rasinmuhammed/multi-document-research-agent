/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      backdropBlur: {
        'xl': '20px',
      },
      animation: {
        'bounce-slow': 'bounce 1.4s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
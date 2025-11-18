/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: 'rgb(0, 160, 235)',
        'primary-dark': 'rgb(0, 144, 211)',
      },
    },
  },
  plugins: [],
}

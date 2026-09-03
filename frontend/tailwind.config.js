/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        base: {
          950: "#08090d",
          900: "#0d0f16",
          850: "#12141d",
          800: "#171a25",
          750: "#1c2030",
          700: "#242939",
          600: "#333a4f",
          500: "#4a5270",
        },
        ink: {
          100: "#eef0f6",
          200: "#c9cede",
          300: "#a2a9c2",
          400: "#7c86a3",
          500: "#5c6690",
        },
        accent: {
          400: "#7c9fff",
          500: "#5b7fff",
          600: "#3f5fe0",
        },
        verified: {
          400: "#4ade80",
          500: "#22c55e",
          950: "#0a1f14",
        },
        partial: {
          400: "#fbbf24",
          500: "#f59e0b",
          950: "#241a05",
        },
        declined: {
          400: "#f87171",
          500: "#ef4444",
          950: "#260a0a",
        },
        contradicted: {
          400: "#f472b6",
          500: "#ec4899",
          950: "#240a1a",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      boxShadow: {
        panel: "0 1px 0 0 rgba(255,255,255,0.04) inset, 0 8px 24px -12px rgba(0,0,0,0.5)",
      },
    },
  },
  plugins: [],
};

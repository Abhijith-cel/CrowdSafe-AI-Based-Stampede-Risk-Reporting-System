/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0F172A",
        surface: "#1E293B",
        surface2: "#243449",
        line: "#334155",
        ink: "#F8FAFC",
        muted: "#94A3B8",
        critical: "#EF4444",
        high: "#F97316",
        moderate: "#FBBF24",
        low: "#22C55E",
        accent: "#3B82F6",
      },
      keyframes: {
        pulseRing: {
          "0%": { boxShadow: "0 0 0 0 rgba(239,68,68,.65)" },
          "100%": { boxShadow: "0 0 0 18px rgba(239,68,68,0)" },
        },
        liveDot: {
          "0%,100%": { opacity: 1 },
          "50%": { opacity: 0.35 },
        },
      },
      animation: {
        "pulse-ring": "pulseRing 1.6s infinite",
        "live-dot": "liveDot 1.6s infinite",
      },
    },
  },
  plugins: [],
};

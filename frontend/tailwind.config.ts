import type { Config } from "tailwindcss"

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        midnight: {
          50: "#f0f1f7",
          100: "#d0d3e6",
          200: "#a1a7cd",
          300: "#727bb4",
          400: "#434f9b",
          500: "#2a356b",
          600: "#222b56",
          700: "#1a2041",
          800: "#11162c",
          900: "#090b17",
          950: "#05060c",
        },
        aurora: {
          50: "#e6faf5",
          100: "#b3f0e0",
          200: "#80e6cb",
          300: "#4ddbb6",
          400: "#26d1a1",
          500: "#00c48c",
          600: "#00a876",
          700: "#008c60",
          800: "#00704a",
          900: "#005434",
        },
        cyber: {
          50: "#e6eeff",
          100: "#b3cbff",
          200: "#80a8ff",
          300: "#4d85ff",
          400: "#2662ff",
          500: "#0040ff",
          600: "#0036d4",
          700: "#002ba8",
          800: "#00217c",
          900: "#001650",
        },
        ember: {
          50: "#fff4e6",
          100: "#ffdcb3",
          200: "#ffc480",
          300: "#ffac4d",
          400: "#ff9426",
          500: "#ff7c00",
          600: "#d46800",
          700: "#a85400",
          800: "#7c4000",
          900: "#502c00",
        },
        surface: {
          dark: "#0a0e1a",
          card: "#111827",
          elevated: "#1a2035",
          border: "#1e293b",
          hover: "#243044",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      boxShadow: {
        glass: "0 8px 32px 0 rgba(0, 0, 0, 0.37)",
        glow: "0 0 20px rgba(0, 196, 140, 0.15)",
        "glow-blue": "0 0 20px rgba(0, 64, 255, 0.15)",
        "glow-amber": "0 0 20px rgba(255, 124, 0, 0.15)",
        inner: "inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)",
      },
      backdropBlur: {
        xs: "2px",
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "float": "float 3s ease-in-out infinite",
        "slide-up": "slideUp 0.5s ease-out",
        "slide-down": "slideDown 0.3s ease-out",
        "fade-in": "fadeIn 0.5s ease-out",
        "scale-in": "scaleIn 0.2s ease-out",
        "shimmer": "shimmer 2s infinite",
        "border-glow": "borderGlow 2s ease-in-out infinite alternate",
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-10px)" },
        },
        slideUp: {
          "0%": { transform: "translateY(20px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        slideDown: {
          "0%": { transform: "translateY(-10px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        scaleIn: {
          "0%": { transform: "scale(0.95)", opacity: "0" },
          "100%": { transform: "scale(1)", opacity: "1" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        borderGlow: {
          "0%": { borderColor: "rgba(0, 196, 140, 0.3)" },
          "100%": { borderColor: "rgba(0, 196, 140, 0.7)" },
        },
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "gradient-conic": "conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))",
      },
    },
  },
  plugins: [],
}
export default config

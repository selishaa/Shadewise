import type { Config } from "tailwindcss";

export default {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ivory: "#F7F1E8",
        cream: "#FBF7F1",
        parchment: "#EFE6DA",
        espresso: "#2C1810",
        "espresso-soft": "#4A3228",
        nude: "#C4A484",
        "nude-soft": "#D9C4AE",
        rose: "#C9A09A",
        "rose-deep": "#A87872",
        burgundy: "#6B2D3C",
        mist: "#F3EBE3",
      },
      fontFamily: {
        display: ["var(--font-display)", "Georgia", "serif"],
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
      },
      backgroundImage: {
        "ivory-wash":
          "radial-gradient(ellipse 120% 80% at 10% -10%, #F3E4D8 0%, transparent 55%), radial-gradient(ellipse 90% 70% at 100% 0%, #EBD9D2 0%, transparent 50%), linear-gradient(180deg, #FBF7F1 0%, #F7F1E8 45%, #F3EBE3 100%)",
        "hero-glow":
          "radial-gradient(ellipse 70% 50% at 70% 40%, rgba(201, 160, 154, 0.28) 0%, transparent 65%)",
      },
      boxShadow: {
        soft: "0 18px 40px -24px rgba(44, 24, 16, 0.35)",
      },
    },
  },
  plugins: [],
} satisfies Config;

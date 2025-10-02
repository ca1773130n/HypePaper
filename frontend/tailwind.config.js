/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // Mobile-first responsive breakpoints (per spec: 375px, 768px, 1024px)
      screens: {
        'sm': '375px',   // Mobile
        'md': '768px',   // Tablet
        'lg': '1024px',  // Desktop
        'xl': '1280px',  // Large desktop
      },
      // Color palette for hype scores
      colors: {
        hype: {
          low: '#6B7280',      // Gray for low hype (0-3)
          medium: '#F59E0B',   // Orange for medium hype (4-6)
          high: '#EF4444',     // Red for high hype (7-10)
        },
      },
      // Animation for loading states
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'shimmer': 'shimmer 2s linear infinite',
      },
      keyframes: {
        shimmer: {
          '0%': { backgroundPosition: '-1000px 0' },
          '100%': { backgroundPosition: '1000px 0' },
        },
      },
    },
  },
  plugins: [],
}

// Portfolio: theme moved here from the inline `tailwind.config` in portfolio_base.html
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./templates/portfolio_*.html"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        "primary": "#135bec",
        "primary-hover": "#1048c0",
        "background-light": "#f6f6f8",
        "background-dark": "#101622",
        "surface-dark": "#1c1f27",
        "surface-secondary": "#282e39",
        "surface-secondary-hover": "#343b49",
        "border-dark": "#3b4354",
        "text-secondary": "#b0b8ca",
      },
      fontFamily: {
        "sans": ["Space Grotesk", "sans-serif"],
      },
      borderRadius: { "DEFAULT": "0.25rem", "lg": "0.5rem", "xl": "0.75rem", "full": "9999px" },
    },
  },
  plugins: [require("@tailwindcss/forms"), require("@tailwindcss/container-queries")],
};

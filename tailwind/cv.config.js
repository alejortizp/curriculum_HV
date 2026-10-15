// CV + cover letter: default Tailwind theme (was the Play CDN with no config)
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/cv.html",
    "./templates/cover_letter.html",
    "./static/ai-suite.js",
  ],
  theme: { extend: {} },
  plugins: [],
};

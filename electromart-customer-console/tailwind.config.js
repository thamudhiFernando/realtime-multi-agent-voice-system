/** @type {import('tailwindcss').Config} */
export default {
    content: [
        './src/app/**/*.{js,ts,jsx,tsx}',   // Next.js App Router files
        './src/components/**/*.{js,ts,jsx,tsx}' // Optional: your components folder
    ],
    theme: {
        extend: {},
    },
    plugins: [],
};
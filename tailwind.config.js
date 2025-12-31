/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./aos/api/templates/**/*.html",
        "./aos/api/static/**/*.js",
    ],
    theme: {
        extend: {
            colors: {
                // Map Tailwind's slate to AOS neutral tokens
                slate: {
                    200: 'var(--aos-neutral-200)',
                    300: 'var(--aos-neutral-300)',
                    400: 'var(--aos-neutral-400)',
                    500: 'var(--aos-neutral-500)',
                    800: 'var(--aos-neutral-800)',
                    900: 'var(--aos-neutral-900)',
                },
                // Map semantic colors to AOS tokens
                green: {
                    400: 'var(--aos-success-hover)',
                    500: 'var(--aos-success-base)',
                },
                blue: {
                    500: 'var(--aos-info-base)',
                },
                purple: {
                    500: 'var(--aos-accent-base)',
                },
                amber: {
                    400: 'var(--aos-warning-hover)',
                    500: 'var(--aos-warning-base)',
                },
                red: {
                    400: 'var(--aos-error-hover)',
                    500: 'var(--aos-error-base)',
                },
            },
        },
    },
    plugins: [],
}

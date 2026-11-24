import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
    plugins: [react()],
    test: {
        environment: 'jsdom',
        setupFiles: ['resources/js/tests/setup.ts'],
        include: ['resources/js/**/*.test.tsx'],
        clearMocks: true,
        restoreMocks: true,
    },
});

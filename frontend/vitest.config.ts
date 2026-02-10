import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
    plugins: [react()],
    test: {
        environment: 'jsdom',
        globals: true,
        setupFiles: ['./vitest.setup.ts'],
        coverage: {
            provider: 'v8',
            reporter: ['text', 'json', 'html', 'lcov'],
            exclude: [
                'node_modules/',
                '.next/',
                'coverage/',
                '**/*.d.ts',
                '**/*.config.*',
                '**/mockData',
                'scripts/'
            ],
            thresholds: {
                lines: 90,
                functions: 90,
                branches: 90,
                statements: 90
            }
        },
        include: ['**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'],
        exclude: ['node_modules', '.next', 'dist', 'coverage']
    },
    resolve: {
        alias: {
            '@': path.resolve(__dirname, './src')
        }
    }
});

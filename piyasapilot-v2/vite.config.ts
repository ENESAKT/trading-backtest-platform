import { defineConfig } from 'vite';

export default defineConfig({
  build: {
    target: 'es2022',
    minify: 'esbuild',
    rollupOptions: {
      output: {
        manualChunks: {
          'lightweight-charts': ['lightweight-charts'],
          'chart.js': ['chart.js'],
        },
      },
    },
  },
  server: {
    port: 5173,
    open: true,
  },
});

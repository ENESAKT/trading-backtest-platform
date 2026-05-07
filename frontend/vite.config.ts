import { defineConfig } from 'vite';

const apiTarget = process.env.VITE_API_TARGET ?? 'http://127.0.0.1:8000';
const wsTarget = apiTarget.replace(/^http/, 'ws');

export default defineConfig({
  build: {
    target: 'es2022',
    minify: 'esbuild',
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules/lightweight-charts')) return 'lightweight-charts';
          if (id.includes('node_modules/chart.js')) return 'chart.js';
          return undefined;
        },
      },
    },
  },
  server: {
    port: 5173,
    open: true,
    proxy: {
      // v2 API: tüm tarihsel/poll çağrıları lokal Python backend'e (live_server.py)
      '/api/v2': {
        target: apiTarget,
        changeOrigin: true,
      },
      '/api/backtest': {
        target: apiTarget,
        changeOrigin: true,
      },
      '/api/mali-analiz': {
        target: apiTarget,
        changeOrigin: true,
      },
      '/api/backtest': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      // /ws/quotes: backend'in worker'larından fan-out edilen canlı bar feed.
      '/ws': {
        target: wsTarget,
        ws: true,
        changeOrigin: true,
      },
    },
  },
});

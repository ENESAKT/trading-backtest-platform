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
      // Tüm /api/* isteklerini backend'e yönlendir (tek kural — duplicate yok)
      '/api': {
        target: apiTarget,
        changeOrigin: true,
      },
      // WebSocket: canlı fiyat + sinyal feed
      '/ws': {
        target: wsTarget,
        ws: true,
        changeOrigin: true,
      },
      // Prometheus metrics
      '/metrics': {
        target: apiTarget,
        changeOrigin: true,
      },
    },
  },
});

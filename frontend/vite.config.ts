import { defineConfig } from 'vite';

const apiTarget = process.env.VITE_API_TARGET ?? 'http://127.0.0.1:8000';
const wsTarget  = apiTarget.replace(/^http/, 'ws');

export default defineConfig({
  build: {
    target: 'es2022',
    minify: 'esbuild',
    emptyOutDir: true,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules/lightweight-charts')) return 'lightweight-charts';
          if (id.includes('node_modules/chart.js'))          return 'chart.js';
        },
      },
    },
  },
  server: {
    port: 5173,
    open: true,
    proxy: {
      '/api': { target: apiTarget, changeOrigin: true },
      '/ws':  { target: wsTarget,  ws: true, changeOrigin: true },
      '/metrics': { target: apiTarget, changeOrigin: true },
    },
  },
});

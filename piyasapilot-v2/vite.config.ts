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
    proxy: {
      // v2 API: tüm tarihsel/poll çağrıları lokal Python backend'e (live_server.py)
      '/api/v2': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
});

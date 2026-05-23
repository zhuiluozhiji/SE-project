import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

const devProxyTarget = process.env.VITE_DEV_PROXY_TARGET || 'http://localhost:8000'
const usePolling = process.env.CHOKIDAR_USEPOLLING === 'true'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    watch: usePolling
      ? {
          usePolling: true,
          interval: 300
        }
      : undefined,
    proxy: {
      '/api': {
        target: devProxyTarget,
        changeOrigin: true
      }
    }
  }
})

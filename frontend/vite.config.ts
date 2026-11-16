import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// /api 代理到本地 FastAPI，前端只管同源调用
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
})

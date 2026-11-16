import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// /api 代理到本地 FastAPI，前端只管同源调用。
// host: true 同时监听 IPv4(0.0.0.0) —— 127.0.0.1:5173 与 localhost:5173 都能打开。
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
})

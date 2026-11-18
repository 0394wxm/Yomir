/// <reference types="vite/client" />

// D6: 前端在桌面壳里与后端同源（后端托管 dist），API 前缀留空即可；
// 若要指向别处，构建时设 VITE_API_BASE。Rust 侧也能通过
// window.__KANBUN_API_BASE__ 注入（见 App.tsx 的 apiBase()）。
interface ImportMetaEnv {
  readonly VITE_API_BASE?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

/// <reference types="vite/client" />

// D6: 前端在桌面壳里与后端同源（后端托管 dist），API 前缀留空即可；
// 若要指向别处，构建时设 VITE_API_BASE。
// D12: 删除了 window.__KANBUN_API_BASE__ 的说明——该注入从未实现（Rust 侧无代码）。
interface ImportMetaEnv {
  readonly VITE_API_BASE?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

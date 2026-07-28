/// <reference types="vite/client" />

// 复用仓库的 framework-agnostic API 客户端（apps/shared/api.js）。
declare module '@shared/api' {
  export function createApi(cfg: any): any
  export const fetchTransport: (method: string, url: string, opt: any) => Promise<{ status: number; json: any }>
  export const uniTransport: any
}

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<Record<string, unknown>, Record<string, unknown>, any>
  export default component
}

interface ImportMetaEnv {
  readonly VITE_API_BASE: string
}
interface ImportMeta {
  readonly env: ImportMetaEnv
}

import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// PC 宽屏管理后台 —— 独立纯 Vue3 SPA（不走 uni-app 多端外壳）。
// 复用仓库的 design-system/tokens.css（@ds）与三端共享 API 客户端 apps/shared/api.js（@shared）。
export default defineConfig({
  base: './',
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      '@shared': fileURLToPath(new URL('../shared', import.meta.url)),
      '@ds': fileURLToPath(new URL('../../design-system', import.meta.url)),
    },
  },
  server: { host: '127.0.0.1', port: 5174 },
})

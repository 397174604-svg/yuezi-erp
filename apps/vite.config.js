import { defineConfig } from 'vite'
import uniPlugin from '@dcloudio/vite-plugin-uni'

// CJS 插件在 ESM(type:module) 下默认导出会被包一层 .default，取真函数
const uni = typeof uniPlugin === 'function' ? uniPlugin : uniPlugin.default

// 三端共用：UNI_INPUT_DIR 指向 staff/mom 之一（产康已并入 staff、beauty 移出）（见 package.json 脚本）
export default defineConfig({
  plugins: [uni()],
})

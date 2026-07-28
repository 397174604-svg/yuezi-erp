import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

import '@ds/tokens.css'            // 设计令牌唯一来源（高奢金白）
import 'element-plus/dist/index.css'
import '@/styles/theme.scss'       // 把金白 token 映射到 Element Plus CSS 变量（须在 EP 默认样式之后）

import App from '@/App.vue'
import router from '@/router'
import { useAuthStore } from '@/stores/auth'

const app = createApp(App)
app.use(createPinia())

// 全量注册 Element Plus 图标，菜单/按钮可用 <component :is="'DataLine'"/> 或 <DataLine/>
for (const [name, comp] of Object.entries(ElementPlusIconsVue)) {
  app.component(name, comp as any)
}

useAuthStore().restore() // 刷新页面后恢复登录态（在挂载路由前，保证首个路由守卫能读到）

app.use(router)
app.use(ElementPlus, { locale: zhCn })
app.mount('#app')

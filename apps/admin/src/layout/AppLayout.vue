<template>
  <el-container class="layout">
    <!-- 侧边栏（暗夜金白） -->
    <el-aside :width="app.collapsed ? '64px' : '232px'" class="aside">
      <div class="brand">
        <span class="logo">☾</span>
        <span v-show="!app.collapsed" class="bn serif">奇德芬芳 · 管理后台</span>
      </div>
      <el-menu :default-active="route.path" :default-openeds="[currentGroupName]" :collapse="app.collapsed" router class="menu" :collapse-transition="false" unique-opened>
        <el-sub-menu v-for="g in groups" :key="g.group" :index="g.group">
          <template #title><el-icon><component :is="groupIcon(g.group)" /></el-icon><span>{{ g.group }}</span></template>
          <el-menu-item v-for="m in g.items" :key="m.path" :index="'/' + m.path">
            <el-icon><component :is="m.icon" /></el-icon>
            <template #title>{{ m.title }}</template>
          </el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>

    <el-container>
      <!-- 顶栏 -->
      <el-header class="header">
        <el-icon class="collapse" @click="app.toggle">
          <component :is="app.collapsed ? 'Expand' : 'Fold'" />
        </el-icon>
        <el-breadcrumb separator="/">
          <el-breadcrumb-item>奇德芬芳</el-breadcrumb-item>
          <el-breadcrumb-item>{{ currentTitle }}</el-breadcrumb-item>
        </el-breadcrumb>
        <el-tag :type="dataTag.type" size="small" effect="light" round class="dkind" :title="dataTag.tip">{{ dataTag.label }}</el-tag>
        <div class="spacer" />
        <el-dropdown @command="onCommand">
          <span class="user">
            <el-avatar :size="28" class="av">{{ initial }}</el-avatar>
            <span class="un">{{ auth.role || '员工' }}</span>
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item disabled>{{ auth.roles.join(' · ') || '—' }}</el-dropdown-item>
              <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>

      <!-- 内容区 -->
      <el-main class="main">
        <router-view v-slot="{ Component }">
          <keep-alive>
            <component :is="Component" />
          </keep-alive>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'
import { visibleGroups, dataKind } from '@/router/menu'

const app = useAppStore()
const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

// 数据来源标注（demo 明示，防误当真实业绩）：真实抽取 / 真配置·演示流水 / 合成演示
const DATA_TAG: Record<string, { label: string; type: 'success' | 'primary' | 'warning'; tip: string }> = {
  real: { label: '真实数据', type: 'success', tip: '本页数据来自奇德芬芳真实抽取导入（员工/门店/项目目录/提成/套餐/耗材BOM/房型/品控标准/问答语料；手机号已脱敏）' },
  mixed: { label: '真实配置·演示流水', type: 'primary', tip: '配置为真实（如房型布局/品控标准），房态/评分等流水为演示数据' },
  demo: { label: '演示数据', type: 'warning', tip: '本页为合成演示数据，非真实经营数据（客户/订单/账单/线索/漏斗/各类经营KPI 均为演示）' },
}
const dataTag = computed(() => DATA_TAG[dataKind(route.path.replace(/^\//, ''))])

// 按权限过滤 + 分组的二级导航：管理层看全部有内容的组；一线只看到自己有权的那几组（空组自动隐藏）
const groups = computed(() => visibleGroups(auth.isManager, auth.perms, auth.isHQ))
// 当前路由所在分组：供 el-menu default-openeds，刷新/直达 URL 时自动展开该组，否则高亮项藏在折叠组里看不见
const currentGroupName = computed(() => {
  const p = route.path.replace(/^\//, '')
  return groups.value.find((g) => g.items.some((m) => m.path === p))?.group || ''
})
// 分组父级图标
const GROUP_ICON: Record<string, string> = { 经营分析: 'DataLine', 客户: 'User', 交易财务: 'Money', 房务护理: 'House', 膳食月嫂: 'Bowl', 库存采购: 'Box', 营销会员: 'ShoppingCart', 商品品控: 'Goods', 系统设置: 'Setting' }
function groupIcon(g: string): string { return GROUP_ICON[g] || 'Menu' }
const currentTitle = computed(() => (route.meta?.title as string) || '')
const initial = computed(() => (auth.role || '奇德芬芳').slice(0, 1))

function onCommand(cmd: string) {
  if (cmd === 'logout') {
    auth.logout()
    router.push('/login')
  }
}

</script>

<style scoped>
.layout {
  height: 100vh;
}
.aside {
  background: var(--night);
  transition: width 0.2s;
  overflow: hidden;
}
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 60px;
  padding: 0 20px;
  color: var(--gold-soft);
  border-bottom: 1px solid rgba(184, 148, 90, 0.18);
}
.brand .logo {
  font-size: 22px;
  color: var(--gold);
}
.brand .bn {
  font-size: 17px;
  letter-spacing: 2px;
  white-space: nowrap;
}
/* 暗夜底上的金白菜单：变量须设在 el-menu 根元素（即 .menu）本身，
   才能 cascade 到 .el-menu-item；写成 :deep(.el-menu) 选不中同一元素。 */
.menu {
  border-right: 0;
  --el-menu-bg-color: transparent;
  --el-menu-text-color: var(--gold);
  --el-menu-hover-bg-color: var(--hair);
  --el-menu-hover-text-color: var(--gold-soft);
  --el-menu-active-color: var(--gold-soft);
}
.menu:deep(.el-menu-item.is-active) {
  background: var(--hair);
}
.header {
  display: flex;
  align-items: center;
  gap: 16px;
  background: var(--paper);
  border-bottom: 1px solid var(--hair);
}
.collapse {
  font-size: 18px;
  cursor: pointer;
  color: var(--ink-2);
}
.dkind {
  margin-left: 4px;
  cursor: help;
}
.spacer {
  flex: 1;
}
.user {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: var(--ink);
  outline: none;
}
.user .av {
  background: var(--gold);
  color: var(--paper);
  font-family: var(--font-cn-serif);
}
.main {
  background: var(--ivory);
  padding: 18px;
}
</style>

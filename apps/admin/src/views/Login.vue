<template>
  <div class="login-wrap">
    <div class="card">
      <div class="brand">
        <span class="logo">☾</span>
        <span class="bn serif">奇德芬芳</span>
        <span class="sub">管 理 后 台</span>
      </div>

      <el-form class="form" @submit.prevent="onLogin">
        <el-form-item>
          <el-input v-model="phone" placeholder="手机号" size="large" clearable>
            <template #prefix><el-icon><User /></el-icon></template>
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-input v-model="password" type="password" placeholder="密码" size="large" show-password @keyup.enter="onLogin">
            <template #prefix><el-icon><Lock /></el-icon></template>
          </el-input>
        </el-form-item>
        <el-button type="primary" size="large" class="btn" :loading="loading" @click="onLogin">登 录</el-button>
      </el-form>

      <div v-if="groups.length" class="demos">
        <div class="dt">演示账号 · 全部 {{ total }} 个（点击填充 · 密码统一下发）</div>
        <el-input v-model="kw" size="small" placeholder="搜姓名 / 手机号 / 角色" clearable class="dsearch" />
        <div v-for="g in filteredGroups" :key="g.role" class="grow">
          <span class="grole">{{ g.role }}<i class="gn">{{ g.list.length }}</i></span>
          <span class="gtags">
            <el-tag v-for="d in g.list" :key="d.phone" class="dtag" effect="plain" @click="fill(d)">{{ d.name || d.phone }}</el-tag>
          </span>
        </div>
        <div v-if="kw && !filteredGroups.length" class="dt">无匹配账号</div>
      </div>
      <div v-else-if="demos.length" class="demos">
        <div class="dt">演示账号（点击填充）</div>
        <el-tag v-for="d in demos" :key="d.phone" class="dtag" effect="plain" @click="fill(d)">
          {{ d.name || d.role || d.phone }}
        </el-tag>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '@/api'
import { firstVisiblePath } from '@/router/menu'
import { filterAccountGroups } from './accountFilter'
import { useAuthStore } from '@/stores/auth'

const phone = ref('')
const password = ref('')
const loading = ref(false)
const demos = ref<any[]>([])
const groups = ref<Array<{ role: string; list: any[] }>>([]) // 按角色分组全量账号（后端 demo-accounts.groups）
const kw = ref('') // 账号搜索：姓名/手机号/角色
const total = computed(() => groups.value.reduce((s, g) => s + g.list.length, 0))
const filteredGroups = computed(() => filterAccountGroups(groups.value, kw.value))
const demoPwd = ref('') // 演示账号共享密码（后端 demo-accounts 放在顶层 data.password）

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

onMounted(async () => {
  // 本地/非生产环境后端会返回演示账号，便于联调；生产返回 404 → 静默忽略。
  try {
    const d = await api().demoAccounts()
    demoPwd.value = d?.password || d?.defaultPassword || ''
    groups.value = (d?.groups || []).filter((g: any) => g?.list?.length)
    const list = Array.isArray(d) ? d : (d?.staff || d?.accounts || d?.list || [])
    demos.value = (list || []).filter((x: any) => x && x.phone)
  } catch { /* 生产无演示账号 */ }
})

function fill(d: any) {
  phone.value = d.phone || ''
  password.value = d.password || d.pwd || demoPwd.value || ''
}

async function onLogin() {
  if (!phone.value || !password.value) {
    ElMessage.warning('请输入手机号和密码')
    return
  }
  loading.value = true
  try {
    const r = await api().login(phone.value.trim(), password.value)
    auth.setSession(r)
    ElMessage.success('登录成功')
    // 落地到当前身份第一个可见模块：管理层→总部驾驶舱，一线→其业务首页（不再死跳 /dashboard 让一线看到全店大屏）
    router.replace((route.query.redirect as string) || ('/' + firstVisiblePath(auth.isManager, auth.perms, auth.isHQ)))
  } catch (e: any) {
    ElMessage.error(e?.message || '登录失败，请检查账号密码')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-wrap {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(120% 120% at 50% 0%, var(--ivory-2), var(--ivory));
}
.card {
  width: 380px;
  background: var(--paper);
  border: 1px solid var(--hair);
  border-radius: var(--r-lg);
  padding: 40px 36px 32px;
  box-shadow: var(--shadow);
}
.brand {
  text-align: center;
  margin-bottom: 28px;
}
.brand .logo {
  display: block;
  font-size: 38px;
  color: var(--gold);
}
.brand .bn {
  display: block;
  font-size: 24px;
  letter-spacing: 3px;
  color: var(--gold-deep);
  margin-top: 6px;
}
.brand .sub {
  display: block;
  font-size: 12px;
  color: var(--ink-3);
  margin-top: 8px;
  letter-spacing: 6px;
}
.btn {
  width: 100%;
  letter-spacing: 8px;
}
.demos {
  margin-top: 22px;
  border-top: 1px solid var(--hair);
  padding-top: 14px;
  max-height: 300px;
  overflow-y: auto;
}
.demos .dt {
  font-size: 12px;
  color: var(--ink-3);
  margin-bottom: 10px;
}
.grow {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 8px;
}
.dsearch {
  margin-bottom: 10px;
}
.grole {
  flex: none;
  width: 62px;
  font-size: 12px;
  color: var(--gold-deep);
  line-height: 24px;
  text-align: right;
}
.grole .gn {
  font-style: normal;
  color: var(--ink-3);
  font-size: 10px;
  margin-left: 2px;
}
.gtags {
  flex: 1;
}
.dtag {
  margin: 0 6px 6px 0;
  cursor: pointer;
}
</style>

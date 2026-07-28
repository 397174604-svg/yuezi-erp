<template>
  <div v-loading="loading">
    <h2 class="ph">系统设置</h2>
    <el-tabs v-model="activeGroup" tab-position="left" class="stabs">
      <el-tab-pane v-for="(items, group) in schema" :key="group" :label="group" :name="group">
        <div class="panel">
          <el-form label-width="160px" class="sform">
            <el-form-item v-for="it in items" :key="it.key" :label="it.label">
              <el-switch v-if="it.type === 'bool'" v-model="model[group][it.key]" active-value="1" inactive-value="0" />
              <el-input-number v-else-if="it.type === 'number'" v-model="model[group][it.key]" :step="numStep(it.key)" />
              <el-input v-else v-model="model[group][it.key]" style="width: 240px" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveGroup(group)">保存「{{ group }}」</el-button>
              <span class="hint">改动后点保存生效（按租户独立存储）</span>
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

const loading = ref(false)
const schema = ref<Record<string, any[]>>({})
const model = reactive<Record<string, Record<string, any>>>({})
const activeGroup = ref('')

function numStep(key: string): number { return key.includes('discount') ? 0.05 : 1 }

async function load() {
  loading.value = true
  try {
    const s = await api().getSettings() || {}
    schema.value = s
    for (const [group, items] of Object.entries(s)) {
      model[group] = model[group] || {}
      for (const it of items as any[]) {
        model[group][it.key] = it.type === 'number' ? Number(it.value) : it.value
      }
    }
    if (!activeGroup.value) activeGroup.value = Object.keys(s)[0] || ''
  } catch (e: any) { ElMessage.error('设置加载失败：' + (e?.message || '')) }
  finally { loading.value = false }
}

async function saveGroup(group: string) {
  try {
    const values: Record<string, string> = {}
    for (const [k, v] of Object.entries(model[group])) values[k] = String(v)
    await api().saveSettings(group, values)
    ElMessage.success('「' + group + '」已保存')
  } catch (e: any) { ElMessage.error('保存失败：' + (e?.message || '')) }
}

onMounted(load)
</script>

<style scoped>
.ph { font-family: var(--font-cn-serif); font-weight: 600; margin: 0 0 16px; }
.stabs { background: var(--paper); border: 1px solid var(--hair); border-radius: var(--r-md); padding: 16px; min-height: 460px; }
.panel { padding: 8px 16px; }
.sform :deep(.el-form-item__label) { color: var(--ink-2); }
.hint { font-size: 12px; color: var(--ink-3); margin-left: 14px; }
</style>

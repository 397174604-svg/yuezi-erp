<template>
  <div>
    <div class="bar">
      <h2 class="ph">业务跟踪台</h2>
      <div class="filters">
        <el-input v-model="date" size="small" placeholder="YYYY-MM-DD" style="width:140px" />
        <el-button type="primary" size="small" @click="load">查询</el-button>
      </div>
    </div>

    <el-row :gutter="14" class="mb">
      <el-col :span="8"><el-card shadow="never" class="stat a"><div class="lbl">今日预约</div><div class="val">{{ d.counts?.appointments ?? 0 }}</div></el-card></el-col>
      <el-col :span="8"><el-card shadow="never" class="stat b"><div class="lbl">预产期临近(14天)</div><div class="val">{{ d.counts?.edcUpcoming ?? 0 }}</div></el-card></el-col>
      <el-col :span="8"><el-card shadow="never" class="stat c"><div class="lbl">沉睡客户(待召回)</div><div class="val">{{ d.counts?.dormant ?? 0 }}</div></el-card></el-col>
    </el-row>

    <el-row :gutter="14">
      <el-col :span="8">
        <el-card shadow="never"><div class="sub">📅 今日预约</div>
          <el-table :data="d.todayAppointments" v-loading="loading" size="small" border empty-text="今日无预约">
            <el-table-column prop="time" label="时间" width="130" /><el-table-column prop="project" label="项目" /><el-table-column prop="tech" label="技师" width="80" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never"><div class="sub">🤰 预产期临近</div>
          <el-table :data="d.edcUpcoming" size="small" border empty-text="近期无预产">
            <el-table-column prop="name" label="客户" width="90" /><el-table-column prop="phone" label="电话" /><el-table-column prop="edc" label="预产期" width="110" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never"><div class="sub">😴 沉睡客户召回</div>
          <el-table :data="d.dormant" size="small" border empty-text="无沉睡客户">
            <el-table-column prop="name" label="客户" width="90" /><el-table-column prop="last_consume" label="末次消费" width="110" /><el-table-column prop="advisor" label="顾问" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

const date = ref('')
const d = ref<any>({ counts: {}, todayAppointments: [], edcUpcoming: [], dormant: [] })
const loading = ref(false)

async function load() {
  loading.value = true
  try { d.value = (await api().trackingToday({ date: date.value || undefined })) || d.value }
  catch (e: any) { ElMessage.error('加载失败：' + (e?.message || '')) }
  finally { loading.value = false }
}

onMounted(load)
</script>

<style scoped>
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.ph { margin: 0; font-size: 18px; }
.filters { display: flex; gap: 8px; align-items: center; }
.mb { margin-bottom: 14px; }
.stat { text-align: center; }
.stat .lbl { color: #888; font-size: 13px; }
.stat .val { font-size: 28px; font-weight: 700; margin-top: 4px; }
.stat.a .val { color: #1971c2; }
.stat.b .val { color: #e8590c; }
.stat.c .val { color: #868e96; }
.sub { font-weight: 600; margin-bottom: 8px; }
</style>

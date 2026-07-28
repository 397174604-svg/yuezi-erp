<template>
  <div v-loading="loading">
    <h2 class="ph">短信营销</h2>
    <el-alert type="warning" :closable="false" show-icon style="margin-bottom: 12px"
      title="短信通道未接入运营商——当前为演示模拟：发送记录与余额扣减为流程展示，短信不会真实下发。接入阿里云/腾讯云短信（需企业资质+签名模板报备）后此提示移除。" />

    <!-- 账号 + 余额预警 -->
    <div class="acct">
      <div class="acol">
        <div class="al">短信签名</div>
        <div class="av serif">{{ acc.sign || '—' }}</div>
      </div>
      <div class="acol">
        <div class="al">剩余条数</div>
        <div class="av serif" :class="{ low: acc.low }">{{ acc.balance ?? 0 }}</div>
        <el-tag v-if="acc.low" type="danger" size="small" effect="dark">余额预警（≤{{ acc.warnQty }}）</el-tag>
      </div>
      <div class="acol">
        <div class="al">已发短信 / 总触达</div>
        <div class="av serif">{{ acc.sends ?? 0 }} 次 / {{ acc.totalRecipients ?? 0 }} 人</div>
      </div>
      <div class="actions">
        <el-button @click="openEdit">编辑签名 / 预警</el-button>
        <el-button type="primary" @click="openRecharge">充值条数</el-button>
      </div>
    </div>

    <div class="grid">
      <!-- 群发 -->
      <div class="panel send">
        <div class="ph2">短信群发</div>
        <el-form label-width="76px">
          <el-form-item label="场景"><el-select v-model="form.scene" style="width: 100%"><el-option v-for="s in SCENES" :key="s" :label="s" :value="s" /></el-select></el-form-item>
          <el-form-item label="收件人数"><el-input-number v-model="form.recipients" :min="1" :step="10" /></el-form-item>
          <el-form-item label="内容">
            <el-input v-model="form.content" type="textarea" :rows="4" placeholder="短信内容（会自动加签名前缀）" maxlength="300" show-word-limit />
          </el-form-item>
          <el-form-item label="预计消耗">{{ form.recipients || 0 }} 条（1 条/人）</el-form-item>
          <el-button type="primary" :disabled="!form.content || !(form.recipients > 0)" @click="doSend">确认群发</el-button>
        </el-form>
      </div>

      <!-- 发送记录 -->
      <div class="panel">
        <div class="ph2">发送记录</div>
        <el-table :data="records" border stripe size="small" empty-text="暂无发送记录" max-height="420">
          <el-table-column prop="created_at" label="时间" width="160" />
          <el-table-column prop="scene" label="场景" width="100" />
          <el-table-column prop="content" label="内容" min-width="200" show-overflow-tooltip />
          <el-table-column prop="recipients" label="收件人" width="80" align="center" />
          <el-table-column prop="cost" label="消耗" width="70" align="center" />
          <el-table-column label="状态" width="80"><template #default="{ row }"><el-tag :type="row.status === '已发' ? 'success' : 'danger'" size="small" effect="dark">{{ row.status }}</el-tag></template></el-table-column>
        </el-table>
      </div>
    </div>

    <!-- 编辑签名/预警 -->
    <el-dialog v-model="editVisible" title="编辑签名 / 预警" width="400px">
      <el-form label-width="80px">
        <el-form-item label="短信签名"><el-input v-model="edit.sign" /></el-form-item>
        <el-form-item label="余额预警线"><el-input-number v-model="edit.warnQty" :min="0" :step="100" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="editVisible = false">取消</el-button><el-button type="primary" @click="saveEdit">保存</el-button></template>
    </el-dialog>

    <!-- 充值 -->
    <el-dialog v-model="rechargeVisible" title="充值短信条数" width="360px">
      <el-input-number v-model="rechargeQty" :min="100" :step="500" style="width: 100%" />
      <template #footer><el-button @click="rechargeVisible = false">取消</el-button><el-button type="primary" @click="doRecharge">确认充值</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

const SCENES = ['营销群发', '到期提醒', '生日关怀', '活动推广', '回访邀约']
const loading = ref(false)
const acc = ref<any>({})
const records = ref<any[]>([])
const form = reactive<any>({ scene: '营销群发', recipients: 50, content: '' })

async function loadAll() {
  loading.value = true
  try {
    acc.value = await api().getSmsSummary() || {}
    records.value = await api().listSmsRecords({ limit: 100 }) || []
  } catch (e: any) { ElMessage.error('短信数据加载失败：' + (e?.message || '')) }
  finally { loading.value = false }
}

async function doSend() {
  try {
    const r = await api().sendSms({ scene: form.scene, content: form.content, recipients: form.recipients })
    ElMessage.success(`群发成功，消耗 ${r.cost} 条，剩余 ${r.balance} 条`)
    form.content = ''
    loadAll()
  } catch (e: any) { ElMessage.error('群发失败：' + (e?.message || '')) }
}

// 编辑签名/预警
const editVisible = ref(false)
const edit = reactive<any>({ sign: '', warnQty: 0 })
function openEdit() { edit.sign = acc.value.sign; edit.warnQty = acc.value.warnQty; editVisible.value = true }
async function saveEdit() {
  try { await api().updateSmsAccount({ sign: edit.sign, warnQty: edit.warnQty }); ElMessage.success('已保存'); editVisible.value = false; loadAll() }
  catch (e: any) { ElMessage.error('保存失败：' + (e?.message || '')) }
}

// 充值
const rechargeVisible = ref(false)
const rechargeQty = ref(1000)
function openRecharge() { rechargeQty.value = 1000; rechargeVisible.value = true }
async function doRecharge() {
  try { await api().rechargeSms(rechargeQty.value); ElMessage.success('充值成功'); rechargeVisible.value = false; loadAll() }
  catch (e: any) { ElMessage.error('充值失败：' + (e?.message || '')) }
}

onMounted(loadAll)
</script>

<style scoped>
.ph { font-family: var(--font-cn-serif); font-weight: 600; margin: 0 0 16px; }
.acct { display: flex; align-items: center; gap: 30px; background: var(--paper); border: 1px solid var(--hair); border-radius: var(--r-md); padding: 22px 28px; margin-bottom: 18px; }
.acol .al { font-size: 12px; color: var(--ink-3); }
.acol .av { font-size: 26px; color: var(--gold-deep); font-weight: 600; margin-top: 2px; }
.acol .av.low { color: var(--danger); }
.actions { margin-left: auto; display: flex; gap: 10px; }
.grid { display: flex; gap: 18px; align-items: flex-start; }
.panel { background: var(--paper); border: 1px solid var(--hair); border-radius: var(--r-md); padding: 20px; }
.panel.send { width: 380px; flex-shrink: 0; }
.panel:not(.send) { flex: 1; }
.ph2 { font-family: var(--font-cn-serif); font-weight: 600; margin-bottom: 16px; padding-left: 10px; border-left: 3px solid var(--gold); }
</style>

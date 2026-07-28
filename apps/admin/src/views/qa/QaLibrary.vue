<template>
  <div>
    <div class="bar">
      <h2 class="ph">AI 客服知识库</h2>
      <div>
        <el-button size="small" type="primary" @click="openCreate()">新增问答</el-button>
        <el-button size="small" :loading="loading" @click="load">刷新</el-button>
      </div>
    </div>
    <el-alert type="info" :closable="false" show-icon class="mb"
      title="检索式硬校验：宝妈端提问只从本库检索作答，低于阈值自动转人工并落未命中日志（右栏）。来源=调研为通用母婴常识冷启动；真实 5 年问题库到位后导入替换。" />
    <el-card shadow="never" class="mb">
      <div class="tryrow">
        <el-input v-model="tryQ" placeholder="检索测试：输入宝妈口吻的问题，看会命中哪条（不计数、不落未命中）" clearable @keyup.enter="doTry" style="max-width: 520px" />
        <el-button size="default" @click="doTry" :loading="trying">测试检索</el-button>
        <span v-if="tried && !tryHits.length" class="miss">未命中 → 线上会转人工并记录</span>
      </div>
      <el-table v-if="tryHits.length" :data="tryHits" size="small" border class="mt">
        <el-table-column prop="score" label="得分" width="70" align="right" />
        <el-table-column prop="question" label="命中问题" min-width="220" />
        <el-table-column prop="category" label="类目" width="140" />
        <el-table-column prop="source" label="来源" width="100" />
      </el-table>
    </el-card>
    <div class="panes">
      <el-card shadow="never" class="pane" v-loading="loading">
        <template #header>
          <div class="hd"><b>问答库（{{ rows.length }}）</b>
            <div class="flt">
              <el-select v-model="fCat" placeholder="类目" clearable size="small" style="width: 150px" @change="load">
                <el-option v-for="c in cats" :key="c" :label="c" :value="c" />
              </el-select>
              <el-select v-model="fSrc" placeholder="来源" clearable size="small" style="width: 110px" @change="load">
                <el-option label="调研" value="调研" /><el-option label="院内文档" value="院内文档" /><el-option label="测试" value="测试" />
              </el-select>
              <el-select v-model="fRev" placeholder="审核" clearable size="small" style="width: 100px" @change="load">
                <el-option label="已审核" value="1" /><el-option label="未审核" value="0" />
              </el-select>
              <el-input v-model="fQ" placeholder="搜问题/答案/关键词" clearable size="small" style="width: 180px" @keyup.enter="load" @clear="load" />
            </div>
          </div>
        </template>
        <el-table :data="rows" size="small" border empty-text="暂无语料">
          <el-table-column prop="question" label="问题" min-width="200" show-overflow-tooltip />
          <el-table-column prop="category" label="类目" width="130" />
          <el-table-column prop="source" label="来源" width="92">
            <template #default="{ row }"><el-tag size="small" effect="dark" :type="row.source === '院内文档' ? 'success' : 'info'">{{ row.source }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="hit_count" label="命中" width="64" align="right" />
          <el-table-column prop="status" label="状态" width="80">
            <template #default="{ row }"><el-tag size="small" effect="dark" :type="row.status === '启用' ? 'success' : 'danger'">{{ row.status }}</el-tag></template>
          </el-table-column>
          <el-table-column label="审核" width="96">
            <template #default="{ row }">
              <el-tooltip v-if="row.reviewed_at" :content="row.reviewed_by + ' · ' + String(row.reviewed_at).slice(0, 10)">
                <el-tag size="small" effect="dark" type="success">已审核</el-tag>
              </el-tooltip>
              <el-tag v-else size="small" effect="dark" type="warning">未审核</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="186" fixed="right">
            <template #default="{ row }">
              <el-button v-if="!row.reviewed_at" link type="success" size="small" @click="review(row)">审核</el-button>
              <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
              <el-button link size="small" @click="toggle(row)">{{ row.status === '启用' ? '停用' : '启用' }}</el-button>
              <el-popconfirm title="确认删除该问答？" @confirm="del(row)"><template #reference><el-button link type="danger" size="small">删</el-button></template></el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
      <el-card shadow="never" class="pane" v-loading="loadingMiss">
        <template #header><div class="hd"><b>未命中日志（转人工）</b>
          <el-select v-model="fMiss" size="small" clearable placeholder="状态" style="width: 110px" @change="loadMiss">
            <el-option label="待处理" value="待处理" /><el-option label="已补录" value="已补录" /><el-option label="已忽略" value="已忽略" />
          </el-select></div></template>
        <el-table :data="missRows" size="small" border empty-text="暂无未命中——问答库覆盖良好">
          <el-table-column prop="query" label="客户提问" min-width="200" show-overflow-tooltip />
          <el-table-column prop="created_at" label="时间" width="140">
            <template #default="{ row }">{{ (row.created_at || '').slice(5, 16) }}</template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="84">
            <template #default="{ row }"><el-tag size="small" effect="dark" :type="row.status === '待处理' ? 'warning' : row.status === '已补录' ? 'success' : 'info'">{{ row.status }}</el-tag></template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" :disabled="row.status === '已补录'" @click="supplement(row)">补录</el-button>
              <el-button link size="small" :disabled="row.status !== '待处理'" @click="setMiss(row, '已忽略')">忽略</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>
    <el-dialog v-model="dlg" :title="form.qaId ? '编辑问答' : '新增问答'" width="620px">
      <el-form label-width="72px">
        <el-form-item label="问题"><el-input v-model="form.question" placeholder="客户口吻，如：宝宝脸上起小红疹怎么办" /></el-form-item>
        <el-form-item label="答案"><el-input v-model="form.answer" type="textarea" :rows="5" placeholder="80-220 字，谨慎保守；症状类结尾须带就医提示" /></el-form-item>
        <el-form-item label="关键词"><el-input v-model="form.keywords" placeholder="逗号分隔，覆盖口语说法，如：疹子,红点,湿疹" /></el-form-item>
        <el-form-item label="类目">
          <el-select v-model="form.category" allow-create filterable style="width: 240px">
            <el-option v-for="c in cats" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="来源">
          <el-select v-model="form.source" style="width: 160px">
            <el-option label="调研" value="调研" /><el-option label="院内文档" value="院内文档" /><el-option label="测试" value="测试" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlg = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api'
const rows = ref<any[]>([]); const missRows = ref<any[]>([]); const cats = ref<string[]>([])
const loading = ref(false); const loadingMiss = ref(false); const saving = ref(false)
const fCat = ref(''); const fSrc = ref(''); const fQ = ref(''); const fMiss = ref(''); const fRev = ref('')
const tryQ = ref(''); const tryHits = ref<any[]>([]); const trying = ref(false); const tried = ref(false)
const dlg = ref(false); const form = ref<any>({})
let missFrom: any = null // 「补录」来源行：保存成功后自动标已补录
async function load() {
  loading.value = true
  try {
    rows.value = await api().qaEntries({ category: fCat.value || undefined, source: fSrc.value || undefined, q: fQ.value || undefined, reviewed: fRev.value || undefined })
    cats.value = [...new Set(rows.value.map((r: any) => r.category).filter(Boolean))] as string[]
  } catch (e: any) { ElMessage.error('加载失败：' + (e?.message || '')) } finally { loading.value = false }
}
async function loadMiss() {
  loadingMiss.value = true
  try { missRows.value = await api().qaUnanswered({ status: fMiss.value || undefined }) }
  catch (e: any) { ElMessage.error('加载失败：' + (e?.message || '')) } finally { loadingMiss.value = false }
}
async function doTry() {
  if (!tryQ.value.trim()) return
  trying.value = true; tried.value = false
  try { tryHits.value = await api().qaSearch(tryQ.value.trim(), 5); tried.value = true }
  catch (e: any) { ElMessage.error(e?.message || '检索失败') } finally { trying.value = false }
}
function openCreate(preset?: any) { form.value = { source: '调研', category: cats.value[0] || '', ...(preset || {}) }; dlg.value = true }
function openEdit(row: any) { missFrom = null; form.value = { qaId: row.qa_id, question: row.question, answer: row.answer, keywords: row.keywords, category: row.category, source: row.source }; dlg.value = true }
async function save() {
  saving.value = true
  try {
    const f = form.value
    if (f.qaId) await api().qaUpdate(f.qaId, { question: f.question, answer: f.answer, keywords: f.keywords, category: f.category, source: f.source })
    else await api().qaCreate({ question: f.question, answer: f.answer, keywords: f.keywords, category: f.category, source: f.source })
    if (missFrom) { await api().qaSetUnanswered(missFrom.id, '已补录'); missFrom = null; loadMiss() }
    dlg.value = false; ElMessage.success('已保存'); load()
  } catch (e: any) { ElMessage.error(e?.message || '保存失败') } finally { saving.value = false }
}
async function review(row: any) {
  try {
    const { value } = await ElMessageBox.prompt('请输入审核人姓名（医学背景负责人，签核后内容责任由机构承担）', '医护审核签核', { confirmButtonText: '签核', cancelButtonText: '取消', inputPattern: /\S+/, inputErrorMessage: '审核人必填' })
    await api().qaReview(row.qa_id, String(value).trim())
    ElMessage.success('已签核'); load()
  } catch (e: any) { if (e !== 'cancel' && e?.message) ElMessage.error(e.message) }
}
async function toggle(row: any) {
  try { await api().qaUpdate(row.qa_id, { status: row.status === '启用' ? '停用' : '启用' }); load() }
  catch (e: any) { ElMessage.error(e?.message || '操作失败') }
}
async function del(row: any) {
  try { await api().qaRemove(row.qa_id); ElMessage.success('已删除'); load() }
  catch (e: any) { ElMessage.error(e?.message || '删除失败') }
}
function supplement(row: any) { missFrom = row; openCreate({ question: row.query }) }
async function setMiss(row: any, status: string) {
  try { await api().qaSetUnanswered(row.id, status); loadMiss() }
  catch (e: any) { ElMessage.error(e?.message || '操作失败') }
}
onMounted(() => { load(); loadMiss() })
</script>
<style scoped>
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.ph { margin: 0; font-size: 18px; } .mb { margin-bottom: 12px; } .mt { margin-top: 10px; }
.tryrow { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.miss { color: var(--el-color-warning); font-size: 13px; }
.panes { display: grid; grid-template-columns: 3fr 2fr; gap: 12px; }
.pane { min-width: 0; }
.hd { display: flex; align-items: center; justify-content: space-between; gap: 8px; flex-wrap: wrap; }
.flt { display: flex; gap: 8px; flex-wrap: wrap; }
@media (max-width: 1100px) { .panes { grid-template-columns: 1fr; } }
</style>

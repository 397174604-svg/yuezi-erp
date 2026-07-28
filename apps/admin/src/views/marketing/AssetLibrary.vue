<template>
  <div>
    <div class="bar">
      <h2 class="ph">图片素材库</h2>
      <div class="ops">
        <el-upload :show-file-list="false" :before-upload="beforeUpload" accept="image/*" multiple :disabled="uploading">
          <el-button type="primary" :loading="uploading" :icon="Upload">上传图片</el-button>
        </el-upload>
        <el-button :icon="Refresh" :loading="loading" @click="load">刷新</el-button>
      </div>
    </div>
    <el-alert
      title="上传即在浏览器压缩（长边 1600 / JPEG 0.85）并生成缩略图（长边 320）；服务端再剥离 EXIF（含 GPS）。图片以公开素材入库，供各端引用。"
      type="info" :closable="false" show-icon class="tip" />

    <div v-loading="loading" class="grid" :class="{ empty: !items.length && !loading }">
      <div v-for="it in items" :key="it.media_id" class="card">
        <el-image class="thumb" :src="it.thumbUrl" :preview-src-list="[it.fullUrl]" :initial-index="0" fit="cover" hide-on-click-modal preview-teleported>
          <template #error><div class="ph-img">加载失败</div></template>
        </el-image>
        <div class="meta">
          <span class="name" :title="it.filename || ('#' + it.media_id)">{{ it.filename || ('#' + it.media_id) }}</span>
          <span class="size">{{ fmtSize(it.size) }}</span>
        </div>
        <el-button class="del" link type="danger" size="small" :icon="Delete" @click="remove(it)">删除</el-button>
      </div>
      <el-empty v-if="!items.length && !loading" description="暂无图片素材，点右上「上传图片」" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, Refresh, Delete } from '@element-plus/icons-vue'
import { mediaApi, mediaSrc } from '@/api'

const REF = 'asset' // 素材库主体标识；缩略图同 refType，tag='thumb'、ref_id=主图 id 关联
const MAIN_EDGE = 1600, MAIN_Q = 0.85, THUMB_EDGE = 320, THUMB_Q = 0.7

interface Item { media_id: number; filename: string | null; size: number; thumbUrl: string; fullUrl: string; thumbId?: number }
const items = ref<Item[]>([])
const loading = ref(false)
const uploading = ref(false)

function fmtSize(n: number): string { return n >= 1024 * 1024 ? (n / 1024 / 1024).toFixed(1) + 'MB' : Math.max(1, Math.round(n / 1024)) + 'KB' }

function loadImage(file: File): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => resolve(img)
    img.onerror = () => reject(new Error('图片解码失败'))
    img.src = URL.createObjectURL(file)
  })
}
// canvas 等比缩放 + JPEG 重编码（顺带丢弃 EXIF；服务端仍会二次剥离兜底）。返回纯 base64（无 data: 前缀）。
function toJpegBase64(img: HTMLImageElement, maxEdge: number, quality: number): string {
  const scale = Math.min(1, maxEdge / Math.max(img.width, img.height))
  const w = Math.max(1, Math.round(img.width * scale)), h = Math.max(1, Math.round(img.height * scale))
  const canvas = document.createElement('canvas')
  canvas.width = w; canvas.height = h
  const ctx = canvas.getContext('2d')
  if (!ctx) throw new Error('canvas 不可用')
  ctx.drawImage(img, 0, 0, w, h)
  return canvas.toDataURL('image/jpeg', quality).replace(/^data:[^,]+,/, '')
}

// el-upload before-upload 拦截：自行压缩 + 双份上传（主图 + 缩略图），返回 false 阻止其默认请求。
function beforeUpload(file: File): boolean {
  void handleFile(file)
  return false
}
async function handleFile(file: File) {
  if (!/^image\//.test(file.type)) { ElMessage.warning('请选择图片文件'); return }
  uploading.value = true
  let objUrl = ''
  try {
    const img = await loadImage(file); objUrl = img.src
    const main = toJpegBase64(img, MAIN_EDGE, MAIN_Q)
    const thumb = toJpegBase64(img, THUMB_EDGE, THUMB_Q)
    const up = await mediaApi.upload({ refType: REF, mime: 'image/jpeg', dataBase64: main, filename: file.name, alt: file.name, visibility: 'public' })
    await mediaApi.upload({ refType: REF, tag: 'thumb', refId: up.mediaId, mime: 'image/jpeg', dataBase64: thumb, visibility: 'public' })
    ElMessage.success(`已上传：${file.name}`)
    await load()
  } catch (e: any) { ElMessage.error('上传失败：' + (e?.message || '')) }
  finally { if (objUrl) URL.revokeObjectURL(objUrl); uploading.value = false }
}

async function load() {
  loading.value = true
  try {
    const rows = await mediaApi.list({ refType: REF })
    const thumbs = new Map<number, { url: string; id: number }>()
    for (const r of rows) if (r.tag === 'thumb' && r.ref_id) thumbs.set(Number(r.ref_id), { url: r.url, id: r.media_id })
    items.value = rows.filter((r) => r.tag !== 'thumb').map((r) => {
      const t = thumbs.get(r.media_id)
      return { media_id: r.media_id, filename: r.filename, size: r.size, thumbUrl: mediaSrc(t?.url || r.url), fullUrl: mediaSrc(r.url), thumbId: t?.id }
    })
  } catch (e: any) { ElMessage.error('加载失败：' + (e?.message || '')); items.value = [] }
  finally { loading.value = false }
}
async function remove(it: Item) {
  try {
    await ElMessageBox.confirm('确认删除该图片？（不可撤销）', '删除素材', { type: 'warning' })
    await mediaApi.remove(it.media_id)
    if (it.thumbId) await mediaApi.remove(it.thumbId) // 连带删缩略图，避免孤儿
    ElMessage.success('已删除')
    await load()
  } catch (e: any) { if (e !== 'cancel') ElMessage.error('删除失败：' + (e?.message || '')) }
}
onMounted(load)
</script>

<style scoped>
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; gap: 8px; flex-wrap: wrap; }
.ph { margin: 0; font-size: 18px; }
.ops { display: flex; align-items: center; gap: 8px; }
.tip { margin-bottom: 12px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 12px; min-height: 120px; }
.grid.empty { display: block; }
.card { border: 1px solid var(--el-border-color-lighter); border-radius: 8px; overflow: hidden; background: var(--el-bg-color); display: flex; flex-direction: column; }
.thumb { width: 100%; height: 140px; display: block; background: var(--el-fill-color-light); }
.ph-img { width: 100%; height: 140px; display: flex; align-items: center; justify-content: center; color: var(--el-text-color-secondary); font-size: 12px; }
.meta { display: flex; align-items: center; justify-content: space-between; gap: 6px; padding: 6px 8px 0; }
.name { font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.size { font-size: 12px; color: var(--el-text-color-secondary); flex-shrink: 0; }
.del { align-self: flex-end; margin: 2px 6px 6px; }
</style>

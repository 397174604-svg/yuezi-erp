<template>
  <view class="screen">
    <view class="demo-flag">演示数据</view>
    <view class="topbar">
      <text class="back" @tap="back">‹</text>
      <text class="nm">奇德芬芳</text>
      <view class="who"><text class="wn">{{ name }}</text><text v-if="room" class="wr">{{ room }}</text></view>
    </view>
    <scroll-view scroll-y class="scroll">
      <view class="pad">
        <view class="cols">

          <!-- 左栏：宝妈评估 8 项（默认常态档，护士只改异常项） -->
          <view class="col col-mom">
            <view class="yz-card">
              <view class="ct1">宝妈评估<text class="sub">默认常态档 · 只改异常项</text></view>
              <view class="vitals">
                <view class="vi"><text class="vl">体温 ℃</text><input class="vin" type="digit" v-model="assess.temperature" placeholder="36.5" /></view>
                <view class="vi"><text class="vl">血压 mmHg</text><input class="vin" v-model="assess.bloodPressure" placeholder="118/76" /></view>
                <view class="vi"><text class="vl">脉搏 次/分</text><input class="vin" type="number" v-model="assess.pulse" placeholder="76" /></view>
                <view class="vi"><text class="vl">产后天数</text><input class="vin" type="number" v-model="assess.postpartumDay" placeholder="12" /></view>
              </view>
              <view v-for="g in chipGroups" :key="g.key" class="cgrp">
                <text class="gl">{{ g.label }}</text>
                <view class="chips">
                  <text v-for="op in g.options" :key="op" :class="['chip', assess[g.key] === op ? 'on' : '']" @tap="pickChip(g.key, op)">{{ op }}</text>
                </view>
              </view>
              <view v-if="tplMiss" class="note-warn">评估选项模板加载失败（网络异常），暂只能填数值与备注</view>
              <view class="cgrp"><text class="gl">评估备注</text><input class="vin full" v-model="assess.notes" placeholder="其他观察（可空）" /></view>
              <view class="cgrp"><text class="gl">本次巡房异常</text><input class="vin full" v-model="abnormal" placeholder="无异常可不填（默认「正常」）" /></view>
              <view class="cgrp">
                <text class="gl">评估拍照（≤3 张，点图删除）</text>
                <view class="photos">
                  <image v-for="(p, i) in momPhotos" :key="p.mediaId" class="ph" :src="imgUrl(p.url)" mode="aspectFill" @tap="delPhoto(momPhotos, i)" />
                  <view v-if="momPhotos.length < 3" class="ph add" @tap="addPhoto('mom', null)">＋拍照</view>
                </view>
              </view>
            </view>
          </view>

          <!-- 右栏：宝宝快捷录入（多胎 tab） -->
          <view class="col col-baby">
            <view class="yz-card">
              <view class="ct1">宝宝记录<text class="sub">3 秒快捷录入 · 先攒后交</text></view>
              <view v-if="!babies.length" class="empty">暂无宝宝档案（请先在后台为该客户建宝宝档案）</view>
              <block v-else>
                <view v-if="babies.length > 1" class="btabs">
                  <text v-for="(b, i) in babies" :key="b.baby_id" :class="['btab', i === activeBaby ? 'on' : '']" @tap="activeBaby = i">{{ babyName(b, i) }}</text>
                </view>
                <view v-if="curOpenSleep" class="sleepbar">
                  <text class="st">上段睡眠未闭合：入睡 {{ hm(curOpenSleep.logTime) }}</text>
                  <text class="sbtn" @tap="wakeUp">记录醒来</text>
                </view>
                <view class="quick">
                  <text v-for="q in quicks" :key="q" class="qbtn" @tap="openPopup(q)">＋{{ q }}</text>
                </view>
              </block>
              <view v-if="entries.length" class="pend">
                <view class="pt">本次待提交（{{ entries.length }} 条）</view>
                <view v-for="(e, i) in entries" :key="e.uid" class="pe">
                  <view class="pinfo">
                    <text class="pk">{{ e.kind }}<text class="pb"> · {{ e.babyName }}</text></text>
                    <text class="ps">{{ sumEntry(e) }} · {{ hm(e.logTime) }}</text>
                    <view class="photos sm">
                      <image v-for="(p, pi) in e.photos" :key="p.mediaId" class="ph" :src="imgUrl(p.url)" mode="aspectFill" @tap="delPhoto(e.photos, pi)" />
                      <view v-if="e.photos.length < 3" class="ph add" @tap="addPhoto('entry', e)">＋</view>
                    </view>
                  </view>
                  <text class="pdel" @tap="removeEntry(i)">删除</text>
                </view>
              </view>
            </view>
          </view>

        </view>
      </view>
    </scroll-view>

    <!-- 底部主按钮：聚合为 round-full 一次提交 -->
    <view class="footer">
      <view :class="['mainbtn', busy ? 'dis' : '']" @tap="submit">{{ busy ? '提交中…' : '完成巡房并提交' }}</view>
    </view>

    <!-- 半屏弹层（自实现遮罩，无 uni-popup 依赖） -->
    <view v-if="popup" class="wb-mask" @tap="popup = ''">
      <view class="sheet" @tap.stop>
        <view class="sh"><text class="sht">＋{{ popup }} · {{ curBabyName }}</text><text class="shx" @tap="popup = ''">✕</text></view>

        <block v-if="popup === '喂养'">
          <view class="cgrp"><text class="gl">喂养方式</text><view class="chips">
            <text v-for="o in C.FEED" :key="o" :class="['chip', form.feedType === o ? 'on' : '']" @tap="form.feedType = o">{{ o }}</text>
          </view></view>
          <view class="cgrp"><text class="gl">奶量 ml（常用档，可微调）</text><view class="chips">
            <text v-for="n in C.AMOUNTS" :key="n" :class="['chip', Number(form.amount) === n ? 'on' : '']" @tap="form.amount = n">{{ n }}</text>
          </view>
          <view class="stepper">
            <text class="stp" @tap="bump('amount', -10)">−10</text>
            <input class="vin mid" type="number" v-model="form.amount" placeholder="奶量" />
            <text class="stp" @tap="bump('amount', 10)">＋10</text>
          </view></view>
        </block>

        <block v-else-if="popup === '尿便'">
          <view class="cgrp"><text class="gl">类型</text><view class="chips">
            <text v-for="o in C.DIAPER" :key="o" :class="['chip', form.diaperType === o ? 'on' : '']" @tap="form.diaperType = o">{{ o }}</text>
          </view></view>
          <view class="cgrp"><text class="gl">量档</text><view class="chips">
            <text v-for="o in C.LEVELS" :key="o" :class="['chip', form.amountLevel === o ? 'on' : '']" @tap="form.amountLevel = o">{{ o }}</text>
          </view></view>
        </block>

        <block v-else-if="popup === '睡眠'">
          <view v-if="curOpenSleep" class="sleepbar">
            <text class="st">上段睡眠未闭合：入睡 {{ hm(curOpenSleep.logTime) }}</text>
          </view>
          <view class="bigrow">
            <view class="big" @tap="sleepStart">睡了<text class="bs">记入睡 = 现在</text></view>
            <view class="big alt" @tap="sleepWake">醒了<text class="bs">闭合上段睡眠</text></view>
          </view>
        </block>

        <block v-else-if="popup === '哭闹'">
          <view class="cgrp"><text class="gl">时长（分钟）</text><view class="chips">
            <text v-for="n in C.CRY" :key="n" :class="['chip', Number(form.durationMin) === n ? 'on' : '']" @tap="form.durationMin = n">{{ n }}</text>
          </view>
          <view class="stepper">
            <text class="stp" @tap="bump('durationMin', -5)">−5</text>
            <input class="vin mid" type="number" v-model="form.durationMin" placeholder="分钟" />
            <text class="stp" @tap="bump('durationMin', 5)">＋5</text>
          </view></view>
          <view class="cgrp"><text class="gl">原因备注</text><input class="vin full" v-model="form.note" placeholder="如：肠胀气、求抱（可空）" /></view>
        </block>

        <block v-else-if="popup === '体征'">
          <view class="cgrp"><text class="gl">指标</text><view class="chips">
            <text v-for="o in C.METRICS" :key="o" :class="['chip', form.metric === o ? 'on' : '']" @tap="form.metric = o">{{ o }}</text>
          </view></view>
          <view class="cgrp"><text class="gl">数值（{{ metricUnit }}）</text>
            <input class="vin mid" type="digit" v-model="form.metricValue" placeholder="如 36.8" />
          </view>
        </block>

        <block v-else-if="popup === '护理'">
          <view class="cgrp"><text class="gl">护理项目</text><view class="chips">
            <text v-for="o in C.CARES" :key="o" :class="['chip', form.careType === o ? 'on' : '']" @tap="form.careType = o">{{ o }}</text>
          </view></view>
        </block>

        <view v-if="popup !== '睡眠'" class="sbm" @tap="confirmPopup">加入待提交</view>
      </view>
    </view>
  </view>
</template>

<script>
// M-A 结构化巡房工作台（F070/F071/F072）：宝妈 8 项评估 + 宝宝 5 类快捷日志 + 照护拍照，
// 攒一屏后经 round-full 单事务整包提交；草稿实时落 storage 防丢。iPad 横屏两栏（>750px），手机纵向堆叠。
import { REMOTE, loadAssessTemplate, loadBabies, loadOpenSleep, closeSleepLog, submitRoundFull, uploadCarePhoto, attachPhoto } from '@/common/remote.js'

// 宝宝日志枚举（SOT 在后端 babyService，此处为交互契约同版镜像）
const C = {
  FEED: ['母乳', '配方奶', '混合'],
  AMOUNTS: [30, 60, 90, 120],
  DIAPER: ['小便', '大便', '混合'],
  LEVELS: ['少', '中', '多'],
  METRICS: ['体温', '体重', '黄疸', '身长', '头围'],
  CARES: ['洗澡', '抚触', '游泳', '脐部', '疫苗'],
  CRY: [5, 10, 30],
}
const METRIC_UNIT = { 体温: '℃', 体重: 'g', 黄疸: 'mg/dL', 身长: 'cm', 头围: 'cm' }
const nowIso = () => new Date().toISOString()

/* 拍照压缩 → dataURL(JPEG q0.8, 长边≤1280)。H5 走 canvas；小程序兜底走 compressImage+文件系统读 base64。 */
// #ifdef H5
function compressToDataUrl(path) {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => {
      try {
        const long = Math.max(img.width, img.height) || 1
        const scale = long > 1280 ? 1280 / long : 1
        const w = Math.max(1, Math.round(img.width * scale)), h = Math.max(1, Math.round(img.height * scale))
        const cv = document.createElement('canvas'); cv.width = w; cv.height = h
        cv.getContext('2d').drawImage(img, 0, 0, w, h)
        resolve(cv.toDataURL('image/jpeg', 0.8))
      } catch (e) { reject(e) }
    }
    img.onerror = reject
    img.src = path
  })
}
// #endif
// #ifndef H5
function compressToDataUrl(path) {
  return new Promise((resolve, reject) => {
    const read = (fp) => uni.getFileSystemManager().readFile({
      filePath: fp, encoding: 'base64',
      success: (f) => resolve('data:image/jpeg;base64,' + f.data), fail: reject,
    })
    uni.compressImage({ src: path, quality: 80, success: (r) => read(r.tempFilePath), fail: () => read(path) })
  })
}
// #endif

export default {
  data() {
    return {
      customerId: 0, name: '', room: '',
      tpl: null, tplMiss: false, // 评估枚举模板（后端 SOT）
      assess: { temperature: '', bloodPressure: '', pulse: '', postpartumDay: '', lochia_color: '', lochia_amount: '', fundus: '', perineum_heal: '', perineum_type: '', breast: '', mood: '', notes: '' },
      abnormal: '',
      momPhotos: [], // 宝妈评估照片 {mediaId,url}（已上传、待 attach）
      babies: [], activeBaby: 0,
      openSleep: {}, // babyId -> {logId, logTime} 开放睡眠段
      entries: [], // 宝宝日志草稿：{uid,babyId,babyName,kind,...,logTime,photos[]}
      popup: '', form: {},
      quicks: ['喂养', '尿便', '睡眠', '哭闹', '体征', '护理'],
      C,
      busy: false, wakeBusy: false, ready: false,
    }
  },
  computed: {
    draftKey() { return 'round_draft_' + this.customerId },
    curBaby() { return this.babies[this.activeBaby] || {} },
    curBabyName() { return this.babyName(this.curBaby, this.activeBaby) },
    curOpenSleep() { return this.openSleep[this.curBaby.baby_id] || null },
    metricUnit() { return METRIC_UNIT[this.form.metric] || '' },
    // 宝妈 chip 单选组（选项来自后端模板）
    chipGroups() {
      const t = this.tpl; if (!t) return []
      return [
        { key: 'lochia_color', label: '恶露颜色', options: t.lochia_color || [] },
        { key: 'lochia_amount', label: '恶露量', options: t.lochia_amount || [] },
        { key: 'fundus', label: '宫底', options: t.fundus || [] },
        { key: 'perineum_heal', label: '会阴愈合', options: t.perineum_heal || [] },
        { key: 'perineum_type', label: '伤口类型', options: t.perineum_type || [] },
        { key: 'breast', label: '乳房', options: t.breast || [] },
        { key: 'mood', label: '情绪', options: t.mood || [] },
      ]
    },
    // 草稿快照（深 watch 实时落 storage）
    draftState() { return { assess: this.assess, abnormal: this.abnormal, entries: this.entries, momPhotos: this.momPhotos } },
  },
  watch: {
    draftState: {
      deep: true,
      handler() {
        if (!this.ready || !this.customerId) return
        try { uni.setStorageSync(this.draftKey, JSON.stringify(this.draftState)) } catch (e) { /* 存储满等异常不阻断录入 */ }
      },
    },
  },
  async onLoad(q) {
    // #ifdef H5
    // iPad 横屏逃逸：解除 App.vue 的 480px 手机框（仅本页生效，onUnload 撤销）
    try { document.documentElement.classList.add('ym-wb-wide') } catch (e) { /* SSR 兜底 */ }
    // #endif
    this.customerId = Number(q.customerId) || 0
    this.name = decodeURIComponent(q.name || '')
    this.room = decodeURIComponent(q.room || '')
    if (!this.customerId) { uni.showToast({ title: '缺少客户参数', icon: 'none' }); setTimeout(() => uni.navigateBack(), 600); return }

    // 草稿恢复（先问，再拉模板/宝宝）
    let restored = false
    let raw = ''
    try { raw = uni.getStorageSync(this.draftKey) } catch (e) { /* ignore */ }
    if (raw) {
      const ok = await new Promise((r) => uni.showModal({ title: '恢复草稿', content: '发现该客户未提交的巡房草稿，是否恢复？', confirmText: '恢复', cancelText: '丢弃', success: (e) => r(e.confirm), fail: () => r(false) }))
      if (ok) {
        try {
          const d = JSON.parse(raw)
          this.assess = { ...this.assess, ...(d.assess || {}) }
          this.abnormal = d.abnormal || ''
          this.entries = Array.isArray(d.entries) ? d.entries : []
          this.momPhotos = Array.isArray(d.momPhotos) ? d.momPhotos : []
          restored = true
        } catch (e) { /* 草稿损坏 → 忽略 */ }
      }
      if (!restored) { try { uni.removeStorageSync(this.draftKey) } catch (e) { /* ignore */ } }
    }

    // 模板 + 宝宝并行拉取
    const [tpl, babies] = await Promise.all([loadAssessTemplate(), loadBabies(this.customerId)])
    this.tpl = tpl; this.tplMiss = !tpl
    this.babies = babies
    if (tpl && !restored) this.applyDefaults()
    // 每个宝宝查开放睡眠段（上次巡房记了入睡未闭合）
    const oss = await Promise.all(babies.map((b) => loadOpenSleep(b.baby_id)))
    const map = {}
    oss.forEach((os, i) => { if (os) map[babies[i].baby_id] = os })
    this.openSleep = map
    this.ready = true
  },
  onUnload() {
    // #ifdef H5
    try { document.documentElement.classList.remove('ym-wb-wide') } catch (e) { /* ignore */ }
    // #endif
  },
  methods: {
    back() { uni.navigateBack() },
    toast(t) { uni.showToast({ title: t, icon: 'none' }) },
    babyName(b, i) { return (b && b.name) || ('宝宝' + (i + 1)) },
    imgUrl(u) { return /^https?:/.test(u || '') ? u : (REMOTE.baseUrl || '') + (u || '') },
    hm(t) {
      if (!t) return ''
      const d = new Date(t)
      if (isNaN(d.getTime())) return String(t).slice(11, 16)
      const p = (n) => (n < 10 ? '0' : '') + n
      return p(d.getHours()) + ':' + p(d.getMinutes())
    },
    // 常态档默认选中（护士只改异常项）。伤口类型属客观事实，不设默认。
    applyDefaults() {
      const t = this.tpl
      const pk = (list, want) => ((list && list.length) ? (list.includes(want) ? want : list[0]) : '')
      this.assess.lochia_color = this.assess.lochia_color || pk(t.lochia_color, '浆液恶露')
      this.assess.lochia_amount = this.assess.lochia_amount || pk(t.lochia_amount, '量中')
      this.assess.fundus = this.assess.fundus || ((t.fundus || [])[0] || '')
      this.assess.perineum_heal = this.assess.perineum_heal || pk(t.perineum_heal, '愈合良好')
      this.assess.breast = this.assess.breast || pk(t.breast, '柔软')
      this.assess.mood = this.assess.mood || pk(t.mood, '情绪良好')
    },
    pickChip(key, op) { this.assess[key] = (this.assess[key] === op ? '' : op) }, // 再点一次=取消（可留空的字段不强填）

    /* —— 宝宝快捷录入 —— */
    openPopup(q) {
      if (!this.babies.length) return this.toast('该客户暂无宝宝档案')
      if (q === '喂养') this.form = { feedType: '母乳', amount: 90 }
      else if (q === '尿便') this.form = { diaperType: '小便', amountLevel: '中' }
      else if (q === '哭闹') this.form = { durationMin: 5, note: '' }
      else if (q === '体征') this.form = { metric: '体温', metricValue: '' }
      else if (q === '护理') this.form = { careType: '洗澡' }
      else this.form = {}
      this.popup = q
    },
    bump(k, d) { this.form[k] = Math.max(0, (Number(this.form[k]) || 0) + d) },
    confirmPopup() {
      const f = this.form, b = this.curBaby
      const base = { uid: Date.now() + '-' + Math.random().toString(36).slice(2, 6), babyId: b.baby_id, babyName: this.curBabyName, logTime: nowIso(), photos: [] }
      let e = null
      if (this.popup === '喂养') {
        const amt = (f.amount === '' || f.amount == null) ? null : Number(f.amount)
        if (amt != null && !(amt > 0)) return this.toast('奶量须为正数')
        e = { ...base, kind: '喂养', feedType: f.feedType }
        if (amt) e.amount = amt
      } else if (this.popup === '尿便') {
        e = { ...base, kind: '尿便', diaperType: f.diaperType, amountLevel: f.amountLevel }
      } else if (this.popup === '哭闹') {
        const d = parseInt(f.durationMin, 10)
        if (!(d > 0)) return this.toast('时长须为正整数分钟')
        e = { ...base, kind: '哭闹', durationMin: d }
        if (f.note) e.note = f.note
      } else if (this.popup === '体征') {
        const v = parseFloat(f.metricValue)
        if (isNaN(v)) return this.toast('请填写数值')
        e = { ...base, kind: '健康', metric: f.metric, metricValue: v }
      } else if (this.popup === '护理') {
        e = { ...base, kind: '护理', careType: f.careType }
      }
      if (e) { this.entries.push(e); this.popup = ''; this.toast('已加入待提交') }
    },
    removeEntry(i) { this.entries.splice(i, 1) },

    /* —— 睡眠两键 —— */
    sleepStart() {
      const b = this.curBaby
      this.entries.push({ uid: Date.now() + '-' + Math.random().toString(36).slice(2, 6), babyId: b.baby_id, babyName: this.curBabyName, kind: '睡眠', logTime: nowIso(), photos: [] })
      this.popup = ''
      this.toast('已记入睡（醒来后再记一笔闭合）')
    },
    async sleepWake() {
      const b = this.curBaby
      if (this.openSleep[b.baby_id]) { await this.wakeUp(); this.popup = ''; return } // 服务端开放段 → 直接 close
      for (let i = this.entries.length - 1; i >= 0; i--) { // 本次草稿里的入睡 → 就地补 endTime
        const e = this.entries[i]
        if (e.kind === '睡眠' && e.babyId === b.baby_id && !e.endTime) {
          let et = new Date()
          if (et.toISOString() <= e.logTime) et = new Date(new Date(e.logTime).getTime() + 60000) // 后端要求醒>睡
          this.entries.splice(i, 1, { ...e, endTime: et.toISOString() })
          this.popup = ''
          return this.toast('已记录醒来')
        }
      }
      this.toast('暂无未闭合的睡眠段')
    },
    async wakeUp() { // 闭合服务端开放睡眠段（上次巡房记的入睡）
      if (this.wakeBusy) return
      const b = this.curBaby, os = this.openSleep[b.baby_id]
      if (!os) return
      this.wakeBusy = true
      const r = await closeSleepLog(b.baby_id, os.logId)
      this.wakeBusy = false
      if (r.ok) {
        const map = { ...this.openSleep }; delete map[b.baby_id]; this.openSleep = map
        this.toast('已记录醒来')
      } else this.toast(r.msg || '操作失败')
    },

    /* —— 拍照（F072）：压缩→即传 /media/care 得 mediaId 存草稿，提交后 attach 回填 —— */
    addPhoto(type, entry) {
      const arr = type === 'mom' ? this.momPhotos : entry.photos
      const remain = 3 - arr.length
      if (remain <= 0) return this.toast('每条记录最多 3 张')
      const refType = type === 'mom' ? 'postpartum_assessment' : 'baby_log'
      uni.chooseImage({
        count: remain, sourceType: ['camera', 'album'], sizeType: ['compressed'],
        success: async (res) => {
          const paths = (res.tempFilePaths || []).slice(0, remain)
          for (const p of paths) {
            uni.showLoading({ title: '上传中…' })
            try {
              const dataUrl = await compressToDataUrl(p)
              const r = await uploadCarePhoto(refType, 'image/jpeg', dataUrl)
              if (r.ok) arr.push({ mediaId: r.mediaId, url: r.url })
              else this.toast(r.msg || '上传失败')
            } catch (e) { this.toast('图片处理失败') }
            uni.hideLoading()
          }
        },
      })
    },
    async delPhoto(arr, i) {
      const ok = await new Promise((r) => uni.showModal({ title: '移除照片', content: '移除这张照片？（已上传的图不随记录挂载）', success: (e) => r(e.confirm), fail: () => r(false) }))
      if (ok) arr.splice(i, 1)
    },

    /* —— 待提交摘要 —— */
    sumEntry(e) {
      if (e.kind === '喂养') return e.feedType + (e.amount ? ' · ' + e.amount + 'ml' : '')
      if (e.kind === '尿便') return e.diaperType + ' · 量' + (e.amountLevel || '—')
      if (e.kind === '睡眠') return '入睡 ' + this.hm(e.logTime) + (e.endTime ? ' → 醒 ' + this.hm(e.endTime) : '（未醒）')
      if (e.kind === '哭闹') return e.durationMin + ' 分钟' + (e.note ? ' · ' + e.note : '')
      if (e.kind === '健康') return e.metric + ' ' + e.metricValue + (METRIC_UNIT[e.metric] || '')
      if (e.kind === '护理') return e.careType || ''
      return ''
    },

    /* —— 聚合提交（round-full 单事务）—— */
    buildAssessment() {
      const a = this.assess, out = {}
      const t = parseFloat(a.temperature); if (a.temperature !== '' && !isNaN(t)) out.temperature = t
      if (a.bloodPressure) out.bloodPressure = String(a.bloodPressure).trim()
      const pu = parseInt(a.pulse, 10); if (a.pulse !== '' && !isNaN(pu)) out.pulse = pu
      const pd = parseInt(a.postpartumDay, 10); if (a.postpartumDay !== '' && !isNaN(pd)) out.postpartumDay = pd
      for (const k of ['lochia_color', 'lochia_amount', 'fundus', 'perineum_heal', 'perineum_type', 'breast', 'mood']) { if (a[k]) out[k] = a[k] }
      if (a.notes) out.notes = a.notes
      return Object.keys(out).length ? out : null
    },
    buildLogs() {
      return this.entries.map((e) => {
        const l = { babyId: e.babyId, kind: e.kind, logTime: e.logTime }
        if (e.feedType) l.feedType = e.feedType
        if (e.amount) l.amount = Number(e.amount)
        if (e.diaperType) l.diaperType = e.diaperType
        if (e.amountLevel) l.amountLevel = e.amountLevel
        if (e.metric) l.metric = e.metric
        if (e.metricValue !== '' && e.metricValue != null) l.metricValue = Number(e.metricValue)
        if (e.careType) l.careType = e.careType
        if (e.endTime) l.endTime = e.endTime
        if (e.durationMin) l.durationMin = Number(e.durationMin)
        if (e.note) l.note = e.note
        return l
      })
    },
    async submit() {
      if (this.busy) return
      let assessment = this.buildAssessment()
      if (!assessment && this.momPhotos.length) assessment = {} // 有评估照片须落一条评估记录承载挂载
      const babyLogs = this.buildLogs()
      if (!assessment && !babyLogs.length) return this.toast('请至少填写宝妈评估或一条宝宝日志')
      this.busy = true
      const r = await submitRoundFull({ customerId: this.customerId, roomNo: this.room || undefined, abnormal: this.abnormal || '正常', assessment: assessment || undefined, babyLogs })
      if (!r.ok) { this.busy = false; return this.toast(r.msg || '提交失败') }
      // 照片回填：逐条 attach，失败自动重试一次；仍失败仅提示，不阻塞主流程
      const jobs = []
      if (r.assessId) for (const p of this.momPhotos) jobs.push({ mediaId: p.mediaId, refType: 'postpartum_assessment', refId: r.assessId })
      for (let i = 0; i < this.entries.length; i++) {
        const logId = (r.logIds || [])[i]
        if (!logId) continue
        for (const p of this.entries[i].photos) jobs.push({ mediaId: p.mediaId, refType: 'baby_log', refId: logId })
      }
      let fail = 0
      for (const j of jobs) {
        let a = await attachPhoto(j.mediaId, j.refType, j.refId)
        if (!a.ok) a = await attachPhoto(j.mediaId, j.refType, j.refId) // 重试一次
        if (!a.ok) fail++
      }
      this.ready = false // 停止草稿续写
      try { uni.removeStorageSync(this.draftKey) } catch (e) { /* ignore */ }
      this.busy = false
      this.toast(fail ? ('巡房已记录（' + fail + ' 张照片回填失败）') : '巡房已记录')
      setTimeout(() => uni.navigateBack(), 700)
    },
  },
}
</script>

<style lang="scss">
/* #ifdef H5 */
/* 仅本页生效的宽屏逃逸：workbench onLoad 给 html 挂 ym-wb-wide，解除 App.vue 的 480px 手机框，iPad 才能两栏。 */
@media screen and (min-width: 750px) {
  html.ym-wb-wide uni-app { max-width: 1180px !important; box-shadow: none; }
}
/* #endif */
</style>

<style lang="scss" scoped>
.screen { display: flex; flex-direction: column; height: 100vh; }
.topbar { display: flex; align-items: center; padding: 28rpx 40rpx 8rpx; }
.back { font-size: 48rpx; color: $gold-deep; width: 56rpx; }
.nm { font-family: $font-display; font-size: 38rpx; letter-spacing: 4rpx; color: $gold-deep; }
.who { margin-left: auto; display: flex; align-items: center; gap: 12rpx; }
.who .wn { font-family: $font-cn-serif; font-size: 28rpx; font-weight: 600; }
.who .wr { font-size: 21rpx; color: $gold-deep; border: 1rpx solid $hair-s; padding: 4rpx 16rpx; border-radius: 40rpx; }
.scroll { flex: 1; min-height: 0; height: 0; } /* height:0+flex:1：压住 flex 子项 min-height:auto，内容长时才在 scroll-view 内滚，footer 恒吸底 */
.pad { padding: 8rpx 40rpx 40rpx; }
.empty { text-align: center; color: $ink-3; font-size: 24rpx; padding: 60rpx 0; }

/* 两栏：>750px（iPad 横屏）左宝妈右宝宝，窄屏纵向堆叠 */
.cols { display: flex; flex-direction: column; gap: 24rpx; }
.col { min-width: 0; }
@media screen and (min-width: 750px) {
  .cols { flex-direction: row; align-items: flex-start; }
  .col-mom { flex: 5; }
  .col-baby { flex: 6; }
}

.ct1 { font-family: $font-cn-serif; font-size: 31rpx; font-weight: 600; margin-bottom: 20rpx; }
.ct1 .sub { font-size: 21rpx; color: $ink-3; font-weight: 400; margin-left: 14rpx; }

/* 宝妈体征输入 */
.vitals { display: flex; flex-wrap: wrap; gap: 16rpx; margin-bottom: 22rpx; }
.vi { width: calc(50% - 8rpx); box-sizing: border-box; }
.vl { display: block; font-size: 21rpx; color: $ink-2; margin-bottom: 8rpx; }
.vin { border: 1rpx solid $hair-s; border-radius: 20rpx; padding: 12rpx 20rpx; font-size: 27rpx; background: $paper; }
.vin.full { width: 100%; box-sizing: border-box; }
.vin.mid { flex: 1; text-align: center; }

/* chip 单选组 */
.cgrp { margin-bottom: 20rpx; }
.gl { display: block; font-size: 21rpx; color: $ink-2; margin-bottom: 10rpx; }
.chips { display: flex; flex-wrap: wrap; gap: 12rpx; }
.chip { font-size: 23rpx; color: $ink-2; border: 1rpx solid $hair; padding: 10rpx 22rpx; border-radius: 40rpx; background: $paper; }
.chip.on { color: #fff; background: linear-gradient(135deg, #E9D4A4, #9C7838); border-color: transparent; }
.note-warn { font-size: 22rpx; color: #A3582D; background: rgba(224,180,140,.16); border: 1rpx solid #E0B48C; border-radius: 20rpx; padding: 14rpx 22rpx; margin-bottom: 20rpx; }

/* 照片 */
.photos { display: flex; flex-wrap: wrap; gap: 14rpx; }
.photos .ph { width: 120rpx; height: 120rpx; border-radius: 20rpx; border: 1rpx solid $hair; }
.photos .ph.add { display: flex; align-items: center; justify-content: center; font-size: 22rpx; color: $gold-deep; background: rgba(231,212,172,.18); border: 1rpx dashed $hair-s; }
.photos.sm .ph { width: 88rpx; height: 88rpx; }

/* 宝宝 tab + 快捷按钮 */
.btabs { display: flex; flex-wrap: wrap; gap: 12rpx; margin-bottom: 20rpx; }
.btab { font-size: 24rpx; color: $ink-2; border: 1rpx solid $hair; padding: 10rpx 26rpx; border-radius: 40rpx; background: $paper; }
.btab.on { color: $gold-deep; border-color: $hair-s; background: rgba(231,212,172,.28); font-weight: 600; }
.quick { display: flex; flex-wrap: wrap; gap: 14rpx; margin-bottom: 8rpx; }
.qbtn { font-size: 25rpx; color: $gold-deep; border: 1rpx solid $hair-s; padding: 16rpx 30rpx; border-radius: 24rpx; background: $paper; }

/* 开放睡眠段横条 */
.sleepbar { display: flex; align-items: center; background: rgba(110,139,106,.12); border: 1rpx solid rgba(110,139,106,.3); border-radius: 20rpx; padding: 14rpx 22rpx; margin-bottom: 18rpx; }
.sleepbar .st { flex: 1; font-size: 23rpx; color: #577053; }
.sleepbar .sbtn { font-size: 22rpx; color: #fff; background: #6E8B6A; padding: 8rpx 22rpx; border-radius: 40rpx; }

/* 待提交列表 */
.pend { border-top: 1rpx solid $hair; margin-top: 22rpx; padding-top: 18rpx; }
.pt { font-size: 23rpx; color: $ink-2; margin-bottom: 12rpx; }
.pe { display: flex; align-items: flex-start; padding: 16rpx 0; border-bottom: 1rpx solid $hair; }
.pe:last-child { border-bottom: 0; }
.pinfo { flex: 1; min-width: 0; }
.pk { font-family: $font-cn-serif; font-size: 26rpx; font-weight: 600; }
.pk .pb { font-size: 21rpx; color: $ink-3; font-weight: 400; }
.ps { display: block; font-size: 22rpx; color: $ink-2; margin: 6rpx 0 8rpx; }
.pdel { font-size: 21rpx; color: #A3582D; border: 1rpx solid #E0B48C; padding: 8rpx 18rpx; border-radius: 40rpx; margin-left: 16rpx; flex-shrink: 0; }

/* 底部主按钮 */
.footer { padding: 16rpx 40rpx calc(env(safe-area-inset-bottom) + 20rpx); background: rgba(251,247,240,.96); border-top: 1rpx solid $hair; }
.mainbtn { text-align: center; color: #fff; font-size: 30rpx; letter-spacing: 4rpx; background: linear-gradient(135deg, #E9D4A4, #9C7838); padding: 24rpx 0; border-radius: 60rpx; box-shadow: 0 16rpx 40rpx -20rpx rgba(140,106,54,.6); }
.mainbtn.dis { opacity: .55; }
@media screen and (min-width: 750px) { .mainbtn { max-width: 640px; margin: 0 auto; } }

/* 半屏弹层（自实现） */
.wb-mask { position: fixed; left: 0; top: 0; right: 0; bottom: 0; background: rgba(39,33,25,.45); z-index: 1000; display: flex; align-items: flex-end; justify-content: center; }
.sheet { width: 100%; max-width: 640px; box-sizing: border-box; background: $ivory; border-radius: 44rpx 44rpx 0 0; padding: 28rpx 36rpx calc(env(safe-area-inset-bottom) + 32rpx); max-height: 80vh; overflow-y: auto; }
@media screen and (min-width: 750px) { .wb-mask { align-items: center; } .sheet { border-radius: 44rpx; } }
.sh { display: flex; align-items: center; margin-bottom: 24rpx; }
.sht { font-family: $font-cn-serif; font-size: 30rpx; font-weight: 600; }
.shx { margin-left: auto; font-size: 30rpx; color: $ink-3; padding: 8rpx 16rpx; }
.stepper { display: flex; align-items: center; gap: 16rpx; margin-top: 14rpx; }
.stp { font-size: 24rpx; color: $gold-deep; border: 1rpx solid $hair-s; padding: 10rpx 26rpx; border-radius: 40rpx; background: $paper; }
.bigrow { display: flex; gap: 20rpx; margin: 10rpx 0 6rpx; }
.big { flex: 1; text-align: center; font-family: $font-cn-serif; font-size: 34rpx; font-weight: 600; color: #fff; background: linear-gradient(135deg, #E9D4A4, #9C7838); border-radius: 28rpx; padding: 34rpx 0; }
.big.alt { background: #6E8B6A; }
.big .bs { display: block; font-size: 20rpx; font-weight: 400; opacity: .85; margin-top: 8rpx; letter-spacing: 2rpx; }
.sbm { text-align: center; color: #fff; font-size: 28rpx; letter-spacing: 4rpx; background: linear-gradient(135deg, #E9D4A4, #9C7838); padding: 22rpx 0; border-radius: 60rpx; margin-top: 26rpx; }

.demo-flag { position: fixed; top: calc(env(safe-area-inset-top) + 10rpx); left: 50%; transform: translateX(-50%); z-index: 999; font-size: 20rpx; color: #8C6A36; background: rgba(231,212,172,.92); border: 1rpx solid rgba(184,148,90,.42); padding: 4rpx 16rpx; border-radius: 40rpx; box-shadow: 0 4rpx 16rpx -10rpx rgba(74,56,24,.4); }
</style>

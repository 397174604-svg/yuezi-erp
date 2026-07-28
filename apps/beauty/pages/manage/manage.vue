<template>
  <view class="screen">
    <view class="demo-flag">演示数据</view>
    <view class="dhead">
      <text class="back" @tap="back">‹</text>
      <text class="title">{{ cfg ? cfg.title : '管理' }}</text>
      <text v-if="cfg && (cfg.kind === 'list' || cfg.kind === 'storeList')" class="act" @tap="openCreate">{{ cfg.addLabel || '新增' }}</text>
    </view>

    <scroll-view scroll-y class="scroll">
      <view class="pad">
        <view v-if="loading" class="hint">加载中…</view>
        <view v-else-if="!cfg" class="hint">加载失败，请重试</view>

        <!-- 列表型：人员 / 话术 -->
        <view v-else-if="cfg.kind === 'list'" class="yz-card">
          <view class="lrow" v-for="row in cfg.rows" :key="row.id">
            <view class="linfo">
              <text class="lt">{{ row.cells[0] }}</text>
              <text class="lm">{{ row.cells.slice(1).join(' · ') }}</text>
            </view>
            <view class="ops">
              <text v-if="key === 'staff'" class="op" @tap="pickRole(row)">改角色</text>
              <text v-if="key === 'staff'" :class="['op', row.status === '在职' ? 'danger' : 'on']" @tap="toggle(row)">{{ row.status === '在职' ? '离职' : '复职' }}</text>
              <text v-if="key === 'scripts'" :class="['op', row.status === '启用' ? 'danger' : 'on']" @tap="toggle(row)">{{ row.status === '启用' ? '停用' : '启用' }}</text>
              <text v-if="key === 'scripts'" class="op danger" @tap="removeRow(row)">删除</text>
            </view>
          </view>
          <view v-if="!cfg.rows.length" class="hint">暂无数据，点右上角新增</view>
        </view>

        <!-- 库房入出库 -->
        <view v-else-if="cfg.kind === 'stock'" class="yz-card">
          <view class="lrow" v-for="row in cfg.rows" :key="row.itemId">
            <view class="linfo">
              <text class="lt">{{ row.cells[0] }}</text>
              <text class="lm">库存 {{ row.qty }} · 预警 {{ row.cells[2] }} <text v-if="row.low" class="warn">⚠ 低库存</text></text>
            </view>
            <view class="ops">
              <text class="op on" @tap="stockAction(row, 'inbound')">入库</text>
              <text class="op danger" @tap="stockAction(row, 'outbound')">出库</text>
            </view>
          </view>
          <view v-if="!cfg.rows.length" class="hint">暂无库存数据</view>
        </view>

        <!-- 会员等级折扣设置 -->
        <view v-else-if="cfg.kind === 'levels'" class="yz-card">
          <view class="lrow" v-for="row in cfg.rows" :key="row.name">
            <view class="linfo"><text class="lt">{{ row.cells[0] }}</text><text class="lm">当前 {{ row.cells[1] }}（收银按此自动算价）</text></view>
            <view class="ops"><text class="op" @tap="editDiscount(row)">改折扣</text></view>
          </view>
        </view>

        <!-- 多店列表：店铺管理（列表+编辑+新增）-->
        <view v-else-if="cfg.kind === 'storeList'" class="yz-card">
          <view class="lrow" v-for="row in cfg.rows" :key="row.id">
            <view class="linfo">
              <text class="lt">{{ row.cells[0] }}</text>
              <text class="lm">{{ row.cells[1] }}</text>
            </view>
            <view class="ops"><text class="op" @tap="editStore(row)">编辑</text></view>
          </view>
          <view v-if="!cfg.rows.length" class="hint">暂无门店，点右上角新增</view>
        </view>

        <!-- 表单型：店铺管理 -->
        <view v-else-if="cfg.kind === 'form'" class="yz-card form">
          <view class="frow"><text class="fl">店铺名称</text><input class="fi" v-model="cfg.entity.name" disabled /></view>
          <view class="frow"><text class="fl">负责人</text><input class="fi" v-model="cfg.entity.manager" placeholder="负责人" /></view>
          <view class="frow"><text class="fl">电话</text><input class="fi" v-model="cfg.entity.phone" placeholder="联系电话" /></view>
          <view class="frow"><text class="fl">地址</text><input class="fi" v-model="cfg.entity.address" placeholder="店铺地址" /></view>
          <view class="frow"><text class="fl">行业类型</text><input class="fi" v-model="cfg.entity.industry" placeholder="如 产康 / 月子" /></view>
          <view class="save" :class="{ busy: submitting }" @tap="saveStore">{{ submitting ? '保存中…' : '保存' }}</view>
        </view>
      </view>
    </scroll-view>

    <!-- 新增表单浮层 -->
    <view v-if="formOpen" class="mask" @tap="formOpen = false">
      <view class="sheet" @tap.stop>
        <text class="sht">{{ formTitle }}</text>
        <view class="frow" v-for="f in formFields" :key="f.k">
          <text class="fl">{{ f.l }}</text>
          <picker v-if="f.type === 'picker'" mode="selector" :range="f.options" @change="e => formModel[f.k] = f.options[e.detail.value]">
            <view class="fi pick">{{ formModel[f.k] || ('选择' + f.l) }}</view>
          </picker>
          <input v-else class="fi" v-model="formModel[f.k]" :placeholder="f.l" />
        </view>
        <view class="sbtns">
          <text class="sb" @tap="formOpen = false">取消</text>
          <text class="sb primary" :class="{ busy: submitting }" @tap="saveForm">{{ submitting ? '提交中…' : '确定' }}</text>
        </view>
      </view>
    </view>
  </view>
</template>
<script>
import { loadManage, manageAction } from '@/common/remote.js'
export default {
  data() { return { key: '', cfg: null, loading: true, submitting: false, formOpen: false, formTitle: '', formAction: '', formModel: {}, formFields: [] } },
  async onLoad(q) { this.key = q.key; await this.refresh() },
  methods: {
    back() { uni.navigateBack() },
    async refresh() { this.loading = true; this.cfg = await loadManage(this.key); this.loading = false },
    async run(action, payload, okMsg) {
      if (this.submitting) return
      this.submitting = true
      const r = await manageAction(this.key, action, payload)
      this.submitting = false
      if (r.ok) { uni.showToast({ title: okMsg || '已完成', icon: 'none' }); this.formOpen = false; await this.refresh() }
      else uni.showToast({ title: r.msg || '操作失败', icon: 'none' })
    },
    busy() { if (this.submitting) { uni.showToast({ title: '操作进行中，请稍候', icon: 'none' }); return true } return false },
    storeFields() { return [{ k: 'name', l: '店铺名称' }, { k: 'manager', l: '负责人' }, { k: 'phone', l: '电话' }, { k: 'region', l: '所在地区' }, { k: 'address', l: '地址' }, { k: 'industry', l: '行业类型' }, { k: 'status', l: '店铺状态', type: 'picker', options: ['正常', '停用'] }, { k: 'sortWeight', l: '排序权重' }] },
    openCreate() {
      if (this.busy()) return
      this.formModel = {}; this.formAction = 'create'
      if (this.key === 'staff') {
        this.formTitle = '新增员工'; this.formFields = [{ k: 'name', l: '姓名' }, { k: 'phone', l: '电话' }, { k: 'department', l: '部门' }, { k: 'position', l: '职位' }, { k: 'wxNotify', l: '微信通知', type: 'picker', options: ['关', '开'] }]
        if ((this.cfg.roleOptions || []).length) this.formFields.splice(2, 0, { k: 'role', l: '角色', type: 'picker', options: this.cfg.roleOptions }) // 空字典则不渲染坏 picker
      } else if (this.key === 'store') {
        this.formTitle = '新增门店'; this.formFields = this.storeFields()
      } else { this.formTitle = '新增话术'; this.formFields = [{ k: 'scene', l: '场景' }, { k: 'title', l: '标题' }, { k: 'content', l: '内容' }] }
      this.formOpen = true
    },
    editStore(row) {
      if (this.busy()) return
      this.formAction = 'edit'; this.formTitle = '编辑门店'
      this.formModel = { id: row.id, name: row.name, manager: row.manager, phone: row.phone, address: row.address, industry: row.industry, region: row.region, status: row.status, sortWeight: row.sortWeight }
      this.formFields = this.storeFields(); this.formOpen = true
    },
    async saveForm() {
      const m = this.formModel
      if (this.key === 'staff' && (!(m.name || '').trim() || !(m.phone || '').trim())) return uni.showToast({ title: '姓名、电话必填', icon: 'none' })
      if (this.key === 'scripts' && !(m.title || '').trim()) return uni.showToast({ title: '标题必填', icon: 'none' })
      if (this.key === 'store' && !(m.name || '').trim()) return uni.showToast({ title: '店铺名称必填', icon: 'none' })
      const payload = { ...m } // trim 收口：避免纯空白绕过校验入库
      for (const f of ['name', 'phone', 'title', 'scene', 'manager', 'address', 'industry', 'position', 'region', 'department']) if (typeof payload[f] === 'string') payload[f] = payload[f].trim()
      await this.run(this.formAction, payload, this.formAction === 'edit' ? '已保存' : '已新增')
    },
    pickRole(row) {
      if (this.busy()) return
      const opts = this.cfg.roleOptions || []
      if (!opts.length) return uni.showToast({ title: '无可选角色', icon: 'none' })
      uni.showActionSheet({ itemList: opts, success: e => this.run('role', { id: row.id, role: opts[e.tapIndex] }, '角色已更新') })
    },
    async toggle(row) {
      if (this.busy()) return
      const verb = (this.key === 'staff' ? (row.status === '在职' ? '离职' : '复职') : (row.status === '启用' ? '停用' : '启用'))
      const label = this.key === 'scripts' ? (row.title || row.cells[1] || row.cells[0]) : row.cells[0] // 话术显示标题而非场景
      const ok = await new Promise(r => uni.showModal({ title: '确认' + verb, content: label, success: e => r(e.confirm), fail: () => r(false) }))
      if (ok) await this.run('toggle', { id: row.id, status: row.status }, verb + '成功')
    },
    async removeRow(row) {
      if (this.busy()) return
      const ok = await new Promise(r => uni.showModal({ title: '确认删除', content: row.title || row.cells[1] || '该话术', success: e => r(e.confirm), fail: () => r(false) }))
      if (ok) await this.run('remove', { id: row.id }, '已删除')
    },
    async stockAction(row, dir) {
      if (this.busy()) return
      const label = dir === 'inbound' ? '入库' : '出库'
      const res = await new Promise(r => uni.showModal({ title: label + '：' + row.cells[0], editable: true, placeholderText: '数量', success: e => r(e.confirm ? e.content : null), fail: () => r(null) }))
      const qty = Number(res)
      if (!Number.isInteger(qty) || qty <= 0) { if (res !== null) uni.showToast({ title: '请输入正整数', icon: 'none' }); return }
      if (qty > 1000000) return uni.showToast({ title: '单次数量过大（≤100万）', icon: 'none' })
      await this.run(dir, { itemId: row.itemId, qty }, label + ' ' + qty + ' 成功')
    },
    async editDiscount(row) {
      if (this.busy()) return
      const res = await new Promise(r => uni.showModal({ title: '设置「' + row.name + '」折扣', content: String(row.discount), editable: true, placeholderText: '折扣率 0~1（0.8=8折，1=不打折）', success: e => r(e.confirm ? e.content : null), fail: () => r(null) }))
      if (res === null) return
      const d = Number(res)
      if (!(d > 0 && d <= 1)) return uni.showToast({ title: '折扣率须为 0~1', icon: 'none' })
      await this.run('setDiscount', { name: row.name, discount: d }, '已设置')
    },
    async saveStore() {
      const e = this.cfg.entity
      if (!e.id) return uni.showToast({ title: '暂无可编辑门店', icon: 'none' }) // 防 /stores/undefined
      await this.run('edit', { id: e.id, manager: e.manager, phone: e.phone, address: e.address, industry: e.industry }, '已保存')
    },
  },
}
</script>
<style lang="scss" scoped>
.screen { display: flex; flex-direction: column; height: 100vh; }
.dhead { display: flex; align-items: center; padding: 28rpx 40rpx 12rpx; }
.back { font-size: 48rpx; color: $gold-deep; width: 56rpx; } .title { font-family: $font-cn-serif; font-size: 32rpx; font-weight: 600; }
.act { margin-left: auto; font-size: 24rpx; color: #fff; background: linear-gradient(135deg,#E9D4A4,#9C7838); padding: 12rpx 26rpx; border-radius: 40rpx; }
.scroll { flex: 1; } .pad { padding: 8rpx 40rpx 60rpx; }
.hint { text-align: center; color: $ink-3; font-size: 24rpx; padding: 60rpx 0; }
.lrow { display: flex; align-items: center; padding: 24rpx 0; border-bottom: 1rpx solid $hair; } .lrow:last-child { border-bottom: 0; }
.linfo { flex: 1; } .lt { font-family: $font-cn-serif; font-size: 28rpx; font-weight: 600; } .lm { display: block; font-size: 22rpx; color: $ink-3; margin-top: 8rpx; } .warn { color: #A3582D; margin-left: 8rpx; }
.ops { display: flex; gap: 14rpx; flex-shrink: 0; }
.op { font-size: 22rpx; color: $gold-deep; border: 1rpx solid $hair-s; padding: 12rpx 22rpx; border-radius: 40rpx; } .op.danger { color: #A3582D; border-color: #E0B48C; } .op.on { color: #577053; border-color: #bcd; }
.form .frow, .sheet .frow { display: flex; align-items: center; padding: 22rpx 0; border-bottom: 1rpx solid $hair; }
.fl { width: 150rpx; font-size: 25rpx; color: $ink-2; } .fi { flex: 1; font-size: 26rpx; border: 1rpx solid $hair; border-radius: 12rpx; padding: 14rpx 18rpx; } .fi.pick { color: $ink; }
.save { margin-top: 32rpx; text-align: center; color: #fff; background: linear-gradient(135deg,#E9D4A4,#9C7838); padding: 24rpx; border-radius: 60rpx; font-size: 28rpx; } .save.busy { opacity: .6; }
.mask { position: fixed; inset: 0; background: rgba(43,38,32,.45); display: flex; align-items: flex-end; z-index: 50; }
.sheet { width: 100%; background: $ivory; border-radius: 36rpx 36rpx 0 0; padding: 36rpx 40rpx 48rpx; }
.sht { font-family: $font-cn-serif; font-size: 30rpx; font-weight: 600; display: block; margin-bottom: 12rpx; }
.sbtns { display: flex; gap: 20rpx; margin-top: 32rpx; } .sb { flex: 1; text-align: center; padding: 22rpx; border-radius: 60rpx; font-size: 27rpx; border: 1rpx solid $hair; color: $ink-2; } .sb.primary { color: #fff; background: linear-gradient(135deg,#E9D4A4,#9C7838); border: none; } .sb.busy { opacity: .6; }

.demo-flag { position: fixed; top: calc(env(safe-area-inset-top) + 10rpx); left: 50%; transform: translateX(-50%); z-index: 999; font-size: 20rpx; color: #8C6A36; background: rgba(231,212,172,.92); border: 1rpx solid rgba(184,148,90,.42); padding: 4rpx 16rpx; border-radius: 40rpx; box-shadow: 0 4rpx 16rpx -10rpx rgba(74,56,24,.4); }
</style>

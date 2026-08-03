<template>
  <div class="schedule-workbench">
    <section class="hero-panel">
      <div><div class="eyebrow"><i class="el-icon-date" /> 预约与排班 · {{ config.featureId }}</div><h1>{{ config.title }}</h1><p>{{ config.description }}</p></div>
      <div class="hero-actions"><el-button icon="el-icon-refresh" :loading="loading" @click="loadAll">刷新</el-button><el-button v-if="!isOnlineBoard && activeTab === 'appointments'" type="primary" icon="el-icon-plus" @click="openCreate">新建预约</el-button><el-button v-if="!isOnlineBoard && activeTab === 'schedules'" type="primary" icon="el-icon-plus" @click="openSchedule">新增排班</el-button><el-tag v-if="isOnlineBoard" type="success" effect="dark">多渠道资源看板</el-tag></div>
    </section>

    <el-tabs v-model="activeTab" @tab-click="loadCurrent"><el-tab-pane :label="isOnlineBoard ? '在线预约资源' : '预约列表'" name="appointments" /><el-tab-pane v-if="!isOnlineBoard && canViewSchedules" label="人员排班" name="schedules" /></el-tabs>

    <el-card shadow="never" class="filter-card"><el-form :inline="true" size="small"><el-form-item label="门店"><el-select v-model="filters.storeId" :disabled="!isAllStores" clearable placeholder="全部可见门店"><el-option v-for="store in filterStores" :key="store.id" :label="store.name" :value="store.id" /></el-select></el-form-item><el-form-item label="日期"><el-date-picker v-model="filters.date" type="date" value-format="yyyy-MM-dd" placeholder="选择日期" /></el-form-item><template v-if="isOnlineBoard"><el-form-item label="技师"><el-select v-model="filters.technician" clearable filterable placeholder="全部技师"><el-option v-for="staff in options.staff" :key="staff.id" :label="staff.name" :value="staff.name" /></el-select></el-form-item><el-form-item label="渠道"><el-select v-model="filters.channel" clearable placeholder="全部渠道"><el-option v-for="channel in channelOptions" :key="channel" :label="channel" :value="channel" /></el-select></el-form-item></template><el-form-item><el-button type="primary" @click="loadCurrent">查询</el-button><el-button @click="resetFilters">重置</el-button></el-form-item></el-form></el-card>

    <el-alert v-if="loadError" class="load-error" type="error" :closable="false" show-icon :title="loadError" />
    <el-card shadow="never" class="table-card">
      <div slot="header" class="table-heading"><div><h2>{{ isOnlineBoard ? '技师 / 时段 / 渠道占用看板' : (activeTab === 'appointments' ? '预约资源与状态' : '人员档期与容量') }}</h2><p>{{ isOnlineBoard ? '汇总当前门店在线预约资源，按技师、时段和来源渠道区分，不在本页修改排班。' : '预约、设备、床位和人员班次均按顶栏当前门店管理。' }}</p></div><div class="table-actions"><el-button v-if="activeTab === 'appointments' && !isOnlineBoard" size="small" icon="el-icon-close" :disabled="!cancellableSelection.length" @click="cancelSelectedAppointments">取消所选预约</el-button><el-tag type="success" effect="plain">{{ isOnlineBoard ? '只读资源看板' : '预约业务域' }}</el-tag></div></div>
      <el-table v-loading="loading" :data="filteredRows" border stripe @selection-change="handleSelectionChange"><el-table-column v-if="activeTab === 'appointments' && !isOnlineBoard" type="selection" width="42" /><template v-if="activeTab === 'appointments'"><el-table-column prop="appointmentNo" label="预约单号" min-width="150" /><el-table-column prop="customerName" label="客户" min-width="100" /><el-table-column prop="store" label="门店" min-width="140" /><el-table-column prop="serviceCategory" label="项目分类" min-width="105" /><el-table-column prop="serviceItem" label="服务项目" min-width="150" /><el-table-column prop="appointmentDate" label="预约日期" min-width="110" /><el-table-column prop="appointmentPeriod" label="时段" min-width="110" /><el-table-column prop="technician" label="服务人员" min-width="105" /><el-table-column prop="servicePlace" label="预约资源" min-width="170" show-overflow-tooltip /><el-table-column v-if="isOnlineBoard" prop="channel" label="预约渠道" min-width="110" /><el-table-column prop="serviceStatus" :label="isOnlineBoard ? '占用状态' : '状态'" min-width="100"><template slot-scope="scope"><el-tag size="mini" :type="statusType(scope.row.serviceStatus)">{{ scope.row.serviceStatus }}</el-tag></template></el-table-column><el-table-column v-if="!isOnlineBoard" label="操作" width="100" fixed="right"><template slot-scope="scope"><el-button type="text" :disabled="!canCancelAppointment(scope.row)" @click="cancelAppointment(scope.row)">取消预约</el-button></template></el-table-column></template><template v-else><el-table-column prop="staffName" label="人员" min-width="110" /><el-table-column prop="store" label="门店" min-width="140" /><el-table-column prop="scheduleDate" label="日期" min-width="110" /><el-table-column prop="shiftName" label="班次" min-width="100" /><el-table-column prop="startTime" label="开始" min-width="90" /><el-table-column prop="endTime" label="结束" min-width="90" /><el-table-column prop="maxBookings" label="服务容量" min-width="90" /><el-table-column prop="bookedCount" label="已预约" min-width="90" /><el-table-column prop="shiftStatus" label="排班状态" min-width="100"><template slot-scope="scope"><el-tag size="mini" :type="statusType(scope.row.shiftStatus)">{{ scope.row.shiftStatus }}</el-tag></template></el-table-column><el-table-column prop="remark" label="备注" min-width="140" show-overflow-tooltip /><el-table-column label="操作" width="160" fixed="right"><template slot-scope="scope"><el-button type="text" @click="openSchedule(scope.row)">编辑</el-button><el-button type="text" :disabled="scope.row.shiftStatus === '停诊'" @click="cancelSchedule(scope.row)">取消班次</el-button><el-button type="text" class="danger-link" @click="deleteSchedule(scope.row)">删除</el-button></template></el-table-column></template></el-table>
      <div v-if="!loading && !filteredRows.length" class="empty-state">当前条件下没有可见记录。</div>
    </el-card>

    <el-dialog title="新建预约" :visible.sync="dialogVisible" width="720px" @closed="resetForm"><el-alert title="保存会校验当前门店、客户、服务人员、日期与时段冲突；设备和床位作为预约资源一并记录。" type="info" :closable="false" /><el-form label-position="top" class="booking-form"><el-row :gutter="14"><el-col :span="12"><el-form-item label="门店" required><el-select v-model="form.storeId" disabled class="full"><el-option v-for="store in writeStores" :key="store.id" :label="store.name" :value="store.id" /></el-select></el-form-item></el-col><el-col :span="12"><el-form-item label="客户" required><el-select v-model="form.customerId" filterable class="full"><el-option v-for="customer in availableCustomers" :key="customer.id" :label="customer.name + ' · ' + (customer.mobile || customer.phone || '')" :value="customer.id" /></el-select></el-form-item></el-col><el-col :span="12"><el-form-item label="服务人员" required><el-select v-model="form.technicianStaffId" filterable class="full"><el-option v-for="staff in availableStaff" :key="staff.id" :label="staff.name" :value="staff.id" /></el-select></el-form-item></el-col><el-col :span="12"><el-form-item label="预约日期" required><el-date-picker v-model="form.appointmentDate" type="date" value-format="yyyy-MM-dd" :picker-options="futureDateOptions" class="full" /></el-form-item></el-col><el-col :span="12"><el-form-item label="服务项目" required><el-select v-model="form.serviceItem" filterable class="full" @change="syncServiceCategory"><el-option-group v-for="group in serviceProjectGroups" :key="group.label" :label="group.label"><el-option v-for="project in group.options" :key="project" :label="project" :value="project" /></el-option-group></el-select></el-form-item></el-col><el-col :span="12"><el-form-item label="预约时段" required><el-select v-model="form.appointmentPeriod" class="full"><el-option v-for="period in appointmentPeriods" :key="period" :label="period" :value="period" /></el-select></el-form-item></el-col><el-col :span="12"><el-form-item label="预约设备"><el-select v-model="form.reservedDevices" multiple collapse-tags filterable class="full"><el-option v-for="device in deviceOptions" :key="device" :label="device" :value="device" /></el-select></el-form-item></el-col><el-col :span="12"><el-form-item label="预约床位"><el-select v-model="form.reservedBeds" multiple collapse-tags filterable class="full"><el-option v-for="bed in bedOptions" :key="bed" :label="bed" :value="bed" /></el-select></el-form-item></el-col><el-col :span="12"><el-form-item label="服务次数"><el-input-number v-model="form.serviceCount" :min="1" :max="99" class="full" /></el-form-item></el-col><el-col :span="12"><el-form-item label="服务地点"><el-input v-model.trim="form.locationNote" maxlength="60" placeholder="例如 产康室 2" /></el-form-item></el-col></el-row><el-form-item label="备注"><el-input v-model.trim="form.remark" type="textarea" maxlength="200" /></el-form-item></el-form><span slot="footer"><el-button @click="dialogVisible = false">取消</el-button><el-button type="primary" :loading="saving" @click="saveAppointment">保存预约</el-button></span></el-dialog>

    <el-dialog :title="editingSchedule ? '编辑排班' : '新增排班'" :visible.sync="scheduleDialogVisible" width="620px" @closed="resetScheduleForm"><el-form label-position="top"><el-row :gutter="14"><el-col :span="12"><el-form-item label="门店" required><el-select v-model="scheduleForm.storeId" disabled class="full"><el-option v-for="store in writeStores" :key="store.id" :label="store.name" :value="store.id" /></el-select></el-form-item></el-col><el-col :span="12"><el-form-item label="员工" required><el-select v-model="scheduleForm.staffId" filterable class="full"><el-option v-for="staff in scheduleStaff" :key="staff.id" :label="staff.name" :value="staff.id" /></el-select></el-form-item></el-col><el-col :span="12"><el-form-item label="排班日期" required><el-date-picker v-model="scheduleForm.scheduleDate" type="date" value-format="yyyy-MM-dd" class="full" /></el-form-item></el-col><el-col :span="12"><el-form-item label="班次" required><el-select v-model="scheduleForm.shiftName" class="full" @change="applyShiftTime"><el-option v-for="shift in shiftOptions" :key="shift.name" :label="shift.name" :value="shift.name" /></el-select></el-form-item></el-col><el-col :span="12"><el-form-item label="开始时间" required><el-time-select v-model="scheduleForm.startTime" :picker-options="{ start: '06:00', step: '00:30', end: '23:00' }" class="full" /></el-form-item></el-col><el-col :span="12"><el-form-item label="结束时间" required><el-time-select v-model="scheduleForm.endTime" :picker-options="{ start: '06:30', step: '00:30', end: '23:30', minTime: scheduleForm.startTime }" class="full" /></el-form-item></el-col><el-col :span="12"><el-form-item label="服务容量" required><el-input-number v-model="scheduleForm.maxBookings" :min="0" :max="99" class="full" /></el-form-item></el-col><el-col :span="12"><el-form-item label="排班状态"><el-select v-model="scheduleForm.shiftStatus" class="full"><el-option v-for="status in scheduleStatuses" :key="status" :label="status" :value="status" /></el-select></el-form-item></el-col></el-row><el-form-item label="备注"><el-input v-model.trim="scheduleForm.remark" type="textarea" maxlength="200" /></el-form-item></el-form><span slot="footer"><el-button @click="scheduleDialogVisible = false">取消</el-button><el-button type="primary" :loading="saving" @click="saveSchedule">保存排班</el-button></span></el-dialog>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import { getCustomerModuleData, saveCustomerModuleRecord } from '@/api/erp-customer'
import { getMvpOptions } from '@/api/erp-mvp'
import { getRehabModuleData, getRehabOptions, performRehabModuleAction, saveRehabModuleRecord } from '@/api/erp-rehab'
import { getSchedulePageConfig } from '@/config/schedule-pages'

const SERVICE_PROJECT_GROUPS = [
  { label: '产后类', options: ['产后基础评估', '疤痕松解', '淋巴疏通', '臀部塑形', '基础套餐护理项目', '修养套餐护理项目', '修复套餐康复项目', '女王套餐专属护理', '总统套餐专属护理'] },
  { label: '产康服务', options: ['盆底肌修复', '腹直肌修复', '腺体修复', '体质调理', '修复7+21疗程'] },
  { label: '护理服务', options: ['妈妈基础护理', '宝宝基础护理', '母乳喂养指导'] },
  { label: '膳食服务', options: ['月子餐营养评估', '个性化加餐'] },
  { label: '客房服务', options: ['入住环境准备', '客房深度清洁'] },
  { label: '增值服务', options: ['满月照预约', '产后康复复测'] },
  { label: '软硬件服务', options: ['设备理疗预约', '智能体测'] },
  { label: '大礼包', options: ['入住大礼包领取', '满月礼包领取'] },
  { label: '科研肌肤', options: ['肌肤检测', '产后肌肤管理'] }
]
const DEVICE_OPTIONS = ['人体雕刻家', '汤姆森颈压床', '绛私细胞焕活仪', '艾灸仪', '暖骨仪', '红外线理疗仪', '太空舱', '能量氧疗舱', '通泽医疗盆底肌', '通泽医疗腹直肌电刺激']
const BED_OPTIONS = [...Array.from({ length: 10 }, (_, index) => `VIP${index + 1}`), '洗头床']
const SHIFT_OPTIONS = [
  { name: '早班', start: '08:00', end: '12:00' },
  { name: '午班', start: '12:00', end: '18:00' },
  { name: '晚班', start: '18:00', end: '22:00' }
]

export default {
  name: 'ScheduleWorkbench',
  data() {
    return {
      activeTab: 'appointments', loading: false, saving: false, loadError: '',
      rows: { appointments: [], schedules: [] }, options: { stores: [], customers: [], staff: [] },
      filters: { storeId: '', date: '', technician: '', channel: '' }, dialogVisible: false, form: {},
      appointmentSelection: [], scheduleDialogVisible: false, editingSchedule: false, scheduleForm: {},
      serviceProjectGroups: SERVICE_PROJECT_GROUPS, deviceOptions: DEVICE_OPTIONS, bedOptions: BED_OPTIONS,
      appointmentPeriods: ['08:00-09:00', '09:00-10:00', '10:00-11:00', '11:00-12:00', '14:00-15:00', '15:00-16:00', '16:00-17:00', '17:00-18:00', '19:00-20:00'],
      shiftOptions: SHIFT_OPTIONS, scheduleStatuses: ['出勤', '休息', '请假', '停诊'],
      futureDateOptions: { disabledDate: time => time.getTime() < new Date().setHours(0, 0, 0, 0) }
    }
  },
  computed: {
    ...mapGetters(['permissions', 'currentStoreId']),
    businessStoreId() { return String(this.currentStoreId || 'all') },
    isAllStores() { return this.businessStoreId === 'all' },
    businessStoreValue() {
      const store = this.options.stores.find(item => String(item.id) === this.businessStoreId)
      return store ? store.id : this.businessStoreId
    },
    writeStores() { return this.isAllStores ? [] : this.options.stores.filter(store => String(store.id) === this.businessStoreId) },
    filterStores() { return this.isAllStores ? this.options.stores : this.writeStores },
    pageTitle() { return this.$route.meta.configTitle || this.$route.meta.title.replace(/\s*★$/, '') },
    config() { return getSchedulePageConfig(this.pageTitle) },
    isOnlineBoard() { return this.config.mode === 'online-board' },
    canUseRecoveryAppointments() { return this.permissions.some(item => ['RECOVERY.VIEW', 'RECOVERY.QUERY'].includes(item)) },
    canUseCustomerAppointments() { return this.permissions.some(item => ['CUSTOMER.VIEW', 'CUSTOMER.QUERY'].includes(item)) },
    canViewSchedules() { return this.canUseRecoveryAppointments },
    channelOptions() { return [...new Set(this.rows.appointments.map(row => row.channel).filter(Boolean))] },
    currentRows() { return this.rows[this.activeTab] || [] },
    filteredRows() { return this.currentRows.filter(row => (!this.filters.storeId || String(row.storeId) === String(this.filters.storeId)) && (!this.filters.date || (row.appointmentDate || row.scheduleDate) === this.filters.date) && (!this.filters.technician || row.technician === this.filters.technician) && (!this.filters.channel || row.channel === this.filters.channel)) },
    availableCustomers() { return this.options.customers.filter(row => !this.form.storeId || String(row.storeId) === String(this.form.storeId)) },
    availableStaff() { return this.options.staff.filter(row => !this.form.storeId || String(row.storeId) === String(this.form.storeId)) },
    scheduleStaff() { return this.options.staff.filter(row => !this.scheduleForm.storeId || String(row.storeId) === String(this.scheduleForm.storeId)) },
    cancellableSelection() { return this.appointmentSelection.filter(this.canCancelAppointment) }
  },
  watch: {
    '$route.fullPath': { immediate: true, handler() { this.activeTab = this.config.defaultTab; this.loadAll() } },
    currentStoreId(value, previous) {
      if (String(value) === String(previous)) return
      this.filters.storeId = String(value || 'all') === 'all' ? '' : String(value)
      this.loadAll()
    }
  },
  methods: {
    async loadAll() { await this.loadOptions(); await this.loadCurrent() },
    async loadOptions() {
      try {
        const response = this.canUseRecoveryAppointments
          ? await getRehabOptions({ silentError: true })
          : await getMvpOptions({ silentError: true })
        const data = response.data || {}
        this.options = {
          stores: data.stores || [],
          customers: (data.customers || []).map(item => ({ ...item, storeId: item.storeId || item.store_id })),
          staff: (data.staff || []).map(item => ({ ...item, storeId: item.storeId || item.store_id }))
        }
        this.filters.storeId = this.isAllStores ? '' : this.businessStoreValue
      } catch (error) {
        this.options = { stores: [], customers: [], staff: [] }
        this.loadError = '当前账号暂时无法读取预约基础选项。'
      }
    },
    normalizeCustomerAppointment(row) {
      const appointmentAt = row.appointmentAt || row.appointment_at || row.createdAt || ''
      return {
        ...row,
        appointmentNo: row.appointmentNo || row.recordNo || `YY-${row.id}`,
        customerName: row.customerName || row.visitor || row.name,
        storeId: row.storeId || row.store_id,
        serviceItem: row.serviceItem || row.appointmentType || '到店预约',
        appointmentDate: String(appointmentAt).slice(0, 10),
        appointmentPeriod: String(appointmentAt).length > 10 ? String(appointmentAt).slice(11, 16) : '',
        technician: row.technician || row.receptionist || row.salesperson || '',
        channel: row.channel || row.source || '',
        serviceStatus: row.serviceStatus || row.arrivalStatus || row.status || '待确认'
      }
    },
    async loadCurrent() {
      this.loading = true
      this.loadError = ''
      try {
        if (this.activeTab === 'appointments' && !this.canUseRecoveryAppointments && this.canUseCustomerAppointments) {
          const response = await getCustomerModuleData('appointments', this.filters.storeId ? { storeId: this.filters.storeId } : {}, { silentError: true })
          const list = response.data && response.data.list
          this.$set(this.rows, 'appointments', Array.isArray(list) ? list.map(this.normalizeCustomerAppointment) : [])
          return
        }
        if (!this.canUseRecoveryAppointments) {
          this.$set(this.rows, this.activeTab, [])
          this.loadError = '当前角色未授权人员排班数据。'
          return
        }
        const key = this.activeTab === 'appointments' ? 'service-appointments' : 'staff-schedule-settings'
        const queryStoreId = this.filters.storeId || this.businessStoreId
        const response = await getRehabModuleData(key, queryStoreId === 'all' ? {} : { storeId: queryStoreId }, { silentError: true })
        const list = response.data && response.data.list
        this.$set(this.rows, this.activeTab, Array.isArray(list) ? list : [])
      } catch (error) {
        this.$set(this.rows, this.activeTab, [])
        this.loadError = '预约数据暂时无法加载，请稍后刷新。'
      } finally {
        this.loading = false
      }
    },
    resetFilters() { this.filters = { storeId: this.isAllStores ? '' : this.businessStoreValue, date: '', technician: '', channel: '' }; this.loadCurrent() },
    openCreate() {
      if (this.isAllStores) return this.$message.warning('全部门店仅支持汇总查询，请先在顶栏选择具体门店')
      this.form = { storeId: this.businessStoreValue, customerId: '', technicianStaffId: '', serviceCategory: '', serviceItem: '', appointmentDate: '', appointmentPeriod: '', reservedDevices: [], reservedBeds: [], serviceCount: 1, locationNote: '', remark: '' }
      this.dialogVisible = true
    },
    syncServiceCategory(project) {
      const group = this.serviceProjectGroups.find(item => item.options.includes(project))
      this.$set(this.form, 'serviceCategory', group ? group.label : '')
    },
    resetForm() { this.form = {} },
    async saveAppointment() {
      if (this.isAllStores) return this.$message.warning('全部门店仅支持汇总查询，请先在顶栏选择具体门店')
      this.form.storeId = this.businessStoreValue
      const required = ['storeId', 'customerId', 'technicianStaffId', 'serviceItem', 'appointmentDate', 'appointmentPeriod']
      if (required.some(key => !this.form[key])) return this.$message.warning('请填写门店、客户、服务人员、项目、日期和时段')
      if (!/^((?:[01]\d|2[0-3]):[0-5]\d)-((?:[01]\d|2[0-3]):[0-5]\d)$/.test(this.form.appointmentPeriod)) return this.$message.warning('预约时段格式应为 HH:mm-HH:mm')
      this.saving = true
      try {
        const resources = [
          this.form.reservedDevices.length ? `设备：${this.form.reservedDevices.join('、')}` : '',
          this.form.reservedBeds.length ? `床位：${this.form.reservedBeds.join('、')}` : '',
          this.form.locationNote ? `地点：${this.form.locationNote}` : ''
        ].filter(Boolean)
        const appointmentPayload = { ...this.form, servicePlace: resources.join('；') || '门店服务区' }
        if (this.canUseRecoveryAppointments) {
          await saveRehabModuleRecord('service-appointments', appointmentPayload)
        } else {
          const customer = this.options.customers.find(item => String(item.id) === String(this.form.customerId)) || {}
          const staff = this.options.staff.find(item => String(item.id) === String(this.form.technicianStaffId)) || {}
          await saveCustomerModuleRecord('appointments', {
            visitor: customer.name,
            mobile: customer.phone || customer.mobile,
            storeId: this.form.storeId,
            appointmentAt: `${this.form.appointmentDate} ${this.form.appointmentPeriod.split('-')[0]}:00`,
            appointmentType: this.form.serviceItem,
            receptionist: staff.name,
            remark: [appointmentPayload.servicePlace, this.form.remark].filter(Boolean).join('；')
          })
        }
        this.dialogVisible = false
        this.$message.success('预约已保存')
        await this.loadCurrent()
      } catch (error) {
        this.$message.error('预约保存失败：请检查门店、客户、人员、日期和时段。')
      } finally {
        this.saving = false
      }
    },
    handleSelectionChange(rows) { this.appointmentSelection = rows },
    canCancelAppointment(row) { return row && row.id && !['已完成', '已取消'].includes(row.serviceStatus) },
    statusType(status) {
      if (['已完成', '出勤', '已确认'].includes(status)) return 'success'
      if (['已取消', '停诊', '请假'].includes(status)) return 'info'
      if (['待服务', '已预约', '休息'].includes(status)) return 'warning'
      return ''
    },
    async cancelAppointment(row, silentSuccess = false) {
      if (this.isAllStores) return this.$message.warning('全部门店仅支持汇总查询，请先在顶栏选择具体门店')
      if (!this.canCancelAppointment(row)) return this.$message.warning('该预约当前状态不可取消')
      try {
        await this.$confirm(`确认取消预约 ${row.appointmentNo || ''}（${row.customerName || '客户'}）？`, '取消预约', { type: 'warning' })
      } catch (error) { return false }
      await performRehabModuleAction('service-appointments', '取消', { id: row.id, storeId: row.storeId || this.businessStoreValue })
      if (!silentSuccess) { this.$message.success('预约已取消，资源占用已释放'); await this.loadCurrent() }
      return true
    },
    async cancelSelectedAppointments() {
      const rows = this.cancellableSelection
      if (!rows.length) return this.$message.warning('请选择可取消的预约')
      try {
        await this.$confirm(`确认取消所选 ${rows.length} 条预约？`, '批量取消预约', { type: 'warning' })
      } catch (error) { return }
      this.saving = true
      try {
        for (const row of rows) await performRehabModuleAction('service-appointments', '取消', { id: row.id, storeId: row.storeId || this.businessStoreValue })
        this.$message.success(`已取消 ${rows.length} 条预约`)
        await this.loadCurrent()
      } catch (error) {
        this.$message.error('部分预约取消失败，请刷新后重试')
      } finally { this.saving = false }
    },
    openSchedule(row) {
      if (this.isAllStores) return this.$message.warning('全部门店仅支持汇总查询，请先在顶栏选择具体门店')
      this.editingSchedule = Boolean(row && row.id)
      this.scheduleForm = row && row.id
        ? { id: row.id, storeId: this.businessStoreValue, staffId: row.staffId, scheduleDate: row.scheduleDate, shiftName: row.shiftName, startTime: row.startTime, endTime: row.endTime, maxBookings: Number(row.maxBookings || 0), shiftStatus: row.shiftStatus || '出勤', remark: row.remark || '' }
        : { storeId: this.businessStoreValue, staffId: '', scheduleDate: '', shiftName: '早班', startTime: '08:00', endTime: '12:00', maxBookings: 6, shiftStatus: '出勤', remark: '' }
      this.scheduleDialogVisible = true
    },
    resetScheduleForm() { this.scheduleForm = {}; this.editingSchedule = false },
    applyShiftTime(name) {
      const shift = this.shiftOptions.find(item => item.name === name)
      if (shift) { this.$set(this.scheduleForm, 'startTime', shift.start); this.$set(this.scheduleForm, 'endTime', shift.end) }
    },
    async saveSchedule() {
      if (this.isAllStores) return this.$message.warning('全部门店仅支持汇总查询，请先在顶栏选择具体门店')
      this.scheduleForm.storeId = this.businessStoreValue
      const required = ['storeId', 'staffId', 'scheduleDate', 'shiftName', 'startTime', 'endTime']
      if (required.some(key => !this.scheduleForm[key])) return this.$message.warning('请完整选择门店、员工、日期、班次和时间')
      if (this.scheduleForm.startTime >= this.scheduleForm.endTime) return this.$message.warning('结束时间必须晚于开始时间')
      this.saving = true
      try {
        await saveRehabModuleRecord('staff-schedule-settings', this.scheduleForm)
        this.scheduleDialogVisible = false
        this.$message.success(this.editingSchedule ? '排班已更新' : '排班已新增')
        await this.loadCurrent()
      } catch (error) { this.$message.error('排班保存失败，请检查员工、日期和班次是否冲突') } finally { this.saving = false }
    },
    async cancelSchedule(row) {
      if (this.isAllStores) return this.$message.warning('全部门店仅支持汇总查询，请先在顶栏选择具体门店')
      try { await this.$confirm(`确认取消 ${row.staffName} 在 ${row.scheduleDate} 的${row.shiftName}？`, '取消班次', { type: 'warning' }) } catch (error) { return }
      try {
        await saveRehabModuleRecord('staff-schedule-settings', { ...row, storeId: row.storeId || this.businessStoreValue, shiftStatus: '停诊' })
        this.$message.success('班次已取消并标记为停诊')
        await this.loadCurrent()
      } catch (error) { this.$message.error('取消班次失败，请稍后重试') }
    },
    async deleteSchedule(row) {
      if (this.isAllStores) return this.$message.warning('全部门店仅支持汇总查询，请先在顶栏选择具体门店')
      try { await this.$confirm(`删除后不可恢复，确认删除 ${row.staffName} 在 ${row.scheduleDate} 的排班？`, '删除排班', { type: 'warning' }) } catch (error) { return }
      try {
        await performRehabModuleAction('staff-schedule-settings', '删除', { id: row.id, storeId: row.storeId || this.businessStoreValue })
        this.$message.success('排班已删除')
        await this.loadCurrent()
      } catch (error) { this.$message.error('排班删除失败，请确认该记录仍然有效') }
    }
  }
}
</script>

<style lang="scss" scoped>
.schedule-workbench { min-height:calc(100vh - 84px); padding:22px; color:#26354c; background:#f3f6fa; }.hero-panel { display:flex; align-items:center; justify-content:space-between; gap:24px; padding:24px 28px; color:#fff; background:linear-gradient(125deg,#3e4c5f,#9b7947); border-radius:14px; }.eyebrow { margin-bottom:7px; color:#f6e5c0; font-size:13px; font-weight:700; }.hero-panel h1 { margin:0 0 8px; font-size:27px; }.hero-panel p { margin:0; color:#f6f1e8; font-size:14px; }.hero-actions,.table-actions { display:flex; align-items:center; gap:10px; }.filter-card,.table-card { border:0; border-radius:12px; }.filter-card { margin-bottom:14px; }.load-error { margin-bottom:14px; }.table-heading { display:flex; align-items:center; justify-content:space-between; gap:16px; }.table-heading h2 { margin:0 0 4px; font-size:16px; }.table-heading p { margin:0; color:#84909c; font-size:12px; }.empty-state { padding:32px; color:#8994a0; text-align:center; }.booking-form { margin-top:16px; }.full { width:100%; }.danger-link { color:#f56c6c; } @media (max-width:700px) { .schedule-workbench { padding:12px; }.hero-panel,.table-heading { align-items:flex-start; flex-direction:column; }.hero-actions { width:100%; }.hero-actions .el-button { flex:1; } }
</style>

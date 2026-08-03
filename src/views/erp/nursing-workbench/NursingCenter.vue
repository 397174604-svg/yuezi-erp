<template>
  <div class="care-center">
    <header class="center-toolbar">
      <h2>护理中心</h2>
      <el-select v-model="filters.store" size="small" class="store-select" @change="handleStoreChange">
        <el-option v-for="store in storeOptions" :key="store.value" :label="store.label" :value="store.value" />
      </el-select>
      <el-select v-model="filters.careLevel" size="small" class="level-select">
        <el-option v-for="level in careLevelOptions" :key="level.value" :label="level.label" :value="level.value" />
      </el-select>
    </header>

    <div class="center-layout">
      <aside class="metric-panel">
        <button
          v-for="metric in metrics"
          :key="metric.key"
          type="button"
          class="metric-block"
          :class="{ clickable: metric.action, blank: metric.blank }"
          :title="metric.title || ''"
          :disabled="metric.blank"
          @click="openMetric(metric)"
        >
          <strong v-if="!metric.blank" :class="metric.tone">{{ metric.value }}</strong>
          <span v-if="!metric.blank">{{ metric.label }}</span>
        </button>
      </aside>

      <main class="customer-panel">
        <div class="customer-filter-bar">
          <div class="stay-tabs">
            <button
              v-for="mode in stayModes"
              :key="mode.value"
              type="button"
              :class="{ active: filters.mode === mode.value }"
              @click="filters.mode = mode.value"
            >
              {{ mode.label }}
            </button>
          </div>

          <div class="care-status-filter">
            <span>护理情况：</span>
            <el-checkbox-group v-model="filters.statuses">
              <el-checkbox label="normal"><i class="status-dot normal" />正常</el-checkbox>
              <el-checkbox label="abnormal"><i class="status-dot abnormal" />异常</el-checkbox>
              <el-checkbox label="danger"><i class="status-dot danger" />危险</el-checkbox>
            </el-checkbox-group>
            <el-checkbox :value="false" disabled><i class="status-dot outside" />外出</el-checkbox>
          </div>

          <div class="person-legend">
            <span><i class="person-symbol mother">妈</i>妈妈</span>
            <span><i class="person-symbol boy">男</i>男宝宝</span>
            <span><i class="person-symbol girl">女</i>女宝宝</span>
          </div>
        </div>

        <div v-if="floorGroups.length" class="floor-list">
          <section v-for="group in floorGroups" :key="group.floor" class="floor-group">
            <header class="floor-heading">
              <div>
                <strong>{{ group.floor === '未分层' ? group.floor : `${group.floor}楼` }}</strong>
                <span>（客户数量：{{ group.clients.length }}，宝宝数量：{{ group.babyCount }}）</span>
              </div>
              <button type="button" @click="toggleFloor(group.floor)">
                <i :class="isFloorCollapsed(group.floor) ? 'el-icon-arrow-down' : 'el-icon-arrow-up'" />
                {{ isFloorCollapsed(group.floor) ? '展开' : '收起' }}
              </button>
            </header>

            <div v-show="!isFloorCollapsed(group.floor)" class="customer-card-grid">
              <article
                v-for="client in group.clients"
                :key="client.id"
                class="customer-card"
                :class="`is-${client.status}`"
              >
                <el-popover
                  placement="left-start"
                  width="126"
                  trigger="hover"
                  popper-class="nursing-card-popper"
                >
                  <div class="card-action-menu">
                    <button
                      v-for="action in cardActions"
                      :key="action"
                      type="button"
                      @click="openCardAction(action, client)"
                    >
                      {{ action }}
                    </button>
                  </div>
                  <div slot="reference" class="customer-card-title">
                    {{ client.room }}（{{ client.customerName }}）
                  </div>
                </el-popover>

                <div class="customer-card-body">
                  <div class="card-badges">
                    <button
                      type="button"
                      :class="{ off: !client.sameRoom }"
                      @click="toggleSameRoom(client)"
                    >
                      母婴同室
                    </button>
                    <button
                      v-if="client.pendingCare"
                      type="button"
                      @click="openCardAction('妈妈护理记录', client)"
                    >
                      待护理
                    </button>
                  </div>

                  <div class="people-row">
                    <button
                      type="button"
                      :title="client.customerName"
                      class="person-button"
                      @click="openCareRecord('mother', client)"
                    >
                      <i class="person-symbol mother" :class="client.status">妈</i>
                      <em v-if="client.motherOut" />
                    </button>
                    <button
                      v-for="baby in client.babies"
                      :key="baby.id"
                      type="button"
                      :title="baby.name"
                      class="person-button"
                      @click="openCareRecord('baby', client, baby)"
                    >
                      <i class="person-symbol" :class="[baby.gender === '女' ? 'girl' : 'boy', baby.status]">
                        {{ baby.gender }}
                      </i>
                      <em v-if="baby.outside" />
                    </button>
                    <button type="button" title="添加宝宝" class="add-baby-button" @click="openBabyDialog(client)">
                      <i class="el-icon-plus" />
                    </button>
                  </div>
                </div>

                <footer class="customer-card-footer">
                  <button type="button" title="服务预约" @click="openCardAction('产康服务预约', client)">
                    <i class="el-icon-date" />
                    <b v-if="client.appointmentCount">{{ client.appointmentCount > 99 ? '…' : client.appointmentCount }}</b>
                  </button>
                  <button type="button" title="护理服务确认" @click="openCardAction('护理计划确认', client)">
                    <i class="el-icon-circle-check" />
                  </button>
                </footer>

                <span class="care-type-badge" :style="{ backgroundColor: client.careColor }" :title="client.careType">
                  {{ client.careLevelLabel }}
                </span>
              </article>
            </div>
          </section>
        </div>
        <div v-else class="empty-state">
          <i class="el-icon-receiving" />
          <span>暂无符合条件的在住客户</span>
        </div>
      </main>
    </div>

    <nursing-care-record-dialog
      :visible.sync="careRecordVisible"
      :record-type="careRecordType"
      :client="activeClient"
      :baby="activeBaby"
      @saved="saveCareRecord"
    />
    <nursing-baby-dialog
      :visible.sync="babyDialogVisible"
      :client="activeClient"
      @saved="saveBaby"
    />
    <nursing-legacy-action-dialog
      :visible.sync="legacyActionVisible"
      :action="activeAction"
      :client="activeClient"
    />

    <el-dialog
      :title="activeAction"
      :visible.sync="actionDialogVisible"
      width="720px"
      append-to-body
      :close-on-click-modal="false"
    >
      <div class="action-context">
        <div><span>业务入口：</span><b>{{ activeAction }}</b></div>
        <div><span>房间号：</span><b>{{ activeClient.room || '—' }}</b></div>
        <div><span>客户姓名：</span><b>{{ activeClient.customerName || '—' }}</b></div>
        <div><span>后续处理：</span><b>进入对应业务页面继续办理</b></div>
      </div>
      <div slot="footer">
        <el-button @click="actionDialogVisible = false">关闭</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import NursingBabyDialog from './NursingBabyDialog'
import NursingCareRecordDialog from './NursingCareRecordDialog'
import NursingLegacyActionDialog from './NursingLegacyActionDialog'
import { getNursingModuleData, saveNursingModuleRecord } from '@/api/erp-nursing'

const STORE_OPTIONS = [
  { value: '1', label: '中心广场旗舰店' },
  { value: '2', label: '黄河路轻奢店' }
]

const STORE_VALUE_BY_ROUTE_ID = {
  1: '1',
  2: '2'
}

const ROUTE_ID_BY_STORE_VALUE = {
  1: '1',
  2: '2'
}

function routeStoreValue(route, currentStoreId = '1') {
  const current = STORE_VALUE_BY_ROUTE_ID[Number(currentStoreId)]
  if (current) return current
  const query = (route && route.query) || {}
  const byId = STORE_VALUE_BY_ROUTE_ID[Number(query.storeId)]
  if (byId) return byId
  const byName = STORE_OPTIONS.find(item => item.label === query.store)
  if (byName) return byName.value

  const storeName = String(query.store || '')
  if (storeName.includes('黄河路')) return '2'
  if (storeName.includes('中心') || storeName.includes('建设路')) return '1'

  return '1'
}

const CARE_LEVEL_OPTIONS = [
  { value: '-1', label: '选择护理等级' },
  { value: '519', label: '一级护理' },
  { value: '520', label: '二级护理' }
]

const CARD_ACTIONS = [
  '产康服务预约',
  '产康服务确认',
  '护理计划单',
  '妈妈护理记录',
  '产康服务记录',
  '月嫂服务记录',
  '医生查房记录',
  '健康评估',
  '外出申请'
]

const LEGACY_ACTIONS = [...CARD_ACTIONS, '护理计划确认']

export default {
  name: 'NursingCenter',
  components: { NursingBabyDialog, NursingCareRecordDialog, NursingLegacyActionDialog },
  data() {
    return {
      storeOptions: STORE_OPTIONS,
      careLevelOptions: CARE_LEVEL_OPTIONS,
      stayModes: [{ value: '0', label: '会所' }, { value: '1', label: '到家' }],
      cardActions: CARD_ACTIONS,
      filters: {
        store: routeStoreValue(this.$route, this.$store.getters.currentStoreId),
        careLevel: '-1',
        mode: '0',
        statuses: []
      },
      clients: [],
      collapsedFloors: {},
      careRecordVisible: false,
      careRecordType: 'mother',
      babyDialogVisible: false,
      legacyActionVisible: false,
      actionDialogVisible: false,
      activeAction: '',
      activeClient: {},
      activeBaby: {}
    }
  },
  computed: {
    ...mapGetters(['currentStoreId']),
    isAllStores() {
      return String(this.currentStoreId || 'all') === 'all'
    },
    storeClients() {
      return this.clients.filter(client => client.store === this.filters.store)
    },
    filteredClients() {
      return this.storeClients.filter(client => {
        if (client.mode !== this.filters.mode) return false
        if (this.filters.careLevel !== '-1' && client.careLevel !== this.filters.careLevel) return false
        if (this.filters.statuses.length && !this.filters.statuses.includes(client.status)) return false
        return true
      })
    },
    floorGroups() {
      const grouped = this.filteredClients.reduce((result, client) => {
        if (!result[client.floor]) result[client.floor] = []
        result[client.floor].push(client)
        return result
      }, {})
      return Object.keys(grouped).sort((a, b) => Number(a) - Number(b)).map(floor => ({
        floor,
        clients: grouped[floor],
        babyCount: grouped[floor].reduce((sum, client) => sum + client.babies.length, 0)
      }))
    },
    metrics() {
      const clients = this.storeClients
      const babies = clients.reduce((result, client) => result.concat(client.babies), [])
      const allPeopleStatuses = clients.map(client => client.status).concat(babies.map(baby => baby.status))
      const totalServices = clients.reduce((sum, client) => (
        sum + Number(client.pendingServices || 0) + Number(client.completedServices || 0)
      ), 0)
      const pendingServices = clients.reduce((sum, client) => (
        sum + Number(client.pendingServices || 0)
      ), 0)
      return [
        { key: 'people', label: '在住总人数', value: clients.length + babies.length },
        { key: 'mothers', label: '妈妈人数', value: clients.length },
        { key: 'babies', label: '宝宝人数', value: babies.length },
        { key: 'rounds', label: '待查房数', value: clients.filter(client => client.status !== 'normal').length },
        { key: 'mother-care', label: '妈妈待护理', value: clients.filter(client => client.pendingCare).length },
        { key: 'baby-care', label: '宝宝待护理', value: clients.filter(client => client.pendingCare).reduce((sum, client) => sum + client.babies.length, 0) },
        { key: 'natural', label: '顺产', value: clients.filter(client => client.delivery === '顺产').length, action: '入住评估单' },
        { key: 'caesarean', label: '剖腹产', value: clients.filter(client => client.delivery === '剖腹产').length, action: '入住评估单' },
        { key: 'miscarriage', label: '小产', value: clients.filter(client => client.delivery === '小产').length, action: '入住评估单' },
        { key: 'checked-baby', label: '入住宝宝', value: babies.filter(baby => !baby.outside).length },
        { key: 'boys', label: '男宝宝', value: babies.filter(baby => baby.gender === '男').length },
        { key: 'girls', label: '女宝宝', value: babies.filter(baby => baby.gender === '女').length },
        { key: 'normal', label: '正常', value: allPeopleStatuses.filter(status => status === 'normal').length, tone: 'normal', title: '在线总人数减异常和危险人数' },
        { key: 'abnormal', label: '异常', value: allPeopleStatuses.filter(status => status === 'abnormal').length, tone: 'abnormal', title: '妈妈+宝宝异常总数' },
        { key: 'danger', label: '危险', value: allPeopleStatuses.filter(status => status === 'danger').length, tone: 'danger', title: '妈妈+宝宝危险总数' },
        { key: 'services', label: '总服务数', value: totalServices },
        { key: 'pending', label: '待服务', value: pendingServices, action: '待服务' },
        { key: 'done', label: '已服务', value: totalServices - pendingServices },
        { key: 'one', label: '一对一护理', value: clients.filter(client => client.careType === '一对一护理').length },
        { key: 'many', label: '一对多护理', value: clients.filter(client => client.careType === '一对多护理').length },
        { key: 'blank', blank: true, label: '', value: '' }
      ]
    }
  },
  watch: {
    '$route.query': {
      deep: true,
      handler(routeQuery) {
        const store = routeStoreValue(
          { query: routeQuery },
          this.$store.getters.currentStoreId
        )
        if (store !== this.filters.store) {
          this.filters.store = store
          this.loadClients()
        }
      }
    },
    currentStoreId(value, previous) {
      if (String(value) === String(previous) || String(value || 'all') === 'all') return
      const store = routeStoreValue(this.$route, value)
      if (store !== this.filters.store) {
        this.filters.store = store
        this.loadClients()
      }
    }
  },
  mounted() {
    this.loadClients()
  },
  methods: {
    handleStoreChange(store) {
      const storeId = ROUTE_ID_BY_STORE_VALUE[Number(store)]
      if (!storeId || String(this.$route.query.storeId || '') === storeId) return
      this.$router.replace({
        query: {
          ...this.$route.query,
          storeId
        }
      })
    },
    isFloorCollapsed(floor) {
      return Boolean(this.collapsedFloors[floor])
    },
    toggleFloor(floor) {
      this.$set(this.collapsedFloors, floor, !this.isFloorCollapsed(floor))
    },
    toggleSameRoom(client) {
      this.$message.warning('母婴同室状态尚未接入正式写入，请在入住交接中记录')
    },
    openCareRecord(type, client, baby = {}) {
      this.activeClient = client
      this.activeBaby = baby
      this.careRecordType = type
      this.careRecordVisible = true
    },
    openBabyDialog(client) {
      this.activeClient = client
      this.babyDialogVisible = true
    },
    openCardAction(action, client) {
      this.activeClient = client
      this.activeBaby = {}
      this.activeAction = action
      if (LEGACY_ACTIONS.includes(action)) {
        this.actionDialogVisible = false
        this.legacyActionVisible = true
        return
      }
      this.legacyActionVisible = false
      this.actionDialogVisible = true
    },
    openMetric(metric) {
      if (!metric.action) return
      this.activeClient = {}
      this.activeAction = metric.action
      this.legacyActionVisible = false
      this.actionDialogVisible = true
    },
    async loadClients() {
      try {
        const response = await getNursingModuleData('nursing-center', {
          storeId: this.filters.store
        })
        const rows = response.data && Array.isArray(response.data.list)
          ? response.data.list
          : []
        this.clients = rows.map(row => ({
          ...row,
          store: String(row.storeId),
          mode: '0',
          floor: String(row.floor || '未分层'),
          room: row.room || '未分房',
          status: 'unassessed',
          careLevel: '-1',
          careLevelLabel: row.careLevel || '未设置',
          careType: row.careType || '未设置',
          careColor: '#8793a3',
          delivery: row.deliveryMode || '未记录',
          sameRoom: null,
          pendingCare: Number(row.pendingServices || 0) > 0,
          motherOut: false,
          appointmentCount: 0,
          babies: (row.babies || []).map(baby => ({
            ...baby,
            status: 'unassessed',
            outside: false
          }))
        }))
      } catch (error) {
        this.clients = []
      }
    },
    async saveCareRecord({ recordType, form }) {
      if (this.isAllStores) return this.$message.warning('全部门店仅支持汇总查询，请先在顶栏选择具体门店')
      const resource = recordType === 'baby'
        ? 'baby-nursing-records'
        : 'mother-nursing-records'
      try {
        await saveNursingModuleRecord(resource, {
          ...form,
          customerName: this.activeClient.customerName,
          customerId: this.activeClient.id,
          babyName: this.activeBaby.name,
          babyId: this.activeBaby.id,
          storeId: String(this.currentStoreId)
        })
        this.$message.success('护理记录已保存')
      } catch (error) {
        this.$message.warning(error.message || '护理记录保存失败')
      }
    },
    async saveBaby(form) {
      if (this.isAllStores) return this.$message.warning('全部门店仅支持汇总查询，请先在顶栏选择具体门店')
      try {
        await saveNursingModuleRecord('baby-files', {
          ...form,
          customerName: this.activeClient.customerName,
          customerId: this.activeClient.id,
          storeId: String(this.currentStoreId)
        })
        this.$message.success('宝宝档案已保存')
      } catch (error) {
        this.$message.warning(error.message || '宝宝档案保存失败')
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.care-center {
  min-height: calc(100vh - 124px);
  border: 1px solid #e5e9ee;
  border-radius: 5px;
  background: #fff;
  color: #344257;
}
.center-toolbar {
  display: flex;
  align-items: center;
  min-height: 48px;
  padding: 0 15px;
  border-bottom: 1px solid #e8ebef;
}
.center-toolbar h2 { margin: 0 12px 0 0; color: #333; font-size: 15px; }
.store-select { width: 178px; margin-right: 7px; }
.level-select { width: 150px; }
.center-layout { display: grid; grid-template-columns: 330px minmax(0, 1fr); min-height: calc(100vh - 174px); }
.metric-panel {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  align-content: start;
  border-right: 1px solid #e6e9ed;
  background: #fbfcfd;
}
.metric-block {
  min-height: 88px;
  padding: 12px 5px;
  border: 0;
  border-right: 1px solid #e8ebef;
  border-bottom: 1px solid #e8ebef;
  background: transparent;
  cursor: default;
}
.metric-block:nth-child(3n) { border-right: 0; }
.metric-block strong { display: block; margin-bottom: 7px; color: #5d94cb; font-size: 25px; font-weight: 500; }
.metric-block span { color: #647186; font-size: 12px; }
.metric-block strong.normal { color: #438ed0; }
.metric-block strong.abnormal { color: #e0a128; }
.metric-block strong.danger { color: #df5c65; }
.metric-block.clickable { cursor: pointer; }
.metric-block.clickable:hover { background: #f2f8fd; }
.metric-block.blank { cursor: default; }
.customer-panel { min-width: 0; }
.customer-filter-bar {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  min-height: 62px;
  padding: 0 15px;
  border-bottom: 1px solid #e7eaee;
  gap: 12px 22px;
}
.stay-tabs { align-self: stretch; display: flex; }
.stay-tabs button {
  min-width: 68px;
  padding: 0 14px;
  border: 0;
  border-bottom: 2px solid transparent;
  color: #606d80;
  background: transparent;
  cursor: pointer;
}
.stay-tabs button.active { border-bottom-color: #4695d0; color: #347fb9; }
.care-status-filter { display: flex; align-items: center; min-width: 430px; color: #536176; font-size: 12px; }
.care-status-filter > span { margin-right: 10px; }
.care-status-filter ::v-deep .el-checkbox-group { display: inline-flex; }
.care-status-filter ::v-deep .el-checkbox { margin-right: 14px; }
.status-dot { display: inline-block; width: 10px; height: 10px; margin-right: 4px; border-radius: 2px; vertical-align: -1px; }
.status-dot.normal { background: #4d9ed9; }
.status-dot.abnormal { background: #efb242; }
.status-dot.danger { background: #e65c69; }
.status-dot.outside { border: 1px solid #ff9b02; background: #fff; }
.person-legend { display: flex; gap: 12px; color: #59677a; font-size: 12px; white-space: nowrap; }
.person-legend span { display: inline-flex; align-items: center; gap: 4px; }
.person-symbol {
  display: inline-grid;
  place-items: center;
  width: 27px;
  height: 27px;
  border-radius: 50%;
  color: #fff;
  font-size: 11px;
  font-style: normal;
  background: #5ca2d7;
}
.person-symbol.mother { background: #df79a4; }
.person-symbol.boy { background: #5b9fd3; }
.person-symbol.girl { background: #da80b3; }
.person-symbol.abnormal { box-shadow: 0 0 0 3px rgba(239, 178, 66, .28); }
.person-symbol.danger { box-shadow: 0 0 0 3px rgba(230, 92, 105, .26); }
.floor-list { padding: 0 16px 22px; }
.floor-group { margin-top: 13px; }
.floor-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 8px;
  border-bottom: 1px solid #e5e5e5;
}
.floor-heading strong { color: #333; font-size: 16px; }
.floor-heading span { color: #999; font-size: 13px; }
.floor-heading button { border: 0; color: #7b8797; background: transparent; cursor: pointer; font-size: 12px; }
.customer-card-grid { display: flex; flex-wrap: wrap; gap: 14px; padding-top: 13px; }
.customer-card {
  position: relative;
  width: 180px;
  border: 1px solid #dce8f1;
  border-radius: 3px;
  background: #eef8ff;
  box-shadow: 0 2px 5px rgba(38, 62, 86, .06);
}
.customer-card.is-abnormal { border-color: #f0d69b; background: #fff8e9; }
.customer-card.is-danger { border-color: #efafb4; background: #fff0f1; }
.customer-card-title {
  min-height: 32px;
  padding: 8px 10px;
  overflow: hidden;
  border-radius: 3px 3px 0 0;
  color: #fff;
  background: #5d9ed0;
  cursor: pointer;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.is-abnormal .customer-card-title { background: #e7ad3f; }
.is-danger .customer-card-title { background: #df626c; }
.customer-card-body { min-height: 78px; padding: 8px 10px; }
.card-badges { display: flex; gap: 5px; min-height: 21px; }
.card-badges button {
  padding: 2px 5px;
  border: 1px solid #7db2dc;
  border-radius: 2px;
  color: #347daf;
  background: #fff;
  cursor: pointer;
  font-size: 10px;
}
.card-badges button.off { border-color: #c8cdd3; color: #9aa2ac; }
.people-row { display: flex; align-items: center; gap: 8px; margin-top: 11px; overflow-x: auto; }
.person-button, .add-baby-button {
  position: relative;
  flex: 0 0 auto;
  padding: 0;
  border: 0;
  background: transparent;
  cursor: pointer;
}
.person-button em {
  position: absolute;
  right: -2px;
  bottom: -1px;
  width: 9px;
  height: 9px;
  border: 2px solid #fff;
  border-radius: 50%;
  background: #ff9b02;
}
.add-baby-button {
  display: grid;
  place-items: center;
  width: 27px;
  height: 27px;
  border: 1px dashed #aeb8c4;
  border-radius: 50%;
  color: #a3adb8;
}
.customer-card-footer {
  display: flex;
  justify-content: space-around;
  min-height: 34px;
  padding: 4px 34px 4px 8px;
  border-top: 1px solid rgba(100, 130, 160, .15);
  background: rgba(255, 255, 255, .55);
}
.customer-card-footer button {
  position: relative;
  border: 0;
  color: #607c96;
  background: transparent;
  cursor: pointer;
  font-size: 17px;
}
.customer-card-footer b {
  position: absolute;
  top: -2px;
  right: -7px;
  min-width: 14px;
  padding: 1px 3px;
  border-radius: 7px;
  color: #fff;
  background: #e35e68;
  font-size: 8px;
}
.care-type-badge {
  position: absolute;
  right: 0;
  bottom: 0;
  max-width: 52px;
  padding: 3px 5px;
  overflow: hidden;
  border-radius: 3px 0 3px 0;
  color: #fff;
  font-size: 9px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.card-action-menu { display: flex; flex-direction: column; }
.card-action-menu button { padding: 6px 8px; border: 0; color: #485568; background: #fff; cursor: pointer; text-align: left; font-size: 12px; }
.card-action-menu button:hover { color: #df565f; background: #f5f5f5; }
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 120px;
  color: #909399;
}
.empty-state i { color: #c0c4cc; font-size: 30px; }
.action-context { display: grid; grid-template-columns: 1fr 1fr; gap: 12px 18px; margin-bottom: 16px; padding: 15px; border: 1px solid #e5e9ee; border-radius: 5px; background: #f8fafc; font-size: 13px; }
.action-context div:last-child { grid-column: 1 / -1; }
.action-context span { color: #7d8897; }
.action-context code { color: #51657b; }
@media (max-width: 1180px) {
  .center-layout { grid-template-columns: 285px minmax(0, 1fr); }
  .customer-filter-bar { grid-template-columns: 1fr; padding: 10px 15px; }
  .stay-tabs { min-height: 38px; }
}
@media (max-width: 760px) {
  .center-toolbar { flex-wrap: wrap; gap: 7px; padding: 10px; }
  .center-layout { display: block; }
  .metric-panel { border-right: 0; }
  .care-status-filter { min-width: 0; flex-wrap: wrap; }
}
</style>

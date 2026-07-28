<template>
  <div class="foundation-page">
    <div class="page-heading">
      <div>
        <div class="eyebrow">系统设置 · 权限与主数据底座</div>
        <h1>{{ title }}</h1>
        <p>{{ description }}</p>
      </div>
      <div class="heading-actions">
        <el-tag effect="plain" type="success">第一阶段</el-tag>
        <el-button icon="el-icon-refresh" @click="loadData">刷新</el-button>
        <el-button type="primary" icon="el-icon-plus" @click="openCreate">{{ createLabel }}</el-button>
      </div>
    </div>

    <div v-loading="loading">
      <template v-if="pageType === 'organization'">
        <div class="metric-grid">
          <div v-for="metric in organizationMetrics" :key="metric.label" class="metric-card">
            <i :class="metric.icon" :style="{ color: metric.color, background: metric.color + '16' }" />
            <div><b>{{ metric.value }}</b><span>{{ metric.label }}</span></div>
          </div>
        </div>
        <el-row :gutter="16">
          <el-col :lg="7" :xs="24">
            <el-card shadow="never" class="content-card organization-tree">
              <div slot="header" class="card-title"><span>组织架构</span><el-button type="text" @click="dialogType = 'department'; dialogVisible = true">新增部门</el-button></div>
              <el-tree :data="organizationTree" node-key="id" default-expand-all :expand-on-click-node="false">
                <span slot-scope="{ node, data }" class="tree-node"><span><i :class="data.icon || 'el-icon-office-building'" />{{ node.label }}</span><el-tag v-if="data.count" size="mini" type="info">{{ data.count }}人</el-tag></span>
              </el-tree>
            </el-card>
          </el-col>
          <el-col :lg="17" :xs="24">
            <el-card shadow="never" class="content-card">
              <div slot="header" class="card-title"><span>门店档案</span><el-button type="text" @click="dialogType = 'store'; dialogVisible = true">新增门店</el-button></div>
              <div class="store-grid">
                <div v-for="store in stores" :key="store.id" class="store-card">
                  <div class="store-head"><span class="store-icon"><i class="el-icon-house" /></span><div><b>{{ store.name }}</b><small>{{ store.code }}</small></div><el-tag size="mini" type="success">{{ store.status }}</el-tag></div>
                  <div class="store-stats"><span><b>{{ store.departments }}</b>部门</span><span><b>{{ store.employees }}</b>职员</span><span><b>{{ store.rooms }}</b>客房</span></div>
                  <div class="store-foot"><span>负责人：{{ store.manager }}</span><el-button type="text" @click="editRecord('store', store)">配置</el-button></div>
                </div>
              </div>
            </el-card>
            <el-card shadow="never" class="content-card">
              <div slot="header" class="card-title"><span>部门列表</span><small>部门决定默认数据范围与审批归属</small></div>
              <el-table :data="departments" stripe>
                <el-table-column prop="name" label="部门名称" min-width="120" />
                <el-table-column prop="store" label="所属门店" min-width="150" />
                <el-table-column prop="leader" label="负责人" width="100" />
                <el-table-column prop="employees" label="人数" width="76" />
                <el-table-column prop="dataScope" label="默认数据范围" min-width="120" />
                <el-table-column label="状态" width="86"><template slot-scope="scope"><el-tag :type="scope.row.status === '启用' ? 'success' : 'info'" size="mini">{{ scope.row.status }}</el-tag></template></el-table-column>
                <el-table-column label="操作" width="110"><template slot-scope="scope"><el-button type="text" @click="editRecord('department', scope.row)">编辑</el-button><el-button type="text">成员</el-button></template></el-table-column>
              </el-table>
            </el-card>
          </el-col>
        </el-row>
      </template>

      <template v-else-if="pageType === 'role-permission'">
        <el-row :gutter="16">
          <el-col :lg="9" :xs="24">
            <el-card shadow="never" class="content-card role-card">
              <div slot="header" class="card-title"><span>角色列表</span><small>{{ roles.length }} 个角色</small></div>
              <el-table :data="roles" highlight-current-row @row-click="selectRole">
                <el-table-column prop="name" label="角色名称" min-width="110" />
                <el-table-column prop="code" label="编码" min-width="120" />
                <el-table-column prop="users" label="用户" width="65" />
                <el-table-column label="状态" width="70"><template slot-scope="scope"><el-tag type="success" size="mini">{{ scope.row.status }}</el-tag></template></el-table-column>
              </el-table>
            </el-card>
          </el-col>
          <el-col :lg="15" :xs="24">
            <el-card shadow="never" class="content-card permission-card">
              <div slot="header" class="card-title"><div><span>{{ activeRole.name || '请选择角色' }}</span><el-tag v-if="activeRole.code" size="mini" effect="plain">{{ activeRole.code }}</el-tag></div><el-button type="primary" size="small" @click="savePermissions">保存权限</el-button></div>
              <div class="scope-line"><span>数据范围</span><el-radio-group v-model="activeRole.dataScope" size="small"><el-radio-button label="本人数据" /><el-radio-button label="本部门" /><el-radio-button label="本门店" /><el-radio-button label="全部数据" /></el-radio-group></div>
              <el-table :data="permissions" border size="small">
                <el-table-column prop="module" label="业务模块" min-width="110" />
                <el-table-column v-for="action in permissionActions" :key="action.key" :label="action.label" width="66" align="center"><template slot-scope="scope"><el-checkbox v-model="scope.row[action.key]" /></template></el-table-column>
                <el-table-column prop="sensitive" label="敏感字段策略" min-width="115" />
              </el-table>
              <p class="permission-tip"><i class="el-icon-lock" /> 权限由菜单、操作、数据范围和敏感字段四层共同决定；健康和资金字段默认最小授权。</p>
            </el-card>
          </el-col>
        </el-row>
      </template>

      <template v-else-if="pageType === 'user-account'">
        <div class="metric-grid">
          <div v-for="metric in userMetrics" :key="metric.label" class="metric-card"><i :class="metric.icon" :style="{ color: metric.color, background: metric.color + '16' }" /><div><b>{{ metric.value }}</b><span>{{ metric.label }}</span></div></div>
        </div>
        <el-card shadow="never" class="content-card filter-card">
          <div class="filter-line"><el-input v-model="keyword" clearable prefix-icon="el-icon-search" placeholder="搜索账号、姓名或手机号" /><el-select v-model="storeFilter" clearable placeholder="全部门店"><el-option v-for="store in stores" :key="store.id" :label="store.name" :value="store.name" /></el-select><el-select v-model="roleFilter" clearable placeholder="全部角色"><el-option v-for="role in roles" :key="role.id" :label="role.name" :value="role.name" /></el-select><el-button type="primary" icon="el-icon-search">查询</el-button><el-button @click="keyword = ''; storeFilter = ''; roleFilter = ''">重置</el-button></div>
        </el-card>
        <el-card shadow="never" class="content-card">
          <div slot="header" class="card-title"><span>用户账号</span><small>账号、职员、角色和门店四者关联</small></div>
          <el-table :data="filteredUsers" stripe>
            <el-table-column prop="username" label="登录账号" min-width="110" />
            <el-table-column prop="name" label="职员姓名" width="110" />
            <el-table-column prop="mobile" label="联系电话" width="125" />
            <el-table-column prop="store" label="所属门店" min-width="150" />
            <el-table-column prop="department" label="部门" width="105" />
            <el-table-column prop="role" label="角色" width="110" />
            <el-table-column prop="lastLogin" label="最近登录" min-width="145" />
            <el-table-column label="状态" width="90"><template slot-scope="scope"><el-switch v-model="scope.row.status" active-value="启用" inactive-value="停用" /></template></el-table-column>
            <el-table-column label="操作" width="165" fixed="right"><template slot-scope="scope"><el-button type="text" @click="editRecord('user', scope.row)">编辑</el-button><el-button type="text">重置密码</el-button><el-button type="text">授权</el-button></template></el-table-column>
          </el-table>
        </el-card>
      </template>

      <template v-else-if="pageType === 'data-dictionary'">
        <el-row :gutter="16">
          <el-col :lg="7" :xs="24">
            <el-card shadow="never" class="content-card dictionary-types">
              <div slot="header" class="card-title"><span>字典分类</span><el-button type="text" @click="dialogType = 'dictionaryType'; dialogVisible = true">新增分类</el-button></div>
              <button v-for="item in dictionaryTypes" :key="item.id" :class="{ active: activeDictionary.code === item.code }" @click="activeDictionary = item"><span><b>{{ item.name }}</b><small>{{ item.code }}</small></span><el-tag size="mini" type="info">{{ item.items }}</el-tag></button>
            </el-card>
          </el-col>
          <el-col :lg="17" :xs="24">
            <el-card shadow="never" class="content-card">
              <div slot="header" class="card-title"><div><span>{{ activeDictionary.name }}</span><el-tag v-if="activeDictionary.builtIn" size="mini" type="warning" effect="plain">内置字典</el-tag></div><el-button type="primary" size="small" @click="dialogType = 'dictionaryItem'; dialogVisible = true">新增字典项</el-button></div>
              <el-table :data="activeDictionaryItems" stripe>
                <el-table-column prop="label" label="显示名称" min-width="120" />
                <el-table-column prop="value" label="存储值" min-width="150" />
                <el-table-column prop="sort" label="排序" width="72" />
                <el-table-column label="显示颜色" width="105"><template slot-scope="scope"><span class="color-preview" :style="{ background: scope.row.color }" />{{ scope.row.color }}</template></el-table-column>
                <el-table-column label="状态" width="85"><template slot-scope="scope"><el-tag type="success" size="mini">{{ scope.row.status }}</el-tag></template></el-table-column>
                <el-table-column label="操作" width="120"><template slot-scope="scope"><el-button type="text" @click="editRecord('dictionaryItem', scope.row)">编辑</el-button><el-button type="text">停用</el-button></template></el-table-column>
              </el-table>
              <div v-if="!activeDictionaryItems.length" class="empty-dictionary"><i class="el-icon-collection" /><p>此分类尚未配置字典项</p><el-button type="primary" plain @click="dialogType = 'dictionaryItem'; dialogVisible = true">立即配置</el-button></div>
            </el-card>
          </el-col>
        </el-row>
      </template>

      <template v-else>
        <el-card shadow="never" class="content-card">
          <div slot="header" class="card-title"><span>操作权限矩阵</span><small>统一维护列表、新增、编辑、审核、导出和敏感字段权限</small></div>
          <el-table :data="permissions" border>
            <el-table-column prop="module" label="业务模块" min-width="130" />
            <el-table-column v-for="action in permissionActions" :key="action.key" :label="action.label" min-width="82" align="center"><template slot-scope="scope"><el-switch v-model="scope.row[action.key]" /></template></el-table-column>
            <el-table-column prop="sensitive" label="字段策略" min-width="140" />
            <el-table-column label="权限编码" min-width="180"><template slot-scope="scope"><code>{{ permissionCode(scope.row.module) }}</code></template></el-table-column>
          </el-table>
        </el-card>
      </template>
    </div>

    <el-dialog :title="dialogTitle" :visible.sync="dialogVisible" width="620px">
      <el-form :model="form" label-width="100px">
        <el-row :gutter="18">
          <el-col :span="12"><el-form-item label="名称"><el-input v-model="form.name" placeholder="请输入名称" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="编码"><el-input v-model="form.code" placeholder="请输入唯一编码" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="18">
          <el-col :span="12"><el-form-item label="所属门店"><el-select v-model="form.store" style="width:100%" placeholder="请选择门店"><el-option v-for="store in stores" :key="store.id" :label="store.name" :value="store.name" /></el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="负责人"><el-input v-model="form.manager" placeholder="请输入负责人" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="数据范围"><el-select v-model="form.dataScope" style="width:100%" placeholder="请选择数据范围"><el-option label="本人数据" value="本人数据" /><el-option label="本部门" value="本部门" /><el-option label="本门店" value="本门店" /><el-option label="全部数据" value="全部数据" /></el-select></el-form-item>
        <el-form-item label="状态"><el-radio-group v-model="form.status"><el-radio label="启用" /><el-radio label="停用" /></el-radio-group></el-form-item>
        <el-form-item label="备注"><el-input v-model="form.remark" type="textarea" :rows="3" placeholder="填写配置说明" /></el-form-item>
      </el-form>
      <span slot="footer"><el-button @click="dialogVisible = false">取消</el-button><el-button type="primary" :loading="saving" @click="saveRecord">保存</el-button></span>
    </el-dialog>
  </div>
</template>

<script>
import { getFoundationOverview, saveFoundationRecord } from '@/api/erp-foundation'

export default {
  name: 'ErpFoundationPage',
  data() {
    return {
      loading: false,
      saving: false,
      stores: [],
      departments: [],
      roles: [],
      users: [],
      dictionaryTypes: [],
      dictionaryItems: {},
      permissions: [],
      activeRole: {},
      activeDictionary: {},
      keyword: '',
      storeFilter: '',
      roleFilter: '',
      dialogVisible: false,
      dialogType: '',
      form: { name: '', code: '', store: '', manager: '', dataScope: '本门店', status: '启用', remark: '' },
      permissionActions: [{ key: 'view', label: '查看' }, { key: 'create', label: '新增' }, { key: 'edit', label: '编辑' }, { key: 'approve', label: '审核' }, { key: 'export', label: '导出' }]
    }
  },
  computed: {
    pageType() { return this.$route.meta.pageType },
    title() { return this.$route.meta.title },
    description() {
      const map = {
        organization: '以集团、门店、部门和职员为层级，统一控制业务归属与数据边界',
        'role-permission': '配置角色的菜单、操作、数据范围及敏感字段访问权限',
        'user-account': '将登录账号与职员、部门、门店和角色进行关联',
        'data-dictionary': '统一维护跨业务状态、类型、来源和审批动作等基础枚举',
        'operation-permission': '按业务模块维护按钮级权限编码和字段可见范围'
      }
      return map[this.pageType] || '组织与权限基础配置'
    },
    createLabel() {
      return { organization: '新增组织', 'role-permission': '新增角色', 'user-account': '新增用户', 'data-dictionary': '新增字典', 'operation-permission': '新增权限' }[this.pageType]
    },
    dialogTitle() {
      const map = { store: '门店配置', department: '部门配置', user: '用户配置', dictionaryType: '字典分类配置', dictionaryItem: '字典项配置', role: '角色配置', permission: '权限配置' }
      return map[this.dialogType] || '基础资料配置'
    },
    organizationMetrics() {
      return [
        { label: '运营门店', value: this.stores.filter(item => item.status === '启用').length, icon: 'el-icon-house', color: '#ff6f9c' },
        { label: '组织部门', value: this.departments.length, icon: 'el-icon-office-building', color: '#4f8cf7' },
        { label: '在职职员', value: this.users.filter(item => item.status === '启用').length, icon: 'el-icon-user', color: '#45b8ac' },
        { label: '业务角色', value: this.roles.length, icon: 'el-icon-key', color: '#8f7cf6' }
      ]
    },
    userMetrics() {
      return [
        { label: '用户总数', value: this.users.length, icon: 'el-icon-user-solid', color: '#4f8cf7' },
        { label: '启用账号', value: this.users.filter(item => item.status === '启用').length, icon: 'el-icon-circle-check', color: '#45b8ac' },
        { label: '停用账号', value: this.users.filter(item => item.status === '停用').length, icon: 'el-icon-remove-outline', color: '#ef6b6b' },
        { label: '角色数量', value: this.roles.length, icon: 'el-icon-key', color: '#8f7cf6' }
      ]
    },
    organizationTree() {
      return [{ id: 'root', label: '奇德芬芳母婴护理有限公司', icon: 'el-icon-office-building', count: this.users.length, children: this.stores.map(store => ({ id: store.id, label: store.name, icon: 'el-icon-house', count: store.employees, children: this.departments.filter(dept => dept.store === store.name).map(dept => ({ id: dept.id, label: dept.name, icon: 'el-icon-folder-opened', count: dept.employees })) })) }]
    },
    filteredUsers() {
      const keyword = this.keyword.trim().toLowerCase()
      return this.users.filter(item => (!keyword || [item.username, item.name, item.mobile].some(value => value.toLowerCase().includes(keyword))) && (!this.storeFilter || item.store === this.storeFilter) && (!this.roleFilter || item.role === this.roleFilter))
    },
    activeDictionaryItems() {
      return this.dictionaryItems[this.activeDictionary.code] || []
    }
  },
  watch: {
    '$route.path'() { this.dialogVisible = false }
  },
  created() {
    this.loadData()
  },
  methods: {
    async loadData() {
      this.loading = true
      try {
        const { data } = await getFoundationOverview()
        Object.keys(data).forEach(key => { this[key] = data[key] })
        this.activeRole = this.roles[0] || {}
        this.activeDictionary = this.dictionaryTypes[0] || {}
      } finally {
        this.loading = false
      }
    },
    openCreate() {
      const types = { organization: 'department', 'role-permission': 'role', 'user-account': 'user', 'data-dictionary': 'dictionaryType', 'operation-permission': 'permission' }
      this.dialogType = types[this.pageType]
      this.form = { name: '', code: '', store: '', manager: '', dataScope: '本门店', status: '启用', remark: '' }
      this.dialogVisible = true
    },
    editRecord(type, record) {
      this.dialogType = type
      this.form = { ...this.form, ...record, code: record.code || record.value || record.id }
      this.dialogVisible = true
    },
    selectRole(role) {
      this.activeRole = { ...role }
    },
    async saveRecord() {
      if (!this.form.name && !['dictionaryItem', 'permission'].includes(this.dialogType)) {
        this.$message.warning('请填写名称')
        return
      }
      this.saving = true
      try {
        await saveFoundationRecord(this.dialogType || 'record', this.form)
        this.dialogVisible = false
        this.$message.success('配置已保存（模拟接口）')
      } finally {
        this.saving = false
      }
    },
    async savePermissions() {
      await saveFoundationRecord('permissions', { role: this.activeRole, permissions: this.permissions })
      this.$message.success('角色权限已保存（模拟接口）')
    },
    permissionCode(module) {
      const codes = { 客户管理: 'customer', 销售管理: 'sales', 财务管理: 'finance', 客房管理: 'room', 护理管理: 'nursing', 仓存管理: 'warehouse', 系统设置: 'system' }
      return `${codes[module] || 'erp'}:record:action`
    }
  }
}
</script>

<style lang="scss" scoped>
.foundation-page { min-height:calc(100vh - 84px); padding:24px; background:#f4f6f9; color:#253247; }
.page-heading { display:flex; align-items:center; justify-content:space-between; margin-bottom:20px; }
.page-heading h1 { margin:5px 0 7px; font-size:25px; }.page-heading p { margin:0; color:#8a96a8; font-size:13px; }.eyebrow { color:#ff6f9c; font-size:12px; font-weight:700; letter-spacing:1px; }.heading-actions { display:flex; align-items:center; gap:8px; }
.content-card { border:0; border-radius:10px; margin-bottom:16px; box-shadow:0 2px 12px rgba(27,45,75,.055); }.card-title { display:flex; align-items:center; justify-content:space-between; font-weight:700; color:#263445; }.card-title>div { display:flex; align-items:center; gap:8px; }.card-title small { color:#9aa5b4; font-weight:400; }
.metric-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:16px; margin-bottom:16px; }.metric-card { display:flex; align-items:center; min-height:94px; padding:18px 22px; background:#fff; border-radius:10px; box-shadow:0 2px 12px rgba(27,45,75,.055); }.metric-card>i { display:grid; place-items:center; width:48px; height:48px; margin-right:15px; border-radius:12px; font-size:22px; }.metric-card div { display:flex; flex-direction:column; }.metric-card b { font-size:26px; }.metric-card span { margin-top:4px; color:#7b8797; font-size:13px; }
.organization-tree { min-height:610px; }.tree-node { flex:1; display:flex; align-items:center; justify-content:space-between; padding-right:6px; }.tree-node i { margin-right:7px; color:#7790ac; }.store-grid { display:grid; grid-template-columns:repeat(2,1fr); gap:12px; }.store-card { padding:16px; border:1px solid #edf0f4; border-radius:9px; background:#fbfcfe; }.store-head { display:flex; align-items:center; gap:10px; }.store-head>div { flex:1; display:flex; flex-direction:column; }.store-head small { margin-top:3px; color:#99a4b2; }.store-icon { display:grid; place-items:center; width:38px; height:38px; border-radius:10px; color:#ff6f9c; background:#fff0f5; }.store-stats { display:grid; grid-template-columns:repeat(3,1fr); padding:15px 0; margin-top:14px; border-top:1px solid #edf0f4; border-bottom:1px solid #edf0f4; }.store-stats span { text-align:center; color:#8a96a8; font-size:12px; }.store-stats b { display:block; margin-bottom:3px; color:#28384d; font-size:18px; }.store-foot { display:flex; justify-content:space-between; align-items:center; padding-top:8px; color:#7d8998; font-size:12px; }
.role-card,.permission-card { min-height:620px; }.scope-line { display:flex; align-items:center; gap:16px; padding:0 0 18px; }.scope-line>span { color:#7b8797; font-size:13px; }.permission-tip { padding:12px; color:#7f8b9c; background:#f8fafc; border-radius:7px; font-size:12px; }.permission-tip i { margin-right:5px; color:#ff6f9c; }
.filter-line { display:flex; align-items:center; gap:10px; flex-wrap:wrap; }.filter-line .el-input { width:260px; }.filter-line .el-select { width:180px; }
.dictionary-types { min-height:590px; }.dictionary-types button { width:100%; display:flex; align-items:center; justify-content:space-between; padding:13px 14px; margin-bottom:7px; border:0; border-radius:8px; color:#455468; background:#f8fafc; cursor:pointer; text-align:left; }.dictionary-types button:hover,.dictionary-types button.active { color:#ff5f90; background:#fff1f6; }.dictionary-types button span { display:flex; flex-direction:column; }.dictionary-types button small { margin-top:3px; color:#9aa5b4; }.color-preview { display:inline-block; width:10px; height:10px; margin-right:6px; border-radius:50%; }.empty-dictionary { padding:80px 0; color:#9aa5b4; text-align:center; }.empty-dictionary i { font-size:42px; }
code { padding:3px 7px; color:#7453d4; background:#f2effc; border-radius:4px; font-size:11px; }
@media (max-width:1000px){.metric-grid{grid-template-columns:repeat(2,1fr)}.store-grid{grid-template-columns:1fr}.heading-actions{display:none}}
@media (max-width:600px){.foundation-page{padding:14px}.page-heading{align-items:flex-start}.metric-grid{grid-template-columns:1fr}.filter-line .el-input,.filter-line .el-select{width:100%}}
</style>


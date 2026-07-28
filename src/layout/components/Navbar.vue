<template>
  <div class="navbar">
    <hamburger id="hamburger-container" :is-active="sidebar.opened" class="hamburger-container" @toggleClick="toggleSideBar" />
    <div class="menu-label">全部菜单</div>
    <div class="global-search"><i class="el-icon-search" /><input v-model="keyword" placeholder="请输入客户姓名、电话或房间号" @keyup.enter="searchCustomer"></div>
    <div class="right-menu">
      <el-select v-if="device !== 'mobile'" v-model="store" class="store-select" size="mini">
        <el-option v-for="item in allowedStores" :key="item.id" :label="item.name" :value="item.name" />
      </el-select>
      <el-tooltip content="帮助文档" placement="bottom"><span class="nav-action"><i class="el-icon-question" /></span></el-tooltip>
      <el-badge :value="319" :max="99" class="message-badge"><span class="nav-action"><i class="el-icon-message-solid" /></span></el-badge>
      <el-dropdown class="avatar-container" trigger="click">
        <div class="user-chip"><span class="avatar">{{ avatarText }}</span><div><b>{{ name || 'admin' }}</b><small>{{ roleLabel }}</small></div><i class="el-icon-arrow-down" /></div>
        <el-dropdown-menu slot="dropdown">
          <router-link to="/profile/index"><el-dropdown-item icon="el-icon-user">个人中心</el-dropdown-item></router-link>
          <router-link to="/"><el-dropdown-item icon="el-icon-s-home">系统首页</el-dropdown-item></router-link>
          <el-dropdown-item icon="el-icon-key">修改密码</el-dropdown-item>
          <el-dropdown-item divided icon="el-icon-switch-button" @click.native="logout">退出登录</el-dropdown-item>
        </el-dropdown-menu>
      </el-dropdown>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import Hamburger from '@/components/Hamburger'

export default {
  components: { Hamburger },
  data() {
    return {
      keyword: '',
      store: '',
      storeOptions: [
        { id: 1, name: '中心广场旗舰店' },
        { id: 2, name: '黄河路轻奢店' }
      ]
    }
  },
  computed: {
    ...mapGetters(['sidebar', 'device', 'name', 'roles', 'roleNames', 'storeIds']),
    allowedStores() {
      if (this.roles.includes('SYS_ADMIN')) return this.storeOptions
      return this.storeOptions.filter(item => this.storeIds.map(Number).includes(item.id))
    },
    avatarText() {
      return (this.name || '管').slice(0, 1)
    },
    roleLabel() {
      const labels = {
        SYS_ADMIN: '系统管理员',
        SALES_MANAGER: '销售经理',
        RECOVERY_THERAPIST: '产康师',
        HOUSEKEEPER: '客房管家'
      }
      return this.roleNames[0] || labels[this.roles[0]] || '业务人员'
    }
  },
  watch: {
    allowedStores: {
      immediate: true,
      handler(stores) {
        if (!stores.some(item => item.name === this.store)) {
          this.store = stores.length ? stores[0].name : ''
        }
      }
    }
  },
  methods: {
    toggleSideBar() { this.$store.dispatch('app/toggleSideBar') },
    searchCustomer() { if (!this.keyword) return this.$message.warning('请输入客户姓名、电话或房间号'); this.$router.push({ path: '/customer/item-1', query: { keyword: this.keyword }}) },
    async logout() { await this.$store.dispatch('user/logout'); this.$router.push(`/login?redirect=${this.$route.fullPath}`) }
  }
}
</script>

<style lang="scss" scoped>
.navbar{height:58px;display:flex;align-items:center;position:relative;background:#fffdf9;border-bottom:1px solid rgba(140,106,54,.16);box-shadow:0 8px 24px -24px rgba(74,55,26,.55)}.hamburger-container{height:58px;line-height:58px;cursor:pointer;transition:.2s}.hamburger-container:hover{background:#fbf4e8}.menu-label{font-size:13px;color:#6e665a;padding-right:24px;border-right:1px solid #eee7da}.global-search{height:36px;width:330px;margin-left:22px;display:flex;align-items:center;gap:9px;color:#a89e8d}.global-search input{border:0;outline:0;width:100%;font-size:12px;color:#2b2620;background:transparent}.right-menu{margin-left:auto;height:100%;display:flex;align-items:center;gap:12px;padding-right:20px}.store-select{width:150px}.nav-action{display:grid;place-items:center;width:34px;height:34px;border-radius:8px;color:#8f8474;cursor:pointer}.nav-action:hover{background:#f4ecdd;color:#8c6a36}.message-badge{display:flex}.user-chip{display:flex;align-items:center;gap:9px;padding-left:8px;cursor:pointer}.avatar{width:34px;height:34px;display:grid;place-items:center;border-radius:10px;color:#fff;background:linear-gradient(135deg,#e9d4a4,#b8945a 52%,#8c6a36);font-size:13px}.user-chip>div{display:flex;flex-direction:column;line-height:1.3}.user-chip b{font-size:12px;color:#2b2620}.user-chip small{font-size:9px;color:#a89e8d}.user-chip>i{font-size:10px;color:#a89e8d}@media(max-width:900px){.global-search,.menu-label,.store-select{display:none}.right-menu{gap:5px;padding-right:10px}.user-chip>div,.user-chip>i{display:none}}
</style>

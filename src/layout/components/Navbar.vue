<template>
  <div class="navbar">
    <hamburger
      id="hamburger-container"
      :is-active="sidebar.opened"
      class="hamburger-container"
      @toggleClick="toggleSideBar"
    />

    <el-popover
      ref="searchPopover"
      v-model="searchOpen"
      placement="bottom-start"
      width="520"
      trigger="manual"
      popper-class="navbar-search-popper"
    >
      <div class="search-panel">
        <div class="search-panel__head">
          <b>客户与房间快速查询</b>
          <div class="search-panel__head-actions">
            <span>查询范围：{{ searchScopeLabel }}</span>
            <button type="button" class="search-panel__close" aria-label="关闭搜索" @click="closeSearch">
              <i class="el-icon-close" />
            </button>
          </div>
        </div>
        <div v-if="searchLoading" class="search-empty"><i class="el-icon-loading" /> 正在读取最新客户与房态数据</div>
        <template v-else-if="keyword.trim()">
          <section v-if="roomSearchResults.length" class="search-group">
            <div class="search-group__title">
              <span><i class="el-icon-house" /> 房间结果</span>
              <em>展示 {{ roomSearchResults.length }} / 共 {{ roomSearchMatches.length }}</em>
            </div>
            <button
              v-for="item in roomSearchResults"
              :key="`room-${item.id}`"
              type="button"
              class="search-result search-result--room"
              @click="openRoomResult(item)"
            >
              <span class="search-result__avatar"><i class="el-icon-house" /></span>
              <span class="search-result__main">
                <b>房间 {{ item.room_no }}</b>
                <small>{{ item.room_type || '未设置房型' }} · {{ item.store_name }}</small>
              </span>
              <span class="search-result__side">
                <em>{{ item.status || '状态未知' }}</em>
                <small>{{ item.customer_name || '当前无入住客户' }}</small>
              </span>
              <i class="el-icon-arrow-right" />
            </button>
            <button type="button" class="search-view-all" @click="showAllSearch('room')">
              查看全部 {{ roomSearchMatches.length }} 条房间结果
              <i class="el-icon-arrow-right" />
            </button>
          </section>
          <section v-if="customerSearchResults.length" class="search-group">
            <div class="search-group__title">
              <span><i class="el-icon-user" /> 客户结果</span>
              <em>展示 {{ customerSearchResults.length }} / 共 {{ customerSearchMatches.length }}</em>
            </div>
            <button
              v-for="item in customerSearchResults"
              :key="`customer-${item.id}`"
              type="button"
              class="search-result"
              @click="openCustomer(item)"
            >
              <span class="search-result__avatar">{{ item.name.slice(0, 1) }}</span>
              <span class="search-result__main">
                <b>{{ item.name }}</b>
                <small>{{ item.phone || '未留手机号' }} · {{ item.customer_no }}</small>
              </span>
              <span class="search-result__side">
                <em>{{ item.room || '未分房' }}</em>
                <small>{{ item.store_name }}</small>
              </span>
              <i class="el-icon-arrow-right" />
            </button>
            <button type="button" class="search-view-all" @click="showAllSearch('customer')">
              查看全部 {{ customerSearchMatches.length }} 条客户结果
              <i class="el-icon-arrow-right" />
            </button>
          </section>
          <div v-if="!hasSearchResults" class="search-empty">没有找到匹配的客户或房间，请检查关键词</div>
        </template>
        <div v-else class="search-empty">输入姓名、手机号、客户编号或房间号开始查询</div>
      </div>

      <div ref="globalSearch" slot="reference" class="global-search" :class="{ 'is-active': searchOpen }">
        <i class="el-icon-search" />
        <input
          v-model="keyword"
          placeholder="搜索客户、电话或房间号"
          @focus="openSearch"
          @input="handleSearchInput"
          @keyup.enter="searchCustomer"
          @keyup.esc="closeSearch"
        >
        <button
          v-if="keyword"
          type="button"
          class="search-clear"
          aria-label="清空搜索"
          @click="clearSearch"
        ><i class="el-icon-close" /></button>
      </div>
    </el-popover>

    <el-drawer
      :title="allResultsTitle"
      :visible.sync="allResultsOpen"
      size="560px"
      custom-class="navbar-search-drawer"
      append-to-body
    >
      <div class="all-results">
        <div class="all-results__summary">
          {{ searchScopeLabel }} · 关键词“{{ keyword }}”共找到 {{ allResults.length }} 条{{ allResultsType === 'room' ? '房间' : '客户' }}结果
        </div>
        <div class="all-results__list">
          <button
            v-for="item in allResults"
            :key="`${allResultsType}-${item.id}`"
            type="button"
            class="search-result"
            :class="{ 'search-result--room': allResultsType === 'room' }"
            @click="openAllResult(item)"
          >
            <span class="search-result__avatar">
              <i v-if="allResultsType === 'room'" class="el-icon-house" />
              <template v-else>{{ item.name.slice(0, 1) }}</template>
            </span>
            <span class="search-result__main">
              <b>{{ allResultsType === 'room' ? `房间 ${item.room_no}` : item.name }}</b>
              <small v-if="allResultsType === 'room'">{{ item.room_type || '未设置房型' }} · {{ item.store_name }}</small>
              <small v-else>{{ item.phone || '未留手机号' }} · {{ item.customer_no }}</small>
            </span>
            <span class="search-result__side">
              <em>{{ allResultsType === 'room' ? (item.status || '状态未知') : (item.room || '未分房') }}</em>
              <small>{{ allResultsType === 'room' ? (item.customer_name || '当前无入住客户') : item.store_name }}</small>
            </span>
            <i class="el-icon-arrow-right" />
          </button>
        </div>
      </div>
    </el-drawer>

    <div class="right-menu">
      <div class="store-switch">
        <span>当前门店</span>
        <el-select v-model="storeId" size="mini" @change="handleStoreChange">
          <el-option
            v-for="item in allowedStores"
            :key="item.id"
            :label="item.name"
            :value="String(item.id)"
          />
        </el-select>
      </div>

      <notification-center />

      <el-dropdown class="avatar-container" trigger="click">
        <div class="user-chip">
          <span class="avatar">{{ avatarText }}</span>
          <div><b>{{ name || 'admin' }}</b><small>{{ roleLabel }}</small></div>
          <i class="el-icon-arrow-down" />
        </div>
        <el-dropdown-menu slot="dropdown">
          <router-link to="/profile/index"><el-dropdown-item icon="el-icon-user">个人中心</el-dropdown-item></router-link>
          <router-link to="/"><el-dropdown-item icon="el-icon-s-home">系统首页</el-dropdown-item></router-link>
          <el-dropdown-item divided icon="el-icon-switch-button" @click.native="logout">退出登录</el-dropdown-item>
        </el-dropdown-menu>
      </el-dropdown>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import Hamburger from '@/components/Hamburger'
import NotificationCenter from './NotificationCenter'
import { getMvpList } from '@/api/erp-mvp'

export default {
  components: { Hamburger, NotificationCenter },
  data() {
    return {
      keyword: '',
      searchOpen: false,
      searchLoading: false,
      searchLoaded: false,
      searchLoadedAt: 0,
      searchRows: [],
      searchRoomRows: [],
      allResultsOpen: false,
      allResultsType: 'room',
      storeOptions: [
        { id: 'all', name: '全部门店' },
        { id: '1', name: '中心广场旗舰店' },
        { id: '2', name: '黄河路轻奢店' }
      ]
    }
  },
  computed: {
    ...mapGetters(['sidebar', 'device', 'name', 'roles', 'roleNames', 'storeIds', 'currentStoreId']),
    storeId: {
      get() {
        return String(this.currentStoreId || 'all')
      },
      set(value) {
        this.$store.dispatch('app/setCurrentStore', String(value))
      }
    },
    allowedStores() {
      if (this.roles.includes('SYS_ADMIN') || this.name === 'admin') return this.storeOptions
      const ids = this.storeIds.map(String)
      return this.storeOptions.filter(item => item.id !== 'all' && ids.includes(item.id))
    },
    customerSearchMatches() {
      const keyword = this.keyword.trim().toLowerCase()
      if (!keyword) return []
      return this.searchRows
        .filter(item => this.storeId === 'all' || String(item.store_id) === this.storeId)
        .filter(item => [
          item.name,
          item.phone,
          item.customer_no,
          item.room,
          item.store_name
        ].some(value => String(value || '').toLowerCase().includes(keyword)))
    },
    customerSearchResults() {
      return this.customerSearchMatches.slice(0, 5)
    },
    roomSearchMatches() {
      const keyword = this.keyword.trim().toLowerCase()
      if (!keyword) return []
      return this.searchRoomRows
        .filter(item => this.storeId === 'all' || String(item.store_id) === this.storeId)
        .filter(item => [
          item.room_no,
          item.room_type,
          item.status,
          item.customer_name,
          item.store_name
        ].some(value => String(value || '').toLowerCase().includes(keyword)))
    },
    roomSearchResults() {
      return this.roomSearchMatches.slice(0, 5)
    },
    allResults() {
      return this.allResultsType === 'room' ? this.roomSearchMatches : this.customerSearchMatches
    },
    allResultsTitle() {
      return this.allResultsType === 'room' ? '全部房间搜索结果' : '全部客户搜索结果'
    },
    searchScopeLabel() {
      const current = this.allowedStores.find(item => item.id === this.storeId)
      return current ? current.name : '当前门店'
    },
    hasSearchResults() {
      return this.customerSearchResults.length > 0 || this.roomSearchResults.length > 0
    },
    avatarText() {
      return (this.name || '管').slice(0, 1)
    },
    roleLabel() {
      const labels = {
        SYS_ADMIN: '系统管理员',
        admin: '系统管理员',
        SALES_MANAGER: '销售经理',
        RECOVERY_THERAPIST: '产康师',
        HOUSEKEEPER: '客房管家'
      }
      if (this.name === 'admin') return '系统管理员'
      return this.roleNames[0] || labels[this.roles[0]] || '业务人员'
    }
  },
  watch: {
    '$route.query.storeId': {
      immediate: true,
      handler(value) {
        const storeId = String(value || '')
        if (storeId && storeId !== this.storeId && this.allowedStores.some(item => item.id === storeId)) {
          this.$store.dispatch('app/setCurrentStore', storeId)
        }
      }
    },
    allowedStores: {
      immediate: true,
      handler(stores) {
        if (!stores.length) return
        if (!stores.some(item => item.id === this.storeId)) {
          this.$store.dispatch('app/setCurrentStore', stores[0].id)
        }
      }
    }
  },
  mounted() {
    document.addEventListener('click', this.handleSearchOutside, true)
  },
  beforeDestroy() {
    document.removeEventListener('click', this.handleSearchOutside, true)
  },
  methods: {
    toggleSideBar() {
      this.$store.dispatch('app/toggleSideBar')
    },
    async openSearch() {
      this.searchOpen = true
      await this.loadSearchData(true)
    },
    handleSearchInput() {
      this.searchOpen = true
      if (!this.searchLoaded || Date.now() - this.searchLoadedAt > 15000) this.loadSearchData()
    },
    closeSearch() {
      this.searchOpen = false
    },
    handleSearchOutside(event) {
      if (!this.searchOpen) return
      const searchElement = this.$refs.globalSearch
      const popover = this.$refs.searchPopover
      const popperElement = popover && popover.popperElm
      if (searchElement && searchElement.contains(event.target)) return
      if (popperElement && popperElement.contains(event.target)) return
      this.closeSearch()
    },
    clearSearch() {
      this.keyword = ''
      this.searchOpen = true
    },
    showAllSearch(type) {
      this.allResultsType = type
      this.searchOpen = false
      this.allResultsOpen = true
    },
    openAllResult(item) {
      if (this.allResultsType === 'room') return this.openRoomResult(item)
      return this.openCustomer(item)
    },
    async loadSearchData(force = false) {
      if ((!force && this.searchLoaded) || this.searchLoading) return
      this.searchLoading = true
      try {
        const optional = promise => promise.catch(() => ({ data: { list: [] }}))
        const [customers, rooms, bookings] = await Promise.all([
          getMvpList('customers'),
          optional(getMvpList('rooms')),
          optional(getMvpList('bookings'))
        ])
        const roomByCustomer = (bookings.data.list || []).reduce((result, item) => {
          if (item.status !== '已取消') result[item.customer_id] = item.room_no
          return result
        }, {})
        this.searchRows = (customers.data.list || []).map(item => ({
          ...item,
          room: roomByCustomer[item.id] || ''
        }))
        this.searchRoomRows = rooms.data.list || []
        this.searchLoaded = true
        this.searchLoadedAt = Date.now()
      } catch (error) {
        this.$message.error('客户与房间查询数据加载失败，请稍后重试')
      } finally {
        this.searchLoading = false
      }
    },
    searchCustomer() {
      if (!this.keyword.trim()) {
        this.searchOpen = true
        return this.$message.warning('请输入客户姓名、电话或房间号')
      }
      const total = this.customerSearchResults.length + this.roomSearchResults.length
      if (total === 1 && this.customerSearchResults.length === 1) return this.openCustomer(this.customerSearchResults[0])
      if (total === 1 && this.roomSearchResults.length === 1) return this.openRoomResult(this.roomSearchResults[0])
      this.searchOpen = true
    },
    openCustomer(item) {
      this.searchOpen = false
      this.allResultsOpen = false
      this.keyword = ''
      this.$store.dispatch('app/setCurrentStore', String(item.store_id))
      this.$router.push({
        path: '/customer/signing-workbench',
        query: {
          customerId: String(item.id),
          storeId: String(item.store_id),
          store: item.store_name,
          open: 'contracts'
        }
      }).catch(() => {})
    },
    openRoomResult(item) {
      this.searchOpen = false
      this.allResultsOpen = false
      this.keyword = ''
      this.$store.dispatch('app/setCurrentStore', String(item.store_id))
      this.$router.push({
        // The legacy generic room route no longer carries the scoped room-map
        // behaviour.  Global search must land on the restored room-status map
        // with the chosen store and room pre-filtered.
        path: '/mvp/room-map',
        query: {
          room: item.room_no,
          storeId: String(item.store_id),
          store: item.store_name
        }
      }).catch(() => {})
    },
    handleStoreChange(value) {
      const current = this.allowedStores.find(item => item.id === String(value))
      const query = { ...this.$route.query, storeId: String(value) }
      if (current && current.id !== 'all') query.store = current.name
      else delete query.store
      this.$router.replace({ path: this.$route.path, query }).catch(() => {})
      this.searchOpen = false
      this.$message.success(`已切换到${current ? current.name : '当前门店'}`)
    },
    async logout() {
      await this.$store.dispatch('user/logout')
      this.$router.push(`/login?redirect=${this.$route.fullPath}`)
    }
  }
}
</script>

<style lang="scss">
.navbar-search-popper {
  padding: 8px !important;
  border-color: #e7ddcd !important;
  box-shadow: 0 14px 36px rgba(61, 47, 27, .16) !important;
}
.search-panel {
  max-height: min(520px, 68vh);
  overflow-y: auto;
  overscroll-behavior: contain;
}
.search-panel__head {
  position: sticky;
  z-index: 2;
  top: 0;
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding: 8px 10px 10px;
  border-bottom: 1px solid #eee7dc;
  background: #fff;
}
.search-panel__head b { color: #2b2620; font-size: 14px; }
.search-panel__head span { color: #9a8f7f; font-size: 11px; }
.search-panel__head-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.search-panel__close {
  display: grid;
  place-items: center;
  width: 24px;
  height: 24px;
  padding: 0;
  border: 0;
  border-radius: 7px;
  color: #8f8373;
  background: transparent;
  cursor: pointer;
}
.search-panel__close:hover {
  color: #684b22;
  background: #f5ead6;
}
.search-group + .search-group { margin-top: 5px; padding-top: 5px; border-top: 1px solid #eee7dc; }
.search-group__title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px 4px;
  color: #76654c;
  font-size: 11px;
  font-weight: 700;
}
.search-group__title span { display: flex; align-items: center; gap: 5px; }
.search-group__title em {
  min-width: 20px;
  padding: 1px 6px;
  border-radius: 9px;
  color: #8c6a36;
  background: #f5ecdc;
  font-style: normal;
  text-align: center;
}
.search-result {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 10px;
  border: 0;
  border-bottom: 1px solid #f2ece2;
  border-radius: 7px;
  color: #443a2e;
  background: transparent;
  cursor: pointer;
  text-align: left;
}
.search-result:hover { background: #fbf5eb; }
.search-result--room { background: #fffdf8; }
.search-result--room .search-result__avatar {
  color: #8c6a36;
  background: #f5ead6;
}
.search-result__avatar {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  margin-right: 10px;
  border-radius: 9px;
  color: #fff;
  background: linear-gradient(135deg, #d6bb85, #8c6a36);
}
.search-result__main { display: flex; flex: 1; flex-direction: column; gap: 4px; }
.search-result__main b { font-size: 13px; }
.search-result__main small,
.search-result__side small { color: #9a8f7f; font-size: 11px; }
.search-result__side {
  display: flex;
  min-width: 126px;
  margin-right: 8px;
  flex-direction: column;
  gap: 4px;
  text-align: right;
}
.search-result__side em { color: #8c6a36; font-size: 12px; font-style: normal; font-weight: 600; }
.search-view-all {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 10px;
  border: 0;
  color: #8c6a36;
  background: #fbf5eb;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  gap: 5px;
}
.search-view-all:hover { color: #684b22; background: #f5ead6; }
.navbar-search-drawer {
  background: #fffdf9;
}
.navbar-search-drawer .el-drawer__header {
  margin: 0;
  padding: 22px 24px 18px;
  border-bottom: 1px solid #eee7dc;
  color: #2b2620;
  font-size: 18px;
  font-weight: 700;
}
.navbar-search-drawer .el-drawer__body {
  overflow: hidden;
}
.all-results {
  display: flex;
  height: 100%;
  padding: 0 22px 22px;
  box-sizing: border-box;
  flex-direction: column;
}
.all-results__summary {
  padding: 14px 4px;
  color: #76654c;
  font-size: 13px;
}
.all-results__list {
  overflow-y: auto;
  border: 1px solid #eee7dc;
  border-radius: 12px;
  background: #fff;
}
.search-empty { padding: 24px 12px; color: #9a8f7f; text-align: center; }
</style>

<style lang="scss" scoped>
.navbar {
  position: relative;
  display: flex;
  align-items: center;
  height: 58px;
  border-bottom: 1px solid rgba(140, 106, 54, .16);
  background: #fffdf9;
  box-shadow: 0 8px 24px -24px rgba(74, 55, 26, .55);
}
.hamburger-container {
  height: 58px;
  line-height: 58px;
  cursor: pointer;
  transition: .2s;
}
.hamburger-container:hover { background: #fbf4e8; }
.global-search {
  display: flex;
  align-items: center;
  width: min(420px, 38vw);
  height: 36px;
  margin-left: 12px;
  padding: 0 11px;
  gap: 9px;
  border: 1px solid transparent;
  border-radius: 9px;
  color: #a89e8d;
  background: #f8f4ed;
  transition: .2s;
}
.global-search:hover,
.global-search.is-active {
  border-color: #d7c29a;
  background: #fff;
  box-shadow: 0 0 0 3px rgba(184, 148, 90, .09);
}
.global-search input {
  width: 100%;
  border: 0;
  outline: 0;
  color: #2b2620;
  background: transparent;
  font-size: 12px;
}
.search-clear {
  display: grid;
  place-items: center;
  width: 24px;
  height: 24px;
  padding: 0;
  border: 0;
  border-radius: 6px;
  color: #9a8f7f;
  background: transparent;
  cursor: pointer;
}
.search-clear:hover { color: #8c6a36; background: #f4ecdd; }
.right-menu {
  display: flex;
  align-items: center;
  height: 100%;
  margin-left: auto;
  padding-right: 20px;
  gap: 16px;
}
.store-switch {
  display: flex;
  align-items: center;
  gap: 8px;
}
.store-switch > span { color: #8f8474; font-size: 11px; white-space: nowrap; }
.store-switch .el-select { width: 158px; }
.store-switch ::v-deep .el-input__inner {
  border-color: #e2d8c7;
  border-radius: 8px;
  color: #544838;
  background: #fff;
}
.user-chip {
  display: flex;
  align-items: center;
  padding-left: 8px;
  gap: 9px;
  cursor: pointer;
}
.avatar {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 10px;
  color: #fff;
  background: linear-gradient(135deg, #e9d4a4, #b8945a 52%, #8c6a36);
  font-size: 13px;
}
.user-chip > div { display: flex; flex-direction: column; line-height: 1.3; }
.user-chip b { color: #2b2620; font-size: 12px; }
.user-chip small { color: #a89e8d; font-size: 9px; }
.user-chip > i { color: #a89e8d; font-size: 10px; }
@media (max-width: 900px) {
  .global-search { width: min(54vw, 360px); }
  .store-switch { display: none; }
  .right-menu { padding-right: 10px; gap: 5px; }
  .user-chip > div,
  .user-chip > i { display: none; }
}
</style>

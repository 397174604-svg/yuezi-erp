import { defineStore } from 'pinia'

// 应用壳状态：侧边栏折叠、当前门店过滤维度（多门店总部视角用）。
export const useAppStore = defineStore('app', {
  state: () => ({
    collapsed: false,
    storeId: null as number | null, // 顶部门店切换；null=本租户全门店
    stores: [] as Array<{ id: number; name: string }>,
  }),
  actions: {
    toggle() {
      this.collapsed = !this.collapsed
    },
    setStores(list: any[]) {
      this.stores = (list || []).map((s) => ({ id: s.id, name: s.name }))
    },
  },
})

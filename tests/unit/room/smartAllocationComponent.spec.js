jest.mock('@/api/erp-room', () => ({
  getRoomModuleData: jest.fn(),
  saveRoomModuleRecord: jest.fn()
}))

import { shallowMount } from '@vue/test-utils'
import { getRoomModuleData } from '@/api/erp-room'
import SmartRoomAllocation from '@/views/erp/room-workbench/SmartRoomAllocation.vue'

const config = {
  defaultFilters: {
    store: '黄河路轻奢店',
    startDate: '2099-01-01',
    days: 28,
    endDate: '2099-01-29'
  },
  filters: [{ key: 'roomType', options: ['大床房', '套房'] }]
}

const rooms = [
  {
    id: 1,
    room: '601',
    store: '奇德芬芳·黄河路店',
    roomType: '套房',
    roomNoConfirmed: true,
    algorithmEnabled: true,
    status: '空闲',
    bookings: [],
    allocationBlocks: []
  },
  {
    id: 2,
    room: '501',
    store: '奇德芬芳·黄河路店',
    roomType: '大床房',
    roomNoConfirmed: true,
    algorithmEnabled: true,
    status: '空闲',
    bookings: [],
    allocationBlocks: []
  }
]

const packages = [
  {
    basePackageCode: 'YH-PLUS',
    packageNo: 'YH-PLUS@28',
    packageName: '黄河路臻享套餐',
    store: '奇德芬芳·黄河路店',
    days: 28,
    allowedRoomTypes: ['套房']
  },
  {
    basePackageCode: 'YH-PLUS',
    packageNo: 'YH-PLUS@42',
    packageName: '黄河路臻享套餐',
    store: '黄河路轻奢店',
    days: 42,
    allowedRoomTypes: ['大床房']
  }
]

describe('SmartRoomAllocation package change', () => {
  it('requeries on package change and refreshes applied filters without losing recommendations', async() => {
    getRoomModuleData.mockResolvedValue({ data: { list: rooms, packages, stores: [{ name: '黄河路轻奢店' }] }})
    const wrapper = shallowMount(SmartRoomAllocation, {
      propsData: { config, canBook: false },
      mocks: { $route: { query: {}}}
    })

    await wrapper.vm.loadData(true)
    getRoomModuleData.mockClear()
    wrapper.vm.filters.packageNo = 'YH-PLUS@42'
    await wrapper.vm.handlePackageChange()

    expect(getRoomModuleData).toHaveBeenCalledTimes(1)
    expect(getRoomModuleData.mock.calls[0][1].packageNo).toBe('YH-PLUS@42')
    expect(wrapper.vm.appliedFilters.packageNo).toBe('YH-PLUS@42')
    expect(wrapper.vm.appliedFilters.days).toBe('42')
    expect(wrapper.vm.singleRecommendations).toHaveLength(1)
    expect(wrapper.vm.singleRecommendations[0].rooms[0].room).toBe('501')
  })
})

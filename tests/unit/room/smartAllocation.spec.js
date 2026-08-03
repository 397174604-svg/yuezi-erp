import {
  roomMatchesAllocationPackage,
  uniqueAllocationPackages
} from '@/views/erp/room-workbench/smart-allocation-utils'

const storeMatches = (requested, actual) => (
  requested === actual || (requested.includes('黄河路') && actual.includes('黄河路'))
)

describe('Smart room allocation package scope', () => {
  it('deduplicates one Yellow River business package across store aliases and merges room types', () => {
    const packages = uniqueAllocationPackages([
      {
        basePackageCode: 'YH-PLUS',
        packageName: '黄河路臻享套餐',
        store: '奇德芬芳·黄河路店',
        days: 28,
        allowedRoomTypes: ['大床房'],
        referencePrice: 68800
      },
      {
        basePackageCode: 'YH-PLUS',
        packageName: '黄河路臻享套餐',
        store: '黄河路轻奢店',
        days: 28,
        allowedRoomTypes: ['套房'],
        referencePrice: 68800
      },
      {
        basePackageCode: 'YH-PLUS',
        packageName: '黄河路臻享套餐',
        store: '黄河路轻奢店',
        days: 42,
        allowedRoomTypes: ['大床房'],
        referencePrice: 95800
      }
    ], '黄河路轻奢店', storeMatches)

    expect(packages.map(item => item.packageNo)).toEqual(['YH-PLUS@28', 'YH-PLUS@42'])
    expect(packages[0].allowedRoomTypes).toEqual(['大床房', '套房'])
  })

  it('uses selected package codes or allowed room types to filter rooms', () => {
    const selectedPackage = {
      basePackageCode: 'YH-PLUS',
      packageNo: 'YH-PLUS@28',
      allowedRoomTypes: ['套房']
    }

    expect(roomMatchesAllocationPackage({
      allowedPackageCodes: ['YH-PLUS'],
      roomType: '大床房'
    }, selectedPackage)).toBe(true)
    expect(roomMatchesAllocationPackage({
      allowedPackageCodes: ['YH-BASIC'],
      roomType: '套房'
    }, selectedPackage)).toBe(false)
    expect(roomMatchesAllocationPackage({
      roomType: '套房'
    }, selectedPackage)).toBe(true)
    expect(roomMatchesAllocationPackage({
      roomType: '大床房'
    }, selectedPackage)).toBe(false)
    expect(roomMatchesAllocationPackage({ roomType: '大床房' }, null)).toBe(true)
  })
})

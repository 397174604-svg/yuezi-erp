export function allocationPackageNo(item) {
  if (item.packageNo) return String(item.packageNo)
  const code = item.basePackageCode || item.packageCode || item.packageName || 'package'
  const days = item.days === undefined || item.days === null ? '' : `@${item.days}`
  return `${code}${days}`
}

export function uniqueAllocationPackages(packages, storeName, storeMatches) {
  const unique = new Map()
  const source = packages || []
  source
    .filter(item => !storeName || storeMatches(storeName, item.store))
    .forEach(item => {
      const packageNo = allocationPackageNo(item)
      const existing = unique.get(packageNo)
      const allowedRoomTypes = Array.from(new Set([
        ...((existing && existing.allowedRoomTypes) || []),
        ...((item.allowedRoomTypes) || [])
      ].filter(Boolean)))
      if (!existing) {
        unique.set(packageNo, { ...item, packageNo, allowedRoomTypes })
        return
      }
      const prices = [existing.referencePrice, item.referencePrice]
        .filter(value => value !== undefined && value !== null && value !== '')
        .map(Number)
        .filter(value => Number.isFinite(value))
      unique.set(packageNo, {
        ...existing,
        allowedRoomTypes,
        referencePrice: prices.length ? Math.min(...prices) : existing.referencePrice
      })
    })
  return Array.from(unique.values())
}

export function roomMatchesAllocationPackage(room, selectedPackage) {
  if (!selectedPackage) return true
  const packageCode = String(
    selectedPackage.basePackageCode || selectedPackage.packageCode || selectedPackage.packageNo || ''
  ).split('@')[0]
  const allowedPackageCodes = (room.allowedPackageCodes || []).map(String)
  if (allowedPackageCodes.length) {
    return allowedPackageCodes.includes(packageCode) || allowedPackageCodes.includes(String(selectedPackage.packageNo || ''))
  }
  const allowedRoomTypes = selectedPackage.allowedRoomTypes || []
  return !allowedRoomTypes.length || allowedRoomTypes.includes(room.roomType)
}

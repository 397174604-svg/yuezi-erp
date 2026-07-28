<script>
import { REMOTE as R_staff } from '@/common/staff/remote.js'
import { REMOTE as R_rehab } from '@/common/rehab/remote.js'
import { REMOTE as R_beauty } from '@/common/beauty/remote.js'
import { REMOTE as R_mom } from '@/common/mom/remote.js'
import { EMPTY as E_staff } from '@/common/staff/data.js'
import { EMPTY as E_rehab } from '@/common/rehab/data.js'
import { EMPTY as E_beauty } from '@/common/beauty/data.js'
import { EMPTY as E_mom } from '@/common/mom/data.js'
export default {
  globalData: { data: { ...E_staff, ...E_rehab, ...E_beauty, ...E_mom }, live: false },
  onLaunch() {
    let base = (import.meta.env && import.meta.env.VITE_MP_API) || 'http://127.0.0.1:8799'  // 小程序端后端地址（构建时注入；开发者工具/真机连本机局域网 IP）
    // #ifdef H5
    const q = new URLSearchParams(location.search).get('api')
    // 生产走同域；若应用挂在 /yuezi 子路径，API 用同前缀（nginx 反代该前缀→后端）。本地 dev 连 :8799。
    const seg = location.pathname.split('/').filter(Boolean)[0]
    const pfx = (seg && seg !== 'admin' && seg.indexOf('.') < 0) ? '/' + seg : ''
    base = q || (/^5\d\d\d$/.test(location.port) ? ('http://' + (location.hostname || '127.0.0.1') + ':8799') : (location.origin + pfx))
    // #endif
    ;[R_staff, R_rehab, R_beauty, R_mom].forEach((r) => { if (!r.baseUrl) r.baseUrl = base })
  }
}
</script>

<style lang="scss">
/* #ifdef H5 */
@media screen and (min-width: 500px) {
  uni-app { max-width: 480px; margin: 0 auto; box-shadow: 0 0 0 1px rgba(74,56,24,.06), 0 24rpx 80rpx rgba(74,56,24,.10); background: $ivory; }
  uni-tabbar.uni-tabbar-bottom, .uni-tabbar, .cartbar, .mask { left: 50% !important; right: auto !important; width: 480px !important; margin-left: -240px !important; box-sizing: border-box; }
}
/* #endif */
page { background: $ivory; color: $ink; font-family: $font-sans; font-size: 28rpx; line-height: 1.6; }
.yz-card { background: $paper; border: 1rpx solid $hair; border-radius: $radius-md; padding: 28rpx; box-shadow: 0 20rpx 60rpx -36rpx rgba(74,56,24,.45); }
.yz-serif { font-family: $font-display; color: $gold-deep; }
.yz-tag { font-size: 21rpx; padding: 8rpx 16rpx; border-radius: 40rpx; border: 1rpx solid $hair-s; color: $gold-deep; }
.yz-tag--solid { background: linear-gradient(135deg,#E9D4A4,#9C7838); color: #fff; border: none; }
</style>

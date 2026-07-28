<script>
import { EMPTY } from '@/common/data.js'
import { REMOTE, loadDashboard, ensureAuth } from '@/common/remote.js'
// baseUrl 自适应：?api=/VITE_API_BASE 覆盖 > 本地 dev(5xxx 端口)连本地中台 8799 > 生产同域 location.origin(+子路径前缀走 nginx 反代)。换域名无需改代码。
function resolveH5Base(override) {
  if (override) return override
  if (import.meta.env && import.meta.env.VITE_API_BASE) return import.meta.env.VITE_API_BASE
  // 本地静态服务既可能跑在 Vite 的 5xxx，也可能由 dev-up 跑在 8788。
  // 本机访问统一连 8799，避免把 /apps/h5dist/staff 误当成 API 前缀。
  if (['127.0.0.1', 'localhost'].includes(location.hostname)) return `http://${location.hostname}:8799`
  const seg = location.pathname.split('/').filter(Boolean)[0] || ''
  return location.origin + (seg && !seg.includes('.') && seg !== 'api' ? '/' + seg : '')
}
export default {
  globalData: { data: EMPTY, live: false }, // data 初始为空壳；onLaunch 用后端真实数据填充
  async onLaunch() {
    // 数据全部来自后端中台：注入 baseUrl + 租户/门店身份后由 loadDashboard 拉真实数据。
    // 例：REMOTE.baseUrl = 'https://api.example.com'; REMOTE.tenantId = 1; REMOTE.storeId = 1; REMOTE.staffId = 当前员工
    // #ifdef H5
    if (!REMOTE.baseUrl) REMOTE.baseUrl = resolveH5Base(new URLSearchParams(location.search).get('api'))
    // #endif
    // #ifndef H5
    // 小程序无 location：开发期连本地中台（开发者工具需勾「不校验合法域名」）；上线改为已配置 request 合法域名的 HTTPS 域名
    if (!REMOTE.baseUrl) REMOTE.baseUrl = (import.meta.env && import.meta.env.VITE_MP_API) || 'http://127.0.0.1:8799' // 换域名=构建期设 VITE_MP_API=https://你的域名
    // #endif
    if (REMOTE.baseUrl) {
      // 登录闸门：ensureAuth 内含 #ifdef H5 的 tokenFromUrl（PC 后台带 token 跳入，优先级最高）
      // 与本地 dev 演示账号自动登录；生产无演示账号 → 拿不到 token → 跳正式登录页。
      await ensureAuth()
      if (!REMOTE.token) { uni.reLaunch({ url: '/pages/login/login' }); return } // 未登录且非本地自动登录 → 登录页
      try { this.globalData.data = await loadDashboard(); this.globalData.live = true } catch (e) { /* 后端不可用 → 保持空壳，不显示假数据 */ }
    }
  }
}
</script>

<style lang="scss">
/* #ifdef H5 */
/* 宽屏/桌面：移动页面收成手机宽度居中，两侧自动留白。
   不在 uni-app 上加 transform（会让 fixed 的 tabBar 失去吸底、随内容滚走）；
   固定元素（原生 tabBar / 收银底部条 / 弹层遮罩）单独显式居中，仍吸附视口。 */
@media screen and (min-width: 500px) {
  uni-app {
    max-width: 480px;
    margin: 0 auto;
    box-shadow: 0 0 0 1px rgba(74,56,24,.06), 0 24rpx 80rpx rgba(74,56,24,.10);
    background: $ivory;
  }
  uni-tabbar.uni-tabbar-bottom, .uni-tabbar,
  .cartbar, .mask {
    left: 50% !important;
    right: auto !important;
    width: 480px !important;
    margin-left: -240px !important;
    box-sizing: border-box;
  }
}
/* #endif */
/* 全局基样式 · 高奢金白 */
page {
  background: $ivory;
  color: $ink;
  font-family: $font-sans;
  font-size: 28rpx;
  line-height: 1.6;
}
/* 复用组件类（与原型 app/index.html 同名，便于迁移） */
.yz-card { background: $paper; border: 1rpx solid $hair; border-radius: $radius-md; padding: 28rpx; box-shadow: 0 20rpx 60rpx -36rpx rgba(74,56,24,.45); }
.yz-serif { font-family: $font-display; color: $gold-deep; }
.yz-tag { font-size: 21rpx; padding: 8rpx 16rpx; border-radius: 40rpx; border: 1rpx solid $hair-s; color: $gold-deep; }
.yz-tag--solid { background: linear-gradient(135deg,#E9D4A4,#9C7838); color: #fff; border: none; }
</style>

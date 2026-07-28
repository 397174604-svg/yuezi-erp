<script>
import { EMPTY } from '@/common/data.js'
import { REMOTE, loadDashboard, ensureAuth, isAuthenticated } from '@/common/remote.js'
// baseUrl 自适应：?api=/VITE_API_BASE 覆盖 > 本地 dev(5xxx 端口)连本地中台 8799 > 生产同域 location.origin(+子路径前缀走 nginx 反代)。换域名无需改代码。
function resolveH5Base(override) {
  if (override) return override
  if (import.meta.env && import.meta.env.VITE_API_BASE) return import.meta.env.VITE_API_BASE
  if (['127.0.0.1', 'localhost'].includes(location.hostname)) return `http://${location.hostname}:8799`
  const seg = location.pathname.split('/').filter(Boolean)[0] || ''
  return location.origin + (seg && !seg.includes('.') && seg !== 'api' ? '/' + seg : '')
}
export default {
  globalData: { data: EMPTY, live: false }, // data 初始为空壳；onLaunch 登录后用后端真实数据填充
  async onLaunch() {
    // 身份来自手机号/微信登录换取的客户 JWT；本机仅保存 JWT 与必要账号标识。
    // #ifdef H5
    if (!REMOTE.baseUrl) {
      const q = new URLSearchParams(location.search)
      REMOTE.baseUrl = resolveH5Base(q.get('api'))
    }
    // #endif
    // #ifndef H5
    // 小程序无 location：开发期连本地中台（开发者工具需勾「不校验合法域名」）；上线改为已配置 request 合法域名的 HTTPS 域名
    if (!REMOTE.baseUrl) REMOTE.baseUrl = (import.meta.env && import.meta.env.VITE_MP_API) || 'http://127.0.0.1:8799' // 换域名=构建期设 VITE_MP_API=https://你的域名
    // #endif
    if (REMOTE.baseUrl) {
      try { await ensureAuth(); if (isAuthenticated()) { this.globalData.data = await loadDashboard(); this.globalData.live = true } }
      catch (e) { /* 后端不可用 → 保持空壳，不显示假数据 */ }
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
    box-shadow: 0 0 0 1px rgba(90,84,72,.08), 0 24rpx 80rpx rgba(66,58,44,.12);
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
  background-image: linear-gradient(180deg, rgba(255,255,255,.86), rgba(241,239,234,.38));
  color: $ink;
  font-family: $font-sans;
  font-size: 28rpx;
  line-height: 1.6;
}
/* MOM 端全部页面使用自定义导航栏。
   uni-app 会在微信端注入 --status-bar-height；额外留出 36rpx，避免标题、返回键被状态栏或胶囊遮挡。 */
.screen > .topbar,
.screen > .dhead,
.page > .topbar,
.page > .top {
  padding-top: calc(var(--status-bar-height, 0px) + 36rpx) !important;
  box-sizing: border-box;
}
/* 复用组件类（与原型 app/index.html 同名，便于迁移） */
.yz-card { background: rgba(255,255,255,.96); border: 1rpx solid $hair; border-radius: $radius-md; padding: 28rpx; box-shadow: $shadow-soft; }
.yz-serif { font-family: $font-display; color: $gold-deep; }
.yz-tag { font-size: 21rpx; padding: 8rpx 16rpx; border-radius: 40rpx; border: 1rpx solid $hair-s; color: $gold-deep; }
.yz-tag--solid { background: $foil; color: #fff; border: none; }
.yz-platinum { background: $platinum-foil; border: 1rpx solid $platinum; box-shadow: $shadow-soft; }
.yz-foil { background: $foil; color: #fff; }
</style>

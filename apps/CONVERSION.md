# 原型 → uni-app 产品化指南（奇德芬芳）

把已验证的可点击原型（`app/`，Vue3+CDN+mock）产品化为可发布的微信小程序（uni-app Vue3）。

> **端结构（2026-07-17）**：现为两端＝员工端(apps/staff，含并入的产康板块)＋宝妈端(apps/mom)。产康门店端 apps/rehab 已退役、科研美容 apps/beauty 移出为独立项目；下文若有「三端/四端」为历史表述。构建脚本见 apps/package.json（build:all＝staff+mom）。
`apps/rehab/` 是**产康门店端参考实现**，结构与转换规则对三端通用。

## 1. 跑起来
需 [HBuilderX](https://www.dcloud.io/hbuilderx.html)（最省事）或 uni-app CLI。
- HBuilderX：导入 `apps/rehab/` → 运行 → 「运行到浏览器」(H5) 或「运行到小程序模拟器」(需配微信开发者工具路径)。
- CLI：`npx degit dcloudio/uni-preset-vue#vite my-rehab` 取标准脚手架，把本目录的 `pages/ components/ common/ pages.json manifest.json uni.scss App.vue main.js` 覆盖进去，`npm i && npm run dev:mp-weixin`。
> 真机/小程序编译验证需在你的微信开发者工具里完成（本机无法替你编译小程序）。代码按 uni-app Vue3 规范编写。

## 2. 项目结构
```
apps/rehab/
  manifest.json     应用配置（appid 待填、vue3、mp-weixin/h5）
  pages.json        路由 + tabBar（工作台/收银/客户/我的）
  uni.scss          ★ 高奢金白令牌（自动注入每个 SFC，源 design-system/tokens.css）
  main.js App.vue   入口；App.vue globalData.mock = 数据层
  common/data.js    mock 数据 + PAGES 注册表（数据驱动引擎的数据源）
  components/        可抽公共组件（yz-card 等，easycom 自动注册）
  pages/
    home/home.vue        工作台 flagship（已迁，证明设计落地）
    cashier/cashier.vue  收银开单（占位，按原型 rehab·cashier 迁全交互）
    customers/customers.vue 客户列表（已迁，含等级筛选）
    me/me.vue            我的（菜单 → navigateTo sub）
    sub/sub.vue          ★ 通用 sub-page 渲染器（cards/board/form/list）
```

## 3. 转换规则（原型 → uni-app，机械可重复）
| 原型 (app/) | uni-app | 说明 |
|---|---|---|
| `<div>` | `<view>` | 块容器 |
| `<span>/文字` | `<text>` | 文本必须包 text |
| `class="card"` | 同名 class | 类名不变，样式搬进 `<style lang="scss" scoped>` |
| CSS `px` | `rpx`（×2 @375） | 16px→32rpx；字号同理 |
| `@click` | `@tap` | 事件 |
| `v-if/v-for/:class/{{}}` | 不变 | Vue 语法一致 |
| `window.MOCK/PAGES` | `import { MOCK, PAGES } from '@/common/data.js'` | 全局改 ES 模块 |
| 路由切屏 `view='x'` | `uni.navigateTo({url:'/pages/sub/sub?key=x'})` / `uni.switchTab` | tabbar 用 switchTab，二级用 navigateTo |
| `position:absolute` tabbar | `pages.json` 原生 tabBar | 不再手写 |

**数据驱动引擎照搬**：原型 `pages.js` 的 `window.PAGES[app]` 注册表 → 拷进各端 `common/data.js` 的 `export const PAGES`，`sub.vue` 已实现 cards/board/form/list 四类型渲染。**63 个 sub-page 因此零额外页面文件即可全部复用**，只需迁 flagship 页（home/cashier/客户详情等定制屏）。

## 4. 复制出另外两端
`apps/staff/`、`apps/mom/` = 拷贝 `apps/rehab/` 后改三处：
1. `pages.json` 的 tabBar（员工端：工作台/客户/巡房/我的；宝妈端：我的月子/膳食/商城/我的）。
2. `common/data.js` 换成对应端的 mock + PAGES（取自 `app/mock.js` + `app/pages.js` 的 staff/mom 切片）。
3. flagship 页：员工端迁 工作台金刚区 / 客户列表 / 客户档案 / 巡房；宝妈端迁 我的月子(月相 hero) / 膳食 / 账单卡额。其余 sub-page 走通用渲染器。
4. `manifest.json` 各端独立 appid（三个独立小程序）。

## 5. 字体
小程序不支持远程 webfont 直接 `font-family`。Cormorant/思源宋体在小程序端方案：① 标题/数字用 `cover-view`+图片或 canvas；② 或接受系统衬线降级，仅 H5 加 `@font-face`。建议：金色衬线数字这类「signature」处用切图或 unicode 字体子集；正文用系统字体。H5 端可直接 Google Fonts。

## 6. 后端 / 接真实 API
- 共享客户端 `apps/shared/api.js`（三端共用）：`createApi({baseUrl, tenantId, storeId, transport})`，方法 `listCustomers/getCustomer/checkout/transfer`。
- transport 可插拔：**微信小程序用 `uniTransport`**（uni.request），**H5/测试用 `fetchTransport`**。
- 切换：`App.vue onLaunch` 注入 baseUrl + 租户身份（生产从 JWT/登录态取），`common/data.js` 用 `createApi(...)` 取数替 mock；离线/失败可回退 mock。字段对齐 `docs/field-spec.json`。
- 契约以 `server/openapi.yaml` 为准；端到端已由 `server/test/api-client.test.ts` 验证。真机联调需在微信开发者工具配置合法域名 + 登录态。

## 7. 已落地的真实接入（参考实现：产康端）
- **客户端就位**：`apps/{rehab,staff,mom}/common/api.js` = `apps/shared/api.js` 的同步副本（uni-app 工程内不能跨根目录 import，故每端各放一份；shared 更新后重拷或在构建里配 alias）。
- **产康端已接真实调用点**（reference）：
  - `apps/rehab/common/remote.js`：`makeApi()` 用 `uniTransport` 建客户端；`loadDashboard()` 调 `getBusinessStats/listAppointments/listItems` 拉真实数据并映射为 MOCK 同形结构；`checkout()` 真实下单。**任一步失败整体回退 MOCK，不白屏**。
  - `apps/rehab/App.vue` `onLaunch`：`REMOTE.baseUrl` 为空=离线 mock；登录后注入 `baseUrl + tenantId + storeId` 即自动切真实数据。
- **浏览器实证**：`app/console.html`（经 `apps/shared/api.js` + `fetchTransport` 跨域直连）已在浏览器验证拉通 **20 个后端域**（经营/漏斗/客户/门店/员工/线索/话术/预约/护理/排班/库房/转店…），证明前后端在页面层真实打通。
- **staff/mom 也已接线**（与 rehab 同构）：
  - `apps/staff/common/remote.js`：`loadDashboard` 调 getBusinessStats/getFunnel/listLeads/listNursing/listCustomers，映射员工端 mock（kpis 在住/待巡房/跟进、funnel、clients）；`claimLead` 真实抢单。
  - `apps/mom/common/remote.js`：`loadDashboard` 调 getWallet/listProducts/listDiet，映射宝妈端 mock（卡额/本月消费/商城/今日餐单）；`buy` 真实商城下单（支持积分支付）。
  - 两端 `App.vue onLaunch` 均注入 `REMOTE.baseUrl`（mom 还需 `customerId`）后切真实数据，失败回退 mock。
- **三端真实调用点齐备**（闭合审计"api.js 无调用点"）；**小程序真机/编译联调仍需在微信开发者工具完成**（本机不编译小程序）。

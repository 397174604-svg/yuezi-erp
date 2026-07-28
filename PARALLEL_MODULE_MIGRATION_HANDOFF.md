# ERP 并行模块复刻执行与交接

更新日期：2026-07-24

## 2026-07-24 字段级审计进展

- 已对产康、月嫂、膳食、仓存、商城、风控、基础资料 7 个模块的 88 个页面重新只读审计。
- 88 页的顶部工具栏和主查询区已由原 ERP 证据驱动，覆盖 319 个工具栏动作、432 个原始查询控件和 124 个查询区动作。
- 浏览器逐路由对照结果为 88/88 通过，运行时错误 0。
- 风控服务已改为原页面的三栏会员服务矩阵；仓存/基础资料的统计报表页面路由截获问题已修复。
- 详细证据、验证方法和剩余边界见 `REMAINING_MODULE_SURFACE_AUDIT_HANDOFF.md`。
- 下方 2026-07-23 的“Visible/待核验”内容是骨架阶段历史记录；与本节冲突时，以本节和新的总交接文档为准。列表、表单、弹窗和真实业务动作仍需继续审计。

## 本轮结论

- 已为 10 个模块创建独立工作台、页面配置、API、脱敏 Mock 和模块交接文档，并统一接入动态路由与 Mock 汇总。
- 共覆盖 167 个现有子菜单：护理 17、产康 10、月嫂 8、膳食 13、仓存 24、商城 13、风控 1、查询报表 42、基础资料 19、系统设置 20。
- 查询报表以当前 `src/config/erp-menu.js` 为准实际是 42 项，不是早期估计的 43 项；没有擅自补造不存在的菜单。
- 主登录会话已只读提取原 ERP 隐藏菜单树。10 个模块的菜单标题、顺序、原页面 URL 与 `navid` 已取得证据；通用证据表位于 `src/config/original-page-evidence.js`，月嫂、基础资料、系统设置也在各自配置中保留页面身份。
- 除本轮单独重爬并实现的房态详情外，这 10 个模块目前统一处于 `Visible`/Mock 阶段。页面内部筛选、枚举、默认值、工具栏顺序、表头、表单、弹窗、联动、状态机、打印和导出仍需逐页二次核验，不能宣称已完成字段级一比一。
- 所有演示数据均已脱敏；未复制原 ERP 客户、员工、金额、房间排期或健康数据。

## 房态图已完成部分

`src/views/erp/room-workbench/` 已完成并浏览器回归：

- 点击 201 房间任意住户可打开“客户明细”。
- 客户明细包含原页面 17 个页签；首个“客户详细信息”页已按原页面字段分组复刻。
- 点击右上角“详情(1)”可打开“订房详情”。
- 当前入住详情字段已按原页面复刻。
- 下方包含“客户的房间记录 / 过去入住信息 / 未来预定信息”三组横向列表，三组表头均按原页面复刻。
- 住户卡显示脱敏姓名、剩余天数/总天数和入住时间段。

浏览器回归结果：住户弹窗核心字段与页签通过；三组房间记录页签与表头通过；控制台错误 0。

## 模块文件

| 模块 | 配置 | 工作台 | 交接文档 |
|---|---|---|---|
| 护理管理 | `src/config/nursing-pages.js` | `src/views/erp/nursing-workbench/index.vue` | `NURSING_MIGRATION_HANDOFF.md` |
| 产康管理 | `src/config/rehab-pages.js` | `src/views/erp/rehab-workbench/index.vue` | `REHAB_MIGRATION_HANDOFF.md` |
| 月嫂管理 | `src/config/maternity-nurse-pages.js` | `src/views/erp/maternity-nurse-workbench/index.vue` | `MATERNITY_NURSE_MIGRATION_HANDOFF.md` |
| 膳食管理 | `src/config/diet-pages.js` | `src/views/erp/diet-workbench/index.vue` | `DIET_MIGRATION_HANDOFF.md` |
| 仓存管理 | `src/config/inventory-pages.js` | `src/views/erp/inventory-workbench/index.vue` | `INVENTORY_MIGRATION_HANDOFF.md` |
| 商城管理 | `src/config/mall-pages.js` | `src/views/erp/mall-workbench/index.vue` | `MALL_MIGRATION_HANDOFF.md` |
| 风控服务 | `src/config/risk-pages.js` | `src/views/erp/risk-workbench/index.vue` | `RISK_MIGRATION_HANDOFF.md` |
| 查询报表 | `src/config/report-pages.js` | `src/views/erp/report-workbench/index.vue` | `REPORT_MIGRATION_HANDOFF.md` |
| 基础资料 | `src/config/basic-pages.js` | `src/views/erp/basic-workbench/index.vue` | `BASIC_MIGRATION_HANDOFF.md` |
| 系统设置 | `src/config/system-pages.js` | `src/views/erp/system-workbench/index.vue` | `SYSTEM_MIGRATION_HANDOFF.md` |

各模块还有对应的 `src/api/erp-*.js` 和 `mock/erp-*.js`。

## 共享集成

- `src/config/erp-menu.js`
  - `nursing -> nursing-workbench`
  - `recovery -> rehab-workbench`
  - `matron -> maternity-nurse-workbench`
  - `diet -> diet-workbench`
  - `warehouse -> inventory-workbench`
  - `mall -> mall-workbench`
  - `risk -> risk-workbench`
  - `report -> report-workbench`
  - `basic -> basic-workbench`
  - `system -> system-workbench`
- `src/router/index.js` 已注册上述 10 个懒加载组件。
- `mock/index.js` 已注册上述 10 个模块的 Mock。

## 已执行验证

```text
ESLint:
  src/config/**/*.js
  src/api/erp-*.js
  src/views/erp/**/*.vue
  mock/erp-*.js
  mock/index.js
  src/router/index.js
结果：通过

npm.cmd run build:prod
结果：通过
备注：仅保留项目原有的 asset size / entrypoint size 两条体积警告
```

浏览器已验证 10 条首菜单路由均能渲染正确标题：

```text
/nursing/item-1
/recovery/item-1
/matron/item-1
/diet/item-1
/warehouse/item-1
/mall/item-1
/risk/item-1
/report/item-1
/basic/item-1
/system/item-1
```

## 下一轮严格执行顺序

1. 按 `replicate-legacy-erp` Skill 逐模块、逐页面只读取证。
2. 优先替换当前草案中的工具栏、查询字段、下拉全集、默认值和表头。
3. 再打开但不提交新增/编辑/审核弹窗，补齐表单字段、必填、提示和联动。
4. 对金额、库存、耗卡、审批、权限与状态迁移单独建立规则矩阵，不跨页面猜测。
5. 每完成一页，更新对应配置的字段级 `verified` 状态和模块交接文档。
6. 页面实现后必须全量刷新对应哈希路由，核对标题、表头、弹窗和控制台错误。
7. 接入真实后端前保持 Mock-only，不把演示保存、审批、删除、导出或打印描述为真实业务。

# 膳食管理字段级复刻交接记录

## 2026-07-25 自定义状态选择与工具栏图标补齐

- 原客户餐单 `Page/DietManager/ClientMealRecord.aspx?navid=576` 已只读确认：
  - “客户状态”是横向 `ul/li` 状态选择条，不是原生下拉框。
  - 选项及顺序为：`全部、--未到店--、--已入住--、--已离店--`，默认选中“全部”。
  - 顶部工具栏为：`添加、删除、导出、设置`；原图标类依次为 `iconxinzeng、iconshanchu、icondaochu、iconxitongshezhi`。
- 原膳食统计 `Page/DietManager/ReportMealMenuCount.aspx?navid=591` 和送餐统计 `Page/DietManager/ReportMealMenuClient.aspx?navid=592` 已只读确认：
  - “楼层”同样是横向 `ul/li` 选择条。
  - 选项及顺序为：`全部、2楼、3楼、4楼、5楼、6楼`，默认选中“全部”。
- 本地新增 `choice-list` 审计控件，保留横向选择条、精确顺序、默认值和切换状态。
- 产康管理、月嫂管理、膳食管理通过共享审计工具栏补齐动作语义图标；原页代表证据已核验：
  - 产康：设置 `iconxitongshezhi`、读卡 `iconchaxun`。
  - 月嫂：添加 `iconxinzeng`、编辑 `iconedit_icon`、删除 `iconshanchu`。
- 本地已验证客户状态和楼层选项顺序、默认激活项、楼层切换，以及三模块代表页面的工具栏图标。

## 2026-07-24 字段级审计更新

- 13/13 页已只读核验并接入原版顶部工具栏与主查询区：51 个工具栏动作、52 个原始查询控件、19 个查询区动作。
- 订餐列表“已支付/未支付”复选状态已按原页面标记修正。
- 已执行 13 条路由的 DOM 对照，全部通过且浏览器错误为 0。
- 下方旧版“待核验”内容是骨架阶段历史；表格、表单、弹窗和真实执行链仍待继续。

更新日期：2026-07-23

## 证据与完成度声明

- 仓库 `src/config/erp-menu.js` 已确认“膳食管理”及其 13 个子菜单名称和顺序。
- 本次子任务无法连接主任务中已登录的原 ERP 浏览器会话，因此没有把任何筛选项、按钮、表头、表单、枚举、默认值或业务状态标记为原页已验证。
- 当前实现属于 **Visible** 层：提供独立页面结构、脱敏演示数据和本地 Mock 交互。
- 所有页面仍是 **待原系统二次核验**，不能宣称达到 Schema-faithful、Interaction-faithful 或 Integrated。
- 本次未读取、保存或复制原 ERP 的客户、房间、餐单、金额及健康信息。

## 菜单与审计状态

| 序号 | 菜单 | 当前页面形态 | 原系统 URL | 原页字段状态 |
| --- | --- | --- | --- | --- |
| 1 | 客户餐单 | 餐次看板 + 列表 | 待爬取 | 待原系统二次核验 |
| 2 | 菜品管理 | 列表/表单 | 待爬取 | 待原系统二次核验 |
| 3 | 膳食套餐 | 列表/表单 | 待爬取 | 待原系统二次核验 |
| 4 | 膳食统计 | 汇总报表 | 待爬取 | 待原系统二次核验 |
| 5 | 送餐统计 | 汇总报表 | 待爬取 | 待原系统二次核验 |
| 6 | 营养汤设置 | 列表/表单 | 待爬取 | 待原系统二次核验 |
| 7 | 营养汤统计 | 汇总报表 | 待爬取 | 待原系统二次核验 |
| 8 | 客餐供应 | 列表/表单 | 待爬取 | 待原系统二次核验 |
| 9 | 食材采购 | 列表/审核表单 | 待爬取 | 待原系统二次核验 |
| 10 | 膳食销售 | 列表/收退款流程 | 待爬取 | 待原系统二次核验 |
| 11 | 订餐列表 | 列表/状态流程 | 待爬取 | 待原系统二次核验 |
| 12 | 餐卡管理 | 列表/卡操作 | 待爬取 | 待原系统二次核验 |
| 13 | 餐卡消费报表 | 汇总报表 | 待爬取 | 待原系统二次核验 |

## 本轮新增文件

- `src/config/diet-pages.js`：13 个页面的独立草案配置；每个字段均标记 `verified: false`。
- `src/views/erp/diet-workbench/index.vue`：膳食专属工作台、餐次看板、筛选、列表、表单和演示动作。
- `src/api/erp-diet.js`：膳食模块查询、保存和动作接口封装。
- `mock/erp-diet.js`：明确返回 `persisted: false` 的脱敏演示 Mock。

## 根任务集成映射

本子任务没有修改共享文件。根任务合并时需要完成以下三处映射：

1. `src/config/erp-menu.js`

```js
export function getPageType(groupKey, title) {
  if (groupKey === 'diet') return 'diet-workbench'
  // 保留其余既有映射
}
```

该判断必须位于 `'客户餐单': 'meal-plan'` 生效之前，确保 13 个膳食菜单均进入专属工作台。

2. `src/router/index.js`

```js
const dietWorkbenchPage = () => import('@/views/erp/diet-workbench/index')

function getPageComponent(pageType) {
  if (pageType === 'diet-workbench') return dietWorkbenchPage
  // 保留其余既有映射
}
```

3. `mock/index.js`

```js
const erpDiet = require('./erp-diet')

module.exports = [
  // 保留既有 Mock
  ...erpDiet
]
```

## Mock 接口

```text
GET  /vue-element-admin/erp/diet/modules/:resource
POST /vue-element-admin/erp/diet/modules/:resource/save
POST /vue-element-admin/erp/diet/modules/:resource/action
```

Mock 保存与动作仅返回演示操作结果，不代表真实业务持久化。

## 校验记录

- 已对 `src/config/diet-pages.js`、`src/api/erp-diet.js`、`src/views/erp/diet-workbench/index.vue`、`mock/erp-diet.js` 运行 targeted ESLint，结果通过。
- 因按任务要求未修改路由和 Mock 汇总等共享文件，当前专属工作台尚未进入生产构建入口；需由根任务集成后再执行 `npm run build:prod` 和 13 条路由逐页浏览器回归。

## 二次核验清单

原 ERP 恢复可用后，必须逐页重新采集并替换草案：

1. 原 URL、`navid`、页面形态、默认日期和默认门店。
2. 工具栏按钮的精确名称、顺序、位置、权限隐藏和行选择规则。
3. 筛选标签、控件类型、占位项、下拉枚举顺序和默认值。
4. 表格可见列、隐藏技术列、冻结列、金额/数量格式及合计公式。
5. 新增、编辑、审核、反审核、配送、签收、退餐、餐卡和收退款弹窗字段。
6. 客户、房间、餐次、菜品、套餐、营养汤、结算方式之间的真实联动。
7. 打印模板、导出内容、附件、审批意见、消息通知和状态迁移。
8. 接入真实后端后验证库存扣减、采购入库、餐卡余额和财务金额对账。

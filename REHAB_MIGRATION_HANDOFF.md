# 产康管理迁移交接

## 2026-07-24 服务综合查询双模式专项复刻

原系统入口为 `Page/NursingManager/CusServerSearch.aspx?navid=553`。该入口本身是模式容器，实际业务界面位于两个同源 iframe 中；此前仅审计外层静态页面会漏掉主要字段。本轮已经重新登录并完成只读核验。

### 图形模式

- 业务页：`Page/NursingManager/SelectFWByCard.aspx`
- 查询区：`会员卡号 / 读 卡`、`请选择客户 / 选择客户`、提示 `注：店内客户及散客均支持查询`、`项目打印`。
- 客户弹窗：标题 `选择现有客户`，查询字段 `客户名称、手机号码`，动作 `搜  索、确 认`，列表列 `名称、手机号、客户状态、分店`。
- 读卡弹窗：标题 `读卡`，字段 `卡号`。
- 四个横向页签：`月子合同套餐内服务、月子合同套餐外服务、额外购服务、项目卡服务`。
- 已分别核对四个页签下原 `list2/list3/list4/list5/list8/list9` 表格的可见列；项目卡模式同时包含卡列表与卡内服务明细。

### 列表模式

- 业务页：`Page/NursingManager/ComprehensiveServiceSearch.aspx`
- 查询字段顺序：`客户姓名、手机号、项目名称、产康师、剩余次数(<=)、类型、项目类别、意向分店、客户状态`。
- 默认值：类型 `-全部-`，项目类别 `-请选择-`，意向分店 `-全部-`，客户状态 `正入住`。
- 类型全集：`-全部-、套餐内、套餐外、额外购、月嫂合同、产康合同`。
- 项目类别全集：`-请选择-、产后类、产康服务、护理服务、膳食服务、客房服务、增值服务、软硬件服务、大礼包、科颜肌肤`。
- 客户状态全集：`-全部-、正入住、已出所、未入住`；意向分店为 `-全部-、中心广场旗舰店、黄河路轻奢店`。
- 动作：`搜  索、导出`。
- 可见列共 17 列：`姓名、手机号、房间号、分娩方式、分娩日期、入住日期、出所日期、项目名称、卡名称、类型、项目类别、项目时长、已服务次数、剩余次数、产康师、截止日期、销售分店`。

### 实现与验证

- 专属页面：`src/views/erp/rehab-workbench/ServiceOverviewQuery.vue`
- 字段证据配置：`src/config/rehab-service-overview.js`
- jqGrid 只读结构检查：`scripts/inspect-legacy-grid-definitions.py`
- 已通过定向 ESLint、生产构建和本地浏览器回归；图形/列表切换、四页签、客户选择、读卡弹窗、查询控件选项与表头均已检查，控制台错误为 0。
- 当前完成度为 `Schema-faithful + 本地 Mock 交互`。客户查询、实体读卡、打印、导出和服务数据仍未连接真实后端，未复制原系统客户或业务行数据。

## 2026-07-24 字段级审计更新

- 10/10 页已只读核验并接入原版顶部工具栏与主查询区：27 个工具栏动作、40 个查询控件、10 个查询区动作。
- 已执行 10 条路由的 DOM 对照，全部通过且浏览器错误为 0。
- 证据统一存放在 `src/config/audited-legacy-surfaces.json`；下方 2026-07-23 的“待核验”描述是早期骨架记录。
- 表格完整列、业务表单、弹窗和真实写入动作仍为下一阶段。

更新时间：2026-07-23

## 本轮范围与证据边界

本轮按 `replicate-legacy-erp` Skill 建立产康管理专属页面配置、工作台、API 和 Mock。当前并行任务的浏览器运行环境未发现可用的已登录浏览器，因此无法直接读取原 ERP 页面。

以下内容来自本地 `src/config/erp-menu.js` 与 `ERP_MIGRATION.md`：

- 产康管理共有 10 个子菜单。
- 领域主链路为“服务预约 → 人员排班 → 项目执行 → 耗卡/物料消耗 → 健康评估”。
- 当前系统门店基础枚举包含“中心广场旗舰店、黄河路轻奢店”。

除以上三项外，页面 URL、`navid`、工具栏标签与顺序、筛选字段、下拉枚举、表格列、表单字段、必填项、默认值、联动规则和弹窗均为待核验项。本轮提供的是产康专属可运行骨架和脱敏 Mock 演示，不得标记为原 ERP 字段级验收完成。

## 页面清单与当前完成度

| 序号 | 子菜单 | 本地资源 key | 页面形态 | 原 URL | 当前完成度 |
| --- | --- | --- | --- | --- | --- |
| 1 | 未预约客户服务 | `unbooked-customer-services` | 列表 | 待核验 | Visible；Schema 待核验 |
| 2 | 服务预约列表 | `service-appointments` | 列表/表单 | 待核验 | Visible；Interaction 为 Mock |
| 3 | 服务综合查询 | `service-overview-query` | 图形/列表双模式 | `CusServerSearch.aspx?navid=553` | Schema-faithful；Interaction 为 Mock |
| 4 | 服务人员任务表 | `staff-task-board` | 任务看板/列表 | 待核验 | Visible；Schema 待核验 |
| 5 | 人员排班设置 | `staff-schedule-settings` | 周排班/列表 | 待核验 | Visible；Interaction 为 Mock |
| 6 | 技师人员任务表 | `technician-task-board` | 任务看板/列表 | 待核验 | Visible；Interaction 为 Mock |
| 7 | 客户服务查询 | `customer-service-query` | 查询列表 | 待核验 | Visible；Schema 待核验 |
| 8 | 产康服务记录表 | `rehab-service-records` | 列表/表单 | 待核验 | Visible；Interaction 为 Mock |
| 9 | 完成项目消耗表 | `completed-service-consumption` | 查询列表 | 待核验 | Visible；库存集成未接入 |
| 10 | 产康健康评估 | `rehab-health-assessments` | 列表/评估表单 | 待核验 | Visible；Interaction 为 Mock |

## 已创建文件

- `src/config/rehab-pages.js`
  - 10 个页面独立配置。
  - 包含页面模式、说明、演示工具栏、筛选、列和表单字段。
  - 配置不可作为原系统字段证据，须在二次审计后逐项替换。
- `src/views/erp/rehab-workbench/index.vue`
  - 产康专属工作台。
  - 支持任务摘要、周排班概览、列表筛选、分页、详情、表单、导出、打印和本地状态演示。
  - 页面顶部固定显示“待原系统二次核验”。
- `src/api/erp-rehab.js`
  - 产康列表、保存和业务动作接口封装。
- `mock/erp-rehab.js`
  - 明确返回 `persisted: false`，表示演示动作不持久化真实业务数据。

## 根任务集成清单

为避免并行修改冲突，本任务未修改共享集成文件。根任务需要完成以下三处映射：

1. `src/config/erp-menu.js`

```js
if (groupKey === 'recovery') return 'rehab-workbench'
```

应放在通用 `list` / `report` 判断之前。

2. `src/router/index.js`

```js
import rehabWorkbench from '@/views/erp/rehab-workbench/index'
```

并在页面类型组件映射中增加：

```js
'rehab-workbench': rehabWorkbench
```

3. `mock/index.js`

```js
const erpRehab = require('./erp-rehab')
```

并将 `...erpRehab` 加入 `mocks`。

## 原系统二次审计顺序

每页必须独立记录，禁止把相似枚举跨页复用：

1. 从产康管理菜单读取 10 个真实 `href`、`navid` 和默认页。
2. 逐页记录页面形态、默认查询值、日期范围和门店默认值。
3. 记录顶部业务按钮的标签、顺序、位置、权限可见性和选中规则。
4. 记录筛选字段、控件类型、占位语义、完整选项顺序和联动。
5. 记录表格可见列、技术列、金额/次数/状态格式与汇总行。
6. 只读打开新增、编辑、预约、排班、完成服务、评估和详情弹窗，记录字段、必填、默认值、提示及分区。
7. 不在原系统执行保存、删除、审核、完成、耗卡、导出或打印。
8. 用实证更新 `rehab-pages.js`，每完成一页再把顶部状态由“待核验”改为已核对。
9. 全量回归 10 个本地路由、枚举分支、弹窗、选择规则和控制台错误。

## 真实集成待办

- 预约冲突校验、技师可用时段及跨门店排班。
- 服务项目卡和销售单的剩余次数校验。
- 完成服务后的幂等耗卡、物料领用和库存扣减事务。
- 健康评估敏感字段权限、加密、脱敏和访问审计。
- 删除、取消和修改的状态机约束及不可篡改操作日志。
- 与合同、收款、客户、护理、仓存和经营报表的真实接口联通。

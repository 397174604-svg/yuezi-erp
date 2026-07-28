# 商城管理字段级复刻交接记录

## 2026-07-25 育儿档案与工具栏图标回归

- 只读复核原页 `Page/MicroMall/ParentFile.aspx?navid=560`：主查询顺序为“标题、辣妈类别、类别”，类别默认值为“请选择”，选项依次为“请选择、新生儿、婴儿期、幼儿期、学龄前”。
- `src/config/audited-legacy-surfaces.json` 已回填 `cddClassId` 的完整选项和默认值；本地 `/mall/item-6` 已验证可见。
- 商城管理工作台已统一开启顶部动作图标；育儿档案“添加、编辑、删除”分别显示新增、编辑、删除图标。
- 生产构建与 ESLint 通过。

## 2026-07-24 字段级审计更新

- 13/13 页已只读核验并接入原版顶部工具栏与主查询区：41 个工具栏动作、39 个查询控件、20 个查询区动作。
- 已执行 13 条路由的 DOM 对照，全部通过且浏览器错误为 0。
- 下方旧版“待核验”内容是骨架阶段历史；表格、商品/订单表单、弹窗和真实订单动作仍待继续。

更新日期：2026-07-23

## 证据与完成度声明

- 仓库 `src/config/erp-menu.js` 已确认“商城管理”的 13 个子菜单名称和顺序。
- 当前子任务无法连接根任务中已登录的原 ERP 浏览器会话，因此没有把筛选项、按钮、表格列、表单、枚举、默认值或业务状态标记为原页已验证。
- 本轮使用仓库已有 `mama-box` 页面与 Mock 作为草图证据，重新拆分为 13 个独立页面配置，并统一标记 `verified: false`。
- 当前完成度是 **Visible**：页面结构、脱敏演示数据和本地 Mock 交互可运行。
- 全部页面仍是 **待原系统二次核验**，不能宣称达到 Schema-faithful、Interaction-faithful 或 Integrated。
- 本轮未读取、保存或复制原 ERP 的客户、订单、手机号、金额或其他真实业务记录。

## 页面证据矩阵

| 序号 | 菜单 | 草案页面形态 | 原系统 URL / navid | 字段与交互状态 |
| --- | --- | --- | --- | --- |
| 1 | 商品管理 | 列表 / 商品表单 / 上下架 | 待爬取 | 待原系统二次核验 |
| 2 | 商品订单 | 列表 / 支付 / 出库 / 退款状态 | 待爬取 | 待原系统二次核验 |
| 3 | 项目管理 | 列表 / 项目表单 / 上下架 | 待爬取 | 待原系统二次核验 |
| 4 | 月嫂管理 | 列表 / 人员资料 / 可预约状态 | 待爬取 | 待原系统二次核验 |
| 5 | 商品类别设置 | 分类树 / 分类配置 | 待爬取 | 待原系统二次核验 |
| 6 | 育儿档案 | 内容列表 / 发布 / 置顶 | 待爬取 | 待原系统二次核验 |
| 7 | 专家问答 | 问题列表 / 专家回复 | 待爬取 | 待原系统二次核验 |
| 8 | 妈妈评语 | 评语审核 / 公开隐藏 | 待爬取 | 待原系统二次核验 |
| 9 | 辣妈贴吧 | 社区审核 / 置顶 / 推荐 | 待爬取 | 待原系统二次核验 |
| 10 | 图文介绍 | 图文列表 / 发布 / 排序 | 待爬取 | 待原系统二次核验 |
| 11 | 评论回复列表 | 评论评分 / 回复 / 展示范围 | 待爬取 | 待原系统二次核验 |
| 12 | 妈妈课堂 | 课程列表 / 报名信息 | 待爬取 | 待原系统二次核验 |
| 13 | 妈妈课堂排班 | 周排班 / 排班表单 / 报名详情 | 待爬取 | 待原系统二次核验 |

## 本轮新增文件

- `src/config/mall-pages.js`
  - 13 个菜单的独立草案配置。
  - 每页单独定义查询条件、顶部动作、表格列和表单字段。
  - 每个字段和表格列均带 `verified: false`。
- `src/views/erp/mall-workbench/index.vue`
  - 商城专属工作台。
  - 包含普通列表、分类树、课堂周排班、动态表单、详情抽屉、报名演示、上传控件和本地状态演示。
  - 页面顶部和弹窗内持续显示“待原系统二次核验 / Mock 演示”。
- `src/api/erp-mall.js`
  - 商城模块查询、保存和动作接口封装。
- `mock/erp-mall.js`
  - 明确返回 `persisted: false` 与 `synchronizedToMamaApp: false` 的脱敏演示 Mock。

## 根任务集成片段

本子任务未修改共享文件。根任务合并时需添加以下映射，并放在原 `mamaBoxPageTypes` 分支之前，使 13 个菜单全部进入新工作台。

### `src/config/erp-menu.js`

```js
export function getPageType(groupKey, title) {
  if (groupKey === 'mall') return 'mall-workbench'
  // 保留其余既有映射
}
```

### `src/router/index.js`

```js
const mallWorkbenchPage = () => import('@/views/erp/mall-workbench/index')

function getPageComponent(pageType) {
  if (pageType === 'mall-workbench') return mallWorkbenchPage
  // 保留其余既有映射
}
```

### `mock/index.js`

```js
const erpMall = require('./erp-mall')

module.exports = [
  // 保留既有 Mock
  ...erpMall
]
```

## Mock 接口

```text
GET  /vue-element-admin/erp/mall/modules/:resource
POST /vue-element-admin/erp/mall/modules/:resource/save
POST /vue-element-admin/erp/mall/modules/:resource/action
```

Mock 保存与动作不会真实持久化，也不会同步妈妈端。

## 校验记录

- `src/config/mall-pages.js`、`src/api/erp-mall.js`、`src/views/erp/mall-workbench/index.vue`、`mock/erp-mall.js` 已通过项目内置 ESLint。
- 配置键数量检查为 13，且与 `src/config/erp-menu.js` 中商城菜单的 13 个标题逐项一致。
- 本子任务只新增商城独立文件；没有编辑 `src/router/index.js`、`src/config/erp-menu.js`、`mock/index.js`。这些共享文件在进入子任务时已存在其他并行任务变更。
- 因尚未接入共享路由和 Mock 汇总，本子任务没有单独执行生产构建或 13 条路由的浏览器回归；应由根任务集成后统一执行。

## 原系统二次核验清单

原 ERP 会话可用后必须逐页替换本轮推断：

1. 原始 URL、`navid`、页面形态、默认门店、默认日期和默认状态。
2. 查询字段的准确名称、控件类型、选项顺序、占位项与默认值。
3. 顶部工具栏按钮的准确名称、顺序、位置、权限隐藏与行选择规则。
4. 表格可见列、技术隐藏列、冻结列、排序、合计和金额格式。
5. 商品 / 项目的分类树、上下架、推荐、积分、库存及门店可售联动。
6. 商品订单的销售类型与商品类型联动、支付、优惠、欠款、出库、退货与退款弹窗。
7. 月嫂资料、证书、等级、费用、档期与妈妈端预约状态。
8. 育儿档案、图文介绍和社区内容的富文本、图片/视频上传、审核、发布、置顶及推荐流转。
9. 专家问答、妈妈评语与评论回复的分派、审核意见、回复范围和消息通知。
10. 妈妈课堂的课程字段、报名名单、签到、退课、人数上限及排班复制/移动规则。
11. 所有上传附件的格式、数量、大小、预览、删除与持久化规则。
12. 接入真实后端后核验订单、库存、积分、退款和妈妈端同步对账。

# 月嫂管理字段级复刻交接

更新时间：2026-07-24

## 本轮完成

重新登录原“妈妈宝盒”ERP，对月嫂管理 8 个子页面执行只读深层审计，并替换了原先仅展示工具栏、查询区和“待核验清单”的通用占位工作台。

- 8/8 页面已补齐原版顶部工具栏、主查询条件、下拉全集、默认值和主表可见列。
- 页面不再展示 `原系统入口证据`、URL、`navid`、`Schema-faithful`、`二次核验清单`、`待核验`等开发审计文字。
- 月嫂档期改为档期矩阵，包含空闲中、预约中、上户中、请假/休假和重叠状态。
- 月嫂档案补齐护理师档案表单、头像文件选择及服务照片/证书/体检报告/学习经历/工作经历/视频入口。
- 薪酬标准补齐 9 个新增/编辑字段。
- 月嫂合同补齐 22 个合同与收款字段，以及产康项目、商品、卡类、赠送清单 4 个明细页签。
- 月嫂服务记录补齐 11 个派工字段和 30 个结算字段。
- 工具栏单选动作保留原版“请选中一行数据！”前置规则。
- 所有本地业务数据均为脱敏示例，未复制原系统客户、护理师、合同、金额或排班记录。

## 页面证据矩阵

| 序号 | 页面 | 原页面 | 工具栏动作 | 主表可见列 | 本地形态 |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | 月嫂档案 | `Page/BasicInfo/MaternityMatronList.aspx?navid=422` | 3 | 21 | 列表 + 档案表单 |
| 2 | 薪酬标准 | `Page/BasicInfo/MaternityPriceList.aspx?navid=588` | 3 | 8 | 列表 + 薪酬表单 |
| 3 | 月嫂档期 | `Page/BasicInfo/TimeManagement.aspx?navid=593` | 1 | 3 | 档期矩阵 + 请假表单 |
| 4 | 月嫂合同 | `Page/MaternityContract/ContractList.aspx?navid=599` | 14 | 33 | 合同列表 + 合同/收款/明细 |
| 5 | 月嫂服务记录 | `Page/NursingManager/MomServerLogList.aspx?navid=423` | 10 | 28 | 派工列表 + 服务/结算表单 |
| 6 | 月嫂派工审核 | `Page/MaternityContract/MomServerLogSH.aspx?navid=666` | 0 | 26 | 审核查询列表 |
| 7 | 月嫂结算列表 | `Page/NursingManager/MomServerSalary.aspx?navid=665` | 2 | 42 | 结算查询列表 |
| 8 | 月嫂预约记录 | `Page/MaternityContract/MaternityYYList.aspx?navid=641` | 0 | 13 | 预约查询列表 |

主表列依据 jqGrid `colNames` 与 `colModel.hidden` 按索引对齐后提取；隐藏的技术 ID、内部金额和弹窗选择表列没有混入主业务表。

## 主要文件

- `src/config/maternity-nurse-pages.js`
  - 8 页独立配置、主表列、档期状态、表单字段、下拉选项、选择规则和合同明细页签。
- `src/views/erp/maternity-nurse-workbench/index.vue`
  - 月嫂专属列表、档期矩阵、表单、选择器和结算弹窗。
- `src/views/erp/components/AuditedSurfacePanel.vue`
  - 新增 `plain` 模式；月嫂页面只展示原业务工具栏和查询区，不渲染审计说明。
- `scripts/audit-maternity-nurse-depth.py`
  - 只读提取工具栏目标、可见/隐藏 jqGrid 列和空白表单结构。
- `src/config/audited-legacy-surfaces.json`
  - 原版顶部工具栏和查询区的脱敏结构证据。

## Skill 更新

`replicate-legacy-erp` 已新增两条规则：

1. 审计证据、URL、`navid`、完成度徽标和核验清单只能进入配置、测试与交接文档，不得进入业务页面。
2. 自动跟随原页面动作时，只能打开已观察到的静态只读表单；不得自动访问 `ajax`、`NonQuery`、保存、删除、审核、导出、Excel、报表或打印端点。

## 完成边界

当前完成度为：

- 菜单、工具栏、查询区、下拉、默认值、主表列：`Schema-faithful`
- 已审计新增/结算表单与选择规则：`Interaction-faithful（本地 Mock）`
- 保存、删除、审核、派工、真实收款、真实结算、打印和导出：未接真实后端

本地保存类按钮仅验证字段和交互，不会写入原系统或生成真实业务单据。

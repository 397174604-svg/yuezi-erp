# 系统设置模块复刻交接

## 结论

- 当前仓库“系统设置”分组包含 **20 个**子菜单；独立配置 `src/config/system-pages.js` 同样覆盖 **20 个**，标题和顺序逐项一致。
- 主会话已从登录态原 ERP 只读核验 20 个菜单的原始 URL 与 `navid`。本次配置已回填这些页面身份信息。
- 本子任务浏览器运行环境没有可用浏览器，因而没有取得各页面内部模式、字段、控件类型、选项、默认值、树层级、联动、工具栏、表头、表单、权限或状态机证据。
- 当前成果等级仅为 **Visible**：可运行的页面承接骨架与脱敏 Mock 演示；不能宣称 Schema-faithful、Interaction-faithful 或 Integrated。
- 工作台显著区分：
  - “页面身份已核验”：菜单标题、顺序、原始 URL、`navid`。
  - “内部字段待核验”：页面模式、字段、选项、默认值、工具栏、表格、表单、权限、依赖和业务行为。
- 没有实现真实保存、发布、启停、授权、执行、重试、删除、导入、导出、打印或后端持久化。

## 新增文件

- `src/config/system-pages.js`
  - 20 个页面的独立配置草案。
  - 每个推断字段/列均带 `verified: false`。
  - 每页包含已核验 `originalUrl`、`originalNavid`、`pageIdentityVerified: true`。
  - 页面内部 `evidenceLevel` 统一为“内部字段待原系统二次核验”，完成等级统一为 `Visible`。
- `src/views/erp/system-workbench/index.vue`
  - 系统设置独立工作台。
  - 展示页面身份证据、结构假设、依赖核验清单、查询/列表/表单草案和未核验项。
  - 未伪造原 ERP 业务工具栏；仅提供明确标注的本地草案筛选。
- `src/api/erp-system.js`
  - 系统设置 Mock 查询和本地预览接口封装。
- `mock/erp-system.js`
  - 返回空列表，由页面生成脱敏演示数据。
  - 预览接口明确返回 `persisted: false`。

按并行任务约束，本子任务未修改：

- `src/router/index.js`
- `src/config/erp-menu.js`
- `mock/index.js`

## 页面身份与证据矩阵

| 序号 | 菜单标题 | 已核验原始 URL | navid | 菜单/URL | 内部字段、按钮、列、表单、联动 | 当前等级 |
|---:|---|---|---:|---|---|---|
| 1 | 部门管理 | `sys/Departments.aspx?navid=13` | 13 | 已核验 | 待原系统二次核验 | Visible |
| 2 | 角色管理 | `sys/RoleList.aspx?navid=11` | 11 | 已核验 | 待原系统二次核验 | Visible |
| 3 | 用户管理 | `sys/Users.aspx?navid=12` | 12 | 已核验 | 待原系统二次核验 | Visible |
| 4 | 数据字典 | `sys/datadic.aspx?navid=14` | 14 | 已核验 | 待原系统二次核验 | Visible |
| 5 | 审批流程 | `sys/ApprovalProcess.aspx?navid=316` | 316 | 已核验 | 待原系统二次核验 | Visible |
| 6 | 通知公告 | `OA/GongGao/GongGao.aspx?navid=290` | 290 | 已核验 | 待原系统二次核验 | Visible |
| 7 | 返利设置 | `Page/BasicInfo/RebateSetting.aspx?navid=477` | 477 | 已核验 | 待原系统二次核验 | Visible |
| 8 | 会所介绍 | `Page/BasicInfo/ClubIntroduce.aspx?navid=482` | 482 | 已核验 | 待原系统二次核验 | Visible |
| 9 | 导航菜单 | `sys/NavigationList.aspx?navid=10` | 10 | 已核验 | 待原系统二次核验 | Visible |
| 10 | 移动端导航 | `sys/NavigationListAPP.aspx?navid=674` | 674 | 已核验 | 待原系统二次核验 | Visible |
| 11 | 操作按钮 | `sys/ButtonList.aspx?navid=2` | 2 | 已核验 | 待原系统二次核验 | Visible |
| 12 | 操作日志 | `sys/logs.aspx?navid=15` | 15 | 已核验 | 待原系统二次核验 | Visible |
| 13 | 短信发送设置 | `Page/BasicInfo/SetUserForMsm.aspx?navid=280` | 280 | 已核验 | 待原系统二次核验 | Visible |
| 14 | 生日短信提醒 | `Page/BasicInfo/BrithdayRemind.aspx?navid=426` | 426 | 已核验 | 待原系统二次核验 | Visible |
| 15 | 消息发送日志 | `Page/BasicInfo/MsgSendLog.aspx?navid=439` | 439 | 已核验 | 待原系统二次核验 | Visible |
| 16 | 预警参数设置 | `Page/WarningManager/SetPrameter.aspx?navid=381` | 381 | 已核验 | 待原系统二次核验 | Visible |
| 17 | 报表模板自定义 | `Page/BasicInfo/ReportTemplet.aspx?navid=446` | 446 | 已核验 | 待原系统二次核验 | Visible |
| 18 | 模板设置 | `Page/BasicInfo/TemplateList.aspx?navid=672` | 672 | 已核验 | 待原系统二次核验 | Visible |
| 19 | 计划任务 | `Page/BasicInfo/PlanTaskList.aspx?navid=673` | 673 | 已核验 | 待原系统二次核验 | Visible |
| 20 | 系统参数设置 | `Page/WarningManager/SetSysPram.aspx?navid=384` | 384 | 已核验 | 待原系统二次核验 | Visible |

## 原系统二次核验清单

每页必须独立记录，不得因为页面名称相似跨页复用枚举或工具栏：

1. 页面模式、标题区、查询区、工具栏、表格/树/编辑器的实际区域顺序。
2. 默认查询条件、默认日期范围、占位语义和只读/禁用状态。
3. 每个下拉选项的完整文本、顺序、默认值和“全部/请选择”语义。
4. 部门、菜单、角色、字典、范围树的父子层级、默认展开、可选节点和多选规则。
5. 控制字段逐项切换后的从属选项、启用状态和旧值清空行为。
6. 查询按钮与业务按钮分开记录，核对标签、顺序、位置、选中行要求和权限隐藏。
7. 完整表头、隐藏技术列、排序、状态/日期格式、汇总与分页规则。
8. 打开但不提交新增/编辑/配置对话框，记录字段分组、必填、校验、提示、附件和底部动作。
9. 对审批流程、角色权限、计划任务、短信/消息和预警页面，额外记录节点、条件、处理人、权限范围、重试策略和状态机。
10. 本地实现后逐页完整刷新回归，确认没有哈希路由残留组件并检查控制台错误。

## 重点依赖场景（全部待核验）

- 部门管理：上级部门 → 可用子节点；门店 → 部门归属范围。
- 角色管理：数据范围 → 组织范围树；菜单节点 → 操作按钮权限。
- 用户管理：门店 → 部门 → 绑定职员；角色 → 数据权限。
- 数据字典：字典类型 → 字典项；上级字典 → 可选子项。
- 审批流程：业务类型 → 流程节点；节点条件 → 审批人/下一节点。
- 返利设置：返利类型 → 计算基数/数值控件；适用范围 → 对象选择器。
- 导航菜单/移动端导航：菜单类型或跳转类型 → 路由、组件或目标控件。
- 短信发送设置：通道类型 → 接口参数；模板 → 签名与变量。
- 生日短信提醒：接收对象 → 可用变量；短信模板 → 通道。
- 预警参数设置：预警类型 → 阈值单位/比较规则；触发策略 → 通知对象。
- 报表模板自定义：数据源 → 字段；字段类型 → 格式和汇总方式。
- 模板设置：模板类型 → 编辑器/变量；适用范围 → 可用模板。
- 计划任务：任务类型 → 处理器/参数；失败策略 → 重试设置。
- 系统参数设置：数据类型 → 值控件/校验；生效范围 → 组织/门店选择。

以上只是核验任务清单，不是已确认业务规则。

## 验证记录

- 菜单标题差异检查：通过；仓库菜单 20、独立配置 20、缺失 0、额外 0、顺序差异 0。
- 页面身份证据检查：20 个配置均回填原始 URL 与 `navid`。
- Targeted ESLint：通过；校验 `src/config/system-pages.js`、`src/views/erp/system-workbench/index.vue`、`src/api/erp-system.js`。
- `git diff --check` 语义检查：通过；新增的 5 个文件无尾随空格或 EOF 多余空行。
- 编码异常标记扫描：通过；未发现替换字符或常见乱码标记。
- 生产构建和浏览器回归：留给根任务在共享路由与 Mock 集成后统一执行。

## 根任务集成建议

为避免并行 Agent 修改共享文件，根任务统一集成：

1. `src/config/erp-menu.js`
   - 在 `specialPageTypes` 和通用 `system/settings` 分支之前增加：
     - `if (groupKey === 'system') return 'system-workbench'`
2. `src/router/index.js`
   - 懒加载 `@/views/erp/system-workbench/index`。
   - 在 `getPageComponent` 中映射 `system-workbench`。
3. `mock/index.js`
   - 引入并展开 `./erp-system`。

生产构建与浏览器回归应由根任务在共享路由和 Mock 集成后统一执行。

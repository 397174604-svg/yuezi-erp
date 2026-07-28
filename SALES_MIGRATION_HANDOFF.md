# 销售管理字段级复刻：续作执行文档

更新时间：2026-07-23  
项目目录：`C:\Users\39717\Desktop\月子系统erp`  
本地访问：`http://localhost:9527`  
当前开发服务：Vue 开发进程 PID `20004`，本地端口 `9527`

## 当前最新状态（2026-07-23）

销售管理 9 个菜单已全部切换为销售专用工作台，字段配置、筛选项、列表列、新增/编辑表单、明细行、审核、收款、出库、退货、合同变更、套餐升级、优惠券分发和操作轨迹均已落地。独立 API 与 mock 接口已接入，定向 ESLint 与生产构建均已通过。浏览器已逐页核对 9 个菜单，并实际验证合同新增字段、商品明细金额联动、优惠券分发、赠送申请审批和赠送清单保存；最新服务控制台错误为 0。后续接手时优先进行真实后端、数据库、权限与金额库存事务接入，无需重新采集这 9 个页面。

合同管理于 2026-07-23 再次按原 ERP 列表页复核并修正：合同类型筛选完整包含月子合同、婴儿托管、试住合同、续住合同、小月子合同、到家合同；审核状态、客户状态、是否入住选项恢复原枚举；默认筛选为待审核和近 7 天签单日期；门店恢复“全部、中心广场旗舰店、黄河路轻奢店”快捷选择；页面恢复“折扣率=成交金额/参考价格”“未入账金额=已收款未审核的金额”两条业务口径，以及合同汇总行和原工具栏按钮。

## 一、任务目标（已完成前端字段级实现）

把“销售管理”下的 9 个菜单从当前通用列表页改成与“客户管理”相同标准的字段级业务页面：

1. 合同管理
2. 商品销售
3. 销售明细
4. 套餐管理
5. 卡类套餐
6. 赠送管理
7. 优惠管理
8. 优惠券管理
9. 赠送项目申请

“字段级复刻”至少应覆盖：

- 每页原有查询字段及枚举选项；
- 原有列表列、状态标签和横向表格；
- 工具栏业务按钮；
- 新增、编辑、审核、出库、退货、分发等业务弹窗字段；
- 关键状态变化和操作轨迹；
- 独立模拟接口与脱敏演示数据；
- ESLint、生产构建和 9 个菜单的浏览器回归。

## 二、安全与访问说明

原 ERP 登录地址：

`http://qd.mm.hxqt.cn/Page/Login/Login3.aspx`

登录账号：`admin`

登录密码没有写入本文件，避免在项目目录中保存明文凭据。开始续作前，请向用户重新获取密码及登录授权。

只允许读取页面结构、字段名称、按钮、状态和静态脚本，不读取、下载或保存真实客户、合同、收款和销售记录。项目内模拟数据必须使用虚构名称、掩码电话和虚构单据号。

项目中存在临时登录加密工具：

`scripts/erp-login-encrypt.cjs`

该文件只包含登录页公开的 RSA 公钥，不包含账号或密码。它用于生成 ASP.NET 登录表单的 `userLogin` 和 `passWord` 加密值。完成原 ERP 结构核对后可删除此临时工具。

## 三、当前已经完成的工作

### 1. 项目基础

- Vue 2 + Element Admin 项目依赖已安装并可运行；
- 客户管理 18 个页面已完成字段级工作台；
- 客户管理菜单已修正为直属菜单、客服管理子菜单和会员管理子菜单；
- 基础资料、权限、妈妈宝盒等已有专用页面；
- 最近一次客户模块 ESLint 和生产构建均通过。

### 2. 销售管理复刻进度

已完成：

- 原 ERP 授权登录方案验证；
- 9 个销售页面准确地址定位；
- 9 个列表页的主要筛选字段、操作按钮、列表列和部分子表列提取；
- 新增/编辑弹窗对应的原始 ASPX 页面地址定位。

未完成：

- 逐页提取新增/编辑表单的完整字段；
- 创建销售字段配置、专用 Vue 页面、API 和 mock；
- 路由切换；
- 业务联动、代码检查、构建和浏览器回归。

## 四、原 ERP 销售页面准确地址

| 菜单 | 原 ERP 地址 |
| --- | --- |
| 合同管理 | `Page/ContractManager/ContractCreate.aspx?navid=85` |
| 商品销售 | `Page/SalerManager/SalerMangerNew.aspx?navid=523` |
| 销售明细 | `Page/SalerManager/SalesDetailList.aspx?navid=602` |
| 套餐管理 | `Page/ContractManager/PackageInfo.aspx?navid=87` |
| 卡类套餐 | `Page/SalerManager/CardSaleList.aspx?navid=412` |
| 赠送管理 | `Page/GuestRoomManger/EffectsList.aspx?navid=237` |
| 优惠管理 | `Page/SalerManager/DiscountBill.aspx?navid=310` |
| 优惠券管理 | `Page/SalerManager/DiscountListNEW.aspx?navid=534` |
| 赠送项目申请 | `Page/SalerManager/SaleProductSend.aspx?navid=556` |

## 五、已提取的字段结构

### 1. 合同管理

已确认列表列：

- 合同编码、套餐名称、客户姓名、手机号；
- 到店状态、直接到店、是否到店、审核状态；
- 签单人、签单人部门、签单门店；
- 合同最终成交金额、已收款、退款、欠款、未入账金额；
- 合同优惠金额、收款后优惠、应收金额；
- 合同天数、折扣率、预产期、合同签订日期；
- 预定房型、房号、胎型、入住日期、离开日期；
- 续住金额、已收续住金额、续住欠款；
- 升级金额、已收升级金额、升级欠款、合同最终额；
- 合同备注、录入人、护理类型、远程签约、折扣率审核；
- 客户来源、是否首单、录入日期、合同类型、是否变更、审批记录。

已发现的业务动作或弹窗：

- 合同新增、合同编辑、合同变更、批量审核、合同审核；
- 查看详细、审批记录、合同打印、签约；
- 新增收款、收款明细、设置套餐、套餐升级；
- 护理项目、母婴服务计划、客户详情；
- 更换签单人、新增签单人、抄送人；
- 作废、审核通过/驳回、下一审核节点、下一审核人、发送消息。

列表页的完整查询字段尚需继续从静态源码或可见页面提取。

原表单地址：

- 新增：`Page/ContractManager/ContractAdd1.aspx`
- 编辑：`Page/ContractManager/ContractEdit1.aspx?C_SH=...`
- 审核：`Page/ContractManager/ContractEdit.aspx?C_SH=...&ContractID=...`
- 变更/打印：`Page/ContractManager/ContractReport.aspx?...`

### 2. 商品销售

查询字段：

- 单据编号、客户姓名、销售类型、单据状态；
- 支付类型、商品类型、客户状态、数据来源；
- 销售分店、是否显示退货、单据日期起止；
- 销售仓库、介绍人、介绍电话、启用日期。

状态：

- 未支付、已支付、已取消、已付未出库、已出库未支付；
- 换货退货、已退货、不通过。

操作：

- 服务销售、物料销售、卡类销售、星支付；
- 编辑、删除、导出、打印、出库、是否启用；
- 退货、取消、取消退货、收款、变更；
- 折扣率审核、介绍分配。

主表列：

- 销售单编号、客户号、客户姓名、手机号、销售类型；
- 支付方式、消费金额、优惠券金额、欠款金额；
- 销售人、录单所在部门、支付状态；
- 销售日期、制单日期、制单人、销售分店；
- 财务审核、订单来源、介绍人、介绍电话；
- 销售备注、支付备注、最低折扣审核；
- 客户来源、附件、出库单号。

物料子表列：

- 商品名称、单位、单价、积分单价/折后单价、折扣率；
- 数量、商品总价、积分总价/折后总价、备注、所属仓库。

服务子表列：

- 项目名称、单位、单价、积分单价/折后单价；
- 数量、积分总价/总价、优惠金额、有效期、备注。

卡类子表列：

- 套餐名称、单位、套餐价、折后单价、数量；
- 套餐启用日期、套餐有效期、备注。

原表单地址：

- 服务销售：`Page/SalerManager/AddSPSaler.aspx?GetSelType=0`
- 物料销售：`Page/SalerManager/AddSPSalerForWL.aspx?GetSelType=1`
- 卡类销售：`Page/SalerManager/AddSPSaleCard.aspx?GetSelType=3`
- 收款：`Page/SalerManager/Salereceipt.aspx?id=...`
- 服务退货：`Page/SalerManager/SaleTuihuo1.aspx?id=...`
- 物料退货：`Page/SalerManager/SaleTuihuoWL1.aspx?id=...`
- 卡类退货：`Page/SalerManager/SaleTuihuoCard.aspx?id=...`
- 换货：`Page/SalerManager/ChangeOrder.aspx?id=...`

### 3. 销售明细

查询字段：

- 商品名称、销售单号、商品类型、客户姓名；
- 销售类型、单据状态、数据来源、支付类型；
- 销售分店、入住分店、单据日期起止。

快捷动作：服务销售、物料销售、卡类销售、膳食销售、查询、导出。

列表列：

- 编号、商品名称、单位、商品类型、数量、价格、总价、税率、备注；
- 销售单号、客户姓名、手机号、支付方式、销售类型、支付状态；
- 销售日期、销售人、制单日期、销售分店、入住分店；
- 订单来源、销售备注、支付备注。

该页面以查询和跳转新增销售为主，可以不设置通用“新增明细”弹窗。

### 4. 套餐管理

查询字段：套餐名称、所属分店、启用状态、审核状态。

操作：添加、流程审批、编辑、删除、设置、提交、审核、复制、启用、反审核、推荐/取消、屏蔽/取消。

主表列：

- 套餐编号、套餐名称、套餐价格、套餐房型；
- 审核状态、是否启用、是否显示、启用时间；
- 是否推荐、推荐时间、录入人、所属分店、功能。

项目明细列：

- 项目编号、项目名称、项目类别、折扣价；
- 单位、数量、总价、分店。

审核字段：审核结果、审核意见、下一审核节点、下一审核人、是否发送消息、抄送人。

原表单地址：

- 新增：`Page/ContractManager/AddPackage1.aspx`
- 编辑：`Page/ContractManager/PackageEdit1.aspx?PackageID=...`
- 审核：`Page/ContractManager/Package_SH.aspx?PackageID=...`
- 设置：`Page/ContractManager/PlanScheduling.aspx?PackageID=...`

### 5. 卡类套餐

查询字段：卡类名称、启用状态、所属门店。

操作：添加、编辑、删除、复制。

列表列：

- 卡片编号、卡片名称、套餐总金额、审核状态、是否启用；
- 项目类型、有效天数、卡类型、启用时间；
- 分店、是否显示、录入人。

原表单地址：

- 新增：`Page/SalerManager/CardSaleAdd1.aspx`
- 编辑：`Page/SalerManager/CardSaleEdit1.aspx?CardSaleID=...`

### 6. 赠送管理

查询字段：清单名称、所属分店、启用状态。

操作：添加、编辑、删除、导出。

主表列：清单编号、清单名称、是否启用、启用时间、所属分店。

物料明细列：物料编码、物料名称、物料类别、规格型号、单位、单价、数量、总价、备注。

原表单地址：

- 新增：`Page/GuestRoomManger/AddPackage_ZS.aspx`
- 编辑：`Page/GuestRoomManger/PackageEdit_ZS.aspx?PackageID=...`

### 7. 优惠管理

查询字段：客户姓名、优惠券类型、所属分店、审核状态、制单日期起止。

操作：添加、编辑、删除、导出、审核、反审核、停用。

状态：审核通过、审核不通过、已作废、已使用、未使用、已过期。

列表列：

- 编号、客户姓名、手机号、优惠券名称、优惠券类型、优惠项目类型；
- 数量、优惠券金额、剩余金额、有效天数、截止日期；
- 审核状态、审核人、审核意见、备注；
- 制单人、制单时间、分店、状态、停用说明。

原表单地址：

- 新增：`Page/SalerManager/AddDiscount.aspx`
- 编辑：`Page/SalerManager/EditDiscount.aspx?id=...`

### 8. 优惠券管理

查询字段：优惠券类型、所属分店。

操作：添加、编辑、删除、分发。

列表列：

- 优惠券编码、优惠券名称、优惠券类型、优惠项目类型；
- 优惠券金额、所属门店、开始时间、结束时间；
- 总数量、发放数量、每客户限领数量；
- 制单人、制单时间。

分发客户选择列：名称、身份证号、手机号、年龄、客户状态、分店。

原表单地址：

- 新增：`Page/SalerManager/DiscountAddNEW.aspx`
- 编辑：`Page/SalerManager/DiscountEditNEW.aspx?id=...`

### 9. 赠送项目申请

查询字段：客户姓名、单据状态、客户状态、销售分店、赠送类型、销售日期起止、销售仓库。

操作：星支付、流程审批、服务销售、物料销售、卡类销售、删除、撤回、反审核。

状态：已出库、已退货、待出库；审核通过/驳回。

主表列：

- 销售单编号、客户号、客户姓名、手机号、赠送品项；
- 消费金额、销售人、录单所在部门、审核状态；
- 销售日期、制单日期、销售分店、赠送类型、赠送理由；
- 出库、附件、审核记录。

服务/物料明细列：

- 商品名称、单位、单价、折后单价、数量；
- 总价、折后金额、优惠金额、有效期、仓库。

卡类明细列：

- 套餐名称、单位、套餐价、折后单价、数量；
- 套餐启用日期、套餐有效期、备注。

原表单地址：

- 服务赠送：`Page/SalerManager/AddSPSaler.aspx?send=1`
- 物料赠送：`Page/SalerManager/AddSPSalerForWL.aspx?send=1`
- 卡类赠送：`Page/SalerManager/AddSPSaleCard.aspx?send=1&GetSelType=3`

## 六、下一步应先提取的表单页面

登录后依次只读访问以下页面，提取可见标签、输入控件、下拉选项、明细表列和保存规则：

1. `Page/ContractManager/ContractAdd1.aspx`
2. `Page/SalerManager/AddSPSaler.aspx?GetSelType=0`
3. `Page/SalerManager/AddSPSalerForWL.aspx?GetSelType=1`
4. `Page/SalerManager/AddSPSaleCard.aspx?GetSelType=3`
5. `Page/ContractManager/AddPackage1.aspx`
6. `Page/SalerManager/CardSaleAdd1.aspx`
7. `Page/GuestRoomManger/AddPackage_ZS.aspx`
8. `Page/SalerManager/AddDiscount.aspx`
9. `Page/SalerManager/DiscountAddNEW.aspx`
10. `Page/SalerManager/AddSPSaler.aspx?send=1`

建议每页记录：

- 表单分组；
- 字段名称、必填状态、控件类型；
- 下拉枚举；
- 金额、折扣、数量、有效期的校验；
- 客户、商品、项目、套餐、仓库、签单人的选择联动；
- 保存、提交、审核、出库等状态变化。

## 七、建议的代码落地结构

尽量复用客户管理工作台的架构，但不要直接把销售页面塞进客户配置。

建议新增：

```text
src/config/sales-pages.js
src/views/erp/sales-workbench/index.vue
src/api/erp-sales.js
mock/erp-sales.js
```

需要修改：

```text
src/config/erp-menu.js
src/router/index.js
mock/index.js
ERP_MIGRATION.md
```

参考现有实现：

- 页面容器：`src/views/erp/customer-workbench/index.vue`
- 字段配置：`src/config/customer-pages.js`
- API：`src/api/erp-customer.js`
- Mock：`mock/erp-customer.js`

### 路由改造建议

在 `src/config/erp-menu.js` 的 `getPageType` 中增加：

```js
if (groupKey === 'sales') return 'sales-workbench'
```

在 `src/router/index.js` 中增加销售工作台懒加载，并在 `getPageComponent` 中映射 `sales-workbench`。

### 模拟接口建议

```text
GET  /vue-element-admin/erp/sales/modules/:resource
POST /vue-element-admin/erp/sales/modules/:resource/save
POST /vue-element-admin/erp/sales/modules/:resource/action
POST /vue-element-admin/erp/sales/modules/:resource/audit
```

建议资源名：

```text
contracts
product-sales
sales-details
packages
card-packages
gift-lists
discounts
coupons
gift-applications
```

## 八、关键交互验收标准

### 合同管理

- 新增、编辑、审核、作废、变更、打印；
- 创建收款、查看收款、设置套餐、套餐升级；
- 金额摘要显示成交、已收、退款、欠款、优惠和应收；
- 审核弹窗支持通过/驳回、下一节点、审核人、抄送人。

### 商品销售

- 服务、物料、卡类三类新增入口；
- 商品明细支持数量、单价、折扣、优惠和总价联动；
- 支持收款、出库、退货、取消退货、换货；
- 支付和出库状态使用独立状态标签。

### 套餐与卡类套餐

- 套餐基本信息与项目明细分区；
- 支持提交、审核、反审核、启用、推荐、屏蔽、复制；
- 卡类套餐支持有效天数、卡类型和项目类型。

### 优惠与优惠券

- 优惠记录支持审核、反审核、停用；
- 优惠券支持总量、已发数量、每客户限领；
- 分发弹窗支持按客户姓名/手机号筛选并选择客户。

### 赠送

- 赠送清单支持物料明细；
- 赠送项目申请支持服务、物料、卡类三类；
- 支持流程审批、撤回、反审核和出库状态。

## 九、开发与验证命令

不要重新安装依赖，当前 `node_modules` 可用。

代码检查：

```powershell
.\node_modules\.bin\eslint.cmd src\views\erp\sales-workbench\index.vue src\config\sales-pages.js src\router\index.js src\api\erp-sales.js mock\erp-sales.js
```

生产构建：

```powershell
.\node_modules\.bin\vue-cli-service.cmd build
```

如遇到沙箱读取 `node_modules` 的 `EPERM`，应按 Codex 规则申请在沙箱外运行检查或构建。

本地服务：

```text
http://localhost:9527/#/sales/item-1
...
http://localhost:9527/#/sales/item-9
```

浏览器回归时至少验证：

1. 9 个页面标题与字段核对标识；
2. 每页专属筛选项和表格列；
3. 合同新增/审核；
4. 商品销售明细金额联动；
5. 套餐项目明细；
6. 优惠券分发；
7. 赠送申请审核；
8. 旧通用页面已全部切换为销售专用工作台。

完成浏览器工作后，最后一个浏览器动作应保留一个本地销售页面为 `deliverable`，并清理原 ERP 登录页和抓取页。

## 十、工作区注意事项

- 当前工作区有大量未提交修改，均属于用户此前任务，不要重置或覆盖；
- 不要运行 `git reset --hard`、`git checkout --` 等破坏性命令；
- 只修改与销售管理复刻相关的文件；
- 文件编辑使用 `apply_patch`；
- 不要把原 ERP 页面源码、Cookie、密码或真实业务数据保存到项目；
- 不要提交 Git，除非用户明确要求。

## 十一、可直接粘贴给下一位 GPT 的任务说明

> 请打开项目根目录的 `SALES_MIGRATION_HANDOFF.md`，严格按文档继续完成“销售管理”9 个页面的字段级复刻。先向我获取原 ERP 登录密码并只读核对列出的新增/编辑表单字段，然后新增销售字段配置、销售专用工作台、API 和 mock，切换路由，完成关键业务联动、ESLint、生产构建和浏览器逐页回归。保留现有全部用户修改，不读取或保存真实业务数据。

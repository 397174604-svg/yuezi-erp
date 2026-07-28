# 奇德芬芳 ERP：真实业务 ER 与 MySQL 5.7 数据库设计

日期：2026-07-27  
目标数据库：MySQL 5.7.21-log  
设计依据：当前新 ERP 已实现的 MySQL 表、旧妈妈宝盒只读采集结果，以及 `C:\Users\39717\Desktop\月子会所系统\月子会所资料` 中可核验的业务资料。

> 本文只使用资料中的业务结构、规则、频次和价格框架，不展示客户、员工手机号、身份证、住址、工资卡等真实个人数据。花名册只用于确认组织、员工、合同和岗位字段。

## 1. 结论

数据库应采用“模块化单体 + 统一主数据 + 事件流水”的方式建设，不建议把套餐、入住、护理、产康、库存继续堆叠到少数大表。

最重要的设计原则有六条：

1. `tenant_id + store_id` 是所有业务数据的隔离边界，服务层必须强制校验，不能只靠前端门店下拉框。
2. 客户、妈妈、宝宝、陪住人是不同业务主体；统一通过 `care_subjects` 建立护理、产康、膳食可引用的对象。
3. 套餐是“版本 + 门店 + 房型 + 天数 + 生效期 + 权益规则 + 赠品 + 可选组”的组合，不是一张名称价格表。
4. 合同签署时冻结套餐和权益快照；后续调价不能反向修改历史合同。
5. 服务必须形成“权益 → 预约 → 标准版本 → 执行步骤 → 实际耗材 → 库存流水 → 成本”的闭环。
6. 房态、金额、权益余额、库存余额均由不可变流水或时间区间计算，不直接人工改最终数字。

## 2. 资料证据与数据库影响

| 资料 | 已核验的业务事实 | 直接影响的数据库模块 |
| --- | --- | --- |
| 7 份月子套餐 PDF | 28/35/42/56 天价格梯度；按需护理、固定次数、任选项目、单项上限、赠品和家属餐同时存在 | 套餐版本、价格规则、权益规则、选择组、赠品、合同快照 |
| 黄河路店房间安排 | 3～6 楼共有 24 间可售客房；2 楼为产康空间；包含基础大床、一房一厅修复、总统套、女王套 | 空间、楼层、房型、房间、可售状态、房型与套餐销售策略 |
| 黄河路入所服务全流程 | 签约后建呵护群；入所前一周追踪；入住核验材料、余款与押金；房间准备；妈妈/宝宝双评估；离所前准备 | 客户生命周期、入所计划、资料清单、押金、准备清单、双主体评估、离所清单 |
| 护理部主任流程 | 交接班、每日/每周查房、新入住和重点客户加频、异常跨部门沟通、记录留痕 | 班次、排班、交接、护理计划、任务、查房、异常工单 |
| 客房主管流程 | 工单派发、备房、清洁消毒、布草、洗衣、维修、入住 24 小时宣教、满意度 | 客房任务、准备清单、资产交接、洗衣布草、维修、满意度计划 |
| 产康销售政策 | 单次价、疗程价、年卡、部位计次、不可叠加优惠、套餐赠送与销售提成 | 服务项目、价格本、项目卡、权益来源、促销互斥、提成规则 |
| 产康操作标准 | 项目分阶段/步骤执行；操作前后测量和影像；部分项目有禁忌、器械、消毒、复评要求 | 标准版本、步骤、测量定义、知情确认、器械、影像、员工项目授权 |
| 产品配料表 | 项目步骤对应产品编号与标准用量，存在 ml 等计量单位 | 物料主档、计量单位、标准 BOM、实际耗材、批次库存、项目成本 |
| 部门检查标准 | 按部门、类别、权重、检查项、扣分、月份统计运行 | 品控标准版本、检查实例、问题整改、复查、部门得分 |
| 两店花名册 | 员工、门店、部门、岗位、入离职、合同信息需要分层保存 | 组织、员工、职位、劳动合同、账号和 RBAC 分离 |
| 小程序会议纪要 | 移动端执行优先；房态未来占用、经营预测、客户标签、库存成本、积分和品控是明确方向 | 任务中心、事件台账、标签规则、经营事实表、积分与品控扩展 |

## 3. 已核验的套餐与房型实例

下列金额来自扫描版套餐 PDF 的 OCR，可用于建立首版价格规则草案；正式批量导入前仍需业务负责人对原件逐项复核。

| 套餐系列 | 空间/护理特征 | 28 天 | 35 天 | 42 天 | 56 天 |
| --- | --- | ---: | ---: | ---: | ---: |
| 基础套餐 | 大一居室、护士团队 | 24,999 | 29,999 | 35,999 | 45,999 |
| 基础系列 7+21 | 大一居室、7+21 护理 | 27,999 | 33,999 | 39,999 | 51,999 |
| 修复套餐 | 一房一厅、护士团队 | 27,999 | 33,999 | 39,999 | 51,999 |
| 修复 7+21 | 一房一厅、7+21 护理 | 29,999 | 35,999 | 42,999 | 55,999 |
| 修养套餐 | 一房一厅、双师护理 | 32,999 | 39,999 | 46,999 | 61,999 |
| 女王套餐 | 两室两厅、双师护理 | 63,999 | 76,999 | 92,999 | 120,999 |
| 总统套餐 | 三室三厅、双师护理 | 83,999 | 100,999 | 121,999 | 158,999 |

黄河路店首版物理空间：

| 楼层 | 可售房量 | 已核验结构 |
| --- | ---: | --- |
| 2 楼 | 0 | 产康业务空间，不计入客房可售库存 |
| 3 楼 | 8 | 一房一厅，修复类套餐 |
| 4 楼 | 8 | 北侧自东向西 3 间基础大床，其余 5 间一房一厅 |
| 5 楼 | 7 | 北侧自东向西 3 间基础大床，最北 1 间三室三厅总统套，其余 3 间一房一厅 |
| 6 楼 | 1 | 两室两厅女王套 |

房号尚未由资料明确给出，数据库可先建立楼层与房型库存，不应臆造房号。待房号清单确认后再写入 `rooms`。

## 4. 四个有界上下文 ER 图

完整业务拆成四张可维护 ER 子图，组合后是一份数据库蓝图：

1. [核心交易与入住 ER 图](./奇德芬芳ERP-核心交易与入住ER图.mmd)
2. [护理膳食执行 ER 图](./奇德芬芳ERP-护理膳食执行ER图.mmd)
3. [产康权益库存 ER 图](./奇德芬芳ERP-产康权益库存ER图.mmd)
4. [组织权限品控 ER 图](./奇德芬芳ERP-组织权限品控ER图.mmd)

## 5. 模块化表设计

### 5.1 平台、组织与权限

现有表可继续使用：`tenants`、`stores`、`departments`、`positions`、`staff`、`user_accounts`、`roles`、`permissions`、`user_roles`、`role_permissions`、`user_stores`、`role_data_scopes`、`field_permissions`。

必须保持：

- 员工档案与登录账号分离，一个员工可以暂时没有账号。
- 菜单权限、按钮动作、数据范围和字段权限分别授权。
- 员工换岗时关闭旧 `user_roles` 的有效期，不覆盖历史。
- 产康师“能否执行某个项目”使用项目授权表，不用菜单权限替代。

建议新增：

```text
staff_employment_contracts
staff_certifications
staff_training_results
staff_project_authorizations
access_delegations
```

### 5.2 客户与服务主体

现有 `customers` 保存商业客户主档；新增 `care_subjects` 作为执行层统一主体：

```text
customers
customer_entry_profiles
care_subjects
mother_profiles
baby_profiles
guardian_relations
customer_tags
customer_tag_evidence
customer_lifecycle_events
```

约束：

- 一个客户可以对应一位妈妈和多个宝宝。
- 陪住人、付款人和合同签署人不默认等于妈妈。
- 标签必须保存计算规则版本和证据，不直接保存“高价值客户”结论而无来源。
- 生命周期使用事件表推进，客户主表只缓存当前状态。

### 5.3 套餐、价格、促销与权益

目标表：

```text
package_products
package_versions
package_price_rules
package_entitlement_rules
package_choice_groups
package_choice_items
package_gift_rules
service_projects
price_books
price_book_items
promotion_policies
promotion_exclusions
commission_policies
```

关键唯一键与校验：

- `package_versions(package_id, version_no)` 唯一。
- `package_price_rules(package_version_id, store_id, room_type_id, stay_days, effective_from)` 唯一。
- 同一价格规则的生效区间不得重叠，由服务层事务校验。
- `frequency_type` 使用 `ONCE / COUNT / DAILY / WEEKLY / ON_DEMAND / CHOICE`。
- “任选 N 项”必须写入选择组的 `min_select`、`max_select`、`allow_repeat` 和单项上限。
- 合同签署后产生不可变 `contract_package_snapshots` 和 `contract_entitlement_snapshots`。

### 5.4 合同与财务

现有 `contracts`、`finance_receipts` 可扩展，目标表：

```text
contracts
contract_participants
contract_package_snapshots
contract_entitlement_snapshots
contract_charge_lines
accounts_receivable
finance_receipts
receipt_allocations
deposits
refund_applications
refund_allocations
payment_applications
settlements
```

金额规则：

- 所有金额字段使用 `DECIMAL(20,4)`，币种使用 `CHAR(3)`。
- `discount_rate = deal_amount / reference_amount` 仅作为查询结果或缓存值，不能作为唯一事实。
- 已收金额由“已审核且未冲销”的收款分摊汇总。
- 未入账金额由“已收款但未审核”的收款汇总。
- 退款按原收款分摊和原权益流水反向冲销，不直接改合同已收金额或权益余额。
- 退房状态和结算状态分开，支持“已退房未结账”。

### 5.5 客房、订房与入住

目标表：

```text
room_types
spaces
rooms
room_sales_strategies
room_bookings
stays
stay_participants
stay_readiness_templates
stay_readiness_tasks
stay_document_requirements
stay_document_submissions
room_cleaning_tasks
room_maintenance_tasks
room_asset_handovers
room_laundry_orders
room_linen_movements
checkout_plans
```

房态计算：

```text
可售房态
= 预订时间区间
+ 实际入住时间区间
+ 维修占用时间区间
+ 清洁/封房时间区间
```

不能只在 `rooms.status` 中硬写“空闲/入住”。`rooms.operational_status` 只描述房间是否启用，当前和未来房态由区间记录计算。

智能排房至少校验：

1. 用户是否拥有目标门店数据权限；
2. 合同是否已审核且入住日期有效；
3. 房间在目标区间没有预订、入住、维修或封房冲突；
4. 房型与合同快照的房型/升级规则相容；
5. 入住前准备清单是否达到允许入住的最低条件。

### 5.6 护理、交接与异常

目标表：

```text
care_assessment_templates
care_assessment_template_versions
care_assessments
care_plans
care_plan_items
care_tasks
care_task_executions
care_shifts
care_rosters
care_handovers
care_handover_items
care_rounds
service_issues
issue_escalations
```

关键规则：

- 妈妈和宝宝分别评估，均指向 `care_subjects`。
- 新入住、风险等级高、上一班未关闭异常的主体自动提高任务优先级。
- 交接班只携带未完成、异常、新增和重点观察项。
- 护理记录修正采用追加更正，不覆盖已签名执行记录。
- 护理发现膳食、产康、客房问题时创建跨部门 `service_issues`，记录责任部门、SLA、处理和关闭证据。

### 5.7 产康、项目卡与服务执行

目标表：

```text
service_projects
service_project_variants
service_protocol_versions
service_protocol_steps
service_measurement_definitions
service_contraindications
customer_entitlements
entitlement_ledger
service_appointments
service_executions
service_execution_steps
service_measurements
service_consents
service_media
staff_project_authorizations
```

服务综合查询中的四类数据直接来自 `customer_entitlements.source_type`：

```text
PACKAGE_INCLUDED
PACKAGE_EXTRA
ADDITIONAL_PURCHASE
PROJECT_CARD
```

执行完成事务必须同时：

1. 锁定并校验剩余权益；
2. 写入执行事实和步骤结果；
3. 写入权益扣减流水；
4. 写入实际耗材和库存出库流水；
5. 计算本次项目实际材料成本；
6. 写入审计事件。

其中任一步失败，整个事务回滚。

### 5.8 膳食

资料确认入住客户为“一日六餐/三餐三点”，并需要按体质、口味和恢复阶段调整。

目标表：

```text
dishes
dish_versions
dish_ingredients
dietary_restrictions
customer_diet_profiles
meal_plans
meal_plan_items
meal_orders
meal_production_batches
meal_deliveries
meal_samples
```

每次送餐必须关联入住、楼层、房间、餐次和客户禁忌检查结果；配送失败、拒收和改餐都保留原因。

### 5.9 仓存与成本

目标表：

```text
units_of_measure
materials
material_uom_conversions
warehouses
warehouse_bins
stock_lots
stock_movements
stock_balances
project_material_boms
service_material_consumptions
stock_counts
stock_count_lines
```

关键规则：

- 每种物料只能有一个基础计量单位，`ml`、`g`、支、片、套等用换算表处理。
- `stock_movements` 是库存事实，`stock_balances` 是可重建的余额缓存。
- 服务耗材必须记录实际批次，优先采用 FEFO（先到期先出）。
- 扣库存不能只保存“各 10”或“0.5G”等自由文本，导入前必须结构化。

### 5.10 品控、整改与满意度

目标表：

```text
qc_standards
qc_standard_versions
qc_standard_items
qc_inspections
qc_inspection_results
qc_evidence
qc_issues
qc_rectifications
qc_rechecks
qc_score_summaries
satisfaction_survey_templates
satisfaction_surveys
satisfaction_answers
```

品控标准、检查事实、整改和复查必须分表。护理超时、备房超时、维修超时、库存盘点未完成等系统可判断项应自动生成检查事实，人工只补充证据和说明。

## 6. 所有交易表的统一字段

建议每张业务交易表至少包含：

```text
tenant_id
store_id
status
version
created_at
created_by_user_id
updated_at
updated_by_user_id
deleted_at
correlation_id
```

其中：

- `version` 用于乐观锁，避免审批和执行并发覆盖。
- `correlation_id` 串联客户建档、合同、收款、订房、入住和任务展开。
- 已产生财务、权益、库存或护理事实的记录不物理删除，只能作废或冲销。
- 高敏感字段即使按项目要求明文存储，也必须通过 `field_permissions`、访问审计和导出审批限制使用。

## 7. MySQL 5.7 实现约束

- 引擎统一 `InnoDB`，字符集统一 `utf8mb4`。
- 金额使用 `DECIMAL(20,4)`，计量数量建议 `DECIMAL(20,6)`。
- MySQL 5.7 的 `CHECK` 约束不能作为唯一校验手段，状态流转、区间重叠、余额非负必须由服务层事务校验。
- JSON 快照可以使用 `JSON` 类型；需要索引的字段单独落列，不在查询中长期依赖 JSON 扫描。
- 大附件、照片、扫描件存对象存储，MySQL 只保存对象键、哈希、大小、访问级别和业务关联。
- 报表不直接跨几十张业务表实时计算；先使用事实表或按日汇总表，确保交易库可控。

## 8. 与当前数据库的衔接

当前已真实落库并可复用的主干包括：

```text
组织/RBAC
customers
customer_entry_profiles
contracts
finance_receipts
room_types
rooms
room_bookings
recovery_service_entitlements
recovery_appointments
recovery_service_records
recovery_material_consumptions
room_operation_records
mvp_audit_events
```

建议迁移策略：

1. 不删除当前主干表，先补充目标表和外键。
2. 将现有 `recovery_*` 数据映射到统一 `service_*` 与 `customer_entitlements`，保留兼容视图。
3. 将合同当前套餐字段转换为 `contract_package_snapshots`，历史数据标记 `source_quality = LEGACY_DERIVED`。
4. 将当前收款的单合同关联补充为 `receipt_allocations`，保持金额可追溯。
5. 将 `room_bookings` 的入住事实逐步迁移到 `stays`，避免预订和实际入住混在一行。
6. 每一步都做金额、权益、房态、库存和权限对账，不一次性替换全部模块。

## 9. 推荐实施顺序

### 第一阶段：可运营主链

- 套餐版本、价格规则、合同快照、应收与收款分摊；
- 房型、房间、订房、入住、入住参与人；
- 妈妈/宝宝双主体和入所准备清单。

### 第二阶段：服务执行

- 护理评估、计划、班次、任务、交接和异常；
- 产康权益、预约、标准版本、步骤和执行；
- 膳食计划、订单、禁忌校验和送餐。

### 第三阶段：成本与质量

- 物料、批次、库存流水、项目 BOM 和实际耗材；
- 品控标准、检查、整改、复查和满意度；
- 经营事实表与跨门店报表。

### 第四阶段：迁移与对账

- 导入经业务确认的套餐、价格、房型、员工和服务项目；
- 历史合同、收款、权益、入住和库存分别建立迁移批次；
- 对账通过后再切换真实生产入口。

## 10. 仍需业务确认的最小清单

1. 建设路店完整房号、楼层、房型和可售状态。
2. 黄河路店 24 间房的实际房号及 4/5 楼“大床房”精确房型名称。
3. 套餐价格是否按门店一致，以及各套餐版本生效/失效日期。
4. 扫描套餐中每项赠品和权益在 28/35/42/56 天下的最终数量。
5. 套餐升级、换房、续住、跨店订房和提前离所的计价规则。
6. 押金、退款、手续费、未审核收款和结算的会计口径。
7. 护理班次、夜间查房频次、异常 SLA 和必须双签的记录。
8. 产康项目执行人员资质、禁忌、复评节点和耗材换算。
9. 膳食阶段、禁忌、改餐、家属餐和留样规则。
10. 各角色的审批额度、跨店范围和敏感字段权限。

这些缺口不会阻碍先建表和实现 MVP，但在生产数据迁移和自动计费前必须确认。

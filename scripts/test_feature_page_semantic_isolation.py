#!/usr/bin/env python3
"""Regression guard for product routes that previously shared a fallback page."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


router = read("src/router/index.js")
sales = read("src/config/sales-pages.js")
schedule = read("src/config/schedule-pages.js")
schedule_view = read("src/views/erp/schedule-workbench/index.vue")
finance = read("src/config/finance-pages.js")
approval = read("src/config/approval-pages.js")
system = read("src/config/system-pages.js")
placeholder = read("src/views/erp/development-placeholder/index.vue")
p1_page = read("src/views/erp/p1-card-contract-minimal/index.vue")

# The product sidebar order fixes the actual browser paths used in regression:
# /sales/item-1..4 and /schedule/item-1..2.
assert "['sales', '销售管理', 'shopping', '#D17B57', ['F020', 'F050', 'F082', 'F107']]" in router
assert "['schedule', '预约与排班', 'form', '#5E9DAB', ['F017', 'F086']]" in router

# F082/F107/F089 use their existing dedicated card/contract/integration page;
# they must never inherit sales contracts or finance receipts by group fallback.
for token in (
    "'套餐卡/次卡管理': 'development-placeholder'",
    "电子合同: 'development-placeholder'",
    "'储值卡/折扣卡/微信卡包': 'development-placeholder'",
):
    assert token in router
assert "integrationFeaturePageTypes[sourceTitle]" in router
assert "featureId: feature ? feature.id : ''" in router
assert "this.$route.meta.featureId ||" in placeholder
for token in (
    "<template v-if=\"featureId === 'F082'\">",
    "新建待启用卡",
    "核销一次",
    "合同签署归档",
    "登记线下归档",
    "getCountCards({ storeId: this.currentStoreId })",
    "getContractArchives({ storeId: this.currentStoreId })",
):
    assert token in p1_page, f"missing dedicated F082/F107 page behavior: {token}"

# The four sales entries have distinct resource/config semantics.
for token in (
    "'合同与销售': {",
    "source: '合同管理'",
    "'套餐管理': {",
    "key: 'packages'",
    "'套餐卡/次卡管理': {",
    "key: 'card-packages'",
    "电子合同: {",
    "key: 'electronic-contract-archives'",
):
    assert token in sales, f"missing sales semantic token: {token}"
assert "filters: [input('customerName', '客户姓名'), input('contractNo', '合同编号')" in sales
assert "select('packageSelection', '套餐名称'" in sales

# The four sales menu entries also expose visibly different business flows
# instead of only changing the page title over one generic table shell.
sales_view = read("src/views/erp/sales-workbench/index.vue")
for token in (
    "title: '合同履约链路'",
    "title: '套餐目录与价格版本'",
    "title: '套餐卡与次卡规则'",
    "title: '电子签署与归档'",
):
    assert token in sales_view, f"missing sales flow distinction: {token}"

# The online board is not the operational appointment editor: it has its own
# alias, kind, filter dimensions, primary action and status-column definition.
for token in (
    "mode: 'operations'",
    "primaryAction: '新建预约'",
    "filterFields: ['storeId', 'date']",
    "mode: 'online-board'",
    "primaryAction: '刷新看板'",
    "filterFields: ['storeId', 'date', 'technician', 'channel']",
    "在线预约看板: '在线预约看板（技师/时段/多渠道）'",
):
    assert token in schedule, f"missing schedule semantic token: {token}"
for token in (
    'v-if="!isOnlineBoard"',
    'label="技师"',
    'label="渠道"',
    "技师 / 时段 / 渠道占用看板",
    'prop="channel" label="预约渠道"',
    "isOnlineBoard() { return this.config.mode === 'online-board' }",
):
    assert token in schedule_view, f"missing schedule UI distinction: {token}"

# Remaining P0/P2 mappings must resolve to a named feature config instead of
# the default receipt, approval or first-system-page configuration.
assert "key: 'member-card-wallets'" in finance
assert "if (financeStandaloneFeatureConfigs[title])" in finance
assert "featureId: 'F108'" in approval and "title: '审批流引擎'" in approval
assert "key: 'business-flow'" in approval and "key: 'admin-flow'" in approval
for key in ("system-parameter-settings", "history-data-migration", "brand-customization"):
    assert f"key: '{key}'" in system
assert "return systemFeatureConfigs[title] || systemPageConfigs[title]" in system

print("feature page semantic isolation checks passed: sales 4 routes, schedule 2 routes, fallback guards 5 domains")

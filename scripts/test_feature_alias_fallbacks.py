#!/usr/bin/env python3
"""Guards product-title normalization from silently selecting domain fallbacks."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


router = read("src/router/index.js")
matron = read("src/config/maternity-nurse-pages.js")
p0_features = read("src/config/p0-operations-features.js")
finance = read("src/config/finance-pages.js")
recovery = read("src/config/recovery-feature-pages.js")
rehab_view = read("src/views/erp/rehab-workbench/index.vue")
system = read("src/config/system-pages.js")
system_view = read("src/views/erp/system-workbench/index.vue")

# F046: registry title -> visible short title -> settlement resource.
assert "月嫂结算: '月嫂结算列表'" in matron
assert "page('maternity-settlements'" in matron
assert "canonicalPath: '/matron/item-2'" in p0_features
assert "canonicalPath: '/matron/item-3'" in p0_features

# F083: the visible short title is routed to the external-integration boundary,
# while direct config resolution also has a dedicated non-receipt key.
assert "在线支付: 'development-placeholder'" in router
assert "在线支付: {" in finance
assert "key: 'online-payment-integration'" in finance
assert "'在线支付（微信/支付宝）': { source: '在线支付' }" in finance

# F099: parenthetical registry title is normalized to its dedicated catalog,
# and the feature board returns before the legacy unbooked-customer API loads.
assert "产康项目管理: '产康项目管理（疗程/套餐/卡项）'" in recovery
assert "key: 'recovery-programs'" in recovery
assert "if (this.isRecoveryFeaturePage)" in rehab_view

# F098: both registry and short visible titles resolve to the branding key and
# the enhanced branding workbench rather than the generic system definition.
assert "key: 'brand-customization'" in system
assert "systemFeatureConfigs['品牌定制（Logo/主题色/专属域名）'] = systemFeatureConfigs.品牌定制" in system
assert "pageOverrides.品牌定制 = pageOverrides['品牌定制（Logo/主题色/专属域名）']" in system_view

# F016: recharge reporting reuses the receipt schema only after pinning the
# business discriminator to member recharge.
assert "'充值报表': {" in finance
assert "defaultFilters: { receiptType: '会员充值' }" in finance

print("feature alias fallback checks passed: F016/F046/F083/F098/F099")

#!/usr/bin/env python3
"""Static regression checks for the 104-item finance feature mapping.

These checks intentionally do not require a running API.  They make sure a
product-facing finance menu is mapped to a real finance resource and cannot
silently render the generic receipt page again.
"""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class FinanceFeatureIsolationTest(unittest.TestCase):
    def setUp(self):
        self.config = (ROOT / "src/config/finance-pages.js").read_text(encoding="utf-8")
        self.page = (ROOT / "src/views/erp/finance-workbench/index.vue").read_text(encoding="utf-8")

    def test_product_finance_features_have_explicit_source_mappings(self):
        expected = {
            "收银开单与订单": "新增收款",
            "财务收支": "收款管理",
            "退款与报销": "退款申请",
            "收支分析": "收款管理",
            "成本核算": "部门物料预算",
            "充值报表": "收款管理",
            "厂商并行期对账帮手": "交易对账",
            "在线支付（微信/支付宝）": "在线支付",
        }
        for feature, source in expected.items():
            self.assertIn(f"'{feature}': {{", self.config)
            start = self.config.index(f"'{feature}': {{")
            block = self.config[start:start + 800]
            self.assertIn(f"source: '{source}'", block)
            self.assertIn("description:", block)
            self.assertIn("metrics:", block)

    def test_feature_mapping_does_not_use_silent_receipts_fallback(self):
        self.assertIn("const financeFeatureAliases", self.config)
        self.assertIn("const sourceTitle = alias ? alias.source : title", self.config)
        self.assertIn("return alias ? { ...sourceConfig, ...alias } : sourceConfig", self.config)

    def test_finance_pages_use_three_distinct_visible_presentations(self):
        for marker in ("presentation: 'ledger'", "presentation: 'approval'", "presentation: 'analysis'"):
            self.assertIn(marker, self.config)
        for marker in ("config.presentation === 'ledger'", "config.presentation === 'approval'", "config.presentation === 'analysis'"):
            self.assertIn(marker, self.page)

    def test_runtime_uses_config_resource_and_legacy_permission_source(self):
        self.assertIn("financePermissionTitle()", self.page)
        self.assertIn("financeNavIds[this.financePermissionTitle]", self.page)
        self.assertIn("this.config.key === 'receipt-create'", self.page)
        self.assertIn("this.config.key === 'receipts'", self.page)
        self.assertIn("'$route.fullPath'", self.page)


if __name__ == "__main__":
    unittest.main()

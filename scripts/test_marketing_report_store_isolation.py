#!/usr/bin/env python3
"""Static regressions for marketing, reports and store-management surfaces.

The aim is to prevent product feature names from rendering an unrelated
workbench or fabricated local rows when their own data resource is absent.
"""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def source(path):
    return (ROOT / path).read_text(encoding="utf-8")


class ProductSurfaceIsolationTest(unittest.TestCase):
    def test_report_product_features_have_explicit_resources(self):
        report = source("src/config/report-pages.js")
        for title, expected_source in {
            "数据报表（自定义+导出）": "S13销售业绩报表",
            "经营月报": "C0经营月报",
        }.items():
            start = report.index(f"'{title}': {{")
            self.assertIn(f"source: '{expected_source}'", report[start:start + 700])
        self.assertIn("const reportFeatureAliases", report)
        self.assertIn("presentation: 'pending'", report)

    def test_report_view_has_distinct_builder_monthly_and_pending_states(self):
        view = source("src/views/erp/report-workbench/index.vue")
        for marker in ("config.presentation === 'report-builder'", "config.presentation === 'monthly-operation'", "config.presentation === 'pending'"):
            self.assertIn(marker, view)
        self.assertIn("dataStateLabel", view)
        self.assertIn("报表查询失败，请稍后重试", view)

    def test_store_view_does_not_seed_fictional_records_or_fallback_to_f058(self):
        view = source("src/views/erp/store-workbench/index.vue")
        self.assertIn("'门店管理': '门店与渠道（含转店）'", view)
        self.assertIn("|| unavailableDefinition", view)
        self.assertIn("createRows() { return [] }", view)
        self.assertNotIn("上海静安店", view)
        self.assertNotIn("杭州西湖店", view)
        self.assertNotIn("深圳南山店", view)

    def test_marketing_features_do_not_redirect_to_unrelated_customer_or_mall_pages(self):
        config = source("src/config/p0-operations-features.js")
        next_features = {"F039": "F040", "F041": "F042"}
        for feature, next_feature in next_features.items():
            start = config.index(f"id: '{feature}'")
            block = config[start:config.index(f"id: '{next_feature}'", start)]
            self.assertIn("component: 'marketing'", block)
            self.assertNotIn("canonicalPath", block)
        start = config.index("id: 'F127'")
        self.assertIn("title: '分销/渠道佣金'", config[start:start + 500])
        self.assertIn("component: 'marketing'", config[start:start + 500])


if __name__ == "__main__":
    unittest.main()

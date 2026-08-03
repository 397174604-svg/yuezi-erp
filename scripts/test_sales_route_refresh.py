#!/usr/bin/env python3
"""Static regression checks for sales workbench route isolation."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SalesRouteRefreshTest(unittest.TestCase):
    def setUp(self):
        self.router = (ROOT / "src/router/index.js").read_text(encoding="utf-8")
        self.page = (ROOT / "src/views/erp/sales-workbench/index.vue").read_text(encoding="utf-8")

    def test_product_sales_order_is_stable(self):
        self.assertIn("['sales', '销售管理', 'shopping', '#D17B57', ['F020', 'F050', 'F082', 'F107']]", self.router)

    def test_reused_component_activates_new_route(self):
        self.assertIn('beforeRouteUpdate(to, from, next)', self.page)
        self.assertIn('this.$nextTick(() => this.activateRoute(to))', self.page)
        self.assertIn('this.activePageConfig = getSalesPageConfig(pageTitle)', self.page)

    def test_late_response_cannot_replace_new_page(self):
        self.assertIn('const requestId = ++this.loadRequestId', self.page)
        self.assertIn('const pageKey = this.config.key', self.page)
        self.assertIn('if (requestId !== this.loadRequestId || pageKey !== this.config.key) return', self.page)


if __name__ == '__main__':
    unittest.main()

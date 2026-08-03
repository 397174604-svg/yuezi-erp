#!/usr/bin/env python3
"""Fast regression checks for the ERP P0 finance/contract delivery surface."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))

from erp_read_surfaces import report_module  # noqa: E402


P0_REPORTS = {
    "c1-member-recharge-summary",
    "c3-payment-summary-analysis",
    "c4-fund-income-expense-balance",
    "c7-store-income-cost-statistics",
    "c8-product-gross-profit-analysis",
    "c13-receipt-refund-summary",
}


class EmptyCursor:
    def __init__(self, statements: list[tuple[str, object]]):
        self.statements = statements

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def execute(self, sql, params=()):
        self.statements.append((sql, params))

    def fetchall(self):
        return []


class EmptyConnection:
    def __init__(self):
        self.statements: list[tuple[str, object]] = []

    def cursor(self):
        return EmptyCursor(self.statements)


class FinanceContractP0Test(unittest.TestCase):
    def test_real_report_resources_are_implemented_even_when_empty(self):
        user = {"tenant_id": 1, "store_ids": [10]}
        for resource in sorted(P0_REPORTS):
            with self.subTest(resource=resource):
                connection = EmptyConnection()
                result = report_module(connection, user, resource)
                self.assertEqual(result["source"], "mysql")
                self.assertTrue(result["implemented"])
                self.assertEqual(result["list"], [])
                self.assertTrue(connection.statements)
                sql = "\n".join(item[0] for item in connection.statements)
                self.assertIn("tenant_id", sql)
                self.assertIn("store_id", sql)

    def test_navigation_exposes_all_domain_workbenches(self):
        router = (ROOT / "src/router/index.js").read_text(encoding="utf-8")
        for title in (
            "合同管理",
            "商品销售",
            "销售明细",
            "新增收款",
            "收款管理",
            "退款申请",
            "退款审核",
            "发票管理",
            "交易对账",
            "我的费用",
            "费用审核",
            "C1 会员充值汇总明细表",
            "C3 付款汇总分析表",
            "C4 资金收支出余额表",
            "C7 门店收入与成本统计表",
            "C8 商品毛利分析表",
            "C13收款退款汇总表",
            "F080 厂商并行期对账帮手（开发中）",
            "F082 套餐卡/次卡管理（开发中）",
            "F083 在线支付（开发中）",
            "F089 储值卡/折扣卡/微信卡包（开发中）",
            "F107 电子合同（开发中）",
        ):
            with self.subTest(title=title):
                self.assertIn(title, router)

    def test_no_report_demo_fallback_and_money_state_guards_present(self):
        report_view = (
            ROOT / "src/views/erp/report-workbench/index.vue"
        ).read_text(encoding="utf-8")
        api = (ROOT / "server/mvp_api.py").read_text(encoding="utf-8")
        migration = (
            ROOT
            / "database/mysql/migrations"
            / "V20260731_023__finance_reconciliation.sql"
        ).read_text(encoding="utf-8")

        self.assertNotIn("createDemoRows", report_view)
        self.assertNotIn("sampleValue", report_view)
        self.assertIn("退款必须审批通过后才能打款", api)
        self.assertIn("不能重复开票", api)
        self.assertIn("仍有金额差异，不能确认匹配", api)
        self.assertIn("finance_reconciliations", migration)
        self.assertIn("external_reference", migration)

    def test_member_recharge_has_real_wallet_route_and_audit_fields(self):
        api = (ROOT / "server/mvp_api.py").read_text(encoding="utf-8")
        reports = (
            ROOT / "server/erp_read_surfaces.py"
        ).read_text(encoding="utf-8")
        asset_view = (
            ROOT / "src/views/erp/asset-workbench/index.vue"
        ).read_text(encoding="utf-8")
        migration = (
            ROOT
            / "database/mysql/migrations"
            / "V20260731_026__member_wallet_audit_fields.sql"
        ).read_text(encoding="utf-8")

        self.assertIn('asset_prefix = "/vue-element-admin/erp/assets"', api)
        self.assertIn("FOR UPDATE", api)
        self.assertIn("会员余额不足，不能扣款", api)
        self.assertIn("wallet_ledger", reports)
        self.assertIn("operator_user_id", migration)
        self.assertIn("activeTab: 'accounts'", asset_view)
        self.assertNotIn("getAssetList('cards'),", asset_view)


if __name__ == "__main__":
    unittest.main()

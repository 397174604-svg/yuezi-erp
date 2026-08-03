#!/usr/bin/env python3
"""Release-gate tests for finance/contract API state and isolation paths.

The local worktree has no MySQL credentials.  These tests therefore execute
the request-handler methods against a scripted DB-API cursor: they validate
the same SQL, permission, state and error paths without pretending to be a
live database smoke test.
"""

from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))


if "pymysql" not in sys.modules:
    pymysql = types.ModuleType("pymysql")
    cursors = types.ModuleType("pymysql.cursors")
    cursors.DictCursor = object
    pymysql.cursors = cursors
    sys.modules["pymysql"] = pymysql
    sys.modules["pymysql.cursors"] = cursors

from mvp_api import ApiError, MvpRequestHandler  # noqa: E402


class ScriptedCursor:
    def __init__(self, connection):
        self.connection = connection
        self.lastrowid = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def execute(self, sql, params=()):
        self.connection.statements.append((sql, params))
        upper = sql.upper()
        if "INSERT INTO COUNT_CARDS" in upper:
            self.lastrowid = 501
        elif "INSERT INTO SALES_CONTRACT_SIGN_ARCHIVES" in upper:
            self.lastrowid = 901

    def fetchone(self):
        return self.connection.rows.pop(0) if self.connection.rows else None


class ScriptedConnection:
    def __init__(self, rows):
        self.rows = list(rows)
        self.statements = []
        self.commits = 0

    def cursor(self):
        return ScriptedCursor(self)

    def commit(self):
        self.commits += 1


class HandlerHarness(MvpRequestHandler):
    def _success(self, data=None):
        return data or {}


def handler():
    return object.__new__(HandlerHarness)


FINANCE_USER = {
    "tenant_id": 1,
    "user_id": 7,
    "store_ids": [10],
    "roles": [],
    "permissions": {"FINANCE.CREATE", "FINANCE.VIEW"},
}

CONTRACT_USER = {
    "tenant_id": 1,
    "user_id": 7,
    "store_ids": [10],
    "roles": [],
    "permissions": {"LEGACY.WEB.N85.B10", "LEGACY.WEB.N85.B18"},
}

FINANCE_OPERATOR = {
    "tenant_id": 1,
    "user_id": 7,
    "username": "finance",
    "store_ids": [10],
    "roles": [],
    "permissions": {
        "LEGACY.WEB.N317.B3",
        "LEGACY.WEB.N653.B3",
    },
}

REFUND_OPERATOR = {
    "tenant_id": 1,
    "user_id": 7,
    "store_ids": [10],
    "roles": [],
    "permissions": {"LEGACY.WEB.N95.B1"},
}


class FinanceContractReleaseGateTest(unittest.TestCase):
    def test_card_creation_requires_same_store_approved_receipt_and_persists(self):
        connection = ScriptedConnection(
            [
                {"customer_id": 21, "store_id": 10},
                {"receipt_id": 31, "amount": "1200.00"},
                None,
            ]
        )
        result = handler()._create_asset_count_card(
            connection,
            FINANCE_USER,
            {
                "customerId": 21,
                "receiptNo": "SK-001",
                "cardName": "12次产康卡",
                "totalCount": 12,
                "validTo": "2026-12-31",
                "storeId": 10,
            },
        )
        self.assertEqual(result["id"], 501)
        self.assertEqual(result["status"], "待启用")
        self.assertEqual(connection.commits, 1)
        sql = "\n".join(item[0] for item in connection.statements)
        self.assertIn("store_id=%s AND customer_id=%s", sql)
        self.assertIn("status IN ('审核通过','已审核')", sql)
        self.assertIn("INSERT INTO erp_count_card_extensions", sql)
        self.assertIn("INSERT INTO mvp_audit_events", sql)

    def test_card_creation_rejects_cross_store_or_unapproved_receipt(self):
        connection = ScriptedConnection([{"customer_id": 21, "store_id": 10}, None])
        with self.assertRaisesRegex(ApiError, "收款单不存在、未审核或不属于该客户门店"):
            handler()._create_asset_count_card(
                connection,
                FINANCE_USER,
                {
                    "customerId": 21,
                    "receiptNo": "SK-OTHER-STORE",
                    "cardName": "12次产康卡",
                    "totalCount": 12,
                    "validTo": "2026-12-31",
                    "storeId": 10,
                },
            )

    def test_card_consume_rejects_insufficient_remaining_count(self):
        connection = ScriptedConnection(
            [
                {
                    "card_id": 501,
                    "store_id": 10,
                    "total_count": 12,
                    "used_count": 12,
                    "remain_count": 0,
                    "valid_end": "2026-12-31",
                    "lifecycle_status": "正常",
                }
            ]
        )
        with self.assertRaisesRegex(ApiError, "核销次数不能超过剩余次数"):
            handler()._perform_asset_count_card_action(
                connection,
                FINANCE_USER,
                501,
                "consume",
                {"count": 1, "storeId": 10},
            )

    def test_contract_archive_is_local_record_not_external_signature(self):
        connection = ScriptedConnection(
            [
                {
                    "contract_id": 41,
                    "store_id": 10,
                    "status": "已审核",
                    "archive_id": None,
                    "archive_status": None,
                }
            ]
        )
        result = handler()._post_contract_archive_resource(
            connection,
            CONTRACT_USER,
            "/41/archive",
            {
                "signedAt": "2026-07-31",
                "archiveReference": "ZX-20260731-01",
                "originalLocation": "中心店档案室 A 柜 03 格",
                "storeId": 10,
            },
        )
        self.assertEqual(result["id"], 901)
        self.assertEqual(result["status"], "线下已归档")
        sql = "\n".join(item[0] for item in connection.statements)
        self.assertIn("线下纸质签署", sql)
        self.assertNotIn("electronic_sign", sql.lower())
        self.assertIn("INSERT INTO mvp_audit_events", sql)

    def test_p0_release_paths_have_real_actions_and_explicit_external_limits(self):
        api = (ROOT / "server/mvp_api.py").read_text(encoding="utf-8")
        report_view = (ROOT / "src/views/erp/report-workbench/index.vue").read_text(encoding="utf-8")
        self.assertIn("收款金额不能超过合同剩余可收金额", api)
        self.assertIn("退款必须审批通过后才能打款", api)
        self.assertIn("费用必须审批通过后才能打款", api)
        self.assertIn("尚未配置真实支付通道，禁止生成虚假支付结果", api)
        self.assertIn("finance_reconciliations", api)
        self.assertIn("exportRows", report_view)
        self.assertNotIn("createDemoRows", report_view)

    def test_refund_requires_current_store_customer_before_creating(self):
        with self.assertRaisesRegex(ApiError, "退款申请必须选择当前门店客户"):
            handler()._save_finance_refund(
                ScriptedConnection([]),
                REFUND_OPERATOR,
                {"storeId": 10, "refundAmount": 100, "refundType": "合同退款"},
                0,
            )

    def test_paid_expense_and_non_pending_exchange_cannot_be_deleted(self):
        paid_expense = ScriptedConnection(
            [{"expense_id": 71, "store_id": 10, "status": "已打款", "apply_amount": 100}]
        )
        with self.assertRaisesRegex(ApiError, "只有待提交或驳回的费用单可以删除"):
            handler()._finance_expense_action(
                paid_expense, FINANCE_OPERATOR, "my-expenses", "删除", 71, {}
            )

        approved_exchange = ScriptedConnection(
            [{"exchange_id": 81, "store_id": 10, "audit_status": "已通过"}]
        )
        with self.assertRaisesRegex(ApiError, "只有待审核或已驳回的换货单可以删除"):
            handler()._finance_exchange_action(
                approved_exchange, FINANCE_OPERATOR, "删除", 81, {}
            )

    def test_frontend_translates_http_status_and_matches_required_fields(self):
        request = (ROOT / "src/utils/request.js").read_text(encoding="utf-8")
        finance_config = (ROOT / "src/config/finance-pages.js").read_text(encoding="utf-8")
        finance_view = (
            ROOT / "src/views/erp/finance-workbench/index.vue"
        ).read_text(encoding="utf-8")
        api = (ROOT / "server/mvp_api.py").read_text(encoding="utf-8")
        for code, message in (
            ("400", "提交信息不符合业务规则"),
            ("403", "当前账号没有执行此业务操作的权限"),
            ("404", "业务记录不存在，或当前门店无权访问"),
        ):
            self.assertIn(code, request)
            self.assertIn(message, request)
        self.assertIn("picker('customerName', '选择客户', 'customer', true", finance_config)
        self.assertIn("收款单不能直接标记已开票", api)
        self.assertIn("FINANCE_ACTION_BUTTON_IDS", api)
        self.assertIn("saveFinanceModuleRecord", finance_view)
        self.assertIn("performFinanceModuleAction", finance_view)
        for resource in (
            "receipt-create",
            "receipts",
            "refund-applications",
            "refund-audits",
            "debt-audits",
            "invoices",
            "reconciliations",
            "my-expenses",
            "expense-audits",
        ):
            with self.subTest(resource=resource):
                self.assertIn(f'"{resource}"', api)
                self.assertIn(f"key: '{resource}'", finance_config)

    def test_duplicate_entry_consolidation_keeps_each_finance_capability(self):
        finance_config = (ROOT / "src/config/finance-pages.js").read_text(encoding="utf-8")
        finance_view = (
            ROOT / "src/views/erp/finance-workbench/index.vue"
        ).read_text(encoding="utf-8")
        asset_view = (
            ROOT / "src/views/erp/asset-workbench/index.vue"
        ).read_text(encoding="utf-8")
        api = (ROOT / "server/mvp_api.py").read_text(encoding="utf-8")
        self.assertIn("前往新增收款", finance_config)
        self.assertIn("登记真实发票", finance_config)
        self.assertIn("登记退款打款", finance_config)
        self.assertIn("退款申请", finance_config)
        self.assertNotIn("actions: ['添加', '编辑', '删除', '打印', '提交', '打款', '导出']", finance_config)
        self.assertIn("action === '前往新增收款'", finance_view)
        self.assertIn("action === '打款' || action === '登记退款打款'", finance_view)
        self.assertIn('"登记退款打款": 54', api)
        self.assertIn('action in {"打款", "登记退款打款"}', api)
        self.assertNotIn('v-if="false" label="套餐卡 / 次卡"', asset_view)
        self.assertNotIn("createAssetRecord('cards'", asset_view)

    def test_current_store_scope_rejects_all_store_for_finance_details(self):
        scoped_user = handler()._finance_current_store_user(
            FINANCE_USER, {"storeId": 10}
        )
        self.assertEqual(scoped_user["store_ids"], [10])
        with self.assertRaisesRegex(ApiError, "全部门店仅支持汇总查询"):
            handler()._finance_current_store_user(
                FINANCE_USER, {"storeId": "all"}
            )
        with self.assertRaisesRegex(ApiError, "请先选择具体门店"):
            handler()._finance_store_id(
                ScriptedConnection([]), FINANCE_USER, {"storeId": "all"}
            )

    def test_finance_and_contract_pages_expose_distinct_workflow_closures(self):
        finance_config = (ROOT / "src/config/finance-pages.js").read_text(encoding="utf-8")
        finance_view = (
            ROOT / "src/views/erp/finance-workbench/index.vue"
        ).read_text(encoding="utf-8")
        sales_view = (
            ROOT / "src/views/erp/sales-workbench/index.vue"
        ).read_text(encoding="utf-8")
        for title in (
            "退款申请闭环",
            "退款审批与出纳打款",
            "人工交易对账闭环",
            "真实发票档案",
            "本人费用申请",
            "费用审批工作台",
            "付款流水复核",
        ):
            self.assertIn(title, finance_config)
        self.assertIn("rowWorkflowAction", finance_view)
        self.assertIn("runRowWorkflow", finance_view)
        self.assertIn("合同履约闭环", sales_view)
        self.assertIn("contractNextAction", sales_view)
        self.assertIn("runContractNext", sales_view)


if __name__ == "__main__":
    unittest.main()

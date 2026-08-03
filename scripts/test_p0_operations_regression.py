"""Offline regression checks for P0 operation HTTP failures and scope guards.

These assertions intentionally exercise the release contracts that can be
verified without a shared MySQL instance: the browser must translate raw HTTP
failures to operational messages, and P0 write/query paths must retain their
server-side permission and store-scope guards.
"""

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUEST = ROOT / "src/utils/request.js"
FOUNDATION = ROOT / "src/views/erp/foundation/index.vue"
SALES = ROOT / "src/views/erp/sales-workbench/index.vue"
REPORT = ROOT / "src/views/erp/report-workbench/index.vue"
CUSTOMER = ROOT / "src/views/erp/customer-workbench/index.vue"
API = ROOT / "server/mvp_api.py"
READ_SURFACES = ROOT / "server/erp_read_surfaces.py"


class P0OperationsRegressionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.request = REQUEST.read_text(encoding="utf-8")
        cls.foundation = FOUNDATION.read_text(encoding="utf-8")
        cls.sales = SALES.read_text(encoding="utf-8")
        cls.report = REPORT.read_text(encoding="utf-8")
        cls.customer = CUSTOMER.read_text(encoding="utf-8")
        cls.api = API.read_text(encoding="utf-8")
        cls.read_surfaces = READ_SURFACES.read_text(encoding="utf-8")

    def test_http_failures_are_translated_to_business_messages(self) -> None:
        for status, message in (
            (400, "请求参数不符合要求"),
            (403, "当前账号没有此操作权限或无权访问该门店"),
            (404, "业务接口不存在或尚未接入，请勿将此结果视为成功"),
        ):
            self.assertIn(f"{status}: '{message}", self.request)
        self.assertIn("serverMessage || statusMessages", self.request)
        self.assertIn("error.message = message", self.request)

    def test_save_success_is_after_awaited_api_only(self) -> None:
        self.assertIn("await saveFoundationRecord", self.foundation)
        self.assertIn("await saveRolePermissions", self.foundation)
        self.assertNotIn("模拟接口", self.foundation)
        self.assertIn("await saveSalesModuleRecord", self.sales)
        self.assertIn("try {", self.sales)

    def test_report_failure_never_claims_query_success(self) -> None:
        self.assertIn("return false", self.report)
        self.assertIn("if (!loaded) return this.$message.warning", self.report)
        self.assertIn("报表查询失败，请稍后重试", self.report)

    def test_exports_follow_filtered_rows_and_keep_zero_values(self) -> None:
        self.assertIn("this.filteredRows.map", self.report)
        self.assertIn("this.filteredRows.map", self.sales)
        self.assertIn("row[column.key] === undefined || row[column.key] === null", self.sales)

    def test_backend_writes_and_reports_enforce_scope(self) -> None:
        for token in (
            "def _foundation_store_id",
            "self._allowed_store(user, store_id)",
            "def _save_foundation_department",
            "def _save_foundation_role_permissions",
            "当前账号无权访问所选门店",
        ):
            self.assertIn(token, self.api)
        self.assertIn('resource == "c0-monthly-operation"', self.read_surfaces)
        self.assertIn("_store_scope(user, \"receipt\")", self.read_surfaces)

    def test_selected_store_is_sent_and_aggregate_write_is_rejected(self) -> None:
        for page in (self.foundation, self.sales, self.report, self.customer):
            self.assertIn("currentStoreId", page)
        self.assertIn("selectedStoreId: this.currentStoreId", self.foundation)
        self.assertIn("selectedStoreId: this.currentStoreId", self.sales)
        self.assertIn("storeId: this.currentStoreId || 'all'", self.report)
        self.assertIn("storeId: this.currentStoreId || 'all'", self.customer)
        self.assertIn("def _user_for_selected_store", self.api)
        self.assertIn("def _require_selected_write_store", self.api)
        self.assertIn("全部门店仅支持汇总查询", self.api)


if __name__ == "__main__":
    unittest.main()

"""Static acceptance checks for the F038-F061 ERP delivery surface."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FEATURE_CONFIG = ROOT / "src/config/p0-operations-features.js"
ROUTER = ROOT / "src/router/index.js"
MAIN = ROOT / "src/main.js"
SALES_API = ROOT / "src/api/erp-sales.js"
STATUS_VIEW = ROOT / "src/views/erp/p0-operations-status/index.vue"
FOUNDATION_VIEW = ROOT / "src/views/erp/foundation/index.vue"
MVP_API = ROOT / "server/mvp_api.py"
READ_SURFACES = ROOT / "server/erp_read_surfaces.py"
PACKAGE_MIGRATION = ROOT / "database/mysql/migrations/V20260731_024__package_price_versions.sql"
ASSET_MIGRATION = ROOT / "database/mysql/migrations/V20260801_028__member_asset_ledger.sql"
ASSET_VIEW = ROOT / "src/views/erp/asset-workbench/index.vue"


class P0OperationsSurfaceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.feature_source = FEATURE_CONFIG.read_text(encoding="utf-8")
        cls.router_source = ROUTER.read_text(encoding="utf-8")
        cls.main_source = MAIN.read_text(encoding="utf-8")
        cls.sales_api_source = SALES_API.read_text(encoding="utf-8")
        cls.status_source = STATUS_VIEW.read_text(encoding="utf-8")
        cls.foundation_source = FOUNDATION_VIEW.read_text(encoding="utf-8")
        cls.mvp_api_source = MVP_API.read_text(encoding="utf-8")
        cls.read_surfaces_source = READ_SURFACES.read_text(encoding="utf-8")
        cls.asset_source = ASSET_VIEW.read_text(encoding="utf-8")

    def test_all_24_excel_feature_ids_are_declared_once(self) -> None:
        p0_source = self.feature_source.split("export const p1OperationsFeatures")[0]
        declared = re.findall(r"\bid:\s*'(F\d{3})'", p0_source)
        expected = [f"F{number:03d}" for number in range(38, 62)]
        self.assertEqual(declared, expected)
        self.assertEqual(len(set(declared)), 24)

    def test_each_feature_has_permissions_and_delivery_state(self) -> None:
        p0_source = self.feature_source.split("export const p1OperationsFeatures")[0]
        records = re.findall(r"\{ id: '(F\d{3})',(.*?)\n", p0_source)
        self.assertEqual(len(records), 24)
        for feature_id, record in records:
            with self.subTest(feature_id=feature_id):
                self.assertRegex(record, r"permissions:\s*\[[^\]]+\]")
                self.assertRegex(
                    record,
                    r"state:\s*'(real|partial|external|blocked)'",
                )
                self.assertIn("scope:", record)

    def test_router_builds_a_route_for_every_feature(self) -> None:
        self.assertIn(
            "children: [...p0OperationsFeatures, ...p1OperationsFeatures].map(feature => ({",
            self.router_source,
        )
        self.assertIn("path: feature.id.toLowerCase()", self.router_source)
        self.assertIn("featureId: feature.id", self.router_source)
        self.assertIn("permissions: feature.permissions", self.router_source)
        self.assertIn("p0OperationsRoute", self.router_source)

    def test_confirmed_duplicate_entries_redirect_to_formal_workbenches(self) -> None:
        for path in (
            "/customer/member/item-1",
            "/matron/item-1",
            "/matron/item-2",
            "/matron/item-3",
            "/basic/item-2",
            "/sales/item-4",
            "/people/item-6",
            "/people/item-7",
            "/store/item-1",
            "/report/item-13",
            "/system/item-1",
        ):
            self.assertIn(f"canonicalPath: '{path}'", self.feature_source)
        self.assertIn(
            "...(feature.canonicalPath ? { redirect: feature.canonicalPath } : {})",
            self.router_source,
        )
        self.assertIn("pageType: 'store-management'", self.feature_source)
        self.assertIn("'store-management'", self.router_source)

    def test_status_page_never_claims_an_unverified_success(self) -> None:
        self.assertNotIn("$message.success", self.status_source)
        self.assertIn("保持待处理状态", self.status_source)
        self.assertIn("外部服务配置中", self.status_source)

    def test_foundation_write_actions_are_real_or_explicitly_unavailable(self) -> None:
        self.assertNotIn("配置已保存（模拟接口）", self.foundation_source)
        self.assertNotIn("角色权限已保存（模拟接口）", self.foundation_source)
        self.assertIn("saveFoundationRecord", self.foundation_source)
        self.assertIn("saveRolePermissions", self.foundation_source)
        self.assertIn("已保存到当前租户的数据源", self.foundation_source)
        self.assertIn("尚未开放写入，未保存本次修改", self.foundation_source)

    def test_p1_entries_are_visible_without_changing_main_menu_config(self) -> None:
        self.assertIn("export const p1OperationsFeatures", self.feature_source)
        for feature_id in ("F096", "F126", "F127", "F128"):
            self.assertIn(f"id: '{feature_id}'", self.feature_source)
        self.assertNotIn("erp-menu", self.feature_source)

    def test_foundation_writes_are_permission_scoped_and_audited(self) -> None:
        for token in (
            "def _require_foundation_write",
            "SYSTEM.EDIT",
            "def _save_foundation_department",
            "def _save_foundation_role",
            "def _save_foundation_role_permissions",
            "当前账号无权访问所选门店",
            'self._audit(connection, user, "department"',
            'self._audit(connection, user, "role"',
        ):
            self.assertIn(token, self.mvp_api_source)

    def test_monthly_report_and_package_prices_have_real_storage_contracts(self) -> None:
        self.assertIn('resource == "c0-monthly-operation"', self.read_surfaces_source)
        self.assertIn("GROUP BY DATE_FORMAT(receipt.received_at", self.read_surfaces_source)
        self.assertTrue(PACKAGE_MIGRATION.is_file())
        migration = PACKAGE_MIGRATION.read_text(encoding="utf-8")
        self.assertIn("activity_price", migration)
        self.assertIn("effective_date", migration)
        self.assertIn("套餐价格须满足原价≥活动价≥成交价", self.mvp_api_source)

    def test_api_build_cannot_inject_browser_mock(self) -> None:
        self.assertIn(
            "process.env.VUE_APP_ENABLE_MOCK === 'true'",
            self.main_source,
        )
        self.assertIn(
            "process.env.VUE_APP_RUNTIME_MODE !== 'mvp'",
            self.main_source,
        )
        self.assertNotIn(
            "if (process.env.NODE_ENV === 'production')",
            self.main_source,
        )

    def test_package_fields_are_adapted_to_real_sales_api(self) -> None:
        for token in (
            "basePackageName: row.basePackageName || row.packageName",
            "packageName: data.packageName || data.basePackageName",
            "packageAmount: data.packageAmount || data.dealPrice",
            "validDays: data.validDays || data.packageDays",
        ):
            self.assertIn(token, self.sales_api_source)

    def test_hidden_mvp_asset_mock_route_is_removed(self) -> None:
        self.assertNotIn("name: 'AssetWorkbench'", self.router_source)
        self.assertIn(
            "permissions: ['CUSTOMER.VIEW', 'FINANCE.VIEW']",
            self.router_source,
        )

    def test_member_assets_use_a_real_store_owned_ledger(self) -> None:
        self.assertTrue(ASSET_MIGRATION.is_file())
        migration = ASSET_MIGRATION.read_text(encoding="utf-8")
        for table in (
            "member_asset_accounts",
            "member_asset_cards",
            "member_asset_transactions",
        ):
            self.assertIn(table, migration)
        for token in (
            'asset_prefix = "/vue-element-admin/erp/assets"',
            "def _create_member_asset_card",
            "def _consume_member_asset_card",
            "def _adjust_member_asset_account",
            "def _asset_write_store",
        ):
            self.assertIn(token, self.mvp_api_source)
        self.assertIn("selectedStoreId: this.currentStoreId", self.asset_source)
        self.assertIn("storeId: this.currentStoreId || 'all'", self.asset_source)

    def test_non_mock_production_uses_protected_dynamic_routes(self) -> None:
        self.assertIn(
            "process.env.VUE_APP_ENABLE_MOCK !== 'true'",
            self.router_source,
        )
        self.assertIn(
            "useProtectedErpRoutes ? erpDeliveryRoutes : []",
            self.router_source,
        )


if __name__ == "__main__":
    unittest.main()

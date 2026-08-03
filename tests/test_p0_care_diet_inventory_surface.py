import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class P0CareDietInventorySurfaceTest(unittest.TestCase):
    FEATURES = {
        "F021": "护理中心",
        "F022": "护理评估（产后恢复）",
        "F023": "膳食统计",
        "F024": "护理看板",
        "F025": "护理二次销售业绩",
        "F026": "入住交接（物品清点）",
        "F027": "宝宝日志",
        "F028": "订餐配送",
        "F029": "月子餐库",
        "F030": "库房管理",
        "F031": "跨店调拨",
        "F032": "库存盘点",
        "F033": "库存预警",
        "F034": "采购管理",
        "F035": "库存估值",
        "F036": "批次保质期（效期预警）",
        "F037": "供应商管理",
    }

    def test_all_exact_titles_are_in_menu_and_route_allowlist(self):
        menu = (ROOT / "src/config/erp-menu.js").read_text(encoding="utf-8")
        router = (ROOT / "src/router/index.js").read_text(encoding="utf-8")
        for feature_id, title in self.FEATURES.items():
            with self.subTest(feature_id=feature_id):
                self.assertIn(title, menu)
                self.assertIn(title, router)

    def test_write_endpoints_and_store_scope_are_present(self):
        api = (ROOT / "server/mvp_api.py").read_text(encoding="utf-8")
        migration = (
            ROOT
            / "database/mysql/migrations/"
            "V20260731_025__care_diet_inventory_operational_records.sql"
        ).read_text(encoding="utf-8")
        self.assertIn('r"([^/]+)/(save|action)"', api)
        self.assertIn("erp_operational_records", api)
        self.assertIn("store_id BIGINT NOT NULL", migration)
        self.assertIn("ix_operational_scope", migration)

    def test_duplicate_aliases_are_exposed_as_shared_workbench_tabs(self):
        nursing = (ROOT / "src/config/nursing-pages.js").read_text(encoding="utf-8")
        diet = (ROOT / "src/config/diet-pages.js").read_text(encoding="utf-8")
        inventory = (ROOT / "src/config/inventory-pages.js").read_text(encoding="utf-8")
        tab_helper = (ROOT / "src/utils/erp-workbench-tabs.js").read_text(encoding="utf-8")

        self.assertIn("'F022', '护理评估（产后恢复）'", nursing)
        self.assertIn("'F026', '入住交接（物品清点）'", nursing)
        self.assertIn("'F027', '宝宝日志'", nursing)
        self.assertIn("'F028', '订餐配送'", diet)
        self.assertIn("'F029', '月子餐库'", diet)
        for feature_id, title in self.FEATURES.items():
            if feature_id in {"F030", "F031", "F032", "F033", "F034"}:
                self.assertIn(f"'{feature_id}', '{title}'", inventory)
        self.assertIn("findErpRouteByTitle", tab_helper)
        for path in [
            "src/views/erp/nursing-workbench/index.vue",
            "src/views/erp/diet-workbench/index.vue",
            "src/views/erp/inventory-workbench/index.vue",
        ]:
            view = (ROOT / path).read_text(encoding="utf-8")
            self.assertIn("sharedWorkspaceTabs", view)
            self.assertIn("switchSharedWorkspace", view)

    def test_store_scoped_writes_and_reference_options_are_enforced(self):
        api = (ROOT / "server/mvp_api.py").read_text(encoding="utf-8")
        diet_view = (ROOT / "src/views/erp/diet-workbench/index.vue").read_text(encoding="utf-8")
        inventory_view = (ROOT / "src/views/erp/inventory-workbench/index.vue").read_text(encoding="utf-8")
        nursing_dialog = (ROOT / "src/views/erp/nursing-workbench/NursingToolbarDialog.vue").read_text(encoding="utf-8")

        self.assertIn("全部门店仅可查询汇总", api)
        self.assertIn("编辑记录必须选择其所属门店", api)
        self.assertIn("_get_store_reference_options", api)
        self.assertIn("reference-options", api)
        self.assertIn("customer-select", diet_view)
        self.assertIn("dish-select", diet_view)
        self.assertIn("material-select", inventory_view)
        self.assertIn("supplier-select", inventory_view)
        self.assertIn("customer-select", nursing_dialog)
        self.assertIn("room-select", nursing_dialog)

    def test_management_modules_have_dedicated_workflows(self):
        nursing = (ROOT / "src/views/erp/components/NursingP0Workflow.vue").read_text(encoding="utf-8")
        diet = (ROOT / "src/views/erp/components/DietP0Workflow.vue").read_text(encoding="utf-8")
        inventory = (ROOT / "src/views/erp/components/InventoryP0Workflow.vue").read_text(encoding="utf-8")

        self.assertIn("产后恢复观察与跟进", nursing)
        self.assertIn("入住物品清点与交接", nursing)
        self.assertIn("订餐配送履约看板", diet)
        self.assertIn("月子餐库", diet)
        self.assertIn("采购订单履约", inventory)
        self.assertIn("跨店调拨双端跟踪", inventory)
        self.assertIn("库存盘点差异处理", inventory)
        self.assertIn("库存预警处置队列", inventory)


if __name__ == "__main__":
    unittest.main()

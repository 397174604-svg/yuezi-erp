import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DietRoomAssignmentRegressionTest(unittest.TestCase):
    def test_room_is_selected_not_free_text(self):
        config = (ROOT / "src/config/diet-pages.js").read_text(encoding="utf-8")
        view = (ROOT / "src/views/erp/diet-workbench/index.vue").read_text(
            encoding="utf-8"
        )
        self.assertIn("room-select", config)
        self.assertIn("getDietRoomOptions", view)
        self.assertIn("请从当前门店在住客户房间列表中选择房间", view)

    def test_server_checks_store_room_and_active_stay(self):
        api = (ROOT / "server/mvp_api.py").read_text(encoding="utf-8")
        self.assertIn("def _get_diet_room_options", api)
        self.assertIn("booking.status='已入住'", api)
        self.assertIn("所选房间不属于当前门店", api)
        self.assertIn("客户不一致", api)

    def test_p0_error_contract_uses_business_responses(self):
        api = (ROOT / "server/mvp_api.py").read_text(encoding="utf-8")
        view = (ROOT / "src/views/erp/diet-workbench/index.vue").read_text(
            encoding="utf-8"
        )
        self.assertIn("所选门店与当前页面门店不一致", api)  # 403
        self.assertIn("膳食资源不存在", api)  # 404
        self.assertIn("请先选择具体门店后加载房间", api)  # 400
        self.assertIn("保存失败，请核对门店、房间归属和入住状态", view)


if __name__ == "__main__":
    unittest.main()

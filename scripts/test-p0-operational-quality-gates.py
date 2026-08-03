#!/usr/bin/env python3
"""P0 operational UI/API quality gates that do not need a live database."""

import re
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))

from erp_read_surfaces import nursing_module  # noqa: E402
from mvp_api import MvpRequestHandler  # noqa: E402


TARGETS = {
    "护理": ROOT / "src/views/erp/nursing-workbench/index.vue",
    "膳食": ROOT / "src/views/erp/diet-workbench/index.vue",
    "库存": ROOT / "src/views/erp/inventory-workbench/index.vue",
    "会员资产": ROOT / "src/views/erp/asset-workbench/index.vue",
    "报表": ROOT / "src/views/erp/report-workbench/index.vue",
}


class P0OperationalQualityGates(unittest.TestCase):
    def setUp(self):
        self.handler = object.__new__(MvpRequestHandler)
        self.handler._require_any_permission = lambda *_args: None
        self.handler._store_clause = lambda *_args: ("1=1", [])
        self.handler._success = lambda data: data
        self.user = {
            "tenant_id": 1,
            "user_id": 1,
            "store_ids": [1, 2],
            "permissions": [
                "NURSING.VIEW",
                "DIET.VIEW",
                "INVENTORY.VIEW",
                "REPORT.VIEW",
                "FINANCE.VIEW",
            ],
        }

    @patch("erp_read_surfaces._rows", return_value=[{"id": 1}])
    def test_nursing_query_uses_mysql_loader(self, rows):
        result = nursing_module(None, self.user, "nursing-center")
        self.assertEqual(result["source"], "mysql")
        self.assertEqual(result["total"], 1)
        rows.assert_called_once()

    @patch("mvp_api.execute_all", return_value=[{"id": 1}])
    def test_diet_query_returns_database_rows(self, execute_all):
        result = self.handler._get_diet_module_data(
            None, self.user, "dishes", {}
        )
        self.assertEqual(result["total"], 1)
        execute_all.assert_called_once()

    @patch("mvp_api.execute_all", return_value=[{"id": 1}])
    def test_inventory_query_returns_database_rows(self, execute_all):
        result = self.handler._get_inventory_module_data(
            None, self.user, "other-inbounds", {}
        )
        self.assertEqual(result["total"], 1)
        execute_all.assert_called_once()

    def test_unimplemented_writes_are_501_not_404_or_fake_success(self):
        api_source = (ROOT / "server/mvp_api.py").read_text(encoding="utf-8")
        for message in (
            "当前膳食页面尚未接入写操作",
            "当前仓存页面尚未接入写操作",
        ):
            pattern = rf'{re.escape(message)}[\s\S]{{0,120}}501[\s\S]{{0,40}}50100'
            self.assertRegex(api_source, pattern)

        self.assertRegex(
            api_source,
            r'f"当前\{module_name\}页面尚未接入写操作"[\s\S]{0,120}501[\s\S]{0,40}50100',
        )

        banned = re.compile(r"\$message\.success\([^\n]*(演示|本地)")
        for label in ("护理", "膳食", "库存"):
            source = TARGETS[label].read_text(encoding="utf-8")
            self.assertIsNone(banned.search(source), f"{label}入口不得伪报成功")

    def test_failed_queries_never_fall_back_to_demo_rows(self):
        nursing = TARGETS["护理"].read_text(encoding="utf-8")
        diet = TARGETS["膳食"].read_text(encoding="utf-8")
        inventory = TARGETS["库存"].read_text(encoding="utf-8")
        self.assertNotIn("this.rows = this.createDemoRows()", nursing)
        self.assertIn("护理数据查询失败，未使用演示数据替代", nursing)
        self.assertIn("膳食数据查询失败，未使用演示数据替代", diet)
        self.assertIn("库存数据查询失败，未使用演示数据替代", inventory)

    def test_all_five_p0_surfaces_export_current_real_results(self):
        export_markers = {
            "护理": "exportCsv()",
            "膳食": "exportCsv()",
            "库存": "exportCsv()",
            "会员资产": "exportCurrentAsset()",
            "报表": "exportRows()",
        }
        for label, marker in export_markers.items():
            source = TARGETS[label].read_text(encoding="utf-8")
            self.assertIn(marker, source, f"{label}缺少导出实现")
            self.assertNotIn("脱敏演示.csv", source, f"{label}仍在导出演示文件")


if __name__ == "__main__":
    unittest.main(verbosity=2)

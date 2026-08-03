#!/usr/bin/env python3
"""Static guard for F044/F045/F046: no fabricated matron records in the UI."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
VIEW = ROOT / "src/views/erp/maternity-nurse-workbench/index.vue"
API = ROOT / "src/api/erp-maternity-nurse.js"
READ_SURFACES = ROOT / "server/erp_read_surfaces.py"


class MaternityNurseApiSurfaceTests(unittest.TestCase):
    def test_workbench_uses_the_existing_module_api(self):
        source = VIEW.read_text(encoding="utf-8")
        self.assertIn("getMaternityNurseModuleData", source)
        self.assertIn("saveMaternityNurseModuleRecord", source)
        self.assertIn("performMaternityNurseModuleAction", source)
        self.assertIn("async loadRows()", source)
        self.assertIn("当前模块数据暂未接入", source)

    def test_no_fabricated_matrons_or_demo_contract_numbers(self):
        source = VIEW.read_text(encoding="utf-8")
        for marker in (
            "示例护理师",
            "示例客户",
            "脱敏 Mock",
            "YS-DEMO-",
            "字段校验演示完成",
        ):
            self.assertNotIn(marker, source)

    def test_api_keeps_get_save_and_action_boundaries(self):
        source = API.read_text(encoding="utf-8")
        self.assertIn("/vue-element-admin/erp/maternity-nurse/modules/${resource}", source)
        self.assertIn("/save", source)
        self.assertIn("/action", source)

    def test_archive_schedule_and_settlement_resources_are_readable(self):
        source = READ_SURFACES.read_text(encoding="utf-8")
        for resource in (
            "maternity-matron-archives",
            "maternity-schedules",
            "maternity-settlements",
        ):
            self.assertIn(f'"{resource}"', source)


if __name__ == "__main__":
    unittest.main(verbosity=2)

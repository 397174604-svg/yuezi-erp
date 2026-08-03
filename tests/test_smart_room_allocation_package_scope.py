from __future__ import annotations

import importlib
import sys
import types
import unittest
from unittest.mock import patch


ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))

if "pymysql" not in sys.modules:
    pymysql = types.ModuleType("pymysql")
    pymysql.connect = lambda **_: None
    cursors = types.ModuleType("pymysql.cursors")
    cursors.DictCursor = object
    pymysql.cursors = cursors
    sys.modules["pymysql"] = pymysql
    sys.modules["pymysql.cursors"] = cursors

api = importlib.import_module("mvp_api")


class SmartRoomAllocationPackageScopeTest(unittest.TestCase):
    def test_yellow_river_alias_rows_are_merged_by_business_package(self):
        handler = object.__new__(api.MvpRequestHandler)
        user = {"tenant_id": 1, "store_ids": [1, 2], "data_scopes": ["ALL"]}
        rows = [
            {
                "basePackageCode": "YH-PLUS",
                "packageName": "黄河路臻享套餐",
                "store": "奇德芬芳·黄河路店",
                "days": 28,
                "referencePrice": 68800,
                "allowedRoomTypes": "大床房",
            },
            {
                "basePackageCode": "YH-PLUS",
                "packageName": "黄河路臻享套餐",
                "store": "黄河路轻奢店",
                "days": 28,
                "referencePrice": 68800,
                "allowedRoomTypes": "套房",
            },
        ]
        with patch.object(handler, "_store_clause", return_value=("1=1", [])), \
             patch.object(api, "execute_all", return_value=rows):
            result = handler._room_allocation_packages(
                object(), user, {"store": "黄河路轻奢店"}
            )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["packageNo"], "YH-PLUS@28")
        self.assertEqual(result[0]["allowedRoomTypes"], ["大床房", "套房"])


if __name__ == "__main__":
    unittest.main()

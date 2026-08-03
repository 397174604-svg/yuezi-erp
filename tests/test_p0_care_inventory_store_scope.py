from __future__ import annotations

import importlib
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
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


class StoreSelectionContractTest(unittest.TestCase):
    def setUp(self):
        self.handler = object.__new__(api.MvpRequestHandler)
        self.user = {
            "tenant_id": 1,
            "store_ids": [1, 2],
            "data_scopes": ["ALL"],
        }

    def test_all_store_cannot_create_business_document(self):
        for value in ("", "全部门店", "-全部-", "请选择"):
            with self.subTest(value=value), self.assertRaises(api.ApiError):
                self.handler._requested_store_id(
                    object(), self.user, {"store": value}, required=True
                )

    def test_explicit_store_id_is_accepted(self):
        self.assertEqual(
            self.handler._requested_store_id(
                object(), self.user, {"storeId": 2}, required=True
            ),
            2,
        )

    def test_store_name_is_resolved_then_authorized(self):
        with patch.object(api, "execute_one", return_value={"store_id": 1}):
            self.assertEqual(
                self.handler._requested_store_id(
                    object(), self.user,
                    {"store": "中心广场旗舰店"}, required=True
                ),
                1,
            )

    def test_unauthorized_store_is_rejected(self):
        scoped_user = {**self.user, "store_ids": [1], "data_scopes": []}
        with self.assertRaises(api.ApiError):
            self.handler._requested_store_id(
                object(), scoped_user, {"storeId": 2}, required=True
            )


if __name__ == "__main__":
    unittest.main()

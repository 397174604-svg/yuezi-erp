#!/usr/bin/env python3
"""Focused F059 store-scope acceptance tests without a live database."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "server"))

from mvp_api import ApiError, MvpRequestHandler  # noqa: E402


class MemberAssetStoreScopeTests(unittest.TestCase):
    def setUp(self):
        self.handler = object.__new__(MvpRequestHandler)
        self.user = {"tenant_id": 1, "store_ids": [1, 2]}

    def test_all_store_cannot_create_transaction(self):
        for value in (None, "", "all", 0, "0"):
            with self.subTest(value=value), self.assertRaises(ApiError):
                self.handler._asset_store_id(None, self.user, {"storeId": value})

    def test_store_must_be_in_user_scope(self):
        with self.assertRaises(ApiError) as raised:
            self.handler._asset_store_id(None, self.user, {"storeId": 3})
        self.assertEqual(raised.exception.status, 403)

    @patch("mvp_api.execute_one", return_value={"store_id": 2})
    def test_concrete_authorized_store_is_accepted(self, execute_one):
        store_id = self.handler._asset_store_id(
            object(), self.user, {"storeId": "2"}
        )
        self.assertEqual(store_id, 2)
        execute_one.assert_called_once()

    def test_external_integrations_are_traceable_not_configured(self):
        self.handler._require_any_permission = lambda *_args: None
        for resource in ("/payments/1/test", "/messages/1/send"):
            with self.subTest(resource=resource), self.assertRaises(ApiError) as raised:
                self.handler._post_asset_resource(
                    None, self.user, resource, {}
                )
            self.assertEqual(raised.exception.status, 503)
            self.assertEqual(raised.exception.code, 50300)
            self.assertIn("尚未配置", raised.exception.message)


if __name__ == "__main__":
    unittest.main(verbosity=2)

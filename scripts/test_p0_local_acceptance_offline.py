#!/usr/bin/env python3
"""Offline safety and matrix tests for p0_local_acceptance.py."""

from __future__ import annotations

import importlib.util
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).with_name("p0_local_acceptance.py")
SPEC = importlib.util.spec_from_file_location("p0_local_acceptance", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class P0LocalAcceptanceOfflineTest(unittest.TestCase):
    def test_loopback_hosts_are_allowed(self):
        for host in ("127.0.0.1", "::1", "localhost", "LOCALHOST"):
            self.assertTrue(MODULE.is_loopback_host(host))

    def test_remote_hosts_are_rejected(self):
        for host in ("10.0.0.8", "db.example.com", "0.0.0.0", ""):
            self.assertFalse(MODULE.is_loopback_host(host))
        with self.assertRaises(MODULE.AcceptanceError):
            MODULE.assert_local_targets(
                "10.0.0.8", "http://127.0.0.1:3000"
            )
        with self.assertRaises(MODULE.AcceptanceError):
            MODULE.assert_local_targets(
                "127.0.0.1", "https://erp.example.com"
            )

    def test_production_and_staging_runtime_are_rejected(self):
        for runtime in ("production", "prod", "staging", "stage"):
            with self.subTest(runtime=runtime), patch.dict(
                os.environ, {"ERP_RUNTIME_ENV": runtime}, clear=False
            ):
                with self.assertRaises(MODULE.AcceptanceError):
                    MODULE.assert_local_targets(
                        "127.0.0.1", "http://127.0.0.1:3000"
                    )

    def test_mutation_requires_exact_confirmation(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(MODULE.AcceptanceError):
                MODULE.require_mutation_confirmation()
        with patch.dict(
            os.environ,
            {MODULE.CONFIRM_ENV: MODULE.CONFIRM_VALUE},
            clear=True,
        ):
            MODULE.require_mutation_confirmation()

    def test_every_fixture_uses_test_prefix(self):
        usernames = [item.username for item in MODULE.PERSONAS]
        self.assertEqual(len(usernames), len(set(usernames)))
        self.assertTrue(
            all(name.startswith(MODULE.USERNAME_PREFIX) for name in usernames)
        )

    def test_required_personas_cover_both_stores(self):
        keys = {item.key for item in MODULE.PERSONAS}
        for store in ("center", "huanghe"):
            for role in ("manager", "sales", "finance", "nursing"):
                self.assertIn(f"{store}_{role}", keys)
        self.assertIn("admin", keys)
        by_key = {item.key: item for item in MODULE.PERSONAS}
        self.assertEqual(by_key["center_manager"].role_code, "STORE_MANAGER")
        self.assertEqual(by_key["huanghe_manager"].role_code, "STORE_MANAGER")

    def test_write_separation_matrix(self):
        by_key = {item.key: item for item in MODULE.PERSONAS}
        for store in ("center", "huanghe"):
            sales = by_key[f"{store}_sales"]
            finance = by_key[f"{store}_finance"]
            nursing = by_key[f"{store}_nursing"]
            manager = by_key[f"{store}_manager"]
            self.assertIn("SALES.CREATE", sales.allow)
            self.assertIn("SALES.APPROVE", sales.deny)
            self.assertIn("FINANCE.APPROVE", finance.allow)
            self.assertIn("FINANCE.APPROVE", manager.deny)
            self.assertIn("ROOM.EXECUTE", manager.allow)
            self.assertIn("ROOM.EXECUTE", nursing.deny)

    def test_password_hash_is_compatible_shape(self):
        encoded = MODULE.hash_password("local-test-password")
        algorithm, iterations, salt, digest = encoded.split("$")
        self.assertEqual(algorithm, "pbkdf2_sha256")
        self.assertEqual(iterations, "180000")
        self.assertTrue(salt)
        self.assertTrue(digest)

    def test_preflight_reports_blockers_without_credentials(self):
        with patch.dict(
            os.environ,
            {
                "ERP_DB_HOST": "127.0.0.1",
                "ERP_DB_PORT": "9",
                "ERP_MVP_BASE_URL": "http://127.0.0.1:9",
            },
            clear=True,
        ), patch.object(MODULE, "BASE_URL", "http://127.0.0.1:9"):
            result = MODULE.preflight()
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(result["localOnly"])
        self.assertGreaterEqual(len(result["blockers"]), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)

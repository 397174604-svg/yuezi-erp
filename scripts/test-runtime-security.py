#!/usr/bin/env python3
"""Offline regression tests for deployment and store-isolation helpers."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "server"))

from runtime_security import (  # noqa: E402
    RuntimeConfigError,
    allowed_store_id,
    discover_migrations,
    migration_state,
    store_scope_clause,
    validate_runtime_config,
)


class MigrationTests(unittest.TestCase):
    def test_repository_migrations_are_contiguous(self):
        migrations = discover_migrations(
            REPO_ROOT / "database" / "mysql" / "migrations"
        )
        self.assertEqual(migrations[0].sequence, 4)
        self.assertEqual(
            [item.sequence for item in migrations],
            list(range(4, migrations[-1].sequence + 1)),
        )

    def test_gap_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "V20260701_004__first.sql").write_text(
                "SELECT 1;", encoding="utf-8"
            )
            (root / "V20260701_006__third.sql").write_text(
                "SELECT 1;", encoding="utf-8"
            )
            with self.assertRaises(RuntimeConfigError):
                discover_migrations(root)

    def test_checksum_and_unknown_versions_fail_current_state(self):
        migrations = discover_migrations(
            REPO_ROOT / "database" / "mysql" / "migrations"
        )
        applied = {item.version: item.checksum for item in migrations}
        self.assertTrue(migration_state(migrations, applied)["current"])
        applied[migrations[0].version] = "0" * 64
        applied["V20990101_999"] = "1" * 64
        state = migration_state(migrations, applied)
        self.assertFalse(state["current"])
        self.assertEqual(state["checksumMismatches"], [migrations[0].version])
        self.assertEqual(state["unknownApplied"], ["V20990101_999"])

    def test_checksum_is_stable_across_windows_line_endings(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            lf_root = root / "lf"
            crlf_root = root / "crlf"
            lf_root.mkdir()
            crlf_root.mkdir()
            filename = "V20260701_004__first.sql"
            (lf_root / filename).write_bytes(b"SELECT 1;\nSELECT 2;\n")
            (crlf_root / filename).write_bytes(
                b"SELECT 1;\r\nSELECT 2;\r\n"
            )
            self.assertEqual(
                discover_migrations(lf_root)[0].checksum,
                discover_migrations(crlf_root)[0].checksum,
            )


class StoreIsolationTests(unittest.TestCase):
    def test_sys_admin_cannot_bypass_explicit_store_grants(self):
        user = {"roles": ["SYS_ADMIN"], "store_ids": [1, 2]}
        self.assertEqual(allowed_store_id(user, 2), 2)
        with self.assertRaises(RuntimeConfigError):
            allowed_store_id(user, 3)

    def test_store_scope_is_fail_closed(self):
        self.assertEqual(store_scope_clause({"store_ids": []}), ("1=0", []))
        self.assertEqual(
            store_scope_clause({"store_ids": [2, "2", 1]}, "c"),
            ("c.store_id IN (%s,%s)", [2, 1]),
        )


class ProductionConfigTests(unittest.TestCase):
    def valid_environment(self):
        return {
            "ERP_RUNTIME_ENV": "production",
            "ERP_DB_PASSWORD": "not-checked-into-source",
            "ERP_DB_USER": "yuezi_app",
            "ERP_DB_HOST": "127.0.0.1",
            "ERP_DB_NAME": "yuezi",
            "ERP_TOKEN_SECRET": "a" * 32,
            "ERP_CORS_ORIGINS": "https://erp.example.com",
        }

    def test_valid_production_environment(self):
        result = validate_runtime_config(self.valid_environment())
        self.assertEqual(result["environment"], "production")

    def test_root_database_user_is_rejected(self):
        environment = self.valid_environment()
        environment["ERP_DB_USER"] = "root"
        with self.assertRaises(RuntimeConfigError):
            validate_runtime_config(environment)

    def test_http_cors_origin_is_rejected(self):
        environment = self.valid_environment()
        environment["ERP_CORS_ORIGINS"] = "http://erp.example.com"
        with self.assertRaises(RuntimeConfigError):
            validate_runtime_config(environment)

    def test_remote_database_requires_ca(self):
        environment = self.valid_environment()
        environment["ERP_DB_HOST"] = "mysql.internal.example.com"
        with self.assertRaises(RuntimeConfigError):
            validate_runtime_config(environment)
        environment["ERP_DB_SSL_CA"] = "/run/secrets/mysql-ca.pem"
        self.assertTrue(validate_runtime_config(environment)["databaseTls"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

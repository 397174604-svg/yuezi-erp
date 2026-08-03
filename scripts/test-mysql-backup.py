#!/usr/bin/env python3
"""Offline tests for backup checksum and restore target guards."""

from __future__ import annotations

import gzip
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("mysql-backup.py")
SPEC = importlib.util.spec_from_file_location("mysql_backup", SCRIPT)
assert SPEC and SPEC.loader
mysql_backup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mysql_backup)


class BackupVerificationTests(unittest.TestCase):
    def make_backup(self, root: Path) -> Path:
        backup = root / "yuezi-test.sql.gz"
        with gzip.open(backup, "wt", encoding="utf-8") as destination:
            destination.write("CREATE TABLE `example` (`id` BIGINT);\n")
        manifest = {
            "format": "qdf-erp-mysql-logical-backup-v1",
            "database": "yuezi",
            "sha256": mysql_backup.sha256_file(backup),
        }
        mysql_backup.manifest_path(backup).write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        return backup

    def test_valid_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            backup = self.make_backup(Path(directory))
            result = mysql_backup.verify_backup(backup)
            self.assertEqual(result["status"], "verified")

    def test_modified_backup_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            backup = self.make_backup(Path(directory))
            with backup.open("ab") as destination:
                destination.write(b"changed")
            with self.assertRaises(SystemExit):
                mysql_backup.verify_backup(backup)

    def test_live_database_name_requires_extra_guard(self):
        self.assertIsNone(mysql_backup.SCRATCH_DATABASE_PATTERN.fullmatch("yuezi"))
        self.assertIsNotNone(
            mysql_backup.SCRATCH_DATABASE_PATTERN.fullmatch(
                "yuezi_restore_20260731"
            )
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

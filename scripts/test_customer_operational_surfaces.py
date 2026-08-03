#!/usr/bin/env python3
"""Static guards for customer and customer-service acceptance surfaces."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CustomerOperationalSurfaceTests(unittest.TestCase):
    def setUp(self):
        self.records = (ROOT / "server/operational_records.py").read_text(encoding="utf-8")
        self.api = (ROOT / "server/mvp_api.py").read_text(encoding="utf-8")
        self.seed = (ROOT / "scripts/seed_customer_service_acceptance_records.py").read_text(encoding="utf-8")
        self.seed_base = (ROOT / "scripts/seed_local_acceptance_dataset.py").read_text(encoding="utf-8")

    def test_customer_resources_are_registered(self):
        for resource in (
            "clues", "follow-records", "appointments", "public-customers",
            "visits", "satisfaction", "callbacks", "complaints",
            "message-templates", "messages", "point-records", "activities",
        ):
            self.assertIn(f'"{resource}"', self.records)
        self.assertIn('"CUSTOMER": "CUS"', self.records)

    def test_customer_reads_and_writes_use_operational_records(self):
        self.assertIn('connection, user, "CUSTOMER", resource, query', self.api)
        self.assertIn('"CUSTOMER",\n                            module,', self.api)

    def test_acceptance_seed_is_natural_name_and_idempotent(self):
        self.assertIn('"李女士"', self.seed_base)
        self.assertIn('"王女士"', self.seed_base)
        self.assertIn('"张女士"', self.seed_base)
        self.assertIn('"acceptanceKey"', self.seed)
        self.assertIn('"CUSTOMER"', self.seed)
        self.assertIn('"SERVICE"', self.seed)


if __name__ == "__main__":
    unittest.main(verbosity=2)

import unittest
from datetime import datetime

from server.operational_records import (
    apply_action,
    business_no,
    clean_payload,
    parse_record_id,
    validate_resource,
)


class OperationalRecordRulesTest(unittest.TestCase):
    def test_resource_allowlist_rejects_cross_module_resource(self):
        validate_resource("NURSING", "health-assessments")
        with self.assertRaises(ValueError):
            validate_resource("NURSING", "stocktakes")

    def test_payload_cannot_override_scope_or_audit_columns(self):
        cleaned = clean_payload(
            {
                "tenant_id": 9,
                "storeId": 21,
                "version": 99,
                "recordId": "OP-10",
                "action": "审核",
                "customerName": "张女士",
            }
        )
        self.assertEqual(cleaned, {"customerName": "张女士"})

    def test_only_prefixed_record_ids_are_parsed_for_ui_records(self):
        self.assertEqual(parse_record_id("OP-42"), 42)
        self.assertEqual(parse_record_id(42), 42)
        self.assertIsNone(parse_record_id("legacy-42"))

    def test_workflow_action_has_deterministic_state_and_audit_time(self):
        patch, status = apply_action(
            "meal-orders",
            "开始配送",
            {"operator": "配送员A"},
            now=datetime(2026, 7, 31, 16, 30, 0),
        )
        self.assertEqual(status, "配送中")
        self.assertEqual(patch["orderStatus"], "配送中")
        self.assertEqual(patch["lastActionAt"], "2026-07-31T16:30:00")

    def test_purchase_arrival_action_is_completed(self):
        patch, status = apply_action(
            "purchase-orders",
            "到货登记",
            {},
            now=datetime(2026, 7, 31, 17, 0, 0),
        )
        self.assertEqual(status, "已完成")
        self.assertEqual(patch["arrivalStatus"], "已到货")

    def test_rejected_audit_does_not_report_approved(self):
        patch, status = apply_action(
            "purchase-orders",
            "审核",
            {"auditResult": "审核不通过"},
        )
        self.assertEqual(status, "审核不通过")
        self.assertEqual(patch["auditStatus"], "审核不通过")

    def test_generated_business_number_is_stable(self):
        self.assertEqual(
            business_no("INVENTORY", "stock-transfers", 7),
            "INV-STTR-00000007",
        )


if __name__ == "__main__":
    unittest.main()

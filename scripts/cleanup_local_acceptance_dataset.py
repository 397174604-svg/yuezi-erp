#!/usr/bin/env python3
"""Remove only records created by seed_local_acceptance_dataset.py."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".deps"))
import pymysql


BATCH = "LOCAL_ACCEPTANCE_SEED_20260801"


def main():
    if os.environ.get("ERP_LOCAL_DEMO_CONFIRM") != "LOCAL_TEST_ONLY":
        raise SystemExit("Set ERP_LOCAL_DEMO_CONFIRM=LOCAL_TEST_ONLY before cleanup.")
    if os.environ.get("ERP_DB_HOST", "127.0.0.1") not in {"127.0.0.1", "localhost", "::1"}:
        raise SystemExit("Acceptance cleanup is restricted to a loopback database.")
    db = pymysql.connect(
        host=os.environ.get("ERP_DB_HOST", "127.0.0.1"),
        port=int(os.environ.get("ERP_DB_PORT", "3306")),
        user=os.environ["ERP_DB_USER"], password=os.environ["ERP_DB_PASSWORD"],
        database=os.environ.get("ERP_DB_NAME", "yuezi"), charset="utf8mb4", autocommit=False,
    )
    counts = {}
    try:
        with db.cursor() as cursor:
            counts["operationalRows"] = cursor.execute(
                "DELETE FROM erp_operational_records WHERE payload_json LIKE %s",
                (f'%"demoBatch": "{BATCH}"%',),
            )
            # These two local test employees are referenced by historical
            # customer-entry rows.  Retire them instead of breaking that
            # history; inactive employees are excluded from all new selects.
            counts["legacyTestStaffRetired"] = cursor.execute(
                "UPDATE staff SET employment_status='INACTIVE', status='INACTIVE', review_status='ARCHIVED', updated_at=NOW() WHERE source_file='LOCAL_TEST_SEED' AND employee_no IN ('TEST-SALES-CENTER','TEST-SALES-HUANGHE') AND NOT EXISTS (SELECT 1 FROM user_accounts ua WHERE ua.staff_id=staff.staff_id)"
            )
            cursor.execute("SELECT customer_id FROM customers WHERE remark LIKE %s", (BATCH + "%",))
            customer_ids = [int(row[0]) for row in cursor.fetchall()]
            if not customer_ids:
                db.commit()
                print(json.dumps({"status": "cleaned", "batch": BATCH, **counts}, ensure_ascii=False))
                return
            marks = ",".join(["%s"] * len(customer_ids))
            cursor.execute(f"SELECT booking_id,room_id FROM room_bookings WHERE customer_id IN ({marks})", customer_ids)
            bookings = [(int(row[0]), int(row[1])) for row in cursor.fetchall()]
            cursor.execute(f"SELECT contract_id FROM contracts WHERE customer_id IN ({marks}) AND note=%s", (*customer_ids, BATCH))
            contract_ids = [int(row[0]) for row in cursor.fetchall()]
            cursor.execute(f"SELECT receipt_id FROM finance_receipts WHERE customer_id IN ({marks}) AND remark=%s", (*customer_ids, BATCH))
            receipt_ids = [int(row[0]) for row in cursor.fetchall()]
            cursor.execute(f"SELECT baby_id FROM babies WHERE customer_id IN ({marks}) AND note LIKE %s", (*customer_ids, BATCH + "%"))
            baby_ids = [int(row[0]) for row in cursor.fetchall()]

            if baby_ids:
                baby_marks = ",".join(["%s"] * len(baby_ids))
                counts["babyLogs"] = cursor.execute(f"DELETE FROM baby_logs WHERE baby_id IN ({baby_marks}) AND note LIKE %s", (*baby_ids, BATCH + "%"))
                counts["babies"] = cursor.execute(f"DELETE FROM babies WHERE baby_id IN ({baby_marks})", baby_ids)
            all_aggregate_ids = customer_ids + contract_ids + receipt_ids + [row[0] for row in bookings]
            if all_aggregate_ids:
                agg_marks = ",".join(["%s"] * len(all_aggregate_ids))
                cursor.execute(f"DELETE FROM mvp_audit_events WHERE aggregate_id IN ({agg_marks})", all_aggregate_ids)
            if bookings:
                booking_ids = [row[0] for row in bookings]
                room_ids = [row[1] for row in bookings]
                bmarks = ",".join(["%s"] * len(booking_ids))
                counts["bookings"] = cursor.execute(f"DELETE FROM room_bookings WHERE booking_id IN ({bmarks})", booking_ids)
                rmarks = ",".join(["%s"] * len(room_ids))
                cursor.execute(f"UPDATE rooms SET status='空闲', customer_id=NULL WHERE room_id IN ({rmarks})", room_ids)
            if receipt_ids:
                rmarks = ",".join(["%s"] * len(receipt_ids))
                counts["receipts"] = cursor.execute(f"DELETE FROM finance_receipts WHERE receipt_id IN ({rmarks})", receipt_ids)
            # Acceptance customers also received one recovery appointment in the
            # local demo flow.  Delete it by the already batch-scoped customer
            # ids before deleting the customer rows; do not touch appointments
            # belonging to any other customer.
            counts["recoveryAppointments"] = cursor.execute(
                f"DELETE FROM recovery_appointments WHERE customer_id IN ({marks})",
                customer_ids,
            )
            if contract_ids:
                cmarks = ",".join(["%s"] * len(contract_ids))
                # These extension tables are optional and contain only rows created from the selected contracts.
                for table in ["customer_service_entitlements", "contract_entitlement_snapshots", "contract_package_snapshots", "sales_contract_extensions", "contract_sign_archives"]:
                    cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name=%s", (table,))
                    if cursor.fetchone()[0]:
                        cursor.execute(f"DELETE FROM `{table}` WHERE contract_id IN ({cmarks})", contract_ids)
                counts["contracts"] = cursor.execute(f"DELETE FROM contracts WHERE contract_id IN ({cmarks})", contract_ids)
            counts["customers"] = cursor.execute(f"DELETE FROM customers WHERE customer_id IN ({marks})", customer_ids)
            counts["matrons"] = cursor.execute("DELETE FROM staff WHERE source_file=%s AND NOT EXISTS (SELECT 1 FROM user_accounts ua WHERE ua.staff_id=staff.staff_id)", (BATCH,))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    print(json.dumps({"status": "cleaned", "batch": BATCH, **counts}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

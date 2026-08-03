#!/usr/bin/env python3
"""Hide one verified numeric placeholder from customer-facing ERP domains.

The target is deliberately fixed to the legacy local placeholder chain created
on 2026-07-31.  The script refuses to continue if any identifying value no
longer matches.  By default it never touches rooms; with ``--include-booking``
it may release only the single room bound to the exact placeholder booking
after the safety checks pass.  It never touches package masters, role
permissions, or records belonging to natural-name customers.

Dry run (default):
    python scripts/cleanup_known_placeholder_customer_222.py

Apply, on a loopback database only:
    set ERP_LOCAL_DEMO_CONFIRM=LOCAL_TEST_ONLY
    python scripts/cleanup_known_placeholder_customer_222.py --apply
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".deps"))
import pymysql
from pymysql.cursors import DictCursor


CONFIRM_ENV = "ERP_LOCAL_DEMO_CONFIRM"
CONFIRM_VALUE = "LOCAL_TEST_ONLY"
TARGET = {
    "customer": {
        "customer_id": 28,
        "name": "222",
        "phone": "18919715615",
    },
    "contract": {
        "contract_id": 9,
        "contract_no": "HT-20260731-00009",
        "customer_id": 28,
    },
    "receipt": {
        "receipt_id": 4,
        "receipt_no": "SK-20260731-00004",
        "customer_id": 28,
        "contract_id": 9,
    },
    "account": {
        "account_id": 1,
        "account_no": "ACC-1-28",
        "customer_id": 28,
    },
    "booking": {
        "booking_id": 4,
        "booking_no": "DF-20260731-00004",
        "customer_id": 28,
        "contract_id": 9,
        "room_id": 3,
        "store_id": 2,
        "status": "已订房",
    },
}


def require_local_database(apply: bool) -> None:
    host = os.environ.get("ERP_DB_HOST", "127.0.0.1")
    if urlparse(f"mysql://{host}").hostname not in {
        "127.0.0.1",
        "localhost",
        "::1",
    }:
        raise SystemExit("Cleanup is restricted to a loopback database.")
    if apply and os.environ.get(CONFIRM_ENV) != CONFIRM_VALUE:
        raise SystemExit(f"Set {CONFIRM_ENV}={CONFIRM_VALUE} before --apply.")


def connect():
    return pymysql.connect(
        host=os.environ.get("ERP_DB_HOST", "127.0.0.1"),
        port=int(os.environ.get("ERP_DB_PORT", "3306")),
        user=os.environ["ERP_DB_USER"],
        password=os.environ["ERP_DB_PASSWORD"],
        database=os.environ.get("ERP_DB_NAME", "yuezi"),
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=False,
    )


def verify_exact(cursor, table: str, key: str, expected: dict) -> dict:
    cursor.execute(
        f"SELECT * FROM {table} WHERE {key}=%s FOR UPDATE",
        (expected[key],),
    )
    row = cursor.fetchone()
    if not row:
        raise RuntimeError(f"Expected {table}.{key}={expected[key]} was not found.")
    mismatches = {
        field: {"expected": value, "actual": row.get(field)}
        for field, value in expected.items()
        if row.get(field) != value
    }
    if mismatches:
        raise RuntimeError(
            f"Refusing cleanup because {table} no longer matches: "
            + json.dumps(mismatches, ensure_ascii=False, default=str)
        )
    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--include-booking",
        action="store_true",
        help="Also cancel the one exact placeholder booking and safely release its room.",
    )
    args = parser.parse_args()
    require_local_database(args.apply)

    database = connect()
    result = {"mode": "apply" if args.apply else "dry-run", "target": TARGET}
    try:
        with database.cursor() as cursor:
            verify_exact(cursor, "customers", "customer_id", TARGET["customer"])
            verify_exact(cursor, "contracts", "contract_id", TARGET["contract"])
            verify_exact(cursor, "finance_receipts", "receipt_id", TARGET["receipt"])
            verify_exact(cursor, "member_asset_accounts", "account_id", TARGET["account"])
            booking = verify_exact(
                cursor, "room_bookings", "booking_id", TARGET["booking"]
            )
            cursor.execute(
                """
                SELECT room_id, room_no, store_id, customer_id, status, deleted_at
                FROM rooms WHERE room_id=%s FOR UPDATE
                """,
                (booking["room_id"],),
            )
            room = cursor.fetchone()
            if not room:
                raise RuntimeError("The exact placeholder booking room no longer exists.")
            cursor.execute(
                """
                SELECT booking_id, booking_no, customer_id, status, check_in, check_out
                FROM room_bookings
                WHERE room_id=%s AND booking_id<>%s AND deleted_at IS NULL
                  AND status NOT IN ('已取消', '已退房', '已删除')
                ORDER BY booking_id
                """,
                (booking["room_id"], booking["booking_id"]),
            )
            other_active_bookings = cursor.fetchall()
            result["bookingReview"] = {
                "exactBooking": booking,
                "room": room,
                "otherActiveBookings": other_active_bookings,
                "requestedCleanup": args.include_booking,
            }

            changes = {}
            changes["booking"] = 0
            changes["roomReleased"] = 0
            if args.include_booking:
                if other_active_bookings:
                    raise RuntimeError(
                        "Refusing booking cleanup because the room has other active bookings."
                    )
                if room.get("customer_id") not in (None, TARGET["customer"]["customer_id"]):
                    raise RuntimeError(
                        "Refusing booking cleanup because the room belongs to another customer."
                    )
                changes["booking"] = cursor.execute(
                    """
                    UPDATE room_bookings
                    SET status='已取消', deleted_at=NOW(), version=version+1
                    WHERE booking_id=%s AND booking_no=%s AND customer_id=%s
                      AND contract_id=%s AND room_id=%s AND store_id=%s
                      AND status='已订房' AND deleted_at IS NULL
                    """,
                    (
                        TARGET["booking"]["booking_id"],
                        TARGET["booking"]["booking_no"],
                        TARGET["booking"]["customer_id"],
                        TARGET["booking"]["contract_id"],
                        TARGET["booking"]["room_id"],
                        TARGET["booking"]["store_id"],
                    ),
                )
                if changes["booking"] != 1:
                    raise RuntimeError("Exact booking cleanup did not affect one row.")
                changes["roomReleased"] = cursor.execute(
                    """
                    UPDATE rooms SET customer_id=NULL, status='空闲'
                    WHERE room_id=%s AND store_id=%s AND deleted_at IS NULL
                      AND (customer_id IS NULL OR customer_id=%s)
                    """,
                    (
                        TARGET["booking"]["room_id"],
                        TARGET["booking"]["store_id"],
                        TARGET["customer"]["customer_id"],
                    ),
                )
            changes["receipts"] = cursor.execute(
                """
                UPDATE finance_receipts SET status='已删除', version=version+1
                WHERE receipt_id=%s AND receipt_no=%s AND customer_id=%s
                  AND contract_id=%s AND status<>'已删除'
                """,
                (
                    TARGET["receipt"]["receipt_id"],
                    TARGET["receipt"]["receipt_no"],
                    TARGET["receipt"]["customer_id"],
                    TARGET["receipt"]["contract_id"],
                ),
            )
            changes["contracts"] = cursor.execute(
                """
                UPDATE contracts SET deleted_at=NOW(), status='已删除', version=version+1
                WHERE contract_id=%s AND contract_no=%s AND customer_id=%s
                  AND deleted_at IS NULL
                """,
                (
                    TARGET["contract"]["contract_id"],
                    TARGET["contract"]["contract_no"],
                    TARGET["contract"]["customer_id"],
                ),
            )
            changes["memberAccounts"] = cursor.execute(
                """
                UPDATE member_asset_accounts SET status='已注销'
                WHERE account_id=%s AND account_no=%s AND customer_id=%s
                  AND status<>'已注销'
                """,
                (
                    TARGET["account"]["account_id"],
                    TARGET["account"]["account_no"],
                    TARGET["account"]["customer_id"],
                ),
            )
            changes["customers"] = cursor.execute(
                """
                UPDATE customers SET deleted_at=NOW(), status='已关闭'
                WHERE customer_id=%s AND name=%s AND phone=%s
                  AND deleted_at IS NULL
                """,
                (
                    TARGET["customer"]["customer_id"],
                    TARGET["customer"]["name"],
                    TARGET["customer"]["phone"],
                ),
            )
            result["changes"] = changes

        if args.apply:
            database.commit()
        else:
            database.rollback()
    except Exception:
        database.rollback()
        raise
    finally:
        database.close()

    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()

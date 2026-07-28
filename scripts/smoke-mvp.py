#!/usr/bin/env python3
"""Create, verify and remove one desensitized MVP business loop."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import date, timedelta
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEPS = ROOT / ".deps"
if DEPS.exists():
    sys.path.insert(0, str(DEPS))

import pymysql


BASE_URL = os.environ.get("ERP_MVP_BASE_URL", "http://127.0.0.1:3000")
USERNAME = os.environ.get("ERP_BOOTSTRAP_ADMIN_USERNAME", "admin")
PASSWORD = os.environ.get("ERP_BOOTSTRAP_ADMIN_PASSWORD", "")


def api(path: str, method: str = "GET", body=None, token: str = ""):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Token"] = token
    request = Request(
        BASE_URL + path,
        data=json.dumps(body).encode("utf-8") if body is not None else None,
        headers=headers,
        method=method,
    )
    with urlopen(request, timeout=10) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if payload["code"] != 20000:
        raise RuntimeError(payload.get("message", "API request failed"))
    return payload["data"]


def db_connection():
    return pymysql.connect(
        host=os.environ.get("ERP_DB_HOST", "127.0.0.1"),
        port=int(os.environ.get("ERP_DB_PORT", "3306")),
        user=os.environ.get("ERP_DB_USER", "root"),
        password=os.environ["ERP_DB_PASSWORD"],
        database=os.environ.get("ERP_DB_NAME", "yuezi"),
        charset="utf8mb4",
        autocommit=False,
    )


def main():
    if not PASSWORD:
        raise SystemExit("ERP_BOOTSTRAP_ADMIN_PASSWORD is required.")
    token = api(
        "/vue-element-admin/user/login",
        "POST",
        {"username": USERNAME, "password": PASSWORD},
    )["token"]
    options = api("/vue-element-admin/erp/mvp/options", token=token)
    stores = options["stores"]
    rooms = api("/vue-element-admin/erp/mvp/rooms", token=token)["list"]
    if not stores or not rooms:
        raise RuntimeError("A store and room are required for the smoke test.")
    store_id = stores[0]["id"]
    room = next(item for item in rooms if item["store_id"] == store_id)
    suffix = str(int(time.time()))[-8:]
    created = {}
    original_room_status = room["status"]
    try:
        customer = api(
            "/vue-element-admin/erp/mvp/customers",
            "POST",
            {
                "storeId": store_id,
                "name": "MVP验收客户",
                "phone": "139" + suffix,
                "status": "意向A",
                "source": "系统验收",
            },
            token,
        )
        created["customer"] = customer["id"]
        start = date.today() + timedelta(days=1)
        end = start + timedelta(days=28)
        contract = api(
            "/vue-element-admin/erp/mvp/contracts",
            "POST",
            {
                "storeId": store_id,
                "customerId": customer["id"],
                "contractType": "月子合同",
                "packageName": "MVP验收套餐",
                "referenceAmount": 100,
                "amount": 90,
                "days": 28,
                "expectedCheckIn": start.isoformat(),
                "expectedCheckOut": end.isoformat(),
                "signDate": date.today().isoformat(),
            },
            token,
        )
        created["contract"] = contract["id"]
        api(
            f"/vue-element-admin/erp/mvp/contracts/{contract['id']}/approve",
            "POST",
            {},
            token,
        )
        receipt = api(
            "/vue-element-admin/erp/mvp/receipts",
            "POST",
            {
                "storeId": store_id,
                "contractId": contract["id"],
                "receiptType": "合同首付",
                "amount": 30,
                "paymentMethod": "转账",
            },
            token,
        )
        created["receipt"] = receipt["id"]
        api(
            f"/vue-element-admin/erp/mvp/receipts/{receipt['id']}/approve",
            "POST",
            {},
            token,
        )
        booking = api(
            "/vue-element-admin/erp/mvp/bookings",
            "POST",
            {
                "storeId": store_id,
                "contractId": contract["id"],
                "roomId": room["id"],
                "checkIn": start.isoformat(),
                "checkOut": end.isoformat(),
            },
            token,
        )
        created["booking"] = booking["id"]
        api(
            f"/vue-element-admin/erp/mvp/bookings/{booking['id']}/check-in",
            "POST",
            {},
            token,
        )
        bookings = api(
            "/vue-element-admin/erp/mvp/bookings", token=token
        )["list"]
        result = next(item for item in bookings if item["id"] == booking["id"])
        if result["status"] != "已入住":
            raise RuntimeError("The booking did not reach 已入住.")
        print(
            json.dumps(
                {
                    "status": "passed",
                    "customerNo": customer["customerNo"],
                    "contractNo": contract["contractNo"],
                    "receiptNo": receipt["receiptNo"],
                    "bookingNo": booking["bookingNo"],
                    "finalBookingStatus": result["status"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    finally:
        connection = db_connection()
        try:
            with connection.cursor() as cursor:
                if created:
                    cursor.execute(
                        """
                        DELETE FROM mvp_audit_events
                        WHERE (aggregate_type='CUSTOMER' AND aggregate_id=%s)
                           OR (aggregate_type='CONTRACT' AND aggregate_id=%s)
                           OR (aggregate_type='RECEIPT' AND aggregate_id=%s)
                           OR (aggregate_type='BOOKING' AND aggregate_id=%s)
                        """,
                        (
                            created.get("customer", 0),
                            created.get("contract", 0),
                            created.get("receipt", 0),
                            created.get("booking", 0),
                        ),
                    )
                if created.get("booking"):
                    cursor.execute(
                        "DELETE FROM room_bookings WHERE booking_id=%s",
                        (created["booking"],),
                    )
                    cursor.execute(
                        """
                        UPDATE rooms SET status=%s, customer_id=NULL
                        WHERE room_id=%s
                        """,
                        (original_room_status, room["id"]),
                    )
                if created.get("receipt"):
                    cursor.execute(
                        "DELETE FROM finance_receipts WHERE receipt_id=%s",
                        (created["receipt"],),
                    )
                if created.get("contract"):
                    cursor.execute(
                        "DELETE FROM contracts WHERE contract_id=%s",
                        (created["contract"],),
                    )
                if created.get("customer"):
                    cursor.execute(
                        "DELETE FROM customers WHERE customer_id=%s",
                        (created["customer"],),
                    )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()


if __name__ == "__main__":
    main()

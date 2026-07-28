#!/usr/bin/env python3
"""End-to-end regression for the real module APIs.

The test creates desensitized records, runs the role-separated workflow
customer entry -> sales contract -> receipt -> smart allocation -> check-in,
asserts MySQL state, and removes every record it created.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import date, timedelta
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".deps"))

import pymysql
from pymysql.cursors import DictCursor


BASE_URL = os.environ.get("ERP_MVP_BASE_URL", "http://127.0.0.1:3000")


def api(path: str, token: str = "", body=None, query=None):
    if query:
        path = f"{path}?{urlencode(query)}"
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        headers["X-Token"] = token
    request = Request(
        BASE_URL + path,
        data=(
            json.dumps(body, ensure_ascii=False).encode("utf-8")
            if body is not None
            else None
        ),
        headers=headers,
        method="POST" if body is not None else "GET",
    )
    try:
        with urlopen(request, timeout=15) as response:
            status = response.status
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        status = exc.code
        payload = json.loads(exc.read().decode("utf-8"))
    return status, payload


def require_ok(path: str, token: str = "", body=None, query=None):
    status, payload = api(path, token, body, query)
    if status != 200 or payload.get("code") != 20000:
        raise AssertionError(
            f"{path} failed: HTTP {status} {payload.get('message')}"
        )
    return payload["data"]


def login(username: str, password: str) -> str:
    return require_ok(
        "/vue-element-admin/user/login",
        body={"username": username, "password": password},
    )["token"]


def connect():
    return pymysql.connect(
        host=os.environ.get("ERP_DB_HOST", "127.0.0.1"),
        port=int(os.environ.get("ERP_DB_PORT", "3306")),
        user=os.environ.get("ERP_DB_USER", "root"),
        password=os.environ["ERP_DB_PASSWORD"],
        database=os.environ.get("ERP_DB_NAME", "yuezi"),
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=False,
    )


def main():
    required = {
        "ERP_ROOM_ACCOUNT_PASSWORD": "董丽霞",
        "ERP_SALES_ACCOUNT_PASSWORD": "韩新",
        "ERP_BOOTSTRAP_ADMIN_PASSWORD": "admin",
        "ERP_DB_PASSWORD": "MySQL",
    }
    missing = [key for key in required if not os.environ.get(key)]
    if missing:
        raise SystemExit("Missing environment variables: " + ", ".join(missing))

    room_token = login("董丽霞", os.environ["ERP_ROOM_ACCOUNT_PASSWORD"])
    sales_token = login("韩新", os.environ["ERP_SALES_ACCOUNT_PASSWORD"])
    admin_token = login("admin", os.environ["ERP_BOOTSTRAP_ADMIN_PASSWORD"])
    room_info = require_ok("/vue-element-admin/user/info", room_token)
    if "HOUSEKEEPER" not in room_info["roles"]:
        raise AssertionError("董丽霞未映射为 HOUSEKEEPER")

    options = require_ok(
        "/vue-element-admin/erp/customer/entry-options", room_token
    )
    if len(options["stores"]) != 1:
        raise AssertionError(
            f"董丽霞应仅能录入一个门店，当前为 {options['stores']}"
        )
    store = options["stores"][0]
    store_name = store["name"]
    suffix = str(int(time.time()))[-8:]
    phone = "139" + suffix
    start = date.today() + timedelta(days=60)
    end = start + timedelta(days=28)
    created = {}
    original_room = None
    connection = None

    try:
        duplicate = require_ok(
            "/vue-element-admin/erp/customer/duplicate-check",
            room_token,
            {"name": "流程验收客户", "mobile": phone, "wechat": ""},
        )
        if duplicate["records"]:
            raise AssertionError("验收手机号在创建前已存在")

        draft = require_ok(
            "/vue-element-admin/erp/customer/draft",
            room_token,
            {
                "name": "流程验收客户",
                "mobile": phone,
                "wechat": "",
                "status": "意向A",
                "source": "系统验收",
                "intendedStore": store_name,
            },
        )
        created["draft"] = draft["draftId"]
        customer = require_ok(
            "/vue-element-admin/erp/customer",
            room_token,
            {
                "draftId": draft["draftId"],
                "name": "流程验收客户",
                "countryCode": "+86",
                "mobile": phone,
                "wechat": "",
                "status": "意向A",
                "source": "系统验收",
                "intendedStore": store_name,
                "intendedDays": 28,
                "plannedStayDate": start.isoformat(),
                "roomType": "修复套餐",
                "contractAmount": "98000",
                "packageName": "修复套餐",
                "packageAmount": "98000",
                "recoveryStore": store_name,
                "documentType": "中国大陆居民身份证",
                "documentNo": "410000199001010000",
                "sex": "女",
                "birthday": "1990-01-01",
                "age": 36,
                "fetusType": "单胎",
                "pregnancyCount": "一胎",
                "trackerName": "董丽霞",
                "trackerDepartment": "客房部",
                "entryTime": f"{date.today().isoformat()} 10:00:00",
                "address": "流程验收地址",
                "dietNote": "无",
                "customerNote": "端到端自动验收，完成后删除",
                "tags": ["重点关注"],
            },
        )
        created["customer"] = customer["id"]

        duplicate = require_ok(
            "/vue-element-admin/erp/customer/duplicate-check",
            room_token,
            {"name": "流程验收客户", "mobile": phone, "wechat": ""},
        )
        if not duplicate["records"]:
            raise AssertionError("客户创建后查重未命中")

        contract = require_ok(
            "/vue-element-admin/erp/sales/modules/contracts/save",
            sales_token,
            {
                "customerId": customer["id"],
                "store": store_name,
                "contractType": "月子护理",
                "packageName": "修复套餐",
                "referencePrice": "100000",
                "dealAmount": "98000",
                "contractDays": 28,
                "checkInAt": start.isoformat(),
                "checkOutAt": end.isoformat(),
                "signedAt": date.today().isoformat(),
                "roomType": "修复套餐",
                "submit": True,
            },
        )
        created["contract"] = contract["id"]
        require_ok(
            "/vue-element-admin/erp/sales/modules/contracts/action",
            sales_token,
            {"action": "审核", "id": contract["id"]},
        )

        receipt = require_ok(
            "/vue-element-admin/erp/finance/modules/receipt-create/save",
            admin_token,
            {
                "customerId": customer["id"],
                "contractId": contract["id"],
                "store": store_name,
                "receiptType": "合同首付",
                "receiptKind": "收款单",
                "amount": "30000",
                "paymentMethod": "转账",
                "documentDate": date.today().isoformat(),
                "remark": "端到端自动验收，完成后删除",
            },
        )
        created["receipt"] = receipt["id"]
        require_ok(
            "/vue-element-admin/erp/finance/modules/receipts/action",
            admin_token,
            {"action": "审核", "id": receipt["id"]},
        )

        smart = require_ok(
            "/vue-element-admin/erp/room/modules/smart-allocation",
            room_token,
            query={
                "store": store_name,
                "startDate": start.isoformat(),
                "endDate": end.isoformat(),
                "days": "28",
            },
        )
        candidate = next(
            (
                room
                for room in smart["list"]
                if room["status"] == "空闲"
                and not any(
                    not (
                        str(item.get("endAt", ""))[:10] <= start.isoformat()
                        or str(item.get("startAt", ""))[:10] >= end.isoformat()
                    )
                    for item in room.get("bookings", [])
                )
            ),
            None,
        )
        if not candidate:
            raise AssertionError("黄河路门店没有可用于验收的空闲房间")
        original_room = {
            "id": candidate["id"],
            "status": candidate["status"],
        }
        bookable = next(
            (
                item
                for item in smart["customers"]
                if int(item["id"]) == int(customer["id"])
            ),
            None,
        )
        if not bookable or int(bookable["contractId"]) != int(contract["id"]):
            raise AssertionError("审核合同未进入智能排房客户选择器")

        booking = require_ok(
            "/vue-element-admin/erp/room/modules/smart-allocation/save",
            room_token,
            {
                "_action": "订房",
                "customerId": customer["id"],
                "contractId": contract["id"],
                "store": store_name,
                "roomId": candidate["id"],
                "room": candidate["room"],
                "plannedCheckInAt": start.isoformat(),
                "plannedCheckOutAt": end.isoformat(),
                "remark": "端到端自动验收，完成后删除",
            },
        )
        created["booking"] = booking["id"]
        require_ok(
            "/vue-element-admin/erp/room/modules/room-map/action",
            room_token,
            {"action": "入住", "bookingId": booking["id"]},
        )

        stays = require_ok(
            "/vue-element-admin/erp/room/modules/room-stays", room_token
        )["list"]
        final_stay = next(
            (row for row in stays if int(row["id"]) == int(booking["id"])),
            None,
        )
        if not final_stay or final_stay["roomStatus"] != "入住":
            raise AssertionError("订房记录未完成入住状态流转")

        for resource in (
            "customer-meal-plans",
            "diet-packages",
            "diet-statistics",
        ):
            require_ok(
                f"/vue-element-admin/erp/diet/modules/{resource}", room_token
            )

        connection = connect()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT c.status,ct.status AS contract_status,ct.paid,
                       fr.status AS receipt_status,rb.status AS booking_status,
                       r.status AS room_status,cep.document_no
                FROM customers c
                JOIN customer_entry_profiles profile
                  ON profile.customer_id=c.customer_id
                JOIN contracts ct ON ct.customer_id=c.customer_id
                JOIN finance_receipts fr ON fr.contract_id=ct.contract_id
                JOIN room_bookings rb ON rb.contract_id=ct.contract_id
                JOIN rooms r ON r.room_id=rb.room_id
                LEFT JOIN (
                  SELECT customer_id,id_no AS document_no FROM customers
                ) cep ON cep.customer_id=c.customer_id
                WHERE c.customer_id=%s AND ct.contract_id=%s
                  AND fr.receipt_id=%s AND rb.booking_id=%s
                """,
                (
                    customer["id"],
                    contract["id"],
                    receipt["id"],
                    booking["id"],
                ),
            )
            state = cursor.fetchone()
        if not state:
            raise AssertionError("MySQL 未形成完整业务关联")
        if state["booking_status"] != "已入住" or state["room_status"] != "入住":
            raise AssertionError(f"MySQL 入住状态不正确: {state}")
        if float(state["paid"]) != 30000:
            raise AssertionError(f"合同已收款未正确回写: {state['paid']}")
        if state["document_no"] != "410000199001010000":
            raise AssertionError("客户证件号没有按录入值存入 MySQL")

        print(
            json.dumps(
                {
                    "status": "passed",
                    "roles": ["董丽霞/客房管家", "韩新/销售", "admin/财务"],
                    "store": store_name,
                    "customerCode": customer["customerCode"],
                    "contractId": contract["id"],
                    "receiptId": receipt["id"],
                    "bookingId": booking["id"],
                    "room": candidate["room"],
                    "finalStatus": state["booking_status"],
                    "mysqlPaid": str(state["paid"]),
                    "dietLoadEndpoints": 3,
                    "cleanup": "automatic",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    finally:
        if connection is None:
            connection = connect()
        try:
            with connection.cursor() as cursor:
                if created.get("booking"):
                    cursor.execute(
                        "DELETE FROM room_operation_records "
                        "WHERE booking_id=%s",
                        (created["booking"],),
                    )
                    cursor.execute(
                        "DELETE FROM mvp_audit_events "
                        "WHERE aggregate_id=%s AND aggregate_type IN "
                        "('ROOM_BOOKING','BOOKING','ROOM_OPERATION')",
                        (created["booking"],),
                    )
                    cursor.execute(
                        "DELETE FROM room_bookings WHERE booking_id=%s",
                        (created["booking"],),
                    )
                if original_room:
                    cursor.execute(
                        """
                        UPDATE rooms SET status=%s,customer_id=NULL
                        WHERE room_id=%s
                        """,
                        (original_room["status"], original_room["id"]),
                    )
                if created.get("receipt"):
                    cursor.execute(
                        "DELETE FROM finance_receipt_extensions "
                        "WHERE receipt_id=%s",
                        (created["receipt"],),
                    )
                    cursor.execute(
                        "DELETE FROM mvp_audit_events "
                        "WHERE aggregate_id=%s AND aggregate_type IN "
                        "('FINANCE_RECEIPT','RECEIPT')",
                        (created["receipt"],),
                    )
                    cursor.execute(
                        "DELETE FROM finance_receipts WHERE receipt_id=%s",
                        (created["receipt"],),
                    )
                if created.get("contract"):
                    cursor.execute(
                        "DELETE FROM sales_operation_records "
                        "WHERE resource_key='contracts' AND record_key=%s",
                        (str(created["contract"]),),
                    )
                    cursor.execute(
                        "DELETE FROM sales_contract_extensions "
                        "WHERE contract_id=%s",
                        (created["contract"],),
                    )
                    cursor.execute(
                        "DELETE FROM mvp_audit_events "
                        "WHERE aggregate_id=%s AND aggregate_type='CONTRACT'",
                        (created["contract"],),
                    )
                    cursor.execute(
                        "DELETE FROM contracts WHERE contract_id=%s",
                        (created["contract"],),
                    )
                if created.get("customer"):
                    cursor.execute(
                        "DELETE FROM customer_entry_profiles "
                        "WHERE customer_id=%s",
                        (created["customer"],),
                    )
                    cursor.execute(
                        "DELETE FROM mvp_audit_events "
                        "WHERE aggregate_id=%s AND aggregate_type='CUSTOMER'",
                        (created["customer"],),
                    )
                    cursor.execute(
                        "DELETE FROM customers WHERE customer_id=%s",
                        (created["customer"],),
                    )
                if created.get("draft"):
                    cursor.execute(
                        "DELETE FROM customer_entry_drafts WHERE draft_id=%s",
                        (created["draft"],),
                    )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()


if __name__ == "__main__":
    main()

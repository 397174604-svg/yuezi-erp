#!/usr/bin/env python3
"""Read-only smoke check for ERP page-load APIs.

The script never calls a write endpoint.  Credentials are supplied through
environment variables so no password or token is written to the repository.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


BASE_URL = os.getenv("ERP_SMOKE_BASE_URL", "http://127.0.0.1:3000").rstrip("/")
USERNAME = os.getenv("ERP_SMOKE_USERNAME", "admin")
PASSWORD = os.getenv("ERP_SMOKE_PASSWORD", "")


def request(path: str, token: str = "", body: dict | None = None) -> tuple[int, dict]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Token"] = token
    req = urllib.request.Request(BASE_URL + path, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        payload = json.loads(exc.read().decode("utf-8"))
        return exc.code, payload


def page_load_endpoints() -> list[tuple[str, str]]:
    endpoints: list[tuple[str, str]] = [
        ("AUTH", "/vue-element-admin/user/info"),
        ("CUSTOMER-OPTIONS", "/vue-element-admin/erp/customer/entry-options"),
        ("MEMBER-OPTIONS", "/vue-element-admin/erp/assets/options?storeId=all"),
        ("MEMBER-ACCOUNTS", "/vue-element-admin/erp/assets/accounts?storeId=all"),
        ("MEMBER-CARDS", "/vue-element-admin/erp/assets/cards?storeId=all"),
        ("FINANCE-OPTIONS", "/vue-element-admin/erp/finance/options?storeId=1"),
        ("SCHEDULE-OPTIONS", "/vue-element-admin/erp/rehab/options?storeId=1"),
        ("F081", "/vue-element-admin/erp/research/modules/beauty-cases?storeId=1"),
    ]

    customer_resources = {
        "F003": "customers",
        "F004": "customers",
        "F128": "customers",
    }
    service_resources = {"F005": "f005", "F043": "f043", "F084": "f084", "F094": "f094"}
    sales_resources = {"F020": "contracts", "F050": "packages", "F082": "card-packages"}
    finance_resources = {
        "F007": "receipt-create",
        "F009": "receipts",
        "F011": "refund-applications",
        "F012": "reconciliations",
        "F013": "invoices",
        "F014": "reconciliations",
        "F015": "payments",
        "F016": "receipts",
        "F080": "reconciliations",
    }
    schedule_resources = {"F017": "service-appointments", "F086": "staff-schedule-settings"}
    room_resources = {"F018": "room-map", "F019": "smart-allocation"}
    nursing_resources = {
        "F021": "nursing-center",
        "F022": "health-assessments",
        "F024": "nursing-dashboard",
        "F026": "check-in-handover",
        "F075": "record-visibility-scope",
        "F078": "missed-record-reminders",
        "F118": "shift-handover",
        "F119": "infection-management",
        "F125": "nursing-task-orders",
    }
    baby_resources = {
        "F027": "baby-log",
        "F069": "baby-log-completion",
        "F111": "newborn-care-records",
        "F112": "baby-temperature",
        "F115": "baby-growth-profile",
        "F120": "baby-medications",
        "F121": "baby-visitors",
        "F122": "baby-discharge-handover",
    }
    diet_resources = {"F023": "diet-statistics", "F028": "meal-orders", "F029": "dishes"}
    inventory_resources = {
        "F030": "warehouse-stock-query",
        "F031": "stock-transfers",
        "F032": "stocktakes",
        "F033": "stock-warnings",
        "F034": "purchase-orders",
        "F035": "stock-summary-report",
        "F036": "batch-expiry",
        "F037": "supplier-records",
    }
    recovery_resources = {
        "F099": "recovery-programs",
        "F100": "recovery-schedule",
        "F101": "postpartum-assessments",
        "F102": "recovery-service-tracking",
        "F103": "recovery-store-dashboard",
        "F104": "recovery-upsell",
        "F105": "recovery-assets",
        "F106": "recovery-staff-performance",
    }

    for feature_id, resource in customer_resources.items():
        endpoints.append((feature_id, f"/vue-element-admin/erp/customer/modules/{resource}?storeId=all"))
    for feature_id, resource in service_resources.items():
        endpoints.append((feature_id, f"/vue-element-admin/erp/service/{resource}?storeId=all"))
    for feature_id, resource in sales_resources.items():
        endpoints.append((feature_id, f"/vue-element-admin/erp/sales/modules/{resource}?storeId=1"))
    for feature_id, resource in finance_resources.items():
        endpoints.append((feature_id, f"/vue-element-admin/erp/finance/modules/{resource}?storeId=1"))
    for feature_id, resource in schedule_resources.items():
        endpoints.append((feature_id, f"/vue-element-admin/erp/rehab/modules/{resource}?storeId=1"))
    for feature_id, resource in room_resources.items():
        endpoints.append((feature_id, f"/vue-element-admin/erp/room/modules/{resource}?storeId=1"))
    for feature_id, resource in nursing_resources.items():
        endpoints.append((feature_id, f"/vue-element-admin/erp/nursing/modules/{resource}?storeId=1"))
    for feature_id, resource in baby_resources.items():
        endpoints.append((feature_id, f"/vue-element-admin/erp/baby/modules/{resource}?storeId=1"))
    for feature_id, resource in diet_resources.items():
        endpoints.append((feature_id, f"/vue-element-admin/erp/diet/modules/{resource}?storeId=1"))
    for feature_id, resource in inventory_resources.items():
        endpoints.append((feature_id, f"/vue-element-admin/erp/inventory/modules/{resource}?storeId=1"))
    for feature_id, resource in recovery_resources.items():
        endpoints.append((feature_id, f"/vue-element-admin/erp/rehab/modules/{resource}?storeId=1"))
    return endpoints


def main() -> int:
    if not PASSWORD:
        print("ERP_SMOKE_PASSWORD is required", file=sys.stderr)
        return 2
    status, payload = request(
        "/vue-element-admin/user/login",
        body={"username": USERNAME, "password": PASSWORD},
    )
    token = ((payload.get("data") or {}).get("token") if isinstance(payload, dict) else "")
    if status != 200 or not token:
        print(json.dumps({"login": {"status": status, "payload": payload}}, ensure_ascii=False, indent=2))
        return 1

    results = []
    for feature_id, path in page_load_endpoints():
        status, payload = request(path, token=token)
        results.append(
            {
                "featureId": feature_id,
                "path": urllib.parse.urlsplit(path).path,
                "status": status,
                "code": payload.get("code") if isinstance(payload, dict) else None,
                "message": payload.get("message", "") if isinstance(payload, dict) else "",
            }
        )
    failures = [item for item in results if item["status"] != 200 or item["code"] != 20000]
    print(json.dumps({"checked": len(results), "failed": failures}, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

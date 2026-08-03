#!/usr/bin/env python3
"""Live, non-destructive RBAC regression for the confirmed ERP role accounts."""

from __future__ import annotations

import json
import os
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BASE_URL = os.environ.get("ERP_MVP_BASE_URL", "http://127.0.0.1:3000")


def request(path: str, token: str = "", body=None, query=None):
    if query:
        path += "?" + urlencode(query)
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        headers["X-Token"] = token
    req = Request(
        BASE_URL + path,
        data=(json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None),
        headers=headers,
        method="POST" if body is not None else "GET",
    )
    try:
        with urlopen(req, timeout=20) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def login(username: str, password_env: str):
    password = os.environ.get(password_env, "")
    if not password:
        raise RuntimeError(f"{password_env} is required")
    status, payload = request(
        "/vue-element-admin/user/login",
        body={"username": username, "password": password},
    )
    if status != 200 or payload.get("code") != 20000:
        raise AssertionError(f"{username} login failed: HTTP {status}")
    return payload["data"]["token"]


def expect_ok(username: str, token: str, path: str, query=None):
    status, payload = request(path, token=token, query=query)
    if status != 200 or payload.get("code") != 20000:
        raise AssertionError(f"{username} {path}: HTTP {status} {payload}")
    return payload.get("data") or {}


def store_ids(rows):
    values = set()
    for row in rows or []:
        value = row.get("store_id", row.get("storeId"))
        if value not in (None, ""):
            values.add(int(value))
    return values


def main():
    cases = (
        ("韩新", "ERP_SALES_ACCOUNT_PASSWORD", "SALES_MANAGER", {1, 2}),
        ("许曼", "ERP_RECOVERY_ACCOUNT_PASSWORD", "RECOVERY_THERAPIST", {2}),
        ("董丽霞", "ERP_ROOM_ACCOUNT_PASSWORD", "HOUSEKEEPER", {2}),
    )
    report = []
    scoped_paths = (
        "/vue-element-admin/erp/mvp/options",
        "/vue-element-admin/erp/mvp/overview",
        "/vue-element-admin/erp/mvp/customers",
        "/vue-element-admin/erp/mvp/contracts",
        "/vue-element-admin/erp/mvp/receipts",
        "/vue-element-admin/erp/mvp/rooms",
        "/vue-element-admin/erp/mvp/bookings",
        "/vue-element-admin/erp/rehab/options",
        "/vue-element-admin/erp/rehab/modules/service-appointments",
        "/vue-element-admin/erp/rehab/modules/staff-schedule-settings",
    )
    recovery_resources = (
        "unbooked-customer-services",
        "service-appointments",
        "service-overview-query",
        "staff-task-board",
        "staff-schedule-settings",
        "technician-task-board",
        "customer-service-query",
        "rehab-service-records",
        "completed-service-consumption",
        "rehab-health-assessments",
        "recovery-programs",
        "recovery-schedule",
        "postpartum-assessments",
        "recovery-service-tracking",
        "recovery-store-dashboard",
        "recovery-upsell",
        "recovery-assets",
        "recovery-staff-performance",
    )
    for username, password_env, role, expected_stores in cases:
        token = login(username, password_env)
        info = expect_ok(username, token, "/vue-element-admin/user/info")
        if role not in info.get("roles", []):
            raise AssertionError(f"{username}: missing role {role}")
        if set(info.get("storeIds", [])) != expected_stores:
            raise AssertionError(
                f"{username}: stores {info.get('storeIds')} != {sorted(expected_stores)}"
            )

        # NotificationCenter reads all five sources together.  A single 403
        # makes the entire notification panel fail.
        for resource in ("customers", "contracts", "receipts", "bookings"):
            data = expect_ok(
                username, token, f"/vue-element-admin/erp/mvp/{resource}"
            )
            if expected_stores == {2}:
                found = store_ids(data.get("list", []))
                if found - {2}:
                    raise AssertionError(f"{username} {resource}: cross-store rows {found}")
        appointments = expect_ok(
            username,
            token,
            "/vue-element-admin/erp/rehab/modules/service-appointments",
        )
        if expected_stores == {2}:
            found = store_ids(appointments.get("list", []))
            if found - {2}:
                raise AssertionError(f"{username} appointments: cross-store rows {found}")

        expect_ok(username, token, "/vue-element-admin/erp/mvp/overview")
        store_matrix = []
        for store_id in (1, 2):
            expected_status = 200 if store_id in expected_stores else 403
            path_statuses = []
            for path in scoped_paths:
                status, payload = request(
                    path, token=token, query={"storeId": store_id}
                )
                if status != expected_status:
                    raise AssertionError(
                        f"{username} {path} storeId={store_id}: "
                        f"HTTP {status}, expected {expected_status}: {payload}"
                    )
                if status == 200:
                    data = payload.get("data") or {}
                    if path.endswith("/options"):
                        found = {
                            int(item["id"])
                            for item in data.get("stores", [])
                            if item.get("id") not in (None, "")
                        }
                    else:
                        found = store_ids(data.get("list", []))
                    if found - {store_id}:
                        raise AssertionError(
                            f"{username} {path} storeId={store_id}: "
                            f"cross-store rows/options {sorted(found)}"
                        )
                path_statuses.append(status)
            store_matrix.append(
                {
                    "storeId": store_id,
                    "expected": expected_status,
                    "checked": len(path_statuses),
                }
            )
        report.append(
            {
                "username": username,
                "role": role,
                "storeIds": sorted(expected_stores),
                "notificationSources": 5,
                "dashboard": "passed",
                "storeMatrix": store_matrix,
            }
        )

        if role == "SALES_MANAGER":
            # An empty request must reach business validation (400), not RBAC
            # rejection (403); this proves the F017 write permission is active
            # without creating an acceptance-test appointment.
            status, payload = request(
                "/vue-element-admin/erp/rehab/modules/service-appointments/save",
                token=token,
                body={},
            )
            if status == 403 or status not in {400, 404}:
                raise AssertionError(
                    f"{username} F017 write gate: HTTP {status} {payload}"
                )

        if role == "HOUSEKEEPER":
            for resource in (
                "room-map",
                "room-reservations",
                "room-stays",
                "room-change-applications",
                "room-services",
            ):
                data = expect_ok(
                    username,
                    token,
                    f"/vue-element-admin/erp/room/modules/{resource}",
                    query={"storeId": 2},
                )
                found = store_ids(data.get("list", []))
                if found - {2}:
                    raise AssertionError(f"{username} {resource}: cross-store rows {found}")

        if role == "RECOVERY_THERAPIST":
            for store_id, expected_status in ((1, 403), (2, 200)):
                for resource in recovery_resources:
                    path = f"/vue-element-admin/erp/rehab/modules/{resource}"
                    status, payload = request(
                        path, token=token, query={"storeId": store_id}
                    )
                    if status != expected_status:
                        raise AssertionError(
                            f"{username} {resource} storeId={store_id}: "
                            f"HTTP {status}, expected {expected_status}: {payload}"
                        )
                    if status == 200:
                        found = store_ids((payload.get("data") or {}).get("list", []))
                        if found - {2}:
                            raise AssertionError(
                                f"{username} {resource}: cross-store rows {found}"
                            )

    print(json.dumps({"passed": True, "accounts": report}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

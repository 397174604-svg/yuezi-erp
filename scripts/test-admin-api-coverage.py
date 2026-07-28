#!/usr/bin/env python3
"""Check every read surface used by the ERP workbenches with an admin token."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))

from erp_read_surfaces import (  # noqa: E402
    BASIC_RESOURCES,
    MATERNITY_NURSE_RESOURCES,
    NURSING_RESOURCES,
    REPORT_RESOURCES,
    SYSTEM_RESOURCES,
)


BASE_URL = os.environ.get("ERP_API_URL", "http://127.0.0.1:3000").rstrip("/")
USERNAME = os.environ.get("ERP_TEST_USERNAME", "30admin")
PASSWORD = os.environ.get("ERP_TEST_PASSWORD", "")


def request_json(path: str, method: str = "GET", body: dict | None = None, token=""):
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Token"] = token
    request = Request(
        f"{BASE_URL}{path}", data=data, headers=headers, method=method
    )
    try:
        with urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return response.status, payload
    except HTTPError as exc:
        payload = json.loads(exc.read().decode("utf-8"))
        return exc.code, payload


def main() -> int:
    if not PASSWORD:
        print("ERP_TEST_PASSWORD is required.", file=sys.stderr)
        return 2

    status, login = request_json(
        "/vue-element-admin/user/login",
        method="POST",
        body={"username": USERNAME, "password": PASSWORD},
    )
    if status != 200 or login.get("code") != 20000:
        print(f"LOGIN FAILED: HTTP {status} {login.get('message', '')}")
        return 1
    token = login["data"]["token"]

    paths = ["/vue-element-admin/erp/foundation/overview"]
    groups = (
        ("/vue-element-admin/erp/nursing/modules", NURSING_RESOURCES),
        (
            "/vue-element-admin/erp/maternity-nurse/modules",
            MATERNITY_NURSE_RESOURCES,
        ),
        ("/vue-element-admin/erp/report/modules", REPORT_RESOURCES),
        ("/vue-element-admin/erp/system/modules", SYSTEM_RESOURCES),
        ("/vue-element-admin/erp/basic/modules", BASIC_RESOURCES),
    )
    for prefix, resources in groups:
        paths.extend(f"{prefix}/{resource}" for resource in sorted(resources))
    paths.append("/vue-element-admin/erp/risk/modules/yuexi-risk")
    paths.append("/vue-element-admin/erp/mama-box/overview")
    paths.extend(
        (
            "/vue-element-admin/erp/basic/modules/basic-items/preview",
            "/vue-element-admin/erp/system/modules/department-management/preview",
        )
    )

    failures = []
    status_counts: dict[int, int] = {}
    for path in paths:
        current_status, payload = request_json(path, token=token)
        status_counts[current_status] = status_counts.get(current_status, 0) + 1
        if current_status != 200 or payload.get("code") != 20000:
            failures.append(
                {
                    "path": path,
                    "status": current_status,
                    "code": payload.get("code"),
                    "message": payload.get("message"),
                    "errorType": payload.get("data", {}).get("errorType"),
                }
            )

    write_probes = (
        "/vue-element-admin/erp/foundation/stores/save",
        "/vue-element-admin/erp/customer/modules/clues/save",
        "/vue-element-admin/erp/customer/modules/clues/action",
        "/vue-element-admin/erp/diet/modules/dishes/save",
        "/vue-element-admin/erp/diet/modules/dishes/action",
        "/vue-element-admin/erp/inventory/modules/purchase-plans/save",
        "/vue-element-admin/erp/inventory/modules/purchase-plans/action",
        "/vue-element-admin/erp/mall/modules/products/save",
        "/vue-element-admin/erp/mall/modules/products/action",
        "/vue-element-admin/erp/nursing/modules/nursing-plan/save",
        "/vue-element-admin/erp/nursing/modules/nursing-plan/action",
        "/vue-element-admin/erp/maternity-nurse/modules/maternity-schedules/save",
        "/vue-element-admin/erp/maternity-nurse/modules/maternity-schedules/action",
        "/vue-element-admin/erp/mama-box/products/save",
        "/vue-element-admin/erp/mama-box/products/1/publish",
    )
    for path in write_probes:
        current_status, payload = request_json(
            path, method="POST", body={}, token=token
        )
        status_counts[current_status] = status_counts.get(current_status, 0) + 1
        if current_status in {404, 500}:
            failures.append(
                {
                    "path": path,
                    "status": current_status,
                    "code": payload.get("code"),
                    "message": payload.get("message"),
                    "errorType": payload.get("data", {}).get("errorType"),
                }
            )

    print(
        json.dumps(
            {
                "account": USERNAME,
                "checked": len(paths) + len(write_probes),
                "statusCounts": status_counts,
                "failures": failures,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

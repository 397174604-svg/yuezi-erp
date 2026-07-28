#!/usr/bin/env python3
"""Read-only API regression for the imported HOUSEKEEPER account."""

from __future__ import annotations

import json
import os
from urllib.error import HTTPError
from urllib.request import Request, urlopen


BASE_URL = os.environ.get("ERP_MVP_BASE_URL", "http://127.0.0.1:3000")
USERNAME = os.environ.get("ERP_ROOM_ACCOUNT_USERNAME", "董丽霞")
PASSWORD = os.environ.get("ERP_ROOM_ACCOUNT_PASSWORD", "")
RESOURCES = (
    "room-map",
    "room-trend",
    "room-type-trend",
    "smart-allocation",
    "saleable-statistics",
    "room-type-bookings",
    "room-reservations",
    "room-stays",
    "stay-extensions",
    "room-change-applications",
    "gift-distribution",
    "room-services",
    "outing-applications",
    "borrowed-items",
    "laundry",
)


def request(path: str, body=None, token: str = ""):
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        headers["X-Token"] = token
    req = Request(
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
        with urlopen(req, timeout=15) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def main():
    if not PASSWORD:
        raise SystemExit("ERP_ROOM_ACCOUNT_PASSWORD is required.")
    status, payload = request(
        "/vue-element-admin/user/login",
        {"username": USERNAME, "password": PASSWORD},
    )
    if status != 200 or payload.get("code") != 20000:
        raise AssertionError(f"Login failed: {status} {payload}")
    token = payload["data"]["token"]
    status, info = request("/vue-element-admin/user/info", token=token)
    if status != 200:
        raise AssertionError(f"User info failed: {status} {info}")
    if "HOUSEKEEPER" not in info["data"].get("roles", []):
        raise AssertionError(f"Unexpected roles: {info['data'].get('roles')}")
    if info["data"].get("storeIds") != [2]:
        raise AssertionError(
            f"Expected Yellow River store only: {info['data'].get('storeIds')}"
        )

    results = []
    for resource in RESOURCES:
        status, response = request(
            f"/vue-element-admin/erp/room/modules/{resource}",
            token=token,
        )
        if status != 200 or response.get("code") != 20000:
            raise AssertionError(f"{resource}: {status} {response}")
        results.append(
            {
                "resource": resource,
                "status": status,
                "count": len(response["data"].get("list", [])),
            }
        )

    status, allowed = request(
        "/vue-element-admin/erp/room/modules/outing-applications/action",
        {"action": "打印"},
        token,
    )
    if status != 200 or allowed.get("code") != 20000:
        raise AssertionError(f"Allowed button failed: {status} {allowed}")

    status, denied = request(
        "/vue-element-admin/erp/room/modules/stay-extensions/action",
        {"action": "审核", "id": 0},
        token,
    )
    if status != 403:
        raise AssertionError(
            f"UnGranted stay audit must be denied, got {status}: {denied}"
        )

    print(
        json.dumps(
            {
                "username": info["data"]["name"],
                "roles": info["data"]["roles"],
                "storeIds": info["data"]["storeIds"],
                "permissions": len(info["data"].get("permissions", [])),
                "resources": results,
                "allowedButton": "外出申请/打印",
                "deniedButton": "续住信息/审核",
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

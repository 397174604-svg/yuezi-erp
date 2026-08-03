#!/usr/bin/env python3
"""Verify the four MVP login roles without creating business records."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from urllib.error import HTTPError
from urllib.request import Request, urlopen


BASE_URL = os.environ.get("ERP_MVP_BASE_URL", "http://127.0.0.1:3000")


@dataclass(frozen=True)
class AccountCase:
    username: str
    password_env: str
    role: str
    store_ids: tuple[int, ...]
    readable_resources: tuple[str, ...]
    forbidden_resources: tuple[str, ...]


CASES = (
    AccountCase(
        "admin",
        "ERP_BOOTSTRAP_ADMIN_PASSWORD",
        "SYS_ADMIN",
        (1, 2),
        ("customers", "contracts", "receipts", "rooms", "bookings"),
        (),
    ),
    AccountCase(
        "韩新",
        "ERP_SALES_ACCOUNT_PASSWORD",
        "SALES_MANAGER",
        (1, 2),
        ("customers", "contracts", "receipts", "rooms", "bookings"),
        (),
    ),
    AccountCase(
        "许曼",
        "ERP_RECOVERY_ACCOUNT_PASSWORD",
        "RECOVERY_THERAPIST",
        (2,),
        ("customers", "contracts", "receipts", "rooms", "bookings"),
        (),
    ),
    AccountCase(
        "董丽霞",
        "ERP_ROOM_ACCOUNT_PASSWORD",
        "HOUSEKEEPER",
        (2,),
        ("customers", "contracts", "receipts", "rooms", "bookings"),
        (),
    ),
)


def request(path: str, method: str = "GET", body=None, token: str = ""):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Token"] = token
    req = Request(
        BASE_URL + path,
        data=json.dumps(body).encode("utf-8") if body is not None else None,
        headers=headers,
        method=method,
    )
    try:
        with urlopen(req, timeout=10) as response:
            status = response.status
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        status = exc.code
        payload = json.loads(exc.read().decode("utf-8"))
    return status, payload


def login(case: AccountCase) -> str:
    password = os.environ.get(case.password_env, "")
    if not password:
        raise RuntimeError(f"{case.password_env} is required")
    status, payload = request(
        "/vue-element-admin/user/login",
        "POST",
        {"username": case.username, "password": password},
    )
    if status != 200 or payload.get("code") != 20000:
        raise AssertionError(f"{case.username}: login failed ({status})")
    return payload["data"]["token"]


def assert_status(
    username: str,
    path: str,
    expected: int,
    method: str = "GET",
    body=None,
    token: str = "",
):
    status, payload = request(path, method, body, token)
    if status != expected:
        message = payload.get("message", "unknown error")
        raise AssertionError(
            f"{username}: {method} {path} expected {expected}, got {status}: {message}"
        )


def main():
    results = []
    tokens = {}
    for case in CASES:
        token = login(case)
        tokens[case.username] = token
        status, payload = request("/vue-element-admin/user/info", token=token)
        if status != 200:
            raise AssertionError(f"{case.username}: user info failed ({status})")
        info = payload["data"]
        if case.role not in info["roles"]:
            raise AssertionError(f"{case.username}: missing role {case.role}")
        actual_stores = tuple(sorted(int(item) for item in info["storeIds"]))
        if actual_stores != case.store_ids:
            raise AssertionError(
                f"{case.username}: stores {actual_stores}, expected {case.store_ids}"
            )
        for resource in case.readable_resources:
            assert_status(
                case.username,
                f"/vue-element-admin/erp/mvp/{resource}",
                200,
                token=token,
            )
        for resource in case.forbidden_resources:
            assert_status(
                case.username,
                f"/vue-element-admin/erp/mvp/{resource}",
                403,
                token=token,
            )
        results.append(
            {
                "username": case.username,
                "role": case.role,
                "storeIds": list(actual_stores),
                "permissions": len(info["permissions"]),
                "readable": list(case.readable_resources),
                "forbidden": list(case.forbidden_resources),
            }
        )

    denied_action_checks = (
        ("许曼", "/vue-element-admin/erp/mvp/contracts/0/approve", {}),
        ("许曼", "/vue-element-admin/erp/mvp/receipts/0/approve", {}),
        ("许曼", "/vue-element-admin/erp/mvp/bookings", {}),
        ("董丽霞", "/vue-element-admin/erp/mvp/receipts", {}),
    )
    for username, path, body in denied_action_checks:
        assert_status(
            username,
            path,
            403,
            method="POST",
            body=body,
            token=tokens[username],
        )

    print(
        json.dumps(
            {
                "status": "passed",
                "accounts": results,
                "deniedActionChecks": len(denied_action_checks),
                "businessRecordsCreated": 0,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

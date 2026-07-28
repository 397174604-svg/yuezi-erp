#!/usr/bin/env python3
"""Verify role coverage and login for LOCAL_TEST representative accounts."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.mvp_api import connect


BASE_URL = os.environ.get("ERP_MVP_BASE_URL", "http://127.0.0.1:3000")
TENANT_ID = 1


def request(path: str, body=None, token=""):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Token"] = token
    req = Request(
        BASE_URL + path,
        data=json.dumps(body).encode("utf-8") if body is not None else None,
        headers=headers,
        method="POST" if body is not None else "GET",
    )
    try:
        with urlopen(req, timeout=10) as response:
            return response.status, json.loads(
                response.read().decode("utf-8")
            )
    except HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def database_cases():
    connection = connect()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                  ua.username,
                  r.legacy_role_id,
                  r.code AS role_code,
                  r.name AS role_name,
                  GROUP_CONCAT(
                    DISTINCT us.store_id ORDER BY us.store_id SEPARATOR ','
                  ) AS store_ids
                FROM user_accounts ua
                JOIN user_roles ur ON ur.user_id=ua.user_id
                JOIN roles r ON r.role_id=ur.role_id
                LEFT JOIN user_stores us ON us.user_id=ua.user_id
                WHERE ua.tenant_id=%s
                  AND ua.source_system='LOCAL_TEST'
                  AND ua.status='ACTIVE'
                  AND r.source_system='LEGACY_ERP'
                  AND r.status='ACTIVE'
                  AND ur.effective_from <= NOW()
                  AND (ur.effective_to IS NULL OR ur.effective_to > NOW())
                GROUP BY ua.username, r.legacy_role_id, r.code, r.name
                ORDER BY r.legacy_role_id
                """,
                (TENANT_ID,),
            )
            test_accounts = cursor.fetchall()
            cursor.execute(
                """
                SELECT
                  COUNT(*) AS roles_total,
                  SUM(CASE WHEN coverage.account_count > 0 THEN 1 ELSE 0 END)
                    AS roles_covered
                FROM (
                  SELECT
                    r.role_id,
                    COUNT(DISTINCT ua.user_id) AS account_count
                  FROM roles r
                  LEFT JOIN user_roles ur
                    ON ur.role_id=r.role_id
                    AND ur.effective_from <= NOW()
                    AND (ur.effective_to IS NULL OR ur.effective_to > NOW())
                  LEFT JOIN user_accounts ua
                    ON ua.user_id=ur.user_id AND ua.status='ACTIVE'
                  WHERE r.tenant_id=%s
                    AND r.source_system='LEGACY_ERP'
                    AND r.legacy_role_id IS NOT NULL
                    AND r.status='ACTIVE'
                  GROUP BY r.role_id
                ) coverage
                """,
                (TENANT_ID,),
            )
            coverage = cursor.fetchone()
    finally:
        connection.close()
    return test_accounts, coverage


def main():
    password = os.environ.get(
        "ERP_ROLE_TEST_ACCOUNT_INITIAL_PASSWORD", ""
    )
    if not password:
        raise SystemExit(
            "ERP_ROLE_TEST_ACCOUNT_INITIAL_PASSWORD is required."
        )
    cases, coverage = database_cases()
    if int(coverage["roles_total"]) != int(coverage["roles_covered"]):
        raise AssertionError("Not every retained role has an active account.")
    results = []
    for case in cases:
        status, payload = request(
            "/vue-element-admin/user/login",
            {"username": case["username"], "password": password},
        )
        if status != 200 or payload.get("code") != 20000:
            raise AssertionError(
                f'{case["username"]}: login failed ({status})'
            )
        token = payload["data"]["token"]
        status, payload = request(
            "/vue-element-admin/user/info", token=token
        )
        if status != 200:
            raise AssertionError(
                f'{case["username"]}: user info failed ({status})'
            )
        info = payload["data"]
        if case["role_code"] not in info.get("roles", []):
            raise AssertionError(
                f'{case["username"]}: role code mismatch'
            )
        if case["role_name"] not in info.get("roleNames", []):
            raise AssertionError(
                f'{case["username"]}: role name mismatch'
            )
        if info.get("storeIds") != [1]:
            raise AssertionError(
                f'{case["username"]}: expected store [1]'
            )
        if not info.get("mustChangePassword"):
            raise AssertionError(
                f'{case["username"]}: password-change flag missing'
            )
        results.append(
            {
                "username": case["username"],
                "legacyRoleId": case["legacy_role_id"],
                "role": case["role_name"],
                "storeIds": info["storeIds"],
                "permissions": len(info.get("permissions", [])),
            }
        )
    print(
        json.dumps(
            {
                "status": "passed",
                "activeRetainedRoles": int(coverage["roles_total"]),
                "rolesWithActiveAccount": int(coverage["roles_covered"]),
                "representativeTestAccountLogins": len(results),
                "accounts": results,
                "businessRecordsCreated": 0,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Login-regression for every retained active legacy account."""

from __future__ import annotations

import csv
import json
import os
from collections import defaultdict
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / ".private" / "system-settings-import"
BASE_URL = os.environ.get("ERP_MVP_BASE_URL", "http://127.0.0.1:3000")
EXCLUDED_ROLE_IDS = {22, 66, 67, 68, 69, 78, 79, 83}
PASSWORD_OVERRIDES = {
    "admin": "ERP_BOOTSTRAP_ADMIN_PASSWORD",
    "韩新": "ERP_SALES_ACCOUNT_PASSWORD",
    "许曼": "ERP_RECOVERY_ACCOUNT_PASSWORD",
    "董丽霞": "ERP_ROOM_ACCOUNT_PASSWORD",
}


def read_csv(name: str) -> list[dict]:
    with (SOURCE_DIR / name).open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        return list(csv.DictReader(handle))


def integer(value) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return 0


def truthy(value) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


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


def login(username: str, password: str):
    return request(
        "/vue-element-admin/user/login",
        {"username": username, "password": password},
    )


def main():
    initial_password = os.environ.get(
        "ERP_LEGACY_ACCOUNT_INITIAL_PASSWORD", ""
    )
    if not initial_password:
        raise SystemExit("ERP_LEGACY_ACCOUNT_INITIAL_PASSWORD is required.")
    roles = {
        integer(row["KeyId"]): row["RoleName"]
        for row in read_csv("config-roles.csv")
    }
    users = read_csv("config-users.csv")
    relations = read_csv("config-userRoleRelations.csv")
    relations_by_user = defaultdict(list)
    for row in relations:
        role_id = integer(row["roleKeyId"])
        if role_id not in EXCLUDED_ROLE_IDS:
            relations_by_user[integer(row["userKeyId"])].append(role_id)

    active_passed = 0
    disabled_rejected = 0
    multi_role_accounts = 0
    role_names_seen = set()
    for row in users:
        legacy_user_id = integer(row["KeyId"])
        expected_role_ids = relations_by_user.get(legacy_user_id, [])
        if not expected_role_ids:
            continue
        legacy_username = str(row["UserName"]).strip()
        disabled = truthy(row.get("IsDisabled")) or "禁用" in legacy_username
        username = (
            f"legacy-disabled-{legacy_user_id}"
            if disabled
            else legacy_username
        )
        password_env = PASSWORD_OVERRIDES.get(legacy_username)
        password = (
            os.environ.get(password_env, "")
            if password_env
            else initial_password
        )
        if not password:
            raise RuntimeError(f"Missing password environment for {username}")
        status, payload = login(username, password)
        if disabled:
            if status != 401:
                raise AssertionError(
                    f"Disabled account {legacy_user_id} returned {status}"
                )
            disabled_rejected += 1
            continue
        if status != 200 or payload.get("code") != 20000:
            raise AssertionError(
                f"Active account {legacy_user_id} login failed ({status})"
            )
        token = payload["data"]["token"]
        info_status, info_payload = request(
            "/vue-element-admin/user/info", token=token
        )
        if info_status != 200:
            raise AssertionError(
                f"Active account {legacy_user_id} info failed ({info_status})"
            )
        info = info_payload["data"]
        expected_names = {roles[role_id] for role_id in expected_role_ids}
        actual_names = set(info.get("roleNames", []))
        if not expected_names.issubset(actual_names):
            raise AssertionError(
                f"Active account {legacy_user_id} role-name mismatch"
            )
        if not info.get("storeIds"):
            raise AssertionError(
                f"Active account {legacy_user_id} has no store scope"
            )
        if len(expected_role_ids) > 1:
            multi_role_accounts += 1
        role_names_seen.update(expected_names)
        active_passed += 1

    print(
        json.dumps(
            {
                "status": "passed",
                "activeAccountLogins": active_passed,
                "disabledAccountsRejected": disabled_rejected,
                "multiRoleAccounts": multi_role_accounts,
                "retainedRoleNamesObserved": len(role_names_seen),
                "businessRecordsCreated": 0,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

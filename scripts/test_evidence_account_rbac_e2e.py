#!/usr/bin/env python3
"""Evidence and live RBAC audit for the four approved Web accounts.

The script is read-only: it never creates business records.  Passwords are
accepted only through environment variables and are never printed.  It checks
the evidence matrix and migration, database bindings, live login/user-info,
menu-driving permissions, notification data dependencies, representative
route targets, store isolation, and safe allowed/denied operations.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".deps"))

try:
    import pymysql
except ModuleNotFoundError:
    pymysql = None


BASE_URL = os.environ.get("ERP_MVP_BASE_URL", "http://127.0.0.1:3000").rstrip("/")
TENANT_ID = 1
MATRIX_PATH = ROOT / "docs" / "设计与业务规则" / "Web登录账号证据矩阵-2026-08-01.md"
MIGRATION_PATH = ROOT / "database" / "mysql" / "migrations" / "V20260801_031__evidence_backed_role_account_staff.sql"
NOTIFICATION_PATH = ROOT / "src" / "layout" / "components" / "NotificationCenter.vue"
ROUTER_PATH = ROOT / "src" / "router" / "index.js"
PERMISSION_STORE_PATH = ROOT / "src" / "store" / "modules" / "permission.js"
FEATURE_REGISTRY_PATH = ROOT / "src" / "config" / "erp-feature-registry.js"


@dataclass(frozen=True)
class AccountCase:
    username: str
    password_env: str
    role_code: str
    role_name: str
    default_store_id: int
    store_ids: tuple[int, ...]
    allowed_reads: tuple[str, ...]
    forbidden_reads: tuple[str, ...]
    allowed_probe: tuple[str, str, dict[str, Any], tuple[int, ...]]
    denied_probes: tuple[tuple[str, str, dict[str, Any]], ...]


NOTIFICATION_DEPENDENCIES = (
    "/vue-element-admin/erp/mvp/customers",
    "/vue-element-admin/erp/mvp/contracts",
    "/vue-element-admin/erp/mvp/receipts",
    "/vue-element-admin/erp/mvp/bookings",
    "/vue-element-admin/erp/rehab/modules/service-appointments",
)

CASES = (
    AccountCase(
        "admin", "ERP_BOOTSTRAP_ADMIN_PASSWORD", "SYS_ADMIN", "超级管理员", 1, (1, 2),
        (*NOTIFICATION_DEPENDENCIES, "/vue-element-admin/erp/mvp/rooms"), (),
        ("POST", "/vue-element-admin/erp/mvp/contracts/0/approve", {}, (400, 404)), (),
    ),
    AccountCase(
        "韩新", "ERP_SALES_ACCOUNT_PASSWORD", "SALES_MANAGER", "销售经理", 1, (1, 2),
        (*NOTIFICATION_DEPENDENCIES, "/vue-element-admin/erp/mvp/rooms"), (),
        ("POST", "/vue-element-admin/erp/mvp/receipts/0/approve", {}, (400, 404)),
        (),
    ),
    AccountCase(
        "许曼", "ERP_RECOVERY_ACCOUNT_PASSWORD", "RECOVERY_THERAPIST", "产后修复师", 2, (2,),
        (*NOTIFICATION_DEPENDENCIES, "/vue-element-admin/erp/mvp/rooms"), (),
        ("POST", "/vue-element-admin/erp/rehab/modules/recovery-upsell/action", {"recordId": "OP-0", "action": "记录跟进"}, (400, 404, 409)),
        (
            ("POST", "/vue-element-admin/erp/mvp/contracts/0/approve", {}),
            ("POST", "/vue-element-admin/erp/mvp/receipts/0/approve", {}),
            ("POST", "/vue-element-admin/erp/mvp/bookings", {}),
        ),
    ),
    AccountCase(
        "董丽霞", "ERP_ROOM_ACCOUNT_PASSWORD", "HOUSEKEEPER", "客房管家", 2, (2,),
        (
            "/vue-element-admin/erp/mvp/customers", "/vue-element-admin/erp/mvp/contracts",
            "/vue-element-admin/erp/mvp/receipts",
            "/vue-element-admin/erp/mvp/rooms", "/vue-element-admin/erp/mvp/bookings",
            "/vue-element-admin/erp/rehab/modules/service-appointments",
        ),
        (),
        ("POST", "/vue-element-admin/erp/mvp/receipts/0/approve", {}, (400, 404)),
        (("POST", "/vue-element-admin/erp/mvp/receipts", {}),),
    ),
)


def database_connection():
    if pymysql is None:
        raise SystemExit("PyMySQL is required only for --mode database/all; --mode static remains available.")
    missing = [name for name in ("ERP_DB_USER", "ERP_DB_PASSWORD") if not os.environ.get(name)]
    if missing:
        raise SystemExit(f"Database audit requires environment variables: {', '.join(missing)}")
    host = os.environ.get("ERP_DB_HOST", "127.0.0.1")
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise SystemExit("RBAC evidence audit is restricted to loopback MySQL.")
    return pymysql.connect(
        host=host,
        port=int(os.environ.get("ERP_DB_PORT", "3306")),
        user=os.environ["ERP_DB_USER"],
        password=os.environ["ERP_DB_PASSWORD"],
        database=os.environ.get("ERP_DB_NAME", "yuezi"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


def request(path: str, method: str = "GET", body=None, token: str = "", query=None):
    if query:
        path = f"{path}?{urlencode(query)}"
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        headers["X-Token"] = token
    req = Request(
        BASE_URL + path,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None,
        headers=headers,
        method=method,
    )
    try:
        with urlopen(req, timeout=15) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"message": raw[:200]}
        return exc.code, payload
    except URLError as exc:
        raise AssertionError(f"Local ERP API is unavailable: {exc}") from exc


def static_evidence_audit() -> dict:
    matrix = MATRIX_PATH.read_text(encoding="utf-8")
    migration = MIGRATION_PATH.read_text(encoding="utf-8")
    notification = NOTIFICATION_PATH.read_text(encoding="utf-8")
    router = ROUTER_PATH.read_text(encoding="utf-8")
    permission_store = PERMISSION_STORE_PATH.read_text(encoding="utf-8")
    feature_registry = FEATURE_REGISTRY_PATH.read_text(encoding="utf-8")
    for case in CASES:
        assert case.username in matrix, f"evidence matrix missing {case.username}"
        assert case.role_name in matrix, f"evidence matrix missing role {case.role_name}"
    for username in ("韩新", "许曼", "董丽霞"):
        assert username in migration, f"migration missing {username}"
    assert migration.count("CLIENT_CHAT_2026-07-23") >= 3
    assert "许曼曼" in migration and "IDENTITY_PENDING" in migration
    for dependency in NOTIFICATION_DEPENDENCIES:
        resource = dependency.rsplit("/", 1)[-1]
        assert resource in notification, f"notification dependency missing {resource}"
    route_targets = (
        "/dashboard", "/customer/signing-workbench", "/room/item-1", "/schedule/item-1"
    )
    for target in route_targets:
        assert target in notification, f"notification route target missing {target}"
    assert "filterAsyncRoutes" in permission_store
    assert "permissions.includes(permission)" in permission_store
    assert "legacyNavId" in permission_store
    assert "path: 'dashboard'" in router
    assert "redirect: '/dashboard'" in router
    assert "path: 'signing-workbench'" in router
    assert "const erpRoutes" in router
    for feature_id in ("F017", "F018"):
        assert feature_id in feature_registry, f"feature registry missing notification target {feature_id}"
    return {
        "matrix": str(MATRIX_PATH.relative_to(ROOT)),
        "migration": str(MIGRATION_PATH.relative_to(ROOT)),
        "chatEvidenceAccounts": ["韩新", "许曼", "董丽霞"],
        "adminEvidence": "matrix-and-project-owner-confirmation",
        "identityPending": "许曼与花名册许曼曼是否同一人",
        "notificationDependencies": len(NOTIFICATION_DEPENDENCIES),
        "notificationRouteTargets": list(route_targets),
        "routeFilter": "role/permission/legacy-nav",
        "knownReviewItems": [
            "许曼与花名册许曼曼是否同一人仍待甲方确认",
        ],
    }


def database_evidence_audit() -> list[dict]:
    connection = database_connection()
    results = []
    try:
        with connection.cursor() as cursor:
            for case in CASES:
                cursor.execute(
                    """
                    SELECT ua.user_id,ua.username,ua.status AS account_status,
                           ua.default_store_id,ua.staff_id,
                           st.name AS staff_name,st.source_file,st.source_status,
                           st.review_status,
                           GROUP_CONCAT(DISTINCT r.code ORDER BY r.code SEPARATOR ',') AS role_codes,
                           GROUP_CONCAT(DISTINCT r.name ORDER BY r.name SEPARATOR ',') AS role_names,
                           GROUP_CONCAT(DISTINCT us.store_id ORDER BY us.store_id SEPARATOR ',') AS store_ids,
                           COUNT(DISTINCT p.permission_id) AS permission_count
                    FROM user_accounts ua
                    LEFT JOIN staff st ON st.staff_id=ua.staff_id AND st.tenant_id=ua.tenant_id
                    LEFT JOIN user_roles ur ON ur.user_id=ua.user_id
                      AND ur.effective_from<=NOW() AND (ur.effective_to IS NULL OR ur.effective_to>NOW())
                    LEFT JOIN roles r ON r.role_id=ur.role_id AND r.status='ACTIVE'
                    LEFT JOIN user_stores us ON us.user_id=ua.user_id
                    LEFT JOIN role_permissions rp ON rp.role_id=r.role_id AND rp.effect='ALLOW'
                    LEFT JOIN permissions p ON p.permission_id=rp.permission_id AND p.status='ACTIVE'
                    WHERE ua.tenant_id=%s AND ua.username=%s
                    GROUP BY ua.user_id,ua.username,ua.status,ua.default_store_id,ua.staff_id,
                             st.name,st.source_file,st.source_status,st.review_status
                    """,
                    (TENANT_ID, case.username),
                )
                row = cursor.fetchone()
                assert row, f"database account missing: {case.username}"
                role_codes = set(filter(None, str(row.get("role_codes") or "").split(",")))
                role_names = set(filter(None, str(row.get("role_names") or "").split(",")))
                store_ids = tuple(int(item) for item in str(row.get("store_ids") or "").split(",") if item)
                assert row["account_status"] == "ACTIVE", f"{case.username} inactive"
                assert case.role_code in role_codes, f"{case.username} missing {case.role_code}"
                assert role_names, f"{case.username} missing role display name"
                if case.username != "admin":
                    assert int(row["default_store_id"]) == case.default_store_id
                assert store_ids == case.store_ids, f"{case.username} stores {store_ids}, expected {case.store_ids}"
                assert int(row["permission_count"] or 0) > 0, f"{case.username} has no permission grants"
                evidence = "matrix"
                if case.username != "admin":
                    evidence = str(row.get("source_file") or "")
                    assert row.get("staff_name") in ({"许曼", "许曼曼"} if case.username == "许曼" else {case.username})
                results.append({
                    "username": case.username,
                    "roleCode": case.role_code,
                    "roleName": case.role_name,
                    "defaultStoreId": int(row["default_store_id"]),
                    "storeIds": list(store_ids),
                    "staffName": row.get("staff_name"),
                    "evidenceSource": evidence,
                    "sourceStatus": row.get("source_status"),
                    "reviewStatus": row.get("review_status"),
                    "permissionCount": int(row["permission_count"]),
                })
    finally:
        connection.close()
    return results


def assert_response(username: str, path: str, token: str, expected: tuple[int, ...], method="GET", body=None):
    status, payload = request(path, method, body, token)
    if status not in expected:
        raise AssertionError(
            f"{username}: {method} {path} expected {expected}, got {status}: {payload.get('message', '')}"
        )
    return status, payload


def live_rbac_audit() -> tuple[list[dict], list[dict]]:
    accounts = []
    gaps = []
    for case in CASES:
        password = os.environ.get(case.password_env, "")
        if not password:
            raise SystemExit(f"{case.password_env} is required for live RBAC audit")
        status, payload = request(
            "/vue-element-admin/user/login", "POST",
            {"username": case.username, "password": password},
        )
        if status != 200 or payload.get("code") != 20000:
            raise AssertionError(f"{case.username}: login failed ({status})")
        token = payload["data"]["token"]
        _status, info_payload = assert_response(
            case.username, "/vue-element-admin/user/info", token, (200,)
        )
        info = info_payload["data"]
        assert case.role_code in info.get("roles", [])
        assert info.get("roleNames", []), f"{case.username}: missing role display name"
        assert tuple(sorted(int(item) for item in info.get("storeIds", []))) == case.store_ids

        allowed = []
        for path in case.allowed_reads:
            assert_response(case.username, path, token, (200,))
            allowed.append(path)
        forbidden = []
        for path in case.forbidden_reads:
            assert_response(case.username, path, token, (403,))
            forbidden.append(path)

        notification_statuses = []
        for path in NOTIFICATION_DEPENDENCIES:
            dependency_status, _ = request(path, token=token)
            notification_statuses.append({"path": path, "status": dependency_status})
        notification_ready = all(item["status"] == 200 for item in notification_statuses)
        if not notification_ready:
            gaps.append({
                "username": case.username,
                "area": "navbar-notification",
                "reason": "NotificationCenter uses Promise.all, but one or more role dependencies are forbidden.",
                "dependencies": notification_statuses,
            })

        method, path, body, expected = case.allowed_probe
        probe_status, _ = assert_response(case.username, path, token, expected, method, body)
        denied = []
        for denied_method, denied_path, denied_body in case.denied_probes:
            assert_response(case.username, denied_path, token, (403,), denied_method, denied_body)
            denied.append(denied_path)

        store_scope = []
        for store_id in (1, 2):
            expected = (200,) if store_id in case.store_ids else (403,)
            scoped_path = f"/vue-element-admin/erp/mvp/rooms?storeId={store_id}"
            scoped_status, _ = assert_response(case.username, scoped_path, token, expected)
            store_scope.append({"storeId": store_id, "status": scoped_status})

        accounts.append({
            "username": case.username,
            "role": case.role_code,
            "storeIds": list(case.store_ids),
            "permissions": len(info.get("permissions", [])),
            "allowedReads": len(allowed),
            "forbiddenReads": len(forbidden),
            "allowedProbeStatus": probe_status,
            "deniedProbes": len(denied),
            "notificationReady": notification_ready,
            "storeScope": store_scope,
        })
    return accounts, gaps


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("static", "database", "live", "all"), default="all")
    parser.add_argument("--fail-on-notification-gap", action="store_true")
    args = parser.parse_args()
    if urlparse(BASE_URL).hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise SystemExit("Live RBAC audit is restricted to a loopback ERP API.")

    evidence = static_evidence_audit()
    database = database_evidence_audit() if args.mode in {"database", "all"} else []
    live, gaps = live_rbac_audit() if args.mode in {"live", "all"} else ([], [])
    result = {
        "status": "passed-with-gaps" if gaps else "passed",
        "evidence": evidence,
        "databaseAccounts": database,
        "liveAccounts": live,
        "configurationGaps": gaps,
        "businessRecordsCreated": 0,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if gaps and args.fail_on_notification_gap:
        raise SystemExit(2)


if __name__ == "__main__":
    main()

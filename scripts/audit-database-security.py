#!/usr/bin/env python3
"""Read-only tenant, store, account, and RBAC integrity audit."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEPS_DIR = REPO_ROOT / ".deps"
if DEPS_DIR.exists():
    sys.path.insert(0, str(DEPS_DIR))

try:
    import pymysql
    from pymysql.cursors import DictCursor
except ImportError as exc:
    raise SystemExit(
        "PyMySQL is required. Install it with: "
        "python -m pip install --target .deps PyMySQL"
    ) from exc


def connect():
    password = os.environ.get("ERP_DB_PASSWORD", "")
    if not password:
        raise SystemExit("ERP_DB_PASSWORD is required.")
    config = {
        "host": os.environ.get("ERP_DB_HOST", "127.0.0.1"),
        "port": int(os.environ.get("ERP_DB_PORT", "3306")),
        "user": os.environ.get("ERP_DB_USER", "yuezi_auditor"),
        "password": password,
        "database": os.environ.get("ERP_DB_NAME", "yuezi"),
        "charset": "utf8mb4",
        "cursorclass": DictCursor,
        "connect_timeout": 5,
        "read_timeout": 30,
        "autocommit": True,
    }
    ssl_ca = os.environ.get("ERP_DB_SSL_CA", "").strip()
    if ssl_ca:
        config["ssl"] = {"ca": ssl_ca, "check_hostname": True}
    return pymysql.connect(**config)


CHECKS = {
    "crossTenantStaffAccounts": """
        SELECT ua.user_id, ua.username, ua.tenant_id AS account_tenant,
               st.tenant_id AS staff_tenant
        FROM user_accounts ua
        JOIN staff st ON st.staff_id=ua.staff_id
        WHERE st.tenant_id<>ua.tenant_id
    """,
    "crossTenantDefaultStores": """
        SELECT ua.user_id, ua.username, ua.tenant_id AS account_tenant,
               s.tenant_id AS store_tenant, ua.default_store_id
        FROM user_accounts ua
        JOIN stores s ON s.store_id=ua.default_store_id
        WHERE s.tenant_id<>ua.tenant_id
    """,
    "crossTenantUserStores": """
        SELECT ua.user_id, ua.username, ua.tenant_id AS account_tenant,
               s.tenant_id AS store_tenant, us.store_id
        FROM user_stores us
        JOIN user_accounts ua ON ua.user_id=us.user_id
        JOIN stores s ON s.store_id=us.store_id
        WHERE s.tenant_id<>ua.tenant_id
    """,
    "crossTenantUserRoles": """
        SELECT ua.user_id, ua.username, ua.tenant_id AS account_tenant,
               r.tenant_id AS role_tenant, r.code AS role_code
        FROM user_roles ur
        JOIN user_accounts ua ON ua.user_id=ur.user_id
        JOIN roles r ON r.role_id=ur.role_id
        WHERE r.tenant_id<>ua.tenant_id
    """,
    "defaultStoreWithoutGrant": """
        SELECT ua.user_id, ua.username, ua.default_store_id
        FROM user_accounts ua
        LEFT JOIN user_stores us
          ON us.user_id=ua.user_id AND us.store_id=ua.default_store_id
        WHERE ua.status='ACTIVE' AND ua.default_store_id IS NOT NULL
          AND us.user_id IS NULL
    """,
    "activeAccountsWithoutStore": """
        SELECT ua.user_id, ua.username
        FROM user_accounts ua
        LEFT JOIN user_stores us ON us.user_id=ua.user_id
        WHERE ua.status='ACTIVE'
        GROUP BY ua.user_id, ua.username
        HAVING COUNT(us.store_id)=0
    """,
    "activeAccountsWithoutRole": """
        SELECT ua.user_id, ua.username
        FROM user_accounts ua
        LEFT JOIN user_roles ur
          ON ur.user_id=ua.user_id
         AND ur.effective_from<=NOW()
         AND (ur.effective_to IS NULL OR ur.effective_to>NOW())
        LEFT JOIN roles r ON r.role_id=ur.role_id
          AND r.tenant_id=ua.tenant_id AND r.status='ACTIVE'
        WHERE ua.status='ACTIVE'
        GROUP BY ua.user_id, ua.username
        HAVING COUNT(r.role_id)=0
    """,
    "invalidRoleScopeValues": """
        SELECT rds.role_id, r.code AS role_code, rds.module_code,
               rds.scope_type
        FROM role_data_scopes rds
        JOIN roles r ON r.role_id=rds.role_id
        WHERE rds.scope_type NOT IN ('SELF','DEPARTMENT','STORE','ALL')
    """,
}


def audit() -> dict:
    connection = connect()
    try:
        results = {}
        with connection.cursor() as cursor:
            for name, sql in CHECKS.items():
                cursor.execute(sql)
                rows = list(cursor.fetchall())
                results[name] = {"count": len(rows), "sample": rows[:20]}
            cursor.execute(
                """
                SELECT ua.username,
                       GROUP_CONCAT(DISTINCT r.code ORDER BY r.code) AS roles,
                       GROUP_CONCAT(DISTINCT us.store_id ORDER BY us.store_id)
                         AS store_ids
                FROM user_accounts ua
                LEFT JOIN user_roles ur ON ur.user_id=ua.user_id
                  AND ur.effective_from<=NOW()
                  AND (ur.effective_to IS NULL OR ur.effective_to>NOW())
                LEFT JOIN roles r ON r.role_id=ur.role_id
                  AND r.tenant_id=ua.tenant_id AND r.status='ACTIVE'
                LEFT JOIN user_stores us ON us.user_id=ua.user_id
                WHERE ua.status='ACTIVE'
                GROUP BY ua.user_id, ua.username
                ORDER BY ua.username
                """
            )
            accounts = list(cursor.fetchall())
        violation_count = sum(item["count"] for item in results.values())
        return {
            "status": "passed" if violation_count == 0 else "failed",
            "readOnly": True,
            "violationCount": violation_count,
            "checks": results,
            "activeAccounts": accounts,
        }
    finally:
        connection.close()


def main():
    result = audit()
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    if result["violationCount"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()

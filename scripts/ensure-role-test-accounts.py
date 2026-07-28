#!/usr/bin/env python3
"""Ensure every retained legacy role has a dedicated test account.

Every retained role receives one deterministic LOCAL_TEST username. Test
accounts are deliberately unbound from staff, limited to one store, and forced
to change their password. Existing business accounts are never modified.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.mvp_api import connect, hash_password


TENANT_ID = 1
SOURCE_SYSTEM = "LOCAL_TEST"


def active_role_coverage(cursor):
    cursor.execute(
        """
        SELECT
          r.role_id,
          r.legacy_role_id,
          r.code,
          r.name,
          r.role_type,
          COUNT(DISTINCT ua.user_id) AS active_account_count,
          GROUP_CONCAT(
            DISTINCT ua.username ORDER BY ua.username SEPARATOR ','
          ) AS active_accounts
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
        GROUP BY
          r.role_id, r.legacy_role_id, r.code, r.name, r.role_type
        ORDER BY r.legacy_role_id
        """,
        (TENANT_ID,),
    )
    return cursor.fetchall()


def apply():
    initial_password = os.environ.get(
        "ERP_ROLE_TEST_ACCOUNT_INITIAL_PASSWORD", ""
    )
    if not initial_password:
        raise SystemExit(
            "ERP_ROLE_TEST_ACCOUNT_INITIAL_PASSWORD is required."
        )
    connection = connect()
    created = []
    try:
        with connection.cursor() as cursor:
            roles = active_role_coverage(cursor)
            for role in roles:
                username = f'test_{str(role["code"]).lower()}'
                cursor.execute(
                    """
                    SELECT user_id FROM user_accounts
                    WHERE tenant_id=%s AND username=%s
                    """,
                    (TENANT_ID, username),
                )
                account = cursor.fetchone()
                if account:
                    user_id = account["user_id"]
                    cursor.execute(
                        """
                        UPDATE user_accounts
                        SET password_hash=%s,
                            status='ACTIVE',
                            default_store_id=1,
                            source_system=%s,
                            must_change_password=1
                        WHERE user_id=%s
                        """,
                        (
                            hash_password(initial_password),
                            SOURCE_SYSTEM,
                            user_id,
                        ),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO user_accounts(
                          tenant_id, username, password_hash,
                          default_store_id, status, source_system,
                          must_change_password, created_at
                        ) VALUES (%s,%s,%s,1,'ACTIVE',%s,1,NOW())
                        """,
                        (
                            TENANT_ID,
                            username,
                            hash_password(initial_password),
                            SOURCE_SYSTEM,
                        ),
                    )
                    user_id = cursor.lastrowid
                cursor.execute(
                    """
                    DELETE FROM user_roles
                    WHERE user_id=%s AND role_id<>%s
                    """,
                    (user_id, role["role_id"]),
                )
                cursor.execute(
                    """
                    SELECT 1 FROM user_roles
                    WHERE user_id=%s AND role_id=%s
                      AND effective_from <= NOW()
                      AND (effective_to IS NULL OR effective_to > NOW())
                    LIMIT 1
                    """,
                    (user_id, role["role_id"]),
                )
                if not cursor.fetchone():
                    cursor.execute(
                        """
                        INSERT INTO user_roles(
                          user_id, role_id, effective_from
                        ) VALUES (%s,%s,NOW())
                        """,
                        (user_id, role["role_id"]),
                    )
                cursor.execute(
                    "DELETE FROM user_stores WHERE user_id=%s",
                    (user_id,),
                )
                cursor.execute(
                    """
                    INSERT INTO user_stores(
                      user_id, store_id, access_level
                    ) VALUES (%s,1,'READ')
                    """,
                    (user_id,),
                )
                created.append(
                    {
                        "legacyRoleId": role["legacy_role_id"],
                        "roleCode": role["code"],
                        "roleName": role["name"],
                        "username": username,
                        "storeIds": [1],
                        "mustChangePassword": True,
                    }
                )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    return {
        "status": "applied",
        "dedicatedAccountsCreatedOrReset": len(created),
        "accounts": created,
    }


def verify():
    connection = connect()
    try:
        with connection.cursor() as cursor:
            rows = active_role_coverage(cursor)
            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM user_accounts
                WHERE tenant_id=%s AND source_system=%s AND status='ACTIVE'
                """,
                (TENANT_ID, SOURCE_SYSTEM),
            )
            test_account_count = cursor.fetchone()["total"]
    finally:
        connection.close()
    missing = [
        {
            "legacyRoleId": row["legacy_role_id"],
            "roleCode": row["code"],
            "roleName": row["name"],
        }
        for row in rows
        if not int(row["active_account_count"])
    ]
    result = {
        "status": "passed" if not missing else "failed",
        "activeRetainedRoles": len(rows),
        "rolesWithActiveAccount": len(rows) - len(missing),
        "localTestAccounts": int(test_account_count),
        "missingRoles": missing,
    }
    if missing:
        raise SystemExit(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("apply", "verify"))
    args = parser.parse_args()
    result = apply() if args.command == "apply" else verify()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

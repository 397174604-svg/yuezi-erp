#!/usr/bin/env python3
"""Read-only audit of an imported ERP account's menu/button/data-scope grants."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / ".deps"))

import pymysql
from pymysql.cursors import DictCursor


def connect():
    return pymysql.connect(
        host=os.getenv("ERP_DB_HOST", "127.0.0.1"),
        port=int(os.getenv("ERP_DB_PORT", "3306")),
        user=os.getenv("ERP_DB_USER", "root"),
        password=os.environ["ERP_DB_PASSWORD"],
        database=os.getenv("ERP_DB_NAME", "yuezi"),
        charset="utf8mb4",
        cursorclass=DictCursor,
    )


def audit(username: str, nav_ids: list[int]) -> dict:
    if not nav_ids:
        raise SystemExit("至少提供一个 --nav-id")
    placeholders = ",".join(["%s"] * len(nav_ids))
    connection = connect()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT ua.user_id, ua.username, ua.staff_id,
                       ua.default_store_id, ua.department_id,
                       st.name AS staff_name, st.employee_no,
                       st.department, st.position,
                       GROUP_CONCAT(
                         DISTINCT CONCAT(r.code, ':', r.name)
                         ORDER BY r.role_id SEPARATOR ' | '
                       ) AS roles,
                       GROUP_CONCAT(
                         DISTINCT us.store_id ORDER BY us.store_id
                       ) AS store_ids
                FROM user_accounts ua
                LEFT JOIN staff st ON st.staff_id=ua.staff_id
                LEFT JOIN user_roles ur ON ur.user_id=ua.user_id
                LEFT JOIN roles r ON r.role_id=ur.role_id
                LEFT JOIN user_stores us ON us.user_id=ua.user_id
                WHERE ua.username=%s
                GROUP BY ua.user_id
                """,
                (username,),
            )
            account = cursor.fetchone()
            if not account:
                raise SystemExit(f"账号不存在: {username}")

            cursor.execute(
                f"""
                SELECT lpr.menu_id AS nav_id, lpr.menu_name,
                       lpr.button_id, lpr.button_name, p.code
                FROM user_accounts ua
                JOIN user_roles ur ON ur.user_id=ua.user_id
                JOIN role_permissions rp
                  ON rp.role_id=ur.role_id AND rp.effect='ALLOW'
                JOIN permissions p ON p.permission_id=rp.permission_id
                JOIN legacy_permission_resources lpr
                  ON lpr.permission_id=p.permission_id
                WHERE ua.username=%s AND lpr.surface='WEB'
                  AND lpr.menu_id IN ({placeholders})
                ORDER BY lpr.menu_id, lpr.button_id
                """,
                (username, *nav_ids),
            )
            buttons = cursor.fetchall()

            cursor.execute(
                f"""
                SELECT scope.nav_id,
                       SUM(scope.granted=1) AS granted_count,
                       COUNT(*) AS total_count,
                       GROUP_CONCAT(
                         CASE WHEN scope.granted=1
                           THEN scope.department_name END
                         ORDER BY scope.department_id SEPARATOR '、'
                       ) AS granted_departments
                FROM user_accounts ua
                JOIN user_roles ur ON ur.user_id=ua.user_id
                JOIN legacy_role_data_scope_grants scope
                  ON scope.role_id=ur.role_id
                WHERE ua.username=%s
                  AND scope.nav_id IN ({placeholders})
                GROUP BY scope.nav_id
                ORDER BY scope.nav_id
                """,
                (username, *nav_ids),
            )
            data_scopes = cursor.fetchall()
            return {
                "account": account,
                "buttons": buttons,
                "dataScopes": data_scopes,
            }
    finally:
        connection.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", required=True)
    parser.add_argument("--nav-id", action="append", type=int, required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            audit(args.username, args.nav_id),
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    main()

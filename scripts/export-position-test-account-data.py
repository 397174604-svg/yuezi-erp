#!/usr/bin/env python3
"""Export private source data for the position test-account workbook."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.mvp_api import connect


OUTPUT = ROOT / ".private" / "position-test-account-data.json"
TENANT_ID = 1
INTEGRATED_CAPABILITIES = (
    ("CUSTOMER.VIEW", "客户列表查询"),
    ("CUSTOMER.CREATE", "客户建档"),
    ("SALES.VIEW", "合同列表查询"),
    ("SALES.CREATE", "新增合同"),
    ("SALES.APPROVE", "合同审核"),
    ("FINANCE.VIEW", "收款列表查询"),
    ("FINANCE.CREATE", "新增收款"),
    ("FINANCE.APPROVE", "收款审核"),
    ("ROOM.VIEW", "房态及订房查询"),
    ("ROOM.CREATE", "新增订房"),
    ("ROOM.EXECUTE", "办理入住"),
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--login-status",
        default="未执行",
        choices=("未执行", "已通过", "失败"),
    )
    args = parser.parse_args()
    password = os.environ.get(
        "ERP_ROLE_TEST_ACCOUNT_INITIAL_PASSWORD", ""
    )
    if not password:
        raise SystemExit(
            "ERP_ROLE_TEST_ACCOUNT_INITIAL_PASSWORD is required."
        )
    connection = connect()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                  r.role_id,
                  r.legacy_role_id,
                  r.code AS role_code,
                  r.name AS role_name,
                  r.role_type,
                  ua.username,
                  ua.must_change_password,
                  GROUP_CONCAT(
                    DISTINCT CONCAT(s.name, '(ID:', s.store_id, ')')
                    ORDER BY s.store_id SEPARATOR '、'
                  ) AS stores
                FROM roles r
                JOIN user_roles ur
                  ON ur.role_id=r.role_id
                  AND ur.effective_from <= NOW()
                  AND (ur.effective_to IS NULL OR ur.effective_to > NOW())
                JOIN user_accounts ua
                  ON ua.user_id=ur.user_id
                  AND ua.status='ACTIVE'
                  AND ua.source_system='LOCAL_TEST'
                LEFT JOIN user_stores us ON us.user_id=ua.user_id
                LEFT JOIN stores s ON s.store_id=us.store_id
                WHERE r.tenant_id=%s
                  AND r.source_system='LEGACY_ERP'
                  AND r.legacy_role_id IS NOT NULL
                  AND r.status='ACTIVE'
                GROUP BY
                  r.role_id, r.legacy_role_id, r.code, r.name,
                  r.role_type, ua.username, ua.must_change_password
                ORDER BY r.legacy_role_id
                """,
                (TENANT_ID,),
            )
            rows = cursor.fetchall()
            cursor.execute(
                """
                SELECT rp.role_id, p.code
                FROM role_permissions rp
                JOIN permissions p
                  ON p.permission_id=rp.permission_id AND p.status='ACTIVE'
                JOIN roles r
                  ON r.role_id=rp.role_id AND r.status='ACTIVE'
                WHERE r.tenant_id=%s AND rp.effect='ALLOW'
                """,
                (TENANT_ID,),
            )
            permission_rows = cursor.fetchall()
    finally:
        connection.close()

    permissions_by_role = defaultdict(set)
    for row in permission_rows:
        permissions_by_role[row["role_id"]].add(row["code"])

    accounts = []
    for index, row in enumerate(rows, start=1):
        codes = permissions_by_role[row["role_id"]]
        capabilities = [
            label
            for code, label in INTEGRATED_CAPABILITIES
            if code in codes
        ]
        accounts.append(
            {
                "sequence": index,
                "legacyRoleId": int(row["legacy_role_id"]),
                "roleCode": row["role_code"],
                "roleName": row["role_name"],
                "roleType": (
                    "管理角色"
                    if row["role_type"] == "MANAGEMENT"
                    else "岗位角色"
                ),
                "username": row["username"],
                "initialPassword": password,
                "stores": row["stores"] or "未配置",
                "mustChangePassword": (
                    "是" if row["must_change_password"] else "否"
                ),
                "legacyWebPermissions": sum(
                    code.startswith("LEGACY.WEB.") for code in codes
                ),
                "legacyAppPermissions": sum(
                    code.startswith("LEGACY.APP.") for code in codes
                ),
                "integratedCapabilities": (
                    "、".join(capabilities)
                    if capabilities
                    else "仅验证登录、角色显示、原菜单授权与越权拦截"
                ),
                "loginTest": args.login_status,
                "manualTestResult": "未测试",
                "tester": "",
                "testDate": "",
                "remark": "专用验收账号，不关联真实员工",
            }
        )
    if len(accounts) != 28:
        raise SystemExit(
            f"Expected 28 dedicated role accounts, got {len(accounts)}."
        )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(
            {
                "generatedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "loginUrl": "http://127.0.0.1:9530/#/login",
                "accountCount": len(accounts),
                "accounts": accounts,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(OUTPUT)


if __name__ == "__main__":
    main()

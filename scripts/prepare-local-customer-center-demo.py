#!/usr/bin/env python3
"""Prepare the local-only customer center demo baseline.

This script is intentionally restricted to the loopback `yuezi` database. It
creates two clearly labelled test salespeople and soft-deletes only known local
test customer fixtures. Real customer records are never matched by the cleanup.
"""

from __future__ import annotations

import json
import os

import pymysql


CONFIRM_VALUE = "LOCAL_TEST_ONLY"
TEST_STAFF = (
    (1, "TEST-SALES-CENTER", "中心店测试业务员", "销售部"),
    (2, "TEST-SALES-HUANGHE", "黄河路测试业务员", "销售部"),
)
TEST_CUSTOMER_SOURCES = {
    "客户中心测试-王女士": "抖音咨询",
    "客户中心测试-张女士": "客户介绍",
    "客户中心测试-李女士": "自然上门",
}


def required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"{name} is required.")
    return value


def main() -> None:
    if os.environ.get("ERP_LOCAL_SEED_CONFIRM") != CONFIRM_VALUE:
        raise SystemExit(
            f"Set ERP_LOCAL_SEED_CONFIRM={CONFIRM_VALUE} for this local-only task."
        )
    host = required("ERP_DB_HOST")
    database = required("ERP_DB_NAME")
    if host not in {"127.0.0.1", "localhost", "::1"} or database != "yuezi":
        raise SystemExit("Refusing to modify a non-local or non-yuezi database.")

    connection = pymysql.connect(
        host=host,
        port=int(os.environ.get("ERP_DB_PORT", "3306")),
        user=required("ERP_DB_USER"),
        password=required("ERP_DB_PASSWORD"),
        database=database,
        charset="utf8mb4",
        autocommit=False,
        cursorclass=pymysql.cursors.DictCursor,
    )
    try:
        with connection.cursor() as cursor:
            for store_id, employee_no, name, department in TEST_STAFF:
                cursor.execute(
                    """
                    SELECT staff_id
                    FROM staff
                    WHERE tenant_id=1 AND employee_no=%s
                    ORDER BY staff_id LIMIT 1
                    """,
                    (employee_no,),
                )
                existing = cursor.fetchone()
                if existing:
                    cursor.execute(
                        """
                        UPDATE staff
                        SET store_id=%s,name=%s,department=%s,
                            employment_status='ACTIVE',status='ACTIVE',
                            role='销售顾问',position='业务员',
                            review_status='APPROVED',updated_at=NOW()
                        WHERE staff_id=%s
                        """,
                        (store_id, name, department, existing["staff_id"]),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO staff(
                          tenant_id,store_id,employee_no,name,gender,
                          employment_status,role,position,department,status,
                          source_file,review_status,created_at,updated_at
                        ) VALUES (
                          1,%s,%s,%s,'女','ACTIVE','销售顾问','业务员',%s,
                          'ACTIVE','LOCAL_TEST_SEED','APPROVED',NOW(),NOW()
                        )
                        """,
                        (store_id, employee_no, name, department),
                    )

            cursor.execute(
                """
                UPDATE customers
                SET deleted_at=NOW(),updated_at=NOW()
                WHERE tenant_id=1 AND deleted_at IS NULL
                  AND source IN ('LOCAL_P0_TEST','本地数据库测试')
                  AND (
                    name LIKE 'TEST_P0_%'
                    OR name LIKE '测试客户-%'
                    OR name LIKE '客户中心测试-%'
                  )
                """
            )
            archived = cursor.rowcount
            for customer_name, source in TEST_CUSTOMER_SOURCES.items():
                cursor.execute(
                    """
                    UPDATE customers
                    SET source=%s,updated_at=NOW()
                    WHERE tenant_id=1 AND deleted_at IS NULL AND name=%s
                    """,
                    (source, customer_name),
                )
            cursor.execute(
                """
                SELECT staff_id,store_id,employee_no,name
                FROM staff
                WHERE tenant_id=1
                  AND employee_no IN ('TEST-SALES-CENTER','TEST-SALES-HUANGHE')
                ORDER BY store_id
                """
            )
            staff = cursor.fetchall()
        connection.commit()
        print(
            json.dumps(
                {"archivedTestCustomers": archived, "testSalespeople": staff},
                ensure_ascii=False,
            )
        )
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    main()

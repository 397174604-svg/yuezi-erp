#!/usr/bin/env python3
"""Delete only rows marked by seed_local_demo_data.py from a local database."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".deps"))
import pymysql


CONFIRM_ENV = "ERP_LOCAL_DEMO_CONFIRM"
CONFIRM_VALUE = "LOCAL_TEST_ONLY"


def placeholders(values):
    return ",".join(["%s"] * len(values))


def main():
    host = os.environ.get("ERP_DB_HOST", "127.0.0.1")
    if urlparse(f"mysql://{host}").hostname not in {
        "127.0.0.1",
        "localhost",
        "::1",
    }:
        raise SystemExit("Demo cleanup is restricted to a loopback database.")
    if os.environ.get(CONFIRM_ENV) != CONFIRM_VALUE:
        raise SystemExit(
            f"Set {CONFIRM_ENV}={CONFIRM_VALUE} before cleanup."
        )
    connection = pymysql.connect(
        host=host,
        port=int(os.environ.get("ERP_DB_PORT", "3306")),
        user=os.environ["ERP_DB_USER"],
        password=os.environ["ERP_DB_PASSWORD"],
        database=os.environ.get("ERP_DB_NAME", "yuezi"),
        charset="utf8mb4",
        autocommit=False,
    )
    counts = {}
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT coupon_id FROM sales_coupon_extensions
                WHERE remark LIKE 'LOCAL_DEMO_SEED%'
                """
            )
            coupon_ids = [int(row[0]) for row in cursor.fetchall()]
            cursor.execute(
                """
                SELECT tpl_id FROM sales_coupon_template_extensions
                WHERE remark LIKE 'LOCAL_DEMO_SEED%'
                """
            )
            template_ids = [int(row[0]) for row in cursor.fetchall()]
            cursor.execute(
                """
                SELECT customer_id FROM customers
                WHERE remark LIKE 'LOCAL_DEMO_SEED%'
                """
            )
            customer_ids = [int(row[0]) for row in cursor.fetchall()]
            contract_ids = []
            if customer_ids:
                cursor.execute(
                    f"""
                    SELECT contract_id FROM contracts
                    WHERE customer_id IN ({placeholders(customer_ids)})
                      AND (
                        note='LOCAL_DEMO_SEED'
                        OR package_name='基础套餐（本地测试）'
                      )
                    """,
                    customer_ids,
                )
                contract_ids = [int(row[0]) for row in cursor.fetchall()]

            if coupon_ids:
                keys = [str(value) for value in coupon_ids]
                cursor.execute(
                    f"""
                    DELETE FROM sales_operation_records
                    WHERE resource_key='discounts'
                      AND record_key IN ({placeholders(keys)})
                    """,
                    keys,
                )
                cursor.execute(
                    f"""
                    DELETE FROM sales_coupon_extensions
                    WHERE coupon_id IN ({placeholders(coupon_ids)})
                    """,
                    coupon_ids,
                )
                counts["coupons"] = cursor.execute(
                    f"""
                    DELETE FROM coupons
                    WHERE coupon_id IN ({placeholders(coupon_ids)})
                    """,
                    coupon_ids,
                )
            if template_ids:
                keys = [str(value) for value in template_ids]
                cursor.execute(
                    f"""
                    DELETE FROM sales_operation_records
                    WHERE resource_key='coupons'
                      AND record_key IN ({placeholders(keys)})
                    """,
                    keys,
                )
                cursor.execute(
                    f"""
                    DELETE FROM sales_coupon_template_extensions
                    WHERE tpl_id IN ({placeholders(template_ids)})
                    """,
                    template_ids,
                )
                counts["couponTemplates"] = cursor.execute(
                    f"""
                    DELETE FROM coupon_templates
                    WHERE tpl_id IN ({placeholders(template_ids)})
                    """,
                    template_ids,
                )
            if contract_ids:
                cursor.execute(
                    f"""
                    DELETE FROM mvp_audit_events
                    WHERE aggregate_type='CONTRACT'
                      AND aggregate_id IN ({placeholders(contract_ids)})
                    """,
                    contract_ids,
                )
                counts["contracts"] = cursor.execute(
                    f"""
                    DELETE FROM contracts
                    WHERE contract_id IN ({placeholders(contract_ids)})
                    """,
                    contract_ids,
                )
            if customer_ids:
                cursor.execute(
                    f"""
                    DELETE FROM mvp_audit_events
                    WHERE aggregate_type='CUSTOMER'
                      AND aggregate_id IN ({placeholders(customer_ids)})
                    """,
                    customer_ids,
                )
                counts["customers"] = cursor.execute(
                    f"""
                    DELETE FROM customers
                    WHERE customer_id IN ({placeholders(customer_ids)})
                    """,
                    customer_ids,
                )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    print(json.dumps({"status": "cleaned", **counts}, ensure_ascii=False))


if __name__ == "__main__":
    main()

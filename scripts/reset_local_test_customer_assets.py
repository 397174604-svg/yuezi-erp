#!/usr/bin/env python3
"""Archive local test customers and member assets, then seed four usable examples.

This script deliberately does *not* touch stores, rooms, room types, packages,
bookings, admissions, or any customer that is not positively identified as a
local test record.  It writes a JSON backup before changing anything.

Run only against the local database:
  $env:ERP_LOCAL_CUSTOMER_RESET_CONFIRM='RESET_TEST_CUSTOMERS_ONLY'
  python scripts/reset_local_test_customer_assets.py --apply
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pymysql


CONFIRM_VALUE = "RESET_TEST_CUSTOMERS_ONLY"
LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}
TEST_SOURCES = {"本地数据库测试", "LOCAL_P0_TEST"}
TEST_NAME_PREFIXES = ("TEST_P0_", "测试客户-", "客户中心测试-")
TEST_REMARK_PREFIXES = ("LOCAL_DEMO_SEED", "LOCAL_TEST_SEED")
# These are the manually entered local acceptance examples recorded on 2026-07-31.
LEGACY_TEST_NAMES = {"111", "1111", "222", "48948998"}

SAMPLES = (
    {
        "store_id": 1,
        "name": "李四",
        "phone": "18800001001",
        "source": "客户介绍",
        "status": "意向A",
        "card_type": "次卡",
        "amount": Decimal("0"),
        "total_count": 12,
        "remark": "LOCAL_TEST_SEED: 客户与次卡验收样本",
    },
    {
        "store_id": 1,
        "name": "王五",
        "phone": "18800001002",
        "source": "抖音咨询",
        "status": "意向B",
        "card_type": "储值卡",
        "amount": Decimal("3000"),
        "total_count": 0,
        "remark": "LOCAL_TEST_SEED: 客户与储值卡验收样本",
    },
    {
        "store_id": 2,
        "name": "赵六",
        "phone": "18800002001",
        "source": "自然上门",
        "status": "意向A",
        "card_type": "套餐卡",
        "amount": Decimal("0"),
        "total_count": 28,
        "remark": "LOCAL_TEST_SEED: 黄河路客户与套餐卡验收样本",
    },
    {
        "store_id": 2,
        "name": "陈七",
        "phone": "18800002002",
        "source": "老客户转介绍",
        "status": "意向B",
        "card_type": None,
        "amount": Decimal("0"),
        "total_count": 0,
        "remark": "LOCAL_TEST_SEED: 黄河路普通客户验收样本",
    },
)


def db_connect() -> pymysql.connections.Connection:
    missing = [
        key
        for key in ("ERP_DB_HOST", "ERP_DB_PORT", "ERP_DB_NAME", "ERP_DB_USER", "ERP_DB_PASSWORD")
        if not os.environ.get(key)
    ]
    if missing:
        raise RuntimeError(f"缺少数据库环境变量：{', '.join(missing)}")
    host = os.environ["ERP_DB_HOST"].strip().lower()
    if host not in LOCAL_HOSTS:
        raise RuntimeError(f"安全退出：仅允许本机数据库，当前 host={host!r}")
    return pymysql.connect(
        host=host,
        port=int(os.environ["ERP_DB_PORT"]),
        user=os.environ["ERP_DB_USER"],
        password=os.environ["ERP_DB_PASSWORD"],
        database=os.environ["ERP_DB_NAME"],
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )


def json_default(value: Any) -> str:
    if isinstance(value, (datetime,)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return str(value)


def is_test_customer(row: dict[str, Any]) -> bool:
    name = str(row.get("name") or "").strip()
    source = str(row.get("source") or "").strip()
    remark = str(row.get("remark") or "").strip()
    return (
        source in TEST_SOURCES
        or name in LEGACY_TEST_NAMES
        or name.startswith(TEST_NAME_PREFIXES)
        or remark.startswith(TEST_REMARK_PREFIXES)
    )


def backup_rows(cursor: pymysql.cursors.Cursor, customer_ids: list[int]) -> dict[str, Any]:
    if not customer_ids:
        return {"customers": [], "contracts": [], "cards": [], "accounts": [], "transactions": []}
    holders = ",".join(["%s"] * len(customer_ids))
    payload: dict[str, Any] = {}
    for label, table in (
        ("customers", "customers"),
        ("contracts", "contracts"),
        ("cards", "member_asset_cards"),
        ("accounts", "member_asset_accounts"),
        ("transactions", "member_asset_transactions"),
    ):
        cursor.execute(f"SELECT * FROM {table} WHERE customer_id IN ({holders})", customer_ids)
        payload[label] = cursor.fetchall()
    return payload


def write_backup(payload: dict[str, Any], backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = backup_dir / f"local-test-customer-assets-{stamp}.json"
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=json_default), encoding="utf-8")
    return target


def fetch_user_and_staff(cursor: pymysql.cursors.Cursor, tenant_id: int, store_id: int) -> tuple[int, int | None]:
    cursor.execute(
        "SELECT user_id FROM user_accounts WHERE tenant_id=%s AND status='ACTIVE' ORDER BY user_id LIMIT 1",
        (tenant_id,),
    )
    user = cursor.fetchone()
    if not user:
        raise RuntimeError("未找到可用本地用户，无法创建可审计的测试客户")
    cursor.execute(
        """
        SELECT staff_id FROM staff
        WHERE tenant_id=%s AND store_id=%s AND employment_status='ACTIVE'
        ORDER BY staff_id LIMIT 1
        """,
        (tenant_id, store_id),
    )
    staff = cursor.fetchone()
    return int(user["user_id"]), int(staff["staff_id"]) if staff else None


def seed_samples(cursor: pymysql.cursors.Cursor, tenant_id: int) -> list[dict[str, Any]]:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    seeded: list[dict[str, Any]] = []
    for index, sample in enumerate(SAMPLES, start=1):
        creator_id, staff_id = fetch_user_and_staff(cursor, tenant_id, sample["store_id"])
        customer_no = f"LOCAL-{datetime.now():%Y%m%d}-{index:02d}"
        cursor.execute(
            """
            INSERT INTO customers(
              customer_no, tenant_id, store_id, sales_staff_id, name, phone,
              source, status, level, remark, visit_count, created_at, updated_at,
              created_by, created_by_user_id, updated_by
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,0,%s,%s,%s,%s,%s)
            """,
            (
                customer_no, tenant_id, sample["store_id"], staff_id, sample["name"], sample["phone"],
                sample["source"], sample["status"], "普通", sample["remark"], now, now,
                "本地验收", creator_id, "本地验收",
            ),
        )
        customer_id = int(cursor.lastrowid)
        card_id = None
        if sample["card_type"]:
            card_no = f"CARD-LOCAL-{datetime.now():%Y%m%d%H%M%S}-{index:02d}"
            valid_to = (datetime.now() + timedelta(days=365)).date().isoformat()
            is_value_card = sample["card_type"] == "储值卡"
            cursor.execute(
                """
                INSERT INTO member_asset_cards(
                  tenant_id, customer_id, issue_store_id, card_no, card_name, card_type,
                  issue_amount, balance, total_count, remaining_count, valid_to,
                  created_by_user_id
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    tenant_id, customer_id, sample["store_id"], card_no, sample["card_type"], sample["card_type"],
                    sample["amount"], sample["amount"] if is_value_card else Decimal("0"),
                    sample["total_count"], sample["total_count"], valid_to, creator_id,
                ),
            )
            card_id = int(cursor.lastrowid)
            cursor.execute(
                """
                INSERT INTO member_asset_accounts(tenant_id, customer_id, account_no)
                VALUES (%s,%s,%s)
                """,
                (tenant_id, customer_id, f"ACC-{tenant_id}-{customer_id}"),
            )
            cursor.execute(
                """
                INSERT INTO member_asset_transactions(
                  tenant_id, store_id, customer_id, card_id, transaction_no,
                  transaction_type, amount, count_delta, balance_after,
                  remaining_count_after, operator_user_id, remark
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    tenant_id, sample["store_id"], customer_id, card_id,
                    f"AST-LOCAL-{datetime.now():%Y%m%d%H%M%S}-{index:02d}", "发卡",
                    sample["amount"], sample["total_count"],
                    sample["amount"] if is_value_card else Decimal("0"), sample["total_count"], creator_id,
                    sample["remark"],
                ),
            )
        seeded.append({"customer_id": customer_id, "name": sample["name"], "store_id": sample["store_id"], "card_id": card_id})
    return seeded


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="执行归档与测试数据写入；默认仅预览")
    parser.add_argument("--backup-dir", default=r"D:\QideYueziERP\backups\local-test-customer-reset")
    args = parser.parse_args()
    if args.apply and os.environ.get("ERP_LOCAL_CUSTOMER_RESET_CONFIRM") != CONFIRM_VALUE:
        raise RuntimeError(f"拒绝执行：请设置 ERP_LOCAL_CUSTOMER_RESET_CONFIRM={CONFIRM_VALUE}")

    connection = db_connect()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT customer_id,name,source,remark FROM customers WHERE tenant_id=1 AND deleted_at IS NULL ORDER BY customer_id"
            )
            candidates = [row for row in cursor.fetchall() if is_test_customer(row)]
            ids = [int(row["customer_id"]) for row in candidates]
            print(json.dumps({"matched_test_customers": candidates, "count": len(ids)}, ensure_ascii=False, default=json_default))
            if not args.apply:
                print("预览完成：未修改数据库。使用 --apply 和确认环境变量才会执行。")
                return 0

            backup_payload = backup_rows(cursor, ids)
            backup_file = write_backup(backup_payload, Path(args.backup_dir))
            stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if ids:
                holders = ",".join(["%s"] * len(ids))
                # Preserve ledger/audit rows.  Cards and accounts become inactive; customers/contracts are soft deleted.
                cursor.execute(
                    f"UPDATE contracts SET deleted_at=%s WHERE customer_id IN ({holders}) AND deleted_at IS NULL",
                    [stamp, *ids],
                )
                cursor.execute(
                    f"UPDATE member_asset_cards SET status='已注销', deleted_at=%s, updated_at=%s WHERE customer_id IN ({holders}) AND deleted_at IS NULL",
                    [stamp, stamp, *ids],
                )
                cursor.execute(
                    f"UPDATE member_asset_accounts SET status='已注销', balance=0, frozen_amount=0, points=0, updated_at=%s WHERE customer_id IN ({holders})",
                    [stamp, *ids],
                )
                cursor.execute(
                    f"UPDATE customers SET deleted_at=%s, updated_at=%s, updated_by='本地测试归档' WHERE customer_id IN ({holders})",
                    [stamp, stamp, *ids],
                )

            seeded = seed_samples(cursor, tenant_id=1)
            connection.commit()
            print(json.dumps({"backup": str(backup_file), "archived_customer_ids": ids, "seeded": seeded}, ensure_ascii=False))
            return 0
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # never reveal connection secrets
        print(f"失败：{exc}", file=sys.stderr)
        raise SystemExit(1)

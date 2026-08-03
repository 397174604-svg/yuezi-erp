#!/usr/bin/env python3
"""Safely restore the two confirmed room inventories into MySQL.

The canonical source is mock/client-confirmed-data.js.  The script never
changes SmartRoomAllocation.vue or room-workbench/index.vue and never creates
bookings.  Existing room status, customer assignment, price and booking rows
are preserved.  An unreferenced legacy room may be renumbered and reused for a
missing confirmed room; rooms and bookings are never deleted or truncated.
If an extra legacy room has customer or booking references, apply aborts.

Examples:
  python scripts/restore_confirmed_room_inventory.py source-check
  python scripts/restore_confirmed_room_inventory.py preflight
  python scripts/restore_confirmed_room_inventory.py apply
  python scripts/restore_confirmed_room_inventory.py validate
  python scripts/restore_confirmed_room_inventory.py validate \
    --api-base http://127.0.0.1:3000 --api-user admin

Database variables are the same as the ERP API:
ERP_DB_HOST, ERP_DB_PORT, ERP_DB_USER, ERP_DB_PASSWORD and ERP_DB_NAME.
The API password is read from ERP_ACCEPTANCE_PASSWORD unless --api-password
is supplied.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_FILE = ROOT / "mock" / "client-confirmed-data.js"
SOURCE_MARKER = "mock/client-confirmed-data.js（甲方已确认房间资料，2026-07-30）"
EXPECTED = {
    "center": {
        "count": 36,
        "floors": {"2": 11, "3": 10, "4": 9, "5": 6},
        "types": {
            "大床房": 6,
            "小套房": 2,
            "特价房": 2,
            "套房": 24,
            "VIP302": 1,
            "VIP512": 1,
        },
    },
    "yellow": {
        "count": 31,
        "floors": {"3": 8, "4": 11, "5": 11, "6": 1},
        "types": {
            "一房一厅": 23,
            "大床房": 6,
            "总统套房": 1,
            "女王套房": 1,
        },
    },
}

CENTER_TYPE_CODES = {
    "大床房": "CENTER_KING",
    "小套房": "CENTER_SMALL_SUITE",
    "特价房": "CENTER_SPECIAL",
    "套房": "CENTER_SUITE",
    "VIP302": "CENTER_VIP302",
    "VIP512": "CENTER_VIP512",
}


class RestoreError(RuntimeError):
    pass


def json_default(value: Any):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    raise TypeError(type(value).__name__)


def load_confirmed_source() -> dict:
    if not SOURCE_FILE.exists():
        raise RestoreError(f"confirmed source missing: {SOURCE_FILE}")
    js = (
        "const d=require(process.argv[1]);"
        "process.stdout.write(JSON.stringify({"
        "center:d.confirmedCenterRoomSlots,"
        "yellow:d.confirmedYellowRiverRoomSlots,"
        "packages:d.confirmedPackageCatalog.filter(x=>x.store_id===2),"
        "evidence:d.roomInventoryEvidence}));"
    )
    try:
        result = subprocess.run(
            ["node", "-e", js, str(SOURCE_FILE)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", "") or str(exc)
        raise RestoreError(f"failed to load confirmed JS source: {detail}") from exc
    return json.loads(result.stdout)


def assert_source(data: dict) -> dict:
    summary = {}
    for key in ("center", "yellow"):
        rows = data.get(key) or []
        room_numbers = [str(row.get("room_no") or "") for row in rows]
        if len(room_numbers) != len(set(room_numbers)):
            duplicates = sorted(
                room for room, count in Counter(room_numbers).items() if count > 1
            )
            raise RestoreError(f"{key} source has duplicate rooms: {duplicates}")
        floors = Counter(str(row.get("floor")) for row in rows)
        types = Counter(str(row.get("room_type")) for row in rows)
        expected = EXPECTED[key]
        if len(rows) != expected["count"]:
            raise RestoreError(
                f"{key} room count {len(rows)} != {expected['count']}"
            )
        if dict(floors) != expected["floors"]:
            raise RestoreError(
                f"{key} floor counts {dict(floors)} != {expected['floors']}"
            )
        if dict(types) != expected["types"]:
            raise RestoreError(
                f"{key} type counts {dict(types)} != {expected['types']}"
            )
        summary[key] = {
            "count": len(rows),
            "floors": dict(sorted(floors.items())),
            "types": dict(sorted(types.items())),
        }

    packages = data.get("packages") or []
    package_codes = {str(row.get("basePackageCode")) for row in packages}
    expected_codes = {
        "HH-BASE",
        "HH-BASE-721",
        "HH-REPAIR",
        "HH-REPAIR-721",
        "HH-RECOVERY",
        "HH-QUEEN",
        "HH-PRESIDENT",
    }
    if package_codes != expected_codes or len(packages) != 28:
        raise RestoreError(
            f"yellow package source mismatch: {len(packages)} rows, "
            f"codes={sorted(package_codes)}"
        )
    summary["yellowPackagePriceRows"] = len(packages)
    summary["yellowPackageCodes"] = sorted(package_codes)
    return summary


def db_config() -> dict:
    password = os.environ.get("ERP_DB_PASSWORD", "")
    if not password:
        raise RestoreError("ERP_DB_PASSWORD is required for database commands")
    return {
        "host": os.environ.get("ERP_DB_HOST", "127.0.0.1"),
        "port": int(os.environ.get("ERP_DB_PORT", "3306")),
        "user": os.environ.get("ERP_DB_USER", "root"),
        "password": password,
        "database": os.environ.get("ERP_DB_NAME", "yuezi"),
        "charset": "utf8mb4",
        "autocommit": False,
    }


def connect():
    try:
        import pymysql
        from pymysql.cursors import DictCursor
    except ImportError as exc:
        raise RestoreError(
            "PyMySQL is required: install it in the ERP API Python environment"
        ) from exc
    config = db_config()
    config["cursorclass"] = DictCursor
    return pymysql.connect(**config)


def fetch_all(connection, sql: str, params=()) -> list[dict]:
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        return list(cursor.fetchall())


def fetch_one(connection, sql: str, params=()) -> dict | None:
    rows = fetch_all(connection, sql, params)
    return rows[0] if rows else None


def table_exists(connection, table: str) -> bool:
    row = fetch_one(
        connection,
        "SELECT COUNT(*) AS total FROM information_schema.tables "
        "WHERE table_schema=DATABASE() AND table_name=%s",
        (table,),
    )
    return bool(row and int(row["total"]) == 1)


def resolve_stores(connection, tenant_id: int) -> dict:
    rows = fetch_all(
        connection,
        "SELECT store_id,name FROM stores WHERE tenant_id=%s ORDER BY store_id",
        (tenant_id,),
    )
    center = [row for row in rows if "中心" in str(row["name"])]
    yellow = [row for row in rows if "黄河路" in str(row["name"])]
    if len(center) != 1 or len(yellow) != 1:
        raise RestoreError(
            "cannot uniquely resolve center/yellow stores: "
            + json.dumps(rows, ensure_ascii=False, default=json_default)
        )
    return {"center": center[0], "yellow": yellow[0]}


def schema_preflight(connection):
    required = [
        "tenants",
        "stores",
        "rooms",
        "room_bookings",
        "room_types",
        "package_products",
        "package_versions",
        "package_price_rules",
        "user_accounts",
    ]
    missing = [table for table in required if not table_exists(connection, table)]
    if missing:
        raise RestoreError(
            "required schema is missing; run migrations through V20260728_019 first: "
            + ", ".join(missing)
        )


def existing_snapshot(connection, tenant_id: int, stores: dict) -> dict:
    store_ids = [stores["center"]["store_id"], stores["yellow"]["store_id"]]
    room_rows = fetch_all(
        connection,
        """
        SELECT r.*,s.name AS store_name,rt.type_code,rt.name AS type_name,
               (SELECT COUNT(*) FROM room_bookings rb
                WHERE rb.tenant_id=r.tenant_id AND rb.room_id=r.room_id
                  AND rb.deleted_at IS NULL) AS booking_count
        FROM rooms r
        JOIN stores s ON s.store_id=r.store_id
        LEFT JOIN room_types rt ON rt.room_type_id=r.room_type_id
        WHERE r.tenant_id=%s AND r.store_id IN (%s,%s)
        ORDER BY r.store_id,r.floor,r.layout_order,r.room_no,r.room_id
        """,
        (tenant_id, *store_ids),
    )
    room_types = fetch_all(
        connection,
        "SELECT * FROM room_types WHERE tenant_id=%s ORDER BY room_type_id",
        (tenant_id,),
    )
    packages = fetch_all(
        connection,
        """
        SELECT pp.*,pv.package_version_id,pv.version_no,pv.version_status,
               pr.price_rule_id,pr.store_id,pr.room_type_id,pr.stay_days,
               pr.reference_amount,pr.status AS price_status
        FROM package_products pp
        LEFT JOIN package_versions pv ON pv.package_id=pp.package_id
        LEFT JOIN package_price_rules pr
          ON pr.package_version_id=pv.package_version_id
        WHERE pp.tenant_id=%s AND (
          pp.package_code LIKE 'HH-%%' OR pr.store_id=%s OR pr.store_id=%s
        )
        ORDER BY pp.package_id,pv.package_version_id,pr.price_rule_id
        """,
        (tenant_id, *store_ids),
    )
    return {
        "capturedAt": datetime.now().isoformat(timespec="seconds"),
        "tenantId": tenant_id,
        "stores": stores,
        "rooms": room_rows,
        "roomTypes": room_types,
        "packages": packages,
    }


def preflight_report(connection, data: dict, tenant_id: int) -> dict:
    schema_preflight(connection)
    stores = resolve_stores(connection, tenant_id)
    snapshot = existing_snapshot(connection, tenant_id, stores)
    report = {"stores": stores, "current": {}, "blockingExtras": []}
    for key in ("center", "yellow"):
        store_id = stores[key]["store_id"]
        active = [
            row
            for row in snapshot["rooms"]
            if row["store_id"] == store_id and row.get("deleted_at") is None
        ]
        source_numbers = {str(row["room_no"]) for row in data[key]}
        extras = [row for row in active if str(row["room_no"]) not in source_numbers]
        blocking = [
            row
            for row in extras
            if int(row.get("booking_count") or 0) > 0 or row.get("customer_id")
        ]
        report["current"][key] = {
            "activeCount": len(active),
            "sourceCount": len(data[key]),
            "extraUnreferenced": [row["room_no"] for row in extras if row not in blocking],
            "extraWithBusinessReferences": [row["room_no"] for row in blocking],
        }
        report["blockingExtras"].extend(
            {"store": key, "room": row["room_no"]} for row in blocking
        )
    return report


def type_spec(store_key: str, room: dict) -> dict:
    room_type = str(room["room_type"])
    style = str(room.get("room_style") or room_type)
    if store_key == "center":
        code = CENTER_TYPE_CODES[room_type]
        bedrooms = 1
        living = 0 if room_type in {"大床房", "特价房"} else 1
        return {
            "code": code,
            "name": room_type,
            "layout": style,
            "bedrooms": bedrooms,
            "living": living,
            "bed": "大床" if room_type == "大床房" else None,
            "package": "未绑定套餐",
        }
    if room_type == "一房一厅":
        return {"code": "YH_REPAIR_1B1L", "name": room_type, "layout": style, "bedrooms": 1, "living": 1, "bed": None, "package": "修复/修养套餐"}
    if room_type == "大床房":
        code = "YH_BASIC_KING" if str(room["floor"]) == "4" else "YH_BASIC_PACKAGE_KING"
        return {"code": code, "name": room_type, "layout": style, "bedrooms": 1, "living": 0, "bed": "大床", "package": "基础套餐"}
    if room_type == "总统套房":
        return {"code": "YH_PRESIDENT_3B3L", "name": room_type, "layout": style, "bedrooms": 3, "living": 3, "bed": None, "package": "总统套餐"}
    if room_type == "女王套房":
        return {"code": "YH_QUEEN_2B2L", "name": room_type, "layout": style, "bedrooms": 2, "living": 2, "bed": None, "package": "女王套餐"}
    raise RestoreError(f"unknown room type: {store_key}/{room_type}")


def ensure_backup_tables(connection):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS room_inventory_restore_runs (
              run_id BIGINT NOT NULL AUTO_INCREMENT,
              tenant_id BIGINT NOT NULL,
              source_marker VARCHAR(255) NOT NULL,
              status VARCHAR(32) NOT NULL,
              snapshot_json LONGTEXT NOT NULL,
              result_json LONGTEXT NULL,
              created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
              completed_at DATETIME NULL,
              PRIMARY KEY (run_id),
              KEY ix_room_restore_tenant (tenant_id,created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )
    connection.commit()


def backup_snapshot(connection, snapshot: dict, backup_dir: Path) -> int:
    ensure_backup_tables(connection)
    payload = json.dumps(snapshot, ensure_ascii=False, default=json_default)
    backup_dir.mkdir(parents=True, exist_ok=True)
    file_path = backup_dir / f"room-inventory-{datetime.now():%Y%m%d-%H%M%S}.json"
    file_path.write_text(payload, encoding="utf-8")
    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO room_inventory_restore_runs(tenant_id,source_marker,status,snapshot_json) VALUES (%s,%s,'BACKUP_CREATED',%s)",
            (snapshot["tenantId"], SOURCE_MARKER, payload),
        )
        run_id = int(cursor.lastrowid)
    connection.commit()
    print(f"backup file: {file_path}")
    print(f"database backup run_id: {run_id}")
    return run_id


def upsert_room_type(connection, tenant_id: int, spec: dict, sort_order: int) -> int:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO room_types(
              tenant_id,type_code,name,layout_name,bedrooms,living_rooms,
              bed_type,package_name,status,sort_order
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'启用',%s)
            ON DUPLICATE KEY UPDATE
              name=VALUES(name),layout_name=VALUES(layout_name),
              bedrooms=VALUES(bedrooms),living_rooms=VALUES(living_rooms),
              bed_type=VALUES(bed_type),package_name=VALUES(package_name),
              status='启用',sort_order=VALUES(sort_order)
            """,
            (
                tenant_id,
                spec["code"],
                spec["name"],
                spec["layout"],
                spec["bedrooms"],
                spec["living"],
                spec["bed"],
                spec["package"],
                sort_order,
            ),
        )
    row = fetch_one(
        connection,
        "SELECT room_type_id FROM room_types WHERE tenant_id=%s AND type_code=%s",
        (tenant_id, spec["code"]),
    )
    if not row:
        raise RestoreError(f"room type upsert failed: {spec['code']}")
    return int(row["room_type_id"])


def apply_rooms(connection, data: dict, tenant_id: int, stores: dict):
    room_type_ids = {}
    sort_order = 10
    for store_key in ("center", "yellow"):
        for room in data[store_key]:
            spec = type_spec(store_key, room)
            if spec["code"] not in room_type_ids:
                room_type_ids[spec["code"]] = upsert_room_type(
                    connection, tenant_id, spec, sort_order
                )
                sort_order += 10

    for store_key in ("center", "yellow"):
        store_id = int(stores[store_key]["store_id"])
        source_numbers = {str(row["room_no"]) for row in data[store_key]}
        existing = fetch_all(
            connection,
            "SELECT room_id,room_no,customer_id,deleted_at FROM rooms WHERE tenant_id=%s AND store_id=%s ORDER BY room_id",
            (tenant_id, store_id),
        )
        by_number = defaultdict(list)
        for row in existing:
            by_number[str(row["room_no"])].append(row)
        for room_no, rows in by_number.items():
            active = [row for row in rows if row.get("deleted_at") is None]
            if len(active) > 1:
                raise RestoreError(
                    f"duplicate active room rows must be resolved first: {stores[store_key]['name']}/{room_no}"
                )

        extra_rows = fetch_all(
            connection,
            """
            SELECT r.room_id,r.room_no,r.customer_id,
                   (SELECT COUNT(*) FROM room_bookings rb
                    WHERE rb.tenant_id=r.tenant_id AND rb.room_id=r.room_id
                      AND rb.deleted_at IS NULL) AS booking_count
            FROM rooms r
            WHERE r.tenant_id=%s AND r.store_id=%s AND r.deleted_at IS NULL
            ORDER BY r.room_id
            """,
            (tenant_id, store_id),
        )
        extra_rows = [
            row for row in extra_rows
            if str(row["room_no"]) not in source_numbers
        ]
        blocking = [
            row for row in extra_rows
            if row.get("customer_id") or int(row.get("booking_count") or 0) > 0
        ]
        if blocking:
            raise RestoreError(
                "extra rooms have customer/booking references; transaction aborted: "
                + json.dumps(blocking, ensure_ascii=False, default=json_default)
            )
        reusable_extras = [row for row in extra_rows if row not in blocking]

        with connection.cursor() as cursor:
            for layout_order, room in enumerate(data[store_key], start=1):
                room_no = str(room["room_no"])
                candidates = by_number.get(room_no, [])
                active = [row for row in candidates if row.get("deleted_at") is None]
                target = active[0] if active else (candidates[-1] if candidates else None)
                renumbered = False
                if target is None and reusable_extras:
                    target = reusable_extras.pop(0)
                    renumbered = True
                spec = type_spec(store_key, room)
                note_parts = [
                    str(room.get("classification_note") or "").strip(),
                    f"room_style={room.get('room_style') or room['room_type']}",
                    f"source={SOURCE_MARKER}",
                ]
                note = "；".join(part for part in note_parts if part)
                values = (
                    room["room_type"],
                    room_type_ids[spec["code"]],
                    str(room["floor"]),
                    room.get("direction") or "待确认",
                    layout_order,
                    note,
                )
                if target:
                    cursor.execute(
                        """
                        UPDATE rooms SET room_no=%s,room_type=%s,room_type_id=%s,floor=%s,
                          direction=%s,layout_order=%s,note=%s,deleted_at=NULL
                        WHERE room_id=%s AND tenant_id=%s
                        """,
                        (room_no, *values, target["room_id"], tenant_id),
                    )
                    if renumbered:
                        print(
                            f"reused unreferenced room_id={target['room_id']}: "
                            f"{target['room_no']} -> {room_no}"
                        )
                else:
                    cursor.execute(
                        """
                        INSERT INTO rooms(
                          tenant_id,store_id,room_no,room_type,room_type_id,
                          floor,direction,layout_order,price,status,note,created_at
                        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,0,'空闲',%s,NOW())
                        """,
                        (tenant_id, store_id, room_no, *values),
                    )

            if reusable_extras:
                raise RestoreError(
                    "unreferenced extra rooms remain after confirmed inventory was restored; "
                    "rooms are never deleted automatically: "
                    + json.dumps(
                        reusable_extras, ensure_ascii=False, default=json_default
                    )
                )
    return room_type_ids


def room_type_codes_for_package(code: str) -> list[str]:
    if code in {"HH-BASE", "HH-BASE-721"}:
        return ["YH_BASIC_KING", "YH_BASIC_PACKAGE_KING"]
    if code in {"HH-REPAIR", "HH-REPAIR-721", "HH-RECOVERY"}:
        return ["YH_REPAIR_1B1L"]
    if code == "HH-QUEEN":
        return ["YH_QUEEN_2B2L"]
    if code == "HH-PRESIDENT":
        return ["YH_PRESIDENT_3B3L"]
    raise RestoreError(f"unknown yellow package code: {code}")


def apply_yellow_packages(
    connection, data: dict, tenant_id: int, stores: dict, room_type_ids: dict
):
    admin = fetch_one(
        connection,
        "SELECT user_id FROM user_accounts WHERE tenant_id=%s AND username='admin' ORDER BY user_id LIMIT 1",
        (tenant_id,),
    )
    if not admin:
        raise RestoreError("admin user is required to attribute confirmed package records")
    user_id = int(admin["user_id"])
    store_id = int(stores["yellow"]["store_id"])
    grouped = defaultdict(list)
    for row in data["packages"]:
        grouped[str(row["basePackageCode"])].append(row)

    for sort_order, (code, rows) in enumerate(sorted(grouped.items()), start=1):
        name = str(rows[0]["basePackageName"])
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO package_products(
                  tenant_id,package_code,package_name,package_category,status,
                  sort_order,note,created_by_user_id
                ) VALUES (%s,%s,%s,'月子套餐','ACTIVE',%s,%s,%s)
                ON DUPLICATE KEY UPDATE package_name=VALUES(package_name),
                  status='ACTIVE',sort_order=VALUES(sort_order),note=VALUES(note)
                """,
                (tenant_id, code, name, sort_order, SOURCE_MARKER, user_id),
            )
        product = fetch_one(
            connection,
            "SELECT package_id FROM package_products WHERE tenant_id=%s AND package_code=%s AND deleted_at IS NULL",
            (tenant_id, code),
        )
        if not product:
            raise RestoreError(f"package upsert failed: {code}")
        package_id = int(product["package_id"])
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO package_versions(
                  tenant_id,package_id,version_no,effective_from,
                  version_status,source_type,evidence_note,published_at,
                  published_by_user_id,created_by_user_id
                ) VALUES (%s,%s,'2026-07-confirmed','2026-07-30','ACTIVE',
                  'CLIENT_CONFIRMED',%s,NOW(),%s,%s)
                ON DUPLICATE KEY UPDATE version_status='ACTIVE',
                  source_type='CLIENT_CONFIRMED',evidence_note=VALUES(evidence_note),
                  published_at=COALESCE(published_at,NOW()),
                  published_by_user_id=VALUES(published_by_user_id)
                """,
                (tenant_id, package_id, SOURCE_MARKER, user_id, user_id),
            )
        version = fetch_one(
            connection,
            "SELECT package_version_id FROM package_versions WHERE package_id=%s AND version_no='2026-07-confirmed'",
            (package_id,),
        )
        version_id = int(version["package_version_id"])
        for price in rows:
            for type_code in room_type_codes_for_package(code):
                room_type_id = int(room_type_ids[type_code])
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO package_price_rules(
                          tenant_id,package_version_id,store_id,room_type_id,
                          stay_days,reference_amount,currency_code,effective_from,status
                        ) VALUES (%s,%s,%s,%s,%s,%s,'CNY','2026-07-30','ACTIVE')
                        ON DUPLICATE KEY UPDATE reference_amount=VALUES(reference_amount),
                          status='ACTIVE',effective_to=NULL
                        """,
                        (
                            tenant_id,
                            version_id,
                            store_id,
                            room_type_id,
                            int(price["days"]),
                            Decimal(str(price["referencePrice"])),
                        ),
                    )


def validate_database(connection, data: dict, tenant_id: int) -> dict:
    schema_preflight(connection)
    stores = resolve_stores(connection, tenant_id)
    result = {
        "stores": {},
        "centerActivePackageRules": 0,
        "centerConfirmedPackageCatalog": {},
        "yellowMappings": {},
    }
    for key in ("center", "yellow"):
        store_id = int(stores[key]["store_id"])
        rows = fetch_all(
            connection,
            """
            SELECT r.room_no,r.floor,COALESCE(rt.name,r.room_type) AS room_type
            FROM rooms r LEFT JOIN room_types rt ON rt.room_type_id=r.room_type_id
            WHERE r.tenant_id=%s AND r.store_id=%s AND r.deleted_at IS NULL
            ORDER BY r.floor,r.layout_order,r.room_no
            """,
            (tenant_id, store_id),
        )
        floors = Counter(str(row["floor"]) for row in rows)
        types = Counter(str(row["room_type"]) for row in rows)
        expected = EXPECTED[key]
        if len(rows) != expected["count"] or dict(floors) != expected["floors"] or dict(types) != expected["types"]:
            raise RestoreError(
                f"database validation failed for {key}: count={len(rows)}, floors={dict(floors)}, types={dict(types)}"
            )
        if len({row["room_no"] for row in rows}) != len(rows):
            raise RestoreError(f"database has duplicate active room numbers for {key}")
        result["stores"][key] = {
            "storeId": store_id,
            "storeName": stores[key]["name"],
            "count": len(rows),
            "floors": dict(sorted(floors.items())),
            "types": dict(sorted(types.items())),
        }

    center_id = stores["center"]["store_id"]
    center_rules = fetch_one(
        connection,
        "SELECT COUNT(*) AS total FROM package_price_rules WHERE tenant_id=%s AND store_id=%s AND status='ACTIVE'",
        (tenant_id, center_id),
    )
    result["centerActivePackageRules"] = int(center_rules["total"])
    center_catalog = fetch_one(
        connection,
        """
        SELECT COUNT(DISTINCT SUBSTRING_INDEX(pp.package_code,'-',1)) AS families,
               COUNT(DISTINCT pv.package_version_id) AS versions,
               COUNT(DISTINCT pr.price_rule_id) AS price_rules,
               COALESCE(SUM(
                 (profile.original_amount IS NOT NULL)
                 +(profile.activity_amount IS NOT NULL)
                 +(profile.deal_amount IS NOT NULL)
               ),0) AS price_values
        FROM package_products pp
        JOIN package_versions pv ON pv.package_id=pp.package_id
        JOIN package_price_rules pr
          ON pr.package_version_id=pv.package_version_id
        LEFT JOIN package_price_profiles profile
          ON profile.price_rule_id=pr.price_rule_id
        WHERE pp.tenant_id=%s AND pr.store_id=%s
          AND pp.package_code LIKE 'CENTER\\_%%'
          AND pp.status='ACTIVE' AND pv.version_status='ACTIVE'
          AND pr.status='ACTIVE'
        """,
        (tenant_id, center_id),
    )
    result["centerConfirmedPackageCatalog"] = {
        "families": int(center_catalog["families"] or 0),
        "versions": int(center_catalog["versions"] or 0),
        "priceRules": int(center_catalog["price_rules"] or 0),
        "priceValues": int(center_catalog["price_values"] or 0),
    }
    if result["centerConfirmedPackageCatalog"] != {
        "families": 7,
        "versions": 28,
        "priceRules": 28,
        "priceValues": 84,
    }:
        raise RestoreError(
            "center confirmed package catalog mismatch: "
            f"{result['centerConfirmedPackageCatalog']}"
        )

    yellow_id = stores["yellow"]["store_id"]
    rows = fetch_all(
        connection,
        """
        SELECT pp.package_code,rt.type_code,pr.stay_days
        FROM package_products pp
        JOIN package_versions pv ON pv.package_id=pp.package_id
        JOIN package_price_rules pr ON pr.package_version_id=pv.package_version_id
        JOIN room_types rt ON rt.room_type_id=pr.room_type_id
        WHERE pp.tenant_id=%s AND pp.package_code LIKE 'HH-%%'
          AND pp.status='ACTIVE' AND pv.version_status='ACTIVE'
          AND pr.status='ACTIVE' AND pr.store_id=%s
          AND pv.version_no='2026-07-confirmed'
        ORDER BY pp.package_code,rt.type_code,pr.stay_days
        """,
        (tenant_id, yellow_id),
    )
    actual = defaultdict(set)
    for row in rows:
        actual[str(row["package_code"])].add(
            (str(row["type_code"]), int(row["stay_days"]))
        )
    for code in {
        "HH-BASE", "HH-BASE-721", "HH-REPAIR", "HH-REPAIR-721",
        "HH-RECOVERY", "HH-QUEEN", "HH-PRESIDENT",
    }:
        expected_pairs = {
            (type_code, days)
            for type_code in room_type_codes_for_package(code)
            for days in (28, 35, 42, 56)
        }
        if actual[code] != expected_pairs:
            raise RestoreError(
                f"yellow package mapping failed for {code}: {sorted(actual[code])}"
            )
        result["yellowMappings"][code] = len(actual[code])
    return result


def api_request(url: str, method="GET", token=None, payload=None) -> dict:
    data = None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Token"] = token
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def validate_api(base: str, username: str, password: str, stores: dict) -> dict:
    if not password:
        raise RestoreError(
            "API validation requires --api-password or ERP_ACCEPTANCE_PASSWORD"
        )
    base = base.rstrip("/")
    login = api_request(
        f"{base}/vue-element-admin/user/login",
        method="POST",
        payload={"username": username, "password": password},
    )
    token = str((login.get("data") or {}).get("token") or "")
    if not token:
        raise RestoreError(f"API login failed: {login}")
    result = {}
    for key, expected_count in (("center", 36), ("yellow", 31)):
        store_name = str(stores[key]["name"])
        query = urllib.parse.urlencode({"store": store_name})
        counts = {}
        for resource in ("room-map", "smart-allocation"):
            payload = api_request(
                f"{base}/vue-element-admin/erp/room/modules/{resource}?{query}",
                token=token,
            )
            rows = (payload.get("data") or {}).get("list") or []
            counts[resource] = len(rows)
            if len(rows) != expected_count:
                raise RestoreError(
                    f"API {resource}/{store_name} returned {len(rows)}, expected {expected_count}"
                )
        result[key] = counts
    return result


def finish_run(connection, run_id: int, status: str, result: dict):
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE room_inventory_restore_runs SET status=%s,result_json=%s,completed_at=NOW() WHERE run_id=%s",
            (status, json.dumps(result, ensure_ascii=False, default=json_default), run_id),
        )
    connection.commit()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command", choices=["source-check", "preflight", "apply", "validate"]
    )
    parser.add_argument("--tenant-id", type=int, default=1)
    parser.add_argument(
        "--backup-dir", type=Path, default=ROOT / "backups" / "room-inventory"
    )
    parser.add_argument("--api-base", default="")
    parser.add_argument("--api-user", default="admin")
    parser.add_argument("--api-password", default="")
    args = parser.parse_args()

    data = load_confirmed_source()
    source_summary = assert_source(data)
    if args.command == "source-check":
        print(json.dumps(source_summary, ensure_ascii=False, indent=2))
        return 0

    connection = connect()
    try:
        if args.command == "preflight":
            report = preflight_report(connection, data, args.tenant_id)
            print(json.dumps(report, ensure_ascii=False, indent=2, default=json_default))
            return 2 if report["blockingExtras"] else 0
        if args.command == "validate":
            result = validate_database(connection, data, args.tenant_id)
            if args.api_base:
                result["api"] = validate_api(
                    args.api_base,
                    args.api_user,
                    args.api_password or os.environ.get("ERP_ACCEPTANCE_PASSWORD", ""),
                    resolve_stores(connection, args.tenant_id),
                )
            print(json.dumps(result, ensure_ascii=False, indent=2, default=json_default))
            return 0

        report = preflight_report(connection, data, args.tenant_id)
        if report["blockingExtras"]:
            raise RestoreError(
                "preflight found extra rooms with business references: "
                + json.dumps(report["blockingExtras"], ensure_ascii=False)
            )
        stores = resolve_stores(connection, args.tenant_id)
        snapshot = existing_snapshot(connection, args.tenant_id, stores)
        run_id = backup_snapshot(connection, snapshot, args.backup_dir)
        try:
            room_type_ids = apply_rooms(
                connection, data, args.tenant_id, stores
            )
            apply_yellow_packages(
                connection, data, args.tenant_id, stores, room_type_ids
            )
            validation = validate_database(connection, data, args.tenant_id)
            connection.commit()
            finish_run(connection, run_id, "COMPLETED", validation)
        except Exception as exc:
            connection.rollback()
            finish_run(connection, run_id, "FAILED", {"error": str(exc)})
            raise
        print(json.dumps(validation, ensure_ascii=False, indent=2, default=json_default))
        print("bookings were not created or modified")
        return 0
    finally:
        connection.close()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RestoreError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)

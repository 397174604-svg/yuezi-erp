#!/usr/bin/env python3
"""Safely seed the confirmed central-store maternity package price list.

The source is the client supplied price image recorded on 2026-07-29.  It
contains seven package families, four stay lengths and three distinct price
points (original, campaign and deal).  The script is intentionally additive:
it never deletes contracts, bookings, legacy bundles or Huanghe Road records.

The ERP currently has two read models for packages.  ``套餐管理`` reads the
legacy bundle surface while the contract workbench reads normalized catalogue
rules.  Each confirmed row is saved into both models and joined by
``legacy_bundle_id`` so the selector and the management list show the same
three price points.

Commands:
  python scripts/seed_confirmed_center_package_catalog.py source-check
  python scripts/seed_confirmed_center_package_catalog.py preflight
  python scripts/seed_confirmed_center_package_catalog.py backup
  python scripts/seed_confirmed_center_package_catalog.py apply
  python scripts/seed_confirmed_center_package_catalog.py validate

``apply`` makes a JSON backup first.  It requires the central store to be
exactly store_id=1 and refuses to overwrite a manually maintained row.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKUP_DIR = ROOT / "backups"
CENTER_STORE_ID = 1
# Store display names changed while the ERP was rebuilt. Use the immutable
# store ID as the scope and aliases only as a safety check.
CENTER_STORE_ALIASES = (
    "中心广场旗舰店",
    "奇德芬芳·建设路店（中心店）",
    "奇德芬芳建设路店",
    "建设路店",
    "中心店",
)
SOURCE_MARKER = "甲方中心店套餐价目表（2026-07-29确认）"
EFFECTIVE_FROM = "2026-07-29"

PACKAGE_FAMILIES = (
    ("CENTER_BASIC", "基础套餐", "未注明", "CENTER_KING", {
        28: (35880, 24999, 21999), 35: (42880, 29999, 26999),
        42: (49880, 34999, 31999), 56: (62880, 43999, 40999),
    }),
    ("CENTER_REST_B", "修养套餐B", "护士团队", "CENTER_SUITE", {
        28: (39880, 27999, 24999), 35: (47880, 32999, 30999),
        42: (55880, 38999, 35999), 56: (69880, 48999, 45999),
    }),
    ("CENTER_REST_A", "修养套餐A", "7天一对一", "CENTER_SUITE", {
        28: (43880, 30999, 27999), 35: (52880, 36999, 33999),
        42: (61880, 42999, 39999), 56: (78880, 54999, 51999),
    }),
    ("CENTER_ELEGANT_B", "精致尊享B", "双师护航", "CENTER_SUITE", {
        28: (49880, 34999, 31999), 35: (59880, 41999, 38999),
        42: (69880, 48999, 45999), 56: (88880, 61999, 58999),
    }),
    ("CENTER_ELEGANT_A", "精致尊享A", "双师护航", "CENTER_SUITE", {
        28: (52880, 36999, 33999), 35: (66880, 44999, 41999),
        42: (79880, 53999, 48999), 56: (100880, 65999, 62999),
    }),
    ("CENTER_VIP3", "臻享套餐VIP3楼", "双师护航", "CENTER_VIP302", {
        28: (59880, 41999, 38999), 35: (74880, 50999, 47999),
        42: (89880, 58999, 55999), 56: (118880, 74999, 71999),
    }),
    ("CENTER_VIP5", "至尊套餐VIP5楼", "双师护航", "CENTER_VIP512", {
        28: (79880, 53999, 50999), 35: (99880, 65999, 62999),
        42: (118880, 75999, 72999), 56: (159880, 95999, 92999),
    }),
)


class SeedError(RuntimeError):
    pass


def rows():
    result = []
    for family_code, name, nursing_type, room_type_code, prices in PACKAGE_FAMILIES:
        for days, (original, activity, deal) in sorted(prices.items()):
            result.append({
                "packageCode": f"{family_code}-{days}",
                "legacyNo": f"CC-{family_code.replace('CENTER_', '')}-{days}",
                "packageName": name,
                "nursingType": nursing_type,
                "roomTypeCode": room_type_code,
                "days": days,
                "originalPrice": Decimal(str(original)),
                "activityPrice": Decimal(str(activity)),
                "dealPrice": Decimal(str(deal)),
            })
    return result


def json_default(value):
    if isinstance(value, (Decimal, date, datetime)):
        return str(value)
    raise TypeError(type(value).__name__)


def connect():
    try:
        from server.mvp_api import connect as api_connect
    except ImportError as exc:
        raise SeedError("无法加载 ERP 数据库连接") from exc
    return api_connect()


def fetch_all(connection, sql, params=()):
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        return list(cursor.fetchall())


def fetch_one(connection, sql, params=()):
    data = fetch_all(connection, sql, params)
    return data[0] if data else None


def table_exists(connection, name):
    row = fetch_one(
        connection,
        "SELECT COUNT(*) AS total FROM information_schema.tables "
        "WHERE table_schema=DATABASE() AND table_name=%s",
        (name,),
    )
    return bool(row and int(row["total"]) == 1)


def source_check():
    data = rows()
    if len(data) != 28:
        raise SeedError(f"套餐版本数错误：{len(data)}，应为28")
    families = {item["packageName"] for item in data}
    if len(families) != 7:
        raise SeedError(f"套餐类别错误：{len(families)}，应为7")
    if {item["days"] for item in data} != {28, 35, 42, 56}:
        raise SeedError("套餐天数必须为28/35/42/56")
    for item in data:
        if not (item["originalPrice"] >= item["activityPrice"] >= item["dealPrice"] > 0):
            raise SeedError(f"价格顺序错误：{item['packageCode']}")
    return {
        "packageFamilies": len(families),
        "packageVersions": len(data),
        "pricePoints": len(data) * 3,
        "days": [28, 35, 42, 56],
    }


def resolve_center_store(connection, tenant_id):
    stores = fetch_all(
        connection,
        "SELECT store_id,name FROM stores WHERE tenant_id=%s ORDER BY store_id",
        (tenant_id,),
    )
    center = next(
        (row for row in stores if int(row["store_id"]) == CENTER_STORE_ID),
        None,
    )
    if not center:
        raise SeedError(f"Missing fixed central-store ID {CENTER_STORE_ID}")
    display_name = str(center.get("name") or "").strip()
    if not any(alias in display_name or display_name in alias for alias in CENTER_STORE_ALIASES):
        raise SeedError(
            "store_id=1 was not verified by a central-store alias: " +
            json.dumps({"store": center, "acceptedAliases": CENTER_STORE_ALIASES}, ensure_ascii=False)
        )
    duplicates = [
        row for row in stores
        if int(row["store_id"]) != CENTER_STORE_ID
        and any(alias in str(row.get("name") or "") for alias in CENTER_STORE_ALIASES)
    ]
    if duplicates:
        raise SeedError("Multiple central-store aliases found: " + json.dumps(duplicates, ensure_ascii=False))
    return center


def other_store_catalog_signature(connection, tenant_id, center_store_id):
    rows = fetch_all(
        connection,
        """
        SELECT pp.package_code,pv.version_no,pr.price_rule_id,pr.store_id,
               pr.room_type_id,pr.stay_days,pr.reference_amount,
               profile.original_amount,profile.activity_amount,profile.deal_amount
        FROM package_price_rules pr
        JOIN package_versions pv ON pv.package_version_id=pr.package_version_id
        JOIN package_products pp ON pp.package_id=pv.package_id
        LEFT JOIN package_price_profiles profile ON profile.price_rule_id=pr.price_rule_id
        WHERE pr.tenant_id=%s AND pr.store_id<>%s
        ORDER BY pr.store_id,pp.package_code,pv.version_no,pr.price_rule_id
        """,
        (tenant_id, center_store_id),
    )
    canonical = json.dumps(rows, ensure_ascii=False, sort_keys=True, default=json_default)
    return {"count": len(rows), "sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest()}


def preflight(connection, tenant_id=None):
    missing = [name for name in (
        "tenants", "stores", "room_types", "user_accounts", "item_bundles",
        "sales_bundle_extensions", "package_products", "package_versions",
        "package_price_rules", "package_price_profiles",
    ) if not table_exists(connection, name)]
    if missing:
        raise SeedError(
            "缺少套餐价格结构：" + ", ".join(missing) +
            "。请先执行数据库迁移（含 V20260801_029）。"
        )
    tenants = fetch_all(connection, "SELECT tenant_id FROM tenants ORDER BY tenant_id")
    if tenant_id is None:
        if len(tenants) != 1:
            raise SeedError("存在多个租户，请明确传入 --tenant-id")
        tenant_id = int(tenants[0]["tenant_id"])
    center = resolve_center_store(connection, tenant_id)
    other_store_signature = other_store_catalog_signature(connection, tenant_id, CENTER_STORE_ID)
    room_types = fetch_all(
        connection,
        "SELECT room_type_id,type_code,name FROM room_types WHERE tenant_id=%s AND status='启用'",
        (tenant_id,),
    )
    expected_codes = {item["roomTypeCode"] for item in rows()}
    found_codes = {str(item["type_code"]): item for item in room_types}
    absent = sorted(expected_codes - set(found_codes))
    if absent:
        raise SeedError("中心店缺少确认房型：" + "、".join(absent))
    admin = fetch_one(
        connection,
        "SELECT user_id FROM user_accounts WHERE tenant_id=%s AND username='admin' ORDER BY user_id LIMIT 1",
        (tenant_id,),
    )
    if not admin:
        raise SeedError("未找到admin账号，不能记录套餐主数据创建人")
    return {
        "tenantId": tenant_id,
        "center": center,
        "adminUserId": int(admin["user_id"]),
        "roomTypes": found_codes,
        "otherStorePriceRules": other_store_signature["count"],
        "otherStoreSignature": other_store_signature,
    }


def snapshot(connection, context):
    tenant_id = context["tenantId"]
    return {
        "capturedAt": datetime.now().isoformat(timespec="seconds"),
        "source": SOURCE_MARKER,
        "center": context["center"],
        "catalog": fetch_all(
            connection,
            """
            SELECT pp.package_id,pp.package_code,pp.package_name,pp.legacy_bundle_id,
                   pv.package_version_id,pv.legacy_bundle_id,pv.version_no,pv.version_status,
                   pr.price_rule_id,pr.store_id,pr.room_type_id,pr.stay_days,
                   pr.reference_amount,pr.status,profile.original_amount,
                   profile.activity_amount,profile.deal_amount
            FROM package_products pp
            LEFT JOIN package_versions pv ON pv.package_id=pp.package_id
            LEFT JOIN package_price_rules pr ON pr.package_version_id=pv.package_version_id
            LEFT JOIN package_price_profiles profile ON profile.price_rule_id=pr.price_rule_id
            WHERE pp.tenant_id=%s AND pp.package_code LIKE 'CENTER_%%'
            ORDER BY pp.package_id,pv.package_version_id,pr.price_rule_id
            """,
            (tenant_id,),
        ),
        "legacy": fetch_all(
            connection,
            """
            SELECT b.bundle_id,b.domain,b.name,b.price,b.times,b.status,
                   ext.bundle_no,ext.store_id,ext.reference_price,ext.activity_price,
                   ext.effective_date,ext.room_type,ext.audit_status,ext.details
            FROM item_bundles b
            JOIN sales_bundle_extensions ext ON ext.bundle_id=b.bundle_id
            WHERE b.tenant_id=%s AND ext.bundle_no LIKE 'CC-%%'
            ORDER BY b.bundle_id
            """,
            (tenant_id,),
        ),
    }


def write_backup(connection, context):
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    path = BACKUP_DIR / f"center-package-catalog-{datetime.now():%Y%m%d-%H%M%S}.json"
    path.write_text(
        json.dumps(snapshot(connection, context), ensure_ascii=False, indent=2, default=json_default),
        encoding="utf-8",
    )
    return path


def require_owned(existing, identity):
    if not existing:
        return
    marker = str(existing.get("note") or existing.get("details") or existing.get("evidence_note") or "")
    if SOURCE_MARKER not in marker:
        raise SeedError(f"拒绝覆盖非本脚本维护的套餐记录：{identity}")


def apply(connection, context):
    tenant_id = context["tenantId"]
    store_id = int(context["center"]["store_id"])
    user_id = context["adminUserId"]
    room_types = context["roomTypes"]
    backup_path = write_backup(connection, context)
    try:
        with connection.cursor() as cursor:
            for order, item in enumerate(rows(), start=1):
                existing_bundle = fetch_one(
                    connection,
                    """
                    SELECT b.bundle_id,b.note,ext.details FROM item_bundles b
                    JOIN sales_bundle_extensions ext ON ext.bundle_id=b.bundle_id
                    WHERE b.tenant_id=%s AND ext.bundle_no=%s
                    """,
                    (tenant_id, item["legacyNo"]),
                )
                require_owned(existing_bundle, item["legacyNo"])
                if existing_bundle:
                    bundle_id = int(existing_bundle["bundle_id"])
                    cursor.execute(
                        "UPDATE item_bundles SET name=%s,price=%s,times=%s,note=%s,status='启用',version=version+1 WHERE bundle_id=%s",
                        (item["packageName"], item["dealPrice"], item["days"], SOURCE_MARKER, bundle_id),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO item_bundles(tenant_id,domain,name,price,times,note,status,version,created_at)
                        VALUES(%s,'月子套餐',%s,%s,%s,%s,'启用',0,NOW())
                        """,
                        (tenant_id, item["packageName"], item["dealPrice"], item["days"], SOURCE_MARKER),
                    )
                    bundle_id = int(cursor.lastrowid)
                cursor.execute(
                    """
                    INSERT INTO sales_bundle_extensions(
                      bundle_id,store_id,bundle_no,bundle_type,days,reference_price,activity_price,
                      effective_date,room_type,audit_status,enabled_at,recommended,visible,details,room_info,created_by_user_id
                    ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,'审核通过',%s,0,1,%s,%s,%s)
                    ON DUPLICATE KEY UPDATE store_id=VALUES(store_id),bundle_type=VALUES(bundle_type),
                      days=VALUES(days),reference_price=VALUES(reference_price),activity_price=VALUES(activity_price),
                      effective_date=VALUES(effective_date),room_type=VALUES(room_type),audit_status='审核通过',
                      enabled_at=VALUES(enabled_at),visible=1,details=VALUES(details),room_info=VALUES(room_info),
                      created_by_user_id=VALUES(created_by_user_id)
                    """,
                    (
                        bundle_id, store_id, item["legacyNo"], item["nursingType"], item["days"],
                        item["originalPrice"], item["activityPrice"], EFFECTIVE_FROM,
                        room_types[item["roomTypeCode"]]["name"], EFFECTIVE_FROM, SOURCE_MARKER,
                        "适用房型为当前联调推荐，非合同硬绑定；以甲方后续确认规则为准。", user_id,
                    ),
                )

                product = fetch_one(
                    connection,
                    "SELECT package_id,note,legacy_bundle_id FROM package_products WHERE tenant_id=%s AND package_code=%s",
                    (tenant_id, item["packageCode"]),
                )
                if product:
                    require_owned(product, item["packageCode"])
                    package_id = int(product["package_id"])
                    cursor.execute(
                        "UPDATE package_products SET package_name=%s,legacy_bundle_id=NULL,status='ACTIVE',sort_order=%s,note=%s,version=version+1 WHERE package_id=%s",
                        (item["packageName"], order, SOURCE_MARKER, package_id),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO package_products(tenant_id,package_code,package_name,package_category,legacy_bundle_id,status,sort_order,note,created_by_user_id)
                        VALUES(%s,%s,%s,'月子套餐',NULL,'ACTIVE',%s,%s,%s)
                        """,
                        (tenant_id, item["packageCode"], item["packageName"], order, SOURCE_MARKER, user_id),
                    )
                    package_id = int(cursor.lastrowid)

                version_no = f"2026-07-client-confirmed-{item['days']}D"
                version = fetch_one(
                    connection,
                    "SELECT package_version_id,evidence_note,legacy_bundle_id FROM package_versions WHERE package_id=%s AND version_no=%s",
                    (package_id, version_no),
                )
                if version:
                    require_owned(version, f"{item['packageCode']}@{version_no}")
                    if version.get("legacy_bundle_id") not in (None, bundle_id):
                        raise SeedError(f"套餐版本已关联其它业务套餐：{item['packageCode']}@{version_no}")
                    version_id = int(version["package_version_id"])
                    cursor.execute(
                        "UPDATE package_versions SET legacy_bundle_id=%s,effective_from=%s,effective_to=NULL,version_status='ACTIVE',source_type='CLIENT_CONFIRMED',evidence_note=%s,published_at=COALESCE(published_at,NOW()),published_by_user_id=%s WHERE package_version_id=%s",
                        (bundle_id, EFFECTIVE_FROM, SOURCE_MARKER, user_id, version_id),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO package_versions(tenant_id,package_id,legacy_bundle_id,version_no,effective_from,version_status,source_type,evidence_note,published_at,published_by_user_id,created_by_user_id)
                        VALUES(%s,%s,%s,%s,%s,'ACTIVE','CLIENT_CONFIRMED',%s,NOW(),%s,%s)
                        """,
                        (tenant_id, package_id, bundle_id, version_no, EFFECTIVE_FROM, SOURCE_MARKER, user_id, user_id),
                    )
                    version_id = int(cursor.lastrowid)

                room_type_id = int(room_types[item["roomTypeCode"]]["room_type_id"])
                price = fetch_one(
                    connection,
                    """
                    SELECT price_rule_id FROM package_price_rules
                    WHERE package_version_id=%s AND store_id=%s AND room_type_id=%s AND stay_days=%s AND effective_from=%s
                    """,
                    (version_id, store_id, room_type_id, item["days"], EFFECTIVE_FROM),
                )
                if price:
                    price_id = int(price["price_rule_id"])
                    cursor.execute(
                        "UPDATE package_price_rules SET reference_amount=%s,effective_to=NULL,status='ACTIVE',version=version+1 WHERE price_rule_id=%s",
                        (item["originalPrice"], price_id),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO package_price_rules(tenant_id,package_version_id,store_id,room_type_id,stay_days,reference_amount,currency_code,effective_from,status)
                        VALUES(%s,%s,%s,%s,%s,%s,'CNY',%s,'ACTIVE')
                        """,
                        (tenant_id, version_id, store_id, room_type_id, item["days"], item["originalPrice"], EFFECTIVE_FROM),
                    )
                    price_id = int(cursor.lastrowid)
                cursor.execute(
                    """
                    INSERT INTO package_price_profiles(tenant_id,price_rule_id,original_amount,activity_amount,deal_amount,source_type,evidence_note)
                    VALUES(%s,%s,%s,%s,%s,'CLIENT_CONFIRMED',%s)
                    ON DUPLICATE KEY UPDATE original_amount=VALUES(original_amount),activity_amount=VALUES(activity_amount),
                      deal_amount=VALUES(deal_amount),source_type='CLIENT_CONFIRMED',evidence_note=VALUES(evidence_note)
                    """,
                    (tenant_id, price_id, item["originalPrice"], item["activityPrice"], item["dealPrice"], SOURCE_MARKER),
                )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    return backup_path


def validate(connection, context):
    tenant_id = context["tenantId"]
    center_id = int(context["center"]["store_id"])
    expected = rows()
    actual = fetch_all(
        connection,
        """
        SELECT pp.package_code,pp.package_name,pv.version_status,pr.store_id,pr.stay_days,
               pr.reference_amount,profile.original_amount,profile.activity_amount,profile.deal_amount,
               b.price AS legacy_deal,ext.reference_price AS legacy_original,ext.activity_price AS legacy_activity
        FROM package_products pp
        JOIN package_versions pv ON pv.package_id=pp.package_id
        JOIN package_price_rules pr ON pr.package_version_id=pv.package_version_id
        JOIN package_price_profiles profile ON profile.price_rule_id=pr.price_rule_id
        JOIN item_bundles b ON b.bundle_id=pv.legacy_bundle_id
        JOIN sales_bundle_extensions ext ON ext.bundle_id=b.bundle_id
        WHERE pp.tenant_id=%s AND pp.package_code LIKE 'CENTER_%%' AND pr.store_id=%s
        ORDER BY pp.package_code
        """,
        (tenant_id, center_id),
    )
    if len(actual) != 28:
        raise SeedError(f"中心店套餐版本数为{len(actual)}，应为28")
    by_code = {
        (item["package_code"], int(item["stay_days"])): item
        for item in actual
    }
    for item in expected:
        found = by_code.get((item["packageCode"], int(item["days"])))
        if not found:
            raise SeedError(f"缺少套餐版本：{item['packageCode']}")
        expected_values = (item["originalPrice"], item["activityPrice"], item["dealPrice"])
        actual_values = (Decimal(str(found["original_amount"])), Decimal(str(found["activity_amount"])), Decimal(str(found["deal_amount"])))
        legacy_values = (Decimal(str(found["legacy_original"])), Decimal(str(found["legacy_activity"])), Decimal(str(found["legacy_deal"])))
        if actual_values != expected_values or legacy_values != expected_values:
            raise SeedError(f"三价格不一致：{item['packageCode']}")
        if found["version_status"] != "ACTIVE":
            raise SeedError(f"套餐未启用：{item['packageCode']}")
    other = other_store_catalog_signature(connection, tenant_id, center_id)
    if other != context["otherStoreSignature"]:
        raise SeedError(
            "non-central package data changed during center seed: " +
            json.dumps({"before": context["otherStoreSignature"], "after": other})
        )
    return {
        "centerStoreId": center_id,
        "packageFamilies": 7,
        "packageVersions": len(actual),
        "pricePoints": len(actual) * 3,
        "otherStorePriceRulesRetained": other["count"],
        "otherStoreSignature": other,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["source-check", "preflight", "backup", "apply", "validate"])
    parser.add_argument("--tenant-id", type=int)
    args = parser.parse_args()
    try:
        if args.command == "source-check":
            print(json.dumps(source_check(), ensure_ascii=False, indent=2))
            return 0
        connection = connect()
        try:
            context = preflight(connection, args.tenant_id)
            if args.command == "preflight":
                print(json.dumps({"source": source_check(), "preflight": context}, ensure_ascii=False, indent=2, default=json_default))
            elif args.command == "backup":
                print(write_backup(connection, context))
            elif args.command == "apply":
                backup = apply(connection, context)
                result = validate(connection, context)
                result["backup"] = str(backup)
                print(json.dumps(result, ensure_ascii=False, indent=2, default=json_default))
            else:
                print(json.dumps(validate(connection, context), ensure_ascii=False, indent=2, default=json_default))
        finally:
            connection.close()
    except SeedError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

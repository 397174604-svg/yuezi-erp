#!/usr/bin/env python3
"""Seed, verify, or precisely clean F081 and F099-F106 acceptance rows.

Only local MySQL is accepted.  Every inserted row carries the exact marker
``LOCAL_ACCEPTANCE_SEED_20260801`` and cleanup is restricted to the nine
resources declared below.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / ".deps"))

import pymysql

from server.operational_records import business_no


BATCH = "LOCAL_ACCEPTANCE_SEED_20260801"
TENANT_ID = 1
STORE_IDS = (1, 2)
RESOURCES = {
    "RESEARCH": ("beauty-cases",),
    "RECOVERY": (
        "recovery-programs",
        "recovery-schedule",
        "postpartum-assessments",
        "recovery-service-tracking",
        "recovery-store-dashboard",
        "recovery-upsell",
        "recovery-assets",
        "recovery-staff-performance",
    ),
}
IDENTIFIER_FIELDS = {
    "beauty-cases": "caseNo",
    "recovery-programs": "programNo",
    "recovery-schedule": "appointmentNo",
    "postpartum-assessments": "assessmentNo",
    "recovery-service-tracking": "recordNo",
    "recovery-store-dashboard": "dashboardNo",
    "recovery-upsell": "opportunityNo",
    "recovery-assets": "assetNo",
    "recovery-staff-performance": "performanceNo",
}
PEOPLE = {
    1: (
        {"customer": "李静", "staff": "周晓梅", "room": "201"},
        {"customer": "王芳", "staff": "孙丽", "room": "203"},
        {"customer": "张敏", "staff": "陈佳", "room": "205"},
    ),
    2: (
        {"customer": "刘洋", "staff": "赵欣", "room": "301"},
        {"customer": "赵雪", "staff": "吴倩", "room": "302"},
        {"customer": "陈晨", "staff": "郑雯", "room": "303"},
    ),
}


def connection():
    host = os.environ.get("ERP_DB_HOST", "127.0.0.1")
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise SystemExit("Acceptance data operations are restricted to loopback MySQL.")
    return pymysql.connect(
        host=host,
        port=int(os.environ.get("ERP_DB_PORT", "3306")),
        user=os.environ["ERP_DB_USER"],
        password=os.environ["ERP_DB_PASSWORD"],
        database=os.environ.get("ERP_DB_NAME", "yuezi"),
        charset="utf8mb4",
        autocommit=False,
    )


def require_write_confirmation() -> None:
    if os.environ.get("ERP_LOCAL_DEMO_CONFIRM") != "LOCAL_TEST_ONLY":
        raise SystemExit("Set ERP_LOCAL_DEMO_CONFIRM=LOCAL_TEST_ONLY for apply/cleanup.")


def resource_pairs():
    for module_code, resources in RESOURCES.items():
        for resource in resources:
            yield module_code, resource


def delete_marked_rows(cursor) -> int:
    predicates = " OR ".join("(module_code=%s AND resource_code=%s)" for _ in resource_pairs())
    params: list[Any] = []
    for module_code, resource in resource_pairs():
        params.extend((module_code, resource))
    params.append(f'%"demoBatch": "{BATCH}"%')
    return cursor.execute(
        f"""
        DELETE FROM erp_operational_records
        WHERE tenant_id=%s AND ({predicates}) AND payload_json LIKE %s
        """,
        [TENANT_ID, *params],
    )


def base_payload(store_name: str, person: dict[str, str]) -> dict[str, Any]:
    return {
        "demoBatch": BATCH,
        "acceptanceMarker": BATCH,
        "store": store_name,
        "customerName": person["customer"],
        "ownerName": person["staff"],
        "remark": "本地验收资料，禁止用于真实客户触达或外部服务执行。",
    }


def payload_for(resource: str, store_name: str, store_id: int, index: int) -> dict[str, Any]:
    person = PEOPLE[store_id][index - 1]
    day = date(2026, 8, 2) + timedelta(days=index - 1)
    payload = base_payload(store_name, person)
    if resource == "beauty-cases":
        payload.update({
            "room": person["room"], "category": "产康" if index < 3 else "美容",
            "program": ("腹直肌修复", "骨盆修复", "产后体态管理")[index - 1],
            "owner": person["staff"], "baseline": ("分离3.0cm", "骨盆稳定度68", "体态评分62")[index - 1],
            "current": ("分离2.2cm", "骨盆稳定度76", "体态评分71")[index - 1],
            "nextReview": (day + timedelta(days=14)).isoformat(),
            "risk": ("低", "中", "低")[index - 1],
            "stage": ("方案执行中", "复测待复核", "案例已归档")[index - 1],
            "consent": ("已签署", "已签署", "已签署")[index - 1],
            "status": ("方案执行中", "需要复核", "已完成")[index - 1],
        })
    elif resource == "recovery-programs":
        payload.update({
            "programName": ("腹直肌修复疗程", "骨盆修复疗程", "产后体态管理次卡")[index - 1],
            "category": ("疗程", "疗程", "次卡")[index - 1],
            "sessions": (6, 8, 10)[index - 1], "price": (2980, 3980, 4680)[index - 1],
            "validity": ("90天", "120天", "180天")[index - 1],
            "owner": person["staff"], "status": ("已上架", "已上架", "草稿")[index - 1],
        })
    elif resource == "recovery-schedule":
        payload.update({
            "appointmentDate": day.isoformat(), "timePeriod": ("09:00-10:00", "10:30-11:30", "14:00-15:00")[index - 1],
            "programName": ("腹直肌修复", "骨盆修复", "产后体态管理")[index - 1],
            "technician": person["staff"], "status": ("已确认", "待确认", "服务中")[index - 1],
        })
    elif resource == "postpartum-assessments":
        payload.update({
            "assessedAt": day.isoformat(), "assessor": person["staff"],
            "coreScore": (72, 68, 81)[index - 1], "pelvisScore": (70, 75, 84)[index - 1],
            "painScore": (2, 4, 1)[index - 1], "riskLevel": ("低", "中", "低")[index - 1],
            "recommendation": ("建议6次腹直肌修复", "建议8次骨盆修复并两周复测", "保持现有训练频率")[index - 1],
            "status": ("已完成", "待复核", "已完成")[index - 1],
        })
    elif resource == "recovery-service-tracking":
        payload.update({
            "programName": ("腹直肌修复", "骨盆修复", "产后体态管理")[index - 1],
            "serviceDate": day.isoformat(), "technician": person["staff"],
            "beforeValue": ("分离3.0cm", "稳定度68", "体态评分62")[index - 1],
            "afterValue": ("分离2.6cm", "稳定度73", "体态评分67")[index - 1],
            "feedback": ("腹部发力感改善", "腰骶不适减轻", "站姿更稳定")[index - 1],
            "status": ("已完成", "服务中", "待执行")[index - 1],
        })
    elif resource == "recovery-store-dashboard":
        payload.update({
            "period": ("今日", "本周", "本月")[index - 1],
            "appointments": (8, 36, 128)[index - 1], "completed": (6, 29, 103)[index - 1],
            "revenue": (4860, 23800, 97600)[index - 1], "repurchaseRate": ("32%", "35%", "38%")[index - 1],
            "topProgram": ("腹直肌修复", "骨盆修复", "产后体态管理")[index - 1],
            "alert": ("2个预约待确认", "3位客户待复测", "5张次卡临近到期")[index - 1],
            "manager": person["staff"], "status": "已生成",
        })
    elif resource == "recovery-upsell":
        payload.update({
            "currentProgram": ("腹直肌修复", "骨盆修复", "产后体态管理")[index - 1],
            "remainingSessions": (2, 1, 3)[index - 1],
            "recommendation": ("增加4次巩固疗程", "升级综合修复疗程", "续购10次体态管理卡")[index - 1],
            "owner": person["staff"], "nextFollowUp": (day + timedelta(days=3)).isoformat(),
            "opportunityStatus": ("待跟进", "跟进中", "暂不考虑")[index - 1],
            "status": ("待跟进", "跟进中", "暂不考虑")[index - 1],
        })
    elif resource == "recovery-assets":
        payload.update({
            "assetName": ("盆底肌修复仪", "一次性理疗垫", "腹直肌训练带")[index - 1],
            "assetType": ("设备", "耗材", "耗材")[index - 1],
            "specification": ("PK-2026A", "60cm×90cm", "标准型")[index - 1],
            "quantity": (2, 48, 16)[index - 1], "lastMaintenance": (day - timedelta(days=30)).isoformat(),
            "assetStatus": ("在用", "低库存", "在用")[index - 1],
            "custodian": person["staff"], "status": ("在用", "低库存", "在用")[index - 1],
        })
    elif resource == "recovery-staff-performance":
        payload.update({
            "technician": person["staff"], "shiftDate": day.isoformat(),
            "shiftPeriod": ("09:00-17:00", "10:00-18:00", "12:00-20:00")[index - 1],
            "capacity": (6, 6, 5)[index - 1], "completedCount": (5, 4, 4)[index - 1],
            "rating": (4.9, 4.8, 4.7)[index - 1], "upsellAmount": (1280, 980, 680)[index - 1],
            "shiftStatus": ("出勤", "出勤", "出勤")[index - 1], "status": "已确认",
        })
    else:
        raise ValueError(resource)
    return payload


def load_context(cursor):
    cursor.execute(
        "SELECT store_id,name FROM stores WHERE tenant_id=%s AND store_id IN (1,2) ORDER BY store_id",
        (TENANT_ID,),
    )
    stores = {int(row[0]): str(row[1]) for row in cursor.fetchall()}
    if set(stores) != set(STORE_IDS):
        raise RuntimeError(f"Expected stores {STORE_IDS}, found {sorted(stores)}")
    cursor.execute(
        "SELECT user_id FROM user_accounts WHERE tenant_id=%s AND username='admin' LIMIT 1",
        (TENANT_ID,),
    )
    user = cursor.fetchone()
    if not user:
        raise RuntimeError("Admin user is missing.")
    return stores, int(user[0])


def apply() -> None:
    require_write_confirmation()
    db = connection()
    try:
        with db.cursor() as cursor:
            stores, user_id = load_context(cursor)
            removed = delete_marked_rows(cursor)
            inserted = 0
            for store_id in STORE_IDS:
                for module_code, resource in resource_pairs():
                    for index in range(1, 4):
                        payload = payload_for(resource, stores[store_id], store_id, index)
                        status = str(payload.get("status") or "草稿")
                        pending = f"PENDING-{module_code}-{resource}-{store_id}-{index}"
                        cursor.execute(
                            """
                            INSERT INTO erp_operational_records(
                              tenant_id,store_id,module_code,resource_code,business_no,status,
                              payload_json,created_by_user_id,updated_by_user_id
                            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                            """,
                            (TENANT_ID, store_id, module_code, resource, pending, status,
                             json.dumps(payload, ensure_ascii=False), user_id, user_id),
                        )
                        record_id = int(cursor.lastrowid)
                        formal_no = business_no(module_code, resource, record_id)
                        payload[IDENTIFIER_FIELDS[resource]] = formal_no
                        payload["businessNo"] = formal_no
                        cursor.execute(
                            "UPDATE erp_operational_records SET business_no=%s,payload_json=%s WHERE record_id=%s",
                            (formal_no, json.dumps(payload, ensure_ascii=False), record_id),
                        )
                        inserted += 1
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    print(json.dumps({"status": "seeded", "batch": BATCH, "removed": removed, "inserted": inserted}, ensure_ascii=False))


def verify() -> None:
    db = connection()
    results = []
    try:
        with db.cursor() as cursor:
            for store_id in STORE_IDS:
                for module_code, resource in resource_pairs():
                    cursor.execute(
                        """
                        SELECT COUNT(*) FROM erp_operational_records
                        WHERE tenant_id=%s AND store_id=%s AND module_code=%s AND resource_code=%s
                          AND deleted_at IS NULL AND payload_json LIKE %s
                        """,
                        (TENANT_ID, store_id, module_code, resource, f'%"demoBatch": "{BATCH}"%'),
                    )
                    count = int(cursor.fetchone()[0])
                    if count != 3:
                        raise AssertionError(f"{module_code}/{resource}/store-{store_id}: expected 3, got {count}")
                    results.append({"storeId": store_id, "module": module_code, "resource": resource, "rows": count})
    finally:
        db.close()
    print(json.dumps({"status": "verified", "batch": BATCH, "endpoints": len(results), "rows": sum(item["rows"] for item in results), "results": results}, ensure_ascii=False))


def cleanup() -> None:
    require_write_confirmation()
    db = connection()
    try:
        with db.cursor() as cursor:
            removed = delete_marked_rows(cursor)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    print(json.dumps({"status": "cleaned", "batch": BATCH, "removed": removed}, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("apply", "verify", "cleanup"))
    args = parser.parse_args()
    {"apply": apply, "verify": verify, "cleanup": cleanup}[args.command]()


if __name__ == "__main__":
    main()

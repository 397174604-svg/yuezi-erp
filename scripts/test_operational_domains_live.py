#!/usr/bin/env python3
"""Live loopback regression for BABY, MATRON, DIET and INVENTORY records."""

from __future__ import annotations

import importlib.util
import json
import os
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = ROOT / "scripts" / "seed_local_acceptance_dataset.py"
SPEC = importlib.util.spec_from_file_location("acceptance_seed", SEED_PATH)
assert SPEC and SPEC.loader
seed = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(seed)
import pymysql

BASE_URL = os.environ.get("ERP_API_URL", "http://127.0.0.1:3000").rstrip("/")
MARKER = seed.BATCH
DOMAIN_CONFIG = {
    "BABY": {
        "prefix": "baby",
        "required": ("customerName", "babyName", "room", "status", "remark"),
        "writeResource": "newborn-care-records",
        "action": "确认完成",
        "payload": {"recordNo": "NCR-LIVE", "babyName": "安安", "room": "201", "careItem": "脐部护理", "careDate": "2026-08-01", "nurseName": "李护士", "result": "情况正常", "status": "待执行"},
    },
    "MATRON": {
        "prefix": "maternity-nurse",
        "required": ("护理师名称", "护理师等级", "客户名称", "档期情况", "最终金额", "所属分店", "状态"),
        "writeResource": "maternity-settlements",
        "action": "审核",
        "payload": {"护理师名称": "刘芳", "护理师等级": "高级月嫂", "客户名称": "李女士", "档期情况": "服务中", "最终金额": 10800, "所属分店": "当前门店", "状态": "待审核"},
    },
    "DIET": {
        "prefix": "diet",
        "required": ("orderNo", "dishCode", "dishName", "mealType", "mealDate", "quantity", "amount", "deliveryStatus"),
        "writeResource": "meal-orders",
        "action": "确认下单",
        "payload": {"orderNo": "MEAL-LIVE", "dishCode": "D-LIVE", "dishName": "山药小米粥", "mealType": "早餐", "mealDate": "2026-08-01", "quantity": 1, "amount": 68, "deliveryStatus": "待备餐"},
    },
    "INVENTORY": {
        "prefix": "inventory",
        "required": ("materialCode", "materialName", "specification", "unit", "quantity", "currentQuantity", "purchaseNo", "supplierName", "warehouse", "totalAmount", "auditStatus"),
        "writeResource": "stocktakes",
        "action": "开始盘点",
        "payload": {"materialCode": "MAT-LIVE", "materialName": "护理湿巾", "specification": "标准装", "unit": "包", "quantity": 20, "currentQuantity": 20, "purchaseNo": "PO-LIVE", "supplierName": "护理物资供应商", "warehouse": "护理部仓库", "totalAmount": 500, "auditStatus": "待审核"},
    },
}


def verify_database_baseline() -> int | None:
    if not os.environ.get("ERP_DB_PASSWORD"):
        return None
    connection = pymysql.connect(
        host=os.environ.get("ERP_DB_HOST", "127.0.0.1"),
        port=int(os.environ.get("ERP_DB_PORT", "3306")),
        user=os.environ["ERP_DB_USER"],
        password=os.environ["ERP_DB_PASSWORD"],
        database=os.environ.get("ERP_DB_NAME", "yuezi"),
        charset="utf8mb4",
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*) FROM erp_operational_records
                WHERE deleted_at IS NULL AND payload_json LIKE %s
                """,
                (f'%"demoBatch": "{MARKER}"%',),
            )
            active_marker_rows = int(cursor.fetchone()[0])
            cursor.execute(
                """
                SELECT COUNT(*) FROM erp_operational_records
                WHERE deleted_at IS NULL AND payload_json LIKE %s
                """,
                ('%"liveRollback"%',),
            )
            assert int(cursor.fetchone()[0]) == 0
    finally:
        connection.close()
    assert active_marker_rows == 462, active_marker_rows
    return active_marker_rows


def api(path: str, method: str = "GET", body=None, token: str = "", query=None):
    if query:
        path = f"{path}?{urlencode(query)}"
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        headers["X-Token"] = token
    request = Request(
        BASE_URL + path,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None,
        headers=headers,
        method=method,
    )
    try:
        with urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise AssertionError(f"{method} {path}: HTTP {exc.code}: {detail}") from exc
    assert payload.get("code") == 20000, payload
    assert MARKER not in json.dumps(payload, ensure_ascii=False), f"marker leaked: {path}"
    return payload["data"]


def main() -> None:
    assert urlparse(BASE_URL).hostname in {"127.0.0.1", "localhost", "::1"}
    password = os.environ.get("ERP_DEMO_ADMIN_PASSWORD")
    if not password:
        raise SystemExit("ERP_DEMO_ADMIN_PASSWORD is required")
    token = api(
        "/vue-element-admin/user/login",
        "POST",
        {"username": "admin", "password": password},
    )["token"]

    endpoint_count = 0
    resource_count = 0
    for module_code, config in DOMAIN_CONFIG.items():
        resources = seed.RESOURCES[module_code]
        resource_count += len(resources)
        for store_id in (1, 2):
            for resource in resources:
                data = api(
                    f"/vue-element-admin/erp/{config['prefix']}/modules/{resource}",
                    token=token,
                    query={"storeId": store_id},
                )
                rows = data.get("list") or []
                assert len(rows) >= 3, f"{module_code} store {store_id} {resource}: {len(rows)} rows"
                for row in rows[:3]:
                    for field in config["required"]:
                        assert row.get(field) not in (None, ""), f"{module_code} {resource}.{field} missing"
                endpoint_count += 1

    rollback_records = []
    try:
        for module_code, config in DOMAIN_CONFIG.items():
            resource = config["writeResource"]
            base = f"/vue-element-admin/erp/{config['prefix']}/modules/{resource}"
            saved = api(
                f"{base}/save",
                "POST",
                {
                    **config["payload"],
                    "storeId": 1,
                    "customerName": "李女士",
                    "babyName": "安安",
                    "room": "201",
                    "remark": "资料已核验",
                    "liveRollback": datetime.now().isoformat(timespec="microseconds"),
                },
                token,
            )
            record_id = saved.get("recordId")
            assert record_id, saved
            rollback_records.append((base, record_id))
            api(
                f"{base}/action",
                "POST",
                {"recordId": record_id, "action": config["action"]},
                token,
            )
    finally:
        for base, record_id in rollback_records:
            api(
                f"{base}/action",
                "POST",
                {"recordId": record_id, "action": "删除"},
                token,
            )

    for base, record_id in rollback_records:
        rows = api(base, token=token, query={"storeId": 1}).get("list") or []
        assert record_id not in {row.get("recordId") for row in rows}

    active_marker_rows = verify_database_baseline()

    print(
        json.dumps(
            {
                "status": "passed",
                "domains": len(DOMAIN_CONFIG),
                "resources": resource_count,
                "getEndpoints": endpoint_count,
                "writeRollbacks": len(rollback_records),
                "activeMarkerRows": active_marker_rows,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Live HTTP acceptance for F081 and F099-F106 on both local stores."""

from __future__ import annotations

import json
import os
from datetime import datetime
from urllib.error import HTTPError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen


BASE_URL = os.environ.get("ERP_API_URL", "http://127.0.0.1:3000").rstrip("/")
SANITIZED_MARKER = "资料已核验"
RECOVERY_RESOURCES = (
    "recovery-programs",
    "recovery-schedule",
    "postpartum-assessments",
    "recovery-service-tracking",
    "recovery-store-dashboard",
    "recovery-upsell",
    "recovery-assets",
    "recovery-staff-performance",
)
REQUIRED_FIELDS = {
    "beauty-cases": ("caseNo", "customerName", "room", "store", "program", "owner", "status"),
    "recovery-programs": ("programNo", "programName", "category", "sessions", "price", "store", "status"),
    "recovery-schedule": ("appointmentNo", "appointmentDate", "customerName", "programName", "technician", "store", "status"),
    "postpartum-assessments": ("assessmentNo", "customerName", "assessedAt", "assessor", "riskLevel", "store", "status"),
    "recovery-service-tracking": ("recordNo", "customerName", "programName", "serviceDate", "technician", "store", "status"),
    "recovery-store-dashboard": ("dashboardNo", "store", "period", "appointments", "completed", "revenue", "topProgram"),
    "recovery-upsell": ("opportunityNo", "customerName", "currentProgram", "recommendation", "owner", "store", "opportunityStatus"),
    "recovery-assets": ("assetNo", "assetName", "assetType", "quantity", "store", "assetStatus"),
    "recovery-staff-performance": ("performanceNo", "technician", "store", "shiftDate", "completedCount", "rating", "shiftStatus"),
}


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
    assert payload.get("code") == 20000, (method, path, payload)
    return payload["data"]


def rows_for(base: str, store_id: int, token: str):
    data = api(base, token=token, query={"storeId": store_id})
    rows = data.get("list") or []
    seeded = [row for row in rows if row.get("demoBatch") == SANITIZED_MARKER]
    return rows, seeded


def assert_seeded_rows(base: str, resource: str, store_id: int, token: str) -> dict:
    _rows, seeded = rows_for(base, store_id, token)
    assert len(seeded) >= 3, f"{resource}/store-{store_id}: {len(seeded)} acceptance rows"
    for row in seeded[:3]:
        for field in REQUIRED_FIELDS[resource]:
            assert row.get(field) not in (None, ""), f"{resource}.{field} missing: {row}"
    return {"storeId": store_id, "resource": resource, "rows": len(seeded)}


def rollback_chain(base: str, payload: dict, action: str, token: str) -> dict:
    rollback_key = f"RR-LIVE-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    saved = api(f"{base}/save", "POST", {**payload, "liveRollback": rollback_key}, token)
    record_id = saved.get("recordId")
    assert record_id, saved
    deleted = False
    try:
        acted = api(f"{base}/action", "POST", {"recordId": record_id, "action": action}, token)
        assert acted.get("recordId") == record_id, acted
        api(f"{base}/action", "POST", {"recordId": record_id, "action": "删除"}, token)
        deleted = True
    finally:
        if not deleted:
            try:
                api(f"{base}/action", "POST", {"recordId": record_id, "action": "删除"}, token)
            except Exception:
                pass
    store_id = int(payload["storeId"])
    rows, _seeded = rows_for(base, store_id, token)
    assert all(row.get("id") != record_id for row in rows), f"rollback row remains active: {record_id}"
    return {"resource": base.rsplit("/", 1)[-1], "recordId": record_id, "save": "pass", "action": "pass", "delete": "pass"}


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

    gets = []
    research_base = "/vue-element-admin/erp/research/modules/beauty-cases"
    for store_id in (1, 2):
        gets.append(assert_seeded_rows(research_base, "beauty-cases", store_id, token))
    for resource in RECOVERY_RESOURCES:
        base = f"/vue-element-admin/erp/rehab/modules/{resource}"
        for store_id in (1, 2):
            gets.append(assert_seeded_rows(base, resource, store_id, token))

    rollbacks = [
        rollback_chain(
            research_base,
            {
                "storeId": 1, "customerName": "李静", "room": "201", "store": "奇德芬芳·建设路店（中心店）",
                "category": "产康", "program": "腹直肌修复", "owner": "周晓梅", "baseline": "分离3.0cm",
                "current": "待复测", "nextReview": "2026-08-16", "risk": "低", "stage": "方案待执行",
                "consent": "待签署", "status": "待制定方案",
            },
            "记录跟进",
            token,
        ),
        rollback_chain(
            "/vue-element-admin/erp/rehab/modules/recovery-upsell",
            {
                "storeId": 2, "customerName": "刘洋", "store": "奇德芬芳·黄河路店",
                "currentProgram": "腹直肌修复", "remainingSessions": 2, "recommendation": "增加4次巩固疗程",
                "owner": "赵欣", "nextFollowUp": "2026-08-05", "opportunityStatus": "待跟进", "status": "待跟进",
            },
            "记录跟进",
            token,
        ),
    ]
    print(json.dumps({"status": "passed", "getEndpoints": len(gets), "gets": gets, "writeRollbacks": rollbacks}, ensure_ascii=False))


if __name__ == "__main__":
    main()

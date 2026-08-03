"""Live smoke audit for the remaining, non-overlapping ERP domains.

The script deliberately performs read-only requests.  It verifies that every
configured server-backed resource is reachable and reports empty resources so
that an empty database is not mistaken for a successful business acceptance.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "http://127.0.0.1:3000"

BASIC_RESOURCES = [
    "employee-records", "basic-items", "material-records", "room-records",
    "satisfaction-survey-templates", "survey-management", "warehouse-records",
    "supplier-records", "fund-accounts", "report-templates", "nursing-templates",
    "task-management", "service-time-settings", "project-labor-fee-settings",
    "commission-rate-settings", "equipment-management",
    "performance-target-settings", "discount-amount-authorization", "bed-management",
]
MALL_RESOURCES = [
    "products", "orders", "projects", "matrons", "categories", "parenting",
    "questions", "reviews", "community", "content", "comments", "classes",
    "class-schedule",
]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def login(session: requests.Session) -> dict[str, str]:
    response = session.post(
        f"{BASE_URL}/vue-element-admin/user/login",
        json={"username": "admin", "password": "admin123"},
        timeout=10,
    )
    response.raise_for_status()
    token = response.json()["data"]["token"]
    return {"X-Token": token, "Authorization": f"Bearer {token}"}


def fetch_list(
    session: requests.Session,
    headers: dict[str, str],
    path: str,
    *,
    store_id: int = 1,
) -> list[dict]:
    response = session.get(
        f"{BASE_URL}{path}",
        headers=headers,
        params={"storeId": store_id},
        timeout=10,
    )
    assert response.status_code == 200, (
        f"GET {path} returned {response.status_code}: {response.text[:180]}"
    )
    payload = response.json()
    assert payload.get("code") == 20000, f"GET {path}: {payload}"
    data = payload.get("data") or {}
    rows = data.get("list") or []
    assert isinstance(rows, list), f"GET {path} did not return a list"
    return rows


def post_data(session, headers, path, body):
    response = session.post(
        f"{BASE_URL}{path}", headers=headers, json=body, timeout=10
    )
    assert response.status_code == 200, (
        f"POST {path} returned {response.status_code}: {response.text[:220]}"
    )
    payload = response.json()
    assert payload.get("code") == 20000, f"POST {path}: {payload}"
    return payload.get("data") or {}


def assert_write_cycles(session, headers):
    cases = [
        ("basic", "/vue-element-admin/erp/basic/modules/task-management"),
        ("report", "/vue-element-admin/erp/report/modules/c15-fund-account-transactions"),
        ("mall", "/vue-element-admin/erp/mall/modules/content"),
    ]
    completed = []
    for domain, base in cases:
        saved = post_data(session, headers, f"{base}/save", {
            "storeId": 1,
            "name": "验收临时记录",
            "status": "草稿",
            "liveRollback": True,
        })
        record_id = saved["recordId"]
        post_data(session, headers, f"{base}/action", {
            "recordId": record_id, "action": "启用", "note": "验收状态流转"
        })
        post_data(session, headers, f"{base}/action", {
            "recordId": record_id, "action": "删除"
        })
        completed.append(domain)

    saved = post_data(
        session, headers, "/vue-element-admin/erp/mama-box/content/save",
        {"storeId": 1, "title": "验收临时内容", "status": "草稿", "liveRollback": True},
    )
    record_id = saved["recordId"]
    post_data(
        session, headers,
        f"/vue-element-admin/erp/mama-box/content/{record_id}/发布", {},
    )
    post_data(
        session, headers,
        f"/vue-element-admin/erp/mama-box/content/{record_id}/删除", {},
    )
    completed.append("mamaBox")
    return completed


def report_resources() -> list[str]:
    source = read("src/config/report-pages.js")
    resources = re.findall(
        r"defineReport\(\s*'[^']+',\s*'([^']+)'", source
    )
    assert len(resources) == 43 and len(set(resources)) == 43
    return resources


def assert_static_semantic_isolation() -> dict[str, int]:
    marketing = read("src/config/marketing-pages.js")
    marketing_ids = re.findall(r"\n\s*(F\d{3}):\s*\{", marketing)
    marketing_keys = re.findall(r"\n\s*key:\s*'([^']+)'", marketing)
    assert len(marketing_ids) == 9 and len(set(marketing_ids)) == 9
    assert len(marketing_keys) == 9 and len(set(marketing_keys)) == 9
    assert "definition.key" in read("src/views/erp/marketing-workbench/index.vue")

    approval = read("src/config/approval-pages.js")
    assert "'审批中台'" in approval and "'审批流引擎'" in approval
    assert "contract" in approval and "business-flow" in approval

    store = read("src/views/erp/store-workbench/index.vue")
    assert "'门店与渠道（含转店）'" in store
    assert "'连锁多门店管理（资金归集/会员共享）'" in store

    registry = read("src/config/p0-operations-features.js")
    people_ids = [
        "F047", "F048", "F049", "F051", "F052", "F053", "F054",
        "F055", "F096", "F126",
    ]
    for feature_id in people_ids:
        assert f"id: '{feature_id}'" in registry

    basic_view = read("src/views/erp/basic-workbench/index.vue")
    assert ':data="filteredRows"' in basic_view
    assert "getBasicModuleData(this.config.key" in basic_view

    return {
        "approvalPages": 2,
        "marketingPages": len(marketing_ids),
        "organizationPerformanceFeatures": len(people_ids),
        "storePages": 2,
    }


def main() -> None:
    static_counts = assert_static_semantic_isolation()
    session = requests.Session()
    headers = login(session)

    counts: dict[str, dict[str, int]] = {
        "basic": {}, "report": {}, "risk": {}, "mall": {}, "mamaBox": {}
    }
    for resource in BASIC_RESOURCES:
        rows = fetch_list(
            session, headers, f"/vue-element-admin/erp/basic/modules/{resource}"
        )
        counts["basic"][resource] = len(rows)

    for resource in report_resources():
        rows = fetch_list(
            session, headers, f"/vue-element-admin/erp/report/modules/{resource}"
        )
        counts["report"][resource] = len(rows)

    rows = fetch_list(
        session, headers, "/vue-element-admin/erp/risk/modules/yuexi-risk"
    )
    counts["risk"]["yuexi-risk"] = len(rows)

    for resource in MALL_RESOURCES:
        rows = fetch_list(
            session, headers, f"/vue-element-admin/erp/mall/modules/{resource}"
        )
        counts["mall"][resource] = len(rows)

    response = session.get(
        f"{BASE_URL}/vue-element-admin/erp/mama-box/overview",
        headers=headers,
        params={"storeId": 1},
        timeout=10,
    )
    assert response.status_code == 200, response.text[:180]
    overview = response.json().get("data") or {}
    for resource in MALL_RESOURCES[:-1]:
        value = overview.get(resource) or []
        if isinstance(value, list):
            counts["mamaBox"][resource] = len(value)
    schedule = overview.get("schedule") or {}
    counts["mamaBox"]["class-schedule"] = len(schedule.get("rows") or [])

    server_backed = sum(len(group) for group in counts.values())
    non_empty = sum(
        1 for group in counts.values() for row_count in group.values()
        if row_count > 0
    )
    empty = {
        domain: [key for key, value in resources.items() if value == 0]
        for domain, resources in counts.items()
    }
    assert all(not resources for resources in empty.values()), empty
    write_cycles = assert_write_cycles(session, headers)
    print(json.dumps({
        "status": "passed",
        "serverBackedResources": server_backed,
        "nonEmptyResources": non_empty,
        "staticSemanticPages": static_counts,
        "emptyResources": empty,
        "writeCycles": write_cycles,
        "counts": counts,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Live loopback regression for the five nursing operational resources."""

from __future__ import annotations

import json
import os
from datetime import datetime
from urllib.error import HTTPError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen


BASE_URL = os.environ.get("ERP_API_URL", "http://127.0.0.1:3000").rstrip("/")
RESOURCES = {
    "record-visibility-scope": {
        "action": "停用",
        "required": ("ruleNo", "recordType", "scopeLevel", "applicableRole", "effectiveAt", "operator"),
        "payload": {"ruleNo": "RVS-LIVE", "recordType": "护理记录", "scopeLevel": "本人", "applicableRole": "管理员", "effectiveAt": "2026-08-01 18:00", "operator": "admin", "status": "启用"},
    },
    "missed-record-reminders": {
        "action": "确认处理",
        "required": ("reminderNo", "recordType", "dueAt", "owner", "reminderStatus"),
        "payload": {"reminderNo": "REM-LIVE", "recordType": "晨间护理记录", "dueAt": "2026-08-01 18:00", "owner": "admin", "reminderStatus": "待处理"},
    },
    "shift-handover": {
        "action": "确认接班",
        "required": ("handoverNo", "shiftName", "handoverBy", "receiveBy", "riskSummary", "handoverAt", "handoverStatus"),
        "payload": {"handoverNo": "SHF-LIVE", "shiftName": "早班", "handoverBy": "admin", "receiveBy": "李护士", "riskSummary": "资料已核验", "handoverAt": "2026-08-01 18:00", "handoverStatus": "待接班"},
    },
    "infection-management": {
        "action": "关闭",
        "required": ("riskNo", "riskType", "measure", "reviewer", "riskStatus"),
        "payload": {"riskNo": "INF-LIVE", "riskType": "日常筛查", "measure": "继续观察并记录", "reviewer": "admin", "riskStatus": "待复核"},
    },
    "nursing-task-orders": {
        "action": "指派",
        "required": ("taskNo", "taskType", "assignee", "dueAt", "taskStatus"),
        "payload": {"taskNo": "NTO-LIVE", "taskType": "常规护理", "assignee": "李护士", "dueAt": "2026-08-01 18:00", "taskStatus": "待指派"},
    },
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
    assert payload.get("code") == 20000, payload
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
    for store_id in (1, 2):
        for resource, config in RESOURCES.items():
            data = api(
                f"/vue-element-admin/erp/nursing/modules/{resource}",
                token=token,
                query={"storeId": store_id},
            )
            rows = data.get("list") or []
            assert len(rows) >= 3, f"store {store_id} {resource}: {len(rows)} rows"
            for row in rows[:3]:
                for field in config["required"]:
                    assert row.get(field), f"store {store_id} {resource}.{field} missing"
            endpoint_count += 1

    rollback_ids = []
    try:
        for resource, config in RESOURCES.items():
            body = {
                **config["payload"],
                "storeId": 1,
                "customerName": "李女士",
                "room": "201",
                "remark": "资料已核验",
                "liveRollback": datetime.now().isoformat(timespec="microseconds"),
            }
            saved = api(
                f"/vue-element-admin/erp/nursing/modules/{resource}/save",
                "POST",
                body,
                token,
            )
            record_id = saved.get("recordId")
            assert record_id, saved
            rollback_ids.append((resource, record_id))
            api(
                f"/vue-element-admin/erp/nursing/modules/{resource}/action",
                "POST",
                {"recordId": record_id, "action": config["action"]},
                token,
            )
    finally:
        for resource, record_id in rollback_ids:
            api(
                f"/vue-element-admin/erp/nursing/modules/{resource}/action",
                "POST",
                {"recordId": record_id, "action": "删除"},
                token,
            )

    for resource, record_id in rollback_ids:
        rows = api(
            f"/vue-element-admin/erp/nursing/modules/{resource}",
            token=token,
            query={"storeId": 1},
        ).get("list") or []
        assert record_id not in {row.get("recordId") for row in rows}

    print(
        json.dumps(
            {
                "status": "passed",
                "getEndpoints": endpoint_count,
                "writeResources": len(rollback_ids),
                "saveActionRollback": "passed",
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()

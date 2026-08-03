#!/usr/bin/env python3
"""Guard the nursing acceptance rows against workbench default filters."""

from __future__ import annotations

from datetime import date
import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = ROOT / "scripts" / "seed_local_acceptance_dataset.py"
SPEC = importlib.util.spec_from_file_location("acceptance_seed", SEED_PATH)
assert SPEC and SPEC.loader
seed = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(seed)
sys.path.insert(0, str(ROOT / "server"))
from erp_read_surfaces import NURSING_RESOURCES  # noqa: E402
from operational_records import (  # noqa: E402
    MODULE_RESOURCES,
    apply_action,
    identifier_field,
)


def main() -> None:
    today = date.today().isoformat()
    required_defaults = {
        "customerStatus": "- 已入住 -",
        "scheduleType": "护理排班",
        "planDate": today,
        "serviceDate": today,
    }
    required_resource_fields = {
        "record-visibility-scope": ("ruleNo", "recordType", "scopeLevel", "applicableRole", "effectiveAt", "operator"),
        "missed-record-reminders": ("reminderNo", "recordType", "dueAt", "owner", "reminderStatus"),
        "shift-handover": ("handoverNo", "shiftName", "handoverBy", "receiveBy", "riskSummary", "handoverAt", "handoverStatus"),
        "infection-management": ("riskNo", "riskType", "measure", "reviewer", "riskStatus"),
        "nursing-task-orders": ("taskNo", "taskType", "assignee", "dueAt", "taskStatus"),
    }
    expected_actions = {
        "missed-record-reminders": ("确认处理", "reminderStatus", "已完成"),
        "shift-handover": ("确认接班", "handoverStatus", "已接班"),
        "infection-management": ("关闭", "riskStatus", "已关闭"),
        "nursing-task-orders": ("指派", "taskStatus", "待执行"),
    }
    for resource in required_resource_fields:
        assert resource in NURSING_RESOURCES
        assert resource in MODULE_RESOURCES["NURSING"]
    for resource in seed.RESOURCES["NURSING"]:
        payload = seed.record_payload(
            resource,
            1,
            ("李四", "18810001001", "安安"),
            "201",
            "张敏",
        )
        for field, expected in required_defaults.items():
            actual = payload.get(field)
            assert actual == expected, (
                f"{resource}.{field}: expected {expected!r}, got {actual!r}"
            )
        assert payload.get("demoBatch") == seed.BATCH
        assert payload.get("remark") == "资料已核验"
        for field in required_resource_fields.get(resource, ()):
            assert payload.get(field), f"{resource}.{field} must be populated"
        if resource in required_resource_fields:
            assert payload.get(identifier_field(resource))
        if resource in expected_actions:
            action, field, expected = expected_actions[resource]
            patch, _ = apply_action(resource, action, {})
            assert patch.get(field) == expected
    print(
        f"nursing acceptance defaults: "
        f"{len(seed.RESOURCES['NURSING'])}/{len(seed.RESOURCES['NURSING'])} passed"
    )


if __name__ == "__main__":
    main()

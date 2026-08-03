#!/usr/bin/env python3
"""Static release gate for the 104-item ERP Web inventory.

This intentionally *does not* treat a sidebar entry as proof that a feature is
usable.  It verifies the source-of-truth registry, canonical menu assignment,
route component selection and the relevant API prefix.  Findings are written
as machine-readable JSON so release work can prioritise real failures instead
of concealing them behind a generic workbench page.

The check is read-only.  It never calls the local API and never writes project
source; it only writes the requested audit artifact under ``docs/验收``.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "src/config/erp-feature-registry.js"
ROUTER = ROOT / "src/router/index.js"
SERVER = ROOT / "server/mvp_api.py"
REPORT = ROOT / "docs/验收/ERP104静态可达性核查.json"


# The canonical product group decides which workbench route is generated.
# Keep this map explicit: an unknown group must be reported rather than quietly
# assumed to work.
GROUP_COMPONENTS = {
    "dashboard": "dashboard",
    "customer": "customer-workbench",
    "service": "customer-service",
    "member": "member-workbench",
    "sales": "sales-workbench",
    "finance": "finance-workbench",
    "approval": "approval-workbench",
    "schedule": "schedule-workbench",
    "room": "room-workbench",
    "nursing": "nursing-workbench",
    "baby": "baby-workbench",
    "diet": "diet-workbench",
    "warehouse": "inventory-workbench",
    "recovery": "rehab-workbench",
    "research": "research-workbench",
    "matron": "maternity-nurse-workbench",
    "people": "people-workbench",
    "marketing": "customer-workbench",
    "report": "report-workbench",
    "store": "store-workbench",
    "system": "system-workbench",
}

GROUP_API_PREFIXES = {
    "sales": "/vue-element-admin/erp/sales/modules",
    "finance": "/vue-element-admin/erp/finance",
    "nursing": "/vue-element-admin/erp/nursing/modules",
    "baby": "/vue-element-admin/erp/baby/modules",
    "diet": "/vue-element-admin/erp/diet/modules",
    "recovery": "/vue-element-admin/erp/rehab",
}

# These are not merely generic shells: the target resources are absent from the
# current recovery handler.  Keep the exception list visible in the generated
# failure list until corresponding backend resources are implemented.
RECOVERY_RESOURCE_BY_FEATURE = {
    "F099": "recovery-programs",
    "F100": "recovery-schedule",
    "F101": "postpartum-assessments",
    "F102": "recovery-service-tracking",
    "F103": "recovery-store-dashboard",
    "F104": "recovery-upsell",
    "F105": "recovery-assets",
    "F106": "recovery-staff-performance",
}


def parse_registry(source: str) -> list[dict[str, str]]:
    pattern = re.compile(
        r"\['(?P<id>F\d{3})','(?P<title>[^']*)','(?P<domain>[^']*)','(?P<priority>P\d)'\]"
    )
    return [match.groupdict() for match in pattern.finditer(source)]


def parse_menu_assignment(source: str) -> tuple[dict[str, str], Counter[str]]:
    start = source.find("const productMenuDefinitions = [")
    end = source.find("const featureById =", start)
    if start < 0 or end < 0:
        return {}, Counter()
    block = source[start:end]
    assignment: dict[str, str] = {}
    occurrence: Counter[str] = Counter()
    # A group literal has exactly one array of feature ids.  Capture the key
    # first, then assign every Fxxx in its trailing array.
    group_pattern = re.compile(
        r"\['(?P<group>[a-z]+)'\s*,.*?\[(?P<ids>(?:\s*'F\d{3}'\s*,?)+)\]\]",
        re.DOTALL,
    )
    for match in group_pattern.finditer(block):
        group = match.group("group")
        for feature_id in re.findall(r"'(?P<id>F\d{3})'", match.group("ids")):
            occurrence[feature_id] += 1
            assignment.setdefault(feature_id, group)
    return assignment, occurrence


def has_server_prefix(server_source: str, prefix: str) -> bool:
    return prefix in server_source


def finding(feature: dict[str, str], group: str | None, component: str | None,
            code: str, severity: str, detail: str) -> dict[str, str]:
    return {
        "featureId": feature["id"],
        "featureName": feature["title"],
        "priority": feature["priority"],
        "menuGroup": group or "",
        "route": "/dashboard" if group == "dashboard" else (f"/{group}/item-*" if group else ""),
        "component": component or "",
        "code": code,
        "severity": severity,
        "detail": detail,
    }


def main() -> int:
    registry_source = REGISTRY.read_text(encoding="utf-8")
    router_source = ROUTER.read_text(encoding="utf-8")
    server_source = SERVER.read_text(encoding="utf-8")
    registry = parse_registry(registry_source)
    registry_ids = [item["id"] for item in registry]
    registry_by_id = {item["id"]: item for item in registry}
    assignments, occurrences = parse_menu_assignment(router_source)
    # F001/F002 intentionally share the single official dashboard entry. They
    # are represented in route meta rather than the sidebar group array.
    dashboard_feature_ids = {
        item.strip()
        for value in re.findall(r"featureId:\s*'([^']+)'", router_source)
        for item in value.split(",")
        if re.fullmatch(r"F\d{3}", item.strip())
    }
    for feature_id in dashboard_feature_ids:
        if feature_id in registry_by_id and feature_id not in assignments:
            assignments[feature_id] = "dashboard"
            occurrences[feature_id] = 1
    findings: list[dict[str, str]] = []

    if len(registry) != 104:
        findings.append({
            "featureId": "REGISTRY", "featureName": "ERP功能注册表",
            "priority": "P0", "menuGroup": "", "route": "",
            "component": "", "code": "REGISTRY_COUNT_INVALID",
            "severity": "FAIL",
            "detail": f"erp-feature-registry 应为104项，当前为{len(registry)}项。",
        })
    for feature_id, count in sorted(Counter(registry_ids).items()):
        if count > 1:
            feature = registry_by_id[feature_id]
            findings.append(finding(
                feature, None, None, "REGISTRY_ID_DUPLICATE", "FAIL",
                f"功能编号 {feature_id} 在注册表出现 {count} 次。",
            ))

    for feature in registry:
        feature_id = feature["id"]
        group = assignments.get(feature_id)
        component = GROUP_COMPONENTS.get(group or "")
        if not group:
            findings.append(finding(
                feature, None, None, "MENU_ROUTE_MISSING", "FAIL",
                "未在 productMenuDefinitions 找到唯一菜单分配，无法生成正式侧栏路由。",
            ))
            continue
        if occurrences[feature_id] != 1:
            findings.append(finding(
                feature, group, component, "MENU_ROUTE_DUPLICATE", "FAIL",
                f"菜单功能编号出现 {occurrences[feature_id]} 次，必须恰好一次。",
            ))
        if not component:
            findings.append(finding(
                feature, group, None, "ROUTE_COMPONENT_UNKNOWN", "FAIL",
                "菜单组没有明确页面组件映射。",
            ))

        prefix = GROUP_API_PREFIXES.get(group)
        if prefix and not has_server_prefix(server_source, prefix):
            if group == "baby":
                code = "BACKEND_API_PENDING"
                detail = (
                    "宝宝照护页面已停止请求不存在的接口并明确显示待接入，"
                    f"但后端前缀 {prefix} 尚未注册，暂不能标记为完整业务闭环。"
                )
            else:
                code = "API_PREFIX_MISSING"
                detail = f"前端预期接口前缀 {prefix} 未在 mvp_api.py 注册。"
            findings.append(finding(
                feature, group, component, code, "FAIL", detail,
            ))

        if group == "approval" and "approval: 'approval-workbench'" not in router_source:
            findings.append(finding(
                feature, group, component, "GENERIC_WORKBENCH_SHARED", "WARN",
                "审批中心当前复用财务工作台；应核对是否能覆盖行政与业务审批，不可仅以菜单可进入判定完成。",
            ))
        elif group == "schedule" and "schedule: 'schedule-workbench'" not in router_source:
            findings.append(finding(
                feature, group, component, "GENERIC_WORKBENCH_SHARED", "WARN",
                "预约与排班菜单默认复用客房工作台；需逐页确认是否被 /mvp/appointments 专用路由覆盖。",
            ))

        if feature_id in RECOVERY_RESOURCE_BY_FEATURE:
            resource = RECOVERY_RESOURCE_BY_FEATURE[feature_id]
            if f'"{resource}"' not in server_source:
                findings.append(finding(
                    feature, group, component, "BACKEND_RESOURCE_MISSING", "FAIL",
                    f"产康页面预期资源 {resource} 未在 recovery handler 白名单中。",
                ))

    # Shared component is a review signal, not a failure by itself: sales and
    # finance deliberately use one workbench with different backend resources.
    component_groups: dict[str, list[str]] = {}
    for feature_id, group in assignments.items():
        component_groups.setdefault(GROUP_COMPONENTS.get(group, ""), []).append(feature_id)
    for component, feature_ids in sorted(component_groups.items()):
        if component and len(feature_ids) >= 8:
            findings.append({
                "featureId": "GROUP_REVIEW",
                "featureName": "通用工作台复用检查",
                "priority": "P0",
                "menuGroup": ",".join(sorted({assignments[item] for item in feature_ids})),
                "route": "",
                "component": component,
                "code": "GENERIC_COMPONENT_REVIEW",
                "severity": "WARN",
                "detail": f"{component} 承载 {len(feature_ids)} 项功能；需以独立资源、字段和状态流转证明不是重复页面。",
            })

    report = {
        "schemaVersion": 1,
        "registryExpected": 104,
        "registryActual": len(registry),
        "uniqueRegistryIds": len(set(registry_ids)),
        "menuAssigned": len(assignments),
        "failCount": sum(item["severity"] == "FAIL" for item in findings),
        "warningCount": sum(item["severity"] == "WARN" for item in findings),
        "findings": findings,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["failCount"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

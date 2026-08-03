#!/usr/bin/env python3
"""Static menu/route audit for the three evidence-backed operating accounts.

This script does not import Vue or touch the database. It verifies that the
canonical 104-feature registry, generated sidebar, role boundaries and global
quick-entry targets remain mutually consistent for 韩新、许曼、董丽霞.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUTER_PATH = ROOT / "src" / "router" / "index.js"
PERMISSION_PATH = ROOT / "src" / "store" / "modules" / "permission.js"
REGISTRY_PATH = ROOT / "src" / "config" / "erp-feature-registry.js"
NOTIFICATION_PATH = ROOT / "src" / "layout" / "components" / "NotificationCenter.vue"
NAVBAR_PATH = ROOT / "src" / "layout" / "components" / "Navbar.vue"
DASHBOARD_PATH = ROOT / "src" / "views" / "dashboard" / "index.vue"
SURFACE_MIGRATION_PATH = ROOT / "database" / "mysql" / "migrations" / "V20260801_032__role_surface_permission_alignment.sql"

ROLE_CASES = {
    "韩新": {
        "role": "SALES_MANAGER",
        "requiredGroups": {"customer", "sales", "approval", "schedule", "room"},
    },
    "许曼": {
        "role": "RECOVERY_THERAPIST",
        "requiredGroups": {"customer", "schedule", "recovery"},
    },
    "董丽霞": {
        "role": "HOUSEKEEPER",
        "requiredGroups": {"customer", "room"},
    },
}


def between(source: str, start: str, end: str) -> str:
    if start not in source or end not in source:
        raise AssertionError(f"source block missing: {start} ... {end}")
    return source.split(start, 1)[1].split(end, 1)[0]


def parse_registry(source: str) -> dict[str, str]:
    return {
        feature_id: title
        for feature_id, title in re.findall(
            r"\['(F\d{3})'\s*,\s*'([^']+)'\s*,", source
        )
    }


def parse_menu_groups(source: str) -> dict[str, dict]:
    block = between(source, "const productMenuDefinitions =", "const featureById =")
    groups = {}
    pattern = re.compile(
        r"\['([a-z]+)'\s*,\s*'([^']+)'\s*,\s*'[^']+'\s*,\s*'[^']+'\s*,\s*\[([^\]]*)\]\]"
    )
    for key, title, raw_ids in pattern.findall(block):
        groups[key] = {
            "title": title,
            "featureIds": re.findall(r"'(F\d{3})'", raw_ids),
        }
    return groups


def parse_group_roles(source: str) -> dict[str, set[str]]:
    block = between(source, "const groupRoleMatrix =", "const groupRoles =")
    result = {}
    for key, raw_roles in re.findall(r"^\s*([a-z]+):\s*\[([^\]]*)\]", block, re.M):
        result[key] = set(re.findall(r"'([A-Z_]+)'", raw_roles))
    return result


def generated_paths(groups: dict[str, dict]) -> set[str]:
    result = {"/dashboard", "/customer/signing-workbench", "/customer/member-assets"}
    for key, group in groups.items():
        for index, _feature_id in enumerate(group["featureIds"], start=1):
            result.add(f"/{key}/item-{index}")
    result.update({"/mvp/room-map", "/mvp/smart-rooms", "/mvp/appointments"})
    return result


def literal_paths(source: str) -> set[str]:
    return set(re.findall(r"path:\s*'(/[^']+)'", source))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fail-on-findings", action="store_true")
    args = parser.parse_args()

    router = ROUTER_PATH.read_text(encoding="utf-8")
    permission = PERMISSION_PATH.read_text(encoding="utf-8")
    registry_source = REGISTRY_PATH.read_text(encoding="utf-8")
    notification = NOTIFICATION_PATH.read_text(encoding="utf-8")
    navbar = NAVBAR_PATH.read_text(encoding="utf-8")
    dashboard = DASHBOARD_PATH.read_text(encoding="utf-8")
    surface_migration = SURFACE_MIGRATION_PATH.read_text(encoding="utf-8")

    registry = parse_registry(registry_source)
    groups = parse_menu_groups(router)
    group_roles = parse_group_roles(router)
    paths = generated_paths(groups)
    findings: list[dict] = []

    assert len(registry) == 104, f"feature registry must contain 104 unique ids, got {len(registry)}"
    assert groups, "canonical product menu definitions were not parsed"
    assert set(groups) == set(group_roles), "menu groups and role matrix groups differ"

    menu_ids = [feature_id for group in groups.values() for feature_id in group["featureIds"]]
    assert len(menu_ids) == len(set(menu_ids)), "feature ids are duplicated in the sidebar"
    assert set(menu_ids).issubset(registry), "sidebar references an unknown feature id"
    assert set(registry) - set(menu_ids) == {"F001", "F002"}, "only dashboard F001/F002 may stay outside sidebar groups"

    assert "if (!hadChildren || tmp.children.length)" in permission, "empty-parent removal guard missing"
    assert "roles.some(role => route.meta.roles.includes(role))" in permission, "role route filter missing"
    assert "const erpDeliveryRoutes = [...erpRoutes, p0OperationsRoute]" in router
    async_block = router.split("export const asyncRoutes =", 1)[1]
    assert async_block.index("erpDeliveryRoutes") < async_block.index("{ path: '*', redirect: '/404'")

    account_results = []
    for username, case in ROLE_CASES.items():
        role = case["role"]
        visible_groups = {
            key for key, roles in group_roles.items() if role in roles
        }
        missing_groups = sorted(case["requiredGroups"] - visible_groups)
        assert not missing_groups, f"{username} missing evidence-required groups: {missing_groups}"
        empty_groups = sorted(key for key in visible_groups if not groups[key]["featureIds"])
        assert not empty_groups, f"{username} has empty parent groups: {empty_groups}"
        visible_paths = {
            path for path in paths
            if path == "/dashboard" or any(path.startswith(f"/{key}/") for key in visible_groups)
        }
        visible_paths.add("/dashboard")
        feature_count = sum(len(groups[key]["featureIds"]) for key in visible_groups)
        account_results.append({
            "username": username,
            "role": role,
            "visibleGroups": sorted(visible_groups),
            "visibleFeatureCount": feature_count,
            "registeredTargetCount": len(visible_paths),
            "emptyParents": 0,
        })

    notification_targets = literal_paths(notification)
    navbar_targets = literal_paths(navbar)
    dashboard_targets = set(re.findall(r"route:\s*'(/[^']+)'", dashboard))
    for surface, targets in (
        ("notification", notification_targets),
        ("navbar", navbar_targets),
        ("dashboard", dashboard_targets),
    ):
        missing = sorted(target for target in targets if target not in paths)
        assert not missing, f"{surface} contains unregistered targets: {missing}"

    assert ".filter(item => this.canAccessRoute(item.route))" in notification
    assert "canAccessRoute(targetPath)" in dashboard
    assert "ROOM.VIEW" in surface_migration and "ROOM.QUERY" in surface_migration
    for case in ROLE_CASES.values():
        assert case["role"] in surface_migration, f"V032 missing {case['role']}"

    # Navbar does not call canAccessRoute. Its two result targets therefore
    # need independent evidence: all three roles now own the customer parent,
    # while V032 grants scoped ROOM read/query for the hidden room-map target.
    assert "/customer/signing-workbench" in navbar_targets
    assert "/mvp/room-map" in navbar_targets
    for username, case in ROLE_CASES.items():
        role = case["role"]
        if role not in group_roles["customer"]:
            findings.append({
                "severity": "error",
                "username": username,
                "surface": "navbar-customer-search",
                "message": "客户搜索会跳转客户签约页，但该角色没有客户父菜单。",
            })

    result = {
        "status": "passed-with-findings" if findings else "passed",
        "registryFeatures": len(registry),
        "sidebarFeatures": len(menu_ids),
        "dashboardOnlyFeatures": ["F001", "F002"],
        "registeredPaths": len(paths),
        "accounts": account_results,
        "quickEntryTargets": {
            "notification": sorted(notification_targets),
            "navbar": sorted(navbar_targets),
            "dashboard": sorted(dashboard_targets),
        },
        "findings": findings,
        "runtimeMutations": 0,
        "businessRecordsCreated": 0,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if findings and args.fail_on_findings else 0


if __name__ == "__main__":
    raise SystemExit(main())

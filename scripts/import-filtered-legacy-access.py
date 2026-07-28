#!/usr/bin/env python3
"""Import the retained legacy ERP roles, users and exact grants into MySQL.

The source CSV files stay in .private and are never copied into tracked files.
Passwords are not present in the legacy export. New active accounts receive the
temporary password supplied through ERP_LEGACY_ACCOUNT_INITIAL_PASSWORD.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.mvp_api import connect, hash_password


SOURCE_DIR = ROOT / ".private" / "system-settings-import"
SOURCE_SYSTEM = "LEGACY_ERP"
TENANT_ID = 1

EXCLUDED_ROLES = {
    22: "面点师",
    66: "司机",
    67: "保安",
    68: "洗衣工",
    69: "公共保洁",
    78: "客房保洁",
    79: "勤杂工",
    83: "企划",
}

# Keep stable application codes for roles already used by the integrated MVP.
# Other codes preserve the legacy role id so duplicate names remain distinct.
ROLE_CODES = {
    2: "ERP_ADMIN",
    5: "SALES_MANAGER",
    7: "FINANCE_SPECIALIST",
    8: "NURSE",
    9: "HEAD_NURSE",
    10: "KITCHEN_STAFF",
    12: "OPERATIONS_VP",
    15: "HEAD_CHEF",
    18: "HR_MANAGER",
    21: "HOUSEKEEPER",
    62: "SALES_CONSULTANT",
    64: "RECOVERY_MANAGER",
    65: "LOGISTICS_MANAGER",
    70: "MARKETING_DIRECTOR",
    71: "NURSING_DIRECTOR",
    73: "GENERAL_MANAGER",
    74: "RECOVERY_THERAPIST",
    75: "WAREHOUSE_KEEPER",
    77: "OPERATIONS_DIRECTOR",
    82: "MATERNAL_INFANT_CAREGIVER",
    84: "RECOVERY_TECHNICIAN",
    85: "BEAUTY_STORE_MANAGER",
    86: "DOMESTIC_SERVICE_MANAGER",
    89: "LEGACY_NURSE_89",
    91: "HH_GENERAL_MANAGER",
    92: "HH_DEPUTY_GENERAL_MANAGER",
    93: "BEAUTY_TECHNICIAN",
    94: "NAIL_LASH_TECHNICIAN",
}

MANAGEMENT_ROLE_IDS = {
    2,
    5,
    9,
    12,
    15,
    18,
    64,
    65,
    70,
    71,
    73,
    77,
    85,
    86,
    91,
    92,
}


def read_csv(name: str) -> list[dict]:
    path = SOURCE_DIR / name
    if not path.exists():
        raise SystemExit(f"Missing source file: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def integer(value, default=0) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def truthy(value) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def source_data() -> dict:
    roles = read_csv("config-roles.csv")
    users = read_csv("config-users.csv")
    relations = read_csv("config-userRoleRelations.csv")
    departments = read_csv("config-departments.csv")
    web_catalog = read_csv("config-roleWebPermissionCatalog.csv")
    web_grants = read_csv("config-roleWebPermissionGrants.csv")
    app_catalog = read_csv("config-roleAppPermissionCatalog.csv")
    app_grants = read_csv("config-roleAppPermissionGrants.csv")
    data_scopes = read_csv("config-roleSystemSettingDataScopes.csv")

    role_by_id = {integer(row["KeyId"]): row for row in roles}
    actual_exclusions = {
        role_id: role_by_id.get(role_id, {}).get("RoleName")
        for role_id in EXCLUDED_ROLES
    }
    if actual_exclusions != EXCLUDED_ROLES:
        raise SystemExit(
            "Excluded legacy role ids no longer match the captured role names."
        )

    retained_role_ids = set(role_by_id) - set(EXCLUDED_ROLES)
    if retained_role_ids != set(ROLE_CODES):
        raise SystemExit("ROLE_CODES must cover every retained legacy role exactly.")

    relations_by_user = defaultdict(list)
    for relation in relations:
        relations_by_user[integer(relation["userKeyId"])].append(
            integer(relation["roleKeyId"])
        )
    retained_user_ids = {
        user_id
        for user_id, role_ids in relations_by_user.items()
        if any(role_id in retained_role_ids for role_id in role_ids)
    }
    retained_relations = [
        row
        for row in relations
        if integer(row["userKeyId"]) in retained_user_ids
        and integer(row["roleKeyId"]) in retained_role_ids
    ]
    retained_users = [
        row for row in users if integer(row["KeyId"]) in retained_user_ids
    ]

    return {
        "roles": roles,
        "users": users,
        "relations": relations,
        "departments": departments,
        "web_catalog": web_catalog,
        "web_grants": web_grants,
        "app_catalog": app_catalog,
        "app_grants": app_grants,
        "data_scopes": data_scopes,
        "role_by_id": role_by_id,
        "retained_role_ids": retained_role_ids,
        "retained_users": retained_users,
        "retained_user_ids": retained_user_ids,
        "retained_relations": retained_relations,
        "relations_by_user": relations_by_user,
    }


def source_summary(data: dict) -> dict:
    retained_role_ids = data["retained_role_ids"]
    filtered_web_grants = sum(
        integer(row["roleId"]) in retained_role_ids
        for row in data["web_grants"]
    )
    filtered_app_grants = sum(
        integer(row["roleId"]) in retained_role_ids
        for row in data["app_grants"]
    )
    filtered_scopes = sum(
        integer(row["roleId"]) in retained_role_ids
        for row in data["data_scopes"]
    )
    disabled = sum(
        truthy(row.get("IsDisabled"))
        or "禁用" in str(row.get("UserName", ""))
        for row in data["retained_users"]
    )
    return {
        "sourceRoles": len(data["roles"]),
        "importedRoles": len(retained_role_ids),
        "excludedRoles": len(EXCLUDED_ROLES),
        "sourceUsers": len(data["users"]),
        "importedUsers": len(data["retained_users"]),
        "activeUsers": len(data["retained_users"]) - disabled,
        "disabledUsers": disabled,
        "excludedUsers": len(data["users"]) - len(data["retained_users"]),
        "roleRelations": len(data["retained_relations"]),
        "webCatalog": len(data["web_catalog"]),
        "webGrants": filtered_web_grants,
        "appCatalog": len(data["app_catalog"]),
        "appGrants": filtered_app_grants,
        "dataScopeGrants": filtered_scopes,
        "excludedRoleNames": list(EXCLUDED_ROLES.values()),
    }


def permission_code(surface: str, menu_id: int, button_id: int) -> str:
    return f"LEGACY.{surface.upper()}.N{menu_id}.B{button_id}"


def build_department_helpers(data: dict):
    departments = {
        integer(row["KeyId"]): row for row in data["departments"]
    }

    def store_for(department_id: int) -> int:
        seen = set()
        current = department_id
        while current and current not in seen:
            seen.add(current)
            if current == 6:
                return 1
            if current == 21:
                return 2
            current = integer(departments.get(current, {}).get("ParentId"))
        return 1

    return departments, store_for


def upsert_roles(cursor, data: dict) -> dict[int, int]:
    role_ids = {}
    for legacy_id in sorted(data["retained_role_ids"]):
        row = data["role_by_id"][legacy_id]
        code = ROLE_CODES[legacy_id]
        role_type = (
            "MANAGEMENT" if legacy_id in MANAGEMENT_ROLE_IDS else "JOB"
        )
        cursor.execute(
            """
            SELECT role_id FROM roles
            WHERE tenant_id=%s AND code=%s
            """,
            (TENANT_ID, code),
        )
        existing = cursor.fetchone()
        description = (
            str(row.get("Remark") or "").strip()
            or "由原ERP角色及授权明细迁移；以legacy_role_id作为稳定标识。"
        )
        if existing:
            role_id = existing["role_id"]
            cursor.execute(
                """
                UPDATE roles
                SET name=%s, role_type=%s, legacy_role_id=%s,
                    source_system=%s, description=%s, status='ACTIVE'
                WHERE role_id=%s
                """,
                (
                    row["RoleName"],
                    role_type,
                    legacy_id,
                    SOURCE_SYSTEM,
                    description,
                    role_id,
                ),
            )
        else:
            cursor.execute(
                """
                INSERT INTO roles(
                  tenant_id, code, legacy_role_id, source_system, name,
                  role_type, perms_json, is_manager, is_system, data_scope,
                  description, created_at, status
                ) VALUES (%s,%s,%s,%s,%s,%s,'[]',%s,0,1,%s,NOW(),'ACTIVE')
                """,
                (
                    TENANT_ID,
                    code,
                    legacy_id,
                    SOURCE_SYSTEM,
                    row["RoleName"],
                    role_type,
                    int(legacy_id in MANAGEMENT_ROLE_IDS),
                    description,
                ),
            )
            role_id = cursor.lastrowid
        role_ids[legacy_id] = role_id

    for legacy_id, role_name in EXCLUDED_ROLES.items():
        cursor.execute(
            """
            INSERT INTO legacy_role_exclusions(legacy_role_id, role_name, reason)
            VALUES (%s,%s,'当前组织无该岗位，按业务方确认不导入')
            ON DUPLICATE KEY UPDATE
              role_name=VALUES(role_name), reason=VALUES(reason)
            """,
            (legacy_id, role_name),
        )
        cursor.execute(
            """
            UPDATE roles SET status='RETIRED'
            WHERE tenant_id=%s AND source_system=%s AND legacy_role_id=%s
            """,
            (TENANT_ID, SOURCE_SYSTEM, legacy_id),
        )

    # The old normalized marketing placeholder represents the excluded 企划 role.
    cursor.execute(
        """
        UPDATE roles SET status='RETIRED'
        WHERE tenant_id=%s AND code='MARKETING_SPECIALIST'
          AND legacy_role_id IS NULL
        """,
        (TENANT_ID,),
    )
    return role_ids


def upsert_permission_catalog(cursor, rows: list[dict]) -> dict[tuple, int]:
    mapping = {}
    for row in rows:
        surface = str(row["surface"]).strip().upper()
        menu_id = integer(row["menuId"])
        button_id = integer(row.get("buttonId"))
        code = permission_code(surface, menu_id, button_id)
        menu_name = str(row.get("menuName") or "").strip()
        button_name = str(row.get("buttonName") or "").strip()
        display_name = (
            f"{menu_name}/{button_name}" if button_name else menu_name
        )[:128]
        cursor.execute(
            """
            INSERT INTO permissions(
              code, module_code, resource_type, action_code,
              name, sort_order, status
            ) VALUES (%s,%s,%s,'ACCESS',%s,0,'ACTIVE')
            ON DUPLICATE KEY UPDATE name=VALUES(name), status='ACTIVE'
            """,
            (
                code,
                f"LEGACY_{surface}",
                "BUTTON" if button_id else "MENU",
                display_name,
            ),
        )
        cursor.execute(
            "SELECT permission_id FROM permissions WHERE code=%s",
            (code,),
        )
        permission_id = cursor.fetchone()["permission_id"]
        cursor.execute(
            """
            INSERT INTO legacy_permission_resources(
              surface, menu_id, button_id, menu_name, button_name, permission_id
            ) VALUES (%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
              menu_name=VALUES(menu_name),
              button_name=VALUES(button_name),
              permission_id=VALUES(permission_id)
            """,
            (
                surface,
                menu_id,
                button_id,
                menu_name,
                button_name or None,
                permission_id,
            ),
        )
        mapping[(surface, menu_id, button_id)] = permission_id
    return mapping


def import_permission_grants(
    cursor,
    data: dict,
    role_ids: dict[int, int],
    permission_ids: dict[tuple, int],
):
    retained_db_roles = tuple(role_ids.values())
    placeholders = ",".join(["%s"] * len(retained_db_roles))
    cursor.execute(
        f"""
        DELETE rp FROM role_permissions rp
        JOIN permissions p ON p.permission_id=rp.permission_id
        WHERE rp.role_id IN ({placeholders}) AND p.code LIKE 'LEGACY.%%'
        """,
        retained_db_roles,
    )
    imported = {"web": 0, "app": 0}
    for surface, rows in (
        ("WEB", data["web_grants"]),
        ("APP", data["app_grants"]),
    ):
        for row in rows:
            legacy_role_id = integer(row["roleId"])
            role_id = role_ids.get(legacy_role_id)
            if not role_id:
                continue
            key = (
                surface,
                integer(row["menuId"]),
                integer(row.get("buttonId")),
            )
            permission_id = permission_ids.get(key)
            if not permission_id:
                raise RuntimeError(f"Permission catalog entry missing for {key}")
            cursor.execute(
                """
                INSERT IGNORE INTO role_permissions(
                  role_id, permission_id, effect
                ) VALUES (%s,%s,'ALLOW')
                """,
                (role_id, permission_id),
            )
            imported[surface.lower()] += 1
    return imported


def import_data_scopes(cursor, data: dict, role_ids: dict[int, int]) -> int:
    placeholders = ",".join(["%s"] * len(role_ids))
    cursor.execute(
        f"""
        DELETE FROM legacy_role_data_scope_grants
        WHERE role_id IN ({placeholders})
        """,
        tuple(role_ids.values()),
    )
    imported = 0
    for row in data["data_scopes"]:
        role_id = role_ids.get(integer(row["roleId"]))
        if not role_id:
            continue
        cursor.execute(
            """
            INSERT INTO legacy_role_data_scope_grants(
              role_id, nav_id, department_id, parent_department_id,
              department_name, granted, empty_result
            ) VALUES (%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
              parent_department_id=VALUES(parent_department_id),
              department_name=VALUES(department_name),
              granted=VALUES(granted),
              empty_result=VALUES(empty_result)
            """,
            (
                role_id,
                integer(row["navId"]),
                integer(row["departmentId"]),
                integer(row.get("parentDepartmentId")) or None,
                str(row.get("departmentName") or "").strip(),
                int(truthy(row.get("granted"))),
                int(truthy(row.get("emptyResult"))),
            ),
        )
        imported += 1
    return imported


def load_staff(cursor):
    cursor.execute(
        """
        SELECT staff_id, name, department, department_id, store_id
        FROM staff
        WHERE tenant_id=%s AND employment_status='ACTIVE'
        ORDER BY staff_id
        """,
        (TENANT_ID,),
    )
    by_name = defaultdict(list)
    for row in cursor.fetchall():
        by_name[row["name"]].append(row)
    cursor.execute(
        """
        SELECT staff_id, user_id FROM user_accounts
        WHERE staff_id IS NOT NULL
        """
    )
    bound_staff = {
        row["staff_id"]: row["user_id"] for row in cursor.fetchall()
    }
    return by_name, bound_staff


def match_staff(row: dict, by_name: dict, bound_staff: dict, account_id=None):
    name = str(row.get("TrueName") or "").strip()
    department = str(row.get("depname") or "").strip()
    candidates = by_name.get(name, [])
    if len(candidates) > 1 and department:
        exact = [
            item
            for item in candidates
            if str(item.get("department") or "").strip() == department
        ]
        if len(exact) == 1:
            candidates = exact
    if len(candidates) != 1:
        return None
    candidate = candidates[0]
    owner = bound_staff.get(candidate["staff_id"])
    if owner is not None and owner != account_id:
        return None
    return candidate


def upsert_accounts(
    cursor,
    data: dict,
    role_ids: dict[int, int],
    initial_password: str,
) -> dict:
    departments, store_for = build_department_helpers(data)
    by_name, bound_staff = load_staff(cursor)
    retained_ids = sorted(data["retained_user_ids"])
    placeholders = ",".join(["%s"] * len(retained_ids))
    cursor.execute(
        f"""
        DELETE FROM user_accounts
        WHERE tenant_id=%s AND source_system=%s
          AND legacy_user_id NOT IN ({placeholders})
        """,
        (TENANT_ID, SOURCE_SYSTEM, *retained_ids),
    )

    role_relations = defaultdict(list)
    for row in data["retained_relations"]:
        role_relations[integer(row["userKeyId"])].append(
            integer(row["roleKeyId"])
        )

    imported = 0
    active = 0
    disabled = 0
    linked_staff = 0
    unmatched_staff = []
    for row in sorted(
        data["retained_users"], key=lambda item: integer(item["KeyId"])
    ):
        legacy_user_id = integer(row["KeyId"])
        legacy_username = str(row.get("UserName") or "").strip()
        is_disabled = (
            truthy(row.get("IsDisabled")) or "禁用" in legacy_username
        )
        username = (
            f"legacy-disabled-{legacy_user_id}"
            if is_disabled
            else legacy_username
        )
        if not username:
            username = f"legacy-user-{legacy_user_id}"
            is_disabled = True

        cursor.execute(
            """
            SELECT user_id, password_hash, staff_id, must_change_password
            FROM user_accounts
            WHERE tenant_id=%s AND source_system=%s AND legacy_user_id=%s
            """,
            (TENANT_ID, SOURCE_SYSTEM, legacy_user_id),
        )
        existing = cursor.fetchone()
        if not existing and not is_disabled:
            cursor.execute(
                """
                SELECT user_id, password_hash, staff_id, must_change_password
                FROM user_accounts
                WHERE tenant_id=%s AND username=%s
                """,
                (TENANT_ID, username),
            )
            existing = cursor.fetchone()

        account_id = existing["user_id"] if existing else None
        staff = None
        if existing and existing.get("staff_id"):
            cursor.execute(
                """
                SELECT staff_id, name, department, department_id, store_id
                FROM staff WHERE staff_id=%s
                """,
                (existing["staff_id"],),
            )
            staff = cursor.fetchone()
        elif not is_disabled:
            staff = match_staff(row, by_name, bound_staff, account_id)

        department_id = staff.get("department_id") if staff else None
        source_department_id = integer(row.get("DepartmentId"))
        default_store_id = (
            staff.get("store_id")
            if staff
            else store_for(source_department_id)
        )
        status = "DISABLED" if is_disabled else "ACTIVE"
        password_hash = (
            existing["password_hash"]
            if existing
            else hash_password(initial_password)
        )
        must_change = (
            existing["must_change_password"]
            if existing
            else int(not is_disabled)
        )

        if existing:
            cursor.execute(
                """
                UPDATE user_accounts
                SET legacy_user_id=%s, legacy_username=%s, username=%s,
                    staff_id=%s, default_store_id=%s, department_id=%s,
                    status=%s, source_system=%s,
                    must_change_password=%s
                WHERE user_id=%s
                """,
                (
                    legacy_user_id,
                    legacy_username,
                    username,
                    staff["staff_id"] if staff else None,
                    default_store_id,
                    department_id,
                    status,
                    SOURCE_SYSTEM,
                    must_change,
                    account_id,
                ),
            )
        else:
            cursor.execute(
                """
                INSERT INTO user_accounts(
                  tenant_id, legacy_user_id, username, legacy_username,
                  password_hash, staff_id, default_store_id, department_id,
                  status, must_change_password, source_system
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    TENANT_ID,
                    legacy_user_id,
                    username,
                    legacy_username,
                    password_hash,
                    staff["staff_id"] if staff else None,
                    default_store_id,
                    department_id,
                    status,
                    must_change,
                    SOURCE_SYSTEM,
                ),
            )
            account_id = cursor.lastrowid

        if staff:
            bound_staff[staff["staff_id"]] = account_id
            linked_staff += 1
        elif not is_disabled:
            unmatched_staff.append(
                {
                    "legacyUserId": legacy_user_id,
                    "trueName": str(row.get("TrueName") or "").strip(),
                    "department": str(row.get("depname") or "").strip(),
                }
            )

        cursor.execute(
            """
            DELETE ur FROM user_roles ur
            JOIN roles r ON r.role_id=ur.role_id
            WHERE ur.user_id=%s AND r.source_system=%s
            """,
            (account_id, SOURCE_SYSTEM),
        )
        for legacy_role_id in role_relations[legacy_user_id]:
            cursor.execute(
                """
                INSERT IGNORE INTO user_roles(user_id, role_id, effective_from)
                VALUES (%s,%s,NOW())
                """,
                (account_id, role_ids[legacy_role_id]),
            )

        # Store membership is the employee's home store. Cross-department and
        # cross-store visibility stays in the exact per-navigation scope table
        # instead of being flattened into a broad user_stores grant.
        source_store_ids = {default_store_id}
        if legacy_username == "admin" or truthy(row.get("IsAdmin")):
            source_store_ids = {1, 2}
        cursor.execute("DELETE FROM user_stores WHERE user_id=%s", (account_id,))
        for store_id in sorted(item for item in source_store_ids if item):
            cursor.execute(
                """
                INSERT INTO user_stores(user_id, store_id, access_level)
                VALUES (%s,%s,'READ')
                """,
                (account_id, store_id),
            )

        imported += 1
        if is_disabled:
            disabled += 1
        else:
            active += 1

    return {
        "imported": imported,
        "active": active,
        "disabled": disabled,
        "linkedStaff": linked_staff,
        "unmatchedStaffCount": len(unmatched_staff),
        "unmatchedStaff": unmatched_staff,
    }


def apply_import(data: dict, initial_password: str) -> dict:
    if not initial_password:
        raise SystemExit("ERP_LEGACY_ACCOUNT_INITIAL_PASSWORD is required.")
    summary = source_summary(data)
    connection = connect()
    try:
        with connection.cursor() as cursor:
            role_ids = upsert_roles(cursor, data)
            permission_ids = {}
            permission_ids.update(
                upsert_permission_catalog(cursor, data["web_catalog"])
            )
            permission_ids.update(
                upsert_permission_catalog(cursor, data["app_catalog"])
            )
            grant_counts = import_permission_grants(
                cursor, data, role_ids, permission_ids
            )
            scope_count = import_data_scopes(cursor, data, role_ids)
            account_result = upsert_accounts(
                cursor, data, role_ids, initial_password
            )
            detail = {
                "excludedRoles": EXCLUDED_ROLES,
                "accounts": account_result,
            }
            cursor.execute(
                """
                INSERT INTO legacy_access_import_runs(
                  source_roles, imported_roles, excluded_roles,
                  source_users, imported_users, excluded_users,
                  role_relations, web_grants, app_grants,
                  data_scope_grants, detail_json
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    summary["sourceRoles"],
                    summary["importedRoles"],
                    summary["excludedRoles"],
                    summary["sourceUsers"],
                    account_result["imported"],
                    summary["excludedUsers"],
                    summary["roleRelations"],
                    grant_counts["web"],
                    grant_counts["app"],
                    scope_count,
                    json.dumps(detail, ensure_ascii=False),
                ),
            )
        connection.commit()
        return {
            "status": "applied",
            **summary,
            "accounts": account_result,
            "importedWebGrants": grant_counts["web"],
            "importedAppGrants": grant_counts["app"],
            "importedDataScopes": scope_count,
        }
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def verify_import(data: dict) -> dict:
    expected = source_summary(data)
    connection = connect()
    try:
        with connection.cursor() as cursor:
            queries = {
                "activeLegacyRoles": """
                    SELECT COUNT(*) AS total FROM roles
                    WHERE tenant_id=%s AND source_system=%s
                      AND legacy_role_id IS NOT NULL AND status='ACTIVE'
                """,
                "legacyAccounts": """
                    SELECT COUNT(*) AS total FROM user_accounts
                    WHERE tenant_id=%s AND source_system=%s
                      AND legacy_user_id IS NOT NULL
                """,
                "activeLegacyAccounts": """
                    SELECT COUNT(*) AS total FROM user_accounts
                    WHERE tenant_id=%s AND source_system=%s
                      AND legacy_user_id IS NOT NULL AND status='ACTIVE'
                """,
                "excludedRoles": """
                    SELECT COUNT(*) AS total FROM legacy_role_exclusions
                """,
                "permissionResources": """
                    SELECT COUNT(*) AS total FROM legacy_permission_resources
                """,
                "dataScopes": """
                    SELECT COUNT(*) AS total
                    FROM legacy_role_data_scope_grants
                """,
            }
            actual = {}
            for key, sql in queries.items():
                cursor.execute(sql, (TENANT_ID, SOURCE_SYSTEM) if "%s" in sql else ())
                actual[key] = cursor.fetchone()["total"]
            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM user_roles ur
                JOIN user_accounts u ON u.user_id=ur.user_id
                JOIN roles r ON r.role_id=ur.role_id
                WHERE u.tenant_id=%s AND u.source_system=%s
                  AND r.source_system=%s
                """,
                (TENANT_ID, SOURCE_SYSTEM, SOURCE_SYSTEM),
            )
            actual["roleRelations"] = cursor.fetchone()["total"]
    finally:
        connection.close()

    expected_values = {
        "activeLegacyRoles": expected["importedRoles"],
        "legacyAccounts": expected["importedUsers"],
        "activeLegacyAccounts": expected["activeUsers"],
        "excludedRoles": expected["excludedRoles"],
        "permissionResources": expected["webCatalog"] + expected["appCatalog"],
        "dataScopes": expected["dataScopeGrants"],
        "roleRelations": expected["roleRelations"],
    }
    mismatches = {
        key: {"expected": value, "actual": actual.get(key)}
        for key, value in expected_values.items()
        if actual.get(key) != value
    }
    return {
        "status": "passed" if not mismatches else "failed",
        "expected": expected_values,
        "actual": actual,
        "mismatches": mismatches,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command", choices=("dry-run", "apply", "verify"), nargs="?", default="dry-run"
    )
    args = parser.parse_args()
    data = source_data()
    if args.command == "dry-run":
        result = {"status": "dry-run", **source_summary(data)}
    elif args.command == "apply":
        result = apply_import(
            data, os.environ.get("ERP_LEGACY_ACCOUNT_INITIAL_PASSWORD", "")
        )
    else:
        result = verify_import(data)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get("status") == "failed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

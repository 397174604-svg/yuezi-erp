#!/usr/bin/env python3
"""Safely reset the disposable yuezi data and import verified employee data.

The script never accepts a database password on the command line. Set
ERP_DB_PASSWORD in the process environment instead. Employee PII is read from
the gitignored .private directory. The project owner explicitly requires these
roster fields to be stored in plaintext.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEPS_DIR = REPO_ROOT / ".deps"
if DEPS_DIR.exists():
    sys.path.insert(0, str(DEPS_DIR))

try:
    import pymysql
    from pymysql.constants import CLIENT
except ImportError as exc:  # pragma: no cover - environment diagnostic
    raise SystemExit(
        "PyMySQL is required. Install it into .deps with: "
        "python -m pip install --target .deps PyMySQL"
    ) from exc

MIGRATION_DIR = REPO_ROOT / "database" / "mysql" / "migrations"
ACTIVE_EMPLOYEE_CSV = (
    REPO_ROOT / ".private" / "employee-import" / "employees-active.csv"
)
OFFBOARDED_EMPLOYEE_CSV = (
    REPO_ROOT
    / ".private"
    / "employee-import"
    / "employees-offboarded-review.csv"
)
DEFAULT_BACKUP_PATH = (
    REPO_ROOT
    / "database"
    / "mysql"
    / "reference"
    / "yuezi-legacy-schema-20260725.sql"
)
RESET_REPORT_PATH = (
    REPO_ROOT / ".private" / "employee-import" / "yuezi-reset-report.json"
)

EXPECTED_DATABASE = "yuezi"
CHECK_DATABASE = "yuezi_migration_check_20260725"
TENANT_ID = 1
STORE_IDS = {"JS": 1, "HHL": 2}
STORE_NAMES = {
    "JS": "奇德芬芳·建设路店（中心店）",
    "HHL": "奇德芬芳·黄河路店",
}

DEPARTMENT_CODES = {
    "总经办": "GENERAL_OFFICE",
    "销售部": "SALES",
    "护理部": "NURSING",
    "产康部": "RECOVERY",
    "客房部": "ROOM",
    "膳食部": "DIET",
    "企划部": "MARKETING",
    "美容部": "BEAUTY",
}

MODULE_NAMES = {
    "CUSTOMER": "客户管理",
    "SALES": "销售管理",
    "FINANCE": "财务管理",
    "ROOM": "客房管理",
    "NURSING": "护理管理",
    "RECOVERY": "产康管理",
    "MATRON": "月嫂管理",
    "DIET": "膳食管理",
    "INVENTORY": "仓存管理",
    "MALL": "商城管理",
    "RISK": "风控服务",
    "REPORT": "查询报表",
    "BASIC": "基础资料",
    "SYSTEM": "系统设置",
}

ACTION_NAMES = {
    "VIEW": "查看",
    "QUERY": "查询",
    "CREATE": "新增",
    "UPDATE": "编辑",
    "DELETE": "删除",
    "APPROVE": "审核",
    "EXPORT": "导出",
    "PRINT": "打印",
    "ALLOCATE": "分配",
    "EXECUTE": "执行",
}

MIGRATION_PERMISSION_CODES = {
    "SALES.CONTRACT.MEAL_PACKAGE.UPDATE",
    "SALES.DISCOUNT.CONSUME",
}

ROLE_DEFINITIONS = [
    ("SYS_ADMIN", "系统管理员", "SYSTEM", True, True, "ALL"),
    ("GENERAL_MANAGER", "总经理", "MANAGEMENT", True, False, "ALL"),
    ("STORE_MANAGER", "店长", "MANAGEMENT", True, False, "STORE"),
    ("HR_MANAGER", "人事主管", "MANAGEMENT", True, False, "ALL"),
    ("FINANCE_SPECIALIST", "财务专员", "JOB", False, False, "STORE"),
    ("SALES_MANAGER", "销售经理", "MANAGEMENT", True, False, "STORE"),
    ("SALES_CONSULTANT", "母婴顾问", "JOB", False, False, "SELF"),
    ("NURSING_DIRECTOR", "护理主任", "MANAGEMENT", True, False, "STORE"),
    ("NURSE", "护理人员", "JOB", False, False, "DEPARTMENT"),
    ("RECOVERY_MANAGER", "产康经理", "MANAGEMENT", True, False, "STORE"),
    ("RECOVERY_THERAPIST", "产康师", "JOB", False, False, "SELF"),
    ("ROOM_MANAGER", "客房经理", "MANAGEMENT", True, False, "STORE"),
    ("HOUSEKEEPER", "客房管家", "JOB", False, False, "DEPARTMENT"),
    ("DIET_MANAGER", "膳食经理", "MANAGEMENT", True, False, "STORE"),
    ("KITCHEN_STAFF", "膳食员工", "JOB", False, False, "DEPARTMENT"),
    ("MARKETING_SPECIALIST", "企划专员", "JOB", False, False, "STORE"),
    ("WAREHOUSE_KEEPER", "仓库管理员", "JOB", False, False, "STORE"),
    ("BEAUTY_TECHNICIAN", "美容师", "JOB", False, False, "SELF"),
    ("MATRON_MANAGER", "月嫂主管", "MANAGEMENT", True, False, "STORE"),
    ("MATRON", "月嫂", "JOB", False, False, "SELF"),
]

# Conservative baseline. Approval/delete rights are intentionally not inferred
# from department membership and must be assigned by special/management roles.
ROLE_MODULE_ACTIONS = {
    "SYS_ADMIN": {module: set(ACTION_NAMES) for module in MODULE_NAMES},
    "GENERAL_MANAGER": {
        module: {"VIEW", "QUERY", "APPROVE", "EXPORT", "PRINT"}
        for module in MODULE_NAMES
    },
    "STORE_MANAGER": {
        "CUSTOMER": {"VIEW", "QUERY", "CREATE", "UPDATE"},
        "SALES": {"VIEW", "QUERY", "APPROVE", "EXPORT", "PRINT"},
        "FINANCE": {"VIEW", "QUERY", "EXPORT", "PRINT"},
        "ROOM": {
            "VIEW",
            "QUERY",
            "CREATE",
            "UPDATE",
            "ALLOCATE",
            "EXECUTE",
            "PRINT",
        },
        "NURSING": {"VIEW", "QUERY"},
        "RECOVERY": {"VIEW", "QUERY"},
        "DIET": {"VIEW", "QUERY"},
        "REPORT": {"VIEW", "QUERY", "EXPORT"},
    },
    "HR_MANAGER": {
        "BASIC": {"VIEW", "QUERY", "CREATE", "UPDATE", "EXPORT"},
        "SYSTEM": {"VIEW", "QUERY", "CREATE", "UPDATE"},
        "REPORT": {"VIEW", "QUERY", "EXPORT"},
    },
    "FINANCE_SPECIALIST": {
        "FINANCE": {
            "VIEW",
            "QUERY",
            "CREATE",
            "UPDATE",
            "APPROVE",
            "EXPORT",
            "PRINT",
            "EXECUTE",
        },
        "CUSTOMER": {"VIEW", "QUERY"},
        "SALES": {"VIEW", "QUERY"},
        "REPORT": {"VIEW", "QUERY", "EXPORT"},
    },
    "SALES_MANAGER": {
        "CUSTOMER": {"VIEW", "QUERY", "CREATE", "UPDATE", "EXPORT"},
        "SALES": {"VIEW", "QUERY", "CREATE", "UPDATE", "APPROVE", "EXPORT", "PRINT"},
        "FINANCE": {"VIEW", "QUERY", "CREATE", "PRINT"},
        "ROOM": {"VIEW", "QUERY", "CREATE"},
        "REPORT": {"VIEW", "QUERY", "EXPORT"},
    },
    "SALES_CONSULTANT": {
        "CUSTOMER": {"VIEW", "QUERY", "CREATE", "UPDATE"},
        "SALES": {"VIEW", "QUERY", "CREATE", "UPDATE", "PRINT"},
        "FINANCE": {"VIEW", "QUERY", "PRINT"},
        "ROOM": {"VIEW", "QUERY"},
    },
    "NURSING_DIRECTOR": {
        "NURSING": {"VIEW", "QUERY", "CREATE", "UPDATE", "APPROVE", "ALLOCATE", "EXPORT", "PRINT", "EXECUTE"},
        "CUSTOMER": {"VIEW", "QUERY"},
        "ROOM": {"VIEW", "QUERY"},
        "INVENTORY": {"VIEW", "QUERY", "CREATE", "EXECUTE"},
        "REPORT": {"VIEW", "QUERY", "EXPORT"},
    },
    "NURSE": {
        "NURSING": {"VIEW", "QUERY", "CREATE", "UPDATE", "EXECUTE", "PRINT"},
        "CUSTOMER": {"VIEW", "QUERY"},
        "ROOM": {"VIEW", "QUERY"},
        "INVENTORY": {"VIEW", "QUERY", "EXECUTE"},
    },
    "RECOVERY_MANAGER": {
        "RECOVERY": {"VIEW", "QUERY", "CREATE", "UPDATE", "APPROVE", "ALLOCATE", "EXPORT", "PRINT", "EXECUTE"},
        "CUSTOMER": {"VIEW", "QUERY"},
        "ROOM": {"VIEW", "QUERY"},
        "INVENTORY": {"VIEW", "QUERY", "CREATE", "EXECUTE"},
        "REPORT": {"VIEW", "QUERY", "EXPORT"},
    },
    "RECOVERY_THERAPIST": {
        "RECOVERY": {"VIEW", "QUERY", "CREATE", "UPDATE", "EXECUTE", "PRINT"},
        "CUSTOMER": {"VIEW", "QUERY"},
        "ROOM": {"VIEW", "QUERY"},
        "INVENTORY": {"VIEW", "QUERY", "EXECUTE"},
    },
    "ROOM_MANAGER": {
        "ROOM": {"VIEW", "QUERY", "CREATE", "UPDATE", "APPROVE", "ALLOCATE", "EXPORT", "PRINT", "EXECUTE"},
        "CUSTOMER": {"VIEW", "QUERY"},
        "NURSING": {"VIEW", "QUERY"},
        "RECOVERY": {"VIEW", "QUERY"},
        "DIET": {"VIEW", "QUERY"},
        "REPORT": {"VIEW", "QUERY", "EXPORT"},
    },
    "HOUSEKEEPER": {
        "ROOM": {"VIEW", "QUERY", "CREATE", "UPDATE", "EXECUTE", "PRINT"},
        "CUSTOMER": {"VIEW", "QUERY"},
        "NURSING": {"VIEW", "QUERY"},
        "RECOVERY": {"VIEW", "QUERY"},
        "DIET": {"VIEW", "QUERY"},
    },
    "DIET_MANAGER": {
        "DIET": {"VIEW", "QUERY", "CREATE", "UPDATE", "APPROVE", "ALLOCATE", "EXPORT", "PRINT", "EXECUTE"},
        "CUSTOMER": {"VIEW", "QUERY"},
        "ROOM": {"VIEW", "QUERY"},
        "INVENTORY": {"VIEW", "QUERY", "CREATE", "EXECUTE"},
        "REPORT": {"VIEW", "QUERY", "EXPORT"},
    },
    "KITCHEN_STAFF": {
        "DIET": {"VIEW", "QUERY", "CREATE", "UPDATE", "EXECUTE", "PRINT"},
        "CUSTOMER": {"VIEW", "QUERY"},
        "ROOM": {"VIEW", "QUERY"},
        "INVENTORY": {"VIEW", "QUERY", "EXECUTE"},
    },
    "MARKETING_SPECIALIST": {
        "CUSTOMER": {"VIEW", "QUERY"},
        "MALL": {"VIEW", "QUERY", "CREATE", "UPDATE", "EXPORT"},
        "REPORT": {"VIEW", "QUERY", "EXPORT"},
    },
    "WAREHOUSE_KEEPER": {
        "INVENTORY": {"VIEW", "QUERY", "CREATE", "UPDATE", "APPROVE", "EXPORT", "PRINT", "EXECUTE"},
        "NURSING": {"VIEW", "QUERY"},
        "RECOVERY": {"VIEW", "QUERY"},
        "DIET": {"VIEW", "QUERY"},
        "REPORT": {"VIEW", "QUERY", "EXPORT"},
    },
    "BEAUTY_TECHNICIAN": {
        "RECOVERY": {"VIEW", "QUERY", "CREATE", "UPDATE", "EXECUTE", "PRINT"},
        "CUSTOMER": {"VIEW", "QUERY"},
    },
    "MATRON_MANAGER": {
        "MATRON": {"VIEW", "QUERY", "CREATE", "UPDATE", "APPROVE", "ALLOCATE", "EXPORT", "PRINT", "EXECUTE"},
        "CUSTOMER": {"VIEW", "QUERY"},
        "ROOM": {"VIEW", "QUERY"},
        "NURSING": {"VIEW", "QUERY"},
        "REPORT": {"VIEW", "QUERY", "EXPORT"},
    },
    "MATRON": {
        "MATRON": {"VIEW", "QUERY", "CREATE", "UPDATE", "EXECUTE", "PRINT"},
        "CUSTOMER": {"VIEW", "QUERY"},
        "ROOM": {"VIEW", "QUERY"},
        "NURSING": {"VIEW", "QUERY"},
    },
}


def db_config(database=None):
    password = os.environ.get("ERP_DB_PASSWORD")
    if not password:
        raise SystemExit("ERP_DB_PASSWORD is required in the process environment.")
    return {
        "host": os.environ.get("ERP_DB_HOST", "127.0.0.1"),
        "port": int(os.environ.get("ERP_DB_PORT", "3306")),
        "user": os.environ.get("ERP_DB_USER", "root"),
        "password": password,
        "database": database,
        "charset": "utf8mb4",
        "autocommit": False,
        "client_flag": CLIENT.MULTI_STATEMENTS,
    }


def connect(database=None):
    return pymysql.connect(**db_config(database))


def quote_identifier(value):
    if not re.fullmatch(r"[A-Za-z0-9_]+", value):
        raise ValueError(f"Unsafe SQL identifier: {value!r}")
    return f"`{value}`"


def list_base_tables(connection, database):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """,
            (database,),
        )
        return [row[0] for row in cursor.fetchall()]


def table_exists(connection, database, table):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = %s AND table_name = %s
            """,
            (database, table),
        )
        return cursor.fetchone()[0] == 1


def migration_paths():
    return sorted(MIGRATION_DIR.glob("V*.sql"))


def migration_version(path):
    return path.name.split("__", 1)[0]


def migration_checksum(path):
    normalized_sql = (
        path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    )
    return hashlib.sha256(normalized_sql).hexdigest()


def export_schema(database, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    connection = connect(database)
    try:
        tables = list_base_tables(connection, database)
        chunks = [
            "-- Schema-only backup generated before replacing disposable yuezi data.",
            f"-- Generated at {datetime.now().isoformat(timespec='seconds')}",
            "SET NAMES utf8mb4;",
            "SET FOREIGN_KEY_CHECKS=0;",
            f"CREATE DATABASE IF NOT EXISTS {quote_identifier(database)} "
            "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
            f"USE {quote_identifier(database)};",
            "",
        ]
        with connection.cursor() as cursor:
            for table in tables:
                cursor.execute(f"SHOW CREATE TABLE {quote_identifier(table)}")
                ddl = cursor.fetchone()[1]
                ddl = re.sub(r"\sAUTO_INCREMENT=\d+", "", ddl)
                chunks.append(ddl + ";")
                chunks.append("")
        chunks.append("SET FOREIGN_KEY_CHECKS=1;")
        output_path.write_text("\n".join(chunks) + "\n", encoding="utf-8")
        return len(tables)
    finally:
        connection.close()


def clone_schema(source_database, target_database):
    if target_database != CHECK_DATABASE:
        raise ValueError("Migration validation may only use the fixed check database.")
    source = connect(source_database)
    server = connect()
    try:
        tables = list_base_tables(source, source_database)
        with server.cursor() as cursor:
            cursor.execute(f"DROP DATABASE IF EXISTS {quote_identifier(target_database)}")
            cursor.execute(
                f"CREATE DATABASE {quote_identifier(target_database)} "
                "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        server.commit()

        target = connect(target_database)
        try:
            with target.cursor() as target_cursor, source.cursor() as source_cursor:
                target_cursor.execute("SET FOREIGN_KEY_CHECKS=0")
                for table in tables:
                    source_cursor.execute(
                        f"SHOW CREATE TABLE {quote_identifier(table)}"
                    )
                    target_cursor.execute(source_cursor.fetchone()[1])
                if "schema_migrations" in tables:
                    source_cursor.execute(
                        """
                        SELECT version, description, checksum, applied_at
                        FROM schema_migrations
                        ORDER BY version
                        """
                    )
                    migration_rows = source_cursor.fetchall()
                    if migration_rows:
                        target_cursor.executemany(
                            """
                            INSERT INTO schema_migrations
                              (version, description, checksum, applied_at)
                            VALUES (%s, %s, %s, %s)
                            """,
                            migration_rows,
                        )
                target_cursor.execute("SET FOREIGN_KEY_CHECKS=1")
            target.commit()
        finally:
            target.close()
        return len(tables)
    finally:
        source.close()
        server.close()


def apply_migration(connection, database, path):
    version = migration_version(path)
    if table_exists(connection, database, "schema_migrations"):
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT checksum FROM schema_migrations WHERE version = %s",
                (version,),
            )
            row = cursor.fetchone()
            if row:
                if row[0] != migration_checksum(path):
                    raise RuntimeError(
                        f"Migration {version} was applied with a different checksum."
                    )
                return False

    sql = path.read_text(encoding="utf-8")
    with connection.cursor() as cursor:
        cursor.execute(sql)
        while cursor.nextset():
            pass
        cursor.execute(
            """
            INSERT INTO schema_migrations
              (version, description, checksum)
            VALUES (%s, %s, %s)
            """,
            (
                version,
                path.stem.split("__", 1)[-1].replace("_", " "),
                migration_checksum(path),
            ),
        )
    connection.commit()
    return True


def apply_pending_migrations(connection, database):
    applied = []
    for path in migration_paths():
        if apply_migration(connection, database, path):
            applied.append(migration_version(path))
    return applied


def verify_migration_surface(connection, database):
    required_tables = {
        "departments",
        "positions",
        "staff_private",
        "staff_roster_records",
        "permissions",
        "role_permissions",
        "user_accounts",
        "user_roles",
        "user_stores",
        "role_data_scopes",
        "field_permissions",
        "access_delegations",
    }
    existing = set(list_base_tables(connection, database))
    missing = sorted(required_tables - existing)
    if missing:
        raise RuntimeError("Migration is missing tables: " + ", ".join(missing))

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = 'staff'
            """,
            (database,),
        )
        staff_columns = {row[0] for row in cursor.fetchall()}
    required_staff_columns = {
        "employee_no",
        "department_id",
        "position_id",
        "gender",
        "birth_date",
        "education",
        "hire_date",
        "employment_status",
        "review_status",
        "age_at_source",
        "tenure_text",
        "contract_end_date",
        "source_status",
        "source_note",
        "id_no",
        "id_no_normalized",
        "id_no_valid",
        "id_valid_until",
        "home_address",
        "emergency_contact_name",
        "emergency_contact_phone",
        "salary_card_no",
    }
    missing_columns = sorted(required_staff_columns - staff_columns)
    if missing_columns:
        raise RuntimeError(
            "Migration is missing staff columns: " + ", ".join(missing_columns)
        )


def inspect_staff_foreign_keys(database):
    connection = connect(database)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT table_name, constraint_name, column_name,
                       referenced_column_name
                FROM information_schema.key_column_usage
                WHERE referenced_table_schema = %s
                  AND referenced_table_name = 'staff'
                ORDER BY table_name, constraint_name, ordinal_position
                """,
                (database,),
            )
            return [
                {
                    "table": row[0],
                    "constraint": row[1],
                    "column": row[2],
                    "referenced_column": row[3],
                }
                for row in cursor.fetchall()
            ]
    finally:
        connection.close()


def validate_migration(source_database):
    cloned_tables = clone_schema(source_database, CHECK_DATABASE)
    check = connect(CHECK_DATABASE)
    try:
        applied = apply_pending_migrations(check, CHECK_DATABASE)
        verify_migration_surface(check, CHECK_DATABASE)
        active_rows = load_employee_rows(ACTIVE_EMPLOYEE_CSV)
        offboarded_rows = load_roster_rows(OFFBOARDED_EMPLOYEE_CSV)
        with check.cursor() as cursor:
            seed_tenant_and_stores(cursor)
            seed_organization_and_staff(cursor, active_rows, offboarded_rows)
            seed_rbac(cursor)
        check.commit()
        import_verification = verify_import(check)
    finally:
        check.close()

    server = connect()
    try:
        with server.cursor() as cursor:
            cursor.execute(f"DROP DATABASE {quote_identifier(CHECK_DATABASE)}")
        server.commit()
    finally:
        server.close()
    return {
        "cloned_tables": cloned_tables,
        "migrations_applied": applied,
        "full_import_verified": import_verification,
    }


ROSTER_REQUIRED_FIELDS = {
    "employee_no",
    "staging_no",
    "store_code",
    "source_seq",
    "source_row_order",
    "department",
    "position",
    "name",
    "gender",
    "age_at_source",
    "education",
    "mobile",
    "id_no",
    "id_no_raw",
    "id_no_valid",
    "birth_date",
    "id_valid_until",
    "home_address",
    "emergency_contact_name",
    "emergency_contact_phone",
    "hire_date",
    "tenure_text",
    "promotion_history",
    "contract_years_text",
    "contract_start_date",
    "contract_end_date",
    "contract_expiry_reminder",
    "contract_sign_count",
    "salary_card_no",
    "employment_status",
    "source_status",
    "source_note",
    "source_file",
    "source_page",
    "review_status",
}


def load_roster_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError(f"Roster import CSV is empty: {path}")

    missing = ROSTER_REQUIRED_FIELDS - set(rows[0])
    if missing:
        raise ValueError("Roster CSV is missing columns: " + ", ".join(sorted(missing)))
    if any(row["store_code"] not in STORE_IDS for row in rows):
        raise ValueError("Roster CSV contains an unsupported store code.")
    return rows


def load_employee_rows(path):
    rows = load_roster_rows(path)
    employee_nos = [row["employee_no"].strip() for row in rows]
    mobiles = [row["mobile"].strip() for row in rows]
    if any(row["employment_status"] != "ACTIVE" for row in rows):
        raise ValueError("Active employee CSV contains a non-active row.")
    if len(employee_nos) != len(set(employee_nos)):
        raise ValueError("Duplicate employee numbers in active employee CSV.")
    if not all(re.fullmatch(r"1[3-9]\d{9}", mobile) for mobile in mobiles):
        raise ValueError("Every active employee must have a valid mobile number.")
    if len(mobiles) != len(set(mobiles)):
        raise ValueError("Duplicate mobile numbers in active employee CSV.")
    return rows


def stable_position_code(department_code, position_name):
    digest = hashlib.sha1(position_name.encode("utf-8")).hexdigest()[:10].upper()
    return f"{department_code}_{digest}"


def reset_all_data(connection, database):
    if database != EXPECTED_DATABASE:
        raise ValueError(
            f"Refusing destructive reset for {database!r}; expected {EXPECTED_DATABASE!r}."
        )
    tables = list_base_tables(connection, database)
    preserved = {"schema_migrations"}
    reset_tables = [table for table in tables if table not in preserved]
    with connection.cursor() as cursor:
        cursor.execute("SET FOREIGN_KEY_CHECKS=0")
        for table in reset_tables:
            cursor.execute(f"TRUNCATE TABLE {quote_identifier(table)}")
        cursor.execute("SET FOREIGN_KEY_CHECKS=1")
    connection.commit()
    return reset_tables


def seed_tenant_and_stores(cursor):
    cursor.execute(
        """
        INSERT INTO tenants (tenant_id, name, status, expires_at)
        VALUES (%s, %s, %s, NULL)
        """,
        (TENANT_ID, "奇德芬芳", "正常"),
    )
    for store_code in ("JS", "HHL"):
        cursor.execute(
            """
            INSERT INTO stores
              (store_id, tenant_id, name, manager, phone, address, industry,
               domain, region, status, sort_weight, parent_store_id)
            VALUES
              (%s, %s, %s, NULL, NULL, NULL, %s, NULL, %s, %s, %s, NULL)
            """,
            (
                STORE_IDS[store_code],
                TENANT_ID,
                STORE_NAMES[store_code],
                "月子会所",
                "郑州",
                "正常",
                10 if store_code == "JS" else 20,
            ),
        )


def nullable(value):
    value = (value or "").strip()
    return value or None


def nullable_int(value):
    value = (value or "").strip()
    return int(value) if value else None


def seed_organization_and_staff(cursor, rows, offboarded_rows):
    departments_by_store = defaultdict(set)
    for row in rows:
        departments_by_store[row["store_code"]].add(row["department"].strip())

    department_ids = {}
    for store_code in ("JS", "HHL"):
        names = sorted(
            departments_by_store[store_code],
            key=lambda name: (
                list(DEPARTMENT_CODES).index(name)
                if name in DEPARTMENT_CODES
                else 999,
                name,
            ),
        )
        for sort_order, name in enumerate(names, 1):
            code = DEPARTMENT_CODES.get(
                name, "DEPT_" + hashlib.sha1(name.encode()).hexdigest()[:10].upper()
            )
            cursor.execute(
                """
                INSERT INTO departments
                  (tenant_id, store_id, code, name, sort_order, status)
                VALUES (%s, %s, %s, %s, %s, 'ACTIVE')
                """,
                (TENANT_ID, STORE_IDS[store_code], code, name, sort_order),
            )
            department_ids[(store_code, name)] = cursor.lastrowid

    positions = sorted(
        {
            (row["store_code"], row["department"].strip(), row["position"].strip())
            for row in rows
            if row["position"].strip()
        }
    )
    position_ids = {}
    for store_code, department_name, position_name in positions:
        department_id = department_ids[(store_code, department_name)]
        department_code = DEPARTMENT_CODES.get(department_name, "DEPT")
        is_manager = int(
            any(
                token in position_name
                for token in ("总经理", "经理", "主管", "主任", "厨师长")
            )
        )
        cursor.execute(
            """
            INSERT INTO positions
              (tenant_id, department_id, code, name, is_manager, status)
            VALUES (%s, %s, %s, %s, %s, 'ACTIVE')
            """,
            (
                TENANT_ID,
                department_id,
                stable_position_code(department_code, position_name),
                position_name,
                is_manager,
            ),
        )
        position_ids[(store_code, department_name, position_name)] = cursor.lastrowid

    staff_ids = {}
    invalid_id_count = 0
    for row in rows:
        department_name = row["department"].strip()
        position_name = row["position"].strip()
        department_id = department_ids[(row["store_code"], department_name)]
        position_id = (
            position_ids.get((row["store_code"], department_name, position_name))
            if position_name
            else None
        )
        id_no = nullable(row["id_no"])
        if row["id_no_valid"] != "1":
            invalid_id_count += 1
        cursor.execute(
            """
            INSERT INTO staff
              (tenant_id, store_id, employee_no, department_id, position_id,
               name, gender, age_at_source, birth_date, education, hire_date,
               employment_status, tenure_text, promotion_history,
               contract_years_text, contract_start_date, contract_end_date,
               contract_expiry_reminder, contract_sign_count, source_status,
               source_note, phone, id_no, id_no_normalized, id_no_valid,
               id_valid_until, home_address, emergency_contact_name,
               emergency_contact_phone, salary_card_no,
               role, position, department,
               wx_notify, status, password_hash, source_file, source_page,
               source_row, review_status)
            VALUES
              (%s, %s, %s, %s, %s,
               %s, %s, %s, %s, %s, %s,
               'ACTIVE', %s, %s,
               %s, %s, %s,
               %s, %s, %s,
               %s, %s, %s, %s, %s,
               %s, %s, %s,
               %s, %s,
               NULL, %s, %s,
               0, 'ACTIVE', NULL, %s, %s,
               %s, %s)
            """,
            (
                TENANT_ID,
                STORE_IDS[row["store_code"]],
                row["employee_no"].strip(),
                department_id,
                position_id,
                row["name"].strip(),
                nullable(row["gender"]),
                nullable_int(row["age_at_source"]),
                nullable(row["birth_date"]),
                nullable(row["education"]),
                nullable(row["hire_date"]),
                nullable(row["tenure_text"]),
                nullable(row["promotion_history"]),
                nullable(row["contract_years_text"]),
                nullable(row["contract_start_date"]),
                nullable(row["contract_end_date"]),
                nullable(row["contract_expiry_reminder"]),
                nullable_int(row["contract_sign_count"]),
                nullable(row["source_status"]),
                nullable(row["source_note"]),
                row["mobile"].strip(),
                nullable(row["id_no_raw"]),
                id_no,
                int(row["id_no_valid"] == "1"),
                nullable(row["id_valid_until"]),
                nullable(row["home_address"]),
                nullable(row["emergency_contact_name"]),
                nullable(row["emergency_contact_phone"]),
                nullable(row["salary_card_no"]),
                position_name or None,
                department_name,
                row["source_file"].strip(),
                int(row["source_page"]),
                int(row["source_seq"]),
                row["review_status"].strip(),
            ),
        )
        staff_id = cursor.lastrowid
        staff_ids[row["employee_no"].strip()] = staff_id
        cursor.execute(
            """
            INSERT INTO staff_private
              (staff_id, id_no, id_no_raw, id_no_valid, id_valid_until,
               home_address, emergency_contact_name, emergency_contact_phone,
               salary_card_no)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                staff_id,
                id_no,
                nullable(row["id_no_raw"]),
                int(row["id_no_valid"] == "1"),
                nullable(row["id_valid_until"]),
                nullable(row["home_address"]),
                nullable(row["emergency_contact_name"]),
                nullable(row["emergency_contact_phone"]),
                nullable(row["salary_card_no"]),
            ),
        )

    roster_rows = rows + offboarded_rows
    for row in roster_rows:
        cursor.execute(
            """
            INSERT INTO staff_roster_records
              (tenant_id, store_id, staff_id, employee_no, staging_no,
               source_file, source_page, source_seq, source_row_order,
               department, position, employee_name, gender, age_at_source,
               education, mobile, id_no, id_no_raw, id_no_valid, birth_date,
               id_valid_until, home_address, emergency_contact_name,
               emergency_contact_phone, hire_date, tenure_text,
               promotion_history, contract_years_text, contract_start_date,
               contract_end_date, contract_expiry_reminder,
               contract_sign_count, salary_card_no, employment_status,
               source_status, source_note, review_status)
            VALUES
              (%s, %s, %s, %s, %s,
               %s, %s, %s, %s,
               %s, %s, %s, %s, %s,
               %s, %s, %s, %s, %s, %s,
               %s, %s, %s,
               %s, %s, %s,
               %s, %s, %s,
               %s, %s,
               %s, %s, %s,
               %s, %s, %s)
            """,
            (
                TENANT_ID,
                STORE_IDS[row["store_code"]],
                staff_ids.get(row["employee_no"].strip()),
                nullable(row["employee_no"]),
                nullable(row["staging_no"]),
                row["source_file"].strip(),
                int(row["source_page"]),
                nullable_int(row["source_seq"]),
                int(row["source_row_order"]),
                nullable(row["department"]),
                nullable(row["position"]),
                row["name"].strip(),
                nullable(row["gender"]),
                nullable_int(row["age_at_source"]),
                nullable(row["education"]),
                nullable(row["mobile"]),
                nullable(row["id_no"]),
                nullable(row["id_no_raw"]),
                int(row["id_no_valid"] == "1"),
                nullable(row["birth_date"]),
                nullable(row["id_valid_until"]),
                nullable(row["home_address"]),
                nullable(row["emergency_contact_name"]),
                nullable(row["emergency_contact_phone"]),
                nullable(row["hire_date"]),
                nullable(row["tenure_text"]),
                nullable(row["promotion_history"]),
                nullable(row["contract_years_text"]),
                nullable(row["contract_start_date"]),
                nullable(row["contract_end_date"]),
                nullable(row["contract_expiry_reminder"]),
                nullable_int(row["contract_sign_count"]),
                nullable(row["salary_card_no"]),
                row["employment_status"],
                nullable(row["source_status"]),
                nullable(row["source_note"]),
                row["review_status"],
            ),
        )
    return {
        "departments": len(department_ids),
        "positions": len(position_ids),
        "staff": len(rows),
        "staff_private": len(rows),
        "roster_records": len(roster_rows),
        "offboarded_roster_records": len(offboarded_rows),
        "invalid_id_no": invalid_id_count,
    }


def seed_rbac(cursor):
    now_text = datetime.now().isoformat(timespec="seconds")
    permission_ids = {}
    sort_order = 0
    for module_code, module_name in MODULE_NAMES.items():
        for action_code, action_name in ACTION_NAMES.items():
            sort_order += 1
            code = f"{module_code}.{action_code}"
            cursor.execute(
                """
                INSERT INTO permissions
                  (code, module_code, resource_type, action_code, name, sort_order, status)
                VALUES (%s, %s, 'MODULE', %s, %s, %s, 'ACTIVE')
                """,
                (
                    code,
                    module_code,
                    action_code,
                    f"{module_name}-{action_name}",
                    sort_order,
                ),
            )
            permission_ids[(module_code, action_code)] = cursor.lastrowid

    role_ids = {}
    for code, name, role_type, is_manager, is_system, scope in ROLE_DEFINITIONS:
        legacy_scope = {"SELF": 1, "DEPARTMENT": 2, "STORE": 3, "ALL": 4}[scope]
        cursor.execute(
            """
            INSERT INTO roles
              (tenant_id, code, name, role_type, perms_json, is_manager,
               is_system, data_scope, description, created_at, status)
            VALUES (%s, %s, %s, %s, '[]', %s, %s, %s, %s, %s, 'ACTIVE')
            """,
            (
                TENANT_ID,
                code,
                name,
                role_type,
                int(is_manager),
                int(is_system),
                legacy_scope,
                "规范化 RBAC 基线；权限以 role_permissions 与 role_data_scopes 为准。",
                now_text,
            ),
        )
        role_ids[code] = cursor.lastrowid

        modules = ROLE_MODULE_ACTIONS[code]
        for module_code, actions in modules.items():
            allow_cross_store = int(scope == "ALL")
            allow_cross_department = int(scope in {"STORE", "ALL"})
            cursor.execute(
                """
                INSERT INTO role_data_scopes
                  (role_id, module_code, scope_type, allow_cross_store,
                   allow_cross_department, condition_json)
                VALUES (%s, %s, %s, %s, %s, NULL)
                """,
                (
                    role_ids[code],
                    module_code,
                    scope,
                    allow_cross_store,
                    allow_cross_department,
                ),
            )
            for action_code in sorted(actions):
                cursor.execute(
                    """
                    INSERT INTO role_permissions
                      (role_id, permission_id, effect)
                    VALUES (%s, %s, 'ALLOW')
                    """,
                    (
                        role_ids[code],
                        permission_ids[(module_code, action_code)],
                    ),
                )

    # High-risk fields are masked by default for operational roles.
    sensitive_fields = (
        ("CUSTOMER.PROFILE", "mobile"),
        ("CUSTOMER.PROFILE", "id_no"),
        ("STAFF.PROFILE", "mobile"),
        ("STAFF.PROFILE", "id_no"),
        ("FINANCE.RECEIPT", "amount"),
    )
    privileged = {"SYS_ADMIN", "GENERAL_MANAGER", "HR_MANAGER", "FINANCE_SPECIALIST"}
    for role_code, role_id in role_ids.items():
        for resource_code, field_code in sensitive_fields:
            visible = int(
                role_code in privileged
                or (resource_code == "CUSTOMER.PROFILE" and role_code.startswith("SALES"))
            )
            editable = int(
                role_code in {"SYS_ADMIN", "HR_MANAGER"}
                and resource_code == "STAFF.PROFILE"
            )
            masked = int(not visible or role_code not in {"SYS_ADMIN", "HR_MANAGER"})
            cursor.execute(
                """
                INSERT INTO field_permissions
                  (role_id, resource_code, field_code, visible, masked, editable)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (role_id, resource_code, field_code, visible, masked, editable),
            )

    return {
        "permissions": len(permission_ids),
        "roles": len(role_ids),
        "accounts": 0,
    }


def verify_import(connection):
    scalar_queries = {
        "tenants": "SELECT COUNT(*) FROM tenants",
        "stores": "SELECT COUNT(*) FROM stores",
        "departments": "SELECT COUNT(*) FROM departments",
        "positions": "SELECT COUNT(*) FROM positions",
        "staff": "SELECT COUNT(*) FROM staff",
        "staff_private": "SELECT COUNT(*) FROM staff_private",
        "staff_roster_records": "SELECT COUNT(*) FROM staff_roster_records",
        "offboarded_roster_records": (
            "SELECT COUNT(*) FROM staff_roster_records "
            "WHERE employment_status = 'OFFBOARDED'"
        ),
        "roles": "SELECT COUNT(*) FROM roles",
        "permissions": "SELECT COUNT(*) FROM permissions",
        "user_accounts": "SELECT COUNT(*) FROM user_accounts",
        "full_mobile_rows": (
            "SELECT COUNT(*) FROM staff WHERE phone REGEXP '^1[3-9][0-9]{9}$'"
        ),
        "staff_main_id_no_rows": (
            "SELECT COUNT(*) FROM staff WHERE id_no IS NOT NULL"
        ),
        "staff_main_normalized_id_rows": (
            "SELECT COUNT(*) FROM staff WHERE id_no_normalized IS NOT NULL"
        ),
        "staff_main_address_rows": (
            "SELECT COUNT(*) FROM staff WHERE home_address IS NOT NULL"
        ),
        "staff_main_emergency_phone_rows": (
            "SELECT COUNT(*) FROM staff WHERE emergency_contact_phone IS NOT NULL"
        ),
        "staff_main_salary_card_rows": (
            "SELECT COUNT(*) FROM staff WHERE salary_card_no IS NOT NULL"
        ),
        "staff_main_private_mismatches": (
            "SELECT COUNT(*) FROM staff s "
            "JOIN staff_private p ON p.staff_id = s.staff_id "
            "WHERE COALESCE(s.id_no, '') <> COALESCE(p.id_no_raw, '') "
            "OR COALESCE(s.home_address, '') <> COALESCE(p.home_address, '') "
            "OR COALESCE(s.emergency_contact_phone, '') "
            "<> COALESCE(p.emergency_contact_phone, '') "
            "OR COALESCE(s.salary_card_no, '') <> COALESCE(p.salary_card_no, '')"
        ),
        "missing_private_rows": (
            "SELECT COUNT(*) FROM staff s "
            "LEFT JOIN staff_private p ON p.staff_id = s.staff_id "
            "WHERE p.staff_id IS NULL"
        ),
        "staff_needing_id_review": (
            "SELECT COUNT(*) FROM staff WHERE review_status <> 'CORE_VERIFIED'"
        ),
        "missing_id_no_raw": (
            "SELECT COUNT(*) FROM staff_private WHERE id_no_raw IS NULL"
        ),
        "invalid_id_no": (
            "SELECT COUNT(*) FROM staff_private WHERE id_no_valid = 0"
        ),
        "plaintext_id_source_rows": (
            "SELECT COUNT(*) FROM staff_private WHERE id_no_raw IS NOT NULL"
        ),
        "encrypted_private_columns_remaining": (
            "SELECT COUNT(*) FROM information_schema.columns "
            "WHERE table_schema = DATABASE() AND table_name = 'staff_private' "
            "AND (column_name LIKE '%cipher%' OR column_name LIKE '%hash%')"
        ),
    }
    result = {}
    with connection.cursor() as cursor:
        for key, query in scalar_queries.items():
            cursor.execute(query)
            result[key] = cursor.fetchone()[0]
        database = connection.db.decode("utf-8") if isinstance(connection.db, bytes) else connection.db
        allowed_nonempty = {
            "schema_migrations",
            "tenants",
            "stores",
            "departments",
            "positions",
            "staff",
            "staff_private",
            "staff_roster_records",
            "roles",
            "permissions",
            "role_permissions",
            "role_data_scopes",
            "field_permissions",
        }
        unexpected_nonempty = {}
        for table in list_base_tables(connection, database):
            if table in allowed_nonempty:
                continue
            cursor.execute(f"SELECT COUNT(*) FROM {quote_identifier(table)}")
            count = cursor.fetchone()[0]
            if count:
                unexpected_nonempty[table] = count
        result["unexpected_nonempty_tables"] = unexpected_nonempty
        result["legacy_business_tables_empty"] = not unexpected_nonempty

        source_rows = load_roster_rows(ACTIVE_EMPLOYEE_CSV) + load_roster_rows(
            OFFBOARDED_EMPLOYEE_CSV
        )
        field_mapping = {
            "department": "department",
            "position": "position",
            "name": "employee_name",
            "gender": "gender",
            "age_at_source": "age_at_source",
            "education": "education",
            "mobile": "mobile",
            "id_no_raw": "id_no_raw",
            "birth_date": "birth_date",
            "id_valid_until": "id_valid_until",
            "home_address": "home_address",
            "emergency_contact_name": "emergency_contact_name",
            "emergency_contact_phone": "emergency_contact_phone",
            "hire_date": "hire_date",
            "tenure_text": "tenure_text",
            "promotion_history": "promotion_history",
            "contract_years_text": "contract_years_text",
            "contract_start_date": "contract_start_date",
            "contract_end_date": "contract_end_date",
            "contract_expiry_reminder": "contract_expiry_reminder",
            "contract_sign_count": "contract_sign_count",
            "salary_card_no": "salary_card_no",
            "source_status": "source_status",
            "source_note": "source_note",
        }
        field_count_mismatches = {}
        for source_field, database_field in field_mapping.items():
            expected_count = sum(
                bool((row[source_field] or "").strip()) for row in source_rows
            )
            cursor.execute(
                f"""
                SELECT COUNT(*)
                FROM staff_roster_records
                WHERE {quote_identifier(database_field)} IS NOT NULL
                  AND TRIM(CAST({quote_identifier(database_field)} AS CHAR)) <> ''
                """
            )
            actual_count = cursor.fetchone()[0]
            if actual_count != expected_count:
                field_count_mismatches[source_field] = {
                    "expected": expected_count,
                    "actual": actual_count,
                }
        result["roster_field_count_mismatches"] = field_count_mismatches
    expected = {
        "tenants": 1,
        "stores": 2,
        "staff": 94,
        "staff_private": 94,
        "staff_roster_records": 156,
        "offboarded_roster_records": 62,
        "roles": len(ROLE_DEFINITIONS),
        "permissions": len(MODULE_NAMES) * len(ACTION_NAMES),
        "user_accounts": 0,
        "full_mobile_rows": 94,
        "staff_main_id_no_rows": 94,
        "staff_main_normalized_id_rows": 86,
        "staff_main_address_rows": 93,
        "staff_main_emergency_phone_rows": 81,
        "staff_main_salary_card_rows": 32,
        "staff_main_private_mismatches": 0,
        "missing_private_rows": 0,
        "staff_needing_id_review": 8,
        "missing_id_no_raw": 0,
        "invalid_id_no": 8,
        "plaintext_id_source_rows": 94,
        "encrypted_private_columns_remaining": 0,
        "unexpected_nonempty_tables": {},
        "legacy_business_tables_empty": True,
        "roster_field_count_mismatches": {},
    }
    mismatches = {
        key: {"expected": value, "actual": result.get(key)}
        for key, value in expected.items()
        if result.get(key) != value
    }
    if mismatches:
        raise RuntimeError(
            "Post-import verification failed: "
            + json.dumps(mismatches, ensure_ascii=False)
        )
    return result


def reset_and_import(database, employee_path, offboarded_path):
    if database != EXPECTED_DATABASE:
        raise ValueError("The destructive import is restricted to the yuezi database.")
    rows = load_employee_rows(employee_path)
    offboarded_rows = load_roster_rows(offboarded_path)
    if any(row["employment_status"] != "OFFBOARDED" for row in offboarded_rows):
        raise ValueError("Offboarded roster CSV contains a non-offboarded row.")
    connection = connect(database)
    try:
        reset_tables = reset_all_data(connection, database)
        migrations_applied = apply_pending_migrations(connection, database)
        verify_migration_surface(connection, database)
        with connection.cursor() as cursor:
            seed_tenant_and_stores(cursor)
            organization = seed_organization_and_staff(
                cursor, rows, offboarded_rows
            )
            rbac = seed_rbac(cursor)
        connection.commit()
        verification = verify_import(connection)
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    report = {
        "database": database,
        "completed_at": datetime.now().isoformat(timespec="seconds"),
        "reset_table_count": len(reset_tables),
        "migrations_applied": migrations_applied,
        "organization": organization,
        "rbac": rbac,
        "verification": verification,
        "pii_encryption_enabled": False,
        "phone_display_mode": "FULL",
        "plaintext_credentials_imported": False,
        "offboarded_history_imported": True,
    }
    RESET_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESET_REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def bootstrap_minimal(database):
    """Initialize a fresh schema without private employee roster data.

    Fresh databases need tenant/store rows before V010, while normalized RBAC
    tables do not exist until V001. Apply the migration chain in two phases and
    seed the non-sensitive baseline between them.
    """
    if database != EXPECTED_DATABASE:
        raise ValueError(
            "Minimal bootstrap is restricted to the yuezi database."
        )
    connection = connect(database)
    try:
        existing_tables = set(list_base_tables(connection, database))
        required_base = {"tenants", "stores", "roles", "staff"}
        missing_base = sorted(required_base - existing_tables)
        if missing_base:
            raise RuntimeError(
                "Import the reference schema before bootstrap-minimal; "
                "missing tables: " + ", ".join(missing_base)
            )
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM tenants")
            tenant_count = int(cursor.fetchone()[0])
            migration_count = 0
            if table_exists(connection, database, "schema_migrations"):
                cursor.execute("SELECT COUNT(*) FROM schema_migrations")
                migration_count = int(cursor.fetchone()[0])
        if tenant_count or migration_count:
            raise RuntimeError(
                "bootstrap-minimal requires a fresh imported schema with no "
                f"tenant or migration rows; tenants={tenant_count}, "
                f"migrations={migration_count}."
            )

        with connection.cursor() as cursor:
            seed_tenant_and_stores(cursor)
        connection.commit()

        paths = migration_paths()
        baseline_paths = [
            path for path in paths if int(migration_version(path).rsplit("_", 1)[1]) <= 3
        ]
        runtime_paths = [
            path for path in paths if int(migration_version(path).rsplit("_", 1)[1]) > 3
        ]
        applied = []
        for path in baseline_paths:
            if apply_migration(connection, database, path):
                applied.append(migration_version(path))

        with connection.cursor() as cursor:
            rbac = seed_rbac(cursor)
        connection.commit()

        for path in runtime_paths:
            if apply_migration(connection, database, path):
                applied.append(migration_version(path))
        verify_migration_surface(connection, database)
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM tenants")
            tenants = int(cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM stores")
            stores = int(cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM roles")
            roles = int(cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM permissions")
            permissions = int(cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM schema_migrations")
            migrations = int(cursor.fetchone()[0])
        expected = {
            "tenants": 1,
            "stores": 2,
            "roles": len(ROLE_DEFINITIONS),
            "permissions": (
                len(MODULE_NAMES) * len(ACTION_NAMES)
                + len(MIGRATION_PERMISSION_CODES)
            ),
            "migrations": len(paths),
        }
        actual = {
            "tenants": tenants,
            "stores": stores,
            "roles": roles,
            "permissions": permissions,
            "migrations": migrations,
        }
        mismatches = {
            key: {"expected": value, "actual": actual[key]}
            for key, value in expected.items()
            if actual[key] != value
        }
        if mismatches:
            raise RuntimeError(
                "Minimal bootstrap verification failed: "
                + json.dumps(mismatches, ensure_ascii=False)
            )
        return {
            "database": database,
            "mode": "minimal-no-private-roster",
            "migrations_applied": applied,
            "rbac": rbac,
            "verification": actual,
        }
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def dry_run(employee_path, offboarded_path):
    rows = load_employee_rows(employee_path)
    offboarded_rows = load_roster_rows(offboarded_path)
    return {
        "employees": len(rows),
        "stores": dict(
            sorted(
                (
                    code,
                    sum(row["store_code"] == code for row in rows),
                )
                for code in STORE_IDS
            )
        ),
        "departments": len(
            {(row["store_code"], row["department"]) for row in rows}
        ),
        "positions_with_verified_name": len(
            {
                (row["store_code"], row["department"], row["position"])
                for row in rows
                if row["position"].strip()
            }
        ),
        "valid_id_numbers": sum(bool(row["id_no"].strip()) for row in rows),
        "raw_id_numbers": sum(bool(row["id_no_raw"].strip()) for row in rows),
        "invalid_id_numbers": sum(row["id_no_valid"] != "1" for row in rows),
        "home_addresses": sum(bool(row["home_address"].strip()) for row in rows),
        "emergency_phones": sum(
            bool(row["emergency_contact_phone"].strip()) for row in rows
        ),
        "offboarded_roster_records": len(offboarded_rows),
        "pii_encryption_enabled": False,
        "phone_display_mode": "FULL",
        "plaintext_credentials_imported": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=(
            "dry-run",
            "backup-schema",
            "bootstrap-minimal",
            "inspect-staff-fks",
            "validate-migration",
            "reset-import",
            "verify",
        ),
    )
    parser.add_argument("--database", default=EXPECTED_DATABASE)
    parser.add_argument("--employees", type=Path, default=ACTIVE_EMPLOYEE_CSV)
    parser.add_argument(
        "--offboarded", type=Path, default=OFFBOARDED_EMPLOYEE_CSV
    )
    parser.add_argument("--backup-output", type=Path, default=DEFAULT_BACKUP_PATH)
    args = parser.parse_args()

    if args.command == "dry-run":
        result = dry_run(args.employees, args.offboarded)
    elif args.command == "backup-schema":
        result = {
            "database": args.database,
            "tables": export_schema(args.database, args.backup_output),
            "output": str(args.backup_output),
        }
    elif args.command == "bootstrap-minimal":
        result = bootstrap_minimal(args.database)
    elif args.command == "inspect-staff-fks":
        result = inspect_staff_foreign_keys(args.database)
    elif args.command == "validate-migration":
        result = validate_migration(args.database)
    elif args.command == "reset-import":
        result = reset_and_import(
            args.database, args.employees, args.offboarded
        )
    else:
        connection = connect(args.database)
        try:
            result = verify_import(connection)
        finally:
            connection.close()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

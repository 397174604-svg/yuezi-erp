#!/usr/bin/env python3
"""Local MySQL-backed MVP API for the maternity ERP.

The server intentionally implements only the first integrated business loop:
customer -> contract approval -> receipt approval -> booking -> check-in.
It uses the existing MySQL 5.7 database and never falls back to JSON fixtures.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import sys
import time
from datetime import date, datetime, timedelta
from decimal import Decimal
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse


REPO_ROOT = Path(__file__).resolve().parents[1]
DEPS_DIR = REPO_ROOT / ".deps"
if DEPS_DIR.exists():
    sys.path.insert(0, str(DEPS_DIR))

try:
    import pymysql
    from pymysql.cursors import DictCursor
except ImportError as exc:  # pragma: no cover - startup diagnostic
    raise SystemExit(
        "PyMySQL is required. Install it with: "
        "python -m pip install --target .deps PyMySQL"
    ) from exc

from erp_read_surfaces import (
    basic_module,
    foundation_overview,
    mama_box_overview,
    maternity_nurse_module,
    nursing_module,
    report_module,
    risk_module,
    system_module,
)
from operational_records import (
    apply_action,
    business_no,
    clean_payload,
    identifier_field,
    parse_record_id,
    validate_resource,
)
from runtime_security import (
    LOCAL_TOKEN_SECRET,
    RuntimeConfigError,
    allowed_store_id,
    database_ssl_config,
    discover_migrations,
    is_production,
    migration_checksum_matches,
    migration_state,
    parse_bool,
    store_scope_clause,
    validate_runtime_config,
)


MIGRATION_DIR = REPO_ROOT / "database" / "mysql" / "migrations"
MIGRATION_MIN_SEQUENCE = 4
MIGRATION_LOCK_NAME = "qdf_erp_schema_migration"
LOCAL_ACCEPTANCE_MARKER = re.compile(r"LOCAL_ACCEPTANCE_SEED_\d+")
CONTRACT_TYPES = (
    "月子合同",
    "婴儿托管",
    "试住合同",
    "续住合同",
    "小月子合同",
    "到家合同",
)
RECEIPT_TYPES = (
    "合同首付",
    "合同补余收款",
    "合同收款",
    "其他收款",
    "续房收款",
    "服务升级收款",
    "销售收款",
    "产康合同收款",
    "月嫂合同收款",
)
PAYMENT_METHODS = ("现金", "银行卡", "微信", "支付宝", "转账")
PACKAGE_VERSION_STATUSES = ("DRAFT", "ACTIVE", "INACTIVE")
SERVICE_TARGET_MODULES = (
    "NURSING",
    "RECOVERY",
    "DIET",
    "ROOM",
    "MATRON",
    "MALL",
    "OTHER",
)
ENTITLEMENT_MODES = (
    "COUNT",
    "ON_DEMAND",
    "DAILY",
    "WEEKLY",
    "CHOICE",
    "GIFT",
)
LEGACY_ROLE_ACCOUNTS = (
    {
        "username": "韩新",
        "staff_names": ("韩新",),
        "role_code": "SALES_MANAGER",
        # The authenticated legacy page exposed both stores and defaulted to
        # the centre/建设路 store (see V20260727_016).
        "default_store_id": 1,
        "store_ids": (1, 2),
        "password_env": "ERP_SALES_ACCOUNT_PASSWORD",
    },
    {
        "username": "许曼",
        "staff_names": ("许曼", "许曼曼"),
        "role_code": "RECOVERY_THERAPIST",
        "default_store_id": 2,
        "store_ids": (2,),
        "password_env": "ERP_RECOVERY_ACCOUNT_PASSWORD",
    },
    {
        "username": "董丽霞",
        "staff_names": ("董丽霞",),
        "role_code": "HOUSEKEEPER",
        "default_store_id": 2,
        "store_ids": (2,),
        "password_env": "ERP_ROOM_ACCOUNT_PASSWORD",
    },
)


def public_business_payload(value):
    """Hide local acceptance bookkeeping markers from formal Web responses."""
    if isinstance(value, dict):
        return {key: public_business_payload(item) for key, item in value.items()}
    if isinstance(value, list):
        return [public_business_payload(item) for item in value]
    if isinstance(value, tuple):
        return tuple(public_business_payload(item) for item in value)
    if isinstance(value, str):
        return LOCAL_ACCEPTANCE_MARKER.sub("资料已核验", value)
    return value

RECOVERY_RESOURCE_NAV_IDS = {
    "unbooked-customer-services": 266,
    "service-appointments": 257,
    "service-overview-query": 553,
    "staff-task-board": 490,
    "staff-schedule-settings": 541,
    "technician-task-board": 660,
    "customer-service-query": 334,
    "rehab-service-records": 255,
    "completed-service-consumption": 618,
    "rehab-health-assessments": 631,
    "recovery-programs": 553,
    "recovery-schedule": 257,
    "postpartum-assessments": 631,
    "recovery-service-tracking": 255,
    "recovery-store-dashboard": 553,
    "recovery-upsell": 266,
    "recovery-assets": 618,
    "recovery-staff-performance": 541,
}

FORMAL_RECOVERY_RESOURCES = {
    "recovery-programs",
    "recovery-schedule",
    "postpartum-assessments",
    "recovery-service-tracking",
    "recovery-store-dashboard",
    "recovery-upsell",
    "recovery-assets",
    "recovery-staff-performance",
}

RECOVERY_ACTION_BUTTON_IDS = {
    "unbooked-customer-services": {"设置": 20, "读卡": 18},
    "service-appointments": {
        "打印": 48,
        "服务预约": 86,
        "确认完成": 37,
        "取消": 65,
        "预约确认": 91,
        "读卡": 18,
    },
    "staff-task-board": {"添加": 1, "确认完成": 37, "取消": 65},
    "staff-schedule-settings": {"添加": 1, "编辑": 10, "删除": 3},
    "technician-task-board": {"添加": 1, "确认完成": 37, "取消": 65},
    "rehab-service-records": {
        "编辑": 10,
        "批量修改": 145,
        "删除": 3,
        "导出": 19,
        "打印": 48,
        "审核": 21,
        "反审核": 49,
    },
    "rehab-health-assessments": {"添加": 1, "编辑": 10, "删除": 3},
}

FINANCE_RESOURCE_NAV_IDS = {
    "receipt-create": 521,
    "receipts": 90,
    "refund-applications": 95,
    "refund-audits": 96,
    "debt-audits": 281,
    "exchange-audits": 653,
    "invoices": 572,
    "reconciliations": 90,
    "material-budgets": 251,
    "my-expenses": 317,
    "expense-audits": 607,
    "payments": 415,
}

FINANCE_ACTION_BUTTON_IDS = {
    "receipts": {
        "前往新增收款": 1,
        "删除": 3,
        "编辑": 10,
        "导出": 19,
        "审核": 21,
        "打印": 48,
        "反审核": 49,
        "核销": 60,
        "星支付": 93,
        "批量审核": 96,
        "登记真实发票": 120,
        "手续费": 125,
        "扫码支付": 137,
    },
    "refund-applications": {
        "添加": 1,
        "删除": 3,
        "编辑": 10,
        "导出": 19,
        "打印": 48,
        "提交": 58,
    },
    "refund-audits": {
        "反审核": 49,
        "流程审批": 51,
        "登记退款打款": 54,
        "撤回": 132,
    },
    "debt-audits": {"审核": 21},
    "exchange-audits": {"删除": 3, "审核": 21},
    "invoices": {"删除": 3, "导出": 19},
    "reconciliations": {
        "添加": 1,
        "确认匹配": 21,
        "取消匹配": 49,
        "删除": 3,
        "导出": 19,
    },
    "material-budgets": {
        "添加": 1,
        "删除": 3,
        "编辑": 10,
        "导出": 19,
        "流程审批": 51,
        "提交": 58,
        "生成采购计划": 59,
    },
    "my-expenses": {
        "添加": 1,
        "删除": 3,
        "编辑": 10,
        "导出": 19,
        "打印": 48,
        "反审核": 49,
        "打款": 54,
        "提交": 58,
    },
    "expense-audits": {"流程审批": 51},
    "payments": {"导出": 19},
}

ROOM_RESOURCE_NAV_IDS = {
    "room-map": 418,
    "room-trend": 526,
    "room-type-trend": 587,
    "smart-allocation": 517,
    "saleable-statistics": 567,
    "room-type-bookings": 424,
    "room-reservations": 375,
    "room-stays": 558,
    "stay-extensions": 615,
    "room-change-applications": 584,
    "gift-distribution": 284,
    "room-services": 236,
    "outing-applications": 113,
    "borrowed-items": 235,
    "laundry": 238,
}

ROOM_ACTION_BUTTON_IDS = {
    "room-map": {
        "商品销售": 105,
        "订房": 79,
        "入住": 80,
        "续住": 81,
        "换房": 82,
        "退房": 83,
        "结账": 62,
        "入住通知单": 84,
        "客房服务申请": 85,
        "服务预约": 86,
        "房型订房": 87,
        "维修/脏房": 70,
        "跨店订房": 115,
        "跨店换房": 116,
    },
    "smart-allocation": {"订房": 79},
    "room-type-bookings": {"删除": 3, "房型订房": 87},
    "room-reservations": {"编辑": 10, "退订": 76, "退订并结账": 77},
    "room-stays": {
        "编辑": 10,
        "导出": 19,
        "取消": 65,
        "续住": 81,
        "换房": 82,
    },
    "stay-extensions": {
        "删除": 3,
        "编辑": 10,
        "审核": 21,
        "反审核": 49,
        "取消": 65,
    },
    "room-change-applications": {
        "删除": 3,
        "审核": 21,
        "反审核": 49,
    },
    "gift-distribution": {"物品发放": 78},
    "room-services": {"确认完成": 37, "取消": 65, "预约确认": 91},
    "outing-applications": {
        "添加": 1,
        "删除": 3,
        "编辑": 10,
        "审核": 21,
        "确定已返回": 36,
        "打印": 48,
    },
    "borrowed-items": {
        "添加": 1,
        "删除": 3,
        "编辑": 10,
        "确认签收": 38,
        "打印": 48,
    },
    "laundry": {
        "添加": 1,
        "删除": 3,
        "编辑": 10,
        "确认签收": 38,
    },
}

SALES_RESOURCE_NAV_IDS = {
    "contracts": 85,
    "packages": 87,
    "gift-lists": 237,
    "discounts": 310,
    "card-packages": 412,
    "product-sales": 523,
    "coupons": 534,
    "gift-applications": 556,
    "sales-details": 602,
}

SALES_ACTION_BUTTON_IDS = {
    "contracts": {
        "添加": 1,
        "删除": 3,
        "编辑": 10,
        "导出": 19,
        "设置": 20,
        "审核": 21,
        "打印": 48,
        "反审核": 49,
        "流程审批": 51,
        "提交": 58,
        "取消": 65,
        "套餐升级": 71,
        # Legacy renders this action but does not publish a distinct button
        # id. Keep the observed capability separate from page browsing.
        "膳食套餐": "SALES.CONTRACT.MEAL_PACKAGE.UPDATE",
        "编辑模板": 114,
        "变更": 124,
        "远程签约": 151,
        "折扣率审核": 155,
    },
    "packages": {
        "添加": 1,
        "删除": 3,
        "编辑": 10,
        "设置": 20,
        "审核": 21,
        "复制": 28,
        "启用": 34,
        "反审核": 49,
        "流程审批": 51,
        "提交": 58,
        "推荐/取消": 130,
        "屏蔽/取消": 131,
    },
    "gift-lists": {"添加": 1, "删除": 3, "编辑": 10},
    "discounts": {
        "添加": 1,
        "删除": 3,
        "编辑": 10,
        "导出": 19,
        "审核": 21,
        "停用": 35,
        "反审核": 49,
        "核销": "SALES.DISCOUNT.CONSUME",
    },
    "card-packages": {
        "添加": 1,
        "删除": 3,
        "编辑": 10,
        "复制": 28,
    },
    "product-sales": {
        "删除": 3,
        "编辑": 10,
        "导出": 19,
        "打印": 48,
        "退货": 64,
        "取消": 65,
        "收款": 66,
        "服务销售": 72,
        "物料销售": 73,
        "卡类销售": 75,
        "是否启用": 88,
        "出库": 92,
        "星支付": 93,
        "变更": 124,
        "介绍分配": 141,
        "取消退货": 147,
        "折扣率审核": 155,
    },
    "coupons": {"添加": 1, "删除": 3, "编辑": 10, "分发": 95},
    "gift-applications": {
        "删除": 3,
        "反审核": 49,
        "流程审批": 51,
        "服务销售": 72,
        "物料销售": 73,
        "卡类销售": 75,
        "撤回": 132,
    },
    "sales-details": {"导出": 19},
}


class ApiError(Exception):
    def __init__(self, message: str, status: int = 400, code: int = 40000):
        super().__init__(message)
        self.message = message
        self.status = status
        self.code = code


CUSTOMER_SERVICE_TRANSITIONS = {
    "F005": {
        "START": ({"待回访"}, "跟进中"),
        "COMPLETE": ({"待回访", "跟进中"}, "已完成"),
        "ESCALATE": ({"待回访", "跟进中"}, "已升级"),
        "REOPEN": ({"已完成", "已升级"}, "跟进中"),
    },
    "F043": {
        "SUBMIT": ({"草稿"}, "待审核"),
        "PUBLISH": ({"待审核"}, "已发布"),
        "DISABLE": ({"已发布"}, "已停用"),
        "REOPEN": ({"待审核", "已停用"}, "草稿"),
    },
    "F084": {
        "QUEUE": ({"草稿"}, "待发送"),
        "SEND": ({"待发送", "待通道配置"}, "已发送"),
        "CANCEL": ({"草稿", "待发送", "待通道配置"}, "已取消"),
    },
    "F094": {
        "ACCEPT": ({"待接入"}, "处理中"),
        "REPLY": ({"处理中", "等待客户"}, "处理中"),
        "WAIT": ({"处理中"}, "等待客户"),
        "TRANSFER": ({"待接入", "处理中", "等待客户"}, "已转工单"),
        "AI_REPLY": ({"处理中"}, "处理中"),
        "CLOSE": ({"处理中", "等待客户", "已转工单"}, "已关闭"),
    },
}


def customer_service_transition(
    feature_code: str,
    current_status: str,
    action: str,
    channel: str = "",
) -> tuple[str, bool]:
    """Validate one customer-service state transition.

    The boolean indicates that an external integration is required and must
    never be reported as successful by the local ERP.
    """
    feature = str(feature_code or "").upper()
    action_code = str(action or "").upper()
    transition = CUSTOMER_SERVICE_TRANSITIONS.get(feature, {}).get(action_code)
    if not transition:
        raise ApiError("当前客服状态操作不存在", 404, 40400)
    allowed_states, target_status = transition
    if current_status not in allowed_states:
        raise ApiError("当前状态不能执行此操作", 409, 40900)
    external_required = action_code == "AI_REPLY"
    if feature == "F084" and action_code == "SEND":
        internal_channels = {"站内", "站内消息", "站内通知"}
        external_required = str(channel or "").strip() not in internal_channels
        if external_required:
            target_status = "待通道配置"
    return target_status, external_required


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def db_config(database: str | None = None) -> dict:
    try:
        validate_runtime_config()
        ssl = database_ssl_config()
    except RuntimeConfigError as exc:
        raise SystemExit(str(exc)) from exc
    config = {
        "host": env("ERP_DB_HOST", "127.0.0.1"),
        "port": int(env("ERP_DB_PORT", "3306")),
        "user": env("ERP_DB_USER", "root"),
        "password": env("ERP_DB_PASSWORD"),
        "database": database or env("ERP_DB_NAME", "yuezi"),
        "charset": "utf8mb4",
        "cursorclass": DictCursor,
        "autocommit": False,
        "connect_timeout": int(env("ERP_DB_CONNECT_TIMEOUT", "5")),
        "read_timeout": int(env("ERP_DB_READ_TIMEOUT", "30")),
        "write_timeout": int(env("ERP_DB_WRITE_TIMEOUT", "30")),
    }
    if ssl:
        config["ssl"] = ssl
    return config


def connect(database: str | None = None):
    return pymysql.connect(**db_config(database))


def json_default(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return value.isoformat(sep=" ")
    if isinstance(value, date):
        return value.isoformat()
    raise TypeError(f"Unsupported JSON value: {type(value)!r}")


def compact_json(value) -> str:
    return json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), default=json_default
    )


def encode_segment(value: dict) -> str:
    payload = compact_json(value).encode("utf-8")
    return base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")


def decode_segment(value: str) -> dict:
    padding = "=" * (-len(value) % 4)
    return json.loads(base64.urlsafe_b64decode(value + padding))


def token_secret() -> bytes:
    configured = env("ERP_TOKEN_SECRET")
    if configured:
        return configured.encode("utf-8")
    if is_production():
        raise RuntimeConfigError("ERP_TOKEN_SECRET is required in production.")
    return LOCAL_TOKEN_SECRET.encode("utf-8")


def issue_token(user_id: int, username: str) -> str:
    payload = encode_segment(
        {
            "uid": user_id,
            "username": username,
            "exp": int(time.time()) + 12 * 60 * 60,
        }
    )
    signature = hmac.new(
        token_secret(), payload.encode("ascii"), hashlib.sha256
    ).digest()
    return f"{payload}.{base64.urlsafe_b64encode(signature).rstrip(b'=').decode('ascii')}"


def verify_token(token: str) -> dict:
    try:
        payload, signature = token.split(".", 1)
        expected = hmac.new(
            token_secret(), payload.encode("ascii"), hashlib.sha256
        ).digest()
        actual = base64.urlsafe_b64decode(signature + "=" * (-len(signature) % 4))
        if not hmac.compare_digest(expected, actual):
            raise ValueError("signature")
        decoded = decode_segment(payload)
        if int(decoded["exp"]) < int(time.time()):
            raise ValueError("expired")
        return decoded
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ApiError("登录状态已失效，请重新登录", 401, 50008) from exc


def hash_password(password: str) -> str:
    iterations = 180_000
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, iterations
    )
    return "pbkdf2_sha256${}${}${}".format(
        iterations,
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(digest).decode("ascii"),
    )


def check_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            base64.b64decode(salt),
            int(iterations),
        )
        return hmac.compare_digest(actual, base64.b64decode(expected))
    except (TypeError, ValueError):
        return False


def execute_one(connection, sql: str, params=()):
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        return cursor.fetchone()


def execute_all(connection, sql: str, params=()):
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        return cursor.fetchall()


def split_sql(sql_text: str) -> list[str]:
    lines = [
        line
        for line in sql_text.splitlines()
        if not line.lstrip().startswith("--")
    ]
    return [statement.strip() for statement in "\n".join(lines).split(";") if statement.strip()]


def _migration_state_from_rows(
    all_migrations,
    active_migrations,
    applied_rows,
) -> dict:
    known = {item.version: item for item in all_migrations}
    active_versions = {item.version for item in active_migrations}
    applied = {row["version"]: row["checksum"] for row in applied_rows}
    state_input = {
        version: checksum
        for version, checksum in applied.items()
        if version in active_versions or version not in known
    }
    state = migration_state(active_migrations, state_input)
    baseline_mismatches = [
        version
        for version, checksum in applied.items()
        if version in known
        and version not in active_versions
        and not migration_checksum_matches(known[version], checksum)
    ]
    state["checksumMismatches"] = sorted(
        set(state["checksumMismatches"] + baseline_mismatches)
    )
    state["current"] = (
        not state["pending"]
        and not state["checksumMismatches"]
        and not state["unknownApplied"]
    )
    return state


def _migration_status(connection) -> dict:
    all_migrations = discover_migrations(
        MIGRATION_DIR,
        minimum_sequence=1,
    )
    migrations = tuple(
        item for item in all_migrations if item.sequence >= MIGRATION_MIN_SEQUENCE
    )
    table = execute_one(
        connection,
        """
        SELECT COUNT(*) AS total
        FROM information_schema.tables
        WHERE table_schema=%s AND table_name='schema_migrations'
        """,
        (env("ERP_DB_NAME", "yuezi"),),
    )
    if not table or not table["total"]:
        status = migration_state(migrations, {})
        status["schemaTable"] = False
        return status
    applied_rows = execute_all(
        connection,
        "SELECT version, checksum FROM schema_migrations ORDER BY version",
    )
    status = _migration_state_from_rows(
        all_migrations,
        migrations,
        applied_rows,
    )
    status["schemaTable"] = True
    return status


def apply_migrations(include_baseline: bool = False) -> list[dict]:
    all_migrations = discover_migrations(
        MIGRATION_DIR,
        minimum_sequence=1,
    )
    migrations = (
        all_migrations
        if include_baseline
        else tuple(
            item
            for item in all_migrations
            if item.sequence >= MIGRATION_MIN_SEQUENCE
        )
    )
    connection = connect()
    lock_acquired = False
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT GET_LOCK(%s, %s) AS acquired",
                (
                    MIGRATION_LOCK_NAME,
                    int(env("ERP_MIGRATION_LOCK_TIMEOUT", "30")),
                ),
            )
            lock_acquired = cursor.fetchone()["acquired"] == 1
            if not lock_acquired:
                raise RuntimeError("Could not acquire the database migration lock.")
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                  version VARCHAR(64) NOT NULL,
                  description VARCHAR(255) NOT NULL,
                  checksum CHAR(64) NOT NULL,
                  applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  PRIMARY KEY (version)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                  COLLATE=utf8mb4_unicode_ci
                """
            )
            connection.commit()
            applied_rows = execute_all(
                connection,
                "SELECT version, checksum FROM schema_migrations ORDER BY version",
            )
            state = _migration_state_from_rows(
                all_migrations,
                migrations,
                applied_rows,
            )
            if state["checksumMismatches"]:
                raise RuntimeError(
                    "Applied migration checksum mismatch: "
                    + ", ".join(state["checksumMismatches"])
                )
            if state["unknownApplied"]:
                raise RuntimeError(
                    "Database contains migrations absent from this release: "
                    + ", ".join(state["unknownApplied"])
                )
            results = []
            for migration in migrations:
                cursor.execute(
                    "SELECT checksum FROM schema_migrations WHERE version=%s",
                    (migration.version,),
                )
                existing = cursor.fetchone()
                if existing:
                    results.append(
                        {
                            "version": migration.version,
                            "status": "already-applied",
                        }
                    )
                    continue
                sql_text = migration.path.read_text(encoding="utf-8")
                for statement in split_sql(sql_text):
                    cursor.execute(statement)
                cursor.execute(
                    """
                    INSERT INTO schema_migrations(version, description, checksum)
                    VALUES (%s, %s, %s)
                    """,
                    (
                        migration.version,
                        migration.description,
                        migration.checksum,
                    ),
                )
                connection.commit()
                results.append(
                    {"version": migration.version, "status": "applied"}
                )
        return results
    except Exception:
        connection.rollback()
        raise
    finally:
        if lock_acquired:
            try:
                execute_one(
                    connection,
                    "SELECT RELEASE_LOCK(%s) AS released",
                    (MIGRATION_LOCK_NAME,),
                )
            except Exception:
                pass
        connection.close()


def bootstrap(seed_rooms: bool = True) -> dict:
    username = env("ERP_BOOTSTRAP_ADMIN_USERNAME", "admin")
    password = env("ERP_BOOTSTRAP_ADMIN_PASSWORD")
    if not password:
        raise SystemExit("ERP_BOOTSTRAP_ADMIN_PASSWORD is required.")
    connection = connect()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT role_id FROM roles
                WHERE tenant_id=1 AND code='SYS_ADMIN'
                ORDER BY role_id LIMIT 1
                """
            )
            role = cursor.fetchone()
            if not role:
                raise SystemExit("SYS_ADMIN role is missing. Apply V001 first.")
            cursor.execute(
                """
                SELECT store_id FROM stores
                WHERE tenant_id=1 ORDER BY sort_weight DESC, store_id
                """
            )
            stores = cursor.fetchall()
            if not stores:
                raise SystemExit("No active store is available.")
            cursor.execute(
                """
                SELECT user_id FROM user_accounts
                WHERE tenant_id=1 AND username=%s
                """,
                (username,),
            )
            account = cursor.fetchone()
            encoded = hash_password(password)
            if account:
                user_id = account["user_id"]
                cursor.execute(
                    """
                    UPDATE user_accounts
                    SET password_hash=%s, status='ACTIVE',
                        failed_login_count=0, locked_until=NULL,
                        password_changed_at=NOW()
                    WHERE user_id=%s
                    """,
                    (encoded, user_id),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO user_accounts(
                      tenant_id, username, password_hash, default_store_id,
                      status, password_changed_at
                    ) VALUES (1, %s, %s, %s, 'ACTIVE', NOW())
                    """,
                    (username, encoded, stores[0]["store_id"]),
                )
                user_id = cursor.lastrowid
            cursor.execute(
                """
                INSERT IGNORE INTO user_roles(user_id, role_id, effective_from)
                VALUES (%s, %s, NOW())
                """,
                (user_id, role["role_id"]),
            )
            for store in stores:
                cursor.execute(
                    """
                    INSERT INTO user_stores(user_id, store_id, access_level)
                    VALUES (%s, %s, 'MANAGE')
                    ON DUPLICATE KEY UPDATE access_level='MANAGE'
                    """,
                    (user_id, store["store_id"]),
                )
            seeded_rooms = 0
            if seed_rooms:
                room_numbers = (("201", 2), ("202", 2))
                for store in stores:
                    cursor.execute(
                        """
                        SELECT COUNT(*) AS total
                        FROM rooms
                        WHERE tenant_id=1 AND store_id=%s
                        """,
                        (store["store_id"],),
                    )
                    if cursor.fetchone()["total"] == 0:
                        for room_no, floor in room_numbers:
                            cursor.execute(
                                """
                                INSERT INTO rooms(
                                  tenant_id, store_id, room_no, room_type,
                                  floor, price, status, created_at
                                ) VALUES (1, %s, %s, '标准房', %s, 0, '空闲', NOW())
                                """,
                                (store["store_id"], room_no, floor),
                            )
                            seeded_rooms += 1
        connection.commit()
        return {
            "username": username,
            "user_id": user_id,
            "stores": len(stores),
            "seeded_rooms": seeded_rooms,
        }
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def bootstrap_role_accounts() -> list[dict]:
    missing = [
        item["password_env"]
        for item in LEGACY_ROLE_ACCOUNTS
        if not env(item["password_env"])
    ]
    if missing:
        raise SystemExit(
            "Missing account password environment variables: " + ", ".join(missing)
        )
    connection = connect()
    created = []
    try:
        with connection.cursor() as cursor:
            for item in LEGACY_ROLE_ACCOUNTS:
                placeholders = ",".join(["%s"] * len(item["staff_names"]))
                cursor.execute(
                    f"""
                    SELECT staff_id, name, store_id
                    FROM staff
                    WHERE tenant_id=1 AND name IN ({placeholders})
                    ORDER BY FIELD(name, {placeholders})
                    LIMIT 1
                    """,
                    (*item["staff_names"], *item["staff_names"]),
                )
                staff = cursor.fetchone()
                if not staff:
                    raise SystemExit(
                        f"Employee record is missing for {item['username']}."
                    )
                if not staff["store_id"]:
                    raise SystemExit(
                        f"Employee {staff['name']} has no default store."
                    )
                cursor.execute(
                    """
                    SELECT role_id, name FROM roles
                    WHERE tenant_id=1 AND code=%s AND status='ACTIVE'
                    """,
                    (item["role_code"],),
                )
                role = cursor.fetchone()
                if not role:
                    raise SystemExit(f"Role {item['role_code']} is missing.")
                store_ids = tuple(item["store_ids"])
                placeholders = ",".join(["%s"] * len(store_ids))
                cursor.execute(
                    f"""
                    SELECT store_id FROM stores
                    WHERE tenant_id=1 AND store_id IN ({placeholders})
                    """,
                    store_ids,
                )
                existing_store_ids = {
                    int(row["store_id"]) for row in cursor.fetchall()
                }
                missing_store_ids = sorted(set(store_ids) - existing_store_ids)
                if missing_store_ids:
                    raise SystemExit(
                        "Account store scope is missing: "
                        + ", ".join(str(value) for value in missing_store_ids)
                    )
                cursor.execute(
                    """
                    SELECT user_id FROM user_accounts
                    WHERE tenant_id=1 AND username=%s
                    """,
                    (item["username"],),
                )
                account = cursor.fetchone()
                encoded = hash_password(env(item["password_env"]))
                if account:
                    user_id = account["user_id"]
                    cursor.execute(
                        """
                        UPDATE user_accounts
                        SET staff_id=%s, password_hash=%s, default_store_id=%s,
                            status='ACTIVE', failed_login_count=0,
                            locked_until=NULL, password_changed_at=NOW()
                        WHERE user_id=%s
                        """,
                        (
                            staff["staff_id"],
                            encoded,
                            item["default_store_id"],
                            user_id,
                        ),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO user_accounts(
                          tenant_id, staff_id, username, password_hash,
                          default_store_id, status, password_changed_at
                        ) VALUES (1,%s,%s,%s,%s,'ACTIVE',NOW())
                        """,
                        (
                            staff["staff_id"],
                            item["username"],
                            encoded,
                            item["default_store_id"],
                        ),
                    )
                    user_id = cursor.lastrowid
                cursor.execute("DELETE FROM user_roles WHERE user_id=%s", (user_id,))
                cursor.execute(
                    """
                    INSERT INTO user_roles(user_id, role_id, effective_from)
                    VALUES (%s,%s,NOW())
                    """,
                    (user_id, role["role_id"]),
                )
                cursor.execute("DELETE FROM user_stores WHERE user_id=%s", (user_id,))
                for store_id in store_ids:
                    cursor.execute(
                        """
                        INSERT INTO user_stores(user_id, store_id, access_level)
                        VALUES (%s,%s,'MANAGE')
                        """,
                        (user_id, store_id),
                    )
                created.append(
                    {
                        "username": item["username"],
                        "staff_name": staff["name"],
                        "role_code": item["role_code"],
                        "role_name": role["name"],
                        "default_store_id": item["default_store_id"],
                        "store_ids": list(store_ids),
                    }
                )
        connection.commit()
        return created
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def verify_database() -> dict:
    connection = connect()
    try:
        result = {"migrations": _migration_status(connection)}
        for table in (
            "user_accounts",
            "customers",
            "contracts",
            "finance_receipts",
            "rooms",
            "room_bookings",
            "mvp_audit_events",
        ):
            row = execute_one(connection, f"SELECT COUNT(*) AS total FROM {table}")
            result[table] = row["total"]
        result["access_control"] = {
            "total_roles": execute_one(
                connection,
                "SELECT COUNT(*) AS total FROM roles WHERE tenant_id=1",
            )["total"],
            "active_roles": execute_one(
                connection,
                """
                SELECT COUNT(*) AS total FROM roles
                WHERE tenant_id=1 AND status='ACTIVE'
                """,
            )["total"],
            "active_legacy_roles": execute_one(
                connection,
                """
                SELECT COUNT(*) AS total FROM roles
                WHERE tenant_id=1 AND source_system='LEGACY_ERP'
                  AND legacy_role_id IS NOT NULL AND status='ACTIVE'
                """,
            )["total"],
            "active_legacy_accounts": execute_one(
                connection,
                """
                SELECT COUNT(*) AS total FROM user_accounts
                WHERE tenant_id=1 AND source_system='LEGACY_ERP'
                  AND legacy_user_id IS NOT NULL AND status='ACTIVE'
                """,
            )["total"],
            "disabled_legacy_accounts": execute_one(
                connection,
                """
                SELECT COUNT(*) AS total FROM user_accounts
                WHERE tenant_id=1 AND source_system='LEGACY_ERP'
                  AND legacy_user_id IS NOT NULL AND status='DISABLED'
                """,
            )["total"],
            "excluded_legacy_roles": execute_one(
                connection,
                "SELECT COUNT(*) AS total FROM legacy_role_exclusions",
            )["total"],
            "legacy_permission_resources": execute_one(
                connection,
                "SELECT COUNT(*) AS total FROM legacy_permission_resources",
            )["total"],
            "legacy_data_scope_grants": execute_one(
                connection,
                "SELECT COUNT(*) AS total FROM legacy_role_data_scope_grants",
            )["total"],
        }
        result["verified_accounts"] = execute_all(
            connection,
            """
            SELECT ua.username, s.name AS staff_name,
                   GROUP_CONCAT(DISTINCT r.code ORDER BY r.code SEPARATOR ',')
                     AS role_codes,
                   GROUP_CONCAT(DISTINCT us.store_id ORDER BY us.store_id SEPARATOR ',')
                     AS store_ids
            FROM user_accounts ua
            LEFT JOIN staff s ON s.staff_id=ua.staff_id
            LEFT JOIN user_roles ur ON ur.user_id=ua.user_id
              AND ur.effective_from<=NOW()
              AND (ur.effective_to IS NULL OR ur.effective_to>NOW())
            LEFT JOIN roles r ON r.role_id=ur.role_id
            LEFT JOIN user_stores us ON us.user_id=ua.user_id
            WHERE ua.tenant_id=1
              AND ua.username IN ('admin','韩新','许曼','董丽霞')
            GROUP BY ua.user_id
            ORDER BY ua.user_id
            """,
        )
        integrity_checks = {
            "cross_tenant_staff_accounts": """
                SELECT COUNT(*) AS total
                FROM user_accounts ua
                JOIN staff st ON st.staff_id=ua.staff_id
                WHERE st.tenant_id<>ua.tenant_id
            """,
            "cross_tenant_default_stores": """
                SELECT COUNT(*) AS total
                FROM user_accounts ua
                JOIN stores s ON s.store_id=ua.default_store_id
                WHERE s.tenant_id<>ua.tenant_id
            """,
            "cross_tenant_user_stores": """
                SELECT COUNT(*) AS total
                FROM user_stores us
                JOIN user_accounts ua ON ua.user_id=us.user_id
                JOIN stores s ON s.store_id=us.store_id
                WHERE s.tenant_id<>ua.tenant_id
            """,
            "cross_tenant_user_roles": """
                SELECT COUNT(*) AS total
                FROM user_roles ur
                JOIN user_accounts ua ON ua.user_id=ur.user_id
                JOIN roles r ON r.role_id=ur.role_id
                WHERE r.tenant_id<>ua.tenant_id
            """,
            "default_store_without_grant": """
                SELECT COUNT(*) AS total
                FROM user_accounts ua
                LEFT JOIN user_stores us
                  ON us.user_id=ua.user_id
                 AND us.store_id=ua.default_store_id
                WHERE ua.status='ACTIVE' AND ua.default_store_id IS NOT NULL
                  AND us.user_id IS NULL
            """,
            "active_accounts_without_store": """
                SELECT COUNT(*) AS total
                FROM user_accounts ua
                LEFT JOIN user_stores us ON us.user_id=ua.user_id
                WHERE ua.status='ACTIVE'
                GROUP BY ua.user_id
                HAVING COUNT(us.store_id)=0
            """,
        }
        security_integrity = {}
        for name, sql in integrity_checks.items():
            if name == "active_accounts_without_store":
                security_integrity[name] = len(execute_all(connection, sql))
            else:
                security_integrity[name] = execute_one(connection, sql)["total"]
        result["security_integrity"] = security_integrity
        result["security_integrity_passed"] = (
            result["migrations"]["current"]
            and all(value == 0 for value in security_integrity.values())
        )
        return result
    finally:
        connection.close()


class MvpRequestHandler(BaseHTTPRequestHandler):
    server_version = "QdfMvpApi/1.0"

    def log_message(self, format_string, *args):
        sys.stdout.write(
            "%s - %s\n" % (self.log_date_time_string(), format_string % args)
        )
        sys.stdout.flush()

    def do_OPTIONS(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        self._cors_headers()
        self._security_headers()
        self.end_headers()

    def do_GET(self):
        self._handle()

    def do_POST(self):
        self._handle()

    def _cors_headers(self):
        origin = self.headers.get("Origin", "")
        allowed = {
            item.strip()
            for item in env(
                "ERP_CORS_ORIGINS",
                (
                    "http://localhost:9527,http://127.0.0.1:9527,"
                    "http://localhost:9530,http://127.0.0.1:9530"
                ),
            ).split(",")
            if item.strip()
        }
        if origin in allowed:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Token")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")

    def _security_headers(self):
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")

    def _json(self, status: int, payload: dict):
        body = json.dumps(
            payload, ensure_ascii=False, default=json_default
        ).encode("utf-8")
        self.send_response(status)
        self._cors_headers()
        self._security_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _success(self, data=None):
        self._json(
            200,
            {"code": 20000, "data": public_business_payload(data or {})},
        )

    def _body(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise ApiError("Content-Length 不正确") from exc
        if length <= 0:
            return {}
        maximum = int(env("ERP_MAX_REQUEST_BYTES", str(1024 * 1024)))
        if length > maximum:
            raise ApiError("请求内容过大", 413, 41300)
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ApiError("请求内容不是有效 JSON") from exc

    def _handle(self):
        connection = None
        try:
            parsed = urlparse(self.path)
            path = parsed.path.rstrip("/") or "/"
            query = {key: values[-1] for key, values in parse_qs(parsed.query).items()}
            body = self._body() if self.command == "POST" else {}

            if path == "/api/health":
                return self._success(
                    {
                        "service": "qdf-erp-mvp",
                        "status": "alive",
                        "time": datetime.now().isoformat(timespec="seconds"),
                    }
                )

            connection = connect()
            if path == "/api/ready":
                database = execute_one(connection, "SELECT 1 AS ready")
                migrations = _migration_status(connection)
                status = 200 if database and migrations["current"] else 503
                return self._json(
                    status,
                    {
                        "code": 20000 if status == 200 else 50300,
                        "data": {
                            "service": "qdf-erp-mvp",
                            "status": "ready" if status == 200 else "not-ready",
                            "migrations": migrations,
                        },
                    },
                )
            if path == "/vue-element-admin/user/login" and self.command == "POST":
                return self._login(connection, body)
            if (
                path == "/vue-element-admin/user/logout"
                and self.command == "POST"
            ):
                # Logout must also succeed for an expired or previously signed
                # token so the web client can clear its local session cleanly.
                return self._success({"loggedOut": True})

            user = self._authenticate(connection, query)
            if path == "/vue-element-admin/user/info":
                return self._user_info(connection, user)

            baby_prefix = "/vue-element-admin/erp/baby/modules"
            if path.startswith(baby_prefix):
                resource = path[len(baby_prefix):].strip("/")
                operation = ""
                if resource.endswith(("/save", "/action")):
                    resource, operation = resource.rsplit("/", 1)
                if "/" in resource or not resource:
                    raise ApiError("宝宝照护资源不存在", 404, 40400)
                self._require_any_permission(user, ("NURSING.VIEW",))
                if self.command == "GET":
                    scoped_user = self._user_for_selected_store(user, query)
                    return self._success(
                        self._merge_operational_module_rows(
                            connection,
                            scoped_user,
                            "BABY",
                            resource,
                            query,
                            {"list": [], "total": 0},
                        )
                    )
                return self._post_operational_module_record(
                    connection,
                    user,
                    "BABY",
                    resource,
                    operation,
                    body,
                )

            foundation_prefix = "/vue-element-admin/erp/foundation"
            if path.startswith(foundation_prefix):
                resource = path[len(foundation_prefix):] or "/"
                self._require_any_permission(
                    user, ("SYSTEM.VIEW", "BASIC.VIEW")
                )
                if self.command == "GET" and resource == "/overview":
                    return self._success(foundation_overview(connection, self._user_for_selected_store(user, query)))
                if self.command == "POST":
                    return self._post_foundation_resource(
                        connection, user, resource, body
                    )
                raise ApiError("基础平台资源不存在", 404, 40400)

            read_module_routes = (
                (
                    "/vue-element-admin/erp/nursing/modules",
                    nursing_module,
                    ("NURSING.VIEW",),
                    "护理",
                ),
                (
                    "/vue-element-admin/erp/maternity-nurse/modules",
                    maternity_nurse_module,
                    ("MATRON.VIEW", "NURSING.VIEW"),
                    "月嫂",
                ),
                (
                    "/vue-element-admin/erp/report/modules",
                    report_module,
                    ("REPORT.VIEW",),
                    "查询报表",
                ),
                (
                    "/vue-element-admin/erp/system/modules",
                    system_module,
                    ("SYSTEM.VIEW",),
                    "系统设置",
                ),
                (
                    "/vue-element-admin/erp/basic/modules",
                    basic_module,
                    ("BASIC.VIEW", "SYSTEM.VIEW"),
                    "基础资料",
                ),
                (
                    "/vue-element-admin/erp/risk/modules",
                    risk_module,
                    ("RISK.VIEW",),
                    "风控",
                ),
            )
            for route_prefix, loader, permissions, module_name in (
                read_module_routes
            ):
                if not path.startswith(route_prefix):
                    continue
                resource = path[len(route_prefix):].strip("/")
                operation = ""
                if resource.endswith(("/save", "/action")):
                    resource, operation = resource.rsplit("/", 1)
                if "/" in resource or not resource:
                    if self.command == "GET" and resource.endswith("/preview"):
                        resource = resource.rsplit("/", 1)[0]
                    else:
                        raise ApiError(
                            f"{module_name}资源不存在", 404, 40400
                        )
                self._require_any_permission(user, permissions)
                if (
                    self.command == "GET"
                    and module_name == "护理"
                    and resource == "reference-options"
                ):
                    return self._get_store_reference_options(
                        connection, user, "NURSING", query
                    )
                if self.command != "GET":
                    if module_name == "护理" and operation:
                        return self._post_operational_module_record(
                            connection,
                            user,
                            "NURSING",
                            resource,
                            operation,
                            body,
                        )
                    if module_name == "月嫂" and operation:
                        return self._post_operational_module_record(
                            connection,
                            user,
                            "MATRON",
                            resource,
                            operation,
                            body,
                        )
                    durable_module = {
                        "查询报表": "REPORT",
                        "基础资料": "BASIC",
                    }.get(module_name)
                    if durable_module and operation:
                        return self._post_operational_module_record(
                            connection,
                            user,
                            durable_module,
                            resource,
                            operation,
                            body,
                        )
                    raise ApiError(
                        f"当前{module_name}页面尚未接入写操作",
                        403,
                        40300,
                    )
                try:
                    scoped_user = self._user_for_selected_store(user, query)
                    requested_store = self._requested_store_id(scoped_user, query)
                    data = (
                        loader(
                            connection,
                            scoped_user,
                            resource,
                            requested_store,
                        )
                        if module_name == "护理"
                        else loader(connection, scoped_user, resource)
                    )
                    if (
                        module_name == "护理"
                        and resource != "nursing-center"
                    ):
                        data = self._merge_operational_module_rows(
                            connection,
                            scoped_user,
                            "NURSING",
                            resource,
                            query,
                            data,
                        )
                    if module_name == "月嫂":
                        data = self._merge_operational_module_rows(
                            connection,
                            scoped_user,
                            "MATRON",
                            resource,
                            query,
                            data,
                        )
                    return self._success(data)
                except KeyError as exc:
                    raise ApiError(
                        f"{module_name}资源不存在", 404, 40400
                    ) from exc

            mama_box_prefix = "/vue-element-admin/erp/mama-box"
            if path.startswith(mama_box_prefix):
                resource = unquote(path[len(mama_box_prefix):] or "/")
                self._require_any_permission(
                    user, ("MALL.VIEW", "SYSTEM.VIEW")
                )
                if self.command == "GET" and resource == "/overview":
                    return self._success(mama_box_overview(connection, user))
                save_match = re.fullmatch(r"/([^/]+)/save", resource)
                action_match = re.fullmatch(r"/([^/]+)/([^/]+)/([^/]+)", resource)
                if self.command == "POST" and (save_match or action_match):
                    resource_name = (save_match or action_match).group(1)
                    operation = "save" if save_match else "action"
                    payload = dict(body)
                    if action_match:
                        payload.setdefault("recordId", action_match.group(2))
                        payload.setdefault("action", action_match.group(3))
                    return self._post_operational_module_record(
                        connection, user, "MALL", resource_name, operation, payload
                    )
                raise ApiError("妈妈端管理资源不存在", 404, 40400)

            contract_archive_prefix = (
                "/vue-element-admin/erp/contract-archives"
            )
            if path.startswith(contract_archive_prefix):
                resource = path[len(contract_archive_prefix):] or "/"
                if self.command == "GET":
                    return self._get_contract_archive_resource(
                        connection, user, resource, query
                    )
                return self._post_contract_archive_resource(
                    connection, user, resource, body
                )

            finance_prefix = "/vue-element-admin/erp/finance"
            if path.startswith(finance_prefix):
                resource = path[len(finance_prefix):] or "/"
                if self.command == "GET":
                    return self._get_finance_resource(
                        connection, user, resource, query
                    )
                return self._post_finance_resource(
                    connection, user, resource, body
                )

            recovery_prefix = "/vue-element-admin/erp/rehab"
            if path.startswith(recovery_prefix):
                resource = path[len(recovery_prefix):] or "/"
                if self.command == "GET":
                    return self._get_recovery_resource(
                        connection, user, resource, query
                    )
                return self._post_recovery_resource(
                    connection, user, resource, body
                )

            research_prefix = "/vue-element-admin/erp/research/modules"
            if path.startswith(research_prefix):
                resource = path[len(research_prefix):].strip("/")
                operation = ""
                if resource.endswith(("/save", "/action")):
                    resource, operation = resource.rsplit("/", 1)
                if resource != "beauty-cases":
                    raise ApiError("科研美容资源不存在", 404, 40400)
                self._require_any_permission(
                    user, ("RECOVERY.VIEW", "CUSTOMER.VIEW")
                )
                if self.command == "GET":
                    scoped_user = self._user_for_selected_store(user, query)
                    rows = self._operational_module_rows(
                        connection,
                        scoped_user,
                        "RESEARCH",
                        resource,
                        query,
                    )
                    return self._success(
                        {"list": rows, "total": len(rows), "source": "mysql"}
                    )
                return self._post_operational_module_record(
                    connection,
                    user,
                    "RESEARCH",
                    resource,
                    operation,
                    body,
                )

            customer_prefix = "/vue-element-admin/erp/customer"
            if path.startswith(customer_prefix):
                resource = path[len(customer_prefix):] or "/"
                if self.command == "GET" and resource == "/entry-options":
                    return self._get_customer_entry_options(connection, user)
                customer_module = re.fullmatch(
                    r"/modules/([^/]+)", resource
                )
                if self.command == "GET" and customer_module:
                    return self._get_customer_module_data(
                        connection,
                        self._user_for_selected_store(user, query),
                        customer_module.group(1),
                        query,
                    )
                if self.command == "POST":
                    if resource == "/duplicate-check":
                        return self._check_customer_duplicate(
                            connection, user, body
                        )
                    if resource == "/draft":
                        return self._save_customer_entry_draft(
                            connection, user, body
                        )
                    if resource == "/":
                        return self._create_customer_entry(
                            connection, user, body
                        )
                    module_operation = re.fullmatch(
                        r"/modules/([^/]+)/(save|action)", resource
                    )
                    if module_operation:
                        module, operation = module_operation.groups()
                        return self._post_operational_module_record(
                            connection,
                            user,
                            "CUSTOMER",
                            module,
                            operation,
                            body,
                        )

            asset_prefix = "/vue-element-admin/erp/assets"
            if path.startswith(asset_prefix):
                resource = path[len(asset_prefix):] or "/"
                self._require_any_permission(
                    user, ("CUSTOMER.VIEW", "FINANCE.VIEW")
                )
                if self.command == "GET":
                    selected_store = str((query or {}).get("storeId") or "").strip().lower()
                    asset_user = user if selected_store in {"", "all"} else self._user_for_selected_store(user, query)
                    return self._get_member_asset_resource(
                        connection, asset_user, resource, query
                    )
                return self._post_member_asset_resource(
                    connection, user, resource, body
                )

            service_prefix = "/vue-element-admin/erp/service"
            if path.startswith(service_prefix):
                resource = path[len(service_prefix):] or "/"
                if self.command == "GET":
                    return self._get_service_resource(
                        connection,
                        user,
                        resource,
                        query,
                    )
                return self._post_service_resource(
                    connection, user, resource, body
                )

            diet_prefix = "/vue-element-admin/erp/diet/modules"
            if path.startswith(diet_prefix):
                resource = path[len(diet_prefix):].strip("/")
                if self.command == "GET":
                    if resource == "room-options":
                        return self._get_diet_room_options(
                            connection, user, query
                        )
                    if resource == "reference-options":
                        return self._get_store_reference_options(
                            connection, user, "DIET", query
                        )
                    return self._get_diet_module_data(
                        connection, user, resource, query
                    )
                match = re.fullmatch(r"([^/]+)/(save|action)", resource)
                if not match:
                    raise ApiError("膳食资源不存在", 404, 40400)
                return self._post_operational_module_record(
                    connection,
                    user,
                    "DIET",
                    match.group(1),
                    match.group(2),
                    body,
                )

            catalog_prefix = "/vue-element-admin/erp/catalog"
            if path.startswith(catalog_prefix):
                resource = path[len(catalog_prefix):] or "/"
                if self.command == "GET":
                    return self._get_catalog_resource(
                        connection, user, resource, query
                    )
                return self._post_catalog_resource(
                    connection, user, resource, body
                )

            sales_prefix = "/vue-element-admin/erp/sales/modules"
            if path.startswith(sales_prefix):
                resource = path[len(sales_prefix):] or "/"
                if self.command == "GET":
                    match = re.fullmatch(r"/([^/]+)", resource)
                    if not match:
                        raise ApiError("销售资源不存在", 404, 40400)
                    return self._get_sales_module_data(
                        connection, self._user_for_selected_store(user, query), match.group(1), query
                    )
                return self._post_sales_resource(
                    connection, user, resource, body
                )

            room_prefix = "/vue-element-admin/erp/room"
            if path.startswith(room_prefix):
                resource = path[len(room_prefix):] or "/"
                if self.command == "GET":
                    match = re.fullmatch(r"/modules/([^/]+)", resource)
                    if not match:
                        raise ApiError("客房资源不存在", 404, 40400)
                    return self._get_room_module_data(
                        connection, user, match.group(1), query
                    )
                return self._post_room_resource(
                    connection, user, resource, body
                )

            mall_prefix = "/vue-element-admin/erp/mall/modules"
            if path.startswith(mall_prefix):
                resource = path[len(mall_prefix):].strip("/")
                if self.command == "GET":
                    return self._get_mall_module_data(
                        connection, user, resource, query
                    )
                match = re.fullmatch(r"([^/]+)/(save|action)", resource)
                if not match:
                    raise ApiError("商城资源不存在", 404, 40400)
                return self._post_operational_module_record(
                    connection, user, "MALL", match.group(1), match.group(2), body
                )

            inventory_prefix = "/vue-element-admin/erp/inventory/modules"
            if path.startswith(inventory_prefix):
                resource = path[len(inventory_prefix):].strip("/")
                if self.command == "GET":
                    if resource == "reference-options":
                        return self._get_store_reference_options(
                            connection, user, "INVENTORY", query
                        )
                    return self._get_inventory_module_data(
                        connection, user, resource, query
                    )
                match = re.fullmatch(r"([^/]+)/(save|action)", resource)
                if not match:
                    raise ApiError("仓存资源不存在", 404, 40400)
                return self._post_operational_module_record(
                    connection,
                    user,
                    "INVENTORY",
                    match.group(1),
                    match.group(2),
                    body,
                )

            prefix = "/vue-element-admin/erp/mvp"
            if path.startswith(prefix):
                resource = path[len(prefix):] or "/"
                if self.command == "GET":
                    return self._get_resource(connection, user, resource, query)
                return self._post_resource(connection, user, resource, body)
            raise ApiError("接口不存在", 404, 40400)
        except ApiError as exc:
            if connection:
                connection.rollback()
            self._json(
                exc.status,
                {"code": exc.code, "message": exc.message, "data": {}},
            )
        except Exception as exc:  # pragma: no cover - defensive API boundary
            if connection:
                connection.rollback()
            self._json(
                500,
                {
                    "code": 50000,
                    "message": "服务器处理失败",
                    "data": {"errorType": type(exc).__name__},
                },
            )
            self.log_error("%s: %s", type(exc).__name__, exc)
        finally:
            if connection:
                connection.close()

    def _login(self, connection, body: dict):
        username = str(body.get("username", "")).strip()
        password = str(body.get("password", ""))
        account = execute_one(
            connection,
            """
            SELECT user_id, username, password_hash, status, locked_until
            FROM user_accounts
            WHERE tenant_id=1 AND username=%s
            """,
            (username,),
        )
        locked = bool(
            account
            and account.get("locked_until")
            and account["locked_until"] > datetime.now()
        )
        valid = bool(
            account
            and account["status"] == "ACTIVE"
            and not locked
            and check_password(password, account["password_hash"])
        )
        if not valid:
            if account:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE user_accounts
                        SET failed_login_count=failed_login_count+1,
                            locked_until=CASE
                              WHEN failed_login_count+1 >= %s
                              THEN DATE_ADD(NOW(), INTERVAL %s MINUTE)
                              ELSE locked_until
                            END
                        WHERE user_id=%s
                        """,
                        (
                            int(env("ERP_LOGIN_MAX_FAILURES", "5")),
                            int(env("ERP_LOGIN_LOCK_MINUTES", "15")),
                            account["user_id"],
                        ),
                    )
                connection.commit()
            raise ApiError("账号或密码错误", 401, 60204)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE user_accounts
                SET failed_login_count=0, locked_until=NULL, last_login_at=NOW()
                WHERE user_id=%s
                """,
                (account["user_id"],),
            )
        connection.commit()
        self._success(
            {"token": issue_token(account["user_id"], account["username"])}
        )

    def _authenticate(self, connection, query: dict) -> dict:
        token = self.headers.get("X-Token", "")
        if (
            not token
            and not is_production()
            and parse_bool(env("ERP_ALLOW_QUERY_TOKEN"), False)
        ):
            token = query.get("token", "")
        payload = verify_token(token)
        user = execute_one(
            connection,
            """
            SELECT user_id, tenant_id, staff_id, username, default_store_id,
                   department_id, status, must_change_password, source_system,
                   legacy_user_id
            FROM user_accounts
            WHERE user_id=%s AND username=%s
            """,
            (payload["uid"], payload["username"]),
        )
        if not user or user["status"] != "ACTIVE":
            raise ApiError("账号已停用", 401, 50008)
        role_rows = execute_all(
            connection,
            """
            SELECT r.role_id, r.code, r.name
            FROM user_roles ur
            JOIN roles r ON r.role_id=ur.role_id
            WHERE ur.user_id=%s AND r.tenant_id=%s AND r.status='ACTIVE'
              AND ur.effective_from<=NOW()
              AND (ur.effective_to IS NULL OR ur.effective_to>NOW())
            ORDER BY r.is_system DESC, r.data_scope DESC, r.role_id
            """,
            (user["user_id"], user["tenant_id"]),
        )
        user["roles"] = [row["code"] for row in role_rows]
        user["role_names"] = [row["name"] for row in role_rows]
        user["store_ids"] = [
            row["store_id"]
            for row in execute_all(
                connection,
                """
                SELECT s.store_id
                FROM user_stores us
                JOIN stores s ON s.store_id=us.store_id
                WHERE us.user_id=%s AND s.tenant_id=%s
                  AND s.status IN ('ACTIVE','NORMAL','正常','启用')
                ORDER BY s.store_id
                """,
                (user["user_id"], user["tenant_id"]),
            )
        ]
        user["permissions"] = [
            row["code"]
            for row in execute_all(
                connection,
                """
                SELECT DISTINCT p.code
                FROM user_roles ur
                JOIN roles r ON r.role_id=ur.role_id AND r.status='ACTIVE'
                JOIN role_permissions rp ON rp.role_id=ur.role_id
                  AND rp.effect='ALLOW'
                JOIN permissions p ON p.permission_id=rp.permission_id
                  AND p.status='ACTIVE'
                WHERE ur.user_id=%s AND r.tenant_id=%s
                  AND ur.effective_from<=NOW()
                  AND (ur.effective_to IS NULL OR ur.effective_to>NOW())
                ORDER BY p.code
                """,
                (user["user_id"], user["tenant_id"]),
            )
        ]
        field_rules = execute_all(
            connection,
            """
            SELECT fp.visible, fp.masked
            FROM user_roles ur
            JOIN field_permissions fp ON fp.role_id=ur.role_id
            JOIN roles r ON r.role_id=ur.role_id AND r.status='ACTIVE'
            WHERE ur.user_id=%s AND r.tenant_id=%s
              AND fp.resource_code='CUSTOMER.PROFILE'
              AND fp.field_code='mobile'
              AND ur.effective_from<=NOW()
              AND (ur.effective_to IS NULL OR ur.effective_to>NOW())
            """,
            (user["user_id"], user["tenant_id"]),
        )
        user["unmasked_customer_phone"] = any(
            bool(row["visible"]) and not bool(row["masked"])
            for row in field_rules
        )
        user["legacy_data_scopes"] = execute_all(
            connection,
            """
            SELECT scope.nav_id AS navId,
                   GROUP_CONCAT(
                     DISTINCT CASE WHEN scope.granted=1
                       THEN scope.department_id END
                     ORDER BY scope.department_id SEPARATOR ','
                   ) AS departmentIds
            FROM user_roles ur
            JOIN roles r ON r.role_id=ur.role_id AND r.status='ACTIVE'
            JOIN legacy_role_data_scope_grants scope
              ON scope.role_id=ur.role_id
            WHERE ur.user_id=%s AND r.tenant_id=%s
              AND ur.effective_from<=NOW()
              AND (ur.effective_to IS NULL OR ur.effective_to>NOW())
            GROUP BY scope.nav_id
            ORDER BY scope.nav_id
            """,
            (user["user_id"], user["tenant_id"]),
        )
        user["data_scopes"] = execute_all(
            connection,
            """
            SELECT rds.module_code AS moduleCode,
                   rds.scope_type AS scopeType,
                   MAX(rds.allow_cross_store) AS allowCrossStore,
                   MAX(rds.allow_cross_department) AS allowCrossDepartment
            FROM user_roles ur
            JOIN roles r ON r.role_id=ur.role_id
              AND r.tenant_id=%s AND r.status='ACTIVE'
            JOIN role_data_scopes rds ON rds.role_id=r.role_id
            WHERE ur.user_id=%s
              AND ur.effective_from<=NOW()
              AND (ur.effective_to IS NULL OR ur.effective_to>NOW())
            GROUP BY rds.module_code, rds.scope_type
            ORDER BY rds.module_code, rds.scope_type
            """,
            (user["tenant_id"], user["user_id"]),
        )
        return user

    def _user_info(self, connection, user: dict):
        display_name = user["username"]
        if user["staff_id"]:
            staff = execute_one(
                connection,
                "SELECT name FROM staff WHERE staff_id=%s AND tenant_id=%s",
                (user["staff_id"], user["tenant_id"]),
            )
            if staff and staff["name"]:
                display_name = staff["name"]
        roles = user["roles"] or ["authenticated"]
        self._success(
            {
                "roles": roles,
                "roleNames": user.get("role_names") or ["已认证用户"],
                "name": display_name,
                "avatar": "",
                "introduction": "奇德芬芳月子会所业务系统",
                "permissions": user["permissions"],
                "storeIds": user["store_ids"],
                "departmentId": user.get("department_id"),
                "mustChangePassword": bool(user.get("must_change_password")),
                "dataScopes": user.get("data_scopes", []),
                "legacyDataScopes": user.get("legacy_data_scopes", []),
            }
        )

    def _allowed_store(self, user: dict, store_id) -> int:
        try:
            return allowed_store_id(user, store_id)
        except RuntimeConfigError as exc:
            status = 403 if "无权" in str(exc) else 400
            raise ApiError(str(exc), status, 40300 if status == 403 else 40000) from exc

    def _user_for_selected_store(self, user: dict, query: dict) -> dict:
        """Narrow read scope to the current store; `all` is admin aggregate-only."""
        selected = str((query or {}).get("storeId") or "").strip()
        if not selected:
            return user
        if selected.lower() == "all":
            if "SYS_ADMIN" not in user.get("roles", []):
                raise ApiError("普通账号不能查询全部门店数据", 403, 40300)
            return user
        store_id = self._allowed_store(user, selected)
        scoped_user = dict(user)
        scoped_user["store_ids"] = [store_id]
        scoped_user["default_store_id"] = store_id
        return scoped_user

    def _require_selected_write_store(
        self, user: dict, body: dict, actual_store_id: int | None = None
    ) -> int | None:
        """Do not allow a write from the aggregate view or into another store."""
        selected = str((body or {}).get("selectedStoreId") or "").strip()
        if not selected:
            return None
        if selected.lower() == "all":
            raise ApiError("全部门店仅支持汇总查询，请先选择具体门店再保存", 400, 40000)
        selected_id = self._allowed_store(user, selected)
        if actual_store_id is not None and selected_id != int(actual_store_id):
            raise ApiError("保存数据的所属门店必须与当前选中门店一致", 400, 40000)
        return selected_id

    def _store_clause(self, user: dict, alias: str = "") -> tuple[str, list]:
        return store_scope_clause(user, alias)

    def _has_permission(self, user: dict, permission: str) -> bool:
        return permission in user["permissions"]

    def _require_permission(self, user: dict, permission: str):
        if not self._has_permission(user, permission):
            raise ApiError("当前角色没有此操作权限", 403, 40300)

    def _require_any_permission(self, user: dict, permissions):
        if "SYS_ADMIN" in user["roles"]:
            return
        if not any(self._has_permission(user, item) for item in permissions):
            raise ApiError("当前角色没有此操作权限", 403, 40300)

    def _require_recovery_access(
        self, user: dict, resource: str, action: str | None = None
    ):
        nav_id = RECOVERY_RESOURCE_NAV_IDS.get(resource)
        if not nav_id:
            raise ApiError("产康资源不存在", 404, 40400)
        if action is None:
            self._require_any_permission(
                user,
                (
                    f"LEGACY.WEB.N{nav_id}.B18",
                    "RECOVERY.VIEW",
                ),
            )
            return
        normalized = re.sub(r"\s+", "", str(action))
        button_map = RECOVERY_ACTION_BUTTON_IDS.get(resource, {})
        button_id = button_map.get(normalized)
        if button_id is None:
            raise ApiError("当前页面没有此操作", 403, 40300)
        standard_permission = {
            "添加": "RECOVERY.CREATE",
            "服务预约": "RECOVERY.CREATE",
            "编辑": "RECOVERY.UPDATE",
            "批量修改": "RECOVERY.UPDATE",
            "删除": "RECOVERY.UPDATE",
            "打印": "RECOVERY.PRINT",
            "设置": "RECOVERY.UPDATE",
            "读卡": "RECOVERY.VIEW",
            "确认完成": "RECOVERY.EXECUTE",
            "取消": "RECOVERY.EXECUTE",
            "预约确认": "RECOVERY.EXECUTE",
            "审核": "RECOVERY.EXECUTE",
            "反审核": "RECOVERY.EXECUTE",
        }.get(normalized)
        accepted_permissions = [f"LEGACY.WEB.N{nav_id}.B{button_id}"]
        if standard_permission:
            accepted_permissions.append(standard_permission)
        self._require_any_permission(
            user,
            tuple(accepted_permissions),
        )

    def _require_finance_access(
        self, user: dict, resource: str, action: str | None = None
    ):
        nav_id = FINANCE_RESOURCE_NAV_IDS.get(resource)
        if not nav_id:
            raise ApiError("财务资源不存在", 404, 40400)
        if action is None:
            self._require_any_permission(
                user,
                (f"LEGACY.WEB.N{nav_id}.B18", "FINANCE.VIEW"),
            )
            return
        normalized = re.sub(r"\s+", "", str(action))
        if resource == "receipt-create" and normalized == "保存":
            self._require_any_permission(
                user,
                ("FINANCE.CREATE", "LEGACY.WEB.N90.B1"),
            )
            return
        button_id = FINANCE_ACTION_BUTTON_IDS.get(resource, {}).get(normalized)
        if button_id is None:
            raise ApiError("当前财务页面没有此操作", 403, 40300)
        standard_permission = {
            "前往新增收款": "FINANCE.CREATE",
            "添加": "FINANCE.CREATE",
            "编辑": "FINANCE.UPDATE",
            "删除": "FINANCE.UPDATE",
            "导出": "FINANCE.PRINT",
            "打印": "FINANCE.PRINT",
            "提交": "FINANCE.UPDATE",
            "审核": "FINANCE.APPROVE",
            "批量审核": "FINANCE.APPROVE",
            "反审核": "FINANCE.APPROVE",
            "流程审批": "FINANCE.APPROVE",
            "确认匹配": "FINANCE.APPROVE",
            "取消匹配": "FINANCE.APPROVE",
            "登记退款打款": "FINANCE.APPROVE",
            "登记真实发票": "FINANCE.UPDATE",
            "撤回": "FINANCE.UPDATE",
        }.get(normalized)
        accepted_permissions = [f"LEGACY.WEB.N{nav_id}.B{button_id}"]
        if standard_permission:
            accepted_permissions.append(standard_permission)
        self._require_any_permission(
            user,
            tuple(accepted_permissions),
        )

    def _require_room_access(
        self, user: dict, resource: str, action: str | None = None
    ):
        nav_id = ROOM_RESOURCE_NAV_IDS.get(resource)
        if not nav_id:
            raise ApiError("客房资源不存在", 404, 40400)
        if action is None:
            self._require_any_permission(
                user,
                (f"LEGACY.WEB.N{nav_id}.B18", "ROOM.VIEW"),
            )
            return
        normalized = re.sub(r"\s+", "", str(action))
        button_id = ROOM_ACTION_BUTTON_IDS.get(resource, {}).get(normalized)
        if button_id is None:
            raise ApiError("当前客房页面没有此操作", 403, 40300)
        standard_permission = {
            "添加": "ROOM.CREATE",
            "订房": "ROOM.CREATE",
            "房型订房": "ROOM.CREATE",
            "跨店订房": "ROOM.CREATE",
            "编辑": "ROOM.UPDATE",
            "删除": "ROOM.UPDATE",
            "打印": "ROOM.PRINT",
            "导出": "ROOM.PRINT",
            "入住": "ROOM.EXECUTE",
            "续住": "ROOM.EXECUTE",
            "换房": "ROOM.EXECUTE",
            "跨店换房": "ROOM.EXECUTE",
            "退房": "ROOM.EXECUTE",
            "结账": "ROOM.EXECUTE",
            "取消": "ROOM.EXECUTE",
            "退订": "ROOM.EXECUTE",
            "退订并结账": "ROOM.EXECUTE",
            "确认完成": "ROOM.EXECUTE",
            "预约确认": "ROOM.EXECUTE",
            "确认签收": "ROOM.EXECUTE",
            "确定已返回": "ROOM.EXECUTE",
            "物品发放": "ROOM.EXECUTE",
            "维修/脏房": "ROOM.EXECUTE",
            "客房服务申请": "ROOM.EXECUTE",
            "服务预约": "ROOM.EXECUTE",
            "入住通知单": "ROOM.PRINT",
        }.get(normalized)
        accepted_permissions = [f"LEGACY.WEB.N{nav_id}.B{button_id}"]
        if standard_permission:
            accepted_permissions.append(standard_permission)
        self._require_any_permission(
            user,
            tuple(accepted_permissions),
        )

    def _require_sales_access(
        self, user: dict, resource: str, action: str | None = None
    ):
        nav_id = SALES_RESOURCE_NAV_IDS.get(resource)
        if not nav_id:
            raise ApiError("销售资源不存在", 404, 40400)
        if action is None:
            self._require_any_permission(
                user,
                (f"LEGACY.WEB.N{nav_id}.B18", "SALES.VIEW"),
            )
            return
        normalized = re.sub(r"\s+", "", str(action))
        button_id_or_code = SALES_ACTION_BUTTON_IDS.get(resource, {}).get(
            normalized
        )
        if button_id_or_code is None:
            raise ApiError("当前销售页面没有此操作", 403, 40300)
        permission_code = (
            button_id_or_code
            if isinstance(button_id_or_code, str)
            else f"LEGACY.WEB.N{nav_id}.B{button_id_or_code}"
        )
        standard_permission = {
            "添加": "SALES.CREATE",
            "编辑": "SALES.UPDATE",
            "删除": "SALES.UPDATE",
            "设置": "SALES.UPDATE",
            "复制": "SALES.UPDATE",
            "启用": "SALES.UPDATE",
            "停用": "SALES.UPDATE",
            "屏蔽/取消": "SALES.UPDATE",
            "推荐/取消": "SALES.UPDATE",
            "提交": "SALES.UPDATE",
            "取消": "SALES.UPDATE",
            "撤回": "SALES.UPDATE",
            "变更": "SALES.UPDATE",
            "导出": "SALES.EXPORT",
            "打印": "SALES.PRINT",
            "审核": "SALES.APPROVE",
            "反审核": "SALES.APPROVE",
            "流程审批": "SALES.APPROVE",
            "折扣率审核": "SALES.APPROVE",
            "远程签约": "SALES.UPDATE",
            "套餐升级": "SALES.UPDATE",
            "星支付": "SALES.UPDATE",
            "收款": "SALES.UPDATE",
            "出库": "SALES.UPDATE",
            "退货": "SALES.UPDATE",
            "取消退货": "SALES.UPDATE",
            "服务销售": "SALES.UPDATE",
            "物料销售": "SALES.UPDATE",
            "卡类销售": "SALES.UPDATE",
            "是否启用": "SALES.UPDATE",
            "介绍分配": "SALES.UPDATE",
            "分发": "SALES.UPDATE",
        }.get(normalized)
        accepted_permissions = [permission_code]
        if standard_permission and standard_permission != permission_code:
            accepted_permissions.append(standard_permission)
        self._require_any_permission(
            user,
            tuple(accepted_permissions),
        )

    def _finance_store_id(self, connection, user: dict, body: dict) -> int:
        raw = body.get("storeId")
        if raw in (None, "", "all"):
            raise ApiError("请先选择具体门店；全部门店仅支持汇总查询")
        return self._allowed_store(user, raw)

    def _finance_current_store_user(self, user: dict, query: dict) -> dict:
        raw = query.get("storeId")
        if raw in (None, ""):
            raise ApiError("请先选择具体门店查看业务明细；全部门店仅支持汇总查询")
        # Administrators may inspect the aggregate read view.  Write helpers
        # still reject ``all`` through ``_require_selected_write_store`` /
        # ``_finance_store_id``, so this broadens reads without broadening
        # mutation scope.
        return self._user_for_selected_store(user, query)

    def _finance_store_options(self, connection, user: dict) -> list:
        clause, params = self._store_clause(user, "s")
        return execute_all(
            connection,
            f"""
            SELECT s.store_id AS id, s.name
            FROM stores s
            WHERE s.tenant_id=%s
              AND s.status IN ('ACTIVE', '正常')
              AND {clause}
            ORDER BY s.sort_weight DESC, s.store_id
            """,
            [user["tenant_id"], *params],
        )

    def _require_asset_view(self, user: dict):
        self._require_any_permission(
            user,
            (
                "CUSTOMER.VIEW",
                "FINANCE.VIEW",
                "FINANCE.CREATE",
                "LEGACY.WEB.N90.B18",
            ),
        )

    def _get_asset_resource(
        self, connection, user: dict, resource: str, query: dict
    ):
        self._require_asset_view(user)
        scoped_user = self._finance_current_store_user(user, query)
        if resource == "/cards/options":
            return self._success(
                {"customers": self._asset_card_customer_options(connection, user)}
            )
        if resource == "/cards":
            rows = self._asset_card_rows(connection, scoped_user)
            return self._success({"list": rows, "total": len(rows)})
        clause, params = self._store_clause(scoped_user, "c")
        if resource == "/overview":
            row = execute_one(
                connection,
                f"""
                SELECT COUNT(*) AS accountCount,
                       COALESCE(SUM(mw.stored_card_balance),0)
                         AS accountBalance
                FROM customers c
                LEFT JOIN member_wallet mw
                  ON mw.customer_id=c.customer_id
                 AND mw.tenant_id=c.tenant_id
                WHERE c.tenant_id=%s
                  AND c.deleted_at IS NULL
                  AND {clause}
                """,
                [user["tenant_id"], *params],
            ) or {}
            return self._success(
                {
                    "accountCount": int(row.get("accountCount") or 0),
                    "accountBalance": row.get("accountBalance") or 0,
                }
            )
        if resource != "/accounts":
            raise ApiError("会员资产资源不存在", 404, 40400)
        rows = execute_all(
            connection,
            f"""
            SELECT c.customer_id AS id,
                   CONCAT('HY',LPAD(c.customer_id,10,'0')) AS account_no,
                   c.name AS customer_name,
                   c.phone AS mobile,
                   s.name AS store_name,
                   COALESCE(mw.stored_card_balance,0) AS balance,
                   0 AS frozen_amount,
                   COALESCE(mw.points,0) AS points,
                   '正常' AS status
            FROM customers c
            JOIN stores s ON s.store_id=c.store_id
            LEFT JOIN member_wallet mw
              ON mw.customer_id=c.customer_id
             AND mw.tenant_id=c.tenant_id
            WHERE c.tenant_id=%s
              AND c.deleted_at IS NULL
              AND {clause}
            ORDER BY c.customer_id DESC
            LIMIT 1000
            """,
            [user["tenant_id"], *params],
        )
        for row in rows:
            row["mobile"] = self._masked_phone(user, row.get("mobile"))
        return self._success({"list": rows, "total": len(rows)})

    def _post_asset_resource(
        self, connection, user: dict, resource: str, body: dict
    ):
        if resource == "/cards":
            return self._create_asset_count_card(connection, user, body)
        card_action = re.fullmatch(
            r"/cards/(\d+)/(activate|consume|deactivate)", resource
        )
        if card_action:
            return self._perform_asset_count_card_action(
                connection,
                user,
                int(card_action.group(1)),
                card_action.group(2),
                body,
            )
        match = re.fullmatch(
            r"/accounts/(\d+)/(top-up|deduct)", resource
        )
        if not match:
            raise ApiError("会员资产写操作不存在", 404, 40400)
        self._require_any_permission(
            user,
            ("FINANCE.CREATE", "LEGACY.WEB.N90.B1"),
        )
        customer_id = int(match.group(1))
        action = match.group(2)
        transaction_store_id = self._finance_store_id(connection, user, body)
        amount = self._finance_positive_amount(body, "amount")
        if amount > Decimal("1000000"):
            raise ApiError("单笔余额变动不能超过1000000元")
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT c.customer_id,c.store_id,
                       COALESCE(mw.stored_card_balance,0) AS balance
                FROM customers c
                LEFT JOIN member_wallet mw
                  ON mw.customer_id=c.customer_id
                 AND mw.tenant_id=c.tenant_id
                WHERE c.customer_id=%s AND c.tenant_id=%s
                  AND c.deleted_at IS NULL
                FOR UPDATE
                """,
                [customer_id, user["tenant_id"]],
            )
            account = cursor.fetchone()
            if not account:
                raise ApiError("会员账户不存在或无权访问", 404, 40400)
            before = Decimal(str(account.get("balance") or 0))
            delta = amount if action == "top-up" else -amount
            after = before + delta
            if after < 0:
                raise ApiError("会员余额不足，不能扣款")
            cursor.execute(
                """
                INSERT INTO member_wallet(
                  customer_id,tenant_id,stored_card_balance,points,version
                ) VALUES (%s,%s,%s,0,1)
                ON DUPLICATE KEY UPDATE
                  stored_card_balance=VALUES(stored_card_balance),
                  version=version+1
                """,
                (customer_id, user["tenant_id"], after),
            )
            cursor.execute(
                """
                INSERT INTO wallet_ledger(
                  tenant_id,store_id,customer_id,delta,balance_after,reason,
                  payment_method,ref_order,operator_user_id,created_at
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
                """,
                (
                    user["tenant_id"],
                    transaction_store_id,
                    customer_id,
                    delta,
                    after,
                    "ERP手工充值" if action == "top-up" else "ERP手工扣款",
                    "线下登记",
                    self._finance_number(
                        "CZ" if action == "top-up" else "KK"
                    ),
                    user["user_id"],
                ),
            )
        self._audit(
            connection,
            user,
            "member_wallet",
            customer_id,
            "top_up" if action == "top-up" else "deduct",
            transaction_store_id,
            str(before),
            str(after),
            {"amount": str(amount), "source": "ERP_MANUAL"},
        )
        connection.commit()
        return self._success(
            {
                "id": customer_id,
                "balance": after,
                "status": "正常",
            }
        )

    def _asset_card_customer_options(self, connection, user: dict) -> list:
        rows = execute_all(
            connection,
            f"""
            SELECT c.customer_id AS id,c.name,c.phone,c.store_id,
                   s.name AS storeName
            FROM customers c
            JOIN stores s ON s.store_id=c.store_id
            WHERE c.tenant_id=%s AND c.deleted_at IS NULL
            ORDER BY c.customer_id DESC
            LIMIT 1000
            """,
            [user["tenant_id"]],
        )
        for row in rows:
            row["phone"] = self._masked_phone(user, row.get("phone"))
        return rows

    def _asset_card_rows(self, connection, user: dict) -> list:
        clause, params = self._store_clause(user, "card")
        return execute_all(
            connection,
            f"""
            SELECT card.card_id AS id,ext.card_no AS cardNo,
                   card.name AS cardName,c.name AS customerName,
                   s.name AS store,card.total_count AS totalCount,
                   card.remain_count AS remainingCount,
                   card.valid_end AS validTo,
                   CASE
                     WHEN ext.lifecycle_status='正常'
                      AND DATE(card.valid_end)<CURDATE() THEN '已过期'
                     ELSE ext.lifecycle_status
                   END AS status,
                   receipt.receipt_no AS receiptNo,
                   card.created_at AS createdAt
            FROM count_cards card
            JOIN erp_count_card_extensions ext ON ext.card_id=card.card_id
            JOIN customers c ON c.customer_id=card.customer_id
            JOIN stores s ON s.store_id=card.store_id
            JOIN finance_receipts receipt ON receipt.receipt_id=ext.receipt_id
            WHERE card.tenant_id=%s AND card.deleted_at IS NULL
              AND {clause}
            ORDER BY card.card_id DESC
            LIMIT 1000
            """,
            [user["tenant_id"], *params],
        )

    def _require_asset_write(self, user: dict):
        self._require_any_permission(
            user, ("FINANCE.CREATE", "LEGACY.WEB.N90.B1")
        )

    def _create_asset_count_card(
        self, connection, user: dict, body: dict
    ):
        self._require_asset_write(user)
        try:
            customer_id = int(body.get("customerId") or 0)
            total_count = int(body.get("totalCount") or 0)
        except (TypeError, ValueError) as exc:
            raise ApiError("客户或卡次数格式不正确") from exc
        if not customer_id or not 1 <= total_count <= 10000:
            raise ApiError("卡次数须在1至10000之间")
        card_name = str(body.get("cardName") or "").strip()
        receipt_no = str(body.get("receiptNo") or "").strip()
        valid_to = str(body.get("validTo") or "")[:10]
        if not 2 <= len(card_name) <= 100:
            raise ApiError("卡名称须为2至100个字符")
        if not receipt_no or len(receipt_no) > 128:
            raise ApiError("必须填写有效的线下收款单号")
        try:
            valid_date = date.fromisoformat(valid_to)
        except ValueError as exc:
            raise ApiError("有效期格式不正确") from exc
        if valid_date < date.today():
            raise ApiError("有效期不能早于今天")
        transaction_store_id = self._finance_store_id(connection, user, body)
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT c.customer_id,c.store_id
                FROM customers c
                WHERE c.customer_id=%s AND c.tenant_id=%s
                  AND c.deleted_at IS NULL
                FOR UPDATE
                """,
                [customer_id, user["tenant_id"]],
            )
            customer = cursor.fetchone()
            if not customer:
                raise ApiError("客户不存在或无权访问", 404, 40400)
            cursor.execute(
                """
                SELECT receipt_id,amount FROM finance_receipts
                WHERE tenant_id=%s AND store_id=%s AND customer_id=%s
                  AND receipt_no=%s AND status IN ('审核通过','已审核')
                FOR UPDATE
                """,
                (
                    user["tenant_id"],
                    transaction_store_id,
                    customer_id,
                    receipt_no,
                ),
            )
            receipt = cursor.fetchone()
            if not receipt:
                raise ApiError("收款单不存在、未审核或不属于该客户门店")
            cursor.execute(
                """
                SELECT card_id FROM erp_count_card_extensions
                WHERE receipt_id=%s
                """,
                (receipt["receipt_id"],),
            )
            if cursor.fetchone():
                raise ApiError("该收款单已绑定套餐卡，不能重复发卡")
            card_no = self._finance_number("CK")
            cursor.execute(
                """
                INSERT INTO count_cards(
                  tenant_id,store_id,customer_id,name,total_count,used_count,
                  remain_count,valid_start,valid_end,total_amount,unit_price,
                  status,version,created_at
                ) VALUES (%s,%s,%s,%s,%s,0,%s,CURDATE(),%s,%s,%s,'待启用',0,NOW())
                """,
                (
                    user["tenant_id"],
                    transaction_store_id,
                    customer_id,
                    card_name,
                    total_count,
                    total_count,
                    valid_to,
                    receipt["amount"],
                    Decimal(str(receipt["amount"] or 0)) / total_count,
                ),
            )
            card_id = cursor.lastrowid
            cursor.execute(
                """
                INSERT INTO erp_count_card_extensions(
                  card_id,tenant_id,store_id,card_no,receipt_id,
                  lifecycle_status,created_by_user_id
                ) VALUES (%s,%s,%s,%s,%s,'待启用',%s)
                """,
                (
                    card_id,
                    user["tenant_id"],
                    transaction_store_id,
                    card_no,
                    receipt["receipt_id"],
                    user["user_id"],
                ),
            )
        self._audit(
            connection,
            user,
            "count_card",
            card_id,
            "create",
            transaction_store_id,
            None,
            "待启用",
            {"receiptNo": receipt_no, "totalCount": total_count},
        )
        connection.commit()
        return self._success(
            {"id": card_id, "cardNo": card_no, "status": "待启用"}
        )

    def _perform_asset_count_card_action(
        self,
        connection,
        user: dict,
        card_id: int,
        action: str,
        body: dict,
    ):
        self._require_asset_write(user)
        transaction_store_id = self._finance_store_id(connection, user, body)
        clause, params = self._store_clause(user, "card")
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT card.card_id,card.store_id,card.total_count,
                       card.used_count,card.remain_count,card.valid_end,
                       ext.lifecycle_status
                FROM count_cards card
                JOIN erp_count_card_extensions ext ON ext.card_id=card.card_id
                WHERE card.card_id=%s AND card.tenant_id=%s
                  AND card.deleted_at IS NULL AND {clause}
                FOR UPDATE
                """,
                [card_id, user["tenant_id"], *params],
            )
            card = cursor.fetchone()
            if not card:
                raise ApiError("套餐卡不存在或无权访问", 404, 40400)
            if int(card["store_id"]) != transaction_store_id:
                raise ApiError("套餐卡不属于当前选中门店", 404, 40400)
            before = card["lifecycle_status"]
            valid_to = date.fromisoformat(str(card["valid_end"])[:10])
            after = before
            if action == "activate":
                if before != "待启用":
                    raise ApiError("只有待启用的套餐卡可以启用")
                if valid_to < date.today():
                    raise ApiError("已过期套餐卡不能启用")
                after = "正常"
                cursor.execute(
                    """
                    UPDATE erp_count_card_extensions
                    SET lifecycle_status=%s,activated_by_user_id=%s,
                        activated_at=NOW()
                    WHERE card_id=%s
                    """,
                    (after, user["user_id"], card_id),
                )
                cursor.execute(
                    "UPDATE count_cards SET status='生效' WHERE card_id=%s",
                    (card_id,),
                )
            elif action == "consume":
                if before != "正常":
                    raise ApiError("只有正常状态的套餐卡可以核销")
                if valid_to < date.today():
                    raise ApiError("套餐卡已过期，不能核销")
                try:
                    count = int(body.get("count") or 1)
                except (TypeError, ValueError) as exc:
                    raise ApiError("核销次数格式不正确") from exc
                if not 1 <= count <= int(card["remain_count"] or 0):
                    raise ApiError("核销次数不能超过剩余次数")
                remaining = int(card["remain_count"]) - count
                after = "已耗尽" if remaining == 0 else "正常"
                cursor.execute(
                    """
                    UPDATE count_cards
                    SET used_count=used_count+%s,remain_count=%s,
                        status=%s,version=version+1
                    WHERE card_id=%s
                    """,
                    (
                        count,
                        remaining,
                        "已耗尽" if remaining == 0 else "生效",
                        card_id,
                    ),
                )
                cursor.execute(
                    """
                    UPDATE erp_count_card_extensions
                    SET lifecycle_status=%s WHERE card_id=%s
                    """,
                    (after, card_id),
                )
                cursor.execute(
                    """
                    INSERT INTO count_card_logs(
                      tenant_id,card_id,change_count,after_remain,amount,
                      biz_ref,operator_id,remark,created_at
                    ) VALUES (%s,%s,%s,%s,0,%s,%s,%s,NOW())
                    """,
                    (
                        user["tenant_id"],
                        card_id,
                        -count,
                        remaining,
                        self._finance_number("HX"),
                        user["user_id"],
                        "ERP套餐卡核销",
                    ),
                )
            else:
                if before not in {"待启用", "正常"}:
                    raise ApiError("当前状态不能停用套餐卡")
                after = "已停用"
                cursor.execute(
                    """
                    UPDATE erp_count_card_extensions
                    SET lifecycle_status=%s,deactivated_by_user_id=%s,
                        deactivated_at=NOW()
                    WHERE card_id=%s
                    """,
                    (after, user["user_id"], card_id),
                )
                cursor.execute(
                    "UPDATE count_cards SET status='已停用' WHERE card_id=%s",
                    (card_id,),
                )
        self._audit(
            connection,
            user,
            "count_card",
            card_id,
            action,
            int(card["store_id"]),
            before,
            after,
            {},
        )
        connection.commit()
        return self._success({"id": card_id, "status": after})

    def _require_contract_archive_view(self, user: dict):
        self._require_any_permission(user, ("LEGACY.WEB.N85.B18",))

    def _require_contract_archive_write(self, user: dict):
        self._require_any_permission(user, ("LEGACY.WEB.N85.B10",))

    def _get_contract_archive_resource(
        self, connection, user: dict, resource: str, query: dict
    ):
        if resource != "/":
            raise ApiError("合同归档资源不存在", 404, 40400)
        self._require_contract_archive_view(user)
        scoped_user = self._finance_current_store_user(user, query)
        clause, params = self._store_clause(scoped_user, "contract")
        rows = execute_all(
            connection,
            f"""
            SELECT contract.contract_id AS id,contract.contract_no AS contractNo,
                   customer.name AS customerName,s.name AS store,
                   contract.status AS contractStatus,
                   COALESCE(archive.archive_status,'待线下归档')
                     AS archiveStatus,
                   CASE
                     WHEN archive.archive_id IS NULL THEN '未接入（不伪造）'
                     ELSE '未接入；仅登记线下归档'
                   END AS electronicSignStatus,
                   archive.archive_no AS archiveNo,
                   archive.signing_mode AS signingMode,
                   archive.signed_at AS signedAt,
                   archive.archive_reference AS archiveReference,
                   archive.original_location AS originalLocation,
                   archive.void_reason AS voidReason,
                   archive.archived_at AS archivedAt
            FROM contracts contract
            JOIN customers customer ON customer.customer_id=contract.customer_id
            JOIN stores s ON s.store_id=contract.store_id
            LEFT JOIN sales_contract_sign_archives archive
              ON archive.contract_id=contract.contract_id
            WHERE contract.tenant_id=%s AND contract.deleted_at IS NULL
              AND {clause}
            ORDER BY contract.contract_id DESC
            LIMIT 1000
            """,
            [user["tenant_id"], *params],
        )
        return self._success({"list": rows, "total": len(rows)})

    def _post_contract_archive_resource(
        self, connection, user: dict, resource: str, body: dict
    ):
        match = re.fullmatch(r"/(\d+)/(archive|revoke)", resource)
        if not match:
            raise ApiError("合同归档写操作不存在", 404, 40400)
        self._require_contract_archive_write(user)
        selected_store_id = self._finance_store_id(connection, user, body)
        contract_id = int(match.group(1))
        action = match.group(2)
        scoped_user = dict(user)
        scoped_user["store_ids"] = [selected_store_id]
        clause, params = self._store_clause(scoped_user, "contract")
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT contract.contract_id,contract.store_id,contract.status,
                       archive.archive_id,archive.archive_status
                FROM contracts contract
                LEFT JOIN sales_contract_sign_archives archive
                  ON archive.contract_id=contract.contract_id
                WHERE contract.contract_id=%s AND contract.tenant_id=%s
                  AND contract.deleted_at IS NULL AND {clause}
                FOR UPDATE
                """,
                [contract_id, user["tenant_id"], *params],
            )
            contract = cursor.fetchone()
            if not contract:
                raise ApiError("合同不存在或无权访问", 404, 40400)
            before = contract.get("archive_status") or "待线下归档"
            if action == "archive":
                if contract["status"] not in {"已审核", "审核通过"}:
                    raise ApiError("只有已审核合同可以登记签署归档")
                archive_reference = str(
                    body.get("archiveReference") or ""
                ).strip()
                original_location = str(
                    body.get("originalLocation") or ""
                ).strip()
                signed_at = str(body.get("signedAt") or "")[:10]
                if not 2 <= len(archive_reference) <= 128:
                    raise ApiError("请填写2至128个字符的线下归档编号")
                if not 2 <= len(original_location) <= 255:
                    raise ApiError("请填写2至255个字符的纸质原件存放位置")
                try:
                    signed_date = date.fromisoformat(signed_at)
                except ValueError as exc:
                    raise ApiError("签署日期格式不正确") from exc
                if signed_date > date.today():
                    raise ApiError("签署日期不能晚于今天")
                if contract["archive_id"] and before != "已作废":
                    raise ApiError("该合同已登记线下归档，不能重复登记")
                after = "线下已归档"
                if contract["archive_id"]:
                    archive_id = int(contract["archive_id"])
                    cursor.execute(
                        """
                        UPDATE sales_contract_sign_archives
                        SET archive_status=%s,signing_mode='线下纸质签署',
                            signed_at=%s,archive_reference=%s,
                            original_location=%s,void_reason=NULL,
                            archived_by_user_id=%s,archived_at=NOW(),
                            voided_by_user_id=NULL,voided_at=NULL
                        WHERE archive_id=%s
                        """,
                        (
                            after,
                            signed_at,
                            archive_reference,
                            original_location,
                            user["user_id"],
                            archive_id,
                        ),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO sales_contract_sign_archives(
                          tenant_id,store_id,contract_id,archive_no,
                          archive_status,signing_mode,signed_at,
                          archive_reference,original_location,
                          archived_by_user_id
                        ) VALUES (%s,%s,%s,%s,%s,'线下纸质签署',%s,%s,%s,%s)
                        """,
                        (
                            user["tenant_id"],
                            contract["store_id"],
                            contract_id,
                            self._sales_number("DZA"),
                            after,
                            signed_at,
                            archive_reference,
                            original_location,
                            user["user_id"],
                        ),
                    )
                    archive_id = cursor.lastrowid
            else:
                if before != "线下已归档":
                    raise ApiError("只有线下已归档合同可以作废归档")
                reason = str(body.get("reason") or "").strip()
                if not 2 <= len(reason) <= 500:
                    raise ApiError("作废原因须为2至500个字符")
                after = "已作废"
                archive_id = int(contract["archive_id"])
                cursor.execute(
                    """
                    UPDATE sales_contract_sign_archives
                    SET archive_status=%s,void_reason=%s,
                        voided_by_user_id=%s,voided_at=NOW()
                    WHERE archive_id=%s
                    """,
                    (after, reason, user["user_id"], archive_id),
                )
        self._audit(
            connection,
            user,
            "contract_sign_archive",
            archive_id,
            action,
            int(contract["store_id"]),
            before,
            after,
            {"contractId": contract_id},
        )
        connection.commit()
        return self._success(
            {"id": archive_id, "contractId": contract_id, "status": after}
        )

    def _get_finance_resource(
        self, connection, user: dict, resource: str, query: dict
    ):
        if resource == "/options":
            self._require_any_permission(
                user, ("FINANCE.VIEW", "FINANCE.CREATE")
            )
            return self._success(
                {"stores": self._finance_store_options(connection, user)}
            )
        picker = re.fullmatch(
            r"/pickers/(employee|customer|contract)", resource
        )
        if picker:
            return self._get_finance_picker(
                connection, user, picker.group(1), query
            )
        module = re.fullmatch(r"/modules/([^/]+)", resource)
        if not module:
            raise ApiError("财务资源不存在", 404, 40400)
        key = module.group(1)
        self._require_finance_access(user, key)
        scoped_user = self._finance_current_store_user(user, query)
        rows = self._finance_module_rows(connection, scoped_user, key, query)
        return self._success(
            {
                "list": rows,
                "total": len(rows),
                "stores": self._finance_store_options(connection, user),
            }
        )

    def _get_finance_picker(
        self, connection, user: dict, picker_type: str, query: dict
    ):
        self._require_any_permission(
            user,
            (
                "FINANCE.CREATE",
                "FINANCE.VIEW",
                "LEGACY.WEB.N521.B18",
            ),
        )
        scoped_user = self._finance_current_store_user(user, query)
        if picker_type == "contract":
            clause, params = self._store_clause(scoped_user, "ct")
            rows = execute_all(
                connection,
                f"""
                SELECT ct.contract_id AS id,ct.customer_id AS customerId,
                       ct.contract_no AS contractNo,c.name AS customerName,
                       c.phone AS mobile,s.name AS store,ct.amount,
                       COALESCE(SUM(
                         CASE WHEN fr.status<>'已删除'
                           THEN fr.amount ELSE 0 END
                       ),0) AS paid,
                       GREATEST(
                         ct.amount-COALESCE(SUM(
                           CASE WHEN fr.status<>'已删除'
                             THEN fr.amount ELSE 0 END
                         ),0),
                         0
                       ) AS balance,
                       ct.status
                FROM contracts ct
                JOIN customers c ON c.customer_id=ct.customer_id
                JOIN stores s ON s.store_id=ct.store_id
                LEFT JOIN finance_receipts fr
                  ON fr.contract_id=ct.contract_id
                WHERE ct.tenant_id=%s AND ct.deleted_at IS NULL
                  AND ct.status IN ('已审核','审核通过')
                  AND {clause}
                GROUP BY ct.contract_id
                HAVING balance>0
                ORDER BY ct.contract_id DESC
                LIMIT 1000
                """,
                [user["tenant_id"], *params],
            )
            for row in rows:
                row["mobile"] = self._masked_phone(
                    user, row.get("mobile")
                )
            return self._success({"list": rows, "total": len(rows)})

        if picker_type == "customer":
            rows = execute_all(
                connection,
                f"""
                SELECT c.customer_id AS id,
                       COALESCE(ca.phone, c.customer_no) AS username,
                       c.name, c.phone AS mobile, c.status,
                       owner.name AS salesperson, s.name AS store
                FROM customers c
                LEFT JOIN customer_accounts ca
                  ON ca.customer_id=c.customer_id
                LEFT JOIN staff owner ON owner.staff_id=c.sales_staff_id
                LEFT JOIN stores s ON s.store_id=c.store_id
                WHERE c.tenant_id=%s AND c.deleted_at IS NULL
                ORDER BY c.customer_id DESC
                LIMIT 1000
                """,
                [user["tenant_id"]],
            )
            for row in rows:
                row["mobile"] = self._masked_phone(user, row.get("mobile"))
            return self._success({"list": rows, "total": len(rows)})

        if scoped_user["store_ids"]:
            placeholders = ",".join(["%s"] * len(scoped_user["store_ids"]))
            scope_sql = (
                f"COALESCE(st.store_id, ua.default_store_id) "
                f"IN ({placeholders})"
            )
            scope_params = list(scoped_user["store_ids"])
        else:
            scope_sql, scope_params = "1=0", []
        rows = execute_all(
            connection,
            f"""
            SELECT ua.user_id AS id, ua.username, st.name,
                   COALESCE(d.name, st.department) AS department,
                   store.name AS store,
                   GROUP_CONCAT(DISTINCT r.name ORDER BY r.role_id SEPARATOR '、')
                     AS role,
                   ua.status
            FROM user_accounts ua
            LEFT JOIN staff st ON st.staff_id=ua.staff_id
            LEFT JOIN departments d ON d.department_id=st.department_id
            LEFT JOIN stores store
              ON store.store_id=COALESCE(st.store_id, ua.default_store_id)
            LEFT JOIN user_roles ur ON ur.user_id=ua.user_id
            LEFT JOIN roles r ON r.role_id=ur.role_id AND r.status='ACTIVE'
            WHERE ua.tenant_id=%s AND ua.status='ACTIVE' AND {scope_sql}
            GROUP BY ua.user_id
            ORDER BY ua.username
            LIMIT 1000
            """,
            [user["tenant_id"], *scope_params],
        )
        return self._success({"list": rows, "total": len(rows)})

    def _finance_module_rows(
        self, connection, user: dict, resource: str, query: dict
    ) -> list:
        if resource == "receipt-create":
            return []
        if resource == "receipts":
            return self._finance_receipt_rows(connection, user, query)
        if resource in {"refund-applications", "refund-audits"}:
            return self._finance_refund_rows(connection, user)
        if resource == "debt-audits":
            return self._finance_debt_rows(connection, user)
        if resource == "exchange-audits":
            return self._finance_exchange_rows(connection, user)
        if resource == "invoices":
            return self._finance_invoice_rows(connection, user)
        if resource == "reconciliations":
            return self._finance_reconciliation_rows(connection, user)
        if resource == "material-budgets":
            return self._finance_budget_rows(connection, user)
        if resource in {"my-expenses", "expense-audits"}:
            return self._finance_expense_rows(
                connection, user, own_only=resource == "my-expenses"
            )
        if resource == "payments":
            return self._finance_payment_rows(connection, user)
        raise ApiError("财务资源不存在", 404, 40400)

    def _finance_receipt_rows(
        self, connection, user: dict, query: dict
    ) -> list:
        clause, params = self._store_clause(user, "fr")
        tab = str(query.get("tab") or "receipts")
        tab_sql = {
            "prepayments": "AND COALESCE(ext.receipt_kind,'收款单')='预收款'",
            "debts": "AND fr.payment_method='欠款消费'",
            "preauthorizations": "AND ext.income_type='预授权'",
        }.get(
            tab,
            (
                "AND COALESCE(ext.receipt_kind,'收款单')<>'预收款' "
                "AND fr.payment_method<>'欠款消费' "
                "AND COALESCE(ext.income_type,'')<>'预授权'"
            ),
        )
        rows = execute_all(
            connection,
            f"""
            SELECT fr.receipt_id AS id, fr.customer_id AS customerId,
                   fr.receiver_user_id AS cashierId,
                   fr.receipt_no AS receiptNo,
                   ext.invoice_status AS invoiceStatus,
                   c.name AS customerName, c.phone AS mobile,
                   COALESCE(d.name, receiver_staff.department) AS department,
                   receiver.username AS cashier,
                   COALESCE(ext.document_date, DATE(fr.received_at))
                     AS documentDate,
                   fr.receipt_type AS receiptType,
                   fr.payment_method AS paymentMethod,
                   fr.amount, 0 AS taxAmount,
                   ext.source_no AS sourceNo,
                   creator.username AS creator,
                   fr.status AS auditStatus,
                   approver.username AS auditor,
                   ext.audit_remark AS auditRemark,
                   fr.approved_at AS auditedAt, s.name AS store,
                   fr.created_at AS createdAt,
                   COALESCE(ext.fee_amount,0) AS fee,
                   COALESCE(ext.received_amount,fr.amount) AS receivedAmount,
                   ext.bank_name AS bank, ext.bank_account AS bankAccount,
                   fr.received_at AS receivedAt,
                   CASE WHEN COALESCE(ext.settled,0)=1
                     THEN '是' ELSE '否' END AS settled,
                   CASE WHEN COALESCE(ext.settled,0)=1
                     THEN '结算核销' ELSE '未核销' END AS settlement,
                   CASE WHEN COALESCE(ext.settled,0)=1
                     THEN '已核销' ELSE '未核销' END AS writeOffStatus,
                   COALESCE(ext.writeoff_balance,fr.amount)
                     AS writeOffBalance,
                   fr.amount AS documentAmount,
                   fr.amount AS recoverableAmount,
                   ext.customer_status AS customerStatus,
                   fr.contract_id AS contractId,
                   ext.source_no AS saleNo,
                   fr.remark
            FROM finance_receipts fr
            JOIN customers c ON c.customer_id=fr.customer_id
            JOIN stores s ON s.store_id=fr.store_id
            LEFT JOIN finance_receipt_extensions ext
              ON ext.receipt_id=fr.receipt_id
            LEFT JOIN user_accounts receiver
              ON receiver.user_id=fr.receiver_user_id
            LEFT JOIN staff receiver_staff
              ON receiver_staff.staff_id=receiver.staff_id
            LEFT JOIN departments d
              ON d.department_id=receiver_staff.department_id
            LEFT JOIN user_accounts creator
              ON creator.user_id=ext.created_by_user_id
            LEFT JOIN user_accounts approver
              ON approver.user_id=fr.approved_by_user_id
            WHERE fr.tenant_id=%s AND fr.status<>'已删除'
              AND {clause} {tab_sql}
            ORDER BY fr.receipt_id DESC
            LIMIT 1000
            """,
            [user["tenant_id"], *params],
        )
        for row in rows:
            row["mobile"] = self._masked_phone(user, row.get("mobile"))
        return rows

    def _finance_refund_rows(self, connection, user: dict) -> list:
        clause, params = self._store_clause(user, "ro")
        rows = execute_all(
            connection,
            f"""
            SELECT ro.refund_id AS id, ro.customer_id AS customerId,
                   ext.cashier_user_id AS cashierId,
                   ro.refund_no AS refundNo,
                   ro.approval_id AS auditNo, c.name AS customerName,
                   c.phone AS mobile, ro.refund_type AS refundType,
                   ext.refund_channel AS refundChannel,
                   ro.apply_amount AS refundAmount,
                   creator.username AS creator,
                   COALESCE(d.name, creator_staff.department) AS department,
                   ro.actual_amount AS actualRefund, ro.status,
                   LEFT(ro.created_at,10) AS documentDate,
                   COALESCE(ext.audit_status,ro.status) AS auditStatus,
                   ro.pay_method AS paymentMethod, ro.pay_date AS paidAt,
                   payer.username AS payer, s.name AS store,
                   ro.reason, cashier.username AS cashier,
                   ext.bank_name AS bank, ext.bank_account AS bankAccount,
                   salesperson.name AS salesperson, ro.biz_ref AS saleNo,
                   ext.payment_remark AS paymentRemark,
                   ext.bank_branch AS bankBranch, ro.payee,
                   COALESCE(ext.audit_status,ro.status)
                     AS allocationStatus
            FROM refund_orders ro
            LEFT JOIN customers c ON c.customer_id=ro.customer_id
            LEFT JOIN stores s ON s.store_id=ro.store_id
            LEFT JOIN finance_refund_extensions ext
              ON ext.refund_id=ro.refund_id
            LEFT JOIN user_accounts creator
              ON creator.user_id=ext.created_by_user_id
            LEFT JOIN staff creator_staff
              ON creator_staff.staff_id=creator.staff_id
            LEFT JOIN departments d
              ON d.department_id=creator_staff.department_id
            LEFT JOIN user_accounts payer
              ON payer.user_id=ext.paid_by_user_id
            LEFT JOIN user_accounts cashier
              ON cashier.user_id=ext.cashier_user_id
            LEFT JOIN staff salesperson
              ON salesperson.staff_id=c.sales_staff_id
            WHERE ro.tenant_id=%s AND ro.deleted_at IS NULL
              AND {clause}
            ORDER BY ro.refund_id DESC
            LIMIT 1000
            """,
            [user["tenant_id"], *params],
        )
        for row in rows:
            row["mobile"] = self._masked_phone(user, row.get("mobile"))
        return rows

    def _finance_debt_rows(self, connection, user: dict) -> list:
        clause, params = self._store_clause(user, "da")
        rows = execute_all(
            connection,
            f"""
            SELECT da.debt_audit_id AS id, r.room_no AS room,
                   c.name AS customerName, ct.contract_no AS contractNo,
                   ct.package_name AS packageName, ct.amount AS dealAmount,
                   ct.paid AS receivedAmount, rb.status AS roomStatus,
                   creator.username AS creator, rb.check_in AS checkInAt,
                   da.audit_status AS auditStatus,
                   approver.username AS auditor, da.reason, s.name AS store
            FROM finance_debt_audits da
            JOIN customers c ON c.customer_id=da.customer_id
            JOIN stores s ON s.store_id=da.store_id
            LEFT JOIN contracts ct ON ct.contract_id=da.contract_id
            LEFT JOIN room_bookings rb ON rb.booking_id=da.booking_id
            LEFT JOIN rooms r ON r.room_id=da.room_id
            LEFT JOIN user_accounts creator
              ON creator.user_id=da.created_by_user_id
            LEFT JOIN user_accounts approver
              ON approver.user_id=da.approved_by_user_id
            WHERE da.tenant_id=%s AND {clause}
            ORDER BY da.debt_audit_id DESC
            LIMIT 1000
            """,
            [user["tenant_id"], *params],
        )
        return rows

    def _finance_exchange_rows(self, connection, user: dict) -> list:
        clause, params = self._store_clause(user, "ea")
        rows = execute_all(
            connection,
            f"""
            SELECT ea.exchange_id AS id, ea.exchange_no AS exchangeNo,
                   ea.source_order_no AS saleNo,
                   ea.return_order_no AS returnNo, c.name AS customerName,
                   c.phone AS mobile, ea.exchange_type AS exchangeType,
                   applicant.username AS applicant,
                   ea.applied_at AS appliedAt, approver.username AS auditor,
                   ea.approved_at AS auditedAt,
                   ea.audit_status AS auditStatus,
                   ea.outbound_status AS outboundStatus,
                   ea.warehouse_name AS warehouse,
                   ea.difference_amount AS differenceAmount
            FROM finance_exchange_audits ea
            LEFT JOIN customers c ON c.customer_id=ea.customer_id
            LEFT JOIN user_accounts applicant
              ON applicant.user_id=ea.applicant_user_id
            LEFT JOIN user_accounts approver
              ON approver.user_id=ea.approved_by_user_id
            WHERE ea.tenant_id=%s AND ea.deleted_at IS NULL
              AND {clause}
            ORDER BY ea.exchange_id DESC
            LIMIT 1000
            """,
            [user["tenant_id"], *params],
        )
        for row in rows:
            row["mobile"] = self._masked_phone(user, row.get("mobile"))
        return rows

    def _finance_invoice_rows(self, connection, user: dict) -> list:
        clause, params = self._store_clause(user, "i")
        return execute_all(
            connection,
            f"""
            SELECT i.invoice_id AS id, i.amount AS invoiceAmount,
                   i.amount, CONCAT(ROUND(COALESCE(i.tax_rate,0)*100,2),'%%')
                     AS taxRate,
                   i.tax_amount AS taxAmount,
                   i.source_ref AS documentNo,
                   i.source_type AS documentType, i.status,
                   i.created_at AS createdAt, i.invoice_type AS invoiceType,
                   i.invoice_no AS invoiceNo, i.issue_date AS invoicedAt,
                   i.title AS invoiceTitle, c.name AS customerName,
                   '' AS invoiceContent, i.tax_no AS taxpayerNo,
                   i.reg_address AS registeredAddress,
                   i.reg_phone AS registeredPhone,
                   i.bank, i.bank_account AS bankAccount
            FROM invoices i
            LEFT JOIN customers c ON c.customer_id=i.customer_id
            WHERE i.tenant_id=%s AND i.deleted_at IS NULL AND {clause}
            ORDER BY i.invoice_id DESC
            LIMIT 1000
            """,
            [user["tenant_id"], *params],
        )

    def _finance_reconciliation_rows(
        self, connection, user: dict
    ) -> list:
        clause, params = self._store_clause(user, "rec")
        return execute_all(
            connection,
            f"""
            SELECT rec.reconciliation_id AS id,
                   fr.receipt_no AS receiptNo,
                   rec.external_channel AS externalChannel,
                   rec.external_reference AS externalReference,
                   rec.system_amount AS systemAmount,
                   rec.external_amount AS externalAmount,
                   rec.difference_amount AS differenceAmount,
                   rec.transaction_date AS transactionDate,
                   rec.status, s.name AS store,
                   creator.username AS creator,
                   matcher.username AS matchedBy,
                   rec.matched_at AS matchedAt,
                   rec.remark, rec.created_at AS createdAt
            FROM finance_reconciliations rec
            JOIN finance_receipts fr ON fr.receipt_id=rec.receipt_id
            JOIN stores s ON s.store_id=rec.store_id
            JOIN user_accounts creator
              ON creator.user_id=rec.created_by_user_id
            LEFT JOIN user_accounts matcher
              ON matcher.user_id=rec.matched_by_user_id
            WHERE rec.tenant_id=%s AND rec.deleted_at IS NULL
              AND {clause}
            ORDER BY rec.transaction_date DESC,
                     rec.reconciliation_id DESC
            LIMIT 1000
            """,
            [user["tenant_id"], *params],
        )

    def _finance_budget_rows(self, connection, user: dict) -> list:
        clause, params = self._store_clause(user, "b")
        return execute_all(
            connection,
            f"""
            SELECT b.budget_id AS id, b.budget_no AS budgetNo,
                   b.budget_date AS budgetDate,
                   b.department_name AS department,
                   b.total_quantity AS totalQuantity,
                   b.total_amount AS totalAmount, b.status,
                   creator.username AS creator, b.created_at AS createdAt,
                   b.purchase_plan_no AS purchasePlanNo, b.remark
            FROM finance_material_budgets b
            LEFT JOIN user_accounts creator
              ON creator.user_id=b.created_by_user_id
            WHERE b.tenant_id=%s AND b.deleted_at IS NULL AND {clause}
            ORDER BY b.budget_id DESC
            LIMIT 1000
            """,
            [user["tenant_id"], *params],
        )

    def _finance_expense_rows(
        self, connection, user: dict, own_only: bool
    ) -> list:
        clause, params = self._store_clause(user, "eo")
        own_sql = "AND ext.applicant_user_id=%s" if own_only else ""
        if own_only:
            params.append(user["user_id"])
        return execute_all(
            connection,
            f"""
            SELECT eo.expense_id AS id, eo.expense_no AS expenseNo,
                   applicant.username AS applicant,
                   COALESCE(ext.department_name,d.name) AS department,
                   s.name AS store, ext.expense_name AS expenseName,
                   eo.expense_type AS feeType, eo.reason,
                   COALESCE(ext.payout_type,eo.pay_method) AS payoutType,
                   eo.apply_amount AS applyAmount,
                   eo.apply_date AS appliedAt, eo.audit_date AS approvedAt,
                   eo.pay_date AS paidAt, eo.status,
                   CASE WHEN eo.invoice_no IS NULL OR eo.invoice_no=''
                     THEN '无发票' ELSE '有发票' END AS invoice,
                   ext.invoice_type AS invoiceType,
                   ext.attachment_names AS attachment
            FROM expense_orders eo
            JOIN finance_expense_extensions ext
              ON ext.expense_id=eo.expense_id
            LEFT JOIN user_accounts applicant
              ON applicant.user_id=ext.applicant_user_id
            LEFT JOIN departments d ON d.department_id=ext.department_id
            LEFT JOIN stores s ON s.store_id=eo.store_id
            WHERE eo.tenant_id=%s AND eo.deleted_at IS NULL
              AND {clause} {own_sql}
            ORDER BY eo.expense_id DESC
            LIMIT 1000
            """,
            [user["tenant_id"], *params],
        )

    def _finance_payment_rows(self, connection, user: dict) -> list:
        clause, params = self._store_clause(user, "p")
        return execute_all(
            connection,
            f"""
            SELECT p.payment_id AS id, p.payment_no AS paymentNo,
                   p.project_name AS projectName, p.payee, p.amount,
                   p.commission_standard AS commissionStandard,
                   creator.username AS creator,
                   p.payment_status AS paymentStatus,
                   p.audit_status AS auditStatus, p.created_at AS createdAt
            FROM finance_payments p
            LEFT JOIN user_accounts creator
              ON creator.user_id=p.created_by_user_id
            WHERE p.tenant_id=%s AND p.deleted_at IS NULL AND {clause}
            ORDER BY p.payment_id DESC
            LIMIT 1000
            """,
            [user["tenant_id"], *params],
        )

    def _post_finance_resource(
        self, connection, user: dict, resource: str, body: dict
    ):
        match = re.fullmatch(r"/modules/([^/]+)/(save|action)", resource)
        if not match:
            raise ApiError("财务资源不存在", 404, 40400)
        module, operation = match.groups()
        if module not in FINANCE_RESOURCE_NAV_IDS:
            raise ApiError("财务资源不存在", 404, 40400)
        if operation == "save":
            return self._save_finance_record(connection, user, module, body)
        return self._perform_finance_action(connection, user, module, body)

    def _finance_number(self, prefix: str) -> str:
        return (
            f"{prefix}-{datetime.now():%Y%m%d%H%M%S}-"
            f"{secrets.randbelow(10000):04d}"
        )

    def _finance_positive_amount(self, body: dict, key: str) -> Decimal:
        try:
            amount = Decimal(str(body.get(key) or "0"))
        except Exception as exc:
            raise ApiError("金额格式不正确") from exc
        if amount <= 0:
            raise ApiError("金额必须大于0")
        return amount

    def _save_finance_record(
        self, connection, user: dict, resource: str, body: dict
    ):
        record_id = int(body.get("id") or 0)
        if resource in {"receipt-create", "receipts"}:
            return self._save_finance_receipt(
                connection, user, body, record_id
            )
        if resource == "refund-applications":
            return self._save_finance_refund(
                connection, user, body, record_id
            )
        if resource == "material-budgets":
            return self._save_finance_budget(
                connection, user, body, record_id
            )
        if resource == "my-expenses":
            return self._save_finance_expense(
                connection, user, body, record_id
            )
        if resource == "reconciliations" and not record_id:
            return self._save_finance_reconciliation(
                connection, user, body
            )
        raise ApiError("当前财务页面不支持新增或编辑", 403, 40300)

    def _save_finance_reconciliation(
        self, connection, user: dict, body: dict
    ):
        self._require_finance_access(user, "reconciliations", "添加")
        store_id = self._finance_store_id(connection, user, body)
        receipt_no = str(body.get("receiptNo") or "").strip()
        channel = str(body.get("externalChannel") or "").strip()
        external_reference = str(
            body.get("externalReference") or ""
        ).strip()
        transaction_date = str(body.get("transactionDate") or "")[:10]
        if not receipt_no:
            raise ApiError("系统收款单号不能为空")
        if not channel or not external_reference:
            raise ApiError("外部渠道和外部流水号不能为空")
        try:
            date.fromisoformat(transaction_date)
        except ValueError:
            raise ApiError("外部交易日期格式不正确")
        external_amount = self._finance_positive_amount(
            body, "externalAmount"
        )
        receipt = execute_one(
            connection,
            """
            SELECT fr.receipt_id,
                   COALESCE(ext.received_amount,fr.amount) AS system_amount
            FROM finance_receipts fr
            LEFT JOIN finance_receipt_extensions ext
              ON ext.receipt_id=fr.receipt_id
            WHERE fr.tenant_id=%s AND fr.store_id=%s
              AND fr.receipt_no=%s
              AND fr.status IN ('审核通过','已审核')
            """,
            (user["tenant_id"], store_id, receipt_no),
        )
        if not receipt:
            raise ApiError("仅能对账当前门店已审核的有效收款单")
        duplicate = execute_one(
            connection,
            """
            SELECT reconciliation_id
            FROM finance_reconciliations
            WHERE tenant_id=%s AND store_id=%s
              AND external_channel=%s AND external_reference=%s
              AND deleted_at IS NULL
            """,
            (
                user["tenant_id"],
                store_id,
                channel,
                external_reference,
            ),
        )
        if duplicate:
            raise ApiError("该门店的外部流水已登记，不能重复对账")
        system_amount = Decimal(str(receipt["system_amount"] or 0))
        difference = external_amount - system_amount
        status = "待匹配" if difference == 0 else "差异待处理"
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO finance_reconciliations(
                  tenant_id,store_id,receipt_id,external_channel,
                  external_reference,external_amount,system_amount,
                  difference_amount,transaction_date,status,remark,
                  created_by_user_id
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    user["tenant_id"],
                    store_id,
                    receipt["receipt_id"],
                    channel,
                    external_reference,
                    external_amount,
                    system_amount,
                    difference,
                    transaction_date,
                    status,
                    body.get("remark") or None,
                    user["user_id"],
                ),
            )
            reconciliation_id = cursor.lastrowid
        self._audit(
            connection,
            user,
            "FINANCE_RECONCILIATION",
            reconciliation_id,
            "CREATE",
            store_id,
            None,
            status,
            {
                "receiptNo": receipt_no,
                "externalReference": external_reference,
                "differenceAmount": str(difference),
            },
        )
        connection.commit()
        return self._success(
            {
                "id": reconciliation_id,
                "status": status,
                "differenceAmount": difference,
            }
        )

    def _save_finance_receipt(
        self, connection, user: dict, body: dict, receipt_id: int
    ):
        if receipt_id:
            self._require_finance_access(user, "receipts", "编辑")
            receipt = execute_one(
                connection,
                f"""
                SELECT fr.receipt_id, fr.store_id, fr.status
                FROM finance_receipts fr
                WHERE fr.receipt_id=%s AND fr.tenant_id=%s
                  AND {self._store_clause(user, 'fr')[0]}
                """,
                [
                    receipt_id,
                    user["tenant_id"],
                    *self._store_clause(user, "fr")[1],
                ],
            )
            if not receipt:
                raise ApiError("收款单不存在或无权访问", 404, 40400)
            if receipt["status"] != "待审核":
                raise ApiError("只有待审核收款单可以编辑")
        else:
            self._require_finance_access(user, "receipt-create", "保存")

        store_id = self._finance_store_id(connection, user, body)
        customer_id = int(body.get("customerId") or 0)
        customer = execute_one(
            connection,
            """
            SELECT customer_id FROM customers
            WHERE tenant_id=%s AND customer_id=%s AND store_id=%s
              AND deleted_at IS NULL
            """,
            (user["tenant_id"], customer_id, store_id),
        )
        if not customer:
            raise ApiError("请选择当前门店的有效客户")
        cashier_id = int(body.get("cashierId") or user["user_id"])
        cashier = execute_one(
            connection,
            """
            SELECT user_id FROM user_accounts
            WHERE tenant_id=%s AND user_id=%s AND status='ACTIVE'
            """,
            (user["tenant_id"], cashier_id),
        )
        if not cashier:
            raise ApiError("请选择有效收款人")
        amount = self._finance_positive_amount(body, "amount")
        receipt_type = str(body.get("receiptType") or "").strip()
        payment_method = str(body.get("paymentMethod") or "").strip()
        if not receipt_type or not payment_method:
            raise ApiError("款项类别和结算方式不能为空")
        document_date = str(
            body.get("documentDate") or date.today().isoformat()
        )[:10]
        try:
            parsed_document_date = date.fromisoformat(document_date)
        except ValueError:
            raise ApiError("单据日期格式不正确")
        if parsed_document_date > date.today():
            raise ApiError("收款单据日期不能晚于今天")
        if parsed_document_date < date.today() and not str(
            body.get("remark") or ""
        ).strip():
            raise ApiError("历史补录收款必须填写备注说明")
        if str(body.get("invoiceStatus") or "未开票") == "已开票":
            raise ApiError(
                "收款单不能直接标记已开票，请审核通过后登记真实发票号码"
            )
        received_at = f"{document_date} {datetime.now():%H:%M:%S}"
        contract_id = int(body.get("contractId") or 0) or None
        if "合同" in receipt_type and not contract_id:
            raise ApiError("合同类收款必须选择已审核合同")
        if contract_id:
            contract = execute_one(
                connection,
                """
                SELECT ct.contract_id,ct.amount,
                       COALESCE(SUM(
                         CASE WHEN fr.status<>'已删除'
                           AND fr.receipt_id<>%s
                           THEN fr.amount ELSE 0 END
                       ),0) AS recorded_amount
                FROM contracts ct
                LEFT JOIN finance_receipts fr
                  ON fr.contract_id=ct.contract_id
                WHERE ct.tenant_id=%s AND ct.contract_id=%s
                  AND ct.customer_id=%s AND ct.store_id=%s
                  AND ct.deleted_at IS NULL
                  AND ct.status IN ('已审核','审核通过')
                GROUP BY ct.contract_id
                """,
                (
                    receipt_id,
                    user["tenant_id"],
                    contract_id,
                    customer_id,
                    store_id,
                ),
            )
            if not contract:
                raise ApiError("已审核合同不存在或不属于所选客户")
            remaining = Decimal(str(contract["amount"] or 0)) - Decimal(
                str(contract["recorded_amount"] or 0)
            )
            if amount > remaining:
                raise ApiError("收款金额不能超过合同剩余可收金额")
        with connection.cursor() as cursor:
            if receipt_id:
                cursor.execute(
                    """
                    UPDATE finance_receipts
                    SET store_id=%s, customer_id=%s, contract_id=%s,
                        receipt_type=%s, amount=%s, payment_method=%s,
                        received_at=%s, receiver_user_id=%s, remark=%s,
                        version=version+1
                    WHERE receipt_id=%s
                    """,
                    (
                        store_id,
                        customer_id,
                        contract_id,
                        receipt_type,
                        amount,
                        payment_method,
                        received_at,
                        cashier_id,
                        body.get("remark") or None,
                        receipt_id,
                    ),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO finance_receipts(
                      tenant_id,store_id,receipt_no,customer_id,contract_id,
                      receipt_type,amount,payment_method,received_at,
                      receiver_user_id,status,remark
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'待审核',%s)
                    """,
                    (
                        user["tenant_id"],
                        store_id,
                        self._finance_number("SK"),
                        customer_id,
                        contract_id,
                        receipt_type,
                        amount,
                        payment_method,
                        received_at,
                        cashier_id,
                        body.get("remark") or None,
                    ),
                )
                receipt_id = cursor.lastrowid
            cursor.execute(
                """
                INSERT INTO finance_receipt_extensions(
                  receipt_id,receipt_kind,gift_amount,income_type,bank_name,
                  bank_account,invoice_status,coupon_code,document_date,
                  attachment_names,received_amount,writeoff_balance,source_no,
                  customer_status,created_by_user_id
                ) VALUES (
                  %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
                )
                ON DUPLICATE KEY UPDATE
                  receipt_kind=VALUES(receipt_kind),
                  gift_amount=VALUES(gift_amount),
                  income_type=VALUES(income_type),
                  bank_name=VALUES(bank_name),
                  bank_account=VALUES(bank_account),
                  invoice_status=VALUES(invoice_status),
                  coupon_code=VALUES(coupon_code),
                  document_date=VALUES(document_date),
                  attachment_names=VALUES(attachment_names),
                  received_amount=VALUES(received_amount),
                  source_no=VALUES(source_no),
                  customer_status=VALUES(customer_status)
                """,
                (
                    receipt_id,
                    body.get("receiptKind") or "收款单",
                    Decimal(str(body.get("giftAmount") or 0)),
                    body.get("incomeType") or None,
                    body.get("bank") or None,
                    body.get("bankAccount") or None,
                    body.get("invoiceStatus") or "未开票",
                    body.get("coupon") or None,
                    document_date,
                    body.get("attachment") or None,
                    amount,
                    amount,
                    body.get("sourceNo") or None,
                    body.get("customerStatus") or None,
                    user["user_id"],
                ),
            )
        self._audit(
            connection,
            user,
            "FINANCE_RECEIPT",
            receipt_id,
            "UPDATE" if body.get("id") else "CREATE",
            store_id,
            None,
            "待审核",
            {"amount": str(amount), "receiptType": receipt_type},
        )
        connection.commit()
        return self._success({"id": receipt_id})

    def _save_finance_refund(
        self, connection, user: dict, body: dict, refund_id: int
    ):
        self._require_finance_access(
            user,
            "refund-applications",
            "编辑" if refund_id else "添加",
        )
        store_id = self._finance_store_id(connection, user, body)
        amount = self._finance_positive_amount(body, "refundAmount")
        customer_id = int(body.get("customerId") or 0)
        if not customer_id:
            raise ApiError("退款申请必须选择当前门店客户")
        customer = execute_one(
            connection,
            """
            SELECT customer_id FROM customers
            WHERE tenant_id=%s AND customer_id=%s AND store_id=%s
              AND deleted_at IS NULL
            """,
            (user["tenant_id"], customer_id, store_id),
        )
        if not customer:
            raise ApiError("退款客户不存在或不属于当前门店")
        with connection.cursor() as cursor:
            if refund_id:
                row = execute_one(
                    connection,
                    f"""
                    SELECT ro.refund_id, ro.status FROM refund_orders ro
                    WHERE ro.refund_id=%s AND ro.tenant_id=%s
                      AND ro.deleted_at IS NULL
                      AND {self._store_clause(user, 'ro')[0]}
                    """,
                    [
                        refund_id,
                        user["tenant_id"],
                        *self._store_clause(user, "ro")[1],
                    ],
                )
                if not row:
                    raise ApiError("退款单不存在或无权访问", 404, 40400)
                if row["status"] not in {"待提交", "被驳回"}:
                    raise ApiError("只有待提交或被驳回的退款单可以编辑")
                cursor.execute(
                    """
                    UPDATE refund_orders
                    SET store_id=%s,refund_type=%s,biz_ref=%s,customer_id=%s,
                        apply_amount=%s,reason=%s,version=version+1
                    WHERE refund_id=%s
                    """,
                    (
                        store_id,
                        body.get("refundType") or None,
                        body.get("saleNo") or None,
                        customer_id,
                        amount,
                        body.get("reason") or None,
                        refund_id,
                    ),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO refund_orders(
                      tenant_id,store_id,refund_no,refund_type,biz_ref,
                      customer_id,apply_amount,status,reason,created_at
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,'待提交',%s,NOW())
                    """,
                    (
                        user["tenant_id"],
                        store_id,
                        self._finance_number("TK"),
                        body.get("refundType") or None,
                        body.get("saleNo") or None,
                        customer_id,
                        amount,
                        body.get("reason") or None,
                    ),
                )
                refund_id = cursor.lastrowid
            cursor.execute(
                """
                INSERT INTO finance_refund_extensions(
                  refund_id,refund_channel,audit_status,cashier_user_id,
                  created_by_user_id
                ) VALUES (%s,%s,'待提交',%s,%s)
                ON DUPLICATE KEY UPDATE
                  refund_channel=VALUES(refund_channel),
                  cashier_user_id=VALUES(cashier_user_id)
                """,
                (
                    refund_id,
                    body.get("refundChannel") or None,
                    int(body.get("cashierId") or user["user_id"]),
                    user["user_id"],
                ),
            )
        self._audit(
            connection,
            user,
            "FINANCE_REFUND",
            refund_id,
            "UPDATE" if body.get("id") else "CREATE",
            store_id,
            None,
            "待提交",
        )
        connection.commit()
        return self._success({"id": refund_id})

    def _save_finance_budget(
        self, connection, user: dict, body: dict, budget_id: int
    ):
        self._require_finance_access(
            user,
            "material-budgets",
            "编辑" if budget_id else "添加",
        )
        store_id = self._finance_store_id(connection, user, body)
        department = str(body.get("department") or "").strip()
        if not department:
            raise ApiError("预算部门不能为空")
        budget_date = str(
            body.get("budgetDate") or date.today().isoformat()
        )[:10]
        with connection.cursor() as cursor:
            if budget_id:
                scope_clause, scope_params = self._store_clause(user, "b")
                cursor.execute(
                    f"""
                    SELECT b.budget_id
                    FROM finance_material_budgets b
                    WHERE b.budget_id=%s AND b.tenant_id=%s
                      AND b.deleted_at IS NULL AND {scope_clause}
                    FOR UPDATE
                    """,
                    (
                        budget_id,
                        user["tenant_id"],
                        *scope_params,
                    ),
                )
                if cursor.fetchone() is None:
                    raise ApiError(
                        "预算单不存在或不在当前门店权限范围内",
                        404,
                        40400,
                    )
                cursor.execute(
                    """
                    UPDATE finance_material_budgets
                    SET store_id=%s,budget_date=%s,department_name=%s,
                        total_quantity=%s,total_amount=%s,
                        purchase_plan_no=%s,remark=%s,version=version+1
                    WHERE budget_id=%s AND tenant_id=%s AND deleted_at IS NULL
                    """,
                    (
                        store_id,
                        budget_date,
                        department,
                        Decimal(str(body.get("totalQuantity") or 0)),
                        Decimal(str(body.get("totalAmount") or 0)),
                        body.get("purchasePlanNo") or None,
                        body.get("remark") or None,
                        budget_id,
                        user["tenant_id"],
                    ),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO finance_material_budgets(
                      tenant_id,store_id,budget_no,budget_date,
                      department_name,total_quantity,total_amount,
                      status,purchase_plan_no,remark,created_by_user_id
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,'待提交',%s,%s,%s)
                    """,
                    (
                        user["tenant_id"],
                        store_id,
                        body.get("budgetNo") or self._finance_number("YS"),
                        budget_date,
                        department,
                        Decimal(str(body.get("totalQuantity") or 0)),
                        Decimal(str(body.get("totalAmount") or 0)),
                        body.get("purchasePlanNo") or None,
                        body.get("remark") or None,
                        user["user_id"],
                    ),
                )
                budget_id = cursor.lastrowid
        self._audit(
            connection,
            user,
            "FINANCE_BUDGET",
            budget_id,
            "UPDATE" if body.get("id") else "CREATE",
            store_id,
            None,
            "待提交",
        )
        connection.commit()
        return self._success({"id": budget_id})

    def _save_finance_expense(
        self, connection, user: dict, body: dict, expense_id: int
    ):
        self._require_finance_access(
            user,
            "my-expenses",
            "编辑" if expense_id else "添加",
        )
        store_id = self._finance_store_id(connection, user, body)
        amount = self._finance_positive_amount(body, "applyAmount")
        expense_name = str(body.get("expenseName") or "").strip()
        fee_type = str(body.get("feeType") or "").strip()
        if not expense_name or not fee_type:
            raise ApiError("费用名称和费用类型不能为空")
        with connection.cursor() as cursor:
            if expense_id:
                row = execute_one(
                    connection,
                    f"""
                    SELECT eo.expense_id, eo.status
                    FROM expense_orders eo
                    JOIN finance_expense_extensions ext
                      ON ext.expense_id=eo.expense_id
                    WHERE eo.expense_id=%s AND eo.tenant_id=%s
                      AND eo.deleted_at IS NULL
                      AND ext.applicant_user_id=%s
                      AND {self._store_clause(user, 'eo')[0]}
                    """,
                    [
                        expense_id,
                        user["tenant_id"],
                        user["user_id"],
                        *self._store_clause(user, "eo")[1],
                    ],
                )
                if not row:
                    raise ApiError("费用单不存在或不可编辑", 404, 40400)
                if row["status"] not in {"待提交", "驳回"}:
                    raise ApiError("只有待提交或驳回的费用单可以编辑")
                cursor.execute(
                    """
                    UPDATE expense_orders
                    SET store_id=%s,expense_type=%s,apply_amount=%s,
                        reason=%s,version=version+1
                    WHERE expense_id=%s
                    """,
                    (
                        store_id,
                        fee_type,
                        amount,
                        body.get("reason") or None,
                        expense_id,
                    ),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO expense_orders(
                      tenant_id,store_id,expense_no,expense_type,apply_amount,
                      status,reason,apply_date,created_at
                    ) VALUES (%s,%s,%s,%s,%s,'待提交',%s,NOW(),NOW())
                    """,
                    (
                        user["tenant_id"],
                        store_id,
                        self._finance_number("FY"),
                        fee_type,
                        amount,
                        body.get("reason") or None,
                    ),
                )
                expense_id = cursor.lastrowid
            cursor.execute(
                """
                INSERT INTO finance_expense_extensions(
                  expense_id,expense_name,applicant_user_id,department_id,
                  department_name,payout_type,attachment_names
                ) VALUES (%s,%s,%s,%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE
                  expense_name=VALUES(expense_name),
                  department_id=VALUES(department_id),
                  department_name=VALUES(department_name),
                  payout_type=VALUES(payout_type),
                  attachment_names=VALUES(attachment_names)
                """,
                (
                    expense_id,
                    expense_name,
                    user["user_id"],
                    user.get("department_id"),
                    body.get("department") or None,
                    body.get("payoutType") or None,
                    body.get("attachment") or None,
                ),
            )
        self._audit(
            connection,
            user,
            "FINANCE_EXPENSE",
            expense_id,
            "UPDATE" if body.get("id") else "CREATE",
            store_id,
            None,
            "待提交",
            {"amount": str(amount)},
        )
        connection.commit()
        return self._success({"id": expense_id})

    def _perform_finance_action(
        self, connection, user: dict, resource: str, body: dict
    ):
        action = re.sub(r"\s+", "", str(body.get("action") or ""))
        self._require_finance_access(user, resource, action)
        ids = body.get("ids") if isinstance(body.get("ids"), list) else []
        if not ids:
            record_id = int(body.get("id") or 0)
            ids = [record_id] if record_id else []
        if not ids:
            raise ApiError("请选择财务记录")
        normalized_ids = [int(item) for item in ids]
        results = []
        for record_id in normalized_ids:
            results.append(
                self._perform_finance_record_action(
                    connection, user, resource, action, record_id, body
                )
            )
        connection.commit()
        return self._success(
            {"ids": normalized_ids, "results": results, "action": action}
        )

    def _perform_finance_record_action(
        self,
        connection,
        user: dict,
        resource: str,
        action: str,
        record_id: int,
        body: dict,
    ) -> dict:
        if resource == "receipts":
            return self._finance_receipt_action(
                connection, user, action, record_id, body
            )
        if resource in {"refund-applications", "refund-audits"}:
            return self._finance_refund_action(
                connection, user, action, record_id, body
            )
        if resource == "debt-audits":
            return self._finance_debt_action(
                connection, user, action, record_id, body
            )
        if resource == "exchange-audits":
            return self._finance_exchange_action(
                connection, user, action, record_id, body
            )
        if resource == "invoices":
            return self._finance_invoice_action(
                connection, user, action, record_id
            )
        if resource == "reconciliations":
            return self._finance_reconciliation_action(
                connection, user, action, record_id
            )
        if resource == "material-budgets":
            return self._finance_budget_action(
                connection, user, action, record_id, body
            )
        if resource in {"my-expenses", "expense-audits"}:
            return self._finance_expense_action(
                connection, user, resource, action, record_id, body
            )
        raise ApiError("当前财务页面没有可执行操作", 403, 40300)

    def _finance_reconciliation_action(
        self,
        connection,
        user: dict,
        action: str,
        reconciliation_id: int,
    ) -> dict:
        clause, params = self._store_clause(user, "rec")
        row = execute_one(
            connection,
            f"""
            SELECT rec.reconciliation_id,rec.store_id,rec.status,
                   rec.difference_amount
            FROM finance_reconciliations rec
            WHERE rec.reconciliation_id=%s AND rec.tenant_id=%s
              AND rec.deleted_at IS NULL AND {clause}
            """,
            [reconciliation_id, user["tenant_id"], *params],
        )
        if not row:
            raise ApiError("对账记录不存在或无权访问", 404, 40400)
        before = row["status"]
        after = before
        with connection.cursor() as cursor:
            if action == "确认匹配":
                if Decimal(str(row["difference_amount"] or 0)) != 0:
                    raise ApiError("仍有金额差异，不能确认匹配")
                if before == "已匹配":
                    raise ApiError("该外部流水已完成匹配")
                after = "已匹配"
                cursor.execute(
                    """
                    UPDATE finance_reconciliations
                    SET status='已匹配',matched_by_user_id=%s,
                        matched_at=NOW()
                    WHERE reconciliation_id=%s
                    """,
                    (user["user_id"], reconciliation_id),
                )
            elif action == "取消匹配":
                if before != "已匹配":
                    raise ApiError("只有已匹配记录可以取消匹配")
                after = "待匹配"
                cursor.execute(
                    """
                    UPDATE finance_reconciliations
                    SET status='待匹配',matched_by_user_id=NULL,
                        matched_at=NULL
                    WHERE reconciliation_id=%s
                    """,
                    (reconciliation_id,),
                )
            elif action == "删除":
                if before == "已匹配":
                    raise ApiError("已匹配记录须先取消匹配再删除")
                after = "已删除"
                cursor.execute(
                    """
                    UPDATE finance_reconciliations
                    SET deleted_at=NOW() WHERE reconciliation_id=%s
                    """,
                    (reconciliation_id,),
                )
            else:
                raise ApiError("当前对账操作尚未实现", 403, 40300)
        self._audit(
            connection,
            user,
            "FINANCE_RECONCILIATION",
            reconciliation_id,
            action,
            row["store_id"],
            before,
            after,
        )
        return {"id": reconciliation_id, "status": after}

    def _finance_receipt_action(
        self,
        connection,
        user: dict,
        action: str,
        receipt_id: int,
        body: dict,
    ) -> dict:
        clause, params = self._store_clause(user, "fr")
        receipt = execute_one(
            connection,
            f"""
            SELECT fr.receipt_id,fr.store_id,fr.customer_id,fr.amount,
                   fr.receipt_no,fr.status,fr.contract_id,
                   COALESCE(ext.writeoff_balance,fr.amount) AS balance,
                   COALESCE(ext.invoice_status,'未开票') AS invoice_status,
                   COALESCE(ext.settled,0) AS settled
            FROM finance_receipts fr
            LEFT JOIN finance_receipt_extensions ext
              ON ext.receipt_id=fr.receipt_id
            WHERE fr.receipt_id=%s AND fr.tenant_id=%s
              AND fr.status<>'已删除' AND {clause}
            """,
            [receipt_id, user["tenant_id"], *params],
        )
        if not receipt:
            raise ApiError("收款单不存在或无权访问", 404, 40400)
        before = receipt["status"]
        after = before
        with connection.cursor() as cursor:
            if action in {"星支付", "扫码支付"}:
                raise ApiError("尚未配置真实支付通道，禁止生成虚假支付结果")
            if action == "删除":
                if before != "待审核":
                    raise ApiError("只有待审核收款单可以删除")
                after = "已删除"
                cursor.execute(
                    "UPDATE finance_receipts SET status=%s WHERE receipt_id=%s",
                    (after, receipt_id),
                )
            elif action in {"审核", "批量审核"}:
                if before != "待审核":
                    raise ApiError("只有待审核收款单可以审核")
                result = str(body.get("auditResult") or "审核通过")
                after = "审核通过" if "通过" in result else "审核未通过"
                actual = Decimal(str(body.get("actualAmount") or receipt["amount"]))
                cursor.execute(
                    """
                    UPDATE finance_receipts
                    SET status=%s,approved_at=NOW(),approved_by_user_id=%s,
                        version=version+1
                    WHERE receipt_id=%s
                    """,
                    (after, user["user_id"], receipt_id),
                )
                cursor.execute(
                    """
                    UPDATE finance_receipt_extensions
                    SET received_amount=%s,fee_amount=%s,audit_remark=%s
                    WHERE receipt_id=%s
                    """,
                    (
                        actual,
                        Decimal(str(body.get("fee") or 0)),
                        body.get("auditRemark") or None,
                        receipt_id,
                    ),
                )
            elif action == "反审核":
                if before not in {"审核通过", "审核未通过"}:
                    raise ApiError("当前收款状态不能反审核")
                if receipt["invoice_status"] == "已开票" or receipt["settled"]:
                    raise ApiError("已开票或已核销收款不能反审核")
                after = "待审核"
                cursor.execute(
                    """
                    UPDATE finance_receipts
                    SET status='待审核',approved_at=NULL,
                        approved_by_user_id=NULL,version=version+1
                    WHERE receipt_id=%s
                    """,
                    (receipt_id,),
                )
            elif action == "手续费":
                if before != "审核通过":
                    raise ApiError("只有审核通过的收款单可以登记手续费")
                fee = Decimal(str(body.get("fee") or 0))
                if fee < 0:
                    raise ApiError("手续费不能小于0")
                cursor.execute(
                    """
                    UPDATE finance_receipt_extensions
                    SET fee_amount=%s,audit_remark=COALESCE(%s,audit_remark)
                    WHERE receipt_id=%s
                    """,
                    (fee, body.get("remark") or None, receipt_id),
                )
            elif action == "核销":
                if before != "审核通过":
                    raise ApiError("只有审核通过的收款单可以核销")
                amount = self._finance_positive_amount(body, "writeOffAmount")
                balance = Decimal(str(receipt["balance"] or 0))
                if amount > balance:
                    raise ApiError("核销金额不能超过可核销余额")
                writeoff_store = self._finance_store_id(connection, user, body)
                cursor.execute(
                    """
                    INSERT INTO finance_writeoffs(
                      tenant_id,store_id,receipt_id,writeoff_type,
                      payment_method,amount,remark,created_by_user_id
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        user["tenant_id"],
                        writeoff_store,
                        receipt_id,
                        body.get("writeOffType") or "合同收款",
                        body.get("paymentMethod") or "现金",
                        amount,
                        body.get("remark") or None,
                        user["user_id"],
                    ),
                )
                new_balance = balance - amount
                cursor.execute(
                    """
                    UPDATE finance_receipt_extensions
                    SET writeoff_balance=%s,settled=%s
                    WHERE receipt_id=%s
                    """,
                    (new_balance, int(new_balance == 0), receipt_id),
                )
            elif action == "开具发票":
                if before != "审核通过":
                    raise ApiError("只有审核通过的收款单可以开具发票")
                invoice_no = str(body.get("invoiceNo") or "").strip()
                if not invoice_no:
                    raise ApiError("请填写税控或电子发票平台的真实发票号码")
                invoice_date = str(
                    body.get("invoiceDate") or date.today().isoformat()
                )[:10]
                try:
                    date.fromisoformat(invoice_date)
                except ValueError:
                    raise ApiError("开票日期格式不正确")
                duplicate_invoice = execute_one(
                    connection,
                    """
                    SELECT invoice_id FROM invoices
                    WHERE tenant_id=%s AND deleted_at IS NULL
                      AND status<>'已删除'
                      AND (
                        (source_type='收款单' AND source_ref=%s)
                        OR invoice_no=%s
                      )
                    LIMIT 1
                    """,
                    (
                        user["tenant_id"],
                        receipt["receipt_no"],
                        invoice_no,
                    ),
                )
                if duplicate_invoice:
                    raise ApiError("该收款单已开具发票，不能重复开票")
                tax_rate_text = str(body.get("taxRate") or "0").replace("%", "")
                tax_rate = Decimal(tax_rate_text or "0") / Decimal("100")
                if tax_rate < 0 or tax_rate > 1:
                    raise ApiError("税率必须在0%到100%之间")
                if (
                    str(body.get("invoiceTitleType") or "个人") == "单位"
                    and not str(body.get("taxpayerNo") or "").strip()
                ):
                    raise ApiError("单位发票必须填写纳税人识别码")
                tax_amount = (
                    Decimal(str(receipt["amount"])) * tax_rate
                ).quantize(Decimal("0.01"))
                cursor.execute(
                    """
                    INSERT INTO invoices(
                      tenant_id,store_id,invoice_no,invoice_type,title,tax_no,
                      reg_address,reg_phone,bank,bank_account,amount,tax_rate,
                      tax_amount,source_type,source_ref,customer_id,status,
                      issue_date,created_at
                    ) VALUES (
                      %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                      '收款单',%s,%s,'已开票',%s,NOW()
                    )
                    """,
                    (
                        user["tenant_id"],
                        receipt["store_id"],
                        invoice_no,
                        body.get("invoiceType") or "增值税普通发票",
                        body.get("companyName")
                        or body.get("customerName")
                        or "个人",
                        body.get("taxpayerNo") or None,
                        body.get("registeredAddress") or None,
                        body.get("registeredPhone") or None,
                        body.get("bank") or None,
                        body.get("bankAccount") or None,
                        receipt["amount"],
                        tax_rate,
                        tax_amount,
                        receipt["receipt_no"],
                        receipt["customer_id"],
                        invoice_date,
                    ),
                )
                cursor.execute(
                    """
                    UPDATE finance_receipt_extensions
                    SET invoice_status='已开票' WHERE receipt_id=%s
                    """,
                    (receipt_id,),
                )
            else:
                raise ApiError("当前收款操作尚未实现", 403, 40300)
            if receipt.get("contract_id") and action in {
                "审核",
                "批量审核",
                "反审核",
                "删除",
            }:
                cursor.execute(
                    """
                    UPDATE contracts ct
                    SET ct.paid=(
                      SELECT COALESCE(
                        SUM(COALESCE(ext.received_amount,fr.amount)),0
                      )
                      FROM finance_receipts fr
                      LEFT JOIN finance_receipt_extensions ext
                        ON ext.receipt_id=fr.receipt_id
                      WHERE fr.contract_id=ct.contract_id
                        AND fr.status IN ('审核通过','已审核')
                    ),
                    ct.version=ct.version+1
                    WHERE ct.contract_id=%s AND ct.tenant_id=%s
                    """,
                    (receipt["contract_id"], user["tenant_id"]),
                )
        self._audit(
            connection,
            user,
            "FINANCE_RECEIPT",
            receipt_id,
            action,
            receipt["store_id"],
            before,
            after,
        )
        return {"id": receipt_id, "status": after}

    def _finance_refund_action(
        self,
        connection,
        user: dict,
        action: str,
        refund_id: int,
        body: dict,
    ) -> dict:
        clause, params = self._store_clause(user, "ro")
        refund = execute_one(
            connection,
            f"""
            SELECT ro.refund_id,ro.store_id,ro.status,ro.apply_amount
            FROM refund_orders ro
            WHERE ro.refund_id=%s AND ro.tenant_id=%s
              AND ro.deleted_at IS NULL AND {clause}
            """,
            [refund_id, user["tenant_id"], *params],
        )
        if not refund:
            raise ApiError("退款单不存在或无权访问", 404, 40400)
        before = refund["status"]
        after = before
        audit_status = before
        with connection.cursor() as cursor:
            if action == "删除":
                if before not in {"待提交", "被驳回"}:
                    raise ApiError("只有待提交或被驳回退款可以删除")
                cursor.execute(
                    "UPDATE refund_orders SET deleted_at=NOW() WHERE refund_id=%s",
                    (refund_id,),
                )
                after = "已删除"
            elif action == "提交":
                if before not in {"待提交", "被驳回"}:
                    raise ApiError("当前退款状态不能重复提交")
                after = audit_status = "待审核"
                cursor.execute(
                    """
                    UPDATE refund_orders SET status=%s,version=version+1
                    WHERE refund_id=%s
                    """,
                    (after, refund_id),
                )
            elif action in {"打款", "登记退款打款"}:
                if before != "待退款":
                    raise ApiError("退款必须审批通过后才能打款")
                actual = self._finance_positive_amount(body, "actualRefund")
                if actual > Decimal(str(refund["apply_amount"] or 0)):
                    raise ApiError("实退金额不能超过申请退款金额")
                after = audit_status = "已退款"
                cursor.execute(
                    """
                    UPDATE refund_orders
                    SET actual_amount=%s,pay_method=%s,status=%s,payee=%s,
                        pay_date=%s,version=version+1
                    WHERE refund_id=%s
                    """,
                    (
                        actual,
                        body.get("paymentMethod") or None,
                        after,
                        body.get("payee") or None,
                        body.get("paidAt") or date.today().isoformat(),
                        refund_id,
                    ),
                )
                cursor.execute(
                    """
                    UPDATE finance_refund_extensions
                    SET bank_name=%s,bank_branch=%s,bank_account=%s,
                        payment_remark=%s,paid_by_user_id=%s
                    WHERE refund_id=%s
                    """,
                    (
                        body.get("bank") or None,
                        body.get("bankBranch") or None,
                        body.get("bankAccount") or None,
                        body.get("paymentRemark") or None,
                        user["user_id"],
                        refund_id,
                    ),
                )
            elif action == "流程审批":
                if before != "待审核":
                    raise ApiError("只有待审核退款可以执行流程审批")
                result = str(body.get("auditResult") or "通过")
                if "通过" in result:
                    after, audit_status = "待退款", "审核通过"
                else:
                    after = audit_status = "被驳回"
                cursor.execute(
                    """
                    UPDATE refund_orders SET status=%s,version=version+1
                    WHERE refund_id=%s
                    """,
                    (after, refund_id),
                )
            elif action == "反审核":
                if before not in {"待退款", "被驳回"}:
                    raise ApiError("当前退款状态不能反审核")
                after = audit_status = "待审核"
                cursor.execute(
                    """
                    UPDATE refund_orders SET status=%s,version=version+1
                    WHERE refund_id=%s
                    """,
                    (after, refund_id),
                )
            elif action == "撤回":
                if before != "待审核":
                    raise ApiError("只有待审核退款可以撤回")
                after = audit_status = "待提交"
                cursor.execute(
                    """
                    UPDATE refund_orders SET status=%s,version=version+1
                    WHERE refund_id=%s
                    """,
                    (after, refund_id),
                )
            else:
                raise ApiError("当前退款操作尚未实现", 403, 40300)
            if action != "删除":
                cursor.execute(
                    """
                    UPDATE finance_refund_extensions
                    SET audit_status=%s,audit_remark=COALESCE(%s,audit_remark)
                    WHERE refund_id=%s
                    """,
                    (
                        audit_status,
                        body.get("auditRemark") or None,
                        refund_id,
                    ),
                )
        self._audit(
            connection,
            user,
            "FINANCE_REFUND",
            refund_id,
            action,
            refund["store_id"],
            before,
            after,
        )
        return {"id": refund_id, "status": after}

    def _finance_debt_action(
        self,
        connection,
        user: dict,
        action: str,
        debt_id: int,
        body: dict,
    ) -> dict:
        clause, params = self._store_clause(user, "da")
        row = execute_one(
            connection,
            f"""
            SELECT da.debt_audit_id,da.store_id,da.audit_status
            FROM finance_debt_audits da
            WHERE da.debt_audit_id=%s AND da.tenant_id=%s AND {clause}
            """,
            [debt_id, user["tenant_id"], *params],
        )
        if not row:
            raise ApiError("欠款审核记录不存在或无权访问", 404, 40400)
        if action != "审核":
            raise ApiError("当前欠款审核操作尚未实现", 403, 40300)
        result = str(body.get("auditResult") or "审核通过")
        target = "已通过" if "通过" in result else "审核不通过"
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE finance_debt_audits
                SET audit_status=%s,audit_remark=%s,
                    approved_by_user_id=%s,approved_at=NOW()
                WHERE debt_audit_id=%s
                """,
                (
                    target,
                    body.get("auditRemark") or None,
                    user["user_id"],
                    debt_id,
                ),
            )
        self._audit(
            connection,
            user,
            "FINANCE_DEBT_AUDIT",
            debt_id,
            action,
            row["store_id"],
            row["audit_status"],
            target,
        )
        return {"id": debt_id, "status": target}

    def _finance_exchange_action(
        self,
        connection,
        user: dict,
        action: str,
        exchange_id: int,
        body: dict,
    ) -> dict:
        clause, params = self._store_clause(user, "ea")
        row = execute_one(
            connection,
            f"""
            SELECT ea.exchange_id,ea.store_id,ea.audit_status
            FROM finance_exchange_audits ea
            WHERE ea.exchange_id=%s AND ea.tenant_id=%s
              AND ea.deleted_at IS NULL AND {clause}
            """,
            [exchange_id, user["tenant_id"], *params],
        )
        if not row:
            raise ApiError("换货审核记录不存在或无权访问", 404, 40400)
        target = row["audit_status"]
        with connection.cursor() as cursor:
            if action == "删除":
                if row["audit_status"] not in {"待审核", "已驳回"}:
                    raise ApiError("只有待审核或已驳回的换货单可以删除")
                cursor.execute(
                    """
                    UPDATE finance_exchange_audits
                    SET deleted_at=NOW() WHERE exchange_id=%s
                    """,
                    (exchange_id,),
                )
                target = "已删除"
            elif action == "审核":
                result = str(body.get("auditResult") or "审核通过")
                target = "已通过" if "通过" in result else "已驳回"
                cursor.execute(
                    """
                    UPDATE finance_exchange_audits
                    SET audit_status=%s,audit_remark=%s,
                        approved_by_user_id=%s,approved_at=NOW()
                    WHERE exchange_id=%s
                    """,
                    (
                        target,
                        body.get("auditRemark") or None,
                        user["user_id"],
                        exchange_id,
                    ),
                )
            else:
                raise ApiError("当前换货操作尚未实现", 403, 40300)
        self._audit(
            connection,
            user,
            "FINANCE_EXCHANGE",
            exchange_id,
            action,
            row["store_id"],
            row["audit_status"],
            target,
        )
        return {"id": exchange_id, "status": target}

    def _finance_invoice_action(
        self,
        connection,
        user: dict,
        action: str,
        invoice_id: int,
    ) -> dict:
        clause, params = self._store_clause(user, "i")
        row = execute_one(
            connection,
            f"""
            SELECT i.invoice_id,i.store_id,i.status,
                   i.source_type,i.source_ref
            FROM invoices i
            WHERE i.invoice_id=%s AND i.tenant_id=%s
              AND i.deleted_at IS NULL AND {clause}
            """,
            [invoice_id, user["tenant_id"], *params],
        )
        if not row:
            raise ApiError("发票不存在或无权访问", 404, 40400)
        if action != "删除":
            raise ApiError("当前发票操作尚未实现", 403, 40300)
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE invoices SET deleted_at=NOW() WHERE invoice_id=%s",
                (invoice_id,),
            )
            if row["source_type"] == "收款单" and row["source_ref"]:
                cursor.execute(
                    """
                    UPDATE finance_receipt_extensions ext
                    JOIN finance_receipts receipt
                      ON receipt.receipt_id=ext.receipt_id
                    SET ext.invoice_status='未开票'
                    WHERE receipt.tenant_id=%s
                      AND receipt.receipt_no=%s
                      AND NOT EXISTS (
                        SELECT 1 FROM invoices remaining
                        WHERE remaining.tenant_id=%s
                          AND remaining.source_type='收款单'
                          AND remaining.source_ref=%s
                          AND remaining.deleted_at IS NULL
                          AND remaining.invoice_id<>%s
                      )
                    """,
                    (
                        user["tenant_id"],
                        row["source_ref"],
                        user["tenant_id"],
                        row["source_ref"],
                        invoice_id,
                    ),
                )
        self._audit(
            connection,
            user,
            "FINANCE_INVOICE",
            invoice_id,
            action,
            row["store_id"],
            row["status"],
            "已删除",
        )
        return {"id": invoice_id, "status": "已删除"}

    def _finance_budget_action(
        self,
        connection,
        user: dict,
        action: str,
        budget_id: int,
        body: dict,
    ) -> dict:
        clause, params = self._store_clause(user, "b")
        row = execute_one(
            connection,
            f"""
            SELECT b.budget_id,b.store_id,b.status,b.purchase_plan_no
            FROM finance_material_budgets b
            WHERE b.budget_id=%s AND b.tenant_id=%s
              AND b.deleted_at IS NULL AND {clause}
            """,
            [budget_id, user["tenant_id"], *params],
        )
        if not row:
            raise ApiError("预算单不存在或无权访问", 404, 40400)
        target = row["status"]
        detail = {}
        with connection.cursor() as cursor:
            if action == "删除":
                if row["status"] not in {"待提交", "驳回"}:
                    raise ApiError("只有待提交或驳回的预算单可以删除")
                cursor.execute(
                    """
                    UPDATE finance_material_budgets
                    SET deleted_at=NOW() WHERE budget_id=%s
                    """,
                    (budget_id,),
                )
                target = "已删除"
            elif action == "提交":
                target = "审核中"
                cursor.execute(
                    """
                    UPDATE finance_material_budgets
                    SET status=%s,version=version+1 WHERE budget_id=%s
                    """,
                    (target, budget_id),
                )
            elif action == "流程审批":
                result = str(body.get("auditResult") or "通过")
                target = "审核通过" if "通过" in result else "驳回"
                cursor.execute(
                    """
                    UPDATE finance_material_budgets
                    SET status=%s,approved_by_user_id=%s,approved_at=NOW(),
                        version=version+1 WHERE budget_id=%s
                    """,
                    (target, user["user_id"], budget_id),
                )
            elif action == "生成采购计划":
                if row["status"] != "审核通过":
                    raise ApiError("只有审核通过的预算单可以生成采购计划")
                plan_no = row["purchase_plan_no"] or self._finance_number("CG")
                cursor.execute(
                    """
                    UPDATE finance_material_budgets
                    SET purchase_plan_no=%s,status='已下达',version=version+1
                    WHERE budget_id=%s
                    """,
                    (plan_no, budget_id),
                )
                target = "已下达"
                detail["purchasePlanNo"] = plan_no
            else:
                raise ApiError("当前预算操作尚未实现", 403, 40300)
        self._audit(
            connection,
            user,
            "FINANCE_BUDGET",
            budget_id,
            action,
            row["store_id"],
            row["status"],
            target,
            detail,
        )
        return {"id": budget_id, "status": target, **detail}

    def _finance_expense_action(
        self,
        connection,
        user: dict,
        resource: str,
        action: str,
        expense_id: int,
        body: dict,
    ) -> dict:
        clause, params = self._store_clause(user, "eo")
        own_sql = (
            "AND ext.applicant_user_id=%s"
            if resource == "my-expenses" and "SYS_ADMIN" not in user["roles"]
            else ""
        )
        if own_sql:
            params.append(user["user_id"])
        row = execute_one(
            connection,
            f"""
            SELECT eo.expense_id,eo.store_id,eo.status,eo.apply_amount
            FROM expense_orders eo
            JOIN finance_expense_extensions ext
              ON ext.expense_id=eo.expense_id
            WHERE eo.expense_id=%s AND eo.tenant_id=%s
              AND eo.deleted_at IS NULL AND {clause} {own_sql}
            """,
            [expense_id, user["tenant_id"], *params],
        )
        if not row:
            raise ApiError("费用单不存在或无权操作", 404, 40400)
        target = row["status"]
        with connection.cursor() as cursor:
            if action == "删除":
                if row["status"] not in {"待提交", "驳回"}:
                    raise ApiError("只有待提交或驳回的费用单可以删除")
                cursor.execute(
                    """
                    UPDATE expense_orders SET deleted_at=NOW()
                    WHERE expense_id=%s
                    """,
                    (expense_id,),
                )
                target = "已删除"
            elif action == "提交":
                if row["status"] not in {"待提交", "驳回"}:
                    raise ApiError("当前费用状态不能重复提交")
                target = "已提交"
                cursor.execute(
                    """
                    UPDATE expense_orders SET status=%s,version=version+1
                    WHERE expense_id=%s
                    """,
                    (target, expense_id),
                )
            elif action == "流程审批":
                if row["status"] != "已提交":
                    raise ApiError("只有已提交费用可以执行流程审批")
                result = str(body.get("auditResult") or "通过")
                target = "已审批" if "通过" in result else "驳回"
                cursor.execute(
                    """
                    UPDATE expense_orders
                    SET status=%s,audit_date=NOW(),version=version+1
                    WHERE expense_id=%s
                    """,
                    (target, expense_id),
                )
                cursor.execute(
                    """
                    UPDATE finance_expense_extensions
                    SET audit_remark=%s WHERE expense_id=%s
                    """,
                    (body.get("auditRemark") or None, expense_id),
                )
            elif action == "打款":
                if row["status"] != "已审批":
                    raise ApiError("费用必须审批通过后才能打款")
                amount = self._finance_positive_amount(body, "amount")
                if amount > Decimal(str(row["apply_amount"] or 0)):
                    raise ApiError("打款金额不能超过审批申请金额")
                target = "已打款"
                cursor.execute(
                    """
                    UPDATE expense_orders
                    SET actual_amount=%s,pay_method=%s,status=%s,
                        pay_date=%s,version=version+1
                    WHERE expense_id=%s
                    """,
                    (
                        amount,
                        body.get("payoutType") or None,
                        target,
                        body.get("paidAt") or date.today().isoformat(),
                        expense_id,
                    ),
                )
                cursor.execute(
                    """
                    UPDATE finance_expense_extensions
                    SET paid_by_user_id=%s,payout_type=%s,
                        attachment_names=COALESCE(%s,attachment_names)
                    WHERE expense_id=%s
                    """,
                    (
                        user["user_id"],
                        body.get("payoutType") or None,
                        body.get("attachment") or None,
                        expense_id,
                    ),
                )
                cursor.execute(
                    """
                    INSERT INTO finance_payments(
                      tenant_id,store_id,payment_no,project_name,payee,amount,
                      payment_status,audit_status,source_type,source_id,
                      created_by_user_id,paid_by_user_id,paid_at
                    ) VALUES (
                      %s,%s,%s,%s,%s,%s,'已打款','审核通过',
                      '费用单',%s,%s,%s,NOW()
                    )
                    """,
                    (
                        user["tenant_id"],
                        row["store_id"],
                        self._finance_number("FK"),
                        "费用支付",
                        body.get("payee") or user["username"],
                        amount,
                        expense_id,
                        user["user_id"],
                        user["user_id"],
                    ),
                )
            elif action == "反审核":
                if row["status"] not in {"已提交", "已审批", "驳回"}:
                    raise ApiError("当前费用状态不能反审核")
                target = "待提交"
                cursor.execute(
                    """
                    UPDATE expense_orders
                    SET status=%s,audit_date=NULL,version=version+1
                    WHERE expense_id=%s
                    """,
                    (target, expense_id),
                )
            else:
                raise ApiError("当前费用操作尚未实现", 403, 40300)
        self._audit(
            connection,
            user,
            "FINANCE_EXPENSE",
            expense_id,
            action,
            row["store_id"],
            row["status"],
            target,
        )
        return {"id": expense_id, "status": target}

    def _recovery_store_id(self, connection, user: dict, body: dict) -> int:
        raw = body.get("storeId")
        if raw:
            return self._allowed_store(user, raw)
        store_name = str(body.get("store") or "").strip()
        if store_name:
            clause, params = self._store_clause(user, "s")
            row = execute_one(
                connection,
                f"""
                SELECT s.store_id FROM stores s
                WHERE s.tenant_id=%s AND s.name=%s AND {clause}
                """,
                [user["tenant_id"], store_name, *params],
            )
            if row:
                return int(row["store_id"])
            keyword = ""
            if "黄河路" in store_name:
                keyword = "黄河路"
            elif "中心广场" in store_name or "建设路" in store_name:
                keyword = "建设路"
            if keyword:
                row = execute_one(
                    connection,
                    f"""
                    SELECT s.store_id FROM stores s
                    WHERE s.tenant_id=%s AND s.name LIKE %s AND {clause}
                    ORDER BY s.store_id LIMIT 1
                    """,
                    [
                        user["tenant_id"],
                        f"%{keyword}%",
                        *params,
                    ],
                )
                if row:
                    return int(row["store_id"])
        if user.get("default_store_id"):
            return self._allowed_store(user, user["default_store_id"])
        if len(user["store_ids"]) == 1:
            return int(user["store_ids"][0])
        raise ApiError("请选择服务门店")

    def _recovery_customer(
        self, connection, user: dict, body: dict, store_id: int
    ) -> dict:
        customer_id = body.get("customerId")
        params = [user["tenant_id"], store_id]
        where = "c.customer_id=%s"
        if customer_id:
            params.append(int(customer_id))
        else:
            name = str(body.get("customerName") or "").strip()
            if not name:
                raise ApiError("请选择客户")
            where = "c.name=%s"
            params.append(name)
        rows = execute_all(
            connection,
            f"""
            SELECT c.customer_id, c.name, c.store_id
            FROM customers c
            WHERE c.tenant_id=%s AND c.store_id=%s
              AND c.deleted_at IS NULL AND {where}
            LIMIT 2
            """,
            params,
        )
        if not rows:
            raise ApiError("客户不存在或不属于当前门店")
        if len(rows) > 1:
            raise ApiError("存在重名客户，请从客户选择弹窗重新选择")
        return rows[0]

    def _recovery_staff(
        self,
        connection,
        user: dict,
        body: dict,
        store_id: int,
        key: str = "technicianStaffId",
        name_key: str = "technician",
    ) -> dict:
        staff_id = body.get(key)
        name = str(body.get(name_key) or "").strip()
        if not staff_id and not name and user.get("staff_id"):
            staff_id = user["staff_id"]
        params = [user["tenant_id"], store_id]
        where = "st.staff_id=%s"
        if staff_id:
            params.append(int(staff_id))
        else:
            if not name:
                raise ApiError("请选择服务人员")
            where = "st.name=%s"
            params.append(name)
        rows = execute_all(
            connection,
            f"""
            SELECT st.staff_id, st.name, st.store_id
            FROM staff st
            WHERE st.tenant_id=%s AND st.store_id=%s
              AND st.employment_status='ACTIVE' AND {where}
            LIMIT 2
            """,
            params,
        )
        if not rows:
            raise ApiError("服务人员不存在或不属于当前门店")
        if len(rows) > 1:
            raise ApiError("存在同名服务人员，请重新选择")
        return rows[0]

    def _appointment_period(self, body: dict) -> tuple[str | None, str | None]:
        start = str(body.get("periodStart") or "").strip()
        end = str(body.get("periodEnd") or "").strip()
        text = str(
            body.get("appointmentPeriod")
            or body.get("servicePeriod")
            or body.get("timePeriod")
            or ""
        ).strip()
        if text and ("-" in text or "至" in text):
            parts = re.split(r"\s*(?:-|至)\s*", text, maxsplit=1)
            if len(parts) == 2:
                start, end = parts
        for value in (start, end):
            if value and not re.fullmatch(r"\d{1,2}:\d{2}", value):
                raise ApiError("服务时段格式应为 HH:mm-HH:mm")
        return (start or None, end or None)

    def _masked_phone(self, user: dict, phone: str | None) -> str | None:
        if not phone or user["unmasked_customer_phone"]:
            return phone
        if len(phone) < 7:
            return "*" * len(phone)
        return f"{phone[:3]}****{phone[-4:]}"

    def _customer_entry_store_id(
        self, connection, user: dict, body: dict, key: str = "intendedStore"
    ) -> int:
        explicit_id = body.get(f"{key}Id")
        if explicit_id:
            return self._allowed_store(user, explicit_id)
        requested = str(body.get(key) or "").strip()
        if requested:
            clause, params = self._store_clause(user, "s")
            stores = execute_all(
                connection,
                f"""
                SELECT s.store_id, s.name
                FROM stores s
                WHERE s.tenant_id=%s AND {clause}
                ORDER BY s.sort_weight DESC, s.store_id
                """,
                [user["tenant_id"], *params],
            )
            for store in stores:
                if self._room_store_matches(requested, store["name"]):
                    return int(store["store_id"])
            raise ApiError("当前账号无权访问所选门店", 403, 40300)
        if user.get("default_store_id"):
            return self._allowed_store(user, user["default_store_id"])
        if len(user["store_ids"]) == 1:
            return int(user["store_ids"][0])
        raise ApiError("请选择意向分店")

    def _check_customer_duplicate(
        self, connection, user: dict, body: dict
    ):
        self._require_any_permission(
            user, ("CUSTOMER.VIEW", "CUSTOMER.CREATE")
        )
        mobile = re.sub(r"\s+", "", str(body.get("mobile") or ""))
        wechat = str(body.get("wechat") or "").strip()
        if not mobile and not wechat:
            raise ApiError("请先填写客户电话或 QQ/微信")
        contact_sql = []
        contact_params = []
        if mobile:
            contact_sql.append("c.phone=%s")
            contact_params.append(mobile)
        if wechat:
            contact_sql.append("c.wechat=%s")
            contact_params.append(wechat)
        clause, store_params = self._store_clause(user, "c")
        rows = execute_all(
            connection,
            f"""
            SELECT c.customer_id AS id, c.customer_no AS code, c.name,
                   c.phone AS mobile, c.status, c.wechat,
                   tracker.name AS trackerName, s.name AS store
            FROM customers c
            LEFT JOIN staff tracker
              ON tracker.staff_id=c.sales_staff_id
            LEFT JOIN stores s ON s.store_id=c.store_id
            WHERE c.tenant_id=%s AND c.deleted_at IS NULL
              AND ({' OR '.join(contact_sql)}) AND {clause}
            ORDER BY c.customer_id DESC
            LIMIT 20
            """,
            [
                user["tenant_id"],
                *contact_params,
                *store_params,
            ],
        )
        for row in rows:
            row["mobile"] = self._masked_phone(user, row.get("mobile"))
        return self._success({"records": rows, "total": len(rows)})

    def _save_customer_entry_draft(
        self, connection, user: dict, body: dict
    ):
        self._require_any_permission(user, ("CUSTOMER.CREATE",))
        store_id = self._customer_entry_store_id(connection, user, body)
        draft_id = int(body.get("draftId") or 0)
        payload = compact_json(
            {key: value for key, value in body.items() if key != "draftId"}
        )
        with connection.cursor() as cursor:
            if draft_id:
                cursor.execute(
                    """
                    UPDATE customer_entry_drafts
                    SET store_id=%s, payload_json=%s, status='草稿'
                    WHERE draft_id=%s AND tenant_id=%s
                      AND owner_user_id=%s
                    """,
                    (
                        store_id,
                        payload,
                        draft_id,
                        user["tenant_id"],
                        user["user_id"],
                    ),
                )
                if cursor.rowcount == 0:
                    raise ApiError("客户草稿不存在或无权访问", 404, 40400)
            else:
                cursor.execute(
                    """
                    INSERT INTO customer_entry_drafts(
                      tenant_id,store_id,owner_user_id,payload_json,status
                    ) VALUES (%s,%s,%s,%s,'草稿')
                    """,
                    (
                        user["tenant_id"],
                        store_id,
                        user["user_id"],
                        payload,
                    ),
                )
                draft_id = cursor.lastrowid
        connection.commit()
        return self._success(
            {
                "draftId": draft_id,
                "savedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    def _create_customer_entry(
        self, connection, user: dict, body: dict
    ):
        self._require_any_permission(user, ("CUSTOMER.CREATE",))
        name = str(body.get("name") or "").strip()
        mobile = re.sub(r"\s+", "", str(body.get("mobile") or ""))
        wechat = str(body.get("wechat") or "").strip()
        status = str(body.get("status") or "").strip()
        source = str(body.get("source") or "").strip()
        country_code = str(body.get("countryCode") or "+86").strip()
        if not name:
            raise ApiError("客户姓名不能为空")
        if len(name) > 30:
            raise ApiError("客户姓名不能超过30个字符")
        if len(wechat) > 50:
            raise ApiError("QQ/微信不能超过50个字符")
        if not mobile and not wechat:
            raise ApiError("客户电话与 QQ/微信至少填写一项")
        if status == "同意签合同" and not mobile:
            raise ApiError("同意签合同时必须填写客户电话")
        if mobile:
            if country_code == "+86" and not re.fullmatch(
                r"1[3-9]\d{9}", mobile
            ):
                raise ApiError("中国大陆手机号格式不正确")
            if country_code != "+86" and not re.fullmatch(r"\d{6,20}", mobile):
                raise ApiError("联系电话格式不正确")
        if not status:
            raise ApiError("请选择客户状态")
        if not source:
            raise ApiError("请选择客户来源")

        store_id = self._customer_entry_store_id(connection, user, body)
        duplicate_sql = []
        duplicate_params = []
        if mobile:
            duplicate_sql.append("phone=%s")
            duplicate_params.append(mobile)
        if wechat:
            duplicate_sql.append("wechat=%s")
            duplicate_params.append(wechat)
        duplicate = execute_one(
            connection,
            f"""
            SELECT customer_id,customer_no,name
            FROM customers
            WHERE tenant_id=%s AND deleted_at IS NULL
              AND ({' OR '.join(duplicate_sql)})
            ORDER BY customer_id DESC LIMIT 1
            """,
            [user["tenant_id"], *duplicate_params],
        )
        if duplicate and not bool(body.get("duplicateConfirmed")):
            raise ApiError(
                f"客户联系方式已存在于客户"
                f"{duplicate['customer_no'] or duplicate['customer_id']}",
                409,
                40900,
            )

        tracker_id = 0
        try:
            tracker_id = int(
                body.get("salesStaffId") or body.get("trackerId") or 0
            )
        except (TypeError, ValueError):
            tracker_id = 0
        tracker = None
        if tracker_id:
            tracker = execute_one(
                connection,
                """
                SELECT staff_id,store_id,department
                FROM staff
                WHERE staff_id=%s AND tenant_id=%s
                  AND employment_status='ACTIVE'
                """,
                (tracker_id, user["tenant_id"]),
            )
        sales_staff_name = str(
            body.get("salesStaffName") or body.get("trackerName") or ""
        ).strip()
        if not tracker and sales_staff_name:
            tracker = execute_one(
                connection,
                """
                SELECT staff_id,store_id,department
                FROM staff
                WHERE tenant_id=%s AND store_id=%s
                  AND employment_status='ACTIVE' AND name=%s
                ORDER BY staff_id LIMIT 1
                """,
                (
                    user["tenant_id"],
                    store_id,
                    sales_staff_name,
                ),
            )
        if not tracker:
            raise ApiError("请选择当前门店的所属业务员")
        if tracker and int(tracker.get("store_id") or 0) != store_id:
            raise ApiError("所属业务员不属于当前意向门店")
        tracker_id = int(tracker["staff_id"]) if tracker else None

        room_id = int(body.get("roomId") or 0) or None
        if room_id:
            room = execute_one(
                connection,
                """
                SELECT room_id,store_id FROM rooms
                WHERE room_id=%s AND tenant_id=%s AND deleted_at IS NULL
                """,
                (room_id, user["tenant_id"]),
            )
            if not room or int(room["store_id"]) != store_id:
                raise ApiError("意向房间不属于当前意向门店")

        recovery_store_id = None
        if body.get("recoveryStore"):
            recovery_store_id = self._customer_entry_store_id(
                connection, user, body, "recoveryStore"
            )

        def optional_int(value):
            if value in (None, ""):
                return None
            try:
                return int(value)
            except (TypeError, ValueError) as exc:
                raise ApiError("客户数字字段格式不正确") from exc

        def optional_decimal(value):
            if value in (None, ""):
                return None
            try:
                return Decimal(str(value))
            except (ArithmeticError, ValueError) as exc:
                raise ApiError("客户金额字段格式不正确") from exc

        package_id = optional_int(body.get("packageId"))
        package_version_id = optional_int(body.get("packageVersionId"))
        package_price_rule_id = optional_int(
            body.get("packagePriceRuleId")
        )
        if package_version_id or package_price_rule_id:
            if not package_version_id or not package_price_rule_id:
                raise ApiError("套餐版本和价格规则必须同时选择")
            selected_package = execute_one(
                connection,
                """
                SELECT pp.package_id,pp.package_name,
                       pv.package_version_id,pr.price_rule_id,
                       pr.reference_amount,pr.stay_days,
                       rt.name AS room_type
                FROM package_products pp
                JOIN package_versions pv ON pv.package_id=pp.package_id
                JOIN package_price_rules pr
                  ON pr.package_version_id=pv.package_version_id
                JOIN room_types rt ON rt.room_type_id=pr.room_type_id
                WHERE pp.tenant_id=%s AND pp.deleted_at IS NULL
                  AND pp.status='ACTIVE'
                  AND pv.package_version_id=%s
                  AND pv.version_status='ACTIVE'
                  AND pr.price_rule_id=%s
                  AND pr.store_id=%s
                  AND pr.status='ACTIVE'
                  AND pv.effective_from<=CURDATE()
                  AND (
                    pv.effective_to IS NULL
                    OR pv.effective_to>=CURDATE()
                  )
                  AND pr.effective_from<=CURDATE()
                  AND (
                    pr.effective_to IS NULL
                    OR pr.effective_to>=CURDATE()
                  )
                """,
                (
                    user["tenant_id"],
                    package_version_id,
                    package_price_rule_id,
                    store_id,
                ),
            )
            if not selected_package:
                raise ApiError("所选套餐价格当前无效或不适用于意向门店")
            package_id = selected_package["package_id"]
            body = dict(body)
            body["packageName"] = selected_package["package_name"]
            body["packageAmount"] = selected_package["reference_amount"]
            body["intendedDays"] = selected_package["stay_days"]
            body["roomType"] = selected_package["room_type"]
        tags = body.get("tags") if isinstance(body.get("tags"), list) else []
        customer_note = str(body.get("customerNote") or "").strip() or None
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO customers(
                  tenant_id,store_id,sales_staff_id,name,gender,phone,wechat,
                  id_no,id_type,age,birthday,native,source,advisor,status,edc,
                  parity,delivery_type,intent_room,intent_package,referrer,
                  referrer_relation,referrer_phone,review_date,
                  prenatal_hospital,meal_package,level,remark,version,
                  created_at,updated_at,created_by,created_by_user_id
                ) VALUES (
                  %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                  %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,0,NOW(),NOW(),%s,%s
                )
                """,
                (
                    user["tenant_id"],
                    store_id,
                    tracker_id,
                    name,
                    body.get("sex") or "女",
                    mobile or None,
                    wechat or None,
                    body.get("documentNo") or None,
                    body.get("documentType") or None,
                    optional_int(body.get("age")),
                    body.get("birthday") or None,
                    body.get("nativePlace") or None,
                    source,
                    body.get("trackerName") or None,
                    status,
                    body.get("dueDate") or None,
                    body.get("pregnancyCount") or None,
                    body.get("deliveryMethod") or None,
                    body.get("room") or None,
                    body.get("packageName") or None,
                    body.get("introducerName") or None,
                    body.get("introducerType") or None,
                    body.get("introducerPhone") or None,
                    body.get("reviewDate") or None,
                    body.get("prenatalHospital") or None,
                    body.get("mealPackage") or None,
                    "、".join(str(item) for item in tags) or None,
                    customer_note,
                    user["username"],
                    user["user_id"],
                ),
            )
            customer_id = cursor.lastrowid
            customer_no = f"KH-{datetime.now():%Y}-{customer_id:05d}"
            cursor.execute(
                "UPDATE customers SET customer_no=%s WHERE customer_id=%s",
                (customer_no, customer_id),
            )
            cursor.execute(
                """
                INSERT INTO customer_entry_profiles(
                  tenant_id,customer_id,country_code,member_card,tags_json,
                  is_to_store,intended_days,planned_stay_date,
                  intended_room_id,intended_room_type,
                  estimated_contract_amount,intended_package_id,
                  intended_package_version_id,
                  intended_package_price_rule_id,
                  intended_package_name,intended_package_amount,
                  recovery_store_id,companion_name,companion_phone,
                  fetus_type,pregnancy_count,area_id,area_name,first_visit_at,
                  tracker_staff_id,tracker_department,ethnicity,work_unit,
                  occupation,email,entry_time,address,diet_note
                ) VALUES (
                  %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                  %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
                )
                """,
                (
                    user["tenant_id"],
                    customer_id,
                    country_code,
                    body.get("memberCard") or None,
                    compact_json(tags),
                    int(bool(body.get("isToStore"))),
                    optional_int(body.get("intendedDays")),
                    body.get("plannedStayDate") or None,
                    room_id,
                    body.get("roomType") or None,
                    optional_decimal(body.get("contractAmount")),
                    package_id,
                    package_version_id,
                    package_price_rule_id,
                    body.get("packageName") or None,
                    optional_decimal(body.get("packageAmount")),
                    recovery_store_id,
                    body.get("companionName") or None,
                    body.get("companionPhone") or None,
                    body.get("fetusType") or None,
                    body.get("pregnancyCount") or None,
                    str(body.get("areaId") or "") or None,
                    body.get("area") or None,
                    body.get("firstVisitAt") or None,
                    tracker_id,
                    body.get("trackerDepartment")
                    or (tracker.get("department") if tracker else None),
                    body.get("ethnicity") or None,
                    body.get("workUnit") or None,
                    body.get("occupation") or None,
                    body.get("email") or None,
                    body.get("entryTime") or None,
                    body.get("address") or None,
                    body.get("dietNote") or None,
                ),
            )
            draft_id = int(body.get("draftId") or 0)
            if draft_id:
                cursor.execute(
                    """
                    DELETE FROM customer_entry_drafts
                    WHERE draft_id=%s AND tenant_id=%s
                      AND owner_user_id=%s
                    """,
                    (draft_id, user["tenant_id"], user["user_id"]),
                )
        self._audit(
            connection,
            user,
            "CUSTOMER",
            customer_id,
            "CREATE_FROM_ENTRY",
            store_id,
            None,
            status,
            {"customerNo": customer_no},
        )
        connection.commit()
        return self._success(
            {
                "id": customer_id,
                "customerNo": customer_no,
                "customerCode": customer_no,
                "status": status,
            }
        )

    def _get_customer_entry_options(self, connection, user: dict):
        self._require_any_permission(
            user,
            ("CUSTOMER.VIEW", "CUSTOMER.CREATE"),
        )
        clause, params = self._store_clause(user, "s")
        stores = execute_all(
            connection,
            f"""
            SELECT s.store_id AS id, s.name
            FROM stores s
            WHERE s.tenant_id=%s AND {clause}
            ORDER BY s.sort_weight DESC, s.store_id
            """,
            [user["tenant_id"], *params],
        )
        room_clause, room_params = self._store_clause(user, "r")
        rooms = execute_all(
            connection,
            f"""
            SELECT r.room_id AS id, r.room_no AS name,
                   COALESCE(rt.name, r.room_type) AS type,
                   s.name AS store, r.price AS dailyPrice,
                   CASE WHEN r.status='空闲' THEN '可预订'
                        ELSE r.status END AS status
            FROM rooms r
            JOIN stores s ON s.store_id=r.store_id
            LEFT JOIN room_types rt ON rt.room_type_id=r.room_type_id
            WHERE r.tenant_id=%s AND r.deleted_at IS NULL
              AND {room_clause}
            ORDER BY r.store_id, r.floor, r.layout_order, r.room_no
            """,
            [user["tenant_id"], *room_params],
        )
        package_clause, package_params = self._store_clause(user, "pr")
        packages = execute_all(
            connection,
            f"""
            SELECT pp.package_id AS id,
                   pv.package_version_id AS packageVersionId,
                   pr.price_rule_id AS packagePriceRuleId,
                   pp.package_name AS name,
                   pp.package_name AS packageName,
                   pr.reference_amount AS amount,
                   COALESCE(profile.original_amount,pr.reference_amount) AS referencePrice,
                   COALESCE(profile.activity_amount,pr.reference_amount) AS activityPrice,
                   COALESCE(profile.deal_amount,pr.reference_amount) AS salePrice,
                   pr.stay_days AS days,
                   rt.name AS roomType,
                   rt.room_type_id AS roomTypeId,
                   s.name AS store,s.store_id AS storeId,
                   pv.version_no AS versionNo
            FROM package_products pp
            JOIN package_versions pv ON pv.package_id=pp.package_id
            JOIN package_price_rules pr
              ON pr.package_version_id=pv.package_version_id
            LEFT JOIN package_price_profiles profile
              ON profile.price_rule_id=pr.price_rule_id
            JOIN room_types rt ON rt.room_type_id=pr.room_type_id
            JOIN stores s ON s.store_id=pr.store_id
            WHERE pp.tenant_id=%s AND pp.deleted_at IS NULL
              AND pp.status='ACTIVE'
              AND pv.version_status='ACTIVE'
              AND pr.status='ACTIVE'
              AND pv.effective_from<=CURDATE()
              AND (pv.effective_to IS NULL OR pv.effective_to>=CURDATE())
              AND pr.effective_from<=CURDATE()
              AND (pr.effective_to IS NULL OR pr.effective_to>=CURDATE())
              AND {package_clause}
            ORDER BY s.sort_weight DESC,s.store_id,pp.sort_order,
                     rt.sort_order,pr.stay_days,pp.package_id
            """,
            [user["tenant_id"], *package_params],
        )
        if not packages:
            packages = execute_all(
                connection,
                """
                SELECT MIN(rt.room_type_id) AS id,
                       rt.package_name AS name,
                       ROUND(AVG(NULLIF(r.price,0))*28,2) AS amount,
                       28 AS days,
                       GROUP_CONCAT(
                         DISTINCT rt.name ORDER BY rt.sort_order
                         SEPARATOR '、'
                       ) AS roomType
                FROM room_types rt
                LEFT JOIN rooms r
                  ON r.room_type_id=rt.room_type_id
                 AND r.deleted_at IS NULL
                WHERE rt.tenant_id=%s AND rt.status='启用'
                GROUP BY rt.package_name
                ORDER BY MIN(rt.sort_order),rt.package_name
                """,
                (user["tenant_id"],),
            )
        staff_clause, staff_params = self._store_clause(user, "st")
        staff = execute_all(
            connection,
            f"""
            SELECT st.staff_id AS id, st.name, st.department,
                   st.position, st.phone AS mobile, s.name AS store
            FROM staff st
            LEFT JOIN stores s ON s.store_id=st.store_id
            WHERE st.tenant_id=%s AND st.employment_status='ACTIVE'
              AND {staff_clause}
            ORDER BY st.store_id, st.department, st.name
            """,
            [user["tenant_id"], *staff_params],
        )
        dictionary_rows = []
        dictionary_tables = execute_one(
            connection,
            """
            SELECT COUNT(*) AS total
            FROM information_schema.tables
            WHERE table_schema=DATABASE()
              AND table_name IN (
                'sys_dictionary_types', 'sys_dictionary_items'
              )
            """,
        )
        if dictionary_tables and int(dictionary_tables["total"]) == 2:
            dictionary_rows = execute_all(
                connection,
                """
                SELECT dt.code AS typeCode, dt.name AS typeName,
                       di.dictionary_item_id AS id, di.name
                FROM sys_dictionary_types dt
                JOIN sys_dictionary_items di
                  ON di.dictionary_type_id=dt.dictionary_type_id
                WHERE dt.tenant_id=%s AND dt.status='ACTIVE'
                  AND di.status='ACTIVE'
                  AND (
                    dt.name LIKE '%%来源%%' OR dt.code LIKE '%%SOURCE%%'
                    OR dt.name LIKE '%%区域%%' OR dt.name LIKE '%%地区%%'
                    OR dt.code LIKE '%%AREA%%'
                    OR dt.name LIKE '%%医院%%'
                    OR dt.code LIKE '%%HOSPITAL%%'
                  )
                ORDER BY dt.sort_order, di.sort_order,
                         di.dictionary_item_id
                """,
                (user["tenant_id"],),
            )

        def dictionary_values(*keywords):
            return [
                row
                for row in dictionary_rows
                if any(
                    keyword.lower()
                    in f"{row['typeCode']} {row['typeName']}".lower()
                    for keyword in keywords
                )
            ]

        legacy_customer_sources = [
            "客户介绍",
            "住附近",
            "电话来访",
            "大众点评",
            "美团咨询",
            "地推拓客",
            "抖音咨询",
            "小红书咨询",
            "自然上门",
            "网络搜索",
            "市场渠道",
            "二胎入住",
            "内部资源",
        ]
        source_dictionary_rows = dictionary_values("来源", "source")
        sources = [
            {"id": row.get("id") or f"source-{index + 1}", "name": row["name"]}
            for index, row in enumerate(
                source_dictionary_rows
                or [
                    {"id": f"legacy-source-{index + 1}", "name": name}
                    for index, name in enumerate(legacy_customer_sources)
                ]
            )
        ]
        areas = [
            {"id": row["id"], "name": row["name"]}
            for row in dictionary_values("区域", "地区", "area")
        ]
        hospitals = [
            row["name"] for row in dictionary_values("医院", "hospital")
        ]
        introducers = [
            {
                "id": row["id"],
                "name": row["name"],
                "mobile": row.get("mobile"),
                "type": "员工",
            }
            for row in staff
        ]
        return self._success(
            {
                "stores": stores,
                "sources": sources,
                "rooms": rooms,
                "packages": packages,
                "trackers": staff,
                "introducers": introducers,
                "areas": areas,
                "hospitals": hospitals,
            }
        )

    def _get_customer_module_data(
        self, connection, user: dict, resource: str, query: dict
    ):
        self._require_any_permission(
            user,
            ("CUSTOMER.VIEW", "LEGACY.WEB.N37.B18"),
        )
        supported = {
            "clues",
            "my-customers",
            "customers",
            "follow-records",
            "signed-customers",
            "appointments",
            "public-customers",
            "visits",
            "satisfaction",
            "callbacks",
            "complaints",
            "message-templates",
            "messages",
            "point-settings",
            "point-records",
            "activities",
        }
        if resource not in supported:
            raise ApiError("客户资源不存在", 404, 40400)
        if resource not in {"my-customers", "customers", "signed-customers"}:
            rows = self._operational_module_rows(
                connection, user, "CUSTOMER", resource, query
            )
            return self._success({"list": rows, "total": len(rows)})

        store_clause, store_params = self._store_clause(user, "c")
        owner_sql = ""
        owner_params = []
        if resource == "my-customers" and "SYS_ADMIN" not in user["roles"]:
            if not user.get("staff_id"):
                return self._success({"list": [], "total": 0})
            owner_sql = "AND c.sales_staff_id=%s"
            owner_params.append(user["staff_id"])
        contract_filter = ""
        if resource == "signed-customers":
            contract_filter = """
                AND ct.status IN (
                  '已签合同但未审核','已签合同但未入住',
                  '已审核','已订房','已入住'
                )
            """
        rows = execute_all(
            connection,
            f"""
            SELECT c.customer_id AS id, c.name,
                   c.birthday, c.age, c.phone AS mobile,
                   c.wechat, c.status, c.source,
                   c.edc AS dueDate, c.created_at AS createdAt,
                    c.remark, c.customer_no AS memberCard,
                    profile.tags_json AS tagsJson,
                   sales.name AS salesperson,
                   creator.username AS creator,
                   intended.name AS intendedStore,
                   intended.name AS stayStore,
                   MAX(ct.contract_no) AS contractNo,
                   MAX(ct.amount) AS contractAmount,
                   MAX(GREATEST(ct.amount-ct.paid,0)) AS debtAmount,
                   MAX(ct.sign_date) AS signedAt,
                   MAX(rb_room.room_no) AS room
            FROM customers c
            LEFT JOIN staff sales ON sales.staff_id=c.sales_staff_id
            LEFT JOIN user_accounts creator
              ON creator.user_id=c.created_by_user_id
            LEFT JOIN customer_entry_profiles profile
              ON profile.customer_id=c.customer_id
             AND profile.tenant_id=c.tenant_id
            LEFT JOIN stores intended ON intended.store_id=c.store_id
            LEFT JOIN contracts ct
              ON ct.customer_id=c.customer_id
             AND ct.tenant_id=c.tenant_id
             AND ct.deleted_at IS NULL
            LEFT JOIN room_bookings rb
              ON rb.customer_id=c.customer_id
             AND rb.tenant_id=c.tenant_id
             AND rb.deleted_at IS NULL
             AND rb.status IN ('已订房','已入住')
            LEFT JOIN rooms rb_room ON rb_room.room_id=rb.room_id
            WHERE c.tenant_id=%s AND c.deleted_at IS NULL
              AND {store_clause} {owner_sql} {contract_filter}
            GROUP BY c.customer_id
            ORDER BY c.customer_id DESC
            LIMIT 1000
            """,
            [
                user["tenant_id"],
                *store_params,
                *owner_params,
            ],
        )
        for row in rows:
            row["mobile"] = self._masked_phone(user, row.get("mobile"))
            try:
                tags = json.loads(row.pop("tagsJson") or "[]")
            except (TypeError, ValueError, json.JSONDecodeError):
                tags = []
            row["tags"] = "、".join(str(tag).strip() for tag in tags if str(tag).strip())
        return self._success({"list": rows, "total": len(rows)})

    def _requested_store_id(self, user: dict, source: dict) -> int | None:
        raw = source.get("storeId") or source.get("store_id")
        if raw in (None, "", "all"):
            return None
        return self._allowed_store(user, raw)

    def _scoped_store_clause(
        self, user: dict, source: dict, alias: str
    ) -> tuple[str, list]:
        clause, params = self._store_clause(user, alias)
        store_id = self._requested_store_id(user, source)
        if store_id is None:
            return clause, params
        return f"{clause} AND {alias}.store_id=%s", [*params, store_id]

    def _resolve_write_store(
        self, connection, user: dict, body: dict
    ) -> int:
        raw = body.get("storeId") or body.get("store_id")
        if raw not in (None, "", "all"):
            return self._allowed_store(user, raw)
        store_name = str(body.get("store") or "").strip()
        if store_name:
            row = execute_one(
                connection,
                """
                SELECT store_id
                FROM stores
                WHERE tenant_id=%s AND name=%s
                """,
                (user["tenant_id"], store_name),
            )
            if row:
                return self._allowed_store(user, row["store_id"])
        raise ApiError("新增或编辑前请选择具体门店，全部门店仅可查询汇总", 400, 40000)

    def _inventory_quantity(
        self, value, label: str, *, allow_zero: bool = False
    ) -> int:
        try:
            quantity = Decimal(str(value))
        except Exception as exc:
            raise ApiError(f"{label}必须是整数") from exc
        if quantity != quantity.to_integral_value():
            raise ApiError(f"{label}必须是整数")
        quantity_int = int(quantity)
        if quantity_int < 0 or (quantity_int == 0 and not allow_zero):
            suffix = "非负整数" if allow_zero else "正整数"
            raise ApiError(f"{label}必须是{suffix}")
        return quantity_int

    def _inventory_item(self, connection, user: dict, item_name) -> dict:
        name = str(item_name or "").strip()
        if not name:
            raise ApiError("请填写已建档的物料名称")
        rows = execute_all(
            connection,
            """
            SELECT item_id, name, unit
            FROM items
            WHERE tenant_id=%s AND name=%s
            LIMIT 2
            """,
            (user["tenant_id"], name),
        )
        if not rows:
            raise ApiError(
                f"物料“{name}”尚未建档，请先在物料档案维护后再过账",
                409,
                40900,
            )
        if len(rows) > 1:
            raise ApiError(
                f"物料“{name}”存在重名，请先合并物料档案",
                409,
                40900,
            )
        return rows[0]

    def _inventory_store_by_name(
        self, connection, user: dict, value, label: str
    ) -> int:
        name = str(value or "").strip()
        if not name:
            raise ApiError(f"请选择{label}")
        row = execute_one(
            connection,
            """
            SELECT store_id
            FROM stores
            WHERE tenant_id=%s AND name=%s
            """,
            (user["tenant_id"], name),
        )
        if not row:
            raise ApiError(f"{label}不存在")
        return self._allowed_store(user, row["store_id"])

    def _locked_inventory(
        self,
        connection,
        user: dict,
        store_id: int,
        item_id: int,
    ) -> dict:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO inventory(
                  tenant_id, store_id, item_id,
                  qty, warn_qty, avg_cost, version
                )
                VALUES (%s,%s,%s,0,0,0,0)
                ON DUPLICATE KEY UPDATE item_id=VALUES(item_id)
                """,
                (user["tenant_id"], store_id, item_id),
            )
        return execute_one(
            connection,
            """
            SELECT qty, warn_qty, avg_cost, version
            FROM inventory
            WHERE tenant_id=%s AND store_id=%s AND item_id=%s
            FOR UPDATE
            """,
            (user["tenant_id"], store_id, item_id),
        )

    def _record_stock_movement(
        self,
        connection,
        user: dict,
        store_id: int,
        item_id: int,
        movement_type: str,
        quantity: int,
        reference: str,
    ) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO stock_movements(
                  tenant_id, store_id, item_id, type,
                  qty, ref, created_at, created_by
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    user["tenant_id"],
                    store_id,
                    item_id,
                    movement_type,
                    quantity,
                    reference,
                    datetime.now().isoformat(timespec="seconds"),
                    str(user.get("username") or user["user_id"]),
                ),
            )

    def _apply_inventory_save_effect(
        self,
        connection,
        user: dict,
        resource: str,
        store_id: int,
        payload: dict,
    ) -> None:
        if resource != "stock-warnings":
            return
        item = self._inventory_item(
            connection, user, payload.get("materialName")
        )
        safety_quantity = self._inventory_quantity(
            payload.get("safetyQuantity"),
            "安全库存",
            allow_zero=True,
        )
        self._locked_inventory(
            connection, user, store_id, item["item_id"]
        )
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE inventory
                SET warn_qty=%s, version=version+1
                WHERE tenant_id=%s AND store_id=%s AND item_id=%s
                """,
                (
                    safety_quantity,
                    user["tenant_id"],
                    store_id,
                    item["item_id"],
                ),
            )

    def _apply_inventory_action_effect(
        self,
        connection,
        user: dict,
        resource: str,
        action: str,
        existing: dict,
        payload: dict,
        action_payload: dict,
    ) -> None:
        if resource == "stock-transfers" and action == "调入确认":
            if existing["status"] != "待收货":
                raise ApiError("请先完成调出确认，且不可重复调入", 409, 40900)
            source_store = self._inventory_store_by_name(
                connection, user, payload.get("sourceWarehouse"), "调出门店"
            )
            target_store = self._inventory_store_by_name(
                connection, user, payload.get("targetWarehouse"), "调入门店"
            )
            if source_store == target_store:
                raise ApiError("调出门店与调入门店不能相同")
            item = self._inventory_item(
                connection, user, payload.get("materialName")
            )
            quantity = self._inventory_quantity(
                payload.get("quantity"), "调拨数量"
            )
            source_inventory = self._locked_inventory(
                connection, user, source_store, item["item_id"]
            )
            self._locked_inventory(
                connection, user, target_store, item["item_id"]
            )
            if int(source_inventory["qty"] or 0) < quantity:
                raise ApiError("调出门店可用库存不足", 409, 40900)
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE inventory
                    SET qty=qty-%s, version=version+1
                    WHERE tenant_id=%s AND store_id=%s AND item_id=%s
                    """,
                    (
                        quantity,
                        user["tenant_id"],
                        source_store,
                        item["item_id"],
                    ),
                )
                cursor.execute(
                    """
                    UPDATE inventory
                    SET qty=qty+%s, version=version+1
                    WHERE tenant_id=%s AND store_id=%s AND item_id=%s
                    """,
                    (
                        quantity,
                        user["tenant_id"],
                        target_store,
                        item["item_id"],
                    ),
                )
            self._record_stock_movement(
                connection,
                user,
                source_store,
                item["item_id"],
                "调拨出库",
                -quantity,
                existing["business_no"],
            )
            self._record_stock_movement(
                connection,
                user,
                target_store,
                item["item_id"],
                "调拨入库",
                quantity,
                existing["business_no"],
            )
            return

        if resource == "stocktakes" and action == "审核":
            if action_payload.get("auditResult") == "审核不通过":
                return
            if existing["status"] != "待审核":
                raise ApiError("请先完成盘点，再执行审核过账", 409, 40900)
            item = self._inventory_item(
                connection, user, payload.get("materialName")
            )
            actual_quantity = self._inventory_quantity(
                payload.get("actualQuantity"),
                "实盘数量",
                allow_zero=True,
            )
            current = self._locked_inventory(
                connection,
                user,
                existing["store_id"],
                item["item_id"],
            )
            book_quantity = int(current["qty"] or 0)
            difference = actual_quantity - book_quantity
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE inventory
                    SET qty=%s, version=version+1
                    WHERE tenant_id=%s AND store_id=%s AND item_id=%s
                    """,
                    (
                        actual_quantity,
                        user["tenant_id"],
                        existing["store_id"],
                        item["item_id"],
                    ),
                )
            payload.update(
                {
                    "bookQuantity": book_quantity,
                    "differenceQuantity": difference,
                }
            )
            if difference:
                self._record_stock_movement(
                    connection,
                    user,
                    existing["store_id"],
                    item["item_id"],
                    "盘点调整",
                    difference,
                    existing["business_no"],
                )
            return

        if resource == "purchase-orders" and action == "到货登记":
            if existing["status"] != "已审核":
                raise ApiError("采购单审核通过后才能登记到货", 409, 40900)
            item = self._inventory_item(
                connection, user, payload.get("materialName")
            )
            quantity = self._inventory_quantity(
                payload.get("quantity"), "到货数量"
            )
            try:
                unit_price = Decimal(str(payload.get("unitPrice")))
            except Exception as exc:
                raise ApiError("采购单价必须是非负数字") from exc
            if unit_price < 0:
                raise ApiError("采购单价必须是非负数字")
            current = self._locked_inventory(
                connection,
                user,
                existing["store_id"],
                item["item_id"],
            )
            current_quantity = int(current["qty"] or 0)
            current_cost = Decimal(str(current["avg_cost"] or 0))
            resulting_quantity = current_quantity + quantity
            weighted_cost = (
                (
                    current_cost * current_quantity
                    + unit_price * quantity
                )
                / resulting_quantity
            ).quantize(Decimal("0.0001"))
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE inventory
                    SET qty=%s, avg_cost=%s, version=version+1
                    WHERE tenant_id=%s AND store_id=%s AND item_id=%s
                    """,
                    (
                        resulting_quantity,
                        weighted_cost,
                        user["tenant_id"],
                        existing["store_id"],
                        item["item_id"],
                    ),
                )
            self._record_stock_movement(
                connection,
                user,
                existing["store_id"],
                item["item_id"],
                "采购入库",
                quantity,
                existing["business_no"],
            )

    def _get_service_resource(
        self,
        connection,
        user: dict,
        resource: str,
        query: dict,
    ):
        self._require_any_permission(user, ("CUSTOMER.VIEW",))
        match = re.fullmatch(r"/(f\d{3})(?:/([^/]+))?", resource)
        if not match:
            raise ApiError("客服资源不存在", 404, 40400)
        feature_code, record_ref = match.groups()
        try:
            validate_resource("SERVICE", feature_code)
        except ValueError as exc:
            raise ApiError("客服资源不存在", 404, 40400) from exc

        scope_query = dict(query)
        if feature_code == "f043":
            scope_query.pop("storeId", None)
        rows = self._operational_module_rows(
            connection, user, "SERVICE", feature_code, scope_query
        )
        for row in rows:
            row.setdefault("recordNo", row.get("businessNo"))
            row.setdefault("externalStatus", "NOT_REQUIRED")
            row.setdefault("externalStatusLabel", "无需外部通道")

        if record_ref:
            record = next(
                (row for row in rows if str(row.get("id")) == record_ref),
                None,
            )
            if not record:
                raise ApiError("客服记录不存在或不属于当前门店", 404, 40400)
            record_id = parse_record_id(record_ref)
            logs = execute_all(
                connection,
                """
                SELECT event_id AS id, action_code AS action,
                       before_status AS beforeStatus,
                       after_status AS afterStatus,
                       detail_json AS detailJson,
                       created_at AS createdAt
                FROM mvp_audit_events
                WHERE tenant_id=%s AND aggregate_type='SERVICE_RECORD'
                  AND aggregate_id=%s
                ORDER BY event_id DESC
                LIMIT 100
                """,
                (user["tenant_id"], record_id),
            )
            for log in logs:
                detail = log.pop("detailJson", None)
                try:
                    detail = json.loads(detail or "{}")
                except (TypeError, json.JSONDecodeError):
                    detail = {}
                log["note"] = detail.get("note") or detail.get("resource") or ""
            return self._success({"record": record, "logs": logs})

        status = str(query.get("status") or "").strip()
        keyword = str(query.get("keyword") or "").strip().lower()
        if status:
            rows = [row for row in rows if str(row.get("status") or "") == status]
        if keyword:
            rows = [
                row
                for row in rows
                if keyword
                in " ".join(str(value or "") for value in row.values()).lower()
            ]
        return self._success(
            {"list": rows, "total": len(rows), "source": "mysql", "persisted": True}
        )

    def _post_service_resource(
        self,
        connection,
        user: dict,
        resource: str,
        body: dict,
    ):
        match = re.fullmatch(r"/(f\d{3})(?:/([^/]+)/action)?", resource)
        if not match:
            raise ApiError("客服资源不存在", 404, 40400)
        feature_code, record_ref = match.groups()
        try:
            validate_resource("SERVICE", feature_code)
        except ValueError as exc:
            raise ApiError("客服资源不存在", 404, 40400) from exc

        if not record_ref:
            payload = dict(body)
            if not str(payload.get("status") or "").strip():
                payload["status"] = {
                    "f005": "待回访",
                    "f043": "草稿",
                    "f084": "草稿",
                    "f094": "待接入",
                }[feature_code]
            if not payload.get("storeId") and not payload.get("store_id"):
                clause, params = self._store_clause(user, "store")
                origin_store = execute_one(
                    connection,
                    f"""
                    SELECT store.store_id
                    FROM stores store
                    WHERE store.tenant_id=%s AND {clause}
                    ORDER BY store.store_id
                    LIMIT 1
                    """,
                    [user["tenant_id"], *params],
                )
                if not origin_store:
                    raise ApiError("当前账号没有可用门店", 403, 40300)
                payload["storeId"] = origin_store["store_id"]
                if feature_code == "f043":
                    payload["scope"] = "全门店共享"
            return self._post_operational_module_record(
                connection, user, "SERVICE", feature_code, "save", payload
            )

        action = str(body.get("action") or "").strip().upper()
        record_id = parse_record_id(record_ref)
        existing = execute_one(
            connection,
            """
            SELECT store_id, status, payload_json FROM erp_operational_records
            WHERE record_id=%s AND tenant_id=%s
              AND module_code='SERVICE' AND resource_code=%s
              AND deleted_at IS NULL
            """,
            (record_id, user["tenant_id"], feature_code),
        )
        if not existing:
            raise ApiError("客服记录不存在或不属于当前门店", 404, 40400)
        self._allowed_store(user, existing["store_id"])
        # Deletion is a local record operation, not a customer-service state
        # transition.  Route it through the audited operational-record helper
        # so acceptance records and mistaken drafts can be rolled back without
        # teaching every service state machine a fake DELETE transition.
        if action in {"DELETE", "删除"}:
            return self._post_operational_module_record(
                connection,
                user,
                "SERVICE",
                feature_code,
                "action",
                {**body, "id": record_ref, "action": "删除"},
            )
        try:
            existing_payload = json.loads(existing.get("payload_json") or "{}")
        except (TypeError, json.JSONDecodeError):
            existing_payload = {}
        channel = str(existing_payload.get("channel") or "").strip()
        target_status, external_required = customer_service_transition(
            feature_code.upper(), existing["status"], action, channel
        )
        if action == "AI_REPLY":
            raise ApiError(
                "AI 客服未配置模型与知识检索服务，本次未生成或发送回复",
                503,
                50300,
            )

        payload = {**body, "id": record_ref, "status": target_status}
        if external_required:
            current_payload = dict(existing_payload)
            current_payload.update(
                {
                    "status": "待通道配置",
                    "externalStatus": "NOT_CONFIGURED",
                    "externalStatusLabel": "外部通道未配置",
                    "lastAction": action,
                    "lastActionAt": datetime.now().isoformat(timespec="seconds"),
                }
            )
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE erp_operational_records
                    SET status='待通道配置', payload_json=%s,
                        updated_by_user_id=%s, version=version+1
                    WHERE record_id=%s
                    """,
                    (compact_json(current_payload), user["user_id"], record_id),
                )
            self._audit(
                connection,
                user,
                "SERVICE_RECORD",
                record_id,
                action,
                existing["store_id"],
                existing["status"],
                "待通道配置",
                {"resource": feature_code, "note": body.get("note") or ""},
            )
            connection.commit()
            raise ApiError(
                "通知未发送；记录已标记为待通道配置",
                503,
                50300,
            )
        return self._post_operational_module_record(
            connection, user, "SERVICE", feature_code, "action", payload
        )

    def _operational_module_rows(
        self,
        connection,
        user: dict,
        module_code: str,
        resource: str,
        query: dict,
    ) -> list[dict]:
        try:
            validate_resource(module_code, resource)
        except ValueError as exc:
            raise ApiError("业务资源不存在", 404, 40400) from exc
        clause, params = self._scoped_store_clause(user, query, "record")
        rows = execute_all(
            connection,
            f"""
            SELECT record.record_id, record.store_id,
                   record.business_no, record.status,
                   record.payload_json, record.created_at,
                   record.updated_at, store.name AS store_name
            FROM erp_operational_records record
            JOIN stores store ON store.store_id=record.store_id
            WHERE record.tenant_id=%s
              AND record.module_code=%s
              AND record.resource_code=%s
              AND record.deleted_at IS NULL
              AND {clause}
            ORDER BY record.updated_at DESC, record.record_id DESC
            LIMIT 1000
            """,
            [
                user["tenant_id"],
                module_code,
                resource,
                *params,
            ],
        )
        result = []
        id_field = identifier_field(resource)
        for row in rows:
            try:
                payload = json.loads(row.get("payload_json") or "{}")
            except (TypeError, json.JSONDecodeError):
                payload = {}
            if not isinstance(payload, dict):
                payload = {}
            payload.update(
                {
                    "id": f"OP-{row['record_id']}",
                    "recordId": f"OP-{row['record_id']}",
                    "businessNo": row["business_no"],
                    "storeId": row["store_id"],
                    "store": row["store_name"],
                    "status": payload.get("status") or row["status"],
                    "createdAt": payload.get("createdAt")
                    or row["created_at"],
                    "updatedAt": row["updated_at"],
                    "recordSource": "本地MySQL",
                }
            )
            payload.setdefault(id_field, row["business_no"])
            result.append(payload)
        return result

    def _merge_operational_module_rows(
        self,
        connection,
        user: dict,
        module_code: str,
        resource: str,
        query: dict,
        data: dict,
    ) -> dict:
        durable_rows = self._operational_module_rows(
            connection, user, module_code, resource, query
        )
        existing = data.get("list") if isinstance(data, dict) else []
        existing = existing if isinstance(existing, list) else []
        return {
            **(data if isinstance(data, dict) else {}),
            "list": [*durable_rows, *existing],
            "total": len(durable_rows) + len(existing),
            "source": "mysql",
            "persisted": True,
        }

    def _post_operational_module_record(
        self,
        connection,
        user: dict,
        module_code: str,
        resource: str,
        operation: str,
        body: dict,
    ):
        try:
            validate_resource(module_code, resource)
        except ValueError as exc:
            raise ApiError("业务资源不存在", 404, 40400) from exc
        permission_map = {
            "RESEARCH": ("RECOVERY.VIEW", "CUSTOMER.VIEW"),
            "RECOVERY": ("RECOVERY.VIEW",),
            "CUSTOMER": ("CUSTOMER.VIEW",),
            "SERVICE": ("CUSTOMER.VIEW",),
            "NURSING": ("NURSING.VIEW",),
            "BABY": ("NURSING.VIEW",),
            "MATRON": ("MATRON.VIEW", "NURSING.VIEW"),
            "DIET": ("DIET.VIEW", "DIET.QUERY"),
            "INVENTORY": ("INVENTORY.VIEW", "LEGACY.WEB.N358.B18"),
            "BASIC": ("BASIC.VIEW", "SYSTEM.VIEW"),
            "REPORT": ("REPORT.VIEW",),
            "MALL": ("MALL.VIEW", "SYSTEM.VIEW", "LEGACY.WEB.N470.B18"),
        }
        self._require_any_permission(user, permission_map[module_code])
        if operation not in {"save", "action"}:
            raise ApiError("业务操作不存在", 404, 40400)

        write_store_id = None
        if operation == "save":
            write_store_id = self._resolve_write_store(
                connection, user, body
            )

        record_ref = body.get("recordId") or body.get("id")
        record_id = (
            parse_record_id(record_ref)
            if isinstance(record_ref, str) and record_ref.startswith("OP-")
            else None
        )
        if operation == "action" and not record_id:
            raise ApiError(
                "请选择本地已落库记录后执行状态操作",
                409,
                40900,
            )

        existing = None
        if record_id:
            scope_clause, scope_params = self._store_clause(user, "record")
            existing = execute_one(
                connection,
                f"""
                SELECT record.record_id, record.store_id,
                       record.business_no, record.status,
                       record.payload_json
                FROM erp_operational_records record
                WHERE record.record_id=%s
                  AND record.tenant_id=%s
                  AND record.module_code=%s
                  AND record.resource_code=%s
                  AND record.deleted_at IS NULL
                  AND {scope_clause}
                FOR UPDATE
                """,
                [
                    record_id,
                    user["tenant_id"],
                    module_code,
                    resource,
                    *scope_params,
                ],
            )
            if not existing:
                raise ApiError("业务记录不存在或不属于当前门店", 404, 40400)

        if operation == "action":
            action = str(body.get("action") or "").strip()
            if not action:
                raise ApiError("请选择业务操作")
            if action == "删除":
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE erp_operational_records
                        SET deleted_at=NOW(), updated_by_user_id=%s,
                            version=version+1
                        WHERE record_id=%s
                        """,
                        (user["user_id"], record_id),
                    )
                self._audit(
                    connection,
                    user,
                    f"{module_code}_RECORD",
                    record_id,
                    "DELETE",
                    existing["store_id"],
                    existing["status"],
                    "已删除",
                    {"resource": resource},
                )
                connection.commit()
                return self._success(
                    {"persisted": True, "recordId": f"OP-{record_id}"}
                )
            try:
                current_payload = json.loads(existing["payload_json"] or "{}")
            except (TypeError, json.JSONDecodeError):
                current_payload = {}
            if not isinstance(current_payload, dict):
                current_payload = {}
            if module_code == "INVENTORY":
                self._apply_inventory_action_effect(
                    connection,
                    user,
                    resource,
                    action,
                    existing,
                    current_payload,
                    body,
                )
            patch, status = apply_action(resource, action, body)
            current_payload.update(patch)
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE erp_operational_records
                    SET status=%s, payload_json=%s,
                        updated_by_user_id=%s, version=version+1
                    WHERE record_id=%s
                    """,
                    (
                        status,
                        compact_json(current_payload),
                        user["user_id"],
                        record_id,
                    ),
                )
            self._audit(
                connection,
                user,
                f"{module_code}_RECORD",
                record_id,
                action,
                existing["store_id"],
                existing["status"],
                status,
                {"resource": resource, "note": body.get("note") or ""},
            )
            connection.commit()
            return self._success(
                {
                    "persisted": True,
                    "recordId": f"OP-{record_id}",
                    "businessNo": existing["business_no"],
                    "status": status,
                }
            )

        payload = clean_payload(body)
        if not payload:
            raise ApiError("请填写业务记录内容")
        status = str(
            payload.get("status")
            or payload.get("orderStatus")
            or payload.get("stocktakeStatus")
            or payload.get("auditStatus")
            or "草稿"
        )
        if existing:
            if operation == "save" and write_store_id != existing["store_id"]:
                raise ApiError(
                    "编辑记录必须选择其所属门店，不能跨门店变更交易归属",
                    403,
                    40300,
                )
            try:
                merged = json.loads(existing["payload_json"] or "{}")
            except (TypeError, json.JSONDecodeError):
                merged = {}
            merged.update(payload)
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE erp_operational_records
                    SET status=%s, payload_json=%s,
                        updated_by_user_id=%s, version=version+1
                    WHERE record_id=%s
                    """,
                    (
                        status,
                        compact_json(merged),
                        user["user_id"],
                        record_id,
                    ),
                )
            store_id = existing["store_id"]
            generated_no = existing["business_no"]
            before_status = existing["status"]
            action_code = "UPDATE"
            record_payload = merged
        else:
            store_id = write_store_id
            pending_no = f"PENDING-{secrets.token_hex(12)}"
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO erp_operational_records(
                      tenant_id,store_id,module_code,resource_code,
                      business_no,status,payload_json,
                      created_by_user_id,updated_by_user_id
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        user["tenant_id"],
                        store_id,
                        module_code,
                        resource,
                        pending_no,
                        status,
                        compact_json(payload),
                        user["user_id"],
                        user["user_id"],
                    ),
                )
                record_id = cursor.lastrowid
                generated_no = business_no(
                    module_code, resource, record_id
                )
                cursor.execute(
                    """
                    UPDATE erp_operational_records
                    SET business_no=%s
                    WHERE record_id=%s
                    """,
                    (generated_no, record_id),
                )
            before_status = None
            action_code = "CREATE"
            record_payload = payload
        if module_code == "DIET":
            self._validate_diet_room_assignment(
                connection, user, resource, store_id, record_payload
            )
        if module_code == "INVENTORY":
            self._apply_inventory_save_effect(
                connection,
                user,
                resource,
                store_id,
                payload,
            )
        self._audit(
            connection,
            user,
            f"{module_code}_RECORD",
            record_id,
            action_code,
            store_id,
            before_status,
            status,
            {"resource": resource, "businessNo": generated_no},
        )
        connection.commit()
        return self._success(
            {
                "persisted": True,
                "recordId": f"OP-{record_id}",
                "businessNo": generated_no,
                "status": status,
            }
        )

    def _diet_store_id_from_value(
        self, connection, user: dict, source: dict
    ) -> int | None:
        requested = self._requested_store_id(user, source)
        store_name = str(source.get("store") or "").strip()
        if not store_name:
            return requested
        row = execute_one(
            connection,
            """
            SELECT store_id FROM stores
            WHERE tenant_id=%s AND name=%s
            """,
            (user["tenant_id"], store_name),
        )
        if not row:
            raise ApiError("所选门店不存在", 400, 40000)
        store_id = self._allowed_store(user, row["store_id"])
        if requested is not None and requested != store_id:
            raise ApiError("所选门店与当前页面门店不一致", 403, 40300)
        return store_id

    def _get_diet_room_options(
        self, connection, user: dict, query: dict
    ):
        self._require_any_permission(user, ("DIET.VIEW", "DIET.QUERY"))
        store_id = self._diet_store_id_from_value(connection, user, query)
        if store_id is None:
            raise ApiError("请先选择具体门店后加载房间", 400, 40000)
        rows = execute_all(
            connection,
            """
            SELECT room.room_no AS room, booking.store_id AS storeId,
                   store.name AS store, customer.name AS customerName,
                   booking.booking_id AS bookingId
            FROM room_bookings booking
            JOIN rooms room ON room.room_id=booking.room_id
            JOIN stores store ON store.store_id=booking.store_id
            JOIN customers customer ON customer.customer_id=booking.customer_id
            WHERE booking.tenant_id=%s AND booking.store_id=%s
              AND booking.deleted_at IS NULL AND booking.status='已入住'
            ORDER BY room.floor, room.layout_order, room.room_no
            """,
            (user["tenant_id"], store_id),
        )
        return self._success({"list": rows, "total": len(rows)})

    def _get_store_reference_options(
        self, connection, user: dict, module_code: str, query: dict
    ):
        """Return only the selected store's transaction reference values."""
        permissions = {
            "NURSING": ("NURSING.VIEW",),
            "DIET": ("DIET.VIEW", "DIET.QUERY"),
            "INVENTORY": ("INVENTORY.VIEW", "LEGACY.WEB.N358.B18"),
        }
        self._require_any_permission(user, permissions[module_code])
        store_id = self._requested_store_id(user, query)
        if str(query.get("store") or "").strip():
            row = execute_one(
                connection,
                "SELECT store_id FROM stores WHERE tenant_id=%s AND name=%s",
                (user["tenant_id"], str(query.get("store")).strip()),
            )
            if not row:
                raise ApiError("所选门店不存在", 400, 40000)
            named_store_id = self._allowed_store(user, row["store_id"])
            if store_id is not None and store_id != named_store_id:
                raise ApiError("所选门店与当前页面门店不一致", 403, 40300)
            store_id = named_store_id
        if store_id is None:
            raise ApiError(
                "请先选择具体门店后加载客户、房间和业务选项；全部门店仅可汇总查询",
                400,
                40000,
            )
        customers = execute_all(
            connection,
            """
            SELECT DISTINCT customer.customer_id AS id, customer.name,
                   room.room_no AS room
            FROM room_bookings booking
            JOIN customers customer ON customer.customer_id=booking.customer_id
            JOIN rooms room ON room.room_id=booking.room_id
            WHERE booking.tenant_id=%s AND booking.store_id=%s
              AND booking.deleted_at IS NULL AND booking.status='已入住'
            ORDER BY room.floor, room.layout_order, customer.name
            """,
            (user["tenant_id"], store_id),
        )
        rooms = execute_all(
            connection,
            """
            SELECT room.room_id AS id, room.room_no AS room,
                   room.room_type AS roomType
            FROM rooms room
            WHERE room.tenant_id=%s AND room.store_id=%s
              AND room.deleted_at IS NULL
            ORDER BY room.floor, room.layout_order, room.room_no
            """,
            (user["tenant_id"], store_id),
        )
        result = {"storeId": store_id, "customers": customers, "rooms": rooms}
        if module_code == "DIET":
            result["dishes"] = execute_all(
                connection,
                """
                SELECT dish_id AS id, name
                FROM meal_dishes
                WHERE tenant_id=%s AND deleted_at IS NULL
                  AND status IN ('启用','ACTIVE')
                ORDER BY name
                LIMIT 500
                """,
                (user["tenant_id"],),
            )
            result["mealPlans"] = execute_all(
                connection,
                """
                SELECT plan_id AS id, name
                FROM meal_plans
                WHERE tenant_id=%s AND store_id=%s AND deleted_at IS NULL
                ORDER BY name
                LIMIT 500
                """,
                (user["tenant_id"], store_id),
            )
        if module_code == "INVENTORY":
            result["materials"] = execute_all(
                connection,
                """
                SELECT item.item_id AS id, item.name, item.unit
                FROM inventory inv
                JOIN items item ON item.item_id=inv.item_id
                 AND item.tenant_id=inv.tenant_id
                WHERE inv.tenant_id=%s AND inv.store_id=%s
                ORDER BY item.name
                LIMIT 1000
                """,
                (user["tenant_id"], store_id),
            )
            result["suppliers"] = execute_all(
                connection,
                """
                SELECT DISTINCT purchase.supplier AS name
                FROM purchase_orders purchase
                WHERE purchase.tenant_id=%s AND purchase.store_id=%s
                  AND purchase.deleted_at IS NULL
                  AND purchase.supplier IS NOT NULL AND purchase.supplier<>''
                ORDER BY purchase.supplier
                LIMIT 500
                """,
                (user["tenant_id"], store_id),
            )
        return self._success(result)

    def _validate_diet_room_assignment(
        self,
        connection,
        user: dict,
        resource: str,
        store_id: int,
        payload: dict,
    ) -> None:
        if resource not in {
            "customer-meal-plans", "meal-orders", "guest-meal-supply"
        }:
            return
        room = str(payload.get("room") or "").strip()
        requires_room = (
            resource == "customer-meal-plans"
            or payload.get("customerType") == "入住客户"
        )
        if requires_room and not room:
            raise ApiError("请选择当前门店在住客户房间", 400, 40000)
        if not room:
            return
        row = execute_one(
            connection,
            """
            SELECT customer.name AS customer_name
            FROM room_bookings booking
            JOIN rooms room ON room.room_id=booking.room_id
            JOIN customers customer ON customer.customer_id=booking.customer_id
            WHERE booking.tenant_id=%s AND booking.store_id=%s
              AND booking.deleted_at IS NULL AND booking.status='已入住'
              AND room.room_no=%s
            LIMIT 1
            """,
            (user["tenant_id"], store_id, room),
        )
        if not row:
            raise ApiError(
                "所选房间不属于当前门店，或当前没有入住客户",
                400,
                40000,
            )
        customer_name = str(payload.get("customerName") or "").strip()
        if customer_name and customer_name != row["customer_name"]:
            raise ApiError(
                "所选房间的入住客户与填写客户不一致，请从房间列表重新选择",
                400,
                40000,
            )
    def _asset_store_rows(self, connection, user: dict, alias: str, column: str = "store_id") -> tuple[str, list]:
        clause, params = self._store_clause(user, alias)
        if column != "store_id":
            clause = clause.replace(f"{alias}.store_id", f"{alias}.{column}")
        return clause, params

    def _asset_customer(self, connection, user: dict, customer_id: object, store_id: int) -> dict:
        try:
            normalized = int(customer_id)
        except (TypeError, ValueError) as exc:
            raise ApiError("请选择当前门店的会员", 400, 40000) from exc
        row = execute_one(
            connection,
            """SELECT customer_id, name, phone FROM customers
               WHERE tenant_id=%s AND customer_id=%s
                  AND deleted_at IS NULL""",
            (user["tenant_id"], normalized),
        )
        if not row:
            raise ApiError("会员不存在或已停用", 400, 40000)
        return row

    def _get_member_asset_resource(self, connection, user: dict, resource: str, query: dict):
        if resource == "/options":
            customers = execute_all(
                connection,
                f"""SELECT c.customer_id AS id, c.name, c.phone, s.name AS store
                    FROM customers c JOIN stores s ON s.store_id=c.store_id
                    WHERE c.tenant_id=%s AND c.deleted_at IS NULL
                    ORDER BY c.customer_id DESC LIMIT 500""",
                [user["tenant_id"]],
            )
            for customer in customers:
                customer["phone"] = self._masked_phone(user, customer.get("phone"))
            return self._success({"customers": customers, "cardTypes": ["次卡", "储值卡"], "cardPackages": []})
        if resource == "/overview":
            clause, params = self._asset_store_rows(connection, user, "a", "issue_store_id")
            cards = execute_one(
                connection,
                f"""SELECT COUNT(*) AS activeCards, COALESCE(SUM(balance),0) AS cardBalance
                    FROM member_asset_cards a
                    JOIN customers c ON c.customer_id=a.customer_id
                    WHERE a.tenant_id=%s AND c.deleted_at IS NULL
                      AND a.status='正常' AND a.deleted_at IS NULL AND {clause}""",
                [user["tenant_id"], *params],
            ) or {}
            accounts = execute_one(
                connection,
                f"""SELECT COALESCE(SUM(balance),0) AS accountBalance
                    FROM member_asset_accounts a
                    JOIN customers c ON c.customer_id=a.customer_id
                    WHERE a.tenant_id=%s AND c.deleted_at IS NULL
                      AND a.status='正常'""",
                [user["tenant_id"]],
            ) or {}
            return self._success({**cards, **accounts})
        if resource == "/cards":
            clause, params = self._asset_store_rows(connection, user, "a", "issue_store_id")
            rows = execute_all(
                connection,
                f"""SELECT a.card_id AS id, a.card_no, c.name AS customer_name,
                    a.card_name, a.card_type, a.balance, a.total_count,
                    a.remaining_count, a.valid_to,
                    a.status, s.name AS store_name
                    FROM member_asset_cards a
                    JOIN customers c ON c.customer_id=a.customer_id
                    JOIN stores s ON s.store_id=a.issue_store_id
                    WHERE a.tenant_id=%s AND c.deleted_at IS NULL
                      AND a.deleted_at IS NULL AND {clause}
                    ORDER BY a.card_id DESC LIMIT 1000""",
                [user["tenant_id"], *params],
            )
            return self._success({"list": rows, "total": len(rows)})
        if resource == "/accounts":
            rows = execute_all(
                connection,
                f"""SELECT a.account_id AS id, a.account_no, c.name AS customer_name,
                    c.phone AS mobile, s.name AS store_name, a.balance,
                    a.frozen_amount, a.points,
                    a.status
                    FROM member_asset_accounts a
                    JOIN customers c ON c.customer_id=a.customer_id
                    JOIN stores s ON s.store_id=c.store_id
                    WHERE a.tenant_id=%s AND c.deleted_at IS NULL
                    ORDER BY a.account_id DESC LIMIT 1000""",
                [user["tenant_id"]],
            )
            for row in rows:
                row["mobile"] = self._masked_phone(user, row.get("mobile"))
            return self._success({"list": rows, "total": len(rows)})
        raise ApiError("会员资产资源不存在", 404, 40400)

    def _asset_amount(self, value: object) -> Decimal:
        try:
            amount = Decimal(str(value))
        except Exception as exc:
            raise ApiError("金额必须为大于 0 的数字", 400, 40000) from exc
        if amount <= 0 or amount > Decimal("99999999.99"):
            raise ApiError("金额必须在 0 到 99999999.99 之间", 400, 40000)
        return amount.quantize(Decimal("0.0001"))

    def _asset_write_store(self, user: dict, body: dict) -> int:
        store_id = self._require_selected_write_store(user, body)
        if not store_id:
            raise ApiError("请先选择具体门店再办理会员资产交易", 400, 40000)
        return store_id

    def _post_member_asset_resource(self, connection, user: dict, resource: str, body: dict):
        store_id = self._asset_write_store(user, body)
        if resource == "/cards":
            return self._create_member_asset_card(connection, user, body, store_id)
        match = re.fullmatch(r"/(cards|accounts)/(\d+)/(consume|top-up|deduct)", resource)
        if not match:
            raise ApiError("会员资产写入资源不存在", 404, 40400)
        collection, record_id, action = match.groups()
        if collection == "cards" and action == "consume":
            return self._consume_member_asset_card(connection, user, int(record_id), body, store_id)
        if collection == "accounts" and action in {"top-up", "deduct"}:
            return self._adjust_member_asset_account(connection, user, int(record_id), action, body, store_id)
        raise ApiError("当前会员资产操作不支持", 400, 40000)

    def _create_member_asset_card(self, connection, user: dict, body: dict, store_id: int):
        customer = self._asset_customer(connection, user, body.get("customerId"), store_id)
        card_type = str(body.get("cardType") or "").strip()
        if card_type not in {"次卡", "储值卡"}:
            raise ApiError("卡类型仅支持次卡或储值卡", 400, 40000)
        valid_to = str(body.get("validTo") or "").strip()
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", valid_to):
            raise ApiError("请填写有效期", 400, 40000)
        amount = self._asset_amount(body.get("amount"))
        count = int(body.get("totalCount") or 0)
        if card_type == "次卡" and (count < 1 or count > 100000):
            raise ApiError("次卡总次数必须在 1 到 100000 之间", 400, 40000)
        if card_type == "储值卡":
            count = 0
        card_no = self._sales_number("ASSET")
        card_name = str(body.get("cardName") or body.get("packageName") or f"{card_type}资产卡").strip()[:128]
        with connection.cursor() as cursor:
            cursor.execute(
                """INSERT IGNORE INTO member_asset_accounts(tenant_id,customer_id,account_no,status)
                   VALUES(%s,%s,%s,'正常')""",
                (user["tenant_id"], customer["customer_id"], self._sales_number("ACCOUNT")),
            )
            cursor.execute(
                """INSERT INTO member_asset_cards(tenant_id,issue_store_id,customer_id,card_no,card_name,card_type,issue_amount,balance,total_count,remaining_count,valid_to,status,created_by_user_id)
                   VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'正常',%s)""",
                (user["tenant_id"], store_id, customer["customer_id"], card_no, card_name, card_type, amount, amount if card_type == "储值卡" else 0, count, count, valid_to, user["user_id"]),
            )
            card_id = cursor.lastrowid
            cursor.execute(
                """INSERT INTO member_asset_transactions(tenant_id,store_id,customer_id,card_id,transaction_no,transaction_type,amount,count_delta,balance_after,remaining_count_after,remark,operator_user_id)
                   VALUES(%s,%s,%s,%s,%s,'ISSUE',%s,%s,%s,%s,%s,%s)""",
                (user["tenant_id"], store_id, customer["customer_id"], card_id, self._sales_number("ASSET-TX"), amount, count, amount if card_type == "储值卡" else 0, count, "发卡", user["user_id"]),
            )
        self._audit(connection, user, "member_asset_card", card_id, "CREATE", store_id, None, "正常", {"cardNo": card_no, "cardType": card_type})
        connection.commit()
        return self._success({"id": card_id, "cardNo": card_no, "saved": True})

    def _consume_member_asset_card(self, connection, user: dict, card_id: int, body: dict, store_id: int):
        row = execute_one(connection, "SELECT * FROM member_asset_cards WHERE card_id=%s AND tenant_id=%s AND deleted_at IS NULL FOR UPDATE", (card_id, user["tenant_id"]))
        if not row or row["status"] != "正常":
            raise ApiError("资产卡不存在或已停用", 404, 40400)
        amount = self._asset_amount(body.get("amount")) if row["card_type"] == "储值卡" else Decimal("0")
        count = int(body.get("count") or 1) if row["card_type"] == "次卡" else 0
        if count < 1 or count > int(row["remaining_count"]):
            raise ApiError("核销次数超过剩余次数", 400, 40000)
        if amount > Decimal(str(row["balance"])):
            raise ApiError("扣款金额超过可用余额", 400, 40000)
        balance = Decimal(str(row["balance"])) - amount
        remaining = int(row["remaining_count"]) - count
        with connection.cursor() as cursor:
            cursor.execute("UPDATE member_asset_cards SET balance=%s, remaining_count=%s WHERE card_id=%s", (balance, remaining, card_id))
            cursor.execute("""INSERT INTO member_asset_transactions(tenant_id,store_id,customer_id,card_id,transaction_no,transaction_type,amount,count_delta,balance_after,remaining_count_after,remark,operator_user_id) VALUES(%s,%s,%s,%s,%s,'CONSUME',%s,%s,%s,%s,%s,%s)""", (user["tenant_id"], store_id, row["customer_id"], card_id, self._sales_number("ASSET-TX"), -amount, -count, balance, remaining, "资产核销", user["user_id"]))
        self._audit(connection, user, "member_asset_card", card_id, "CONSUME", store_id, None, None, {"amount": str(amount), "count": count})
        connection.commit()
        return self._success({"id": card_id, "balance": balance, "remainingCount": remaining})

    def _adjust_member_asset_account(self, connection, user: dict, account_id: int, action: str, body: dict, store_id: int):
        row = execute_one(connection, "SELECT * FROM member_asset_accounts WHERE account_id=%s AND tenant_id=%s FOR UPDATE", (account_id, user["tenant_id"]))
        if not row or row["status"] != "正常":
            raise ApiError("余额账户不存在或已停用", 404, 40400)
        amount = self._asset_amount(body.get("amount"))
        before = Decimal(str(row["balance"]))
        if action == "deduct" and amount > before:
            raise ApiError("扣款金额超过可用余额", 400, 40000)
        balance = before + amount if action == "top-up" else before - amount
        with connection.cursor() as cursor:
            cursor.execute("UPDATE member_asset_accounts SET balance=%s WHERE account_id=%s", (balance, account_id))
            cursor.execute("""INSERT INTO member_asset_transactions(tenant_id,store_id,customer_id,account_id,transaction_no,transaction_type,amount,balance_after,remark,operator_user_id) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", (user["tenant_id"], store_id, row["customer_id"], account_id, self._sales_number("ASSET-TX"), "TOP_UP" if action == "top-up" else "DEDUCT", amount if action == "top-up" else -amount, balance, "余额充值" if action == "top-up" else "余额扣款", user["user_id"]))
        self._audit(connection, user, "member_asset_account", account_id, action.upper(), store_id, str(before), str(balance), {})
        connection.commit()
        return self._success({"id": account_id, "balance": balance})

    def _get_diet_module_data(
        self, connection, user: dict, resource: str, query: dict
    ):
        self._require_any_permission(user, ("DIET.VIEW", "DIET.QUERY"))
        supported = {
            "customer-meal-plans",
            "dishes",
            "diet-packages",
            "diet-statistics",
            "delivery-statistics",
            "nutrition-soups",
            "nutrition-soup-statistics",
            "guest-meal-supply",
            "ingredient-purchases",
            "diet-sales",
            "meal-orders",
            "meal-cards",
            "meal-card-consumption-report",
        }
        if resource not in supported:
            raise ApiError("膳食资源不存在", 404, 40400)
        clause, params = self._scoped_store_clause(user, query, "dp")
        if resource == "customer-meal-plans":
            rows = execute_all(
                connection,
                f"""
                SELECT dp.plan_id AS id, dp.meal_date AS mealDate,
                       room.room_no AS room, c.name AS customerName,
                       s.name AS store, dp.meal_type AS mealType,
                       dp.dishes_json AS dishName, 1 AS quantity,
                       c.remark AS taboo, NULL AS dietitian,
                       dp.status, NULL AS deliveryTime,
                       dp.delivery_status AS remark
                FROM diet_plans dp
                LEFT JOIN customers c ON c.customer_id=dp.customer_id
                LEFT JOIN stores s ON s.store_id=dp.store_id
                LEFT JOIN room_bookings rb
                  ON rb.customer_id=dp.customer_id
                 AND rb.tenant_id=dp.tenant_id
                 AND rb.deleted_at IS NULL
                 AND rb.status IN ('已订房','已入住')
                LEFT JOIN rooms room ON room.room_id=rb.room_id
                WHERE dp.tenant_id=%s AND dp.deleted_at IS NULL
                  AND {clause}
                ORDER BY dp.meal_date DESC, dp.plan_id DESC
                LIMIT 1000
                """,
                [user["tenant_id"], *params],
            )
        elif resource == "dishes":
            rows = execute_all(
                connection,
                """
                SELECT dish_id AS id,
                       CONCAT('DISH-',LPAD(dish_id,6,'0')) AS dishCode,
                       name AS dishName, category AS dishCategory,
                       NULL AS mealType, NULL AS ingredients,
                       nutrients AS nutrition, NULL AS tabooTag,
                       '份' AS unit, 0 AS standardPrice,
                       '租户共享餐库' AS store,
                       status AS enabled, NULL AS creator,
                       created_at AS createdAt
                FROM meal_dishes
                WHERE tenant_id=%s AND deleted_at IS NULL
                ORDER BY dish_id DESC
                LIMIT 1000
                """,
                (user["tenant_id"],),
            )
        elif resource == "diet-packages":
            package_clause, package_params = self._scoped_store_clause(
                user, query, "mp"
            )
            rows = execute_all(
                connection,
                f"""
                SELECT mp.plan_id AS id,
                       CONCAT('DP-',LPAD(mp.plan_id,6,'0')) AS packageCode,
                       mp.name AS packageName, s.name AS store,
                       mp.days AS cycleDays, '每日三餐三加餐' AS mealStandard,
                       0 AS packageAmount, '入住客户' AS customerType,
                       NULL AS effectiveDate, NULL AS expiryDate,
                       mp.status AS enabled, NULL AS creator,
                       mp.created_at AS createdAt
                FROM meal_plans mp
                LEFT JOIN stores s ON s.store_id=mp.store_id
                WHERE mp.tenant_id=%s AND mp.deleted_at IS NULL
                  AND {package_clause}
                ORDER BY mp.plan_id DESC
                LIMIT 1000
                """,
                [user["tenant_id"], *package_params],
            )
        elif resource in {"diet-statistics", "delivery-statistics"}:
            rows = execute_all(
                connection,
                f"""
                SELECT MIN(dp.plan_id) AS id, dp.meal_date AS statDate,
                       dp.meal_date AS deliveryDate, s.name AS store,
                       dp.meal_type AS mealType,
                       COUNT(*) AS plannedCount,
                       SUM(dp.status IN ('备餐中','配送中','已签收'))
                         AS preparedCount,
                       SUM(dp.delivery_status IN ('配送中','已签收'))
                         AS deliveredCount,
                       SUM(dp.delivery_status='已签收') AS signedCount,
                       SUM(dp.delivery_status='已退餐') AS returnedCount,
                       SUM(dp.delivery_status='配送异常') AS timeoutCount,
                       COUNT(*) AS taskCount,
                       COUNT(DISTINCT dp.customer_id) AS customerCount,
                       CONCAT(
                         ROUND(
                           IF(COUNT(*)=0,0,
                             SUM(dp.delivery_status='已签收')/COUNT(*)*100
                           ),1
                         ),'%%'
                       ) AS completionRate,
                       NULL AS deliveryStaff, NULL AS firstDeliveryAt,
                       NULL AS lastSignedAt, NULL AS remark
                FROM diet_plans dp
                LEFT JOIN stores s ON s.store_id=dp.store_id
                WHERE dp.tenant_id=%s AND dp.deleted_at IS NULL
                  AND {clause}
                GROUP BY dp.meal_date,dp.store_id,dp.meal_type
                ORDER BY dp.meal_date DESC,dp.meal_type
                LIMIT 1000
                """,
                [user["tenant_id"], *params],
            )
        else:
            rows = []
        data = self._merge_operational_module_rows(
            connection,
            user,
            "DIET",
            resource,
            query,
            {"list": rows, "total": len(rows), "source": "mysql"},
        )
        return self._success(data)

    def _catalog_date(
        self,
        value,
        label: str,
        default: date | None = None,
        required: bool = False,
    ) -> date | None:
        raw = str(value or "").strip()
        if not raw:
            if required and default is None:
                raise ApiError(f"{label}不能为空")
            return default
        try:
            return date.fromisoformat(raw[:10])
        except ValueError as exc:
            raise ApiError(f"{label}日期格式不正确") from exc

    def _catalog_service_projects(
        self, connection, user: dict, query: dict
    ) -> list:
        params = [user["tenant_id"]]
        conditions = ["sp.tenant_id=%s", "sp.deleted_at IS NULL"]
        target_module = str(query.get("targetModule") or "").strip()
        if target_module:
            conditions.append("sp.target_module=%s")
            params.append(target_module)
        status = str(query.get("status") or "").strip()
        if status:
            conditions.append("sp.status=%s")
            params.append(status)
        return execute_all(
            connection,
            f"""
            SELECT sp.service_project_id AS id,
                   sp.project_code AS projectCode,
                   sp.project_name AS projectName,
                   sp.target_module AS targetModule,
                   sp.project_category AS projectCategory,
                   sp.unit,sp.status,sp.note,sp.version,
                   sp.created_at AS createdAt,
                   sp.updated_at AS updatedAt
            FROM service_projects sp
            WHERE {' AND '.join(conditions)}
            ORDER BY sp.target_module,sp.project_category,
                     sp.project_name,sp.service_project_id
            """,
            params,
        )

    def _catalog_package_rows(
        self,
        connection,
        user: dict,
        query: dict,
        version_id: int | None = None,
    ) -> list:
        params = [user["tenant_id"]]
        conditions = ["pp.tenant_id=%s", "pp.deleted_at IS NULL"]
        if version_id:
            conditions.append("pv.package_version_id=%s")
            params.append(version_id)
        status = str(query.get("status") or "ACTIVE").strip().upper()
        if status != "ALL":
            if status not in PACKAGE_VERSION_STATUSES:
                raise ApiError("套餐版本状态不正确")
            conditions.append("pv.version_status=%s")
            params.append(status)
        package_id = int(query.get("packageId") or 0)
        if package_id:
            conditions.append("pp.package_id=%s")
            params.append(package_id)
        versions = execute_all(
            connection,
            f"""
            SELECT pp.package_id AS packageId,
                   pp.package_code AS packageCode,
                   pp.package_name AS packageName,
                   pp.package_category AS packageCategory,
                   pp.status AS packageStatus,
                   pv.package_version_id AS packageVersionId,
                   pv.version_no AS versionNo,
                   pv.effective_from AS effectiveFrom,
                   pv.effective_to AS effectiveTo,
                   pv.version_status AS versionStatus,
                   pv.source_type AS sourceType,
                   pv.evidence_note AS evidenceNote,
                   pv.published_at AS publishedAt,
                   pv.created_at AS createdAt,
                   pv.updated_at AS updatedAt
            FROM package_products pp
            JOIN package_versions pv ON pv.package_id=pp.package_id
            WHERE {' AND '.join(conditions)}
            ORDER BY pp.sort_order,pp.package_id,
                     pv.effective_from DESC,pv.package_version_id DESC
            LIMIT 500
            """,
            params,
        )
        requested_store = int(query.get("storeId") or 0)
        if requested_store:
            self._allowed_store(user, requested_store)
        requested_room_type = int(query.get("roomTypeId") or 0)
        requested_days = int(query.get("days") or 0)
        for item in versions:
            price_params = [
                user["tenant_id"],
                item["packageVersionId"],
            ]
            price_conditions = [
                "pr.tenant_id=%s",
                "pr.package_version_id=%s",
            ]
            clause, store_params = self._store_clause(user, "pr")
            price_conditions.append(clause)
            price_params.extend(store_params)
            if requested_store:
                price_conditions.append("pr.store_id=%s")
                price_params.append(requested_store)
            if requested_room_type:
                price_conditions.append("pr.room_type_id=%s")
                price_params.append(requested_room_type)
            if requested_days:
                price_conditions.append("pr.stay_days=%s")
                price_params.append(requested_days)
            if item["versionStatus"] == "ACTIVE":
                price_conditions.extend(
                    [
                        "pr.status='ACTIVE'",
                        "pr.effective_from<=CURDATE()",
                        (
                            "(pr.effective_to IS NULL "
                            "OR pr.effective_to>=CURDATE())"
                        ),
                    ]
                )
            item["priceRules"] = execute_all(
                connection,
                f"""
                SELECT pr.price_rule_id AS priceRuleId,
                       pr.store_id AS storeId,s.name AS store,
                       pr.room_type_id AS roomTypeId,
                       rt.type_code AS roomTypeCode,
                       rt.name AS roomType,
                       pr.stay_days AS stayDays,
                       pr.reference_amount AS referenceAmount,
                       COALESCE(profile.original_amount,pr.reference_amount) AS originalPrice,
                       COALESCE(profile.activity_amount,pr.reference_amount) AS activityPrice,
                       COALESCE(profile.deal_amount,pr.reference_amount) AS dealPrice,
                       pr.currency_code AS currencyCode,
                       pr.effective_from AS effectiveFrom,
                       pr.effective_to AS effectiveTo,
                       pr.status
                FROM package_price_rules pr
                JOIN stores s ON s.store_id=pr.store_id
                JOIN room_types rt ON rt.room_type_id=pr.room_type_id
                LEFT JOIN package_price_profiles profile
                  ON profile.price_rule_id=pr.price_rule_id
                WHERE {' AND '.join(price_conditions)}
                ORDER BY s.sort_weight DESC,s.store_id,rt.sort_order,
                         pr.stay_days,pr.effective_from
                """,
                price_params,
            )
            item["entitlementRules"] = execute_all(
                connection,
                """
                SELECT er.entitlement_rule_id AS entitlementRuleId,
                       er.service_project_id AS serviceProjectId,
                       sp.project_code AS projectCode,
                       sp.project_name AS projectName,
                       sp.target_module AS targetModule,
                       sp.project_category AS projectCategory,
                       sp.unit,er.entitlement_mode AS entitlementMode,
                       er.granted_quantity AS grantedQuantity,
                       er.unlimited_flag AS unlimited,
                       er.per_item_limit AS perItemLimit,
                       er.choice_group_code AS choiceGroupCode,
                       er.valid_days AS validDays,
                       er.status,er.sort_order AS sortOrder,er.note
                FROM package_entitlement_rules er
                JOIN service_projects sp
                  ON sp.service_project_id=er.service_project_id
                WHERE er.tenant_id=%s AND er.package_version_id=%s
                ORDER BY er.sort_order,er.entitlement_rule_id
                """,
                (user["tenant_id"], item["packageVersionId"]),
            )
        return versions

    def _catalog_room_types(self, connection, user: dict) -> list:
        return execute_all(
            connection,
            """
            SELECT room_type_id AS id,type_code AS typeCode,name,
                   layout_name AS layoutName,bedrooms,
                   living_rooms AS livingRooms,bed_type AS bedType,
                   package_name AS packageName,status
            FROM room_types
            WHERE tenant_id=%s AND status='启用'
            ORDER BY sort_order,room_type_id
            """,
            (user["tenant_id"],),
        )

    def _get_catalog_resource(
        self, connection, user: dict, resource: str, query: dict
    ):
        self._require_sales_access(user, "packages")
        if resource == "/service-projects":
            rows = self._catalog_service_projects(
                connection, user, query or {}
            )
            return self._success({"list": rows, "total": len(rows)})
        if resource == "/packages":
            rows = self._catalog_package_rows(
                connection, user, query or {}
            )
            return self._success(
                {
                    "list": rows,
                    "total": len(rows),
                    "stores": self._sales_store_options(connection, user),
                    "roomTypes": self._catalog_room_types(connection, user),
                }
            )
        match = re.fullmatch(r"/packages/(\d+)", resource)
        if match:
            rows = self._catalog_package_rows(
                connection,
                user,
                {"status": "ALL"},
                int(match.group(1)),
            )
            if not rows:
                raise ApiError("套餐版本不存在", 404, 40400)
            return self._success(rows[0])
        raise ApiError("套餐目录资源不存在", 404, 40400)

    def _save_catalog_service_project(
        self, connection, user: dict, body: dict
    ):
        project_id = int(
            body.get("id") or body.get("serviceProjectId") or 0
        )
        self._require_sales_access(
            user, "packages", "编辑" if project_id else "添加"
        )
        project_code = str(body.get("projectCode") or "").strip().upper()
        project_name = str(body.get("projectName") or "").strip()
        target_module = str(body.get("targetModule") or "").strip().upper()
        if not re.fullmatch(r"[A-Z0-9._-]{2,64}", project_code):
            raise ApiError(
                "项目编码仅支持大写字母、数字、点、横线和下划线"
            )
        if not project_name:
            raise ApiError("项目名称不能为空")
        if target_module not in SERVICE_TARGET_MODULES:
            raise ApiError("服务项目所属模块不正确")
        status = str(body.get("status") or "ACTIVE").strip().upper()
        if status not in {"ACTIVE", "INACTIVE"}:
            raise ApiError("服务项目状态不正确")
        with connection.cursor() as cursor:
            if project_id:
                existing = execute_one(
                    connection,
                    """
                    SELECT service_project_id
                    FROM service_projects
                    WHERE service_project_id=%s AND tenant_id=%s
                      AND deleted_at IS NULL
                    """,
                    (project_id, user["tenant_id"]),
                )
                if not existing:
                    raise ApiError("服务项目不存在", 404, 40400)
                cursor.execute(
                    """
                    UPDATE service_projects
                    SET project_code=%s,project_name=%s,target_module=%s,
                        project_category=%s,unit=%s,status=%s,note=%s,
                        version=version+1
                    WHERE service_project_id=%s
                    """,
                    (
                        project_code,
                        project_name,
                        target_module,
                        body.get("projectCategory") or None,
                        body.get("unit") or "次",
                        status,
                        body.get("note") or None,
                        project_id,
                    ),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO service_projects(
                      tenant_id,project_code,project_name,target_module,
                      project_category,unit,status,note,created_by_user_id
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        user["tenant_id"],
                        project_code,
                        project_name,
                        target_module,
                        body.get("projectCategory") or None,
                        body.get("unit") or "次",
                        status,
                        body.get("note") or None,
                        user["user_id"],
                    ),
                )
                project_id = cursor.lastrowid
        connection.commit()
        return self._success({"id": project_id, "status": status})

    def _validate_catalog_price_rules(
        self, connection, user: dict, rules: list
    ) -> list:
        normalized = []
        intervals = {}
        for index, raw in enumerate(rules, start=1):
            if not isinstance(raw, dict):
                raise ApiError(f"第{index}条价格规则格式不正确")
            store_id = self._allowed_store(user, raw.get("storeId"))
            room_type_id = int(raw.get("roomTypeId") or 0)
            room_type = execute_one(
                connection,
                """
                SELECT room_type_id FROM room_types
                WHERE room_type_id=%s AND tenant_id=%s AND status='启用'
                """,
                (room_type_id, user["tenant_id"]),
            )
            if not room_type:
                raise ApiError(f"第{index}条价格规则房型不存在")
            try:
                stay_days = int(raw.get("stayDays") or 0)
                amount = Decimal(str(raw.get("referenceAmount") or 0))
            except (ArithmeticError, TypeError, ValueError) as exc:
                raise ApiError(
                    f"第{index}条价格规则数值格式不正确"
                ) from exc
            if stay_days <= 0 or amount <= 0:
                raise ApiError(
                    f"第{index}条价格规则天数和金额必须大于0"
                )
            effective_from = self._catalog_date(
                raw.get("effectiveFrom"),
                f"第{index}条价格规则生效日期",
                required=True,
            )
            effective_to = self._catalog_date(
                raw.get("effectiveTo"),
                f"第{index}条价格规则失效日期",
            )
            if effective_to and effective_to < effective_from:
                raise ApiError(
                    f"第{index}条价格规则失效日期不能早于生效日期"
                )
            key = (store_id, room_type_id, stay_days)
            interval_end = effective_to or date(9999, 12, 31)
            for prior_start, prior_end in intervals.get(key, []):
                if (
                    effective_from <= prior_end
                    and interval_end >= prior_start
                ):
                    raise ApiError(
                        "同门店、房型和天数的价格生效区间不能重叠"
                    )
            intervals.setdefault(key, []).append(
                (effective_from, interval_end)
            )
            normalized.append(
                {
                    "store_id": store_id,
                    "room_type_id": room_type_id,
                    "stay_days": stay_days,
                    "reference_amount": amount,
                    "currency_code": str(
                        raw.get("currencyCode") or "CNY"
                    ).upper(),
                    "effective_from": effective_from,
                    "effective_to": effective_to,
                }
            )
        return normalized

    def _validate_catalog_entitlement_rules(
        self, connection, user: dict, rules: list
    ) -> list:
        normalized = []
        seen = set()
        for index, raw in enumerate(rules, start=1):
            if not isinstance(raw, dict):
                raise ApiError(f"第{index}条权益规则格式不正确")
            project_id = int(raw.get("serviceProjectId") or 0)
            project = execute_one(
                connection,
                """
                SELECT service_project_id,target_module
                FROM service_projects
                WHERE service_project_id=%s AND tenant_id=%s
                  AND status='ACTIVE' AND deleted_at IS NULL
                """,
                (project_id, user["tenant_id"]),
            )
            if not project:
                raise ApiError(f"第{index}条权益规则服务项目不存在")
            mode = str(
                raw.get("entitlementMode") or "COUNT"
            ).strip().upper()
            if mode not in ENTITLEMENT_MODES:
                raise ApiError(f"第{index}条权益规则类型不正确")
            unlimited = int(bool(raw.get("unlimited")))
            quantity = None
            if not unlimited:
                try:
                    quantity = Decimal(
                        str(raw.get("grantedQuantity") or 0)
                    )
                except (ArithmeticError, ValueError) as exc:
                    raise ApiError(
                        f"第{index}条权益数量格式不正确"
                    ) from exc
                if quantity <= 0:
                    raise ApiError(f"第{index}条权益数量必须大于0")
            per_item_limit = None
            if raw.get("perItemLimit") not in (None, ""):
                try:
                    per_item_limit = Decimal(str(raw["perItemLimit"]))
                except (ArithmeticError, ValueError) as exc:
                    raise ApiError(
                        f"第{index}条权益单项上限格式不正确"
                    ) from exc
                if per_item_limit <= 0:
                    raise ApiError(
                        f"第{index}条权益单项上限必须大于0"
                    )
            valid_days = int(raw.get("validDays") or 0) or None
            if valid_days is not None and valid_days <= 0:
                raise ApiError(
                    f"第{index}条权益有效天数必须大于0"
                )
            choice_group = str(
                raw.get("choiceGroupCode") or ""
            ).strip() or None
            unique_key = (project_id, choice_group or "")
            if unique_key in seen:
                raise ApiError("同一服务项目和选择组不能重复")
            seen.add(unique_key)
            normalized.append(
                {
                    "service_project_id": project_id,
                    "target_module": project["target_module"],
                    "entitlement_mode": mode,
                    "granted_quantity": quantity,
                    "unlimited_flag": unlimited,
                    "per_item_limit": per_item_limit,
                    "choice_group_code": choice_group,
                    "valid_days": valid_days,
                    "sort_order": int(raw.get("sortOrder") or index),
                    "note": raw.get("note") or None,
                }
            )
        return normalized

    def _save_catalog_package(
        self, connection, user: dict, body: dict
    ):
        version_id = int(body.get("packageVersionId") or 0)
        self._require_sales_access(
            user, "packages", "编辑" if version_id else "添加"
        )
        package_code = str(body.get("packageCode") or "").strip().upper()
        package_name = str(body.get("packageName") or "").strip()
        version_no = str(body.get("versionNo") or "").strip()
        if not re.fullmatch(r"[A-Z0-9._-]{2,64}", package_code):
            raise ApiError(
                "套餐编码仅支持大写字母、数字、点、横线和下划线"
            )
        if not package_name:
            raise ApiError("套餐名称不能为空")
        if not version_no:
            raise ApiError("套餐版本号不能为空")
        effective_from = self._catalog_date(
            body.get("effectiveFrom"),
            "套餐版本生效日期",
            default=date.today(),
        )
        effective_to = self._catalog_date(
            body.get("effectiveTo"), "套餐版本失效日期"
        )
        if effective_to and effective_to < effective_from:
            raise ApiError("套餐版本失效日期不能早于生效日期")
        raw_prices = body.get("priceRules")
        raw_entitlements = body.get("entitlementRules")
        if raw_prices is None:
            raw_prices = []
        if raw_entitlements is None:
            raw_entitlements = []
        if not isinstance(raw_prices, list):
            raise ApiError("价格规则必须是数组")
        if not isinstance(raw_entitlements, list):
            raise ApiError("权益规则必须是数组")
        prices = self._validate_catalog_price_rules(
            connection, user, raw_prices
        )
        entitlements = self._validate_catalog_entitlement_rules(
            connection, user, raw_entitlements
        )
        with connection.cursor() as cursor:
            if version_id:
                current = execute_one(
                    connection,
                    """
                    SELECT pv.package_version_id,pv.package_id,
                           pv.version_status
                    FROM package_versions pv
                    JOIN package_products pp ON pp.package_id=pv.package_id
                    WHERE pv.package_version_id=%s AND pv.tenant_id=%s
                      AND pp.deleted_at IS NULL
                    FOR UPDATE
                    """,
                    (version_id, user["tenant_id"]),
                )
                if not current:
                    raise ApiError("套餐版本不存在", 404, 40400)
                if current["version_status"] != "DRAFT":
                    raise ApiError("已发布套餐版本不可编辑，请新建版本")
                package_id = current["package_id"]
                cursor.execute(
                    """
                    UPDATE package_products
                    SET package_code=%s,package_name=%s,
                        package_category=%s,note=%s,version=version+1
                    WHERE package_id=%s
                    """,
                    (
                        package_code,
                        package_name,
                        body.get("packageCategory") or "月子套餐",
                        body.get("note") or None,
                        package_id,
                    ),
                )
                cursor.execute(
                    """
                    UPDATE package_versions
                    SET version_no=%s,effective_from=%s,effective_to=%s,
                        source_type=%s,evidence_note=%s
                    WHERE package_version_id=%s
                    """,
                    (
                        version_no,
                        effective_from,
                        effective_to,
                        body.get("sourceType") or "MANUAL",
                        body.get("evidenceNote") or None,
                        version_id,
                    ),
                )
                cursor.execute(
                    """
                    DELETE FROM package_price_rules
                    WHERE package_version_id=%s
                    """,
                    (version_id,),
                )
                cursor.execute(
                    """
                    DELETE FROM package_entitlement_rules
                    WHERE package_version_id=%s
                    """,
                    (version_id,),
                )
            else:
                package_id = int(body.get("packageId") or 0)
                if package_id:
                    product = execute_one(
                        connection,
                        """
                        SELECT package_id FROM package_products
                        WHERE package_id=%s AND tenant_id=%s
                          AND deleted_at IS NULL
                        """,
                        (package_id, user["tenant_id"]),
                    )
                    if not product:
                        raise ApiError("套餐产品不存在", 404, 40400)
                    cursor.execute(
                        """
                        UPDATE package_products
                        SET package_code=%s,package_name=%s,
                            package_category=%s,note=%s,version=version+1
                        WHERE package_id=%s
                        """,
                        (
                            package_code,
                            package_name,
                            body.get("packageCategory") or "月子套餐",
                            body.get("note") or None,
                            package_id,
                        ),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO package_products(
                          tenant_id,package_code,package_name,
                          package_category,status,sort_order,note,
                          created_by_user_id
                        ) VALUES (%s,%s,%s,%s,'DRAFT',%s,%s,%s)
                        """,
                        (
                            user["tenant_id"],
                            package_code,
                            package_name,
                            body.get("packageCategory") or "月子套餐",
                            int(body.get("sortOrder") or 0),
                            body.get("note") or None,
                            user["user_id"],
                        ),
                    )
                    package_id = cursor.lastrowid
                cursor.execute(
                    """
                    INSERT INTO package_versions(
                      tenant_id,package_id,version_no,effective_from,
                      effective_to,version_status,source_type,evidence_note,
                      created_by_user_id
                    ) VALUES (%s,%s,%s,%s,%s,'DRAFT',%s,%s,%s)
                    """,
                    (
                        user["tenant_id"],
                        package_id,
                        version_no,
                        effective_from,
                        effective_to,
                        body.get("sourceType") or "MANUAL",
                        body.get("evidenceNote") or None,
                        user["user_id"],
                    ),
                )
                version_id = cursor.lastrowid
            for rule in prices:
                cursor.execute(
                    """
                    INSERT INTO package_price_rules(
                      tenant_id,package_version_id,store_id,room_type_id,
                      stay_days,reference_amount,currency_code,
                      effective_from,effective_to,status
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'DRAFT')
                    """,
                    (
                        user["tenant_id"],
                        version_id,
                        rule["store_id"],
                        rule["room_type_id"],
                        rule["stay_days"],
                        rule["reference_amount"],
                        rule["currency_code"],
                        rule["effective_from"],
                        rule["effective_to"],
                    ),
                )
            for rule in entitlements:
                cursor.execute(
                    """
                    INSERT INTO package_entitlement_rules(
                      tenant_id,package_version_id,service_project_id,
                      entitlement_mode,granted_quantity,unlimited_flag,
                      per_item_limit,choice_group_code,valid_days,status,
                      sort_order,note
                    ) VALUES (
                      %s,%s,%s,%s,%s,%s,%s,%s,%s,'DRAFT',%s,%s
                    )
                    """,
                    (
                        user["tenant_id"],
                        version_id,
                        rule["service_project_id"],
                        rule["entitlement_mode"],
                        rule["granted_quantity"],
                        rule["unlimited_flag"],
                        rule["per_item_limit"],
                        rule["choice_group_code"],
                        rule["valid_days"],
                        rule["sort_order"],
                        rule["note"],
                    ),
                )
        self._audit(
            connection,
            user,
            "PACKAGE_VERSION",
            version_id,
            "SAVE_DRAFT",
            None,
            None,
            "DRAFT",
            {
                "packageCode": package_code,
                "priceRuleCount": len(prices),
                "entitlementRuleCount": len(entitlements),
            },
        )
        connection.commit()
        return self._success(
            {
                "packageId": package_id,
                "packageVersionId": version_id,
                "status": "DRAFT",
            }
        )

    def _publish_catalog_package(
        self, connection, user: dict, version_id: int
    ):
        self._require_sales_access(user, "packages", "审核")
        version = execute_one(
            connection,
            """
            SELECT pv.package_version_id,pv.package_id,pv.version_status
            FROM package_versions pv
            JOIN package_products pp ON pp.package_id=pv.package_id
            WHERE pv.package_version_id=%s AND pv.tenant_id=%s
              AND pp.deleted_at IS NULL
            FOR UPDATE
            """,
            (version_id, user["tenant_id"]),
        )
        if not version:
            raise ApiError("套餐版本不存在", 404, 40400)
        if version["version_status"] == "ACTIVE":
            return self._success(
                {"packageVersionId": version_id, "status": "ACTIVE"}
            )
        if version["version_status"] != "DRAFT":
            raise ApiError("只有草稿套餐版本可以发布")
        prices = execute_all(
            connection,
            """
            SELECT price_rule_id,store_id,room_type_id,stay_days,
                   effective_from,effective_to
            FROM package_price_rules
            WHERE package_version_id=%s
            FOR UPDATE
            """,
            (version_id,),
        )
        if not prices:
            raise ApiError("套餐至少需要一条价格规则才能发布")
        for rule in prices:
            overlap = execute_one(
                connection,
                """
                SELECT other.price_rule_id
                FROM package_price_rules other
                JOIN package_versions ov
                  ON ov.package_version_id=other.package_version_id
                WHERE ov.package_id=%s
                  AND ov.package_version_id<>%s
                  AND ov.version_status='ACTIVE'
                  AND other.status='ACTIVE'
                  AND other.store_id=%s
                  AND other.room_type_id=%s
                  AND other.stay_days=%s
                  AND other.effective_from
                    <=COALESCE(%s,'9999-12-31')
                  AND COALESCE(other.effective_to,'9999-12-31')>=%s
                LIMIT 1
                """,
                (
                    version["package_id"],
                    version_id,
                    rule["store_id"],
                    rule["room_type_id"],
                    rule["stay_days"],
                    rule["effective_to"],
                    rule["effective_from"],
                ),
            )
            if overlap:
                raise ApiError(
                    "存在同门店、房型和天数且生效区间重叠的已发布价格"
                )
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE package_versions
                SET version_status='ACTIVE',published_at=NOW(),
                    published_by_user_id=%s
                WHERE package_version_id=%s
                """,
                (user["user_id"], version_id),
            )
            cursor.execute(
                """
                UPDATE package_price_rules SET status='ACTIVE'
                WHERE package_version_id=%s
                """,
                (version_id,),
            )
            cursor.execute(
                """
                UPDATE package_entitlement_rules SET status='ACTIVE'
                WHERE package_version_id=%s
                """,
                (version_id,),
            )
            cursor.execute(
                """
                UPDATE package_products SET status='ACTIVE',version=version+1
                WHERE package_id=%s
                """,
                (version["package_id"],),
            )
        self._audit(
            connection,
            user,
            "PACKAGE_VERSION",
            version_id,
            "PUBLISH",
            None,
            "DRAFT",
            "ACTIVE",
        )
        connection.commit()
        return self._success(
            {"packageVersionId": version_id, "status": "ACTIVE"}
        )

    def _deactivate_catalog_package(
        self, connection, user: dict, version_id: int
    ):
        self._require_sales_access(user, "packages", "启用")
        version = execute_one(
            connection,
            """
            SELECT package_version_id,package_id,version_status
            FROM package_versions
            WHERE package_version_id=%s AND tenant_id=%s
            FOR UPDATE
            """,
            (version_id, user["tenant_id"]),
        )
        if not version:
            raise ApiError("套餐版本不存在", 404, 40400)
        if version["version_status"] != "ACTIVE":
            raise ApiError("只有已发布套餐版本可以停用")
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE package_versions SET version_status='INACTIVE'
                WHERE package_version_id=%s
                """,
                (version_id,),
            )
            cursor.execute(
                """
                UPDATE package_price_rules SET status='INACTIVE'
                WHERE package_version_id=%s
                """,
                (version_id,),
            )
            cursor.execute(
                """
                UPDATE package_entitlement_rules SET status='INACTIVE'
                WHERE package_version_id=%s
                """,
                (version_id,),
            )
            active = execute_one(
                connection,
                """
                SELECT package_version_id FROM package_versions
                WHERE package_id=%s AND version_status='ACTIVE'
                LIMIT 1
                """,
                (version["package_id"],),
            )
            if not active:
                cursor.execute(
                    """
                    UPDATE package_products
                    SET status='INACTIVE',version=version+1
                    WHERE package_id=%s
                    """,
                    (version["package_id"],),
                )
        self._audit(
            connection,
            user,
            "PACKAGE_VERSION",
            version_id,
            "DEACTIVATE",
            None,
            "ACTIVE",
            "INACTIVE",
        )
        connection.commit()
        return self._success(
            {"packageVersionId": version_id, "status": "INACTIVE"}
        )

    def _post_catalog_resource(
        self, connection, user: dict, resource: str, body: dict
    ):
        if resource == "/service-projects/save":
            return self._save_catalog_service_project(
                connection, user, body
            )
        if resource == "/packages/save":
            return self._save_catalog_package(connection, user, body)
        match = re.fullmatch(
            r"/packages/(\d+)/(publish|deactivate)", resource
        )
        if match:
            version_id = int(match.group(1))
            if match.group(2) == "publish":
                return self._publish_catalog_package(
                    connection, user, version_id
                )
            return self._deactivate_catalog_package(
                connection, user, version_id
            )
        raise ApiError("套餐目录资源不存在", 404, 40400)

    def _get_sales_module_data(
        self, connection, user: dict, resource: str, query: dict
    ):
        self._require_sales_access(user, resource)
        loaders = {
            "contracts": self._sales_contract_rows,
            "product-sales": self._sales_order_rows,
            "sales-details": self._sales_detail_rows,
            "packages": self._sales_package_rows,
            "card-packages": self._sales_card_package_rows,
            "gift-lists": self._sales_gift_list_rows,
            "discounts": self._sales_discount_rows,
            "coupons": self._sales_coupon_template_rows,
            "gift-applications": self._sales_gift_application_rows,
        }
        loader = loaders.get(resource)
        if not loader:
            raise ApiError("销售资源不存在", 404, 40400)
        # The request dispatcher has already narrowed `user` when a concrete
        # storeId is selected.  Keep the administrator's full store scope for
        # storeId=all so contract lists can be used as an aggregate query.
        # Write operations still require a concrete store through
        # `_require_selected_write_store`.
        rows = loader(connection, user, query or {})
        return self._success(
            {
                "list": rows,
                "total": len(rows),
                "stores": self._sales_store_options(connection, user),
            }
        )

    def _sales_store_options(self, connection, user: dict) -> list:
        clause, params = self._store_clause(user, "s")
        return execute_all(
            connection,
            f"""
            SELECT s.store_id AS id, s.name
            FROM stores s
            WHERE s.tenant_id=%s
              AND {clause}
            ORDER BY s.sort_weight DESC, s.store_id
            """,
            [user["tenant_id"], *params],
        )

    def _sales_contract_rows(
        self, connection, user: dict, query: dict
    ) -> list:
        clause, params = self._store_clause(user, "ct")
        rows = execute_all(
            connection,
            f"""
            SELECT ct.contract_id AS id, ct.contract_no AS contractNo,
                   ct.package_name AS packageName, c.name AS customerName,
                   ct.package_version_id AS packageVersionId,
                   ct.package_price_rule_id AS packagePriceRuleId,
                   cps.package_code AS packageCode,
                   cps.version_no AS packageVersionNo,
                   COALESCE(entitlement_summary.entitlementCount,0)
                     AS entitlementCount,
                   c.phone AS mobile, c.status AS arrivalStatus,
                   COALESCE(booking_summary.checkedIn,'否') AS checkedIn,
                   ct.status AS auditStatus,
                   owner.name AS salesperson,
                   ct.amount AS dealAmount, ct.paid AS receivedAmount,
                   0 AS refundAmount,
                   GREATEST(ct.amount-ct.paid,0) AS debtAmount,
                   COALESCE(receipt_summary.unpostedAmount,0)
                     AS unpostedAmount,
                   GREATEST(COALESCE(ct.reference_amount,ct.amount)-ct.amount,0)
                     AS discountAmount,
                   0 AS postPaymentDiscount,
                   COALESCE(ct.reference_amount,ct.amount)
                     AS receivableAmount,
                   ct.days AS contractDays,
                   ROUND(ct.discount_rate*100,2) AS discountRate,
                   ext.due_date AS dueDate,
                   ct.sign_date AS signedAt,
                   ext.room_type AS roomType, booking_summary.room AS room,
                   ct.expected_check_in AS checkInAt,
                   ct.expected_check_out AS checkOutAt,
                   ct.amount AS finalAmount,
                   d.name AS salesDepartment,
                   ct.note AS remark, creator.username AS creator,
                   s.name AS store, ext.nursing_type AS nursingType,
                   IF(ext.remote_sign=1,'是','否') AS remoteSign,
                   ext.discount_audit_status AS discountAudit,
                   IF(ext.first_order=1,'是','否') AS firstOrder,
                   ct.created_at AS createdAt,
                   ct.contract_type AS contractType,
                   IF(ext.changed=1,'是','否') AS changed
            FROM contracts ct
            JOIN customers c ON c.customer_id=ct.customer_id
            LEFT JOIN staff owner ON owner.staff_id=c.sales_staff_id
            LEFT JOIN departments d ON d.department_id=owner.department_id
            LEFT JOIN user_accounts creator
              ON creator.user_id=ct.created_by_user_id
            LEFT JOIN stores s ON s.store_id=ct.store_id
            LEFT JOIN (
              SELECT contract_id,
                     SUM(CASE WHEN status='待审核' THEN amount ELSE 0 END)
                       AS unpostedAmount
              FROM finance_receipts
              GROUP BY contract_id
            ) receipt_summary ON receipt_summary.contract_id=ct.contract_id
            LEFT JOIN sales_contract_extensions ext
              ON ext.contract_id=ct.contract_id
            LEFT JOIN contract_package_snapshots cps
              ON cps.package_snapshot_id=(
                SELECT MAX(snapshot.package_snapshot_id)
                FROM contract_package_snapshots snapshot
                WHERE snapshot.contract_id=ct.contract_id
              )
            LEFT JOIN (
              SELECT contract_id,COUNT(*) AS entitlementCount
              FROM customer_service_entitlements
              WHERE status='ACTIVE'
              GROUP BY contract_id
            ) entitlement_summary
              ON entitlement_summary.contract_id=ct.contract_id
            LEFT JOIN (
              SELECT rb.contract_id,
                     IF(MAX(rb.status='已入住')=1,'是','否') AS checkedIn,
                     GROUP_CONCAT(DISTINCT r.room_no ORDER BY r.room_no
                       SEPARATOR ' / ') AS room
              FROM room_bookings rb
              LEFT JOIN rooms r ON r.room_id=rb.room_id
              WHERE rb.deleted_at IS NULL
                AND rb.status IN ('已订房','已入住')
              GROUP BY rb.contract_id
            ) booking_summary ON booking_summary.contract_id=ct.contract_id
            WHERE ct.tenant_id=%s AND ct.deleted_at IS NULL
              AND {clause}
            ORDER BY ct.contract_id DESC
            LIMIT 500
            """,
            [user["tenant_id"], *params],
        )
        for row in rows:
            row["mobile"] = self._masked_phone(user, row.get("mobile"))
            if row.get("discountRate") is not None:
                row["discountRate"] = f"{row['discountRate']}%"
        return rows

    def _sales_order_rows(
        self, connection, user: dict, query: dict
    ) -> list:
        clause, params = self._store_clause(user, "o")
        rows = execute_all(
            connection,
            f"""
            SELECT o.order_no AS id, o.order_no AS saleNo,
                   c.customer_no AS customerNo, c.name AS customerName,
                   c.phone AS mobile, ext.sales_type AS saleType,
                   o.pay_method AS paymentMethod,
                   o.order_amount AS consumeAmount,
                   0 AS couponAmount, o.due_amount AS debtAmount,
                   seller.username AS salesperson,
                   ext.department_name AS department,
                   o.order_status AS paymentStatus,
                   ext.sale_date AS saleDate, o.created_at AS createdAt,
                   o.created_by AS creator, s.name AS store,
                   ext.finance_audit_status AS financeAudit,
                   ext.source, ext.introducer,
                   ext.introducer_mobile AS introducerMobile,
                   ext.remark, ext.payment_remark AS paymentRemark,
                   ext.discount_audit_status AS discountAudit,
                   c.source AS customerSource, ext.attachment,
                   ext.outbound_no AS outboundNo
            FROM orders o
            JOIN sales_order_extensions ext ON ext.order_no=o.order_no
            LEFT JOIN customers c ON c.customer_id=o.customer_id
            LEFT JOIN stores s ON s.store_id=o.store_id
            LEFT JOIN user_accounts seller
              ON seller.user_id=ext.salesperson_user_id
            WHERE o.tenant_id=%s AND o.deleted_at IS NULL
              AND {clause}
            ORDER BY ext.sale_date DESC, o.order_no DESC
            LIMIT 500
            """,
            [user["tenant_id"], *params],
        )
        lines = self._sales_order_lines(
            connection, user, [row["saleNo"] for row in rows]
        )
        for row in rows:
            row["mobile"] = self._masked_phone(user, row.get("mobile"))
            row["lineItems"] = lines.get(row["saleNo"], [])
        return rows

    def _sales_order_lines(
        self, connection, user: dict, order_nos: list
    ) -> dict:
        if not order_nos:
            return {}
        placeholders = ",".join(["%s"] * len(order_nos))
        rows = execute_all(
            connection,
            f"""
            SELECT oi.order_no, oi.id, ext.item_code AS itemNo,
                   oi.name AS itemName, ext.unit,
                   oi.unit_price AS price,
                   COALESCE(ext.discount_price,
                     oi.unit_price*COALESCE(oi.discount,1))
                     AS discountPrice,
                   ROUND(COALESCE(oi.discount,1)*100,2) AS discountRate,
                   oi.qty AS quantity,
                   COALESCE(ext.discount_price,
                     oi.unit_price*COALESCE(oi.discount,1))*oi.qty AS total,
                   ext.valid_days AS validDays, ext.warehouse,
                   ext.product_type AS productType, ext.tax_rate AS taxRate,
                   ext.remark
            FROM order_items oi
            LEFT JOIN sales_order_item_extensions ext
              ON ext.order_item_id=oi.id
            WHERE oi.tenant_id=%s AND oi.order_no IN ({placeholders})
            ORDER BY oi.id
            """,
            [user["tenant_id"], *order_nos],
        )
        grouped = {}
        for row in rows:
            row["discountRate"] = f"{row['discountRate']}%"
            grouped.setdefault(row.pop("order_no"), []).append(row)
        return grouped

    def _sales_detail_rows(
        self, connection, user: dict, query: dict
    ) -> list:
        clause, params = self._store_clause(user, "o")
        rows = execute_all(
            connection,
            f"""
            SELECT oi.id, CONCAT(o.order_no,'-',oi.id) AS detailNo,
                   oi.name AS itemName, ext.unit,
                   ext.product_type AS productType, oi.qty AS quantity,
                   oi.unit_price AS price,
                   COALESCE(ext.discount_price,
                     oi.unit_price*COALESCE(oi.discount,1))*oi.qty AS total,
                   ext.tax_rate AS taxRate, ext.remark,
                   o.order_no AS saleNo, c.name AS customerName,
                   c.phone AS mobile, o.pay_method AS paymentMethod,
                   sale.sales_type AS saleType,
                   o.order_status AS paymentStatus,
                   sale.sale_date AS saleDate,
                   seller.username AS salesperson,
                   o.created_at AS createdAt, s.name AS store,
                   stay_store.name AS stayStore, sale.source,
                   sale.remark AS saleRemark,
                   sale.payment_remark AS paymentRemark
            FROM order_items oi
            JOIN orders o ON o.order_no=oi.order_no
            JOIN sales_order_extensions sale ON sale.order_no=o.order_no
            LEFT JOIN sales_order_item_extensions ext
              ON ext.order_item_id=oi.id
            LEFT JOIN customers c ON c.customer_id=o.customer_id
            LEFT JOIN stores s ON s.store_id=o.store_id
            LEFT JOIN user_accounts seller
              ON seller.user_id=sale.salesperson_user_id
            LEFT JOIN room_bookings rb
              ON rb.customer_id=o.customer_id
             AND rb.deleted_at IS NULL AND rb.status='已入住'
            LEFT JOIN rooms room ON room.room_id=rb.room_id
            LEFT JOIN stores stay_store ON stay_store.store_id=room.store_id
            WHERE o.tenant_id=%s AND o.deleted_at IS NULL
              AND {clause}
            ORDER BY oi.id DESC
            LIMIT 1000
            """,
            [user["tenant_id"], *params],
        )
        for row in rows:
            row["mobile"] = self._masked_phone(user, row.get("mobile"))
            if row.get("taxRate") is not None:
                row["taxRate"] = f"{Decimal(str(row['taxRate'])) * 100}%"
        return rows

    def _sales_bundle_rows(
        self, connection, user: dict, domain: str, query: dict | None = None
    ) -> list:
        clause, params = self._store_clause(user, "ext")
        rows = execute_all(
            connection,
            f"""
            SELECT b.bundle_id AS id, ext.bundle_no,
                   b.name, b.price AS packageAmount,
                   ext.reference_price AS originalPrice,
                   ext.activity_price AS activityPrice,
                   ext.effective_date AS effectiveDate,
                   ext.room_type AS roomType,
                   ext.audit_status AS auditStatus,
                   b.status AS enabled,
                   IF(ext.visible=1,'是','否') AS visible,
                   ext.enabled_at AS enabledAt,
                   IF(ext.recommended=1,'是','否') AS recommended,
                   ext.recommended_at AS recommendedAt,
                   creator.username AS creator, s.name AS store,
                   b.times AS cardCount, ext.days AS validDays,
                   ext.bundle_type AS cardType
            FROM item_bundles b
            JOIN sales_bundle_extensions ext ON ext.bundle_id=b.bundle_id
            JOIN stores s ON s.store_id=ext.store_id
            LEFT JOIN user_accounts creator
              ON creator.user_id=ext.created_by_user_id
            WHERE b.tenant_id=%s AND b.deleted_at IS NULL
              AND b.domain=%s AND {clause}
            ORDER BY b.bundle_id DESC
            LIMIT 500
            """,
            [user["tenant_id"], domain, *params],
        )
        for row in rows:
            if domain == "月子套餐":
                row["packageNo"] = row.pop("bundle_no")
                row["packageName"] = row.pop("name")
            else:
                row["cardNo"] = row.pop("bundle_no")
                row["cardName"] = row.pop("name")
            row["lineItems"] = execute_all(
                connection,
                """
                SELECT line.line_id AS id, item.item_id AS itemNo,
                       item.name AS itemName, item.cat AS itemType,
                       item.unit, item.sale_price AS discountPrice,
                       line.qty AS quantity,
                       item.sale_price*line.qty AS total
                FROM item_bundle_lines line
                JOIN items item ON item.item_id=line.item_id
                WHERE line.bundle_id=%s AND line.tenant_id=%s
                ORDER BY line.line_id
                """,
                (row["id"], user["tenant_id"]),
            )
        return rows

    def _sales_package_rows(
        self, connection, user: dict, query: dict
    ) -> list:
        legacy_rows = self._sales_bundle_rows(
            connection, user, "月子套餐", query
        )
        for row in legacy_rows:
            base_name = str(row.get("packageName") or "").strip()
            nursing_type = str(
                row.pop("cardType", "") or row.get("nursingType") or ""
            ).strip()
            row["basePackageName"] = base_name
            row["nursingType"] = nursing_type
            row["packageDays"] = int(row.get("validDays") or 0)
            row["packageDisplayName"] = (
                f"{base_name}（{nursing_type}）"
                if nursing_type and nursing_type != "未注明"
                else base_name
            )
            row["selectionKey"] = f"legacy:{row['id']}"
            row["catalogOnly"] = False

        # Confirmed package catalogs are the source of truth for store/package
        # selection.  Older sales pages, however, only read ``item_bundles``.
        # Project catalog versions that have no store-local legacy bundle into
        # this read model instead of manufacturing a second writable record.
        # ``id`` deliberately stays NULL: catalog ids must never be sent to the
        # legacy bundle edit/delete endpoints.
        clause, params = self._store_clause(user, "pr")
        catalog_rows = execute_all(
            connection,
            f"""
            SELECT NULL AS id,
                   CONCAT('catalog:',pv.package_version_id,':',pr.store_id,':',
                          pr.stay_days) AS selectionKey,
                   pp.package_id AS packageId,
                   pv.package_version_id AS packageVersionId,
                   MIN(pr.price_rule_id) AS packagePriceRuleId,
                   CONCAT(pp.package_code,'@',pr.stay_days) AS packageNo,
                   pp.package_name AS packageName,
                   pp.package_name AS basePackageName,
                   CASE pp.package_code
                     WHEN 'HH-BASE' THEN '基础护理'
                     WHEN 'HH-BASE-721' THEN '7天一对一+21天团队护理'
                     WHEN 'HH-REPAIR' THEN '产后修复'
                     WHEN 'HH-REPAIR-721' THEN '7天一对一+21天团队护理'
                     WHEN 'HH-RECOVERY' THEN '修养护理'
                     WHEN 'HH-QUEEN' THEN '专属护理'
                     WHEN 'HH-PRESIDENT' THEN '专属护理'
                     ELSE ''
                   END AS nursingType,
                   pr.stay_days AS packageDays,
                   pr.stay_days AS validDays,
                   GROUP_CONCAT(DISTINCT rt.name ORDER BY rt.sort_order
                                SEPARATOR '、') AS roomType,
                   MIN(COALESCE(profile.original_amount,
                                pr.reference_amount)) AS originalPrice,
                   MIN(COALESCE(profile.activity_amount,
                                pr.reference_amount)) AS activityPrice,
                   MIN(COALESCE(profile.deal_amount,
                                pr.reference_amount)) AS dealPrice,
                   MIN(COALESCE(profile.deal_amount,
                                pr.reference_amount)) AS packageAmount,
                   MIN(pr.effective_from) AS effectiveDate,
                   '审核通过' AS auditStatus,
                   '启用' AS enabled,
                   '是' AS visible,
                   '否' AS recommended,
                   '甲方确认套餐目录' AS creator,
                   s.name AS store,
                   pv.source_type AS sourceType,
                   '标准套餐目录（只读）；通过“添加”生成销售套餐配置' AS dataStatus,
                   1 AS catalogOnly
            FROM package_products pp
            JOIN package_versions pv ON pv.package_id=pp.package_id
            JOIN package_price_rules pr
              ON pr.package_version_id=pv.package_version_id
            JOIN stores s ON s.store_id=pr.store_id
            JOIN room_types rt ON rt.room_type_id=pr.room_type_id
            LEFT JOIN package_price_profiles profile
              ON profile.price_rule_id=pr.price_rule_id
            LEFT JOIN item_bundles mapped_legacy
              ON mapped_legacy.bundle_id=COALESCE(
                   pv.legacy_bundle_id,pp.legacy_bundle_id
                 )
             AND mapped_legacy.tenant_id=pp.tenant_id
             AND mapped_legacy.domain='月子套餐'
             AND mapped_legacy.deleted_at IS NULL
            LEFT JOIN sales_bundle_extensions mapped_ext
              ON mapped_ext.bundle_id=mapped_legacy.bundle_id
             AND mapped_ext.store_id=pr.store_id
            LEFT JOIN sales_bundle_extensions legacy_ext
              ON legacy_ext.store_id=pr.store_id
             AND legacy_ext.days=pr.stay_days
            LEFT JOIN item_bundles legacy
              ON legacy.bundle_id=legacy_ext.bundle_id
             AND legacy.tenant_id=pp.tenant_id
             AND legacy.domain='月子套餐'
             AND legacy.name=pp.package_name
             AND legacy.deleted_at IS NULL
            WHERE pp.tenant_id=%s AND pp.deleted_at IS NULL
              AND pp.status='ACTIVE' AND pv.version_status='ACTIVE'
              AND pr.status='ACTIVE'
              AND pv.effective_from<=CURDATE()
              AND (pv.effective_to IS NULL OR pv.effective_to>=CURDATE())
              AND pr.effective_from<=CURDATE()
              AND (pr.effective_to IS NULL OR pr.effective_to>=CURDATE())
              AND mapped_ext.bundle_id IS NULL
              AND legacy.bundle_id IS NULL
              AND {clause}
            GROUP BY pp.package_id,pp.package_code,pp.package_name,
                     pv.package_version_id,pv.source_type,pr.store_id,s.name,
                     pr.stay_days,pp.sort_order
            ORDER BY s.sort_weight DESC,s.store_id,pp.sort_order,
                     pp.package_name,pr.stay_days
            """,
            [user["tenant_id"], *params],
        )
        for row in catalog_rows:
            base_name = str(row.get("basePackageName") or "").strip()
            nursing_type = str(row.get("nursingType") or "").strip()
            row["packageDisplayName"] = (
                f"{base_name}（{nursing_type}）"
                if nursing_type and nursing_type != "未注明"
                else base_name
            )
            row["lineItems"] = []
            row["catalogOnly"] = True
        return [*legacy_rows, *catalog_rows]

    def _sales_card_package_rows(
        self, connection, user: dict, query: dict
    ) -> list:
        return self._sales_bundle_rows(connection, user, "卡类套餐", query)

    def _sales_gift_list_rows(
        self, connection, user: dict, query: dict
    ) -> list:
        clause, params = self._store_clause(user, "gl")
        rows = execute_all(
            connection,
            f"""
            SELECT gl.gift_list_id AS id, gl.list_no AS listNo,
                   gl.list_name AS listName,
                   IF(gl.enabled=1,'启用','未启用') AS enabled,
                   gl.enabled_at AS enabledAt,
                   COALESCE(s.name,'公共') AS store
            FROM sales_gift_lists gl
            LEFT JOIN stores s ON s.store_id=gl.store_id
            WHERE gl.tenant_id=%s AND gl.deleted_at IS NULL
              AND (gl.store_id IS NULL OR {clause})
            ORDER BY gl.gift_list_id DESC
            """,
            [user["tenant_id"], *params],
        )
        for row in rows:
            row["lineItems"] = execute_all(
                connection,
                """
                SELECT line_id AS id, material_code AS materialNo,
                       material_name AS materialName,
                       material_type AS materialType, specification, unit,
                       price, quantity, price*quantity AS total, remark
                FROM sales_gift_list_lines
                WHERE gift_list_id=%s ORDER BY line_id
                """,
                (row["id"],),
            )
        return rows

    def _sales_discount_rows(
        self, connection, user: dict, query: dict
    ) -> list:
        clause, params = self._store_clause(user, "cp")
        rows = execute_all(
            connection,
            f"""
            SELECT cp.coupon_id AS id, cp.code AS discountNo,
                   c.name AS customerName, c.phone AS mobile,
                   COALESCE(ext.coupon_name,tpl.name,cp.type) AS couponName,
                   cp.type AS couponType, tpl.benefit_kind AS itemType,
                   1 AS quantity, cp.benefit AS couponAmount,
                   GREATEST(cp.benefit-ext.remaining_amount,0) AS usedAmount,
                   ext.remaining_amount AS remainingAmount,
                   ext.valid_days AS validDays,
                   ext.starts_at AS startsAt, cp.expire_date AS endsAt,
                   cp.expire_date AS deadline, cp.order_ref AS saleNo,
                   cp.used_at AS usedAt,
                   ext.audit_status AS auditStatus,
                   auditor.username AS auditor,
                   ext.audit_remark AS auditRemark, ext.remark,
                   creator.username AS creator, cp.created_at AS createdAt,
                   s.name AS store,
                   CASE
                     WHEN cp.status IN ('未使用','部分使用')
                       AND cp.expire_date IS NOT NULL
                       AND LEFT(cp.expire_date,10)<CURDATE()
                     THEN '已过期'
                     ELSE cp.status
                   END AS status,
                   ext.disable_reason AS disableReason,
                   (
                     SELECT GROUP_CONCAT(
                       CONCAT(
                         DATE_FORMAT(op.created_at,'%%m-%%d %%H:%%i'),
                         ' ',
                         op.action_name
                       )
                       ORDER BY op.operation_id SEPARATOR '；'
                     )
                     FROM sales_operation_records op
                     WHERE op.tenant_id=cp.tenant_id
                       AND op.resource_key='discounts'
                       AND op.record_key=(
                         CAST(cp.coupon_id AS CHAR)
                         COLLATE utf8mb4_unicode_ci
                       )
                   ) AS operationTrail
            FROM coupons cp
            JOIN sales_coupon_extensions ext ON ext.coupon_id=cp.coupon_id
            LEFT JOIN coupon_templates tpl ON tpl.tpl_id=cp.tpl_id
            LEFT JOIN customers c ON c.customer_id=cp.customer_id
            LEFT JOIN stores s ON s.store_id=cp.store_id
            LEFT JOIN user_accounts auditor
              ON auditor.user_id=ext.auditor_user_id
            LEFT JOIN user_accounts creator
              ON creator.user_id=ext.created_by_user_id
            WHERE cp.tenant_id=%s AND {clause}
            ORDER BY cp.coupon_id DESC
            LIMIT 500
            """,
            [user["tenant_id"], *params],
        )
        for row in rows:
            row["mobile"] = self._masked_phone(user, row.get("mobile"))
        return rows

    def _sales_coupon_template_rows(
        self, connection, user: dict, query: dict
    ) -> list:
        clause, params = self._store_clause(user, "tpl")
        return execute_all(
            connection,
            f"""
            SELECT tpl.tpl_id AS id, ext.coupon_no AS couponNo,
                   tpl.name AS couponName, tpl.type AS couponType,
                   tpl.benefit_kind AS itemType,
                   tpl.benefit AS couponAmount, s.name AS store,
                   ext.starts_at AS startsAt, ext.ends_at AS endsAt,
                    tpl.total_qty AS totalQuantity,
                    tpl.issued_qty AS issuedQuantity,
                    GREATEST(tpl.total_qty-tpl.issued_qty,0)
                      AS remainingQuantity,
                    ext.limit_per_customer AS limitPerCustomer,
                    tpl.status,
                    creator.username AS creator,
                   tpl.created_at AS createdAt
            FROM coupon_templates tpl
            JOIN sales_coupon_template_extensions ext ON ext.tpl_id=tpl.tpl_id
            LEFT JOIN stores s ON s.store_id=tpl.store_id
            LEFT JOIN user_accounts creator
              ON creator.user_id=ext.created_by_user_id
            WHERE tpl.tenant_id=%s AND tpl.deleted_at IS NULL
              AND {clause}
            ORDER BY tpl.tpl_id DESC
            LIMIT 500
            """,
            [user["tenant_id"], *params],
        )

    def _sales_gift_application_rows(
        self, connection, user: dict, query: dict
    ) -> list:
        clause, params = self._store_clause(user, "ga")
        rows = execute_all(
            connection,
            f"""
            SELECT ga.application_id AS id,
                   ga.application_no AS applicationNo,
                   c.customer_no AS customerNo, c.name AS customerName,
                   c.phone AS mobile,
                   GROUP_CONCAT(
                     CONCAT(line.item_name,' × ',line.quantity)
                     ORDER BY line.line_id SEPARATOR '、'
                   ) AS giftItems,
                   ga.consume_amount AS consumeAmount,
                   creator.username AS salesperson,
                   d.name AS department, ga.audit_status AS auditStatus,
                   DATE(ga.created_at) AS saleDate,
                   ga.created_at AS createdAt, s.name AS store,
                   ga.gift_type AS giftType,
                   ga.gift_reason AS giftReason,
                   ga.outbound_status AS outboundStatus,
                   ga.attachment
            FROM sales_gift_applications ga
            JOIN customers c ON c.customer_id=ga.customer_id
            JOIN stores s ON s.store_id=ga.store_id
            LEFT JOIN user_accounts creator
              ON creator.user_id=ga.created_by_user_id
            LEFT JOIN staff st ON st.staff_id=creator.staff_id
            LEFT JOIN departments d ON d.department_id=st.department_id
            LEFT JOIN sales_gift_application_lines line
              ON line.application_id=ga.application_id
            WHERE ga.tenant_id=%s AND ga.deleted_at IS NULL
              AND {clause}
            GROUP BY ga.application_id
            ORDER BY ga.application_id DESC
            LIMIT 500
            """,
            [user["tenant_id"], *params],
        )
        for row in rows:
            row["mobile"] = self._masked_phone(user, row.get("mobile"))
            row["lineItems"] = execute_all(
                connection,
                """
                SELECT line_id AS id, item_code AS itemNo,
                       item_name AS itemName, unit, price, discount_price
                         AS discountPrice, quantity,
                       discount_price*quantity AS total,
                       valid_days AS validDays, warehouse
                FROM sales_gift_application_lines
                WHERE application_id=%s ORDER BY line_id
                """,
                (row["id"],),
            )
        return rows

    def _post_sales_resource(
        self, connection, user: dict, resource: str, body: dict
    ):
        match = re.fullmatch(r"/([^/]+)/(save|action|audit)", resource)
        if not match:
            raise ApiError("销售资源不存在", 404, 40400)
        module, operation = match.groups()
        if module not in SALES_RESOURCE_NAV_IDS:
            raise ApiError("销售资源不存在", 404, 40400)
        if operation == "save":
            return self._save_sales_record(connection, user, module, body)
        if operation == "audit":
            payload = dict(body)
            payload["action"] = payload.get("action") or "审核"
            return self._perform_sales_action(
                connection, user, module, payload
            )
        return self._perform_sales_action(connection, user, module, body)

    def _sales_number(self, prefix: str) -> str:
        return (
            f"{prefix}-{datetime.now():%Y%m%d%H%M%S}-"
            f"{secrets.token_hex(2).upper()}"
        )

    def _sales_store_id(
        self, connection, user: dict, body: dict
    ) -> int:
        explicit_id = body.get("storeId")
        if explicit_id:
            store_id = self._allowed_store(user, explicit_id)
            self._require_selected_write_store(user, body, store_id)
            return store_id
        requested = str(body.get("store") or "").strip()
        if requested and requested != "全部":
            for store in self._sales_store_options(connection, user):
                if self._room_store_matches(requested, store["name"]):
                    store_id = int(store["id"])
                    self._require_selected_write_store(user, body, store_id)
                    return store_id
            raise ApiError("当前账号无权访问所选门店", 403, 40300)
        default_id = user.get("default_store_id")
        if default_id:
            store_id = self._allowed_store(user, default_id)
            self._require_selected_write_store(user, body, store_id)
            return store_id
        if len(user["store_ids"]) == 1:
            store_id = int(user["store_ids"][0])
            self._require_selected_write_store(user, body, store_id)
            return store_id
        raise ApiError("请选择销售门店")

    def _sales_customer(
        self, connection, user: dict, body: dict, store_id: int
    ) -> dict:
        customer_id = int(body.get("customerId") or 0)
        if customer_id:
            row = execute_one(
                connection,
                """
                SELECT customer_id,store_id,customer_no,name,phone,status
                FROM customers
                WHERE customer_id=%s AND tenant_id=%s AND deleted_at IS NULL
                """,
                (customer_id, user["tenant_id"]),
            )
        else:
            name = str(body.get("customerName") or "").strip()
            phone = str(body.get("mobile") or "").strip()
            if not name:
                raise ApiError("请选择现有客户")
            if len(name) > 30:
                raise ApiError("客户姓名不能超过30个字符")
            if not re.fullmatch(r"1[3-9]\d{9}", phone):
                raise ApiError("手机号须为中国大陆11位手机号")
            row = execute_one(
                connection,
                """
                SELECT customer_id,store_id,customer_no,name,phone,status
                FROM customers
                WHERE tenant_id=%s AND deleted_at IS NULL AND name=%s
                  AND (%s='' OR phone=%s)
                ORDER BY customer_id DESC LIMIT 1
                """,
                (user["tenant_id"], name, phone, phone),
            )
        if not row:
            raise ApiError("客户不存在，请先在客户管理建档")
        if int(row["store_id"] or 0) != store_id:
            raise ApiError("客户所属门店与销售门店不一致")
        self._allowed_store(user, row["store_id"])
        return row

    def _sales_text(
        self,
        body: dict,
        key: str,
        label: str,
        *,
        required: bool = False,
        max_length: int = 500,
    ) -> str:
        value = str(body.get(key) or "").strip()
        if required and not value:
            raise ApiError(f"{label}不能为空")
        if len(value) > max_length:
            raise ApiError(f"{label}不能超过{max_length}个字符")
        return value

    def _sales_decimal(
        self, body: dict, key: str, default=0, positive: bool = False
    ) -> Decimal:
        try:
            value = Decimal(str(body.get(key) or default))
        except (ArithmeticError, ValueError) as exc:
            raise ApiError(f"{key}金额格式不正确") from exc
        if positive and value <= 0:
            raise ApiError(f"{key}必须大于0")
        if value < 0:
            raise ApiError(f"{key}不能小于0")
        return value

    def _save_sales_record(
        self, connection, user: dict, resource: str, body: dict
    ):
        if resource == "contracts":
            return self._save_sales_contract(connection, user, body)
        if resource == "product-sales":
            return self._save_sales_order(connection, user, body)
        if resource in {"packages", "card-packages"}:
            return self._save_sales_bundle(
                connection, user, resource, body
            )
        if resource == "gift-lists":
            return self._save_sales_gift_list(connection, user, body)
        if resource == "discounts":
            return self._save_sales_discount(connection, user, body)
        if resource == "coupons":
            return self._save_sales_coupon_template(
                connection, user, body
            )
        if resource == "gift-applications":
            return self._save_sales_gift_application(
                connection, user, body
            )
        raise ApiError("当前销售页面仅支持查询", 403, 40300)

    def _resolve_contract_package(
        self,
        connection,
        user: dict,
        body: dict,
        store_id: int,
        stay_days: int,
        requested_reference: Decimal,
    ) -> dict | None:
        version_id = int(body.get("packageVersionId") or 0)
        price_rule_id = int(body.get("packagePriceRuleId") or 0)
        package_id = int(body.get("packageId") or 0)
        if not any((version_id, price_rule_id, package_id)):
            return None
        room_type_id = int(body.get("roomTypeId") or 0)
        if not room_type_id:
            room_type_name = str(body.get("roomType") or "").strip()
            if room_type_name:
                room_type = execute_one(
                    connection,
                    """
                    SELECT room_type_id
                    FROM room_types
                    WHERE tenant_id=%s AND status='启用'
                      AND (
                        type_code=%s OR name=%s OR package_name=%s
                      )
                    ORDER BY room_type_id LIMIT 1
                    """,
                    (
                        user["tenant_id"],
                        room_type_name,
                        room_type_name,
                        room_type_name,
                    ),
                )
                room_type_id = int(
                    (room_type or {}).get("room_type_id") or 0
                )
        if not room_type_id:
            raise ApiError("规范套餐合同必须选择房型")
        signed_on = self._catalog_date(
            body.get("signedAt") or body.get("signDate"),
            "合同签订日期",
            default=date.today(),
        )
        params = [
            user["tenant_id"],
            store_id,
            room_type_id,
            stay_days,
            signed_on,
            signed_on,
        ]
        selectors = []
        if price_rule_id:
            selectors.append("pr.price_rule_id=%s")
            params.append(price_rule_id)
        if version_id:
            selectors.append("pv.package_version_id=%s")
            params.append(version_id)
        if package_id:
            selectors.append("pp.package_id=%s")
            params.append(package_id)
        package = execute_one(
            connection,
            f"""
            SELECT pp.package_id,pp.package_code,pp.package_name,
                   pv.package_version_id,pv.version_no,
                   pv.effective_from AS version_effective_from,
                   pv.effective_to AS version_effective_to,
                   pr.price_rule_id,pr.room_type_id,pr.stay_days,
                   pr.reference_amount,pr.currency_code,
                   pr.effective_from,pr.effective_to
            FROM package_products pp
            JOIN package_versions pv ON pv.package_id=pp.package_id
            JOIN package_price_rules pr
              ON pr.package_version_id=pv.package_version_id
            WHERE pp.tenant_id=%s AND pp.deleted_at IS NULL
              AND pp.status='ACTIVE'
              AND pv.version_status='ACTIVE'
              AND pr.status='ACTIVE'
              AND pr.store_id=%s
              AND pr.room_type_id=%s
              AND pr.stay_days=%s
              AND pr.effective_from<=%s
              AND (pr.effective_to IS NULL OR pr.effective_to>=%s)
              AND {' AND '.join(selectors)}
            ORDER BY pv.effective_from DESC,pr.effective_from DESC,
                     pv.package_version_id DESC
            LIMIT 1
            """,
            params,
        )
        if not package:
            raise ApiError("没有匹配门店、房型、天数和签订日期的已发布套餐价格")
        catalog_reference = Decimal(str(package["reference_amount"]))
        if requested_reference != catalog_reference:
            raise ApiError(
                "合同参考价格必须使用已发布套餐价格，不能手工覆盖"
            )
        return package

    def _freeze_contract_package(
        self,
        connection,
        user: dict,
        contract_id: int,
        store_id: int,
        deal_amount: Decimal,
        package: dict,
    ):
        existing = execute_one(
            connection,
            """
            SELECT cps.package_snapshot_id,
                   COUNT(cse.customer_entitlement_id) AS granted_count
            FROM contract_package_snapshots cps
            LEFT JOIN contract_entitlement_snapshots ces
              ON ces.package_snapshot_id=cps.package_snapshot_id
            LEFT JOIN customer_service_entitlements cse
              ON cse.entitlement_snapshot_id=ces.entitlement_snapshot_id
            WHERE cps.contract_id=%s
            GROUP BY cps.package_snapshot_id
            """,
            (contract_id,),
        )
        if existing and int(existing["granted_count"] or 0) > 0:
            raise ApiError("合同权益已经发放，不能覆盖套餐快照")
        with connection.cursor() as cursor:
            if existing:
                cursor.execute(
                    """
                    DELETE FROM contract_entitlement_snapshots
                    WHERE package_snapshot_id=%s
                    """,
                    (existing["package_snapshot_id"],),
                )
                cursor.execute(
                    """
                    DELETE FROM contract_package_snapshots
                    WHERE package_snapshot_id=%s
                    """,
                    (existing["package_snapshot_id"],),
                )
            snapshot_payload = {
                "packageCode": package["package_code"],
                "packageName": package["package_name"],
                "versionNo": package["version_no"],
                "priceRuleId": package["price_rule_id"],
                "roomTypeId": package["room_type_id"],
                "stayDays": package["stay_days"],
                "referenceAmount": str(package["reference_amount"]),
                "dealAmount": str(deal_amount),
                "currencyCode": package["currency_code"],
            }
            cursor.execute(
                """
                INSERT INTO contract_package_snapshots(
                  tenant_id,contract_id,package_version_id,price_rule_id,
                  package_code,package_name,version_no,store_id,
                  room_type_id,stay_days,reference_amount,deal_amount,
                  currency_code,effective_from,effective_to,snapshot_json
                ) VALUES (
                  %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
                )
                """,
                (
                    user["tenant_id"],
                    contract_id,
                    package["package_version_id"],
                    package["price_rule_id"],
                    package["package_code"],
                    package["package_name"],
                    package["version_no"],
                    store_id,
                    package["room_type_id"],
                    package["stay_days"],
                    package["reference_amount"],
                    deal_amount,
                    package["currency_code"],
                    package["effective_from"],
                    package["effective_to"],
                    json.dumps(snapshot_payload, ensure_ascii=False),
                ),
            )
            package_snapshot_id = cursor.lastrowid
            cursor.execute(
                """
                INSERT INTO contract_entitlement_snapshots(
                  tenant_id,contract_id,package_snapshot_id,source_rule_id,
                  service_project_id,project_code,project_name,
                  target_module,entitlement_mode,granted_quantity,
                  unlimited_flag,per_item_limit,choice_group_code,
                  valid_days,grant_status
                )
                SELECT er.tenant_id,%s,%s,er.entitlement_rule_id,
                       er.service_project_id,sp.project_code,
                       sp.project_name,sp.target_module,
                       er.entitlement_mode,er.granted_quantity,
                       er.unlimited_flag,er.per_item_limit,
                       er.choice_group_code,er.valid_days,'FROZEN'
                FROM package_entitlement_rules er
                JOIN service_projects sp
                  ON sp.service_project_id=er.service_project_id
                WHERE er.package_version_id=%s
                  AND er.tenant_id=%s
                  AND er.status='ACTIVE'
                  AND sp.status='ACTIVE'
                  AND sp.deleted_at IS NULL
                ORDER BY er.sort_order,er.entitlement_rule_id
                """,
                (
                    contract_id,
                    package_snapshot_id,
                    package["package_version_id"],
                    user["tenant_id"],
                ),
            )

    def _grant_contract_entitlements(
        self, connection, user: dict, contract_id: int
    ) -> int:
        contract = execute_one(
            connection,
            """
            SELECT contract_id,tenant_id,store_id,customer_id,
                   expected_check_in,expected_check_out,sign_date
            FROM contracts
            WHERE contract_id=%s AND tenant_id=%s
            FOR UPDATE
            """,
            (contract_id, user["tenant_id"]),
        )
        if not contract:
            raise ApiError("合同不存在")
        snapshots = execute_all(
            connection,
            """
            SELECT entitlement_snapshot_id,service_project_id,
                   target_module,entitlement_mode,granted_quantity,
                   unlimited_flag,valid_days,grant_status
            FROM contract_entitlement_snapshots
            WHERE contract_id=%s AND tenant_id=%s
            ORDER BY entitlement_snapshot_id
            FOR UPDATE
            """,
            (contract_id, user["tenant_id"]),
        )
        granted = 0
        valid_from = (
            contract["expected_check_in"]
            or contract["sign_date"]
            or date.today()
        )
        if isinstance(valid_from, datetime):
            valid_from = valid_from.date()
        elif isinstance(valid_from, str):
            valid_from = date.fromisoformat(valid_from[:10])
        for snapshot in snapshots:
            existing = execute_one(
                connection,
                """
                SELECT customer_entitlement_id,status,used_quantity,
                       reserved_quantity
                FROM customer_service_entitlements
                WHERE entitlement_snapshot_id=%s
                FOR UPDATE
                """,
                (snapshot["entitlement_snapshot_id"],),
            )
            if existing and existing["status"] == "ACTIVE":
                continue
            if existing and (
                Decimal(str(existing["used_quantity"] or 0)) != 0
                or Decimal(str(existing["reserved_quantity"] or 0)) != 0
            ):
                raise ApiError("已发生使用或预约的合同权益不能重新发放")
            valid_to = contract["expected_check_out"]
            if isinstance(valid_to, datetime):
                valid_to = valid_to.date()
            elif isinstance(valid_to, str) and valid_to:
                valid_to = date.fromisoformat(valid_to[:10])
            if snapshot["valid_days"]:
                valid_to = valid_from + timedelta(
                    days=int(snapshot["valid_days"])
                )
            with connection.cursor() as cursor:
                if existing:
                    cursor.execute(
                        """
                        UPDATE customer_service_entitlements
                        SET status='ACTIVE',valid_from=%s,valid_to=%s,
                            version=version+1
                        WHERE customer_entitlement_id=%s
                        """,
                        (
                            valid_from,
                            valid_to,
                            existing["customer_entitlement_id"],
                        ),
                    )
                    entitlement_id = existing["customer_entitlement_id"]
                    transaction_type = "REGRANT"
                else:
                    cursor.execute(
                        """
                        INSERT INTO customer_service_entitlements(
                          tenant_id,store_id,customer_id,contract_id,
                          entitlement_snapshot_id,service_project_id,
                          target_module,entitlement_mode,granted_quantity,
                          used_quantity,reserved_quantity,unlimited_flag,
                          valid_from,valid_to,status
                        ) VALUES (
                          %s,%s,%s,%s,%s,%s,%s,%s,%s,0,0,%s,%s,%s,'ACTIVE'
                        )
                        """,
                        (
                            user["tenant_id"],
                            contract["store_id"],
                            contract["customer_id"],
                            contract_id,
                            snapshot["entitlement_snapshot_id"],
                            snapshot["service_project_id"],
                            snapshot["target_module"],
                            snapshot["entitlement_mode"],
                            snapshot["granted_quantity"],
                            snapshot["unlimited_flag"],
                            valid_from,
                            valid_to,
                        ),
                    )
                    entitlement_id = cursor.lastrowid
                    transaction_type = "GRANT"
                balance_after = (
                    None
                    if snapshot["unlimited_flag"]
                    else snapshot["granted_quantity"]
                )
                cursor.execute(
                    """
                    INSERT INTO customer_entitlement_ledger(
                      tenant_id,customer_entitlement_id,transaction_type,
                      quantity_change,balance_after,business_type,
                      business_id,operator_user_id,remark
                    ) VALUES (%s,%s,%s,%s,%s,'CONTRACT_APPROVAL',%s,%s,%s)
                    """,
                    (
                        user["tenant_id"],
                        entitlement_id,
                        transaction_type,
                        snapshot["granted_quantity"] or 0,
                        balance_after,
                        int(time.time_ns() // 1000),
                        user["user_id"],
                        f"合同 {contract_id} 审核发放",
                    ),
                )
                cursor.execute(
                    """
                    UPDATE contract_entitlement_snapshots
                    SET grant_status='GRANTED'
                    WHERE entitlement_snapshot_id=%s
                    """,
                    (snapshot["entitlement_snapshot_id"],),
                )
            granted += 1
        return granted

    def _revoke_contract_entitlements(
        self, connection, user: dict, contract_id: int
    ) -> int:
        rows = execute_all(
            connection,
            """
            SELECT cse.customer_entitlement_id,cse.granted_quantity,
                   cse.used_quantity,cse.reserved_quantity,
                   cse.unlimited_flag,ces.entitlement_snapshot_id
            FROM customer_service_entitlements cse
            JOIN contract_entitlement_snapshots ces
              ON ces.entitlement_snapshot_id=cse.entitlement_snapshot_id
            WHERE cse.contract_id=%s AND cse.tenant_id=%s
              AND cse.status='ACTIVE'
            FOR UPDATE
            """,
            (contract_id, user["tenant_id"]),
        )
        for row in rows:
            if (
                Decimal(str(row["used_quantity"] or 0)) != 0
                or Decimal(str(row["reserved_quantity"] or 0)) != 0
            ):
                raise ApiError("合同权益已使用或预约，不能反审核")
        for row in rows:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE customer_service_entitlements
                    SET status='REVOKED',version=version+1
                    WHERE customer_entitlement_id=%s
                    """,
                    (row["customer_entitlement_id"],),
                )
                cursor.execute(
                    """
                    INSERT INTO customer_entitlement_ledger(
                      tenant_id,customer_entitlement_id,transaction_type,
                      quantity_change,balance_after,business_type,
                      business_id,operator_user_id,remark
                    ) VALUES (%s,%s,'REVOKE',%s,0,'CONTRACT_REVERSAL',%s,%s,%s)
                    """,
                    (
                        user["tenant_id"],
                        row["customer_entitlement_id"],
                        -(row["granted_quantity"] or 0),
                        int(time.time_ns() // 1000),
                        user["user_id"],
                        f"合同 {contract_id} 反审核收回",
                    ),
                )
                cursor.execute(
                    """
                    UPDATE contract_entitlement_snapshots
                    SET grant_status='REVOKED'
                    WHERE entitlement_snapshot_id=%s
                    """,
                    (row["entitlement_snapshot_id"],),
                )
        return len(rows)

    def _save_sales_contract(
        self, connection, user: dict, body: dict
    ):
        contract_id = int(body.get("id") or 0)
        self._require_sales_access(
            user, "contracts", "编辑" if contract_id else "添加"
        )
        store_id = self._sales_store_id(connection, user, body)
        customer = self._sales_customer(connection, user, body, store_id)
        amount = self._sales_decimal(body, "dealAmount", positive=True)
        reference = self._sales_decimal(
            body,
            "referencePrice",
            body.get("referenceAmount") or amount,
            positive=True,
        )
        if amount > reference:
            raise ApiError("成交金额不能大于参考价格")
        try:
            days = int(body.get("contractDays") or body.get("days") or 0)
        except (TypeError, ValueError) as exc:
            raise ApiError("合同天数格式不正确") from exc
        if days <= 0:
            raise ApiError("合同天数必须大于0")
        raw_type = str(body.get("contractType") or "月子合同")
        contract_type = {
            "月子护理": "月子合同",
            "婴儿托管": "婴儿托管",
            "试住合同": "试住合同",
        }.get(raw_type, raw_type)
        if contract_type not in CONTRACT_TYPES:
            raise ApiError("合同类型不正确")
        package = self._resolve_contract_package(
            connection,
            user,
            body,
            store_id,
            days,
            reference,
        )
        package_name = (
            package["package_name"]
            if package
            else body.get("packageName") or None
        )
        package_version_id = (
            package["package_version_id"] if package else None
        )
        package_price_rule_id = (
            package["price_rule_id"] if package else None
        )
        discount_rate = (amount / reference).quantize(Decimal("0.0001"))
        status = "待审核" if body.get("submit") else "待提交"
        with connection.cursor() as cursor:
            if contract_id:
                clause, params = self._store_clause(user, "ct")
                existing = execute_one(
                    connection,
                    f"""
                    SELECT ct.contract_id,ct.store_id,ct.status
                    FROM contracts ct
                    WHERE ct.contract_id=%s AND ct.tenant_id=%s
                      AND ct.deleted_at IS NULL AND {clause}
                    """,
                    [contract_id, user["tenant_id"], *params],
                )
                if not existing:
                    raise ApiError("合同不存在或无权访问", 404, 40400)
                cursor.execute(
                    """
                    UPDATE contracts
                    SET store_id=%s,customer_id=%s,contract_type=%s,
                        package_name=%s,
                        package_version_id=COALESCE(%s,package_version_id),
                        package_price_rule_id=COALESCE(
                          %s,package_price_rule_id
                        ),
                        reference_amount=%s,amount=%s,discount_rate=%s,
                        days=%s,expected_check_in=%s,expected_check_out=%s,
                        sign_date=%s,note=%s,status=%s,version=version+1
                    WHERE contract_id=%s
                    """,
                    (
                        store_id,
                        customer["customer_id"],
                        contract_type,
                        package_name,
                        package_version_id,
                        package_price_rule_id,
                        reference,
                        amount,
                        discount_rate,
                        days,
                        body.get("checkInAt") or None,
                        body.get("checkOutAt") or None,
                        body.get("signedAt") or date.today().isoformat(),
                        body.get("remark") or None,
                        status,
                        contract_id,
                    ),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO contracts(
                      tenant_id,store_id,customer_id,contract_type,
                      package_name,package_version_id,package_price_rule_id,
                      reference_amount,amount,paid,discount_rate,days,
                      expected_check_in,expected_check_out,sign_date,status,
                      note,created_by_user_id,version,created_at
                    ) VALUES (
                      %s,%s,%s,%s,%s,%s,%s,%s,%s,0,%s,%s,%s,%s,%s,
                      %s,%s,%s,0,NOW()
                    )
                    """,
                    (
                        user["tenant_id"],
                        store_id,
                        customer["customer_id"],
                        contract_type,
                        package_name,
                        package_version_id,
                        package_price_rule_id,
                        reference,
                        amount,
                        discount_rate,
                        days,
                        body.get("checkInAt") or None,
                        body.get("checkOutAt") or None,
                        body.get("signedAt") or date.today().isoformat(),
                        status,
                        body.get("remark") or None,
                        user["user_id"],
                    ),
                )
                contract_id = cursor.lastrowid
                cursor.execute(
                    "UPDATE contracts SET contract_no=%s WHERE contract_id=%s",
                    (
                        f"HT-{datetime.now():%Y%m%d}-{contract_id:05d}",
                        contract_id,
                    ),
                )
            cursor.execute(
                """
                INSERT INTO sales_contract_extensions(
                  contract_id,due_date,room_type,nursing_type,meal_package,
                  first_order,remote_sign,discount_audit_status,changed,
                  created_by_user_id
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE
                  due_date=VALUES(due_date),room_type=VALUES(room_type),
                  nursing_type=VALUES(nursing_type),
                  meal_package=VALUES(meal_package),
                  first_order=VALUES(first_order),
                  remote_sign=VALUES(remote_sign),
                  discount_audit_status=VALUES(discount_audit_status),
                  changed=VALUES(changed)
                """,
                (
                    contract_id,
                    body.get("dueDate") or None,
                    body.get("roomType") or None,
                    body.get("nursingType") or None,
                    body.get("mealPackage") or None,
                    int(bool(body.get("firstOrder"))),
                    int(bool(body.get("remoteSign"))),
                    "待审核" if body.get("discountAmount") else None,
                    int(bool(body.get("changed"))),
                    user["user_id"],
                ),
            )
            if package:
                self._freeze_contract_package(
                    connection,
                    user,
                    contract_id,
                    store_id,
                    amount,
                    package,
                )
            cursor.execute(
                """
                UPDATE customers
                SET status='已签合同但未审核',updated_at=NOW()
                WHERE customer_id=%s
                """,
                (customer["customer_id"],),
            )
        self._sales_log(
            connection,
            user,
            store_id,
            "contracts",
            contract_id,
            "编辑" if body.get("id") else "添加",
            None,
            status,
        )
        connection.commit()
        return self._success({"id": contract_id, "status": status})

    def _save_sales_order(
        self, connection, user: dict, body: dict
    ):
        order_no = str(body.get("id") or "").strip()
        sale_type = str(body.get("saleType") or "项目销售")
        permission_action = "编辑" if order_no else {
            "项目销售": "服务销售",
            "服务销售": "服务销售",
            "物料销售": "物料销售",
            "卡类销售": "卡类销售",
        }.get(sale_type, "服务销售")
        self._require_sales_access(user, "product-sales", permission_action)
        store_id = self._sales_store_id(connection, user, body)
        customer = self._sales_customer(connection, user, body, store_id)
        lines = body.get("lineItems")
        if not isinstance(lines, list) or not lines:
            raise ApiError("请至少添加一条销售商品明细")
        total = sum(
            self._sales_decimal(
                line,
                "total",
                Decimal(str(line.get("discountPrice") or line.get("price") or 0))
                * Decimal(str(line.get("quantity") or 0)),
            )
            for line in lines
        )
        if total <= 0:
            raise ApiError("销售总金额必须大于0")
        paid = self._sales_decimal(body, "paymentAmount")
        if paid > total:
            raise ApiError("支付金额不能大于销售总金额")
        status = "已支付" if paid == total and total > 0 else "未支付"
        if sale_type == "物料销售" and status == "已支付":
            status = "已付未出库"
        with connection.cursor() as cursor:
            if order_no:
                clause, params = self._store_clause(user, "o")
                existing = execute_one(
                    connection,
                    f"""
                    SELECT o.order_no FROM orders o
                    WHERE o.order_no=%s AND o.tenant_id=%s
                      AND o.deleted_at IS NULL AND {clause}
                    """,
                    [order_no, user["tenant_id"], *params],
                )
                if not existing:
                    raise ApiError("销售单不存在或无权访问", 404, 40400)
                cursor.execute(
                    """
                    UPDATE orders
                    SET store_id=%s,customer_id=%s,domain=%s,
                        order_status=%s,order_amount=%s,paid_amount=%s,
                        due_amount=%s,pay_method=%s,version=version+1,
                        updated_at=NOW()
                    WHERE order_no=%s
                    """,
                    (
                        store_id,
                        customer["customer_id"],
                        sale_type,
                        status,
                        total,
                        paid,
                        total - paid,
                        body.get("paymentMethod") or None,
                        order_no,
                    ),
                )
                cursor.execute(
                    """
                    DELETE ext FROM sales_order_item_extensions ext
                    JOIN order_items oi ON oi.id=ext.order_item_id
                    WHERE oi.order_no=%s
                    """,
                    (order_no,),
                )
                cursor.execute(
                    "DELETE FROM order_items WHERE order_no=%s",
                    (order_no,),
                )
            else:
                order_no = self._sales_number("XS")
                cursor.execute(
                    """
                    INSERT INTO orders(
                      order_no,tenant_id,store_id,customer_id,domain,
                      order_status,order_amount,paid_amount,due_amount,
                      pay_method,created_at,version,updated_at,created_by
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),0,NOW(),%s)
                    """,
                    (
                        order_no,
                        user["tenant_id"],
                        store_id,
                        customer["customer_id"],
                        sale_type,
                        status,
                        total,
                        paid,
                        total - paid,
                        body.get("paymentMethod") or None,
                        user["username"],
                    ),
                )
            cursor.execute(
                """
                INSERT INTO sales_order_extensions(
                  order_no,sales_type,product_type,customer_status,sale_date,
                  salesperson_user_id,department_name,source,introducer,
                  introducer_mobile,remark,payment_remark,
                  finance_audit_status,discount_audit_status,attachment,
                  created_by_user_id
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE
                  sales_type=VALUES(sales_type),
                  product_type=VALUES(product_type),
                  customer_status=VALUES(customer_status),
                  sale_date=VALUES(sale_date),
                  salesperson_user_id=VALUES(salesperson_user_id),
                  department_name=VALUES(department_name),
                  source=VALUES(source),introducer=VALUES(introducer),
                  introducer_mobile=VALUES(introducer_mobile),
                  remark=VALUES(remark),
                  payment_remark=VALUES(payment_remark),
                  attachment=VALUES(attachment)
                """,
                (
                    order_no,
                    sale_type,
                    body.get("productType") or None,
                    body.get("customerStatus") or customer["status"],
                    str(body.get("saleDate") or date.today().isoformat())[:10],
                    user["user_id"],
                    body.get("department") or None,
                    body.get("source") or "PC端",
                    body.get("introducer") or None,
                    body.get("introducerMobile") or None,
                    body.get("remark") or None,
                    body.get("paymentRemark") or None,
                    "待审核" if paid else None,
                    "待审核" if body.get("discountRate") else None,
                    body.get("attachment") or None,
                    user["user_id"],
                ),
            )
            for line in lines:
                price = self._sales_decimal(line, "price")
                discount_price = self._sales_decimal(
                    line, "discountPrice", price
                )
                quantity = self._sales_decimal(
                    line, "quantity", 1, positive=True
                )
                discount = (
                    discount_price / price if price > 0 else Decimal("1")
                )
                cursor.execute(
                    """
                    INSERT INTO order_items(
                      order_no,tenant_id,item_id,name,qty,unit_price,discount
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        order_no,
                        user["tenant_id"],
                        line.get("itemId") or None,
                        line.get("itemName") or "未命名商品",
                        quantity,
                        price,
                        discount,
                    ),
                )
                item_id = cursor.lastrowid
                cursor.execute(
                    """
                    INSERT INTO sales_order_item_extensions(
                      order_item_id,item_code,product_type,unit,
                      discount_price,valid_days,warehouse,tax_rate,remark
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        item_id,
                        line.get("itemNo") or None,
                        line.get("productType") or body.get("productType"),
                        line.get("unit") or None,
                        discount_price,
                        int(line.get("validDays") or 0) or None,
                        line.get("warehouse") or None,
                        Decimal(
                            str(line.get("taxRate") or "0")
                            .replace("%", "")
                        )
                        / Decimal("100"),
                        line.get("remark") or None,
                    ),
                )
        self._sales_log(
            connection,
            user,
            store_id,
            "product-sales",
            order_no,
            "编辑" if body.get("id") else permission_action,
            None,
            status,
            {"amount": str(total)},
        )
        connection.commit()
        return self._success({"id": order_no, "status": status})

    def _save_sales_bundle(
        self, connection, user: dict, resource: str, body: dict
    ):
        bundle_id = int(body.get("id") or 0)
        self._require_sales_access(
            user, resource, "编辑" if bundle_id else "添加"
        )
        store_id = self._sales_store_id(connection, user, body)
        name_key = "packageName" if resource == "packages" else "cardName"
        name = str(body.get(name_key) or "").strip()
        if not name:
            raise ApiError("套餐名称不能为空")
        amount = self._sales_decimal(body, "packageAmount", positive=True)
        if resource == "packages":
            days = int(body.get("packageDays") or body.get("validDays") or 0)
            original_price = self._sales_decimal(body, "originalPrice", positive=True)
            activity_price = self._sales_decimal(body, "activityPrice", positive=True)
            if days <= 0 or days > 365:
                raise ApiError("套餐天数须为 1 至 365 的整数")
            if original_price < activity_price or activity_price < amount:
                raise ApiError("套餐价格须满足原价≥活动价≥成交价")
        domain = "月子套餐" if resource == "packages" else "卡类套餐"
        sub_type = (
            body.get("packageType")
            if resource == "packages"
            else body.get("cardType")
        ) or domain
        status = "启用" if body.get("enabled") else "未启用"
        audit_status = "待审核" if body.get("submit") else "待提交"
        with connection.cursor() as cursor:
            if bundle_id:
                clause, params = self._store_clause(user, "ext")
                existing = execute_one(
                    connection,
                    f"""
                    SELECT b.bundle_id
                    FROM item_bundles b
                    JOIN sales_bundle_extensions ext
                      ON ext.bundle_id=b.bundle_id
                    WHERE b.bundle_id=%s AND b.tenant_id=%s
                      AND b.deleted_at IS NULL AND b.domain=%s
                      AND {clause}
                    """,
                    [bundle_id, user["tenant_id"], domain, *params],
                )
                if not existing:
                    raise ApiError("套餐不存在或无权访问", 404, 40400)
                cursor.execute(
                    """
                    UPDATE item_bundles
                    SET name=%s,price=%s,times=%s,note=%s,status=%s,
                        version=version+1
                    WHERE bundle_id=%s
                    """,
                    (
                        name,
                        amount,
                        int(
                            body.get("cardCount")
                            or body.get("packageDays")
                            or 0
                        )
                        or None,
                        body.get("details") or None,
                        status,
                        bundle_id,
                    ),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO item_bundles(
                      tenant_id,domain,name,price,times,note,status,
                      version,created_at
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,0,NOW())
                    """,
                    (
                        user["tenant_id"],
                        domain,
                        name,
                        amount,
                        int(
                            body.get("cardCount")
                            or body.get("packageDays")
                            or 0
                        )
                        or None,
                        body.get("details") or None,
                        status,
                    ),
                )
                bundle_id = cursor.lastrowid
            bundle_no = (
                body.get("packageNo")
                or body.get("cardNo")
                or f"{'TC' if resource == 'packages' else 'KL'}-"
                f"{bundle_id:06d}"
            )
            cursor.execute(
                """
                INSERT INTO sales_bundle_extensions(
                  bundle_id,store_id,bundle_no,bundle_type,days,
                  reference_price,activity_price,effective_date,room_type,audit_status,enabled_at,
                  recommended,visible,deadline,details,room_info,
                  created_by_user_id
                ) VALUES (
                  %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
                )
                ON DUPLICATE KEY UPDATE
                  store_id=VALUES(store_id),bundle_type=VALUES(bundle_type),
                  days=VALUES(days),reference_price=VALUES(reference_price),
                  activity_price=VALUES(activity_price),effective_date=VALUES(effective_date),
                  room_type=VALUES(room_type),
                  audit_status=VALUES(audit_status),
                  enabled_at=VALUES(enabled_at),
                  recommended=VALUES(recommended),
                  visible=VALUES(visible),deadline=VALUES(deadline),
                  details=VALUES(details),room_info=VALUES(room_info)
                """,
                (
                    bundle_id,
                    store_id,
                    bundle_no,
                    sub_type,
                    int(
                        body.get("packageDays")
                        or body.get("validDays")
                        or 0
                    )
                    or None,
                    self._sales_decimal(body, "referencePrice"),
                    self._sales_decimal(body, "activityPrice"),
                    body.get("effectiveDate") or None,
                    body.get("roomType") or None,
                    audit_status,
                    body.get("enabledAt") or None,
                    int(bool(body.get("recommended"))),
                    int(body.get("visible", True) is not False),
                    body.get("deadline") or None,
                    body.get("details") or None,
                    body.get("roomInfo") or None,
                    user["user_id"],
                ),
            )
            lines = body.get("lineItems")
            if isinstance(lines, list):
                cursor.execute(
                    "DELETE FROM item_bundle_lines WHERE bundle_id=%s",
                    (bundle_id,),
                )
                for line in lines:
                    item_id = int(line.get("itemId") or 0)
                    if item_id:
                        item = execute_one(
                            connection,
                            """
                            SELECT item_id FROM items
                            WHERE item_id=%s AND tenant_id=%s
                            """,
                            (item_id, user["tenant_id"]),
                        )
                    else:
                        item = execute_one(
                            connection,
                            """
                            SELECT item_id FROM items
                            WHERE tenant_id=%s AND name=%s
                            ORDER BY item_id LIMIT 1
                            """,
                            (
                                user["tenant_id"],
                                str(line.get("itemName") or "").strip(),
                            ),
                        )
                    if not item:
                        raise ApiError(
                            "套餐明细必须选择基础资料中已存在的项目"
                        )
                    quantity = int(line.get("quantity") or 1)
                    if quantity <= 0:
                        raise ApiError("套餐明细数量必须大于0")
                    cursor.execute(
                        """
                        INSERT INTO item_bundle_lines(
                          bundle_id,tenant_id,item_id,qty
                        ) VALUES (%s,%s,%s,%s)
                        """,
                        (
                            bundle_id,
                            user["tenant_id"],
                            item["item_id"],
                            quantity,
                        ),
                    )
        self._sales_log(
            connection,
            user,
            store_id,
            resource,
            bundle_id,
            "编辑" if body.get("id") else "添加",
            None,
            audit_status,
        )
        connection.commit()
        return self._success({"id": bundle_id, "status": audit_status})

    def _save_sales_gift_list(
        self, connection, user: dict, body: dict
    ):
        record_id = int(body.get("id") or 0)
        self._require_sales_access(
            user, "gift-lists", "编辑" if record_id else "添加"
        )
        requested_store = str(body.get("store") or "").strip()
        store_id = (
            None
            if requested_store == "公共"
            and "SYS_ADMIN" in user["roles"]
            else self._sales_store_id(connection, user, body)
        )
        list_name = str(body.get("listName") or "").strip()
        if not list_name:
            raise ApiError("清单名称不能为空")
        lines = body.get("lineItems")
        if not isinstance(lines, list) or not lines:
            raise ApiError("请至少添加一条赠送物料明细")
        enabled = int(bool(body.get("enabled", True)))
        with connection.cursor() as cursor:
            if record_id:
                clause, params = self._store_clause(user, "gl")
                existing = execute_one(
                    connection,
                    f"""
                    SELECT gl.gift_list_id
                    FROM sales_gift_lists gl
                    WHERE gl.gift_list_id=%s AND gl.tenant_id=%s
                      AND gl.deleted_at IS NULL
                      AND (gl.store_id IS NULL OR {clause})
                    """,
                    [record_id, user["tenant_id"], *params],
                )
                if not existing:
                    raise ApiError("赠送清单不存在或无权访问", 404, 40400)
                cursor.execute(
                    """
                    UPDATE sales_gift_lists
                    SET store_id=%s,list_name=%s,enabled=%s,enabled_at=%s
                    WHERE gift_list_id=%s
                    """,
                    (
                        store_id,
                        list_name,
                        enabled,
                        body.get("enabledAt") or None,
                        record_id,
                    ),
                )
                cursor.execute(
                    "DELETE FROM sales_gift_list_lines WHERE gift_list_id=%s",
                    (record_id,),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO sales_gift_lists(
                      tenant_id,store_id,list_no,list_name,enabled,enabled_at,
                      created_by_user_id
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        user["tenant_id"],
                        store_id,
                        body.get("listNo") or self._sales_number("QD"),
                        list_name,
                        enabled,
                        body.get("enabledAt") or None,
                        user["user_id"],
                    ),
                )
                record_id = cursor.lastrowid
            for line in lines:
                price = self._sales_decimal(line, "price")
                quantity = self._sales_decimal(
                    line, "quantity", 1, positive=True
                )
                cursor.execute(
                    """
                    INSERT INTO sales_gift_list_lines(
                      gift_list_id,material_code,material_name,material_type,
                      specification,unit,price,quantity,remark
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        record_id,
                        line.get("materialNo") or line.get("itemNo"),
                        line.get("materialName")
                        or line.get("itemName")
                        or "未命名物料",
                        line.get("materialType")
                        or line.get("itemType"),
                        line.get("specification") or None,
                        line.get("unit") or None,
                        price,
                        quantity,
                        line.get("remark") or None,
                    ),
                )
        self._sales_log(
            connection,
            user,
            store_id,
            "gift-lists",
            record_id,
            "编辑" if body.get("id") else "添加",
            None,
            "启用" if enabled else "未启用",
        )
        connection.commit()
        return self._success({"id": record_id})

    def _save_sales_coupon_template(
        self, connection, user: dict, body: dict
    ):
        tpl_id = int(body.get("id") or 0)
        self._require_sales_access(
            user, "coupons", "编辑" if tpl_id else "添加"
        )
        store_id = self._sales_store_id(connection, user, body)
        name = self._sales_text(
            body, "couponName", "优惠券名称", required=True, max_length=50
        )
        coupon_type = self._sales_text(
            body, "couponType", "优惠券类型", required=True, max_length=30
        )
        benefit = self._sales_decimal(body, "couponAmount", positive=True)
        if benefit > Decimal("1000000"):
            raise ApiError("优惠券金额不能超过1000000")
        try:
            total_quantity = int(body.get("totalQuantity") or 0)
            valid_days = int(body.get("validDays") or 30)
            limit_per_customer = int(body.get("limitPerCustomer") or 1)
        except (TypeError, ValueError) as exc:
            raise ApiError("优惠券数量或有效期格式不正确") from exc
        if not 1 <= total_quantity <= 100000:
            raise ApiError("优惠券数量须在1至100000之间")
        if not 1 <= valid_days <= 3650:
            raise ApiError("有效期须在1至3650天之间")
        if not 1 <= limit_per_customer <= min(100, total_quantity):
            raise ApiError("单客户限领数量须为1至100，且不能超过总数量")
        starts_at = self._catalog_date(
            body.get("startsAt"), "优惠开始时间", required=True
        )
        ends_at = self._catalog_date(
            body.get("endsAt"), "优惠结束时间", required=True
        )
        if ends_at < starts_at:
            raise ApiError("优惠结束时间不能早于开始时间")
        if ends_at < date.today():
            raise ApiError("优惠结束时间不能早于今天")
        if not tpl_id and starts_at < date.today():
            raise ApiError("优惠开始时间不能早于今天")
        remark = self._sales_text(
            body, "remark", "优惠券备注", max_length=500
        )
        with connection.cursor() as cursor:
            if tpl_id:
                clause, params = self._store_clause(user, "tpl")
                existing = execute_one(
                    connection,
                    f"""
                    SELECT tpl.tpl_id,tpl.issued_qty
                    FROM coupon_templates tpl
                    WHERE tpl.tpl_id=%s AND tpl.tenant_id=%s
                      AND tpl.deleted_at IS NULL AND {clause}
                    """,
                    [tpl_id, user["tenant_id"], *params],
                )
                if not existing:
                    raise ApiError("优惠券模板不存在或无权访问", 404, 40400)
                if total_quantity < int(existing["issued_qty"] or 0):
                    raise ApiError("优惠券总数量不能小于已发放数量")
                cursor.execute(
                    """
                    UPDATE coupon_templates
                    SET store_id=%s,name=%s,type=%s,benefit=%s,
                        valid_days=%s,total_qty=%s,version=version+1
                    WHERE tpl_id=%s
                    """,
                    (
                        store_id,
                        name,
                        coupon_type,
                        benefit,
                        valid_days,
                        total_quantity,
                        tpl_id,
                    ),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO coupon_templates(
                      tenant_id,store_id,name,type,threshold,benefit,
                      valid_days,benefit_kind,total_qty,issued_qty,status,
                      version,created_at
                    ) VALUES (%s,%s,%s,%s,0,%s,%s,%s,%s,0,'启用',0,NOW())
                    """,
                    (
                        user["tenant_id"],
                        store_id,
                        name,
                        coupon_type,
                        benefit,
                        valid_days,
                        body.get("limitType") or "金额",
                        total_quantity,
                    ),
                )
                tpl_id = cursor.lastrowid
            cursor.execute(
                """
                INSERT INTO sales_coupon_template_extensions(
                  tpl_id,coupon_no,starts_at,ends_at,limit_per_customer,
                  scope,send_type,stackable,remark,created_by_user_id
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE
                  starts_at=VALUES(starts_at),ends_at=VALUES(ends_at),
                  limit_per_customer=VALUES(limit_per_customer),
                  scope=VALUES(scope),send_type=VALUES(send_type),
                  stackable=VALUES(stackable),remark=VALUES(remark)
                """,
                (
                    tpl_id,
                    f"YHQ-{tpl_id:06d}",
                    starts_at,
                    ends_at,
                    limit_per_customer,
                    body.get("scope") or "所有人",
                    body.get("sendType") or "店内发放",
                    int(bool(body.get("stackable"))),
                    remark or None,
                    user["user_id"],
                ),
            )
        self._sales_log(
            connection,
            user,
            store_id,
            "coupons",
            tpl_id,
            "编辑" if body.get("id") else "添加",
            None,
            "启用",
        )
        connection.commit()
        return self._success({"id": tpl_id})

    def _save_sales_discount(
        self, connection, user: dict, body: dict
    ):
        coupon_id = int(body.get("id") or 0)
        self._require_sales_access(
            user, "discounts", "编辑" if coupon_id else "添加"
        )
        store_id = self._sales_store_id(connection, user, body)
        customer = self._sales_customer(connection, user, body, store_id)
        benefit = self._sales_decimal(body, "couponAmount", positive=True)
        if benefit > Decimal("1000000"):
            raise ApiError("优惠券金额不能超过1000000")
        coupon_name = self._sales_text(
            body, "couponName", "优惠券名称", required=True, max_length=50
        )
        coupon_type = self._sales_text(
            body, "couponType", "优惠券类型", required=True, max_length=30
        )
        try:
            valid_days = int(body.get("validDays") or 0) or None
        except (TypeError, ValueError) as exc:
            raise ApiError("有效期格式不正确") from exc
        if valid_days is not None and not 1 <= valid_days <= 3650:
            raise ApiError("有效期须在1至3650天之间")
        starts_at = self._catalog_date(
            body.get("startsAt"), "优惠开始时间"
        )
        ends_at = self._catalog_date(body.get("endsAt"), "优惠结束时间")
        if not ends_at and valid_days:
            ends_at = date.today() + timedelta(days=valid_days)
        if starts_at and ends_at and ends_at < starts_at:
            raise ApiError("优惠结束时间不能早于开始时间")
        if ends_at and ends_at < date.today():
            raise ApiError("优惠结束时间不能早于今天")
        if not coupon_id and starts_at and starts_at < date.today():
            raise ApiError("优惠开始时间不能早于今天")
        remark = self._sales_text(
            body, "remark", "优惠券备注", max_length=500
        )
        with connection.cursor() as cursor:
            if coupon_id:
                clause, params = self._store_clause(user, "cp")
                existing = execute_one(
                    connection,
                    f"""
                    SELECT cp.coupon_id,cp.status,cp.benefit,
                           ext.remaining_amount
                    FROM coupons cp
                    JOIN sales_coupon_extensions ext
                      ON ext.coupon_id=cp.coupon_id
                    WHERE cp.coupon_id=%s AND cp.tenant_id=%s
                      AND {clause}
                    """,
                    [coupon_id, user["tenant_id"], *params],
                )
                if not existing:
                    raise ApiError("优惠记录不存在或无权访问", 404, 40400)
                if existing["status"] != "未使用" or Decimal(
                    str(existing["remaining_amount"] or 0)
                ) != Decimal(str(existing["benefit"] or 0)):
                    raise ApiError("已使用、已核销或已停用的优惠券不能编辑")
                cursor.execute(
                    """
                    UPDATE coupons
                    SET store_id=%s,customer_id=%s,type=%s,
                        benefit=%s,expire_date=%s,version=version+1
                    WHERE coupon_id=%s
                    """,
                    (
                        store_id,
                        customer["customer_id"],
                        coupon_type,
                        benefit,
                        ends_at,
                        coupon_id,
                    ),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO coupons(
                      tenant_id,store_id,customer_id,code,type,threshold,
                      benefit,status,expire_date,version,created_at
                    ) VALUES (%s,%s,%s,%s,%s,0,%s,'未使用',%s,0,NOW())
                    """,
                    (
                        user["tenant_id"],
                        store_id,
                        customer["customer_id"],
                        self._sales_number("YH"),
                        coupon_type,
                        benefit,
                        ends_at,
                    ),
                )
                coupon_id = cursor.lastrowid
            cursor.execute(
                """
                INSERT INTO sales_coupon_extensions(
                  coupon_id,coupon_name,audit_status,starts_at,remaining_amount,
                  valid_days,remark,created_by_user_id
                ) VALUES (%s,%s,'待审核',%s,%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE
                  coupon_name=VALUES(coupon_name),
                  starts_at=VALUES(starts_at),
                  remaining_amount=VALUES(remaining_amount),
                  valid_days=VALUES(valid_days),remark=VALUES(remark)
                """,
                (
                    coupon_id,
                    coupon_name,
                    starts_at,
                    benefit,
                    valid_days,
                    remark or None,
                    user["user_id"],
                ),
            )
        self._sales_log(
            connection,
            user,
            store_id,
            "discounts",
            coupon_id,
            "编辑" if body.get("id") else "添加",
            None,
            "待审核",
        )
        connection.commit()
        return self._success({"id": coupon_id, "status": "待审核"})

    def _save_sales_gift_application(
        self, connection, user: dict, body: dict
    ):
        application_id = int(body.get("id") or 0)
        sale_type = str(body.get("saleType") or "项目销售")
        action = "编辑" if application_id else {
            "项目销售": "服务销售",
            "服务销售": "服务销售",
            "物料销售": "物料销售",
            "卡类销售": "卡类销售",
        }.get(sale_type, "服务销售")
        if application_id:
            raise ApiError("旧系统未授予赠送申请编辑按钮", 403, 40300)
        self._require_sales_access(user, "gift-applications", action)
        store_id = self._sales_store_id(connection, user, body)
        customer = self._sales_customer(connection, user, body, store_id)
        lines = body.get("lineItems")
        if not isinstance(lines, list) or not lines:
            raise ApiError("请至少添加一条赠送品项")
        reason = str(body.get("giftReason") or "").strip()
        if not reason:
            raise ApiError("赠送理由不能为空")
        status = "待审核" if body.get("submit") else "待提交"
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO sales_gift_applications(
                  tenant_id,store_id,application_no,customer_id,gift_type,
                  gift_reason,consume_amount,audit_status,outbound_status,
                  attachment,created_by_user_id
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'未出库',%s,%s)
                """,
                (
                    user["tenant_id"],
                    store_id,
                    self._sales_number("ZS"),
                    customer["customer_id"],
                    body.get("giftType") or "签单赠送",
                    reason,
                    self._sales_decimal(body, "totalAmount"),
                    status,
                    body.get("attachment") or None,
                    user["user_id"],
                ),
            )
            application_id = cursor.lastrowid
            for line in lines:
                price = self._sales_decimal(line, "price")
                discount_price = self._sales_decimal(
                    line, "discountPrice", price
                )
                quantity = self._sales_decimal(
                    line, "quantity", 1, positive=True
                )
                cursor.execute(
                    """
                    INSERT INTO sales_gift_application_lines(
                      application_id,item_code,item_name,unit,price,
                      discount_price,quantity,valid_days,warehouse
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        application_id,
                        line.get("itemNo") or None,
                        line.get("itemName") or "未命名赠送品项",
                        line.get("unit") or None,
                        price,
                        discount_price,
                        quantity,
                        int(line.get("validDays") or 0) or None,
                        line.get("warehouse") or None,
                    ),
                )
        self._sales_log(
            connection,
            user,
            store_id,
            "gift-applications",
            application_id,
            action,
            None,
            status,
        )
        connection.commit()
        return self._success({"id": application_id, "status": status})

    def _sales_log(
        self,
        connection,
        user: dict,
        store_id: int | None,
        resource: str,
        record_key,
        action: str,
        before_status: str | None,
        after_status: str | None,
        detail: dict | None = None,
    ):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO sales_operation_records(
                  tenant_id,store_id,resource_key,record_key,action_name,
                  before_status,after_status,detail_json,actor_user_id
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    user["tenant_id"],
                    store_id,
                    resource,
                    str(record_key),
                    action,
                    before_status,
                    after_status,
                    compact_json(detail or {}),
                    user["user_id"],
                ),
            )

    def _perform_sales_action(
        self, connection, user: dict, resource: str, body: dict
    ):
        self._require_selected_write_store(user, body)
        action = re.sub(r"\s+", "", str(body.get("action") or ""))
        self._require_sales_access(user, resource, action)
        if action == "星支付":
            raise ApiError(
                "尚未配置真实星支付通道，禁止生成虚假支付结果",
                409,
                40900,
            )
        ids = body.get("ids") if isinstance(body.get("ids"), list) else []
        if not ids and body.get("id") not in (None, ""):
            ids = [body.get("id")]
        if not ids:
            raise ApiError("请选择销售业务记录")
        handlers = {
            "contracts": self._sales_contract_action,
            "product-sales": self._sales_order_action,
            "packages": self._sales_bundle_action,
            "card-packages": self._sales_bundle_action,
            "gift-lists": self._sales_gift_list_action,
            "discounts": self._sales_discount_action,
            "coupons": self._sales_coupon_template_action,
            "gift-applications": self._sales_gift_application_action,
        }
        handler = handlers.get(resource)
        if not handler:
            raise ApiError("当前销售页面没有可执行操作", 403, 40300)
        results = [
            handler(connection, user, resource, action, item, body)
            for item in ids
        ]
        connection.commit()
        return self._success(
            {"ids": ids, "action": action, "results": results}
        )

    def _sales_contract_action(
        self,
        connection,
        user: dict,
        resource: str,
        action: str,
        record_id,
        body: dict,
    ) -> dict:
        contract_id = int(record_id)
        clause, params = self._store_clause(user, "ct")
        row = execute_one(
            connection,
            f"""
            SELECT ct.contract_id,ct.store_id,ct.customer_id,ct.status,
                   ct.note
            FROM contracts ct
            WHERE ct.contract_id=%s AND ct.tenant_id=%s
              AND ct.deleted_at IS NULL AND {clause}
            FOR UPDATE
            """,
            [contract_id, user["tenant_id"], *params],
        )
        if not row:
            raise ApiError("合同不存在或无权访问", 404, 40400)
        before = row["status"]
        after = before
        with connection.cursor() as cursor:
            if action == "删除":
                cursor.execute(
                    "UPDATE contracts SET deleted_at=NOW() WHERE contract_id=%s",
                    (contract_id,),
                )
                after = "已删除"
            elif action == "提交":
                after = "待审核"
                cursor.execute(
                    """
                    UPDATE contracts SET status=%s,version=version+1
                    WHERE contract_id=%s
                    """,
                    (after, contract_id),
                )
            elif action in {"审核", "流程审批"}:
                result = str(body.get("auditResult") or "审核通过")
                after = "已审核" if "通过" in result else "驳回"
                cursor.execute(
                    """
                    UPDATE contracts
                    SET status=%s,approved_by_user_id=%s,approved_at=%s,
                        version=version+1
                    WHERE contract_id=%s
                    """,
                    (
                        after,
                        user["user_id"] if after == "已审核" else None,
                        datetime.now() if after == "已审核" else None,
                        contract_id,
                    ),
                )
                if after == "已审核":
                    cursor.execute(
                        """
                        UPDATE customers
                        SET status='已签合同但未入住',updated_at=NOW()
                        WHERE customer_id=%s
                        """,
                        (row["customer_id"],),
                    )
                    self._grant_contract_entitlements(
                        connection, user, contract_id
                    )
            elif action == "反审核":
                self._revoke_contract_entitlements(
                    connection, user, contract_id
                )
                after = "待审核"
                cursor.execute(
                    """
                    UPDATE contracts
                    SET status='待审核',approved_by_user_id=NULL,
                        approved_at=NULL,version=version+1
                    WHERE contract_id=%s
                    """,
                    (contract_id,),
                )
            elif action == "取消":
                self._revoke_contract_entitlements(
                    connection, user, contract_id
                )
                after = "合同中途结束"
                cursor.execute(
                    """
                    UPDATE contracts SET status=%s,note=%s,version=version+1
                    WHERE contract_id=%s
                    """,
                    (
                        after,
                        body.get("cancelReason")
                        or body.get("remark")
                        or row["note"],
                        contract_id,
                    ),
                )
            elif action == "折扣率审核":
                result = str(body.get("auditResult") or "审核通过")
                discount_status = (
                    "审核通过" if "通过" in result else "审核不通过"
                )
                cursor.execute(
                    """
                    UPDATE sales_contract_extensions
                    SET discount_audit_status=%s
                    WHERE contract_id=%s
                    """,
                    (discount_status, contract_id),
                )
            elif action in {
                "设置",
                "套餐升级",
                "膳食套餐",
                "编辑模板",
                "变更",
                "远程签约",
            }:
                detail = body.get("remark") or body.get("changeReason")
                if detail:
                    cursor.execute(
                        """
                        UPDATE contracts SET note=%s,version=version+1
                        WHERE contract_id=%s
                        """,
                        (detail, contract_id),
                    )
                if action in {"套餐升级", "变更"}:
                    cursor.execute(
                        """
                        UPDATE sales_contract_extensions
                        SET changed=1 WHERE contract_id=%s
                        """,
                        (contract_id,),
                    )
                if action == "膳食套餐":
                    meal_package = str(
                        body.get("mealPackage") or ""
                    ).strip()
                    if meal_package not in {"排餐", "点餐"}:
                        raise ApiError("请选择合同膳食套餐")
                    cursor.execute(
                        """
                        UPDATE sales_contract_extensions
                        SET meal_package=%s WHERE contract_id=%s
                        """,
                        (meal_package, contract_id),
                    )
                if action == "远程签约":
                    cursor.execute(
                        """
                        UPDATE sales_contract_extensions
                        SET remote_sign=1 WHERE contract_id=%s
                        """,
                        (contract_id,),
                    )
            else:
                raise ApiError("当前合同操作尚未实现", 403, 40300)
        self._sales_log(
            connection,
            user,
            row["store_id"],
            resource,
            contract_id,
            action,
            before,
            after,
            {"remark": body.get("remark") or body.get("auditRemark")},
        )
        return {"id": contract_id, "status": after}

    def _sales_order_action(
        self,
        connection,
        user: dict,
        resource: str,
        action: str,
        record_id,
        body: dict,
    ) -> dict:
        order_no = str(record_id)
        clause, params = self._store_clause(user, "o")
        row = execute_one(
            connection,
            f"""
            SELECT o.order_no,o.store_id,o.order_status,o.order_amount,
                   o.paid_amount,o.due_amount,ext.enabled,ext.outbound_no
            FROM orders o
            JOIN sales_order_extensions ext ON ext.order_no=o.order_no
            WHERE o.order_no=%s AND o.tenant_id=%s
              AND o.deleted_at IS NULL AND {clause}
            FOR UPDATE
            """,
            [order_no, user["tenant_id"], *params],
        )
        if not row:
            raise ApiError("销售单不存在或无权访问", 404, 40400)
        before = row["order_status"]
        after = before
        with connection.cursor() as cursor:
            if action == "删除":
                cursor.execute(
                    "UPDATE orders SET deleted_at=NOW() WHERE order_no=%s",
                    (order_no,),
                )
                after = "已删除"
            elif action == "退货":
                if before not in {"已支付", "已出库"}:
                    raise ApiError("只有已支付或已出库单据可以退货")
                after = "已退货"
                cursor.execute(
                    """
                    UPDATE orders SET order_status=%s,version=version+1
                    WHERE order_no=%s
                    """,
                    (after, order_no),
                )
                cursor.execute(
                    """
                    UPDATE sales_order_extensions
                    SET returned_at=NOW() WHERE order_no=%s
                    """,
                    (order_no,),
                )
            elif action == "取消退货":
                if before != "已退货":
                    raise ApiError("只有已退货单据可以取消退货")
                after = "已出库" if row["outbound_no"] else "已支付"
                cursor.execute(
                    """
                    UPDATE orders SET order_status=%s,version=version+1
                    WHERE order_no=%s
                    """,
                    (after, order_no),
                )
                cursor.execute(
                    """
                    UPDATE sales_order_extensions
                    SET returned_at=NULL WHERE order_no=%s
                    """,
                    (order_no,),
                )
            elif action == "取消":
                after = "已取消"
                cursor.execute(
                    """
                    UPDATE orders SET order_status=%s,version=version+1
                    WHERE order_no=%s
                    """,
                    (after, order_no),
                )
            elif action == "收款":
                amount = self._sales_decimal(
                    body, "amount", body.get("paymentAmount"), positive=True
                )
                paid = Decimal(str(row["paid_amount"] or 0)) + amount
                total = Decimal(str(row["order_amount"] or 0))
                if paid > total:
                    raise ApiError("累计收款金额不能超过销售总金额")
                due = total - paid
                after = "已支付" if due == 0 else "部分支付"
                cursor.execute(
                    """
                    UPDATE orders
                    SET paid_amount=%s,due_amount=%s,order_status=%s,
                        pay_method=%s,version=version+1,updated_at=NOW()
                    WHERE order_no=%s
                    """,
                    (
                        paid,
                        due,
                        after,
                        body.get("paymentMethod") or None,
                        order_no,
                    ),
                )
                cursor.execute(
                    """
                    UPDATE sales_order_extensions
                    SET payment_remark=%s,finance_audit_status='待审核'
                    WHERE order_no=%s
                    """,
                    (body.get("remark") or None, order_no),
                )
            elif action == "出库":
                if before not in {"已支付", "已付未出库"}:
                    raise ApiError("只有已支付单据可以出库")
                after = "已出库"
                outbound_no = self._sales_number("CK")
                cursor.execute(
                    """
                    UPDATE orders SET order_status=%s,version=version+1
                    WHERE order_no=%s
                    """,
                    (after, order_no),
                )
                cursor.execute(
                    """
                    UPDATE sales_order_extensions
                    SET outbound_no=%s WHERE order_no=%s
                    """,
                    (outbound_no, order_no),
                )
            elif action == "是否启用":
                cursor.execute(
                    """
                    UPDATE sales_order_extensions
                    SET enabled=IF(enabled=1,0,1) WHERE order_no=%s
                    """,
                    (order_no,),
                )
            elif action == "介绍分配":
                cursor.execute(
                    """
                    UPDATE sales_order_extensions
                    SET introducer=%s,introducer_mobile=%s
                    WHERE order_no=%s
                    """,
                    (
                        body.get("introducer") or None,
                        body.get("introducerMobile") or None,
                        order_no,
                    ),
                )
            elif action == "折扣率审核":
                result = str(body.get("auditResult") or "审核通过")
                cursor.execute(
                    """
                    UPDATE sales_order_extensions
                    SET discount_audit_status=%s WHERE order_no=%s
                    """,
                    (
                        "审核通过" if "通过" in result else "审核不通过",
                        order_no,
                    ),
                )
            elif action == "变更":
                cursor.execute(
                    """
                    UPDATE sales_order_extensions SET remark=%s
                    WHERE order_no=%s
                    """,
                    (
                        body.get("changeReason")
                        or body.get("remark")
                        or None,
                        order_no,
                    ),
                )
            else:
                raise ApiError("当前销售单操作尚未实现", 403, 40300)
        self._sales_log(
            connection,
            user,
            row["store_id"],
            resource,
            order_no,
            action,
            before,
            after,
            {"amount": body.get("amount")},
        )
        return {"id": order_no, "status": after}

    def _sales_bundle_action(
        self,
        connection,
        user: dict,
        resource: str,
        action: str,
        record_id,
        body: dict,
    ) -> dict:
        bundle_id = int(record_id)
        domain = "月子套餐" if resource == "packages" else "卡类套餐"
        clause, params = self._store_clause(user, "ext")
        row = execute_one(
            connection,
            f"""
            SELECT b.bundle_id,b.tenant_id,b.domain,b.name,b.price,b.times,
                   b.note,b.status,b.version,ext.store_id,ext.bundle_type,
                   ext.days,ext.reference_price,ext.room_type,
                   ext.audit_status,ext.enabled_at,ext.recommended,
                   ext.visible,ext.deadline,ext.details,ext.room_info
            FROM item_bundles b
            JOIN sales_bundle_extensions ext ON ext.bundle_id=b.bundle_id
            WHERE b.bundle_id=%s AND b.tenant_id=%s
              AND b.deleted_at IS NULL AND b.domain=%s AND {clause}
            FOR UPDATE
            """,
            [bundle_id, user["tenant_id"], domain, *params],
        )
        if not row:
            raise ApiError("套餐不存在或无权访问", 404, 40400)
        before = row["audit_status"]
        after = before
        with connection.cursor() as cursor:
            if action == "删除":
                cursor.execute(
                    """
                    UPDATE item_bundles SET deleted_at=NOW()
                    WHERE bundle_id=%s
                    """,
                    (bundle_id,),
                )
                after = "已删除"
            elif action == "提交":
                after = "待审核"
                cursor.execute(
                    """
                    UPDATE sales_bundle_extensions SET audit_status=%s
                    WHERE bundle_id=%s
                    """,
                    (after, bundle_id),
                )
            elif action in {"审核", "流程审批"}:
                result = str(body.get("auditResult") or "审核通过")
                after = "审核通过" if "通过" in result else "审核不通过"
                cursor.execute(
                    """
                    UPDATE sales_bundle_extensions SET audit_status=%s
                    WHERE bundle_id=%s
                    """,
                    (after, bundle_id),
                )
            elif action == "反审核":
                after = "待审核"
                cursor.execute(
                    """
                    UPDATE sales_bundle_extensions SET audit_status=%s
                    WHERE bundle_id=%s
                    """,
                    (after, bundle_id),
                )
            elif action == "启用":
                cursor.execute(
                    """
                    UPDATE item_bundles SET status='启用',version=version+1
                    WHERE bundle_id=%s
                    """,
                    (bundle_id,),
                )
                cursor.execute(
                    """
                    UPDATE sales_bundle_extensions SET enabled_at=NOW()
                    WHERE bundle_id=%s
                    """,
                    (bundle_id,),
                )
            elif action == "推荐/取消":
                cursor.execute(
                    """
                    UPDATE sales_bundle_extensions
                    SET recommended=IF(recommended=1,0,1),
                        recommended_at=IF(recommended=0,NOW(),NULL)
                    WHERE bundle_id=%s
                    """,
                    (bundle_id,),
                )
            elif action == "屏蔽/取消":
                cursor.execute(
                    """
                    UPDATE sales_bundle_extensions
                    SET visible=IF(visible=1,0,1) WHERE bundle_id=%s
                    """,
                    (bundle_id,),
                )
            elif action == "设置":
                cursor.execute(
                    """
                    UPDATE sales_bundle_extensions
                    SET details=COALESCE(%s,details)
                    WHERE bundle_id=%s
                    """,
                    (body.get("remark") or None, bundle_id),
                )
            elif action == "复制":
                cursor.execute(
                    """
                    INSERT INTO item_bundles(
                      tenant_id,domain,name,price,times,note,status,
                      version,created_at
                    ) VALUES (%s,%s,%s,%s,%s,%s,'未启用',0,NOW())
                    """,
                    (
                        row["tenant_id"],
                        row["domain"],
                        f"{row['name']}-副本",
                        row["price"],
                        row["times"],
                        row["note"],
                    ),
                )
                clone_id = cursor.lastrowid
                cursor.execute(
                    """
                    INSERT INTO sales_bundle_extensions(
                      bundle_id,store_id,bundle_no,bundle_type,days,
                      reference_price,room_type,audit_status,enabled_at,
                      recommended,visible,deadline,details,room_info,
                      created_by_user_id
                    ) VALUES (
                      %s,%s,%s,%s,%s,%s,%s,'待提交',NULL,0,%s,%s,%s,%s,%s
                    )
                    """,
                    (
                        clone_id,
                        row["store_id"],
                        f"{'TC' if resource == 'packages' else 'KL'}-"
                        f"{clone_id:06d}",
                        row["bundle_type"],
                        row["days"],
                        row["reference_price"],
                        row["room_type"],
                        row["visible"],
                        row["deadline"],
                        row["details"],
                        row["room_info"],
                        user["user_id"],
                    ),
                )
                after = "待提交"
            else:
                raise ApiError("当前套餐操作尚未实现", 403, 40300)
        self._sales_log(
            connection,
            user,
            row["store_id"],
            resource,
            bundle_id,
            action,
            before,
            after,
        )
        return {"id": bundle_id, "status": after}

    def _sales_gift_list_action(
        self,
        connection,
        user: dict,
        resource: str,
        action: str,
        record_id,
        body: dict,
    ) -> dict:
        if action != "删除":
            raise ApiError("当前赠送清单操作尚未实现", 403, 40300)
        gift_list_id = int(record_id)
        clause, params = self._store_clause(user, "gl")
        row = execute_one(
            connection,
            f"""
            SELECT gl.gift_list_id,gl.store_id
            FROM sales_gift_lists gl
            WHERE gl.gift_list_id=%s AND gl.tenant_id=%s
              AND gl.deleted_at IS NULL
              AND (gl.store_id IS NULL OR {clause})
            """,
            [gift_list_id, user["tenant_id"], *params],
        )
        if not row:
            raise ApiError("赠送清单不存在或无权访问", 404, 40400)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE sales_gift_lists SET deleted_at=NOW()
                WHERE gift_list_id=%s
                """,
                (gift_list_id,),
            )
        self._sales_log(
            connection,
            user,
            row["store_id"],
            resource,
            gift_list_id,
            action,
            "启用",
            "已删除",
        )
        return {"id": gift_list_id, "status": "已删除"}

    def _sales_discount_action(
        self,
        connection,
        user: dict,
        resource: str,
        action: str,
        record_id,
        body: dict,
    ) -> dict:
        coupon_id = int(record_id)
        clause, params = self._store_clause(user, "cp")
        row = execute_one(
            connection,
            f"""
            SELECT cp.coupon_id,cp.store_id,cp.status,cp.benefit,
                   cp.expire_date,cp.order_ref,cp.used_at,
                   ext.audit_status,ext.starts_at,ext.remaining_amount
            FROM coupons cp
            JOIN sales_coupon_extensions ext ON ext.coupon_id=cp.coupon_id
            WHERE cp.coupon_id=%s AND cp.tenant_id=%s AND {clause}
            FOR UPDATE
            """,
            [coupon_id, user["tenant_id"], *params],
        )
        if not row:
            raise ApiError("优惠记录不存在或无权访问", 404, 40400)
        before = row["audit_status"]
        after = before
        log_detail = {}
        with connection.cursor() as cursor:
            if action == "删除":
                if Decimal(str(row["remaining_amount"] or 0)) != Decimal(
                    str(row["benefit"] or 0)
                ):
                    raise ApiError("已发生核销的优惠券不能删除")
                cursor.execute(
                    "UPDATE coupons SET status='已删除' WHERE coupon_id=%s",
                    (coupon_id,),
                )
                after = "已删除"
            elif action == "审核":
                if row["status"] != "未使用":
                    raise ApiError("只有未使用的优惠券可以审核")
                result = str(body.get("auditResult") or "审核通过")
                after = (
                    "审核不通过"
                    if "不通过" in result or "驳回" in result
                    else "已通过"
                )
                audit_remark = self._sales_text(
                    body, "auditRemark", "审核意见", max_length=500
                )
                cursor.execute(
                    """
                    UPDATE sales_coupon_extensions
                    SET audit_status=%s,audit_remark=%s,
                        auditor_user_id=%s
                    WHERE coupon_id=%s
                    """,
                    (
                        after,
                        audit_remark or None,
                        user["user_id"],
                        coupon_id,
                    ),
                )
            elif action == "反审核":
                if row["status"] != "未使用":
                    raise ApiError("已使用或已停用的优惠券不能反审核")
                after = "待审核"
                cursor.execute(
                    """
                    UPDATE sales_coupon_extensions
                    SET audit_status='待审核',auditor_user_id=NULL
                    WHERE coupon_id=%s
                    """,
                    (coupon_id,),
                )
            elif action == "核销":
                if row["audit_status"] != "已通过":
                    raise ApiError("优惠券审核通过后才能核销")
                if row["status"] not in ("未使用", "部分使用"):
                    raise ApiError("当前优惠券状态不允许核销")
                starts_at = self._catalog_date(
                    row.get("starts_at"), "优惠开始时间"
                )
                expire_date = self._catalog_date(
                    row.get("expire_date"), "优惠结束时间"
                )
                if starts_at and starts_at > date.today():
                    raise ApiError("优惠券尚未到生效日期")
                if expire_date and expire_date < date.today():
                    raise ApiError("优惠券已过期")
                consume_amount = self._sales_decimal(
                    body, "consumeAmount", positive=True
                )
                if consume_amount > Decimal("1000000"):
                    raise ApiError("本次核销金额不能超过1000000")
                remaining = Decimal(str(row["remaining_amount"] or 0))
                if consume_amount > remaining:
                    raise ApiError("本次核销金额不能超过剩余金额")
                sale_no = self._sales_text(
                    body,
                    "saleNo",
                    "关联业务单号",
                    required=True,
                    max_length=64,
                )
                redeem_remark = self._sales_text(
                    body,
                    "remark",
                    "核销说明",
                    required=True,
                    max_length=500,
                )
                new_remaining = remaining - consume_amount
                after = "已核销" if new_remaining == 0 else "部分使用"
                cursor.execute(
                    """
                    UPDATE coupons
                    SET status=%s,used_at=NOW(),order_ref=%s,
                        version=version+1
                    WHERE coupon_id=%s
                    """,
                    (after, sale_no, coupon_id),
                )
                cursor.execute(
                    """
                    UPDATE sales_coupon_extensions
                    SET remaining_amount=%s
                    WHERE coupon_id=%s
                    """,
                    (new_remaining, coupon_id),
                )
                log_detail = {
                    "saleNo": sale_no,
                    "consumeAmount": str(consume_amount),
                    "remainingAmount": str(new_remaining),
                    "remark": redeem_remark,
                }
            elif action == "停用":
                if row["status"] in ("已核销", "已删除", "已停用"):
                    raise ApiError("当前优惠券状态不允许停用")
                disable_reason = self._sales_text(
                    body,
                    "disableReason",
                    "停用原因",
                    required=True,
                    max_length=500,
                )
                after = "已停用"
                cursor.execute(
                    "UPDATE coupons SET status='已停用' WHERE coupon_id=%s",
                    (coupon_id,),
                )
                cursor.execute(
                    """
                    UPDATE sales_coupon_extensions SET disable_reason=%s
                    WHERE coupon_id=%s
                    """,
                    (disable_reason, coupon_id),
                )
                log_detail = {"disableReason": disable_reason}
            else:
                raise ApiError("当前优惠操作尚未实现", 403, 40300)
        self._sales_log(
            connection,
            user,
            row["store_id"],
            resource,
            coupon_id,
            action,
            before,
            after,
            log_detail,
        )
        return {"id": coupon_id, "status": after}

    def _sales_coupon_template_action(
        self,
        connection,
        user: dict,
        resource: str,
        action: str,
        record_id,
        body: dict,
    ) -> dict:
        tpl_id = int(record_id)
        clause, params = self._store_clause(user, "tpl")
        row = execute_one(
            connection,
            f"""
            SELECT tpl.tpl_id,tpl.store_id,tpl.name,tpl.type,tpl.benefit,
                   tpl.valid_days,tpl.total_qty,tpl.issued_qty,tpl.status
            FROM coupon_templates tpl
            WHERE tpl.tpl_id=%s AND tpl.tenant_id=%s
              AND tpl.deleted_at IS NULL AND {clause}
            FOR UPDATE
            """,
            [tpl_id, user["tenant_id"], *params],
        )
        if not row:
            raise ApiError("优惠券模板不存在或无权访问", 404, 40400)
        if action == "删除":
            if int(row["issued_qty"] or 0) > 0:
                raise ApiError("已有发放记录的优惠券模板不能删除")
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE coupon_templates SET deleted_at=NOW()
                    WHERE tpl_id=%s
                    """,
                    (tpl_id,),
                )
            self._sales_log(
                connection,
                user,
                row["store_id"],
                resource,
                tpl_id,
                action,
                row["status"],
                "已删除",
            )
            return {"id": tpl_id, "status": "已删除"}
        if action != "分发":
            raise ApiError("当前优惠券操作尚未实现", 403, 40300)
        if row["status"] != "启用":
            raise ApiError("只有启用中的优惠券模板可以分发")
        store_id = int(row["store_id"])
        customer = self._sales_customer(
            connection,
            user,
            {
                "customerId": body.get("customerId"),
                "customerName": body.get("customerName"),
                "mobile": body.get("mobile"),
            },
            store_id,
        )
        try:
            quantity = int(body.get("quantity") or 1)
        except (TypeError, ValueError) as exc:
            raise ApiError("发放数量格式不正确") from exc
        if not 1 <= quantity <= 100:
            raise ApiError("单次发放数量须在1至100之间")
        remark = self._sales_text(
            body, "remark", "发放说明", max_length=500
        )
        ext = execute_one(
            connection,
            """
            SELECT starts_at,ends_at,limit_per_customer
            FROM sales_coupon_template_extensions WHERE tpl_id=%s
            """,
            (tpl_id,),
        )
        starts_at = self._catalog_date(
            ext.get("starts_at"), "优惠开始时间"
        )
        ends_at = self._catalog_date(ext.get("ends_at"), "优惠结束时间")
        if starts_at and starts_at > date.today():
            raise ApiError("优惠券尚未到可发放日期")
        if ends_at and ends_at < date.today():
            raise ApiError("优惠券已超过发放截止日期")
        if int(row["issued_qty"] or 0) + quantity > int(
            row["total_qty"] or 0
        ):
            raise ApiError("发放数量超过模板剩余可发行数量")
        already = execute_one(
            connection,
            """
            SELECT COUNT(*) AS total FROM coupons
            WHERE tenant_id=%s AND tpl_id=%s AND customer_id=%s
              AND status<>'已删除'
            """,
            (user["tenant_id"], tpl_id, customer["customer_id"]),
        )
        if int(already["total"] or 0) + quantity > int(
            ext["limit_per_customer"] or 1
        ):
            raise ApiError("超过单客户可领用数量")
        expire_date = (
            ext.get("ends_at")
            or (date.today() + timedelta(days=int(row["valid_days"] or 30)))
        )
        with connection.cursor() as cursor:
            for _ in range(quantity):
                cursor.execute(
                    """
                    INSERT INTO coupons(
                      tenant_id,store_id,tpl_id,customer_id,code,type,
                      threshold,benefit,status,expire_date,version,created_at
                    ) VALUES (%s,%s,%s,%s,%s,%s,0,%s,'未使用',%s,0,NOW())
                    """,
                    (
                        user["tenant_id"],
                        store_id,
                        tpl_id,
                        customer["customer_id"],
                        self._sales_number("YH"),
                        row["type"],
                        row["benefit"],
                        expire_date,
                    ),
                )
                coupon_id = cursor.lastrowid
                cursor.execute(
                    """
                    INSERT INTO sales_coupon_extensions(
                      coupon_id,coupon_name,audit_status,starts_at,
                      remaining_amount,
                      valid_days,remark,created_by_user_id
                    ) VALUES (%s,%s,'已通过',%s,%s,%s,%s,%s)
                    """,
                    (
                        coupon_id,
                        row["name"],
                        ext.get("starts_at"),
                        row["benefit"],
                        row["valid_days"],
                        remark or None,
                        user["user_id"],
                    ),
                )
            cursor.execute(
                """
                UPDATE coupon_templates
                SET issued_qty=issued_qty+%s,version=version+1
                WHERE tpl_id=%s
                """,
                (quantity, tpl_id),
            )
        self._sales_log(
            connection,
            user,
            store_id,
            resource,
            tpl_id,
            action,
            row["status"],
            row["status"],
            {
                "customerId": customer["customer_id"],
                "quantity": quantity,
            },
        )
        return {"id": tpl_id, "issued": quantity}

    def _sales_gift_application_action(
        self,
        connection,
        user: dict,
        resource: str,
        action: str,
        record_id,
        body: dict,
    ) -> dict:
        application_id = int(record_id)
        clause, params = self._store_clause(user, "ga")
        row = execute_one(
            connection,
            f"""
            SELECT ga.application_id,ga.store_id,ga.audit_status
            FROM sales_gift_applications ga
            WHERE ga.application_id=%s AND ga.tenant_id=%s
              AND ga.deleted_at IS NULL AND {clause}
            FOR UPDATE
            """,
            [application_id, user["tenant_id"], *params],
        )
        if not row:
            raise ApiError("赠送申请不存在或无权访问", 404, 40400)
        before = row["audit_status"]
        after = before
        with connection.cursor() as cursor:
            if action == "删除":
                cursor.execute(
                    """
                    UPDATE sales_gift_applications SET deleted_at=NOW()
                    WHERE application_id=%s
                    """,
                    (application_id,),
                )
                after = "已删除"
            elif action == "流程审批":
                result = str(body.get("auditResult") or "审核通过")
                after = "审核通过" if "通过" in result else "审核不通过"
                cursor.execute(
                    """
                    UPDATE sales_gift_applications
                    SET audit_status=%s,approved_by_user_id=%s,
                        approved_at=%s
                    WHERE application_id=%s
                    """,
                    (
                        after,
                        user["user_id"] if after == "审核通过" else None,
                        datetime.now()
                        if after == "审核通过"
                        else None,
                        application_id,
                    ),
                )
            elif action == "反审核":
                after = "待审核"
                cursor.execute(
                    """
                    UPDATE sales_gift_applications
                    SET audit_status='待审核',approved_by_user_id=NULL,
                        approved_at=NULL
                    WHERE application_id=%s
                    """,
                    (application_id,),
                )
            elif action == "撤回":
                after = "待提交"
                cursor.execute(
                    """
                    UPDATE sales_gift_applications
                    SET audit_status='待提交'
                    WHERE application_id=%s
                    """,
                    (application_id,),
                )
            else:
                raise ApiError("当前赠送申请操作尚未实现", 403, 40300)
        self._sales_log(
            connection,
            user,
            row["store_id"],
            resource,
            application_id,
            action,
            before,
            after,
        )
        return {"id": application_id, "status": after}

    def _get_room_module_data(
        self, connection, user: dict, resource: str, query: dict
    ):
        self._require_room_access(user, resource)
        if resource in {"room-map", "room-trend", "smart-allocation"}:
            result = self._room_inventory_rows(connection, user, query)
            payload = {"list": result, "total": len(result)}
            if resource == "smart-allocation":
                payload["customers"] = self._room_bookable_customers(
                    connection, user
                )
                # Smart allocation needs the same active, store-scoped package
                # price rules that are used when a contract is created.  Keep
                # this separate from room inventory so a store with no package
                # master data (currently the centre store) can still allocate
                # rooms by room type.
                payload["packages"] = self._room_allocation_packages(
                    connection, user, query
                )
            payload["stores"] = self._room_store_options(connection, user)
            return self._success(payload)
        if resource == "room-type-trend":
            rows = self._room_type_trend_rows(connection, user, query)
            return self._success({"list": rows, "total": len(rows)})
        if resource == "saleable-statistics":
            rows = self._room_saleable_rows(connection, user, query)
            return self._success({"list": rows, "total": len(rows)})
        if resource in {
            "room-type-bookings",
            "room-reservations",
            "room-stays",
        }:
            rows = self._room_booking_rows(connection, user, resource, query)
            return self._success({"list": rows, "total": len(rows)})
        loaders = {
            "stay-extensions": self._room_extension_rows,
            "room-change-applications": self._room_change_rows,
            "gift-distribution": self._room_gift_rows,
            "room-services": self._room_service_rows,
            "outing-applications": self._room_outing_rows,
            "borrowed-items": self._room_borrow_rows,
            "laundry": self._room_laundry_rows,
        }
        loader = loaders.get(resource)
        if not loader:
            raise ApiError("客房资源不存在", 404, 40400)
        rows = loader(connection, user)
        return self._success({"list": rows, "total": len(rows)})

    def _room_store_options(self, connection, user: dict) -> list:
        clause, params = self._store_clause(user, "s")
        return execute_all(
            connection,
            f"""
            SELECT s.store_id AS id, s.name
            FROM stores s
            WHERE s.tenant_id=%s AND {clause}
            ORDER BY s.sort_weight DESC, s.store_id
            """,
            [user["tenant_id"], *params],
        )

    def _room_store_matches(self, requested: str, actual: str) -> bool:
        if not requested or requested == "全部":
            return True
        if requested == actual:
            return True
        if "黄河路" in requested:
            return "黄河路" in actual
        if "中心广场" in requested or "建设路" in requested:
            return "中心广场" in actual or "建设路" in actual
        return False

    def _room_inventory_rows(
        self, connection, user: dict, query: dict | None = None
    ) -> list:
        query = query or {}
        clause, params = self._store_clause(user, "r")
        rows = execute_all(
            connection,
            f"""
            SELECT r.room_id AS id, r.room_no AS room, r.store_id AS storeId,
                   s.name AS store,
                   COALESCE(rt.name, r.room_type) AS roomType,
                   COALESCE(rt.layout_name, r.room_type) AS roomStyle,
                   r.floor, r.direction, r.status, r.price,
                   r.note AS remark, c.name AS customerName
            FROM rooms r
            JOIN stores s ON s.store_id=r.store_id
            LEFT JOIN room_types rt ON rt.room_type_id=r.room_type_id
            LEFT JOIN customers c ON c.customer_id=r.customer_id
            WHERE r.tenant_id=%s AND r.deleted_at IS NULL AND {clause}
            ORDER BY r.store_id, r.floor, r.layout_order, r.room_no
            """,
            [user["tenant_id"], *params],
        )
        booking_clause, booking_params = self._store_clause(user, "rb")
        booking_rows = execute_all(
            connection,
            f"""
            SELECT rb.booking_id AS id, rb.room_id AS roomId,
                   rb.customer_id AS customerId, rb.contract_id AS contractId,
                   c.name AS customerName, c.phone AS mobile,
                   c.wechat, c.id_type AS idType, c.id_no AS idNo,
                   c.birthday, c.gender, c.age, c.native,
                   c.source AS customerSource, c.status AS customerStatus,
                   c.edc, c.parity, c.prenatal_hospital AS prenatalHospital,
                   c.meal_package AS mealPackage,
                   c.remark AS customerRemark,
                   ct.contract_no AS contractNo,
                   ct.package_name AS packageName,
                   ct.amount AS contractAmount,
                   rb.status, rb.check_in AS startAt, rb.check_out AS endAt,
                   rb.actual_check_in_at AS checkInAt,
                   rb.actual_check_out_at AS actualCheckOutAt,
                   DATEDIFF(rb.check_out, rb.check_in) AS totalDays
            FROM room_bookings rb
            JOIN customers c ON c.customer_id=rb.customer_id
            LEFT JOIN contracts ct ON ct.contract_id=rb.contract_id
            WHERE rb.tenant_id=%s AND rb.deleted_at IS NULL
              AND {booking_clause}
              AND rb.status IN ('已订房','已入住','已退房')
            ORDER BY rb.check_in, rb.booking_id
            """,
            [user["tenant_id"], *booking_params],
        )
        bookings_by_room = {}
        for booking in booking_rows:
            total_days = int(booking.get("totalDays") or 0)
            end_value = str(booking.get("endAt") or "")[:10]
            end_date = (
                datetime.strptime(end_value, "%Y-%m-%d").date()
                if end_value
                else None
            )
            booking["totalDays"] = total_days
            booking["remainingDays"] = max(
                0, (end_date - date.today()).days if end_date else 0
            )
            booking["stayedDays"] = max(
                0, total_days - booking["remainingDays"]
            )
            booking["plannedCheckInAt"] = booking.get("startAt")
            booking["expectedCheckOutAt"] = booking.get("endAt")
            booking["roomStatus"] = booking.get("status")
            bookings_by_room.setdefault(booking["roomId"], []).append(booking)
        requested_store = str(query.get("store") or "").strip()
        requested_room = str(query.get("room") or "").strip()
        requested_type = str(query.get("roomType") or "").strip()
        requested_direction = str(query.get("direction") or "").strip()
        requested_floor = str(query.get("floor") or "").strip()
        if requested_store and not any(
            self._room_store_matches(
                requested_store, str(row.get("store") or "")
            )
            for row in rows
        ):
            requested_store = ""
        status_keys = {
            "入住": "occupied",
            "已入住": "occupied",
            "预约": "reserved",
            "已订房": "reserved",
            "空闲": "available",
            "待清洁": "cleaning",
            "脏房": "cleaning",
            "维修": "maintenance",
            "员工入住": "staff",
        }
        result = []
        for row in rows:
            raw_floor = row.get("floor")
            row["floorNumber"] = raw_floor
            row["floor"] = (
                f"{raw_floor}楼" if raw_floor not in (None, "") else ""
            )
            row["statusKey"] = status_keys.get(
                row.get("status"), "available"
            )
            room_bookings = bookings_by_room.get(row["id"], [])
            row["stays"] = [
                item
                for item in room_bookings
                if item.get("status") in {"已订房", "已入住"}
            ]
            row["bookings"] = row["stays"]
            row["pastStays"] = [
                {
                    **item,
                    "room": row["room"],
                    "roomType": row["roomType"],
                    "roomStyle": row["roomStyle"],
                }
                for item in room_bookings
                if item.get("status") == "已退房"
            ]
            row["detailCount"] = len(
                [item for item in row["stays"] if item["status"] == "已订房"]
            )
            row["availableRange"] = (
                "暂无入住安排"
                if not row["stays"]
                else "、".join(
                    f"{item['startAt']}~{item['endAt']}"
                    for item in row["stays"]
                )
            )
            if not self._room_store_matches(
                requested_store, str(row.get("store") or "")
            ):
                continue
            if requested_room and requested_room not in str(row["room"]):
                continue
            if requested_type and requested_type not in str(row["roomType"]):
                continue
            if requested_direction and requested_direction != row["direction"]:
                continue
            if requested_floor and requested_floor not in str(row["floor"]):
                continue
            result.append(row)
        return result

    def _room_allocation_packages(
        self, connection, user: dict, query: dict | None = None
    ) -> list:
        """Return active package versions grouped for smart allocation.

        A package version can have several price rules, one for each allowed
        room type.  The allocation page needs one selectable package per
        store/day combination plus the complete set of allowed room types.
        """
        clause, params = self._store_clause(user, "s")
        rows = execute_all(
            connection,
            f"""
            SELECT pp.package_code AS basePackageCode,
                   pp.package_name AS packageName,
                   s.name AS store,
                   pr.stay_days AS days,
                   MIN(pr.reference_amount) AS referencePrice,
                   GROUP_CONCAT(
                     DISTINCT rt.name ORDER BY rt.sort_order SEPARATOR '|'
                   ) AS allowedRoomTypes
            FROM package_products pp
            JOIN package_versions pv ON pv.package_id=pp.package_id
            JOIN package_price_rules pr
              ON pr.package_version_id=pv.package_version_id
            JOIN stores s ON s.store_id=pr.store_id
            JOIN room_types rt ON rt.room_type_id=pr.room_type_id
            WHERE pp.tenant_id=%s AND pp.deleted_at IS NULL
              AND pp.status='ACTIVE'
              AND pv.version_status='ACTIVE'
              AND pr.status='ACTIVE'
              AND pv.effective_from<=CURDATE()
              AND (pv.effective_to IS NULL OR pv.effective_to>=CURDATE())
              AND pr.effective_from<=CURDATE()
              AND (pr.effective_to IS NULL OR pr.effective_to>=CURDATE())
              AND {clause}
            GROUP BY pp.package_code, pp.package_name, s.name,
                     pr.stay_days, pp.sort_order
            ORDER BY s.name, pp.sort_order, pp.package_name, pr.stay_days
            """,
            [user["tenant_id"], *params],
        )
        requested_store = str((query or {}).get("store") or "").strip()
        result = []
        packages_by_no = {}
        for row in rows:
            if requested_store and not self._room_store_matches(
                requested_store, str(row.get("store") or "")
            ):
                continue
            row["days"] = int(row.get("days") or 0)
            row["packageNo"] = f"{row['basePackageCode']}@{row['days']}"
            row["allowedRoomTypes"] = [
                item for item in str(row.get("allowedRoomTypes") or "").split("|")
                if item
            ]
            existing = packages_by_no.get(row["packageNo"])
            if not existing:
                packages_by_no[row["packageNo"]] = row
                result.append(row)
                continue
            existing["allowedRoomTypes"] = list(dict.fromkeys(
                [*existing.get("allowedRoomTypes", []), *row["allowedRoomTypes"]]
            ))
            if row.get("referencePrice") is not None and (
                existing.get("referencePrice") is None
                or row["referencePrice"] < existing["referencePrice"]
            ):
                existing["referencePrice"] = row["referencePrice"]
        return result

    def _room_bookable_customers(self, connection, user: dict) -> list:
        clause, params = self._store_clause(user, "c")
        rows = execute_all(
            connection,
            f"""
            SELECT c.customer_id AS id, c.name AS customerName,
                   c.phone AS mobile, c.status, s.name AS store,
                   ct.contract_id AS contractId, ct.contract_no AS contractNo,
                   ct.package_name AS packageName,
                   ct.amount AS contractAmount, ct.paid AS paidAmount,
                   GREATEST(ct.amount-COALESCE(ct.paid,0),0)
                     AS outstandingAmount,
                   ct.days AS bookableDays,
                   ct.expected_check_in AS birthDate,
                   COALESCE(c.intent_room, '') AS reservedRoomType,
                   staff.name AS salesperson
            FROM customers c
            JOIN stores s ON s.store_id=c.store_id
            JOIN contracts ct
              ON ct.customer_id=c.customer_id AND ct.deleted_at IS NULL
             AND ct.status='已审核'
            LEFT JOIN staff ON staff.staff_id=c.sales_staff_id
            WHERE c.tenant_id=%s AND c.deleted_at IS NULL AND {clause}
              AND COALESCE(ct.paid,0)>0
              AND NOT EXISTS (
                SELECT 1 FROM room_bookings rb
                WHERE rb.contract_id=ct.contract_id
                  AND rb.deleted_at IS NULL
                  AND rb.status IN ('已订房','已入住')
              )
            ORDER BY c.customer_id DESC
            LIMIT 1000
            """,
            [user["tenant_id"], *params],
        )
        for row in rows:
            row["status"] = "- 未订房 -"
        return rows

    def _room_type_trend_rows(
        self, connection, user: dict, query: dict
    ) -> list:
        inventory = self._room_inventory_rows(connection, user, query)
        grouped = {}
        for room in inventory:
            item = grouped.setdefault(
                room["roomType"],
                {"id": room["roomType"], "roomType": room["roomType"],
                 "total": 0, "bookings": [], "maintenance": 0},
            )
            item["total"] += 1
            item["bookings"].extend(room.get("bookings") or [])
            if room.get("status") in {"维修", "脏房"}:
                item["maintenance"] += 1
        return list(grouped.values())

    def _room_saleable_rows(
        self, connection, user: dict, query: dict
    ) -> list:
        rooms = self._room_inventory_rows(connection, user, query)
        date_range = query.get("stayRange")
        if isinstance(date_range, str):
            try:
                date_range = json.loads(date_range)
            except json.JSONDecodeError:
                date_range = []
        start_text = (
            str((date_range or [None])[0] or date.today())[:10]
        )
        end_text = (
            str((date_range or [None, None])[1] or start_text)[:10]
        )
        start_date = datetime.strptime(start_text, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_text, "%Y-%m-%d").date()

        def available_starts(room: dict, duration: int) -> int:
            count = 0
            cursor = start_date
            while cursor + timedelta(days=duration) <= end_date:
                candidate_end = cursor + timedelta(days=duration)
                conflict = any(
                    not (
                        str(item.get("endAt") or "")[:10]
                        <= cursor.isoformat()
                        or str(item.get("startAt") or "")[:10]
                        >= candidate_end.isoformat()
                    )
                    for item in room.get("bookings") or []
                )
                if not conflict and room.get("status") not in {"维修", "脏房"}:
                    count += 1
                cursor += timedelta(days=1)
            return count

        result = []
        for room in rooms:
            result.append(
                {
                    "id": room["id"],
                    "room": room["room"],
                    "roomStatus": room["status"],
                    "days28": available_starts(room, 28),
                    "days7": available_starts(room, 7),
                    "days10": available_starts(room, 10),
                    "days42": available_starts(room, 42),
                }
            )
        return result

    def _room_booking_rows(
        self, connection, user: dict, resource: str, query: dict
    ) -> list:
        clause, params = self._store_clause(user, "rb")
        status_sql = ""
        if resource == "room-reservations":
            status_sql = "AND rb.status='已订房'"
        elif resource == "room-stays":
            status_sql = "AND rb.status IN ('已入住','已退房','已取消')"
        rows = execute_all(
            connection,
            f"""
            SELECT rb.booking_id AS id, rb.booking_no AS bookingNo,
                   rb.customer_id AS customerId, rb.contract_id AS contractId,
                   rb.room_id AS roomId, r.room_no AS room,
                   COALESCE(rt.name, r.room_type) AS roomType,
                   c.name AS customerName, c.phone AS mobile,
                   c.status AS customerStatus, s.name AS store,
                   contract_store.name AS contractStore,
                   ct.contract_no AS contractName,
                   ct.amount AS contractAmount, ct.days AS contractDays,
                   DATEDIFF(rb.check_out, rb.check_in) AS roomDays,
                   rb.check_in AS plannedCheckInAt,
                   rb.check_out AS plannedCheckOutAt,
                   rb.actual_check_in_at AS checkInAt,
                   COALESCE(rb.actual_check_out_at, rb.check_out) AS checkOutAt,
                   DATEDIFF(rb.check_out, rb.check_in) AS plannedDays,
                   CASE WHEN rb.status='已入住' THEN '入住'
                        WHEN rb.status='已订房' THEN '预约'
                        WHEN rb.status='已退房' THEN '退房'
                        ELSE rb.status END AS roomStatus,
                   rb.amount, rb.note AS remark, rb.created_at AS createdAt,
                   creator.username AS creator,
                   CASE WHEN rb.status='已订房' THEN '正常'
                        ELSE rb.status END AS roomTypeStatus,
                   CASE WHEN DATEDIFF(rb.check_out, rb.check_in)>0
                        THEN COALESCE(ct.amount,0) /
                             DATEDIFF(rb.check_out, rb.check_in)
                        ELSE 0 END AS dailyAmount,
                   GREATEST(COALESCE(ct.amount,0)-COALESCE(ct.paid,0),0)
                     AS balanceAmount,
                   COALESCE(extension_totals.extensionDays,0)
                     AS extensionDays,
                   extension_totals.extensionAt,
                   COALESCE(extension_totals.extensionAmount,0)
                     AS extensionAmount,
                   COALESCE(extension_totals.receivedExtensionAmount,0)
                     AS receivedExtensionAmount
            FROM room_bookings rb
            JOIN rooms r ON r.room_id=rb.room_id
            JOIN stores s ON s.store_id=rb.store_id
            JOIN customers c ON c.customer_id=rb.customer_id
            LEFT JOIN room_types rt ON rt.room_type_id=r.room_type_id
            LEFT JOIN contracts ct ON ct.contract_id=rb.contract_id
            LEFT JOIN stores contract_store
              ON contract_store.store_id=ct.store_id
            LEFT JOIN user_accounts creator
              ON creator.user_id=rb.created_by_user_id
            LEFT JOIN (
              SELECT booking_id, SUM(extension_days) AS extensionDays,
                     MAX(start_at) AS extensionAt,
                     SUM(extension_amount) AS extensionAmount,
                     SUM(received_amount) AS receivedExtensionAmount
              FROM room_stay_extensions
              WHERE deleted_at IS NULL AND status<>'已取消'
              GROUP BY booking_id
            ) extension_totals
              ON extension_totals.booking_id=rb.booking_id
            WHERE rb.tenant_id=%s AND rb.deleted_at IS NULL
              AND {clause} {status_sql}
            ORDER BY rb.booking_id DESC
            LIMIT 1000
            """,
            [user["tenant_id"], *params],
        )
        return rows

    def _room_extension_rows(self, connection, user: dict) -> list:
        clause, params = self._store_clause(user, "e")
        return execute_all(
            connection,
            f"""
            SELECT e.extension_id AS id, r.room_no AS room,
                   c.name AS customerName, c.phone AS mobile,
                   e.extension_amount AS extensionAmount,
                   e.received_amount AS receivedAmount,
                   0 AS unpostedAmount,
                   GREATEST(e.extension_amount-e.received_amount,0)
                     AS debtAmount,
                   e.extension_days AS extensionDays,
                   e.start_at AS startAt, e.end_at AS endAt,
                   e.remark, e.extension_salesperson AS extensionSalesperson,
                   creator.username AS salesperson,
                   e.created_at AS createdAt, e.created_at AS signedAt,
                   e.status, e.audit_status AS auditStatus,
                   e.approved_at AS auditedAt, approver.username AS auditor,
                   '' AS attachment, e.extension_type AS extensionType,
                   e.status AS extensionStatus, s.name AS store,
                   e.booking_id AS bookingId
            FROM room_stay_extensions e
            JOIN rooms r ON r.room_id=e.room_id
            JOIN customers c ON c.customer_id=e.customer_id
            JOIN stores s ON s.store_id=e.store_id
            JOIN user_accounts creator ON creator.user_id=e.created_by_user_id
            LEFT JOIN user_accounts approver
              ON approver.user_id=e.approved_by_user_id
            WHERE e.tenant_id=%s AND e.deleted_at IS NULL AND {clause}
            ORDER BY e.extension_id DESC
            LIMIT 1000
            """,
            [user["tenant_id"], *params],
        )

    def _room_change_rows(self, connection, user: dict) -> list:
        clause, params = self._store_clause(user, "a")
        return execute_all(
            connection,
            f"""
            SELECT a.change_id AS id, c.name AS customerName,
                   c.phone AS mobile, source_room.room_no AS room,
                   target_room.room_no AS targetRoom,
                   a.changed_at AS changedAt, a.reason,
                   a.audit_status AS auditStatus,
                   approver.username AS auditor,
                   a.audit_opinion AS auditOpinion,
                   a.approved_at AS auditedAt,
                   applicant.username AS applicant,
                   a.created_at AS appliedAt, s.name AS store,
                   a.booking_id AS bookingId
            FROM room_change_applications a
            JOIN customers c ON c.customer_id=a.customer_id
            JOIN rooms source_room
              ON source_room.room_id=a.source_room_id
            JOIN rooms target_room
              ON target_room.room_id=a.target_room_id
            JOIN stores s ON s.store_id=a.store_id
            JOIN user_accounts applicant
              ON applicant.user_id=a.applicant_user_id
            LEFT JOIN user_accounts approver
              ON approver.user_id=a.approved_by_user_id
            WHERE a.tenant_id=%s AND a.deleted_at IS NULL AND {clause}
            ORDER BY a.change_id DESC
            LIMIT 1000
            """,
            [user["tenant_id"], *params],
        )

    def _room_gift_rows(self, connection, user: dict) -> list:
        clause, params = self._store_clause(user, "g")
        return execute_all(
            connection,
            f"""
            SELECT g.distribution_id AS id, ct.contract_no AS contractName,
                   r.room_no AS room, c.name AS customerName,
                   rb.check_in AS plannedCheckInAt,
                   ct.status AS auditStatus, salesperson.name AS salesperson,
                   dept.name AS department, g.gift_status AS giftStatus,
                   g.gift_items AS customGift, s.name AS store,
                   g.booking_id AS bookingId
            FROM room_gift_distributions g
            JOIN customers c ON c.customer_id=g.customer_id
            JOIN stores s ON s.store_id=g.store_id
            LEFT JOIN contracts ct ON ct.contract_id=g.contract_id
            LEFT JOIN room_bookings rb ON rb.booking_id=g.booking_id
            LEFT JOIN rooms r ON r.room_id=g.room_id
            LEFT JOIN staff salesperson
              ON salesperson.staff_id=c.sales_staff_id
            LEFT JOIN departments dept
              ON dept.department_id=salesperson.department_id
            WHERE g.tenant_id=%s AND g.deleted_at IS NULL AND {clause}
            ORDER BY g.distribution_id DESC
            LIMIT 1000
            """,
            [user["tenant_id"], *params],
        )

    def _room_service_rows(self, connection, user: dict) -> list:
        clause, params = self._store_clause(user, "request")
        return execute_all(
            connection,
            f"""
            SELECT request.service_id AS id, r.room_no AS room,
                   c.name AS customerName,
                   COALESCE(rt.name,r.room_type) AS roomType,
                   COALESCE(rt.layout_name,r.room_type) AS roomStyle,
                   request.service_type AS serviceType,
                   request.applied_at AS appliedAt,
                   request.service_status AS serviceStatus,
                   request.remark, staff.name AS serviceStaff,
                   COALESCE(request.completed_at,request.scheduled_at)
                     AS serviceAt,
                   s.name AS store, request.booking_id AS bookingId
            FROM room_service_requests request
            JOIN rooms r ON r.room_id=request.room_id
            JOIN stores s ON s.store_id=request.store_id
            LEFT JOIN room_types rt ON rt.room_type_id=r.room_type_id
            LEFT JOIN customers c ON c.customer_id=request.customer_id
            LEFT JOIN staff ON staff.staff_id=request.service_staff_id
            WHERE request.tenant_id=%s AND request.deleted_at IS NULL
              AND {clause}
            ORDER BY request.service_id DESC
            LIMIT 1000
            """,
            [user["tenant_id"], *params],
        )

    def _room_outing_rows(self, connection, user: dict) -> list:
        clause, params = self._store_clause(user, "outing")
        return execute_all(
            connection,
            f"""
            SELECT outing.outing_id AS id, c.name AS customerName,
                   CONCAT(outing.start_at,' — ',outing.expected_return_at)
                     AS outingAt,
                   outing.outing_days AS outingDays, outing.reason,
                   outing.escort, dept.name AS department,
                   outing.created_at AS createdAt,
                   creator.username AS creator,
                   outing.outing_status AS outingStatus,
                   outing.person_type AS personType,
                   outing.returned_at AS returnedAt, s.name AS store,
                   outing.customer_id AS customerId,
                   outing.booking_id AS bookingId
            FROM room_outing_applications outing
            JOIN customers c ON c.customer_id=outing.customer_id
            JOIN stores s ON s.store_id=outing.store_id
            JOIN user_accounts creator
              ON creator.user_id=outing.created_by_user_id
            LEFT JOIN departments dept
              ON dept.department_id=creator.department_id
            WHERE outing.tenant_id=%s AND outing.deleted_at IS NULL
              AND {clause}
            ORDER BY outing.outing_id DESC
            LIMIT 1000
            """,
            [user["tenant_id"], *params],
        )

    def _room_borrow_rows(self, connection, user: dict) -> list:
        clause, params = self._store_clause(user, "borrow")
        return execute_all(
            connection,
            f"""
            SELECT borrow.borrow_id AS id, r.room_no AS room,
                   c.name AS customerName, borrow.item_name AS itemName,
                   borrow.borrowed_at AS borrowedAt,
                   creator.username AS creator, borrow.remark,
                   borrow.return_status AS returnStatus,
                   borrow.expected_return_at AS expectedReturnAt,
                   borrow.signed_at AS signedAt, borrow.signer,
                   s.name AS store, borrow.deposit,
                   borrow.deposit_paid AS depositPaid, borrow.rent,
                   borrow.rent_paid AS rentPaid,
                   borrow.customer_id AS customerId,
                   borrow.booking_id AS bookingId
            FROM room_borrowed_items borrow
            JOIN rooms r ON r.room_id=borrow.room_id
            JOIN customers c ON c.customer_id=borrow.customer_id
            JOIN stores s ON s.store_id=borrow.store_id
            JOIN user_accounts creator
              ON creator.user_id=borrow.created_by_user_id
            WHERE borrow.tenant_id=%s AND borrow.deleted_at IS NULL
              AND {clause}
            ORDER BY borrow.borrow_id DESC
            LIMIT 1000
            """,
            [user["tenant_id"], *params],
        )

    def _room_laundry_rows(self, connection, user: dict) -> list:
        clause, params = self._store_clause(user, "laundry")
        return execute_all(
            connection,
            f"""
            SELECT laundry.laundry_id AS id, r.room_no AS room,
                   laundry.department, c.name AS customerName,
                   laundry.sent_at AS sentAt,
                   laundry.special_requirement AS specialRequirement,
                   laundry.sign_status AS signStatus, laundry.signer,
                   laundry.signed_at AS signedAt, laundry.remark,
                   creator.username AS creator, s.name AS store,
                   laundry.customer_id AS customerId,
                   laundry.booking_id AS bookingId
            FROM room_laundry_records laundry
            JOIN rooms r ON r.room_id=laundry.room_id
            JOIN customers c ON c.customer_id=laundry.customer_id
            JOIN stores s ON s.store_id=laundry.store_id
            JOIN user_accounts creator
              ON creator.user_id=laundry.created_by_user_id
            WHERE laundry.tenant_id=%s AND laundry.deleted_at IS NULL
              AND {clause}
            ORDER BY laundry.laundry_id DESC
            LIMIT 1000
            """,
            [user["tenant_id"], *params],
        )

    def _post_room_resource(
        self, connection, user: dict, resource: str, body: dict
    ):
        match = re.fullmatch(r"/modules/([^/]+)/(save|action)", resource)
        if not match:
            raise ApiError("客房资源不存在", 404, 40400)
        module, operation = match.groups()
        if module not in ROOM_RESOURCE_NAV_IDS:
            raise ApiError("客房资源不存在", 404, 40400)
        if operation == "save":
            return self._save_room_record(connection, user, module, body)
        return self._perform_room_action(connection, user, module, body)

    def _room_store_id(
        self, connection, user: dict, body: dict, key: str = "store"
    ) -> int:
        explicit_id = body.get(f"{key}Id")
        if explicit_id:
            return self._allowed_store(user, explicit_id)
        requested = str(body.get(key) or "").strip()
        if requested:
            for store in self._room_store_options(connection, user):
                if self._room_store_matches(requested, store["name"]):
                    return int(store["id"])
            raise ApiError("当前账号无权访问所选门店", 403, 40300)
        default_id = user.get("default_store_id")
        if default_id:
            return self._allowed_store(user, default_id)
        if len(user["store_ids"]) == 1:
            return int(user["store_ids"][0])
        raise ApiError("请选择门店")

    def _room_customer(
        self, connection, user: dict, body: dict, store_id: int
    ) -> dict:
        customer_id = int(body.get("customerId") or 0)
        if customer_id:
            row = execute_one(
                connection,
                """
                SELECT customer_id, store_id, name, phone
                FROM customers
                WHERE customer_id=%s AND tenant_id=%s AND deleted_at IS NULL
                """,
                (customer_id, user["tenant_id"]),
            )
        else:
            name = str(body.get("customerName") or "").strip()
            phone = str(body.get("mobile") or "").strip()
            if not name:
                raise ApiError("请选择现有客户")
            row = execute_one(
                connection,
                """
                SELECT customer_id, store_id, name, phone
                FROM customers
                WHERE tenant_id=%s AND deleted_at IS NULL AND name=%s
                  AND (%s='' OR phone=%s)
                ORDER BY customer_id DESC
                LIMIT 1
                """,
                (user["tenant_id"], name, phone, phone),
            )
        if not row:
            raise ApiError("客户不存在，请先在客户管理建档")
        self._allowed_store(user, row["store_id"])
        return row

    def _room_contract(
        self, connection, user: dict, customer_id: int, body: dict
    ) -> dict:
        contract_id = int(body.get("contractId") or 0)
        if contract_id:
            row = execute_one(
                connection,
                """
                SELECT contract_id, store_id, customer_id, contract_no,
                       status, amount, paid,
                       expected_check_in, expected_check_out
                FROM contracts
                WHERE contract_id=%s AND tenant_id=%s AND deleted_at IS NULL
                """,
                (contract_id, user["tenant_id"]),
            )
        else:
            row = execute_one(
                connection,
                """
                SELECT contract_id, store_id, customer_id, contract_no,
                       status, amount, paid,
                       expected_check_in, expected_check_out
                FROM contracts
                WHERE tenant_id=%s AND customer_id=%s
                  AND deleted_at IS NULL AND status='已审核'
                ORDER BY contract_id DESC
                LIMIT 1
                """,
                (user["tenant_id"], customer_id),
            )
        if not row or row["customer_id"] != customer_id:
            raise ApiError("客户没有可用于订房的已审核合同")
        if row["status"] != "已审核":
            raise ApiError("只有已审核合同可以订房")
        if Decimal(str(row.get("paid") or 0)) <= 0:
            raise ApiError("至少一笔收款审核入账后才可以订房")
        return row

    def _room_by_body(
        self,
        connection,
        user: dict,
        body: dict,
        store_id: int,
        key: str = "room",
        allow_auto: bool = False,
    ) -> dict:
        room_id = int(body.get(f"{key}Id") or 0)
        if not room_id and key == "room":
            room_id = int(body.get("roomId") or 0)
        room_no = str(body.get(key) or "").strip()
        room_type = str(body.get("roomType") or "").strip()
        if room_id:
            row = execute_one(
                connection,
                """
                SELECT room_id, store_id, room_no, room_type, status,
                       customer_id
                FROM rooms
                WHERE room_id=%s AND tenant_id=%s AND deleted_at IS NULL
                """,
                (room_id, user["tenant_id"]),
            )
        elif room_no:
            row = execute_one(
                connection,
                """
                SELECT room_id, store_id, room_no, room_type, status,
                       customer_id
                FROM rooms
                WHERE tenant_id=%s AND store_id=%s AND room_no=%s
                  AND deleted_at IS NULL
                """,
                (user["tenant_id"], store_id, room_no),
            )
        elif allow_auto and room_type:
            row = execute_one(
                connection,
                """
                SELECT r.room_id, r.store_id, r.room_no, r.room_type,
                       r.status, r.customer_id
                FROM rooms r
                LEFT JOIN room_types rt
                  ON rt.room_type_id=r.room_type_id
                WHERE r.tenant_id=%s AND r.store_id=%s
                  AND r.deleted_at IS NULL AND r.status='空闲'
                  AND (r.room_type=%s OR rt.name=%s OR rt.package_name=%s)
                ORDER BY r.floor, r.layout_order, r.room_no
                LIMIT 1
                """,
                (
                    user["tenant_id"],
                    store_id,
                    room_type,
                    room_type,
                    room_type,
                ),
            )
        else:
            row = None
        if not row:
            raise ApiError("未找到可用房间")
        self._allowed_store(user, row["store_id"])
        if int(row["store_id"]) != int(store_id):
            raise ApiError("房间不属于所选门店")
        return row

    def _room_active_booking(
        self,
        connection,
        user: dict,
        body: dict,
        resource: str,
    ) -> dict:
        booking_id = int(body.get("bookingId") or 0)
        if not booking_id and resource in {
            "room-reservations",
            "room-stays",
            "room-type-bookings",
        }:
            booking_id = int(body.get("id") or 0)
        if booking_id:
            row = execute_one(
                connection,
                """
                SELECT booking_id, tenant_id, store_id, room_id, customer_id,
                       contract_id, check_in, check_out, status
                FROM room_bookings
                WHERE booking_id=%s AND tenant_id=%s AND deleted_at IS NULL
                """,
                (booking_id, user["tenant_id"]),
            )
        else:
            room_id = int(body.get("roomId") or 0)
            if not room_id and resource == "room-map":
                room_id = int(body.get("id") or 0)
            row = execute_one(
                connection,
                """
                SELECT booking_id, tenant_id, store_id, room_id, customer_id,
                       contract_id, check_in, check_out, status
                FROM room_bookings
                WHERE tenant_id=%s AND room_id=%s AND deleted_at IS NULL
                  AND status IN ('已订房','已入住')
                ORDER BY FIELD(status,'已入住','已订房'), booking_id DESC
                LIMIT 1
                """,
                (user["tenant_id"], room_id),
            )
        if not row:
            raise ApiError("未找到当前订房或入住记录")
        self._allowed_store(user, row["store_id"])
        return row

    def _save_room_record(
        self, connection, user: dict, resource: str, body: dict
    ):
        action = re.sub(r"\s+", "", str(body.get("_action") or ""))
        if not action:
            action = "编辑" if body.get("id") else "添加"
        self._require_room_access(user, resource, action)
        if resource in {
            "room-map",
            "smart-allocation",
            "room-type-bookings",
            "room-reservations",
            "room-stays",
        }:
            return self._save_room_booking(
                connection, user, resource, body, action
            )
        if resource == "stay-extensions":
            return self._save_room_extension(connection, user, body)
        if resource == "outing-applications":
            return self._save_room_outing(connection, user, body)
        if resource == "borrowed-items":
            return self._save_room_borrow(connection, user, body)
        if resource == "laundry":
            return self._save_room_laundry(connection, user, body)
        raise ApiError("当前客房页面不支持新增或编辑", 403, 40300)

    def _save_room_booking(
        self,
        connection,
        user: dict,
        resource: str,
        body: dict,
        action: str,
    ):
        booking_id = int(body.get("id") or 0)
        if resource in {"room-map", "smart-allocation"}:
            booking_id = int(body.get("bookingId") or 0)
        if booking_id:
            booking = self._room_active_booking(
                connection, user, {**body, "bookingId": booking_id}, resource
            )
            check_in = str(
                body.get("plannedCheckInAt")
                or body.get("checkInAt")
                or booking["check_in"]
            )[:10]
            check_out = str(
                body.get("plannedCheckOutAt")
                or body.get("checkOutAt")
                or booking["check_out"]
            )[:10]
            room = self._room_by_body(
                connection,
                user,
                body,
                booking["store_id"],
                allow_auto=True,
            )
            if not check_in or not check_out or check_in >= check_out:
                raise ApiError("预住日期必须早于预离开日期")
            if check_in < date.today().isoformat():
                raise ApiError("预住日期不能早于今天")
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE room_bookings
                    SET room_id=%s, check_in=%s, check_out=%s, note=%s,
                        version=version+1
                    WHERE booking_id=%s
                    """,
                    (
                        room["room_id"],
                        check_in,
                        check_out,
                        body.get("remark"),
                        booking_id,
                    ),
                )
            self._audit(
                connection,
                user,
                "ROOM_BOOKING",
                booking_id,
                "UPDATE",
                booking["store_id"],
                booking["status"],
                booking["status"],
            )
            connection.commit()
            return self._success({"id": booking_id})
        store_id = self._room_store_id(connection, user, body)
        customer = self._room_customer(connection, user, body, store_id)
        contract = self._room_contract(
            connection, user, customer["customer_id"], body
        )
        if int(contract["store_id"]) != store_id:
            raise ApiError("订房门店必须与合同门店一致")
        room_body = dict(body)
        if resource == "room-map" and body.get("id") and not body.get("roomId"):
            room_body["roomId"] = body["id"]
        room = self._room_by_body(
            connection,
            user,
            room_body,
            store_id,
            allow_auto=action in {"房型订房", "订房"},
        )
        check_in = str(
            body.get("plannedCheckInAt")
            or body.get("startDate1")
            or contract.get("expected_check_in")
            or ""
        )[:10]
        check_out = str(
            body.get("plannedCheckOutAt")
            or body.get("endDate1")
            or contract.get("expected_check_out")
            or ""
        )[:10]
        if not check_in or not check_out or check_in >= check_out:
            raise ApiError("预住日期必须早于预离开日期")
        if check_in < date.today().isoformat():
            raise ApiError("预住日期不能早于今天")
        contract_conflict = execute_one(
            connection,
            """
            SELECT booking_id FROM room_bookings
            WHERE contract_id=%s AND deleted_at IS NULL
              AND status IN ('已订房','已入住')
              AND NOT (check_out<=%s OR check_in>=%s)
            LIMIT 1
            """,
            (contract["contract_id"], check_in, check_out),
        )
        if contract_conflict:
            raise ApiError("该合同在所选日期已有订房记录")
        conflict = execute_one(
            connection,
            """
            SELECT booking_id FROM room_bookings
            WHERE room_id=%s AND deleted_at IS NULL
              AND status IN ('已订房','已入住')
              AND NOT (check_out<=%s OR check_in>=%s)
            LIMIT 1
            """,
            (room["room_id"], check_in, check_out),
        )
        if conflict:
            raise ApiError("所选日期内房间已被占用")
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO room_bookings(
                  tenant_id, store_id, room_id, customer_id, contract_id,
                  check_in, check_out, status, note, version, created_at,
                  source, created_by_user_id
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,'已订房',%s,0,NOW(),
                          'ERP_ROOM',%s)
                """,
                (
                    user["tenant_id"],
                    store_id,
                    room["room_id"],
                    customer["customer_id"],
                    contract["contract_id"],
                    check_in,
                    check_out,
                    body.get("remark"),
                    user["user_id"],
                ),
            )
            booking_id = cursor.lastrowid
            cursor.execute(
                "UPDATE room_bookings SET booking_no=%s WHERE booking_id=%s",
                (f"KF-{datetime.now():%Y%m%d}-{booking_id:05d}", booking_id),
            )
            cursor.execute(
                "UPDATE rooms SET status='已订房' WHERE room_id=%s",
                (room["room_id"],),
            )
            cursor.execute(
                "UPDATE customers SET status='已订房',updated_at=NOW() "
                "WHERE customer_id=%s",
                (customer["customer_id"],),
            )
        self._audit(
            connection,
            user,
            "ROOM_BOOKING",
            booking_id,
            "CREATE",
            store_id,
            None,
            "已订房",
            {"action": action, "roomId": room["room_id"]},
        )
        connection.commit()
        return self._success({"id": booking_id})

    def _save_room_extension(
        self, connection, user: dict, body: dict
    ):
        extension_id = int(body.get("id") or 0)
        booking = self._room_active_booking(
            connection, user, body, "room-stays"
        )
        start_at = str(body.get("startAt") or booking["check_out"])[:10]
        end_at = str(body.get("endAt") or "")[:10]
        days = int(body.get("extensionDays") or 0)
        if not end_at and days > 0:
            end_at = (
                datetime.strptime(start_at, "%Y-%m-%d").date()
                + timedelta(days=days)
            ).isoformat()
        if not start_at or not end_at or start_at >= end_at:
            raise ApiError("续住开始日期必须早于结束日期")
        if days <= 0:
            days = (
                datetime.strptime(end_at, "%Y-%m-%d").date()
                - datetime.strptime(start_at, "%Y-%m-%d").date()
            ).days
        if extension_id:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE room_stay_extensions
                    SET extension_type=%s,start_at=%s,end_at=%s,
                        extension_days=%s,extension_amount=%s,
                        extension_salesperson=%s,remark=%s,version=version+1
                    WHERE extension_id=%s AND tenant_id=%s
                    """,
                    (
                        body.get("extensionType") or "月子续住",
                        start_at,
                        end_at,
                        days,
                        body.get("extensionAmount") or 0,
                        body.get("extensionSalesperson"),
                        body.get("remark"),
                        extension_id,
                        user["tenant_id"],
                    ),
                )
            record_id = extension_id
        else:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO room_stay_extensions(
                      tenant_id,store_id,booking_id,customer_id,room_id,
                      extension_type,start_at,end_at,extension_days,
                      extension_amount,received_amount,status,audit_status,
                      remark,extension_salesperson,created_by_user_id
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,0,
                              '待续住','待审核',%s,%s,%s)
                    """,
                    (
                        user["tenant_id"],
                        booking["store_id"],
                        booking["booking_id"],
                        booking["customer_id"],
                        booking["room_id"],
                        body.get("extensionType") or "月子续住",
                        start_at,
                        end_at,
                        days,
                        body.get("extensionAmount") or 0,
                        body.get("remark"),
                        body.get("extensionSalesperson"),
                        user["user_id"],
                    ),
                )
                record_id = cursor.lastrowid
        self._audit(
            connection,
            user,
            "ROOM_EXTENSION",
            record_id,
            "UPDATE" if extension_id else "CREATE",
            booking["store_id"],
            None,
            "待审核",
        )
        connection.commit()
        return self._success({"id": record_id})

    def _save_room_outing(self, connection, user: dict, body: dict):
        outing_id = int(body.get("id") or 0)
        store_id = self._room_store_id(connection, user, body)
        customer = self._room_customer(connection, user, body, store_id)
        booking = execute_one(
            connection,
            """
            SELECT booking_id FROM room_bookings
            WHERE tenant_id=%s AND customer_id=%s AND store_id=%s
              AND deleted_at IS NULL AND status='已入住'
            ORDER BY booking_id DESC LIMIT 1
            """,
            (user["tenant_id"], customer["customer_id"], store_id),
        )
        start_at = body.get("startAt")
        end_at = body.get("endAt")
        if not start_at or not end_at:
            raise ApiError("请填写外出和预计返回时间")
        values = (
            customer["customer_id"],
            (booking or {}).get("booking_id"),
            body.get("personType") or "产妇",
            start_at,
            end_at,
            int(body.get("outingDays") or 0),
            body.get("escort"),
            body.get("reason"),
        )
        with connection.cursor() as cursor:
            if outing_id:
                cursor.execute(
                    """
                    UPDATE room_outing_applications
                    SET customer_id=%s,booking_id=%s,person_type=%s,
                        start_at=%s,expected_return_at=%s,outing_days=%s,
                        escort=%s,reason=%s,version=version+1
                    WHERE outing_id=%s AND tenant_id=%s
                    """,
                    (*values, outing_id, user["tenant_id"]),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO room_outing_applications(
                      tenant_id,store_id,booking_id,customer_id,person_type,
                      start_at,expected_return_at,outing_days,escort,reason,
                      outing_status,created_by_user_id
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                              '从未被审核',%s)
                    """,
                    (
                        user["tenant_id"],
                        store_id,
                        (booking or {}).get("booking_id"),
                        customer["customer_id"],
                        body.get("personType") or "产妇",
                        start_at,
                        end_at,
                        int(body.get("outingDays") or 0),
                        body.get("escort"),
                        body.get("reason"),
                        user["user_id"],
                    ),
                )
                outing_id = cursor.lastrowid
        connection.commit()
        return self._success({"id": outing_id})

    def _save_room_borrow(self, connection, user: dict, body: dict):
        borrow_id = int(body.get("id") or 0)
        store_id = self._room_store_id(connection, user, body)
        customer = self._room_customer(connection, user, body, store_id)
        room = self._room_by_body(connection, user, body, store_id)
        booking = execute_one(
            connection,
            """
            SELECT booking_id FROM room_bookings
            WHERE tenant_id=%s AND customer_id=%s AND room_id=%s
              AND deleted_at IS NULL AND status='已入住'
            ORDER BY booking_id DESC LIMIT 1
            """,
            (user["tenant_id"], customer["customer_id"], room["room_id"]),
        )
        if not body.get("itemName") or not body.get("borrowedAt"):
            raise ApiError("借用物品和借物时间不能为空")
        with connection.cursor() as cursor:
            if borrow_id:
                cursor.execute(
                    """
                    UPDATE room_borrowed_items
                    SET customer_id=%s,room_id=%s,item_name=%s,borrowed_at=%s,
                        expected_return_at=%s,deposit=%s,rent=%s,remark=%s
                    WHERE borrow_id=%s AND tenant_id=%s
                    """,
                    (
                        customer["customer_id"],
                        room["room_id"],
                        body.get("itemName"),
                        body.get("borrowedAt"),
                        body.get("expectedReturnAt") or None,
                        body.get("deposit") or 0,
                        body.get("rent") or 0,
                        body.get("remark"),
                        borrow_id,
                        user["tenant_id"],
                    ),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO room_borrowed_items(
                      tenant_id,store_id,booking_id,customer_id,room_id,
                      item_name,borrowed_at,expected_return_at,deposit,rent,
                      return_status,remark,created_by_user_id
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'未还',%s,%s)
                    """,
                    (
                        user["tenant_id"],
                        store_id,
                        (booking or {}).get("booking_id"),
                        customer["customer_id"],
                        room["room_id"],
                        body.get("itemName"),
                        body.get("borrowedAt"),
                        body.get("expectedReturnAt") or None,
                        body.get("deposit") or 0,
                        body.get("rent") or 0,
                        body.get("remark"),
                        user["user_id"],
                    ),
                )
                borrow_id = cursor.lastrowid
        connection.commit()
        return self._success({"id": borrow_id})

    def _save_room_laundry(self, connection, user: dict, body: dict):
        laundry_id = int(body.get("id") or 0)
        store_id = self._room_store_id(connection, user, body)
        customer = self._room_customer(connection, user, body, store_id)
        room = self._room_by_body(connection, user, body, store_id)
        booking = execute_one(
            connection,
            """
            SELECT booking_id FROM room_bookings
            WHERE tenant_id=%s AND customer_id=%s AND room_id=%s
              AND deleted_at IS NULL AND status='已入住'
            ORDER BY booking_id DESC LIMIT 1
            """,
            (user["tenant_id"], customer["customer_id"], room["room_id"]),
        )
        if not body.get("department") or not body.get("sentAt"):
            raise ApiError("送洗部门和送洗时间不能为空")
        with connection.cursor() as cursor:
            if laundry_id:
                cursor.execute(
                    """
                    UPDATE room_laundry_records
                    SET customer_id=%s,room_id=%s,department=%s,sent_at=%s,
                        special_requirement=%s,remark=%s
                    WHERE laundry_id=%s AND tenant_id=%s
                    """,
                    (
                        customer["customer_id"],
                        room["room_id"],
                        body.get("department"),
                        body.get("sentAt"),
                        body.get("specialRequirement"),
                        body.get("remark"),
                        laundry_id,
                        user["tenant_id"],
                    ),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO room_laundry_records(
                      tenant_id,store_id,booking_id,customer_id,room_id,
                      department,sent_at,special_requirement,sign_status,
                      remark,created_by_user_id
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'未签收',%s,%s)
                    """,
                    (
                        user["tenant_id"],
                        store_id,
                        (booking or {}).get("booking_id"),
                        customer["customer_id"],
                        room["room_id"],
                        body.get("department"),
                        body.get("sentAt"),
                        body.get("specialRequirement"),
                        body.get("remark"),
                        user["user_id"],
                    ),
                )
                laundry_id = cursor.lastrowid
        connection.commit()
        return self._success({"id": laundry_id})

    def _perform_room_action(
        self, connection, user: dict, resource: str, body: dict
    ):
        action = re.sub(r"\s+", "", str(body.get("action") or ""))
        self._require_room_access(user, resource, action)
        if action in {"打印", "导出"}:
            return self._success({"handledBy": "browser"})
        if resource == "room-map":
            return self._perform_room_map_action(
                connection, user, body, action
            )
        if resource == "room-reservations":
            return self._perform_room_reservation_action(
                connection, user, body, action
            )
        if resource == "room-stays" and action in {"续住", "换房"}:
            return self._perform_room_map_action(
                connection, user, body, action
            )
        if resource == "stay-extensions":
            return self._perform_room_extension_action(
                connection, user, body, action
            )
        if resource == "room-change-applications":
            return self._perform_room_change_action(
                connection, user, body, action
            )
        if resource == "gift-distribution":
            return self._perform_room_gift_action(
                connection, user, body, action
            )
        if resource == "room-services":
            return self._perform_room_service_action(
                connection, user, body, action
            )
        if resource == "outing-applications":
            return self._perform_room_outing_action(
                connection, user, body, action
            )
        if resource in {"borrowed-items", "laundry"}:
            return self._perform_room_support_action(
                connection, user, resource, body, action
            )
        if action == "删除":
            return self._soft_delete_room_records(
                connection, user, resource, body
            )
        raise ApiError("当前客房页面不支持此操作", 403, 40300)

    def _perform_room_map_action(
        self, connection, user: dict, body: dict, action: str
    ):
        booking = None
        if action not in {"维修/脏房"}:
            booking = self._room_active_booking(
                connection, user, body, "room-map"
            )
        if action == "入住":
            if booking["status"] != "已订房":
                raise ApiError("只有已订房记录可以办理入住")
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE room_bookings
                    SET status='已入住',actual_check_in_at=NOW(),
                        version=version+1
                    WHERE booking_id=%s
                    """,
                    (booking["booking_id"],),
                )
                cursor.execute(
                    "UPDATE rooms SET status='入住',customer_id=%s "
                    "WHERE room_id=%s",
                    (booking["customer_id"], booking["room_id"]),
                )
                cursor.execute(
                    "UPDATE customers SET status='已入住',updated_at=NOW() "
                    "WHERE customer_id=%s",
                    (booking["customer_id"],),
                )
            after_status = "已入住"
        elif action == "续住":
            payload = {
                **body,
                "bookingId": booking["booking_id"],
                "id": None,
            }
            return self._save_room_extension(connection, user, payload)
        elif action in {"换房", "跨店换房"}:
            target_store_id = (
                self._room_store_id(connection, user, body, "targetStore")
                if action == "跨店换房"
                else booking["store_id"]
            )
            target = self._room_by_body(
                connection,
                user,
                body,
                target_store_id,
                key="targetRoom",
            )
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO room_change_applications(
                      tenant_id,store_id,booking_id,customer_id,
                      source_room_id,target_store_id,target_room_id,
                      changed_at,reason,audit_status,applicant_user_id
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'待审核',%s)
                    """,
                    (
                        user["tenant_id"],
                        booking["store_id"],
                        booking["booking_id"],
                        booking["customer_id"],
                        booking["room_id"],
                        target_store_id,
                        target["room_id"],
                        body.get("changedAt") or datetime.now(),
                        body.get("reason") or "客房换房申请",
                        user["user_id"],
                    ),
                )
                change_id = cursor.lastrowid
            connection.commit()
            return self._success({"id": change_id, "status": "待审核"})
        elif action == "退房":
            room_status = body.get("roomStatus") or "脏房"
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE room_bookings
                    SET status='已退房',actual_check_out_at=%s,
                        version=version+1
                    WHERE booking_id=%s
                    """,
                    (
                        body.get("checkOutAt") or datetime.now(),
                        booking["booking_id"],
                    ),
                )
                cursor.execute(
                    "UPDATE rooms SET status=%s,customer_id=NULL "
                    "WHERE room_id=%s",
                    (room_status, booking["room_id"]),
                )
                cursor.execute(
                    "UPDATE customers SET status='已退房',updated_at=NOW() "
                    "WHERE customer_id=%s",
                    (booking["customer_id"],),
                )
            after_status = "已退房"
        elif action == "维修/脏房":
            store_id = self._room_store_id(connection, user, body)
            room_body = dict(body)
            if body.get("id") and not body.get("roomId"):
                room_body["roomId"] = body["id"]
            room = self._room_by_body(connection, user, room_body, store_id)
            target_status = body.get("targetStatus") or "维修"
            if target_status not in {"维修", "脏房", "空闲"}:
                raise ApiError("房态只能设置为维修、脏房或空闲")
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE rooms SET status=%s WHERE room_id=%s",
                    (target_status, room["room_id"]),
                )
            booking = {
                "booking_id": 0,
                "store_id": room["store_id"],
                "room_id": room["room_id"],
                "customer_id": room.get("customer_id"),
            }
            after_status = target_status
        elif action in {"客房服务申请", "服务预约"}:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO room_service_requests(
                      tenant_id,store_id,booking_id,customer_id,room_id,
                      service_type,applied_at,scheduled_at,service_status,
                      remark,created_by_user_id
                    ) VALUES (%s,%s,%s,%s,%s,%s,NOW(),%s,%s,%s,%s)
                    """,
                    (
                        user["tenant_id"],
                        booking["store_id"],
                        booking["booking_id"],
                        booking["customer_id"],
                        booking["room_id"],
                        body.get("serviceType") or action,
                        body.get("serviceAt") or None,
                        "未完成服务"
                        if action == "客房服务申请"
                        else "待预约确认",
                        body.get("remark"),
                        user["user_id"],
                    ),
                )
                service_id = cursor.lastrowid
            connection.commit()
            return self._success({"id": service_id})
        elif action == "结账":
            contract = execute_one(
                connection,
                """
                SELECT amount,paid FROM contracts WHERE contract_id=%s
                """,
                (booking["contract_id"],),
            )
            if contract and Decimal(contract["amount"] or 0) > Decimal(
                contract["paid"] or 0
            ):
                raise ApiError("合同仍有余款，请先完成收款审核")
            after_status = "已结账"
        else:
            after_status = "已记录"
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO room_operation_records(
                  tenant_id,store_id,booking_id,customer_id,room_id,
                  operation_type,status,payload_json,created_by_user_id
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    user["tenant_id"],
                    booking["store_id"],
                    booking.get("booking_id") or None,
                    booking.get("customer_id"),
                    booking.get("room_id"),
                    action,
                    after_status,
                    json.dumps(body, ensure_ascii=False, default=json_default),
                    user["user_id"],
                ),
            )
            operation_id = cursor.lastrowid
        self._audit(
            connection,
            user,
            "ROOM_OPERATION",
            operation_id,
            action,
            booking["store_id"],
            None,
            after_status,
        )
        connection.commit()
        return self._success({"id": operation_id, "status": after_status})

    def _perform_room_reservation_action(
        self, connection, user: dict, body: dict, action: str
    ):
        booking = self._room_active_booking(
            connection, user, body, "room-reservations"
        )
        if action not in {"退订", "退订并结账"}:
            raise ApiError("当前订房记录不支持此操作")
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE room_bookings
                SET status=%s,deleted_at=NOW(),version=version+1
                WHERE booking_id=%s
                """,
                (
                    "已退订已结账" if action == "退订并结账" else "已退订",
                    booking["booking_id"],
                ),
            )
            cursor.execute(
                "UPDATE rooms SET status='空闲',customer_id=NULL "
                "WHERE room_id=%s",
                (booking["room_id"],),
            )
        connection.commit()
        return self._success(
            {
                "id": booking["booking_id"],
                "status": "已退订已结账"
                if action == "退订并结账"
                else "已退订",
            }
        )

    def _perform_room_extension_action(
        self, connection, user: dict, body: dict, action: str
    ):
        extension_id = int(body.get("id") or 0)
        row = execute_one(
            connection,
            """
            SELECT extension_id,store_id,booking_id,end_at,status,audit_status
            FROM room_stay_extensions
            WHERE extension_id=%s AND tenant_id=%s AND deleted_at IS NULL
            """,
            (extension_id, user["tenant_id"]),
        )
        if not row:
            raise ApiError("续住记录不存在")
        self._allowed_store(user, row["store_id"])
        with connection.cursor() as cursor:
            if action == "删除":
                cursor.execute(
                    "UPDATE room_stay_extensions SET deleted_at=NOW() "
                    "WHERE extension_id=%s",
                    (extension_id,),
                )
            elif action == "取消":
                cursor.execute(
                    """
                    UPDATE room_stay_extensions
                    SET status='已取消',cancelled_at=NOW(),version=version+1
                    WHERE extension_id=%s
                    """,
                    (extension_id,),
                )
            elif action == "审核":
                cursor.execute(
                    """
                    UPDATE room_stay_extensions
                    SET audit_status='已审核',status='已续住',
                        approved_by_user_id=%s,approved_at=NOW(),
                        version=version+1
                    WHERE extension_id=%s
                    """,
                    (user["user_id"], extension_id),
                )
                cursor.execute(
                    "UPDATE room_bookings SET check_out=%s,version=version+1 "
                    "WHERE booking_id=%s",
                    (row["end_at"], row["booking_id"]),
                )
            elif action == "反审核":
                cursor.execute(
                    """
                    UPDATE room_stay_extensions
                    SET audit_status='待审核',status='待续住',
                        approved_by_user_id=NULL,approved_at=NULL,
                        version=version+1
                    WHERE extension_id=%s
                    """,
                    (extension_id,),
                )
            else:
                raise ApiError("当前续住记录不支持此操作")
        connection.commit()
        return self._success({"id": extension_id, "action": action})

    def _perform_room_change_action(
        self, connection, user: dict, body: dict, action: str
    ):
        change_id = int(body.get("id") or 0)
        row = execute_one(
            connection,
            """
            SELECT change_id,store_id,booking_id,customer_id,source_room_id,
                   target_store_id,target_room_id,audit_status
            FROM room_change_applications
            WHERE change_id=%s AND tenant_id=%s AND deleted_at IS NULL
            """,
            (change_id, user["tenant_id"]),
        )
        if not row:
            raise ApiError("换房申请不存在")
        self._allowed_store(user, row["store_id"])
        with connection.cursor() as cursor:
            if action == "删除":
                cursor.execute(
                    "UPDATE room_change_applications SET deleted_at=NOW() "
                    "WHERE change_id=%s",
                    (change_id,),
                )
            elif action == "审核":
                target = execute_one(
                    connection,
                    "SELECT status FROM rooms WHERE room_id=%s FOR UPDATE",
                    (row["target_room_id"],),
                )
                if not target or target["status"] not in {"空闲", "脏房"}:
                    raise ApiError("目标房间当前不可换入")
                cursor.execute(
                    """
                    UPDATE room_change_applications
                    SET audit_status='审核通过',audit_opinion=%s,
                        approved_by_user_id=%s,approved_at=NOW(),
                        version=version+1
                    WHERE change_id=%s
                    """,
                    (
                        body.get("auditOpinion"),
                        user["user_id"],
                        change_id,
                    ),
                )
                cursor.execute(
                    "UPDATE rooms SET status='空闲',customer_id=NULL "
                    "WHERE room_id=%s",
                    (row["source_room_id"],),
                )
                cursor.execute(
                    "UPDATE rooms SET status='入住',customer_id=%s "
                    "WHERE room_id=%s",
                    (row["customer_id"], row["target_room_id"]),
                )
                cursor.execute(
                    """
                    UPDATE room_bookings
                    SET room_id=%s,store_id=%s,version=version+1
                    WHERE booking_id=%s
                    """,
                    (
                        row["target_room_id"],
                        row["target_store_id"],
                        row["booking_id"],
                    ),
                )
            elif action == "反审核":
                cursor.execute(
                    """
                    UPDATE room_change_applications
                    SET audit_status='待审核',audit_opinion=NULL,
                        approved_by_user_id=NULL,approved_at=NULL,
                        version=version+1
                    WHERE change_id=%s
                    """,
                    (change_id,),
                )
            else:
                raise ApiError("当前换房申请不支持此操作")
        connection.commit()
        return self._success({"id": change_id, "action": action})

    def _perform_room_gift_action(
        self, connection, user: dict, body: dict, action: str
    ):
        distribution_id = int(body.get("id") or 0)
        if distribution_id:
            row = execute_one(
                connection,
                """
                SELECT distribution_id,store_id FROM room_gift_distributions
                WHERE distribution_id=%s AND tenant_id=%s
                  AND deleted_at IS NULL
                """,
                (distribution_id, user["tenant_id"]),
            )
            if not row:
                raise ApiError("赠送记录不存在")
            self._allowed_store(user, row["store_id"])
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE room_gift_distributions
                    SET gift_items=%s,gift_status='已赠送',issued_at=%s,
                        issued_by_user_id=%s,remark=%s
                    WHERE distribution_id=%s
                    """,
                    (
                        body.get("giftItems") or "合同入住赠品",
                        body.get("issuedAt") or datetime.now(),
                        user["user_id"],
                        body.get("remark"),
                        distribution_id,
                    ),
                )
        else:
            booking = self._room_active_booking(
                connection, user, body, "room-map"
            )
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO room_gift_distributions(
                      tenant_id,store_id,booking_id,customer_id,contract_id,
                      room_id,gift_items,gift_status,issued_at,
                      issued_by_user_id,remark,created_by_user_id
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,'已赠送',%s,%s,%s,%s)
                    """,
                    (
                        user["tenant_id"],
                        booking["store_id"],
                        booking["booking_id"],
                        booking["customer_id"],
                        booking["contract_id"],
                        booking["room_id"],
                        body.get("giftItems") or "合同入住赠品",
                        body.get("issuedAt") or datetime.now(),
                        user["user_id"],
                        body.get("remark"),
                        user["user_id"],
                    ),
                )
                distribution_id = cursor.lastrowid
        connection.commit()
        return self._success({"id": distribution_id, "status": "已赠送"})

    def _perform_room_service_action(
        self, connection, user: dict, body: dict, action: str
    ):
        service_id = int(body.get("id") or 0)
        row = execute_one(
            connection,
            """
            SELECT service_id,store_id FROM room_service_requests
            WHERE service_id=%s AND tenant_id=%s AND deleted_at IS NULL
            """,
            (service_id, user["tenant_id"]),
        )
        if not row:
            raise ApiError("客房服务记录不存在")
        self._allowed_store(user, row["store_id"])
        status_map = {
            "确认完成": "已完成服务",
            "取消": "已取消",
            "预约确认": "已确认预约",
        }
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE room_service_requests
                SET service_status=%s,
                    confirmed_by_user_id=CASE WHEN %s='预约确认'
                      THEN %s ELSE confirmed_by_user_id END,
                    completed_by_user_id=CASE WHEN %s='确认完成'
                      THEN %s ELSE completed_by_user_id END,
                    completed_at=CASE WHEN %s='确认完成'
                      THEN NOW() ELSE completed_at END,
                    cancelled_at=CASE WHEN %s='取消'
                      THEN NOW() ELSE cancelled_at END
                WHERE service_id=%s
                """,
                (
                    status_map[action],
                    action,
                    user["user_id"],
                    action,
                    user["user_id"],
                    action,
                    action,
                    service_id,
                ),
            )
        connection.commit()
        return self._success({"id": service_id, "status": status_map[action]})

    def _perform_room_outing_action(
        self, connection, user: dict, body: dict, action: str
    ):
        if action == "删除":
            return self._soft_delete_room_records(
                connection, user, "outing-applications", body
            )
        outing_id = int(body.get("id") or 0)
        row = execute_one(
            connection,
            """
            SELECT outing_id,store_id FROM room_outing_applications
            WHERE outing_id=%s AND tenant_id=%s AND deleted_at IS NULL
            """,
            (outing_id, user["tenant_id"]),
        )
        if not row:
            raise ApiError("外出申请不存在")
        self._allowed_store(user, row["store_id"])
        with connection.cursor() as cursor:
            if action == "审核":
                status = (
                    "审核不通过"
                    if body.get("auditResult") == "审核不通过"
                    else "审核已通过"
                )
                cursor.execute(
                    """
                    UPDATE room_outing_applications
                    SET outing_status=%s,approved_by_user_id=%s,
                        approved_at=NOW(),version=version+1
                    WHERE outing_id=%s
                    """,
                    (status, user["user_id"], outing_id),
                )
            elif action == "确定已返回":
                status = "已返回"
                cursor.execute(
                    """
                    UPDATE room_outing_applications
                    SET outing_status='已返回',returned_at=%s,
                        version=version+1
                    WHERE outing_id=%s
                    """,
                    (body.get("returnedAt") or datetime.now(), outing_id),
                )
            else:
                raise ApiError("当前外出申请不支持此操作")
        connection.commit()
        return self._success({"id": outing_id, "status": status})

    def _perform_room_support_action(
        self,
        connection,
        user: dict,
        resource: str,
        body: dict,
        action: str,
    ):
        if action == "删除":
            return self._soft_delete_room_records(
                connection, user, resource, body
            )
        if action != "确认签收":
            raise ApiError("当前记录不支持此操作")
        record_id = int(body.get("id") or 0)
        if resource == "borrowed-items":
            table, id_column = "room_borrowed_items", "borrow_id"
            status_sql = "return_status='已还'"
        else:
            table, id_column = "room_laundry_records", "laundry_id"
            status_sql = "sign_status='已签收'"
        row = execute_one(
            connection,
            f"""
            SELECT {id_column} AS id,store_id FROM {table}
            WHERE {id_column}=%s AND tenant_id=%s AND deleted_at IS NULL
            """,
            (record_id, user["tenant_id"]),
        )
        if not row:
            raise ApiError("记录不存在")
        self._allowed_store(user, row["store_id"])
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                UPDATE {table}
                SET {status_sql},signed_at=%s,signer=%s
                WHERE {id_column}=%s
                """,
                (
                    body.get("signedAt") or datetime.now(),
                    body.get("signer") or user["username"],
                    record_id,
                ),
            )
        connection.commit()
        return self._success({"id": record_id, "status": "已签收"})

    def _soft_delete_room_records(
        self, connection, user: dict, resource: str, body: dict
    ):
        mapping = {
            "room-type-bookings": ("room_bookings", "booking_id"),
            "stay-extensions": ("room_stay_extensions", "extension_id"),
            "room-change-applications": (
                "room_change_applications",
                "change_id",
            ),
            "outing-applications": (
                "room_outing_applications",
                "outing_id",
            ),
            "borrowed-items": ("room_borrowed_items", "borrow_id"),
            "laundry": ("room_laundry_records", "laundry_id"),
        }
        if resource not in mapping:
            raise ApiError("当前页面不支持删除")
        table, id_column = mapping[resource]
        ids = body.get("ids") or [body.get("id")]
        ids = [int(item) for item in ids if item]
        if not ids:
            raise ApiError("请选择要删除的记录")
        placeholders = ",".join(["%s"] * len(ids))
        clause, params = self._store_clause(user)
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                UPDATE {table}
                SET deleted_at=NOW()
                WHERE tenant_id=%s AND {id_column} IN ({placeholders})
                  AND {clause}
                """,
                [user["tenant_id"], *ids, *params],
            )
            affected = cursor.rowcount
        connection.commit()
        if affected != len(ids):
            raise ApiError("部分记录不存在或不在当前门店权限范围", 403, 40300)
        return self._success({"deleted": affected})

    def _get_mall_module_data(
        self, connection, user: dict, resource: str, query: dict
    ):
        self._require_any_permission(
            user,
            ("LEGACY.WEB.N470.B18",),
        )
        supported = {
            "products",
            "orders",
            "projects",
            "matrons",
            "categories",
            "parenting",
            "questions",
            "reviews",
            "community",
            "content",
            "comments",
            "classes",
            "class-schedule",
        }
        if resource not in supported:
            raise ApiError("商城资源不存在", 404, 40400)
        scoped_user = self._user_for_selected_store(user, query)
        overview = mama_box_overview(connection, scoped_user)
        overview_key = "schedule" if resource == "class-schedule" else resource
        overview_value = overview.get(overview_key)
        rows = (
            overview_value.get("rows", [])
            if isinstance(overview_value, dict)
            else overview_value
        )
        rows = rows if isinstance(rows, list) else []
        if rows or resource != "products":
            return self._success({"list": rows, "total": len(rows), "source": "mysql"})
        rows = execute_all(
            connection,
            """
            SELECT p.product_id AS id,
                   CONCAT('SP-', LPAD(p.product_id, 6, '0')) AS code,
                   p.name, p.cat AS category,
                   p.price AS originalPrice, p.price AS salePrice,
                   p.points_price AS pointPrice,
                   p.stock AS stockQuantity, p.status,
                   CASE WHEN COALESCE(p.points_price,0)>0
                     THEN '是' ELSE '否' END AS integral,
                   '' AS store, '' AS spec, '' AS unit,
                   '' AS recommended
            FROM products p
            WHERE p.tenant_id=%s AND p.deleted_at IS NULL
            ORDER BY p.product_id DESC
            LIMIT 500
            """,
            (user["tenant_id"],),
        )
        for row in rows:
            if row.get("status") == "在售":
                row["status"] = "已上架"
            elif row.get("status") in {"停售", "停用"}:
                row["status"] = "已下架"
        return self._success({"list": rows, "total": len(rows)})

    def _get_inventory_module_data(
        self, connection, user: dict, resource: str, query: dict
    ):
        self._require_any_permission(
            user,
            ("INVENTORY.VIEW", "LEGACY.WEB.N358.B18"),
        )
        supported = {
            "purchase-plans",
            "purchase-orders",
            "purchase-order-audits",
            "other-inbounds",
            "purchase-inbounds",
            "material-requisitions",
            "sales-outbounds",
            "material-requisitions-no-amount",
            "stock-transfers",
            "purchase-returns",
            "stocktakes",
            "stock-damages",
            "opening-stock-import",
            "stock-warnings",
            "opening-stock-query",
            "gift-list-plans",
            "stock-summary-report",
            "stock-ledger-report",
            "department-requisition-report",
            "warehouse-stock-query",
            "purchase-detail-report",
            "supplier-prepayments",
            "supplier-payments",
            "accounts-payable-detail",
            "batch-expiry",
            "supplier-records",
        }
        if resource not in supported:
            raise ApiError("仓存资源不存在", 404, 40400)
        rows = []
        inventory_clause, inventory_params = self._scoped_store_clause(
            user, query, "inv"
        )
        if resource in {
            "warehouse-stock-query",
            "stock-summary-report",
            "opening-stock-query",
        }:
            rows = execute_all(
                connection,
                f"""
                SELECT inv.item_id AS id, store.name AS store,
                       store.name AS warehouse,
                       item.item_id AS materialCode,
                       item.name AS materialName, item.cat AS specification,
                       item.unit, inv.qty AS currentQuantity,
                       0 AS lockedQuantity, inv.qty AS availableQuantity,
                       inv.avg_cost AS unitPrice,
                       inv.qty*inv.avg_cost AS stockAmount,
                       inv.qty AS closingQuantity,
                       inv.qty*inv.avg_cost AS closingAmount,
                       0 AS openingQuantity, 0 AS openingAmount,
                       0 AS inQuantity, 0 AS inAmount,
                       0 AS outQuantity, 0 AS outAmount,
                       MIN(batch.expiry_date) AS expiryDate,
                       CASE
                         WHEN inv.qty<0 THEN '负库存'
                         WHEN inv.qty=0 THEN '零库存'
                         ELSE '有库存'
                       END AS stockCondition
                FROM inventory inv
                JOIN items item
                  ON item.item_id=inv.item_id
                 AND item.tenant_id=inv.tenant_id
                JOIN stores store ON store.store_id=inv.store_id
                LEFT JOIN inventory_batches batch
                  ON batch.tenant_id=inv.tenant_id
                 AND batch.store_id=inv.store_id
                 AND batch.item_id=inv.item_id
                 AND batch.deleted_at IS NULL
                 AND batch.qty>0
                WHERE inv.tenant_id=%s AND {inventory_clause}
                GROUP BY inv.store_id,inv.item_id
                ORDER BY store.sort_weight DESC,store.store_id,item.name
                LIMIT 1000
                """,
                [user["tenant_id"], *inventory_params],
            )
        elif resource == "stock-warnings":
            rows = execute_all(
                connection,
                f"""
                SELECT inv.item_id AS id,
                       item.item_id AS materialCode,
                       item.name AS materialName,
                       item.cat AS specification,item.unit,
                       store.name AS store,store.name AS warehouse,
                       inv.qty AS currentQuantity,
                       inv.warn_qty AS safetyQuantity,
                       NULL AS maxQuantity,
                       MIN(batch.expiry_date) AS expiryDate,
                       CASE
                         WHEN MIN(batch.expiry_date)<CURDATE()
                           THEN '已过期'
                         WHEN MIN(batch.expiry_date)
                              <=DATE_ADD(CURDATE(),INTERVAL 30 DAY)
                           THEN '临期'
                         WHEN inv.qty=0 THEN '库存为零'
                         WHEN inv.qty<=inv.warn_qty THEN '低于安全库存'
                         ELSE '正常'
                       END AS warningType,
                       CASE
                         WHEN inv.qty<=inv.warn_qty
                           OR MIN(batch.expiry_date)
                              <=DATE_ADD(CURDATE(),INTERVAL 30 DAY)
                         THEN '未处理'
                         ELSE '正常'
                       END AS warningStatus,
                       NULL AS lastHandledAt
                FROM inventory inv
                JOIN items item
                  ON item.item_id=inv.item_id
                 AND item.tenant_id=inv.tenant_id
                JOIN stores store ON store.store_id=inv.store_id
                LEFT JOIN inventory_batches batch
                  ON batch.tenant_id=inv.tenant_id
                 AND batch.store_id=inv.store_id
                 AND batch.item_id=inv.item_id
                 AND batch.deleted_at IS NULL
                 AND batch.qty>0
                WHERE inv.tenant_id=%s AND {inventory_clause}
                GROUP BY inv.store_id,inv.item_id
                HAVING warningType<>'正常'
                ORDER BY expiryDate, currentQuantity
                LIMIT 1000
                """,
                [user["tenant_id"], *inventory_params],
            )
        elif resource == "batch-expiry":
            batch_clause, batch_params = self._scoped_store_clause(
                user, query, "batch"
            )
            rows = execute_all(
                connection,
                f"""
                SELECT batch.batch_id AS id,
                       batch.batch_no AS batchNo,
                       item.item_id AS materialCode,
                       item.name AS materialName,item.unit,
                       store.name AS store,store.name AS warehouse,
                       batch.qty AS currentQuantity,
                       batch.production_date AS productionDate,
                       batch.expiry_date AS expiryDate,
                       batch.ref AS sourceDocument,
                       CASE
                         WHEN batch.expiry_date<CURDATE() THEN '已过期'
                         WHEN batch.expiry_date
                              <=DATE_ADD(CURDATE(),INTERVAL 30 DAY)
                           THEN '临期'
                         ELSE '有效'
                       END AS expiryStatus
                FROM inventory_batches batch
                JOIN items item
                  ON item.item_id=batch.item_id
                 AND item.tenant_id=batch.tenant_id
                JOIN stores store ON store.store_id=batch.store_id
                WHERE batch.tenant_id=%s
                  AND batch.deleted_at IS NULL
                  AND {batch_clause}
                ORDER BY batch.expiry_date,batch.batch_id
                LIMIT 1000
                """,
                [user["tenant_id"], *batch_params],
            )
        elif resource in {
            "purchase-orders",
            "purchase-order-audits",
            "purchase-detail-report",
        }:
            purchase_clause, purchase_params = self._scoped_store_clause(
                user, query, "purchase"
            )
            rows = execute_all(
                connection,
                f"""
                SELECT purchase.po_id AS id,
                       purchase.po_no AS purchaseNo,
                       LEFT(purchase.created_at,10) AS purchaseDate,
                       purchase.supplier,store.name AS store,
                       store.name AS warehouse,
                       item.item_id AS materialCode,
                       item.name AS materialName,item.cat AS specification,
                       item.unit,line.qty AS quantity,
                       line.qty AS purchaseQuantity,
                       line.unit_cost AS unitPrice,
                       line.qty*line.unit_cost AS amount,
                       line.qty AS receivedQuantity,
                       CASE WHEN purchase.status IN ('已入库','已完成')
                         THEN line.qty ELSE 0 END AS inboundQuantity,
                       purchase.total_cost AS totalAmount,
                       purchase.created_by AS buyer,
                       purchase.status AS auditStatus,
                       purchase.status AS arrivalStatus,
                       purchase.note AS remark
                FROM purchase_orders purchase
                LEFT JOIN purchase_lines line
                  ON line.po_id=purchase.po_id
                 AND line.tenant_id=purchase.tenant_id
                LEFT JOIN items item ON item.item_id=line.item_id
                JOIN stores store ON store.store_id=purchase.store_id
                WHERE purchase.tenant_id=%s
                  AND purchase.deleted_at IS NULL
                  AND {purchase_clause}
                ORDER BY purchase.po_id DESC,line.line_id
                LIMIT 1000
                """,
                [user["tenant_id"], *purchase_params],
            )
        elif resource == "stock-transfers":
            allowed = [
                int(value)
                for value in user.get("store_ids") or []
                if str(value).isdigit()
            ]
            if allowed:
                placeholders = ",".join(["%s"] * len(allowed))
                params = [
                    user["tenant_id"],
                    *allowed,
                    *allowed,
                ]
                requested = self._requested_store_id(user, query)
                requested_sql = ""
                if requested is not None:
                    requested_sql = (
                        " AND (transfer.from_store=%s"
                        " OR transfer.to_store=%s)"
                    )
                    params.extend([requested, requested])
                rows = execute_all(
                    connection,
                    f"""
                    SELECT transfer.transfer_id AS id,
                           transfer.transfer_no AS transferNo,
                           LEFT(transfer.created_at,10) AS transferDate,
                           source.name AS sourceWarehouse,
                           target.name AS targetWarehouse,
                           item.item_id AS materialCode,
                           item.name AS materialName,
                           item.cat AS specification,item.unit,
                           transfer.qty AS quantity,
                           transfer.status AS transferStatus,
                           transfer.status AS auditStatus,
                           transfer.created_by AS operator,
                           transfer.note AS remark
                    FROM stock_transfers transfer
                    JOIN stores source
                      ON source.store_id=transfer.from_store
                    JOIN stores target
                      ON target.store_id=transfer.to_store
                    JOIN items item ON item.item_id=transfer.item_id
                    WHERE transfer.tenant_id=%s
                      AND transfer.deleted_at IS NULL
                      AND transfer.from_store IN ({placeholders})
                      AND transfer.to_store IN ({placeholders})
                      {requested_sql}
                    ORDER BY transfer.transfer_id DESC
                    LIMIT 1000
                    """,
                    params,
                )
        elif resource == "stocktakes":
            stocktake_clause, stocktake_params = (
                self._scoped_store_clause(user, query, "stocktake")
            )
            rows = execute_all(
                connection,
                f"""
                SELECT stocktake.stocktake_id AS id,
                       stocktake.stocktake_no AS stocktakeNo,
                       LEFT(stocktake.created_at,10) AS stocktakeDate,
                       store.name AS store,store.name AS warehouse,
                       item.item_id AS materialCode,
                       item.name AS materialName,item.unit,
                       line.book_qty AS bookQuantity,
                       line.counted_qty AS actualQuantity,
                       line.variance AS differenceQuantity,
                       line.variance*inventory.avg_cost AS differenceAmount,
                       stocktake.status AS stocktakeStatus,
                       stocktake.created_by AS stocktaker,
                       stocktake.status AS auditStatus,
                       stocktake.note AS remark
                FROM stocktakes stocktake
                JOIN stores store ON store.store_id=stocktake.store_id
                LEFT JOIN stocktake_lines line
                  ON line.stocktake_id=stocktake.stocktake_id
                 AND line.tenant_id=stocktake.tenant_id
                LEFT JOIN items item ON item.item_id=line.item_id
                LEFT JOIN inventory
                  ON inventory.tenant_id=stocktake.tenant_id
                 AND inventory.store_id=stocktake.store_id
                 AND inventory.item_id=line.item_id
                WHERE stocktake.tenant_id=%s
                  AND stocktake.deleted_at IS NULL
                  AND {stocktake_clause}
                ORDER BY stocktake.stocktake_id DESC,line.line_id
                LIMIT 1000
                """,
                [user["tenant_id"], *stocktake_params],
            )
        elif resource in {"stock-ledger-report", "other-inbounds"}:
            movement_clause, movement_params = (
                self._scoped_store_clause(user, query, "movement")
            )
            inbound_filter = (
                "AND movement.type IN "
                "('盘盈入库','调拨入库','退料入库','其他入库')"
                if resource == "other-inbounds"
                else ""
            )
            rows = execute_all(
                connection,
                f"""
                SELECT movement.id,
                       COALESCE(NULLIF(movement.ref,''),
                         CONCAT('MOVE-',movement.id)) AS documentNo,
                       COALESCE(NULLIF(movement.ref,''),
                         CONCAT('IN-',movement.id)) AS inboundNo,
                       LEFT(movement.created_at,10) AS businessDate,
                       LEFT(movement.created_at,10) AS inboundDate,
                       movement.type AS businessType,
                       movement.type AS inboundType,
                       store.name AS store,store.name AS warehouse,
                       item.item_id AS materialCode,
                       item.name AS materialName,item.unit,
                       CASE WHEN movement.qty>0
                         THEN movement.qty ELSE 0 END AS inQuantity,
                       CASE WHEN movement.qty<0
                         THEN -movement.qty ELSE 0 END AS outQuantity,
                       movement.qty AS quantity,
                       inventory.qty AS balanceQuantity,
                       inventory.avg_cost AS unitPrice,
                       inventory.qty*inventory.avg_cost AS balanceAmount,
                       movement.created_by AS operator,
                       movement.created_by AS creator
                FROM stock_movements movement
                LEFT JOIN items item ON item.item_id=movement.item_id
                LEFT JOIN stores store ON store.store_id=movement.store_id
                LEFT JOIN inventory
                  ON inventory.tenant_id=movement.tenant_id
                 AND inventory.store_id=movement.store_id
                 AND inventory.item_id=movement.item_id
                WHERE movement.tenant_id=%s
                  AND {movement_clause}
                  {inbound_filter}
                ORDER BY movement.id DESC
                LIMIT 1000
                """,
                [user["tenant_id"], *movement_params],
            )
        data = self._merge_operational_module_rows(
            connection,
            user,
            "INVENTORY",
            resource,
            query,
            {"list": rows, "total": len(rows), "source": "mysql"},
        )
        return self._success(data)

    def _audit(
        self,
        connection,
        user: dict,
        aggregate_type: str,
        aggregate_id: int,
        action: str,
        store_id: int | None,
        before_status: str | None,
        after_status: str | None,
        detail: dict | None = None,
    ):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO mvp_audit_events(
                  tenant_id, store_id, actor_user_id, aggregate_type,
                  aggregate_id, action_code, before_status, after_status,
                  detail_json
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    user["tenant_id"],
                    store_id,
                    user["user_id"],
                    aggregate_type,
                    aggregate_id,
                    action,
                    before_status,
                    after_status,
                    compact_json(detail or {}),
                ),
            )

    def _require_foundation_write(self, user: dict):
        self._require_any_permission(user, ("SYSTEM.EDIT", "BASIC.EDIT"))

    def _foundation_store_id(self, connection, user: dict, payload: dict) -> int:
        requested_id = payload.get("storeId") or payload.get("store_id")
        if requested_id:
            return self._allowed_store(user, requested_id)
        requested_name = str(payload.get("store") or "").strip()
        if not requested_name:
            raise ApiError("请选择所属门店")
        clause, params = self._store_clause(user, "s")
        row = execute_one(
            connection,
            f"""
            SELECT s.store_id AS id FROM stores s
            WHERE s.tenant_id=%s AND s.name=%s AND {clause}
            LIMIT 1
            """,
            [user["tenant_id"], requested_name, *params],
        )
        if not row:
            raise ApiError("当前账号无权访问所选门店", 403, 40300)
        return int(row["id"])

    def _foundation_manager_id(
        self, connection, user: dict, store_id: int, manager: object
    ) -> int | None:
        name = str(manager or "").strip()
        if not name:
            return None
        row = execute_one(
            connection,
            """
            SELECT staff_id AS id FROM staff
            WHERE tenant_id=%s AND store_id=%s AND name=%s
              AND employment_status='ACTIVE'
            LIMIT 1
            """,
            (user["tenant_id"], store_id, name),
        )
        if not row:
            raise ApiError("负责人须为所选门店的在职职员")
        return int(row["id"])

    def _foundation_status(self, value: object) -> str:
        if str(value or "启用") in {"启用", "ACTIVE", "正常"}:
            return "ACTIVE"
        return "ACTIVE" if str(value or "启用") in {"启用", "ACTIVE", "正常"} else "INACTIVE"

    def _foundation_code(self, value: object, label: str) -> str:
        code = str(value or "").strip().upper()
        if not re.fullmatch(r"[A-Z0-9_]{2,64}", code):
            raise ApiError(f"{label}仅可使用 2-64 位大写字母、数字或下划线")
        return code

    def _post_foundation_resource(
        self, connection, user: dict, resource: str, body: dict
    ):
        if resource == "/roles/save":
            return self._save_foundation_role(connection, user, body)
        if resource == "/departments/save":
            return self._save_foundation_department(connection, user, body)
        if resource == "/stores/save":
            return self._save_foundation_store(connection, user, body)
        if resource == "/users/save":
            return self._save_foundation_user(connection, user, body)
        match = re.fullmatch(r"/roles/(\d+)/permissions", resource)
        if match:
            return self._save_foundation_role_permissions(
                connection, user, int(match.group(1)), body
            )
        raise ApiError("基础平台写入资源不存在", 404, 40400)

    def _save_foundation_user(self, connection, user: dict, body: dict):
        """Create or edit a login account linked to an existing employee."""
        self._require_foundation_write(user)
        account_id = int(body.get("id") or 0)
        username = str(body.get("username") or "").strip()
        staff_name = str(body.get("name") or "").strip()
        initial_password = str(body.get("initialPassword") or "")
        role_id = int(body.get("roleId") or 0)
        store_id = self._foundation_store_id(connection, user, body)
        self._require_selected_write_store(user, body, store_id)

        if not re.fullmatch(r"[A-Za-z0-9_.@\-\u4e00-\u9fff]{2,64}", username):
            raise ApiError("登录账号须为2-64位中文、字母、数字或 _ . @ -")
        if not staff_name or len(staff_name) > 64:
            raise ApiError("员工姓名不能为空且不超过64字符")
        if not account_id and not (6 <= len(initial_password) <= 64):
            raise ApiError("新建账号的初始密码须为6-64位")
        if account_id and initial_password:
            raise ApiError("编辑账号时不能修改初始密码，请使用独立的密码重置流程")

        role = execute_one(
            connection,
            """SELECT role_id, name FROM roles
               WHERE tenant_id=%s AND role_id=%s AND status='ACTIVE'""",
            (user["tenant_id"], role_id),
        )
        if not role:
            raise ApiError("请选择当前租户内启用的角色")

        staff_rows = execute_all(
            connection,
            """SELECT staff_id, name FROM staff
               WHERE tenant_id=%s AND store_id=%s AND name=%s
                 AND employment_status='ACTIVE'
               ORDER BY staff_id LIMIT 2""",
            (user["tenant_id"], store_id, staff_name),
        )
        if not staff_rows:
            raise ApiError("未找到该门店的在职员工，请先在员工档案中建立员工")
        if len(staff_rows) > 1:
            raise ApiError("该门店存在同名员工，请先在员工档案中补充唯一员工编号")
        staff_id = int(staff_rows[0]["staff_id"])

        previous = None
        if account_id:
            previous = execute_one(
                connection,
                """SELECT user_id, staff_id, username, default_store_id, status
                   FROM user_accounts
                   WHERE tenant_id=%s AND user_id=%s""",
                (user["tenant_id"], account_id),
            )
            if not previous:
                raise ApiError("员工账号不存在", 404, 40400)
            self._allowed_store(user, previous.get("default_store_id"))

        duplicate_username = execute_one(
            connection,
            """SELECT user_id FROM user_accounts
               WHERE tenant_id=%s AND username=%s AND user_id<>%s LIMIT 1""",
            (user["tenant_id"], username, account_id),
        )
        if duplicate_username:
            raise ApiError("登录账号已存在")
        duplicate_staff = execute_one(
            connection,
            """SELECT user_id FROM user_accounts
               WHERE tenant_id=%s AND staff_id=%s AND user_id<>%s LIMIT 1""",
            (user["tenant_id"], staff_id, account_id),
        )
        if duplicate_staff:
            raise ApiError("该员工已经绑定登录账号")

        current_role = execute_one(
            connection,
            """SELECT role_id FROM user_roles
               WHERE user_id=%s AND effective_from<=NOW()
                 AND (effective_to IS NULL OR effective_to>NOW())
               ORDER BY effective_from DESC LIMIT 1""",
            (account_id,),
        ) if account_id else None

        status = self._foundation_status(body.get("status"))
        with connection.cursor() as cursor:
            if account_id:
                cursor.execute(
                    """UPDATE user_accounts
                       SET staff_id=%s, username=%s, default_store_id=%s,
                           status=%s
                       WHERE tenant_id=%s AND user_id=%s""",
                    (staff_id, username, store_id, status, user["tenant_id"], account_id),
                )
            else:
                cursor.execute(
                    """INSERT INTO user_accounts
                       (tenant_id, staff_id, username, password_hash,
                        default_store_id, status, password_changed_at)
                       VALUES(%s,%s,%s,%s,%s,%s,NOW())""",
                    (
                        user["tenant_id"], staff_id, username,
                        hash_password(initial_password), store_id, status,
                    ),
                )
                account_id = int(cursor.lastrowid)

            if not current_role or int(current_role["role_id"]) != role_id:
                # Expire rather than delete assignments so history remains auditable.
                cursor.execute(
                    """UPDATE user_roles SET effective_to=NOW()
                       WHERE user_id=%s AND effective_from<=NOW()
                         AND (effective_to IS NULL OR effective_to>NOW())""",
                    (account_id,),
                )
                cursor.execute(
                    """INSERT INTO user_roles
                       (user_id, role_id, effective_from, assigned_by)
                       VALUES(%s,%s,NOW(),%s)""",
                    (account_id, role_id, user["user_id"]),
                )
            # Preserve existing cross-store grants and ensure the new default store.
            cursor.execute(
                """INSERT INTO user_stores(user_id, store_id, access_level)
                   VALUES(%s,%s,'MANAGE')
                   ON DUPLICATE KEY UPDATE access_level='MANAGE'""",
                (account_id, store_id),
            )

        self._audit(
            connection, user, "user_account", account_id,
            "EDIT" if previous else "CREATE", store_id,
            previous.get("status") if previous else None, status,
            {"username": username, "staffId": staff_id, "roleId": role_id},
        )
        connection.commit()
        return self._success({"id": account_id, "saved": True})

    def _save_foundation_store(self, connection, user: dict, body: dict):
        self._require_foundation_write(user)
        store_id = int(body.get("id") or 0)
        name = str(body.get("name") or "").strip()
        manager = str(body.get("manager") or "").strip()
        if not name or len(name) > 128 or len(manager) > 64:
            raise ApiError("门店名称不能为空且不超过128字符，负责人不超过64字符")
        if not store_id:
            # New locations are a headquarters-only operation.  They start
            # inactive so that a new master record cannot accidentally accept
            # customers before staff, rooms and package data are configured.
            if "SYS_ADMIN" not in user.get("roles", []):
                raise ApiError("仅系统管理员可新增门店", 403, 40300)
            selected = str(body.get("selectedStoreId") or "").strip().lower()
            if selected and selected != "all":
                raise ApiError("新增门店请在全部门店视图办理", 400, 40000)
            duplicate = execute_one(
                connection,
                "SELECT store_id FROM stores WHERE tenant_id=%s AND name=%s LIMIT 1",
                (user["tenant_id"], name),
            )
            if duplicate:
                raise ApiError("已存在同名门店，请直接编辑该门店档案")
            next_row = execute_one(
                connection,
                "SELECT COALESCE(MAX(store_id), 0) + 1 AS next_id FROM stores",
            )
            store_id = int(next_row["next_id"])
            with connection.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO stores
                       (store_id, tenant_id, name, manager, status, sort_weight)
                       VALUES (%s,%s,%s,%s,%s,%s)""",
                    (store_id, user["tenant_id"], name, manager or None, "INACTIVE", 0),
                )
            self._audit(
                connection, user, "store", store_id, "CREATE", store_id,
                None, "INACTIVE", {"name": name, "remark": body.get("remark") or ""},
            )
            connection.commit()
            return self._success({"id": store_id, "saved": True, "status": "INACTIVE"})
        self._allowed_store(user, store_id)
        self._require_selected_write_store(user, body, store_id)
        existing = execute_one(
            connection,
            "SELECT status FROM stores WHERE tenant_id=%s AND store_id=%s",
            (user["tenant_id"], store_id),
        )
        if not existing:
            raise ApiError("门店不存在或无权访问", 404, 40400)
        with connection.cursor() as cursor:
            cursor.execute(
                """UPDATE stores SET name=%s, manager=%s, status=%s
                   WHERE tenant_id=%s AND store_id=%s""",
                (name, manager or None, self._foundation_status(body.get("status")), user["tenant_id"], store_id),
            )
        self._audit(connection, user, "store", store_id, "EDIT", store_id, existing.get("status"), self._foundation_status(body.get("status")), {"name": name})
        connection.commit()
        return self._success({"id": store_id, "saved": True})

    def _save_foundation_department(self, connection, user: dict, body: dict):
        self._require_foundation_write(user)
        department_id = int(body.get("id") or 0)
        name = str(body.get("name") or "").strip()
        if not name or len(name) > 128:
            raise ApiError("部门名称不能为空且不超过128字符")
        code = self._foundation_code(body.get("code"), "部门编码")
        store_id = self._foundation_store_id(connection, user, body)
        self._require_selected_write_store(user, body, store_id)
        manager_id = self._foundation_manager_id(connection, user, store_id, body.get("manager"))
        status = self._foundation_status(body.get("status"))
        if department_id:
            clause, params = self._store_clause(user, "d")
            previous = execute_one(
                connection,
                f"SELECT status, store_id FROM departments d WHERE d.department_id=%s AND d.tenant_id=%s AND {clause}",
                [department_id, user["tenant_id"], *params],
            )
            if not previous:
                raise ApiError("部门不存在或无权访问", 404, 40400)
        else:
            previous = None
        duplicate = execute_one(
            connection,
            """SELECT department_id AS id FROM departments
               WHERE tenant_id=%s AND store_id=%s AND code=%s
                 AND department_id<>%s LIMIT 1""",
            (user["tenant_id"], store_id, code, department_id),
        )
        if duplicate:
            raise ApiError("该门店已存在相同部门编码")
        with connection.cursor() as cursor:
            if department_id:
                cursor.execute(
                    """UPDATE departments SET store_id=%s, code=%s, name=%s,
                           manager_staff_id=%s, status=%s
                       WHERE department_id=%s AND tenant_id=%s""",
                    (store_id, code, name, manager_id, status, department_id, user["tenant_id"]),
                )
            else:
                cursor.execute(
                    """INSERT INTO departments(tenant_id, store_id, code, name,
                           manager_staff_id, status)
                       VALUES(%s,%s,%s,%s,%s,%s)""",
                    (user["tenant_id"], store_id, code, name, manager_id, status),
                )
                department_id = cursor.lastrowid
        self._audit(connection, user, "department", department_id, "EDIT" if previous else "CREATE", store_id, previous.get("status") if previous else None, status, {"code": code, "name": name})
        connection.commit()
        return self._success({"id": department_id, "saved": True})

    def _save_foundation_role(self, connection, user: dict, body: dict):
        self._require_foundation_write(user)
        self._require_selected_write_store(user, body)
        role_id = int(body.get("id") or 0)
        name = str(body.get("name") or "").strip()
        if not name or len(name) > 128:
            raise ApiError("角色名称不能为空且不超过128字符")
        code = self._foundation_code(body.get("code"), "角色编码")
        scope_map = {"全部数据": 1, "本门店": 2, "本部门": 3, "本人数据": 4}
        data_scope = scope_map.get(body.get("dataScope"))
        if not data_scope:
            raise ApiError("请选择有效的数据范围")
        status = self._foundation_status(body.get("status"))
        previous = execute_one(
            connection,
            "SELECT status FROM roles WHERE role_id=%s AND tenant_id=%s",
            (role_id, user["tenant_id"]),
        ) if role_id else None
        if role_id and not previous:
            raise ApiError("角色不存在", 404, 40400)
        duplicate = execute_one(
            connection,
            "SELECT role_id AS id FROM roles WHERE tenant_id=%s AND code=%s AND role_id<>%s LIMIT 1",
            (user["tenant_id"], code, role_id),
        )
        if duplicate:
            raise ApiError("角色编码已存在")
        with connection.cursor() as cursor:
            if role_id:
                cursor.execute(
                    """UPDATE roles SET name=%s, code=%s, data_scope=%s,
                           description=%s, status=%s
                       WHERE role_id=%s AND tenant_id=%s""",
                    (name, code, data_scope, body.get("remark") or None, status, role_id, user["tenant_id"]),
                )
            else:
                cursor.execute(
                    """INSERT INTO roles(tenant_id, code, name, role_type,
                           data_scope, description, status, created_at)
                       VALUES(%s,%s,%s,'JOB',%s,%s,%s,NOW())""",
                    (user["tenant_id"], code, name, data_scope, body.get("remark") or None, status),
                )
                role_id = cursor.lastrowid
        self._audit(connection, user, "role", role_id, "EDIT" if previous else "CREATE", None, previous.get("status") if previous else None, status, {"code": code, "name": name})
        connection.commit()
        return self._success({"id": role_id, "saved": True})

    def _save_foundation_role_permissions(
        self, connection, user: dict, role_id: int, body: dict
    ):
        self._require_foundation_write(user)
        self._require_selected_write_store(user, body)
        role = execute_one(
            connection,
            "SELECT role_id, status FROM roles WHERE role_id=%s AND tenant_id=%s",
            (role_id, user["tenant_id"]),
        )
        if not role:
            raise ApiError("角色不存在", 404, 40400)
        scope_map = {"全部数据": 1, "本门店": 2, "本部门": 3, "本人数据": 4}
        data_scope = scope_map.get(body.get("dataScope"))
        if not data_scope:
            raise ApiError("请选择有效的数据范围")
        requested = {
            (str(item.get("module") or ""), str(item.get("action") or ""))
            for item in body.get("permissions", [])
            if isinstance(item, dict)
        }
        action_sql = """CASE
            WHEN action_code IN ('VIEW','QUERY') THEN 'view'
            WHEN action_code IN ('CREATE','ADD') THEN 'create'
            WHEN action_code IN ('EDIT','UPDATE') THEN 'edit'
            WHEN action_code IN ('APPROVE','AUDIT') THEN 'approve'
            WHEN action_code='EXPORT' THEN 'export' END"""
        rows = execute_all(
            connection,
            f"""SELECT permission_id, module_code AS module,
                       {action_sql} AS action
                FROM permissions WHERE status='ACTIVE'""",
        )
        permitted_ids = [row["permission_id"] for row in rows if (row["module"], row["action"]) in requested]
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM role_permissions WHERE role_id=%s AND effect='ALLOW'", (role_id,))
            for permission_id in permitted_ids:
                cursor.execute(
                    """INSERT INTO role_permissions(role_id, permission_id, effect)
                       VALUES(%s,%s,'ALLOW')
                       ON DUPLICATE KEY UPDATE effect='ALLOW'""",
                    (role_id, permission_id),
                )
            cursor.execute("UPDATE roles SET data_scope=%s WHERE role_id=%s", (data_scope, role_id))
        self._audit(connection, user, "role", role_id, "PERMISSION_EDIT", None, role.get("status"), role.get("status"), {"allowCount": len(permitted_ids), "dataScope": data_scope})
        connection.commit()
        return self._success({"id": role_id, "saved": True, "allowCount": len(permitted_ids)})

    def _get_resource(self, connection, user: dict, resource: str, query: dict):
        # An explicit store selection must be inside the signed-in account's
        # store scope.  Previously the generic MVP resources silently ignored
        # an unauthorized storeId and returned the account's normal rows,
        # which made the UI look as if the forbidden store had been selected.
        # Keep an omitted/all selector as the authorised aggregate scope, but
        # narrow every concrete selector before any resource query is built.
        selected_store = str((query or {}).get("storeId") or "").strip()
        if selected_store and selected_store.lower() != "all":
            user = self._user_for_selected_store(user, query)
        clause, values = self._store_clause(user)
        if resource == "/options":
            stores = execute_all(
                connection,
                f"""
                SELECT store_id AS id, name
                FROM stores WHERE tenant_id=%s AND {clause}
                ORDER BY sort_weight DESC, store_id
                """,
                [user["tenant_id"], *values],
            )
            staff = execute_all(
                connection,
                f"""
                SELECT staff_id AS id, name, department, position, store_id
                FROM staff
                WHERE tenant_id=%s AND employment_status='ACTIVE' AND {clause}
                ORDER BY store_id, department, name
                """,
                [user["tenant_id"], *values],
            )
            package_clause, package_values = self._store_clause(user, "pr")
            packages = execute_all(
                connection,
                f"""
                SELECT pp.package_id AS id,
                       pv.package_version_id AS packageVersionId,
                       pr.price_rule_id AS packagePriceRuleId,
                       pp.package_name AS packageName,
                       pr.stay_days AS days,
                       COALESCE(profile.original_amount, pr.reference_amount)
                         AS referencePrice,
                       COALESCE(profile.activity_amount, pr.reference_amount)
                         AS activityPrice,
                       COALESCE(profile.deal_amount, pr.reference_amount)
                         AS salePrice,
                       rt.room_type_id AS roomTypeId,
                       rt.name AS roomType,
                       pr.store_id AS storeId
                FROM package_products pp
                JOIN package_versions pv
                  ON pv.package_id=pp.package_id
                JOIN package_price_rules pr
                  ON pr.package_version_id=pv.package_version_id
                JOIN room_types rt ON rt.room_type_id=pr.room_type_id
                LEFT JOIN package_price_profiles profile
                  ON profile.price_rule_id=pr.price_rule_id
                WHERE pp.tenant_id=%s AND pp.deleted_at IS NULL
                  AND pp.status='ACTIVE' AND pv.version_status='ACTIVE'
                  AND pr.status='ACTIVE'
                  AND pv.effective_from<=CURDATE()
                  AND (pv.effective_to IS NULL OR pv.effective_to>=CURDATE())
                  AND pr.effective_from<=CURDATE()
                  AND (pr.effective_to IS NULL OR pr.effective_to>=CURDATE())
                  AND {package_clause}
                ORDER BY pr.store_id, pp.sort_order, rt.sort_order,
                         pr.stay_days, pp.package_id
                """,
                [user["tenant_id"], *package_values],
            )
            # A legacy import may contain duplicate price-rule rows for the
            # same package, room type and stay length.  The signing UI must
            # expose one unambiguous choice, while retaining the first active
            # rule for subsequent contract creation.
            unique_packages = {}
            for package in packages:
                package_key = (
                    package["storeId"], package["packageName"],
                    package["roomTypeId"], package["days"],
                    str(package["salePrice"]),
                )
                unique_packages.setdefault(package_key, package)
            packages = list(unique_packages.values())
            booking_contracts = []
            if self._has_permission(user, "ROOM.CREATE"):
                booking_contracts = execute_all(
                    connection,
                    f"""
                    SELECT ct.contract_id AS id, ct.contract_no,
                           ct.customer_id, c.name AS customer_name,
                           ct.store_id, ct.status, ct.amount, ct.paid,
                           ct.package_name,
                           ext.room_type AS room_type,
                           GREATEST(ct.amount-COALESCE(ct.paid,0),0)
                             AS outstanding_amount,
                           ct.expected_check_in, ct.expected_check_out
                    FROM contracts ct
                    JOIN customers c ON c.customer_id=ct.customer_id
                    LEFT JOIN sales_contract_extensions ext
                      ON ext.contract_id=ct.contract_id
                    WHERE ct.tenant_id=%s AND ct.deleted_at IS NULL
                      AND ct.status='已审核'
                      AND COALESCE(ct.paid,0)>0
                      AND {self._store_clause(user, 'ct')[0]}
                      AND NOT EXISTS (
                        SELECT 1 FROM room_bookings rb
                        WHERE rb.contract_id=ct.contract_id
                          AND rb.deleted_at IS NULL
                          AND rb.status IN ('已订房','已入住')
                      )
                    ORDER BY ct.contract_id DESC
                    LIMIT 200
                    """,
                    [
                        user["tenant_id"],
                        *self._store_clause(user, "ct")[1],
                    ],
                )
            return self._success(
                {
                    "stores": stores,
                    "staff": staff,
                    "contractTypes": CONTRACT_TYPES,
                    "receiptTypes": RECEIPT_TYPES,
                    "paymentMethods": PAYMENT_METHODS,
                    "packages": packages,
                    "permissions": user["permissions"],
                    "roles": user["roles"],
                    "bookingContracts": booking_contracts,
                }
            )
        if resource == "/overview":
            return self._overview(connection, user)
        if resource == "/customers":
            self._require_permission(user, "CUSTOMER.VIEW")
            rows = execute_all(
                connection,
                f"""
                SELECT c.customer_id AS id, c.customer_no, c.name, c.phone,
                       c.wechat, c.status, c.source, c.edc, c.store_id,
                       s.name AS store_name, st.name AS salesperson,
                       c.created_at
                FROM customers c
                LEFT JOIN stores s ON s.store_id=c.store_id
                LEFT JOIN staff st ON st.staff_id=c.sales_staff_id
                WHERE c.tenant_id=%s AND c.deleted_at IS NULL
                  AND {self._store_clause(user, 'c')[0]}
                ORDER BY c.customer_id DESC
                LIMIT 200
                """,
                [user["tenant_id"], *self._store_clause(user, "c")[1]],
            )
            for row in rows:
                row["phone"] = self._masked_phone(user, row["phone"])
            return self._success({"list": rows, "total": len(rows)})
        if resource == "/contracts":
            self._require_permission(user, "SALES.VIEW")
            rows = execute_all(
                connection,
                f"""
                SELECT ct.contract_id AS id, ct.contract_no, ct.contract_type,
                       ct.customer_id, c.name AS customer_name, ct.package_name,
                       ct.reference_amount, ct.amount, ct.discount_rate,
                       ct.paid, GREATEST(ct.amount-ct.paid,0) AS outstanding_amount,
                       COALESCE(SUM(CASE WHEN fr.status='待审核' THEN fr.amount ELSE 0 END),0)
                         AS unposted_amount,
                       ct.days, ct.expected_check_in, ct.expected_check_out,
                       ct.status, ct.sign_date, ct.store_id, s.name AS store_name
                FROM contracts ct
                JOIN customers c ON c.customer_id=ct.customer_id
                LEFT JOIN stores s ON s.store_id=ct.store_id
                LEFT JOIN finance_receipts fr ON fr.contract_id=ct.contract_id
                WHERE ct.tenant_id=%s AND ct.deleted_at IS NULL
                  AND {self._store_clause(user, 'ct')[0]}
                GROUP BY ct.contract_id
                ORDER BY ct.contract_id DESC
                LIMIT 200
                """,
                [user["tenant_id"], *self._store_clause(user, "ct")[1]],
            )
            return self._success({"list": rows, "total": len(rows)})
        if resource == "/receipts":
            self._require_permission(user, "FINANCE.VIEW")
            rows = execute_all(
                connection,
                f"""
                SELECT fr.receipt_id AS id, fr.receipt_no, fr.customer_id,
                       c.name AS customer_name, fr.contract_id, ct.contract_no,
                       fr.receipt_type, fr.amount, fr.payment_method,
                       fr.received_at, fr.status, fr.remark, fr.store_id,
                       s.name AS store_name, u.username AS receiver
                FROM finance_receipts fr
                JOIN customers c ON c.customer_id=fr.customer_id
                LEFT JOIN contracts ct ON ct.contract_id=fr.contract_id
                LEFT JOIN stores s ON s.store_id=fr.store_id
                JOIN user_accounts u ON u.user_id=fr.receiver_user_id
                WHERE fr.tenant_id=%s AND {self._store_clause(user, 'fr')[0]}
                ORDER BY fr.receipt_id DESC
                LIMIT 200
                """,
                [user["tenant_id"], *self._store_clause(user, "fr")[1]],
            )
            return self._success({"list": rows, "total": len(rows)})
        if resource == "/rooms":
            self._require_permission(user, "ROOM.VIEW")
            rows = execute_all(
                connection,
                f"""
                SELECT r.room_id AS id, r.room_no,
                       COALESCE(rt.name, r.room_type) AS room_type,
                       rt.layout_name, rt.package_name, rt.bed_type,
                       r.floor, r.direction, r.layout_order,
                       r.price, r.status, r.store_id, s.name AS store_name,
                       c.name AS customer_name
                FROM rooms r
                JOIN stores s ON s.store_id=r.store_id
                LEFT JOIN room_types rt ON rt.room_type_id=r.room_type_id
                LEFT JOIN customers c ON c.customer_id=r.customer_id
                WHERE r.tenant_id=%s AND r.deleted_at IS NULL
                  AND {self._store_clause(user, 'r')[0]}
                ORDER BY r.store_id, r.floor, r.layout_order, r.room_no
                """,
                [user["tenant_id"], *self._store_clause(user, "r")[1]],
            )
            return self._success({"list": rows, "total": len(rows)})
        if resource == "/bookings":
            self._require_permission(user, "ROOM.VIEW")
            rows = execute_all(
                connection,
                f"""
                SELECT rb.booking_id AS id, rb.booking_no, rb.contract_id,
                       ct.contract_no, rb.customer_id, c.name AS customer_name,
                       rb.room_id, r.room_no, rb.check_in, rb.check_out,
                       rb.actual_check_in_at, rb.actual_check_out_at,
                       rb.status, rb.store_id, s.name AS store_name
                FROM room_bookings rb
                JOIN rooms r ON r.room_id=rb.room_id
                JOIN customers c ON c.customer_id=rb.customer_id
                LEFT JOIN contracts ct ON ct.contract_id=rb.contract_id
                LEFT JOIN stores s ON s.store_id=rb.store_id
                WHERE rb.tenant_id=%s AND rb.deleted_at IS NULL
                  AND {self._store_clause(user, 'rb')[0]}
                ORDER BY rb.booking_id DESC
                LIMIT 200
                """,
                [user["tenant_id"], *self._store_clause(user, "rb")[1]],
            )
            return self._success({"list": rows, "total": len(rows)})
        raise ApiError("资源不存在", 404, 40400)

    def _get_recovery_resource(
        self, connection, user: dict, resource: str, query: dict
    ):
        selected_store = str((query or {}).get("storeId") or "").strip()
        if selected_store and selected_store.lower() != "all":
            user = self._user_for_selected_store(user, query)
        if resource == "/options":
            self._require_any_permission(user, ("RECOVERY.VIEW",))
            store_clause, store_params = self._store_clause(user, "s")
            customer_clause, customer_params = self._store_clause(user, "c")
            staff_clause, staff_params = self._store_clause(user, "st")
            stores = execute_all(
                connection,
                f"""
                SELECT s.store_id AS id, s.name
                FROM stores s
                WHERE s.tenant_id=%s AND {store_clause}
                ORDER BY s.sort_weight DESC, s.store_id
                """,
                [user["tenant_id"], *store_params],
            )
            customers = execute_all(
                connection,
                f"""
                SELECT c.customer_id AS id, c.name, c.phone AS mobile,
                       c.status, c.store_id AS storeId, s.name AS store
                FROM customers c
                JOIN stores s ON s.store_id=c.store_id
                WHERE c.tenant_id=%s AND c.deleted_at IS NULL
                  AND {customer_clause}
                ORDER BY c.customer_id DESC
                LIMIT 300
                """,
                [user["tenant_id"], *customer_params],
            )
            for row in customers:
                row["mobile"] = self._masked_phone(user, row["mobile"])
            staff = execute_all(
                connection,
                f"""
                SELECT st.staff_id AS id, st.name, st.store_id AS storeId,
                       st.department, st.position
                FROM staff st
                WHERE st.tenant_id=%s AND st.employment_status='ACTIVE'
                  AND {staff_clause}
                  AND (
                    st.department LIKE '%%产康%%'
                    OR st.department_id=%s
                    OR st.staff_id=%s
                  )
                ORDER BY st.store_id, st.name
                """,
                [
                    user["tenant_id"],
                    *staff_params,
                    user.get("department_id"),
                    user.get("staff_id"),
                ],
            )
            return self._success(
                {"stores": stores, "customers": customers, "staff": staff}
            )

        match = re.fullmatch(r"/modules/([^/]+)", resource)
        if not match:
            raise ApiError("产康资源不存在", 404, 40400)
        module = match.group(1)
        self._require_recovery_access(user, module)
        if module in FORMAL_RECOVERY_RESOURCES:
            rows = self._operational_module_rows(
                connection,
                user,
                "RECOVERY",
                module,
                query,
            )
            return self._success(
                {"list": rows, "total": len(rows), "source": "mysql"}
            )
        rows = self._recovery_rows(connection, user, module)
        rows = self._filter_recovery_rows(rows, query)
        return self._success({"list": rows, "total": len(rows)})

    def _current_room_sql(self, customer_alias: str) -> str:
        return f"""
          (
            SELECT r.room_no
            FROM room_bookings rb
            JOIN rooms r ON r.room_id=rb.room_id
            WHERE rb.customer_id={customer_alias}.customer_id
              AND rb.status='已入住' AND rb.deleted_at IS NULL
            ORDER BY rb.actual_check_in_at DESC, rb.booking_id DESC
            LIMIT 1
          )
        """

    def _recovery_rows(self, connection, user: dict, resource: str) -> list:
        if resource in {
            "service-appointments",
            "staff-task-board",
            "technician-task-board",
        }:
            clause, params = self._store_clause(user, "ra")
            own_sql = ""
            if (
                resource == "technician-task-board"
                and "SYS_ADMIN" not in user["roles"]
            ):
                own_sql = " AND ra.technician_staff_id=%s"
                params.append(user.get("staff_id") or -1)
            rows = execute_all(
                connection,
                f"""
                SELECT ra.appointment_id AS id,
                       ra.appointment_no AS appointmentNo,
                       ra.customer_id AS customerId,
                       ra.entitlement_id AS entitlementId,
                       ra.store_id AS storeId,
                       c.name AS customerName, c.phone AS mobile,
                       {self._current_room_sql('c')} AS room,
                       s.name AS store, ra.service_name AS serviceItem,
                       ra.project_category AS serviceCategory,
                       ra.appointment_date AS appointmentDate,
                       CONCAT(
                         COALESCE(DATE_FORMAT(ra.period_start,'%%H:%%i'),''),
                         CASE WHEN ra.period_start IS NOT NULL
                                   OR ra.period_end IS NOT NULL THEN '-' ELSE '' END,
                         COALESCE(DATE_FORMAT(ra.period_end,'%%H:%%i'),'')
                       ) AS appointmentPeriod,
                       CONCAT(
                         COALESCE(DATE_FORMAT(ra.period_start,'%%H:%%i'),''),
                         CASE WHEN ra.period_start IS NOT NULL
                                   OR ra.period_end IS NOT NULL THEN '-' ELSE '' END,
                         COALESCE(DATE_FORMAT(ra.period_end,'%%H:%%i'),'')
                       ) AS timePeriod,
                       ra.technician_staff_id AS technicianStaffId,
                       st.name AS technician, st.name AS staffName,
                       st.department, ra.service_count AS serviceCount,
                       ra.status AS serviceStatus, ra.status AS taskStatus,
                       ra.service_place AS servicePlace,
                       creator.username AS createdBy,
                       ra.created_at AS createdAt, ra.remark
                FROM recovery_appointments ra
                JOIN customers c ON c.customer_id=ra.customer_id
                JOIN stores s ON s.store_id=ra.store_id
                LEFT JOIN staff st ON st.staff_id=ra.technician_staff_id
                JOIN user_accounts creator
                  ON creator.user_id=ra.created_by_user_id
                WHERE ra.tenant_id=%s AND ra.deleted_at IS NULL
                  AND {clause}{own_sql}
                ORDER BY ra.appointment_date DESC,
                         ra.period_start DESC, ra.appointment_id DESC
                LIMIT 1000
                """,
                [user["tenant_id"], *params],
            )
            for row in rows:
                row["mobile"] = self._masked_phone(user, row["mobile"])
                row["taskDate"] = row["appointmentDate"]
                row["usedCount"] = row["serviceCount"] if row["taskStatus"] == "已完成" else 0
            return rows

        if resource == "staff-schedule-settings":
            clause, params = self._store_clause(user, "rss")
            return execute_all(
                connection,
                f"""
                SELECT rss.schedule_id AS id, rss.store_id AS storeId,
                       rss.staff_id AS staffId, st.name AS staffName,
                       st.position AS jobTitle, s.name AS store,
                       rss.schedule_date AS scheduleDate,
                       rss.shift_name AS shiftName,
                       DATE_FORMAT(rss.start_time,'%%H:%%i') AS startTime,
                       DATE_FORMAT(rss.end_time,'%%H:%%i') AS endTime,
                       rss.max_bookings AS maxBookings,
                       (
                         SELECT COUNT(*)
                         FROM recovery_appointments ra
                         WHERE ra.technician_staff_id=rss.staff_id
                           AND ra.appointment_date=rss.schedule_date
                           AND ra.status NOT IN ('已取消')
                           AND ra.deleted_at IS NULL
                       ) AS bookedCount,
                       rss.status AS shiftStatus, rss.remark
                FROM recovery_staff_schedules rss
                JOIN staff st ON st.staff_id=rss.staff_id
                JOIN stores s ON s.store_id=rss.store_id
                WHERE rss.tenant_id=%s AND rss.deleted_at IS NULL
                  AND {clause}
                ORDER BY rss.schedule_date DESC, rss.start_time, st.name
                LIMIT 1000
                """,
                [user["tenant_id"], *params],
            )

        if resource in {
            "unbooked-customer-services",
            "customer-service-query",
            "service-overview-query",
        }:
            clause, params = self._store_clause(user, "e")
            unbooked = (
                " AND (e.total_count-e.used_count-e.booked_count)>0"
                if resource == "unbooked-customer-services"
                else ""
            )
            rows = execute_all(
                connection,
                f"""
                SELECT e.entitlement_id AS id,
                       e.entitlement_id AS entitlementId,
                       e.customer_id AS customerId, e.store_id AS storeId,
                       c.name AS customerName, c.phone AS mobile,
                       {self._current_room_sql('c')} AS room,
                       s.name AS store,
                       CASE
                         WHEN c.status='已入住' THEN '正入住'
                         WHEN c.status IN ('已退房','已退房已结账',
                                           '已退房但未结账') THEN '已出所'
                         ELSE '未入住'
                       END AS customerStatus,
                       c.delivery_type AS deliveryMode,
                       NULL AS deliveryDate,
                       (
                         SELECT rb.check_in FROM room_bookings rb
                         WHERE rb.customer_id=c.customer_id
                           AND rb.deleted_at IS NULL
                         ORDER BY rb.booking_id DESC LIMIT 1
                       ) AS checkInDate,
                       (
                         SELECT rb.check_out FROM room_bookings rb
                         WHERE rb.customer_id=c.customer_id
                           AND rb.deleted_at IS NULL
                         ORDER BY rb.booking_id DESC LIMIT 1
                       ) AS checkOutDate,
                       e.service_name AS serviceItem,
                       e.service_name AS serviceName,
                       e.project_category AS projectCategory,
                       e.source_type AS serviceType,
                       e.card_no AS cardNo, e.card_name AS cardName,
                       e.stage, e.unit, e.unit_price AS price,
                       e.duration_minutes AS durationMinutes,
                       e.total_count AS totalCount,
                       e.booked_count AS bookedCount,
                       e.used_count AS usedCount,
                       e.used_count AS completedCount,
                       GREATEST(e.total_count-e.used_count-e.booked_count,0)
                         AS remainingCount,
                       st.name AS technician,
                       e.valid_from AS startDate, e.valid_until AS validUntil,
                       e.valid_until AS deadline, e.valid_until AS endDate,
                       e.source_no AS salesDocumentNo,
                       e.source_no AS sourceNo
                FROM recovery_service_entitlements e
                JOIN customers c ON c.customer_id=e.customer_id
                JOIN stores s ON s.store_id=e.store_id
                LEFT JOIN staff st ON st.staff_id=e.assigned_staff_id
                WHERE e.tenant_id=%s AND e.deleted_at IS NULL
                  AND e.status='有效' AND {clause}{unbooked}
                ORDER BY c.name, e.valid_until, e.entitlement_id
                LIMIT 1000
                """,
                [user["tenant_id"], *params],
            )
            today = date.today()
            for row in rows:
                row["mobile"] = self._masked_phone(user, row["mobile"])
                row["serviceCategory"] = row["projectCategory"]
                row["remainingQuantity"] = row["remainingCount"]
                row["quantity"] = row["totalCount"]
                row["assignee"] = row["technician"]
                if row.get("validUntil"):
                    row["remainingDays"] = max(
                        (row["validUntil"] - today).days, 0
                    )
                else:
                    row["remainingDays"] = None
                minutes = row.get("durationMinutes")
                row["duration"] = (
                    float(minutes) / 60 if minutes is not None else None
                )
            return rows

        if resource == "rehab-service-records":
            clause, params = self._store_clause(user, "rr")
            rows = execute_all(
                connection,
                f"""
                SELECT rr.record_id AS id, rr.record_no AS recordNo,
                       rr.customer_id AS customerId, rr.store_id AS storeId,
                       c.name AS customerName, c.phone AS mobile,
                       {self._current_room_sql('c')} AS room,
                       s.name AS store, rr.service_name AS serviceItem,
                       rr.service_date AS serviceDate,
                       CONCAT(
                         COALESCE(DATE_FORMAT(rr.period_start,'%%H:%%i'),''),
                         CASE WHEN rr.period_start IS NOT NULL
                                   OR rr.period_end IS NOT NULL THEN '-' ELSE '' END,
                         COALESCE(DATE_FORMAT(rr.period_end,'%%H:%%i'),'')
                       ) AS servicePeriod,
                       rr.technician_staff_id AS technicianStaffId,
                       st.name AS technician, rr.used_count AS usedCount,
                       rr.service_result AS serviceResult,
                       rr.customer_feedback AS customerFeedback,
                       rr.review_status AS reviewStatus,
                       creator.username AS createdBy, rr.created_at AS createdAt
                FROM recovery_service_records rr
                JOIN customers c ON c.customer_id=rr.customer_id
                JOIN stores s ON s.store_id=rr.store_id
                JOIN staff st ON st.staff_id=rr.technician_staff_id
                JOIN user_accounts creator
                  ON creator.user_id=rr.created_by_user_id
                WHERE rr.tenant_id=%s AND rr.deleted_at IS NULL
                  AND {clause}
                ORDER BY rr.service_date DESC, rr.record_id DESC
                LIMIT 1000
                """,
                [user["tenant_id"], *params],
            )
            for row in rows:
                row["mobile"] = self._masked_phone(user, row["mobile"])
            return rows

        if resource == "completed-service-consumption":
            clause, params = self._store_clause(user, "mc")
            return execute_all(
                connection,
                f"""
                SELECT mc.consumption_id AS id,
                       mc.document_no AS documentNo,
                       rr.customer_id AS customerId,
                       c.name AS customerName, s.name AS store,
                       rr.service_name AS serviceItem,
                       rr.service_date AS completedAt,
                       st.name AS technician, rr.used_count AS usedCount,
                       mc.material_name AS materialName,
                       mc.material_category AS materialCategory,
                       mc.quantity AS materialQuantity, mc.unit,
                       mc.warehouse_name AS warehouse,
                       mc.stock_status AS stockStatus
                FROM recovery_material_consumptions mc
                JOIN recovery_service_records rr
                  ON rr.record_id=mc.service_record_id
                JOIN customers c ON c.customer_id=rr.customer_id
                JOIN stores s ON s.store_id=mc.store_id
                JOIN staff st ON st.staff_id=rr.technician_staff_id
                WHERE mc.tenant_id=%s AND {clause}
                ORDER BY rr.service_date DESC, mc.consumption_id DESC
                LIMIT 1000
                """,
                [user["tenant_id"], *params],
            )

        if resource == "rehab-health-assessments":
            clause, params = self._store_clause(user, "ha")
            rows = execute_all(
                connection,
                f"""
                SELECT ha.assessment_id AS id,
                       ha.assessment_no AS assessmentNo,
                       ha.customer_id AS customerId, ha.store_id AS storeId,
                       c.name AS customerName, c.phone AS mobile,
                       {self._current_room_sql('c')} AS room,
                       s.name AS store, ha.assessment_name AS assessmentName,
                       ha.assessment_type AS assessmentType,
                       ha.assessed_at AS assessedAt,
                       ha.postpartum_days AS postpartumDays,
                       st.name AS assessor, ha.main_concern AS mainConcern,
                       ha.assessment_result AS assessmentResult,
                       ha.recommendation, ha.contraindication,
                       ha.created_at AS createdAt
                FROM recovery_health_assessments ha
                JOIN customers c ON c.customer_id=ha.customer_id
                JOIN stores s ON s.store_id=ha.store_id
                JOIN staff st ON st.staff_id=ha.assessor_staff_id
                WHERE ha.tenant_id=%s AND ha.deleted_at IS NULL
                  AND {clause}
                ORDER BY ha.assessed_at DESC, ha.assessment_id DESC
                LIMIT 1000
                """,
                [user["tenant_id"], *params],
            )
            for row in rows:
                row["mobile"] = self._masked_phone(user, row["mobile"])
            return rows
        raise ApiError("产康资源不存在", 404, 40400)

    def _filter_recovery_rows(self, rows: list, query: dict) -> list:
        aliases = {
            "customerName": ("customerName",),
            "mobile": ("mobile",),
            "serviceItem": ("serviceItem", "serviceName"),
            "serviceName": ("serviceItem", "serviceName"),
            "technician": ("technician", "staffName"),
            "staffName": ("staffName", "technician"),
            "store": ("store",),
            "customerStatus": ("customerStatus",),
            "serviceStatus": ("serviceStatus", "taskStatus"),
            "taskStatus": ("taskStatus", "serviceStatus"),
            "shiftStatus": ("shiftStatus",),
            "assessmentType": ("assessmentType",),
            "materialName": ("materialName",),
            "serviceType": ("serviceType",),
            "projectCategory": ("projectCategory",),
        }
        result = rows
        for key, target_keys in aliases.items():
            value = str(query.get(key) or "").strip()
            if not value or value in {"-全部-", "-请选择-", "全部"}:
                continue
            if key == "store":
                if "黄河路" in value:
                    value = "黄河路"
                elif "中心广场" in value:
                    value = "建设路"
            result = [
                row
                for row in result
                if any(
                    value in str(row.get(target) or "")
                    for target in target_keys
                )
            ]
        customer_id = str(query.get("customerId") or "").strip()
        if customer_id:
            result = [
                row
                for row in result
                if str(row.get("customerId") or "") == customer_id
            ]
        card_no = str(query.get("cardNo") or "").strip()
        if card_no:
            result = [
                row for row in result if str(row.get("cardNo") or "") == card_no
            ]
        remaining_max = str(query.get("remainingMax") or "").strip()
        if remaining_max:
            try:
                maximum = Decimal(remaining_max)
                result = [
                    row
                    for row in result
                    if Decimal(str(row.get("remainingCount") or 0)) <= maximum
                ]
            except ArithmeticError as exc:
                raise ApiError("剩余次数必须是数字") from exc
        return result

    def _overview(self, connection, user: dict):
        result = {}
        for key, table, permission in (
            ("customers", "customers", "CUSTOMER.VIEW"),
            ("contracts", "contracts", "SALES.VIEW"),
            ("receipts", "finance_receipts", "FINANCE.VIEW"),
            ("bookings", "room_bookings", "ROOM.VIEW"),
        ):
            if not self._has_permission(user, permission):
                result[key] = 0
                continue
            clause, params = self._store_clause(user)
            deleted_filter = (
                " AND deleted_at IS NULL"
                if table in {"customers", "contracts", "room_bookings"}
                else ""
            )
            row = execute_one(
                connection,
                f"""
                SELECT COUNT(*) AS total FROM {table}
                WHERE tenant_id=%s AND {clause}{deleted_filter}
                """,
                [user["tenant_id"], *params],
            )
            result[key] = row["total"]
        result["pendingContracts"] = 0
        if self._has_permission(user, "SALES.VIEW"):
            result["pendingContracts"] = execute_one(
                connection,
                f"""
                SELECT COUNT(*) AS total FROM contracts
                WHERE tenant_id=%s AND status='已签合同但未审核'
                  AND {self._store_clause(user)[0]}
                """,
                [user["tenant_id"], *self._store_clause(user)[1]],
            )["total"]
        result["pendingReceipts"] = 0
        if self._has_permission(user, "FINANCE.VIEW"):
            result["pendingReceipts"] = execute_one(
                connection,
                f"""
                SELECT COUNT(*) AS total FROM finance_receipts
                WHERE tenant_id=%s AND status='待审核'
                  AND {self._store_clause(user)[0]}
                """,
                [user["tenant_id"], *self._store_clause(user)[1]],
            )["total"]
        return self._success(result)

    def _post_recovery_resource(
        self, connection, user: dict, resource: str, body: dict
    ):
        match = re.fullmatch(r"/modules/([^/]+)/(save|action)", resource)
        if not match:
            raise ApiError("产康资源不存在", 404, 40400)
        module, operation = match.groups()
        if module not in RECOVERY_RESOURCE_NAV_IDS:
            raise ApiError("产康资源不存在", 404, 40400)
        if module in FORMAL_RECOVERY_RESOURCES:
            return self._post_operational_module_record(
                connection,
                user,
                "RECOVERY",
                module,
                operation,
                body,
            )
        if operation == "save":
            return self._save_recovery_record(connection, user, module, body)
        return self._perform_recovery_action(connection, user, module, body)

    def _save_recovery_record(
        self, connection, user: dict, resource: str, body: dict
    ):
        record_id = int(body.get("id") or 0)
        if resource in {
            "service-appointments",
            "staff-task-board",
            "technician-task-board",
        }:
            if record_id:
                raise ApiError("原角色未授权编辑服务预约", 403, 40300)
            create_action = (
                "服务预约"
                if resource == "service-appointments"
                else "添加"
            )
            self._require_recovery_access(user, resource, create_action)
            return self._create_recovery_appointment(
                connection, user, body
            )

        if resource == "staff-schedule-settings":
            self._require_recovery_access(
                user, resource, "编辑" if record_id else "添加"
            )
            return self._save_recovery_schedule(
                connection, user, body, record_id
            )

        if resource == "rehab-service-records":
            if not record_id:
                raise ApiError("原角色未授权新增服务记录", 403, 40300)
            self._require_recovery_access(user, resource, "编辑")
            return self._update_recovery_service_record(
                connection, user, body, record_id
            )

        if resource == "rehab-health-assessments":
            self._require_recovery_access(
                user, resource, "编辑" if record_id else "添加"
            )
            return self._save_recovery_assessment(
                connection, user, body, record_id
            )
        raise ApiError("当前页面没有保存操作", 403, 40300)

    def _create_recovery_appointment(
        self, connection, user: dict, body: dict
    ):
        store_id = self._recovery_store_id(connection, user, body)
        customer = self._recovery_customer(
            connection, user, body, store_id
        )
        staff = self._recovery_staff(
            connection, user, body, store_id
        )
        service_name = str(
            body.get("serviceItem") or body.get("serviceName") or ""
        ).strip()
        if not service_name:
            raise ApiError("服务项目不能为空")
        appointment_date = str(
            body.get("appointmentDate") or body.get("taskDate") or ""
        ).strip()
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", appointment_date):
            raise ApiError("请选择预约日期")
        if appointment_date < date.today().isoformat():
            raise ApiError("预约日期不能早于今天")
        start, end = self._appointment_period(body)
        if not start or not end:
            raise ApiError("预约时段格式应为 HH:mm-HH:mm")
        start = datetime.strptime(start, "%H:%M").strftime("%H:%M")
        end = datetime.strptime(end, "%H:%M").strftime("%H:%M")
        if start >= end:
            raise ApiError("预约结束时间必须晚于开始时间")
        try:
            service_count = Decimal(str(body.get("serviceCount") or 1))
        except ArithmeticError as exc:
            raise ApiError("服务次数不正确") from exc
        if service_count <= 0:
            raise ApiError("服务次数必须大于 0")

        entitlement_id = int(body.get("entitlementId") or 0) or None
        entitlement = None
        if entitlement_id:
            entitlement = execute_one(
                connection,
                """
                SELECT entitlement_id, customer_id, store_id, service_name,
                       total_count, used_count, booked_count, status
                FROM recovery_service_entitlements
                WHERE entitlement_id=%s AND tenant_id=%s
                  AND deleted_at IS NULL FOR UPDATE
                """,
                (entitlement_id, user["tenant_id"]),
            )
            if (
                not entitlement
                or entitlement["customer_id"] != customer["customer_id"]
                or entitlement["store_id"] != store_id
                or entitlement["status"] != "有效"
            ):
                raise ApiError("客户可用服务不存在")
            available = (
                entitlement["total_count"]
                - entitlement["used_count"]
                - entitlement["booked_count"]
            )
            if service_count > available:
                raise ApiError("预约次数不能超过可用剩余次数")
            service_name = entitlement["service_name"]

        conflict = execute_one(
            connection,
            """
            SELECT appointment_id
            FROM recovery_appointments
            WHERE tenant_id=%s AND store_id=%s
              AND technician_staff_id=%s AND appointment_date=%s
              AND deleted_at IS NULL AND status<>'已取消'
              AND NOT (period_end<=%s OR period_start>=%s)
            LIMIT 1
            """,
            (
                user["tenant_id"],
                store_id,
                staff["staff_id"],
                appointment_date,
                start,
                end,
            ),
        )
        if conflict:
            raise ApiError("该服务人员在所选时段已有预约")

        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO recovery_appointments(
                  appointment_no, tenant_id, store_id, customer_id,
                  entitlement_id, service_name, project_category,
                  appointment_date, period_start, period_end,
                  technician_staff_id, service_place, service_count,
                  status, remark, created_by_user_id
                ) VALUES (
                  'PENDING',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                  '已预约',%s,%s
                )
                """,
                (
                    user["tenant_id"],
                    store_id,
                    customer["customer_id"],
                    entitlement_id,
                    service_name,
                    body.get("serviceCategory")
                    or body.get("projectCategory")
                    or None,
                    appointment_date,
                    start,
                    end,
                    staff["staff_id"],
                    body.get("servicePlace") or None,
                    service_count,
                    body.get("remark") or None,
                    user["user_id"],
                ),
            )
            appointment_id = cursor.lastrowid
            appointment_no = (
                f"PKYY-{datetime.now():%Y%m%d}-{appointment_id:05d}"
            )
            cursor.execute(
                """
                UPDATE recovery_appointments
                SET appointment_no=%s WHERE appointment_id=%s
                """,
                (appointment_no, appointment_id),
            )
            if entitlement_id:
                cursor.execute(
                    """
                    UPDATE recovery_service_entitlements
                    SET booked_count=booked_count+%s
                    WHERE entitlement_id=%s
                    """,
                    (service_count, entitlement_id),
                )
        self._audit(
            connection,
            user,
            "RECOVERY_APPOINTMENT",
            appointment_id,
            "CREATE",
            store_id,
            None,
            "已预约",
        )
        connection.commit()
        return self._success(
            {"id": appointment_id, "appointmentNo": appointment_no}
        )

    def _save_recovery_schedule(
        self, connection, user: dict, body: dict, schedule_id: int
    ):
        store_id = self._recovery_store_id(connection, user, body)
        staff = self._recovery_staff(
            connection,
            user,
            body,
            store_id,
            key="staffId",
            name_key="staffName",
        )
        schedule_date = str(body.get("scheduleDate") or "").strip()
        shift_name = str(body.get("shiftName") or "").strip()
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", schedule_date):
            raise ApiError("请选择排班日期")
        if not shift_name:
            raise ApiError("班次不能为空")
        status = str(body.get("shiftStatus") or "出勤").strip()
        if status not in {"出勤", "休息", "请假", "停诊"}:
            raise ApiError("排班状态不正确")
        start, end = self._appointment_period(
            {
                "periodStart": body.get("startTime"),
                "periodEnd": body.get("endTime"),
            }
        )
        try:
            max_bookings = int(body.get("maxBookings") or 0)
        except ValueError as exc:
            raise ApiError("可预约人数不正确") from exc
        if max_bookings < 0:
            raise ApiError("可预约人数不能小于 0")

        before = None
        with connection.cursor() as cursor:
            if schedule_id:
                before = execute_one(
                    connection,
                    """
                    SELECT schedule_id, store_id, status
                    FROM recovery_staff_schedules
                    WHERE schedule_id=%s AND tenant_id=%s
                      AND deleted_at IS NULL FOR UPDATE
                    """,
                    (schedule_id, user["tenant_id"]),
                )
                if not before:
                    raise ApiError("排班记录不存在")
                self._allowed_store(user, before["store_id"])
                cursor.execute(
                    """
                    UPDATE recovery_staff_schedules
                    SET store_id=%s, staff_id=%s, schedule_date=%s,
                        shift_name=%s, start_time=%s, end_time=%s,
                        max_bookings=%s, status=%s, remark=%s,
                        version=version+1
                    WHERE schedule_id=%s
                    """,
                    (
                        store_id,
                        staff["staff_id"],
                        schedule_date,
                        shift_name,
                        start,
                        end,
                        max_bookings,
                        status,
                        body.get("remark") or None,
                        schedule_id,
                    ),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO recovery_staff_schedules(
                      tenant_id, store_id, staff_id, schedule_date,
                      shift_name, start_time, end_time, max_bookings,
                      status, remark, created_by_user_id
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        user["tenant_id"],
                        store_id,
                        staff["staff_id"],
                        schedule_date,
                        shift_name,
                        start,
                        end,
                        max_bookings,
                        status,
                        body.get("remark") or None,
                        user["user_id"],
                    ),
                )
                schedule_id = cursor.lastrowid
        self._audit(
            connection,
            user,
            "RECOVERY_SCHEDULE",
            schedule_id,
            "UPDATE" if before else "CREATE",
            store_id,
            before["status"] if before else None,
            status,
        )
        connection.commit()
        return self._success({"id": schedule_id})

    def _update_recovery_service_record(
        self, connection, user: dict, body: dict, record_id: int
    ):
        record = execute_one(
            connection,
            """
            SELECT record_id, store_id, entitlement_id, used_count,
                   review_status
            FROM recovery_service_records
            WHERE record_id=%s AND tenant_id=%s AND deleted_at IS NULL
            FOR UPDATE
            """,
            (record_id, user["tenant_id"]),
        )
        if not record:
            raise ApiError("服务记录不存在")
        self._allowed_store(user, record["store_id"])
        if record["review_status"] == "已审核":
            raise ApiError("已审核记录不能编辑")
        staff = self._recovery_staff(
            connection, user, body, record["store_id"]
        )
        service_date = str(body.get("serviceDate") or "").strip()
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", service_date):
            raise ApiError("请选择服务日期")
        start, end = self._appointment_period(body)
        try:
            used_count = Decimal(str(body.get("usedCount") or 1))
        except ArithmeticError as exc:
            raise ApiError("耗卡次数不正确") from exc
        if used_count <= 0:
            raise ApiError("耗卡次数必须大于 0")
        if record["entitlement_id"] and used_count != record["used_count"]:
            entitlement = execute_one(
                connection,
                """
                SELECT total_count, used_count
                FROM recovery_service_entitlements
                WHERE entitlement_id=%s FOR UPDATE
                """,
                (record["entitlement_id"],),
            )
            adjusted = (
                entitlement["used_count"]
                - record["used_count"]
                + used_count
            )
            if adjusted < 0 or adjusted > entitlement["total_count"]:
                raise ApiError("修改后的耗卡次数超过服务权益总次数")
        with connection.cursor() as cursor:
            if record["entitlement_id"] and used_count != record["used_count"]:
                cursor.execute(
                    """
                    UPDATE recovery_service_entitlements
                    SET used_count=used_count-%s+%s
                    WHERE entitlement_id=%s
                    """,
                    (
                        record["used_count"],
                        used_count,
                        record["entitlement_id"],
                    ),
                )
            cursor.execute(
                """
                UPDATE recovery_service_records
                SET service_date=%s, period_start=%s, period_end=%s,
                    technician_staff_id=%s, used_count=%s,
                    service_result=%s, customer_feedback=%s,
                    version=version+1
                WHERE record_id=%s
                """,
                (
                    service_date,
                    start,
                    end,
                    staff["staff_id"],
                    used_count,
                    body.get("serviceResult") or None,
                    body.get("customerFeedback") or None,
                    record_id,
                ),
            )
        self._audit(
            connection,
            user,
            "RECOVERY_RECORD",
            record_id,
            "UPDATE",
            record["store_id"],
            record["review_status"],
            record["review_status"],
        )
        connection.commit()
        return self._success({"id": record_id})

    def _save_recovery_assessment(
        self, connection, user: dict, body: dict, assessment_id: int
    ):
        store_id = self._recovery_store_id(connection, user, body)
        customer = self._recovery_customer(
            connection, user, body, store_id
        )
        staff = self._recovery_staff(
            connection,
            user,
            body,
            store_id,
            key="assessorStaffId",
            name_key="assessor",
        )
        assessed_at = str(body.get("assessedAt") or "").strip()
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", assessed_at):
            raise ApiError("请选择评估日期")
        result = str(body.get("assessmentResult") or "").strip()
        if not result:
            raise ApiError("评估结果不能为空")
        assessment_name = str(
            body.get("assessmentName")
            or body.get("assessmentType")
            or "产康健康评估"
        ).strip()
        before = None
        with connection.cursor() as cursor:
            if assessment_id:
                before = execute_one(
                    connection,
                    """
                    SELECT assessment_id, store_id
                    FROM recovery_health_assessments
                    WHERE assessment_id=%s AND tenant_id=%s
                      AND deleted_at IS NULL FOR UPDATE
                    """,
                    (assessment_id, user["tenant_id"]),
                )
                if not before:
                    raise ApiError("健康评估不存在")
                self._allowed_store(user, before["store_id"])
                cursor.execute(
                    """
                    UPDATE recovery_health_assessments
                    SET store_id=%s, customer_id=%s, assessment_name=%s,
                        assessment_type=%s, assessed_at=%s,
                        assessor_staff_id=%s, main_concern=%s,
                        assessment_result=%s, recommendation=%s,
                        contraindication=%s, version=version+1
                    WHERE assessment_id=%s
                    """,
                    (
                        store_id,
                        customer["customer_id"],
                        assessment_name,
                        body.get("assessmentType") or None,
                        assessed_at,
                        staff["staff_id"],
                        body.get("mainConcern") or None,
                        result,
                        body.get("recommendation") or None,
                        body.get("contraindication") or None,
                        assessment_id,
                    ),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO recovery_health_assessments(
                      assessment_no, tenant_id, store_id, customer_id,
                      assessment_name, assessment_type, assessed_at,
                      assessor_staff_id, main_concern, assessment_result,
                      recommendation, contraindication, created_by_user_id
                    ) VALUES (
                      'PENDING',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
                    )
                    """,
                    (
                        user["tenant_id"],
                        store_id,
                        customer["customer_id"],
                        assessment_name,
                        body.get("assessmentType") or None,
                        assessed_at,
                        staff["staff_id"],
                        body.get("mainConcern") or None,
                        result,
                        body.get("recommendation") or None,
                        body.get("contraindication") or None,
                        user["user_id"],
                    ),
                )
                assessment_id = cursor.lastrowid
                assessment_no = (
                    f"PKPG-{datetime.now():%Y%m%d}-{assessment_id:05d}"
                )
                cursor.execute(
                    """
                    UPDATE recovery_health_assessments
                    SET assessment_no=%s WHERE assessment_id=%s
                    """,
                    (assessment_no, assessment_id),
                )
        self._audit(
            connection,
            user,
            "RECOVERY_ASSESSMENT",
            assessment_id,
            "UPDATE" if before else "CREATE",
            store_id,
            None,
            None,
        )
        connection.commit()
        return self._success({"id": assessment_id})

    def _perform_recovery_action(
        self, connection, user: dict, resource: str, body: dict
    ):
        action = re.sub(r"\s+", "", str(body.get("action") or ""))
        self._require_recovery_access(user, resource, action)
        record_id = int(body.get("id") or 0)
        if not record_id:
            raise ApiError("请选择一条业务记录")

        if action == "设置" and resource == "unbooked-customer-services":
            entitlement = execute_one(
                connection,
                """
                SELECT entitlement_id, store_id
                FROM recovery_service_entitlements
                WHERE entitlement_id=%s AND tenant_id=%s
                  AND deleted_at IS NULL FOR UPDATE
                """,
                (record_id, user["tenant_id"]),
            )
            if not entitlement:
                raise ApiError("客户服务权益不存在")
            self._allowed_store(user, entitlement["store_id"])
            staff = self._recovery_staff(
                connection, user, body, entitlement["store_id"]
            )
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE recovery_service_entitlements
                    SET assigned_staff_id=%s WHERE entitlement_id=%s
                    """,
                    (staff["staff_id"], record_id),
                )
            connection.commit()
            return self._success({"id": record_id})

        if resource in {
            "service-appointments",
            "staff-task-board",
            "technician-task-board",
        } and action in {"预约确认", "确认完成", "取消"}:
            return self._transition_recovery_appointment(
                connection, user, record_id, action, body
            )

        if resource == "rehab-service-records" and action == "批量修改":
            record = execute_one(
                connection,
                """
                SELECT record_id, store_id, review_status
                FROM recovery_service_records
                WHERE record_id=%s AND tenant_id=%s
                  AND deleted_at IS NULL FOR UPDATE
                """,
                (record_id, user["tenant_id"]),
            )
            if not record:
                raise ApiError("服务记录不存在")
            self._allowed_store(user, record["store_id"])
            if record["review_status"] == "已审核":
                raise ApiError("已审核记录不能批量修改")
            staff = self._recovery_staff(
                connection, user, body, record["store_id"]
            )
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE recovery_service_records
                    SET technician_staff_id=%s, version=version+1
                    WHERE record_id=%s
                    """,
                    (staff["staff_id"], record_id),
                )
            self._audit(
                connection,
                user,
                "RECOVERY_RECORD",
                record_id,
                "BATCH_UPDATE",
                record["store_id"],
                record["review_status"],
                record["review_status"],
            )
            connection.commit()
            return self._success({"id": record_id})

        if resource == "rehab-service-records" and action == "删除":
            record = execute_one(
                connection,
                """
                SELECT record_id, store_id, appointment_id, entitlement_id,
                       used_count, review_status
                FROM recovery_service_records
                WHERE record_id=%s AND tenant_id=%s
                  AND deleted_at IS NULL FOR UPDATE
                """,
                (record_id, user["tenant_id"]),
            )
            if not record:
                raise ApiError("服务记录不存在")
            self._allowed_store(user, record["store_id"])
            if record["review_status"] == "已审核":
                raise ApiError("已审核记录不能删除")
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE recovery_service_records
                    SET deleted_at=NOW(), version=version+1
                    WHERE record_id=%s
                    """,
                    (record_id,),
                )
                if record["appointment_id"]:
                    cursor.execute(
                        """
                        UPDATE recovery_appointments
                        SET status='待服务', completed_at=NULL,
                            version=version+1
                        WHERE appointment_id=%s
                        """,
                        (record["appointment_id"],),
                    )
                if record["entitlement_id"]:
                    cursor.execute(
                        """
                        UPDATE recovery_service_entitlements
                        SET used_count=GREATEST(used_count-%s,0),
                            booked_count=booked_count+%s
                        WHERE entitlement_id=%s
                        """,
                        (
                            record["used_count"],
                            record["used_count"],
                            record["entitlement_id"],
                        ),
                    )
            self._audit(
                connection,
                user,
                "RECOVERY_RECORD",
                record_id,
                "DELETE",
                record["store_id"],
                record["review_status"],
                None,
            )
            connection.commit()
            return self._success({"id": record_id})

        if action == "删除":
            table_map = {
                "staff-schedule-settings": ("recovery_staff_schedules", "schedule_id"),
                "rehab-health-assessments": (
                    "recovery_health_assessments",
                    "assessment_id",
                ),
            }
            target = table_map.get(resource)
            if not target:
                raise ApiError("当前页面不支持删除")
            table, id_column = target
            row = execute_one(
                connection,
                f"""
                SELECT {id_column} AS id, store_id
                FROM {table}
                WHERE {id_column}=%s AND tenant_id=%s
                  AND deleted_at IS NULL FOR UPDATE
                """,
                (record_id, user["tenant_id"]),
            )
            if not row:
                raise ApiError("业务记录不存在")
            self._allowed_store(user, row["store_id"])
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    UPDATE {table} SET deleted_at=NOW()
                    WHERE {id_column}=%s
                    """,
                    (record_id,),
                )
            self._audit(
                connection,
                user,
                "RECOVERY_DELETE",
                record_id,
                "DELETE",
                row["store_id"],
                None,
                None,
                {"resource": resource},
            )
            connection.commit()
            return self._success({"id": record_id})

        if (
            resource == "rehab-service-records"
            and action in {"审核", "反审核"}
        ):
            record = execute_one(
                connection,
                """
                SELECT record_id, store_id, review_status
                FROM recovery_service_records
                WHERE record_id=%s AND tenant_id=%s
                  AND deleted_at IS NULL FOR UPDATE
                """,
                (record_id, user["tenant_id"]),
            )
            if not record:
                raise ApiError("服务记录不存在")
            self._allowed_store(user, record["store_id"])
            target = "已审核" if action == "审核" else "未审核"
            expected = "未审核" if action == "审核" else "已审核"
            if record["review_status"] != expected:
                raise ApiError(f"只有{expected}记录可以{action}")
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE recovery_service_records
                    SET review_status=%s, reviewed_by_user_id=%s,
                        reviewed_at=%s, version=version+1
                    WHERE record_id=%s
                    """,
                    (
                        target,
                        user["user_id"] if target == "已审核" else None,
                        datetime.now() if target == "已审核" else None,
                        record_id,
                    ),
                )
            self._audit(
                connection,
                user,
                "RECOVERY_RECORD",
                record_id,
                action,
                record["store_id"],
                expected,
                target,
            )
            connection.commit()
            return self._success({"id": record_id, "status": target})
        raise ApiError("当前操作尚未接入", 400, 40000)

    def _transition_recovery_appointment(
        self,
        connection,
        user: dict,
        appointment_id: int,
        action: str,
        body: dict,
    ):
        appointment = execute_one(
            connection,
            """
            SELECT appointment_id, appointment_no, tenant_id, store_id,
                   customer_id, entitlement_id, service_name,
                   project_category, appointment_date, period_start,
                   period_end, technician_staff_id, service_count, status
            FROM recovery_appointments
            WHERE appointment_id=%s AND tenant_id=%s
              AND deleted_at IS NULL FOR UPDATE
            """,
            (appointment_id, user["tenant_id"]),
        )
        if not appointment:
            raise ApiError("服务预约不存在")
        self._allowed_store(user, appointment["store_id"])

        if action == "预约确认":
            if appointment["status"] != "已预约":
                raise ApiError("只有已预约记录可以预约确认")
            target = "待服务"
        elif action == "取消":
            if appointment["status"] in {"已完成", "已取消"}:
                raise ApiError("已完成或已取消预约不能再次取消")
            target = "已取消"
        else:
            if appointment["status"] not in {"已预约", "待服务", "服务中"}:
                raise ApiError("当前状态不能确认完成")
            target = "已完成"

        completed_count = appointment["service_count"]
        completion_date = appointment["appointment_date"]
        completion_start = appointment["period_start"]
        completion_end = appointment["period_end"]
        technician_staff_id = appointment["technician_staff_id"]
        if action == "确认完成":
            try:
                completed_count = Decimal(
                    str(body.get("usedCount") or appointment["service_count"])
                )
            except ArithmeticError as exc:
                raise ApiError("本次耗卡次数不正确") from exc
            if (
                completed_count <= 0
                or completed_count > appointment["service_count"]
            ):
                raise ApiError("本次耗卡次数必须大于 0 且不能超过预约次数")
            requested_date = str(body.get("serviceDate") or "").strip()
            if requested_date:
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", requested_date):
                    raise ApiError("服务日期格式不正确")
                completion_date = requested_date
            if body.get("servicePeriod"):
                completion_start, completion_end = self._appointment_period(body)
            if body.get("technician") or body.get("technicianStaffId"):
                staff = self._recovery_staff(
                    connection, user, body, appointment["store_id"]
                )
                technician_staff_id = staff["staff_id"]

        with connection.cursor() as cursor:
            if action == "预约确认":
                cursor.execute(
                    """
                    UPDATE recovery_appointments
                    SET status=%s, confirmed_at=NOW(), version=version+1
                    WHERE appointment_id=%s
                    """,
                    (target, appointment_id),
                )
            elif action == "取消":
                cursor.execute(
                    """
                    UPDATE recovery_appointments
                    SET status=%s, cancelled_at=NOW(), version=version+1
                    WHERE appointment_id=%s
                    """,
                    (target, appointment_id),
                )
                if appointment["entitlement_id"]:
                    cursor.execute(
                        """
                        UPDATE recovery_service_entitlements
                        SET booked_count=GREATEST(booked_count-%s,0)
                        WHERE entitlement_id=%s
                        """,
                        (
                            appointment["service_count"],
                            appointment["entitlement_id"],
                        ),
                    )
            else:
                if appointment["entitlement_id"]:
                    entitlement = execute_one(
                        connection,
                        """
                        SELECT total_count, used_count, booked_count
                        FROM recovery_service_entitlements
                        WHERE entitlement_id=%s FOR UPDATE
                        """,
                        (appointment["entitlement_id"],),
                    )
                    if (
                        not entitlement
                        or entitlement["used_count"]
                        + completed_count
                        > entitlement["total_count"]
                    ):
                        raise ApiError("服务权益剩余次数不足")
                    cursor.execute(
                        """
                        UPDATE recovery_service_entitlements
                        SET used_count=used_count+%s,
                            booked_count=GREATEST(booked_count-%s,0)
                        WHERE entitlement_id=%s
                        """,
                        (
                            completed_count,
                            appointment["service_count"],
                            appointment["entitlement_id"],
                        ),
                    )
                cursor.execute(
                    """
                    UPDATE recovery_appointments
                    SET status='已完成', completed_at=NOW(),
                        technician_staff_id=%s,
                        version=version+1
                    WHERE appointment_id=%s
                    """,
                    (technician_staff_id, appointment_id),
                )
                cursor.execute(
                    """
                    INSERT INTO recovery_service_records(
                      record_no, tenant_id, store_id, customer_id,
                      appointment_id, entitlement_id, service_name,
                      project_category, technician_staff_id, service_date,
                      period_start, period_end, used_count,
                      created_by_user_id
                    ) VALUES (
                      'PENDING',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
                    )
                    """,
                    (
                        user["tenant_id"],
                        appointment["store_id"],
                        appointment["customer_id"],
                        appointment_id,
                        appointment["entitlement_id"],
                        appointment["service_name"],
                        appointment["project_category"],
                        technician_staff_id,
                        completion_date,
                        completion_start,
                        completion_end,
                        completed_count,
                        user["user_id"],
                    ),
                )
                record_id = cursor.lastrowid
                record_no = (
                    f"PKJL-{datetime.now():%Y%m%d}-{record_id:05d}"
                )
                cursor.execute(
                    """
                    UPDATE recovery_service_records
                    SET record_no=%s WHERE record_id=%s
                    """,
                    (record_no, record_id),
                )
                cursor.execute(
                    """
                    UPDATE recovery_service_records
                    SET service_result=%s, customer_feedback=%s
                    WHERE record_id=%s
                    """,
                    (
                        body.get("serviceResult") or None,
                        body.get("customerFeedback") or None,
                        record_id,
                    ),
                )
        self._audit(
            connection,
            user,
            "RECOVERY_APPOINTMENT",
            appointment_id,
            action,
            appointment["store_id"],
            appointment["status"],
            target,
        )
        connection.commit()
        return self._success({"id": appointment_id, "status": target})

    def _post_resource(self, connection, user: dict, resource: str, body: dict):
        if resource == "/customers":
            return self._create_customer(connection, user, body)
        if resource == "/contracts":
            return self._create_contract(connection, user, body)
        match = re.fullmatch(r"/contracts/(\d+)/approve", resource)
        if match:
            return self._approve_contract(connection, user, int(match.group(1)))
        if resource == "/receipts":
            return self._create_receipt(connection, user, body)
        match = re.fullmatch(r"/receipts/(\d+)/approve", resource)
        if match:
            return self._approve_receipt(connection, user, int(match.group(1)))
        if resource == "/bookings":
            return self._create_booking(connection, user, body)
        match = re.fullmatch(r"/bookings/(\d+)/check-in", resource)
        if match:
            return self._check_in(connection, user, int(match.group(1)))
        raise ApiError("资源不存在", 404, 40400)

    def _create_customer(self, connection, user: dict, body: dict):
        self._require_permission(user, "CUSTOMER.CREATE")
        name = str(body.get("name", "")).strip()
        phone = str(body.get("phone", "")).strip()
        if not name:
            raise ApiError("客户姓名不能为空")
        if len(name) > 30:
            raise ApiError("客户姓名不能超过30个字符")
        if not re.fullmatch(r"1[3-9]\d{9}", phone):
            raise ApiError("手机号格式不正确")
        store_id = self._allowed_store(user, body.get("storeId"))
        duplicate = execute_one(
            connection,
            """
            SELECT customer_id, customer_no, name
            FROM customers
            WHERE tenant_id=%s AND phone=%s AND deleted_at IS NULL
            LIMIT 1
            """,
            (user["tenant_id"], phone),
        )
        if duplicate:
            raise ApiError(
                f"手机号已存在于客户 {duplicate['customer_no'] or duplicate['customer_id']}"
            )
        sales_staff_id = body.get("salesStaffId") or None
        if sales_staff_id:
            staff = execute_one(
                connection,
                """
                SELECT staff_id FROM staff
                WHERE staff_id=%s AND tenant_id=%s AND store_id=%s
                """,
                (sales_staff_id, user["tenant_id"], store_id),
            )
            if not staff:
                raise ApiError("业务员不存在或不属于所选门店")
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO customers(
                  tenant_id, store_id, sales_staff_id, name, gender, phone,
                  wechat, source, status, edc, birthday, remark, version,
                  created_at, updated_at, created_by, created_by_user_id
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,0,NOW(),NOW(),%s,%s)
                """,
                (
                    user["tenant_id"],
                    store_id,
                    sales_staff_id,
                    name,
                    body.get("gender") or "女",
                    phone,
                    body.get("wechat") or None,
                    body.get("source") or None,
                    body.get("status") or "意向A",
                    body.get("edc") or None,
                    body.get("birthday") or None,
                    body.get("remark") or None,
                    user["username"],
                    user["user_id"],
                ),
            )
            customer_id = cursor.lastrowid
            customer_no = f"KH-{datetime.now():%Y}-{customer_id:05d}"
            cursor.execute(
                "UPDATE customers SET customer_no=%s WHERE customer_id=%s",
                (customer_no, customer_id),
            )
        self._audit(
            connection,
            user,
            "CUSTOMER",
            customer_id,
            "CREATE",
            store_id,
            None,
            body.get("status") or "意向A",
        )
        connection.commit()
        self._success({"id": customer_id, "customerNo": customer_no})

    def _create_contract(self, connection, user: dict, body: dict):
        self._require_permission(user, "SALES.CREATE")
        store_id = self._allowed_store(user, body.get("storeId"))
        customer_id = int(body.get("customerId") or 0)
        customer = execute_one(
            connection,
            """
            SELECT customer_id, store_id FROM customers
            WHERE customer_id=%s AND tenant_id=%s AND deleted_at IS NULL
            """,
            (customer_id, user["tenant_id"]),
        )
        if not customer:
            raise ApiError("客户不存在")
        if customer["store_id"] != store_id:
            raise ApiError("合同门店必须与客户门店一致")
        contract_type = str(body.get("contractType", ""))
        if contract_type not in CONTRACT_TYPES:
            raise ApiError("合同类型不正确")
        try:
            reference = Decimal(str(body.get("referenceAmount", "0")))
            amount = Decimal(str(body.get("amount", "0")))
            days = int(body.get("days", 0))
        except (ValueError, ArithmeticError) as exc:
            raise ApiError("合同金额或入住天数不正确") from exc
        if reference <= 0 or amount <= 0 or days <= 0:
            raise ApiError("参考价格、成交金额和入住天数必须大于 0")
        if amount > reference:
            raise ApiError("成交金额不能大于参考价格")
        package = self._resolve_contract_package(
            connection,
            user,
            body,
            store_id,
            days,
            reference,
        )
        package_name = (
            package["package_name"]
            if package
            else body.get("packageName") or None
        )
        discount_rate = (amount / reference).quantize(Decimal("0.0001"))
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO contracts(
                  tenant_id, store_id, customer_id, contract_type,
                  package_name, package_version_id, package_price_rule_id,
                  reference_amount, amount, paid, discount_rate, days,
                  expected_check_in, expected_check_out, sign_date, status,
                  note, created_by_user_id, version, created_at
                ) VALUES (
                  %s,%s,%s,%s,%s,%s,%s,%s,%s,0,%s,%s,%s,%s,%s,
                  '已签合同但未审核',%s,%s,0,NOW()
                )
                """,
                (
                    user["tenant_id"],
                    store_id,
                    customer_id,
                    contract_type,
                    package_name,
                    package["package_version_id"] if package else None,
                    package["price_rule_id"] if package else None,
                    reference,
                    amount,
                    discount_rate,
                    days,
                    body.get("expectedCheckIn") or None,
                    body.get("expectedCheckOut") or None,
                    body.get("signDate") or date.today().isoformat(),
                    body.get("note") or None,
                    user["user_id"],
                ),
            )
            contract_id = cursor.lastrowid
            contract_no = f"HT-{datetime.now():%Y%m%d}-{contract_id:05d}"
            cursor.execute(
                "UPDATE contracts SET contract_no=%s WHERE contract_id=%s",
                (contract_no, contract_id),
            )
            if package:
                self._freeze_contract_package(
                    connection,
                    user,
                    contract_id,
                    store_id,
                    amount,
                    package,
                )
            cursor.execute(
                """
                UPDATE customers SET status='已签合同但未审核', updated_at=NOW()
                WHERE customer_id=%s
                """,
                (customer_id,),
            )
        self._audit(
            connection,
            user,
            "CONTRACT",
            contract_id,
            "CREATE",
            store_id,
            None,
            "已签合同但未审核",
            {"discountRate": str(discount_rate)},
        )
        connection.commit()
        self._success(
            {
                "id": contract_id,
                "contractNo": contract_no,
                "discountRate": float(discount_rate),
            }
        )

    def _approve_contract(self, connection, user: dict, contract_id: int):
        self._require_permission(user, "SALES.APPROVE")
        contract = execute_one(
            connection,
            """
            SELECT contract_id, customer_id, store_id, status
            FROM contracts WHERE contract_id=%s AND tenant_id=%s
            FOR UPDATE
            """,
            (contract_id, user["tenant_id"]),
        )
        if not contract:
            raise ApiError("合同不存在")
        self._allowed_store(user, contract["store_id"])
        if contract["status"] != "已签合同但未审核":
            raise ApiError("只有待审核合同可以审核")
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE contracts SET status='已审核', approved_at=NOW(),
                  approved_by_user_id=%s, version=version+1
                WHERE contract_id=%s
                """,
                (user["user_id"], contract_id),
            )
            cursor.execute(
                """
                UPDATE customers SET status='已签合同但未入住', updated_at=NOW()
                WHERE customer_id=%s
                """,
                (contract["customer_id"],),
            )
            self._grant_contract_entitlements(
                connection, user, contract_id
            )
        self._audit(
            connection,
            user,
            "CONTRACT",
            contract_id,
            "APPROVE",
            contract["store_id"],
            contract["status"],
            "已审核",
        )
        connection.commit()
        self._success({"id": contract_id, "status": "已审核"})

    def _create_receipt(self, connection, user: dict, body: dict):
        self._require_permission(user, "FINANCE.CREATE")
        store_id = self._allowed_store(user, body.get("storeId"))
        contract_id = int(body.get("contractId") or 0)
        contract = execute_one(
            connection,
            """
            SELECT contract_id, customer_id, store_id, amount, paid
            FROM contracts
            WHERE contract_id=%s AND tenant_id=%s AND deleted_at IS NULL
            """,
            (contract_id, user["tenant_id"]),
        )
        if not contract:
            raise ApiError("合同不存在")
        if contract["store_id"] != store_id:
            raise ApiError("收款门店必须与合同门店一致")
        receipt_type = str(body.get("receiptType", ""))
        payment_method = str(body.get("paymentMethod", ""))
        if receipt_type not in RECEIPT_TYPES:
            raise ApiError("收款类型不正确")
        if payment_method not in PAYMENT_METHODS:
            raise ApiError("支付方式不正确")
        try:
            amount = Decimal(str(body.get("amount", "0")))
        except ArithmeticError as exc:
            raise ApiError("收款金额不正确") from exc
        if amount <= 0:
            raise ApiError("收款金额必须大于 0")
        pending = execute_one(
            connection,
            """
            SELECT COALESCE(SUM(amount),0) AS total
            FROM finance_receipts
            WHERE contract_id=%s AND tenant_id=%s AND store_id=%s
              AND status='待审核'
            """,
            (contract_id, user["tenant_id"], store_id),
        )["total"]
        if contract["paid"] + pending + amount > contract["amount"]:
            raise ApiError("审核金额、未审核金额与本次收款合计不能超过成交金额")
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO finance_receipts(
                  tenant_id, store_id, receipt_no, customer_id, contract_id,
                  receipt_type, amount, payment_method, received_at,
                  receiver_user_id, status, remark
                ) VALUES (%s,%s,'PENDING',%s,%s,%s,%s,%s,%s,%s,'待审核',%s)
                """,
                (
                    user["tenant_id"],
                    store_id,
                    contract["customer_id"],
                    contract_id,
                    receipt_type,
                    amount,
                    payment_method,
                    body.get("receivedAt")
                    or datetime.now().isoformat(sep=" ", timespec="seconds"),
                    user["user_id"],
                    body.get("remark") or None,
                ),
            )
            receipt_id = cursor.lastrowid
            receipt_no = f"SK-{datetime.now():%Y%m%d}-{receipt_id:05d}"
            cursor.execute(
                "UPDATE finance_receipts SET receipt_no=%s WHERE receipt_id=%s",
                (receipt_no, receipt_id),
            )
        self._audit(
            connection,
            user,
            "RECEIPT",
            receipt_id,
            "CREATE",
            store_id,
            None,
            "待审核",
            {"amount": str(amount)},
        )
        connection.commit()
        self._success({"id": receipt_id, "receiptNo": receipt_no})

    def _approve_receipt(self, connection, user: dict, receipt_id: int):
        self._require_permission(user, "FINANCE.APPROVE")
        receipt = execute_one(
            connection,
            """
            SELECT receipt_id, contract_id, store_id, amount, status
            FROM finance_receipts
            WHERE receipt_id=%s AND tenant_id=%s FOR UPDATE
            """,
            (receipt_id, user["tenant_id"]),
        )
        if not receipt:
            raise ApiError("收款单不存在")
        self._allowed_store(user, receipt["store_id"])
        if receipt["status"] != "待审核":
            raise ApiError("只有待审核收款单可以审核")
        contract = execute_one(
            connection,
            """
            SELECT contract_id, amount, paid FROM contracts
            WHERE contract_id=%s AND tenant_id=%s AND store_id=%s
            FOR UPDATE
            """,
            (
                receipt["contract_id"],
                user["tenant_id"],
                receipt["store_id"],
            ),
        )
        if not contract:
            raise ApiError("收款单关联的合同不存在")
        if contract["paid"] + receipt["amount"] > contract["amount"]:
            raise ApiError("审核后已收款将超过合同成交金额")
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE finance_receipts
                SET status='已审核', approved_at=NOW(), approved_by_user_id=%s,
                    version=version+1
                WHERE receipt_id=%s
                """,
                (user["user_id"], receipt_id),
            )
            cursor.execute(
                """
                UPDATE contracts SET paid=paid+%s, version=version+1
                WHERE contract_id=%s
                """,
                (receipt["amount"], receipt["contract_id"]),
            )
        self._audit(
            connection,
            user,
            "RECEIPT",
            receipt_id,
            "APPROVE",
            receipt["store_id"],
            "待审核",
            "已审核",
            {"amount": str(receipt["amount"])},
        )
        connection.commit()
        self._success({"id": receipt_id, "status": "已审核"})

    def _create_booking(self, connection, user: dict, body: dict):
        self._require_permission(user, "ROOM.CREATE")
        store_id = self._allowed_store(user, body.get("storeId"))
        contract_id = int(body.get("contractId") or 0)
        room_id = int(body.get("roomId") or 0)
        check_in = str(body.get("checkIn", ""))
        check_out = str(body.get("checkOut", ""))
        if not check_in or not check_out or check_in >= check_out:
            raise ApiError("入住日期必须早于离店日期")
        contract = execute_one(
            connection,
            """
            SELECT contract_id, customer_id, store_id, status
            FROM contracts
            WHERE contract_id=%s AND tenant_id=%s AND deleted_at IS NULL
            """,
            (contract_id, user["tenant_id"]),
        )
        if not contract or contract["status"] != "已审核":
            raise ApiError("只有已审核合同可以订房")
        if contract["store_id"] != store_id:
            raise ApiError("订房门店必须与合同门店一致")
        room = execute_one(
            connection,
            """
            SELECT room_id, store_id, status FROM rooms
            WHERE room_id=%s AND tenant_id=%s AND deleted_at IS NULL
            """,
            (room_id, user["tenant_id"]),
        )
        if not room or room["store_id"] != store_id:
            raise ApiError("房间不存在或不属于当前门店")
        conflict = execute_one(
            connection,
            """
            SELECT booking_id FROM room_bookings
            WHERE room_id=%s AND tenant_id=%s AND store_id=%s
              AND deleted_at IS NULL
              AND status IN ('已订房','已入住')
              AND NOT (check_out<=%s OR check_in>=%s)
            LIMIT 1
            """,
            (room_id, user["tenant_id"], store_id, check_in, check_out),
        )
        if conflict:
            raise ApiError("该日期范围内房间已被占用")
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO room_bookings(
                  tenant_id, store_id, room_id, customer_id, contract_id,
                  check_in, check_out, status, version, created_at,
                  created_by_user_id, source
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,'已订房',0,NOW(),%s,'ERP')
                """,
                (
                    user["tenant_id"],
                    store_id,
                    room_id,
                    contract["customer_id"],
                    contract_id,
                    check_in,
                    check_out,
                    user["user_id"],
                ),
            )
            booking_id = cursor.lastrowid
            booking_no = f"DF-{datetime.now():%Y%m%d}-{booking_id:05d}"
            cursor.execute(
                """
                UPDATE room_bookings SET booking_no=%s WHERE booking_id=%s
                """,
                (booking_no, booking_id),
            )
            cursor.execute(
                "UPDATE rooms SET status='已预订' WHERE room_id=%s", (room_id,)
            )
            cursor.execute(
                """
                UPDATE customers SET status='已订房', updated_at=NOW()
                WHERE customer_id=%s
                """,
                (contract["customer_id"],),
            )
        self._audit(
            connection,
            user,
            "BOOKING",
            booking_id,
            "CREATE",
            store_id,
            None,
            "已订房",
            {"roomId": room_id, "checkIn": check_in, "checkOut": check_out},
        )
        connection.commit()
        self._success({"id": booking_id, "bookingNo": booking_no})

    def _check_in(self, connection, user: dict, booking_id: int):
        self._require_permission(user, "ROOM.EXECUTE")
        booking = execute_one(
            connection,
            """
            SELECT booking_id, room_id, customer_id, store_id, status
            FROM room_bookings
            WHERE booking_id=%s AND tenant_id=%s FOR UPDATE
            """,
            (booking_id, user["tenant_id"]),
        )
        if not booking:
            raise ApiError("订房记录不存在")
        self._allowed_store(user, booking["store_id"])
        if booking["status"] != "已订房":
            raise ApiError("只有已订房记录可以办理入住")
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE room_bookings
                SET status='已入住', actual_check_in_at=NOW(), version=version+1
                WHERE booking_id=%s
                """,
                (booking_id,),
            )
            cursor.execute(
                """
                UPDATE rooms SET status='入住', customer_id=%s WHERE room_id=%s
                """,
                (booking["customer_id"], booking["room_id"]),
            )
            cursor.execute(
                """
                UPDATE customers SET status='已入住', updated_at=NOW()
                WHERE customer_id=%s
                """,
                (booking["customer_id"],),
            )
        self._audit(
            connection,
            user,
            "BOOKING",
            booking_id,
            "CHECK_IN",
            booking["store_id"],
            "已订房",
            "已入住",
        )
        connection.commit()
        self._success({"id": booking_id, "status": "已入住"})


def serve(host: str, port: int):
    try:
        runtime = validate_runtime_config()
    except RuntimeConfigError as exc:
        raise SystemExit(str(exc)) from exc
    require_current_schema = parse_bool(
        env("ERP_REQUIRE_CURRENT_SCHEMA"),
        runtime["environment"] == "production",
    )
    if require_current_schema:
        connection = connect()
        try:
            migrations = _migration_status(connection)
        finally:
            connection.close()
        if not migrations["current"]:
            raise SystemExit(
                "Database schema is not current: "
                + compact_json(migrations)
            )
    server = ThreadingHTTPServer((host, port), MvpRequestHandler)
    print(f"QDF ERP MVP API listening on http://{host}:{port}", flush=True)
    print("Data source: MySQL (no JSON/mock fallback)", flush=True)
    print(f"Runtime environment: {runtime['environment']}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=("serve", "migrate", "bootstrap", "bootstrap-roles", "verify"),
    )
    parser.add_argument("--host", default=env("ERP_API_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(env("ERP_API_PORT", "3000")))
    parser.add_argument("--no-seed-rooms", action="store_true")
    parser.add_argument(
        "--include-baseline",
        action="store_true",
        help="apply V001-V003 after a DBA imports the legacy schema baseline",
    )
    args = parser.parse_args()

    if args.command == "serve":
        if args.include_baseline:
            parser.error("--include-baseline is only valid with migrate")
        serve(args.host, args.port)
    elif args.command == "migrate":
        print(
            json.dumps(
                apply_migrations(include_baseline=args.include_baseline),
                ensure_ascii=False,
                indent=2,
            )
        )
    elif args.command == "bootstrap":
        if args.include_baseline:
            parser.error("--include-baseline is only valid with migrate")
        print(
            json.dumps(
                bootstrap(seed_rooms=not args.no_seed_rooms),
                ensure_ascii=False,
                indent=2,
            )
        )
    elif args.command == "bootstrap-roles":
        if args.include_baseline:
            parser.error("--include-baseline is only valid with migrate")
        print(
            json.dumps(
                bootstrap_role_accounts(),
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        if args.include_baseline:
            parser.error("--include-baseline is only valid with migrate")
        print(json.dumps(verify_database(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

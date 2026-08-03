#!/usr/bin/env python3
"""Local-only P0 main-flow and RBAC acceptance runner.

The runner never connects to a non-loopback database or API. It provisions
temporary TEST_P0_* accounts and two sentinel customers, exercises the real API,
and removes every fixture and business record it creates.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import secrets
import socket
import sys
import time
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEPS_DIR = ROOT / ".deps"
if DEPS_DIR.exists():
    sys.path.insert(0, str(DEPS_DIR))

TENANT_ID = 1
SOURCE_SYSTEM = "LOCAL_P0_TEST"
USERNAME_PREFIX = "TEST_P0_"
CUSTOMER_PREFIX = "TEST_P0_RBAC_"
CONFIRM_ENV = "ERP_P0_LOCAL_TEST_CONFIRM"
CONFIRM_VALUE = "LOCAL_TEST_ONLY"
PASSWORD_ENV = "ERP_P0_TEST_PASSWORD"
BASE_URL = os.environ.get("ERP_MVP_BASE_URL", "http://127.0.0.1:3000").rstrip("/")

P0_PERMISSIONS = frozenset(
    {
        "CUSTOMER.VIEW",
        "CUSTOMER.CREATE",
        "SALES.VIEW",
        "SALES.CREATE",
        "SALES.APPROVE",
        "FINANCE.VIEW",
        "FINANCE.CREATE",
        "FINANCE.APPROVE",
        "ROOM.VIEW",
        "ROOM.CREATE",
        "ROOM.EXECUTE",
    }
)


@dataclass(frozen=True)
class Persona:
    key: str
    username: str
    role_code: str
    store_key: str
    allow: frozenset[str]
    deny: frozenset[str]


READ_CUSTOMER_ROOM = frozenset({"CUSTOMER.VIEW", "ROOM.VIEW"})
PERSONAS = (
    Persona(
        "admin",
        "TEST_P0_SYS_ADMIN",
        "SYS_ADMIN",
        "both",
        P0_PERMISSIONS,
        frozenset(),
    ),
    Persona(
        "center_manager",
        "TEST_P0_CENTER_MANAGER",
        "STORE_MANAGER",
        "center",
        frozenset(
            {
                "CUSTOMER.VIEW",
                "CUSTOMER.CREATE",
                "SALES.VIEW",
                "SALES.APPROVE",
                "FINANCE.VIEW",
                "ROOM.VIEW",
                "ROOM.CREATE",
                "ROOM.EXECUTE",
            }
        ),
        frozenset({"FINANCE.CREATE", "FINANCE.APPROVE"}),
    ),
    Persona(
        "huanghe_manager",
        "TEST_P0_HUANGHE_MANAGER",
        "STORE_MANAGER",
        "huanghe",
        frozenset(
            {
                "CUSTOMER.VIEW",
                "CUSTOMER.CREATE",
                "SALES.VIEW",
                "SALES.APPROVE",
                "FINANCE.VIEW",
                "ROOM.VIEW",
                "ROOM.CREATE",
                "ROOM.EXECUTE",
            }
        ),
        frozenset({"FINANCE.CREATE", "FINANCE.APPROVE"}),
    ),
    Persona(
        "center_sales",
        "TEST_P0_CENTER_SALES",
        "SALES_CONSULTANT",
        "center",
        frozenset(
            {
                "CUSTOMER.VIEW",
                "CUSTOMER.CREATE",
                "SALES.VIEW",
                "SALES.CREATE",
            }
        ),
        frozenset(
            {
                "SALES.APPROVE",
                "FINANCE.CREATE",
                "FINANCE.APPROVE",
                "ROOM.CREATE",
                "ROOM.EXECUTE",
            }
        ),
    ),
    Persona(
        "huanghe_sales",
        "TEST_P0_HUANGHE_SALES",
        "SALES_CONSULTANT",
        "huanghe",
        frozenset(
            {
                "CUSTOMER.VIEW",
                "CUSTOMER.CREATE",
                "SALES.VIEW",
                "SALES.CREATE",
            }
        ),
        frozenset(
            {
                "SALES.APPROVE",
                "FINANCE.CREATE",
                "FINANCE.APPROVE",
                "ROOM.CREATE",
                "ROOM.EXECUTE",
            }
        ),
    ),
    Persona(
        "center_finance",
        "TEST_P0_CENTER_FINANCE",
        "FINANCE_SPECIALIST",
        "center",
        frozenset(
            {
                "CUSTOMER.VIEW",
                "FINANCE.VIEW",
                "FINANCE.CREATE",
                "FINANCE.APPROVE",
            }
        ),
        frozenset(
            {
                "CUSTOMER.CREATE",
                "SALES.CREATE",
                "SALES.APPROVE",
                "ROOM.CREATE",
                "ROOM.EXECUTE",
            }
        ),
    ),
    Persona(
        "huanghe_finance",
        "TEST_P0_HUANGHE_FINANCE",
        "FINANCE_SPECIALIST",
        "huanghe",
        frozenset(
            {
                "CUSTOMER.VIEW",
                "FINANCE.VIEW",
                "FINANCE.CREATE",
                "FINANCE.APPROVE",
            }
        ),
        frozenset(
            {
                "CUSTOMER.CREATE",
                "SALES.CREATE",
                "SALES.APPROVE",
                "ROOM.CREATE",
                "ROOM.EXECUTE",
            }
        ),
    ),
    Persona(
        "center_nursing",
        "TEST_P0_CENTER_NURSING",
        "NURSE",
        "center",
        READ_CUSTOMER_ROOM | frozenset({"NURSING.VIEW"}),
        frozenset(
            {
                "CUSTOMER.CREATE",
                "SALES.CREATE",
                "SALES.APPROVE",
                "FINANCE.CREATE",
                "FINANCE.APPROVE",
                "ROOM.CREATE",
                "ROOM.EXECUTE",
            }
        ),
    ),
    Persona(
        "huanghe_nursing",
        "TEST_P0_HUANGHE_NURSING",
        "NURSE",
        "huanghe",
        READ_CUSTOMER_ROOM | frozenset({"NURSING.VIEW"}),
        frozenset(
            {
                "CUSTOMER.CREATE",
                "SALES.CREATE",
                "SALES.APPROVE",
                "FINANCE.CREATE",
                "FINANCE.APPROVE",
                "ROOM.CREATE",
                "ROOM.EXECUTE",
            }
        ),
    ),
)


class AcceptanceError(RuntimeError):
    """An actionable acceptance failure."""


def is_loopback_host(host: str) -> bool:
    normalized = str(host or "").strip().lower()
    return normalized in {"127.0.0.1", "::1", "localhost"}


def assert_local_targets(db_host: str, base_url: str) -> None:
    if not is_loopback_host(db_host):
        raise AcceptanceError(
            f"Refusing non-loopback ERP_DB_HOST: {db_host!r}"
        )
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not is_loopback_host(
        parsed.hostname or ""
    ):
        raise AcceptanceError(
            f"Refusing non-loopback ERP_MVP_BASE_URL: {base_url!r}"
        )
    runtime = os.environ.get("ERP_RUNTIME_ENV", "development").strip().lower()
    if runtime in {"production", "prod", "staging", "stage"}:
        raise AcceptanceError(
            f"Refusing ERP_RUNTIME_ENV={runtime!r}; use a local test runtime."
        )


def require_mutation_confirmation() -> None:
    if os.environ.get(CONFIRM_ENV) != CONFIRM_VALUE:
        raise AcceptanceError(
            f"{CONFIRM_ENV} must equal {CONFIRM_VALUE!r} before fixtures "
            "or business records can be changed."
        )


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


def load_pymysql():
    try:
        import pymysql
        from pymysql.cursors import DictCursor
    except ImportError as exc:
        raise AcceptanceError(
            "PyMySQL is unavailable. Install server/requirements.txt into "
            "an isolated project environment before real DB acceptance."
        ) from exc
    return pymysql, DictCursor


def connect():
    pymysql, dict_cursor = load_pymysql()
    host = os.environ.get("ERP_DB_HOST", "127.0.0.1")
    assert_local_targets(host, BASE_URL)
    password = os.environ.get("ERP_DB_PASSWORD", "")
    if not password:
        raise AcceptanceError("ERP_DB_PASSWORD is required.")
    ssl_config = None
    ca_path = os.environ.get("ERP_DB_SSL_CA", "").strip()
    if ca_path:
        ssl_config = {
            "ca": ca_path,
            "check_hostname": os.environ.get(
                "ERP_DB_SSL_CHECK_HOSTNAME", "true"
            ).lower()
            not in {"0", "false", "no", "off"},
        }
    return pymysql.connect(
        host=host,
        port=int(os.environ.get("ERP_DB_PORT", "3306")),
        user=os.environ.get("ERP_DB_USER", "yuezi_app"),
        password=password,
        database=os.environ.get("ERP_DB_NAME", "yuezi"),
        charset="utf8mb4",
        cursorclass=dict_cursor,
        autocommit=False,
        connect_timeout=int(os.environ.get("ERP_DB_CONNECT_TIMEOUT", "5")),
        read_timeout=int(os.environ.get("ERP_DB_READ_TIMEOUT", "15")),
        write_timeout=int(os.environ.get("ERP_DB_WRITE_TIMEOUT", "15")),
        ssl=ssl_config,
    )


def socket_open(host: str, port: int, timeout: float = 0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def api(path: str, token: str = "", body=None, method: str | None = None):
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        headers["X-Token"] = token
    request = Request(
        BASE_URL + path,
        data=(
            json.dumps(body, ensure_ascii=False).encode("utf-8")
            if body is not None
            else None
        ),
        headers=headers,
        method=method or ("POST" if body is not None else "GET"),
    )
    try:
        with urlopen(request, timeout=15) as response:
            status = response.status
            raw = response.read().decode("utf-8")
    except HTTPError as exc:
        status = exc.code
        raw = exc.read().decode("utf-8")
    except URLError as exc:
        raise AcceptanceError(f"API is unreachable at {BASE_URL}: {exc}") from exc
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AcceptanceError(
            f"API returned non-JSON for {path}: HTTP {status}"
        ) from exc
    return status, payload


def require_ok(path: str, token: str = "", body=None):
    status, payload = api(path, token, body)
    if status != 200 or payload.get("code") != 20000:
        raise AcceptanceError(
            f"{path} failed: HTTP {status} {payload.get('message')}"
        )
    return payload.get("data") or {}


def assert_api_error(
    path: str,
    token: str,
    body,
    *,
    expected_status: int,
    expected_code: int,
    message_contains: str,
):
    status, payload = api(path, token, body)
    message = str(payload.get("message") or "")
    if (
        status != expected_status
        or payload.get("code") != expected_code
        or message_contains not in message
    ):
        raise AcceptanceError(
            f"{path} expected HTTP {expected_status}/code {expected_code}/"
            f"message containing {message_contains!r}, got HTTP {status}/"
            f"code {payload.get('code')}/{message!r}"
        )
    return payload


def login(username: str, password: str) -> str:
    return require_ok(
        "/vue-element-admin/user/login",
        body={"username": username, "password": password},
    )["token"]


def select_stores(cursor) -> dict[str, dict]:
    cursor.execute(
        """
        SELECT store_id, name, status
        FROM stores
        WHERE tenant_id=%s
        ORDER BY sort_weight DESC, store_id
        """,
        (TENANT_ID,),
    )
    stores = cursor.fetchall()
    active = [
        row
        for row in stores
        if str(row.get("status") or "").strip().upper()
        in {"ACTIVE", "NORMAL", "正常", "启用"}
    ]
    center = [
        row
        for row in active
        if "中心" in str(row["name"]) or "建设路" in str(row["name"])
    ]
    huanghe = [row for row in active if "黄河路" in str(row["name"])]
    if len(center) != 1 or len(huanghe) != 1:
        raise AcceptanceError(
            "Expected exactly one active center/建设路 store and one active "
            f"黄河路 store; found center={len(center)}, huanghe={len(huanghe)}."
        )
    if int(center[0]["store_id"]) == int(huanghe[0]["store_id"]):
        raise AcceptanceError("Center and Huanghe stores resolved to the same id.")
    return {"center": center[0], "huanghe": huanghe[0]}


def select_published_package(cursor, store_id: int) -> dict | None:
    cursor.execute(
        """
        SELECT pp.package_id,pp.package_name,pv.package_version_id,
               pr.price_rule_id,pr.room_type_id,rt.name AS room_type,
               pr.stay_days,pr.reference_amount
        FROM package_price_rules pr
        JOIN package_versions pv
          ON pv.package_version_id=pr.package_version_id
         AND pv.tenant_id=pr.tenant_id
        JOIN package_products pp
          ON pp.package_id=pv.package_id AND pp.tenant_id=pv.tenant_id
        JOIN room_types rt
          ON rt.room_type_id=pr.room_type_id AND rt.tenant_id=pr.tenant_id
        WHERE pr.tenant_id=%s AND pr.store_id=%s
          AND pr.status='ACTIVE' AND pv.version_status='ACTIVE'
          AND pp.status='ACTIVE' AND pp.deleted_at IS NULL
          AND pv.effective_from<=CURRENT_DATE
          AND (pv.effective_to IS NULL OR pv.effective_to>=CURRENT_DATE)
          AND pr.effective_from<=CURRENT_DATE
          AND (pr.effective_to IS NULL OR pr.effective_to>=CURRENT_DATE)
        ORDER BY pp.sort_order,pp.package_id,pv.package_version_id,
                 pr.price_rule_id
        LIMIT 1
        """,
        (TENANT_ID, store_id),
    )
    return cursor.fetchone()


def role_map(cursor) -> dict[str, dict]:
    codes = sorted({item.role_code for item in PERSONAS})
    placeholders = ",".join(["%s"] * len(codes))
    cursor.execute(
        f"""
        SELECT role_id, code, name, status
        FROM roles
        WHERE tenant_id=%s AND code IN ({placeholders})
        """,
        (TENANT_ID, *codes),
    )
    rows = {str(row["code"]): row for row in cursor.fetchall()}
    missing = [
        code
        for code in codes
        if code not in rows or str(rows[code]["status"]).upper() != "ACTIVE"
    ]
    if missing:
        raise AcceptanceError(
            "Required active roles are missing: " + ", ".join(missing)
        )
    return rows


def persona_store_ids(persona: Persona, stores: dict[str, dict]) -> tuple[int, ...]:
    if persona.store_key == "both":
        return tuple(sorted(int(item["store_id"]) for item in stores.values()))
    return (int(stores[persona.store_key]["store_id"]),)


def apply_fixtures() -> dict:
    require_mutation_confirmation()
    password = os.environ.get(PASSWORD_ENV, "")
    if len(password) < 12:
        raise AcceptanceError(f"{PASSWORD_ENV} must contain at least 12 characters.")
    connection = connect()
    result = {"accounts": [], "sentinels": {}}
    try:
        with connection.cursor() as cursor:
            stores = select_stores(cursor)
            roles = role_map(cursor)
            for persona in PERSONAS:
                cursor.execute(
                    """
                    SELECT user_id, source_system
                    FROM user_accounts
                    WHERE tenant_id=%s AND username=%s
                    """,
                    (TENANT_ID, persona.username),
                )
                existing = cursor.fetchone()
                if existing and existing.get("source_system") != SOURCE_SYSTEM:
                    raise AcceptanceError(
                        f"Refusing to overwrite non-test account {persona.username}."
                    )
                store_ids = persona_store_ids(persona, stores)
                encoded = hash_password(password)
                if existing:
                    user_id = int(existing["user_id"])
                    cursor.execute(
                        """
                        UPDATE user_accounts
                        SET staff_id=NULL, password_hash=%s,
                            default_store_id=%s, status='ACTIVE',
                            failed_login_count=0, locked_until=NULL,
                            source_system=%s, must_change_password=0,
                            password_changed_at=NOW()
                        WHERE user_id=%s
                        """,
                        (encoded, store_ids[0], SOURCE_SYSTEM, user_id),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO user_accounts(
                          tenant_id, staff_id, username, password_hash,
                          default_store_id, status, failed_login_count,
                          source_system, must_change_password,
                          password_changed_at, created_at
                        ) VALUES (
                          %s,NULL,%s,%s,%s,'ACTIVE',0,%s,0,NOW(),NOW()
                        )
                        """,
                        (
                            TENANT_ID,
                            persona.username,
                            encoded,
                            store_ids[0],
                            SOURCE_SYSTEM,
                        ),
                    )
                    user_id = int(cursor.lastrowid)
                cursor.execute("DELETE FROM user_roles WHERE user_id=%s", (user_id,))
                cursor.execute(
                    """
                    INSERT INTO user_roles(user_id, role_id, effective_from)
                    VALUES (%s,%s,NOW())
                    """,
                    (user_id, roles[persona.role_code]["role_id"]),
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
                result["accounts"].append(
                    {
                        "username": persona.username,
                        "role": persona.role_code,
                        "storeIds": list(store_ids),
                    }
                )

            cursor.execute(
                """
                DELETE FROM customers
                WHERE tenant_id=%s AND source=%s AND name LIKE %s
                """,
                (TENANT_ID, SOURCE_SYSTEM, CUSTOMER_PREFIX + "%"),
            )
            stamp = str(int(time.time()))[-7:]
            for index, store_key in enumerate(("center", "huanghe"), start=1):
                store_id = int(stores[store_key]["store_id"])
                name = f"{CUSTOMER_PREFIX}{store_key.upper()}_{stamp}"
                phone = f"188{stamp}{index}"[-11:]
                cursor.execute(
                    """
                    INSERT INTO customers(
                      tenant_id,store_id,name,gender,phone,source,status,
                      version,created_at,updated_at,created_by
                    ) VALUES (%s,%s,%s,'女',%s,%s,'意向A',0,NOW(),NOW(),%s)
                    """,
                    (
                        TENANT_ID,
                        store_id,
                        name,
                        phone,
                        SOURCE_SYSTEM,
                        SOURCE_SYSTEM,
                    ),
                )
                result["sentinels"][store_key] = {
                    "id": int(cursor.lastrowid),
                    "name": name,
                    "storeId": store_id,
                }
        connection.commit()
        return result
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def fixture_snapshot() -> dict:
    connection = connect()
    try:
        with connection.cursor() as cursor:
            stores = select_stores(cursor)
            cursor.execute(
                """
                SELECT user_id,username,default_store_id
                FROM user_accounts
                WHERE tenant_id=%s AND source_system=%s
                  AND username LIKE %s
                ORDER BY username
                """,
                (TENANT_ID, SOURCE_SYSTEM, USERNAME_PREFIX + "%"),
            )
            accounts = cursor.fetchall()
            cursor.execute(
                """
                SELECT customer_id AS id,name,store_id AS storeId
                FROM customers
                WHERE tenant_id=%s AND source=%s AND name LIKE %s
                ORDER BY customer_id
                """,
                (TENANT_ID, SOURCE_SYSTEM, CUSTOMER_PREFIX + "%"),
            )
            sentinels = cursor.fetchall()
    finally:
        connection.close()
    by_store = {int(row["storeId"]): row for row in sentinels}
    expected_store_ids = {
        key: int(row["store_id"]) for key, row in stores.items()
    }
    if len(accounts) != len(PERSONAS):
        raise AcceptanceError(
            f"Expected {len(PERSONAS)} TEST accounts, found {len(accounts)}."
        )
    if set(by_store) != set(expected_store_ids.values()):
        raise AcceptanceError(
            "Expected one TEST sentinel customer in each target store."
        )
    return {
        "stores": stores,
        "accounts": accounts,
        "sentinels": {
            key: by_store[store_id]
            for key, store_id in expected_store_ids.items()
        },
    }


DENIED_CALLS = {
    "CUSTOMER.CREATE": (
        "/vue-element-admin/erp/mvp/customers",
        {"name": "TEST_P0_DENIED", "phone": "18800000000", "storeId": 0},
    ),
    "SALES.CREATE": ("/vue-element-admin/erp/mvp/contracts", {}),
    "SALES.APPROVE": (
        "/vue-element-admin/erp/mvp/contracts/0/approve",
        {},
    ),
    "FINANCE.CREATE": ("/vue-element-admin/erp/mvp/receipts", {}),
    "FINANCE.APPROVE": (
        "/vue-element-admin/erp/mvp/receipts/0/approve",
        {},
    ),
    "ROOM.CREATE": ("/vue-element-admin/erp/mvp/bookings", {}),
    "ROOM.EXECUTE": (
        "/vue-element-admin/erp/mvp/bookings/0/check-in",
        {},
    ),
}


def assert_denied(token: str, permission: str) -> None:
    path, body = DENIED_CALLS[permission]
    status, payload = api(path, token=token, body=body)
    if status != 403:
        raise AcceptanceError(
            f"{permission} denial expected HTTP 403, got {status}: "
            f"{payload.get('message')}"
        )


def test_rbac() -> dict:
    snapshot = fixture_snapshot()
    password = os.environ.get(PASSWORD_ENV, "")
    if not password:
        raise AcceptanceError(f"{PASSWORD_ENV} is required.")
    stores = snapshot["stores"]
    sentinels = snapshot["sentinels"]
    results = []
    for persona in PERSONAS:
        token = login(persona.username, password)
        info = require_ok("/vue-element-admin/user/info", token)
        if persona.role_code not in set(info.get("roles") or []):
            raise AcceptanceError(
                f"{persona.username} is missing role {persona.role_code}."
            )
        actual_stores = tuple(
            sorted(int(value) for value in info.get("storeIds") or [])
        )
        expected_stores = persona_store_ids(persona, stores)
        if actual_stores != expected_stores:
            raise AcceptanceError(
                f"{persona.username} storeIds={actual_stores}, "
                f"expected={expected_stores}."
            )
        permissions = set(info.get("permissions") or [])
        missing = sorted(persona.allow - permissions)
        unexpected = sorted(persona.deny & permissions)
        if missing or unexpected:
            raise AcceptanceError(
                f"{persona.username} permission matrix mismatch: "
                f"missing={missing}, forbiddenPresent={unexpected}"
            )
        customers = require_ok(
            "/vue-element-admin/erp/mvp/customers", token
        ).get("list", [])
        visible_ids = {int(row["id"]) for row in customers}
        own_keys = (
            ("center", "huanghe")
            if persona.store_key == "both"
            else (persona.store_key,)
        )
        other_keys = tuple(
            key for key in ("center", "huanghe") if key not in own_keys
        )
        if any(int(sentinels[key]["id"]) not in visible_ids for key in own_keys):
            raise AcceptanceError(
                f"{persona.username} cannot see its own-store sentinel."
            )
        if any(int(sentinels[key]["id"]) in visible_ids for key in other_keys):
            raise AcceptanceError(
                f"{persona.username} leaked a cross-store sentinel."
            )

        if persona.store_key != "both":
            other_key = "huanghe" if persona.store_key == "center" else "center"
            denied_phone = "187" + str(int(time.time()))[-8:]
            status, payload = api(
                "/vue-element-admin/erp/mvp/customers",
                token,
                {
                    "name": "TEST_P0_CROSS_STORE_DENIED",
                    "phone": denied_phone,
                    "storeId": int(stores[other_key]["store_id"]),
                },
            )
            if status != 403:
                raise AcceptanceError(
                    f"{persona.username} cross-store create expected 403, "
                    f"got {status}: {payload.get('message')}"
                )
        for permission in sorted(persona.deny & DENIED_CALLS.keys()):
            assert_denied(token, permission)
        results.append(
            {
                "username": persona.username,
                "role": persona.role_code,
                "storeIds": list(actual_stores),
                "permissionCount": len(permissions),
                "deniedChecks": len(persona.deny & DENIED_CALLS.keys()),
            }
        )
    return {"status": "passed", "personas": results}


def flow_personas(store_key: str) -> dict[str, Persona]:
    manager_key = f"{store_key}_manager"
    sales_key = f"{store_key}_sales"
    finance_key = f"{store_key}_finance"
    nursing_key = f"{store_key}_nursing"
    mapping = {item.key: item for item in PERSONAS}
    return {
        "manager": mapping[manager_key],
        "sales": mapping[sales_key],
        "finance": mapping[finance_key],
        "nursing": mapping[nursing_key],
    }


def choose_room(token: str, start: str, end: str) -> dict:
    rooms = require_ok("/vue-element-admin/erp/mvp/rooms", token).get("list", [])
    bookings = require_ok(
        "/vue-element-admin/erp/mvp/bookings", token
    ).get("list", [])
    occupied = {
        int(row["room_id"])
        for row in bookings
        if row.get("status") in {"已订房", "已入住"}
        and not (str(row.get("check_out")) <= start or str(row.get("check_in")) >= end)
    }
    for room in rooms:
        if (
            int(room["id"]) not in occupied
            and room.get("status") == "空闲"
            and not room.get("customer_name")
        ):
            return room
    raise AcceptanceError(
        "No empty, customer-free and conflict-free room is available for "
        "the test period."
    )


def cleanup_flow(connection, created: dict, original_room: dict | None) -> None:
    with connection.cursor() as cursor:
        aggregates = (
            ("BOOKING", created.get("booking")),
            ("RECEIPT", created.get("receipt")),
            ("CONTRACT", created.get("contract")),
            ("CUSTOMER", created.get("customer")),
        )
        for aggregate_type, aggregate_id in aggregates:
            if aggregate_id:
                cursor.execute(
                    """
                    DELETE FROM mvp_audit_events
                    WHERE aggregate_type=%s AND aggregate_id=%s
                    """,
                    (aggregate_type, aggregate_id),
                )
        if created.get("booking"):
            cursor.execute(
                "DELETE FROM room_bookings WHERE booking_id=%s",
                (created["booking"],),
            )
        if original_room:
            cursor.execute(
                """
                UPDATE rooms SET status=%s,customer_id=%s
                WHERE room_id=%s
                """,
                (
                    original_room["status"],
                    original_room["customer_id"],
                    original_room["id"],
                ),
            )
        if created.get("receipt"):
            cursor.execute(
                "DELETE FROM finance_receipts WHERE receipt_id=%s",
                (created["receipt"],),
            )
        if created.get("contract"):
            cursor.execute(
                """
                DELETE cel
                FROM customer_entitlement_ledger cel
                JOIN customer_service_entitlements cse
                  ON cse.customer_entitlement_id=cel.customer_entitlement_id
                WHERE cse.contract_id=%s
                """,
                (created["contract"],),
            )
            cursor.execute(
                "DELETE FROM customer_service_entitlements WHERE contract_id=%s",
                (created["contract"],),
            )
            cursor.execute(
                "DELETE FROM contract_entitlement_snapshots WHERE contract_id=%s",
                (created["contract"],),
            )
            cursor.execute(
                "DELETE FROM contract_package_snapshots WHERE contract_id=%s",
                (created["contract"],),
            )
            cursor.execute(
                "DELETE FROM contracts WHERE contract_id=%s",
                (created["contract"],),
            )
        if created.get("customer"):
            cursor.execute(
                "DELETE FROM customers WHERE customer_id=%s",
                (created["customer"],),
            )
    connection.commit()


def test_store_flow(store_key: str) -> dict:
    snapshot = fixture_snapshot()
    stores = snapshot["stores"]
    store = stores[store_key]
    other_key = "huanghe" if store_key == "center" else "center"
    actors = flow_personas(store_key)
    other_actors = flow_personas(other_key)
    password = os.environ[PASSWORD_ENV]
    tokens = {
        key: login(persona.username, password)
        for key, persona in actors.items()
    }
    other_tokens = {
        key: login(persona.username, password)
        for key, persona in other_actors.items()
    }
    suffix = str(int(time.time() * 1000))[-8:]
    phone = "186" + suffix
    start_date = date.today() + timedelta(days=120)
    created: dict[str, int] = {}
    original_room = None
    connection = connect()
    try:
        customer = require_ok(
            "/vue-element-admin/erp/mvp/customers",
            tokens["sales"],
            {
                "name": f"TEST_P0_FLOW_{store_key.upper()}_{suffix}",
                "phone": phone,
                "storeId": int(store["store_id"]),
                "source": SOURCE_SYSTEM,
                "remark": "P0 local automated acceptance; delete after test",
            },
        )
        created["customer"] = int(customer["id"])

        contract_body = {
            "storeId": int(store["store_id"]),
            "customerId": created["customer"],
            "contractType": "月子合同",
            "referenceAmount": "100000",
            "amount": "98000",
            "days": 28,
            "signDate": date.today().isoformat(),
            "note": SOURCE_SYSTEM,
        }
        assert_api_error(
            "/vue-element-admin/erp/mvp/contracts",
            tokens["sales"],
            {key: value for key, value in contract_body.items() if key != "storeId"},
            expected_status=400,
            expected_code=40000,
            message_contains="请选择门店",
        )
        if store_key == "huanghe":
            assert_api_error(
                "/vue-element-admin/erp/mvp/contracts",
                tokens["sales"],
                contract_body,
                expected_status=400,
                expected_code=40000,
                message_contains="黄河路店合同必须选择本店已发布套餐",
            )
            with connection.cursor() as cursor:
                package = select_published_package(cursor, int(store["store_id"]))
            connection.commit()
            if not package:
                raise AcceptanceError(
                    "huanghe: at least one active published package price rule "
                    "for the Huanghe store is required before end-to-end acceptance."
                )
            reference = Decimal(str(package["reference_amount"]))
            contract_body.update(
                {
                    "packageId": int(package["package_id"]),
                    "packageVersionId": int(package["package_version_id"]),
                    "packagePriceRuleId": int(package["price_rule_id"]),
                    "packageName": package["package_name"],
                    "roomTypeId": int(package["room_type_id"]),
                    "roomType": package["room_type"],
                    "referenceAmount": str(reference),
                    "amount": str((reference * Decimal("0.98")).quantize(Decimal("0.01"))),
                    "days": int(package["stay_days"]),
                }
            )
        stay_days = int(contract_body["days"])
        start = start_date.isoformat()
        end = (start_date + timedelta(days=stay_days)).isoformat()
        contract_body.update(
            {"expectedCheckIn": start, "expectedCheckOut": end}
        )
        contract = require_ok(
            "/vue-element-admin/erp/mvp/contracts",
            tokens["sales"],
            contract_body,
        )
        created["contract"] = int(contract["id"])
        assert_api_error(
            f"/vue-element-admin/erp/mvp/contracts/{created['contract']}/approve",
            other_tokens["manager"],
            {},
            expected_status=403,
            expected_code=40300,
            message_contains="无权访问该门店",
        )
        require_ok(
            f"/vue-element-admin/erp/mvp/contracts/{created['contract']}/approve",
            tokens["manager"],
            {},
        )
        room = choose_room(tokens["manager"], start, end)
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT status,customer_id FROM rooms WHERE room_id=%s",
                (room["id"],),
            )
            room_state = cursor.fetchone()
        original_room = {
            "id": int(room["id"]),
            "status": room_state["status"],
            "customer_id": room_state["customer_id"],
        }
        connection.commit()
        booking_body = {
            "storeId": int(store["store_id"]),
            "contractId": created["contract"],
            "roomId": int(room["id"]),
            "checkIn": start,
            "checkOut": end,
        }
        assert_api_error(
            "/vue-element-admin/erp/mvp/bookings",
            tokens["manager"],
            booking_body,
            expected_status=400,
            expected_code=40000,
            message_contains="合同至少有一笔已审核收款后才可订房",
        )
        contract_amount = Decimal(str(contract_body["amount"]))
        receipt_amount = min(
            Decimal("30000"),
            (contract_amount * Decimal("0.30")).quantize(Decimal("0.01")),
        )
        receipt = require_ok(
            "/vue-element-admin/erp/mvp/receipts",
            tokens["finance"],
            {
                "storeId": int(store["store_id"]),
                "contractId": created["contract"],
                "receiptType": "合同首付",
                "amount": str(receipt_amount),
                "paymentMethod": "转账",
                "remark": SOURCE_SYSTEM,
            },
        )
        created["receipt"] = int(receipt["id"])
        assert_api_error(
            f"/vue-element-admin/erp/mvp/receipts/{created['receipt']}/approve",
            other_tokens["finance"],
            {},
            expected_status=403,
            expected_code=40300,
            message_contains="无权访问该门店",
        )
        require_ok(
            f"/vue-element-admin/erp/mvp/receipts/{created['receipt']}/approve",
            tokens["finance"],
            {},
        )
        # End the REPEATABLE READ snapshot before the API creates and updates
        # the booking in separate connections. The final relationship query
        # must observe those committed API transactions.
        connection.commit()
        booking = require_ok(
            "/vue-element-admin/erp/mvp/bookings",
            tokens["manager"],
            booking_body,
        )
        created["booking"] = int(booking["id"])
        assert_api_error(
            f"/vue-element-admin/erp/mvp/bookings/{created['booking']}/check-in",
            other_tokens["manager"],
            {},
            expected_status=403,
            expected_code=40300,
            message_contains="无权访问该门店",
        )
        require_ok(
            f"/vue-element-admin/erp/mvp/bookings/{created['booking']}/check-in",
            tokens["manager"],
            {},
        )
        nursing_customers = require_ok(
            "/vue-element-admin/erp/mvp/customers", tokens["nursing"]
        ).get("list", [])
        if created["customer"] not in {
            int(row["id"]) for row in nursing_customers
        }:
            raise AcceptanceError(
                f"{store_key}: nursing cannot read the own-store flow customer."
            )
        assert_denied(tokens["nursing"], "FINANCE.APPROVE")
        assert_denied(tokens["nursing"], "ROOM.EXECUTE")

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT c.status AS customer_status,
                       ct.status AS contract_status,ct.paid,
                       fr.status AS receipt_status,
                       rb.status AS booking_status,r.status AS room_status
                FROM customers c
                JOIN contracts ct ON ct.customer_id=c.customer_id
                JOIN finance_receipts fr ON fr.contract_id=ct.contract_id
                JOIN room_bookings rb ON rb.contract_id=ct.contract_id
                JOIN rooms r ON r.room_id=rb.room_id
                WHERE c.customer_id=%s AND ct.contract_id=%s
                  AND fr.receipt_id=%s AND rb.booking_id=%s
                """,
                (
                    created["customer"],
                    created["contract"],
                    created["receipt"],
                    created["booking"],
                ),
            )
            state = cursor.fetchone()
        if not state:
            raise AcceptanceError(f"{store_key}: incomplete MySQL relationship.")
        expected = {
            "customer_status": "已入住",
            "contract_status": "已审核",
            "receipt_status": "已审核",
            "booking_status": "已入住",
            "room_status": "入住",
        }
        mismatches = {
            key: {"actual": state[key], "expected": value}
            for key, value in expected.items()
            if state[key] != value
        }
        if mismatches or Decimal(str(state["paid"])) != receipt_amount:
            raise AcceptanceError(
                f"{store_key}: final DB state mismatch: "
                f"{mismatches}, paid={state['paid']}"
            )
        return {
            "store": store["name"],
            "storeId": int(store["store_id"]),
            "customerId": created["customer"],
            "contractId": created["contract"],
            "receiptId": created["receipt"],
            "bookingId": created["booking"],
            "roomId": int(room["id"]),
            "finalStatus": "已入住",
            "crossStoreDenials": 3,
            "validatedErrors": 6 if store_key == "huanghe" else 5,
            "cleanup": "automatic",
        }
    finally:
        if connection is None and created:
            connection = connect()
        if connection is not None:
            try:
                cleanup_flow(connection, created, original_room)
            except Exception:
                connection.rollback()
                raise
            finally:
                connection.close()


def cleanup_fixtures() -> dict:
    require_mutation_confirmation()
    connection = connect()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT user_id,username
                FROM user_accounts
                WHERE tenant_id=%s AND source_system=%s
                  AND username LIKE %s
                """,
                (TENANT_ID, SOURCE_SYSTEM, USERNAME_PREFIX + "%"),
            )
            accounts = cursor.fetchall()
            account_ids = [int(row["user_id"]) for row in accounts]
            if account_ids:
                placeholders = ",".join(["%s"] * len(account_ids))
                cursor.execute(
                    """
                    SELECT user_id FROM user_accounts
                    WHERE tenant_id=%s AND username='admin'
                    ORDER BY user_id LIMIT 1
                    """,
                    (TENANT_ID,),
                )
                system_account = cursor.fetchone()
                if not system_account:
                    raise AcceptanceError("Cannot find the local admin account for fixture cleanup.")
                system_user_id = int(system_account["user_id"])
                # Keep any pre-existing local test business records intact while
                # releasing every foreign-key actor reference before deleting
                # the temporary TEST_P0 accounts. Query the schema so newly
                # added modules cannot reintroduce an orphan-cleanup failure.
                cursor.execute(
                    """
                    SELECT DISTINCT TABLE_NAME,COLUMN_NAME
                    FROM information_schema.KEY_COLUMN_USAGE
                    WHERE REFERENCED_TABLE_SCHEMA=DATABASE()
                      AND REFERENCED_TABLE_NAME='user_accounts'
                      AND TABLE_NAME NOT IN ('user_accounts','user_roles','user_stores')
                    """
                )
                user_references = cursor.fetchall()
                for reference in user_references:
                    table = reference["TABLE_NAME"].replace("`", "``")
                    column = reference["COLUMN_NAME"].replace("`", "``")
                    cursor.execute(
                        f"UPDATE `{table}` SET `{column}`=%s WHERE `{column}` IN ({placeholders})",
                        (system_user_id, *account_ids),
                    )
                cursor.execute(
                    f"""
                    SELECT COUNT(*) AS total
                    FROM mvp_audit_events
                    WHERE actor_user_id IN ({placeholders})
                    """,
                    account_ids,
                )
                refs = int(cursor.fetchone()["total"])
                if refs:
                    raise AcceptanceError("Temporary audit actor reassignment did not complete.")
            cursor.execute(
                """
                DELETE FROM customers
                WHERE tenant_id=%s AND source=%s AND name LIKE %s
                """,
                (TENANT_ID, SOURCE_SYSTEM, CUSTOMER_PREFIX + "%"),
            )
            deleted_customers = cursor.rowcount
            if account_ids:
                placeholders = ",".join(["%s"] * len(account_ids))
                cursor.execute(
                    f"DELETE FROM user_roles WHERE user_id IN ({placeholders})",
                    account_ids,
                )
                cursor.execute(
                    f"DELETE FROM user_stores WHERE user_id IN ({placeholders})",
                    account_ids,
                )
                cursor.execute(
                    f"""
                    DELETE FROM user_accounts
                    WHERE user_id IN ({placeholders})
                      AND source_system=%s
                      AND username LIKE %s
                    """,
                    (*account_ids, SOURCE_SYSTEM, USERNAME_PREFIX + "%"),
                )
                deleted_accounts = cursor.rowcount
            else:
                deleted_accounts = 0
        connection.commit()
        return {
            "status": "cleaned",
            "accountsDeleted": deleted_accounts,
            "sentinelCustomersDeleted": deleted_customers,
        }
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def cleanup_stale_flows() -> dict:
    """Remove only interrupted LOCAL_P0_TEST main-flow records."""
    require_mutation_confirmation()
    connection = connect()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT customer_id
                FROM customers
                WHERE tenant_id=%s AND source=%s AND name LIKE 'TEST_P0_FLOW_%%'
                """,
                (TENANT_ID, SOURCE_SYSTEM),
            )
            customer_ids = [int(row["customer_id"]) for row in cursor.fetchall()]
            if not customer_ids:
                return {
                    "status": "cleaned",
                    "customersDeleted": 0,
                    "contractsDeleted": 0,
                    "receiptsDeleted": 0,
                    "bookingsDeleted": 0,
                }
            customer_marks = ",".join(["%s"] * len(customer_ids))
            cursor.execute(
                f"""
                SELECT contract_id
                FROM contracts
                WHERE tenant_id=%s AND customer_id IN ({customer_marks})
                """,
                (TENANT_ID, *customer_ids),
            )
            contract_ids = [int(row["contract_id"]) for row in cursor.fetchall()]
            booking_ids = []
            room_ids = []
            receipt_ids = []
            if contract_ids:
                contract_marks = ",".join(["%s"] * len(contract_ids))
                cursor.execute(
                    f"""
                    SELECT booking_id,room_id
                    FROM room_bookings
                    WHERE tenant_id=%s AND contract_id IN ({contract_marks})
                    """,
                    (TENANT_ID, *contract_ids),
                )
                bookings = cursor.fetchall()
                booking_ids = [int(row["booking_id"]) for row in bookings]
                room_ids = [int(row["room_id"]) for row in bookings]
                cursor.execute(
                    f"""
                    SELECT receipt_id
                    FROM finance_receipts
                    WHERE tenant_id=%s AND contract_id IN ({contract_marks})
                    """,
                    (TENANT_ID, *contract_ids),
                )
                receipt_ids = [
                    int(row["receipt_id"]) for row in cursor.fetchall()
                ]

            aggregate_sets = (
                ("BOOKING", booking_ids),
                ("RECEIPT", receipt_ids),
                ("CONTRACT", contract_ids),
                ("CUSTOMER", customer_ids),
            )
            for aggregate_type, aggregate_ids in aggregate_sets:
                if not aggregate_ids:
                    continue
                marks = ",".join(["%s"] * len(aggregate_ids))
                cursor.execute(
                    f"""
                    DELETE FROM mvp_audit_events
                    WHERE aggregate_type=%s AND aggregate_id IN ({marks})
                    """,
                    (aggregate_type, *aggregate_ids),
                )
            if booking_ids:
                marks = ",".join(["%s"] * len(booking_ids))
                cursor.execute(
                    f"DELETE FROM room_bookings WHERE booking_id IN ({marks})",
                    booking_ids,
                )
            if room_ids:
                marks = ",".join(["%s"] * len(room_ids))
                cursor.execute(
                    f"""
                    UPDATE rooms
                    SET status='空闲',customer_id=NULL
                    WHERE room_id IN ({marks})
                      AND (customer_id IS NULL OR customer_id IN ({customer_marks}))
                      AND status IN ('已预订','入住')
                    """,
                    (*room_ids, *customer_ids),
                )
            if receipt_ids:
                marks = ",".join(["%s"] * len(receipt_ids))
                cursor.execute(
                    f"""
                    DELETE FROM finance_receipts
                    WHERE receipt_id IN ({marks})
                    """,
                    receipt_ids,
                )
            if contract_ids:
                marks = ",".join(["%s"] * len(contract_ids))
                cursor.execute(
                    f"""
                    DELETE cel
                    FROM customer_entitlement_ledger cel
                    JOIN customer_service_entitlements cse
                      ON cse.customer_entitlement_id=cel.customer_entitlement_id
                    WHERE cse.contract_id IN ({marks})
                    """,
                    contract_ids,
                )
                cursor.execute(
                    f"""
                    DELETE FROM customer_service_entitlements
                    WHERE contract_id IN ({marks})
                    """,
                    contract_ids,
                )
                cursor.execute(
                    f"""
                    DELETE FROM contract_entitlement_snapshots
                    WHERE contract_id IN ({marks})
                    """,
                    contract_ids,
                )
                cursor.execute(
                    f"""
                    DELETE FROM contract_package_snapshots
                    WHERE contract_id IN ({marks})
                    """,
                    contract_ids,
                )
                cursor.execute(
                    f"DELETE FROM contracts WHERE contract_id IN ({marks})",
                    contract_ids,
                )
            cursor.execute(
                f"DELETE FROM customers WHERE customer_id IN ({customer_marks})",
                customer_ids,
            )
        connection.commit()
        return {
            "status": "cleaned",
            "customersDeleted": len(customer_ids),
            "contractsDeleted": len(contract_ids),
            "receiptsDeleted": len(receipt_ids),
            "bookingsDeleted": len(booking_ids),
        }
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def cleanup_all() -> dict:
    flow = cleanup_stale_flows()
    fixtures = cleanup_fixtures()
    return {"status": "cleaned", "flow": flow, "fixtures": fixtures}


def preflight() -> dict:
    host = os.environ.get("ERP_DB_HOST", "127.0.0.1")
    port = int(os.environ.get("ERP_DB_PORT", "3306"))
    reasons = []
    try:
        assert_local_targets(host, BASE_URL)
    except AcceptanceError as exc:
        reasons.append(str(exc))
    if not os.environ.get("ERP_DB_PASSWORD"):
        reasons.append("ERP_DB_PASSWORD is not configured.")
    if not os.environ.get(PASSWORD_ENV):
        reasons.append(f"{PASSWORD_ENV} is not configured.")
    if not socket_open(host, port):
        reasons.append(f"MySQL is not listening on {host}:{port}.")
    try:
        load_pymysql()
    except AcceptanceError as exc:
        reasons.append(str(exc))
    api_status = None
    try:
        api_status, payload = api("/api/ready")
        if api_status != 200:
            reasons.append(
                "API readiness failed: "
                + str(payload.get("data", {}).get("status") or api_status)
            )
    except AcceptanceError as exc:
        reasons.append(str(exc))
    stores = {}
    roles = []
    migrations = {}
    if not reasons:
        connection = connect()
        try:
            with connection.cursor() as cursor:
                stores = select_stores(cursor)
                roles = sorted(role_map(cursor))
                cursor.execute(
                    """
                    SELECT version,checksum,applied_at
                    FROM schema_migrations ORDER BY version
                    """
                )
                migration_rows = cursor.fetchall()
                migrations = {
                    "count": len(migration_rows),
                    "latest": (
                        migration_rows[-1]["version"] if migration_rows else None
                    ),
                }
        except Exception as exc:
            reasons.append(f"Database readiness failed: {exc}")
        finally:
            connection.close()
    return {
        "status": "ready" if not reasons else "blocked",
        "localOnly": True,
        "database": {
            "host": host,
            "port": port,
            "name": os.environ.get("ERP_DB_NAME", "yuezi"),
        },
        "api": {"baseUrl": BASE_URL, "status": api_status},
        "migrations": migrations,
        "stores": {
            key: {"id": int(row["store_id"]), "name": row["name"]}
            for key, row in stores.items()
        },
        "roles": roles,
        "blockers": reasons,
    }


def run_all() -> dict:
    require_mutation_confirmation()
    readiness = preflight()
    if readiness["status"] != "ready":
        raise AcceptanceError(
            "Preflight is blocked: " + "; ".join(readiness["blockers"])
        )
    fixtures = apply_fixtures()
    try:
        rbac = test_rbac()
        flows = [test_store_flow("center"), test_store_flow("huanghe")]
        return {
            "status": "passed",
            "preflight": readiness,
            "fixtures": fixtures,
            "rbac": rbac,
            "flows": flows,
        }
    finally:
        cleanup_all()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=(
            "preflight",
            "apply-fixtures",
            "test-rbac",
            "test-flow",
            "cleanup-fixtures",
            "cleanup",
            "all",
        ),
    )
    parser.add_argument(
        "--store",
        choices=("center", "huanghe", "both"),
        default="both",
        help="Store selection for test-flow.",
    )
    args = parser.parse_args()
    try:
        if args.command == "preflight":
            result = preflight()
            print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
            return 0 if result["status"] == "ready" else 2
        if args.command == "apply-fixtures":
            result = apply_fixtures()
        elif args.command == "test-rbac":
            result = test_rbac()
        elif args.command == "test-flow":
            stores = (
                ("center", "huanghe") if args.store == "both" else (args.store,)
            )
            result = {
                "status": "passed",
                "flows": [test_store_flow(item) for item in stores],
            }
        elif args.command == "cleanup-fixtures":
            result = cleanup_fixtures()
        elif args.command == "cleanup":
            result = cleanup_all()
        else:
            result = run_all()
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        return 0
    except (AcceptanceError, KeyError, ValueError) as exc:
        print(
            json.dumps(
                {"status": "failed", "error": str(exc)},
                ensure_ascii=False,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

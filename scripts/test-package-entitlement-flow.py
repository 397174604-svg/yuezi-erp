#!/usr/bin/env python3
"""Exercise normalized package pricing, contract snapshots and entitlements."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import date
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from server.mvp_api import connect


BASE_URL = os.environ.get(
    "ERP_MVP_BASE_URL", "http://127.0.0.1:3001"
).rstrip("/")


def request(path: str, method: str = "GET", body=None, token: str = ""):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Token"] = token
    req = Request(
        BASE_URL + path,
        data=(
            json.dumps(body, ensure_ascii=False).encode("utf-8")
            if body is not None
            else None
        ),
        headers=headers,
        method=method,
    )
    try:
        with urlopen(req, timeout=15) as response:
            return response.status, json.loads(
                response.read().decode("utf-8")
            )
    except HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def require_ok(path: str, token: str, body=None, method: str = "POST"):
    status, payload = request(path, method, body, token)
    if status != 200 or payload.get("code") != 20000:
        raise AssertionError(
            f"{method} {path} failed: {status} "
            f"{payload.get('message', payload)}"
        )
    return payload["data"]


def login() -> str:
    password = os.environ.get("ERP_BOOTSTRAP_ADMIN_PASSWORD", "")
    if not password:
        raise RuntimeError("ERP_BOOTSTRAP_ADMIN_PASSWORD is required")
    return require_ok(
        "/vue-element-admin/user/login",
        "",
        {"username": "admin", "password": password},
    )["token"]


def main():
    token = login()
    unique = str(int(time.time() * 1000))
    created = {}
    connection = connect()
    try:
        catalog = require_ok(
            "/vue-element-admin/erp/catalog/packages?status=ALL",
            token,
            method="GET",
        )
        stores = catalog.get("stores") or []
        room_types = catalog.get("roomTypes") or []
        if not stores or not room_types:
            raise AssertionError("套餐目录缺少门店或房型基础数据")
        store = next(
            (item for item in stores if "黄河路" in item["name"]),
            stores[0],
        )
        room_type = next(
            (
                item
                for item in room_types
                if "修复" in item.get("packageName", "")
            ),
            room_types[0],
        )
        project = require_ok(
            "/vue-element-admin/erp/catalog/service-projects/save",
            token,
            {
                "projectCode": f"TEST.RECOVERY.{unique}",
                "projectName": f"套餐权益验收项目-{unique}",
                "targetModule": "RECOVERY",
                "projectCategory": "自动验收",
                "unit": "次",
                "status": "ACTIVE",
            },
        )
        created["project"] = project["id"]
        package = require_ok(
            "/vue-element-admin/erp/catalog/packages/save",
            token,
            {
                "packageCode": f"TEST.PACKAGE.{unique}",
                "packageName": f"套餐价格权益验收-{unique}",
                "packageCategory": "月子套餐",
                "versionNo": "V1",
                "effectiveFrom": date.today().isoformat(),
                "sourceType": "AUTOMATED_TEST",
                "evidenceNote": "自动化验收完成后删除",
                "priceRules": [
                    {
                        "storeId": store["id"],
                        "roomTypeId": room_type["id"],
                        "stayDays": 28,
                        "referenceAmount": "1000.00",
                        "currencyCode": "CNY",
                        "effectiveFrom": date.today().isoformat(),
                    }
                ],
                "entitlementRules": [
                    {
                        "serviceProjectId": project["id"],
                        "entitlementMode": "COUNT",
                        "grantedQuantity": "3",
                        "validDays": 60,
                    }
                ],
            },
        )
        created["package"] = package["packageId"]
        created["version"] = package["packageVersionId"]
        published = require_ok(
            (
                "/vue-element-admin/erp/catalog/packages/"
                f"{package['packageVersionId']}/publish"
            ),
            token,
            {},
        )
        if published["status"] != "ACTIVE":
            raise AssertionError("套餐版本未发布")
        detail = require_ok(
            (
                "/vue-element-admin/erp/catalog/packages/"
                f"{package['packageVersionId']}"
            ),
            token,
            method="GET",
        )
        price_rule = detail["priceRules"][0]
        created["price"] = price_rule["priceRuleId"]

        phone = f"199{unique[-8:]}"
        customer = require_ok(
            "/vue-element-admin/erp/mvp/customers",
            token,
            {
                "storeId": store["id"],
                "name": f"套餐链路验收-{unique[-6:]}",
                "phone": phone,
                "status": "意向A",
                "source": "系统验收",
                "remark": "自动化验收完成后删除",
            },
        )
        created["customer"] = customer["id"]

        status, rejected = request(
            "/vue-element-admin/erp/mvp/contracts",
            "POST",
            {
                "storeId": store["id"],
                "customerId": customer["id"],
                "contractType": "月子合同",
                "packageId": package["packageId"],
                "packageVersionId": package["packageVersionId"],
                "packagePriceRuleId": price_rule["priceRuleId"],
                "roomTypeId": room_type["id"],
                "referenceAmount": "999.00",
                "amount": "900.00",
                "days": 28,
                "signDate": date.today().isoformat(),
            },
            token,
        )
        if status != 400 or "已发布套餐价格" not in rejected.get(
            "message", ""
        ):
            raise AssertionError("手工篡改参考价格没有被拒绝")

        contract = require_ok(
            "/vue-element-admin/erp/mvp/contracts",
            token,
            {
                "storeId": store["id"],
                "customerId": customer["id"],
                "contractType": "月子合同",
                "packageId": package["packageId"],
                "packageVersionId": package["packageVersionId"],
                "packagePriceRuleId": price_rule["priceRuleId"],
                "roomTypeId": room_type["id"],
                "referenceAmount": "1000.00",
                "amount": "900.00",
                "days": 28,
                "signDate": date.today().isoformat(),
            },
        )
        created["contract"] = contract["id"]
        require_ok(
            f"/vue-element-admin/erp/mvp/contracts/{contract['id']}/approve",
            token,
            {},
        )

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT ct.package_version_id,ct.package_price_rule_id,
                       cps.package_snapshot_id,
                       ces.entitlement_snapshot_id,ces.grant_status,
                       cse.customer_entitlement_id,cse.granted_quantity,
                       cse.used_quantity,cse.reserved_quantity,cse.status,
                       ledger.transaction_type,ledger.balance_after
                FROM contracts ct
                JOIN contract_package_snapshots cps
                  ON cps.contract_id=ct.contract_id
                JOIN contract_entitlement_snapshots ces
                  ON ces.contract_id=ct.contract_id
                JOIN customer_service_entitlements cse
                  ON cse.entitlement_snapshot_id=ces.entitlement_snapshot_id
                JOIN customer_entitlement_ledger ledger
                  ON ledger.customer_entitlement_id=
                     cse.customer_entitlement_id
                WHERE ct.contract_id=%s
                ORDER BY ledger.ledger_id
                """,
                (contract["id"],),
            )
            state = cursor.fetchone()
        if not state:
            raise AssertionError("合同审核后未形成套餐快照和权益流水")
        if (
            state["grant_status"] != "GRANTED"
            or state["status"] != "ACTIVE"
            or str(state["granted_quantity"]) != "3.0000"
            or state["transaction_type"] != "GRANT"
        ):
            raise AssertionError(f"套餐权益状态不正确: {state}")
        print(
            json.dumps(
                {
                    "status": "passed",
                    "store": store["name"],
                    "roomType": room_type["name"],
                    "packageVersionId": package["packageVersionId"],
                    "priceRuleId": price_rule["priceRuleId"],
                    "contractId": contract["id"],
                    "packageSnapshotId": state["package_snapshot_id"],
                    "entitlementId": state["customer_entitlement_id"],
                    "grantedQuantity": str(state["granted_quantity"]),
                    "tamperedPriceRejected": True,
                    "cleanup": "automatic",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    finally:
        try:
            with connection.cursor() as cursor:
                if created.get("contract"):
                    cursor.execute(
                        """
                        DELETE ledger FROM customer_entitlement_ledger ledger
                        JOIN customer_service_entitlements entitlement
                          ON entitlement.customer_entitlement_id=
                             ledger.customer_entitlement_id
                        WHERE entitlement.contract_id=%s
                        """,
                        (created["contract"],),
                    )
                    cursor.execute(
                        """
                        DELETE FROM customer_service_entitlements
                        WHERE contract_id=%s
                        """,
                        (created["contract"],),
                    )
                    cursor.execute(
                        """
                        DELETE FROM contract_entitlement_snapshots
                        WHERE contract_id=%s
                        """,
                        (created["contract"],),
                    )
                    cursor.execute(
                        """
                        DELETE FROM contract_package_snapshots
                        WHERE contract_id=%s
                        """,
                        (created["contract"],),
                    )
                    cursor.execute(
                        """
                        DELETE FROM mvp_audit_events
                        WHERE aggregate_type='CONTRACT'
                          AND aggregate_id=%s
                        """,
                        (created["contract"],),
                    )
                    cursor.execute(
                        "DELETE FROM contracts WHERE contract_id=%s",
                        (created["contract"],),
                    )
                if created.get("customer"):
                    cursor.execute(
                        """
                        DELETE FROM mvp_audit_events
                        WHERE aggregate_type='CUSTOMER'
                          AND aggregate_id=%s
                        """,
                        (created["customer"],),
                    )
                    cursor.execute(
                        "DELETE FROM customers WHERE customer_id=%s",
                        (created["customer"],),
                    )
                if created.get("version"):
                    cursor.execute(
                        """
                        DELETE FROM mvp_audit_events
                        WHERE aggregate_type='PACKAGE_VERSION'
                          AND aggregate_id=%s
                        """,
                        (created["version"],),
                    )
                    cursor.execute(
                        """
                        DELETE FROM package_entitlement_rules
                        WHERE package_version_id=%s
                        """,
                        (created["version"],),
                    )
                    cursor.execute(
                        """
                        DELETE FROM package_price_rules
                        WHERE package_version_id=%s
                        """,
                        (created["version"],),
                    )
                    cursor.execute(
                        """
                        DELETE FROM package_versions
                        WHERE package_version_id=%s
                        """,
                        (created["version"],),
                    )
                if created.get("package"):
                    cursor.execute(
                        "DELETE FROM package_products WHERE package_id=%s",
                        (created["package"],),
                    )
                if created.get("project"):
                    cursor.execute(
                        """
                        DELETE FROM service_projects
                        WHERE service_project_id=%s
                        """,
                        (created["project"],),
                    )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()


if __name__ == "__main__":
    main()

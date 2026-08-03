#!/usr/bin/env python3
"""Read-only API regression for the imported legacy SALES_MANAGER account."""

from __future__ import annotations

import json
import os
from urllib.error import HTTPError
from urllib.request import Request, urlopen


BASE_URL = os.environ.get("ERP_MVP_BASE_URL", "http://127.0.0.1:3000")
USERNAME = os.environ.get("ERP_SALES_ACCOUNT_USERNAME", "韩新")
PASSWORD = os.environ.get("ERP_SALES_ACCOUNT_PASSWORD", "")
RESOURCES = (
    "contracts",
    "product-sales",
    "sales-details",
    "packages",
    "card-packages",
    "gift-lists",
    "discounts",
    "coupons",
    "gift-applications",
)
EXPECTED_PERMISSIONS = (
    "SALES.VIEW",
    "SALES.CREATE",
    "SALES.UPDATE",
    "SALES.CONTRACT.MEAL_PACKAGE.UPDATE",
    "RECOVERY.VIEW",
    "RECOVERY.CREATE",
)


def request(path: str, body=None, token: str = ""):
    headers = {"Content-Type": "application/json; charset=utf-8"}
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
        method="POST" if body is not None else "GET",
    )
    try:
        with urlopen(req, timeout=15) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def main():
    if not PASSWORD:
        raise SystemExit("ERP_SALES_ACCOUNT_PASSWORD is required.")
    status, payload = request(
        "/vue-element-admin/user/login",
        {"username": USERNAME, "password": PASSWORD},
    )
    if status != 200 or payload.get("code") != 20000:
        raise AssertionError(f"Login failed: {status} {payload}")
    token = payload["data"]["token"]
    status, info = request("/vue-element-admin/user/info", token=token)
    if status != 200:
        raise AssertionError(f"User info failed: {status} {info}")
    user = info["data"]
    if "SALES_MANAGER" not in user.get("roles", []):
        raise AssertionError(f"Unexpected roles: {user.get('roles')}")
    missing = [
        code
        for code in EXPECTED_PERMISSIONS
        if code not in user.get("permissions", [])
    ]
    if missing:
        raise AssertionError(f"Missing imported permissions: {missing}")
    if len(user.get("storeIds", [])) < 2:
        raise AssertionError(
            "韩新真实首页可选中心与黄河两店，本地范围未完成对齐: "
            f"{user.get('storeIds')}"
        )

    results = []
    store_names = set()
    for resource in RESOURCES:
        status, response = request(
            f"/vue-element-admin/erp/sales/modules/{resource}",
            token=token,
        )
        if status != 200 or response.get("code") != 20000:
            raise AssertionError(f"{resource}: {status} {response}")
        store_names.update(
            item["name"]
            for item in response["data"].get("stores", [])
            if item.get("name")
        )
        results.append(
            {
                "resource": resource,
                "status": status,
                "count": len(response["data"].get("list", [])),
            }
        )
    if not any("黄河路" in name for name in store_names):
        raise AssertionError(f"Missing Yellow River store: {store_names}")
    if not any(
        "中心广场" in name or "建设路" in name for name in store_names
    ):
        raise AssertionError(f"Missing centre store: {store_names}")

    status, channel_guard = request(
        "/vue-element-admin/erp/sales/modules/product-sales/action",
        {"action": "星支付", "id": "NO-READ-ONLY-CHECK"},
        token,
    )
    if status != 409:
        raise AssertionError(
            "Granted 星支付 must reach the real-channel guard, got "
            f"{status}: {channel_guard}"
        )

    status, denied = request(
        "/vue-element-admin/erp/sales/modules/product-sales/action",
        {"action": "添加", "id": "NO-READ-ONLY-CHECK"},
        token,
    )
    if status != 403:
        raise AssertionError(
            f"UnGranted 商品销售/添加 must be denied: {status} {denied}"
        )

    status, visible_contract_action = request(
        "/vue-element-admin/erp/sales/modules/contracts/action",
        {"action": "膳食套餐", "id": "0"},
        token,
    )
    if status != 404:
        raise AssertionError(
            "合同页实时可见的膳食套餐应通过浏览权限校验并进入记录校验，"
            f"当前返回: {status} {visible_contract_action}"
        )

    print(
        json.dumps(
            {
                "username": user["name"],
                "roles": user["roles"],
                "storeIds": user["storeIds"],
                "stores": sorted(store_names),
                "permissions": len(user.get("permissions", [])),
                "resources": results,
                "allowedButton": "商品销售/星支付（到达支付通道保护）",
                "visibleContractButton": "合同管理/膳食套餐（到达记录校验）",
                "deniedButton": "商品销售/添加",
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

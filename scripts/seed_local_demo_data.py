#!/usr/bin/env python3
"""Seed a small, repeatable, non-PII demo set through the real local API."""

from __future__ import annotations

import json
import os
from datetime import date, timedelta
from urllib.parse import urlparse
from urllib.error import HTTPError
from urllib.request import Request, urlopen


BASE_URL = os.environ.get("ERP_MVP_BASE_URL", "http://127.0.0.1:3000")
CONFIRM_ENV = "ERP_LOCAL_DEMO_CONFIRM"
CONFIRM_VALUE = "LOCAL_TEST_ONLY"


def api(path: str, method: str = "GET", body=None, token: str = ""):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Token"] = token
    request = Request(
        BASE_URL + path,
        data=json.dumps(body).encode("utf-8") if body is not None else None,
        headers=headers,
        method=method,
    )
    try:
        with urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        payload = json.loads(exc.read().decode("utf-8"))
        raise RuntimeError(
            payload.get("message") or f"API request failed: HTTP {exc.code}"
        ) from exc
    if payload.get("code") != 20000:
        raise RuntimeError(payload.get("message") or "API request failed")
    return payload["data"]


def main():
    target = urlparse(BASE_URL)
    if target.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise SystemExit("Demo seed is restricted to a loopback API.")
    if os.environ.get(CONFIRM_ENV) != CONFIRM_VALUE:
        raise SystemExit(
            f"Set {CONFIRM_ENV}={CONFIRM_VALUE} before writing demo data."
        )
    username = os.environ.get("ERP_DEMO_ADMIN_USERNAME", "admin").strip()
    password = os.environ.get("ERP_DEMO_ADMIN_PASSWORD", "")
    if not password:
        password = os.environ.get("ERP_BOOTSTRAP_ADMIN_PASSWORD", "")
    if not password:
        raise SystemExit(
            "ERP_DEMO_ADMIN_PASSWORD or ERP_BOOTSTRAP_ADMIN_PASSWORD is required."
        )

    token = api(
        "/vue-element-admin/user/login",
        "POST",
        {"username": username, "password": password},
    )["token"]
    options = api("/vue-element-admin/erp/mvp/options", token=token)
    stores = options.get("stores", [])
    if len(stores) < 2:
        raise RuntimeError("Two local stores are required before demo seeding.")

    existing_customers = api(
        "/vue-element-admin/erp/mvp/customers", token=token
    ).get("list", [])
    customers_by_phone = {
        str(row.get("phone") or row.get("mobile") or ""): row
        for row in existing_customers
    }
    created_customers = []
    created_contracts = []
    created_templates = []
    distributed = []
    today = date.today()

    for store in stores:
        store_id = int(store["id"])
        store_name = str(store.get("name") or "")
        is_huanghe = "黄河" in store_name
        store_index = 2 if is_huanghe else 1
        store_label = "黄河路店" if is_huanghe else "中心店"
        store_customers = []
        for customer_index in (1, 2):
            phone = f"1880000{store_index}{customer_index:03d}"
            customer_name = f"测试客户-{store_label}-{customer_index:02d}"
            customer = customers_by_phone.get(phone)
            if not customer:
                saved_customer = api(
                    "/vue-element-admin/erp/mvp/customers",
                    "POST",
                    {
                        "storeId": store_id,
                        "name": customer_name,
                        "phone": phone,
                        "status": "意向A",
                        "source": "本地数据库测试",
                        "remark": "LOCAL_DEMO_SEED，可在正式导入前清理",
                    },
                    token,
                )
                customer = {
                    **saved_customer,
                    "name": customer_name,
                    "phone": phone,
                    "storeId": store_id,
                }
                created_customers.append(customer["customerNo"])
            store_customers.append(customer)

        existing_contracts = api(
            "/vue-element-admin/erp/mvp/contracts", token=token
        ).get("list", [])
        customer_id = int(store_customers[0]["id"])
        contract = next(
            (
                row
                for row in existing_contracts
                if int(row.get("customer_id") or row.get("customerId") or 0)
                == customer_id
            ),
            None,
        )
        if not contract:
            check_in = today + timedelta(days=30 + store_index)
            check_out = check_in + timedelta(days=28)
            contract = api(
                "/vue-element-admin/erp/mvp/contracts",
                "POST",
                {
                    "storeId": store_id,
                    "customerId": customer_id,
                    "contractType": "月子合同",
                    "packageName": "基础套餐（本地测试）",
                    "referenceAmount": 24999,
                    "amount": 21999,
                    "days": 28,
                    "expectedCheckIn": check_in.isoformat(),
                    "expectedCheckOut": check_out.isoformat(),
                    "signDate": today.isoformat(),
                    "note": "LOCAL_DEMO_SEED",
                },
                token,
            )
            api(
                f"/vue-element-admin/erp/mvp/contracts/{contract['id']}/approve",
                "POST",
                {},
                token,
            )
            created_contracts.append(contract["contractNo"])

        template_name = f"{store_label}新客体验券（本地测试）"
        templates = api(
            "/vue-element-admin/erp/sales/modules/coupons", token=token
        ).get("list", [])
        template = next(
            (row for row in templates if row.get("couponName") == template_name),
            None,
        )
        if not template:
            template = api(
                "/vue-element-admin/erp/sales/modules/coupons/save",
                "POST",
                {
                    "storeId": store_id,
                    "couponName": template_name,
                    "couponAmount": 300 if store_index == 1 else 500,
                    "totalQuantity": 20,
                    "couponType": "现金券",
                    "limitType": "项目",
                    "startsAt": today.isoformat(),
                    "endsAt": (today + timedelta(days=180)).isoformat(),
                    "validDays": 180,
                    "limitPerCustomer": 2,
                    "scope": "所有人",
                    "sendType": "店内发放",
                    "remark": "LOCAL_DEMO_SEED",
                },
                token,
            )
            created_templates.append(template["id"])

        discounts = api(
            "/vue-element-admin/erp/sales/modules/discounts", token=token
        ).get("list", [])
        customer_name = store_customers[0].get("name")
        if not any(
            row.get("customerName") == customer_name
            and row.get("couponName") == template_name
            for row in discounts
        ):
            api(
                "/vue-element-admin/erp/sales/modules/coupons/action",
                "POST",
                {
                    "action": "分发",
                    "ids": [template["id"]],
                    "customerName": customer_name,
                    "mobile": store_customers[0].get("phone")
                    or store_customers[0].get("mobile"),
                    "quantity": 1,
                    "remark": "LOCAL_DEMO_SEED",
                },
                token,
            )
            distributed.append(template_name)

    print(
        json.dumps(
            {
                "status": "seeded",
                "createdCustomers": created_customers,
                "createdContracts": created_contracts,
                "createdTemplates": created_templates,
                "distributedCoupons": distributed,
                "dataSource": "real-local-mysql",
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

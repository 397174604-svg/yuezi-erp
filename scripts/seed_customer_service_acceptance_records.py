#!/usr/bin/env python3
"""Add three natural-name acceptance rows to customer and service pages.

This helper is loopback-only and idempotent.  It does not create customers,
contracts, receipts, bookings, rooms, packages, or permissions; it only fills
the durable page records used by the customer/customer-service workbenches.
"""

from __future__ import annotations

import json
import os
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from seed_local_acceptance_dataset import PEOPLE, RESOURCES, record_payload


BASE_URL = os.environ.get("ERP_MVP_BASE_URL", "http://127.0.0.1:3000")
CONFIRM_ENV = "ERP_LOCAL_DEMO_CONFIRM"
CONFIRM_VALUE = "LOCAL_TEST_ONLY"


def api(path: str, token: str = "", method: str = "GET", body=None) -> dict:
    request = Request(
        BASE_URL + path,
        data=(
            json.dumps(body, ensure_ascii=False).encode("utf-8")
            if body is not None
            else None
        ),
        headers={
            "Content-Type": "application/json",
            **({"X-Token": token} if token else {}),
        },
        method=method,
    )
    with urlopen(request, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if payload.get("code") != 20000:
        raise RuntimeError(payload.get("message") or f"{method} {path} failed")
    return payload.get("data") or {}


def require_local_confirmation() -> None:
    if urlparse(BASE_URL).hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise SystemExit("Acceptance records are restricted to a loopback API.")
    if os.environ.get(CONFIRM_ENV) != CONFIRM_VALUE:
        raise SystemExit(f"Set {CONFIRM_ENV}={CONFIRM_VALUE} before seeding.")


def existing_keys(token: str, path: str) -> set[str]:
    data = api(path, token=token)
    return {
        str(row.get("acceptanceKey") or "")
        for row in data.get("list", [])
        if row.get("acceptanceKey")
    }


def main() -> None:
    require_local_confirmation()
    password = os.environ.get("ERP_DEMO_ADMIN_PASSWORD", "admin123")
    token = api(
        "/vue-element-admin/user/login",
        method="POST",
        body={"username": "admin", "password": password},
    )["token"]

    options = api("/vue-element-admin/erp/mvp/options", token=token)
    stores = sorted(options.get("stores", []), key=lambda row: int(row["id"]))
    if not stores:
        raise RuntimeError("No authorized store is available.")
    created: dict[str, int] = {}
    for store_index, store in enumerate(stores, 1):
        store_id = int(store["id"])
        people = PEOPLE.get(store_index, PEOPLE[1])
        for module in ("CUSTOMER", "SERVICE"):
            for resource in RESOURCES[module]:
                if module == "CUSTOMER":
                    list_path = (
                        "/vue-element-admin/erp/customer/modules/"
                        f"{quote(resource)}?storeId={store_id}"
                    )
                    save_path = (
                        "/vue-element-admin/erp/customer/modules/"
                        f"{quote(resource)}/save"
                    )
                else:
                    list_path = (
                        f"/vue-element-admin/erp/service/{resource}?storeId={store_id}"
                    )
                    save_path = f"/vue-element-admin/erp/service/{resource}"

                known = existing_keys(token, list_path)
                added = 0
                for index, person in enumerate(people, 1):
                    key = f"QDF-ACCEPT-{module}-{resource}-{store_id}-{index}"
                    if key in known:
                        continue
                    payload = record_payload(
                        resource,
                        index,
                        person,
                        room_no=["201", "203", "205"][index - 1],
                        matron=["刘芳", "陈静", "王敏"][index - 1],
                    )
                    payload.update(
                        {
                            "storeId": store_id,
                            "store": store.get("name") or "",
                            "acceptanceKey": key,
                        }
                    )
                    api(save_path, token=token, method="POST", body=payload)
                    added += 1
                created[f"{store_id}:{module}/{resource}"] = added

    verification = {}
    for store in stores:
        store_id = int(store["id"])
        for module in ("CUSTOMER", "SERVICE"):
            for resource in RESOURCES[module]:
                if module == "CUSTOMER":
                    path = (
                        "/vue-element-admin/erp/customer/modules/"
                        f"{quote(resource)}?storeId={store_id}"
                    )
                else:
                    path = f"/vue-element-admin/erp/service/{resource}?storeId={store_id}"
                rows = api(path, token=token).get("list", [])
                verification[f"{store_id}:{module}/{resource}"] = len(rows)
                if len(rows) < 3:
                    raise RuntimeError(
                        f"store {store_id} {module}/{resource} has fewer than 3 records"
                    )

    print(
        json.dumps(
            {
                "status": "seeded",
                "storeIds": [int(store["id"]) for store in stores],
                "created": created,
                "verifiedTotals": verification,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

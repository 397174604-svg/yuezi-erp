#!/usr/bin/env python3
"""Regression checks for the normalized-to-sales package read projection."""

from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def check_static() -> None:
    api = (ROOT / "server" / "mvp_api.py").read_text(encoding="utf-8")
    vue = (ROOT / "src" / "views" / "erp" / "sales-workbench" / "index.vue").read_text(encoding="utf-8")
    adapter = (ROOT / "src" / "api" / "erp-sales.js").read_text(encoding="utf-8")
    config = (ROOT / "src" / "config" / "sales-pages.js").read_text(encoding="utf-8")
    restore = (ROOT / "scripts" / "restore_confirmed_room_inventory.py").read_text(encoding="utf-8")

    required_api = (
        "legacy.bundle_id IS NULL",
        "AS selectionKey",
        "AS catalogOnly",
        "mapped_ext.bundle_id IS NULL",
        "GROUP BY pp.package_id,pp.package_code,pp.package_name",
        'row["packageDisplayName"]',
        "return [*legacy_rows, *catalog_rows]",
    )
    missing = [text for text in required_api if text not in api]
    if missing:
        raise AssertionError(f"package projection missing: {missing}")
    if "NULL AS id" not in api:
        raise AssertionError("catalog projection must not expose normalized ids as legacy ids")
    if ":selectable=\"rowSelectable\"" not in vue or "if (row.catalogOnly)" not in vue:
        raise AssertionError("catalog-only rows are not protected from legacy writes")
    if "row.selectionKey || row.id" not in vue:
        raise AssertionError("package selector lacks an opaque selection key")
    if "packageDisplayName" not in adapter or "packageDisplayName" not in config:
        raise AssertionError("full package display name is not wired to the list")
    if '"priceValues": 84' not in restore or "center store has active package-price rules" in restore:
        raise AssertionError("room inventory validator still rejects the confirmed center package catalog")
    if re.search(r"performSalesModuleAction\([^\n]+catalog", vue):
        raise AssertionError("catalog id must not be forwarded to legacy actions")


def request_json(url: str, *, method: str = "GET", body: dict | None = None, token: str = "") -> dict:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Token"] = token
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def check_api(base: str, username: str, password: str) -> dict:
    login = request_json(
        f"{base.rstrip('/')}/vue-element-admin/user/login",
        method="POST",
        body={"username": username, "password": password},
    )
    token = login["data"]["token"]
    summary = {}
    for store_id in (1, 2):
        query = urllib.parse.urlencode({"storeId": store_id})
        payload = request_json(
            f"{base.rstrip('/')}/vue-element-admin/erp/sales/modules/packages?{query}",
            token=token,
        )["data"]
        rows = payload.get("list") or []
        if len(rows) != 28:
            raise AssertionError(f"storeId={store_id} package rows {len(rows)} != 28")
        unique_versions = {
            (row.get("basePackageName"), int(row.get("packageDays") or 0))
            for row in rows
        }
        if len(unique_versions) != 28:
            raise AssertionError(
                f"storeId={store_id} package versions are duplicated: "
                f"{len(unique_versions)} unique"
            )
        names = {row.get("basePackageName") for row in rows}
        if len(names) != 7:
            raise AssertionError(f"storeId={store_id} package families {len(names)} != 7")
        keys = [str(row.get("selectionKey") or "") for row in rows]
        if any(not key for key in keys) or len(keys) != len(set(keys)):
            raise AssertionError(
                f"storeId={store_id} selection keys are missing or duplicated"
            )
        catalog_rows = [row for row in rows if row.get("catalogOnly")]
        if any(row.get("id") not in (None, "") for row in catalog_rows):
            raise AssertionError("normalized catalog id leaked into legacy id field")
        if any(not row.get("packageDisplayName") for row in rows):
            raise AssertionError("package display name is incomplete")
        if store_id == 2 and len(catalog_rows) != 28:
            raise AssertionError("storeId=2 normalized catalog projection is incomplete")
        summary[str(store_id)] = {
            "rows": len(rows),
            "catalogRows": len(catalog_rows),
            "packageNames": len(names),
            "uniqueVersions": len(unique_versions),
        }
        if store_id == 1:
            displays = {row.get("packageDisplayName") for row in rows}
            expected = {
                "修养套餐B（护士团队）",
                "修养套餐A（7天一对一）",
                "精致尊享B（双师护航）",
                "精致尊享A（双师护航）",
                "臻享套餐VIP3楼（双师护航）",
                "至尊套餐VIP5楼（双师护航）",
            }
            if not expected.issubset(displays):
                raise AssertionError(
                    f"center package display names incomplete: {sorted(expected - displays)}"
                )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-base")
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password", default=os.environ.get("ERP_ACCEPTANCE_PASSWORD"))
    args = parser.parse_args()
    check_static()
    summary = None
    if args.api_base:
        if not args.password:
            raise SystemExit("--password is required with --api-base")
        summary = check_api(args.api_base, args.username, args.password)
    suffix = f" {json.dumps(summary, ensure_ascii=False)}" if summary else ""
    print(f"sales package projection regression: PASS{suffix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

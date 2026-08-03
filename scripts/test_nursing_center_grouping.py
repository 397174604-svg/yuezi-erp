#!/usr/bin/env python3
"""Regression check for nursing-center under MySQL ONLY_FULL_GROUP_BY."""

from __future__ import annotations

import argparse
import json
import os
import urllib.parse
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def request_json(url: str, *, method: str = "GET", body: dict | None = None, token: str = "") -> dict:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Token"] = token
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise AssertionError(f"HTTP {exc.code}: {detail}") from exc


def check_static() -> None:
    source = (ROOT / "server" / "erp_read_surfaces.py").read_text(encoding="utf-8")
    api = (ROOT / "server" / "mvp_api.py").read_text(encoding="utf-8")
    required = (
        "MAX(room.room_no) AS room",
        "MAX(room.floor) AS floor",
        "MAX(s.name) AS store",
        "GROUP BY c.customer_id,c.name,c.store_id,c.status",
        "ORDER BY floor, room, c.customer_id",
    )
    missing = [text for text in required if text not in source]
    if missing:
        raise AssertionError(f"nursing-center grouping regression: {missing}")
    if 'and resource != "nursing-center"' not in api:
        raise AssertionError("read-only nursing center is still sent to the operational merge registry")


def check_api(base: str, username: str, password: str) -> dict:
    login = request_json(
        f"{base.rstrip('/')}/vue-element-admin/user/login",
        method="POST",
        body={"username": username, "password": password},
    )
    token = login["data"]["token"]
    query = urllib.parse.urlencode({"storeId": 1})
    payload = request_json(
        f"{base.rstrip('/')}/vue-element-admin/erp/nursing/modules/nursing-center?{query}",
        token=token,
    )["data"]
    rows = payload.get("list") or []
    ids = [row.get("id") for row in rows]
    if len(ids) != len(set(ids)):
        raise AssertionError("nursing-center returned duplicate customer rows")
    return {"storeId": 1, "rows": len(rows), "uniqueCustomers": len(set(ids))}


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
    print(f"nursing-center grouping regression: PASS{suffix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

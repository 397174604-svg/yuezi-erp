#!/usr/bin/env python3
"""Live regression gate for member assets and the three customer surfaces."""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PORT = 3011
BASE = f"http://127.0.0.1:{PORT}"


def request(path: str, token: str = "", payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Token"] = token
    method = "POST" if payload is not None else "GET"
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def wait_for_port(process: subprocess.Popen, timeout: float = 12) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if process.poll() is not None:
            stdout, stderr = process.communicate(timeout=2)
            raise RuntimeError(f"API exited early: {stdout}\n{stderr}")
        try:
            with socket.create_connection(("127.0.0.1", PORT), timeout=0.3):
                return
        except OSError:
            time.sleep(0.2)
    raise RuntimeError("API did not open the regression-test port")


def assert_frontend_contracts() -> None:
    router = (ROOT / "src/router/index.js").read_text(encoding="utf-8")
    customer = (ROOT / "src/views/erp/customer-workbench/index.vue").read_text(encoding="utf-8")
    configs = (ROOT / "src/config/customer-pages.js").read_text(encoding="utf-8")
    assert "客户中台: 'customer-center'" in router
    assert "Math.max(0, 36 - index * 3)" not in customer
    assert "'业务跟踪台':" in configs and "'客户标签体系':" in configs
    assert "stageCounts[stage]" in customer


def main() -> int:
    missing = [name for name in ("ERP_DB_PASSWORD", "ERP_TOKEN_SECRET") if not os.environ.get(name)]
    if missing:
        print("SKIP: missing runtime secrets: " + ", ".join(missing))
        return 2
    assert_frontend_contracts()
    env = os.environ.copy()
    env.update({"ERP_API_HOST": "127.0.0.1", "ERP_API_PORT": str(PORT)})
    process = subprocess.Popen(
        [sys.executable, "server/mvp_api.py", "serve"],
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        wait_for_port(process)
        login = request(
            "/vue-element-admin/user/login",
            payload={"username": "admin", "password": os.environ.get("ERP_TEST_ADMIN_PASSWORD", "admin123")},
        )
        token = login["data"]["token"]
        checks = {
            "asset-options-all": "/vue-element-admin/erp/assets/options?storeId=all",
            "asset-overview-all": "/vue-element-admin/erp/assets/overview?storeId=all",
            "asset-cards-all": "/vue-element-admin/erp/assets/cards?storeId=all",
            "asset-accounts-all": "/vue-element-admin/erp/assets/accounts?storeId=all",
            "asset-cards-store": "/vue-element-admin/erp/assets/cards?storeId=1",
            "customers-all": "/vue-element-admin/erp/customer/modules/customers?storeId=all",
        }
        for label, path in checks.items():
            result = request(path, token=token)
            assert result.get("code") == 20000, f"{label}: {result}"
            print(f"PASS {label}")
        print("PASS frontend customer surface contracts")
        return 0
    except (AssertionError, RuntimeError, urllib.error.URLError) as exc:
        print(f"FAIL {exc}")
        return 1
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


if __name__ == "__main__":
    raise SystemExit(main())

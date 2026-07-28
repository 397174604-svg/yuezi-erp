"""Inspect a small, sanitized legacy query-control fragment.

This diagnostic accepts credentials only through ERP_USER / ERP_PASSWORD and
prints query markup with text values removed. It never writes cookies or HTML
to disk and must not be pointed at business-data grids.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
from pathlib import Path

import requests
from bs4 import BeautifulSoup, Tag


ROOT = Path(__file__).resolve().parents[1]
AUDIT_FILE = ROOT / "scripts" / "audit-nursing-query-areas.py"


def load_audit_module():
    spec = importlib.util.spec_from_file_location("legacy_audit", str(AUDIT_FILE))
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load shared ERP audit helpers")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sanitize(fragment: Tag) -> str:
    copy = BeautifulSoup(str(fragment), "html.parser")
    for node in copy.find_all(["script", "style"]):
        node.decompose()
    for node in copy.find_all(["input", "textarea"]):
        input_type = node.get("type", "text").lower()
        if input_type not in {"button", "submit", "radio", "checkbox"}:
            node["value"] = ""
            node.string = ""
    return copy.prettify()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Legacy path below the ERP host")
    parser.add_argument("selector", help="CSS selector for the target control")
    parser.add_argument(
        "--levels",
        type=int,
        default=1,
        help="Number of parent levels to include (default: 1).",
    )
    args = parser.parse_args()

    username = os.environ.get("ERP_USER", "")
    password = os.environ.get("ERP_PASSWORD", "")
    if not username or not password:
        raise RuntimeError("Set ERP_USER and ERP_PASSWORD for the temporary session")

    audit = load_audit_module()
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 Chrome/126 Safari/537.36"})
    audit.login(session, username, password)
    response = audit.fetch(session, args.path)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    nodes = soup.select(args.selector)
    if not nodes:
        raise RuntimeError("No matching control")
    for index, node in enumerate(nodes, 1):
        parent = node
        for _ in range(max(0, args.levels)):
            if not isinstance(parent.parent, Tag):
                break
            parent = parent.parent
        print(f"--- match {index} ---")
        print(sanitize(parent))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

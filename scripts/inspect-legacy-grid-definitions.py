"""Extract desensitized jqGrid schema from one authenticated legacy page.

Credentials are read only from ERP_USER / ERP_PASSWORD. The script prints
grid ids, captions, column labels, model names, and hidden flags; it never
prints grid rows, cookies, or full page source.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
AUDIT_FILE = ROOT / "scripts" / "audit-nursing-query-areas.py"


def load_audit_module():
    spec = importlib.util.spec_from_file_location("legacy_audit", str(AUDIT_FILE))
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load shared ERP audit helpers")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def balanced_array(source: str, start: int) -> str:
    opening = source.find("[", start)
    if opening < 0:
        return ""
    depth = 0
    quote = ""
    escaped = False
    for index in range(opening, len(source)):
        char = source[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = ""
            continue
        if char in {"'", '"'}:
            quote = char
        elif char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                return source[opening + 1:index]
    return ""


def quoted_items(source: str) -> list[str]:
    return [
        re.sub(r"<[^>]+>", "", match.group(1)).strip()
        for match in re.finditer(r"""["']([^"']*)["']""", source)
    ]


def top_level_objects(source: str) -> list[str]:
    result = []
    start = -1
    depth = 0
    quote = ""
    escaped = False
    for index, char in enumerate(source):
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = ""
            continue
        if char in {"'", '"'}:
            quote = char
        elif char == "{":
            if depth == 0:
                start = index
            depth += 1
        elif char == "}" and depth:
            depth -= 1
            if depth == 0 and start >= 0:
                result.append(source[start + 1:index])
                start = -1
    return result


def grid_definitions(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    source = "\n".join(script.get_text("\n") for script in soup.find_all("script"))
    starts = list(
        re.finditer(
            r"""(?:jQuery|\$)\(\s*["']#(?P<id>list\d+)["']\s*\)\.jqGrid\s*\(\s*\{""",
            source,
        )
    )
    result = []
    for index, match in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(source)
        segment = source[match.start():end]
        names_at = re.search(r"colNames\s*:", segment)
        model_at = re.search(r"colModel\s*:", segment)
        caption = re.search(r"""caption\s*:\s*["']([^"']*)["']""", segment)
        col_names = quoted_items(balanced_array(segment, names_at.end())) if names_at else []
        model_source = balanced_array(segment, model_at.end()) if model_at else ""
        models = []
        for body in top_level_objects(model_source):
            name = re.search(r"""name\s*:\s*["']([^"']+)["']""", body)
            if not name:
                continue
            hidden = re.search(r"hidden\s*:\s*(true|false)", body)
            models.append(
                {
                    "name": name.group(1),
                    "hidden": hidden.group(1) == "true" if hidden else False,
                }
            )
        result.append(
            {
                "gridId": match.group("id"),
                "caption": caption.group(1) if caption else "",
                "colNames": col_names,
                "colModel": models,
            }
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Observed legacy path below the ERP host")
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
    print(json.dumps(grid_definitions(response.text), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

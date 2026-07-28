"""Read-only legacy ERP toolbar/query/grid schema extractor.

Credentials are accepted only through ERP_USER and ERP_PASSWORD. The script
prints desensitized UI schema and never writes HTML, cookies, or business rows.
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup, Tag


ROOT = Path(__file__).resolve().parents[1]
NURSING_AUDIT = ROOT / "scripts" / "audit-nursing-query-areas.py"
EVIDENCE_FILE = ROOT / "src" / "config" / "original-page-evidence.js"
TARGET_MODULES = (
    "recovery",
    "matron",
    "diet",
    "warehouse",
    "mall",
    "risk",
    "basic",
)
NON_QUERY_INPUT_TYPES = {"button", "submit", "image", "reset", "hidden", "file"}


def load_audit_module():
    spec = importlib.util.spec_from_file_location("nursing_query_audit", str(NURSING_AUDIT))
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load the shared ERP audit helpers")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


AUDIT = load_audit_module()


def parse_page_map(groups: Iterable[str]) -> Dict[str, Dict[str, str]]:
    source = EVIDENCE_FILE.read_text(encoding="utf-8")
    result: Dict[str, Dict[str, str]] = {}
    for group in groups:
        match = re.search(
            rf"^\s{{2}}{re.escape(group)}:\s*\{{\s*$"
            rf"(?P<body>.*?)"
            rf"^\s{{2}}\}},\s*$",
            source,
            flags=re.M | re.S,
        )
        if not match:
            raise RuntimeError(f"Missing original-page evidence group: {group}")
        pages: Dict[str, str] = {}
        for line in match.group("body").splitlines():
            entry = re.match(
                r"^\s{4}(?:'(?P<quoted>[^']+)'|(?P<plain>[^:]+)):\s*'(?P<url>[^']+)'",
                line,
            )
            if not entry:
                continue
            title = (entry.group("quoted") or entry.group("plain") or "").strip()
            pages[title] = entry.group("url")
        result[group] = pages
    return result


def visible_control(node: Tag) -> bool:
    if AUDIT.is_hidden(node):
        return False
    if node.name != "input":
        return True
    return node.get("type", "text").lower() not in NON_QUERY_INPUT_TYPES


def compact_action_text(node: Tag) -> str:
    if node.name == "input":
        return (node.get("value") or node.get("title") or "").strip()
    return AUDIT.compact_text(node)


def nearby_text(node: Tag, direction: str) -> str:
    sibling = node.next_sibling if direction == "next" else node.previous_sibling
    for _ in range(8):
        if sibling is None:
            break
        if isinstance(sibling, str):
            text = " ".join(sibling.split()).strip("：: ")
            if text and len(text) <= 30:
                return text
        elif isinstance(sibling, Tag):
            if sibling.name in {"input", "select", "textarea", "button"}:
                break
            text = AUDIT.compact_text(sibling).strip("：: ")
            if text and len(text) <= 30:
                return text
        sibling = (
            sibling.next_sibling if direction == "next" else sibling.previous_sibling
        )
    return ""


def punctuated_previous_label(node: Tag) -> str:
    sibling = node.previous_sibling
    for _ in range(4):
        if sibling is None:
            break
        if isinstance(sibling, str):
            raw = " ".join(sibling.split())
            if raw:
                return raw.strip("：: ") if raw.endswith(("：", ":")) else ""
        elif isinstance(sibling, Tag):
            if sibling.name in {"input", "select", "textarea", "button"}:
                break
            raw = AUDIT.compact_text(sibling)
            if raw:
                return raw.strip("：: ") if raw.endswith(("：", ":")) else ""
        sibling = sibling.previous_sibling
    return ""


def group_label(node: Tag) -> str:
    name = node.get("name", "")
    previous = node.previous_sibling
    while previous is not None:
        if isinstance(previous, Tag) and previous.name == "input":
            if name and previous.get("name", "") == name:
                return ""
            break
        previous = previous.previous_sibling
    label = nearby_text(node, "previous")
    if label:
        return label
    parent = node.parent if isinstance(node.parent, Tag) else None
    if parent is not None:
        return nearby_text(parent, "previous")
    return ""


def enhance_label(node: Tag, soup: BeautifulSoup, existing: str) -> str:
    input_type = (
        node.get("type", "").lower()
        if node.name == "input"
        else ""
    )
    if input_type in {"checkbox", "radio"}:
        prefixed = punctuated_previous_label(node)
        if prefixed:
            return prefixed[:80]
        node_id = node.get("id")
        if node_id:
            label = soup.find("label", attrs={"for": node_id})
            text = AUDIT.compact_text(label)
            if text:
                return text[:80]
        option_text = nearby_text(node, "next")
        if option_text:
            return option_text[:80]
        context = group_label(node)
        if context:
            return context[:80]
        return existing

    sibling = node.previous_sibling
    for _ in range(8):
        if sibling is None:
            break
        if isinstance(sibling, str):
            text = " ".join(sibling.split()).strip("：: ")
            if text and len(text) <= 30:
                return text
        elif isinstance(sibling, Tag):
            if sibling.name in {"input", "select", "textarea", "button"}:
                break
            text = AUDIT.compact_text(sibling).strip("：: ")
            if text and len(text) <= 30:
                return text
        sibling = sibling.previous_sibling
    if existing and len(existing) <= 40:
        return existing
    return existing


def control_schema(node: Tag, soup: BeautifulSoup) -> dict:
    schema = AUDIT.control_schema(node, soup)
    schema["label"] = enhance_label(node, soup, schema.get("label", ""))
    if node.name == "input" and node.get("type", "").lower() in {"checkbox", "radio"}:
        schema["groupLabel"] = group_label(node)
    return schema


def first_query_button(soup: BeautifulSoup) -> Optional[Tag]:
    for node in soup.find_all(["button", "input", "a", "span"]):
        if AUDIT.is_hidden(node):
            continue
        if node.name == "input" and node.get("type", "text").lower() not in {
            "button",
            "submit",
            "image",
        }:
            continue
        if AUDIT.normalized_button_text(node) in AUDIT.QUERY_WORDS:
            return node
    return None


def query_root(button: Tag) -> Optional[Tag]:
    current = button.parent if isinstance(button.parent, Tag) else None
    best: Optional[Tag] = None
    best_count = 0
    while isinstance(current, Tag) and current.name not in {"form", "body", "html"}:
        controls = [
            node
            for node in current.find_all(["input", "select", "textarea"])
            if visible_control(node)
        ]
        count = len(controls)
        if count > best_count:
            best = current
            best_count = count
        elif best_count and count == best_count:
            break
        if count > 40:
            break
        current = current.parent if isinstance(current.parent, Tag) else None
    return best


def query_surface(soup: BeautifulSoup) -> dict:
    button = first_query_button(soup)
    if not button:
        return {"button": "", "controls": [], "actions": []}
    root = query_root(button)
    if root is None:
        return {
            "button": compact_action_text(button),
            "controls": [],
            "actions": [compact_action_text(button)],
        }
    controls = [
        control_schema(node, soup)
        for node in root.find_all(["input", "select", "textarea"])
        if visible_control(node)
    ]
    actions: List[str] = []
    for node in root.find_all(["button", "input", "a", "span"]):
        if AUDIT.is_hidden(node):
            continue
        if node.name == "input" and node.get("type", "text").lower() not in {
            "button",
            "submit",
            "image",
        }:
            continue
        text = compact_action_text(node)
        if not text or len(text) > 40:
            continue
        if (
            node.name in {"button", "a"}
            or node.get("onclick")
            or node.get("id", "").lower().startswith("btn")
            or AUDIT.normalized_button_text(node) in AUDIT.QUERY_WORDS
        ):
            if text not in {"X", "×"} and text not in actions:
                actions.append(text)
    primary_text = compact_action_text(button)
    if primary_text and primary_text not in actions:
        actions.append(primary_text)
    return {"button": primary_text, "controls": controls, "actions": actions}


def toolbar_containers(soup: BeautifulSoup) -> List[Tag]:
    containers: List[Tag] = []
    for node in soup.find_all(True):
        node_id = str(node.get("id", ""))
        classes = " ".join(str(item) for item in node.get("class", []))
        if re.search(r"(^|[-_])tool(?:bar)?($|[-_])", node_id, re.I) or re.search(
            r"(^|\s|[-_])tool(?:bar)?($|\s|[-_])", classes, re.I
        ):
            if not AUDIT.is_hidden(node):
                containers.append(node)
    return containers


def toolbar_actions(soup: BeautifulSoup) -> Tuple[List[dict], List[dict]]:
    containers = toolbar_containers(soup)
    actions: List[dict] = []
    container_meta: List[dict] = []
    for container in containers:
        container_meta.append(
            {
                "tag": container.name,
                "id": container.get("id", ""),
                "class": " ".join(container.get("class", [])),
            }
        )
        candidates: List[Tuple[Tag, str]] = []
        for node in container.find_all(["input", "button", "a", "span", "li", "div"]):
            if AUDIT.is_hidden(node):
                continue
            text = compact_action_text(node)
            if not text or len(text) > 40:
                continue
            if node.name == "input" and node.get("type", "text").lower() not in {
                "button",
                "submit",
                "image",
            }:
                continue
            if (
                node.name in {"input", "button", "a"}
                or node.get("id")
                or node.get("onclick")
                or node.get("href")
            ):
                candidates.append((node, text))
        candidate_nodes = {id(node) for node, _ in candidates}
        for node, text in candidates:
            has_candidate_child = any(
                id(child) in candidate_nodes
                for child in node.find_all(["input", "button", "a", "span", "li", "div"])
            )
            if has_candidate_child:
                continue
            item = {
                "text": text,
                "tag": node.name,
                "id": node.get("id", ""),
                "class": " ".join(node.get("class", [])),
                "disabled": node.has_attr("disabled"),
            }
            if item["text"] not in [action["text"] for action in actions]:
                actions.append(item)
    return actions, container_meta


def grid_headers(soup: BeautifulSoup) -> List[str]:
    result: List[str] = []
    for node in soup.find_all("th"):
        if AUDIT.is_hidden(node):
            continue
        text = AUDIT.compact_text(node)
        if text and len(text) <= 80 and text not in result:
            result.append(text)
    if result:
        return result
    source = str(soup)
    match = re.search(r"colNames\s*:\s*\[(?P<items>.*?)\]", source, re.S)
    if not match:
        return result
    for text in re.findall(r"['\"]([^'\"]*)['\"]", match.group("items")):
        cleaned = " ".join(text.split())
        if cleaned and cleaned not in result:
            result.append(cleaned)
    return result


def static_tables(soup: BeautifulSoup) -> List[List[List[str]]]:
    tables: List[List[List[str]]] = []
    for table in soup.find_all("table"):
        rows: List[List[str]] = []
        for row in table.find_all("tr"):
            cells = [
                AUDIT.compact_text(cell)
                for cell in row.find_all(["th", "td"])
            ]
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)
    return tables


def compact_page_schema(html: str, include_static_tables: bool = False) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    query = query_surface(soup)
    toolbar, containers = toolbar_actions(soup)
    result = {
        "toolbar": toolbar,
        "toolbarContainers": containers,
        "query": query,
        "gridHeaders": grid_headers(soup),
    }
    if include_static_tables:
        result["staticTables"] = static_tables(soup)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--module",
        action="append",
        choices=TARGET_MODULES,
        help="Limit extraction to one or more module keys.",
    )
    parser.add_argument("--page-limit", type=int, default=0)
    parser.add_argument(
        "--write-config",
        help="Write the desensitized UI schema JSON below src/config.",
    )
    parser.add_argument(
        "--merge-config",
        action="store_true",
        help="Merge selected modules into an existing generated config.",
    )
    args = parser.parse_args()

    username = os.environ.get("ERP_USER", "")
    password = os.environ.get("ERP_PASSWORD", "")
    if not username or not password:
        raise RuntimeError("Set ERP_USER and ERP_PASSWORD for the temporary read-only session")

    selected_modules = tuple(args.module or TARGET_MODULES)
    page_map = parse_page_map(selected_modules)
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/126 Safari/537.36"
        }
    )
    AUDIT.login(session, username, password)

    output = {
        "schemaVersion": 1,
        "auditedOn": dt.date.today().isoformat(),
        "authenticated": True,
        "modules": {},
    }
    processed = 0
    for module, pages in page_map.items():
        output["modules"][module] = {}
        for title, path in pages.items():
            if args.page_limit and processed >= args.page_limit:
                break
            response = AUDIT.fetch(session, path)
            output["modules"][module][title] = {
                "path": path,
                "status": response.status_code,
                "schema": compact_page_schema(
                    response.text, include_static_tables=module == "risk"
                )
                if response.status_code == 200
                else None,
            }
            processed += 1
        if args.page_limit and processed >= args.page_limit:
            break

    rendered = json.dumps(output, ensure_ascii=False, indent=2) + "\n"
    if args.write_config:
        config_root = (ROOT / "src" / "config").resolve()
        target = (config_root / args.write_config).resolve()
        try:
            target.relative_to(config_root)
        except ValueError as error:
            raise RuntimeError("The generated schema must stay below src/config") from error
        if args.merge_config and target.exists():
            existing = json.loads(target.read_text(encoding="utf-8"))
            existing["schemaVersion"] = output["schemaVersion"]
            existing["auditedOn"] = output["auditedOn"]
            existing["authenticated"] = True
            existing.setdefault("modules", {}).update(output["modules"])
            output = existing
            rendered = json.dumps(output, ensure_ascii=False, indent=2) + "\n"
        target.write_text(rendered, encoding="utf-8")
        json.dump(
            {
                "written": str(target),
                "moduleCount": len(output["modules"]),
                "pageCount": sum(len(pages) for pages in output["modules"].values()),
            },
            sys.stdout,
            ensure_ascii=False,
            indent=2,
        )
        sys.stdout.write("\n")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

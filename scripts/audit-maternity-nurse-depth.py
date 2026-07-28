"""Audit desensitized deep UI schema for the legacy maternity-nurse module.

Credentials are accepted only through ERP_USER / ERP_PASSWORD. The script
prints toolbar targets, visible jqGrid columns, and blank/static form schema.
It never prints cookies, page source, grid rows, or real business field values.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
from pathlib import Path, PurePosixPath
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag


ROOT = Path(__file__).resolve().parents[1]
AUDIT_FILE = ROOT / "scripts" / "audit-nursing-query-areas.py"
GRID_FILE = ROOT / "scripts" / "inspect-legacy-grid-definitions.py"

PAGES = {
    "月嫂档案": "Page/BasicInfo/MaternityMatronList.aspx?navid=422",
    "薪酬标准": "Page/BasicInfo/MaternityPriceList.aspx?navid=588",
    "月嫂档期": "Page/BasicInfo/TimeManagement.aspx?navid=593",
    "月嫂合同": "Page/MaternityContract/ContractList.aspx?navid=599",
    "月嫂服务记录": "Page/NursingManager/MomServerLogList.aspx?navid=423",
    "月嫂派工审核": "Page/MaternityContract/MomServerLogSH.aspx?navid=666",
    "月嫂结算列表": "Page/NursingManager/MomServerSalary.aspx?navid=665",
    "月嫂预约记录": "Page/MaternityContract/MaternityYYList.aspx?navid=641",
}

OBSERVED_SELECTION_FORM_BASES = {
    "月嫂档期": ["Page/BasicInfo/TimeManagementAdd.aspx"],
    "月嫂服务记录": ["Page/NursingManager/MomServerLogAcount.aspx"],
}

NON_FORM_TYPES = {"hidden", "button", "submit", "reset", "image"}


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load helper: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


AUDIT = load_module("maternity_audit_helpers", AUDIT_FILE)
GRID = load_module("maternity_grid_helpers", GRID_FILE)


def compact_text(node: Tag | None) -> str:
    return AUDIT.compact_text(node) if node is not None else ""


def is_visible_control(node: Tag) -> bool:
    if AUDIT.is_hidden(node):
        return False
    return not (
        node.name == "input"
        and node.get("type", "text").lower() == "hidden"
    )


def field_label(node: Tag, soup: BeautifulSoup) -> str:
    node_id = node.get("id", "")
    if node_id:
        explicit = soup.find("label", attrs={"for": node_id})
        text = compact_text(explicit)
        if text:
            return text[:100]

    if node.name == "input" and node.get("type", "").lower() in {
        "checkbox",
        "radio",
    }:
        sibling = node.next_sibling
        for _ in range(4):
            if sibling is None:
                break
            if isinstance(sibling, str):
                text = " ".join(sibling.split()).strip("：: ")
            elif isinstance(sibling, Tag):
                if sibling.name in {"input", "select", "textarea", "button"}:
                    break
                text = compact_text(sibling).strip("：: ")
            else:
                text = ""
            if text:
                return text[:100]
            sibling = sibling.next_sibling

    cell = node.find_parent(["td", "th"])
    if cell is not None:
        previous = cell.find_previous_sibling(["td", "th"])
        text = compact_text(previous)
        if text:
            return text[:100]

    sibling = node.previous_sibling
    for _ in range(8):
        if sibling is None:
            break
        if isinstance(sibling, str):
            text = " ".join(sibling.split()).strip("：: ")
        elif isinstance(sibling, Tag):
            if sibling.name in {"input", "select", "textarea", "button"}:
                break
            text = compact_text(sibling).strip("：: ")
        else:
            text = ""
        if text:
            return text[:100]
        sibling = sibling.previous_sibling
    return ""


def safe_default(node: Tag) -> str:
    value = str(node.get("value", ""))
    if not value:
        return ""
    input_type = node.get("type", "text").lower()
    if input_type in {"checkbox", "radio"}:
        return value if len(value) <= 20 else "<non-empty>"
    if (
        value in {"0", "1"}
        or re.fullmatch(r"\d{4}-\d{1,2}-\d{1,2}", value)
        or value.startswith("-")
    ):
        return value
    return "<non-empty>"


def choice_group_label(node: Tag) -> str:
    if node.name != "input" or node.get("type", "").lower() not in {
        "checkbox",
        "radio",
    }:
        return ""
    cell = node.find_parent(["td", "th"])
    if cell is None:
        return ""
    previous = cell.find_previous_sibling(["td", "th"])
    return compact_text(previous)[:100]


def form_schema(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    controls = []
    for node in soup.find_all(["input", "select", "textarea"]):
        if not is_visible_control(node):
            continue
        item = {
            "tag": node.name,
            "id": node.get("id", ""),
            "name": node.get("name", ""),
            "type": (
                "select"
                if node.name == "select"
                else "textarea"
                if node.name == "textarea"
                else node.get("type", "text").lower()
            ),
            "label": field_label(node, soup),
            "disabled": node.has_attr("disabled"),
            "readonly": node.has_attr("readonly"),
        }
        if node.name == "select":
            options = node.find_all("option")
            item["options"] = [compact_text(option) for option in options]
            item["selected"] = [
                compact_text(option)
                for option in options
                if option.has_attr("selected")
            ]
            if not item["selected"] and options:
                item["selected"] = [compact_text(options[0])]
        elif node.name == "input":
            input_type = item["type"]
            if input_type in {"checkbox", "radio"}:
                item["checked"] = node.has_attr("checked")
                item["groupLabel"] = choice_group_label(node)
            item["default"] = safe_default(node)
        controls.append(item)

    actions = []
    for node in soup.find_all(["button", "input", "a"]):
        if AUDIT.is_hidden(node):
            continue
        if node.name == "input" and node.get("type", "text").lower() not in {
            "button",
            "submit",
            "reset",
        }:
            continue
        text = (
            str(node.get("value", "")).strip()
            if node.name == "input"
            else compact_text(node)
        )
        if text and len(text) <= 40 and text not in actions:
            actions.append(text)
    return {"controls": controls, "actions": actions}


def toolbar_ids(soup: BeautifulSoup) -> list[tuple[str, str]]:
    toolbar = soup.find(id="toolbar")
    if toolbar is None:
        return []
    result = []
    for node in toolbar.find_all(["span", "a", "button", "input"]):
        if AUDIT.is_hidden(node):
            continue
        node_id = node.get("id", "")
        text = (
            str(node.get("value", "")).strip()
            if node.name == "input"
            else compact_text(node)
        )
        if node_id and text and (node_id, text) not in result:
            result.append((node_id, text))
    return result


def action_evidence(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    source = "\n".join(script.get_text("\n") for script in soup.find_all("script"))
    action_nodes = toolbar_ids(soup)
    markers = []
    for action_id, text in action_nodes:
        marker = re.search(
            rf"""(?:\$|jQuery)\(\s*["']#{re.escape(action_id)}["']\s*\)\.click""",
            source,
        )
        markers.append((marker.start() if marker else -1, action_id, text))
    ordered_starts = sorted(start for start, _, _ in markers if start >= 0)
    evidence = []
    for start, action_id, text in markers:
        snippet = ""
        if start >= 0:
            following = [item for item in ordered_starts if item > start]
            end = following[0] if following else start + 2200
            snippet = source[start:end]
        targets = []
        for match in re.finditer(
            r"""(?P<quote>["'])(?P<path>[A-Za-z0-9_./-]+\.aspx(?:\?[^"'<>]*)?)(?P=quote)""",
            snippet,
        ):
            target = match.group("path").strip()
            if target.lower().startswith("ajax/"):
                continue
            if target not in targets:
                targets.append(target)
        evidence.append(
            {
                "id": action_id,
                "text": text,
                "targets": targets,
                "requiresSelection": bool(
                    re.search(r"selrow|getGridParam[^;]*selrow", snippet)
                ),
                "selectionWarning": (
                    "请选中一行数据！"
                    if "请选中一行数据" in snippet
                    else ""
                ),
                "confirmText": (
                    "您确定要删除吗？"
                    if "您确定要删除吗" in snippet
                    else ""
                ),
            }
        )
    return evidence


def visible_grids(html: str) -> list[dict]:
    result = []
    for grid in GRID.grid_definitions(html):
        names = grid.get("colNames", [])
        models = grid.get("colModel", [])
        visible = []
        hidden = []
        for index, label in enumerate(names):
            model = models[index] if index < len(models) else {}
            item = {
                "label": label,
                "name": model.get("name", ""),
            }
            if model.get("hidden", False):
                hidden.append(item)
            else:
                visible.append(item)
        result.append(
            {
                "gridId": grid.get("gridId", ""),
                "caption": grid.get("caption", ""),
                "visibleColumns": visible,
                "hiddenColumns": hidden,
            }
        )
    return result


def row_action_labels(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    source = "\n".join(script.get_text("\n") for script in soup.find_all("script"))
    result = []
    for match in re.finditer(
        r""">\s*([\u4e00-\u9fff][\u4e00-\u9fffA-Za-z0-9/（）()·\s]{0,24})\s*</(?:a|span|button)>""",
        source,
        re.I,
    ):
        text = " ".join(match.group(1).split())
        if text and text not in result:
            result.append(text)
    return result


def static_form_targets(page_path: str, actions: list[dict]) -> list[str]:
    page_url = f"http://qd.mm.hxqt.cn/{page_path}"
    result = []
    for action in actions:
        if action["text"] != "添加" or action["requiresSelection"]:
            continue
        for target in action["targets"]:
            if "+" in target:
                continue
            parsed = urlparse(target)
            if parsed.query:
                continue
            absolute = urljoin(page_url, target)
            path = absolute.replace("http://qd.mm.hxqt.cn/", "", 1)
            suffix = PurePosixPath(urlparse(path).path).name.lower()
            if (
                suffix in {"login3.aspx", "news_add.aspx", "nonquery.aspx"}
                or re.search(r"(?:ajax|excel|export|report|print)", path, re.I)
            ):
                continue
            if path not in result:
                result.append(path)
    return result


def main() -> int:
    username = os.environ.get("ERP_USER", "")
    password = os.environ.get("ERP_PASSWORD", "")
    if not username or not password:
        raise RuntimeError("Set ERP_USER and ERP_PASSWORD for the temporary session")

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/126 Safari/537.36"
            )
        }
    )
    AUDIT.login(session, username, password)

    output = {}
    fetched_forms = set()
    for title, page_path in PAGES.items():
        response = AUDIT.fetch(session, page_path)
        response.raise_for_status()
        actions = action_evidence(response.text)
        page = {
            "path": page_path,
            "actions": actions,
            "grids": visible_grids(response.text),
            "rowActionLabels": row_action_labels(response.text),
            "forms": [],
        }
        form_paths = static_form_targets(page_path, actions)
        form_paths.extend(OBSERVED_SELECTION_FORM_BASES.get(title, []))
        for form_path in form_paths:
            if form_path in fetched_forms:
                continue
            fetched_forms.add(form_path)
            form_response = AUDIT.fetch(session, form_path)
            if form_response.status_code != 200:
                page["forms"].append(
                    {"path": form_path, "status": form_response.status_code}
                )
                continue
            page["forms"].append(
                {
                    "path": form_path,
                    "status": form_response.status_code,
                    "schema": form_schema(form_response.text),
                    "grids": visible_grids(form_response.text),
                }
            )
        output[title] = page

    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

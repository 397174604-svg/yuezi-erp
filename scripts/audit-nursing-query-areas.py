"""Read-only legacy ERP query-area schema extractor.

Credentials are accepted only through ERP_USER and ERP_PASSWORD environment
variables. The script prints control schema and never writes HTML, cookies, or
business rows to disk.
"""

from __future__ import annotations

import json
import argparse
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag


BASE_URL = "http://qd.mm.hxqt.cn/"
LOGIN_PATH = "Page/Login/Login3.aspx"
ROOT = Path(__file__).resolve().parents[1]
ENCRYPT_SCRIPT = ROOT / "scripts" / "erp-login-encrypt.cjs"

PAGES = {
    "护理计划": "Page/NursingManager/NursingPlan1.aspx?navid=110",
    "护理部排班第二版": "Page/ServiceCenter/SchedulingManagerNewTWO.aspx?navid=669",
    "宝宝档案": "Page/SalerManager/BabyInfoMassage.aspx?navid=314",
    "健康评估": "Page/NurseManagerNew/HealthAssessmentList.aspx?navid=537",
    "膳食评估": "Page/NurseManagerNew/MealAssessList.aspx?navid=655",
    "自定义查房": "Page/NurseManagerNew/LookRoundList.aspx?navid=112",
    "医生查房记录": "Page/NursingManager/CheckRecord.aspx?navid=575",
    "膳食禁忌查房": "Page/NurseManagerNew/MealScheduleList.aspx?navid=600",
    "护理计划确认": "Page/ServiceCenter/NursingplanOK.aspx?navid=604",
    "护理项目记录": "Page/NursingManager/NursingPlanMangerHL.aspx?navid=585",
    "妈妈护理记录": "Page/NurseManagerNew/MaternalCareLogList.aspx?navid=505",
    "宝宝护理记录": "Page/NurseManagerNew/BabyRecordInfo.aspx?navid=506",
    "妈妈护理汇总": "Page/Report/MamaNurseReport.aspx?navid=557",
    "宝宝护理汇总": "Page/Report/BabyNurseReport1.aspx?navid=536",
    "护理部排班表": "Page/ServiceCenter/SchedulingManagerNew.aspx?navid=275",
    "入住物品交接": "Page/NursingManager/ItemListing.aspx?navid=114",
}

QUERY_WORDS = {"查询", "搜索", "检索"}
DATE_VALUE = re.compile(
    r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}(?:\s+\d{1,2}:\d{2}(?::\d{2})?)?$"
)


def encrypt(value: str) -> str:
    result = subprocess.run(
        ["node", str(ENCRYPT_SCRIPT), value],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def login(session: requests.Session, username: str, password: str) -> None:
    login_url = urljoin(BASE_URL, LOGIN_PATH)
    response = session.get(login_url, timeout=20)
    response.raise_for_status()
    response.encoding = response.apparent_encoding or "utf-8"
    soup = BeautifulSoup(response.text, "html.parser")
    payload = {}
    for node in soup.find_all(
        "input", attrs={"type": re.compile(r"^hidden$", re.I), "name": True}
    ):
        payload[node.get("name")] = node.get("value", "")
    payload.update(
        {
            "userLogin": encrypt(username),
            "passWord": encrypt(password),
            "lgtype": payload.get("lgtype", "0"),
            "aurocodeId": payload.get("aurocodeId", "0"),
            "btnLogin.x": "1",
            "btnLogin.y": "1",
        }
    )
    payload.pop("txtName", None)
    payload.pop("iptPwd", None)
    result = session.post(
        login_url,
        data=payload,
        headers={"Referer": login_url},
        timeout=25,
        allow_redirects=True,
    )
    result.raise_for_status()
    if "Login3.aspx" in result.url or 'id="btnLogin"' in result.text:
        raise RuntimeError("Legacy ERP login did not establish an authenticated session")


def fetch(session: requests.Session, path: str) -> requests.Response:
    url = urljoin(BASE_URL, path)
    last = None
    for attempt in range(4):
        try:
            response = session.get(url, timeout=30)
            if response.status_code < 500:
                response.encoding = response.apparent_encoding or "utf-8"
                return response
            last = response
        except requests.RequestException as error:
            last = error
        time.sleep(0.6 * (attempt + 1))
    if isinstance(last, requests.Response):
        last.encoding = last.apparent_encoding or "utf-8"
        return last
    raise last or RuntimeError(f"Unable to read {url}")


def compact_text(node: Tag | None) -> str:
    if not node:
        return ""
    return " ".join(node.get_text(" ", strip=True).split())


def is_hidden(node: Tag) -> bool:
    if node.name == "input" and node.get("type", "text").lower() == "hidden":
        return True
    current: Tag | None = node
    while isinstance(current, Tag):
        style = current.get("style", "").replace(" ", "").lower()
        classes = {str(item).lower() for item in current.get("class", [])}
        if "display:none" in style or "visibility:hidden" in style:
            return True
        if {"hidden", "hide"} & classes:
            return True
        current = current.parent if isinstance(current.parent, Tag) else None
    return False


def field_label(node: Tag, soup: BeautifulSoup) -> str:
    node_id = node.get("id")
    if node_id:
        label = soup.find("label", attrs={"for": node_id})
        text = compact_text(label)
        if text:
            return text[:80]

    parent_label = node.find_parent("label")
    text = compact_text(parent_label)
    if text and len(text) <= 80:
        return text

    cell = node.find_parent(["td", "th"])
    if cell:
        previous = cell.find_previous_sibling(["td", "th"])
        text = compact_text(previous)
        if text and len(text) <= 80:
            return text
        own = compact_text(cell)
        node_text = compact_text(node)
        if node_text:
            own = own.replace(node_text, "", 1).strip()
        if own and len(own) <= 40:
            return own

    previous = node.find_previous_sibling(["label", "span", "em", "strong"])
    text = compact_text(previous)
    return text[:80] if text and len(text) <= 80 else ""


def safe_value(node: Tag) -> str:
    value = node.get("value", "")
    field_name = f"{node.get('id', '')} {node.get('name', '')}".lower()
    field_type = node.get("type", "text").lower()
    if not value:
        return ""
    if (
        field_type in {"date", "datetime", "datetime-local", "month", "time"}
        or any(token in field_name for token in ("date", "time", "year", "month", "day"))
        or DATE_VALUE.match(value)
        or value in {"0", "1", "-1"}
    ):
        return value
    return "<non-empty>"


def control_schema(node: Tag, soup: BeautifulSoup) -> dict:
    schema = {
        "tag": node.name,
        "id": node.get("id", ""),
        "name": node.get("name", ""),
        "type": node.get("type", "") if node.name == "input" else node.name,
        "label": field_label(node, soup),
        "placeholder": node.get("placeholder", ""),
        "disabled": node.has_attr("disabled"),
        "readonly": node.has_attr("readonly"),
    }
    if node.name == "select":
        options = []
        selected = []
        for option in node.find_all("option"):
            label = compact_text(option)
            options.append(label)
            if option.has_attr("selected"):
                selected.append(label)
        if not selected:
            first = node.find("option")
            if first:
                selected.append(compact_text(first))
        schema["options"] = options
        schema["selected"] = selected
    elif node.name == "input":
        schema["value"] = safe_value(node)
        if node.get("type", "").lower() in {"checkbox", "radio"}:
            schema["checked"] = node.has_attr("checked")
    return schema


def button_text(node: Tag) -> str:
    if node.name == "input":
        return (node.get("value") or node.get("title") or "").strip()
    return compact_text(node)


def normalized_button_text(node: Tag) -> str:
    return re.sub(r"\s+", "", button_text(node))


def find_query_container(button: Tag) -> Tag:
    fallback = button.find_parent("form") or button.parent
    current = button.parent
    while isinstance(current, Tag):
        classes = {str(item) for item in current.get("class", [])}
        if {"divList", "search"} & classes:
            return current
        if current.name in {"div", "table", "tbody", "tr", "form", "fieldset"}:
            controls = [
                item
                for item in current.select("input, select, textarea")
                if not is_hidden(item)
            ]
            if controls and len(controls) <= 28:
                fallback = current
                if current.name in {"tr", "div", "fieldset"}:
                    return current
        current = current.parent if isinstance(current.parent, Tag) else None
    return fallback


def extract_schema(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    buttons = []
    query_buttons = []
    primary_query_controls = []
    primary_query_button = None
    ordered_nodes = soup.select(
        "input, select, textarea, button, a"
    )
    for node in ordered_nodes:
        if is_hidden(node):
            continue
        if node.name in {"button", "a"} or (
            node.name == "input"
            and node.get("type", "text").lower() in {"button", "submit", "image"}
        ):
            if normalized_button_text(node) in QUERY_WORDS:
                primary_query_button = node
                break
            continue
        if node.name == "input" and node.get("type", "text").lower() == "hidden":
            continue
        primary_query_controls.append(control_schema(node, soup))

    for node in soup.select("button, input[type=button], input[type=submit], input[type=image], a"):
        if is_hidden(node):
            continue
        text = button_text(node)
        if not text:
            continue
        item = {
            "text": text[:80],
            "tag": node.name,
            "id": node.get("id", ""),
            "class": " ".join(node.get("class", [])),
        }
        buttons.append(item)
        if normalized_button_text(node) in QUERY_WORDS:
            query_buttons.append(node)

    containers = []
    seen = set()
    for button in query_buttons:
        container = find_query_container(button)
        marker = id(container)
        if marker in seen:
            continue
        seen.add(marker)
        controls = [
            control_schema(node, soup)
            for node in container.select("input, select, textarea")
            if not is_hidden(node)
        ]
        containers.append(
            {
                "queryButton": button_text(button),
                "buttonId": button.get("id", ""),
                "containerTag": container.name,
                "containerId": container.get("id", ""),
                "containerClass": " ".join(container.get("class", [])),
                "text": compact_text(container)[:500],
                "controls": controls,
            }
        )

    all_visible_controls = [
        control_schema(node, soup)
        for node in soup.select("input, select, textarea")
        if not is_hidden(node)
    ]
    all_selects = []
    for node in soup.select("select"):
        item = control_schema(node, soup)
        item["hidden"] = is_hidden(node)
        item["class"] = " ".join(node.get("class", []))
        item["style"] = node.get("style", "")
        all_selects.append(item)
    return {
        "primaryQueryArea": {
            "button": button_text(primary_query_button) if primary_query_button else "",
            "buttonId": primary_query_button.get("id", "") if primary_query_button else "",
            "controls": primary_query_controls if primary_query_button else [],
        },
        "queryAreas": containers,
        "visibleControls": all_visible_controls,
        "selectsIncludingHidden": all_selects,
        "visibleButtons": buttons,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--page",
        action="append",
        choices=tuple(PAGES),
        help="Limit extraction to one or more page titles.",
    )
    arguments = parser.parse_args()
    username = os.environ.get("ERP_USER", "")
    password = os.environ.get("ERP_PASSWORD", "")
    if not username or not password:
        raise RuntimeError("Set ERP_USER and ERP_PASSWORD for the temporary read-only session")

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/126 Safari/537.36"
        }
    )
    login(session, username, password)

    result = {"authenticated": True, "pages": {}}
    selected_pages = arguments.page or list(PAGES)
    for title in selected_pages:
        path = PAGES[title]
        response = fetch(session, path)
        page = {
            "path": path,
            "status": response.status_code,
            "schema": extract_schema(response.text) if response.status_code == 200 else None,
        }
        result["pages"][title] = page
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

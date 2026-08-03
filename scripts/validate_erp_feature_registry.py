"""Static release gate for the 104-item ERP Web feature inventory.

This check deliberately validates the source files instead of browser labels so a
menu refactor cannot accidentally omit, duplicate or rename a feature without
being caught by the release smoke suite.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "src" / "config" / "erp-feature-registry.js"
ROUTER = ROOT / "src" / "router" / "index.js"


def feature_ids(source: str) -> list[str]:
    return re.findall(r"\['(F\d{3})'\s*,", source)


def main() -> int:
    registry_source = REGISTRY.read_text(encoding="utf-8")
    router_source = ROUTER.read_text(encoding="utf-8")

    registry_ids = feature_ids(registry_source)
    registry_set = set(registry_ids)
    errors: list[str] = []

    if len(registry_ids) != 104:
        errors.append(f"ERP功能清单应为104项，当前为{len(registry_ids)}项")
    if len(registry_set) != len(registry_ids):
        duplicate_ids = sorted(
            item for item in registry_set if registry_ids.count(item) > 1
        )
        errors.append(f"ERP功能编号重复：{', '.join(duplicate_ids)}")

    menu_block = router_source.split("const productMenuDefinitions =", 1)[1]
    menu_block = menu_block.split("const featureById =", 1)[0]
    menu_ids = set(re.findall(r"'(F\d{3})'", menu_block))
    dashboard_ids = set(re.findall(r"featureId:\s*'([^']+)'", router_source))
    dashboard_ids = {
        item.strip() for value in dashboard_ids for item in value.split(",")
    }
    assigned_ids = menu_ids | dashboard_ids

    missing = sorted(registry_set - assigned_ids)
    unknown = sorted(assigned_ids - registry_set)
    if missing:
        errors.append(f"菜单/首页缺少功能：{', '.join(missing)}")
    if unknown:
        errors.append(f"菜单/首页存在未注册功能：{', '.join(unknown)}")

    if errors:
        print("ERP 104项功能注册校验失败：")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print("ERP 104项功能注册校验通过：104项唯一功能均已分配到首页或左侧菜单。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

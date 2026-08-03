#!/usr/bin/env python3
"""Static regression guard for Vue workbench route reuse.

Vue Router intentionally reuses the same component for sibling ERP item routes.
Stateful workbenches must therefore reset on ``$route.fullPath`` and must not
allow a response started by the previous route to overwrite the current page.
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def source(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


stateful_workbenches = {
    "nursing": "src/views/erp/nursing-workbench/index.vue",
    "diet": "src/views/erp/diet-workbench/index.vue",
    "inventory": "src/views/erp/inventory-workbench/index.vue",
    "baby": "src/views/erp/baby-workbench/index.vue",
    "report": "src/views/erp/report-workbench/index.vue",
    "people": "src/views/erp/people-workbench/index.vue",
    "member": "src/views/erp/member-workbench/index.vue",
}

for name, relative_path in stateful_workbenches.items():
    text = source(relative_path)
    assert "'$route.fullPath'" in text, f"{name} must reset when a sibling route replaces it"
    assert "loadSequence" in text, f"{name} must reject responses from the previous route"

for name in ("nursing", "diet", "inventory"):
    text = source(stateful_workbenches[name])
    assert "meta.configTitle || meta.title" in text, f"{name} must resolve the unstarred config title"
    assert ".replace(/\\s*★\\s*$/, '')" in text, f"{name} must not fall back because of the P0 marker"

# These workbenches are synchronous or presentation-only, but still need to
# derive their current definition from route meta on every render/change.
approval = source("src/views/erp/approval-workbench/index.vue")
store = source("src/views/erp/store-workbench/index.vue")
assert "$route.meta.configTitle" in approval and "getApprovalPageConfig(this.pageTitle)" in approval
assert "'$route.fullPath'" in store and "this.reloadRows()" in store

print("workbench route reuse checks: 9/9 passed")

#!/usr/bin/env python3
"""Static regression for F052/F053/F058/F061 formal setting routes."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


router = read("src/router/index.js")
features = read("src/config/p0-operations-features.js")
foundation = read("src/views/erp/foundation/index.vue")
store = read("src/views/erp/store-workbench/index.vue")
system = read("src/views/erp/system-workbench/index.vue")

# Canonical sidebar order determines the four formal routes.
assert "['people', '组织与绩效', 'tree', '#7B8A9A', ['F025', 'F047', 'F048', 'F049', 'F051', 'F052', 'F053'" in router
assert "['store', '门店管理', 'international', '#7B8A9A', ['F058', 'F093']]" in router
assert "['system', '系统设置', 'lock', '#65758B', ['F061', 'F079', 'F098']]" in router

# Dedicated page types prevent the four entries sharing a generic shell.
for token in (
    "'员工与组织': 'organization'",
    "'角色权限': 'role-permission'",
    "'门店与渠道': 'store-management'",
    "if (foundationPageTypes.includes(pageType)) return foundationPage",
    "if (pageType === 'store-management') return storeWorkbenchPage",
    "if (pageType === 'system-workbench') return systemWorkbenchPage",
):
    assert token in router, f"missing dedicated settings mapping: {token}"

expected_aliases = {
    "F052": "/people/item-6",
    "F053": "/people/item-7",
    "F058": "/store/item-1",
    "F061": "/system/item-1",
}
for feature_id, target in expected_aliases.items():
    line = next(line for line in features.splitlines() if f"id: '{feature_id}'" in line)
    assert f"canonicalPath: '{target}'" in line, f"{feature_id} does not redirect to {target}"

assert "/system/item-20" not in features, "F061 still redirects to the removed legacy item-20 route"

# Each destination exposes its own title and workflow instead of a shared list.
for token in ("pageType === 'organization'", "pageType === 'role-permission'", "组织部门", "业务角色"):
    assert token in foundation, f"foundation settings surface missing {token}"
for token in ("<h1>门店与渠道</h1>", "新增门店", "门店配置规则", "门店档案已保存"):
    assert token in store, f"store settings surface missing {token}"
for token in ("系统设置:", "featureId: 'F061'", "isSystemSettings()", "系统参数"):
    assert token in system, f"system settings surface missing {token}"

# Compatibility routes redirect before the wildcard 404 route is installed.
assert "...(feature.canonicalPath ? { redirect: feature.canonicalPath } : {})" in router
async_block = router.split("export const asyncRoutes =", 1)[1]
assert async_block.index("erpDeliveryRoutes") < async_block.index("{ path: '*', redirect: '/404'")

print("P0 settings route isolation passed: F052 people/6, F053 people/7, F058 store/1, F061 system/1")

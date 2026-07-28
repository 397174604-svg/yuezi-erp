#!/usr/bin/env python3
"""Generate the private account/RBAC acceptance-test document from MySQL.

The generated document intentionally contains no password, password hash,
mobile number, ID number, cookie, token, or business record.
"""

from __future__ import annotations

import csv
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.mvp_api import connect


SOURCE_DIR = ROOT / ".private" / "system-settings-import"
OUTPUT = ROOT / ".private" / "账号权限测试文档-2026-07-26.md"
TENANT_ID = 1

INTEGRATED_CAPABILITIES = (
    ("CUSTOMER.VIEW", "客户列表查询"),
    ("CUSTOMER.CREATE", "客户建档"),
    ("SALES.VIEW", "合同列表查询"),
    ("SALES.CREATE", "新增合同"),
    ("SALES.APPROVE", "合同审核"),
    ("FINANCE.VIEW", "收款列表查询"),
    ("FINANCE.CREATE", "新增收款"),
    ("FINANCE.APPROVE", "收款审核"),
    ("ROOM.VIEW", "房态及订房列表查询"),
    ("ROOM.CREATE", "新增订房"),
    ("ROOM.EXECUTE", "办理入住"),
)


def read_csv(name: str) -> list[dict]:
    with (SOURCE_DIR / name).open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        return list(csv.DictReader(handle))


def integer(value, default=0) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def md(value) -> str:
    text = str(value or "").strip()
    return text.replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def join_or_none(values, separator="、") -> str:
    items = [str(value).strip() for value in values if str(value).strip()]
    return separator.join(items) if items else "无"


def load_navigation():
    rows = read_csv("config-navigation.csv")
    navigation = {integer(row["KeyId"]): row for row in rows}
    source_order = {integer(row["KeyId"]): index for index, row in enumerate(rows)}

    def root_id(menu_id: int) -> int:
        current = menu_id
        seen = set()
        while current and current not in seen:
            seen.add(current)
            row = navigation.get(current)
            if not row:
                return menu_id
            parent_id = integer(row.get("ParentID"))
            if not parent_id:
                return current
            current = parent_id
        return menu_id

    return navigation, source_order, root_id


def load_source_role_metadata():
    roles = {
        integer(row["KeyId"]): row for row in read_csv("config-roles.csv")
    }
    navigation, source_order, root_id = load_navigation()
    top_modules = defaultdict(set)
    for row in read_csv("config-roleWebPermissionGrants.csv"):
        role_id = integer(row["roleId"])
        root = root_id(integer(row["menuId"]))
        title = str(navigation.get(root, {}).get("NavTitle") or "").strip()
        if title:
            top_modules[role_id].add((source_order.get(root, 999999), title))
    return roles, {
        role_id: [title for _, title in sorted(items)]
        for role_id, items in top_modules.items()
    }


def query_database():
    connection = connect()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                  ua.user_id,
                  ua.legacy_user_id,
                  ua.username,
                  ua.legacy_username,
                  ua.status,
                  ua.must_change_password,
                  ua.staff_id,
                  COALESCE(s.name, ua.legacy_username, ua.username) AS display_name,
                  COALESCE(s.department, d.name, '') AS department_name
                FROM user_accounts ua
                LEFT JOIN staff s ON s.staff_id=ua.staff_id
                LEFT JOIN departments d ON d.department_id=ua.department_id
                WHERE ua.tenant_id=%s
                  AND (
                    ua.legacy_user_id IS NOT NULL
                    OR ua.source_system='LOCAL_TEST'
                  )
                ORDER BY
                  CASE WHEN ua.status='ACTIVE' THEN 0 ELSE 1 END,
                  CASE WHEN ua.source_system='LEGACY_ERP' THEN 0 ELSE 1 END,
                  ua.legacy_user_id,
                  ua.user_id
                """,
                (TENANT_ID,),
            )
            accounts = cursor.fetchall()

            cursor.execute(
                """
                SELECT
                  ur.user_id,
                  r.role_id,
                  r.legacy_role_id,
                  r.code,
                  r.name,
                  r.role_type
                FROM user_roles ur
                JOIN roles r ON r.role_id=ur.role_id
                JOIN user_accounts ua ON ua.user_id=ur.user_id
                WHERE ua.tenant_id=%s
                  AND r.status='ACTIVE'
                  AND ur.effective_from <= NOW()
                  AND (ur.effective_to IS NULL OR ur.effective_to > NOW())
                ORDER BY ur.user_id, r.legacy_role_id, r.role_id
                """,
                (TENANT_ID,),
            )
            roles = cursor.fetchall()

            cursor.execute(
                """
                SELECT us.user_id, s.store_id, s.name
                FROM user_stores us
                JOIN stores s ON s.store_id=us.store_id
                JOIN user_accounts ua ON ua.user_id=us.user_id
                WHERE ua.tenant_id=%s
                ORDER BY us.user_id, s.store_id
                """,
                (TENANT_ID,),
            )
            stores = cursor.fetchall()

            cursor.execute(
                """
                SELECT DISTINCT ur.user_id, p.code
                FROM user_roles ur
                JOIN roles r ON r.role_id=ur.role_id AND r.status='ACTIVE'
                JOIN role_permissions rp
                  ON rp.role_id=r.role_id AND rp.effect='ALLOW'
                JOIN permissions p
                  ON p.permission_id=rp.permission_id AND p.status='ACTIVE'
                JOIN user_accounts ua ON ua.user_id=ur.user_id
                WHERE ua.tenant_id=%s
                  AND ur.effective_from <= NOW()
                  AND (ur.effective_to IS NULL OR ur.effective_to > NOW())
                ORDER BY ur.user_id, p.code
                """,
                (TENANT_ID,),
            )
            permissions = cursor.fetchall()

            cursor.execute(
                """
                SELECT
                  ur.user_id,
                  COUNT(DISTINCT scope.nav_id) AS nav_count,
                  COUNT(DISTINCT CONCAT(
                    scope.nav_id, ':', scope.department_id
                  )) AS scope_count,
                  COUNT(DISTINCT CASE WHEN scope.granted=1 THEN CONCAT(
                    scope.nav_id, ':', scope.department_id
                  ) END) AS granted_scope_count
                FROM user_roles ur
                JOIN roles r ON r.role_id=ur.role_id AND r.status='ACTIVE'
                JOIN legacy_role_data_scope_grants scope
                  ON scope.role_id=r.role_id
                JOIN user_accounts ua ON ua.user_id=ur.user_id
                WHERE ua.tenant_id=%s
                  AND ur.effective_from <= NOW()
                  AND (ur.effective_to IS NULL OR ur.effective_to > NOW())
                GROUP BY ur.user_id
                """,
                (TENANT_ID,),
            )
            scopes = cursor.fetchall()

            cursor.execute(
                """
                SELECT DISTINCT rp.role_id, p.code
                FROM role_permissions rp
                JOIN roles r ON r.role_id=rp.role_id AND r.status='ACTIVE'
                JOIN permissions p
                  ON p.permission_id=rp.permission_id AND p.status='ACTIVE'
                WHERE r.tenant_id=%s AND rp.effect='ALLOW'
                ORDER BY rp.role_id, p.code
                """,
                (TENANT_ID,),
            )
            role_permissions = cursor.fetchall()

            cursor.execute(
                """
                SELECT
                  r.role_id,
                  r.legacy_role_id,
                  r.code,
                  r.name,
                  r.role_type,
                  COUNT(DISTINCT CASE
                    WHEN p.code LIKE 'LEGACY.WEB.%%' THEN p.permission_id
                  END) AS web_permission_count,
                  COUNT(DISTINCT CASE
                    WHEN p.code LIKE 'LEGACY.APP.%%' THEN p.permission_id
                  END) AS app_permission_count,
                  COUNT(DISTINCT CASE
                    WHEN p.code NOT LIKE 'LEGACY.%%' THEN p.permission_id
                  END) AS integrated_permission_count,
                  COUNT(DISTINCT CONCAT(
                    scope.nav_id, ':', scope.department_id
                  )) AS data_scope_row_count,
                  COUNT(DISTINCT CASE WHEN scope.granted=1 THEN CONCAT(
                    scope.nav_id, ':', scope.department_id
                  ) END) AS data_scope_granted_count
                FROM roles r
                LEFT JOIN role_permissions rp
                  ON rp.role_id=r.role_id AND rp.effect='ALLOW'
                LEFT JOIN permissions p
                  ON p.permission_id=rp.permission_id AND p.status='ACTIVE'
                LEFT JOIN legacy_role_data_scope_grants scope
                  ON scope.role_id=r.role_id
                WHERE r.tenant_id=%s
                  AND r.source_system='LEGACY_ERP'
                  AND r.legacy_role_id IS NOT NULL
                  AND r.status='ACTIVE'
                GROUP BY
                  r.role_id, r.legacy_role_id, r.code, r.name, r.role_type
                ORDER BY r.legacy_role_id
                """,
                (TENANT_ID,),
            )
            role_summary = cursor.fetchall()

        return (
            accounts,
            roles,
            stores,
            permissions,
            scopes,
            role_permissions,
            role_summary,
        )
    finally:
        connection.close()


def capability_names(permission_codes: set[str]) -> list[str]:
    return [
        label
        for code, label in INTEGRATED_CAPABILITIES
        if code in permission_codes
    ]


def build_document() -> str:
    source_roles, top_modules = load_source_role_metadata()
    (
        accounts,
        role_rows,
        store_rows,
        permission_rows,
        scope_rows,
        role_permission_rows,
        role_summary,
    ) = query_database()

    roles_by_user = defaultdict(list)
    for row in role_rows:
        roles_by_user[row["user_id"]].append(row)
    stores_by_user = defaultdict(list)
    for row in store_rows:
        stores_by_user[row["user_id"]].append(row)
    permissions_by_user = defaultdict(set)
    for row in permission_rows:
        permissions_by_user[row["user_id"]].add(row["code"])
    scopes_by_user = {
        row["user_id"]: row for row in scope_rows
    }

    active_count = sum(row["status"] == "ACTIVE" for row in accounts)
    disabled_count = sum(row["status"] != "ACTIVE" for row in accounts)
    must_change_count = sum(
        row["status"] == "ACTIVE" and bool(row["must_change_password"])
        for row in accounts
    )
    linked_staff_count = sum(bool(row["staff_id"]) for row in accounts)
    legacy_accounts = [
        row for row in accounts if row["legacy_user_id"] is not None
    ]
    test_accounts = [
        row for row in accounts if row["legacy_user_id"] is None
    ]
    active_legacy_unlinked = sum(
        row["status"] == "ACTIVE" and not row["staff_id"]
        for row in legacy_accounts
    )
    multi_role_count = sum(
        len(roles_by_user[row["user_id"]]) > 1 for row in accounts
    )
    scope_snapshot_rows = sum(
        integer(row["data_scope_row_count"]) for row in role_summary
    )
    granted_scope_rows = sum(
        integer(row["data_scope_granted_count"]) for row in role_summary
    )

    lines = [
        "# 奇德芬芳 ERP 账号、功能与权限测试文档",
        "",
        f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "- 数据来源：本地 MySQL `yuezi` 中的账号、角色、权限、门店和数据范围",
        "- 适用版本：当前 MySQL MVP（客户 → 合同 → 收款 → 订房 → 入住）",
        "- 安全说明：本文不包含密码、密码哈希、手机号、身份证、Cookie、Token 或真实业务记录。",
        "",
        "## 1. 测试结论口径",
        "",
        "本文严格区分以下状态：",
        "",
        "1. **已导入授权**：原 ERP 的 Web/App 菜单按钮授权已经进入 MySQL；部门数据范围快照也已入库，但必须按快照中的 `granted` 状态解释。",
        "2. **已接入功能**：当前前端操作已经调用真实 MySQL 后端，并由接口校验权限。",
        "3. **待接入功能**：授权数据虽然存在，但对应业务模块的真实后端接口、状态机或数据表尚未全部完成。",
        "",
        "> 因此，“旧 ERP 有权限”不等于“当前系统的该业务功能已经完整实现”。当前可做真实闭环验收的是客户、合同、收款、订房和入住主链路。",
        "",
        "## 2. 当前账号总览",
        "",
        "| 指标 | 数量 |",
        "|---|---:|",
        f"| 当前测试范围账号 | {len(accounts)} |",
        f"| 原 ERP 迁移账号 | {len(legacy_accounts)} |",
        f"| 补充角色代表账号 | {len(test_accounts)} |",
        f"| 可登录账号 | {active_count} |",
        f"| 禁用账号 | {disabled_count} |",
        f"| 保留角色 | {len(role_summary)} |",
        f"| 多角色账号 | {multi_role_count} |",
        f"| 已关联员工花名册 | {linked_staff_count} |",
        f"| 可用业务账号待关联员工 | {active_legacy_unlinked} |",
        f"| 首次登录必须改密 | {must_change_count} |",
        f"| 原数据范围快照行 | {scope_snapshot_rows} |",
        f"| 快照中明确授权行 | {granted_scope_rows} |",
        "",
        "已按业务确认排除：面点师、司机、保安、洗衣工、公共保洁、客房保洁、勤杂工、企划。只有这些排除角色的账号不会出现在下表。",
        "",
        "> 当前采集的原 ERP 数据范围快照中，`granted` 全部为 0，所以不能把这些快照行当成已授予的部门权限。当前 MVP 实际执行的是账号的门店范围；原 ERP 部门级授权需要重新核验后再启用。",
        "",
        "## 3. 角色功能矩阵",
        "",
        "“原 ERP 顶级模块”是该角色原授权的模块入口；“当前已接入功能”只列真实 MySQL API 已实现且已授权的动作。",
        "",
        "| 原角色ID | 角色 | 代表账号 | 类型 | 原 ERP 顶级模块 | Web权限 | App权限 | 数据范围快照/授权 | 当前已接入功能 |",
        "|---:|---|---|---|---|---:|---:|---:|---|",
    ]

    representative_by_role = defaultdict(list)
    for row in role_rows:
        account = next(
            (
                item
                for item in accounts
                if item["user_id"] == row["user_id"]
                and item["status"] == "ACTIVE"
            ),
            None,
        )
        if account:
            representative_by_role[row["role_id"]].append(
                (
                    0 if account["legacy_user_id"] is None else 1,
                    str(account["username"]),
                )
            )
    permissions_by_role = defaultdict(set)
    for row in role_permission_rows:
        permissions_by_role[row["role_id"]].add(row["code"])
    for row in role_summary:
        role_id = row["role_id"]
        legacy_role_id = integer(row["legacy_role_id"])
        module_names = top_modules.get(legacy_role_id, [])
        capabilities = capability_names(permissions_by_role.get(role_id, set()))
        lines.append(
            "| {legacy_id} | {name} | {representative} | {role_type} | {modules} | "
            "{web} | {app} | {scope} | {capabilities} |".format(
                legacy_id=legacy_role_id,
                name=md(row["name"]),
                representative=md(
                    sorted(
                        representative_by_role.get(role_id, [(9, "无")])
                    )[0][1]
                ),
                role_type="管理角色" if row["role_type"] == "MANAGEMENT" else "岗位角色",
                modules=md(join_or_none(module_names)),
                web=integer(row["web_permission_count"]),
                app=integer(row["app_permission_count"]),
                scope=(
                    f'{integer(row["data_scope_row_count"])}/'
                    f'{integer(row["data_scope_granted_count"])}'
                ),
                capabilities=md(join_or_none(capabilities)),
            )
        )

    lines.extend(
        [
            "",
            "## 4. 逐账号测试清单",
            "",
            "账号状态为“禁用”的记录只验证拒绝登录；“登录账号”列是当前系统实际用户名。若禁用账号被改成技术隔离名，原账号仍保留在“原账号”列用于追溯。",
            "",
            "| 用例 | 账号类型 | 登录账号 | 原账号 | 姓名 | 部门 | 状态 | 角色 | 门店范围 | 当前已接入功能 | 旧Web/App授权 | 数据范围 | 员工关联 |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
        ]
    )

    for index, account in enumerate(accounts, start=1):
        user_id = account["user_id"]
        user_roles = roles_by_user.get(user_id, [])
        permission_codes = permissions_by_user.get(user_id, set())
        web_count = sum(code.startswith("LEGACY.WEB.") for code in permission_codes)
        app_count = sum(code.startswith("LEGACY.APP.") for code in permission_codes)
        scope = scopes_by_user.get(user_id, {})
        stores = [
            f'{row["name"]}(ID:{row["store_id"]})'
            for row in stores_by_user.get(user_id, [])
        ]
        role_names = []
        for row in user_roles:
            if row["legacy_role_id"] is None:
                role_names.append(f'{row["name"]}(本地)')
            else:
                role_names.append(
                    f'{row["name"]}(原ID:{row["legacy_role_id"]})'
                )
        capabilities = (
            capability_names(permission_codes)
            if account["status"] == "ACTIVE"
            else []
        )
        lines.append(
            "| ACC-{index:03d} | {account_type} | {username} | {legacy_username} | "
            "{display_name} | {department} | {status} | {roles} | "
            "{stores} | {capabilities} | Web {web}/App {app} | "
            "{navs}页/{scopes}项/授权{granted}项 | {staff} |".format(
                index=index,
                account_type=(
                    "原ERP业务账号"
                    if account["legacy_user_id"] is not None
                    else "角色验收账号"
                ),
                username=md(account["username"]),
                legacy_username=md(account["legacy_username"]),
                display_name=md(account["display_name"]),
                department=md(account["department_name"]) or "未匹配",
                status="可登录" if account["status"] == "ACTIVE" else "禁用",
                roles=md(join_or_none(role_names)),
                stores=md(join_or_none(stores)),
                capabilities=md(join_or_none(capabilities)),
                web=web_count,
                app=app_count,
                navs=integer(scope.get("nav_count")),
                scopes=integer(scope.get("scope_count")),
                granted=integer(scope.get("granted_scope_count")),
                staff="已关联" if account["staff_id"] else "待关联",
            )
        )

    lines.extend(
        [
            "",
            "## 5. 测试环境与准备",
            "",
            "1. MySQL 5.7 的 `yuezi` 库可连接，迁移版本 `V20260726_005` 至 `V20260726_009` 已应用。",
            "2. 启动 API：`npm run api:mvp`；默认地址为 `http://127.0.0.1:3000`。",
            "3. 启动前端：`npm run dev:mvp`；浏览器打开命令输出的本地地址。",
            "4. 密码由系统管理员通过安全渠道提供。不要把密码写入本文、测试截图、提交记录或缺陷单。",
            "5. 临时账号登录后若 `mustChangePassword=true`，应先完成改密；当前版本若尚无改密界面，登记为上线阻断项。",
            "6. 测试真实新增/审核流程时必须使用专用测试客户，并在验证结束后清理；批量账号测试本身不创建业务记录。",
            "",
            "## 6. 通用账号测试用例",
            "",
            "### AUTH-001 可用账号登录",
            "",
            "- 对第 4 节所有“可登录”账号逐一登录。",
            "- 预期：HTTP 200、返回 Token；`/vue-element-admin/user/info` 返回对应中文角色、门店和权限代码。",
            "- 预期：页面右上角角色名称与第 4 节一致，刷新页面后会话仍有效。",
            "",
            "### AUTH-002 禁用账号拒绝登录",
            "",
            "- 对第 4 节所有“禁用”账号尝试登录。",
            "- 预期：HTTP 401；不签发 Token；不能访问任何业务 API。",
            "",
            "### RBAC-001 菜单与按钮权限",
            "",
            "- 登录后记录实际可见菜单、页内顶部工具栏、查询按钮、行按钮和弹窗按钮。",
            "- 逐项与第 3 节的原 ERP 授权范围比对；无权限入口必须隐藏或禁用。",
            "- 直接输入无权限路由、直接请求无权限 API 时仍必须返回 403，不能只依赖前端隐藏。",
            "",
            "### SCOPE-001 门店与部门数据范围",
            "",
            "- 切换门店或传入其他门店 `storeId` 查询。",
            "- 预期：只返回第 4 节“门店范围”内数据；越权门店返回 403。",
            "- 原 ERP 部门范围快照当前全部是 `granted=0`，只能验证快照完整性，不能把部门列表解释为有效授权。",
            "- 部门级数据权限正式启用前，必须重新采集至少一个明确勾选的角色作为阳性样本，并验证未勾选部门为阴性样本。",
            "",
            "### PASSWORD-001 首次改密",
            "",
            "- 对“首次登录必须改密”的账号登录。",
            "- 预期：系统强制进入改密流程；修改成功后旧密码失效，新密码可登录。",
            "- 当前 API 已返回 `mustChangePassword` 标记；若前端仍允许跳过，应判失败。",
            "",
            "## 7. 已接入主链路测试",
            "",
            "### MVP-001 客户",
            "",
            "- 有 `CUSTOMER.VIEW`：客户列表接口返回 200。",
            "- 有 `CUSTOMER.CREATE`：可创建测试客户；无权限账号直接 POST 返回 403。",
            "",
            "### MVP-002 合同",
            "",
            "- 有 `SALES.VIEW`：合同列表接口返回 200。",
            "- 有 `SALES.CREATE`：可为测试客户新增合同。",
            "- 有 `SALES.APPROVE`：可审核待审合同；无审核权账号返回 403。",
            "",
            "### MVP-003 收款",
            "",
            "- 有 `FINANCE.VIEW`：收款列表接口返回 200。",
            "- 有 `FINANCE.CREATE`：可新增收款。",
            "- 有 `FINANCE.APPROVE`：可审核待审收款；无审核权账号返回 403。",
            "",
            "### MVP-004 订房与入住",
            "",
            "- 有 `ROOM.VIEW`：房态和订房列表接口返回 200。",
            "- 有 `ROOM.CREATE`：可创建订房。",
            "- 有 `ROOM.EXECUTE`：可办理入住；无执行权账号返回 403。",
            "",
            "### FLOW-001 主链路闭环",
            "",
            "按“客户建档 → 新增合同 → 合同审核 → 新增收款 → 收款审核 → 订房 → 入住”顺序执行。",
            "",
            "预期：每一步状态正确、操作者写入审计日志、门店范围有效、金额状态一致；测试结束后清理测试业务记录。",
            "",
            "## 8. 自动化测试命令",
            "",
            "下列环境变量必须只在当前终端或安全的密钥管理中设置，不能写进仓库：数据库密码、管理员密码、各代表账号密码和临时账号初始密码。",
            "",
            "```powershell",
            "npm run verify:legacy:access",
            "npm run test:legacy:accounts",
            "npm run verify:test:role-accounts",
            "npm run test:role-accounts",
            "npm run test:mvp:rbac",
            "python scripts/smoke-mvp.py",
            "npm run build:mvp",
            "npm run docs:test:accounts",
            "```",
            "",
            "自动化验收标准：",
            "",
            "- 58 个原 ERP 可用账号全部登录成功。",
            "- 6 个禁用账号全部返回 401。",
            f"- {len(test_accounts)} 个补充角色代表账号全部登录成功，28 个保留角色达到 28/28 账号覆盖。",
            "- 每个账号角色名称、门店范围和权限集合与 MySQL 一致。",
            "- 原数据范围快照 3538 行存在，且当前明确授权行保持为 0，不误授予部门权限。",
            "- 代表角色的允许接口返回 200，禁止接口返回 403。",
            "- 主链路全部成功，脚本清理后业务表不残留测试记录。",
            "- MVP 生产构建成功，浏览器控制台无错误。",
            "",
            "## 9. 当前限制与上线前阻断项",
            "",
            "1. 原 ERP 精确菜单/按钮授权和数据范围已经迁入，但护理、产康、月嫂、膳食、仓存、商城、审批、报表等模块仍需逐接口接入权限校验后，才能标记为“已接入”。",
            f"2. 当前有 {active_legacy_unlinked} 个可用业务账号尚未与员工花名册唯一关联；补充的 {len(test_accounts)} 个角色验收账号故意不绑定员工。业务账号在排班、绩效、服务执行人和审计责任人正式启用前必须完成匹配。",
            "3. 首次改密必须形成不可绕过的后端策略；仅返回标记但不阻断业务不满足上线要求。",
            "4. 每个页面还需按原 ERP 独立核验：顶部工具栏、查询条件、行操作、弹窗按钮和数据范围，不能用角色拥有菜单权限代替页面字段级验收。",
            "5. 测试环境不得使用真实客户、金额、医疗护理记录或生产附件。",
            "",
            "## 10. 2026-07-26 本轮实测结果",
            "",
            "| 检查项 | 实测结果 |",
            "|---|---|",
            "| 权限导入一致性 | 通过：28 个角色、64 个原账号、65 条用户角色关系、1265 个权限资源、3538 条数据范围快照均与源清单一致 |",
            "| 原账号登录 | 通过：58 个可用账号登录成功，6 个禁用账号全部被 401 拒绝，未创建业务记录 |",
            f"| 角色账号覆盖 | 通过：28/28 个保留角色均有独立测试账号；{len(test_accounts)} 个职位测试账号全部登录成功 |",
            "| 代表角色 RBAC | 通过：admin、韩新、许曼、董丽霞的可读资源、门店范围及 4 个禁止动作符合预期 |",
            "| MVP 主链路 | 通过：客户 → 合同审核 → 收款审核 → 订房 → 入住，最终状态为“已入住” |",
            "| 测试数据清理 | 通过：客户、合同、收款、订房、审计事件均为 0；仅保留 4 间基础房间 |",
            "| 生产构建 | 通过：`build --mode mvp` 编译成功 |",
            "",
            "## 11. 测试记录模板",
            "",
            "| 日期 | 构建号 | 用例 | 账号 | 角色 | 门店 | 结果 | 实际现象/HTTP状态 | 缺陷编号 | 测试人 |",
            "|---|---|---|---|---|---|---|---|---|---|",
            "|  |  |  |  |  |  | 通过/失败 |  |  |  |",
            "",
        ]
    )
    return "\n".join(lines)


def main():
    if not os.environ.get("ERP_DB_PASSWORD"):
        raise SystemExit("ERP_DB_PASSWORD is required.")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(build_document(), encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()

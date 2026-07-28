"""Read-only ERP surfaces backed by the normalized MySQL database.

These helpers deliberately return an empty list when a legacy screen has no
corresponding business rows yet.  They never manufacture demo records and
never fall back to JSON files.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any


SYSTEM_RESOURCES = {
    "department-management",
    "role-management",
    "user-management",
    "data-dictionary",
    "approval-workflow",
    "notice-announcement",
    "rebate-settings",
    "club-introduction",
    "navigation-menu",
    "mobile-navigation",
    "operation-buttons",
    "operation-log",
    "sms-send-settings",
    "birthday-sms-reminder",
    "message-send-log",
    "warning-parameter-settings",
    "custom-report-template",
    "template-settings",
    "scheduled-task",
    "system-parameter-settings",
}

BASIC_RESOURCES = {
    "employee-records",
    "basic-items",
    "material-records",
    "room-records",
    "satisfaction-survey-templates",
    "survey-management",
    "warehouse-records",
    "supplier-records",
    "fund-accounts",
    "report-templates",
    "nursing-templates",
    "task-management",
    "service-time-settings",
    "project-labor-fee-settings",
    "commission-rate-settings",
    "equipment-management",
    "performance-target-settings",
    "discount-amount-authorization",
    "bed-management",
}

NURSING_RESOURCES = {
    "nursing-center",
    "nursing-plan",
    "nursing-roster-v2",
    "baby-files",
    "health-assessments",
    "diet-assessments",
    "custom-rounds",
    "doctor-rounds",
    "diet-taboo-rounds",
    "nursing-plan-confirmations",
    "nursing-project-records",
    "mother-nursing-records",
    "baby-nursing-records",
    "mother-nursing-summary",
    "baby-nursing-summary",
    "nursing-roster",
    "check-in-handover",
}

MATERNITY_NURSE_RESOURCES = {
    "maternity-matron-archives",
    "maternity-salary-standards",
    "maternity-schedules",
    "maternity-contracts",
    "maternity-service-records",
    "maternity-dispatch-audits",
    "maternity-settlements",
    "maternity-appointments",
}

REPORT_RESOURCES = {
    "s1-sales-ranking",
    "s2-customer-brief",
    "s3-best-selling-ranking",
    "s4-dm-customer-contract-summary",
    "s5-product-consumption-summary",
    "s6-sales-statistics",
    "s7-service-sales-summary",
    "s8-card-sales-summary",
    "s9-cross-store-consumption",
    "s10-sml-daily-sales",
    "s11-gift-item-details",
    "s12-customer-cross-store-service-consumption",
    "s13-sales-performance",
    "f1-monthly-occupancy",
    "f2-room-status-overall-analysis",
    "f3-monthly-reservation-details",
    "f4-monthly-checkout-details",
    "f5-prestay-customer-purchase",
    "f6-occupancy-rate",
    "c0-daily-operation",
    "c1-member-recharge-summary",
    "c2-receipt-settlement-type-summary",
    "c3-payment-summary-analysis",
    "c4-fund-income-expense-balance",
    "c5-month-day-statistical-analysis",
    "c6-customer-receipt-tracking",
    "c7-store-income-cost-statistics",
    "c8-product-gross-profit-analysis",
    "c9-referrer-report",
    "c12-cashback-consumption-query",
    "c10-receipt-item-summary",
    "c11-service-consumption-income",
    "c13-receipt-refund-summary",
    "c14-contract-performance",
    "c15-fund-account-transactions",
    "c16-receipt-and-settlement-types",
    "h1-customer-service-records",
    "h2-baby-vital-sign-statistics",
    "h3-mother-temperature-weight-trend",
    "h4-rehab-service-work-summary",
    "wechat-customer-service-report",
    "mother-app-sharing-report",
}


def _rows(connection, sql: str, params: Any = ()) -> list[dict]:
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        return list(cursor.fetchall())


def _store_scope(user: dict, alias: str = "") -> tuple[str, list]:
    if "SYS_ADMIN" in user.get("roles", []):
        return "1=1", []
    store_ids = list(user.get("store_ids") or [])
    if not store_ids:
        return "1=0", []
    column = f"{alias}.store_id" if alias else "store_id"
    return (
        f"{column} IN ({','.join(['%s'] * len(store_ids))})",
        store_ids,
    )


def _status(value: Any) -> str:
    return "启用" if str(value or "").upper() in {
        "ACTIVE",
        "NORMAL",
        "启用",
        "正常",
        "在职",
    } else "停用"


def foundation_overview(connection, user: dict) -> dict:
    tenant_id = user["tenant_id"]
    store_clause, store_params = _store_scope(user, "s")
    stores = _rows(
        connection,
        f"""
        SELECT s.store_id AS id, s.name,
               CONCAT('STORE-', LPAD(s.store_id, 3, '0')) AS code,
               s.manager,
               COUNT(DISTINCT d.department_id) AS departments,
               COUNT(DISTINCT st.staff_id) AS employees,
               COUNT(DISTINCT room.room_id) AS rooms,
               s.status
        FROM stores s
        LEFT JOIN departments d
          ON d.store_id=s.store_id AND d.tenant_id=s.tenant_id
        LEFT JOIN staff st
          ON st.store_id=s.store_id AND st.tenant_id=s.tenant_id
         AND st.employment_status='ACTIVE'
        LEFT JOIN rooms room
          ON room.store_id=s.store_id AND room.tenant_id=s.tenant_id
         AND room.deleted_at IS NULL
        WHERE s.tenant_id=%s AND {store_clause}
        GROUP BY s.store_id
        ORDER BY s.sort_weight DESC, s.store_id
        """,
        [tenant_id, *store_params],
    )
    for row in stores:
        row["status"] = _status(row.get("status"))

    department_clause, department_params = _store_scope(user, "d")
    departments = _rows(
        connection,
        f"""
        SELECT d.department_id AS id, d.name, d.code,
               s.name AS store, manager.name AS leader,
               COUNT(st.staff_id) AS employees,
               CASE
                 WHEN d.parent_department_id IS NULL THEN '本门店'
                 ELSE '本部门'
               END AS dataScope,
               d.status
        FROM departments d
        JOIN stores s ON s.store_id=d.store_id
        LEFT JOIN staff manager ON manager.staff_id=d.manager_staff_id
        LEFT JOIN staff st
          ON st.department_id=d.department_id
         AND st.employment_status='ACTIVE'
        WHERE d.tenant_id=%s AND {department_clause}
        GROUP BY d.department_id
        ORDER BY d.store_id, d.sort_order, d.department_id
        """,
        [tenant_id, *department_params],
    )
    for row in departments:
        row["status"] = _status(row.get("status"))

    roles = _rows(
        connection,
        """
        SELECT r.role_id AS id, r.name, r.code,
               COUNT(DISTINCT ur.user_id) AS users,
               CASE r.data_scope
                 WHEN 1 THEN '全部数据'
                 WHEN 2 THEN '本门店'
                 WHEN 3 THEN '本部门'
                 ELSE '本人数据'
               END AS dataScope,
               COUNT(DISTINCT rp.permission_id) AS menus,
               r.status
        FROM roles r
        LEFT JOIN user_roles ur
          ON ur.role_id=r.role_id
         AND ur.effective_from<=NOW()
         AND (ur.effective_to IS NULL OR ur.effective_to>NOW())
        LEFT JOIN role_permissions rp
          ON rp.role_id=r.role_id AND rp.effect='ALLOW'
        WHERE r.tenant_id=%s
        GROUP BY r.role_id
        ORDER BY r.is_system DESC, r.data_scope, r.role_id
        """,
        (tenant_id,),
    )
    for row in roles:
        row["status"] = _status(row.get("status"))

    if "SYS_ADMIN" in user.get("roles", []):
        user_clause, user_params = "1=1", []
    else:
        user_store_ids = list(user.get("store_ids") or [])
        user_clause = (
            f"ua.default_store_id IN ({','.join(['%s'] * len(user_store_ids))})"
            if user_store_ids
            else "1=0"
        )
        user_params = user_store_ids
    users = _rows(
        connection,
        f"""
        SELECT ua.user_id AS id, ua.username,
               COALESCE(st.name, ua.username) AS name,
               st.phone AS mobile, s.name AS store,
               COALESCE(d.name, st.department) AS department,
               GROUP_CONCAT(DISTINCT r.name ORDER BY r.name SEPARATOR '、') AS role,
               ua.last_login_at AS lastLogin,
               ua.status
        FROM user_accounts ua
        LEFT JOIN staff st ON st.staff_id=ua.staff_id
        LEFT JOIN departments d ON d.department_id=ua.department_id
        LEFT JOIN stores s ON s.store_id=ua.default_store_id
        LEFT JOIN user_roles ur
          ON ur.user_id=ua.user_id
         AND ur.effective_from<=NOW()
         AND (ur.effective_to IS NULL OR ur.effective_to>NOW())
        LEFT JOIN roles r ON r.role_id=ur.role_id
        WHERE ua.tenant_id=%s AND {user_clause}
        GROUP BY ua.user_id
        ORDER BY ua.user_id
        """,
        [tenant_id, *user_params],
    )
    for row in users:
        row["status"] = _status(row.get("status"))

    dictionary_types = _rows(
        connection,
        """
        SELECT dt.dictionary_type_id AS id, dt.name, dt.code,
               COUNT(di.dictionary_item_id) AS items,
               1 AS builtIn
        FROM sys_dictionary_types dt
        LEFT JOIN sys_dictionary_items di
          ON di.dictionary_type_id=dt.dictionary_type_id
        WHERE dt.tenant_id=%s
        GROUP BY dt.dictionary_type_id
        ORDER BY dt.sort_order, dt.dictionary_type_id
        """,
        (tenant_id,),
    )
    dictionary_rows = _rows(
        connection,
        """
        SELECT dt.code AS typeCode, di.dictionary_item_id AS id,
               di.name AS label, COALESCE(di.code, di.name) AS value,
               di.sort_order AS sort,
               COALESCE(di.ext_value_1, '#b18a47') AS color,
               di.status
        FROM sys_dictionary_items di
        JOIN sys_dictionary_types dt
          ON dt.dictionary_type_id=di.dictionary_type_id
        WHERE dt.tenant_id=%s
        ORDER BY dt.sort_order, di.sort_order, di.dictionary_item_id
        """,
        (tenant_id,),
    )
    dictionary_items: dict[str, list] = defaultdict(list)
    for row in dictionary_rows:
        type_code = row.pop("typeCode")
        row["status"] = _status(row.get("status"))
        dictionary_items[type_code].append(row)

    permission_rows = _rows(
        connection,
        """
        SELECT module_code AS module,
               MAX(action_code IN ('VIEW','QUERY')) AS `view`,
               MAX(action_code IN ('CREATE','ADD')) AS `create`,
               MAX(action_code IN ('EDIT','UPDATE')) AS `edit`,
               MAX(action_code IN ('APPROVE','AUDIT')) AS `approve`,
               MAX(action_code='EXPORT') AS `export`,
               '按角色字段权限控制' AS `sensitive`
        FROM permissions
        WHERE status='ACTIVE'
        GROUP BY module_code
        ORDER BY module_code
        """,
    )
    return {
        "stores": stores,
        "departments": departments,
        "roles": roles,
        "users": users,
        "dictionaryTypes": dictionary_types,
        "dictionaryItems": dict(dictionary_items),
        "permissions": permission_rows,
        "source": "mysql",
    }


def system_module(connection, user: dict, resource: str) -> dict:
    tenant_id = user["tenant_id"]
    if resource not in SYSTEM_RESOURCES:
        raise KeyError(resource)

    if resource == "department-management":
        clause, params = _store_scope(user, "d")
        rows = _rows(
            connection,
            f"""
            SELECT d.department_id AS id, d.code AS departmentCode,
                   d.name AS departmentName, parent.name AS parentDepartment,
                   s.name AS store, manager.name AS manager,
                   d.sort_order AS sortOrder, d.status
            FROM departments d
            JOIN stores s ON s.store_id=d.store_id
            LEFT JOIN departments parent
              ON parent.department_id=d.parent_department_id
            LEFT JOIN staff manager ON manager.staff_id=d.manager_staff_id
            WHERE d.tenant_id=%s AND {clause}
            ORDER BY d.store_id, d.sort_order, d.department_id
            """,
            [tenant_id, *params],
        )
    elif resource == "role-management":
        rows = _rows(
            connection,
            """
            SELECT r.role_id AS id, r.code AS roleCode, r.name AS roleName,
                   CASE r.data_scope
                     WHEN 1 THEN '全部数据'
                     WHEN 2 THEN '本门店'
                     WHEN 3 THEN '本部门'
                     ELSE '本人数据'
                   END AS dataScope,
                   COUNT(DISTINCT ur.user_id) AS userCount,
                   r.updated_at AS updatedAt, r.status
            FROM roles r
            LEFT JOIN user_roles ur
              ON ur.role_id=r.role_id
             AND ur.effective_from<=NOW()
             AND (ur.effective_to IS NULL OR ur.effective_to>NOW())
            WHERE r.tenant_id=%s
            GROUP BY r.role_id
            ORDER BY r.is_system DESC, r.data_scope, r.role_id
            """,
            (tenant_id,),
        )
    elif resource == "user-management":
        if "SYS_ADMIN" in user.get("roles", []):
            clause, params = "1=1", []
        else:
            user_store_ids = list(user.get("store_ids") or [])
            clause = (
                "ua.default_store_id IN "
                f"({','.join(['%s'] * len(user_store_ids))})"
                if user_store_ids
                else "1=0"
            )
            params = user_store_ids
        rows = _rows(
            connection,
            f"""
            SELECT ua.user_id AS id, ua.username AS account,
                   COALESCE(st.name, ua.username) AS displayName,
                   st.phone AS mobile, s.name AS store,
                   COALESCE(d.name, st.department) AS department,
                   GROUP_CONCAT(DISTINCT r.name ORDER BY r.name SEPARATOR '、')
                     AS roles,
                   ua.last_login_at AS lastLoginAt,
                   ua.status AS accountStatus
            FROM user_accounts ua
            LEFT JOIN staff st ON st.staff_id=ua.staff_id
            LEFT JOIN stores s ON s.store_id=ua.default_store_id
            LEFT JOIN departments d ON d.department_id=ua.department_id
            LEFT JOIN user_roles ur
              ON ur.user_id=ua.user_id
             AND ur.effective_from<=NOW()
             AND (ur.effective_to IS NULL OR ur.effective_to>NOW())
            LEFT JOIN roles r ON r.role_id=ur.role_id
            WHERE ua.tenant_id=%s AND {clause}
            GROUP BY ua.user_id
            ORDER BY ua.user_id
            """,
            [tenant_id, *params],
        )
        for row in rows:
            row["accountStatus"] = _status(row.get("accountStatus"))
        return {"list": rows, "total": len(rows), "source": "mysql"}
    elif resource == "data-dictionary":
        rows = _rows(
            connection,
            """
            SELECT di.dictionary_item_id AS id, dt.code AS dictionaryCode,
                   dt.name AS dictionaryName,
                   COALESCE(di.code, di.name) AS itemValue,
                   di.name AS itemLabel, di.sort_order AS sortOrder,
                   di.updated_at AS updatedAt, di.status
            FROM sys_dictionary_items di
            JOIN sys_dictionary_types dt
              ON dt.dictionary_type_id=di.dictionary_type_id
            WHERE dt.tenant_id=%s
            ORDER BY dt.sort_order, di.sort_order, di.dictionary_item_id
            """,
            (tenant_id,),
        )
    elif resource == "approval-workflow":
        rows = _rows(
            connection,
            """
            SELECT MIN(p.approval_process_id) AS id,
                   COALESCE(p.code, CONCAT('WF-', c.legacy_category_id))
                     AS workflowCode,
                   c.name AS workflowName, c.name AS businessType,
                   COUNT(p.approval_process_id) AS nodeCount,
                   GROUP_CONCAT(DISTINCT p.role_name ORDER BY p.sequence_no
                     SEPARATOR ' → ') AS applicableScope,
                   MAX(p.status) AS status
            FROM sys_approval_categories c
            LEFT JOIN sys_approval_processes p
              ON p.approval_category_id=c.approval_category_id
            WHERE c.tenant_id=%s
            GROUP BY c.approval_category_id
            ORDER BY c.approval_category_id
            """,
            (tenant_id,),
        )
    elif resource in {"navigation-menu", "mobile-navigation"}:
        surface = "WEB" if resource == "navigation-menu" else "APP"
        rows = _rows(
            connection,
            """
            SELECT child.menu_id AS id,
                   CONCAT(%s, '-', child.legacy_menu_id) AS menuCode,
                   child.title AS menuName, parent.title AS parentMenu,
                   child.link_url AS routePath, child.icon_class AS icon,
                   child.sort_order AS sortOrder,
                   IF(child.is_visible=1, 'ACTIVE', 'INACTIVE') AS status
            FROM sys_legacy_menus child
            LEFT JOIN sys_legacy_menus parent
              ON parent.menu_id=child.parent_menu_id
            WHERE child.tenant_id=%s AND child.surface=%s
            ORDER BY child.sort_order, child.menu_id
            """,
            (surface, tenant_id, surface),
        )
        if resource == "mobile-navigation":
            for row in rows:
                row.update(
                    {
                        "navigationCode": row.pop("menuCode"),
                        "navigationName": row.pop("menuName"),
                        "parentNavigation": row.pop("parentMenu"),
                        "clientType": "APP",
                        "target": row.pop("routePath"),
                    }
                )
    elif resource == "operation-buttons":
        rows = _rows(
            connection,
            """
            SELECT button_id AS id,
                   CONCAT('BTN-', legacy_button_id) AS buttonCode,
                   name AS buttonName,
                   COALESCE(button_tag, CONCAT('LEGACY.BUTTON.',
                     legacy_button_id)) AS permissionCode,
                   '' AS menu, '按钮' AS buttonType,
                   sort_order AS sortOrder, 'ACTIVE' AS status
            FROM sys_legacy_buttons
            WHERE tenant_id=%s
            ORDER BY sort_order, button_id
            """,
            (tenant_id,),
        )
    elif resource == "operation-log":
        clause, params = _store_scope(user, "event")
        rows = _rows(
            connection,
            f"""
            SELECT event.event_id AS id,
                   COALESCE(st.name, ua.username) AS operator,
                   ua.username AS account,
                   event.aggregate_type AS module,
                   event.action_code AS operationType,
                   CONCAT(event.aggregate_type, '#', event.aggregate_id,
                     ' ', event.action_code) AS operationContent,
                   event.created_at AS operationAt,
                   '成功' AS result
            FROM mvp_audit_events event
            JOIN user_accounts ua ON ua.user_id=event.actor_user_id
            LEFT JOIN staff st ON st.staff_id=ua.staff_id
            WHERE event.tenant_id=%s AND {clause}
            ORDER BY event.event_id DESC
            LIMIT 1000
            """,
            [tenant_id, *params],
        )
        return {"list": rows, "total": len(rows), "source": "mysql"}
    elif resource == "sms-send-settings":
        rows = _rows(
            connection,
            """
            SELECT n.sms_node_id AS id, n.node_name AS configName,
                   '旧ERP短信节点' AS channelType,
                   n.node_code AS smsSignature,
                   '系统配置' AS provider,
                   COUNT(r.legacy_user_id) AS sender,
                   n.status
            FROM sys_sms_nodes n
            LEFT JOIN sys_sms_recipients r ON r.sms_node_id=n.sms_node_id
            WHERE n.tenant_id=%s
            GROUP BY n.sms_node_id
            ORDER BY n.sort_order, n.sms_node_id
            """,
            (tenant_id,),
        )
    elif resource == "warning-parameter-settings":
        rows = _rows(
            connection,
            """
            SELECT warning_parameter_id AS id,
                   CONCAT('WARN-', legacy_warning_id) AS warningCode,
                   warning_name AS warningName,
                   threshold_value AS warningValue,
                   remark, updated_at AS updatedAt,
                   'ACTIVE' AS status
            FROM sys_warning_parameters
            WHERE tenant_id=%s
            ORDER BY warning_parameter_id
            """,
            (tenant_id,),
        )
    elif resource == "custom-report-template":
        rows = _rows(
            connection,
            """
            SELECT report_template_id AS id,
                   CONCAT('REPORT-', legacy_template_id) AS templateCode,
                   title AS templateName, type_name AS businessType,
                   memo AS templateFormat, creator_name AS updatedBy,
                   legacy_created_at AS updatedAt,
                   'ACTIVE' AS status
            FROM sys_report_templates
            WHERE tenant_id=%s
            ORDER BY sort_order, report_template_id
            """,
            (tenant_id,),
        )
    elif resource == "template-settings":
        rows = _rows(
            connection,
            """
            SELECT message_template_id AS id, template_code AS templateCode,
                   template_name AS templateName, type_name AS templateType,
                   external_template_id AS externalTemplateId,
                   explanation, remark, 'ACTIVE' AS status
            FROM sys_message_templates
            WHERE tenant_id=%s
            ORDER BY message_template_id
            """,
            (tenant_id,),
        )
    elif resource == "scheduled-task":
        rows = _rows(
            connection,
            """
            SELECT plan_task_id AS id, task_code AS taskCode,
                   task_title AS taskName, start_time AS startAt,
                   end_time AS endAt, interval_days AS intervalDays,
                   recipient_type AS recipientType, status
            FROM sys_plan_tasks
            WHERE tenant_id=%s
            ORDER BY plan_task_id
            """,
            (tenant_id,),
        )
    elif resource == "system-parameter-settings":
        rows = _rows(
            connection,
            """
            SELECT parameter_id AS id, parameter_code AS parameterCode,
                   parameter_type AS parameterType,
                   parameter_value AS parameterValue,
                   parameter_level AS parameterLevel,
                   remark, updated_at AS updatedAt,
                   'ACTIVE' AS status
            FROM sys_parameters
            WHERE tenant_id=%s
            ORDER BY parameter_type, parameter_id
            """,
            (tenant_id,),
        )
    elif resource == "rebate-settings":
        rows = _rows(
            connection,
            """
            SELECT c.rebate_category_setting_id AS id,
                   c.category_code AS ruleCode, c.category_name AS ruleName,
                   p.rebate_mode AS rebateType, '全部门店' AS applicableScope,
                   c.calculation_mode AS calculationRule,
                   c.rebate_value AS rebateValue,
                   IF(c.enabled=1, 'ACTIVE', 'INACTIVE') AS status
            FROM sys_rebate_category_settings c
            JOIN sys_rebate_profiles p
              ON p.rebate_profile_id=c.rebate_profile_id
            WHERE p.tenant_id=%s
            ORDER BY c.rebate_category_setting_id
            """,
            (tenant_id,),
        )
    elif resource == "club-introduction":
        clause, params = _store_scope(user, "profile")
        rows = _rows(
            connection,
            f"""
            SELECT profile.club_profile_id AS id, s.name AS store,
                   profile.club_name AS title, profile.image_path AS cover,
                   profile.updated_at AS updatedAt,
                   'ACTIVE' AS publishStatus
            FROM sys_club_profiles profile
            LEFT JOIN stores s ON s.store_id=profile.store_id
            WHERE profile.tenant_id=%s
              AND (profile.store_id IS NULL OR {clause})
            ORDER BY profile.club_profile_id
            """,
            [tenant_id, *params],
        )
        return {"list": rows, "total": len(rows), "source": "mysql"}
    elif resource == "message-send-log":
        clause, params = _store_scope(user, "sms")
        rows = _rows(
            connection,
            f"""
            SELECT sms.sms_id AS id, sms.scene AS messageType,
                   sms.recipients AS recipient, sms.content AS messageTitle,
                   sms.status AS sendStatus, sms.created_at AS sendAt
            FROM sms_records sms
            WHERE sms.tenant_id=%s AND sms.deleted_at IS NULL
              AND {clause}
            ORDER BY sms.sms_id DESC
            LIMIT 1000
            """,
            [tenant_id, *params],
        )
        return {"list": rows, "total": len(rows), "source": "mysql"}
    else:
        # Notice bodies and birthday-recipient rows were intentionally not
        # imported, so their honest result is an empty MySQL-backed set.
        rows = []

    for row in rows:
        if "status" in row:
            row["status"] = _status(row.get("status"))
    return {"list": rows, "total": len(rows), "source": "mysql"}


def basic_module(connection, user: dict, resource: str) -> dict:
    if resource not in BASIC_RESOURCES:
        raise KeyError(resource)
    tenant_id = user["tenant_id"]
    rows: list[dict]
    if resource == "employee-records":
        clause, params = _store_scope(user, "st")
        rows = _rows(
            connection,
            f"""
            SELECT st.staff_id AS id, st.employee_no AS employeeNo,
                   st.name AS employeeName, st.gender,
                   s.name AS store,
                   COALESCE(d.name, st.department) AS department,
                   COALESCE(p.name, st.position) AS position,
                   st.phone AS mobile, st.hire_date AS hireDate,
                   st.employment_status AS status
            FROM staff st
            LEFT JOIN stores s ON s.store_id=st.store_id
            LEFT JOIN departments d ON d.department_id=st.department_id
            LEFT JOIN positions p ON p.position_id=st.position_id
            WHERE st.tenant_id=%s AND {clause}
            ORDER BY st.store_id, st.department_id, st.staff_id
            """,
            [tenant_id, *params],
        )
    elif resource in {"basic-items", "material-records"}:
        domain_filter = (
            "AND i.domain IN ('SERVICE','服务','产康','护理')"
            if resource == "basic-items"
            else "AND i.domain NOT IN ('SERVICE','服务','产康','护理')"
        )
        rows = _rows(
            connection,
            f"""
            SELECT i.item_id AS id,
                   CONCAT('ITEM-', LPAD(i.item_id, 6, '0')) AS itemCode,
                   i.name AS itemName, i.cat AS category,
                   i.unit, i.sale_price AS salePrice,
                   i.cost_price AS referenceCost, i.duration,
                   i.status
            FROM items i
            WHERE i.tenant_id=%s {domain_filter}
            ORDER BY i.item_id
            """,
            (tenant_id,),
        )
    elif resource == "room-records":
        clause, params = _store_scope(user, "room")
        rows = _rows(
            connection,
            f"""
            SELECT room.room_id AS id, room.room_no AS roomNo,
                   s.name AS store, room.floor,
                   COALESCE(rt.name, room.room_type) AS roomType,
                   rt.layout_name AS roomStyle,
                   room.direction AS orientation,
                   room.status AS roomStatus
            FROM rooms room
            JOIN stores s ON s.store_id=room.store_id
            LEFT JOIN room_types rt ON rt.room_type_id=room.room_type_id
            WHERE room.tenant_id=%s AND room.deleted_at IS NULL
              AND {clause}
            ORDER BY room.store_id, room.floor, room.layout_order, room.room_no
            """,
            [tenant_id, *params],
        )
        return {"list": rows, "total": len(rows), "source": "mysql"}
    elif resource == "supplier-records":
        rows = _rows(
            connection,
            """
            SELECT supplier_id AS id,
                   CONCAT('SUP-', LPAD(supplier_id, 6, '0')) AS supplierCode,
                   name AS supplierName, contact AS contactName,
                   phone AS contactPhone, address, status AS cooperationStatus
            FROM suppliers
            WHERE tenant_id=%s AND deleted_at IS NULL
            ORDER BY supplier_id
            """,
            (tenant_id,),
        )
        return {"list": rows, "total": len(rows), "source": "mysql"}
    elif resource == "report-templates":
        rows = _rows(
            connection,
            """
            SELECT report_template_id AS id,
                   CONCAT('REPORT-', legacy_template_id) AS templateCode,
                   title AS templateName, type_name AS businessType,
                   memo AS templateFormat, creator_name AS updatedBy,
                   legacy_created_at AS updatedAt,
                   'ACTIVE' AS status
            FROM sys_report_templates
            WHERE tenant_id=%s
            ORDER BY sort_order, report_template_id
            """,
            (tenant_id,),
        )
    else:
        rows = []
    for row in rows:
        if "status" in row:
            row["status"] = _status(row.get("status"))
    return {"list": rows, "total": len(rows), "source": "mysql"}


def nursing_module(connection, user: dict, resource: str) -> dict:
    if resource not in NURSING_RESOURCES:
        raise KeyError(resource)
    tenant_id = user["tenant_id"]
    clause, params = _store_scope(user, "c")
    rows: list[dict] = []
    if resource == "nursing-center":
        rows = _rows(
            connection,
            f"""
            SELECT c.customer_id AS id, c.name AS customerName,
                   room.room_no AS room, s.name AS store,
                   c.status AS customerStatus,
                   COUNT(DISTINCT baby.baby_id) AS babyCount,
                   0 AS pendingServices, 0 AS completedServices
            FROM customers c
            JOIN stores s ON s.store_id=c.store_id
            LEFT JOIN room_bookings booking
              ON booking.customer_id=c.customer_id
             AND booking.tenant_id=c.tenant_id
             AND booking.deleted_at IS NULL
             AND booking.status IN ('已订房','已入住')
            LEFT JOIN rooms room ON room.room_id=booking.room_id
            LEFT JOIN babies baby
              ON baby.customer_id=c.customer_id
             AND baby.tenant_id=c.tenant_id
             AND baby.deleted_at IS NULL
            WHERE c.tenant_id=%s AND c.deleted_at IS NULL AND {clause}
            GROUP BY c.customer_id
            ORDER BY room.floor, room.room_no, c.customer_id
            """,
            [tenant_id, *params],
        )
    elif resource == "baby-files":
        baby_clause, baby_params = _store_scope(user, "baby")
        rows = _rows(
            connection,
            f"""
            SELECT baby.baby_id AS id, baby.name AS babyName,
                   baby.gender, baby.birth_date AS birthDate,
                   baby.birth_weight AS birthWeight,
                   c.name AS motherName, c.status AS customerStatus,
                   room.room_no AS room, s.name AS store,
                   baby.note AS remark
            FROM babies baby
            JOIN customers c ON c.customer_id=baby.customer_id
            LEFT JOIN stores s ON s.store_id=baby.store_id
            LEFT JOIN room_bookings booking
              ON booking.customer_id=c.customer_id
             AND booking.deleted_at IS NULL
             AND booking.status IN ('已订房','已入住')
            LEFT JOIN rooms room ON room.room_id=booking.room_id
            WHERE baby.tenant_id=%s AND baby.deleted_at IS NULL
              AND {baby_clause}
            ORDER BY baby.baby_id DESC
            """,
            [tenant_id, *baby_params],
        )
    elif resource in {"baby-nursing-records", "baby-nursing-summary"}:
        baby_clause, baby_params = _store_scope(user, "baby")
        if resource == "baby-nursing-records":
            rows = _rows(
                connection,
                f"""
                SELECT log.log_id AS id, baby.name AS babyName,
                       c.name AS motherName, log.kind AS recordType,
                       log.feed_type AS feedType, log.amount,
                       log.diaper_type AS diaperType,
                       log.metric, log.metric_value AS metricValue,
                       log.care_type AS careType, log.duration_min AS duration,
                       log.log_time AS recordAt, operator.name AS recorder,
                       log.note AS remark
                FROM baby_logs log
                JOIN babies baby ON baby.baby_id=log.baby_id
                JOIN customers c ON c.customer_id=baby.customer_id
                LEFT JOIN staff operator ON operator.staff_id=log.operator_id
                WHERE log.tenant_id=%s AND {baby_clause}
                ORDER BY log.log_id DESC
                LIMIT 1000
                """,
                [tenant_id, *baby_params],
            )
        else:
            rows = _rows(
                connection,
                f"""
                SELECT MIN(log.log_id) AS id, baby.name AS babyName,
                       c.name AS motherName, log.kind AS recordType,
                       COUNT(*) AS recordCount,
                       MAX(log.log_time) AS latestRecordAt
                FROM baby_logs log
                JOIN babies baby ON baby.baby_id=log.baby_id
                JOIN customers c ON c.customer_id=baby.customer_id
                WHERE log.tenant_id=%s AND {baby_clause}
                GROUP BY baby.baby_id, log.kind
                ORDER BY latestRecordAt DESC
                """,
                [tenant_id, *baby_params],
            )
    elif resource in {"health-assessments", "diet-assessments"}:
        profile_clause, profile_params = _store_scope(user, "profile")
        domain = "膳食" if resource == "diet-assessments" else "月子"
        rows = _rows(
            connection,
            f"""
            SELECT profile.profile_id AS id, c.name AS customerName,
                   room.room_no AS room, s.name AS store,
                   profile.domain AS assessmentType,
                   profile.assess_stage AS assessmentStage,
                   profile.height, profile.weight, profile.blood_type AS bloodType,
                   profile.past_history AS pastHistory,
                   profile.allergy, profile.notes AS assessmentResult,
                   profile.created_by AS assessor,
                   profile.created_at AS assessedAt
            FROM health_profiles profile
            JOIN customers c ON c.customer_id=profile.customer_id
            LEFT JOIN stores s ON s.store_id=profile.store_id
            LEFT JOIN room_bookings booking
              ON booking.customer_id=c.customer_id
             AND booking.deleted_at IS NULL
             AND booking.status IN ('已订房','已入住')
            LEFT JOIN rooms room ON room.room_id=booking.room_id
            WHERE profile.tenant_id=%s AND profile.deleted_at IS NULL
              AND profile.domain=%s AND {profile_clause}
            ORDER BY profile.profile_id DESC
            """,
            [tenant_id, domain, *profile_params],
        )
    elif resource == "check-in-handover":
        handover_clause, handover_params = _store_scope(user, "handover")
        rows = _rows(
            connection,
            f"""
            SELECT handover.handover_id AS id, c.name AS customerName,
                   room.room_no AS room, s.name AS store,
                   handover.kind AS handoverType,
                   handover.operator, handover.status AS receiveStatus,
                   handover.time AS handoverAt
            FROM handovers handover
            LEFT JOIN customers c ON c.customer_id=handover.customer_id
            LEFT JOIN stores s ON s.store_id=handover.store_id
            LEFT JOIN room_bookings booking
              ON booking.customer_id=c.customer_id
             AND booking.deleted_at IS NULL
             AND booking.status IN ('已订房','已入住')
            LEFT JOIN rooms room ON room.room_id=booking.room_id
            WHERE handover.tenant_id=%s AND handover.deleted_at IS NULL
              AND {handover_clause}
            ORDER BY handover.handover_id DESC
            """,
            [tenant_id, *handover_params],
        )
    return {"list": rows, "total": len(rows), "source": "mysql"}


def maternity_nurse_module(connection, user: dict, resource: str) -> dict:
    if resource not in MATERNITY_NURSE_RESOURCES:
        raise KeyError(resource)
    rows: list[dict] = []
    if resource == "maternity-matron-archives":
        clause, params = _store_scope(user, "st")
        rows = _rows(
            connection,
            f"""
            SELECT st.staff_id AS id, st.employee_no AS number,
                   st.name, st.phone, s.name AS store,
                   COALESCE(p.name, st.position) AS practiceType,
                   st.education, st.gender AS sex,
                   st.birth_date AS birthDate, st.hire_date AS entryDate,
                   st.employment_status AS jobStatus
            FROM staff st
            LEFT JOIN stores s ON s.store_id=st.store_id
            LEFT JOIN positions p ON p.position_id=st.position_id
            WHERE st.tenant_id=%s AND {clause}
              AND (
                st.position LIKE '%%月嫂%%'
                OR st.role LIKE '%%月嫂%%'
                OR p.name LIKE '%%月嫂%%'
              )
            ORDER BY st.store_id, st.staff_id
            """,
            [user["tenant_id"], *params],
        )
    return {"list": rows, "total": len(rows), "source": "mysql"}


def risk_module(connection, user: dict, resource: str) -> dict:
    if resource != "yuexi-risk":
        raise KeyError(resource)
    clause, params = _store_scope(user, "event")
    rows = _rows(
        connection,
        f"""
        SELECT event.event_id AS id,
               event.aggregate_type AS eventType,
               event.aggregate_id AS businessId,
               event.action_code AS action,
               event.before_status AS beforeStatus,
               event.after_status AS afterStatus,
               ua.username AS operator,
               event.created_at AS occurredAt
        FROM mvp_audit_events event
        JOIN user_accounts ua ON ua.user_id=event.actor_user_id
        WHERE event.tenant_id=%s AND {clause}
        ORDER BY event.event_id DESC
        LIMIT 1000
        """,
        [user["tenant_id"], *params],
    )
    return {
        "list": rows,
        "total": len(rows),
        "source": "mysql",
        "evidenceLevel": "MySQL业务审计事件",
    }


def mama_box_overview(connection, user: dict) -> dict:
    """Return the 妈妈端 management overview from real MySQL tables."""
    tenant_id = user["tenant_id"]
    item_rows = _rows(
        connection,
        """
        SELECT item_id AS id,
               CONCAT('ITEM-', LPAD(item_id, 6, '0')) AS code,
               name, domain, cat AS category, unit,
               cost_price AS costPrice, exp_price AS originalPrice,
               sale_price AS salePrice, member_bonus AS pointPrice,
               status
        FROM items
        WHERE tenant_id=%s
        ORDER BY item_id
        """,
        (tenant_id,),
    )
    service_domains = {
        "SERVICE",
        "RECOVERY",
        "NURSING",
        "产康",
        "护理",
        "服务",
    }
    products = []
    projects = []
    for row in item_rows:
        row["store"] = "全部门店"
        row["integral"] = "是" if row.get("pointPrice") else "否"
        row["recommended"] = "否"
        row["status"] = (
            "已上架"
            if str(row.get("status") or "").upper()
            in {"ACTIVE", "NORMAL", "启用", "正常", "已上架"}
            else "已下架"
        )
        if str(row.get("domain") or "").upper() in service_domains:
            row["inStore"] = "是"
            projects.append(row)
        else:
            row["spec"] = ""
            products.append(row)

    order_clause, order_params = _store_scope(user, "orders")
    orders = _rows(
        connection,
        f"""
        SELECT orders.order_no AS id, orders.order_no AS code,
               orders.domain AS type, orders.pay_method AS payMethod,
               orders.order_amount AS amount,
               GREATEST(
                 COALESCE(orders.order_amount,0)
                 - COALESCE(orders.paid_amount,0)
                 - COALESCE(orders.due_amount,0),
                 0
               ) AS coupon,
               orders.due_amount AS debt, orders.created_at AS orderedAt,
               s.name AS store, customer.name AS customer,
               customer.phone AS mobile, '门店自提' AS pickup,
               CASE
                 WHEN COALESCE(orders.paid_amount,0)<=0 THEN '未支付'
                 WHEN COALESCE(orders.due_amount,0)>0 THEN '部分支付'
                 ELSE '已支付'
               END AS payStatus,
               CASE
                 WHEN ext.outbound_no IS NULL OR ext.outbound_no=''
                   THEN '待出库'
                 ELSE '已出库'
               END AS stockStatus,
               orders.order_status AS status
        FROM orders
        LEFT JOIN stores s ON s.store_id=orders.store_id
        LEFT JOIN customers customer
          ON customer.customer_id=orders.customer_id
        LEFT JOIN sales_order_extensions ext
          ON ext.order_no=orders.order_no
        WHERE orders.tenant_id=%s AND orders.deleted_at IS NULL
          AND {order_clause}
        ORDER BY orders.created_at DESC
        LIMIT 1000
        """,
        [tenant_id, *order_params],
    )

    staff_clause, staff_params = _store_scope(user, "staff")
    matrons = _rows(
        connection,
        f"""
        SELECT staff.staff_id AS id, staff.employee_no AS code,
               staff.name, s.name AS store,
               TIMESTAMPDIFF(YEAR,staff.birth_date,CURDATE()) AS age,
               staff.phone AS mobile,
               COALESCE(position.name,staff.position) AS jobType,
               COALESCE(position.name,staff.position) AS level,
               0 AS standardFee,
               CASE
                 WHEN staff.employment_status='ACTIVE' THEN '可预约'
                 ELSE '停用'
               END AS serviceStatus,
               CASE
                 WHEN staff.employment_status='ACTIVE' THEN '启用'
                 ELSE '停用'
               END AS status
        FROM staff
        LEFT JOIN positions position
          ON position.position_id=staff.position_id
        LEFT JOIN stores s ON s.store_id=staff.store_id
        WHERE staff.tenant_id=%s AND {staff_clause}
          AND (
            staff.position LIKE '%%月嫂%%'
            OR staff.role LIKE '%%月嫂%%'
            OR position.name LIKE '%%月嫂%%'
          )
        ORDER BY staff.store_id, staff.staff_id
        """,
        [tenant_id, *staff_params],
    )

    categories = _rows(
        connection,
        """
        SELECT MIN(item_id) AS id,
               COALESCE(cat,'未分类') AS name,
               CASE
                 WHEN UPPER(COALESCE(domain,'')) IN
                   ('SERVICE','RECOVERY','NURSING') THEN '服务项目'
                 ELSE '商城商品'
               END AS parent,
               COUNT(*) AS products,
               '启用' AS status
        FROM items
        WHERE tenant_id=%s
        GROUP BY COALESCE(cat,'未分类'),
                 CASE
                   WHEN UPPER(COALESCE(domain,'')) IN
                     ('SERVICE','RECOVERY','NURSING') THEN '服务项目'
                   ELSE '商城商品'
                 END
        ORDER BY parent, name
        """,
        (tenant_id,),
    )
    return {
        "products": products,
        "orders": orders,
        "projects": projects,
        "matrons": matrons,
        "categories": categories,
        "parenting": [],
        "questions": [],
        "reviews": [],
        "community": [],
        "content": [],
        "comments": [],
        "classes": [],
        "schedule": {"start": "", "end": "", "days": [], "rows": []},
        "source": "mysql",
    }


def report_module(connection, user: dict, resource: str) -> dict:
    if resource not in REPORT_RESOURCES:
        raise KeyError(resource)
    tenant_id = user["tenant_id"]
    rows: list[dict] = []

    if resource in {"s1-sales-ranking", "s13-sales-performance"}:
        clause, params = _store_scope(user, "contract")
        rows = _rows(
            connection,
            f"""
            SELECT COALESCE(st.name, ua.username, '未分配') AS salesperson,
                   COALESCE(st.department, '未分配') AS department,
                   COUNT(contract.contract_id) AS contractCount,
                   COALESCE(SUM(contract.amount),0) AS contractAmount,
                   COALESCE(SUM(contract.paid),0) AS receivedAmount
            FROM contracts contract
            LEFT JOIN user_accounts ua
              ON ua.user_id=contract.created_by_user_id
            LEFT JOIN staff st ON st.staff_id=ua.staff_id
            WHERE contract.tenant_id=%s AND contract.deleted_at IS NULL
              AND {clause}
            GROUP BY COALESCE(st.name, ua.username, '未分配'),
                     COALESCE(st.department, '未分配')
            ORDER BY contractAmount DESC
            """,
            [tenant_id, *params],
        )
        for index, row in enumerate(rows, 1):
            row["rank"] = index
            if resource == "s13-sales-performance":
                row["contractAmount"] = row.get("contractAmount", 0)
                row["totalAmount"] = row.get("contractAmount", 0)
    elif resource == "s2-customer-brief":
        clause, params = _store_scope(user, "customer")
        rows = _rows(
            connection,
            f"""
            SELECT DATE(customer.created_at) AS statDate, s.name AS store,
                   COUNT(customer.customer_id) AS newCustomerCount,
                   SUM(customer.status IN ('同意签合同','已签合同但未入住',
                     '已签合同但未审核','已订房','已入住')) AS signedCount,
                   SUM(customer.status='已入住') AS checkInCount,
                   0 AS visitCount
            FROM customers customer
            JOIN stores s ON s.store_id=customer.store_id
            WHERE customer.tenant_id=%s AND customer.deleted_at IS NULL
              AND {clause}
            GROUP BY DATE(customer.created_at), customer.store_id
            ORDER BY statDate DESC, customer.store_id
            """,
            [tenant_id, *params],
        )
    elif resource in {
        "s4-dm-customer-contract-summary",
        "c6-customer-receipt-tracking",
    }:
        clause, params = _store_scope(user, "contract")
        rows = _rows(
            connection,
            f"""
            SELECT contract.contract_no AS contractNo,
                   customer.name AS customerName, s.name AS store,
                   COALESCE(st.name, ua.username) AS salesperson,
                   contract.sign_date AS contractDate,
                   contract.reference_amount AS referenceAmount,
                   contract.amount AS dealAmount,
                   contract.amount AS contractAmount,
                   contract.paid AS receivedAmount,
                   GREATEST(COALESCE(contract.amount,0)-
                     COALESCE(contract.paid,0),0) AS debtAmount,
                   contract.status AS contractStatus
            FROM contracts contract
            JOIN customers customer
              ON customer.customer_id=contract.customer_id
            JOIN stores s ON s.store_id=contract.store_id
            LEFT JOIN user_accounts ua
              ON ua.user_id=contract.created_by_user_id
            LEFT JOIN staff st ON st.staff_id=ua.staff_id
            WHERE contract.tenant_id=%s AND contract.deleted_at IS NULL
              AND {clause}
            ORDER BY contract.contract_id DESC
            """,
            [tenant_id, *params],
        )
    elif resource in {
        "f1-monthly-occupancy",
        "f2-room-status-overall-analysis",
        "f6-occupancy-rate",
    }:
        clause, params = _store_scope(user, "room")
        rows = _rows(
            connection,
            f"""
            SELECT MIN(room.room_id) AS id,
                   DATE_FORMAT(CURDATE(), '%%Y-%%m') AS statMonth,
                   CURDATE() AS statDate, s.name AS store,
                   COALESCE(rt.name, room.room_type) AS roomType,
                   COUNT(room.room_id) AS totalRoomCount,
                   COUNT(room.room_id) AS availableRoomDays,
                   SUM(room.status='入住') AS occupiedRoomCount,
                   SUM(room.status IN ('已预订','已订房')) AS reservedRoomCount,
                   SUM(room.status IN ('空闲','空房')) AS vacantRoomCount,
                   ROUND(
                     SUM(room.status='入住')*100/
                     NULLIF(COUNT(room.room_id),0),2
                   ) AS occupancyRate
            FROM rooms room
            JOIN stores s ON s.store_id=room.store_id
            LEFT JOIN room_types rt ON rt.room_type_id=room.room_type_id
            WHERE room.tenant_id=%s AND room.deleted_at IS NULL
              AND {clause}
            GROUP BY room.store_id, COALESCE(rt.name, room.room_type)
            ORDER BY room.store_id, roomType
            """,
            [tenant_id, *params],
        )
        for row in rows:
            row["roomCount"] = row.get("totalRoomCount")
            row["occupiedCount"] = row.get("occupiedRoomCount")
            row["reservedCount"] = row.get("reservedRoomCount")
            row["vacantCount"] = row.get("vacantRoomCount")
            row["occupiedRoomDays"] = row.get("occupiedRoomCount")
            row["reservedRoomDays"] = row.get("reservedRoomCount")
    elif resource in {
        "f3-monthly-reservation-details",
        "f4-monthly-checkout-details",
    }:
        clause, params = _store_scope(user, "booking")
        rows = _rows(
            connection,
            f"""
            SELECT booking.booking_id AS id, customer.name AS customerName,
                   s.name AS store, room.room_no AS roomNo,
                   COALESCE(rt.name, room.room_type) AS roomType,
                   booking.check_in AS plannedCheckInDate,
                   booking.check_out AS plannedCheckOutDate,
                   DATEDIFF(booking.check_out, booking.check_in) AS plannedDays,
                   booking.actual_check_in_at AS checkInDate,
                   booking.actual_check_out_at AS checkoutDate,
                   booking.status AS reserveStatus,
                   booking.status AS settlementStatus
            FROM room_bookings booking
            JOIN customers customer
              ON customer.customer_id=booking.customer_id
            JOIN rooms room ON room.room_id=booking.room_id
            LEFT JOIN room_types rt ON rt.room_type_id=room.room_type_id
            JOIN stores s ON s.store_id=booking.store_id
            WHERE booking.tenant_id=%s AND booking.deleted_at IS NULL
              AND {clause}
            ORDER BY booking.booking_id DESC
            """,
            [tenant_id, *params],
        )
    elif resource in {
        "c0-daily-operation",
        "c2-receipt-settlement-type-summary",
        "c16-receipt-and-settlement-types",
    }:
        clause, params = _store_scope(user, "receipt")
        rows = _rows(
            connection,
            f"""
            SELECT MIN(receipt.receipt_id) AS id,
                   DATE(receipt.received_at) AS statDate,
                   receipt.receipt_type AS receiptType,
                   receipt.payment_method AS settlementType,
                   s.name AS store,
                   COUNT(receipt.receipt_id) AS documentCount,
                   COALESCE(SUM(receipt.amount),0) AS receiptAmount,
                   COALESCE(SUM(receipt.amount),0) AS receivedAmount,
                   0 AS refundAmount, 0 AS paymentAmount,
                   COALESCE(SUM(receipt.amount),0) AS incomeAmount,
                   0 AS costAmount,
                   COALESCE(SUM(receipt.amount),0) AS netAmount
            FROM finance_receipts receipt
            JOIN stores s ON s.store_id=receipt.store_id
            WHERE receipt.tenant_id=%s AND {clause}
            GROUP BY DATE(receipt.received_at), receipt.store_id,
                     receipt.receipt_type, receipt.payment_method
            ORDER BY statDate DESC, receipt.store_id
            """,
            [tenant_id, *params],
        )
    elif resource == "h1-customer-service-records":
        clause, params = _store_scope(user, "request")
        rows = _rows(
            connection,
            f"""
            SELECT request.service_id AS id,
                   request.applied_at AS serviceDate,
                   customer.name AS customerName, room.room_no AS roomNo,
                   request.service_type AS serviceName,
                   assignee.name AS serviceStaff,
                   request.service_status AS serviceStatus,
                   request.remark AS serviceResult,
                   s.name AS store
            FROM room_service_requests request
            JOIN customers customer
              ON customer.customer_id=request.customer_id
            LEFT JOIN rooms room ON room.room_id=request.room_id
            LEFT JOIN staff assignee ON assignee.staff_id=request.service_staff_id
            JOIN stores s ON s.store_id=request.store_id
            WHERE request.tenant_id=%s AND request.deleted_at IS NULL
              AND {clause}
            ORDER BY request.service_id DESC
            """,
            [tenant_id, *params],
        )
    elif resource == "h2-baby-vital-sign-statistics":
        baby_clause, baby_params = _store_scope(user, "baby")
        rows = _rows(
            connection,
            f"""
            SELECT log.log_id AS id, log.log_time AS recordDate,
                   baby.name AS babyName, customer.name AS customerName,
                   room.room_no AS roomNo,
                   IF(log.metric='体温',log.metric_value,NULL) AS temperature,
                   IF(log.metric='体重',log.metric_value,NULL) AS weight,
                   log.note AS otherSigns, staff.name AS recorder
            FROM baby_logs log
            JOIN babies baby ON baby.baby_id=log.baby_id
            JOIN customers customer
              ON customer.customer_id=baby.customer_id
            LEFT JOIN staff ON staff.staff_id=log.operator_id
            LEFT JOIN room_bookings booking
              ON booking.customer_id=customer.customer_id
             AND booking.deleted_at IS NULL
             AND booking.status IN ('已订房','已入住')
            LEFT JOIN rooms room ON room.room_id=booking.room_id
            WHERE log.tenant_id=%s AND {baby_clause}
            ORDER BY log.log_id DESC
            LIMIT 1000
            """,
            [tenant_id, *baby_params],
        )
    elif resource == "h4-rehab-service-work-summary":
        clause, params = _store_scope(user, "record")
        rows = _rows(
            connection,
            f"""
            SELECT MIN(record.record_id) AS id,
                   record.service_name AS serviceName,
                   st.name AS technician,
                   COUNT(record.record_id) AS completedCount,
                   SUM(record.used_count) AS consumedCount,
                   COUNT(DISTINCT record.customer_id) AS customerCount,
                   s.name AS store
            FROM recovery_service_records record
            LEFT JOIN staff st ON st.staff_id=record.technician_staff_id
            JOIN stores s ON s.store_id=record.store_id
            WHERE record.tenant_id=%s AND record.deleted_at IS NULL
              AND {clause}
            GROUP BY record.store_id, record.service_name,
                     record.technician_staff_id
            ORDER BY completedCount DESC
            """,
            [tenant_id, *params],
        )

    return {
        "list": rows,
        "total": len(rows),
        "source": "mysql",
        "implemented": bool(rows) or resource in {
            "s1-sales-ranking",
            "s13-sales-performance",
            "s2-customer-brief",
            "s4-dm-customer-contract-summary",
            "c6-customer-receipt-tracking",
            "f1-monthly-occupancy",
            "f2-room-status-overall-analysis",
            "f6-occupancy-rate",
            "f3-monthly-reservation-details",
            "f4-monthly-checkout-details",
            "c0-daily-operation",
            "c2-receipt-settlement-type-summary",
            "c16-receipt-and-settlement-types",
            "h1-customer-service-records",
            "h2-baby-vital-sign-statistics",
            "h4-rehab-service-work-summary",
        },
    }

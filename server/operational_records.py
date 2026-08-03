"""Shared validation and workflow rules for store-scoped ERP records."""

from __future__ import annotations

from datetime import datetime
from typing import Any


MODULE_RESOURCES = {
    "RESEARCH": {
        "beauty-cases",
    },
    "RECOVERY": {
        "recovery-programs",
        "recovery-schedule",
        "postpartum-assessments",
        "recovery-service-tracking",
        "recovery-store-dashboard",
        "recovery-upsell",
        "recovery-assets",
        "recovery-staff-performance",
    },
    "CUSTOMER": {
        "clues",
        "follow-records",
        "appointments",
        "public-customers",
        "visits",
        "satisfaction",
        "callbacks",
        "complaints",
        "message-templates",
        "messages",
        "point-records",
        "activities",
    },
    "SERVICE": {
        "f005",
        "f043",
        "f084",
        "f094",
    },
    "NURSING": {
        "nursing-plan",
        "nursing-roster-v2",
        "nursing-dashboard",
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
        "nursing-sales-performance",
        "record-visibility-scope",
        "missed-record-reminders",
        "shift-handover",
        "infection-management",
        "nursing-task-orders",
    },
    "BABY": {
        "baby-log",
        "baby-log-completion",
        "newborn-care-records",
        "baby-temperature",
        "baby-medications",
        "baby-growth-profile",
        "baby-visitors",
        "baby-discharge-handover",
    },
    "MATRON": {
        "maternity-matron-archives",
        "maternity-salary-standards",
        "maternity-schedules",
        "maternity-contracts",
        "maternity-service-records",
        "maternity-dispatch-audits",
        "maternity-settlements",
        "maternity-appointments",
    },
    "DIET": {
        "customer-meal-plans",
        "dishes",
        "diet-packages",
        "diet-statistics",
        "delivery-statistics",
        "nutrition-soups",
        "nutrition-soup-statistics",
        "guest-meal-supply",
        "ingredient-purchases",
        "diet-sales",
        "meal-orders",
        "meal-cards",
        "meal-card-consumption-report",
    },
    "INVENTORY": {
        "purchase-plans",
        "purchase-orders",
        "purchase-order-audits",
        "other-inbounds",
        "purchase-inbounds",
        "material-requisitions",
        "sales-outbounds",
        "material-requisitions-no-amount",
        "stock-transfers",
        "purchase-returns",
        "stocktakes",
        "stock-damages",
        "opening-stock-import",
        "stock-warnings",
        "opening-stock-query",
        "gift-list-plans",
        "stock-summary-report",
        "stock-ledger-report",
        "department-requisition-report",
        "warehouse-stock-query",
        "purchase-detail-report",
        "supplier-prepayments",
        "supplier-payments",
        "accounts-payable-detail",
        "batch-expiry",
        "supplier-records",
    },
    "BASIC": {
        "basic-items", "material-records", "satisfaction-survey-templates",
        "survey-management", "warehouse-records", "supplier-records",
        "fund-accounts", "report-templates", "nursing-templates",
        "task-management", "service-time-settings",
        "project-labor-fee-settings", "commission-rate-settings",
        "equipment-management", "performance-target-settings",
        "discount-amount-authorization", "bed-management",
    },
    "REPORT": {
        "s3-best-selling-ranking", "s5-product-consumption-summary",
        "s6-sales-statistics", "s7-service-sales-summary",
        "s8-card-sales-summary", "s9-cross-store-consumption",
        "s10-sml-daily-sales", "s11-gift-item-details",
        "s12-customer-cross-store-service-consumption",
        "f5-prestay-customer-purchase", "c1-member-recharge-summary",
        "c3-payment-summary-analysis", "c5-month-day-statistical-analysis",
        "c8-product-gross-profit-analysis", "c9-referrer-report",
        "c12-cashback-consumption-query", "c10-receipt-item-summary",
        "c11-service-consumption-income", "c14-contract-performance",
        "c15-fund-account-transactions", "h1-customer-service-records",
        "h3-mother-temperature-weight-trend",
        "h4-rehab-service-work-summary", "wechat-customer-service-report",
        "mother-app-sharing-report",
    },
    "MALL": {
        "products", "orders", "projects", "matrons", "categories",
        "parenting", "questions", "reviews", "community", "content",
        "comments", "classes", "class-schedule",
    },
}

IDENTIFIER_FIELDS = {
    "nursing-plan": "planNo",
    "nursing-roster-v2": "scheduleNo",
    "nursing-dashboard": "scheduleNo",
    "health-assessments": "assessmentNo",
    "check-in-handover": "handoverNo",
    "baby-nursing-records": "recordNo",
    "record-visibility-scope": "ruleNo",
    "missed-record-reminders": "reminderNo",
    "shift-handover": "handoverNo",
    "infection-management": "riskNo",
    "nursing-task-orders": "taskNo",
    "meal-orders": "orderNo",
    "dishes": "dishCode",
    "diet-packages": "packageCode",
    "purchase-orders": "purchaseNo",
    "stock-transfers": "transferNo",
    "stocktakes": "stocktakeNo",
    "supplier-records": "supplierCode",
    "batch-expiry": "batchNo",
}

PREFIXES = {
    "RESEARCH": "RES",
    "RECOVERY": "REC",
    "CUSTOMER": "CUS",
    "SERVICE": "CSR",
    "NURSING": "NUR",
    "BABY": "BABY",
    "MATRON": "MAT",
    "DIET": "DIET",
    "INVENTORY": "INV",
    "BASIC": "BAS",
    "REPORT": "RPT",
    "MALL": "MALL",
}

ACTION_PATCHES = {
    "启用": {"enabled": "启用", "status": "启用"},
    "停用": {"enabled": "停用", "status": "停用"},
    "提交": {"auditStatus": "待审核", "status": "待审核"},
    "审核": {"auditStatus": "已审核", "status": "已审核"},
    "反审核": {"auditStatus": "待审核", "status": "待审核"},
    "确认完成": {"confirmStatus": "已确认", "status": "已完成"},
    "确认签收": {"orderStatus": "已签收", "status": "已签收"},
    "确认下单": {"orderStatus": "待备餐", "status": "待备餐"},
    "开始备餐": {"orderStatus": "备餐中", "status": "备餐中"},
    "开始配送": {"orderStatus": "配送中", "status": "配送中"},
    "退餐": {"orderStatus": "已退餐", "status": "已退餐"},
    "开始盘点": {"stocktakeStatus": "盘点中", "status": "盘点中"},
    "录入盘点": {"stocktakeStatus": "待审核", "status": "待审核"},
    "完成盘点": {"stocktakeStatus": "待审核", "status": "待审核"},
    "调出确认": {"transferStatus": "待收货", "status": "待收货"},
    "调入确认": {"transferStatus": "已完成", "status": "已完成"},
    "生成采购计划": {"warningStatus": "处理中", "status": "待采购"},
    "确认收货": {"arrivalStatus": "已到货", "status": "已到货"},
    "到货登记": {"arrivalStatus": "已到货", "status": "已完成"},
}

FORBIDDEN_PAYLOAD_KEYS = {
    "tenant_id",
    "tenantId",
    "store_id",
    "created_by_user_id",
    "updated_by_user_id",
    "deleted_at",
    "version",
    "recordId",
    "action",
}


def validate_resource(module_code: str, resource: str) -> None:
    if resource not in MODULE_RESOURCES.get(module_code, set()):
        raise ValueError("resource")


def clean_payload(payload: dict[str, Any]) -> dict[str, Any]:
    cleaned = {
        str(key): value
        for key, value in payload.items()
        if key not in FORBIDDEN_PAYLOAD_KEYS and not str(key).startswith("_")
    }
    cleaned.pop("storeId", None)
    cleaned.pop("id", None)
    return cleaned


def parse_record_id(value: Any) -> int | None:
    if isinstance(value, str) and value.startswith("OP-"):
        value = value[3:]
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def business_no(module_code: str, resource: str, record_id: int) -> str:
    prefix = PREFIXES[module_code]
    resource_token = "".join(
        part[:2].upper() for part in resource.split("-") if part
    )[:8]
    return f"{prefix}-{resource_token}-{record_id:08d}"


def identifier_field(resource: str) -> str:
    return IDENTIFIER_FIELDS.get(resource, "businessNo")


def apply_action(
    resource: str,
    action: str,
    payload: dict[str, Any],
    now: datetime | None = None,
) -> tuple[dict[str, Any], str]:
    timestamp = (now or datetime.now()).isoformat(timespec="seconds")
    patch = dict(ACTION_PATCHES.get(action, {}))
    rejected = (
        action == "审核"
        and payload.get("auditResult") == "审核不通过"
    )
    if rejected:
        patch.update({"auditStatus": "审核不通过", "status": "审核不通过"})
    elif resource == "stocktakes" and action == "审核":
        patch.update({"stocktakeStatus": "已完成", "status": "已完成"})
    elif resource == "missed-record-reminders" and action == "确认处理":
        patch.update({"reminderStatus": "已完成", "status": "已完成"})
    elif resource == "shift-handover" and action == "确认接班":
        patch.update({"handoverStatus": "已接班", "status": "已接班"})
    elif resource == "infection-management" and action == "复核":
        patch.update({"riskStatus": "处理中", "status": "处理中"})
    elif resource == "infection-management" and action == "关闭":
        patch.update({"riskStatus": "已关闭", "status": "已关闭"})
    elif resource == "nursing-task-orders" and action == "指派":
        patch.update({"taskStatus": "待执行", "status": "待执行"})
    elif resource == "nursing-task-orders" and action == "确认完成":
        patch.update({"taskStatus": "已完成", "status": "已完成"})
    patch.update(clean_payload(payload))
    patch["lastAction"] = action
    patch["lastActionAt"] = timestamp
    status = str(patch.get("status") or action or "已更新")
    return patch, status

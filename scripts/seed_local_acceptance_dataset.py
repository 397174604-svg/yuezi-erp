#!/usr/bin/env python3
"""Create an isolated local acceptance dataset for the ERP Web release.

All inserted rows carry ``LOCAL_ACCEPTANCE_SEED_20260801`` so they can be
removed without touching room masters, package masters, permissions, or
imported legacy data.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".deps"))
import pymysql


BASE_URL = os.environ.get("ERP_MVP_BASE_URL", "http://127.0.0.1:3000")
CONFIRM_ENV = "ERP_LOCAL_DEMO_CONFIRM"
CONFIRM_VALUE = "LOCAL_TEST_ONLY"
BATCH = "LOCAL_ACCEPTANCE_SEED_20260801"

PEOPLE = {
    1: [("李女士", "18810001001", "小满"), ("王女士", "18810001002", "安安"), ("周女士", "18810001003", "乐乐")],
    2: [("张女士", "18810002001", "朵朵"), ("赵女士", "18810002002", "果果"), ("陈女士", "18810002003", "玖玖")],
}
MATRONS = {
    1: [("刘芳", "18820001001"), ("陈静", "18820001002"), ("王敏", "18820001003")],
    2: [("孙丽", "18820002001"), ("周敏", "18820002002"), ("赵芳", "18820002003")],
}

RESOURCES = {
    "CUSTOMER": [
        "clues", "follow-records", "appointments", "public-customers",
        "visits", "satisfaction", "callbacks", "complaints",
        "message-templates", "messages", "point-records", "activities",
    ],
    "SERVICE": ["f005", "f043", "f084", "f094"],
    "BABY": [
        "baby-log", "baby-log-completion", "newborn-care-records",
        "baby-temperature", "baby-medications", "baby-growth-profile",
        "baby-visitors", "baby-discharge-handover",
    ],
    "MATRON": [
        "maternity-salary-standards", "maternity-schedules",
        "maternity-contracts", "maternity-service-records",
        "maternity-dispatch-audits", "maternity-settlements",
        "maternity-appointments",
    ],
    "NURSING": [
        "nursing-plan", "nursing-roster-v2", "nursing-dashboard", "baby-files",
        "health-assessments", "diet-assessments", "custom-rounds", "doctor-rounds",
        "diet-taboo-rounds", "nursing-plan-confirmations", "nursing-project-records",
        "mother-nursing-records", "baby-nursing-records", "mother-nursing-summary",
        "baby-nursing-summary", "nursing-roster", "check-in-handover",
        "nursing-sales-performance", "record-visibility-scope",
        "missed-record-reminders", "shift-handover",
        "infection-management", "nursing-task-orders",
    ],
    "DIET": [
        "customer-meal-plans", "dishes", "diet-packages", "diet-statistics",
        "delivery-statistics", "nutrition-soups", "nutrition-soup-statistics",
        "guest-meal-supply", "ingredient-purchases", "diet-sales", "meal-orders",
        "meal-cards", "meal-card-consumption-report",
    ],
    "INVENTORY": [
        "purchase-plans", "purchase-orders", "purchase-order-audits", "other-inbounds",
        "purchase-inbounds", "material-requisitions", "sales-outbounds",
        "material-requisitions-no-amount", "stock-transfers", "purchase-returns",
        "stocktakes", "stock-damages", "opening-stock-import", "stock-warnings",
        "opening-stock-query", "gift-list-plans", "stock-summary-report",
        "stock-ledger-report", "department-requisition-report", "warehouse-stock-query",
        "purchase-detail-report", "supplier-prepayments", "supplier-payments",
        "accounts-payable-detail", "batch-expiry", "supplier-records",
    ],
    "BASIC": [
        "basic-items", "material-records", "satisfaction-survey-templates",
        "survey-management", "warehouse-records", "supplier-records",
        "fund-accounts", "report-templates", "nursing-templates",
        "task-management", "service-time-settings", "project-labor-fee-settings",
        "commission-rate-settings", "equipment-management",
        "performance-target-settings", "discount-amount-authorization",
        "bed-management",
    ],
    "REPORT": [
        "s3-best-selling-ranking", "s5-product-consumption-summary",
        "s6-sales-statistics", "s7-service-sales-summary", "s8-card-sales-summary",
        "s9-cross-store-consumption", "s10-sml-daily-sales",
        "s11-gift-item-details", "s12-customer-cross-store-service-consumption",
        "f5-prestay-customer-purchase", "c1-member-recharge-summary",
        "c3-payment-summary-analysis", "c5-month-day-statistical-analysis",
        "c8-product-gross-profit-analysis", "c9-referrer-report",
        "c12-cashback-consumption-query", "c10-receipt-item-summary",
        "c11-service-consumption-income", "c14-contract-performance",
        "c15-fund-account-transactions", "h1-customer-service-records",
        "h3-mother-temperature-weight-trend", "h4-rehab-service-work-summary",
        "wechat-customer-service-report", "mother-app-sharing-report",
    ],
    "MALL": [
        "products", "orders", "projects", "matrons", "categories",
        "parenting", "questions", "reviews", "community", "content",
        "comments", "classes", "class-schedule",
    ],
}


def api(path: str, method: str = "GET", body=None, token: str = ""):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Token"] = token
    request = Request(
        BASE_URL + path,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None,
        headers=headers,
        method=method,
    )
    try:
        with urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path}: HTTP {exc.code}: {detail}") from exc
    if payload.get("code") != 20000:
        raise RuntimeError(payload.get("message") or f"{method} {path} failed")
    return payload["data"]


def connection():
    return pymysql.connect(
        host=os.environ.get("ERP_DB_HOST", "127.0.0.1"),
        port=int(os.environ.get("ERP_DB_PORT", "3306")),
        user=os.environ["ERP_DB_USER"],
        password=os.environ["ERP_DB_PASSWORD"],
        database=os.environ.get("ERP_DB_NAME", "yuezi"),
        charset="utf8mb4",
        autocommit=False,
    )


def record_payload(resource: str, index: int, person: tuple[str, str, str], room_no: str, matron: str):
    customer_name, phone, baby_name = person
    today = date.today().isoformat()
    common = {
        "demoBatch": BATCH,
        "customerName": customer_name,
        "mobile": phone,
        "babyName": baby_name,
        "room": room_no,
        "store": "",
        "nurseName": matron,
        "operator": matron,
        "status": ["待处理", "进行中", "已完成"][index - 1],
        "createdAt": f"{today} {8 + index:02d}:30",
        "remark": "资料已核验",
    }
    specifics = {
        "baby-log": {"logDate": today, "feeding": "母乳+配方", "sleep": "3小时", "diaper": "正常", "temperature": "36.6℃"},
        "baby-log-completion": {"logDate": today, "sleepHours": 3 + index, "cryCount": index, "stoolAmount": "正常", "completionStatus": "已补全"},
        "newborn-care-records": {"recordNo": f"NCR-{index:03d}", "careItem": ["沐浴", "脐部护理", "黄疸观察"][index - 1], "careDate": today, "result": "情况正常"},
        "baby-temperature": {"measuredAt": f"{today} {8 + index:02d}:00", "temperature": 36.5 + index / 10, "measurer": matron, "temperatureStatus": "正常", "actionNote": "持续观察"},
        "baby-medications": {"medicineNo": f"MED-{index:03d}", "medicineName": "维生素D", "dose": "1滴", "medicationDate": today, "medicationStatus": "已服用"},
        "baby-growth-profile": {"recordDate": today, "ageDays": 5 + index, "weight": 3.2 + index / 10, "height": 50 + index, "milestone": "生长正常", "growthStage": "住中观察"},
        "baby-visitors": {"visitNo": f"VIS-{index:03d}", "visitorName": ["李先生", "王先生", "周先生"][index - 1], "relationship": "父亲", "visitDate": today, "disinfection": "已完成", "visitStatus": "已离场"},
        "baby-discharge-handover": {"handoverNo": f"HOV-{index:03d}", "handoverDate": today, "careSummary": "护理情况稳定", "medicine": "无", "familySigned": "已签收", "handoverStatus": "已完成"},
    }
    common.update(specifics.get(resource, {}))
    if resource in RESOURCES["CUSTOMER"]:
        common.update({
            "name": customer_name,
            "visitor": customer_name,
            "contactName": customer_name,
            "wechat": f"qdf{phone[-4:]}",
            "source": ["客户介绍", "自然上门", "抖音咨询"][index - 1],
            "salesperson": ["李顾问", "王顾问", "陈顾问"][index - 1],
            "follower": ["李顾问", "王顾问", "陈顾问"][index - 1],
            "followStatus": ["待跟进", "跟进中", "已转化"][index - 1],
            "followType": ["销售跟进", "咨询跟进", "回访跟进"][index - 1],
            "contactType": ["电话交流", "微信交流", "来店参观"][index - 1],
            "followedAt": f"{today} {9 + index:02d}:00",
            "nextFollowAt": f"{today} {14 + index:02d}:00",
            "content": ["确认到店时间", "沟通房型偏好", "确认签约资料"][index - 1],
            "visitorCount": index,
            "appointmentAt": f"{today} {10 + index:02d}:30",
            "arrivalStatus": ["已邀约", "是", "否"][index - 1],
            "visitAt": f"{today} {11 + index:02d}:00",
            "location": "会客区",
            "surveyAt": today,
            "surveyType": ["入住回访", "服务回访", "离所回访"][index - 1],
            "satisfaction": ["满意", "非常满意", "满意"][index - 1],
            "score": [92, 96, 90][index - 1],
            "callbackType": ["第一阶段", "第二阶段", "出院回访"][index - 1],
            "callbackAt": f"{today} {15 + index:02d}:00",
            "details": ["入住适应良好", "护理服务满意", "离所注意事项已说明"][index - 1],
            "target": ["护理服务", "膳食服务", "客房服务"][index - 1],
            "complaintType": ["服务及时性", "沟通问题", "责任心"][index - 1],
            "department": ["护理部", "膳食部", "客房部"][index - 1],
            "handled": ["未处理", "处理中", "已处理"][index - 1],
            "title": ["预产期提醒", "入住准备提醒", "离所回访提醒"][index - 1],
            "messageTitle": ["到店确认", "入住物品提醒", "离所健康提醒"][index - 1],
            "channel": ["站内消息", "短信", "微信"][index - 1],
            "sendStatus": ["待发送", "已发送", "已发送"][index - 1],
            "plannedAt": f"{today} {16 + index:02d}:00",
            "pointValue": [100, 200, 300][index - 1],
            "pointType": ["获取积分", "获取积分", "使用积分"][index - 1],
            "activityStatus": ["草稿", "启用", "启用"][index - 1],
            "startsAt": today,
            "endsAt": (date.today() + timedelta(days=14)).isoformat(),
        })
    if resource in RESOURCES["SERVICE"]:
        service_statuses = {
            "f005": ["待回访", "跟进中", "已完成"],
            "f043": ["草稿", "待审核", "已发布"],
            "f084": ["草稿", "待发送", "已发送"],
            "f094": ["待接入", "处理中", "等待客户"],
        }
        common.update({
            "contactName": customer_name,
            "subject": {
                "f005": ["入住第三日回访", "护理服务回访", "离所健康回访"],
                "f043": ["入住办理说明", "套餐价格说明", "护理服务说明"],
                "f084": ["预约确认通知", "入住准备通知", "护理服务通知"],
                "f094": ["预约房型咨询", "套餐价格咨询", "护理服务咨询"],
            }[resource][index - 1],
            "category": ["入住服务", "套餐服务", "护理服务"][index - 1],
            "priority": ["普通", "重要", "普通"][index - 1],
            "channel": ["站内消息", "电话", "微信"][index - 1],
            "score": [92, 96, 90][index - 1],
            "content": ["确认客户入住体验", "核对服务执行情况", "记录后续服务需求"][index - 1],
            "assignedName": ["李客服", "王客服", "陈客服"][index - 1],
            "status": service_statuses[resource][index - 1],
        })
    if resource.startswith("maternity-"):
        common.update({
            "护理师名称": matron, "护理师等级": ["初级月嫂", "中级月嫂", "高级月嫂"][index - 1],
            "客户名称": customer_name, "档期情况": "可预约" if index == 1 else "服务中",
            "最终金额": 8800 + index * 800, "所属分店": "当前门店", "状态": common["status"],
            "startDate": today, "endDate": (date.today() + timedelta(days=28)).isoformat(),
        })
    if resource in RESOURCES["NURSING"]:
        common.update({
            "planNo": f"NUR-{index:03d}", "assessmentNo": f"ASS-{index:03d}",
            "nursingItem": ["产妇晨间护理", "宝宝喂养观察", "入住交接"][index - 1],
            "result": "已按计划完成", "department": "护理部",
            # 护理工作台会在前端继续应用页面默认筛选。验收数据必须
            # 与这些默认值一致，否则接口已有 3 条记录但页面仍显示 0 条。
            "customerStatus": "- 已入住 -",
            "scheduleType": "护理排班",
            "planDate": today,
            "serviceDate": today,
            "scheduleRange": today,
            "recordRange": today,
            "completedRange": today,
        })
        nursing_specifics = {
            "record-visibility-scope": {
                "ruleNo": f"RVS-{index:03d}",
                "recordType": ["妈妈护理记录", "宝宝护理记录", "查房记录"][index - 1],
                "scopeLevel": ["总部", "本门店", "本人"][index - 1],
                "applicableRole": ["护理总监", "护理主管", "责任护士"][index - 1],
                "effectiveAt": f"{today} 09:00",
                "operator": matron,
                "status": "启用",
            },
            "missed-record-reminders": {
                "reminderNo": f"REM-{index:03d}",
                "recordType": ["晨间护理记录", "宝宝喂养记录", "入住交接记录"][index - 1],
                "dueAt": f"{today} {9 + index:02d}:00",
                "owner": matron,
                "reminderStatus": ["待处理", "处理中", "已完成"][index - 1],
            },
            "shift-handover": {
                "handoverNo": f"SHF-{index:03d}",
                "shiftName": ["早班", "中班", "晚班"][index - 1],
                "handoverBy": matron,
                "receiveBy": ["李护士", "王护士", "周护士"][index - 1],
                "riskSummary": ["重点观察产妇体温", "宝宝喂养情况稳定", "入住物品已清点"][index - 1],
                "handoverAt": f"{today} {7 + index * 4:02d}:30",
                "handoverStatus": ["待接班", "已接班", "需补充"][index - 1],
            },
            "infection-management": {
                "riskNo": f"INF-{index:03d}",
                "riskType": ["日常筛查", "环境消毒复核", "接触风险观察"][index - 1],
                "measure": ["继续观察并记录", "已完成区域消毒", "加强手卫生管理"][index - 1],
                "reviewer": ["李主管", "王主管", "周主管"][index - 1],
                "riskStatus": ["待复核", "处理中", "已关闭"][index - 1],
            },
            "nursing-task-orders": {
                "taskNo": f"NTO-{index:03d}",
                "taskType": ["常规护理", "临时需求", "异常复核"][index - 1],
                "assignee": matron,
                "dueAt": f"{today} {10 + index:02d}:30",
                "taskStatus": ["待指派", "执行中", "已完成"][index - 1],
            },
        }
        common.update(nursing_specifics.get(resource, {}))
    if resource in RESOURCES["DIET"]:
        common.update({
            "orderNo": f"MEAL-{index:03d}", "dishCode": f"D{index:03d}",
            "dishName": ["山药小米粥", "清炖鲫鱼汤", "时蔬鸡肉饭"][index - 1],
            "mealType": ["早餐", "午餐", "晚餐"][index - 1], "mealDate": today,
            "quantity": 1, "amount": 58 + index * 10, "deliveryStatus": "已签收",
        })
    if resource in RESOURCES["INVENTORY"]:
        common.update({
            "materialCode": f"MAT-{index:03d}", "materialName": ["婴儿纸尿裤", "护理湿巾", "消毒棉签"][index - 1],
            "specification": "标准装", "unit": "包", "quantity": 20 + index * 5,
            "currentQuantity": 20 + index * 5, "purchaseNo": f"PO-{index:03d}",
            "supplierName": "本地验收供应商", "warehouse": "护理部仓库",
            "totalAmount": 500 + index * 120, "auditStatus": "审核通过",
        })
    if resource in RESOURCES["BASIC"]:
        code = f"BAS-{date.today():%Y%m%d}-{index:03d}"
        operator = ["李顾问", "王主管", "陈护士"][index - 1]
        common.update({
            "itemCode": code, "itemName": ["产后基础护理", "新生儿沐浴", "营养评估"][index - 1],
            "materialCode": code, "materialName": ["护理垫", "消毒棉签", "婴儿湿巾"][index - 1],
            "category": ["护理服务", "消毒用品", "母婴用品"][index - 1],
            "unit": ["次", "盒", "包"][index - 1], "referencePrice": 180 + index * 20,
            "referenceCost": 20 + index * 5, "businessType": ["护理", "膳食", "客房"][index - 1],
            "templateCode": code, "templateName": ["入住满意度问卷", "护理记录模板", "经营日报模板"][index - 1],
            "templateType": ["满意度", "护理", "经营"][index - 1], "questionCount": 8 + index,
            "applicableScope": "当前门店", "updatedBy": operator, "updatedAt": f"{today} 10:00",
            "surveyCode": code, "surveyName": ["入住体验调查", "膳食满意度调查", "离所回访调查"][index - 1],
            "surveyType": ["入住", "膳食", "离所"][index - 1], "publishScope": "当前门店",
            "publishStatus": ["草稿", "已发布", "已结束"][index - 1], "effectiveDate": today,
            "warehouseCode": code, "warehouseName": ["护理用品库", "膳食耗材库", "客房备品库"][index - 1],
            "warehouseType": ["护理", "膳食", "客房"][index - 1], "manager": operator, "location": f"{index}楼库房",
            "supplierCode": code, "supplierName": ["青岛安康母婴用品", "青岛鲜品供应链", "青岛洁净日化"][index - 1],
            "supplierType": ["母婴用品", "食材", "清洁用品"][index - 1], "contactName": ["李经理", "王经理", "陈经理"][index - 1],
            "contactPhone": ["18610001001", "18610001002", "18610001003"][index - 1], "settlementMethod": "月结",
            "cooperationStatus": ["正常", "正常", "待复核"][index - 1],
            "accountCode": code, "accountName": ["营业收入账户", "采购结算账户", "备用金账户"][index - 1],
            "accountType": ["收入", "支出", "备用金"][index - 1], "bankName": "中国工商银行", "accountNo": f"6222****{1000 + index}",
            "templateFormat": "标准表格", "version": f"V1.{index}", "nursingType": ["产妇", "宝宝", "交接"][index - 1],
            "applicableObject": ["产妇", "宝宝", "护理班组"][index - 1], "itemCount": 6 + index,
            "taskCode": code, "taskName": ["入住资料核验", "护理计划确认", "离所物品清点"][index - 1],
            "taskCategory": ["入住", "护理", "离所"][index - 1], "department": ["销售部", "护理部", "客房部"][index - 1],
            "frequency": "每日", "duration": 30 + index * 10, "serviceType": ["护理", "膳食", "客房"][index - 1],
            "serviceName": ["晨间护理", "加餐配送", "客房整理"][index - 1], "weekday": "周一至周日",
            "timeRange": ["08:00-10:00", "15:00-17:00", "10:00-12:00"][index - 1], "capacity": 6 + index,
            "projectCode": code, "projectName": ["产后基础护理", "宝宝沐浴", "客房深度清洁"][index - 1],
            "projectType": ["护理", "宝宝", "客房"][index - 1], "feeRule": "按次", "laborFee": 60 + index * 10,
            "ruleName": ["护理服务提成", "膳食销售提成", "会员开卡提成"][index - 1], "employeeScope": ["护士", "顾问", "销售"][index - 1],
            "calculationBase": "实收金额", "commissionRate": 3 + index,
            "equipmentNo": code, "equipmentName": ["婴儿体重秤", "消毒设备", "产康理疗仪"][index - 1],
            "equipmentType": ["测量", "消毒", "理疗"][index - 1], "purchaseDate": today,
            "nextMaintenanceDate": (date.today() + timedelta(days=90)).isoformat(), "equipmentStatus": ["正常", "正常", "待保养"][index - 1],
            "targetPeriod": f"{date.today():%Y-%m}", "targetObject": ["销售部", "护理部", "客房部"][index - 1],
            "targetType": ["合同额", "服务量", "满意度"][index - 1], "targetAmount": 80000 + index * 10000, "targetQuantity": 20 + index,
            "authorizedObject": operator, "objectType": "员工", "singleLimit": 1000 * index, "periodLimit": 5000 * index,
            "bedNo": f"BED-{index:03d}", "roomNo": ["201", "303", "F06"][index - 1], "floor": ["2楼", "3楼", "4楼"][index - 1],
            "bedType": "母婴同室", "occupantType": "产妇", "bedStatus": ["空闲", "预留", "使用中"][index - 1],
        })
    if resource in RESOURCES["REPORT"]:
        common.update({
            "reportNo": f"RPT-{date.today():%Y%m%d}-{index:03d}", "statDate": today,
            "rank": index, "salesperson": ["李顾问", "王主管", "陈护士"][index - 1],
            "department": ["销售部", "护理部", "客房部"][index - 1], "contractCount": index,
            "contractAmount": 21999 * index, "receivedAmount": 10000 * index,
            "contractNo": f"HT-{date.today():%Y%m%d}-{index:03d}", "itemName": ["基础套餐", "修养套餐", "修复套餐"][index - 1],
            "category": ["月子套餐", "护理服务", "产康服务"][index - 1], "quantity": index,
            "amount": 1200 * index, "salesAmount": 21999 * index, "serviceName": ["产妇护理", "宝宝护理", "产康服务"][index - 1],
            "cardType": ["次卡", "储值卡", "套餐卡"][index - 1], "crossStore": "否",
            "orderNo": f"ORD-{date.today():%Y%m%d}-{index:03d}", "giftName": ["入住礼包", "护理礼包", "离所礼包"][index - 1],
            "checkIn": today, "checkOut": (date.today() + timedelta(days=28)).isoformat(),
            "roomNo": ["201", "303", "F06"][index - 1], "roomType": ["大床房", "套房", "特价房"][index - 1],
            "occupancyRate": 65 + index * 5, "paymentMethod": ["微信", "银行卡", "现金"][index - 1], "receiptType": "合同收款",
            "incomeAmount": 10000 * index, "expenseAmount": 3000 * index, "balance": 7000 * index,
            "grossProfit": 5000 * index, "referrer": ["客户介绍", "自然到店", "线上咨询"][index - 1], "cashbackAmount": 100 * index,
            "refundAmount": 0, "performanceRate": 75 + index * 5, "accountName": ["营业收入账户", "采购结算账户", "备用金账户"][index - 1],
            "transactionNo": f"TRX-{date.today():%Y%m%d}-{index:03d}", "serviceDate": today,
            "temperature": 36.5 + index / 10, "weight": 55 + index, "workCount": 5 + index,
            "channel": ["微信", "电话", "到店"][index - 1], "sharingCount": 10 * index,
        })
    if resource in RESOURCES["MALL"]:
        common.update({
            "code": f"MALL-{date.today():%Y%m%d}-{index:03d}", "name": ["婴儿棉柔巾", "月子营养汤包", "产后修复服务"][index - 1],
            "category": ["母婴用品", "营养食品", "产康服务"][index - 1], "spec": ["80抽", "7日装", "单次"][index - 1],
            "unit": ["包", "盒", "次"][index - 1], "originalPrice": 120 + index * 30, "salePrice": 99 + index * 20,
            "pointPrice": 1000 * index, "stockQuantity": 30 + index * 10, "integral": "是", "recommended": "是" if index == 1 else "否",
            "type": ["商城订单", "积分订单", "服务订单"][index - 1], "payMethod": ["微信", "积分", "储值卡"][index - 1],
            "amount": 199 * index, "coupon": 10 * index, "debt": 0, "orderedAt": f"{today} {9 + index:02d}:00",
            "customer": customer_name, "pickup": "门店自提", "payStatus": "已支付", "stockStatus": "已出库",
            "level": ["初级", "中级", "高级"][index - 1], "standardFee": 8800 + index * 800, "serviceStatus": ["可预约", "服务中", "可预约"][index - 1],
            "parent": "商城分类", "navigationName": ["母婴好物", "营养膳食", "产康服务"][index - 1], "sort": index, "products": 3 + index,
            "title": ["新生儿护理要点", "科学月子餐建议", "产后恢复指南"][index - 1], "section": "育儿课堂",
            "stage": ["孕期", "住中", "离所"][index - 1], "contentType": "图文", "author": ["李顾问", "王主管", "陈护士"][index - 1],
            "publishedAt": today, "pinned": "否", "question": ["入住需要准备什么？", "宝宝护理如何安排？", "离所后如何复查？"][index - 1],
            "nickname": customer_name, "askedAt": f"{today} 11:00", "expert": ["李顾问", "王主管", "陈护士"][index - 1],
            "replyStatus": ["待回复", "已回复", "已回复"][index - 1], "visibility": "公开",
            "content": ["服务体验很好", "护理安排细致", "环境整洁舒适"][index - 1], "images": 0, "views": 50 * index,
            "commentType": "商品评价", "target": ["棉柔巾", "营养汤包", "修复服务"][index - 1],
            "productScore": 5, "packageScore": 5, "speedScore": 5, "serviceScore": 5,
            "classDate": today, "period": ["上午", "下午", "晚上"][index - 1], "className": ["新手爸妈课堂", "母乳喂养课堂", "产后恢复课堂"][index - 1],
            "teacher": ["李顾问", "王主管", "陈护士"][index - 1], "location": ["多功能厅", "护理教室", "产康中心"][index - 1],
            "startTime": ["09:00", "14:00", "18:30"][index - 1], "endTime": ["10:30", "15:30", "20:00"][index - 1],
            "capacity": 12, "registrations": 3 + index, "enabled": "启用",
        })
    return common


def ensure_local_only():
    if urlparse(BASE_URL).hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise SystemExit("Acceptance seed is restricted to a loopback API.")
    if os.environ.get(CONFIRM_ENV) != CONFIRM_VALUE:
        raise SystemExit(f"Set {CONFIRM_ENV}={CONFIRM_VALUE} before seeding.")
    if os.environ.get("ERP_DB_HOST", "127.0.0.1") not in {"127.0.0.1", "localhost", "::1"}:
        raise SystemExit("Acceptance seed is restricted to a loopback database.")


def main():
    ensure_local_only()
    password = os.environ.get("ERP_DEMO_ADMIN_PASSWORD") or os.environ.get("ERP_BOOTSTRAP_ADMIN_PASSWORD")
    if not password:
        raise SystemExit("ERP_DEMO_ADMIN_PASSWORD is required.")
    token = api("/vue-element-admin/user/login", "POST", {"username": "admin", "password": password})["token"]
    options = api("/vue-element-admin/erp/mvp/options", token=token)
    stores = sorted(options.get("stores", []), key=lambda row: int(row["id"]))[:2]
    if len(stores) != 2:
        raise RuntimeError("Two stores are required before acceptance seeding.")
    rooms = api("/vue-element-admin/erp/mvp/rooms", token=token).get("list", [])
    existing_customers = api("/vue-element-admin/erp/mvp/customers", token=token).get("list", [])
    existing_by_phone = {str(row.get("phone") or row.get("mobile") or ""): row for row in existing_customers}
    created = {"customers": [], "contracts": [], "receipts": [], "bookings": []}
    customer_rows: dict[int, list[dict]] = {}

    for store_index, store in enumerate(stores, 1):
        store_id = int(store["id"])
        available_rooms = [row for row in rooms if int(row.get("store_id") or row.get("storeId") or 0) == store_id and str(row.get("status") or "") in {"空闲", "可用"}]
        if len(available_rooms) < 3:
            raise RuntimeError(f"Store {store_id} needs at least three available rooms.")
        customer_rows[store_id] = []
        for index, person in enumerate(PEOPLE[store_index], 1):
            name, phone, _baby = person
            customer = existing_by_phone.get(phone)
            if not customer:
                customer = api("/vue-element-admin/erp/mvp/customers", "POST", {
                    "storeId": store_id, "name": name, "phone": phone, "status": "意向A",
                    "source": ["客户介绍", "自然上门", "抖音咨询"][index - 1],
                    "remark": f"{BATCH}|本地验收客户",
                }, token)
                created["customers"].append(customer["id"])
            customer_rows[store_id].append(customer)
            start = date.today() + timedelta(days=index)
            end = start + timedelta(days=28)
            contract = api("/vue-element-admin/erp/mvp/contracts", "POST", {
                "storeId": store_id, "customerId": int(customer["id"]), "contractType": "月子合同",
                "packageName": "基础套餐", "referenceAmount": 24999, "amount": 21999,
                "days": 28, "expectedCheckIn": start.isoformat(), "expectedCheckOut": end.isoformat(),
                "signDate": date.today().isoformat(), "note": BATCH,
            }, token)
            api(f"/vue-element-admin/erp/mvp/contracts/{contract['id']}/approve", "POST", {}, token)
            created["contracts"].append(contract["id"])
            receipt = api("/vue-element-admin/erp/mvp/receipts", "POST", {
                "storeId": store_id, "contractId": contract["id"], "receiptType": "合同首付",
                "amount": 10000 + index * 1000, "paymentMethod": ["转账", "微信", "银行卡"][index - 1],
                "remark": BATCH,
            }, token)
            api(f"/vue-element-admin/erp/mvp/receipts/{receipt['id']}/approve", "POST", {}, token)
            created["receipts"].append(receipt["id"])
            room = available_rooms[index - 1]
            booking = api("/vue-element-admin/erp/mvp/bookings", "POST", {
                "storeId": store_id, "contractId": contract["id"], "roomId": room["id"],
                "checkIn": start.isoformat(), "checkOut": end.isoformat(), "note": BATCH,
            }, token)
            api(f"/vue-element-admin/erp/mvp/bookings/{booking['id']}/check-in", "POST", {}, token)
            created["bookings"].append(booking["id"])

    db = connection()
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT tenant_id, user_id FROM user_accounts WHERE username='admin' AND status='ACTIVE' ORDER BY user_id LIMIT 1")
            tenant_id, user_id = cursor.fetchone()
            for store_index, store in enumerate(stores, 1):
                store_id = int(store["id"])
                # 月嫂是验收人员档案，不创建登录账号。
                for index, (name, phone) in enumerate(MATRONS[store_index], 1):
                    cursor.execute("""
                        INSERT INTO staff (
                          tenant_id, store_id, employee_no, name, gender, employment_status,
                          phone, role, position, department, status, source_file, source_page,
                          source_row, review_status, source_note
                        ) VALUES (%s,%s,%s,%s,'女','ACTIVE',%s,'月嫂','月嫂','护理部','ACTIVE',%s,1,%s,'VERIFIED',%s)
                        ON DUPLICATE KEY UPDATE name=VALUES(name), position='月嫂', department='护理部', source_note=VALUES(source_note)
                    """, (tenant_id, store_id, f"YS-{store_id}-{index:03d}", name, phone, BATCH, index, BATCH))
                cursor.execute("SELECT staff_id, name FROM staff WHERE tenant_id=%s AND store_id=%s AND source_file=%s ORDER BY staff_id", (tenant_id, store_id, BATCH))
                seeded_matrons = cursor.fetchall()
                people = PEOPLE[store_index]
                current_customers = customer_rows[store_id]
                cursor.execute("SELECT room_id, room_no FROM rooms WHERE store_id=%s AND customer_id IN (%s,%s,%s) ORDER BY room_id", (store_id, *(int(c["id"]) for c in current_customers)))
                occupied_rooms = cursor.fetchall()
                if len(occupied_rooms) < 3:
                    raise RuntimeError(f"Store {store_id} booking linkage is incomplete.")
                for index, (person, customer, room_row) in enumerate(zip(people, current_customers, occupied_rooms), 1):
                    _name, _phone, baby_name = person
                    cursor.execute("SELECT baby_id FROM babies WHERE customer_id=%s AND note LIKE %s LIMIT 1", (int(customer["id"]), BATCH + "%"))
                    existing_baby = cursor.fetchone()
                    if existing_baby:
                        baby_id = int(existing_baby[0])
                    else:
                        cursor.execute("""
                            INSERT INTO babies (tenant_id,store_id,customer_id,name,gender,birth_date,birth_weight,note,created_at)
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        """, (tenant_id, store_id, int(customer["id"]), baby_name, "女" if index % 2 else "男", (date.today() - timedelta(days=5 + index)).isoformat(), 3.1 + index / 10, BATCH, datetime.now().isoformat(timespec="seconds")))
                        baby_id = cursor.lastrowid
                    cursor.execute("SELECT 1 FROM baby_logs WHERE baby_id=%s AND note LIKE %s", (baby_id, BATCH + "%"))
                    if not cursor.fetchone():
                        cursor.execute("""
                            INSERT INTO baby_logs (tenant_id,baby_id,kind,feed_type,amount,metric,metric_value,care_type,note,operator_id,log_time,created_at)
                            VALUES (%s,%s,'护理','母乳',%s,'体温',36.6,'日常观察',%s,%s,%s,%s)
                        """, (tenant_id, baby_id, 60 + index * 10, BATCH, user_id, datetime.now().isoformat(timespec="seconds"), datetime.now().isoformat(timespec="seconds")))
                for module, resources in RESOURCES.items():
                    for resource in resources:
                        for index, (person, room_row) in enumerate(zip(people, occupied_rooms), 1):
                            matron_name = seeded_matrons[index - 1][1] if index <= len(seeded_matrons) else MATRONS[store_index][index - 1][0]
                            payload = record_payload(resource, index, person, str(room_row[1]), str(matron_name))
                            payload["store"] = str(store.get("name") or "")
                            business_no = f"{BATCH[-8:]}-{module[:3]}-{store_id}-{resource[:18]}-{index}"
                            cursor.execute("""
                                INSERT INTO erp_operational_records (
                                  tenant_id,store_id,module_code,resource_code,business_no,status,
                                  payload_json,created_by_user_id,updated_by_user_id
                                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                                ON DUPLICATE KEY UPDATE status=VALUES(status), payload_json=VALUES(payload_json),
                                  updated_by_user_id=VALUES(updated_by_user_id), deleted_at=NULL
                            """, (tenant_id, store_id, module, resource, business_no, payload["status"], json.dumps(payload, ensure_ascii=False), user_id, user_id))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    print(json.dumps({
        "status": "seeded", "batch": BATCH, "stores": len(stores),
        "customers": len(created["customers"]), "contracts": len(created["contracts"]),
        "receipts": len(created["receipts"]), "bookings": len(created["bookings"]),
        "operationalRows": sum(len(rows) for rows in RESOURCES.values()) * 3 * len(stores),
        "cleanup": "python scripts/cleanup_local_acceptance_dataset.py",
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

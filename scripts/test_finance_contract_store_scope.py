#!/usr/bin/env python3
"""Offline regression checks for P0 finance/contract store scoping.

The production integration test still needs MySQL and a running API.  These
checks deliberately run without either dependency so a branch cannot silently
reintroduce implicit-store writes or unscoped finance pickers.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def method_source(name: str) -> str:
    text = source("server/mvp_api.py")
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return ast.get_source_segment(text, node) or ""
    raise AssertionError(f"method not found: {name}")


class StoreScopeRegressionTest(unittest.TestCase):
    def test_finance_and_sales_writes_never_fall_back_to_default_store(self):
        for name in ("_finance_store_id", "_sales_store_id"):
            block = method_source(name)
            self.assertIn("全部门店仅用于查询", block)
            self.assertNotIn("default_store_id", block)
            self.assertNotIn('len(user["store_ids"])', block)

    def test_finance_pickers_require_and_forward_concrete_store(self):
        backend = source("server/mvp_api.py")
        frontend = source("src/views/erp/finance-workbench/index.vue")
        api = source("src/api/erp-finance.js")
        self.assertIn("picker.group(1), query", backend)
        self.assertIn("store_id = self._finance_store_id(connection, user, query)", backend)
        self.assertIn("{ store: this.receiptForm.store }", frontend)
        self.assertIn("{ store: this.dialogForm.store }", frontend)
        self.assertIn("params = {}", api)

    def test_store_is_before_downstream_entities_in_forms(self):
        finance = source("src/config/finance-pages.js")
        receipt = finance[finance.index("'新增收款':"):finance.index("'收款管理':")]
        refund = finance[finance.index("'退款申请':"):finance.index("'退款审核':")]
        sales = source("src/config/sales-pages.js")
        contract = sales[sales.index("'合同管理':"):sales.index("'商品销售':")]
        contract = contract[contract.index("formFields:"):]
        self.assertLess(receipt.index("select('store'"), receipt.index("picker('cashier'"))
        self.assertLess(receipt.index("select('store'"), receipt.index("picker('customerName'"))
        self.assertLess(refund.index("select('store'"), refund.index("picker('customerName'"))
        self.assertLess(contract.index("select('store'"), contract.index("input('customerName'"))

    def test_cross_store_exception_is_limited_to_members(self):
        finance_customer = method_source("_finance_customer_for_store")
        sales_customer = method_source("_sales_customer")
        self.assertIn("customer_accounts", finance_customer)
        self.assertIn("普通客户仅可在所属门店办理", finance_customer)
        self.assertIn("customer_accounts", sales_customer)
        self.assertIn("普通客户仅可在所属门店签约", sales_customer)

    def test_secondary_admin_contract_writes_require_store_context(self):
        contract = source("apps/admin/src/views/contracts/ContractList.vue")
        self.assertIn("const canWriteStore = computed(() => Number(auth.storeId) > 0)", contract)
        self.assertIn(':disabled="!canWriteStore"', contract)
        self.assertIn("storeId: auth.storeId", contract)

    def test_huanghe_contract_requires_a_published_local_package(self):
        resolver = method_source("_resolve_contract_package")
        self.assertIn('"黄河路"', resolver)
        self.assertIn("黄河路店合同必须选择本店已发布套餐", resolver)

    def test_booking_requires_an_approved_receipt(self):
        booking = method_source("_create_booking")
        self.assertIn("status, paid", booking)
        self.assertIn("合同至少有一笔已审核收款后才可订房", booking)


if __name__ == "__main__":
    unittest.main()

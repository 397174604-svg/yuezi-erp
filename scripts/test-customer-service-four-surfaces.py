#!/usr/bin/env python3
import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))

from mvp_api import ApiError, customer_service_transition  # noqa: E402


class CustomerServiceFourSurfaceTests(unittest.TestCase):
    def test_registry_stays_at_104_unique_features(self):
        source = (ROOT / "src/config/erp-feature-registry.js").read_text(encoding="utf-8")
        identifiers = re.findall(r"\['(F\d{3})'", source)
        self.assertEqual(len(identifiers), 104)
        self.assertEqual(len(set(identifiers)), 104)

    def test_four_titles_route_to_four_distinct_components(self):
        router = (ROOT / "src/router/index.js").read_text(encoding="utf-8")
        expected = {
            "满意度回访": "service-satisfaction",
            "AI客服知识库": "service-knowledge",
            "消息通知中心": "service-notification",
            "智能客服": "service-smart-support",
        }
        for title, page_type in expected.items():
            self.assertIn(f"{title}: '{page_type}'", router)
            self.assertIn(f"pageType === '{page_type}'", router)
        self.assertEqual(len(set(expected.values())), 4)

    def test_each_surface_has_its_own_feature_definition(self):
        pages = {
            "satisfaction.vue": "F005",
            "knowledge.vue": "F043",
            "notification.vue": "F084",
            "smart-support.vue": "F094",
        }
        base = ROOT / "src/views/erp/customer-service"
        for filename, feature_code in pages.items():
            source = (base / filename).read_text(encoding="utf-8")
            self.assertIn(f"featureCode: '{feature_code}'", source)
            self.assertIn("actions:", source)
            self.assertIn("fields:", source)
            self.assertIn("metrics:", source)

    def test_member_titles_do_not_fall_back_to_one_shared_page(self):
        source = (ROOT / "src/views/erp/member-workbench/index.vue").read_text(
            encoding="utf-8"
        )
        self.assertIn("const normalizeFeatureTitle", source)
        self.assertIn("pageDefinitionByTitle[normalizeFeatureTitle(this.pageTitle)]", source)
        for feature_code in ("F006", "F008", "F040", "F059", "F060", "F087", "F088"):
            self.assertIn(f"featureId: '{feature_code}'", source)
        router = (ROOT / "src/router/index.js").read_text(encoding="utf-8")
        self.assertIn("资产账单: 'asset-workbench'", router)
        self.assertIn("pageType === 'asset-workbench'", router)

    def test_satisfaction_state_flow(self):
        self.assertEqual(
            customer_service_transition("F005", "待回访", "START"),
            ("跟进中", False),
        )
        self.assertEqual(
            customer_service_transition("F005", "跟进中", "COMPLETE"),
            ("已完成", False),
        )

    def test_knowledge_publish_requires_review_state(self):
        self.assertEqual(
            customer_service_transition("F043", "待审核", "PUBLISH"),
            ("已发布", False),
        )
        with self.assertRaises(ApiError):
            customer_service_transition("F043", "草稿", "PUBLISH")

    def test_internal_message_can_send(self):
        self.assertEqual(
            customer_service_transition("F084", "待发送", "SEND", "站内消息"),
            ("已发送", False),
        )

    def test_external_message_never_reports_fake_success(self):
        self.assertEqual(
            customer_service_transition("F084", "待发送", "SEND", "短信"),
            ("待通道配置", True),
        )
        api = (ROOT / "server/mvp_api.py").read_text(encoding="utf-8")
        self.assertIn("通知未发送；记录已标记为待通道配置", api)
        self.assertRegex(api, r"通知未发送；记录已标记为待通道配置[\s\S]{0,120}503")

    def test_ai_reply_is_explicitly_external(self):
        self.assertEqual(
            customer_service_transition("F094", "处理中", "AI_REPLY"),
            ("处理中", True),
        )
        with self.assertRaises(ApiError):
            customer_service_transition("F094", "待接入", "AI_REPLY")

    def test_migration_has_records_and_logs(self):
        migration = (ROOT / "database/mysql/migrations/V20260801_022__customer_service_surfaces.sql").read_text(encoding="utf-8")
        self.assertIn("CREATE TABLE IF NOT EXISTS customer_service_records", migration)
        self.assertIn("CREATE TABLE IF NOT EXISTS customer_service_logs", migration)
        self.assertIn("feature_code", migration)


if __name__ == "__main__":
    unittest.main(verbosity=2)

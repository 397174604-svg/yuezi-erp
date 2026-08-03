#!/usr/bin/env python3
"""Static acceptance for the nine independent marketing feature surfaces."""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "src/config/marketing-pages.js"
VIEW = ROOT / "src/views/erp/marketing-workbench/index.vue"
ROUTER = ROOT / "src/router/index.js"
P0 = ROOT / "src/config/p0-operations-features.js"

FEATURE_IDS = ("F038", "F039", "F041", "F042", "F085", "F090", "F091", "F092", "F127")


class MarketingFeatureIsolationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = CONFIG.read_text(encoding="utf-8")
        cls.view = VIEW.read_text(encoding="utf-8")
        cls.router = ROUTER.read_text(encoding="utf-8")
        cls.p0 = P0.read_text(encoding="utf-8")

    def block(self, feature_id):
        start = self.config.index(f"  {feature_id}: {{")
        following = [self.config.find(f"  {candidate}: {{", start + 1) for candidate in FEATURE_IDS]
        following = [index for index in following if index > start]
        end = min(following) if following else self.config.index("\n}\n\nexport function", start)
        return self.config[start:end]

    def test_all_nine_features_have_independent_business_definitions(self):
        keys, actions, column_sets, field_sets = [], [], [], []
        for feature_id in FEATURE_IDS:
            block = self.block(feature_id)
            with self.subTest(feature_id=feature_id):
                for token in ("key:", "eyebrow:", "description:", "primaryAction:", "metrics:", "filters:", "columns:", "formFields:", "statuses:"):
                    self.assertIn(token, block)
                self.assertGreaterEqual(block.count("['"), 8)
                keys.append(re.search(r"key: '([^']+)'", block).group(1))
                actions.append(re.search(r"primaryAction: '([^']+)'", block).group(1))
                column_sets.append(re.search(r"columns: \[(.*?)\],\n", block, re.S).group(1))
                field_sets.append(re.search(r"formFields: \[(.*?)\],\n", block, re.S).group(1))
        self.assertEqual(len(set(keys)), 9)
        self.assertEqual(len(set(actions)), 9)
        self.assertEqual(len(set(column_sets)), 9)
        self.assertEqual(len(set(field_sets)), 9)

    def test_four_p0_features_use_marketing_workbench_without_redirect(self):
        for feature_id in ("F038", "F039", "F041", "F042"):
            start = self.p0.index(f"id: '{feature_id}'")
            end = self.p0.find("\n", start)
            record = self.p0[start:end]
            self.assertIn("component: 'marketing'", record)
            self.assertNotIn("canonicalPath", record)

    def test_formal_menu_and_hidden_routes_share_the_marketing_component(self):
        for token in (
            "marketing: 'marketing-workbench'",
            "if (pageType === 'marketing-workbench') return marketingWorkbenchPage",
            "marketing: marketingWorkbenchPage",
        ):
            self.assertIn(token, self.router)

    def test_view_provides_real_local_workflow_without_fake_seed_rows(self):
        for token in (
            "definition.filters",
            "definition.columns",
            "definition.formFields",
            "definition.statuses",
            "advanceRecord",
            "exportRows",
            "请先在顶部选择具体门店",
            "localStorage",
        ):
            self.assertIn(token, self.view)
        self.assertNotIn("示例业务 A", self.config)
        self.assertNotIn("示例业务 B", self.config)


if __name__ == "__main__":
    unittest.main()

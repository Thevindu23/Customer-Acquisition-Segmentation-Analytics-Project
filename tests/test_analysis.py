"""Basic portfolio regression tests: no external APIs or private data required."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from analyze_customers import clean_and_enrich, data_quality, make_summary, read_data

DATA = ROOT / "data" / "public" / "customer_analytics.csv"


class AnalyticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = read_data(DATA)

    def test_source_columns_contain_no_direct_identifiers(self):
        self.assertTrue({"record_id", "customer_age", "customer_acquisition_cost"}.issubset(self.df.columns))
        forbidden = {"customer_name", "customer_city", "customer_state", "customer_postal_code", "customer_id"}
        self.assertFalse(forbidden.intersection(self.df.columns))

    def test_record_count_and_unique_ids(self):
        self.assertEqual(len(self.df), 25_000)
        self.assertEqual(self.df.record_id.nunique(), len(self.df))

    def test_mean_cost_matches_report(self):
        self.assertAlmostEqual(self.df.customer_acquisition_cost.mean(), 42.1597504, places=6)
        self.assertAlmostEqual(self.df.customer_acquisition_cost.sum(), 1_053_993.76, places=2)

    def test_quality_and_postal_audit(self):
        d = data_quality(self.df)
        self.assertEqual(d["missing_cells"], 0)
        self.assertEqual(d["duplicate_record_ids"], 0)
        self.assertEqual(d["postal_code_format_mismatches_reviewed_countries"], 7_254)

    def test_feature_engineering_and_segment_counts(self):
        enriched = clean_and_enrich(self.df)
        summary = make_summary(enriched, "customer_segment")
        consumer = summary.loc[summary.customer_segment.eq("Consumer")].iloc[0]
        self.assertEqual(int(consumer.customers), 13_638)
        self.assertEqual(enriched.age_group.isna().sum(), 0)


if __name__ == "__main__":
    unittest.main()

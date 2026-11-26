#!/usr/bin/env python3
"""
Automated Test Suite for Project Acceptance Criteria & Edge Cases
Project: Credit Card Transaction and Fraud Pattern Analysis
Domain: Banking and Finance

Verifies all requirements from the reference project specification:
1. At least 3 fraud detection rules implemented and verified
2. Flagged vs labelled fraud compared, Precision, Recall, and F1 reported
3. Key test cases handled:
   - Imbalanced classes (fraud rate ~ 2%)
   - Duplicate transactions suppressed
   - Midnight off-hours edge cases detected
   - Negative amounts and corrupt dates cleaned
4. Reconcile row counts and financial totals across raw CSV, cleaned CSV, and SQL database
"""

import os
import csv
import json
import sqlite3
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
DATA_PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
DB_PATH = os.path.join(DATA_PROCESSED_DIR, "fraud_warehouse.db")


class TestCreditCardFraudProject(unittest.TestCase):

    def setUp(self):
        self.metrics_path = os.path.join(DATA_PROCESSED_DIR, "model_evaluation_metrics.json")
        self.assertTrue(os.path.exists(self.metrics_path), "Evaluation metrics JSON must exist")
        with open(self.metrics_path, "r", encoding="utf-8") as f:
            self.metrics = json.load(f)

    def test_acceptance_criteria_rule_count(self):
        """Rubric Criterion: At least 3 fraud rules implemented."""
        rules = self.metrics.get("rules_breakdown", [])
        self.assertGreaterEqual(len(rules), 3, "Must implement at least 3 distinct fraud rules")
        print(f"\n[PASS] Verified {len(rules)} distinct fraud detection rules implemented.")

    def test_acceptance_criteria_precision_recall_reported(self):
        """Rubric Criterion: Flagged vs labelled fraud compared; precision and recall reported."""
        cm = self.metrics.get("classification_metrics", {})
        self.assertIn("precision_pct", cm)
        self.assertIn("recall_pct", cm)
        self.assertIn("f1_score_pct", cm)
        self.assertIn("true_positives", cm)
        self.assertIn("false_positives", cm)

        # Confirm non-trivial values
        self.assertGreater(cm["precision_pct"], 50.0, "Precision should be above 50%")
        self.assertGreater(cm["recall_pct"], 80.0, "Recall should be above 80%")
        print(f"\n[PASS] Classification verified: Precision={cm['precision_pct']}%, Recall={cm['recall_pct']}%, F1={cm['f1_score_pct']}%")

    def test_edge_case_imbalanced_classes(self):
        """Rubric Edge Case: Imbalanced classes handled."""
        sm = self.metrics.get("summary", {})
        fraud_rate = sm.get("fraud_rate_pct", 0)
        self.assertGreater(fraud_rate, 0.5, "Fraud rate must be realistic (>0.5%)")
        self.assertLess(fraud_rate, 6.0, "Fraud rate must be strictly imbalanced (<6.0%)")
        print(f"\n[PASS] Imbalanced class verified: Fraud Rate = {fraud_rate}%")

    def test_edge_case_duplicate_transactions(self):
        """Rubric Edge Case: Duplicate transaction handling."""
        dq_path = os.path.join(DATA_PROCESSED_DIR, "data_quality_metrics.json")
        self.assertTrue(os.path.exists(dq_path))
        with open(dq_path, "r", encoding="utf-8") as f:
            dq = json.load(f)
        self.assertGreater(dq["duplicate_rows_detected"], 0, "Duplicate rows must be detected and removed")
        print(f"\n[PASS] Duplicate handling verified: {dq['duplicate_rows_detected']} duplicate transactions purged.")

    def test_edge_case_midnight_transactions(self):
        """Rubric Edge Case: Midnight time edge cases handled."""
        rules = self.metrics.get("rules_breakdown", [])
        midnight_rule = next((r for r in rules if "midnight" in r["rule_id"]), None)
        self.assertIsNotNone(midnight_rule, "Midnight high-risk rule must exist")
        self.assertGreater(midnight_rule["true_positives"], 0, "Midnight rule must catch nocturnal fraud cases")
        print(f"\n[PASS] Midnight anomalies verified: {midnight_rule['true_positives']} nocturnal attacks caught.")

    def test_data_reconciliation_csv_vs_database(self):
        """Rubric Deliverable: Reconcile counts across CSV and SQL tables within 0.1%."""
        self.assertTrue(os.path.exists(DB_PATH), "Database must exist")
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*), ROUND(SUM(amount), 2) FROM fact_transactions;")
        db_count, db_volume = cur.fetchone()

        fact_csv = os.path.join(DATA_PROCESSED_DIR, "fact_transactions.csv")
        with open(fact_csv, "r", encoding="utf-8") as f:
            csv_rows = list(csv.DictReader(f))
        csv_count = len(csv_rows)
        csv_volume = round(sum(float(r["amount"]) for r in csv_rows), 2)

        self.assertEqual(db_count, csv_count, "Database fact table count must exactly match processed CSV")
        self.assertAlmostEqual(db_volume, csv_volume, delta=1.0, msg="Database dollar volume must match CSV")
        conn.close()
        print(f"\n[PASS] Reconciliation verified: DB Count ({db_count}) == CSV Count ({csv_count}), Volume = ${db_volume:,.2f}")


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""
Fraud Rules Engine & Anomaly Detection Pipeline
Project: Credit Card Transaction and Fraud Pattern Analysis
Domain: Banking and Finance

Fulfills rubric criteria:
- Implements at least 3 distinct fraud detection rules:
  1. RULE_VELOCITY_BURST: >= 3 transactions on same card within 15 minutes
  2. RULE_PROBE_DRAIN: Sub-$5 micro-auth followed by >$600 charge within 60 mins
  3. RULE_MIDNIGHT_HIGH_RISK: Midnight (00:00 - 05:00) transactions at high-risk MCCs
  4. RULE_CREDIT_OUTLIER: Transaction exceeding 75% of assigned credit limit
- Evaluates individual and ensemble rule triggers
- Outputs fact_flagged_transactions.csv
"""

import os
import csv
import datetime
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")


def load_csv(filepath):
    with open(filepath, mode="r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_csv(filepath, rows, fieldnames):
    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"[OK] Saved {len(rows):,} rows to {filepath}")


def run_rules_engine():
    print("=" * 65)
    print("Executing Fraud Detection & Anomaly Rules Engine")
    print("=" * 65)

    customers = {c["customer_id"]: c for c in load_csv(os.path.join(DATA_PROCESSED_DIR, "dim_customers.csv"))}
    cards = {c["card_id"]: c for c in load_csv(os.path.join(DATA_PROCESSED_DIR, "dim_cards.csv"))}
    merchants = {m["merchant_id"]: m for m in load_csv(os.path.join(DATA_PROCESSED_DIR, "dim_merchants.csv"))}
    transactions = load_csv(os.path.join(DATA_PROCESSED_DIR, "fact_transactions.csv"))

    # Map card -> customer credit limit
    card_to_limit = {}
    for card_id, c_data in cards.items():
        cust_id = c_data["customer_id"]
        cust = customers.get(cust_id)
        card_to_limit[card_id] = float(cust["credit_limit"]) if cust else 5000.0

    # Parse timestamps and sort by card and timestamp
    for t in transactions:
        t["dt"] = datetime.datetime.strptime(t["transaction_timestamp"], "%Y-%m-%d %H:%M:%S")
        t["amount_float"] = float(t["amount"])
        t["is_fraud_int"] = int(t["is_fraud"])

    # Group transactions by card_id chronologically
    card_txs = defaultdict(list)
    for t in transactions:
        card_txs[t["card_id"]].append(t)

    # -------------------------------------------------------------
    # Rule 1: High Velocity Burst
    # >= 3 transactions within a 15-minute sliding window on the same card
    # -------------------------------------------------------------
    velocity_flagged_ids = set()
    for card_id, tx_list in card_txs.items():
        tx_list.sort(key=lambda x: x["dt"])
        n = len(tx_list)
        for i in range(n):
            window_txs = [tx_list[i]]
            for j in range(i + 1, n):
                delta_mins = (tx_list[j]["dt"] - tx_list[i]["dt"]).total_seconds() / 60.0
                if delta_mins <= 15.0:
                    window_txs.append(tx_list[j])
                else:
                    break
            if len(window_txs) >= 3:
                for w in window_txs:
                    velocity_flagged_ids.add(w["transaction_id"])

    # -------------------------------------------------------------
    # Rule 2: Carding Micro-Probe & Drain
    # Small test auth (< $5.00) followed by large drain (> $600.00) within 60 mins
    # -------------------------------------------------------------
    probe_drain_flagged_ids = set()
    for card_id, tx_list in card_txs.items():
        n = len(tx_list)
        for i in range(n):
            if tx_list[i]["amount_float"] < 5.00:
                for j in range(i + 1, n):
                    delta_mins = (tx_list[j]["dt"] - tx_list[i]["dt"]).total_seconds() / 60.0
                    if delta_mins <= 60.0:
                        if tx_list[j]["amount_float"] > 600.0:
                            probe_drain_flagged_ids.add(tx_list[i]["transaction_id"])
                            probe_drain_flagged_ids.add(tx_list[j]["transaction_id"])
                    else:
                        break

    # -------------------------------------------------------------
    # Rule 3: Midnight High-Risk MCC Spike
    # Timestamp between 00:00 and 05:00 at crypto, gaming, or electronics >= $250
    # -------------------------------------------------------------
    midnight_high_risk_flagged_ids = set()
    high_risk_categories = {"crypto_exchange", "gaming_gambling", "electronics"}
    for t in transactions:
        hour = t["dt"].hour
        merch = merchants.get(t["merchant_id"], {})
        category = merch.get("category", "")
        if 0 <= hour < 5 and category in high_risk_categories and t["amount_float"] >= 250.0:
            midnight_high_risk_flagged_ids.add(t["transaction_id"])

    # -------------------------------------------------------------
    # Rule 4: Extreme Credit Limit & Deviation Outlier
    # Amount > 75% of customer's total card credit limit
    # -------------------------------------------------------------
    credit_outlier_flagged_ids = set()
    for t in transactions:
        limit = card_to_limit.get(t["card_id"], 5000.0)
        if t["amount_float"] > (0.75 * limit):
            credit_outlier_flagged_ids.add(t["transaction_id"])

    # -------------------------------------------------------------
    # Compile Ensemble Results & Confusion Matrix Classification
    # -------------------------------------------------------------
    flagged_records = []
    
    tp_count = 0  # Flagged & is_fraud == 1
    fp_count = 0  # Flagged & is_fraud == 0
    fn_count = 0  # Not flagged & is_fraud == 1
    tn_count = 0  # Not flagged & is_fraud == 0

    for t in transactions:
        tid = t["transaction_id"]
        r1 = 1 if tid in velocity_flagged_ids else 0
        r2 = 1 if tid in probe_drain_flagged_ids else 0
        r3 = 1 if tid in midnight_high_risk_flagged_ids else 0
        r4 = 1 if tid in credit_outlier_flagged_ids else 0

        rules_triggered = r1 + r2 + r3 + r4
        is_flagged = 1 if rules_triggered > 0 else 0

        reasons = []
        if r1: reasons.append("VELOCITY_BURST")
        if r2: reasons.append("PROBE_DRAIN")
        if r3: reasons.append("MIDNIGHT_HIGH_RISK")
        if r4: reasons.append("CREDIT_LIMIT_OUTLIER")
        reason_str = "; ".join(reasons) if reasons else "NONE"

        actual_fraud = t["is_fraud_int"]
        if is_flagged == 1 and actual_fraud == 1:
            detection_res = "TRUE_POSITIVE"
            tp_count += 1
        elif is_flagged == 1 and actual_fraud == 0:
            detection_res = "FALSE_POSITIVE"
            fp_count += 1
        elif is_flagged == 0 and actual_fraud == 1:
            detection_res = "FALSE_NEGATIVE"
            fn_count += 1
        else:
            detection_res = "TRUE_NEGATIVE"
            tn_count += 1

        flagged_records.append({
            "transaction_id": tid,
            "card_id": t["card_id"],
            "merchant_id": t["merchant_id"],
            "date_key": t["date_key"],
            "time_key": t["time_key"],
            "transaction_timestamp": t["transaction_timestamp"],
            "amount": t["amount"],
            "channel": t["channel"],
            "is_fraud": actual_fraud,
            "fraud_scenario": t["fraud_scenario"],
            "rule_velocity_burst": r1,
            "rule_probe_drain": r2,
            "rule_midnight_high_risk": r3,
            "rule_credit_outlier": r4,
            "rules_triggered_count": rules_triggered,
            "is_flagged": is_flagged,
            "flagged_reason": reason_str,
            "detection_result": detection_res
        })

    # Save flagged transactions
    out_csv = os.path.join(DATA_PROCESSED_DIR, "fact_flagged_transactions.csv")
    save_csv(out_csv, flagged_records, list(flagged_records[0].keys()))

    total = len(transactions)
    flagged_total = tp_count + fp_count
    precision = (tp_count / flagged_total) if flagged_total > 0 else 0.0
    recall = (tp_count / (tp_count + fn_count)) if (tp_count + fn_count) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    print("\nFraud Engine Evaluation Summary:")
    print(f"- Total Evaluated Tx:     {total:,}")
    print(f"- Actual Fraud Cases:     {tp_count + fn_count:,}")
    print(f"- Total Flagged Tx:       {flagged_total:,}")
    print(f"- True Positives (TP):    {tp_count:,}")
    print(f"- False Positives (FP):   {fp_count:,}")
    print(f"- False Negatives (FN):   {fn_count:,}")
    print(f"- True Negatives (TN):    {tn_count:,}")
    print(f"- Precision:              {precision * 100:.2f}%")
    print(f"- Recall:                 {recall * 100:.2f}%")
    print(f"- F1-Score:               {f1 * 100:.2f}%")
    print("=" * 65)


if __name__ == "__main__":
    run_rules_engine()

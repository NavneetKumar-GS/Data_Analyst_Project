#!/usr/bin/env python3
"""
Dashboard Data Exporter
Project: Credit Card Transaction and Fraud Pattern Analysis
Domain: Banking and Finance

Exports processed metrics, aggregations, and flagged transactions to dashboard/data.js
so the standalone HTML dashboard runs locally without CORS restrictions or external web servers.
"""

import os
import csv
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
DASHBOARD_DIR = os.path.join(BASE_DIR, "dashboard")


def load_csv(filepath):
    with open(filepath, mode="r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def export_data():
    print("Exporting data for interactive dashboard...")
    metrics_path = os.path.join(DATA_PROCESSED_DIR, "model_evaluation_metrics.json")
    with open(metrics_path, "r", encoding="utf-8") as f:
        model_metrics = json.load(f)

    customers = {c["customer_id"]: c for c in load_csv(os.path.join(DATA_PROCESSED_DIR, "dim_customers.csv"))}
    cards = {c["card_id"]: c for c in load_csv(os.path.join(DATA_PROCESSED_DIR, "dim_cards.csv"))}
    merchants = {m["merchant_id"]: m for m in load_csv(os.path.join(DATA_PROCESSED_DIR, "dim_merchants.csv"))}
    flagged = load_csv(os.path.join(DATA_PROCESSED_DIR, "fact_flagged_transactions.csv"))
    dates = load_csv(os.path.join(DATA_PROCESSED_DIR, "dim_dates.csv"))

    # Daily trend aggregations
    daily_map = {}
    for d in dates:
        daily_map[d["full_date"]] = {
            "date": d["full_date"],
            "total_spend": 0.0,
            "fraud_dollars": 0.0,
            "fraud_count": 0,
            "tx_count": 0
        }

    # Hourly distribution
    hourly_counts = {h: {"hour": h, "fraud": 0, "legit": 0, "fraud_dollars": 0.0} for h in range(24)}

    # Flagged enriched transactions list
    enriched_flagged = []
    for t in flagged:
        dt_str = t["transaction_timestamp"]
        date_part = dt_str.split(" ")[0]
        hour_part = int(dt_str.split(" ")[1].split(":")[0])
        amt = float(t["amount"])
        is_f = int(t["is_fraud"])

        if date_part in daily_map:
            daily_map[date_part]["total_spend"] += amt
            daily_map[date_part]["tx_count"] += 1
            if is_f == 1:
                daily_map[date_part]["fraud_dollars"] += amt
                daily_map[date_part]["fraud_count"] += 1

        if is_f == 1:
            hourly_counts[hour_part]["fraud"] += 1
            hourly_counts[hour_part]["fraud_dollars"] += amt
        else:
            hourly_counts[hour_part]["legit"] += 1

        if t["is_flagged"] == "1":
            card = cards.get(t["card_id"], {})
            cust = customers.get(card.get("customer_id", ""), {})
            merch = merchants.get(t["merchant_id"], {})
            enriched_flagged.append({
                "id": t["transaction_id"],
                "timestamp": t["transaction_timestamp"],
                "card_number": card.get("card_number_masked", "Unknown"),
                "customer_name": cust.get("full_name", "Unknown"),
                "customer_tier": cust.get("risk_tier", "Moderate"),
                "credit_limit": float(cust.get("credit_limit", 5000)),
                "merchant_name": merch.get("merchant_name", "Unknown"),
                "merchant_category": merch.get("category", "Unknown"),
                "amount": amt,
                "channel": t["channel"],
                "is_fraud": is_f,
                "reasons": t["flagged_reason"],
                "result": t["detection_result"],
                "rule_velocity": int(t["rule_velocity_burst"]),
                "rule_probe": int(t["rule_probe_drain"]),
                "rule_midnight": int(t["rule_midnight_high_risk"]),
                "rule_credit": int(t["rule_credit_outlier"])
            })

    daily_trend = sorted(list(daily_map.values()), key=lambda x: x["date"])
    hourly_list = [hourly_counts[h] for h in range(24)]

    dashboard_bundle = {
        "metrics": model_metrics,
        "daily_trend": daily_trend,
        "hourly_distribution": hourly_list,
        "flagged_transactions": enriched_flagged
    }

    out_js = os.path.join(DASHBOARD_DIR, "data.js")
    with open(out_js, "w", encoding="utf-8") as f:
        f.write("const DASHBOARD_DATA = " + json.dumps(dashboard_bundle, indent=2) + ";\n")
    print(f"[OK] Exported dashboard bundle to {out_js} ({len(enriched_flagged)} flagged records)")


if __name__ == "__main__":
    export_data()

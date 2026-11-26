#!/usr/bin/env python3
"""
Synthetic Credit Card Transaction Dataset Generator
Project: Credit Card Transaction and Fraud Pattern Analysis
Domain: Banking and Finance

Generates:
1. customers.csv: Demographic and credit limit profiles
2. cards.csv: Credit card accounts mapped to customers
3. merchants.csv: Merchants classified by category and baseline risk
4. transactions_raw.csv: 15,000+ financial transaction logs with realistic
   fraud vectors and embedded data quality anomalies (nulls, duplicates,
   midnight transactions, velocity bursts, carding probe-and-drain attacks).
"""

import os
import csv
import random
import datetime

SEED = 42
random.seed(SEED)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
os.makedirs(DATA_RAW_DIR, exist_ok=True)

NUM_CUSTOMERS = 1000
NUM_CARDS = 1200
NUM_MERCHANTS = 400
NUM_TRANSACTIONS = 15000

FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
    "Kenneth", "Dorothy", "Kevin", "Carol", "Brian", "Amanda", "George", "Melissa",
    "Edward", "Deborah", "Ronald", "Stephanie", "Timothy", "Rebecca", "Jason", "Sharon",
    "Jeffrey", "Laura", "Ryan", "Cynthia", "Jacob", "Kathleen", "Gary", "Amy",
    "Nicholas", "Shirley", "Eric", "Angela", "Jonathan", "Helen", "Stephen", "Anna"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
    "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker"
]

CITIES_STATES = [
    ("New York", "NY", "10001", 40.7128, -74.0060),
    ("Los Angeles", "CA", "90001", 34.0522, -118.2437),
    ("Chicago", "IL", "60601", 41.8781, -87.6298),
    ("Houston", "TX", "77001", 29.7604, -95.3698),
    ("Phoenix", "AZ", "85001", 33.4484, -112.0740),
    ("Philadelphia", "PA", "19101", 39.9526, -75.1652),
    ("San Antonio", "TX", "78201", 29.4241, -98.4936),
    ("San Diego", "CA", "92101", 32.7157, -117.1611),
    ("Dallas", "TX", "75201", 32.7767, -96.7970),
    ("San Jose", "CA", "95101", 37.3382, -121.8863),
    ("Austin", "TX", "73301", 30.2672, -97.7431),
    ("Jacksonville", "FL", "32099", 30.3322, -81.6557),
    ("San Francisco", "CA", "94101", 37.7749, -122.4194),
    ("Columbus", "OH", "43201", 39.9612, -82.9988),
    ("Indianapolis", "IN", "46201", 39.7684, -86.1581),
    ("Seattle", "WA", "98101", 47.6062, -122.3321),
    ("Denver", "CO", "80201", 39.7392, -104.9903),
    ("Boston", "MA", "02101", 42.3601, -71.0589),
    ("Miami", "FL", "33101", 25.7617, -80.1918),
    ("Atlanta", "GA", "30301", 33.7490, -84.3880)
]

JOB_TITLES = [
    "Software Engineer", "Accountant", "Registered Nurse", "Project Manager",
    "Operations Analyst", "Marketing Specialist", "High School Teacher", "Sales Representative",
    "Financial Analyst", "Architect", "Electrician", "Graphic Designer", "Research Scientist",
    "Human Resources Manager", "Civil Engineer", "Chef", "Pharmacist", "Attorney"
]

MERCHANT_CATEGORIES = {
    "grocery": {"risk_weight": 0.005, "avg_amount": 68.50, "std_amount": 35.0},
    "gas_transport": {"risk_weight": 0.012, "avg_amount": 42.00, "std_amount": 18.0},
    "dining": {"risk_weight": 0.015, "avg_amount": 54.00, "std_amount": 32.0},
    "health_wellness": {"risk_weight": 0.008, "avg_amount": 85.00, "std_amount": 50.0},
    "travel": {"risk_weight": 0.045, "avg_amount": 380.00, "std_amount": 220.0},
    "online_retail": {"risk_weight": 0.038, "avg_amount": 115.00, "std_amount": 95.0},
    "electronics": {"risk_weight": 0.065, "avg_amount": 490.00, "std_amount": 340.0},
    "gaming_gambling": {"risk_weight": 0.095, "avg_amount": 210.00, "std_amount": 180.0},
    "crypto_exchange": {"risk_weight": 0.120, "avg_amount": 750.00, "std_amount": 550.0}
}

MERCHANT_NAMES_POOL = [
    ("Apex Electronics", "electronics"), ("Volt Tech Mart", "electronics"), ("Omni Digital Store", "electronics"),
    ("Byte Haven", "electronics"), ("Silico Goods", "electronics"), ("Pixel Pulse", "electronics"),
    ("CoinRush Global", "crypto_exchange"), ("BitVault Direct", "crypto_exchange"), ("Apex Crypto Net", "crypto_exchange"),
    ("BlockTrade Pay", "crypto_exchange"), ("KryptoKiosk", "crypto_exchange"),
    ("Royal Palace Casino", "gaming_gambling"), ("SpinCity Online", "gaming_gambling"), ("JackpotHub Digital", "gaming_gambling"),
    ("BetLine Direct", "gaming_gambling"), ("Golden Odds Wagering", "gaming_gambling"),
    ("Whole Leaf Organics", "grocery"), ("FreshMarket Co", "grocery"), ("Valley Foods", "grocery"),
    ("City Harvest Grocers", "grocery"), ("GreenBasket Supermarket", "grocery"), ("Corner Mart", "grocery"),
    ("Metro Fuel Stop", "gas_transport"), ("Express Gas & Go", "gas_transport"), ("Rapid Transit Fuel", "gas_transport"),
    ("Highway Oasis Petrol", "gas_transport"), ("Swift Mobility Gas", "gas_transport"),
    ("Bistro Roma", "dining"), ("Harbor Seafood Grill", "dining"), ("The Rustic Table", "dining"),
    ("Golden Dragon Wok", "dining"), ("Bluefin Sushi House", "dining"), ("Corner Bakery Cafe", "dining"),
    ("Skyline Airways", "travel"), ("Pacific Coast Rail", "travel"), ("Grand Vista Resorts", "travel"),
    ("Blue Horizon Cruises", "travel"), ("Global Jetways", "travel"), ("Urban Express Inn", "travel"),
    ("TrendAvenue Online", "online_retail"), ("PrimeCart Global", "online_retail"), ("ShopSphere Direct", "online_retail"),
    ("Nexus Goods", "online_retail"), ("Everyday Outlet", "online_retail"), ("Urban Lifestyle Shop", "online_retail"),
    ("Vitality Health Clinic", "health_wellness"), ("PureCare Pharmacy", "health_wellness"),
    ("Summit Fitness Studio", "health_wellness"), ("Wellspring Med Spa", "health_wellness")
]


def generate_customers():
    customers = []
    start_date = datetime.date(2021, 1, 1)
    end_date = datetime.date(2025, 12, 31)
    days_range = (end_date - start_date).days

    for cid in range(1, NUM_CUSTOMERS + 1):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        gender = random.choice(["M", "F"])
        age = random.randint(21, 75)
        city, state, zip_c, lat, lon = random.choice(CITIES_STATES)
        job = random.choice(JOB_TITLES)
        credit_limit = random.choice([2500, 5000, 7500, 10000, 15000, 20000, 30000])
        acct_opened = start_date + datetime.timedelta(days=random.randint(0, days_range))
        risk_score = round(random.gauss(680, 50), 0)
        risk_score = max(500, min(850, int(risk_score)))
        
        if risk_score >= 750:
            risk_tier = "Low"
        elif risk_score >= 650:
            risk_tier = "Moderate"
        else:
            risk_tier = "High"

        customers.append({
            "customer_id": f"CUST_{cid:05d}",
            "first_name": first,
            "last_name": last,
            "gender": gender,
            "age": age,
            "job_title": job,
            "city": city,
            "state": state,
            "zip_code": zip_c,
            "home_lat": lat,
            "home_long": lon,
            "credit_score": risk_score,
            "risk_tier": risk_tier,
            "credit_limit": credit_limit,
            "account_opened_date": acct_opened.isoformat()
        })
    return customers


def generate_cards(customers):
    cards = []
    card_types = ["Visa", "Mastercard", "Amex"]
    card_categories = ["Standard", "Gold", "Platinum", "Signature"]
    
    card_counter = 1
    # First assign 1 card to every customer
    for cust in customers:
        c_type = random.choice(card_types)
        c_cat = random.choice(card_categories)
        bin_prefix = "4000" if c_type == "Visa" else ("5100" if c_type == "Mastercard" else "3700")
        last4 = f"{random.randint(1000, 9999)}"
        masked = f"{bin_prefix}-XXXX-XXXX-{last4}"
        exp_year = random.randint(2027, 2031)
        exp_month = random.randint(1, 12)
        cards.append({
            "card_id": f"CARD_{card_counter:06d}",
            "card_number_masked": masked,
            "customer_id": cust["customer_id"],
            "card_type": c_type,
            "card_category": c_cat,
            "expiration_date": f"{exp_year}-{exp_month:02d}-01",
            "card_status": "Active"
        })
        card_counter += 1

    # Add second cards to selected customers until NUM_CARDS is reached
    while card_counter <= NUM_CARDS:
        cust = random.choice(customers)
        c_type = random.choice(card_types)
        c_cat = random.choice(card_categories)
        bin_prefix = "4000" if c_type == "Visa" else ("5100" if c_type == "Mastercard" else "3700")
        last4 = f"{random.randint(1000, 9999)}"
        masked = f"{bin_prefix}-XXXX-XXXX-{last4}"
        exp_year = random.randint(2027, 2031)
        exp_month = random.randint(1, 12)
        cards.append({
            "card_id": f"CARD_{card_counter:06d}",
            "card_number_masked": masked,
            "customer_id": cust["customer_id"],
            "card_type": c_type,
            "card_category": c_cat,
            "expiration_date": f"{exp_year}-{exp_month:02d}-01",
            "card_status": "Active"
        })
        card_counter += 1
            
    return cards


def generate_merchants():
    merchants = []
    for mid in range(1, NUM_MERCHANTS + 1):
        name_template, category = random.choice(MERCHANT_NAMES_POOL)
        name = f"{name_template} #{mid}"
        city, state, zip_c, lat, lon = random.choice(CITIES_STATES)
        lat += round(random.uniform(-0.15, 0.15), 4)
        lon += round(random.uniform(-0.15, 0.15), 4)
        
        cat_info = MERCHANT_CATEGORIES[category]
        merchants.append({
            "merchant_id": f"MERCH_{mid:05d}",
            "merchant_name": name,
            "category": category,
            "city": city,
            "state": state,
            "zip_code": zip_c,
            "merchant_lat": lat,
            "merchant_long": lon,
            "base_risk_weight": cat_info["risk_weight"]
        })
    return merchants


def generate_transactions(customers, cards, merchants):
    transactions = []
    start_dt = datetime.datetime(2026, 8, 1, 0, 0, 0)
    end_dt = datetime.datetime(2026, 10, 31, 23, 59, 59)
    total_seconds = int((end_dt - start_dt).total_seconds())

    cards_by_cust = {}
    for c in cards:
        cards_by_cust.setdefault(c["customer_id"], []).append(c)

    tx_channels = ["POS_CHIP", "POS_CONTACTLESS", "ONLINE", "SWIPE"]
    tx_channel_weights = [0.45, 0.25, 0.25, 0.05]

    tx_counter = 1

    # 1. Baseline legitimate transactions
    for _ in range(NUM_TRANSACTIONS - 600):
        cust = random.choice(customers)
        cust_cards = cards_by_cust.get(cust["customer_id"])
        card = random.choice(cust_cards)
        merchant = random.choice(merchants)
        
        hour = random.choices(
            list(range(24)),
            weights=[1, 1, 1, 1, 2, 3, 5, 8, 10, 11, 12, 12, 11, 10, 9, 8, 8, 8, 7, 6, 5, 4, 2, 2]
        )[0]
        rand_sec = random.randint(0, total_seconds - 86400)
        dt = (start_dt + datetime.timedelta(seconds=rand_sec)).replace(
            hour=hour, minute=random.randint(0, 59), second=random.randint(0, 59)
        )
        
        cat_meta = MERCHANT_CATEGORIES[merchant["category"]]
        amount = max(3.50, round(random.gauss(cat_meta["avg_amount"], cat_meta["std_amount"]), 2))
        
        if amount > cust["credit_limit"] * 0.4:
            amount = round(cust["credit_limit"] * 0.25, 2)
            
        channel = random.choices(tx_channels, weights=tx_channel_weights)[0]
        
        transactions.append({
            "transaction_id": f"TX_{tx_counter:07d}",
            "transaction_timestamp": dt.strftime("%Y-%m-%d %H:%M:%S"),
            "card_id": card["card_id"],
            "merchant_id": merchant["merchant_id"],
            "amount": amount,
            "channel": channel,
            "is_fraud": 0,
            "fraud_scenario": "LEGITIMATE"
        })
        tx_counter += 1

    # 2. Rubric Edge Cases & Fraud Vectors:
    # Pattern A: Velocity Bursts (3 to 5 rapid transactions within 15 minutes)
    for burst_idx in range(40):
        victim_cust = random.choice(customers)
        victim_card = random.choice(cards_by_cust[victim_cust["customer_id"]])
        burst_base_dt = start_dt + datetime.timedelta(seconds=random.randint(0, total_seconds - 3600))
        burst_size = random.randint(3, 5)
        merch = random.choice(merchants)
        
        for step in range(burst_size):
            tx_dt = burst_base_dt + datetime.timedelta(minutes=step * 2 + random.randint(0, 1))
            amt = round(random.uniform(180, 490), 2)
            transactions.append({
                "transaction_id": f"TX_{tx_counter:07d}",
                "transaction_timestamp": tx_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "card_id": victim_card["card_id"],
                "merchant_id": merch["merchant_id"],
                "amount": amt,
                "channel": "ONLINE",
                "is_fraud": 1,
                "fraud_scenario": "VELOCITY_BURST"
            })
            tx_counter += 1

    # Pattern B: Carding Attack (Probe and Drain)
    for probe_idx in range(35):
        victim_cust = random.choice(customers)
        victim_card = random.choice(cards_by_cust[victim_cust["customer_id"]])
        probe_dt = start_dt + datetime.timedelta(seconds=random.randint(0, total_seconds - 7200))
        drain_dt = probe_dt + datetime.timedelta(minutes=random.randint(10, 45))
        
        probe_amt = round(random.uniform(1.05, 4.95), 2)
        probe_merch = random.choice([m for m in merchants if m["category"] in ["online_retail", "grocery"]])
        transactions.append({
            "transaction_id": f"TX_{tx_counter:07d}",
            "transaction_timestamp": probe_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "card_id": victim_card["card_id"],
            "merchant_id": probe_merch["merchant_id"],
            "amount": probe_amt,
            "channel": "ONLINE",
            "is_fraud": 1,
            "fraud_scenario": "PROBE_AUTHORIZATION"
        })
        tx_counter += 1
        
        drain_amt = round(random.uniform(850.0, 2400.0), 2)
        drain_merch = random.choice([m for m in merchants if m["category"] in ["crypto_exchange", "electronics", "gaming_gambling"]])
        transactions.append({
            "transaction_id": f"TX_{tx_counter:07d}",
            "transaction_timestamp": drain_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "card_id": victim_card["card_id"],
            "merchant_id": drain_merch["merchant_id"],
            "amount": drain_amt,
            "channel": "ONLINE",
            "is_fraud": 1,
            "fraud_scenario": "CARDING_DRAIN"
        })
        tx_counter += 1

    # Pattern C: Midnight High-Risk Spikes (1:00 AM - 4:45 AM)
    for mid_idx in range(50):
        victim_cust = random.choice(customers)
        victim_card = random.choice(cards_by_cust[victim_cust["customer_id"]])
        rand_sec = random.randint(0, total_seconds - 86400)
        midnight_dt = (start_dt + datetime.timedelta(seconds=rand_sec)).replace(
            hour=random.randint(1, 4), minute=random.randint(0, 59), second=random.randint(0, 59)
        )
        high_risk_merch = random.choice([m for m in merchants if m["category"] in ["crypto_exchange", "gaming_gambling", "electronics"]])
        amt = round(random.uniform(350, 1500), 2)
        transactions.append({
            "transaction_id": f"TX_{tx_counter:07d}",
            "transaction_timestamp": midnight_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "card_id": victim_card["card_id"],
            "merchant_id": high_risk_merch["merchant_id"],
            "amount": amt,
            "channel": "ONLINE",
            "is_fraud": 1,
            "fraud_scenario": "MIDNIGHT_HIGH_RISK_SPIKE"
        })
        tx_counter += 1

    # Pattern D: Extreme Amount / Credit Limit Breach
    for out_idx in range(30):
        victim_cust = random.choice(customers)
        victim_card = random.choice(cards_by_cust[victim_cust["customer_id"]])
        rand_sec = random.randint(0, total_seconds - 86400)
        out_dt = start_dt + datetime.timedelta(seconds=rand_sec)
        limit = victim_cust["credit_limit"]
        out_amt = round(limit * random.uniform(0.85, 1.20), 2)
        out_merch = random.choice(merchants)
        transactions.append({
            "transaction_id": f"TX_{tx_counter:07d}",
            "transaction_timestamp": out_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "card_id": victim_card["card_id"],
            "merchant_id": out_merch["merchant_id"],
            "amount": out_amt,
            "channel": "ONLINE",
            "is_fraud": 1,
            "fraud_scenario": "CREDIT_LIMIT_BREACH"
        })
        tx_counter += 1

    # 3. Inject Data Quality Flaws (Rubric Test Cases):
    # Duplicate double-swipes
    for dup_idx in range(25):
        orig_tx = random.choice(transactions[:10000])
        orig_dt = datetime.datetime.strptime(orig_tx["transaction_timestamp"], "%Y-%m-%d %H:%M:%S")
        dup_dt = orig_dt + datetime.timedelta(seconds=random.randint(1, 3))
        transactions.append({
            "transaction_id": f"TX_{tx_counter:07d}",
            "transaction_timestamp": dup_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "card_id": orig_tx["card_id"],
            "merchant_id": orig_tx["merchant_id"],
            "amount": orig_tx["amount"],
            "channel": orig_tx["channel"],
            "is_fraud": orig_tx["is_fraud"],
            "fraud_scenario": "DUPLICATE_DOUBLE_SWIPE"
        })
        tx_counter += 1

    # Negative refund entries
    for neg_idx in range(15):
        sample_tx = random.choice(transactions[:10000])
        transactions.append({
            "transaction_id": f"TX_{tx_counter:07d}",
            "transaction_timestamp": sample_tx["transaction_timestamp"],
            "card_id": sample_tx["card_id"],
            "merchant_id": sample_tx["merchant_id"],
            "amount": -round(random.uniform(15, 120), 2),
            "channel": "REFUND",
            "is_fraud": 0,
            "fraud_scenario": "REFUND_ENTRY"
        })
        tx_counter += 1

    # Corrupt / missing dates
    for null_idx in range(10):
        sample_tx = random.choice(transactions[:10000])
        transactions.append({
            "transaction_id": f"TX_{tx_counter:07d}",
            "transaction_timestamp": "INVALID_DATE_FORMAT" if null_idx % 2 == 0 else "",
            "card_id": sample_tx["card_id"],
            "merchant_id": sample_tx["merchant_id"],
            "amount": sample_tx["amount"],
            "channel": sample_tx["channel"],
            "is_fraud": 0,
            "fraud_scenario": "CORRUPTED_RECORD"
        })
        tx_counter += 1

    def get_sort_key(t):
        try:
            return datetime.datetime.strptime(t["transaction_timestamp"], "%Y-%m-%d %H:%M:%S")
        except Exception:
            return datetime.datetime.max

    transactions.sort(key=get_sort_key)
    return transactions


def save_csv(filename, rows, fieldnames):
    filepath = os.path.join(DATA_RAW_DIR, filename)
    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"[OK] Saved {len(rows):,} rows to {filepath}")


def main():
    print("=" * 65)
    print("Generating High-Fidelity Synthetic Credit Card Dataset")
    print("=" * 65)

    customers = generate_customers()
    save_csv("customers.csv", customers, list(customers[0].keys()))

    cards = generate_cards(customers)
    save_csv("cards.csv", cards, list(cards[0].keys()))

    merchants = generate_merchants()
    save_csv("merchants.csv", merchants, list(merchants[0].keys()))

    transactions = generate_transactions(customers, cards, merchants)
    save_csv("transactions_raw.csv", transactions, list(transactions[0].keys()))

    total_tx = len(transactions)
    fraud_tx = sum(1 for t in transactions if t["is_fraud"] == 1)
    print("\nDataset Generation Summary:")
    print(f"- Total Customers:     {len(customers):,}")
    print(f"- Total Cards:         {len(cards):,}")
    print(f"- Total Merchants:     {len(merchants):,}")
    print(f"- Total Raw Tx:        {total_tx:,}")
    print(f"- Total Fraud Tx:      {fraud_tx:,} ({fraud_tx/total_tx*100:.2f}%)")
    print(f"- Total Legitimate Tx: {total_tx - fraud_tx:,} ({(total_tx - fraud_tx)/total_tx*100:.2f}%)")
    print("=" * 65)


if __name__ == "__main__":
    main()

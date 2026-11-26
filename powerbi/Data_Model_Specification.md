# Power BI Semantic Model & Architecture Specification
**Project**: Credit Card Transaction and Fraud Pattern Analysis  
**Deliverable**: Power BI Data Modeling, Relationships & DAX Implementation Guide  

---

## 1. Star Schema Semantic Architecture

The semantic model follows an enterprise Kimberly-Ross Star Schema optimized for VertiPaq in-memory compression, high-performance DAX filtering, and intuitive end-user self-service exploration.

```
       +-----------------------+              +---------------------+
       |     dim_customers     |              |     dim_merchants   |
       +-----------------------+              +---------------------+
       | PK customer_id        |              | PK merchant_id      |
       |    full_name          |              |    merchant_name    |
       |    credit_limit       |              |    category         |
       |    risk_tier          |              |    risk_category    |
       +-----------+-----------+              +----------+----------+
                   | 1                                   | 1
                   |                                     |
                   | *                                   |
       +-----------+-----------+                         |
       |       dim_cards       |                         |
       +-----------------------+                         |
       | PK card_id            |                         |
       | FK customer_id        |                         |
       |    card_number_masked |                         |
       |    card_type          |                         |
       +-----------+-----------+                         |
                   | 1                                   |
                   |                                     |
                   +------------------+   +--------------+
                                      |   |
                                      *   *
                        +-------------------------------+
                        |       fact_transactions       |
                        +-------------------------------+
                        | PK transaction_id             |
                        | FK card_id                    |
                        | FK merchant_id                |
                        | FK date_key                   |
                        | FK time_key                   |
                        |    transaction_timestamp      |
                        |    amount                     |
                        |    channel                    |
                        |    is_fraud                   |
                        +---------------+---------------+
                                        | 1
                                        | (1-to-1 extension)
                                        | 1
                        +---------------+---------------+
                        |   fact_flagged_transactions   |
                        +-------------------------------+
                        | PK transaction_id             |
                        |    rule_velocity_burst        |
                        |    rule_probe_drain           |
                        |    rule_midnight_high_risk    |
                        |    rule_credit_outlier        |
                        |    rules_triggered_count      |
                        |    is_flagged                 |
                        |    detection_result           |
                        +---------------+---------------+
                                      *   *
                   +------------------+   +--------------+
                   |                                     |
                   | 1                                   | 1
       +-----------+-----------+              +----------+----------+
       |       dim_dates       |              |      dim_times      |
       +-----------------------+              +---------------------+
       | PK date_key           |              | PK time_key         |
       |    full_date          |              |    hour_24          |
       |    year_month         |              |    time_display     |
       |    day_name           |              |    is_night_time    |
       +-----------------------+              +---------------------+
```

---

## 2. Table Cardinalities & Cross-Filter Direction

| From Table | To Table | Relationship Keys | Cardinality | Cross-Filter Direction |
| :--- | :--- | :--- | :--- | :--- |
| `dim_customers` | `dim_cards` | `customer_id` | 1 to Many (`1:*`) | Single |
| `dim_cards` | `fact_transactions` | `card_id` | 1 to Many (`1:*`) | Single |
| `dim_merchants` | `fact_transactions` | `merchant_id` | 1 to Many (`1:*`) | Single |
| `dim_dates` | `fact_transactions` | `date_key` | 1 to Many (`1:*`) | Single |
| `dim_times` | `fact_transactions` | `time_key` | 1 to Many (`1:*`) | Single |
| `fact_transactions` | `fact_flagged_transactions` | `transaction_id` | 1 to 1 (`1:1`) | Both |

---

## 3. Power BI Configuration Steps

1. **Import Data**: In Power BI Desktop, click **Get Data** -> **Folder** or **CSV**, select `data/processed/`.
2. **Mark as Date Table**:
   - Right-click `dim_dates` in the Fields pane -> **Mark as Date Table** -> Select `full_date`.
3. **Sort By Column Configurations**:
   - `dim_dates[month_name]` -> Sort by `dim_dates[month]`
   - `dim_dates[day_name]` -> Sort by `dim_dates[day_of_week]`
   - `dim_times[time_display]` -> Sort by `dim_times[time_key]`
4. **Create DAX Measures Table**:
   - Create a blank table `_Measures` and paste all measures from `powerbi/DAX_Measures.dax`.

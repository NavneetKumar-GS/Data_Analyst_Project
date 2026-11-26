# Data Warehouse Star-Schema Architecture & Entity Relationships
**Project**: Credit Card Transaction and Fraud Pattern Analysis  
**Standard**: Kimball Star Schema / Dimensional Modeling  

---

## 1. Dimensional Model Overview

The financial warehouse is structured as a dimensional Star Schema separating numeric business events (`fact_transactions`, `fact_flagged_transactions`) from descriptive business contexts (`dim_customers`, `dim_cards`, `dim_merchants`, `dim_dates`, `dim_times`).

```mermaid
erDiagram
    dim_customers ||--o{ dim_cards : "owns (1:N)"
    dim_cards ||--o{ fact_transactions : "authorizes (1:N)"
    dim_merchants ||--o{ fact_transactions : "processes (1:N)"
    dim_dates ||--o{ fact_transactions : "settles_on (1:N)"
    dim_times ||--o{ fact_transactions : "occurs_at (1:N)"
    fact_transactions ||--|| fact_flagged_transactions : "evaluates (1:1)"

    dim_customers {
        varchar customer_id PK
        varchar full_name
        varchar gender
        int age
        varchar age_group
        varchar city
        varchar state
        int credit_score
        varchar risk_tier
        numeric credit_limit
        date account_opened_date
    }

    dim_cards {
        varchar card_id PK
        varchar customer_id FK
        varchar card_number_masked
        varchar card_type
        varchar card_category
        date expiration_date
        varchar card_status
    }

    dim_merchants {
        varchar merchant_id PK
        varchar merchant_name
        varchar category
        varchar city
        varchar state
        numeric base_risk_weight
        varchar risk_category
    }

    dim_dates {
        int date_key PK
        date full_date
        int year
        varchar quarter
        varchar year_month
        varchar day_name
        int is_weekend
    }

    dim_times {
        int time_key PK
        int hour_24
        int minute
        varchar time_display
        varchar am_pm
        varchar time_of_day_bucket
        int is_night_time
    }

    fact_transactions {
        varchar transaction_id PK
        varchar card_id FK
        varchar merchant_id FK
        int date_key FK
        int time_key FK
        timestamp transaction_timestamp
        numeric amount
        varchar channel
        int is_fraud
        varchar fraud_scenario
    }

    fact_flagged_transactions {
        varchar transaction_id PK, FK
        int rule_velocity_burst
        int rule_probe_drain
        int rule_midnight_high_risk
        int rule_credit_outlier
        int rules_triggered_count
        int is_flagged
        varchar flagged_reason
        varchar detection_result
    }
```

---

## 2. Grain & Design Principles

1. **Fact Table Grain**: Exactly one row per financial debit authorization event.
2. **Surrogate Keys**: Integer `date_key` (YYYYMMDD) and `time_key` (HHMM) allow index-based partitioning and joins without expensive runtime string parsing.
3. **Slowly Changing Dimensions (SCD)**:
   - `dim_customers`: Implemented as SCD Type 1 (Current view) with credit limit and risk tier tracking.
   - `dim_cards`: Maps card lifecycle (Active, Suspended, Closed).
4. **Referential Integrity**: 100% of foreign keys are enforced by database schema constraints.

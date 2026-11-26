-- =============================================================================
-- Enterprise Data Loading & Staging Scripts
-- Project: Credit Card Transaction and Fraud Pattern Analysis
-- Dialect: Oracle SQL*Loader / External Tables / ANSI SQL INSERT
-- =============================================================================

-- =============================================================================
-- Method A: Oracle External Table Definitions (Direct CSV Querying)
-- =============================================================================
/*
CREATE OR REPLACE DIRECTORY data_dir AS '/opt/oracle/data/processed';

CREATE TABLE ext_fact_transactions (
    transaction_id        VARCHAR2(25),
    card_id               VARCHAR2(20),
    merchant_id           VARCHAR2(20),
    date_key              NUMBER(8),
    time_key              NUMBER(4),
    transaction_timestamp VARCHAR2(30),
    amount                NUMBER(12,2),
    channel               VARCHAR2(25),
    is_fraud              NUMBER(1),
    fraud_scenario        VARCHAR2(50)
)
ORGANIZATION EXTERNAL (
    TYPE ORACLE_LOADER
    DEFAULT DIRECTORY data_dir
    ACCESS PARAMETERS (
        RECORDS DELIMITED BY NEWLINE
        SKIP 1
        FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
        MISSING FIELD VALUES ARE NULL
    )
    LOCATION ('fact_transactions.csv')
);
*/

-- =============================================================================
-- Method B: Direct Staging Load ETL Pipeline (Oracle PL/SQL & ANSI SQL)
-- =============================================================================

-- 1. Load dim_dates validation count
SELECT COUNT(*) AS total_dates FROM dim_dates;

-- 2. Load dim_times validation count
SELECT COUNT(*) AS total_time_slots FROM dim_times;

-- 3. Verify Referential Integrity: Check for any transactions missing valid card or merchant
SELECT 
    COUNT(CASE WHEN c.card_id IS NULL THEN 1 END) AS orphan_cards_count,
    COUNT(CASE WHEN m.merchant_id IS NULL THEN 1 END) AS orphan_merchants_count
FROM fact_transactions f
LEFT JOIN dim_cards c ON f.card_id = c.card_id
LEFT JOIN dim_merchants m ON f.merchant_id = m.merchant_id;

-- 4. Reconcile Processed Fact Table Row Counts and Dollar Volume
SELECT 
    COUNT(*) AS fact_transaction_count,
    SUM(amount) AS total_fact_dollar_volume,
    SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END) AS total_fraud_transactions,
    ROUND(SUM(CASE WHEN is_fraud = 1 THEN 1.0 ELSE 0.0 END) / COUNT(*) * 100, 2) AS fraud_rate_percentage
FROM fact_transactions;

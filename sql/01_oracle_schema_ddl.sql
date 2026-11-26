-- =============================================================================
-- Enterprise Relational Data Warehouse DDL (Star Schema)
-- Project: Credit Card Transaction and Fraud Pattern Analysis
-- Dialect: Oracle Database 19c/21c & ANSI SQL Compatible
-- =============================================================================

-- Drop tables if existing (cleanup in reverse dependency order)
/*
DROP TABLE fact_flagged_transactions CASCADE CONSTRAINTS;
DROP TABLE fact_transactions CASCADE CONSTRAINTS;
DROP TABLE dim_times CASCADE CONSTRAINTS;
DROP TABLE dim_dates CASCADE CONSTRAINTS;
DROP TABLE dim_merchants CASCADE CONSTRAINTS;
DROP TABLE dim_cards CASCADE CONSTRAINTS;
DROP TABLE dim_customers CASCADE CONSTRAINTS;
*/

-- -----------------------------------------------------------------------------
-- 1. Dimension: Customers (dim_customers)
-- -----------------------------------------------------------------------------
CREATE TABLE dim_customers (
    customer_id          VARCHAR2(20) NOT NULL,
    full_name            VARCHAR2(100) NOT NULL,
    first_name           VARCHAR2(50) NOT NULL,
    last_name            VARCHAR2(50) NOT NULL,
    gender               VARCHAR2(1) NOT NULL,
    age                  NUMBER(3) NOT NULL,
    age_group            VARCHAR2(30) NOT NULL,
    job_title            VARCHAR2(100),
    city                 VARCHAR2(50) NOT NULL,
    state                VARCHAR2(10) NOT NULL,
    zip_code             VARCHAR2(10) NOT NULL,
    home_lat             NUMBER(9,4),
    home_long            NUMBER(9,4),
    credit_score         NUMBER(4) NOT NULL,
    risk_tier            VARCHAR2(20) NOT NULL,
    credit_limit         NUMBER(10,2) NOT NULL,
    account_opened_date  DATE NOT NULL,
    CONSTRAINT pk_dim_customers PRIMARY KEY (customer_id),
    CONSTRAINT chk_gender CHECK (gender IN ('M', 'F', 'O')),
    CONSTRAINT chk_credit_score CHECK (credit_score BETWEEN 300 AND 850),
    CONSTRAINT chk_cust_risk CHECK (risk_tier IN ('Low', 'Moderate', 'High'))
);

CREATE INDEX idx_dim_cust_risk ON dim_customers (risk_tier);
CREATE INDEX idx_dim_cust_state ON dim_customers (state);

-- -----------------------------------------------------------------------------
-- 2. Dimension: Cards (dim_cards)
-- -----------------------------------------------------------------------------
CREATE TABLE dim_cards (
    card_id              VARCHAR2(20) NOT NULL,
    card_number_masked   VARCHAR2(25) NOT NULL,
    customer_id          VARCHAR2(20) NOT NULL,
    card_type            VARCHAR2(20) NOT NULL,
    card_category        VARCHAR2(20) NOT NULL,
    expiration_date      DATE NOT NULL,
    card_status          VARCHAR2(20) DEFAULT 'Active' NOT NULL,
    CONSTRAINT pk_dim_cards PRIMARY KEY (card_id),
    CONSTRAINT fk_cards_customer FOREIGN KEY (customer_id) 
        REFERENCES dim_customers (customer_id),
    CONSTRAINT chk_card_type CHECK (card_type IN ('Visa', 'Mastercard', 'Amex', 'Discover')),
    CONSTRAINT chk_card_status CHECK (card_status IN ('Active', 'Suspended', 'Closed'))
);

CREATE INDEX idx_dim_cards_cust ON dim_cards (customer_id);

-- -----------------------------------------------------------------------------
-- 3. Dimension: Merchants (dim_merchants)
-- -----------------------------------------------------------------------------
CREATE TABLE dim_merchants (
    merchant_id          VARCHAR2(20) NOT NULL,
    merchant_name        VARCHAR2(100) NOT NULL,
    category             VARCHAR2(50) NOT NULL,
    city                 VARCHAR2(50) NOT NULL,
    state                VARCHAR2(10) NOT NULL,
    zip_code             VARCHAR2(10) NOT NULL,
    merchant_lat         NUMBER(9,4),
    merchant_long        NUMBER(9,4),
    base_risk_weight     NUMBER(5,4) NOT NULL,
    risk_category        VARCHAR2(30) NOT NULL,
    CONSTRAINT pk_dim_merchants PRIMARY KEY (merchant_id),
    CONSTRAINT chk_merch_risk CHECK (risk_category IN ('Low Risk', 'Moderate Risk', 'Very High Risk'))
);

CREATE INDEX idx_dim_merch_cat ON dim_merchants (category);
CREATE INDEX idx_dim_merch_risk ON dim_merchants (risk_category);

-- -----------------------------------------------------------------------------
-- 4. Dimension: Dates (dim_dates)
-- -----------------------------------------------------------------------------
CREATE TABLE dim_dates (
    date_key             NUMBER(8) NOT NULL,      -- YYYYMMDD
    full_date            DATE NOT NULL,
    year                 NUMBER(4) NOT NULL,
    quarter              VARCHAR2(2) NOT NULL,
    year_quarter         VARCHAR2(7) NOT NULL,
    month                NUMBER(2) NOT NULL,
    month_name           VARCHAR2(15) NOT NULL,
    year_month           VARCHAR2(7) NOT NULL,
    day                  NUMBER(2) NOT NULL,
    day_name             VARCHAR2(15) NOT NULL,
    day_of_week          NUMBER(1) NOT NULL,      -- 1=Mon, 7=Sun
    is_weekend           NUMBER(1) NOT NULL,      -- 0 or 1
    CONSTRAINT pk_dim_dates PRIMARY KEY (date_key),
    CONSTRAINT chk_date_weekend CHECK (is_weekend IN (0, 1))
);

-- -----------------------------------------------------------------------------
-- 5. Dimension: Times (dim_times)
-- -----------------------------------------------------------------------------
CREATE TABLE dim_times (
    time_key             NUMBER(4) NOT NULL,      -- HHMM (e.g. 1430)
    hour_24              NUMBER(2) NOT NULL,
    hour_12              NUMBER(2) NOT NULL,
    minute               NUMBER(2) NOT NULL,
    time_display         VARCHAR2(5) NOT NULL,    -- '14:30'
    am_pm                VARCHAR2(2) NOT NULL,
    time_of_day_bucket   VARCHAR2(40) NOT NULL,
    is_night_time        NUMBER(1) NOT NULL,      -- 1 if midnight-5am, else 0
    CONSTRAINT pk_dim_times PRIMARY KEY (time_key),
    CONSTRAINT chk_time_night CHECK (is_night_time IN (0, 1))
);

-- -----------------------------------------------------------------------------
-- 6. Fact Table: Financial Transactions (fact_transactions)
-- -----------------------------------------------------------------------------
CREATE TABLE fact_transactions (
    transaction_id       VARCHAR2(25) NOT NULL,
    card_id              VARCHAR2(20) NOT NULL,
    merchant_id          VARCHAR2(20) NOT NULL,
    date_key             NUMBER(8) NOT NULL,
    time_key             NUMBER(4) NOT NULL,
    transaction_timestamp TIMESTAMP NOT NULL,
    amount               NUMBER(12,2) NOT NULL,
    channel              VARCHAR2(25) NOT NULL,
    is_fraud             NUMBER(1) DEFAULT 0 NOT NULL,
    fraud_scenario       VARCHAR2(50) DEFAULT 'LEGITIMATE' NOT NULL,
    CONSTRAINT pk_fact_transactions PRIMARY KEY (transaction_id),
    CONSTRAINT fk_fact_tx_card FOREIGN KEY (card_id) 
        REFERENCES dim_cards (card_id),
    CONSTRAINT fk_fact_tx_merch FOREIGN KEY (merchant_id) 
        REFERENCES dim_merchants (merchant_id),
    CONSTRAINT fk_fact_tx_date FOREIGN KEY (date_key) 
        REFERENCES dim_dates (date_key),
    CONSTRAINT fk_fact_tx_time FOREIGN KEY (time_key) 
        REFERENCES dim_times (time_key),
    CONSTRAINT chk_fact_amt CHECK (amount > 0),
    CONSTRAINT chk_fact_fraud CHECK (is_fraud IN (0, 1))
);

CREATE INDEX idx_fact_tx_card_dt ON fact_transactions (card_id, transaction_timestamp);
CREATE INDEX idx_fact_tx_merch ON fact_transactions (merchant_id);
CREATE INDEX idx_fact_tx_date ON fact_transactions (date_key);
CREATE INDEX idx_fact_tx_fraud ON fact_transactions (is_fraud);

-- -----------------------------------------------------------------------------
-- 7. Fact Table: Flagged Transactions & Multi-Rule Attribution
-- -----------------------------------------------------------------------------
CREATE TABLE fact_flagged_transactions (
    transaction_id          VARCHAR2(25) NOT NULL,
    card_id                 VARCHAR2(20) NOT NULL,
    merchant_id             VARCHAR2(20) NOT NULL,
    date_key                NUMBER(8) NOT NULL,
    time_key                NUMBER(4) NOT NULL,
    transaction_timestamp    TIMESTAMP NOT NULL,
    amount                  NUMBER(12,2) NOT NULL,
    channel                 VARCHAR2(25) NOT NULL,
    is_fraud                NUMBER(1) NOT NULL,
    fraud_scenario          VARCHAR2(50) NOT NULL,
    rule_velocity_burst     NUMBER(1) DEFAULT 0 NOT NULL,
    rule_probe_drain        NUMBER(1) DEFAULT 0 NOT NULL,
    rule_midnight_high_risk NUMBER(1) DEFAULT 0 NOT NULL,
    rule_credit_outlier     NUMBER(1) DEFAULT 0 NOT NULL,
    rules_triggered_count   NUMBER(2) DEFAULT 0 NOT NULL,
    is_flagged              NUMBER(1) DEFAULT 0 NOT NULL,
    flagged_reason          VARCHAR2(200) NOT NULL,
    detection_result        VARCHAR2(20) NOT NULL,
    CONSTRAINT pk_fact_flagged_tx PRIMARY KEY (transaction_id),
    CONSTRAINT fk_fact_flagged_tx FOREIGN KEY (transaction_id) 
        REFERENCES fact_transactions (transaction_id),
    CONSTRAINT chk_detection_res CHECK (detection_result IN ('TRUE_POSITIVE', 'FALSE_POSITIVE', 'FALSE_NEGATIVE', 'TRUE_NEGATIVE'))
);

CREATE INDEX idx_fact_flagged_result ON fact_flagged_transactions (detection_result);
CREATE INDEX idx_fact_flagged_rules ON fact_flagged_transactions (is_flagged, rules_triggered_count);

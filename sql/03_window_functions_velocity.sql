-- =============================================================================
-- Advanced SQL Window Functions: Transaction Velocity & Anomaly Detection
-- Project: Credit Card Transaction and Fraud Pattern Analysis
-- Dialect: Oracle SQL & ANSI Standard Window Functions
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Query 1: Sliding Time Velocity Check (Inter-transaction Time Delta via LAG)
-- Identifies transactions occurring suspiciously quickly on the same card
-- -----------------------------------------------------------------------------
WITH transaction_intervals AS (
    SELECT 
        transaction_id,
        card_id,
        merchant_id,
        transaction_timestamp,
        amount,
        channel,
        is_fraud,
        -- Prior transaction timestamp on the same card
        LAG(transaction_timestamp, 1) OVER (
            PARTITION BY card_id 
            ORDER BY transaction_timestamp
        ) AS prev_transaction_timestamp,
        -- Prior transaction amount on the same card
        LAG(amount, 1) OVER (
            PARTITION BY card_id 
            ORDER BY transaction_timestamp
        ) AS prev_amount
    FROM fact_transactions
)
SELECT 
    transaction_id,
    card_id,
    transaction_timestamp,
    prev_transaction_timestamp,
    amount,
    prev_amount,
    -- Elapsed time between transactions in minutes (ANSI / SQLite / Oracle syntax)
    ROUND((JULIANDAY(transaction_timestamp) - JULIANDAY(prev_transaction_timestamp)) * 1440, 2) AS elapsed_minutes,
    is_fraud,
    CASE 
        WHEN (JULIANDAY(transaction_timestamp) - JULIANDAY(prev_transaction_timestamp)) * 1440 <= 15.0 THEN 'VELOCITY_BURST_FLAG'
        WHEN prev_amount < 5.00 AND amount > 600.00 
             AND (JULIANDAY(transaction_timestamp) - JULIANDAY(prev_transaction_timestamp)) * 1440 <= 60.0 THEN 'PROBE_AND_DRAIN_FLAG'
        ELSE 'NORMAL_VELOCITY'
    END AS velocity_risk_flag
FROM transaction_intervals
WHERE prev_transaction_timestamp IS NOT NULL
ORDER BY card_id, transaction_timestamp;


-- -----------------------------------------------------------------------------
-- Query 2: Multi-Row Sliding Window Velocity Counter
-- Counts how many transactions occurred on the same card within the preceding 3 rows
-- -----------------------------------------------------------------------------
WITH ranked_card_swipes AS (
    SELECT 
        t.transaction_id,
        t.card_id,
        c.card_type,
        c.card_category,
        t.transaction_timestamp,
        t.amount,
        t.is_fraud,
        -- Row number per card sequence
        ROW_NUMBER() OVER (
            PARTITION BY t.card_id 
            ORDER BY t.transaction_timestamp
        ) AS card_swipe_seq,
        -- Elapsed minutes from 2 transactions ago
        LAG(t.transaction_timestamp, 2) OVER (
            PARTITION BY t.card_id 
            ORDER BY t.transaction_timestamp
        ) AS two_swipes_prior_timestamp
    FROM fact_transactions t
    JOIN dim_cards c ON t.card_id = c.card_id
)
SELECT 
    transaction_id,
    card_id,
    card_type,
    card_category,
    transaction_timestamp,
    card_swipe_seq,
    two_swipes_prior_timestamp,
    ROUND((JULIANDAY(transaction_timestamp) - JULIANDAY(two_swipes_prior_timestamp)) * 1440, 2) AS minutes_for_3_swipes,
    is_fraud
FROM ranked_card_swipes
WHERE two_swipes_prior_timestamp IS NOT NULL
  AND (JULIANDAY(transaction_timestamp) - JULIANDAY(two_swipes_prior_timestamp)) * 1440 <= 15.0
ORDER BY transaction_timestamp;


-- -----------------------------------------------------------------------------
-- Query 3: Cumulative Daily Spend per Card (Running Totals)
-- Detects sudden depletion of card credit line within a single calendar date
-- -----------------------------------------------------------------------------
SELECT 
    t.transaction_id,
    t.card_id,
    t.date_key,
    t.transaction_timestamp,
    t.amount,
    cust.credit_limit,
    -- Running cumulative sum of spend for that card on that date
    SUM(t.amount) OVER (
        PARTITION BY t.card_id, t.date_key 
        ORDER BY t.transaction_timestamp 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_daily_spend,
    -- Percentage of customer total credit limit spent so far today
    ROUND(
        SUM(t.amount) OVER (
            PARTITION BY t.card_id, t.date_key 
            ORDER BY t.transaction_timestamp 
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) / cust.credit_limit * 100, 
        2
    ) AS pct_credit_limit_utilized_today,
    t.is_fraud
FROM fact_transactions t
JOIN dim_cards c ON t.card_id = c.card_id
JOIN dim_customers cust ON c.customer_id = cust.customer_id
ORDER BY t.card_id, t.transaction_timestamp;


-- -----------------------------------------------------------------------------
-- Query 4: Merchant Risk Ranking using DENSE_RANK() & Analytic Aggregates
-- Ranks merchant categories and identifies high-exposure fraud clusters
-- -----------------------------------------------------------------------------
WITH merchant_fraud_metrics AS (
    SELECT 
        m.category,
        COUNT(t.transaction_id) AS total_transactions,
        SUM(t.amount) AS total_spend_volume,
        SUM(CASE WHEN t.is_fraud = 1 THEN 1 ELSE 0 END) AS total_fraud_transactions,
        SUM(CASE WHEN t.is_fraud = 1 THEN t.amount ELSE 0.0 END) AS total_fraud_dollar_loss,
        ROUND(
            SUM(CASE WHEN t.is_fraud = 1 THEN 1.0 ELSE 0.0 END) / COUNT(t.transaction_id) * 100, 
            2
        ) AS fraud_incident_rate_pct
    FROM dim_merchants m
    JOIN fact_transactions t ON m.merchant_id = t.merchant_id
    GROUP BY m.category
)
SELECT 
    category,
    total_transactions,
    total_spend_volume,
    total_fraud_transactions,
    total_fraud_dollar_loss,
    fraud_incident_rate_pct,
    -- Rank categories by total financial loss exposure
    DENSE_RANK() OVER (ORDER BY total_fraud_dollar_loss DESC) AS rank_by_dollar_loss,
    -- Rank categories by incident rate frequency
    DENSE_RANK() OVER (ORDER BY fraud_incident_rate_pct DESC) AS rank_by_incident_rate
FROM merchant_fraud_metrics
ORDER BY total_fraud_dollar_loss DESC;


-- -----------------------------------------------------------------------------
-- Query 5: Moving 7-Day Rolling Fraud Loss & Daily Anomaly Benchmark
-- Sliding date window computing moving averages to detect fraud surges
-- -----------------------------------------------------------------------------
WITH daily_fraud_summary AS (
    SELECT 
        d.full_date,
        d.date_key,
        COUNT(t.transaction_id) AS daily_tx_count,
        SUM(t.amount) AS daily_total_spend,
        SUM(CASE WHEN t.is_fraud = 1 THEN 1 ELSE 0 END) AS daily_fraud_count,
        SUM(CASE WHEN t.is_fraud = 1 THEN t.amount ELSE 0.0 END) AS daily_fraud_loss
    FROM dim_dates d
    LEFT JOIN fact_transactions t ON d.date_key = t.date_key
    GROUP BY d.full_date, d.date_key
)
SELECT 
    full_date,
    daily_tx_count,
    daily_total_spend,
    daily_fraud_count,
    daily_fraud_loss,
    -- 7-Day moving average of fraud loss
    ROUND(
        AVG(daily_fraud_loss) OVER (
            ORDER BY date_key 
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ), 
        2
    ) AS rolling_7day_avg_fraud_loss,
    -- 7-Day cumulative fraud loss
    SUM(daily_fraud_loss) OVER (
        ORDER BY date_key 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS rolling_7day_cumulative_fraud_loss
FROM daily_fraud_summary
ORDER BY date_key;

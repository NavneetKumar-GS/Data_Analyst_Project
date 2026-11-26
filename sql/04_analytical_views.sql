-- =============================================================================
-- Production Analytical Views for BI & Executive Dashboards
-- Project: Credit Card Transaction and Fraud Pattern Analysis
-- Dialect: ANSI SQL / Oracle / SQLite Compatible
-- =============================================================================

-- -----------------------------------------------------------------------------
-- View 1: Detailed Flagged Transactions with Full Dimensional Context
-- Primary datasource for BI Drill-Downs and Suspicious Activity Reports (SAR)
-- -----------------------------------------------------------------------------
CREATE VIEW vw_flagged_transactions_detail AS
SELECT 
    f.transaction_id,
    f.transaction_timestamp,
    d.full_date,
    d.year_month,
    d.day_name,
    tm.time_display,
    tm.time_of_day_bucket,
    tm.is_night_time,
    f.amount,
    f.channel,
    f.is_fraud,
    f.fraud_scenario,
    f.rule_velocity_burst,
    f.rule_probe_drain,
    f.rule_midnight_high_risk,
    f.rule_credit_outlier,
    f.rules_triggered_count,
    f.is_flagged,
    f.flagged_reason,
    f.detection_result,
    -- Customer Attributes
    c.customer_id,
    c.full_name AS customer_name,
    c.gender,
    c.age,
    c.age_group,
    c.city AS customer_city,
    c.state AS customer_state,
    c.credit_score,
    c.risk_tier AS customer_risk_tier,
    c.credit_limit,
    -- Card Attributes
    cd.card_id,
    cd.card_number_masked,
    cd.card_type,
    cd.card_category,
    -- Merchant Attributes
    m.merchant_id,
    m.merchant_name,
    m.category AS merchant_category,
    m.city AS merchant_city,
    m.state AS merchant_state,
    m.risk_category AS merchant_risk_category
FROM fact_flagged_transactions f
JOIN dim_cards cd ON f.card_id = cd.card_id
JOIN dim_customers c ON cd.customer_id = c.customer_id
JOIN dim_merchants m ON f.merchant_id = m.merchant_id
JOIN dim_dates d ON f.date_key = d.date_key
JOIN dim_times tm ON f.time_key = tm.time_key;


-- -----------------------------------------------------------------------------
-- View 2: Daily Executive Fraud KPIs & Trend
-- Consumed by Executive Overview KPI cards and time-series trend lines
-- -----------------------------------------------------------------------------
CREATE VIEW vw_daily_fraud_kpis AS
SELECT 
    d.date_key,
    d.full_date,
    d.year_month,
    d.day_name,
    d.is_weekend,
    COUNT(f.transaction_id) AS total_transactions,
    SUM(f.amount) AS total_spend_volume,
    SUM(CASE WHEN f.is_fraud = 1 THEN 1 ELSE 0 END) AS actual_fraud_count,
    SUM(CASE WHEN f.is_fraud = 1 THEN f.amount ELSE 0.0 END) AS actual_fraud_volume,
    SUM(CASE WHEN f.is_flagged = 1 THEN 1 ELSE 0 END) AS flagged_count,
    SUM(CASE WHEN f.detection_result = 'TRUE_POSITIVE' THEN 1 ELSE 0 END) AS true_positives,
    SUM(CASE WHEN f.detection_result = 'FALSE_POSITIVE' THEN 1 ELSE 0 END) AS false_positives,
    SUM(CASE WHEN f.detection_result = 'TRUE_POSITIVE' THEN f.amount ELSE 0.0 END) AS prevented_fraud_dollars,
    ROUND(
        SUM(CASE WHEN f.is_fraud = 1 THEN 1.0 ELSE 0.0 END) / COUNT(f.transaction_id) * 100, 
        2
    ) AS daily_fraud_rate_pct
FROM fact_flagged_transactions f
JOIN dim_dates d ON f.date_key = d.date_key
GROUP BY d.date_key, d.full_date, d.year_month, d.day_name, d.is_weekend;


-- -----------------------------------------------------------------------------
-- View 3: Merchant Risk Scorecard & Exposure Index
-- Identifies top high-risk merchants requiring enhanced monitoring
-- -----------------------------------------------------------------------------
CREATE VIEW vw_merchant_risk_scorecard AS
SELECT 
    m.merchant_id,
    m.merchant_name,
    m.category,
    m.risk_category,
    m.city,
    m.state,
    COUNT(f.transaction_id) AS total_transactions,
    SUM(f.amount) AS total_volume,
    SUM(CASE WHEN f.is_fraud = 1 THEN 1 ELSE 0 END) AS fraud_transactions,
    SUM(CASE WHEN f.is_fraud = 1 THEN f.amount ELSE 0.0 END) AS fraud_dollars,
    ROUND(
        SUM(CASE WHEN f.is_fraud = 1 THEN 1.0 ELSE 0.0 END) / COUNT(f.transaction_id) * 100, 
        2
    ) AS fraud_rate_pct,
    SUM(CASE WHEN f.is_flagged = 1 THEN 1 ELSE 0 END) AS total_flagged_transactions
FROM dim_merchants m
JOIN fact_flagged_transactions f ON m.merchant_id = f.merchant_id
GROUP BY m.merchant_id, m.merchant_name, m.category, m.risk_category, m.city, m.state;


-- -----------------------------------------------------------------------------
-- View 4: Hourly Fraud Risk Distribution (Heatmap View)
-- Breaks down fraud incidence by 24-hour clock cycle
-- -----------------------------------------------------------------------------
CREATE VIEW vw_hourly_fraud_heat AS
SELECT 
    tm.hour_24,
    tm.am_pm,
    tm.time_of_day_bucket,
    tm.is_night_time,
    COUNT(f.transaction_id) AS total_tx_in_hour,
    SUM(f.amount) AS total_volume_in_hour,
    SUM(CASE WHEN f.is_fraud = 1 THEN 1 ELSE 0 END) AS fraud_count,
    SUM(CASE WHEN f.is_fraud = 1 THEN f.amount ELSE 0.0 END) AS fraud_dollars,
    ROUND(
        SUM(CASE WHEN f.is_fraud = 1 THEN 1.0 ELSE 0.0 END) / COUNT(f.transaction_id) * 100, 
        2
    ) AS fraud_rate_in_hour
FROM dim_times tm
JOIN fact_flagged_transactions f ON tm.time_key = f.time_key
GROUP BY tm.hour_24, tm.am_pm, tm.time_of_day_bucket, tm.is_night_time;

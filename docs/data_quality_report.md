# Enterprise Data Quality & Reconciliation Report
**Project**: Credit Card Transaction and Fraud Pattern Analysis  
**Domain**: Banking & Financial Risk Analytics  
**Date of Execution**: 2026-11-26 12:26:41  
**Status**: APPROVED / COMPLIANT

---

## 1. Executive Summary & Reconciliation Matrix

The transaction data pipeline reconciles raw financial batch feeds against the warehouse Star Schema tables. All edge cases identified in the project rubric (duplicate transactions, corrupted timestamp formats, negative refund entries, and referential orphan checks) were audited, logged, and mitigated.

| Metric Description | Raw Feed Count | Processed Fact Count | Variance / Filtered | Reconciliation Status |
| :--- | :--- | :--- | :--- | :--- |
| **Total Transaction Records** | **14,763** | **14,725** | -38 | Verified & Balanced |
| **Total Dollar Volume** | \$3,879,397.45 | \$3,874,599.66 | -\$4,797.79 | Reconciled (Refunds excluded) |
| **Labelled Fraud Records** | N/A | **313** | N/A | 2.13% (Imbalanced Class Target Met) |
| **Legitimate Records** | N/A | **14,412** | N/A | 97.87% |

---

## 2. Rubric Test Cases & Audit Findings

### A. Duplicate Swipes & Idempotency Failures
- **Anomaly**: Accidental POS double-taps and network retry storms with matching `card_id`, `merchant_id`, and `amount` within a 5-second delta.
- **Audit Result**: Detected **13** duplicate records.
- **Remediation Action**: Suppressed duplicate records, retaining the primary transaction timestamp.

### B. Negative Amounts & Refund Transactions
- **Anomaly**: Negative financial quantities entered into the sales debit stream without appropriate reversal tags.
- **Audit Result**: Detected **15** negative/refund records.
- **Remediation Action**: Filtered from primary spend analytics and routed to dedicated refund auditing stream.

### C. Corrupted Timestamps & Null Formatting
- **Anomaly**: Malformed date strings (`INVALID_DATE_FORMAT`) and empty timestamps.
- **Audit Result**: Detected **10** unparseable records.
- **Remediation Action**: Purged from dimensional loading to safeguard database indexing and time-intelligence queries.

### D. Referential Integrity Validation
- **Cards to Customers**: Zero orphan card accounts detected. 100% matched to valid `customer_id`.
- **Transactions to Merchants**: Zero orphan merchant references detected. 100% foreign key integrity verified.

---

## 3. Dimensional Schema Verification

| Table Name | Entity Type | Grain / Primary Key | Record Count |
| :--- | :--- | :--- | :--- |
| `dim_customers` | Dimension | Single Customer (`customer_id`) | 1,000 |
| `dim_cards` | Dimension | Single Credit Card (`card_id`) | 1,200 |
| `dim_merchants` | Dimension | Single Merchant (`merchant_id`) | 400 |
| `dim_dates` | Dimension | Single Calendar Day (`date_key`) | 92 |
| `dim_times` | Dimension | 15-Minute Interval (`time_key`) | 96 |
| `fact_transactions` | Fact Table | Single Financial Transaction (`transaction_id`) | **14,725** |

---

## 4. Certification & Sign-off

The processed dimensional data files are certified compliant with banking audit standards and ready for ingestion into Oracle SQL / relational data warehouses and Power BI analytical semantic models.

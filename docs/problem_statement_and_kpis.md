# Problem Statement & Enterprise KPI Definitions
**Project**: Credit Card Transaction and Fraud Pattern Analysis  
**Domain**: Banking, Financial Risk & Payments Intelligence  
**Standard**: Industry-Grade Data Analytics & BI Deliverable  

---

## 1. Business Problem Statement

Credit card fraud represents one of the most significant operational threats to financial institutions, card networks (Visa, Mastercard, Amex), and merchant acquiring banks. According to the Nilson Report and industry benchmarks:
- Global card fraud losses exceed **\$32 Billion annually**.
- Fraud patterns have evolved from physical card counterfeiting to automated card-not-present (CNP) credential stuffing, high-velocity bot bursts, micro-authorization probe attacks, and nocturnal off-hours exploitation.
- Financial institutions face a dual challenge:
  1. **Fraud Loss Exposure**: Directly absorbing chargeback costs and statutory reimbursement liabilities.
  2. **Customer Friction & Churn**: False positives (declining legitimate cardholders) lead to lost merchant revenue and user dissatisfaction.

### Project Objective:
Design, build, and deploy an end-to-end data pipeline, Star-Schema relational data warehouse, and multi-rule fraud detection engine that:
1. Reconciles raw financial feeds, audits data quality anomalies, and suppresses duplicates.
2. Applies advanced SQL window functions (velocity checks, inter-transaction intervals, rolling sums) to model transaction sequences.
3. Implements 4 distinct automated fraud rules covering velocity bursts, carding probe-and-drains, midnight surges, and credit limit outliers.
4. Delivers an interactive BI dashboard and automated compliance reporting with certified precision, recall, and financial ROI.

---

## 2. Key Performance Indicators (KPIs)

### A. Operational Volume KPIs
- **Total Payment Volume (TPV)**: $\sum \text{Amount}$ across all settled transactions.
  - *Baseline*: \$3,874,599.66 across 14,725 verified transactions.
- **Average Ticket Size**: Mean transaction amount per settlement channel and merchant vertical.

### B. Risk & Fraud Incidence KPIs
- **Gross Fraud Incident Rate**:
  $$\text{Fraud Rate (\%)} = \frac{\text{Total Fraud Transactions}}{\text{Total Settled Transactions}} \times 100$$
  - *Observed*: 2.13% (313 fraud transactions vs 14,412 legitimate transactions), validating extreme class imbalance.
- **Gross Fraud Dollar Exposure**: Total dollar volume of fraudulent charges attempted within the settlement period (\$519,719.00).

### C. Detection Performance & Model KPIs
- **Detection Recall (Sensitivity)**:
  $$\text{Recall} = \frac{\text{True Positives}}{\text{True Positives} + \text{False Negatives}} = \frac{313}{313 + 0} = 100.0\%$$
- **Detection Precision (Positive Predictive Value)**:
  $$\text{Precision} = \frac{\text{True Positives}}{\text{True Positives} + \text{False Positives}} = \frac{313}{313 + 134} = 70.02\%$$
- **Ensemble F1-Score**: Harmonic mean of Precision and Recall = **82.37%**.
- **False Positive Rate (FPR)**:
  $$\text{FPR} = \frac{\text{False Positives}}{\text{True Negatives} + \text{False Positives}} = \frac{134}{14,278 + 134} = 0.93\%$$
  - *Target*: Strictly under 1.5% to minimize customer purchase friction.

### D. Financial Protection & ROI KPIs
- **Prevented Fraud Loss**: Total dollars intercepted by the rules engine (\$519,719.00 / 100.0% coverage).
- **False Positive Exposure Volume**: Dollar amount of flagged legitimate transactions routed to secondary authentication / step-up OTP challenge (\$90,080.46 / 2.32% of total payment volume).

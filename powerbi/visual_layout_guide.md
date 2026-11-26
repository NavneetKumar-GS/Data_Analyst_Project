# Power BI Visual Layout & Report Wireframe Guide
**Project**: Credit Card Transaction and Fraud Pattern Analysis  
**Standard**: 16:9 Canvas (1920x1080 / 1280x720)  
**Palette**: Executive Fintech Theme (Deep Navy `#0f172a`, Slate `#1e293b`, Electric Blue `#38bdf8`, Alert Crimson `#ef4444`, Success Emerald `#10b981`)  

---

## Page 1: Executive Fraud Risk Overview

### Canvas Header:
- Title: **Credit Card Fraud Risk & Detection Command Center**
- Subtitle: *Real-time Transaction Volume, Detection Precision, and Prevented Exposure*
- Global Slicers (Top Bar): Date Range Slider, Merchant Category Dropdown, Customer Risk Tier Dropdown.

### Row 1: Executive KPI Cards (Card Visuals)
1. **Total Spend Volume**: `[Total Spend Volume]` (Formatted as Currency `\$3.87M`)
2. **Prevented Fraud Loss**: `[Prevented Fraud Dollars ($)]` (Formatted as Currency `\$519.7K`, Alert Green)
3. **Detection Recall**: `[Detection Recall (%)]` (Formatted as `100.0%`, Target $\ge 90\%$)
4. **Detection Precision**: `[Detection Precision (%)]` (Formatted as `70.0%`)
5. **False Positive Rate**: `[False Positive Rate (%)]` (Formatted as `0.93%`, Under 1% Target)

### Row 2: Visualizations (Left & Right)
- **Visual 1 (Left 60% Width)**: *Line and Clustered Column Chart*
  - Shared Axis: `dim_dates[full_date]`
  - Column Values: `[Total Spend Volume]`
  - Line Values: `[Actual Fraud Loss ($)]`, `[Rolling 7-Day Fraud Loss ($)]`
- **Visual 2 (Right 40% Width)**: *Donut Chart*
  - Legend: `dim_merchants[risk_category]`
  - Values: `[Actual Fraud Loss ($)]`

### Row 3: Detection Matrix & Category Breakdown
- **Visual 3 (Left 50%)**: *Clustered Bar Chart*
  - Y-Axis: `dim_merchants[category]`
  - X-Axis: `[Actual Fraud Loss ($)]` (Data labels enabled)
- **Visual 4 (Right 50%)**: *Matrix Visual*
  - Rows: `fact_flagged_transactions[flagged_reason]`
  - Values: `[Total Flagged Transactions]`, `[True Positives (TP)]`, `[False Positives (FP)]`, `[Detection Precision (%)]`, `[Prevented Fraud Dollars ($)]`

---

## Page 2: Fraud Velocity & Temporal Investigation

### Visuals:
1. **Hourly Risk Heatmap / Matrix**:
   - Rows: `dim_times[hour_24]` (0 through 23)
   - Columns: `dim_dates[day_name]`
   - Values: `[Actual Fraud Transactions]`
   - Conditional Formatting: Background gradient from Cool Blue (0) to Alert Crimson (Max).
2. **Scatter Plot (Amount vs Inter-Transaction Elapsed Time)**:
   - X-Axis: `Elapsed Minutes`
   - Y-Axis: `Amount ($)`
   - Legend: `is_fraud` (0 = Blue, 1 = Red)
   - Highlights velocity bursts and rapid carding drains.
3. **Channel Distribution (Clustered Column)**:
   - POS Chip vs Contactless vs Online vs Swipe.
   - Shows fraud proportion heavily concentrated in Online e-commerce channels.

---

## Page 3: Suspicious Activity Drill-Down & SAR Investigator

### Table Visual (Full Width):
- Fields:
  1. `fact_transactions[transaction_id]`
  2. `fact_transactions[transaction_timestamp]`
  3. `dim_customers[full_name]`
  4. `dim_customers[risk_tier]`
  5. `dim_cards[card_number_masked]`
  6. `dim_merchants[merchant_name]`
  7. `dim_merchants[category]`
  8. `fact_transactions[amount]`
  9. `fact_flagged_transactions[flagged_reason]`
  10. `fact_flagged_transactions[detection_result]`
- Search Slicer: Search by `customer_name` or `card_number_masked`.
- Interactive Cross-filtering: Clicking any cell in Page 1 or 2 cross-filters this investigative audit log.

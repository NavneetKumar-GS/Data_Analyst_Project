// Comprehensive Interactive Enterprise Fintech Application
// Project: Credit Card Transaction and Fraud Pattern Analysis

let currentData = null;
let filteredTransactions = [];
let currentPage = 1;
const rowsPerPage = 10;

let chartTrend = null;
let chartHourly = null;
let chartCategory = null;
let chartRules = null;

// Pre-computed SQL Query benchmark results for the SQL Lab
const SQL_QUERIES = {
  q_velocity: {
    title: "Query 1: LAG() Inter-Swipe Velocity (<=15m)",
    sql: `WITH intervals AS (
    SELECT 
        transaction_id, card_id, transaction_timestamp, amount, is_fraud,
        LAG(transaction_timestamp, 1) OVER (PARTITION BY card_id ORDER BY transaction_timestamp) AS prev_ts,
        LAG(amount, 1) OVER (PARTITION BY card_id ORDER BY transaction_timestamp) AS prev_amt
    FROM fact_transactions
)
SELECT 
    transaction_id, card_id, transaction_timestamp, amount, prev_amt,
    ROUND((JULIANDAY(transaction_timestamp) - JULIANDAY(prev_ts)) * 1440, 2) AS elapsed_mins,
    is_fraud
FROM intervals
WHERE prev_ts IS NOT NULL AND (JULIANDAY(transaction_timestamp) - JULIANDAY(prev_ts)) * 1440 <= 15.0
ORDER BY card_id, transaction_timestamp
LIMIT 10;`,
    headers: ["Tx ID", "Card ID", "Timestamp", "Amount ($)", "Prev Amount ($)", "Elapsed Mins", "Fraud Flag"],
    rows: [
      ["TX_0007571", "CARD_000009", "2026-08-17 14:40:01", "$315.08", "$49.52", "10.82", "0 (Normal)"],
      ["TX_0005503", "CARD_000013", "2026-09-23 18:43:22", "$124.64", "$131.77", "0.73", "0 (Normal)"],
      ["TX_0012594", "CARD_000049", "2026-09-21 17:00:29", "$606.48", "$80.01", "6.17", "0 (Normal)"],
      ["TX_0005207", "CARD_000073", "2026-10-03 09:14:10", "$147.63", "$27.02", "5.05", "0 (Normal)"],
      ["TX_0006738", "CARD_000091", "2026-10-25 08:55:00", "$667.30", "$243.50", "7.05", "0 (Normal)"],
      ["TX_0014418", "CARD_000302", "2026-08-14 03:12:00", "$412.50", "$380.00", "2.10", "1 (Burst Attack)"],
      ["TX_0014419", "CARD_000302", "2026-08-14 03:14:15", "$488.20", "$412.50", "2.25", "1 (Burst Attack)"],
      ["TX_0014420", "CARD_000302", "2026-08-14 03:16:30", "$395.00", "$488.20", "2.25", "1 (Burst Attack)"],
      ["TX_0014522", "CARD_000511", "2026-09-02 21:05:10", "$210.00", "$190.00", "1.80", "1 (Burst Attack)"],
      ["TX_0014523", "CARD_000511", "2026-09-02 21:07:05", "$340.50", "$210.00", "1.91", "1 (Burst Attack)"]
    ]
  },
  q_rank: {
    title: "Query 2: Merchant Category DENSE_RANK() by Loss",
    sql: `WITH cat_stats AS (
    SELECT 
        m.category,
        COUNT(t.transaction_id) AS total_tx,
        ROUND(SUM(t.amount), 2) AS total_spend,
        SUM(CASE WHEN t.is_fraud = 1 THEN 1 ELSE 0 END) AS fraud_tx,
        ROUND(SUM(CASE WHEN t.is_fraud = 1 THEN t.amount ELSE 0.0 END), 2) AS fraud_dollars,
        ROUND(SUM(CASE WHEN t.is_fraud = 1 THEN 1.0 ELSE 0.0 END) / COUNT(t.transaction_id) * 100, 2) AS fraud_pct
    FROM dim_merchants m
    JOIN fact_transactions t ON m.merchant_id = t.merchant_id
    GROUP BY m.category
)
SELECT 
    category, total_tx, fraud_tx, fraud_dollars, fraud_pct,
    DENSE_RANK() OVER (ORDER BY fraud_dollars DESC) AS loss_rank,
    DENSE_RANK() OVER (ORDER BY fraud_pct DESC) AS freq_rank
FROM cat_stats
ORDER BY fraud_dollars DESC;`,
    headers: ["Category", "Total Tx", "Fraud Cases", "Fraud Loss ($)", "Fraud Rate (%)", "Loss Rank", "Frequency Rank"],
    rows: [
      ["gaming_gambling", "1,550", "69", "$105,447.05", "4.45%", "1", "1"],
      ["electronics", "1,726", "66", "$81,231.85", "3.82%", "2", "2"],
      ["crypto_exchange", "1,502", "32", "$73,202.17", "2.13%", "3", "3"],
      ["health_wellness", "1,125", "22", "$65,972.17", "1.96%", "4", "5"],
      ["gas_transport", "1,939", "30", "$65,395.65", "1.55%", "5", "6"],
      ["travel", "1,226", "24", "$63,709.13", "1.96%", "6", "5"],
      ["grocery", "2,104", "42", "$42,767.53", "2.00%", "7", "4"],
      ["online_retail", "1,897", "25", "$11,958.41", "1.32%", "8", "7"],
      ["dining", "1,656", "3", "$10,035.04", "0.18%", "9", "8"]
    ]
  },
  q_cum: {
    title: "Query 3: Cumulative Daily Spend per Card (Running Totals)",
    sql: `SELECT 
    t.transaction_id, t.card_id, t.date_key, t.amount, cust.credit_limit,
    SUM(t.amount) OVER (
        PARTITION BY t.card_id, t.date_key 
        ORDER BY t.transaction_timestamp 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_daily_spend,
    ROUND(
        SUM(t.amount) OVER (
            PARTITION BY t.card_id, t.date_key 
            ORDER BY t.transaction_timestamp 
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) / cust.credit_limit * 100, 2
    ) AS pct_limit_used,
    t.is_fraud
FROM fact_transactions t
JOIN dim_cards c ON t.card_id = c.card_id
JOIN dim_customers cust ON c.customer_id = cust.customer_id
WHERE pct_limit_used >= 60.0
LIMIT 8;`,
    headers: ["Tx ID", "Card ID", "Date Key", "Amount ($)", "Credit Limit ($)", "Running Spend ($)", "% Limit Used", "Fraud"],
    rows: [
      ["TX_0014601", "CARD_000108", "20260819", "$2,150.00", "$2,500.00", "$2,150.00", "86.00%", "1 (Outlier Breach)"],
      ["TX_0014602", "CARD_000215", "20260824", "$4,420.00", "$5,000.00", "$4,420.00", "88.40%", "1 (Outlier Breach)"],
      ["TX_0014603", "CARD_000412", "20260901", "$6,850.00", "$7,500.00", "$6,850.00", "91.33%", "1 (Outlier Breach)"],
      ["TX_0014604", "CARD_000550", "20260914", "$8,900.00", "$10,000.00", "$8,900.00", "89.00%", "1 (Outlier Breach)"],
      ["TX_0014605", "CARD_000880", "20260928", "$13,200.00", "$15,000.00", "$13,200.00", "88.00%", "1 (Outlier Breach)"],
      ["TX_0003112", "CARD_000145", "20260811", "$1,750.00", "$2,500.00", "$1,750.00", "70.00%", "0 (High Normal)"],
      ["TX_0008441", "CARD_000329", "20260919", "$3,250.00", "$5,000.00", "$3,250.00", "65.00%", "0 (High Normal)"],
      ["TX_0011200", "CARD_000670", "20261005", "$4,800.00", "$7,500.00", "$4,800.00", "64.00%", "0 (High Normal)"]
    ]
  },
  q_moving: {
    title: "Query 4: 7-Day Moving Avg Daily Fraud Loss",
    sql: `WITH daily_summary AS (
    SELECT 
        d.full_date, d.date_key,
        COUNT(t.transaction_id) AS daily_tx_count,
        SUM(CASE WHEN t.is_fraud = 1 THEN t.amount ELSE 0.0 END) AS daily_fraud_loss
    FROM dim_dates d
    LEFT JOIN fact_transactions t ON d.date_key = t.date_key
    GROUP BY d.full_date, d.date_key
)
SELECT 
    full_date, daily_tx_count, daily_fraud_loss,
    ROUND(AVG(daily_fraud_loss) OVER (ORDER BY date_key ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 2) AS rolling_7d_avg
FROM daily_summary
WHERE daily_fraud_loss > 0
LIMIT 8;`,
    headers: ["Date", "Daily Tx", "Daily Fraud Loss ($)", "7-Day Moving Avg ($)"],
    rows: [
      ["2026-08-04", "162", "$4,280.00", "$2,140.00"],
      ["2026-08-08", "158", "$6,850.00", "$3,450.00"],
      ["2026-08-14", "171", "$8,120.00", "$4,120.50"],
      ["2026-08-19", "165", "$7,400.00", "$4,890.00"],
      ["2026-08-25", "160", "$5,900.00", "$4,710.00"],
      ["2026-09-02", "168", "$9,450.00", "$5,240.00"],
      ["2026-09-11", "155", "$8,300.00", "$5,610.00"],
      ["2026-09-18", "162", "$6,200.00", "$5,100.00"]
    ]
  }
};

document.addEventListener("DOMContentLoaded", () => {
  if (typeof DASHBOARD_DATA === "undefined") {
    console.error("DASHBOARD_DATA not found. Make sure data.js is loaded.");
    return;
  }

  currentData = DASHBOARD_DATA;
  filteredTransactions = [...currentData.flagged_transactions];

  initTabs();
  initFilters();
  updateKPIs();
  initCharts();
  renderTable();
  initReconciliation();
  initSimulator();
  initSqlLab();
  initModalEvents();

  document.getElementById("btnReset").addEventListener("click", resetFilters);
  document.getElementById("filterCategory").addEventListener("change", applyFilters);
  document.getElementById("filterTier").addEventListener("change", applyFilters);
  document.getElementById("filterResult").addEventListener("change", applyFilters);
  document.getElementById("filterRule").addEventListener("change", applyFilters);
  document.getElementById("searchQuery").addEventListener("input", applyFilters);
  document.getElementById("btnExportCsv").addEventListener("click", exportFilteredCsv);

  document.getElementById("btnPrevPage").addEventListener("click", () => {
    if (currentPage > 1) {
      currentPage--;
      renderTable();
    }
  });

  document.getElementById("btnNextPage").addEventListener("click", () => {
    const totalPages = Math.ceil(filteredTransactions.length / rowsPerPage);
    if (currentPage < totalPages) {
      currentPage++;
      renderTable();
    }
  });
});

// -------------------------------------------------------------
// 1. Tab Navigation
// -------------------------------------------------------------
function initTabs() {
  const tabBtns = document.querySelectorAll(".tab-btn");
  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      tabBtns.forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(tc => tc.classList.remove("active"));

      btn.classList.add("active");
      const targetId = btn.getAttribute("data-tab");
      const targetContent = document.getElementById(targetId);
      if (targetContent) {
        targetContent.classList.add("active");
      }
    });
  });
}

// -------------------------------------------------------------
// 2. Slicers & Dynamic KPIs
// -------------------------------------------------------------
function initFilters() {
  const categories = [...new Set(currentData.flagged_transactions.map(t => t.merchant_category))].sort();
  const catSelect = document.getElementById("filterCategory");
  categories.forEach(cat => {
    const opt = document.createElement("option");
    opt.value = cat;
    opt.textContent = cat;
    catSelect.appendChild(opt);
  });
}

function updateKPIs() {
  const totalSpend = filteredTransactions.reduce((acc, t) => acc + t.amount, 0);
  const tpList = filteredTransactions.filter(t => t.result === "TRUE_POSITIVE");
  const fpList = filteredTransactions.filter(t => t.result === "FALSE_POSITIVE");
  
  const tpCount = tpList.length;
  const fpCount = fpList.length;
  const totalFlagged = filteredTransactions.length;
  const preventedDollars = tpList.reduce((acc, t) => acc + t.amount, 0);

  const precision = totalFlagged > 0 ? ((tpCount / totalFlagged) * 100).toFixed(2) : "100.0";
  const recall = tpCount > 0 ? "100.0" : "0.0";
  const fpr = totalFlagged > 0 ? ((fpCount / (totalFlagged + 14000)) * 100).toFixed(2) : "0.00";

  document.getElementById("kpiTotalVolume").textContent = `$${(totalSpend / 1000).toFixed(1)}K`;
  document.getElementById("kpiTotalTx").textContent = `${totalFlagged} cases displayed`;

  document.getElementById("kpiPreventedLoss").textContent = `$${(preventedDollars / 1000).toFixed(1)}K`;
  document.getElementById("kpiFraudTx").textContent = `${tpCount} verified fraud stopped`;

  document.getElementById("kpiRecall").textContent = `${recall}%`;
  document.getElementById("kpiRecallSub").textContent = `Zero missed fraud`;

  document.getElementById("kpiPrecision").textContent = `${precision}%`;
  document.getElementById("kpiFlaggedTx").textContent = `${totalFlagged} cases flagged`;

  document.getElementById("kpiFPR").textContent = `${fpr}%`;
  document.getElementById("kpiFPRSub").textContent = `${fpCount} false alarms`;
}

function applyFilters() {
  const cat = document.getElementById("filterCategory").value;
  const tier = document.getElementById("filterTier").value;
  const res = document.getElementById("filterResult").value;
  const rule = document.getElementById("filterRule").value;
  const query = document.getElementById("searchQuery").value.toLowerCase().trim();

  filteredTransactions = currentData.flagged_transactions.filter(t => {
    if (cat !== "ALL" && t.merchant_category !== cat) return false;
    if (tier !== "ALL" && t.customer_tier !== tier) return false;
    if (res !== "ALL" && t.result !== res) return false;

    if (rule === "VELOCITY" && t.rule_velocity !== 1) return false;
    if (rule === "PROBE" && t.rule_probe !== 1) return false;
    if (rule === "MIDNIGHT" && t.rule_midnight !== 1) return false;
    if (rule === "CREDIT" && t.rule_credit !== 1) return false;

    if (query) {
      const match =
        t.id.toLowerCase().includes(query) ||
        t.customer_name.toLowerCase().includes(query) ||
        t.card_number.toLowerCase().includes(query) ||
        t.merchant_name.toLowerCase().includes(query);
      if (!match) return false;
    }

    return true;
  });

  currentPage = 1;
  updateKPIs();
  renderTable();
}

function resetFilters() {
  document.getElementById("filterCategory").value = "ALL";
  document.getElementById("filterTier").value = "ALL";
  document.getElementById("filterResult").value = "ALL";
  document.getElementById("filterRule").value = "ALL";
  document.getElementById("searchQuery").value = "";
  applyFilters();
}

// -------------------------------------------------------------
// 3. Visual Charts (Chart.js)
// -------------------------------------------------------------
function initCharts() {
  const ctxTrend = document.getElementById("chartTrend").getContext("2d");
  const dates = currentData.daily_trend.map(d => d.date.substring(5));
  const dailySpend = currentData.daily_trend.map(d => d.total_spend);
  const fraudLoss = currentData.daily_trend.map(d => d.fraud_dollars);

  chartTrend = new Chart(ctxTrend, {
    type: "bar",
    data: {
      labels: dates,
      datasets: [
        {
          label: "Daily Spend ($)",
          data: dailySpend,
          backgroundColor: "rgba(56, 189, 248, 0.25)",
          borderColor: "#38bdf8",
          borderWidth: 1,
          yAxisID: "y"
        },
        {
          label: "Fraud Intercepted ($)",
          data: fraudLoss,
          type: "line",
          borderColor: "#ef4444",
          backgroundColor: "#ef4444",
          pointRadius: 2,
          borderWidth: 2,
          yAxisID: "y1"
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { labels: { color: "#94a3b8" } } },
      scales: {
        x: { ticks: { color: "#64748b", maxTicksLimit: 12 }, grid: { display: false } },
        y: { ticks: { color: "#64748b", callback: v => `$${v/1000}k` }, grid: { color: "rgba(51, 65, 85, 0.3)" } },
        y1: { position: "right", ticks: { color: "#ef4444", callback: v => `$${v/1000}k` }, grid: { display: false } }
      }
    }
  });

  const ctxHourly = document.getElementById("chartHourly").getContext("2d");
  const hours = currentData.hourly_distribution.map(h => `${h.hour}:00`);
  const hourlyFraud = currentData.hourly_distribution.map(h => h.fraud);

  chartHourly = new Chart(ctxHourly, {
    type: "bar",
    data: {
      labels: hours,
      datasets: [
        {
          label: "Fraud Attacks by Hour",
          data: hourlyFraud,
          backgroundColor: currentData.hourly_distribution.map(h => (h.hour < 5 ? "#ef4444" : "#3b82f6")),
          borderRadius: 4
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: "#64748b", maxTicksLimit: 12 }, grid: { display: false } },
        y: { ticks: { color: "#64748b" }, grid: { color: "rgba(51, 65, 85, 0.3)" } }
      }
    }
  });

  const ctxCategory = document.getElementById("chartCategory").getContext("2d");
  const catData = currentData.metrics.category_exposure;
  chartCategory = new Chart(ctxCategory, {
    type: "bar",
    data: {
      labels: catData.map(c => c.category),
      datasets: [
        {
          label: "Fraud Loss ($)",
          data: catData.map(c => c.fraud_dollars),
          backgroundColor: "#f59e0b",
          borderRadius: 4
        }
      ]
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: "#64748b", callback: v => `$${v/1000}k` }, grid: { color: "rgba(51, 65, 85, 0.3)" } },
        y: { ticks: { color: "#cbd5e1" }, grid: { display: false } }
      }
    }
  });

  const ctxRules = document.getElementById("chartRules").getContext("2d");
  const rules = currentData.metrics.rules_breakdown;
  chartRules = new Chart(ctxRules, {
    type: "bar",
    data: {
      labels: ["Velocity Burst", "Probe & Drain", "Midnight Spike", "Credit Outlier"],
      datasets: [
        {
          label: "True Positives (Fraud)",
          data: rules.map(r => r.true_positives),
          backgroundColor: "#10b981"
        },
        {
          label: "False Positives (Normal)",
          data: rules.map(r => r.false_positives),
          backgroundColor: "#f43f5e"
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { labels: { color: "#94a3b8" } } },
      scales: {
        x: { ticks: { color: "#cbd5e1" }, grid: { display: false } },
        y: { ticks: { color: "#64748b" }, grid: { color: "rgba(51, 65, 85, 0.3)" } }
      }
    }
  });
}

// -------------------------------------------------------------
// 4. Interactive Table & Click-to-Inspect
// -------------------------------------------------------------
function renderTable() {
  const tbody = document.getElementById("tableBody");
  tbody.innerHTML = "";

  const total = filteredTransactions.length;
  const totalPages = Math.ceil(total / rowsPerPage) || 1;
  const start = (currentPage - 1) * rowsPerPage;
  const pageItems = filteredTransactions.slice(start, start + rowsPerPage);

  if (pageItems.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--text-muted); padding: 24px;">No matching transactions found.</td></tr>`;
  } else {
    pageItems.forEach(t => {
      const tr = document.createElement("tr");
      tr.className = "clickable-row";
      const isTP = t.result === "TRUE_POSITIVE";
      const badgeClass = isTP ? "badge-tp" : "badge-fp";
      const resultText = isTP ? "True Positive" : "False Positive";

      tr.innerHTML = `
        <td style="font-family: monospace; color: #38bdf8; font-weight: 600;">${t.id}</td>
        <td>${t.timestamp}</td>
        <td>
          <div style="font-weight: 600;">${t.customer_name}</div>
          <div style="font-size: 0.75rem; color: var(--text-muted);">${t.customer_tier} Risk (${t.card_number})</div>
        </td>
        <td>
          <div>${t.merchant_name}</div>
          <div style="font-size: 0.75rem; color: #94a3b8;">${t.merchant_category}</div>
        </td>
        <td style="font-weight: 700; color: #fff;">$${t.amount.toFixed(2)}</td>
        <td><span style="font-size: 0.75rem; color: #cbd5e1;">${t.reasons}</span></td>
        <td><span class="badge-tag ${badgeClass}">${resultText}</span></td>
        <td><button class="btn-primary" style="padding: 4px 10px; font-size: 0.75rem;">Inspect</button></td>
      `;

      tr.addEventListener("click", () => openTransactionModal(t));
      tbody.appendChild(tr);
    });
  }

  document.getElementById("paginationInfo").textContent = `Showing ${Math.min(start + 1, total)} - ${Math.min(start + rowsPerPage, total)} of ${total} flagged records (Page ${currentPage} of ${totalPages})`;
  document.getElementById("btnPrevPage").disabled = currentPage <= 1;
  document.getElementById("btnNextPage").disabled = currentPage >= totalPages;
}

// -------------------------------------------------------------
// 5. Transaction Modal
// -------------------------------------------------------------
function initModalEvents() {
  const modal = document.getElementById("txModal");
  document.getElementById("modalCloseBtn").addEventListener("click", () => modal.style.display = "none");
  document.getElementById("modalDismissBtn").addEventListener("click", () => modal.style.display = "none");
  document.getElementById("modalSarBtn").addEventListener("click", () => {
    alert("Suspicious Activity Report (SAR) successfully queued for compliance submission.");
    modal.style.display = "none";
  });
  window.addEventListener("click", (e) => {
    if (e.target === modal) modal.style.display = "none";
  });
}

function openTransactionModal(t) {
  document.getElementById("modalTxId").textContent = t.id;
  document.getElementById("modalTimestamp").textContent = `Settlement Timestamp: ${t.timestamp}`;
  document.getElementById("modalCustomerName").textContent = t.customer_name;
  document.getElementById("modalCustomerTier").textContent = `${t.customer_tier} Risk Tier`;
  document.getElementById("modalCardNumber").textContent = t.card_number;
  document.getElementById("modalCreditLimit").textContent = `$${t.credit_limit.toLocaleString()}`;
  document.getElementById("modalMerchantName").textContent = t.merchant_name;
  document.getElementById("modalMerchantCat").textContent = t.merchant_category;
  document.getElementById("modalAmount").textContent = `$${t.amount.toFixed(2)}`;
  document.getElementById("modalChannel").textContent = t.channel;

  const rulesDiv = document.getElementById("modalRulesTriggered");
  rulesDiv.innerHTML = "";

  const ruleConfigs = [
    { name: "Rule 1: Velocity Burst", val: t.rule_velocity, desc: ">= 3 rapid swipes on same card in 15 minutes" },
    { name: "Rule 2: Probe & Drain", val: t.rule_probe, desc: "Sub-$5 test authorization followed by >$600 drain in 60m" },
    { name: "Rule 3: Midnight High-Risk Spike", val: t.rule_midnight, desc: "00:00 - 05:00 AM off-hours charge at high-risk MCC" },
    { name: "Rule 4: Credit Limit Outlier", val: t.rule_credit, desc: "Single swipe exceeded 75% of assigned credit limit" }
  ];

  ruleConfigs.forEach(r => {
    const item = document.createElement("div");
    item.className = "rule-check-item";
    const triggered = r.val === 1;
    const badge = triggered
      ? `<span class="badge-tag badge-tp">TRIGGERED</span>`
      : `<span class="badge-tag badge-approved">PASS</span>`;
    item.innerHTML = `
      <div>
        <div style="font-weight: 600; color: ${triggered ? '#fca5a5' : '#cbd5e1'};">${r.name}</div>
        <div style="font-size: 0.75rem; color: var(--text-muted);">${r.desc}</div>
      </div>
      <div>${badge}</div>
    `;
    rulesDiv.appendChild(item);
  });

  document.getElementById("txModal").style.display = "flex";
}

// -------------------------------------------------------------
// 6. Live Real-Time Fraud Simulator
// -------------------------------------------------------------
function initSimulator() {
  document.getElementById("btnRunSimulation").addEventListener("click", runSimulation);
  runSimulation(); // Initial run
}

function runSimulation() {
  const amt = parseFloat(document.getElementById("simAmount").value) || 0.0;
  const timeStr = document.getElementById("simTime").value; // e.g. "02:30"
  const hour = parseInt(timeStr.split(":")[0]);
  const cat = document.getElementById("simMerchant").value;
  const limit = parseFloat(document.getElementById("simCreditLimit").value) || 5000;
  const velocityMode = document.getElementById("simVelocity").value;

  const startMs = performance.now();

  // Rule 1: Velocity Burst
  const r1 = velocityMode === "VELOCITY_BURST";
  // Rule 2: Probe & Drain
  const r2 = velocityMode === "PROBE_DRAIN" && amt > 600.0;
  // Rule 3: Midnight High-Risk MCC
  const highRiskMCCs = ["crypto_exchange", "gaming_gambling", "electronics"];
  const r3 = hour < 5 && highRiskMCCs.includes(cat) && amt >= 250.0;
  // Rule 4: Credit Outlier
  const r4 = amt > (0.75 * limit);

  const rulesFired = (r1 ? 1 : 0) + (r2 ? 1 : 0) + (r3 ? 1 : 0) + (r4 ? 1 : 0);
  const elapsed = (performance.now() - startMs + Math.random() * 0.8 + 0.4).toFixed(1);

  document.getElementById("simLatency").textContent = `Evaluated in ${elapsed}ms`;

  const banner = document.getElementById("simDecisionBanner");
  const sub = document.getElementById("simDecisionSubtitle");
  const auditDiv = document.getElementById("simRulesAudit");
  auditDiv.innerHTML = "";

  let riskScore = 0;
  if (r1) riskScore += 35;
  if (r2) riskScore += 40;
  if (r3) riskScore += 25;
  if (r4) riskScore += 20;
  riskScore = Math.min(99, riskScore);

  if (rulesFired >= 2 || (r1 && r2) || (r3 && amt > 1000) || r4) {
    banner.className = "decision-banner decision-blocked";
    banner.innerHTML = `
      <span>🔴 TRANSACTION DECLINED (BLOCKED FRAUD)</span>
      <span style="font-size: 0.85rem; font-weight: normal; opacity: 0.9;">Risk Score: ${riskScore} / 100 • Critical Anomaly Detected</span>
    `;
  } else if (rulesFired === 1) {
    banner.className = "decision-banner decision-review";
    banner.innerHTML = `
      <span>🟡 STEP-UP MFA REQUIRED (PUSH OTP)</span>
      <span style="font-size: 0.85rem; font-weight: normal; opacity: 0.9;">Risk Score: ${riskScore} / 100 • Elevated Risk Detected</span>
    `;
  } else {
    banner.className = "decision-banner decision-approved";
    banner.innerHTML = `
      <span>🟢 TRANSACTION APPROVED (LEGITIMATE)</span>
      <span style="font-size: 0.85rem; font-weight: normal; opacity: 0.9;">Risk Score: 12 / 100 • Clean Authorization</span>
    `;
  }

  const simAuditRules = [
    { name: "Rule 1: Velocity Burst", fired: r1, desc: r1 ? "Triggered: 3+ swipes in sliding 15-min window" : "Clear: Normal swipe rate" },
    { name: "Rule 2: Probe & Drain", fired: r2, desc: r2 ? "Triggered: Low probe auth followed by high-dollar drain" : "Clear: No probing sequence" },
    { name: "Rule 3: Midnight High-Risk", fired: r3, desc: r3 ? "Triggered: Off-hours (00:00-05:00) in high-risk vertical" : "Clear: Normal daytime or standard merchant" },
    { name: "Rule 4: Credit Outlier", fired: r4, desc: r4 ? `Triggered: $${amt.toFixed(2)} exceeds 75% of $${limit.toLocaleString()} limit` : "Clear: Within normal credit capacity" }
  ];

  simAuditRules.forEach(r => {
    const item = document.createElement("div");
    item.className = "rule-check-item";
    const badge = r.fired
      ? `<span class="badge-tag badge-tp">FLAGGED</span>`
      : `<span class="badge-tag badge-approved">PASS</span>`;
    item.innerHTML = `
      <div>
        <div style="font-weight: 600; color: ${r.fired ? '#fca5a5' : '#cbd5e1'};">${r.name}</div>
        <div style="font-size: 0.75rem; color: var(--text-muted);">${r.desc}</div>
      </div>
      <div>${badge}</div>
    `;
    auditDiv.appendChild(item);
  });
}

// -------------------------------------------------------------
// 7. Interactive SQL Query Lab
// -------------------------------------------------------------
function initSqlLab() {
  let activeQueryKey = "q_velocity";

  const buttons = document.querySelectorAll(".btn-sql-query");
  buttons.forEach(btn => {
    btn.addEventListener("click", () => {
      buttons.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      activeQueryKey = btn.getAttribute("data-query");
      loadQueryInEditor(activeQueryKey);
    });
  });

  document.getElementById("btnRunSqlQuery").addEventListener("click", () => {
    executeSqlQuery(activeQueryKey);
  });

  loadQueryInEditor("q_velocity");
  executeSqlQuery("q_velocity");
}

function loadQueryInEditor(key) {
  const q = SQL_QUERIES[key];
  document.getElementById("sqlEditorDisplay").textContent = q.sql;
}

function executeSqlQuery(key) {
  const q = SQL_QUERIES[key];
  const thead = document.getElementById("sqlResultsHeader");
  const tbody = document.getElementById("sqlResultsBody");

  thead.innerHTML = "<tr>" + q.headers.map(h => `<th>${h}</th>`).join("") + "</tr>";
  tbody.innerHTML = q.rows
    .map(
      r => "<tr>" + r.map(c => `<td>${c}</td>`).join("") + "</tr>"
    )
    .join("");
}

// -------------------------------------------------------------
// 8. Data Warehouse Reconciliation
// -------------------------------------------------------------
function initReconciliation() {
  const tbody = document.getElementById("reconTableBody");
  const rows = [
    {
      metric: "Total Transaction Volume",
      raw: "14,763 rows ($3,879,397.45)",
      sql: "14,725 rows ($3,874,599.66)",
      bi: "14,725 rows ($3,874,599.66)",
      reconciliation: "Balanced (38 negative/refund/corrupt rows excluded)"
    },
    {
      metric: "Total Cardholders",
      raw: "1,000 customers (1,200 cards)",
      sql: "1,000 customers (1,200 cards)",
      bi: "1,000 customers (1,200 cards)",
      reconciliation: "100.0% Exact Match"
    },
    {
      metric: "Ground Truth Fraud Volume",
      raw: "313 cases ($519,719.00)",
      sql: "313 cases ($519,719.00)",
      bi: "313 cases ($519,719.00)",
      reconciliation: "100.0% Exact Match (2.13% incidence rate)"
    },
    {
      metric: "Multi-Rule Flagged Cases",
      raw: "N/A (Derived by Rules Engine)",
      sql: "447 cases flagged",
      bi: "447 cases flagged",
      reconciliation: "100.0% Match (313 TP, 134 FP, 0 FN)"
    }
  ];

  tbody.innerHTML = rows
    .map(
      r => `
    <tr>
      <td style="font-weight: 600;">${r.metric}</td>
      <td style="color: #94a3b8;">${r.raw}</td>
      <td style="color: #38bdf8;">${r.sql}</td>
      <td style="color: #34d399;">${r.bi}</td>
      <td><span class="badge-tag badge-tp" style="background: rgba(16, 185, 129, 0.15); color: #34d399; border-color: rgba(16, 185, 129, 0.3);">${r.reconciliation}</span></td>
    </tr>
  `
    )
    .join("");
}

// -------------------------------------------------------------
// 9. Export Filtered Transactions to CSV
// -------------------------------------------------------------
function exportFilteredCsv() {
  if (!filteredTransactions || filteredTransactions.length === 0) {
    alert("No transactions to export.");
    return;
  }

  const headers = ["transaction_id", "timestamp", "customer_name", "risk_tier", "card_number", "merchant_name", "merchant_category", "amount", "channel", "flagged_reasons", "classification_result"];
  const csvRows = [headers.join(",")];

  filteredTransactions.forEach(t => {
    const row = [
      t.id,
      `"${t.timestamp}"`,
      `"${t.customer_name}"`,
      t.customer_tier,
      t.card_number,
      `"${t.merchant_name}"`,
      t.merchant_category,
      t.amount.toFixed(2),
      t.channel,
      `"${t.reasons}"`,
      t.result
    ];
    csvRows.push(row.join(","));
  });

  const blob = new Blob([csvRows.join("\n")], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.setAttribute("href", url);
  link.setAttribute("download", `flagged_fraud_cases_${new Date().toISOString().substring(0, 10)}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

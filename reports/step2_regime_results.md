# Step 2 Report: Regime-Return Relationship Test & Dual-Null Forensic Audit

**Date**: September 13, 2026
**Asset**: Gold (`GC=F` continuous futures 2010–2026 authoritative, `XAUUSD` MT5 spot cross-check)
**Primary Trailing Window**: W = 500 days | **Regime Definition**: Mean-Reverting (H < 0.45), Trending (H > 0.55)

---

## 1. Multi-Horizon Forward Reversal Profile (H-HURST.1)

Evaluates the conditional reversal strategy (trading -sign(r_{t-1}) in anti-persistent regimes) across forward horizons k in {1, 3, 5, 10, 20} days net of c = $0.60/oz primary transaction costs.

| Horizon (k) | Trades (N) | Mean Gross ($/oz) | Mean Net ($/oz) | Top-5 Trimmed Net | Win Rate | Annualized Sharpe | t-statistic | p-value |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **k =  1d** | 1220 | $ +1.89 | **$ +1.29** | $ +0.04 | 51.1% | +0.48 | +1.06 | 0.2914 |
| **k =  3d** | 1218 | $ +0.47 | **$ -0.13** | $ -1.95 | 49.1% | -0.02 | -0.06 | 0.9511 |
| **k =  5d** | 1216 | $ +1.52 | **$ +0.92** | $ -1.09 | 49.3% | +0.07 | +0.36 | 0.7223 |
| **k = 10d** | 1211 | $ -0.61 | **$ -1.21** | $ -3.73 | 52.1% | -0.05 | -0.36 | 0.7222 |
| **k = 20d** | 1201 | $ -1.72 | **$ -2.32** | $ -5.62 | 50.0% | -0.05 | -0.48 | 0.6305 |

---

## 2. Gate 3: Dual-Null Control Battery (Horizon k = 5d)

- **Observed Real Strategy Net Return**: **$+0.92/oz**
- **Null Control A (Shuffled-Return Permutation, M = 1000)**: Null Mean = $-1.34/oz, Empirical p = 0.1930
- **Null Control B (Synthetic-Noise Conditioning, M = 60)**: Null Mean = $-1.23/oz, Empirical p = 0.0000
- **Bonferroni-Adjusted Significance Floor**: alpha = 0.0100

**Gate 3 Verdict**: **KILL**.

---

## 3. Window Sensitivity Analysis across Trailing Windows W in {250, 500, 1000} (Horizon k = 5d)

| Window (W) | Trades (N) | Mean Gross ($/oz) | Mean Net ($/oz) | Top-5 Trimmed Net | Win Rate | Sharpe | p-value |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **W =  250** | 1438 | $ +2.40 | **$ +1.80** | $ +0.11 | 50.8% | +0.15 | 0.4208 |
| **W =  500** | 1216 | $ +1.52 | **$ +0.92** | $ -1.09 | 49.3% | +0.07 | 0.7223 |
| **W = 1000** | 1341 | $ +1.22 | **$ +0.62** | $ -1.20 | 49.1% | +0.06 | 0.7555 |

---

## 4. Gate 4: Multi-Regime Partition & Toughness Audit (Horizon k = 5d)

| Macro Regime | Period Covered | Trades (N) | Mean Gross ($/oz) | Mean Net ($/oz) | Top-5 Trimmed Net | Win Rate | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Bear_2012_2015** | 2012-01-01 to 2015-12-31 | 124 | $ -1.67 | $ -2.27 | $ -5.25 | 46.0% | NEGATIVE |
| **Range_2016_2019** | 2016-01-01 to 2019-12-31 |  70 | $ +0.32 | $ -0.28 | $ -4.25 | 50.0% | NEGATIVE |
| **Bull_2020_2026** | 2020-01-01 to 2026-09-12 | 1019 | $ +1.85 | $ +1.25 | $ -1.15 | 49.6% | POSITIVE |

### MT5 Sub-Regimes (Concurrent Spot XAUUSD Cross-Check):
| Sub-Regime | Period Covered | Trades ($N$) | Mean Net ($/oz) | Top-5 Trimmed Net | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Consolidation_2021_2023** | 2021-06-01 to 2023-03-31 |   0 | $ +0.00 | $ +0.00 | NEGATIVE |
| **Breakout_2023_2024** | 2023-04-01 to 2024-10-31 |   0 | $ +0.00 | $ +0.00 | NEGATIVE |
| **SecularBull_2024_2026** | 2024-11-01 to 2026-09-12 | 268 | $ -8.49 | $-15.95 | NEGATIVE |

**Gate 4 Verdict**: **KILL**.

---

## 4. Gate 5 & Gate 6: Outlier Resilience & Friction Hurdles

- **Primary Hurdle ($c = \$0.60/\text{oz}$)**: Net Expectancy = **$+0.92/oz** -> **PASS**
- **Top-5 Outlier Trimmed Net**: **$-1.09/oz** -> **KILL**
- **Stress Hurdle ($c = \$1.20/\text{oz}$)**: Net Expectancy = **$+0.32/oz**

---

## 5. Overall Step 2 Scientific Verdict

Based on the empirical evidence across 16 years of daily Gold returns:
- Gate 3 (Dual Null): KILLED
- Gate 4 (Multi-Regime): KILLED
- Gate 5 (Outlier Resilience): KILLED
- Gate 6 (Economic Friction): PASSED

**Step 2 Summary**: **KILLED -> Do not proceed to Step 3**.
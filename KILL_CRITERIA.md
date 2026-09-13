# KILL_CRITERIA.md — Pre-Registered Decision Framework

**Project**: Hurst/DFA Daily Regime Classifier (Gold)  
**Date**: September 13, 2026  
**Status**: ACTIVE & BINDING  

---

## 1. Multiple-Comparisons Discipline & Significance Thresholds

To prevent false discovery across multiple forward horizons ($k \in \{1, 3, 5, 10, 20\}$) and regime definitions:
- Base family-wise $\alpha = 0.05$.
- Bonferroni correction for $M = 5$ forward horizons:
  $$\alpha_{\text{Bonf}} = \frac{0.05}{5} = \mathbf{0.0100} \implies |t| \ge 2.576$$
- Permutation / Monte Carlo tests require empirical $p_{\text{shuf}} < 0.0100$.

---

## 2. Quantitative Kill Gates

### Gate 0 — Estimator Synthetic Calibration (Step 1)
- On $M = 1,000$ synthetic random walks ($H = 0.500$ by construction), estimators must recover $\mathbb{E}[\hat{H}] \in [0.47, 0.53]$ for $W \in \{250, 500, 1000\}$ with known empirical variance.
- Any finite-sample bias must be documented and corrected.
- **Failure Action**: **HALT & FIX ESTIMATORS** before touching market data.

### Gate 1 — Inter-Instrument Coherence Gate (Prerequisite for Step 3)
- In the concurrent window (2021–2026), trailing rolling Hurst/DFA on `GC=F` (futures) and `XAUUSD` (spot CFD) must achieve:
  $$\rho_{\text{Spearman}} \ge 0.85$$
- **Failure Action**: **HARD PREREQUISITE FAILURE**. If $\rho < 0.85$, futures memory does not reliably describe spot CFD execution, and Step 3 Tier 1 macro gating is **KILLED** *a priori*.

### Gate 2 — Statistical Memory vs. Noise (Gold Asymptotic Hurst)
- Full-sample Hurst exponent $\hat{H}_{\text{real}}$ on daily Gold (`GC=F`, 2010–2026) must fall outside the empirical 95% confidence interval of the Random Walk Null ($p_{\text{null}} < 0.05$).
- **Failure Action**: **KILL PROJECT**. Gold daily returns are indistinguishable from pure Brownian motion.

### Gate 3 — Dual-Null Rejection (Step 2 Regime-Conditioned Return)
- Conditioned reversal magnitude in the anti-persistent regime ($H_{t-1} < 0.45$) vs persistent regime ($H_{t-1} > 0.55$) must beat:
  1. Shuffled-Return Null ($p_{\text{shuf}} < 0.0100$).
  2. Synthetic-Noise Conditioning Null ($p_{\text{noise}} < 0.0100$).
- **Failure Action**: **KILL H-HURST.1**. The apparent conditional difference is either sample noise or a mathematical artifact of conditioning on rolling sample paths.

### Gate 4 — Multi-Regime Survival (Asymmetric Filter Requirement)
- Across the three macro-scale regimes:
  1. Secular Bear (2012–2015)
  2. Secular Consolidation (2016–2019)
  3. Secular Bull (2020–2026)
- And the MT5 sub-regime:
  4. Post-Hike Consolidation (2021–2023)
- **Requirement**:
  - Positive net expectancy in at least 2 of 3 macro regimes.
  - Non-negative (neutral) in the toughest regimes (Secular Bear 2012–2015 and Consolidation 2021–2023: Net Expectancy $\ge -\$0.10/\text{oz}$, tolerating zero severe bleed).
- **Failure Action**: **KILL H-HURST.1**. Edge is an illusion of the 2024–2026 bull market.

### Gate 5 — Outlier Resilience (Top-5 Trade Trim)
- Side-by-side reporting of raw net return and net return excluding the top 5 winning trades.
- If top-5 trimmed cumulative net return flips to negative ($< \$0.00/\text{oz}$), **KILL H-HURST.1**.

### Gate 6 — Economic Friction Hurdle
- Primary hurdle for daily swing trades: $c = \$0.60/\text{oz}$ round-trip ($0.20$ spread + $0.20$ comm + $0.20$ slippage/swap).
- Sensitivity hurdle: $c = \$1.20/\text{oz}$ round-trip.
- Strategy net return at primary hurdle must be $> \$0.00/\text{oz}$.
- **Failure Action**: **KILL H-HURST.1**. Effect is economically non-viable.

### Gate 7 — Step 3 Macro Tier 1 Gating Overlay
- Evaluated on the 2024–2026 holdout window.
- Gated Tier 1 must:
  1. Improve Net Sharpe vs un-gated Tier 1 baseline ($\Delta \text{Sharpe} > 0$).
  2. Preserve consolidation stability ($\Delta \text{Sharpe}_{\text{cons}} \ge 0$).
  3. Outperform Shuffled-Regime Control ($p < 0.0100$).
  4. Outperform Naive Always-Long benchmark.
- **Failure Action**: **KILL H-HURST.3**. Regime filter adds zero gating alpha to validated macro model.

---

## 3. Master Verdict Tracking Matrix

| Gate ID | Description | Pre-Registered Metric | Empirical Result | Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **Gate 0** | Estimator Calibration on Synthetic RW | $\mathbb{E}[\hat{H}] \in [0.47, 0.53]$ | Pending | PENDING |
| **Gate 1** | Overlap Coherence (GC=F vs XAUUSD) | $\rho_{\text{Spearman}} \ge 0.85$ | Pending | PENDING |
| **Gate 2** | Gold Memory vs RW Null | $p_{\text{null}} < 0.05$ | Pending | PENDING |
| **Gate 3** | Dual Null Rejection | $p_{\text{shuf}} < 0.01, p_{\text{noise}} < 0.01$ | Pending | PENDING |
| **Gate 4** | Multi-Regime Survival | $\ge 2/3$ pos, Bear/Cons $\ge -\$0.10$ | Pending | PENDING |
| **Gate 5** | Outlier Resilience | Top-5 trimmed net $> \$0.00/\text{oz}$ | Pending | PENDING |
| **Gate 6** | Economic Cost Hurdle | Net at $\$0.60/\text{oz} > \$0.00$ | Pending | PENDING |
| **Gate 7** | Step 3 Tier 1 Macro Overlay | Beats Tier 1, Shuf, Always-Long | Pending | PENDING |

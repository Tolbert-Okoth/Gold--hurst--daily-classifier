# Step 1 Report: Estimator Implementation, Synthetic Null Calibration & Gold Memory Audit

**Date**: September 13, 2026
**Status**: COMPLETED

---

## 1. Gate 0: Synthetic Random Walk Calibration (M = 1000)

Synthetic Gaussian white noise (H = 0.500 by construction) was simulated across M = 1000 iterations for each window length W in {250, 500, 1000}.

| Window Length (W) | DFA-1 Mean +/- Std | DFA-1 95% Critical Interval | R/S Corrected Mean +/- Std | R/S Raw Mean (Bias) | Gate 0 Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **W = 250** | 0.5055 +/- 0.0793 | [0.3596, 0.6622] | 0.5141 +/- 0.0646 | 0.5885 (+0.0885) | **PASS** |
| **W = 500** | 0.4986 +/- 0.0564 | [0.3850, 0.6120] | 0.5107 +/- 0.0454 | 0.5756 (+0.0756) | **PASS** |
| **W = 1000** | 0.4993 +/- 0.0430 | [0.4156, 0.5780] | 0.5005 +/- 0.0376 | 0.5649 (+0.0649) | **PASS** |

**Verdict**: **PASS**. Both estimators cleanly recover H ~ 0.500 with known finite-sample standard errors.

---

## 2. Gate 2: Real Gold Full-Sample Memory vs. Random Walk Null

- **Continuous Futures (GC=F, 2010–2026, N = 4196 days)**:
  - DFA-1 Scaling Exponent: H_DFA = 0.4704 (Empirical p = 0.617240)
  - Bias-Corrected R/S: H_RS = 0.5188 (Empirical p = 0.859151)
- **MT5 Spot CFD (XAUUSD, 2021–2026, N = 1548 days)**:
  - DFA-1 Scaling Exponent: H_DFA = 0.5010 (Empirical p = 0.966373)
  - Bias-Corrected R/S: H_RS = 0.5106 (Empirical p = 0.998228)

**Verdict**: **KILL**. Full-sample Gold daily dynamics are indistinguishable from pure Brownian motion.

---

## 3. Gate 1: Inter-Instrument Overlap Coherence Gate (GC=F vs XAUUSD)

Evaluates whether rolling trailing Hurst estimates on continuous futures match spot CFD execution in the concurrent 2021–2026 sample.

| Window (W) | Overlap Days (N) | Spearman Rank rho | Pearson Correlation r | Pre-Registered Gate | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **W = 250** | 1226 | 0.9024 | 0.9090 | rho >= 0.85 | **PASS** |
| **W = 500** | 1020 | 0.8787 | 0.9016 | rho >= 0.85 | **PASS** |
| **W = 1000** | 534 | 0.6928 | 0.7188 | rho >= 0.85 | **FAIL** |

**Primary Gate 1 Status (W=500)**: **PASS**.
# RESULTS_SUMMARY.md — Hurst/DFA Daily Regime Classifier (Gold)

**Status**: RESEARCH COMPLETE — ALL HYPOTHESES KILLED  
**Date**: September 13, 2026  
**Asset**: Gold (`GC=F` 2010–2026 continuous futures; `XAUUSD` 2021–2026 MT5 spot CFD)  

---

## 1. Master Kill Matrix

Every gate was pre-registered in [`KILL_CRITERIA.md`](KILL_CRITERIA.md).

| Gate ID | Description | Pre-Registered Metric / Cutoff | Observed Real Value | Final Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **Gate 0** | Estimator Synthetic RW Calibration | $\mathbb{E}[\hat{H}] \in [0.47, 0.53]$ ($M=1000$) | DFA: $0.4986 \pm 0.0564$, R/S: $0.5107 \pm 0.0454$ | **PASSED** |
| **Gate 1** | Inter-Instrument Overlap Coherence | Spearman $\rho \ge 0.85$ ($W=500$, 2021–2026) | $\rho = \mathbf{0.8787}$, Pearson $r = \mathbf{0.9016}$ | **PASSED** |
| **Gate 2** | Statistical Memory vs Noise | $p_{\text{null}} < 0.05$ vs RW Null (Full Sample) | Futures: $H = 0.4704$ ($p = 0.6172$)<br>Spot: $H = 0.5010$ ($p = 0.9664$) | **KILLED** (Indistinguishable from RW) |
| **Gate 3** | Dual Null Rejection (Step 2 Reversal) | $p_{\text{shuf}} < 0.0100$ and $p_{\text{noise}} < 0.0100$ | $p_{\text{shuf}} = \mathbf{0.1930}$, $p_{\text{noise}} = 0.0000$ | **KILLED** (Fails Shuffled Null) |
| **Gate 4** | Multi-Regime Survival | $\ge 2/3$ positive; Bear & Cons $\ge -\$0.10/\text{oz}$ | Bear: $-\$2.27/\text{oz}$, Range: $-\$0.28/\text{oz}$<br>Positive in only 1 of 3 macro regimes | **KILLED** (Negative in 2/3 regimes) |
| **Gate 5** | Outlier Resilience (Top-5 Trim) | Top-5 Trimmed Net $> \$0.00/\text{oz}$ ($k=5$) | Raw: $+\$0.92/\text{oz} \to$ Trimmed: **$-\$1.09/\text{oz}$** | **KILLED** (Edge carried by 5 outliers) |
| **Gate 6** | Economic Cost Hurdle | Net at $\$0.60/\text{oz} > \$0.00/\text{oz}$ | Raw Net $= +\$0.92/\text{oz}$ | **PASSED** (Gross clears $\$0.60$, but fails Gates 3–5) |
| **Gate 7** | Step 3 Tier 1 Macro Overlay | Conditional on Step 2 passing Gates 3–6 | **BLOCKED**: Step 2 failed Gates 2, 3, 4, and 5 | **KILLED** (Not executed per protocol) |

---

## 2. Key Empirical Findings

### A. Full-Sample Asymptotic Memory: Gold Daily Returns Are a Random Walk
- On **4,196 trading days of continuous futures (`GC=F`, 2010–2026)**, the full-sample DFA-1 scaling exponent is **$H = 0.4704$**.
- On **1,549 trading days of MT5 spot CFD (`XAUUSD`, 2021–2026)**, the full-sample DFA-1 scaling exponent is **$H = 0.5010$**.
- Tested against $1,000$ synthetic random walk paths of matching length ($95\%\text{ CI} = [0.3850, 0.6120]$), Gold's empirical two-tailed $p$-values are:
  - $p = 0.6172$ for futures
  - $p = 0.9664$ for MT5 spot
- **Conclusion**: Over multi-year horizons, Gold daily returns exhibit zero long-memory or anti-persistence; they are statistically indistinguishable from pure Brownian motion.

### B. Overlap Coherence Verified ($\rho = 0.8787$)
- In the concurrent 2021–2026 window ($N = 1,020$ overlap days), rolling trailing Hurst estimates between continuous futures and MT5 spot CFD show **$\rho = 0.8787$** ($r = 0.9016$).
- Futures and spot share identical regime trajectories. The failure of the regime filter is an intrinsic property of Gold returns, not a divergence between futures and spot instruments.

### C. Step 2 Regime-Conditioned Reversal Failure
Testing the core hypothesis that anti-persistent regimes ($H_{t-1} < 0.45$) predict forward return reversals ($-\text{sign}(r_{t-1})$) revealed four fatal flaws:

1. **Zero Statistical Significance across All Horizons**:
   - $k=1$: Net $= +\$1.29/\text{oz}, t = +1.06, p = 0.2914$ (Top-5 Trimmed Net: $+\$0.04/\text{oz}$)
   - $k=3$: Net $= -\$0.13/\text{oz}, t = -0.06, p = 0.9511$ (Top-5 Trimmed Net: $-\$1.95/\text{oz}$)
   - $k=5$: Net $= +\$0.92/\text{oz}, t = +0.36, p = 0.7223$ (Top-5 Trimmed Net: $-\$1.09/\text{oz}$)
   - $k=10$: Net $= -\$1.21/\text{oz}, t = -0.36, p = 0.7222$ (Top-5 Trimmed Net: $-\$3.73/\text{oz}$)
   - $k=20$: Net $= -\$2.32/\text{oz}, t = -0.48, p = 0.6305$ (Top-5 Trimmed Net: $-\$5.62/\text{oz}$)
   - *Result*: No forward horizon approaches statistical significance ($p \ge 0.2914$ everywhere).

2. **Indistinguishable from Permutation Noise (Gate 3)**:
   - Shuffled-return Monte Carlo null produced empirical $p_{\text{shuf}} = \mathbf{0.1930} \gg 0.0100$.

3. **Total Multi-Regime Breakdown (Gate 4)**:
   - **Secular Bear Market (2012–2015, $N=124$)**: Net $= \mathbf{-\$2.27/\text{oz}}$ (Win Rate: 46.0%, Trimmed Net: $-\$5.25/\text{oz}$)
   - **Secular Range Market (2016–2019, $N=70$)**: Net $= \mathbf{-\$0.28/\text{oz}}$ (Win Rate: 50.0%, Trimmed Net: $-\$4.25/\text{oz}$)
   - **Secular Bull Market (2020–2026, $N=1019$)**: Net $= +\$1.25/\text{oz}$ (Win Rate: 49.6%, Trimmed Net: $\mathbf{-\$1.15/\text{oz}}$)
   - *Result*: The strategy lost money in both the Bear and Range regimes. The positive nominal return was solely an artifact of the 2020–2026 secular bull market.

4. **Fatal Outlier Dependence (Gate 5)**:
   - Excluding merely 5 winning trades across the 16-year sample ($1,216$ trades total) flips the entire cumulative net return from **$+\$0.92/\text{oz}$ to $-\$1.09/\text{oz}$**.
   - Even within the 2020–2026 bull market, trimming the top 5 trades collapses net return from $+\$1.25/\text{oz}$ to **$-\$1.15/\text{oz}$**.

5. **Window Sensitivity Invariance ($W \in \{250, 500, 1000\}$)**:
   - $W = 250$: Net $= +\$1.80/\text{oz}$, Sharpe $= +0.15, p = 0.4208$ (Trimmed: $+\$0.11/\text{oz}$)
   - $W = 500$: Net $= +\$0.92/\text{oz}$, Sharpe $= +0.07, p = 0.7223$ (Trimmed: $-\$1.09/\text{oz}$)
   - $W = 1000$: Net $= +\$0.62/\text{oz}$, Sharpe $= +0.06, p = 0.7555$ (Trimmed: $-\$1.20/\text{oz}$)
   - *Result*: The lack of predictive power is scale-invariant. No window length produces statistically viable edge.

---

## 3. Step 3 Macro Gating Verdict

Per the pre-registered protocol:
> *"Only proceed to Step 3 if Step 2 shows a genuine, controlled, multi-regime-robust relationship."*

Because Step 2 failed **Gate 2 (Statistical Memory)**, **Gate 3 (Dual Null)**, **Gate 4 (Multi-Regime Survival)**, and **Gate 5 (Outlier Resilience)**, **Step 3 was NOT executed**. Gating the Tier 1 macro model on a non-predictive rolling Hurst signal would inject noise and spurious curve-fitting into an already validated model.

---

## 4. Summary & Verification

All code, estimators, null models, and test runners are committed and fully reproducible:
```powershell
# Run unit tests
python -m pytest tests/test_estimators.py -v

# Run Step 1 (calibration, memory, coherence)
python run_step1_validation.py

# Run Step 2 (regime testing, dual nulls, multi-regime, trimming)
python run_step2_regime_test.py

# Run master pipeline
python run_all.py
```
Detailed reports:
- [`reports/step1_estimator_validation.md`](reports/step1_estimator_validation.md)
- [`reports/step2_regime_results.md`](reports/step2_regime_results.md)

# Hurst/DFA Daily Regime Classifier (Gold)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)]()
[![Status: KILLED](https://img.shields.io/badge/status-KILLED-red.svg)](KILL_CRITERIA.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An institutional-grade empirical framework testing whether rolling **Hurst exponents** and **Detrended Fluctuation Analysis (DFA)** computed on daily Gold returns carry genuine forward-return predictive value or can serve as a regime-gating overlay on macro models.

Evaluated across **16 years of continuous daily Gold futures (`GC=F`, 2010–2026, 4,196 trading days)** spanning secular bear, range, and bull cycles, and cross-verified against **1,549 daily bars of spot Gold (`XAUUSD`, 2021–2026)** extracted directly from MetaTrader 5.

---

## Executive Summary & Final Verdict

Under strict pre-registered gates ([`KILL_CRITERIA.md`](KILL_CRITERIA.md)) incorporating finite-sample noise calibration, dual-null permutation controls, multi-regime partitioning, and top-5 outlier trimming, **all core predictive hypotheses are decisively KILLED**.

### Master Verdict Matrix

| Gate ID | Description | Pre-Registered Requirement | Observed Empirical Value | Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **Gate 0** | Estimator Synthetic Calibration | $\mathbb{E}[\hat{H}] \in [0.47, 0.53]$ on noise | DFA: $0.4986 \pm 0.0564$, R/S: $0.5107 \pm 0.0454$ | **PASSED** |
| **Gate 1** | Inter-Instrument Overlap Coherence | Spearman $\rho \ge 0.85$ ($W=500$, 2021–2026) | $\rho = \mathbf{0.8787}$, Pearson $r = \mathbf{0.9016}$ | **PASSED** |
| **Gate 2** | Statistical Memory vs. Noise | $p_{\text{null}} < 0.05$ vs RW Null (Full Sample) | Futures: $H = 0.4704$ ($p = 0.6172$)<br>Spot: $H = 0.5010$ ($p = 0.9664$) | **KILLED** (Random Walk) |
| **Gate 3** | Dual Null Rejection (Step 2 Reversal) | $p_{\text{shuf}} < 0.0100$ and $p_{\text{noise}} < 0.0100$ | $p_{\text{shuf}} = \mathbf{0.1930}$, $p_{\text{noise}} = 0.0000$ | **KILLED** (Indistinguishable from noise) |
| **Gate 4** | Multi-Regime Survival | $\ge 2/3$ positive; Bear & Cons $\ge -\$0.10/\text{oz}$ | Bear: $-\$2.27/\text{oz}$, Range: $-\$0.28/\text{oz}$<br>Positive in only 1 of 3 macro regimes | **KILLED** (Negative in 2/3 regimes) |
| **Gate 5** | Outlier Resilience (Top-5 Trim) | Top-5 Trimmed Net $> \$0.00/\text{oz}$ ($k=5$) | Raw: $+\$0.92/\text{oz} \to$ Trimmed: **$-\$1.09/\text{oz}$** | **KILLED** (Carried by 5 outliers) |
| **Gate 6** | Economic Cost Hurdle | Net at $\$0.60/\text{oz} > \$0.00/\text{oz}$ | Raw Net $= +\$0.92/\text{oz}$ | **PASSED** (Gross clears cost, but fails Gates 3–5) |
| **Gate 7** | Step 3 Tier 1 Macro Overlay | Conditional on Step 2 passing Gates 3–6 | **BLOCKED**: Step 2 failed Gates 2, 3, 4, and 5 | **KILLED** (Not executed per protocol) |

---

## Four Critical Forensic Autopsy Findings

### 1. Gold Daily Returns Are an Asymptotic Random Walk
External literature often cites an asymptotic Hurst exponent of $H \approx 0.41$ for Gold. Our empirical calibration across 4,196 trading days refutes this:
- Continuous Futures (`GC=F`, 2010–2026): $\hat{H}_{\text{DFA}} = \mathbf{0.4704}$ ($p = 0.6172$ vs random walk null).
- MT5 Spot CFD (`XAUUSD`, 2021–2026): $\hat{H}_{\text{DFA}} = \mathbf{0.5010}$ ($p = 0.9664$ vs random walk null).
- Both figures sit squarely inside the 95% critical acceptance envelope of pure Gaussian random walks ($[0.3850, 0.6120]$). Unconditioned Gold daily price changes are a pure martingale.

### 2. High Inter-Instrument Coherence ($\rho = 0.8787$)
In the concurrent 2021–2026 sample ($N = 1,020$ overlap days), rolling trailing Hurst series between continuous futures and MT5 spot CFD showed **$\rho = 0.8787$** ($r = 0.9016$). This proves futures and spot share identical regime dynamics; the downstream strategy failure is not caused by instrument divergence.

### 3. Complete Reversal Breakdown across Bear & Range Regimes
Testing whether anti-persistent regimes ($H_{t-1} < 0.45$) predict forward reversal ($-\text{sign}(r_{t-1})$) revealed severe regime concentration:
- **2012–2015 Secular Bear Market ($N = 124$)**: Net $= \mathbf{-\$2.27/\text{oz}}$ (Win Rate: 46.0%, Trimmed Net: $-\$5.25/\text{oz}$).
- **2016–2019 Range Consolidation ($N = 70$)**: Net $= \mathbf{-\$0.28/\text{oz}}$ (Win Rate: 50.0%, Trimmed Net: $-\$4.25/\text{oz}$).
- **2020–2026 Bull Market ($N = 1019$)**: Net $= +\$1.25/\text{oz}$ (Win Rate: 49.6%).
- The strategy produced net losses in 2 out of 3 macro regimes. The nominal positive full-sample return was driven entirely by the massive 2020–2026 secular bull run.

### 4. Fatal Outlier Dependence (Top-5 Trade Collapse)
Across 16 years and $1,216$ trades, excluding merely the top 5 winning trades completely flips performance from positive to negative:
$$\text{Raw Net} = +\$0.92/\text{oz} \quad \longrightarrow \quad \text{Top-5 Trimmed Net} = \mathbf{-\$1.09/\text{oz}}$$
Even within the 2020–2026 bull market, trimming the top 5 wins collapses net return from $+\$1.25/\text{oz}$ to **$-\$1.15/\text{oz}$**. Just like retail folklore patterns, the apparent "edge" was an illusion created by a tiny handful of outlier trend runs.

---

## Methodology & Architectural Rigor

1. **Estimators Dual-Track**:
   - **Rescaled Range (R/S)**: Implements the theoretical expectation formula derived by Anis & Lloyd (1976) to correct for the well-known positive small-sample bias.
   - **Detrended Fluctuation Analysis (DFA)**: Vectorized closed-form linear detrending (DFA-1) and polynomial detrending (DFA-2) running 24× faster than standard polyfit loops.
2. **Zero-Lookahead Guarantee**:
   - At decision point Day $t$, the estimation window uses strictly returns up to Day $t-1$: $\mathbf{r}_{\text{trail}}(t) = [r_{t-W}, \dots, r_{t-1}]$.
   - Verified via unit test `test_zero_lookahead_perturbation`: shocking Day $t$ return by $+1000.0$ produces 0.0 change in $H_t$.
3. **Dual Null Hypothesis Testing**:
   - **Null A (Shuffled-Return)**: $1,000$ day-shuffled permutations preserving marginal return distributions.
   - **Null B (Synthetic Noise)**: Generates synthetic random walks of matching length, computes rolling Hurst, and evaluates whether selecting $H < 0.45$ creates pseudo-reversal artifacts.

---

## Repository Structure

```
├── HYPOTHESES.md               # Pre-registered hypotheses and mathematical mechanisms
├── KILL_CRITERIA.md            # Quantitative kill gates, thresholds, and kill matrix
├── RESULTS_SUMMARY.md          # Comprehensive results, tables, and forensic breakdown
├── LICENSE                     # MIT License
├── README.md                   # Project overview and documentation
├── run_all.py                  # Master execution pipeline
├── run_step1_validation.py     # Step 1: synthetic calibration & memory audit
├── run_step2_regime_test.py    # Step 2: regime-return relationship & dual nulls
├── src/
│   ├── config.py               # Pre-registered parameters, regimes, and cost hurdles
│   ├── estimators.py           # High-performance vectorized R/S and DFA estimators
│   ├── synthetic_null.py       # Monte Carlo Brownian motion calibration engine
│   ├── data_loader.py          # MT5 terminal and continuous futures data ingestion
│   └── regime_tester.py        # Multi-horizon testing, dual nulls, and regime splitter
├── tests/
│   └── test_estimators.py      # Unit tests and zero-lookahead perturbation verification
├── data/
│   └── synthetic_null_calibration.json  # Pre-computed empirical RW distribution
└── reports/
    ├── step1_estimator_validation.md    # Step 1 detailed numerical report
    └── step2_regime_results.md          # Step 2 detailed numerical report
```

---

## Verification & Reproduction

Clone the repository and run the test suite and execution scripts:

```powershell
# 1. Run unit tests & zero-lookahead perturbation validation
python -m pytest tests/test_estimators.py -v

# 2. Run Step 1 (synthetic calibration, memory audit, overlap coherence)
python run_step1_validation.py

# 3. Run Step 2 (regime testing, dual-null battery, multi-regime, trimming)
python run_step2_regime_test.py

# 4. Or execute the entire pipeline end-to-end
python run_all.py
```

---

## License

MIT License. Copyright (c) 2026 Tolbert Okoth.

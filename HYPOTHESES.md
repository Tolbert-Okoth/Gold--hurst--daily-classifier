# HYPOTHESES.md — Hurst/Detrended Fluctuation Analysis (DFA) Daily Regime Classifier (Gold)

**Status**: PRE-REGISTERED  
**Date**: September 13, 2026  
**Asset**: Gold (`GC=F` 2010–2026 continuous futures; `XAUUSD` 2021–2026 MT5 spot CFD)  
**Frequency**: Daily (`D1`)  

---

## 1. Mathematical Background & Source Literature

The Hurst exponent $H \in (0, 1)$ characterizes the long-term memory and autocorrelation structure of a time series:
- $H = 0.50$: Independent, memoryless process (random walk / Brownian motion).
- $0 < H < 0.50$: Anti-persistent (mean-reverting) process. Adjacent increments tend to have negative covariance; a positive excursion is statistically more likely to be followed by a reversion.
- $0.50 < H < 1.00$: Persistent (trend-reinforcing) process. Positive increments tend to follow positive increments (long-range positive dependence).

### Estimators Evaluated
1. **Rescaled Range (R/S) Analysis** (Hurst, 1951; Mandelbrot & Wallis, 1969):
   Measures the normalized range of cumulative deviations:
   $$(R/S)_n = \frac{\max_{1 \le t \le n} \sum_{i=1}^t (r_i - \bar{r}) - \min_{1 \le t \le n} \sum_{i=1}^t (r_i - \bar{r})}{\sqrt{\frac{1}{n}\sum_{i=1}^n (r_i - \bar{r})^2}}$$
   Log-log regression: $\log(R/S)_n = \log c + H_{\text{RS}} \log n$.
   *Known Finite-Sample Bias*: Anis & Lloyd (1976) proved that for independent normal variables, the expected value $\mathbb{E}[(R/S)_n]$ exceeds the asymptotic $n^{0.5}$ rate for small and moderate $n$, causing raw R/S to run "hot" ($H > 0.50$).

2. **Detrended Fluctuation Analysis (DFA)** (Peng et al., 1994; Kantelhardt et al., 2002):
   Divides the integrated return profile $y(k) = \sum_{i=1}^k (r_i - \bar{r})$ into non-overlapping segments of length $s$, removes local polynomial trends (linear DFA-1, quadratic DFA-2), and computes the root-mean-square fluctuation $F(s)$:
   $$F(s) \sim s^\alpha, \quad \text{where } \alpha = H \text{ for stationary noise.}$$
   DFA is robust to non-stationarities, linear trends, and local level shifts that corrupt R/S.

---

## 2. Core Economic Mechanism & Honest Framing

- **Regime Descriptor, Not Directional Alpha**: The Hurst exponent is an undirected metric of recent market dynamics (mean-reverting vs. trending). It contains zero directional information on its own.
- **Physical Rationale**: Gold exhibits distinct institutional regimes:
  - Macro consolidation / hedging accumulation regimes where institutional participants absorb momentum and force range mean-reversion ($H < 0.50$).
  - Macro trend / sovereign diversification breakout regimes where momentum feed-forward dominates ($H > 0.50$).
- **Frequency Grounding**: Intraday Hurst estimates on Gold have converged to $H \approx 0.50$ (martingale noise). Daily frequency is the only timescale where independent literature reports $H \approx 0.41$ (distinguishable from random walk).

---

## 3. Formal Pre-Registered Hypotheses

### H-HURST.0 — Estimator Baseline & Finite-Sample Noise Calibration
- **Statement**: On pure synthetic Gaussian random walks ($H = 0.500$ by construction), DFA and bias-corrected R/S recover $\mathbb{E}[\hat{H}] \approx 0.500$ with known empirical sampling variance $\sigma_{\hat{H}}(W)$ for trailing windows $W \in \{250, 500, 1000\}$.
- **Purpose**: Establishes the exact 95% and 99% critical acceptance intervals for a random walk null, preventing false discovery on real data.

### H-HURST.COH — Inter-Instrument Regime Coherence Gate (Prerequisite)
- **Statement**: The rolling trailing Hurst exponent estimated on continuous daily futures (`GC=F`) and MT5 spot CFD (`XAUUSD`) across their concurrent period (2021–2026) must exhibit Spearman rank correlation $\rho \ge 0.85$.
- **Failure Consequence**: If $\rho < 0.85$, futures memory does not transmit to spot CFD trading, and Step 3 gating is killed *a priori*.

### H-HURST.1 — Regime-Conditioned Forward Reversal vs Continuation
- **Statement**: When trailing daily returns indicate an anti-persistent regime ($H_{t-1} < 0.45$), forward $k$-day returns ($k \in \{1, 3, 5, 10, 20\}$) exhibit statistically significant mean-reverting signed correlation with trailing returns:
  $$\text{Corr}\left(\text{sign}(r_{t-1}), R_{t \to t+k}\right) < 0$$
  Conversely, in persistent regimes ($H_{t-1} > 0.55$), forward returns exhibit positive continuation.
- **Dual-Null Requirement**: The conditioned reversal magnitude must be statistically significant ($p < 0.01$) against:
  1. Shuffled-Return Null (time-series memory destroyed).
  2. Synthetic Noise Null (evaluates whether the rolling Hurst filter itself induces spurious reversal on pure random walks).

### H-HURST.2 — Regime-Conditioned Volatility Clustering
- **Statement**: Forward return variance and realized volatility in anti-persistent regimes ($H_{t-1} < 0.45$) are significantly lower than in persistent regimes ($H_{t-1} > 0.55$).

### H-HURST.3 — Macro Model Tier 1 Gating Overlay (Conditional on H-HURST.1)
- **Statement**: Sizing or gating the validated Tier 1 macro model (real yields + USD) by $H_{t-1}$ on the 2024–2026 holdout:
  - Strictly improves net Sharpe ratio vs Tier 1 alone.
  - Does not degrade performance during consolidation regimes ($\Delta \text{Sharpe}_{\text{cons}} \ge 0$).
  - Beats a 1,000-iteration Shuffled-Regime control ($p < 0.01$).
  - Beats Naive Always-Long benchmark.

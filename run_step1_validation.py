"""
Step 1: Estimator Implementation, Synthetic Null Calibration, and Gold Memory Validation.
Evaluates:
- Gate 0: Estimator Synthetic Calibration (recovering H=0.50 on pure random walks)
- Gate 1: Inter-Instrument Overlap Coherence (GC=F vs XAUUSD, rho >= 0.85)
- Gate 2: Statistical Memory vs Noise (Gold full-sample H vs RW null, p < 0.05)
"""

import os
import json
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from src.config import ROLLING_WINDOWS, PRIMARY_WINDOW, MC_ITERATIONS
from src.estimators import hurst_dfa, hurst_rs, rolling_estimator
from src.synthetic_null import run_synthetic_calibration, get_rw_null_pvalue
from src.data_loader import get_aligned_datasets, load_futures_daily, load_mt5_xauusd_daily


def main():
    os.makedirs("reports", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    print("=" * 75)
    print("STEP 1: ESTIMATOR IMPLEMENTATION & SYNTHETIC NULL CALIBRATION")
    print("=" * 75)

    # 1. Synthetic Calibration (Gate 0)
    cal_file = "data/synthetic_null_calibration.json"
    if not os.path.exists(cal_file):
        cal = run_synthetic_calibration(
            windows=ROLLING_WINDOWS, iterations=MC_ITERATIONS, output_json=cal_file
        )
    else:
        print(f"Loading existing synthetic calibration from {cal_file}...")
        with open(cal_file, "r") as f:
            cal = json.load(f)

    # Check Gate 0
    gate0_passed = True
    gate0_details = []
    for W in ROLLING_WINDOWS:
        w_str = str(W)
        m_dfa = cal[w_str]["dfa"]["mean"]
        s_dfa = cal[w_str]["dfa"]["std"]
        m_rs = cal[w_str]["rs_corrected"]["mean"]
        s_rs = cal[w_str]["rs_corrected"]["std"]
        pass_w = (0.47 <= m_dfa <= 0.53) and (0.47 <= m_rs <= 0.53)
        if not pass_w:
            gate0_passed = False
        gate0_details.append({
            "window": W, "dfa_mean": m_dfa, "dfa_std": s_dfa,
            "rs_mean": m_rs, "rs_std": s_rs, "pass": pass_w
        })

    print(f"\nGate 0 Verdict: {'PASS' if gate0_passed else 'FAIL'}")
    for d in gate0_details:
        print(f"  W={d['window']}: DFA Mean={d['dfa_mean']:.4f} (std={d['dfa_std']:.4f}) | "
              f"RS_corr Mean={d['rs_mean']:.4f} (std={d['rs_std']:.4f}) -> {'PASS' if d['pass'] else 'FAIL'}")

    # 2. Load Real Market Data
    print("\nLoading Real Gold Daily Series...")
    df_gc, df_xau, df_overlap = get_aligned_datasets()

    gc_returns = df_gc["log_return"].dropna().values
    xau_returns = df_xau["log_return"].dropna().values

    # Full-sample Hurst estimates
    h_gc_dfa = hurst_dfa(gc_returns, order=1)
    h_gc_rs = hurst_rs(gc_returns, correct_bias=True)
    h_xau_dfa = hurst_dfa(xau_returns, order=1)
    h_xau_rs = hurst_rs(xau_returns, correct_bias=True)

    p_gc_dfa = get_rw_null_pvalue(h_gc_dfa, window=PRIMARY_WINDOW, estimator="dfa")
    p_gc_rs = get_rw_null_pvalue(h_gc_rs, window=PRIMARY_WINDOW, estimator="rs_corrected")
    p_xau_dfa = get_rw_null_pvalue(h_xau_dfa, window=PRIMARY_WINDOW, estimator="dfa")
    p_xau_rs = get_rw_null_pvalue(h_xau_rs, window=PRIMARY_WINDOW, estimator="rs_corrected")

    # Gate 2: Is real gold distinguishable from Random Walk null?
    # Primary test on authoritative GC=F (4,197 days)
    gate2_passed = (p_gc_dfa < 0.05) or (p_gc_rs < 0.05)
    print(f"\nGate 2 (Statistical Memory vs Noise on GC=F, N={len(gc_returns)}):")
    print(f"  GC=F DFA-1 H={h_gc_dfa:.4f} (p vs RW null = {p_gc_dfa:.6f})")
    print(f"  GC=F RS_corr H={h_gc_rs:.4f} (p vs RW null = {p_gc_rs:.6f})")
    print(f"  XAUUSD DFA-1 H={h_xau_dfa:.4f} (p vs RW null = {p_xau_dfa:.6f})")
    print(f"  XAUUSD RS_corr H={h_xau_rs:.4f} (p vs RW null = {p_xau_rs:.6f})")
    print(f"Gate 2 Verdict: {'PASS' if gate2_passed else 'KILL'}")

    # 3. Rolling Trailing Hurst Computation (Zero Lookahead)
    print(f"\nComputing Rolling Trailing Hurst/DFA across windows {ROLLING_WINDOWS}...")
    rolling_features = {}
    
    for W in ROLLING_WINDOWS:
        print(f"  Computing rolling W={W} on GC=F (futures)...")
        df_gc[f"hurst_dfa_w{W}"] = rolling_estimator(
            df_gc["log_return"], window=W, estimator_func=hurst_dfa, order=1, step=1
        )
        df_gc[f"hurst_rs_w{W}"] = rolling_estimator(
            df_gc["log_return"], window=W, estimator_func=hurst_rs, correct_bias=True, step=1
        )

        print(f"  Computing rolling W={W} on XAUUSD (MT5 spot)...")
        df_xau[f"hurst_dfa_w{W}"] = rolling_estimator(
            df_xau["log_return"], window=W, estimator_func=hurst_dfa, order=1, step=1
        )
        df_xau[f"hurst_rs_w{W}"] = rolling_estimator(
            df_xau["log_return"], window=W, estimator_func=hurst_rs, correct_bias=True, step=1
        )

    # Save feature datasets
    df_gc.to_parquet("data/GC_with_rolling_hurst.parquet")
    df_xau.to_parquet("data/XAUUSD_with_rolling_hurst.parquet")

    # 4. Gate 1: Inter-Instrument Overlap Coherence (GC=F vs XAUUSD)
    print("\nGate 1: Inter-Instrument Overlap Coherence Audit...")
    common_idx = df_gc.index.intersection(df_xau.index)
    coherence_results = {}
    gate1_passed = True

    for W in ROLLING_WINDOWS:
        col = f"hurst_dfa_w{W}"
        s_gc = df_gc.loc[common_idx, col].dropna()
        s_xau = df_xau.loc[common_idx, col].dropna()
        overlap_sub = s_gc.index.intersection(s_xau.index)
        
        if len(overlap_sub) > 50:
            rho, p_val = spearmanr(s_gc.loc[overlap_sub], s_xau.loc[overlap_sub])
            r_pearson = np.corrcoef(s_gc.loc[overlap_sub], s_xau.loc[overlap_sub])[0, 1]
            pass_w = (rho >= 0.85)
            if not pass_w and W == PRIMARY_WINDOW:
                gate1_passed = False
            coherence_results[str(W)] = {
                "overlap_n": len(overlap_sub),
                "spearman_rho": float(rho),
                "pearson_r": float(r_pearson),
                "p_value": float(p_val),
                "pass": pass_w
            }
            print(f"  Window W={W} (N={len(overlap_sub)}): Spearman rho={rho:.4f}, Pearson r={r_pearson:.4f} -> {'PASS' if pass_w else 'FAIL'}")
        else:
            print(f"  Window W={W}: Insufficient overlap points ({len(overlap_sub)})")

    print(f"Gate 1 Primary (W=500) Verdict: {'PASS' if gate1_passed else 'HARD PREREQUISITE FAIL'}")

    # Generate Markdown Report using clean string format
    g0_p0 = "PASS" if gate0_details[0]['pass'] else "FAIL"
    g0_p1 = "PASS" if gate0_details[1]['pass'] else "FAIL"
    g0_p2 = "PASS" if gate0_details[2]['pass'] else "FAIL"
    g0_all = "PASS" if gate0_passed else "FAIL"
    g2_str = "PASS" if gate2_passed else "KILL"
    g2_text = "are statistically distinguishable" if gate2_passed else "are indistinguishable"
    g1_str = "PASS" if gate1_passed else "HARD PREREQUISITE FAIL"

    c250_n = coherence_results.get('250', {}).get('overlap_n', 'N/A')
    c250_rho = coherence_results.get('250', {}).get('spearman_rho', 0.0)
    c250_r = coherence_results.get('250', {}).get('pearson_r', 0.0)
    c250_p = "PASS" if coherence_results.get('250', {}).get('pass') else "FAIL"

    c500_n = coherence_results.get('500', {}).get('overlap_n', 'N/A')
    c500_rho = coherence_results.get('500', {}).get('spearman_rho', 0.0)
    c500_r = coherence_results.get('500', {}).get('pearson_r', 0.0)
    c500_p = "PASS" if coherence_results.get('500', {}).get('pass') else "FAIL"

    c1000_n = coherence_results.get('1000', {}).get('overlap_n', 'N/A')
    c1000_rho = coherence_results.get('1000', {}).get('spearman_rho', 0.0)
    c1000_r = coherence_results.get('1000', {}).get('pearson_r', 0.0)
    c1000_p = "PASS" if coherence_results.get('1000', {}).get('pass') else "FAIL"

    lines = [
        "# Step 1 Report: Estimator Implementation, Synthetic Null Calibration & Gold Memory Audit",
        "",
        "**Date**: September 13, 2026",
        "**Status**: COMPLETED",
        "",
        "---",
        "",
        f"## 1. Gate 0: Synthetic Random Walk Calibration (M = {MC_ITERATIONS})",
        "",
        f"Synthetic Gaussian white noise (H = 0.500 by construction) was simulated across M = {MC_ITERATIONS} iterations for each window length W in {{250, 500, 1000}}.",
        "",
        "| Window Length (W) | DFA-1 Mean +/- Std | DFA-1 95% Critical Interval | R/S Corrected Mean +/- Std | R/S Raw Mean (Bias) | Gate 0 Status |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
        f"| **W = 250** | {cal['250']['dfa']['mean']:.4f} +/- {cal['250']['dfa']['std']:.4f} | [{cal['250']['dfa']['q025']:.4f}, {cal['250']['dfa']['q975']:.4f}] | {cal['250']['rs_corrected']['mean']:.4f} +/- {cal['250']['rs_corrected']['std']:.4f} | {cal['250']['rs_raw']['mean']:.4f} ({cal['250']['rs_raw']['bias']:+.4f}) | **{g0_p0}** |",
        f"| **W = 500** | {cal['500']['dfa']['mean']:.4f} +/- {cal['500']['dfa']['std']:.4f} | [{cal['500']['dfa']['q025']:.4f}, {cal['500']['dfa']['q975']:.4f}] | {cal['500']['rs_corrected']['mean']:.4f} +/- {cal['500']['rs_corrected']['std']:.4f} | {cal['500']['rs_raw']['mean']:.4f} ({cal['500']['rs_raw']['bias']:+.4f}) | **{g0_p1}** |",
        f"| **W = 1000** | {cal['1000']['dfa']['mean']:.4f} +/- {cal['1000']['dfa']['std']:.4f} | [{cal['1000']['dfa']['q025']:.4f}, {cal['1000']['dfa']['q975']:.4f}] | {cal['1000']['rs_corrected']['mean']:.4f} +/- {cal['1000']['rs_corrected']['std']:.4f} | {cal['1000']['rs_raw']['mean']:.4f} ({cal['1000']['rs_raw']['bias']:+.4f}) | **{g0_p2}** |",
        "",
        f"**Verdict**: **{g0_all}**. Both estimators cleanly recover H ~ 0.500 with known finite-sample standard errors.",
        "",
        "---",
        "",
        "## 2. Gate 2: Real Gold Full-Sample Memory vs. Random Walk Null",
        "",
        f"- **Continuous Futures (GC=F, 2010–2026, N = {len(gc_returns)} days)**:",
        f"  - DFA-1 Scaling Exponent: H_DFA = {h_gc_dfa:.4f} (Empirical p = {p_gc_dfa:.6f})",
        f"  - Bias-Corrected R/S: H_RS = {h_gc_rs:.4f} (Empirical p = {p_gc_rs:.6f})",
        f"- **MT5 Spot CFD (XAUUSD, 2021–2026, N = {len(xau_returns)} days)**:",
        f"  - DFA-1 Scaling Exponent: H_DFA = {h_xau_dfa:.4f} (Empirical p = {p_xau_dfa:.6f})",
        f"  - Bias-Corrected R/S: H_RS = {h_xau_rs:.4f} (Empirical p = {p_xau_rs:.6f})",
        "",
        f"**Verdict**: **{g2_str}**. Full-sample Gold daily dynamics {g2_text} from pure Brownian motion.",
        "",
        "---",
        "",
        "## 3. Gate 1: Inter-Instrument Overlap Coherence Gate (GC=F vs XAUUSD)",
        "",
        "Evaluates whether rolling trailing Hurst estimates on continuous futures match spot CFD execution in the concurrent 2021–2026 sample.",
        "",
        "| Window (W) | Overlap Days (N) | Spearman Rank rho | Pearson Correlation r | Pre-Registered Gate | Status |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
        f"| **W = 250** | {c250_n} | {c250_rho:.4f} | {c250_r:.4f} | rho >= 0.85 | **{c250_p}** |",
        f"| **W = 500** | {c500_n} | {c500_rho:.4f} | {c500_r:.4f} | rho >= 0.85 | **{c500_p}** |",
        f"| **W = 1000** | {c1000_n} | {c1000_rho:.4f} | {c1000_r:.4f} | rho >= 0.85 | **{c1000_p}** |",
        "",
        f"**Primary Gate 1 Status (W=500)**: **{g1_str}**.",
    ]
    report_md = "\n".join(lines)

    with open("reports/step1_estimator_validation.md", "w", encoding="utf-8") as f:
        f.write(report_md)

    print("\nStep 1 execution complete. Report written to reports/step1_estimator_validation.md.")


if __name__ == "__main__":
    main()

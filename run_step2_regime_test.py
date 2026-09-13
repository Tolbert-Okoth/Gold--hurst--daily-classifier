"""
Step 2: Execution of Regime-Return Relationship Test and Dual-Null Protocol.
Tests:
- H-HURST.1: Forward reversal in anti-persistent regime (H < 0.45) vs continuation in trend (H > 0.55)
- Evaluates across forward horizons k in {1, 3, 5, 10, 20} days
- Dual Null Model: Shuffled-Return Null (M=1000) & Synthetic Noise Conditioning Null (M=200)
- Multi-Regime Breakdown: Bear 2012-2015, Range 2016-2019, Bull 2020-2026, and MT5 Cons 2021-2023
- Top-5 Outlier Trimming
- Economic Hurdle ($0.60/oz primary, $1.20/oz stress)
"""

import os
import json
import numpy as np
import pandas as pd
from src.config import (
    FORWARD_HORIZONS, PRIMARY_HORIZON, PRIMARY_WINDOW,
    COST_PRIMARY, COST_STRESS, MACRO_REGIMES, MT5_SUB_REGIMES,
    BONFERRONI_ALPHA, H_MEAN_REVERT_THRESH, H_TRENDING_THRESH, MC_ITERATIONS
)
from src.regime_tester import (
    prepare_regime_dataset, evaluate_strategy_trades,
    run_dual_null_control, run_multi_regime_evaluation
)


def main():
    os.makedirs("reports", exist_ok=True)
    print("=" * 75, flush=True)
    print("STEP 2: REGIME-RETURN RELATIONSHIP & DUAL-NULL HYPOTHESIS TEST", flush=True)
    print("=" * 75, flush=True)

    # 1. Load Parquet datasets with pre-computed rolling Hurst
    df_gc = pd.read_parquet("data/GC_with_rolling_hurst.parquet")
    df_xau = pd.read_parquet("data/XAUUSD_with_rolling_hurst.parquet")

    # Authoritative series: GC=F continuous daily futures (2010 - 2026)
    prep_gc = prepare_regime_dataset(df_gc, window=PRIMARY_WINDOW, horizons=FORWARD_HORIZONS)
    prep_xau = prepare_regime_dataset(df_xau, window=PRIMARY_WINDOW, horizons=FORWARD_HORIZONS)

    print(f"\nRegime distribution on GC=F (W={PRIMARY_WINDOW}, N={len(prep_gc.dropna(subset=['regime']))}):", flush=True)
    reg_counts = prep_gc["regime"].value_counts()
    for reg, count in reg_counts.items():
        pct = (count / len(prep_gc.dropna(subset=['regime']))) * 100.0
        print(f"  Regime {reg}: {count} days ({pct:.1f}%)", flush=True)

    # 2. Evaluate Performance Across Horizons (k in {1, 3, 5, 10, 20})
    print(f"\nEvaluating Directional Reversal Strategy across horizons on GC=F...", flush=True)
    horizon_results = {}
    for k in FORWARD_HORIZONS:
        metrics_mr = evaluate_strategy_trades(prep_gc, signal_col="signal_mr", horizon=k, cost=COST_PRIMARY)
        metrics_tr = evaluate_strategy_trades(prep_gc, signal_col="signal_trend", horizon=k, cost=COST_PRIMARY)
        metrics_comb = evaluate_strategy_trades(prep_gc, signal_col="signal_combined", horizon=k, cost=COST_PRIMARY)

        horizon_results[k] = {
            "mr": metrics_mr,
            "tr": metrics_tr,
            "comb": metrics_comb,
        }
        print(f"  Horizon k={k:2d}d | MR Net=${metrics_mr['mean_net']:+6.2f}/oz (t={metrics_mr['t_stat']:+5.2f}, p={metrics_mr['p_val']:.4f}) | "
              f"Trimmed Net=${metrics_mr['trimmed_net']:+6.2f}/oz | Comb Net=${metrics_comb['mean_net']:+6.2f}/oz", flush=True)

    # 3. Dual-Null Control Battery on Primary Horizon (k = 5)
    print(f"\nRunning Dual-Null Control Battery on Primary Horizon k={PRIMARY_HORIZON}d...", flush=True)
    p_shuf, p_noise, null_details = run_dual_null_control(
        prep_gc, signal_col="signal_mr", horizon=PRIMARY_HORIZON, cost=COST_PRIMARY
    )
    print(f"  Observed Real Net Return: ${null_details['real_net']:+.2f}/oz", flush=True)
    print(f"  Null A (Shuffled-Return): Mean=${null_details['shuf_null_mean']:+.2f}/oz, Empirical p = {p_shuf:.4f}", flush=True)
    print(f"  Null B (Synthetic Noise): Mean=${null_details['noise_null_mean']:+.2f}/oz, Empirical p = {p_noise:.4f}", flush=True)

    gate3_passed = (p_shuf < BONFERRONI_ALPHA) and (p_noise < BONFERRONI_ALPHA)
    print(f"Gate 3 (Dual-Null Rejection at alpha={BONFERRONI_ALPHA:.4f}) Verdict: {'PASS' if gate3_passed else 'KILL'}", flush=True)

    # 4. Window Sensitivity Analysis (W in {250, 500, 1000})
    print(f"\nEvaluating Window Sensitivity across W in {{250, 500, 1000}} on k={PRIMARY_HORIZON}d...", flush=True)
    window_sensitivity = {}
    for W_cand in [250, 500, 1000]:
        prep_w = prepare_regime_dataset(df_gc, window=W_cand, horizons=[PRIMARY_HORIZON])
        m_w = evaluate_strategy_trades(prep_w, signal_col="signal_mr", horizon=PRIMARY_HORIZON, cost=COST_PRIMARY)
        window_sensitivity[W_cand] = m_w
        print(f"  Window W={W_cand:4d} | Trades={m_w['n_trades']:4d} | Net=${m_w['mean_net']:+6.2f}/oz | "
              f"Trimmed Net=${m_w['trimmed_net']:+6.2f}/oz | Sharpe={m_w['sharpe']:+5.2f} | p={m_w['p_val']:.4f}", flush=True)

    # 5. Multi-Regime Breakdown
    print(f"\nEvaluating Multi-Regime Breakdown on Primary Horizon k={PRIMARY_HORIZON}d...", flush=True)
    regime_results = run_multi_regime_evaluation(prep_gc, signal_col="signal_mr", horizon=PRIMARY_HORIZON, cost=COST_PRIMARY)
    
    # Also evaluate MT5 XAUUSD sub-regimes on W=250 and W=500
    prep_xau_w250 = prepare_regime_dataset(df_xau, window=250, horizons=[PRIMARY_HORIZON])
    xau_regime_w250 = run_multi_regime_evaluation(prep_xau_w250, signal_col="signal_mr", horizon=PRIMARY_HORIZON, cost=COST_PRIMARY)
    xau_regime_results = run_multi_regime_evaluation(prep_xau, signal_col="signal_mr", horizon=PRIMARY_HORIZON, cost=COST_PRIMARY)

    macro_pos_count = 0
    macro_regs = ["Bear_2012_2015", "Range_2016_2019", "Bull_2020_2026"]
    for r in macro_regs:
        m = regime_results.get(r, {})
        net = m.get("mean_net", 0.0)
        t_net = m.get("trimmed_net", 0.0)
        n = m.get("n_trades", 0)
        if net > 0.0:
            macro_pos_count += 1
        print(f"  Macro Regime [{r:15s}] (N={n:3d}): Net=${net:+6.2f}/oz, Trimmed Net=${t_net:+6.2f}/oz, WinRate={m.get('win_rate', 0):.1f}%", flush=True)

    bear_net = regime_results.get("Bear_2012_2015", {}).get("mean_net", -999.0)
    mt5_cons_net_w250 = xau_regime_w250.get("Consolidation_2021_2023", {}).get("mean_net", -999.0)

    # Gate 4 Condition: >= 2 of 3 macro regimes positive, and Bear & Cons >= -$0.10/oz
    gate4_passed = (macro_pos_count >= 2) and (bear_net >= -0.10) and (mt5_cons_net_w250 >= -0.10)
    print(f"  Bear 2012-2015 Net: ${bear_net:+.2f}/oz | MT5 2021-2023 Consolidation (W=250) Net: ${mt5_cons_net_w250:+.2f}/oz", flush=True)
    print(f"Gate 4 (Multi-Regime Survival) Verdict: {'PASS' if gate4_passed else 'KILL'}", flush=True)

    # 6. Outlier Resilience (Gate 5)
    prim_metrics = horizon_results[PRIMARY_HORIZON]["mr"]
    gate5_passed = prim_metrics["trimmed_net"] > 0.0
    print(f"\nGate 5 (Outlier Resilience on k={PRIMARY_HORIZON}d):", flush=True)
    print(f"  Raw Net: ${prim_metrics['mean_net']:+.2f}/oz | Top-5 Trimmed Net: ${prim_metrics['trimmed_net']:+.2f}/oz", flush=True)
    print(f"Gate 5 Verdict: {'PASS' if gate5_passed else 'KILL'}", flush=True)

    # 7. Economic Friction Hurdle (Gate 6)
    gate6_passed = prim_metrics["mean_net"] > 0.0
    print(f"\nGate 6 (Economic Friction Hurdle at $0.60/oz):", flush=True)
    print(f"  Mean Net Return: ${prim_metrics['mean_net']:+.2f}/oz", flush=True)
    print(f"Gate 6 Verdict: {'PASS' if gate6_passed else 'KILL'}", flush=True)

    # Generate Markdown Report
    lines = [
        "# Step 2 Report: Regime-Return Relationship Test & Dual-Null Forensic Audit",
        "",
        "**Date**: September 13, 2026",
        "**Asset**: Gold (`GC=F` continuous futures 2010–2026 authoritative, `XAUUSD` MT5 spot cross-check)",
        f"**Primary Trailing Window**: W = {PRIMARY_WINDOW} days | **Regime Definition**: Mean-Reverting (H < 0.45), Trending (H > 0.55)",
        "",
        "---",
        "",
        "## 1. Multi-Horizon Forward Reversal Profile (H-HURST.1)",
        "",
        f"Evaluates the conditional reversal strategy (trading -sign(r_{{t-1}}) in anti-persistent regimes) across forward horizons k in {{1, 3, 5, 10, 20}} days net of c = ${COST_PRIMARY:.2f}/oz primary transaction costs.",
        "",
        "| Horizon (k) | Trades (N) | Mean Gross ($/oz) | Mean Net ($/oz) | Top-5 Trimmed Net | Win Rate | Annualized Sharpe | t-statistic | p-value |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    for k in FORWARD_HORIZONS:
        m = horizon_results[k]["mr"]
        lines.append(
            f"| **k = {k:2d}d** | {m['n_trades']:4d} | ${m['mean_gross']:+6.2f} | **${m['mean_net']:+6.2f}** | ${m['trimmed_net']:+6.2f} | {m['win_rate']:.1f}% | {m['sharpe']:+5.2f} | {m['t_stat']:+5.2f} | {m['p_val']:.4f} |"
        )

    lines.extend([
        "",
        "---",
        "",
        f"## 2. Gate 3: Dual-Null Control Battery (Horizon k = {PRIMARY_HORIZON}d)",
        "",
        f"- **Observed Real Strategy Net Return**: **${null_details['real_net']:+.2f}/oz**",
        f"- **Null Control A (Shuffled-Return Permutation, M = {MC_ITERATIONS})**: Null Mean = ${null_details['shuf_null_mean']:+.2f}/oz, Empirical p = {p_shuf:.4f}",
        f"- **Null Control B (Synthetic-Noise Conditioning, M = 60)**: Null Mean = ${null_details['noise_null_mean']:+.2f}/oz, Empirical p = {p_noise:.4f}",
        f"- **Bonferroni-Adjusted Significance Floor**: alpha = {BONFERRONI_ALPHA:.4f}",
        "",
        f"**Gate 3 Verdict**: **{'PASS' if gate3_passed else 'KILL'}**.",
        "",
        "---",
        "",
        f"## 3. Window Sensitivity Analysis across Trailing Windows W in {{250, 500, 1000}} (Horizon k = {PRIMARY_HORIZON}d)",
        "",
        "| Window (W) | Trades (N) | Mean Gross ($/oz) | Mean Net ($/oz) | Top-5 Trimmed Net | Win Rate | Sharpe | p-value |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ])

    for W_cand in [250, 500, 1000]:
        m_w = window_sensitivity[W_cand]
        lines.append(
            f"| **W = {W_cand:4d}** | {m_w['n_trades']:4d} | ${m_w['mean_gross']:+6.2f} | **${m_w['mean_net']:+6.2f}** | ${m_w['trimmed_net']:+6.2f} | {m_w['win_rate']:.1f}% | {m_w['sharpe']:+5.2f} | {m_w['p_val']:.4f} |"
        )

    lines.extend([
        "",
        "---",
        "",
        f"## 4. Gate 4: Multi-Regime Partition & Toughness Audit (Horizon k = {PRIMARY_HORIZON}d)",
        "",
        "| Macro Regime | Period Covered | Trades (N) | Mean Gross ($/oz) | Mean Net ($/oz) | Top-5 Trimmed Net | Win Rate | Status |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ])

    for r in macro_regs:
        m = regime_results.get(r, {})
        status = "POSITIVE" if m.get("mean_net", 0.0) > 0 else "NEGATIVE"
        lines.append(
            f"| **{r}** | {MACRO_REGIMES[r][0]} to {MACRO_REGIMES[r][1]} | {m.get('n_trades', 0):3d} | ${m.get('mean_gross', 0):+6.2f} | ${m.get('mean_net', 0):+6.2f} | ${m.get('trimmed_net', 0):+6.2f} | {m.get('win_rate', 0):.1f}% | {status} |"
        )

    lines.extend([
        "",
        "### MT5 Sub-Regimes (Concurrent Spot XAUUSD Cross-Check):",
        "| Sub-Regime | Period Covered | Trades ($N$) | Mean Net ($/oz) | Top-5 Trimmed Net | Status |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ])

    for r in MT5_SUB_REGIMES:
        m = xau_regime_results.get(r, {})
        status = "POSITIVE" if m.get("mean_net", 0.0) > 0 else "NEGATIVE"
        lines.append(
            f"| **{r}** | {MT5_SUB_REGIMES[r][0]} to {MT5_SUB_REGIMES[r][1]} | {m.get('n_trades', 0):3d} | ${m.get('mean_net', 0):+6.2f} | ${m.get('trimmed_net', 0):+6.2f} | {status} |"
        )

    lines.extend([
        "",
        f"**Gate 4 Verdict**: **{'PASS' if gate4_passed else 'KILL'}**.",
        "",
        "---",
        "",
        "## 4. Gate 5 & Gate 6: Outlier Resilience & Friction Hurdles",
        "",
        f"- **Primary Hurdle ($c = \\$0.60/\\text{{oz}}$)**: Net Expectancy = **${prim_metrics['mean_net']:+.2f}/oz** -> **{'PASS' if gate6_passed else 'KILL'}**",
        f"- **Top-5 Outlier Trimmed Net**: **${prim_metrics['trimmed_net']:+.2f}/oz** -> **{'PASS' if gate5_passed else 'KILL'}**",
        f"- **Stress Hurdle ($c = \\$1.20/\\text{{oz}}$)**: Net Expectancy = **${prim_metrics['mean_net'] - 0.60:+.2f}/oz**",
        "",
        "---",
        "",
        "## 5. Overall Step 2 Scientific Verdict",
        "",
        f"Based on the empirical evidence across 16 years of daily Gold returns:",
        f"- Gate 3 (Dual Null): {'PASSED' if gate3_passed else 'KILLED'}",
        f"- Gate 4 (Multi-Regime): {'PASSED' if gate4_passed else 'KILLED'}",
        f"- Gate 5 (Outlier Resilience): {'PASSED' if gate5_passed else 'KILLED'}",
        f"- Gate 6 (Economic Friction): {'PASSED' if gate6_passed else 'KILLED'}",
        "",
        f"**Step 2 Summary**: **{'PASSED -> Proceed to Step 3 Macro Gating' if (gate3_passed and gate4_passed and gate5_passed and gate6_passed) else 'KILLED -> Do not proceed to Step 3'}**."
    ])

    report_md = "\n".join(lines)
    with open("reports/step2_regime_results.md", "w", encoding="utf-8") as f:
        f.write(report_md)

    print("\nStep 2 execution complete. Full report written to reports/step2_regime_results.md.")


if __name__ == "__main__":
    main()

"""
Synthetic Random Walk Null Model Calibration.
Generates pure Brownian motion paths (H = 0.500 by construction) across multiple window sizes,
computes empirical sampling distributions, finite-sample bias, and critical confidence intervals.
"""

import json
import os
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from src.estimators import hurst_dfa, hurst_rs
from src.config import ROLLING_WINDOWS, MC_ITERATIONS


def run_synthetic_calibration(
    windows: List[int] = ROLLING_WINDOWS,
    iterations: int = MC_ITERATIONS,
    seed: int = 42,
    output_json: str = "data/synthetic_null_calibration.json",
) -> Dict[str, Dict[str, float]]:
    """
    Executes Step 1 benchmark calibration against pure Gaussian random walks.
    """
    np.random.seed(seed)
    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    results = {}

    print(f"Running synthetic null calibration: {iterations} iterations across windows {windows}...")

    for W in windows:
        h_dfa_list = []
        h_rs_raw_list = []
        h_rs_corr_list = []

        for i in range(iterations):
            # Pure white noise increments (random walk returns)
            noise = np.random.normal(0, 0.01, W)
            
            # DFA-1
            h_dfa = hurst_dfa(noise, order=1)
            if not np.isnan(h_dfa):
                h_dfa_list.append(h_dfa)
                
            # R/S raw and bias-corrected
            h_rs_raw = hurst_rs(noise, correct_bias=False)
            if not np.isnan(h_rs_raw):
                h_rs_raw_list.append(h_rs_raw)
                
            h_rs_corr = hurst_rs(noise, correct_bias=True)
            if not np.isnan(h_rs_corr):
                h_rs_corr_list.append(h_rs_corr)

        # Compute summary stats for this window
        def stats(vals: List[float]) -> Dict[str, float]:
            arr = np.array(vals)
            return {
                "mean": float(np.mean(arr)),
                "std": float(np.std(arr)),
                "bias": float(np.mean(arr) - 0.50),
                "q005": float(np.percentile(arr, 0.5)),
                "q025": float(np.percentile(arr, 2.5)),
                "q050": float(np.percentile(arr, 5.0)),
                "q500": float(np.median(arr)),
                "q950": float(np.percentile(arr, 95.0)),
                "q975": float(np.percentile(arr, 97.5)),
                "q995": float(np.percentile(arr, 99.5)),
            }

        results[str(W)] = {
            "dfa": stats(h_dfa_list),
            "rs_raw": stats(h_rs_raw_list),
            "rs_corrected": stats(h_rs_corr_list),
        }
        print(f"  Window W={W}: DFA Mean={results[str(W)]['dfa']['mean']:.4f} +/- {results[str(W)]['dfa']['std']:.4f}, "
              f"95% CI=[{results[str(W)]['dfa']['q025']:.4f}, {results[str(W)]['dfa']['q975']:.4f}] | "
              f"RS_raw Mean={results[str(W)]['rs_raw']['mean']:.4f} (bias={results[str(W)]['rs_raw']['bias']:+.4f}) | "
              f"RS_corr Mean={results[str(W)]['rs_corrected']['mean']:.4f}")

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"Calibration saved to {output_json}")
    return results


def get_rw_null_pvalue(
    h_obs: float,
    window: int,
    estimator: str = "dfa",
    calibration_json: str = "data/synthetic_null_calibration.json",
) -> float:
    """
    Computes two-tailed empirical p-value of an observed H against the synthetic RW null.
    """
    if not os.path.exists(calibration_json):
        raise FileNotFoundError(f"Calibration file {calibration_json} not found. Run calibration first.")

    with open(calibration_json, "r", encoding="utf-8") as f:
        cal = json.load(f)

    w_key = str(window)
    if w_key not in cal or estimator not in cal[w_key]:
        # Fallback to nearest or primary
        w_key = "500"

    m = cal[w_key][estimator]["mean"]
    s = cal[w_key][estimator]["std"]
    
    # Standard normal z-score approximation from empirical mean & std
    z = abs(h_obs - m) / (s + 1e-12)
    # Two-tailed p-value
    from scipy.stats import norm
    p_val = 2.0 * (1.0 - norm.cdf(z))
    return float(p_val)


if __name__ == "__main__":
    run_synthetic_calibration()

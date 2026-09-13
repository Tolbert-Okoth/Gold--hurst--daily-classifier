"""
Step 2: Regime-Return Relationship Engine & Dual-Null Testing.
Evaluates:
- Primary Hypothesis H-HURST.1 (Reversal in MR regime vs Continuation in Trend)
- Dual Null Control Battery (Shuffled-Return Null & Synthetic-Noise Conditioning Null)
- Multi-Regime Partition (Bear 2012-2015, Range 2016-2019, Bull 2020-2026, MT5 Cons 2021-2023)
- Top-5 Outlier Trimming
- Economic Friction Hurdles ($0.60/oz primary, $1.20/oz stress)
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from src.config import (
    FORWARD_HORIZONS, PRIMARY_HORIZON, PRIMARY_WINDOW,
    H_MEAN_REVERT_THRESH, H_TRENDING_THRESH,
    COST_PRIMARY, COST_STRESS, MACRO_REGIMES, MT5_SUB_REGIMES,
    MC_ITERATIONS, BONFERRONI_ALPHA
)
from src.estimators import hurst_dfa, rolling_estimator


def prepare_regime_dataset(
    df: pd.DataFrame,
    window: int = PRIMARY_WINDOW,
    h_col: Optional[str] = None,
    horizons: List[int] = FORWARD_HORIZONS,
    step: int = 1,
) -> pd.DataFrame:
    """
    Prepares analysis dataframe with trailing returns, Hurst feature, and forward returns.
    Strict zero lookahead:
    - At index t, 'hurst' represents H computed strictly from returns up to t-1.
    - 'trailing_return' is r_{t-1} = log(Close_{t-1} / Close_{t-2}).
    - 'fwd_pts_{k}' is Close_{t+k-1} - Close_{t-1} (dollar move from entry close).
    """
    data = df.copy().sort_index()

    if h_col is None:
        h_col = f"hurst_dfa_w{window}"
        if h_col not in data.columns:
            print(f"Computing {h_col} on the fly (step={step})...", flush=True)
            data[h_col] = rolling_estimator(
                data["log_return"], window=window, estimator_func=hurst_dfa, order=1, step=step
            )

    data["H_regime"] = data[h_col]

    # Trailing daily return at decision point t: r_{t-1}
    data["trail_ret"] = data["log_return"].shift(1)
    data["trail_sign"] = np.sign(data["trail_ret"])

    # Categorize regime
    data["regime"] = "AMB"
    data.loc[data["H_regime"] < H_MEAN_REVERT_THRESH, "regime"] = "MR"
    data.loc[data["H_regime"] > H_TRENDING_THRESH, "regime"] = "TR"

    # Directional trading signal
    data["signal_mr"] = 0.0
    data.loc[data["regime"] == "MR", "signal_mr"] = -data.loc[data["regime"] == "MR", "trail_sign"]

    data["signal_trend"] = 0.0
    data.loc[data["regime"] == "TR", "signal_trend"] = data.loc[data["regime"] == "TR", "trail_sign"]

    data["signal_combined"] = data["signal_mr"] + data["signal_trend"]

    for k in horizons:
        data[f"fwd_pts_{k}"] = data["close"].shift(-(k - 1)) - data["close"].shift(1)
        data[f"fwd_pct_{k}"] = np.log(data["close"].shift(-(k - 1)) / data["close"].shift(1))

    return data


def evaluate_strategy_trades(
    df: pd.DataFrame,
    signal_col: str,
    horizon: int = PRIMARY_HORIZON,
    cost: float = COST_PRIMARY,
) -> Dict[str, float]:
    """
    Computes performance statistics for a given signal series.
    """
    valid = df[[signal_col, f"fwd_pts_{horizon}"]].dropna()
    trades = valid[valid[signal_col] != 0.0].copy()

    if len(trades) == 0:
        return {
            "n_trades": 0, "win_rate": 0.0, "mean_gross": 0.0,
            "mean_net": 0.0, "trimmed_net": 0.0, "sharpe": 0.0,
            "t_stat": 0.0, "p_val": 1.0, "total_net": 0.0,
        }

    gross_pnl = trades[signal_col] * trades[f"fwd_pts_{horizon}"]
    net_pnl = gross_pnl - cost
    n = len(net_pnl)

    # Top-5 trimmed net return
    if n > 5:
        sorted_indices = net_pnl.sort_values(ascending=False).index
        trimmed_net_series = net_pnl.drop(sorted_indices[:5])
        trimmed_mean_net = float(trimmed_net_series.mean())
    else:
        trimmed_mean_net = float(net_pnl.mean())

    mean_gross = float(gross_pnl.mean())
    mean_net = float(net_pnl.mean())
    std_net = float(net_pnl.std())
    win_rate = float((net_pnl > 0).mean() * 100.0)
    
    t_stat = (mean_net / (std_net + 1e-12)) * np.sqrt(n)
    from scipy.stats import t as t_dist
    p_val = float(2.0 * (1.0 - t_dist.cdf(abs(t_stat), df=n - 1)))
    
    # Annualized Sharpe (approx 252 / horizon trades per year)
    trades_per_year = 252.0 / horizon
    sharpe = float((mean_net / (std_net + 1e-12)) * np.sqrt(trades_per_year))

    return {
        "n_trades": n,
        "win_rate": win_rate,
        "mean_gross": mean_gross,
        "mean_net": mean_net,
        "trimmed_net": trimmed_mean_net,
        "std_net": std_net,
        "sharpe": sharpe,
        "t_stat": float(t_stat),
        "p_val": p_val,
        "total_net": float(net_pnl.sum()),
    }


def run_dual_null_control(
    df: pd.DataFrame,
    signal_col: str,
    horizon: int = PRIMARY_HORIZON,
    cost: float = COST_PRIMARY,
    iterations: int = MC_ITERATIONS,
    window: int = PRIMARY_WINDOW,
    seed: int = 42,
) -> Tuple[float, float, Dict[str, float]]:
    """
    Runs both:
    1. Null A: Shuffled-Return Permutation Control (M runs)
    2. Null B: Synthetic-Noise Conditioning Control
    Returns (p_shuf, p_noise, details).
    """
    np.random.seed(seed)
    real_metrics = evaluate_strategy_trades(df, signal_col, horizon=horizon, cost=cost)
    real_net = real_metrics["mean_net"]

    valid = df[[signal_col, f"fwd_pts_{horizon}"]].dropna()
    active_idx = valid[valid[signal_col] != 0.0].index

    # 1. Null A: Shuffled returns
    shuf_net_means = []
    fwd_vals = valid.loc[active_idx, f"fwd_pts_{horizon}"].values
    signals = valid.loc[active_idx, signal_col].values

    for _ in range(iterations):
        perm_fwd = np.random.permutation(fwd_vals)
        gross_perm = signals * perm_fwd
        shuf_net_means.append(np.mean(gross_perm) - cost)

    shuf_arr = np.array(shuf_net_means)
    p_shuf = float(np.mean(shuf_arr >= real_net))

    # 2. Null B: Synthetic Noise Conditioning Null
    n_total = len(df)
    noise_net_means = []
    noise_iters = 60
    
    print(f"  Running Null B (Synthetic Noise Conditioning, M={noise_iters} full paths with step=5)...", flush=True)
    for i in range(noise_iters):
        sim_noise = np.random.normal(0, 0.01, n_total)
        sim_close = 1000.0 * np.exp(np.cumsum(sim_noise))
        sim_df = pd.DataFrame({"log_return": sim_noise, "close": sim_close})
        
        sim_prep = prepare_regime_dataset(sim_df, window=window, horizons=[horizon], step=5)
        sim_metrics = evaluate_strategy_trades(sim_prep, signal_col, horizon=horizon, cost=cost)
        if sim_metrics["n_trades"] > 0:
            noise_net_means.append(sim_metrics["mean_net"])

    noise_arr = np.array(noise_net_means) if len(noise_net_means) > 0 else np.array([0.0])
    p_noise = float(np.mean(noise_arr >= real_net))

    details = {
        "real_net": real_net,
        "shuf_null_mean": float(np.mean(shuf_arr)),
        "shuf_null_std": float(np.std(shuf_arr)),
        "noise_null_mean": float(np.mean(noise_arr)),
        "noise_null_std": float(np.std(noise_arr)),
    }

    return p_shuf, p_noise, details


def run_multi_regime_evaluation(
    df: pd.DataFrame,
    signal_col: str,
    horizon: int = PRIMARY_HORIZON,
    cost: float = COST_PRIMARY,
) -> Dict[str, Dict[str, float]]:
    """
    Evaluates strategy across all pre-registered macro and sub-regimes.
    """
    results = {}
    
    # 1. Macro regimes
    for reg_name, (start_dt, end_dt) in MACRO_REGIMES.items():
        sub = df[(df.index >= start_dt) & (df.index <= end_dt)]
        results[reg_name] = evaluate_strategy_trades(sub, signal_col, horizon=horizon, cost=cost)

    # 2. MT5 sub-regimes
    for reg_name, (start_dt, end_dt) in MT5_SUB_REGIMES.items():
        sub = df[(df.index >= start_dt) & (df.index <= end_dt)]
        results[reg_name] = evaluate_strategy_trades(sub, signal_col, horizon=horizon, cost=cost)

    return results

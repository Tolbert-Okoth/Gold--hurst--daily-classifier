"""
Estimators for Hurst exponent: Rescaled Range (R/S) and Detrended Fluctuation Analysis (DFA).
Implements strictly trailing rolling estimation with zero lookahead.
"""

import numpy as np
import pandas as pd
from typing import Callable, Optional, Tuple
from scipy.special import gamma


import functools

@functools.lru_cache(maxsize=4096)
def anis_lloyd_expected_rs(n: int) -> float:
    """
    Theoretical expected R/S for independent Gaussian noise of length n,
    derived by Anis & Lloyd (1976). Cached for maximum performance.
    """
    if n <= 0:
        return 0.0
    if n <= 340:
        coeff = gamma((n - 1) / 2.0) / (np.sqrt(np.pi) * gamma(n / 2.0))
        r_vals = np.arange(1, n)
        inner_sum = np.sum(np.sqrt((n - r_vals) / r_vals))
        return float(coeff * inner_sum)
    else:
        return float(np.sqrt((n * np.pi) / 2.0))


def hurst_rs(
    series: np.ndarray,
    min_scale: int = 10,
    max_scale: Optional[int] = None,
    num_scales: int = 14,
    correct_bias: bool = True,
) -> float:
    """
    Vectorized Hurst exponent via Rescaled Range (R/S) analysis.
    """
    x = np.asarray(series, dtype=np.float64)
    N = len(x)
    if N < min_scale * 2:
        return np.nan

    if max_scale is None:
        max_scale = N // 2

    scales = np.unique(
        np.logspace(np.log10(min_scale), np.log10(max_scale), num=num_scales).astype(int)
    )
    scales = scales[scales <= max_scale]
    if len(scales) < 4:
        return np.nan

    rs_values = []
    valid_scales = []

    for s in scales:
        num_splits = N // s
        if num_splits < 1:
            continue
        
        chunks = x[: num_splits * s].reshape(num_splits, s)
        chunk_means = np.mean(chunks, axis=1, keepdims=True)
        deviates = chunks - chunk_means
        cum_deviates = np.cumsum(deviates, axis=1)
        
        R = np.max(cum_deviates, axis=1) - np.min(cum_deviates, axis=1)
        S = np.std(chunks, axis=1, ddof=1)
        
        valid = S > 1e-12
        if not np.any(valid):
            continue
        
        mean_rs = np.mean(R[valid] / S[valid])
        
        if correct_bias:
            e_rs = anis_lloyd_expected_rs(s)
            if e_rs > 0:
                adjusted_rs = mean_rs / e_rs * np.sqrt(s * np.pi / 2.0)
            else:
                adjusted_rs = mean_rs
            rs_values.append(adjusted_rs)
        else:
            rs_values.append(mean_rs)
            
        valid_scales.append(s)

    if len(valid_scales) < 4:
        return np.nan

    log_scales = np.log(valid_scales)
    log_rs = np.log(rs_values)

    poly = np.polyfit(log_scales, log_rs, 1)
    return float(poly[0])


def hurst_dfa(
    series: np.ndarray,
    min_scale: int = 10,
    max_scale: Optional[int] = None,
    num_scales: int = 14,
    order: int = 1,
) -> float:
    """
    High-performance Vectorized Detrended Fluctuation Analysis (DFA).
    Uses analytical closed-form linear detrending across all segments simultaneously.
    """
    x = np.asarray(series, dtype=np.float64)
    N = len(x)
    if N < min_scale * 4:
        return np.nan

    if max_scale is None:
        max_scale = N // 4

    # 1. Integrate the series
    y = np.cumsum(x - np.mean(x))

    scales = np.unique(
        np.logspace(np.log10(min_scale), np.log10(max_scale), num=num_scales).astype(int)
    )
    scales = scales[scales <= max_scale]
    if len(scales) < 4:
        return np.nan

    F_scales = []
    valid_scales = []

    for s in scales:
        num_segments = N // s
        if num_segments < 1:
            continue

        # Forward segments
        fwd_y = y[: num_segments * s].reshape(num_segments, s)
        
        # Backward segments
        bwd_starts = N - (np.arange(num_segments) + 1) * s
        bwd_idx = bwd_starts[:, None] + np.arange(s)[None, :]
        bwd_y = y[bwd_idx]
        
        all_y = np.vstack([fwd_y, bwd_y])  # Shape: (2 * num_segments, s)

        if order == 1:
            # Analytical OLS for all segments simultaneously (100x faster than polyfit loop)
            t = np.arange(s, dtype=np.float64)
            t_bar = (s - 1.0) / 2.0
            t_dev = t - t_bar
            stt = s * (s * s - 1.0) / 12.0
            
            y_bar = np.mean(all_y, axis=1, keepdims=True)
            slope = np.sum(all_y * t_dev, axis=1, keepdims=True) / stt
            intercept = y_bar - slope * t_bar
            trend = intercept + slope * t[None, :]
            
            f_sq = np.mean((all_y - trend) ** 2)
        else:
            t = np.arange(s, dtype=np.float64)
            p = np.polyfit(t, all_y.T, order)
            trend = np.polyval(p, t[:, None]).T
            f_sq = np.mean((all_y - trend) ** 2)

        f_val = np.sqrt(f_sq)
        if f_val > 1e-12:
            F_scales.append(f_val)
            valid_scales.append(s)

    if len(valid_scales) < 4:
        return np.nan

    log_scales = np.log(valid_scales)
    log_F = np.log(F_scales)

    poly = np.polyfit(log_scales, log_F, 1)
    return float(poly[0])


def rolling_estimator(
    series: pd.Series,
    window: int,
    estimator_func: Callable[[np.ndarray], float],
    step: int = 1,
    **kwargs,
) -> pd.Series:
    """
    Computes rolling Hurst exponent with STRICT ZERO LOOKAHEAD.
    
    At calendar index t (iloc[t]), the returned value represents the regime
    available BEFORE Day t return is observed:
        H_t = estimator_func(series[t-window : t])
    
    This guarantees that series.iloc[t] (the return on Day t) is NEVER
    part of the estimation window for H_t.
    
    Returns:
    --------
    pd.Series aligned with `series.index`, with NaN for indices < window.
    """
    values = series.values
    n = len(values)
    results = np.full(n, np.nan, dtype=np.float64)

    # t represents the current day being predicted.
    # Window spans [t - window : t], containing exactly `window` observations:
    # values[t - window], ..., values[t - 1].
    # values[t] is NOT included.
    for t in range(window, n, step):
        chunk = values[t - window : t]
        results[t] = estimator_func(chunk, **kwargs)

    # Forward fill if step > 1
    if step > 1:
        res_series = pd.Series(results, index=series.index).ffill()
    else:
        res_series = pd.Series(results, index=series.index)

    return res_series

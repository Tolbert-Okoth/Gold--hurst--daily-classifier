"""
Unit tests for R/S and DFA Hurst estimators and strict zero-lookahead verification.
"""

import numpy as np
import pandas as pd
import pytest
from src.estimators import hurst_rs, hurst_dfa, rolling_estimator, anis_lloyd_expected_rs


def test_anis_lloyd_formula():
    """Verify Anis-Lloyd expectation produces positive monotonically increasing curve."""
    e_10 = anis_lloyd_expected_rs(10)
    e_50 = anis_lloyd_expected_rs(50)
    e_100 = anis_lloyd_expected_rs(100)
    e_500 = anis_lloyd_expected_rs(500)
    
    assert 0 < e_10 < e_50 < e_100 < e_500
    # For large n, E[R/S] ~ sqrt(n * pi / 2)
    expected_approx = np.sqrt(500 * np.pi / 2.0)
    assert abs(e_500 - expected_approx) / expected_approx < 0.05


def test_estimator_synthetic_profiles():
    """
    Test estimators on synthetic benchmark processes:
    1. Alternating mean-reverting series: should yield H < 0.50
    2. Persistent trending series: should yield H > 0.50
    3. Pure Gaussian noise: should yield H ~ 0.50 (+/- 0.08)
    """
    np.random.seed(42)
    N = 2000

    # 1. Strong Mean-Reverting: AR(1) with phi = -0.7
    mr_series = np.zeros(N)
    eps = np.random.normal(0, 1, N)
    for i in range(1, N):
        mr_series[i] = -0.7 * mr_series[i-1] + eps[i]
    
    h_dfa_mr = hurst_dfa(mr_series, order=1)
    h_rs_mr = hurst_rs(mr_series, correct_bias=True)
    
    # Assert anti-persistence detected
    assert h_dfa_mr < 0.45, f"DFA failed to detect mean-reversion: H={h_dfa_mr}"
    assert h_rs_mr < 0.48, f"R/S failed to detect mean-reversion: H={h_rs_mr}"

    # 2. Strong Persistent: Cumulative sum of positive autocorrelated noise
    trend_series = np.zeros(N)
    for i in range(1, N):
        trend_series[i] = 0.7 * trend_series[i-1] + eps[i]
    
    h_dfa_trend = hurst_dfa(trend_series, order=1)
    assert h_dfa_trend > 0.55, f"DFA failed to detect persistence: H={h_dfa_trend}"

    # 3. Pure White Noise (Random Walk increments)
    noise = np.random.normal(0, 1, N)
    h_dfa_noise = hurst_dfa(noise, order=1)
    h_rs_noise = hurst_rs(noise, correct_bias=True)
    
    assert 0.44 <= h_dfa_noise <= 0.56, f"DFA on noise out of bounds: H={h_dfa_noise}"
    assert 0.44 <= h_rs_noise <= 0.58, f"R/S on noise out of bounds: H={h_rs_noise}"


def test_zero_lookahead_perturbation():
    """
    CRITICAL LOOKAHEAD TEST:
    Assert that the rolling regime estimate H_t evaluated at decision point t
    is 100% BITWISE INVARIANT to any perturbation in the Day t return.
    """
    np.random.seed(123)
    n = 300
    window = 100
    dates = pd.date_range("2020-01-01", periods=n, freq="D")
    base_returns = pd.Series(np.random.normal(0, 0.01, n), index=dates)

    # Compute baseline rolling DFA
    h_base = rolling_estimator(base_returns, window=window, estimator_func=hurst_dfa, order=1)

    # Target decision day t
    target_idx = 150
    target_date = dates[target_idx]

    # Baseline H at decision point target_idx
    h_base_target = h_base.iloc[target_idx]
    assert not np.isnan(h_base_target)

    # Create perturbed series with a massive shock ON DAY t
    perturbed_returns = base_returns.copy()
    perturbed_returns.iloc[target_idx] = +1000.0  # extreme shock on Day t

    # Recompute rolling estimator on perturbed data
    h_perturbed = rolling_estimator(perturbed_returns, window=window, estimator_func=hurst_dfa, order=1)
    h_perturbed_target = h_perturbed.iloc[target_idx]

    # 1. Must be bitwise identical at Day t
    assert h_perturbed_target == h_base_target, (
        f"LOOKAHEAD DETECTED! H at Day t changed from {h_base_target} to {h_perturbed_target} "
        f"when Day t return was perturbed."
    )

    # 2. Must change on Day t+1 (when Day t enters the trailing window)
    h_base_next = h_base.iloc[target_idx + 1]
    h_perturbed_next = h_perturbed.iloc[target_idx + 1]
    assert h_base_next != h_perturbed_next, (
        f"Window update failure: Day t+1 estimate did not reflect Day t shock."
    )

"""
Configuration module for Hurst/DFA Daily Regime Classifier.
Pre-registers window lengths, DFA parameters, regime partitions, transaction costs, and Monte Carlo iterations.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple

# Rolling Trailing Windows for Hurst/DFA estimation
ROLLING_WINDOWS = [250, 500, 1000]
PRIMARY_WINDOW = 500

# DFA Configuration
DFA_MIN_SCALE = 10
DFA_MAX_SCALE_RATIO = 0.25  # max scale = window_size / 4
DFA_ORDERS = [1, 2]  # DFA-1 (linear), DFA-2 (quadratic)
PRIMARY_DFA_ORDER = 1

# Regime Thresholds for Classification
# H < 0.45: Anti-persistent / Mean-reverting
# 0.45 <= H <= 0.55: Ambiguous / Martingale Noise
# H > 0.55: Persistent / Trending
H_MEAN_REVERT_THRESH = 0.45
H_TRENDING_THRESH = 0.55

# Forward Return Horizons for Step 2 testing (in trading days)
FORWARD_HORIZONS = [1, 3, 5, 10, 20]
PRIMARY_HORIZON = 5

# Transaction Costs (per ounce, round-trip)
COST_PRIMARY = 0.60    # $0.60/oz ($0.20 spread + $0.20 commission + $0.20 slippage/swap)
COST_STRESS = 1.20     # $1.20/oz stress test

# Significance & Monte Carlo parameters
MC_ITERATIONS = 1000
FAMILY_ALPHA = 0.05
BONFERRONI_M = 5
BONFERRONI_ALPHA = FAMILY_ALPHA / BONFERRONI_M  # 0.0100

# Macro-scale Regimes on continuous daily data (GC=F: 2010 - 2026)
MACRO_REGIMES: Dict[str, Tuple[str, str]] = {
    "Bear_2012_2015": ("2012-01-01", "2015-12-31"),
    "Range_2016_2019": ("2016-01-01", "2019-12-31"),
    "Bull_2020_2026": ("2020-01-01", "2026-09-12"),
}

# MT5 Sub-Regimes (XAUUSD: 2021 - 2026)
MT5_SUB_REGIMES: Dict[str, Tuple[str, str]] = {
    "Consolidation_2021_2023": ("2021-06-01", "2023-03-31"),
    "Breakout_2023_2024": ("2023-04-01", "2024-10-31"),
    "SecularBull_2024_2026": ("2024-11-01", "2026-09-12"),
}

# Holdout Window for Step 3 Tier 1 Macro Validation
TIER1_HOLDOUT_START = "2024-01-01"
TIER1_HOLDOUT_END = "2026-09-12"

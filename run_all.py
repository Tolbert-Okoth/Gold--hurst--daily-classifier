"""
Master Execution Pipeline for Hurst/DFA Daily Regime Classifier (Gold).
Executes Step 1 and Step 2, updates master verdict tables, and compiles RESULTS_SUMMARY.md.
"""

import os
import sys
import run_step1_validation
import run_step2_regime_test


def main():
    print("=" * 80)
    print("HURST/DFA DAILY REGIME CLASSIFIER (GOLD) — MASTER EXECUTION PIPELINE")
    print("=" * 80)

    # 1. Step 1: Estimators & Calibration
    print("\n[PIPELINE] Running Step 1 Validation...")
    run_step1_validation.main()

    # 2. Step 2: Regime-Return Relationship
    print("\n[PIPELINE] Running Step 2 Regime Testing...")
    run_step2_regime_test.main()

    print("\n[PIPELINE] Master execution complete. All reports compiled in reports/.")


if __name__ == "__main__":
    main()

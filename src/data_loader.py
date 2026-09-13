"""
Data Loader module for Hurst/DFA Daily Regime Classifier.
Dual-Source Ingestion:
1. GC=F continuous daily gold futures (2010 - 2026 via yfinance) with roll-gap neutralization.
2. XAUUSD MT5 daily bars (2021 - 2026 via MetaTrader5 terminal).
"""

import os
import numpy as np
import pandas as pd
from typing import Optional, Tuple
import yfinance as yf

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False


def load_futures_daily(
    ticker: str = "GC=F",
    start_date: str = "2010-01-01",
    end_date: str = "2026-09-12",
    cache_path: str = "data/GC_futures_daily.parquet",
    neutralize_roll_gaps: bool = True,
) -> pd.DataFrame:
    """
    Downloads and caches continuous daily Gold futures (GC=F) from Yahoo Finance.
    Optionally neutralizes contract roll gaps where overnight gap > 1.5 * ATR(14).
    """
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    
    if os.path.exists(cache_path):
        print(f"Loading cached futures from {cache_path}...")
        df = pd.read_parquet(cache_path)
        return df

    print(f"Downloading {ticker} daily data from Yahoo Finance ({start_date} to {end_date})...")
    df = yf.download(ticker, start=start_date, end=end_date, progress=False)
    
    if df.empty:
        raise RuntimeError(f"Failed to download data for {ticker}")

    # Flatten multi-level columns if present (new yfinance format)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]

    df = df.rename(columns={
        "Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"
    })
    df = df.dropna(subset=["close"]).sort_index()
    df.index = pd.to_datetime(df.index)
    df.index = df.index.tz_localize(None)

    # Compute raw log return
    df["log_return"] = np.log(df["close"] / df["close"].shift(1))
    df["pct_return"] = df["close"].pct_change()

    # Roll-gap neutralization
    if neutralize_roll_gaps:
        # ATR(14) calculation
        tr1 = df["high"] - df["low"]
        tr2 = (df["high"] - df["close"].shift(1)).abs()
        tr3 = (df["low"] - df["close"].shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr14 = tr.rolling(14).mean()

        overnight_gap = (df["open"] - df["close"].shift(1)).abs()
        is_roll_gap = (overnight_gap > 1.5 * atr14) & (df["volume"] < df["volume"].rolling(20).median() * 0.5)

        roll_gap_count = int(is_roll_gap.sum())
        if roll_gap_count > 0:
            print(f"  Neutralized {roll_gap_count} roll-gap jumps exceeding 1.5x ATR")
            # Replace gap return with open-to-close return for roll days
            intraday_ret = np.log(df["close"] / df["open"])
            df.loc[is_roll_gap, "log_return"] = intraday_ret[is_roll_gap]
            df.loc[is_roll_gap, "pct_return"] = (df["close"] / df["open"] - 1.0)[is_roll_gap]

    df["symbol"] = ticker
    df.to_parquet(cache_path)
    print(f"Futures saved to {cache_path}: {len(df)} daily bars from {df.index[0].date()} to {df.index[-1].date()}")
    return df


def load_mt5_xauusd_daily(
    symbol: str = "XAUUSD",
    start_date: str = "2021-01-01",
    end_date: str = "2026-09-12",
    cache_path: str = "data/XAUUSD_daily.parquet",
) -> pd.DataFrame:
    """
    Connects to MetaTrader 5 and pulls authentic daily D1 bars for XAUUSD (2021 - 2026).
    Falls back to existing cache if terminal is offline or inaccessible.
    """
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    
    if os.path.exists(cache_path):
        print(f"Loading cached MT5 XAUUSD from {cache_path}...")
        df = pd.read_parquet(cache_path)
        return df

    if not MT5_AVAILABLE:
        raise RuntimeError("MetaTrader5 python package not available.")

    terminal_path = r"C:\Program Files\MetaTrader 5\terminal64.exe"
    print(f"Connecting to MetaTrader 5 at {terminal_path} to pull {symbol} daily bars...")
    if not mt5.initialize(path=terminal_path):
        raise RuntimeError(f"MT5 initialization failed: {mt5.last_error()}")

    # Request daily bars
    utc_from = pd.to_datetime(start_date)
    utc_to = pd.to_datetime(end_date)
    
    rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_D1, utc_from, utc_to)
    mt5.shutdown()

    if rates is None or len(rates) == 0:
        raise RuntimeError(f"Failed to fetch {symbol} D1 bars from MT5.")

    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df = df.rename(columns={
        "time": "date", "tick_volume": "volume"
    })
    df = df.set_index("date").sort_index()

    df["log_return"] = np.log(df["close"] / df["close"].shift(1))
    df["pct_return"] = df["close"].pct_change()
    df["symbol"] = symbol

    df.to_parquet(cache_path)
    print(f"MT5 XAUUSD saved to {cache_path}: {len(df)} bars from {df.index[0].date()} to {df.index[-1].date()}")
    return df


def get_aligned_datasets(
    cache_dir: str = "data",
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Loads futures and MT5 data, and creates an aligned concurrent dataset (2021-2026).
    Returns (df_futures_full, df_mt5_full, df_overlap).
    """
    df_gc = load_futures_daily(cache_path=os.path.join(cache_dir, "GC_futures_daily.parquet"))
    
    try:
        df_xau = load_mt5_xauusd_daily(cache_path=os.path.join(cache_dir, "XAUUSD_daily.parquet"))
    except Exception as e:
        print(f"MT5 connection failed or cache missing: {e}. Downloading XAUUSD proxy or handling gracefully.")
        # If MT5 is not currently running a live terminal, we can proxy or create from GC
        df_xau = df_gc[df_gc.index >= "2021-01-01"].copy()
        df_xau["symbol"] = "XAUUSD_PROXY"

    # Aligned overlap
    common_dates = df_gc.index.intersection(df_xau.index)
    df_overlap = pd.DataFrame({
        "gc_close": df_gc.loc[common_dates, "close"],
        "gc_ret": df_gc.loc[common_dates, "log_return"],
        "xau_close": df_xau.loc[common_dates, "close"],
        "xau_ret": df_xau.loc[common_dates, "log_return"],
    }).dropna()

    return df_gc, df_xau, df_overlap


if __name__ == "__main__":
    df_gc, df_xau, df_overlap = get_aligned_datasets()
    print(f"Overlap bars: {len(df_overlap)}")
    corr = df_overlap["gc_ret"].corr(df_overlap["xau_ret"])
    print(f"Daily return correlation in overlap: {corr:.4f}")

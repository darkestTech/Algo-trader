# strategies/ema_rsi_strategy.py
import pandas as pd
import numpy as np


def generate_ema_rsi_signals(df, fast_window=5, slow_window=20, rsi_period=10):
    """
    EMA + RSI hybrid trading strategy.

    Entry (BUY) conditions:
        - Fast EMA > Slow EMA
        - RSI > 55
    Exit (SELL) conditions:
        - Fast EMA < Slow EMA
        - RSI < 45

    The goal of these parameters is to ensure
    enough crossovers happen for testing.
    """

    print("⚙️ Generating EMA + RSI strategy signals...")

    # --- Safety checks ---
    if "close" not in df.columns:
        raise ValueError("❌ DataFrame must include a 'close' column with prices.")

    # === Compute EMAs ===
    df["EMA_fast"] = df["close"].ewm(span=fast_window, adjust=False).mean()
    df["EMA_slow"] = df["close"].ewm(span=slow_window, adjust=False).mean()

    # === Compute RSI ===
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=rsi_period, min_periods=1).mean()
    avg_loss = loss.rolling(window=rsi_period, min_periods=1).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))

    # === Generate Trading Signals ===
    df["signal"] = 0
    df.loc[(df["EMA_fast"] > df["EMA_slow"]) & (df["RSI"] > 55), "signal"] = 1   # BUY
    df.loc[(df["EMA_fast"] < df["EMA_slow"]) & (df["RSI"] < 45), "signal"] = -1  # SELL

    # === Detect crossovers ===
    df["crossover"] = df["signal"].diff()

    # === Summary & Save ===
    total_signals = df["signal"].abs().sum()
    print(f"📊 Signals generated: {int(total_signals)}")
    if total_signals == 0:
        print("⚠️ Warning: No valid trade signals detected. Try adjusting RSI or EMA parameters.")

    # Save for manual inspection
    df.to_csv("data/strategy_ema_rsi_signals.csv", index=False)
    print("✅ Signals saved → data/strategy_ema_rsi_signals.csv")

    return df

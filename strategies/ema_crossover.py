# strategies/ema_crossover.py

import os
import sys
import pandas as pd

# ✅ Add project root to import path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_handler import clean_and_prepare_data, fetch_ohlcv


def generate_ema_signals(df, fast_window=5, slow_window=20):
    """
    Generate buy/sell signals based on EMA crossover strategy.
    Buy when EMA_fast > EMA_slow, Sell when EMA_fast < EMA_slow.
    """
    print("⚙️ Generating EMA crossover signals...")

    df["EMA_fast"] = df["close"].ewm(span=fast_window, adjust=False).mean()
    df["EMA_slow"] = df["close"].ewm(span=slow_window, adjust=False).mean()

    # Signal column: 1 = Buy, -1 = Sell, 0 = Neutral
    df["signal"] = 0
    df.loc[df["EMA_fast"] > df["EMA_slow"], "signal"] = 1
    df.loc[df["EMA_fast"] < df["EMA_slow"], "signal"] = -1

    # Detect crossovers (actual entry/exit points)
    df["crossover"] = df["signal"].diff()

    # Save results
    df.to_csv("data/strategy_ema_signals.csv", index=False)
    print("✅ Signals generated and saved to data/strategy_ema_signals.csv")

    return df


if __name__ == "__main__":
    df = fetch_ohlcv("bitcoin", 30)
    df = clean_and_prepare_data(df)
    df = generate_ema_signals(df)

    print("\n📊 Last 5 signal rows:")
    print(df[["timestamp", "close", "EMA_fast", "EMA_slow", "signal", "crossover"]].tail())

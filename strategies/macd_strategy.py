# strategies/macd_strategy.py
import pandas as pd

def generate_macd_signals(df, short=12, long=26, signal=9):
    """
    Compute MACD line, signal line, histogram, and buy/sell signals.
    Returns DataFrame with 'crossover' column like other strategies.
    """
    df = df.copy()
    df["ema_short"] = df["close"].ewm(span=short, adjust=False).mean()
    df["ema_long"] = df["close"].ewm(span=long, adjust=False).mean()
    df["macd"] = df["ema_short"] - df["ema_long"]
    df["signal_line"] = df["macd"].ewm(span=signal, adjust=False).mean()
    df["histogram"] = df["macd"] - df["signal_line"]

    df["crossover"] = 0
    df.loc[(df["macd"] > df["signal_line"]) & (df["macd"].shift(1) <= df["signal_line"].shift(1)), "crossover"] = 2  # Buy
    df.loc[(df["macd"] < df["signal_line"]) & (df["macd"].shift(1) >= df["signal_line"].shift(1)), "crossover"] = -2  # Sell

    df.to_csv("data/strategy_macd_signals.csv", index=False)
    return df

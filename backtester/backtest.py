# backtester/backtest.py
import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ✅ Allow relative imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_handler import fetch_ohlcv, clean_and_prepare_data
from utils.analytics import calculate_performance_metrics, print_performance_report

INITIAL_BALANCE = 1000
MAX_RISK_PER_TRADE = 0.02  # 2%
MAX_DRAWDOWN = 0.10        # 10%


# ----------------------------
# 📊 Backtest Function
# ----------------------------
def backtest_strategy(df):
    balance = INITIAL_BALANCE
    equity_curve = []
    trades = []
    peak = INITIAL_BALANCE
    position = 0  # 1=long, -1=short, 0=flat

    for i in range(1, len(df)):
        price = df["close"].iloc[i]
        signal = df["crossover"].iloc[i]

        # Update drawdown
        peak = max(peak, balance)
        drawdown = (peak - balance) / peak

        # Stop trading if drawdown exceeds limit
        if drawdown > MAX_DRAWDOWN:
            print("⚠️ Max drawdown reached — stopping trades.")
            break

        # Dynamic position size based on volatility
        volatility = df["close"].pct_change().rolling(10).std().iloc[i]
        risk_factor = min(1.0, MAX_RISK_PER_TRADE / max(volatility, 1e-4))
        position_size = balance * risk_factor

        if signal == 1 and position == 0:  # Buy
            entry_price = price
            position = 1

        elif signal == -1 and position == 1:  # Sell
            profit = (price - entry_price) / entry_price * position_size
            balance += profit
            trades.append({
                "timestamp": df["timestamp"].iloc[i],
                "entry": entry_price,
                "exit": price,
                "profit_$": profit,
                "balance": balance
            })
            position = 0

        equity_curve.append({
            "timestamp": df["timestamp"].iloc[i],
            "balance": balance
        })

    equity_df = pd.DataFrame(equity_curve)
    trades_df = pd.DataFrame(trades)
    return balance, trades_df, equity_df


# ----------------------------
# 📈 Plot Equity Curve
# ----------------------------
def plot_equity_curve(equity_df, title="Equity Curve – Strategy Result"):
    plt.figure(figsize=(10, 5))
    plt.plot(equity_df["timestamp"], equity_df["balance"], label="Equity Curve")
    plt.xlabel("Time")
    plt.ylabel("Balance ($)")
    plt.title(title)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show(block=True)  # Keeps chart open until manually closed


# ----------------------------
# 🚀 Main
# ----------------------------
if __name__ == "__main__":
    from strategies.macd_strategy import generate_macd_signals
    from strategies.ema_rsi_strategy import generate_ema_rsi_signals

    print("📊 Fetching bitcoin data for backtest...")

    data_path = "data/bitcoin_cleaned.csv"
    if os.path.exists(data_path):
        print("💾 Using cached data from data/bitcoin_cleaned.csv")
        df = pd.read_csv(data_path, parse_dates=["timestamp"])
    else:
        print("🌐 Fetching fresh data from CoinGecko (may take ~15 s)...")
        df = fetch_ohlcv()
        df = clean_and_prepare_data(df)
        df.to_csv(data_path, index=False)
        print("💾 Cleaned data saved to data/bitcoin_cleaned.csv")

    # === Strategy Selection ===
    print("\n🎯 Choose strategy:")
    print("1 – EMA + RSI")
    print("2 – MACD")
    choice = input("Enter 1 or 2 (default = 1): ").strip() or "1"

    if choice == "2":
        print("⚙️ Running MACD strategy...")
        df = generate_macd_signals(df)
        strategy_name = "macd"
    else:
        print("⚙️ Running EMA + RSI strategy...")
        df = generate_ema_rsi_signals(df)
        strategy_name = "ema_rsi"

    print("📈 Running backtest with dynamic sizing + drawdown protection...")
    final_balance, trades_df, equity_df = backtest_strategy(df)

    # === Save per-strategy results ===
    equity_path = f"data/equity_curve_{strategy_name}.csv"
    trades_path = f"data/backtest_trades_{strategy_name}.csv"

    equity_df.to_csv(equity_path, index=False)

    if trades_df.empty:
        print(f"⚠️ No trades generated for {strategy_name}. Saving empty template file.")
        pd.DataFrame(columns=["timestamp", "entry", "exit", "profit_$", "balance"]).to_csv(trades_path, index=False)
    else:
        trades_df.to_csv(trades_path, index=False)

    print(f"💾 Saved results → {trades_path}, {equity_path}")

    # === Analytics ===
    total_return = ((final_balance - INITIAL_BALANCE) / INITIAL_BALANCE) * 100
    print("✅ Backtest Complete!")
    print(f"📊 Final Balance: ${final_balance:.2f}")
    print(f"💰 Total Return: {total_return:.2f}%")
    print(f"🧾 Total Trades: {len(trades_df)}")

    results = calculate_performance_metrics(trades_df, equity_df)
    print_performance_report(results)

    # === Visualization ===
    plot_equity_curve(equity_df, title=f"Equity Curve – {strategy_name.upper()}")

    print("✅ Analytics printed and chart opened.")
    input("\n📈 Press [Enter] to close chart and exit... ")

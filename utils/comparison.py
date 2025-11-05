# utils/comparison.py
import pandas as pd
from utils.analytics import calculate_performance_metrics

def compare_strategies():
    strategies = {
        "EMA + RSI": {
            "trades": "data/backtest_trades_ema_rsi.csv",
            "equity": "data/equity_curve_ema_rsi.csv"
        },
        "MACD": {
            "trades": "data/backtest_trades_macd.csv",
            "equity": "data/equity_curve_macd.csv"
        }
    }

    results = {}
    for name, paths in strategies.items():
        try:
            trades_df = pd.read_csv(paths["trades"])
            equity_df = pd.read_csv(paths["equity"])
            if not trades_df.empty and not equity_df.empty:
                results[name] = calculate_performance_metrics(trades_df, equity_df)
        except Exception:
            continue
    return results

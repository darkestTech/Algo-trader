import numpy as np
import pandas as pd


def calculate_performance_metrics(trades_df, equity_df, risk_free_rate=0.0):
    """
    Compute key trading performance metrics.
    """

    if trades_df.empty or "profit_$" not in trades_df.columns:
        return {"error": "No trades or missing data"}

    # clean data 
    trades_df = trades_df.dropna(subset=["profit_$"])
    profits = trades_df["profit_$"].values
    if len(profits) == 0:
        return {"error": "No profit data"}

    total_trades = len(profits)
    winning = profits[profits > 0]
    losing = profits[profits <= 0]

    # metrics 
    win_rate = len(winning) / total_trades * 100 if total_trades else 0
    avg_win = np.mean(winning) if len(winning) else 0
    avg_loss = abs(np.mean(losing)) if len(losing) else 0
    profit_factor = (winning.sum() / abs(losing.sum())) if len(losing) else np.inf
    rr_ratio = avg_win / avg_loss if avg_loss != 0 else np.nan

    #  max drawdown 
    if "balance" in equity_df.columns:
        equity = equity_df["balance"].values
        high = np.maximum.accumulate(equity)
        drawdown = (equity - high) / high
        max_dd = abs(np.min(drawdown)) * 100
    else:
        max_dd = np.nan

    # sharpe ratio 
    returns = np.diff(equity_df["balance"].values) / equity_df["balance"].shift(1).fillna(method="bfill").values[:-1]
    sharpe = 0 if np.std(returns) == 0 else (np.mean(returns) - risk_free_rate) / np.std(returns) * np.sqrt(252)

    results = {
        "total_trades": total_trades,
        "win_rate_%": round(win_rate, 2),
        "profit_factor": round(profit_factor, 2),
        "avg_RR": round(rr_ratio, 2),
        "max_drawdown_%": round(max_dd, 2),
        "sharpe_ratio": round(sharpe, 2),
    }

    return results


def print_performance_report(results):
    """
    Nicely format the results dictionary for terminal output.
    """
    print("\n📊 PERFORMANCE REPORT")
    print("────────────────────────────")
    for k, v in results.items():
        if isinstance(v, float):
            print(f"{k:<20} : {v}")
        else:
            print(f"{k:<20} : {v}")
    print("────────────────────────────\n")

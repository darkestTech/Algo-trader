# dashboard/app.py
import os
import sys
import pandas as pd
import plotly.express as px
import streamlit as st

# ✅ Import paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.analytics import calculate_performance_metrics
from utils.comparison import compare_strategies

# --- UI Config ---
st.set_page_config(page_title="Algo-Trader Dashboard", layout="wide")
st.title("📊 Algo-Trader Multi-Strategy Dashboard")

# --- Strategy Selector ---
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

st.sidebar.header("⚙️ Strategy Options")
selected_strategy = st.sidebar.selectbox("Select Strategy", list(strategies.keys()), index=0)
show_comparison = st.sidebar.checkbox("📈 Show Comparison Overlay", value=False)

# --- 🧠 Parameter Tuning Sidebar ---
st.sidebar.subheader("🧠 Parameter Tuning")

if selected_strategy == "EMA + RSI":
    ema_short = st.sidebar.slider("EMA Short Period", 5, 30, 12)
    ema_long = st.sidebar.slider("EMA Long Period", 20, 100, 26)
    rsi_period = st.sidebar.slider("RSI Period", 7, 30, 14)
    rsi_overbought = st.sidebar.slider("RSI Overbought", 60, 90, 70)
    rsi_oversold = st.sidebar.slider("RSI Oversold", 10, 50, 30)
else:
    macd_short = st.sidebar.slider("MACD Short EMA", 5, 20, 12)
    macd_long = st.sidebar.slider("MACD Long EMA", 20, 50, 26)
    macd_signal = st.sidebar.slider("MACD Signal EMA", 5, 20, 9)

st.sidebar.info("")

# --- Load Strategy Files ---
paths = strategies[selected_strategy]
if not (os.path.exists(paths["trades"]) and os.path.exists(paths["equity"])):
    st.error(f"❌ Run backtester first for {selected_strategy}.")
    st.stop()

try:
    trades_df = pd.read_csv(paths["trades"])
    equity_df = pd.read_csv(paths["equity"])
    if trades_df.empty:
        st.warning(f"⚠️ No trades found for {selected_strategy}.")
except pd.errors.EmptyDataError:
    st.error(f"❌ Data file for {selected_strategy} is empty or invalid.")
    st.stop()

# --- Metrics ---
results = calculate_performance_metrics(trades_df, equity_df)
col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Trades", results.get("total_trades", 0))
col2.metric("Win Rate (%)", results.get("win_rate_%", 0))
col3.metric("Profit Factor", results.get("profit_factor", 0))
col4.metric("Avg R/R", results.get("avg_RR", 0))
col5.metric("Max Drawdown (%)", results.get("max_drawdown_%", 0))
col6.metric("Sharpe Ratio", results.get("sharpe_ratio", 0))

st.markdown("---")

# --- Equity Curve / Comparison ---
if show_comparison:
    st.subheader("📊 Strategy Comparison — Equity Over Time")

    fig = px.line(template="plotly_dark")
    for strat_name, files in strategies.items():
        if os.path.exists(files["equity"]):
            try:
                eq = pd.read_csv(files["equity"])
                if not eq.empty:
                    fig.add_scatter(x=eq["timestamp"], y=eq["balance"], mode="lines", name=strat_name)
            except Exception:
                pass
    fig.update_layout(title="Equity Curves Comparison", xaxis_title="Time", yaxis_title="Balance ($)")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.subheader(f"📈 Equity Curve — {selected_strategy}")
    fig_equity = px.line(
        equity_df,
        x="timestamp",
        y="balance",
        title=f"Equity Curve ({selected_strategy})",
        template="plotly_dark",
        markers=True,
    )
    st.plotly_chart(fig_equity, use_container_width=True)

# --- Profit Distribution ---
if "profit_$" in trades_df.columns and not trades_df.empty:
    st.subheader("💹 Profit Distribution")
    fig_hist = px.histogram(
        trades_df,
        x="profit_$",
        nbins=20,
        color_discrete_sequence=["#00C2FF"],
        template="plotly_dark",
    )
    st.plotly_chart(fig_hist, use_container_width=True)

# --- Trade Log ---
st.subheader("🧾 Recent Trades")
if not trades_df.empty:
    st.dataframe(trades_df.tail(15), use_container_width=True)
else:
    st.info("No trades to display for this strategy.")

# --- Comparison Table ---
if show_comparison:
    st.markdown("### 📋 Strategy Performance Summary")
    all_results = compare_strategies()
    if all_results:
        df_summary = pd.DataFrame(all_results).T
        st.dataframe(df_summary, use_container_width=True)
    else:
        st.warning("⚠️ No comparison data available. Run both backtests first.")

st.success(f"✅ {selected_strategy} dashboard loaded successfully.")

# live/paper_trader.py

import os
import sys
import time
import random
import requests
import pandas as pd
from datetime import datetime

# ✅ Add project root to import path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategies.ema_crossover import generate_ema_signals
from core.data_handler import clean_and_prepare_data, fetch_ohlcv

# === Configuration ===
SYMBOL_ID = "bitcoin"
INTERVAL = 20          # seconds between price checks
START_BALANCE = 1000
MAX_RETRIES = 3


def load_or_fetch_data():
    """
    Load cached cleaned data if available, otherwise fetch from CoinGecko.
    Prevents hanging on slow API calls.
    """
    data_path = "data/bitcoin_cleaned.csv"
    if os.path.exists(data_path):
        print("💾 Using cached data from data/bitcoin_cleaned.csv")
        return pd.read_csv(data_path, parse_dates=["timestamp"])
    else:
        print("🌐 Fetching historical data from CoinGecko (may take ~15s)...")
        df = fetch_ohlcv("bitcoin", 30)
        df = clean_and_prepare_data(df)
        return df


def get_latest_price(symbol_id="bitcoin"):
    """
    Fetch latest price with rate-limit handling and fallback.
    Tries CoinGecko first, then falls back to CryptoCompare if needed.
    """
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol_id}&vs_currencies=usd"
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 429:
                print("⚠️ Rate limit hit — waiting 60 s before retry...")
                time.sleep(60)
                continue

            response.raise_for_status()
            data = response.json()
            price = data[symbol_id]["usd"]
            return price

        except requests.exceptions.RequestException as e:
            print(f"⚠️ Price fetch error: {e}")
            time.sleep(random.randint(5, 15))

    # === Fallback to CryptoCompare ===
    try:
        print("🔄 Switching to backup API (CryptoCompare)...")
        alt = requests.get("https://min-api.cryptocompare.com/data/price?fsym=BTC&tsyms=USD", timeout=10)
        alt.raise_for_status()
        data = alt.json()
        return data["USD"]
    except Exception as e:
        print(f"❌ Backup API failed: {e}")
        return None


def paper_trade(df, balance=START_BALANCE):
    """
    Run EMA crossover strategy in a live-like loop using new data points.
    Simulates buy/sell trades and logs results.
    """
    position = 0
    entry_price = 0
    trade_log = []

    print(f"🚀 Starting Paper Trading for {SYMBOL_ID.upper()}")
    print(f"💰 Starting balance: ${balance}")

    while True:
        try:
            latest_price = get_latest_price(SYMBOL_ID)
            if latest_price is None:
                print("⚠️ No price fetched, retrying shortly...")
                time.sleep(10)
                continue

            timestamp = datetime.utcnow()

            # Add new tick to dataframe
            new_row = {"timestamp": timestamp, "close": latest_price}
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df = df.tail(50).reset_index(drop=True)

            # Recalculate EMA signals
            df = generate_ema_signals(df, fast_window=5, slow_window=20)
            signal = int(df["signal"].iloc[-1])
            crossover = df["crossover"].iloc[-1]

            print(f"[{timestamp:%H:%M:%S}] Price: ${latest_price:.2f} | Signal: {signal}")

            # Simulated trading logic
            if crossover == 2 and position == 0:
                position = 1
                entry_price = latest_price
                print(f"🟢 BUY executed at ${entry_price:.2f}")
                trade_log.append({"timestamp": timestamp, "action": "BUY", "price": entry_price})

            elif crossover == -2 and position == 1:
                position = 0
                profit = (latest_price - entry_price) / entry_price * 100
                balance *= (1 + profit / 100)
                print(f"🔴 SELL executed at ${latest_price:.2f} | Profit: {profit:.2f}% | Balance: ${balance:.2f}")
                trade_log.append({
                    "timestamp": timestamp,
                    "action": "SELL",
                    "price": latest_price,
                    "profit_%": profit,
                    "balance": balance
                })
                pd.DataFrame(trade_log).to_csv("data/paper_trades.csv", index=False)

            time.sleep(INTERVAL)

        except KeyboardInterrupt:
            print("\n🛑 Paper trading stopped manually.")
            pd.DataFrame(trade_log).to_csv("data/paper_trades.csv", index=False)
            print("💾 Trades saved to data/paper_trades.csv")
            break

        except Exception as e:
            print(f"⚠️ Runtime error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    try:
        df = load_or_fetch_data()
        paper_trade(df)
    except Exception as e:
        print(f"❌ Startup error: {e}")

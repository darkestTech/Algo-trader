# core/data_handler.py

import requests
import pandas as pd
from datetime import datetime

def fetch_ohlcv(symbol_id="bitcoin", days=30):
    """
    Fetch historical OHLC data from CoinGecko.
    symbol_id: CoinGecko asset ID (e.g., 'bitcoin', 'ethereum')
    days: number of days of data (1, 7, 30, 90, 'max')
    """
    print(f"⏳ Fetching {symbol_id} data from CoinGecko for {days} days...")

    url = f"https://api.coingecko.com/api/v3/coins/{symbol_id}/ohlc?vs_currency=usd&days={days}"
    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(f"❌ Failed to fetch data: {response.status_code}, {response.text}")

    data = response.json()
    df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

    print(f"✅ Data fetched! {len(df)} rows received.")
    return df


def clean_and_prepare_data(df):
    """
    Clean the OHLCV data and prepare it for strategy use.
    """
    print("🧹 Cleaning and preparing data...")

    # Remove duplicates
    df = df.drop_duplicates(subset=["timestamp"])

    # Sort by time
    df = df.sort_values(by="timestamp").reset_index(drop=True)

    # Compute additional metrics
    df["returns"] = df["close"].pct_change()
    df["ma_5"] = df["close"].rolling(window=5).mean()
    df["ma_20"] = df["close"].rolling(window=20).mean()

    # Drop NaN rows (first few moving averages)
    df = df.dropna()

    print(f"✅ Data cleaned. Final shape: {df.shape}")

    # Save cleaned data
    df.to_csv("data/bitcoin_cleaned.csv", index=False)
    print("💾 Cleaned data saved to data/bitcoin_cleaned.csv")

    return df


if __name__ == "__main__":
    df = fetch_ohlcv("bitcoin", 30)
    df_clean = clean_and_prepare_data(df)

    print("\n📊 Last 5 rows of cleaned data:")
    print(df_clean.tail())

#!/usr/bin/env python3
import pandas as pd
import yfinance as yf
from datetime import datetime

OUT = "data/soybean_prices.csv"
TICKER = "ZS=F"  # CBOT Soybean continuous
START = "2005-01-01"

def main():
    print("Downloading daily OHLCV for", TICKER, "from", START)
    df = yf.download(TICKER, start=START, progress=False, auto_adjust=False)
    if df.empty:
        raise SystemExit("No data returned. Check internet or ticker.")

    # Normalize column names (handle both single-level and multi-level columns)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.rename(columns={
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Adj Close": "adj_close",
        "Volume": "volume"
    })
    df.index = pd.to_datetime(df.index)
    df["date"] = df.index.date

    # If adj_close doesn't exist, use close
    if "adj_close" not in df.columns:
        df["adj_close"] = df["close"]

    # Some sources don't include open interest in Yahoo; keep column for later merges
    df["open_interest"] = pd.NA
    # Keep only needed columns
    cols = ["date", "open", "high", "low", "close", "adj_close", "volume", "open_interest"]
    df = df[cols].dropna(subset=["close"])
    df.to_csv(OUT, index=False)
    print("Wrote", OUT, "rows:", len(df))

if __name__ == "__main__":
    main()

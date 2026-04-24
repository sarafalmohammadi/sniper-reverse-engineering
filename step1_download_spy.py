#!/usr/bin/env python3
"""Step 1: Download SPY 1-min bars from Polygon.io API."""

import requests
import pandas as pd
import os
import time

API_KEY = "C5z3c4yphrBDGbIt3M0TqPJ0Ltu2Ekt4"
BASE = "https://api.polygon.io"


def download_spy_1min():
    fname = "market_data/SPY_1min.csv"
    if os.path.exists(fname):
        df = pd.read_csv(fname)
        print(f"SPY data already exists: {len(df)} rows")
        return df

    os.makedirs("market_data", exist_ok=True)
    bars = []
    url = f"{BASE}/v2/aggs/ticker/SPY/range/1/minute/2026-01-01/2026-04-24"
    params = {"apiKey": API_KEY, "limit": 50000, "sort": "asc", "adjusted": "false"}

    page = 0
    while url:
        page += 1
        r = requests.get(url, params=params)
        data = r.json()
        results = data.get("results", [])
        bars.extend(results)
        print(f"  Page {page}: got {len(results)} bars (total: {len(bars)})")

        next_url = data.get("next_url")
        if next_url:
            url = next_url + f"&apiKey={API_KEY}"
            params = {}
        else:
            url = None
        time.sleep(0.15)

    df = pd.DataFrame(bars)
    df.rename(columns={
        "t": "timestamp", "o": "open", "h": "high",
        "l": "low", "c": "close", "v": "volume"
    }, inplace=True)
    df["datetime_et"] = (
        pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        .dt.tz_convert("America/New_York")
    )
    df["spx_approx"] = df["close"] * 10
    df.to_csv(fname, index=False)
    print(f"Saved SPY data: {len(df)} rows to {fname}")
    return df


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    spy_df = download_spy_1min()
    print(f"SPY bars: {len(spy_df)} rows")
    print(f"Date range: {spy_df['datetime_et'].iloc[0]} to {spy_df['datetime_et'].iloc[-1]}")

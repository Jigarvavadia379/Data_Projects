import sys
import subprocess
def install_if_missing(pkg_name, import_name=None):
    module = import_name or pkg_name
    try:
        __import__(module)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg_name])

install_if_missing("streamlit")

import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
import requests

# --- Resilient autocomplete function ---
def lookup_tickers(query, region="US", lang="en"):
    url = "https://autoc.finance.yahoo.com/autoc"
    params = {"query": query, "region": region, "lang": lang, "corsDomain": "finance.yahoo.com"}
    try:
        resp = requests.get(url, params=params, timeout=5)
        data = resp.json().get("ResultSet", {}).get("Result", [])
        matches = [(item["symbol"], item["name"]) for item in data if item.get("typeDisp") == "Equity"]
        # Always add the raw query as a last option (for direct ticker)
        if query.upper() not in [sym for sym, _ in matches]:
            matches.append((query.upper(), f"Manual entry ({query.upper()})"))
        return matches
    except Exception as e:
        # On error, just use the query as ticker
        return [(query.upper(), f"Manual entry ({query.upper()})")]

st.set_page_config(page_title="Stock Search & Candlestick", layout="wide")
st.title("🔎 Stock Search & Dynamic Candlestick Chart")

search = st.text_input("🔍 Search for a company or ticker (try 'Google', 'Bharat', 'Tata', 'AAPL', 'GOOGL', etc)")
picked_symbol = None
picked_name = None

if search:
    # Try IN first, then US, then merge (remove dups)
    matches = lookup_tickers(search, region="IN") + lookup_tickers(search, region="US")
    seen = set()
    unique_matches = []
    for sym, name in matches:
        if sym not in seen:
            unique_matches.append((sym, name))
            seen.add(sym)
    display_options = [f"{name} ({symbol})" for symbol, name in unique_matches]
    picked = st.selectbox("Select from suggestions:", display_options)
    if picked:
        idx = display_options.index(picked)
        picked_symbol = unique_matches[idx][0]
        picked_name = unique_matches[idx][1]


# --- Period and Interval ---
period = st.selectbox("History period", ["1d", "7d", "30d", "90d"], index=0)
interval = st.selectbox("Interval", ["1m", "5m", "15m", "30m", "60m", "1d"], index=1)

# --- Plotly Candlestick Chart ---
@st.cache_data(ttl=300)
def fetch_data(symbol, period, interval):
    df = yf.download(picked_symbol, period=period, interval=interval, progress=False)
    # flatten MultiIndex columns if present
    if isinstance(df.columns, (pd.MultiIndex)):
        df.columns = df.columns.get_level_values(0)
    if df.empty:
        return df
    # normalize case to match, in case yahoo changed column names
    df.columns = [str(c).capitalize() for c in df.columns]
    needed_cols = ["Open", "High", "Low", "Close"]
    present_cols = [col for col in needed_cols if col in df.columns]
    if len(present_cols) < 4:
        # Not all OHLC columns are present, return empty
        return pd.DataFrame()
    df = df.dropna(subset=present_cols)
    # Convert index to IST if needed
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC").tz_convert("Asia/Kolkata")
    else:
        df.index = df.index.tz_convert("Asia/Kolkata")
    return df


if picked_symbol:
    st.markdown(f"### :chart_with_upwards_trend: {picked_name} (`{picked_symbol}`)")
    df = fetch_data(picked_symbol, period, interval)
    if not df.empty:
        fig = go.Figure(go.Candlestick(
            x=df.index,
            open=df["Open"], high=df["High"],
            low=df["Low"], close=df["Close"],
            name=picked_symbol
        ))
        fig.update_layout(
            template="plotly_dark",
            title=f"{picked_name} ({picked_symbol}) Candlestick Chart",
            xaxis=dict(title="Date / Time"),
            yaxis=dict(title="Price"),
            height=600
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for this symbol/period/interval.")
else:
    st.info("Search for a stock above to get started!")

# Analysis 

# Calculate Moving Averages
df['SMA_20'] = df['Close'].rolling(window=20).mean()  # 20-day Simple MA
df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()  # 50-day Exponential MA

# Signal: Buy when SMA crosses above EMA, Sell when SMA crosses below EMA
df['Signal'] = 0
df['Signal'][20:] = np.where(df['SMA_20'][20:] > df['EMA_50'][20:], 1, 0)
df['Position'] = df['Signal'].diff()

# Plotting
plt.figure(figsize=(14,8))
plt.plot(df['Close'], label='Close Price', color='blue', alpha=0.5)
plt.plot(df['SMA_20'], label='20-Day SMA', color='green')
plt.plot(df['EMA_50'], label='50-Day EMA', color='red')
plt.scatter(df[df['Position'] == 1].index, 
            df[df['Position'] == 1]['Close'], 
            marker='^', color='g', label='Buy Signal', s=100)
plt.scatter(df[df['Position'] == -1].index, 
            df[df['Position'] == -1]['Close'], 
            marker='v', color='r', label='Sell Signal', s=100)
plt.title(f'{ticker} Moving Average Crossover Signals')
plt.xlabel('Date')
plt.ylabel('Price')
plt.legend()
plt.grid()
plt.show()

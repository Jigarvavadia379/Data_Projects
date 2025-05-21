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
    df = yf.download(symbol, period=period, interval=interval, progress=False)
    if isinstance(df.columns, (list, tuple)) and isinstance(df.columns[0], tuple):
        df.columns = [c[0] for c in df.columns]
    if not df.empty:
        if df.index.tz is None:
            df.index = df.index.tz_localize("UTC").tz_convert("Asia/Kolkata")
        else:
            df.index = df.index.tz_convert("Asia/Kolkata")
        df = df.dropna(subset=["Open", "High", "Low", "Close"])
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

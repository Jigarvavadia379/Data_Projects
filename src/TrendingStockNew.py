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

st.set_page_config(page_title="Dynamic Intraday Candles", layout="wide")
st.title("🔍 NIFTY-Style Candlestick Viewer")

# — Sidebar inputs —
symbol = st.sidebar.text_input("Ticker symbol", value="^NSEI")
period = st.sidebar.selectbox("History period", ["1d","7d","30d","90d"], index=0)
interval = st.sidebar.selectbox("Interval", ["1m","5m","15m","30m","60m"], index=1)

# — Fetch data —
@st.cache_data(ttl=300)
def fetch_data(sym, per, inter):
    df = yf.download(sym, period=per, interval=inter, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    # convert to IST
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC").tz_convert("Asia/Kolkata")
    else:
        df.index = df.index.tz_convert("Asia/Kolkata")
    return df.dropna(subset=["Open","High","Low","Close"])

df = fetch_data(symbol, period, interval)

if df.empty:
    st.error(f"No data for {symbol} with period={period}, interval={interval}.")
    st.stop()

# — Chart —
fig = go.Figure(go.Candlestick(
    x=df.index, open=df["Open"], high=df["High"],
    low=df["Low"], close=df["Close"], name=symbol
))

fig.update_layout(
    title=f"{symbol} Candlestick ({interval}, last {period})",
    template="plotly_dark",
    xaxis=dict(
        title="Time (IST)",
        tickformat="%d %b %H:%M",
        rangeslider=dict(visible=False),
        rangeselector=dict(
            buttons=[
                dict(count=1, label='1d', step='day',   stepmode='backward'),
                dict(count=7, label='7d', step='day',   stepmode='backward'),
                dict(count=1, label='1m', step='month', stepmode='backward'),
                dict(step='all', label='All')
            ]
        ),
        rangebreaks=[
            # remove weekends
            dict(bounds=["sat", "mon"]),
            # remove hours from 15:30 to midnight
            dict(bounds=[15.5, 24], pattern="hour"),
            # remove hours from midnight to 09:15
            dict(bounds=[0, 9.25], pattern="hour")
        ]
    ),
    yaxis=dict(title="Price"),
    margin=dict(l=20, r=20, t=40, b=20),
    height=600
)

st.plotly_chart(fig, use_container_width=True)
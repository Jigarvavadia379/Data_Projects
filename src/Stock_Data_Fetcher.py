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

def lookup_tickers(query, region="IN", lang="en"):
    url = "https://autoc.finance.yahoo.com/autoc"
    params = {"query": query, "region": region, "lang": lang, "corsDomain": "finance.yahoo.com"}
    try:
        resp = requests.get(url, params=params, timeout=5)
        data = resp.json().get("ResultSet", {}).get("Result", [])
        return [(item["symbol"], item["name"]) for item in data if item.get("typeDisp") == "Equity"]
    except Exception:
        return []

st.set_page_config(page_title="Stock Search & Candlestick", layout="wide")
st.title("🔎 Stock Search & Dynamic Candlestick Chart")

search = st.text_input("🔍 Search for a company or ticker (try 'Google', 'Bharat', 'Tata', etc)")
picked_symbol = None
picked_name = None

if search:
    matches = lookup_tickers(search)
    if matches:
        display_options = [f"{name} ({symbol})" for symbol, name in matches]
        picked = st.selectbox("Select from suggestions:", display_options)
        if picked:
            idx = display_options.index(picked)
            picked_symbol = matches[idx][0]
            picked_name = matches[idx][1]
    else:
        st.warning("No matching stocks found.")

# Period and Interval inputs
period = st.selectbox("History period", ["1d", "7d", "30d", "90d"], index=0)
interval = st.selectbox("Interval", ["1m", "5m", "15m", "30m", "60m"], index=1)

@st.cache_data(ttl=300)
def fetch_data(symbol, period, interval):
    df = yf.download(symbol, period=period, interval=interval, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    if not df.empty:
        # convert to IST if possible
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
            hovermode="x",
            dragmode="pan",
            title=dict(
                text=f"{picked_symbol} Candlestick ({interval}, last {period})",
                x=0.5,
                xanchor='center'
            ),
            xaxis=dict(
                title="Time (IST)",
                tickformat="%d %b %H:%M",
                showspikes=True,
                spikemode='across',
                spikesnap='cursor',
                showline=True,
                showgrid=True,
                spikedash='solid',
                spikethickness=1,
                rangeslider=dict(visible=False),
                rangeselector=dict(
                    buttons=[
                        dict(count=1, label='1d', step='day', stepmode='backward'),
                        dict(count=7, label='7d', step='day', stepmode='backward'),
                        dict(count=1, label='1m', step='month', stepmode='backward'),
                        dict(step='all', label='All')
                    ]
                )
            ),
            yaxis=dict(
                title="Price",
                showspikes=True,
                spikemode='across',
                spikesnap='cursor',
                showline=True,
                showgrid=True,
                spikedash='solid',
                spikethickness=1
            ),
            margin=dict(l=20, r=20, t=40, b=20),
            height=600
        )
        st.plotly_chart(
            fig,
            use_container_width=True,
            config={"modeBarButtonsToRemove": ['zoom2d','pan2d','select2d','lasso2d']}
        )
    else:
        st.info("No data available for this symbol/period/interval.")
else:
    st.info("Search for a stock above to get started!")

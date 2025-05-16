import sys
import subprocess

# Install required packages if missing
def install_if_missing(pkg_name, import_name=None):
    module = import_name or pkg_name
    try:
        __import__(module)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg_name])

install_if_missing("yfinance")
install_if_missing("mplfinance")
install_if_missing("pandas")

import yfinance as yf
import mplfinance as mpf
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from datetime import datetime, time, timedelta

# 1) Download last 2 days of 1-minute data to cover yesterday
symbol = "HAL.NS"
raw = yf.download(symbol, period='1d', interval='1m', progress=False)

if isinstance(raw.columns, pd.MultiIndex):
    raw.columns = raw.columns.get_level_values(0)

# 2) Convert to IST
if raw.index.tz is None:
    raw.index = raw.index.tz_localize("UTC").tz_convert("Asia/Kolkata")
else:
    raw.index = raw.index.tz_convert("Asia/Kolkata")

# 3) Filter for yesterday's session (09:15–15:30 IST)
today = datetime.now().date()
yesterday = today - timedelta(days=1)
intraday = raw.loc[
    (raw.index.date == yesterday) &
    (raw.index.time >= time(9, 15)) &
    (raw.index.time <= time(15, 30))
    ]

# 4) Keep only OHLC
intraday = intraday[['Open','High','Low','Close']].dropna()
intraday = intraday.astype(float)


fig = go.Figure(go.Candlestick(
    x=intraday.index,
    open=intraday['Open'],
    high=intraday['High'],
    low=intraday['Low'],
    close=intraday['Close'],
    name='NIFTY 50'
))

fig.update_layout(
    title=f'NIFTY 50 Intraday Candles ({yesterday})',
    xaxis=dict(tickformat='%H:%M', rangeslider=dict(visible=False)),
    yaxis=dict(title='Price'),
    template='plotly_dark',
    autosize=True,       # let it fill its container
    margin=dict(l=10, r=10, t=40, b=10)
)

# —— Render in your browser for full‐screen view —— #
pio.renderers.default = 'browser'
fig.show(config={'responsive': True})
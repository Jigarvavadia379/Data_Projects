import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

def fetch_live_nifty_index(index_name='NIFTY 50'):
    url = 'https://www.nseindia.com/api/market-data-pre-open?key=NIFTY'
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }

    # Fetch live data
    with requests.Session() as s:
        s.headers.update(headers)
        response = s.get(url)
        data = response.json()

    # Extract index data
    index_data = data.get('data', [])

    for item in index_data:
        if item.get('indexName') == index_name:
            print(f"{index_name} Live Data:")
            print(f"  Last Price: {item.get('lastPrice')}")
            print(f"  Change: {item.get('change')}")
            print(f"  Percent Change: {item.get('pChange')}%")
            return item

    print(f"{index_name} data not found.")
    return None

# Example usage
fetch_live_nifty_index('NIFTY 50')
fetch_live_nifty_index('NIFTY 100')

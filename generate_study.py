import yfinance as yf
import pandas as pd
import numpy as np
import os
from datetime import datetime
from pandas_datareader import data as pdr

# Indicators with their specific sources and weights
# Note: HY_Spread (20%) and Money_Market (2%) are the 'Lead' anchors.
indicators = {
    "VIX": {"ticker": "^VIX", "w": 0.12, "dir": -1, "source": "yahoo"},
    "DXY": {"ticker": "DX-Y.NYB", "w": 0.15, "dir": -1, "source": "yahoo"},
    "10Y_Yield": {"ticker": "^TNX", "w": 0.08, "dir": -1, "source": "yahoo"},
    "Gold": {"ticker": "GC=F", "w": 0.05, "dir": -1, "source": "yahoo"},
    "BTC": {"ticker": "BTC-USD", "w": 0.07, "dir": 1, "source": "yahoo"},
    "Copper": {"ticker": "HG=F", "w": 0.08, "dir": 1, "source": "yahoo"},
    "SPY": {"ticker": "SPY", "w": 0.05, "dir": 1, "source": "yahoo"},
    "RSP": {"ticker": "RSP", "w": 0.10, "dir": 1, "source": "yahoo"},
    "IWM": {"ticker": "IWM", "w": 0.10, "dir": 1, "source": "yahoo"},
    "HY_Spread": {"ticker": "BAMLH0A0HYM2", "w": 0.20, "dir": -1, "source": "fred"},
    "Money_Market": {"ticker": "WMMNS", "w": 0.02, "dir": -1, "source": "fred"}
}

def generate_study():
    start_date = "1994-01-01"
    end_date = datetime.now().strftime("%Y-%m-%d")
    fred_key = os.getenv('FRED_API_KEY')

    # 1. Initialize with S&P 500
    sp500_raw = yf.download("^GSPC", start=start_date, end=end_date, progress=False)
    master_df = pd.DataFrame(index=sp500_raw.index)
    master_df['SP500_Close'] = sp500_raw['Close']

    # 2. Fetch all 11 indicators
    for name, info in indicators.items():
        try:
            if info['source'] == 'yahoo':
                data = yf.download(info['ticker'], start=start_date, end=end_date, progress=False)['Close']
            else:
                data = pdr.get_data_fred(info['ticker'], start=start_date, end=end_date, api_key=fred_key)
            
            if not data.empty:
                master_df[name] = data
        except Exception as e:
            print(f"Skipping {name}: {e}")

    master_df = master_df.sort_index().ffill()
    crss_series = []
    
    # 3. CRSS Math Loop
    for i in range(len(master_df)):
        if i < 252:
            crss_series.append(np.nan)
            continue

        lookback = master_df.iloc[i-252:i]
        current = master_df.iloc[i]
        temp_score, active_weights = 0, 0

        for name, info in indicators.items():
            if name not in current or pd.isna(current[name]): continue
            series = lookback[name].dropna()
            if len(series) < 100: continue
            
            mean, std = series.mean(), series.std()
            if std == 0: continue
            
            z = (current[name] - mean) / (std * 3)
            norm = max(min(z * info['dir'], 1), -1)
            temp_score += (norm * info['w'])
            active_weights += info['w']

        final_daily = (temp_score / active_weights) * 100 if active_weights > 0 else 0
        crss_series.append(round(final_daily, 2))

    master_df['CRSS_Score'] = crss_series
    master_df.loc["1995-01-01":].to_csv('historical_crss_study.csv')

if __name__ == "__main__":
    generate_study()
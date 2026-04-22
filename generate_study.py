import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# Define indicators and lead-heavy weights
indicators = {
    "VIX": {"ticker": "^VIX", "w": 0.12, "dir": -1},
    "DXY": {"ticker": "DX-Y.NYB", "w": 0.15, "dir": -1},
    "10Y_Yield": {"ticker": "^TNX", "w": 0.08, "dir": -1},
    "Gold": {"ticker": "GC=F", "w": 0.05, "dir": -1},
    "BTC": {"ticker": "BTC-USD", "w": 0.07, "dir": 1},
    "Copper": {"ticker": "HG=F", "w": 0.08, "dir": 1},
    "SPY": {"ticker": "SPY", "w": 0.05, "dir": 1},
    "RSP": {"ticker": "RSP", "w": 0.10, "dir": 1},
    "IWM": {"ticker": "IWM", "w": 0.10, "dir": 1}
}

def generate_study():
    start_date = "1994-01-01"
    end_date = datetime.now().strftime("%Y-%m-%d")

    print("--- Step 1: Downloading Historical Data ---")
    try:
        # Get S&P 500 Close
        sp500_raw = yf.download("^GSPC", start=start_date, end=end_date, progress=False)
        sp500 = sp500_raw['Close']
    except Exception as e:
        print(f"Error fetching SP500: {e}")
        return

    data_frames = {}
    for name, info in indicators.items():
        print(f"Fetching {name}...")
        try:
            df = yf.download(info['ticker'], start=start_date, end=end_date, progress=False)['Close']
            data_frames[name] = df
        except:
            print(f"Warning: Skipping {name}")

    # Combine into one master table
    master_df = pd.DataFrame(data_frames)
    master_df['SP500'] = sp500
    master_df = master_df.sort_index().ffill()

    print("--- Step 2: Calculating 30-Year CRSS History ---")
    crss_series = []
    
    # Iterate through each day to calculate the rolling Z-Score
    for i in range(len(master_df)):
        if i < 252: # Need 1 year of prior data for the first calculation
            crss_series.append(np.nan)
            continue

        lookback = master_df.iloc[i-252:i]
        current = master_df.iloc[i]
        
        temp_score = 0
        active_weights = 0

        for name, info in indicators.items():
            if name not in current or pd.isna(current[name]):
                continue
            
            series = lookback[name].dropna()
            if len(series) < 150: # Ensure enough data points for a valid mean
                continue
            
            mean = series.mean()
            std = series.std()
            if std == 0: continue
            
            # Normalize to -1 to +1 range
            z = (current[name] - mean) / (std * 3)
            norm = max(min(z * info['dir'], 1), -1)
            
            temp_score += (norm * info['w'])
            active_weights += info['w']

        # Re-scale if some indicators were missing (e.g., pre-BTC)
        final_daily = (temp_score / active_weights) * 100 if active_weights > 0 else 0
        crss_series.append(round(final_daily, 2))

    master_df['CRSS'] = crss_series
    
    # Save the data starting from 1995
    final_output = master_df.loc["1995-01-01":][['CRSS', 'SP500']]
    final_output.to_csv('historical_crss_study.csv')
    print("--- SUCCESS: historical_crss_study.csv generated ---")

if __name__ == "__main__":
    generate_study()
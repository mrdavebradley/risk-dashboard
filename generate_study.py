import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# 1. Define Indicators and the new 'Lead-Heavy' weights
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
    # Note: For local script, we skip FRED/MM-Flows or use proxies to keep it simple
}

def generate_historical_study():
    print("Fetching historical data (1994 - Present)...")
    start_date = "1994-01-01" # 1 year buffer for 1995 start
    
    # Download S&P 500 for the 3rd column
    sp500 = yf.download("^GSPC", start=start_date)['Close']
    
    # Download all indicators
    data_frames = {}
    for name, info in indicators.items():
        print(f"Downloading {name}...")
        df = yf.download(info['ticker'], start=start_date, progress=False)['Close']
        data_frames[name] = df

    # Align all data into one table
    master_df = pd.DataFrame(data_frames)
    master_df['SP500'] = sp500
    master_df = master_df.fillna(method='ffill')

    # 2. Calculate Daily CRSS
    print("Calculating rolling scores...")
    crss_series = []
    
    for i in range(len(master_df)):
        if i < 252: # Need at least 1 year of data
            crss_series.append(np.nan)
            continue
            
        daily_scores = []
        current_row = master_df.iloc[i]
        lookback_window = master_df.iloc[i-252:i]
        
        active_weights = 0
        temp_score = 0
        
        for name, info in indicators.items():
            val = current_row[name]
            if pd.isna(val): continue # Asset didn't exist yet
            
            mean = lookback_window[name].mean()
            std = lookback_window[name].std()
            
            if std == 0: continue
            
            z = (val - mean) / (std * 3)
            norm = max(min(z * info['dir'], 1), -1)
            
            temp_score += (norm * info['w'])
            active_weights += info['w']
            
        # Re-weight to 100% based on what was available that day
        final_daily = (temp_score / active_weights) * 100 if active_weights > 0 else 0
        crss_series.append(round(final_daily, 2))

    master_df['CRSS'] = crss_series
    
    # Filter to 1995 onwards
    final_table = master_df.loc["1995-01-01":][['CRSS', 'SP500']]
    final_table.to_csv("historical_crss_study.csv")
    print("CSV Saved: historical_crss_study.csv")

    # 3. Create the Chart
    fig, ax1 = plt.subplots(figsize=(14, 7))
    
    # Plot S&P 500 (Log scale is better for 30 years)
    ax1.set_yscale('log')
    ax1.plot(final_table.index, final_table['SP500'], color='gray', alpha=0.3, label='S&P 500')
    ax1.set_ylabel('S&P 500 (Log Scale)', color='gray')
    
    # Plot CRSS
    ax2 = ax1.twinx()
    ax2.plot(final_table.index, final_table['CRSS'], color='emerald', linewidth=1, label='CRSS Score')
    ax2.axhline(y=35, color='green', linestyle='--', alpha=0.3)
    ax2.axhline(y=-35, color='red', linestyle='--', alpha=0.3)
    ax2.set_ylabel('CRSS Score', color='white')
    
    plt.title("Historical CRSS vs S&P 500 (1995-Present)")
    plt.savefig("historical_chart.png")
    print("Chart Saved: historical_chart.png")

if __name__ == "__main__":
    generate_historical_study()
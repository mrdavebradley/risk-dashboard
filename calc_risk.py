import yfinance as yf
import pandas as pd
from fredapi import Fred
import numpy as np

# --- SETUP ---
FRED_KEY = "370f65ef821e3a8625d72c28a55c764b"
fred = Fred(api_key=FRED_KEY)

def get_risk_score():
    print("Fetching market data... this may take a moment.")
    
    # 1. Define our Indicators: (Ticker, Direction, Weight)
    # Direction -1 means HIGHER value = MORE RISK (Risk-Off)
    # Direction +1 means HIGHER value = BETTER MARKET (Risk-On)
    indicators = {
        'VIX': {'ticker': '^VIX', 'dir': -1, 'w': 0.12},
        'DXY': {'ticker': 'DX-Y.NYB', 'dir': -1, 'w': 0.10},
        '10Y_Yield': {'ticker': 'DGS10', 'dir': 1, 'w': 0.08, 'source': 'fred'},
        'HY_Spread': {'ticker': 'BAMLH0A0HYM2', 'dir': -1, 'w': 0.12, 'source': 'fred'},
        'Gold': {'ticker': 'GC=F', 'dir': -1, 'w': 0.08},
        'BTC': {'ticker': 'BTC-USD', 'dir': 1, 'w': 0.05},
        'Copper': {'ticker': 'HG=F', 'dir': 1, 'w': 0.05}, # Used for Copper/Gold ratio
        'SPY': {'ticker': 'SPY', 'dir': 1, 'w': 0.00}, # Benchmark
        'RSP': {'ticker': 'RSP', 'dir': 1, 'w': 0.10}, # For Breadth
        'IWM': {'ticker': 'IWM', 'dir': 1, 'w': 0.08}  # For Small-caps
    }

    scores = []
    
# 2. Fetch Data and Calculate Normalization (The Math)
    for name, info in indicators.items():
        try:
            if info.get('source') == 'fred':
                data = fred.get_series(info['ticker']).dropna()
            else:
                # Updated to handle the new yfinance format
                downloaded = yf.download(info['ticker'], period="1y", interval="1d", progress=False)
                if isinstance(downloaded, pd.DataFrame) and not downloaded.empty:
                    # This ensures we get a single column of data regardless of formatting
                    data = downloaded['Close'].squeeze()
                else:
                    continue

            current_val = float(data.iloc[-1])
            mean_val = data.mean()
            std_val = data.std()
            
            # This is the N_i calculation from our equation
            z_score = (current_val - mean_val) / (std_val * 3)
            normalized_score = max(min(z_score * info['dir'], 1), -1)
            
            weighted_contribution = normalized_score * info['w']
            scores.append(weighted_contribution)
            print(f"✔ {name}: {current_val:.2f} (Contrib: {weighted_contribution:.2f})")
            
        except Exception as e:
            print(f"✘ Error fetching {name}: {e}")

    # 3. Final Calculation
    crss = sum(scores) * 100
    return round(crss, 2)

# Run it!
final_score = get_risk_score()
print("\n" + "="*30)
print(f"FINAL CRSS SCORE: {final_score}")

if final_score > 35:
    print("SENTIMENT: RISK-ON 🟢")
elif final_score < -35:
    print("SENTIMENT: RISK-OFF 🔴")
else:
    print("SENTIMENT: NEUTRAL 🟡")
print("="*30)